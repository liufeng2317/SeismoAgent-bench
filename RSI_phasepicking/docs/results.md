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
| 2026-11-13 | 开始挑选第一批并下载波形；用户未另指定区域，按建议使用 R2（圣贝纳迪诺山、Cajon Pass） |
| 2026-11-13 | 短周期台（只有 EHZ、水平向只有加速度计）的 PhaseNet 输入用 EHZ + HNE + HNN 拼成三分量，与分析员的做法一致 |
| 2026-11-13 | 基线分三层：基础 base 是 STA/LTA + AIC；PhaseNet、EQTransformer 等同域 DL 拾取器及其集成是强基线，代表 DL 训练的天花板，用于对比最终结果；agent + 强基线用于 OOD 区域和极端情况，由 agent 调整拾取、剔除明显错误 |
| 2026-11-13 | 研究主线是一条递进的链：Q1 基础 base + agent 能否持续提升 → Q2 持续提升说明 RSI 可行 → Q3 上限能否达到或超过 PhaseNet 等基线 → Q4 在 DL 的 OOD 场景中能否迭代出拾取专家；原 H1–H4 改编为 Q1–Q4 和辅助问题 S1、S2 |

## a 数据与标签（调研阶段的初步结果）

这些数字来自调研阶段的小样本分析，正式选数据前由 a2、a4 更新。

| 结果 | 数字 | 来源 |
|---|---|---|
| SCSN 终审事件中 manual P 拾取的比例 | 2012 年 99%，2021 年 68%，2024 年 45%；Ridgecrest/Coso 2025–26 年 M2.5–3 为 57%；2019-07-04 至 06 约 80%（每组抽样 25–40 个事件） | `brain_storm/deep_research/01_analyst_picks_scsn_ncsn.md`；脚本 `brain_storm/deep_research/scripts/01_02_analyst_picks/` |
| SCSN 质量值与权重码 | 1.0/0.8/0.5/0.2 对应权重码 0–3（约 0.03/0.06/0.15/0.30 s） | 同上 |
| SCSN 与 NCSN 分析员间差异（36 个事件、374 对） | P 双方都标 i：中位 0.01 s、90% 分位 0.04 s；P 标 e 和 S：中位 0.05 s、90% 分位 0.30 s；两网是否共享拾取待确认 | `brain_storm/deep_research/02_pick_label_noise.md`；`brain_storm/deep_research/scripts/01_02_analyst_picks/cross_rows*.json` |

### a1、a2 第 1 轮：候选区域与标签统计（2026-11-13）

候选区域：50 km 圈，排除与 Ridgecrest/Coso 框重叠的圈、M≥2.5 事件 20% 以上落在深盆地框内的圈，要求圈内 ≥25 个 CI/AZ 台站，候选之间相距 ≥100 km。来源：`results/a_data_labels/a1_events/candidate_regions.csv`。标签统计为 2020-01 至 2026-11-12 全部 M≥2.5 事件（582 个）的 SCEDC QuakeML。来源：`results/a_data_labels/a2_labels/region_summary.csv` 及同目录的分项表。

| 区域 | 位置 | 事件 | 台站 | 人工 P 比例（剔除 PhaseNet 时段后） | 人工 S 比例 | 最近 5 台人工 P | 每事件人工 P 中位数 | 人工 P 中 impulsive | 方位角空隙中位数 |
|---|---|---|---|---|---|---|---|---|---|
| R1 | 圣哈辛托断层带（Anza、San Gorgonio Pass） | 267 | 43 | 0.59（0.59） | 0.91 | 0.43 | 59 | 0.32 | 22° |
| R2 | 圣贝纳迪诺山、Cajon Pass | 159 | 50 | 0.64（0.66） | 0.91 | 0.52 | 81 | 0.31 | 17° |
| R3 | 西 Transverse Ranges、Tejon | 123 | 35 | 0.71（0.74） | 0.92 | 0.58 | 50 | 0.27 | 25° |
| R4 | 圣迭戈 | 33 | 31 | 0.66（0.66） | 0.91 | 0.68 | 57 | 0.36 | 28° |

- 每个区几乎所有 M≥2.5 事件都有 ≥10 个人工 P 拾取（R1 266/267，R2 159/159，R3 120/123，R4 31/33）。
- 人工 P 比例随震级升高：M3–4 比 M2.5–3 高 6–14 个百分点（R4 除外）。
- 人工 P 中有极性的比例与 impulsive 比例几乎相同（约 0.26–0.36），极性基本只标在 impulsive 起始上。
- 人工 P 的权重码以 2 为主（约 60–68%），权重码 0 只占约 7–10%。
- 每个事件的拾取数中位约 130–250 个，远多于试点的约 30 个台站：SCEDC 目录包含远台拾取，选台站时要按区域框截取。

### a1 第 3 轮：第一批事件和台站（2026-11-13）

来源：`results/a_data_labels/a1_first_batch/`（`stations.csv`、`events.csv`、`selection.json`）和 `results/a_data_labels/a2_labels/reference_picks_first_batch.csv`。

