#!/usr/bin/env python3
"""lhg-earnings 硬门①（警告级，不拦截）：写文档时命中投顾表述即提醒。

触发：PostToolUse / Write|Edit。扫描写入的 .md/.txt 文本，
命中买入/卖出/目标价等投顾表述时给出 additionalContext 警告。

逃生方式：
  1. 删掉或改写投顾表述（推荐）。
  2. LHG_EARNINGS_HOOKS_OFF=1（环境变量，当前会话有效）。
  3. /plugin disable lhg-earnings（整个插件停用，hooks 不再触发）。

设计原则：内部出错 fail-open 只放行不打扰；永远 exit 0、不拦截写入。
零第三方依赖。
"""

import json
import os
import re
import sys

ADVISORY_RE = re.compile(
    r"买入|卖出|目标价|推荐买|强烈推荐|增持建议|减持建议|抄底|加仓|割肉|看涨|看跌|"
    r"止损|止盈|买点|卖点|逢低买|逢高卖|建议买|建议卖|强烈买入"
)
TEXT_EXTS = {".md", ".txt", ".markdown"}


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

    # 读刚写入的内容（content 字段优先，拿不到就读文件）
    content = tool_input.get("content") or ""
    if not content and os.path.isfile(file_path):
        try:
            with open(file_path, encoding="utf-8", errors="replace") as fh:
                content = fh.read()
        except OSError:
            return 0
    if not content:
        return 0

    hits = []
    for i, ln in enumerate(content.split("\n")):
        m = ADVISORY_RE.search(ln)
        if m:
            hits.append((i + 1, m.group(0)))
            if len(hits) >= 5:
                break
    if not hits:
        return 0

    lines = ["合规提醒（lhg-earnings）：%s 命中投顾表述（本插件合规红线），请删掉或改写为中性事实描述。"
             % os.path.basename(file_path)]
    for lineno, word in hits:
        lines.append("- 第 %d 行命中「%s」" % (lineno, word))
    lines.append("黑名单见 skill lhg-earnings-compliance 第 2 节；"
                 "关闭本提醒：export LHG_EARNINGS_HOOKS_OFF=1（当前会话有效）。")
    out = {"hookSpecificOutput": {
        "hookEventName": "PostToolUse",
        "additionalContext": "\n".join(lines),
    }}
    sys.stdout.write(json.dumps(out, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
