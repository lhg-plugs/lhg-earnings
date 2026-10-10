#!/usr/bin/env python3
"""lhg-earnings 确定性财报审计：21 条规则，零第三方依赖。

扫描目标目录下的 data.json（财务数据）与 report.md（解读报告），做三件事：
  1. 指标公式复算（毛利率 / 净利率 / ROE / 资产负债率）
  2. 数据缺失标记与同比/环比异常提示
  3. 风险阈值提示（资产负债率>70%、经营现金流为负、现金流背离等）
  4. 合规检查（报告中不许出现买入/卖出/目标价等投顾表述；必须带"不构成投资建议"声明）

用法：
    python3 earnings_audit.py --target <目录> [--format json|text] [--fail-on blocker|warning|nit]

data.json 结构示例：
    {
      "company": "示例科技股份有限公司",
      "data_source": "用户提供（2025 年年报关键数据）",
      "periods": [
        {"label": "2024", "revenue": 1000, "cost": 650, "net_profit": 120,
         "equity": 800, "assets": 2000, "liabilities": 1200,
         "operating_cash_flow": 100, "receivables": 150, "inventory": 120,
         "goodwill": 60,
         "computed": {"gross_margin": 35.0, "net_margin": 12.0, "roe": 15.0, "debt_ratio": 60.0}}
      ]
    }
单位自由，但 periods 内必须统一。

规则与文案均为本项目原创。
"""

import argparse
import json
import os
import re
import sys

VERSION = "1.0.0"
TOOL = "lhg-earnings/earnings-audit"

# 投顾表述黑名单（合规红线：绝不许出现在输出报告里）
ADVISORY_RE = re.compile(
    r"买入|卖出|目标价|推荐买|强烈推荐|增持建议|减持建议|抄底|加仓|割肉|看涨|看跌|"
    r"止损|止盈|买点|卖点|逢低买|逢高卖|建议买|建议卖|买方|卖方评级|强烈买入"
)

EXIT_BY_LEVEL = {"blocker": 2, "warning": 1, "nit": 1}


class Finding:
    __slots__ = ("rule_id", "severity", "category", "title", "file", "line", "snippet", "detail")

    def __init__(self, rule_id, severity, category, title, file, line, snippet, detail):
        self.rule_id = rule_id
        self.severity = severity
        self.category = category
        self.title = title
        self.file = file
        self.line = line
        self.snippet = snippet
        self.detail = detail

    def to_dict(self):
        return {
            "rule_id": self.rule_id, "severity": self.severity,
            "category": self.category, "title": self.title,
            "file": self.file, "line": self.line,
            "snippet": self.snippet, "detail": self.detail,
        }


RULES = []
_RULE_BY_ID = {}


def rule(rule_id, severity, category, title, detail):
    def deco(fn):
        r = {"id": rule_id, "severity": severity,
             "category": category, "title": title, "detail": detail}
        _RULE_BY_ID[rule_id] = r
        r["check"] = fn
        RULES.append(r)
        return fn
    return deco


def F(rule_id, path, line=0, snippet=""):
    r = _RULE_BY_ID[rule_id]
    return Finding(r["id"], r["severity"], r["category"], r["title"],
                   path, line, snippet, r["detail"])


def get(p, key):
    v = p.get(key)
    return v if isinstance(v, (int, float)) and not isinstance(v, bool) else None


def pct(dev):
    """绝对偏差转百分点展示。"""
    return abs(dev)


# ---------------- 数据完整性 ----------------

@rule("E-DATA-001", "blocker", "数据完整性", "data.json 缺失或不可解析",
      "目标目录下没有可解析的 data.json。没有数据一切免谈：请按模板先把财报关键数据结构化。")
def r_data_001(ctx):
    if ctx["data"] is None:
        return [F("E-DATA-001", ctx["data_path"])]
    return []


@rule("E-DATA-002", "blocker", "数据完整性", "缺公司名或无任何财报期",
      "company 或 periods 缺失/为空。至少要提供一个报告期的财务数据，趋势解读至少需要两期。")
def r_data_002(ctx):
    d = ctx["data"]
    if d is None:
        return []
    if not d.get("company") or not d.get("periods"):
        return [F("E-DATA-002", ctx["data_path"])]
    return []


@rule("E-DATA-003", "blocker", "数据完整性", "某期缺关键字段",
      "某报告期缺 revenue / net_profit / assets 之一。这些是算增速、算利润率、算杠杆的"
      "最小必需集，缺了指标全是猜的。")
