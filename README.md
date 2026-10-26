<!-- About 简介（推送后填写到仓库 About 栏）：
财报分析助手，财报丢进来出指标解读与风险清单（非投资建议） ｜ 一键安装：/plugin marketplace add lhg-plugs/lhg-earnings
-->
<!-- topics（推送后打）：claude-code, claude-plugin, agent-skills, finance, earnings -->

# lhg-earnings：财报分析助手

> **一句话介绍**：把年报/季报（或关键数据）丢进来，自动算核心指标、做多期趋势对比、列风险清单（商誉/应收/存货/现金流背离）——小白也能看懂财报。
>
> **一键安装**：在 Claude Code 里运行
> ```
> /plugin marketplace add lhg-plugs/lhg-earnings
> /plugin install lhg-earnings@lhg-plugs
> ```

> **合规声明**：数据源短板——本插件依赖用户提供或公开数据快照，非实时行情；
> 本插件仅做财务数据解读教育，**不构成投资建议**。绝不输出买入/卖出/目标价等投顾表述。

## 它是什么

`lhg-earnings` 是一个 Claude Code 插件（plugin 为主、skill 为辅）：

- **4 个命令**（小白入口）：`earnings` 财报解读主流程，`indicators` 指标速算，`risks` 风险扫描，`audit` 插件自查
- **4 个平台中立 skill**（方法论，可移植到豆包/Workbuddy 等 agent 平台）：解读主流程、指标计算手册、风险扫描手册、合规手册
- **3 个专家 agent**：财报解读、指标计算、风险扫描
- **2 个合规硬门 hooks**：投顾表述警告、缺合规声明警告（均可一键豁免，不骚扰）
- **21 条确定性审计规则**：纯 Python、零第三方依赖，指标公式复算 + 数据缺失标记 + 同比/环比 + 风险阈值

## 4 个命令用法

| 命令 | 作用 | 示例 |
|---|---|---|
| `/lhg-earnings:earnings` | 财报丢进来 → 结构化 → 指标 → 趋势 → 风险清单 → 合规报告 | `/lhg-earnings:earnings` 然后粘贴财报 |
| `/lhg-earnings:indicators` | 指标速算：毛利率/净利率/ROE/资产负债率一键算出并复算 | `/lhg-earnings:indicators` 然后粘贴关键数据 |
| `/lhg-earnings:risks` | 风险扫描：21 条规则找雷，输出分级风险清单 | `/lhg-earnings:risks <数据目录>` |
| `/lhg-earnings:audit` | 插件自查：冒烟测试 + 审计脚本 + 合规文案扫描 | `/lhg-earnings:audit` |

## 自查说明

自查 = 确定性脚本（机器）+ 合规检查：

1. 先跑 `scripts/audit/earnings_audit.py`（21 条规则），零 LLM 成本；
2. 发现分三级：**blocker**（现金流背离、投顾表述、缺合规声明——必须修）、**warning**（高杠杆、商誉、应收暴涨等——修或写豁免理由）、**nit**（顺手修）；
3. 再按 `lhg-earnings-compliance` 的输出前检查清单过一遍（全文无投顾表述、末尾有合规声明、数字可追溯）。

blocker 清零才能发报告；为清零改规则算作弊，不许。

## 目录结构

```
lhg-earnings/
├── .claude-plugin/          # plugin.json（插件清单）+ marketplace.json（本仓即市场）
├── commands/                # 4 个命令：earnings / indicators / risks / audit
├── skills/                  # 4 个平台中立 skill（flow/indicators/risks/compliance）
├── agents/                  # 3 个专家 agent（report-analyst / indicator-calc / risk-screener）
├── hooks/                   # 2 个合规硬门（投顾表述警告 / 缺声明警告）+ 逃生说明
├── scripts/audit/           # 21 条确定性审计规则（零第三方依赖）
├── fixtures/                # 冒烟测试用例（坏/好对照）
├── smoke_test.py            # 一键冒烟测试
├── ATTRIBUTION.md           # 灵感来源与许可声明
└── LICENSE                  # MIT
```

