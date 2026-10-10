---
description: 插件自查：跑冒烟测试 + 财报审计脚本 + 合规文案扫描，确认插件自身健康。
argument-hint: [--fix]
---

# /lhg-earnings:audit —— 插件自查

## 流程

### 1. 跑插件冒烟测试

```bash
cd ${CLAUDE_PLUGIN_ROOT} && python3 smoke_test.py
```

必须全绿：JSON 合法、skill/command/agent 完整、fixtures 埋点全命中、hooks 行为正确。

### 2. 跑财报审计脚本（用好坏 fixtures 自检）

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/audit/earnings_audit.py --target ${CLAUDE_PLUGIN_ROOT}/fixtures/report-bad --format text
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/audit/earnings_audit.py --target ${CLAUDE_PLUGIN_ROOT}/fixtures/report-good --format text
```

- 坏用例：必须 exit != 0，且 E-RISK-003 / E-COMP-001 / E-COMP-002 三个 blocker 全命中
- 好用例：必须 exit == 0，零 blocker

### 3. 合规文案扫描

检查本插件所有 skill 与命令文档：

- 每个 SKILL.md 开头有合规声明
- 全文无投顾表述（买入/卖出/目标价……）
- `/earnings` 输出模板末尾有合规声明

`--fix` 参数：自动修复可修复项（如补合规声明）；修不了的列入"需人工处理"。

## 硬规则

- 冒烟测试有失败就说"通过" → 不许。
- 为通过测试改 fixtures 或调松规则阈值 → 这是作弊，不许。
