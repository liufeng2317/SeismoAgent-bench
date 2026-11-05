# 进度与结果

工作清单和每项的状态见 [注册表](../01_Register.md)；这里放结果和检验记录。

| 位置 | 内容 | 更新方式 |
|---|---|---|
| [`2026-11-05_results_summary.md`](2026-11-05_results_summary.md) | 当前结果汇总：S0/S1 正式运行及图、后端消融及 checker 作用图、主要发现、进度 | 有新结果时更新 |
| [`SCORE_TABLE.md`](SCORE_TABLE.md) | 全部案例和运行的完整分数表 | 自动生成（`python -m SeismoAgentBench.scoring.catalog_metrics table`），不手改 |
| [`RESULTS_OVERVIEW.md`](RESULTS_OVERVIEW.md) | 一页概览：案例 × 配置矩阵，每次运行一行 | 同上 |
| [`checker_validation/`](checker_validation/README.md) | checker 的逐轮检验记录 01–10（方法、数据、读数） | 每轮检验后新增一篇，写成后不改结论 |
| [`backend_audit/`](backend_audit/README.md) | 后端消融运行的逐运行决策审计 | 写成后不改 |
| [`analyses/`](analyses/) | 专题分析：可达结果的互相关重定位（2026-11-04）；专家经验的证据（参数敏感性、错误选择、组件替换、知识替换） | 写成后只补更正 |
| [`archive/`](archive/) | 已被注册表取代的旧文档：10-30 的状态与计划、10-29 的进度汇总 | 不再更新 |
