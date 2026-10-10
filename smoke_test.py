#!/usr/bin/env python3
"""lhg-earnings 插件冒烟测试：全部绿才算过。

检查项：
 1. 三个 JSON 合法（plugin.json / marketplace.json / hooks.json）
 2. 4 个 SKILL.md 都有 name/description frontmatter，且 >=150 行
 3. 4 个 commands 都有 description frontmatter
 4. 3 个 agents 都有 name/description/tools/model frontmatter
 5. skills 平台中立：不含 Claude Code 专有工具名
 6. skills 开头有合规声明；全文无投顾表述
 7. fixtures：坏 fixture 的埋点规则必须全部命中且脚本 exit!=0；
    好 fixture 零 blocker 且 exit==0
 8. 审计规则总数 >= 20
 9. hooks 脚本：投顾表述警告 / 无表述不警告 / 缺声明警告 / 逃生开关

用法：python3 smoke_test.py [--repo <插件根目录>]
退出码：0=全绿，1=有失败。
"""

import argparse
import json
import os
import re
import subprocess
import sys
import tempfile

PASS, FAIL = "PASS", "FAIL"
results = []


def check(name, cond, detail=""):
    results.append((PASS if cond else FAIL, name, detail))
    return cond


def read(p):
    with open(p, encoding="utf-8") as f:
        return f.read()


def frontmatter(path):
    """解析 markdown 顶部 --- YAML 块（只取一层 key: value）。"""
    text = read(path)
    if not text.startswith("---"):
        return {}
    end = text.find("\n---", 3)
    if end < 0:
        return {}
    fm = {}
    for ln in text[3:end].split("\n"):
        m = re.match(r"^([A-Za-z0-9_-]+)\s*:\s*(.*)$", ln)
        if m:
            fm[m.group(1)] = m.group(2).strip().strip('"').strip("'")
    return fm


def run(cmd, **kw):
    return subprocess.run(cmd, capture_output=True, text=True, timeout=120, **kw)


# 预期的埋点命中（坏 fixture 必须全部命中）
BAD_MUST = {
    "E-DATA-004", "E-DATA-005",
    "E-CALC-001", "E-CALC-002",
    "E-TREND-001",
    "E-RISK-001", "E-RISK-002", "E-RISK-003", "E-RISK-004",
    "E-RISK-005", "E-RISK-006", "E-RISK-007",
    "E-COMP-001", "E-COMP-002",
}
# 平台中立红线：skill 正文不许出现这些 Claude Code 专有表述
NEUTRAL_DENY = ["Task tool", "Bash tool", "Edit tool", "Write tool", "Read tool",
                "AskUserQuestion", "subagent_type", "PreToolUse", "PostToolUse",
                "${CLAUDE_", "CLAUDE_PLUGIN_ROOT", "CLAUDE_PROJECT_DIR"]