def r_data_003(ctx):
    d = ctx["data"]
    if d is None or not d.get("periods"):
        return []
    out = []
    for p in d["periods"]:
        missing = [k for k in ("revenue", "net_profit", "assets") if get(p, k) is None]
        if missing:
            out.append(F("E-DATA-003", ctx["data_path"], 0,
                         "%s 缺：%s" % (p.get("label", "?"), "、".join(missing))))
    return out


@rule("E-DATA-004", "warning", "数据完整性", "某期缺可选字段",
      "缺 cost / equity / liabilities / operating_cash_flow / receivables / inventory / goodwill"
      " 中的部分字段。缺啥、对应的指标（毛利率 / ROE / 杠杆 / 现金流 / 周转 / 商誉风险）就做不了，"
      "报告里必须明确标注「缺数据」，不许编。")
def r_data_004(ctx):
    d = ctx["data"]
    if d is None or not d.get("periods"):
        return []
    out = []
    for p in d["periods"]:
        missing = [k for k in ("cost", "equity", "liabilities", "operating_cash_flow",
                               "receivables", "inventory", "goodwill") if get(p, k) is None]
        if missing:
            out.append(F("E-DATA-004", ctx["data_path"], 0,
                         "%s 缺：%s" % (p.get("label", "?"), "、".join(missing))))
    return out


@rule("E-DATA-005", "warning", "数据完整性", "数据来源未声明",
      "data.json 没有 data_source 字段。本插件依赖用户提供或公开数据快照、非实时行情，"
      "来源必须声明，否则读者会误以为是官方实时数据。")
def r_data_005(ctx):
    d = ctx["data"]
    if d is None:
        return []
    if not d.get("data_source"):
        return [F("E-DATA-005", ctx["data_path"])]
    return []


# ---------------- 指标公式复算 ----------------

def _calc_hits(ctx, key, need, formula, unit):
    d = ctx["data"]
    out = []
    for p in d.get("periods", []):
        vals = {k: get(p, k) for k in need}
        if any(v is None for v in vals.values()):
            continue
        reported = (p.get("computed") or {}).get(key)
        if reported is None:
            continue
        actual = formula(vals)
        if actual is None:
            continue
        if pct(actual - reported) > 1.0:
            out.append(F("E-CALC-001" if key == "gross_margin" else
                         "E-CALC-002" if key == "net_margin" else
                         "E-CALC-003" if key == "roe" else "E-CALC-004",
                         ctx["data_path"], 0,
                         "%s：公式复算 %s%s，报告写了 %s%s（偏差>1个百分点）"
                         % (p.get("label", "?"), round(actual, 2), unit,
                            round(reported, 2), unit)))
    return out


@rule("E-CALC-001", "warning", "公式复算", "毛利率复算偏差",
      "毛利率 = (营收 - 营业成本) / 营收 × 100%。复算值与报告值偏差超过 1 个百分点，"
      "说明数据口径或计算有问题，先对账再解读。")
def r_calc_001(ctx):
    d = ctx["data"]
    if d is None or not d.get("periods"):
        return []
    return _calc_hits(ctx, "gross_margin", ("revenue", "cost"),
                      lambda v: (v["revenue"] - v["cost"]) / v["revenue"] * 100
                      if v["revenue"] else None, "%")


@rule("E-CALC-002", "warning", "公式复算", "净利率复算偏差",
      "净利率 = 净利润 / 营收 × 100%。偏差超过 1 个百分点先对账：常见原因是混用了"
      "归母净利润和扣非净利润。")
def r_calc_002(ctx):
    d = ctx["data"]
    if d is None or not d.get("periods"):
        return []
    return _calc_hits(ctx, "net_margin", ("revenue", "net_profit"),
                      lambda v: v["net_profit"] / v["revenue"] * 100
                      if v["revenue"] else None, "%")


@rule("E-CALC-003", "warning", "公式复算", "ROE 复算偏差",
      "ROE = 净利润 / 净资产 × 100%（简易口径；严谨口径用平均净资产）。"
      "偏差超过 1 个百分点先对账：常见原因是净资产用了期末值还是平均值口径不一。")
def r_calc_003(ctx):
    d = ctx["data"]
    if d is None or not d.get("periods"):
        return []
    return _calc_hits(ctx, "roe", ("net_profit", "equity"),
                      lambda v: v["net_profit"] / v["equity"] * 100
                      if v["equity"] else None, "%")


@rule("E-CALC-004", "warning", "公式复算", "资产负债率复算偏差",
      "资产负债率 = 总负债 / 总资产 × 100%。偏差超过 1 个百分点先对账。")
