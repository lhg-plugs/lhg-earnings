# 灵感来源与致谢（Attribution）

本插件的**方法论灵感**来自以下优秀的开源项目与公开方法论，**所有实现代码、检测规则与文案均为原创**，未复制任何第三方的原文案与代码。

| 项目 | 作者 / 组织 | 许可 | 链接 | 借鉴了什么思路 |
|---|---|---|---|---|
| financial-statement-analysis | Viprasol-Tech | 未声明（公开仓库） | https://github.com/Viprasol-Tech/financial-statement-analysis | "把分析师的检查清单编码成确定性流程"的思想：比率公式展示、现金流质量检查、红旗扫描；本插件审计脚本的规则引擎模式受其启发，**规则条目全部自研** |
| financeskills | gajetoso | 未声明（公开仓库） | https://github.com/gajetoso/financeskills | 财经 skill 按"财务分析/审计合规/风险"分类组织的思想；本插件 4 个 skill 的分工受其启发 |
| financial-statement-agent | manojm404（hermes-skills-migration） | MIT | https://github.com/manojm404/hermes-skills-migration | 用 Python 脚本对 JSON 财务数据做同比/环比计算与异常规则扫描的模式（应收暴涨、现金流背离等）；本插件 `earnings_audit.py` 的数据驱动审计思想受其启发，**规则与代码全部原创** |
| ai-finance skills（earnings-analysis / ratio-analysis） | haiting202-web（jiufeng-invest） | 未声明（公开仓库） | https://github.com/haiting202-web/jiufeng-invest | "禁止编造数字、缺数据标注暂缺"的数据诚实纪律，以及输出强制风险提示的合规思想；本插件的数据诚实三原则与合规声明规范受其启发 |
| financial-statement-analysis | yunusemrejr（yunuspi） | 未声明（公开仓库） | 搜索可见的公开 skill | "区分报告数字、确定性计算与分析师假设"的思想；本插件"数字只抄不算、缺数据明确标注"的纪律受其启发 |
| laogu-report（定期报告深拆） | 老谷拆财报 / 刘洪光（用户自有 IP） | 自有 | https://github.com/laogu-caibao/laogu-report | 逐项拆解利润表/资产负债表/现金流量表的中文散户解读方法论；本插件主流程的"三表拆解"结构受其启发 |

## 声明

1. **借鉴思路，实现与文案均为原创**：以上项目的具体文案、规则原文、代码实现均未被复制。本插件的 skill 方法论文案、审计规则、命令流程、hooks 脚本均为独立撰写。
2. **许可合规**：上表项目均为公开仓库，MIT 许可的项目允许在保留声明的前提下进行思路借鉴与二次创作；未声明许可的项目仅做思路层面的借鉴，未复制任何代码与文案。本文件即为保留声明的一部分。
3. **商标与归属**：各项目名称与作者署名归其各自所有者所有。

## 本插件自身的许可

本插件原创部分采用 MIT 许可（见 `LICENSE` 文件），版权所有：刘洪光（https://github.com/lhg-skills）。