- 台站：R2 中心 0.6° 内有 HH 或 EH 通道的 CI/AZ 台站共 75 个，按其在 R2 事件上的人工 P 拾取数取前 30 个。
- 事件：M≥3、不在 PhaseNet 时段、在这 30 个台站上至少 8 个人工 P 和 4 个人工 S 的事件共 46 个，按年份轮流抽取 40 个（2020–2026 每年都有），震级 3.01–4.34。
- 参考拾取：这 40 个事件在 30 个台站上共 2,115 个拾取，其中人工 1,862 个（P 883、S 979）。
- 波形：SCEDC FDSN dataselect，发震时刻前 120 s 至后 240 s，HH、EH、HN 通道，所有位置码；SCEDC 的批量（POST）请求返回无数据，改为每个事件一次普通查询。
- 波形抽查（`results/a_data_labels/a2_labels/waveform_check/coverage.csv`）：40 个事件全部下载（336 MB），每个事件 26–30 个台站有数据，人工拾取全部落在有数据的时段内。5 个事件（40183482、40184058、41458472、41459168、41459312）有遥测缺数，每处最长约 5–8 s，分布在多个台站；拾取环节要能处理缺数。
- 通道：30 个台站中 12 个是短周期台，只有 EHZ，水平向只有加速度计 HNE/HNN。分析员在这些台站上 P 拾在 EHZ，S 拾在 HNE/HNN（人工 S 中 319 个在 HN 上）；另有 22 个人工拾取在未下载的 BH 通道上。PASC 有 00、10 两套位置码。

## b 基线流水线

| 结果 | 内容 | 来源 |
|---|---|---|
| 流水线打通（b1，第一批 40 个 R2 事件） | 三种拾取都走完全流程，40 个事件全部定位。对目录的震中偏移中位数：B8 分析员拾取 0.43 km、B1 PhaseNet 0.50 km、B0 STA/LTA + AIC 0.45 km；深度差中位数 +0.36 / +0.22 / +0.45 km；发震时刻差中位数 −0.005 / +0.02 / +0.01 s；RMS 中位数均约 0.18–0.19 s。B8 复现目录位置到约 0.4 km，说明定位器、模型和台站表基本无误 | `results/b_baseline/b1_pipeline/<B0,B1,B8>/5_location/locations.csv`、`overview.png` |
| 流水线中修正的问题 | ① 网络触发：只用“5 台”门槛时噪声台站让窗口平均提前约 30 s，改为取重合计数的峰；② ObsPy `ar_pick` 对同一输入重复调用约 8% 返回 S = 0，改为水平分量 STA/LTA + AIC；③ 关联要求 S 时 B0 有 13 个事件关联不上，改为不要求 S；④ 零相位滤波在 M4 事件上使 STA/LTA 提前约 1 s 触发、AIC 拾早（P 平均绝对误差 0.076 s，约 180 个 P 早 0.4–3 s），检测、精修、网络触发和画图全部改为因果滤波后 P 平均绝对误差降到 0.026 s | `docs/design.md` 5.1 |
| 台站通道 | 按 40 个事件统计，24 个台站主要用 HH，6 个只有 EHZ 加加速度计；不少台站在 2020–2026 年间从短周期升级为宽频带；LUC2 有 10 个事件、PEM 有 7 个事件没有数据 | `results/b_baseline/b1_pipeline/B0/2_channels/` |
| 拾取评分（b2，对 manual 拾取；匹配容差 P ±0.5 s、S ±1.0 s；括号内为事件 bootstrap 95% 区间见 `scorecard.csv`） | P：B0 召回 0.91、精确 0.99、平均绝对误差 0.026 s、0.1 s 内 0.95；B1 召回 0.89、精确 0.99、0.043 s、0.89。S：B0 召回 0.73、精确 0.98、0.109 s、0.1 s 内 0.68；B1 召回 0.67、精确 0.99、0.115 s、0.64。相对 B8 定位的震中偏移中位数 B0 0.32 km、B1 0.36 km | `results/b_baseline/b2_scoring/` |
| 由此得到的判断 | 在第一批 M≥3、高信噪比的事件上，正确实现的经典方法与同域 PhaseNet 持平，P 的计时更准；两者的主要不足都在 S（召回 0.67–0.73，缓起 S 的 0.1 s 内比例约 0.6）。这批事件太容易，区分不出方法：Q1–Q3 的学习和对比需要更难的事件（M2–3、低信噪比、缓起、事件重叠）和 OOD 场景 | 同上 |
| SCSN 定位用的一维模型 | Hutton et al. 2010（BSSA 100(2)）：1932–2008 目录除 Long Beach 序列外都用 Hadley–Kanamori 模型定位，表 5 给出 SCSN 版本（层顶 0/5.5/16/32 km，Vp 5.5/6.3/6.7/7.8 km/s，Vp/Vs 1.73）；文中说该模型适合 Mojave 沙漠和 Transverse Ranges，在深盆地（Imperial Valley、洛杉矶盆地、Ventura 盆地）近似很差，并计划改用三维模型。2010 年以后的日常定位模型未核实 | https://authors.library.caltech.edu/records/bkpgd-rab65 （已读原文 PDF 第 8 页） |

## c 预实验（调研阶段的初步结果）

| 结果 | 数字 | 来源 |
|---|---|---|
| 留一残差对单个拾取误差的检出率（模拟：20 台、残余模型误差 0.1 s、误报 5%） | 0.1 s 约 1%，0.3 s 约 15%，1 s 约 96%；7 台时 1 s 约 33% | `brain_storm/deep_research/03_residuals_as_pick_feedback.md`；`brain_storm/deep_research/scripts/03_residual_detectability/detect_sim2_out.txt` |
