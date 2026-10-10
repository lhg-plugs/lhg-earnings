#!/usr/bin/env python3
"""lhg-earnings 硬门②（警告级，不拦截）：财报解读报告缺少合规声明即提醒。

触发：PostToolUse / Write|Edit。当写入的 .md 文件看起来像一份财报解读
（含"财报"/"指标"/"毛利率"等关键词）却没有"不构成投资建议"声明时，
给出 additionalContext 警告，提醒补上合规声明。

逃生方式：
  1. 在报告末尾补上合规声明（推荐，模板见 skill lhg-earnings-compliance 第 3 节）。
  2. LHG_EARNINGS_HOOKS_OFF=1（环境变量，当前会话有效）。
  3. /plugin disable lhg-earnings（整个插件停用，hooks 不再触发）。

设计原则：内部出错 fail-open 只放行不打扰；永远 exit 0、不拦截写入。
零第三方依赖。
"""

import json
import os
import re
import sys

REPORT_HINT_RE = re.compile(r"财报|毛利率|净利率|资产负债率|经营现金流|解读报告")
TEXT_EXTS = {".md", ".markdown"}


def main() -> int:
    if os.environ.get("LHG_EARNINGS_HOOKS_OFF") == "1":
        return 0
    try:
        raw = sys.stdin.read()
        payload = json.loads(raw) if raw.strip() else {}
    except Exception:
        return 0  # fail-open

    tool_input = payload.get("tool_input", {}) or {}
    file_path = tool_input.get("file_path", "") or ""
    _, ext = os.path.splitext(file_path)
    if ext.lower() not in TEXT_EXTS:
        return 0

    content = tool_input.get("content") or ""
    if not content and os.path.isfile(file_path):
        try:
            with open(file_path, encoding="utf-8", errors="replace") as fh:
                content = fh.read()
        except OSError:
            return 0
    if not content:
        return 0

    if not REPORT_HINT_RE.search(content):
        return 0  # 不是财报解读，不打扰
    if "不构成投资建议" in content:
        return 0  # 已有声明，不打扰

    msg = (
        "合规提醒（lhg-earnings）：%s 疑似财报解读报告，但缺少「不构成投资建议」声明。\n"
        "请在报告末尾补上（模板见 skill lhg-earnings-compliance 第 3 节）：\n"
        "**合规声明**：数据源短板——本解读依赖用户提供或公开数据快照，\n"
        "非实时行情；本插件仅做财务数据解读教育，不构成投资建议。\n"
        "关闭本提醒：export LHG_EARNINGS_HOOKS_OFF=1（当前会话有效）。"
    ) % os.path.basename(file_path)
    out = {"hookSpecificOutput": {
        "hookEventName": "PostToolUse",
        "additionalContext": msg,
    }}
    sys.stdout.write(json.dumps(out, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