## 什么时候用 / 什么时候不用（FAQ）

**什么时候用：**

- 你拿到一份年报/季报，想快速知道"赚不赚钱、健不健康、有没有雷"时 → 用 `/lhg-earnings:earnings`
- 你只想算几个指标、核对一下财报里的数据对不对时 → 用 `/lhg-earnings:indicators`
- 你想系统性地排查一家公司的财务风险（商誉、应收、存货、现金流）时 → 用 `/lhg-earnings:risks`
- 你想学习"财报到底怎么看"的方法论时 → 读它的 4 个 skill，平台中立，可移植

**什么时候不用：**

- 你想问"这只股票能不能买、目标价多少"时 → **不用，这是红线**。本插件只做财务数据解读教育，不构成投资建议，不回答任何买卖问题
- 你需要实时行情、盘中数据时 → 不用。本插件依赖用户提供或公开数据快照，非实时行情
- 你要的是估值建模（DCF、相对估值）时 → 不用，它的边界止于"解读财报"，不做估值与投资决策
- 你希望 AI 自由发挥、不接受合规硬门时 → 它的投顾表述警告会让你烦（可关，但那就别装它）

**合规问答：**

- **Q：它会告诉我买哪只股票吗？** A：不会。任何输出都不许带买入/卖出/目标价等投顾表述，这是插件的合规红线，审计脚本与 hooks 双重检查。
- **Q：它的数据是实时的吗？** A：不是。依赖你提供的数据或公开数据快照，报告开头必须声明数据来源。
- **Q：每份报告都有免责声明吗？** A：有。报告末尾强制带"不构成投资建议"声明，缺失会被审计脚本判为 blocker。

## lhg-plugs 插件矩阵