def r_calc_004(ctx):
    d = ctx["data"]
    if d is None or not d.get("periods"):
        return []
    return _calc_hits(ctx, "debt_ratio", ("liabilities", "assets"),
                      lambda v: v["liabilities"] / v["assets"] * 100
                      if v["assets"] else None, "%")


# ---------------- 趋势 ----------------

@rule("E-TREND-001", "warning", "趋势", "营收增速异常波动",
      "营收同比增速超过 ±50%。先排除并购/剥离/会计政策变更等一次性因素，"
      "再谈「增长」时，别把并表增长当内生增长。")
def r_trend_001(ctx):
    d = ctx["data"]
    if d is None:
        return []
    ps = d.get("periods", [])
    out = []
    for prev, cur in zip(ps, ps[1:]):
        pr, cr = get(prev, "revenue"), get(cur, "revenue")
        if pr and cr and pr != 0:
            g = (cr - pr) / abs(pr) * 100
            if abs(g) > 50:
                out.append(F("E-TREND-001", ctx["data_path"], 0,
                             "%s→%s 营收增速 %s%%，波动过大"
                             % (prev.get("label"), cur.get("label"), round(g, 1))))
    return out


@rule("E-TREND-002", "warning", "趋势", "净利润剧烈波动或盈亏互转",
      "净利润同比增速超过 ±100% 或由盈转亏/由亏转盈。这种波动多半来自非经常性损益，"
      "必须拆出扣非净利润再看主业成色。")
def r_trend_002(ctx):
    d = ctx["data"]
    if d is None:
        return []
    ps = d.get("periods", [])
    out = []
    for prev, cur in zip(ps, ps[1:]):
        pn, cn = get(prev, "net_profit"), get(cur, "net_profit")
        if pn is None or cn is None:
            continue
        label = "%s→%s" % (prev.get("label"), cur.get("label"))
        if (pn > 0) != (cn > 0) or (pn == 0) != (cn == 0):
            out.append(F("E-TREND-002", ctx["data_path"], 0, label + " 盈亏互转"))
        elif pn != 0 and abs((cn - pn) / abs(pn) * 100) > 100:
            out.append(F("E-TREND-002", ctx["data_path"], 0,
                         label + " 净利增速 %s%%，波动剧烈" % round((cn - pn) / abs(pn) * 100, 1)))
    return out


@rule("E-TREND-003", "nit", "趋势", "只有一期数据，做不了趋势",
      "只有一期数据时同比/环比都算不出来，解读只能停留在「单期体检」层面，"
      "报告里必须写清楚这是单期快照、不是趋势判断。")
def r_trend_003(ctx):
    d = ctx["data"]
    if d is None:
        return []
    ps = d.get("periods", [])
    if len(ps) == 1:
        return [F("E-TREND-003", ctx["data_path"])]
    return []


# ---------------- 风险阈值 ----------------

@rule("E-RISK-001", "warning", "风险", "资产负债率超过 70%",
      "资产负债率 > 70% 属于高杠杆区间。先看行业属性（金融/地产天然高杠杆），"
      "再看有息负债占比与利息保障倍数，别只看一个数下结论。")
def r_risk_001(ctx):
    d = ctx["data"]
    if d is None:
        return []
    out = []
    for p in d.get("periods", []):
        l, a = get(p, "liabilities"), get(p, "assets")
        if l is not None and a:
            r = l / a * 100
            if r > 70:
                out.append(F("E-RISK-001", ctx["data_path"], 0,
                             "%s 资产负债率 %s%%" % (p.get("label"), round(r, 1))))
    return out


@rule("E-RISK-002", "warning", "风险", "经营现金流为负",
      "经营活动现金流净额为负。利润表可以靠会计估计调节，现金流是试金石："
      "连续为负先看是扩张性投入（正常）还是回款恶化（危险）。")
def r_risk_002(ctx):
    d = ctx["data"]
    if d is None:
        return []
    return [F("E-RISK-002", ctx["data_path"], 0, "%s 经营现金流 %s" % (p.get("label"), get(p, "operating_cash_flow")))
            for p in d.get("periods", []) if get(p, "operating_cash_flow") is not None
            and get(p, "operating_cash_flow") < 0]


@rule("E-RISK-003", "blocker", "风险", "净利润为正但经营现金流为负（现金流背离）",
      "账面盈利、现金流失血：典型的利润质量红灯。常见病因是应收账款/存货积压"
      "或激进的收入确认。解读报告必须把这一条放在风险清单首位，不许轻描淡写。")