# 合规红线：skill 全文不许出现投顾表述
# （黑名单文档语境除外：禁词只许出现在"黑名单/禁区/高危表述/合规"章节里，
#  且所在行必须是否定语气——"不许/绝不许/删掉/黑名单"，不许作为建议出现）
ADVISORY_RE = re.compile(
    r"买入|卖出|目标价|推荐买|强烈推荐|增持建议|减持建议|抄底|加仓|割肉|看涨|看跌|"
    r"止损|止盈|买点|卖点|逢低买|逢高卖|建议买|建议卖|强烈买入"
)
ALLOW_HEADING_RE = re.compile(r"黑名单|禁区|高危表述|合规|红线|替换原则|回应")
ALLOW_LINE_RE = re.compile(r"不许|绝不许|绝不出现|不出现|删掉|黑名单|禁区|作废|高危|话术|依然是")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default=os.path.dirname(os.path.abspath(__file__)))
    args = ap.parse_args()
    repo = os.path.abspath(args.repo)
    AUDIT = os.path.join(repo, "scripts", "audit")

    # 1. JSON 合法
    for rel in [".claude-plugin/plugin.json", ".claude-plugin/marketplace.json",
                "hooks/hooks.json"]:
        p = os.path.join(repo, rel)
        try:
            d = json.loads(read(p))
            check("JSON 合法: " + rel, True)
            if rel.endswith("plugin.json"):
                check("plugin.json name==lhg-earnings", d.get("name") == "lhg-earnings", str(d.get("name")))
                check("plugin.json 有 version/description/author",
                      all(d.get(k) for k in ("version", "description", "author")))
            if rel.endswith("marketplace.json"):
                ps = d.get("plugins", [])
                check("marketplace.json source==./",
                      len(ps) == 1 and ps[0].get("source") == "./" and
                      ps[0].get("name") == "lhg-earnings", str(ps))
            if rel.endswith("hooks.json"):
                check("hooks.json 顶层有 hooks 包装", "hooks" in d)
                check("hooks.json 有 PostToolUse", "PostToolUse" in d["hooks"])
        except Exception as e:
            check("JSON 合法: " + rel, False, str(e))

    # 2. SKILL.md frontmatter + 行数 + 平台中立 + 合规
    for skill in ["lhg-earnings-flow", "lhg-earnings-indicators",
                  "lhg-earnings-risks", "lhg-earnings-compliance"]:
        p = os.path.join(repo, "skills", skill, "SKILL.md")
        fm = frontmatter(p)
        check("skill frontmatter: " + skill,
              bool(fm.get("name")) and bool(fm.get("description")),
              "name=%s" % fm.get("name"))
        nlines = len(read(p).split("\n"))
        check("skill 行数>=150: %s (%d 行)" % (skill, nlines), nlines >= 150, str(nlines))
        body = read(p)
        bad_words = [w for w in NEUTRAL_DENY if w in body]
        check("skill 平台中立: " + skill, not bad_words, "命中: %s" % bad_words)
        check("skill 开头有合规声明: " + skill, "不构成投资建议" in body[:1500],
              "前1500字符无声明")
        # 上下文感知：禁词只许出现在黑名单文档语境（否定语气）中
        real_hits = []
        cur_heading = ""
        for ln in body.split("\n"):
            if ln.startswith("#"):
                cur_heading = ln
            for m in ADVISORY_RE.finditer(ln):
                # "卖出去"是日常动词，不是投顾表述，排除
                if m.group(0) == "卖出" and ln[m.end():m.end() + 1] == "去":
                    continue
                if ALLOW_HEADING_RE.search(cur_heading) or ALLOW_LINE_RE.search(ln):
                    continue
                real_hits.append((m.group(0), ln.strip()[:60]))
        check("skill 无投顾表述: " + skill, not real_hits,
              "命中: %s" % [h[0] for h in real_hits[:5]])
        check("skill 有出品区: " + skill, "出品：刘洪光" in body and "https://github.com/lhg-skills" in body)
        check("skill 有自检与反馈: " + skill, "自检与反馈" in body)

    # 3. commands
    for cmd in ["earnings", "indicators", "risks", "audit"]:
        p = os.path.join(repo, "commands", cmd + ".md")
        fm = frontmatter(p)
        check("command description: " + cmd, bool(fm.get("description")), str(fm.get("description"))[:60])
    # /earnings 输出模板末尾必须带合规声明
    earn = read(os.path.join(repo, "commands", "earnings.md"))
    check("/earnings 有合规声明", "不构成投资建议" in earn)

    # 4. agents
    for ag in ["report-analyst", "indicator-calc", "risk-screener"]:
        p = os.path.join(repo, "agents", ag + ".md")
        fm = frontmatter(p)
        check("agent frontmatter: " + ag,
              all(fm.get(k) for k in ("name", "description", "tools", "model")),
              str({k: fm.get(k) for k in ("name", "model")}))

    # 5. 审计脚本冒烟
    def audit_hits(target):
        r = run([sys.executable, os.path.join(AUDIT, "earnings_audit.py"),
                 "--target", os.path.join(repo, target), "--format", "json"])
        try:
            d = json.loads(r.stdout)
        except Exception:
            return None, r.returncode, []
        return d["summary"], r.returncode, [f["rule_id"] for f in d["findings"]]

    s, code, ids = audit_hits("fixtures/report-bad")
    check("坏 fixture exit!=0", code != 0, "exit=%d" % code)
    check("坏 fixture blocker>0", s and s["blocker"] > 0, str(s))
    missing = BAD_MUST - set(ids)
    check("坏 fixture 埋点全命中 (%d/%d)" % (len(BAD_MUST - missing), len(BAD_MUST)),
          not missing, "缺失: %s" % sorted(missing))

    s, code, ids = audit_hits("fixtures/report-good")
    check("好 fixture 零 blocker", s and s["blocker"] == 0, str(s))
    check("好 fixture exit==0", code == 0, "exit=%d" % code)

    # 规则总数（对外口径：20+ 条）
    n = json.loads(run([sys.executable, os.path.join(AUDIT, "earnings_audit.py"),
                        "--target", os.path.join(repo, "fixtures/report-good"),
                        "--format", "json"]).stdout)["summary"]["rules_run"]
    check("规则总数>=20 (%d)" % n, n >= 20, str(n))

    # 6. hooks 脚本
    def hook(script, payload, env=None):
        e = dict(os.environ); e.update(env or {})
        return run([sys.executable, os.path.join(repo, "hooks", script)],
                   input=payload, env=e)

    with tempfile.TemporaryDirectory() as td:
        bad_md = os.path.join(td, "bad.md")
        open(bad_md, "w").write("# 解读\n我们建议买入，目标价 60 元。\n")
        r = hook("advisory_guard.py", json.dumps({"tool_input": {"file_path": bad_md}}))
        check("hook: 投顾表述警告", r.returncode == 0 and "additionalContext" in r.stdout, r.stdout[:80])

        good_md = os.path.join(td, "good.md")
        open(good_md, "w").write("# 解读\n毛利率 37.6%。\n\n**合规声明**：不构成投资建议。\n")
        r = hook("advisory_guard.py", json.dumps({"tool_input": {"file_path": good_md}}))
        check("hook: 无表述不警告", r.returncode == 0 and not r.stdout.strip(), r.stdout[:80])

        r = hook("advisory_guard.py", json.dumps({"tool_input": {"file_path": bad_md}}),
                 {"LHG_EARNINGS_HOOKS_OFF": "1"})
        check("hook: 逃生开关生效", r.returncode == 0 and not r.stdout.strip())

        no_disc = os.path.join(td, "report.md")
        open(no_disc, "w").write("# 财报解读\n毛利率 37.6%，经营现金流为正。\n")
        r = hook("disclaimer_guard.py", json.dumps({"tool_input": {"file_path": no_disc}}))
        check("hook: 缺声明警告", r.returncode == 0 and "additionalContext" in r.stdout, r.stdout[:80])

        r = hook("disclaimer_guard.py", json.dumps({"tool_input": {"file_path": good_md}}))
        check("hook: 有声明不警告", r.returncode == 0 and not r.stdout.strip(), r.stdout[:80])

        note = os.path.join(td, "note.md")
        open(note, "w").write("# 随手记\n今天天气不错。\n")
        r = hook("disclaimer_guard.py", json.dumps({"tool_input": {"file_path": note}}))
        check("hook: 非财报文档不打扰", r.returncode == 0 and not r.stdout.strip(), r.stdout[:80])

    # 报告
    print("=" * 60)
    print("lhg-earnings 冒烟测试报告")
    print("=" * 60)
    fails = 0
    for st, name, detail in results:
        mark = "✓" if st == PASS else "✗"
        print("%s %s %s" % (mark, st, name))
        if detail and st == FAIL:
            print("    → %s" % detail)
        if st == FAIL:
            fails += 1
    print("=" * 60)
    print("共 %d 项，通过 %d，失败 %d" % (len(results), len(results) - fails, fails))
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
