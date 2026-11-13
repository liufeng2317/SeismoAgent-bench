# 结果与决定

按 `design.md` 的顺序分节。只记结论性的数字，并写明来源文件；用户的决定写明日期。

## 用户的决定

| 日期 | 决定 |
|---|---|
| 2026-11-13 | 本任务是 SeismoAgentBench 仓库里的分支项目；研究、结论和建议只写在 `RSI_phasepicking/` 下，不推到上游项目层面 |
| 2026-11-13 | 不再联系 Advikar 索取试点的事件列表、评分程序和提交结果（联系不上）；试点的数字只作参考，按其描述自行重建同类设置 |
| 2026-11-13 | 不在 AGU 摘要库和 ESSOAr 中补充检索新颖性 |
| 2026-11-13 | 已核实两篇 SeisAgentBench：ICLR 2027 投稿做勘探地震数据处理，ICML 2026 海报做破裂反演，都不是直接竞争者；Si et al.（SSA 2026）是预训练大模型的拾取评测，不是 agent |
| 2026-11-13 | 测试候选不按模型训练截止划分，关心的是震相是否由人工拾取；先获取全部事件列表，波形只取少量，第一批几十个事件即可打通流程 |
| 2026-11-13 | 基础 baseline 的区域不选 Ridgecrest/Coso（该区研究多、与其他区域差别大），改选南加州其他区域 |

## a 数据与标签（调研阶段的初步结果）

这些数字来自调研阶段的小样本分析，正式选数据前由 a2、a4 更新。

| 结果 | 数字 | 来源 |
|---|---|---|
| SCSN 终审事件中 manual P 拾取的比例 | 2012 年 99%，2021 年 68%，2024 年 45%；Ridgecrest/Coso 2025–26 年 M2.5–3 为 57%；2019-07-04 至 06 约 80%（每组抽样 25–40 个事件） | `brain_storm/deep_research/01_analyst_picks_scsn_ncsn.md`；脚本 `brain_storm/deep_research/scripts/01_02_analyst_picks/` |
| SCSN 质量值与权重码 | 1.0/0.8/0.5/0.2 对应权重码 0–3（约 0.03/0.06/0.15/0.30 s） | 同上 |
| SCSN 与 NCSN 分析员间差异（36 个事件、374 对） | P 双方都标 i：中位 0.01 s、90% 分位 0.04 s；P 标 e 和 S：中位 0.05 s、90% 分位 0.30 s；两网是否共享拾取待确认 | `brain_storm/deep_research/02_pick_label_noise.md`；`brain_storm/deep_research/scripts/01_02_analyst_picks/cross_rows*.json` |

## b 基线流水线

| 结果 | 内容 | 来源 |
|---|---|---|
| SCSN 定位用的一维模型 | Hutton et al. 2010（BSSA 100(2)）：1932–2008 目录除 Long Beach 序列外都用 Hadley–Kanamori 模型定位，表 5 给出 SCSN 版本（层顶 0/5.5/16/32 km，Vp 5.5/6.3/6.7/7.8 km/s，Vp/Vs 1.73）；文中说该模型适合 Mojave 沙漠和 Transverse Ranges，在深盆地（Imperial Valley、洛杉矶盆地、Ventura 盆地）近似很差，并计划改用三维模型。2010 年以后的日常定位模型未核实 | https://authors.library.caltech.edu/records/bkpgd-rab65 （已读原文 PDF 第 8 页） |

## c 预实验（调研阶段的初步结果）

| 结果 | 数字 | 来源 |
|---|---|---|
| 留一残差对单个拾取误差的检出率（模拟：20 台、残余模型误差 0.1 s、误报 5%） | 0.1 s 约 1%，0.3 s 约 15%，1 s 约 96%；7 台时 1 s 约 33% | `brain_storm/deep_research/03_residuals_as_pick_feedback.md`；`brain_storm/deep_research/scripts/03_residual_detectability/detect_sim2_out.txt` |