def r_risk_003(ctx):
    d = ctx["data"]
    if d is None:
        return []
    out = []
    for p in d.get("periods", []):
        n, c = get(p, "net_profit"), get(p, "operating_cash_flow")
        if n is not None and c is not None and n > 0 and c < 0:
            out.append(F("E-RISK-003", ctx["data_path"], 0,
                         "%s 净利 %s 但经营现金流 %s" % (p.get("label"), n, c)))
    return out


@rule("E-RISK-004", "warning", "风险", "商誉占净资产超过 30%",
      "商誉 / 净资产 > 30%。商誉是并购溢价的「空气」，减值测试主观性强，"
      "高商誉公司一旦业绩变脸就是商誉减值暴雷。必须去看并购标的的业绩承诺完成情况。")
def r_risk_004(ctx):
    d = ctx["data"]
    if d is None:
        return []
    out = []
    for p in d.get("periods", []):
        g, e = get(p, "goodwill"), get(p, "equity")
        if g is not None and e:
            r = g / e * 100
            if r > 30:
                out.append(F("E-RISK-004", ctx["data_path"], 0,
                             "%s 商誉/净资产 %s%%" % (p.get("label"), round(r, 1))))
    return out


@rule("E-RISK-005", "warning", "风险", "应收账款增速远超营收增速",
      "应收账款增速 - 营收增速 > 20 个百分点。钱没收回来、收入先确认了："
      "要么是放宽信用政策冲收入，要么是下游出问题。去看账龄结构和坏账计提。")
def r_risk_005(ctx):
    d = ctx["data"]
    if d is None:
        return []
    ps = d.get("periods", [])
    out = []
    for prev, cur in zip(ps, ps[1:]):
        pr, cr = get(prev, "revenue"), get(cur, "revenue")
        pa, ca = get(prev, "receivables"), get(cur, "receivables")
        if pr and cr and pa and ca and pr != 0 and pa != 0:
            rg = (cr - pr) / abs(pr) * 100
            ag = (ca - pa) / abs(pa) * 100
            if ag - rg > 20:
                out.append(F("E-RISK-005", ctx["data_path"], 0,
                             "%s→%s 应收增速 %s%% vs 营收增速 %s%%"
                             % (prev.get("label"), cur.get("label"),
                                round(ag, 1), round(rg, 1))))
    return out


@rule("E-RISK-006", "warning", "风险", "存货增速远超营收增速",
      "存货增速 - 营收增速 > 20 个百分点。货卖不动先囤着：要么是备货赌行情，"
      "要么是滞销。去看存货跌价准备计提是否充足。")
def r_risk_006(ctx):
    d = ctx["data"]
    if d is None:
        return []
    ps = d.get("periods", [])
    out = []
    for prev, cur in zip(ps, ps[1:]):
        pr, cr = get(prev, "revenue"), get(cur, "revenue")
        pi, ci = get(prev, "inventory"), get(cur, "inventory")
        if pr and cr and pi and ci and pr != 0 and pi != 0:
            rg = (cr - pr) / abs(pr) * 100
            ig = (ci - pi) / abs(pi) * 100
            if ig - rg > 20:
                out.append(F("E-RISK-006", ctx["data_path"], 0,
                             "%s→%s 存货增速 %s%% vs 营收增速 %s%%"
                             % (prev.get("label"), cur.get("label"),
                                round(ig, 1), round(rg, 1))))
    return out


@rule("E-RISK-007", "warning", "风险", "毛利率同比下滑超 5 个百分点",
      "毛利率同比下滑 > 5 个百分点。先区分是价格战（收入端）、成本上涨（成本端），"
      "还是一次性因素；连续下滑要看产品竞争力是否在丧失。")
def r_risk_007(ctx):
    d = ctx["data"]
    if d is None:
        return []
    ps = d.get("periods", [])
    out = []
    for prev, cur in zip(ps, ps[1:]):
        def gm(p):
            r, c = get(p, "revenue"), get(p, "cost")
            return (r - c) / r * 100 if r and c is not None else None
        g0, g1 = gm(prev), gm(cur)
        if g0 is not None and g1 is not None and g0 - g1 > 5:
            out.append(F("E-RISK-007", ctx["data_path"], 0,
                         "%s→%s 毛利率 %s%%→%s%%，下滑 %s 个百分点"
                         % (prev.get("label"), cur.get("label"),
                            round(g0, 1), round(g1, 1), round(g0 - g1, 1))))
    return out