| 插件 | 一句话 | 安装 |
|---|---|---|
| [lhg-fullstack](https://github.com/lhg-plugs/lhg-fullstack) | 小白一句话 → 高质量全栈应用 | `/plugin install lhg-fullstack@lhg-plugs` |
| [lhg-video-edit](https://github.com/lhg-plugs/lhg-video-edit) | 一句话把口播素材剪成爆款短视频（+口播脚本子命令） | `/plugin install lhg-video-edit@lhg-plugs` |
| [lhg-wechat-article](https://github.com/lhg-plugs/lhg-wechat-article) | 公众号写作专家：选题到排版一气呵成 | `/plugin install lhg-wechat-article@lhg-plugs` |
| [lhg-xiaohongshu](https://github.com/lhg-plugs/lhg-xiaohongshu) | 小红书种草专家：卖点到爆款笔记一键生成 | `/plugin install lhg-xiaohongshu@lhg-plugs` |
| [lhg-resume](https://github.com/lhg-plugs/lhg-resume) | 简历优化专家：ATS诊断到模拟面试一条龙 | `/plugin install lhg-resume@lhg-plugs` |
| [lhg-ppt](https://github.com/lhg-plugs/lhg-ppt) | PPT制作专家：述职融资答辩一键成稿 | `/plugin install lhg-ppt@lhg-plugs` |
| [lhg-excel](https://github.com/lhg-plugs/lhg-excel) | 表格数据专家：清洗透视图表一条龙 | `/plugin install lhg-excel@lhg-plugs` |
| [lhg-thesis](https://github.com/lhg-plugs/lhg-thesis) | 毕业论文助手：开题到盲审的写作流水线 | `/plugin install lhg-thesis@lhg-plugs` |
| [lhg-miniprogram](https://github.com/lhg-plugs/lhg-miniprogram) | 小程序开发专家：一句话生成微信小程序 | `/plugin install lhg-miniprogram@lhg-plugs` |
| [lhg-contract](https://github.com/lhg-plugs/lhg-contract) | 合同审查助手：风险条款标红+修改建议 | `/plugin install lhg-contract@lhg-plugs` |
| [lhg-geo](https://github.com/lhg-plugs/lhg-geo) | AI搜索优化专家：品牌在AI回答里的可见度 | `/plugin install lhg-geo@lhg-plugs` |
| [lhg-poster](https://github.com/lhg-plugs/lhg-poster) | 海报设计专家：一句话生成手机端海报 | `/plugin install lhg-poster@lhg-plugs` |
| [lhg-shopify](https://github.com/lhg-plugs/lhg-shopify) | 独立站建站专家：高转化店铺一键搭建 | `/plugin install lhg-shopify@lhg-plugs` |
| [lhg-fiction](https://github.com/lhg-plugs/lhg-fiction) | 网文写作专家：大纲到逐章+人设一致性检测 | `/plugin install lhg-fiction@lhg-plugs` |
| [lhg-drama-script](https://github.com/lhg-plugs/lhg-drama-script) | 短剧剧本专家：分集大纲到单集剧本 | `/plugin install lhg-drama-script@lhg-plugs` |
| [lhg-lit-review](https://github.com/lhg-plugs/lhg-lit-review) | 文献综述专家：框架到引用校验一条龙 | `/plugin install lhg-lit-review@lhg-plugs` |
| [lhg-salary-talk](https://github.com/lhg-plugs/lhg-salary-talk) | 薪酬谈判专家：策略到话术演练 | `/plugin install lhg-salary-talk@lhg-plugs` |
| [lhg-biz-report](https://github.com/lhg-plugs/lhg-biz-report) | 商业分析专家：数据到图文报告一键生成 | `/plugin install lhg-biz-report@lhg-plugs` |
| [lhg-study-abroad](https://github.com/lhg-plugs/lhg-study-abroad) | 留学文书专家：PS推荐信多轮打磨 | `/plugin install lhg-study-abroad@lhg-plugs` |
| [lhg-meal-plan](https://github.com/lhg-plugs/lhg-meal-plan) | 营养食谱专家：测算到一周食谱+采购单 | `/plugin install lhg-meal-plan@lhg-plugs` |
| [lhg-competitor](https://github.com/lhg-plugs/lhg-competitor) | 竞品分析专家：五维框架+对比矩阵+SWOT+差异化建议报告 | `/plugin install lhg-competitor@lhg-plugs` |
| [lhg-social-ops](https://github.com/lhg-plugs/lhg-social-ops) | 社媒运营专家：定位→日历→分发策略→复盘，策略+复盘闭环 | `/plugin install lhg-social-ops@lhg-plugs` |
| [lhg-headline](https://github.com/lhg-plugs/lhg-headline) | 爆款标题专家：多平台标题公式生成+合规检测+点击率打分 | `/plugin install lhg-headline@lhg-plugs` |
| [lhg-logo](https://github.com/lhg-plugs/lhg-logo) | Logo设计专家：品牌概念→几何规范→多尺寸导出自检 | `/plugin install lhg-logo@lhg-plugs` |
| [lhg-ecom-design](https://github.com/lhg-plugs/lhg-ecom-design) | 电商视觉专家：卖点到高点击主图一键策划 | `/plugin install lhg-ecom-design@lhg-plugs` |
| [lhg-ecom-report](https://github.com/lhg-plugs/lhg-ecom-report) | 电商复盘专家：店铺数据到周/月复盘报告 | `/plugin install lhg-ecom-report@lhg-plugs` |
| [lhg-lesson-plan](https://github.com/lhg-plugs/lhg-lesson-plan) | 课程设计专家：课标对齐→教案课件→知识点覆盖校验 | `/plugin install lhg-lesson-plan@lhg-plugs` |
| [lhg-dashboard](https://github.com/lhg-plugs/lhg-dashboard) | 数据看板专家：指标体系→看板布局→图表规范校验 | `/plugin install lhg-dashboard@lhg-plugs` |
| [lhg-book-translate](https://github.com/lhg-plugs/lhg-book-translate) | 书籍翻译专家：术语锁定→章节翻译→一致性审计 | `/plugin install lhg-book-translate@lhg-plugs` |
| [lhg-infographic](https://github.com/lhg-plugs/lhg-infographic) | 信息图表专家：数据→图表选型→Canvas绘制→可读性审计 | `/plugin install lhg-infographic@lhg-plugs` |
| [lhg-live-script](https://github.com/lhg-plugs/lhg-live-script) | 直播话术专家：开播钩子到逼单成交，话术一次写完 | `/plugin install lhg-live-script@lhg-plugs` |
| [lhg-course-create](https://github.com/lhg-plugs/lhg-course-create) | 课程制作专家：大纲到试听课，一门课从 0 到可交付 | `/plugin install lhg-course-create@lhg-plugs` |
| [lhg-exam-maker](https://github.com/lhg-plugs/lhg-exam-maker) | 出题组卷专家：知识点→蓝图→组卷→覆盖率校验 | `/plugin install lhg-exam-maker@lhg-plugs` |
| [lhg-weekly-review](https://github.com/lhg-plugs/lhg-weekly-review) | 周报复盘专家：记录→结构化周报→亮点→风险预警 | `/plugin install lhg-weekly-review@lhg-plugs` |
| [lhg-money-plan](https://github.com/lhg-plugs/lhg-money-plan) | 理财规划助手：收支→预算→储蓄目标（非投资建议） | `/plugin install lhg-money-plan@lhg-plugs` |
| [lhg-finmodel](https://github.com/lhg-plugs/lhg-finmodel) | 财务建模专家：假设→三表搭建→勾稽校验→敏感性分析 | `/plugin install lhg-finmodel@lhg-plugs` |
| [lhg-mini-game](https://github.com/lhg-plugs/lhg-mini-game) | H5游戏专家：一句话生成可玩H5小游戏 | `/plugin install lhg-mini-game@lhg-plugs` |
| [lhg-browser-ext](https://github.com/lhg-plugs/lhg-browser-ext) | 浏览器插件专家：一句话想法生成MV3插件 | `/plugin install lhg-browser-ext@lhg-plugs` |
| [lhg-bp](https://github.com/lhg-plugs/lhg-bp) | 商业计划书专家：九章BP→投资人自检→路演版 | `/plugin install lhg-bp@lhg-plugs` |
| [lhg-survey](https://github.com/lhg-plugs/lhg-survey) | 问卷分析专家：清洗→统计→图表→结论报告 | `/plugin install lhg-survey@lhg-plugs` |
| [lhg-product-pick](https://github.com/lhg-plugs/lhg-product-pick) | 跨境选品专家：目标市场→五维打分表→供应链 checklist→风险清单 | `/plugin install lhg-product-pick@lhg-plugs` |
| [lhg-labor-rights](https://github.com/lhg-plugs/lhg-labor-rights) | 劳动维权助手：纠纷场景→仲裁流程指引→文书模板→证据清单 | `/plugin install lhg-labor-rights@lhg-plugs` |
| [lhg-pet-care](https://github.com/lhg-plugs/lhg-pet-care) | 宠物养护专家：建档→驱虫/疫苗/饮食时间表→健康 checklist | `/plugin install lhg-pet-care@lhg-plugs` |
| [lhg-oss-launch](https://github.com/lhg-plugs/lhg-oss-launch) | 开源冷启动专家：README→launch 素材→一键成片指引 | `/plugin install lhg-oss-launch@lhg-plugs` |
| [lhg-community](https://github.com/lhg-plugs/lhg-community) | 社群运营专家：定位→入群SOP→内容日历→转化话术→流失召回 | `/plugin install lhg-community@lhg-plugs` |
| [lhg-taobao](https://github.com/lhg-plugs/lhg-taobao) | 店铺运营专家：选品→上架→标题/主图优化→数据复盘 | `/plugin install lhg-taobao@lhg-plugs` |
| [lhg-sci-figure](https://github.com/lhg-plugs/lhg-sci-figure) | 学术图表专家：数据→期刊配图规范→图表生成→规范脚本校验 | `/plugin install lhg-sci-figure@lhg-plugs` |
| [lhg-sop](https://github.com/lhg-plugs/lhg-sop) | SOP沉淀专家：流程访谈→SOP文档→检查清单→版本管理 | `/plugin install lhg-sop@lhg-plugs` |
| [lhg-podcast](https://github.com/lhg-plugs/lhg-podcast) | 播客制作专家：选题→录制→剪辑→shownotes→分发，一期节目全流程 | `/plugin install lhg-podcast@lhg-plugs` |
| [lhg-motion-video](https://github.com/lhg-plugs/lhg-motion-video) | 动效视频专家：需求→导演brief→纯代码渲染→成片导出 | `/plugin install lhg-motion-video@lhg-plugs` |
| [lhg-user-growth](https://github.com/lhg-plugs/lhg-user-growth) | 用户增长专家：杠杆诊断→可执行实验清单→复盘 | `/plugin install lhg-user-growth@lhg-plugs` |
| [lhg-growth-lab](https://github.com/lhg-plugs/lhg-growth-lab) | 增长实验专家：假设→实验设计→显著性判定→复盘 | `/plugin install lhg-growth-lab@lhg-plugs` |
| [lhg-webscraper](https://github.com/lhg-plugs/lhg-webscraper) | 爬虫采集专家：合规方案→反爬应对→数据清洗（仅公开数据） | `/plugin install lhg-webscraper@lhg-plugs` |
| [lhg-sql](https://github.com/lhg-plugs/lhg-sql) | SQL取数专家：业务问题→SQL生成→方言适配→性能自检 | `/plugin install lhg-sql@lhg-plugs` |
| [lhg-api-integration](https://github.com/lhg-plugs/lhg-api-integration) | API对接专家：文档→鉴权→调用封装→重试限流→联调 | `/plugin install lhg-api-integration@lhg-plugs` |
| [lhg-email](https://github.com/lhg-plugs/lhg-email) | 邮件营销专家：用户分层→序列邮件→送达率checklist | `/plugin install lhg-email@lhg-plugs` |
| [lhg-ads](https://github.com/lhg-plugs/lhg-ads) | 广告投放专家：策略→素材清单→数据复盘（方法论非效果承诺） | `/plugin install lhg-ads@lhg-plugs` |
| [lhg-amazon-listing](https://github.com/lhg-plugs/lhg-amazon-listing) | 亚马逊运营专家：标题→五点→关键词→Listing评分 | `/plugin install lhg-amazon-listing@lhg-plugs` |
| [lhg-promo](https://github.com/lhg-plugs/lhg-promo) | 促销策划专家：玩法设计→利润测算→执行清单→复盘 | `/plugin install lhg-promo@lhg-plugs` |
| [lhg-user-research](https://github.com/lhg-plugs/lhg-user-research) | 用户调研专家：问卷/访谈提纲→回收分析→洞察报告 | `/plugin install lhg-user-research@lhg-plugs` |
| [lhg-insurance](https://github.com/lhg-plugs/lhg-insurance) | 保险配置助手：家庭保障缺口分析→四险种配置方案→条款坑点清单 | `/plugin install lhg-insurance@lhg-plugs` |
| [lhg-pr](https://github.com/lhg-plugs/lhg-pr) | PR发稿专家：事件→通稿三版本→媒体清单→发布节奏表 | `/plugin install lhg-pr@lhg-plugs` |
| [lhg-job-desc](https://github.com/lhg-plugs/lhg-job-desc) | JD撰写专家：岗位信息→评分→多版本，18条规则拦截歧视词 | `/plugin install lhg-job-desc@lhg-plugs` |
| [lhg-travel](https://github.com/lhg-plugs/lhg-travel) | 旅行规划专家：日行程→POI→预算表→打包清单，16条规则审计 | `/plugin install lhg-travel@lhg-plugs` |
| [lhg-event-plan](https://github.com/lhg-plugs/lhg-event-plan) | 活动策划专家：目标→预算/排期/风险清单→执行手册→复盘 | `/plugin install lhg-event-plan@lhg-plugs` |
| [lhg-rebuttal](https://github.com/lhg-plugs/lhg-rebuttal) | 论文返修专家：审稿意见→逐条回应→修改对照表→学术英语润色 | `/plugin install lhg-rebuttal@lhg-plugs` |
| [lhg-mobile-app](https://github.com/lhg-plugs/lhg-mobile-app) | 移动App专家：想法→MVP范围→跨端选型→上架checklist | `/plugin install lhg-mobile-app@lhg-plugs` |
| [lhg-cs-script](https://github.com/lhg-plugs/lhg-cs-script) | 客服话术专家：高频场景话术库+差评管理（review-care）+话术自查 | `/plugin install lhg-cs-script@lhg-plugs` |
| [lhg-startup-legal](https://github.com/lhg-plugs/lhg-startup-legal) | 创业法务助手：选型→注册→股权→协议一条龙（非律师意见） | `/plugin install lhg-startup-legal@lhg-plugs` |
| [lhg-ip](https://github.com/lhg-plugs/lhg-ip) | 知产保护助手：四象限判断→申请流程→维权清单（非律师意见） | `/plugin install lhg-ip@lhg-plugs` |
| [lhg-paper](https://github.com/lhg-plugs/lhg-paper) | 期刊论文助手：选题→框架→写作→图表→投稿自查→返修（学术诚信声明） | `/plugin install lhg-paper@lhg-plugs` |
| [lhg-grant](https://github.com/lhg-plugs/lhg-grant) | 基金申请助手：选题→申请书框架→评审视角自检→预算表 | `/plugin install lhg-grant@lhg-plugs` |
| [lhg-rental](https://github.com/lhg-plugs/lhg-rental) | 租房避坑助手：合同审查→押金/中介坑清单→纠纷应对模板 | `/plugin install lhg-rental@lhg-plugs` |
| [lhg-secondhand](https://github.com/lhg-plugs/lhg-secondhand) | 二手避坑助手：验机清单→价格评估→交易安全模板 | `/plugin install lhg-secondhand@lhg-plugs` |
| [lhg-experiment](https://github.com/lhg-plugs/lhg-experiment) | 实验设计专家：假设→实验设计→功效测算→结果解读 | `/plugin install lhg-experiment@lhg-plugs` |
| [lhg-patent](https://github.com/lhg-plugs/lhg-patent) | 专利撰写助手：交底书→权利要求书→说明书→新创性自检（需代理人复核） | `/plugin install lhg-patent@lhg-plugs` |
| [lhg-wedding](https://github.com/lhg-plugs/lhg-wedding) | 婚礼策划专家：预算→流程→供应商清单→当天执行手册 | `/plugin install lhg-wedding@lhg-plugs` |
| [lhg-fund-dca](https://github.com/lhg-plugs/lhg-fund-dca) | 基金定投助手：目标→定投计划→筛选框架→纪律执行（非投资建议） | `/plugin install lhg-fund-dca@lhg-plugs` |
| [lhg-earnings](https://github.com/lhg-plugs/lhg-earnings) | 财报分析助手：财报丢进来→指标解读→风险清单（非投资建议） | `/plugin install lhg-earnings@lhg-plugs` |

## 自检与反馈

本插件自带质检：每次使用后可跑 `python3 smoke_test.py` 一键验证（JSON 合法、skill/command/agent 完整性、合规声明、21 条规则、fixtures 命中、hooks 行为）。

发现 bug 或有改进建议，以 `[QC] <一句话问题>` 为标题提交到 https://github.com/lhg-plugs/lhg-earnings/issues，正文写清"复现步骤 → 实际表现 → 期望表现"。

## 出品：刘洪光

本插件由真人出镜 IP「刘洪光」（安徽合肥）出品，归属 [lhg-skills](https://github.com/lhg-skills)。

- GitHub 主页：https://github.com/lhg-skills —— 全部 skill 开源在此，欢迎 star
- 抖音：搜「刘老师讲AI实战」
- 微信：lhgsmsw