# ---------------- 合规 ----------------

@rule("E-COMP-001", "blocker", "合规", "报告含投顾表述",
      "report.md 里出现了买入/卖出/目标价/抄底/加仓等投顾表述。这是插件的合规红线："
      "本插件只做财务数据解读教育，绝不输出买卖建议。删掉或改写为中性事实描述。")
def r_comp_001(ctx):
    if ctx["report"] is None:
        return []
    out = []
    for i, ln in enumerate(ctx["report"].split("\n")):
        m = ADVISORY_RE.search(ln)
        if m:
            out.append(F("E-COMP-001", ctx["report_path"], i + 1,
                         "命中「%s」：%s" % (m.group(0), ln.strip()[:80])))
    return out


@rule("E-COMP-002", "blocker", "合规", "报告缺少合规声明",
      "report.md 里没有「不构成投资建议」声明。每份解读报告末尾必须带合规声明："
      "数据源短板 + 仅做解读教育 + 不构成投资建议。这是红线，不是可选项。")
def r_comp_002(ctx):
    if ctx["report"] is None:
        return []
    if "不构成投资建议" not in ctx["report"]:
        return [F("E-COMP-002", ctx["report_path"])]
    return []


# ---------------- 主流程 ----------------

def load_target(target):
    data_path = os.path.join(target, "data.json")
    report_path = os.path.join(target, "report.md")
    data = None
    try:
        with open(data_path, encoding="utf-8") as fh:
            data = json.load(fh)
    except OSError:
        data = None
    except json.JSONDecodeError:
        data = "INVALID"
    report = None
    if os.path.isfile(report_path):
        try:
            with open(report_path, encoding="utf-8") as fh:
                report = fh.read()
        except OSError:
            report = None
    return {"data": None if data == "INVALID" else data,
            "data_invalid": data == "INVALID",
            "data_path": data_path,
            "report": report, "report_path": report_path}


def run_checks(ctx):
    findings = []
    for r in RULES:
        try:
            findings.extend(r["check"](ctx))
        except Exception as e:  # 单规则失败不拖累整体
            findings.append(Finding(r["id"], "nit", "脚本自身", "规则执行异常",
                                    ctx["data_path"], 0, str(e)[:120], ""))
    if ctx["data_invalid"]:
        findings.insert(0, Finding("E-DATA-001", "blocker", "数据完整性",
                                   "data.json 缺失或不可解析", ctx["data_path"], 0,
                                   "JSON 解析失败", ""))
    return findings


def summarize(findings):
    s = {"blocker": 0, "warning": 0, "nit": 0}
    for f in findings:
        s[f.severity] = s.get(f.severity, 0) + 1
    return s


def render_text(findings, summary):
    lines = ["[%s] 财报审计：blocker=%d warning=%d nit=%d（共 %d 条规则）"
             % (TOOL, summary["blocker"], summary["warning"], summary["nit"], len(RULES))]
    order = {"blocker": 0, "warning": 1, "nit": 2}
    for f in sorted(findings, key=lambda x: (order.get(x.severity, 3), x.rule_id)):
        loc = f.file + (":%d" % f.line if f.line else "")
        lines.append("[%s][%s] %s @ %s" % (f.severity.upper(), f.rule_id, f.title, loc))
        if f.snippet:
            lines.append("    %s" % f.snippet)
        if f.detail:
            lines.append("    → %s" % f.detail)
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser(description="lhg-earnings 确定性财报审计（21 条规则）")
    ap.add_argument("--target", required=True, help="含 data.json（可选 report.md）的目录")
    ap.add_argument("--format", choices=("json", "text"), default="text")
    ap.add_argument("--fail-on", choices=("blocker", "warning", "nit"), default="blocker",
                    help="达到该级别即非零退出")
    args = ap.parse_args()

    ctx = load_target(args.target)
    findings = run_checks(ctx)
    summary = summarize(findings)
    summary["rules_run"] = len(RULES)

    if args.format == "json":
        print(json.dumps({"tool": TOOL, "version": VERSION, "summary": summary,
                          "findings": [f.to_dict() for f in findings]},
                         ensure_ascii=False, indent=2))
    else:
        print(render_text(findings, summary))

    levels = {"blocker": 3, "warning": 2, "nit": 1}
    worst = max([levels.get(f.severity, 0) for f in findings], default=0)
    return 2 if worst >= levels[args.fail_on] else 0


if __name__ == "__main__":
    sys.exit(main())
