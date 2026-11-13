# 02. 拾取的标签噪声

## 要回答的问题

- 分析员之间、同一分析员前后两次的 P、S 拾取差多少（按起始类型 impulsive/emergent 和 SNR 分）？查 Zeiler & Velasco 2009（BSSA）、Freedman 1966、Douglas et al.、Leonard 2000、Diehl et al. 2009/2012、Käslin et al. 2018 及更新的研究；以及 ML 与分析员的残差分布（Ross et al. 2018 σ≈0.023 s 的说法；Zhu & Beroza 2019；Mousavi 2020；Münchmeyer 2022）。
- 地震 ML 数据集中的标签错误（设计稿引用的 arXiv 2511.09805，核实）及其规模。
- 半合成拾取基准：有没有人把同一台站同一通道的真实事件前噪声叠加到高 SNR 记录上、扫描 SNR，用已知起始时间测拾取精度？合成起始和数据增强式的评估也算。设计稿说这是新做法，是否属实？
- 低于什么样的"标签噪声底线"只能说"与分析员更一致"，不能说"更准确"？

影响的决定："更准确"和"与分析员更一致"的分界；半合成测试集怎么做。

## 结论摘要

- **Ross et al. 2018 的 σ=0.023 s 是"条件很好"的一致性数字，不是标签噪声。** 原文：CNN 只看以分析员拾取为中心、随机平移 ±0.5 s 的 4 s 窗口（1–20 Hz 因果滤波，只用 P、只用垂直分量），计算均值和标准差前用 outer fence 剔除了极端离群值；同一测试集 75% 的拾取在 0.028 s 内，90 百分位绝对差 0.074 s，SNR<5 时误差迅速增大 [1]。作者自己写"For records with low SNR, the network still mimics the human analysts' behavior"[1]——这正是"一致"而非"准确"。
- **ML 与分析员的一致性大致在 0.03–0.08 s（P）和 0.08–0.11 s（S）**：PhaseNet 在 NCEDC 测试集上 P σ=51.5 ms、S σ=82.9 ms（只统计 |Δt|<0.5 s）[2]；EQTransformer 在 STEAD 测试集上 P σ=0.03 s、S σ=0.11 s，与 JMA 人工拾取比 σ≈0.08 s、MAE≈0.06 s [3]；Münchmeyer et al. 2022 三个最好模型的平均 P MAE：STEAD 0.08 s、ETHZ 0.12 s、SCEDC 0.14 s、Iquique 0.21 s、INSTANCE 0.26 s，残差近似 Laplace 分布、众数为零，跨数据集应用时 >0.45 s 的离群可达 10% [4]。PhaseNet 训练标签本身用 σ=0.1 s 的高斯表示，作者明说"The arrival-times in the training dataset contain errors and biases"[2]。
- **我们自做的跨机构对比给出了一个可直接用的"分析员间噪声"估计**：同一事件、同一台站上 SCSN 与 NCSN 分析员各自的 manual 拾取（36 个事件、374 对）。P：两边都标 i 的 89 对，|Δt| 中位数 0.01 s、90 百分位 0.04 s、>0.1 s 只有 1%；两边都标 e 的 102 对，|Δt| 中位数 0.05 s、90 百分位 0.30 s、>0.1 s 占 29%、>0.3 s 占 11%。S（66 对）：|Δt| 中位数 0.05 s、90 百分位 0.30 s、>0.1 s 占 32%。onset 判读不一致很常见：308 对 P 中 117 对一边 i 一边 e（§2.3）。样本小、两边是否完全独立未核实。
- **标签错误规模**：Aguilar Suarez & Beroza（arXiv 2511.09805，2025-11-12）用 PhaseNet+EQTransformer 集成检查 8 个数据集 860 万个样本，平均错误率 3.9%（STEAD 0.01% 到 INSTANCE 7.98%，CEED 6.12%）；主要错误是未标注的地震和"噪声"样本中含地震；到时错误只筛查了 >2 s 的情况，作者说"We identified only a few such examples"，**没有给出亚秒级到时误差的统计** [5]。SCEDC 数据集因与 CEED 重复而未单独检查 [5]。设计稿引用属实，但它不能回答亚秒级标签噪声的问题。
- **半合成（真实噪声叠加）不是新做法。** DeepDenoiser（Zhu, Mousavi & Beroza 2019, IEEE TGRS）把 NCEDC 的高 SNR 地震记录与真实噪声记录相加生成不同 SNR 的训练和测试数据；并在一条记录上取**事件前 30 s 同一通道的噪声**，缩放后叠加、扫描 SNR，测 STA/LTA 拾取的时间变化：4 dB 时延迟 0.5 s，更低时拾不到 [6]。EQTransformer 和 SeisBench 的增强是加高斯噪声、插入第二个事件等 [3][4]。**我们没有找到**系统地用同台同通道事件前真实噪声、按 SNR 扫描、比较多种 ML 拾取器（及 LLM）误差的已发表基准（本次检索额度用尽，未能做完整的新颖性检索，见"未解决与待核"）。准确的说法是"把已有的半合成做法系统化为拾取精度基准"，不能说"首创"。
- **建议的"标签噪声底线"按层设定，而不是一个数**：P 两边都标 i 时约 0.01–0.02 s（中位绝对差）/0.04 s（90%）；P 标 e 时约 0.05 s / 0.30 s；S 约 0.05 s / 0.30 s（§2.3）。网络给的名义不确定度更粗：SCSN QuakeML 权重码 0/1/2/3 → 0.03/0.06/0.15/0.30 s；NCSN 文档中分析员设想的主观误差 0.02/0.10/0.20/0.30 s [7][方向 01]。试点"agent P MAE 0.02 s vs PhaseNet 0.04 s"落在 i 层底线附近、远低于 e 层底线，只能写成"与分析员更一致"。
- **一个常被忽略的统计点**：如果标签噪声与被比较的拾取器独立且无偏，MSE 可以分解为"拾取器真实误差方差 + 标签噪声方差"，两个拾取器之间的 MSE 差仍是它们真实精度之差的无偏估计（推断，标准结论）；问题出在标签噪声与某个拾取器**相关**的时候——PhaseNet 在 SCSN/NCSN 标签上训练、SCSN 2023-11 以后的部分标签直接是 PhaseNet 拾取（方向 01）。所以"比 PhaseNet 更准"可以在独立标签上检验，"比分析员更准"则无法用分析员标签检验。

## 详细发现

### 1. 文献中的分析员间 / 分析员内差异

| 文献 | 核实情况 | 能确认的内容 |
|---|---|---|
| Zeiler & Velasco 2009, BSSA 99(5), 2759–2770, "Seismogram Picking Error from Analyst Review (SPEAR): Single-Analyst and Institution Analysis" | 元数据经 Crossref 核实；全文未打开（出版社页面需验证、摘要被屏蔽）[8] | 项目已有笔记（转引 NMSOP-2 第 16 章）称：高 SNR 的本地/区域事件人工 P 误差约 0.1 s、分析员系统性偏晚；不同机构之间差 0.2–0.6 s（1σ），各机构内部自洽 [9]。**此为二手转述，未见原文，待核** |
| Leonard 2000, BSSA 90(6), 1384–1390, "Comparison of Manual and Automatic Onset Time Picking" | 元数据经 Crossref 核实；全文未打开 [10] | 无可确认的数字 |
| Diehl, Kissling, Husen & Aldersons 2009, GJI 176(2), 542–554, "Consistent phase picking for regional tomography models: application to the greater Alpine region" | 元数据核实；OUP 全文被 Cloudflare 拦截 [11] | 项目笔记称该文用"最早/最晚可能起始时间"定义质量等级与不确定区间，并主张区域层析需完全重拾以保证一致性 [9]。具体区间数值**待核** |
| Diehl et al. 2009b（BSSA 99(3)，自动 S 拾取器与 S 质量等级） | 未打开 | 无 |
| Freedman 1966 | **未找到**（未能检索） | 无 |
| Douglas et al.（1997?） | **未找到**；项目笔记只有转引 [9] | 无 |
| Käslin et al. 2018 | **未找到**，无法确认该文献存在 | 无 |
| Diehl et al. 2012 | **未找到** | 无 |

结论：本次没能读到任何一篇直接测量分析员间/分析员内差异的原文。设计稿"分析员之间约 0.1–0.2 s"的出处仍不确定；转述中的"机构间 0.2–0.6 s"可能主要针对区域/远震，与本地 Ml≤3 事件的 i 型 P 不可直接比较（推断）。我们自己的跨机构对比（§2.3）是目前唯一核实过的本地数字。

### 2. ML 与分析员的残差，以及我们的跨机构对比

#### 2.1 ML 与分析员

| 研究 | 数据 | 一致性数字 | 注意事项 |
|---|---|---|---|
| Ross, Meier & Hauksson 2018 [1] | SCSN 2000–2017，273,882 个事件、692 台、≤120 km、4,847,248 个人工 P 拾取；75/25 随机划分记录 | 均值 −3 ms；σ=0.023 s；75% 在 0.028 s 内；90 百分位 0.074 s | 窗口以分析员拾取为中心 ±0.5 s 随机平移；剔除极端离群后算 σ；只有 P；"SNR" 定义为拾取前后 0.5 s 峰值比；SNR<5 误差迅速增大；按记录而非事件划分训练/测试（同一事件的其他台站可能在训练集中） |
| Zhu & Beroza 2019（PhaseNet）[2] | NCEDC，779,514 条同时有 P、S 的三分量记录，按台站分层划分 | P μ=2.1 ms、σ=51.5 ms；S μ=3.3 ms、σ=82.9 ms（|Δt|<0.5 s）；AR 拾取器 P σ=84 ms、S σ=181 ms | |Δt|<0.1 s 才算命中；标签用 σ=0.1 s 高斯 |
| Mousavi et al. 2020（EQTransformer）[3] | STEAD 测试集；日本 Tottori 序列 JMA 人工拾取约 42,000 个 | STEAD：EQT P σ=0.03 s、S σ=0.11 s；PhaseNet P σ=0.08、S σ=0.11；GPD P σ=0.10、S σ=0.14；JMA 对比 σ≈0.08 s、MAE≈0.06 s、均值约 0.01 s | STEAD 测试集来自与训练集同分布的数据 |
| Münchmeyer et al. 2022 [4] | SeisBench 9 个数据集 | 三个最好模型平均 P MAE：STEAD 0.08、ETHZ 0.12、SCEDC 0.14、Iquique 0.21、INSTANCE 0.26 s；残差近似 Laplace、众数为零；跨数据集 >0.45 s 离群可达 10% | INSTANCE MAE 较高可能部分因为"约 15–20 名标注员"导致一致性较低；一个 INSTANCE 例子中标签约晚 0.5 s，所有模型都拾到了真实起始；"the deep learning models are able to learn a more consistent picking than present in the dataset, because they can not reproduce differences between human annotators" |
| Tepp et al. 2025 [12] | SCSN 业务 hypoPN 测试 | 相对最终分析员拾取，PhaseNet 的中位数、均值、标准差都优于 STA/LTA，S 改善更大（数值仅在图中）；**SNR 与时间精度的相关性弱于 phase score 与时间精度的相关性，S 尤其如此**（补充图 S1） | 最终分析员拾取中有原样保留的 PhaseNet 拾取（方向 01） |

要点：
- 这些数字都是"与某个机构的分析员拾取的一致性"，不是相对真值的误差。它们同时包含模型误差、标签噪声以及模型学到的标签偏差（推断）。
- SCEDC 数据集上 MAE 0.14 s 高于 STEAD 0.08 s [4]；方向 01 实测显示 2013 年以后 SCSN 终审拾取中有约 20–55% 是自动拾取，SCEDC 训练/测试标签实际上是"分析员 + 自动拾取器"的混合（推断）。

#### 2.2 网络给出的名义不确定度

| 权重码 | SCSN / NCEDC QuakeML `time/uncertainty`（实测） | SCSN S3 相位文件 quality | NCSN 文档"主观误差"[7] | 典型 onset |
|---|---|---|---|---|
| 0 | 0.03 s | 1.0 | 0.02 s | i |
| 1 | 0.06 s | 0.8（=0.75） | 0.10 s | i |
| 2 | 0.15 s | 0.5 | 0.20 s | e |
| 3 | 0.30 s | 0.2（=0.25） | 0.30 s | e |

这些是分析员选择的类别，不是测量值；QuakeML 的不确定度由权重码查表得到（方向 01 §2.3）。

#### 2.3 我们自做的跨机构对比：SCSN 分析员 vs NCSN 分析员（本文分析）

**方法**：从 NCEDC 月度 Hypoinverse 相位文件（21 个月，2018–2026）中取复核标记为 F、Md≥1.0、位于两网重叠带的事件（Parkfield 一带 35.5–36.3°N、121.0–119.8°W；Coso/Owens/Ridgecrest/Kern 一带 35.0–37.2°N、118.6–116.5°W；第一轮另用 35.0–38.2°N、121.0–116.5°W、Md≥1.5）。对每个事件在 SCEDC 按发震时刻 ±5 s 查找唯一对应事件，分别取两个 FDSN QuakeML，只保留两边都是 `evaluationMode=manual` 的拾取，按（台网、台站、震相）配对，Δt = t_CI − t_NC。两边时间都只到 0.01 s。脚本与结果：`scripts/01_02_analyst_picks/cross_net.py`、`cross_net2.py`，配对数据 `cross_rows.json`（第一轮）、`cross_rows2.json`（第二轮），合并去重后 36 个事件、374 对（M1.3–5.6）。

| 子集 | 对数 | Δt 中位数 | 1.4826×MAD | |Δt| 中位数 | |Δt| 90 百分位 | |Δt|>0.1 s | |Δt|>0.3 s |
|---|---|---|---|---|---|---|---|
| P 全部 | 308 | −0.010 | 0.030 | 0.020 | 0.200 | 18% | 7% |
| P 两边都 i | 89 | 0.000 | 0.015 | 0.010 | 0.040 | 1% | 0% |
| P 两边都 e | 102 | −0.010 | 0.059 | 0.050 | 0.300 | 29% | 11% |
| P i/e 不一致 | 117 | −0.010 | 0.044 | 0.030 | 0.190 | 21% | 9% |
| P 同一通道 | 288 | −0.010 | 0.030 | 0.020 | 0.180 | 16% | 6% |
| S 全部 | 66 | 0.000 | 0.074 | 0.050 | 0.300 | 32% | 11% |
| S 两边都 i | 13 | 0.000 | 0.059 | 0.040 | 0.140 | 38% | 0% |
| S 两边都 e | 28 | +0.005 | 0.126 | 0.080 | 0.300 | 39% | 11% |
| S 同一通道 | 37 | 0.000 | 0.044 | 0.030 | 0.140 | 16% | 3% |

onset 判读（CI, NC）：P 为 (e,e) 102、(i,i) 89、(e,i) 111、(i,e) 6；S 为 (e,e) 28、(i,i) 13、(e,i) 19、(i,e) 6。

解读：
- 对 i 型 P，两个机构的分析员几乎逐样点一致（中位 0.01 s，90% 在 0.04 s 内）。对 e 型 P 和 S，中位差约 0.05 s，但有 10% 左右差 ≥0.3 s 的长尾。整体没有系统偏差（中位数 −0.01 至 0 s）。
- SCSN 分析员明显比 NCSN 更倾向于标 e（111 对 vs 6 对），与方向 01 中两个网络 i 比例的差别一致。onset 标记在机构间不可移植。
- **局限**（全部待核）：(1) 样本小，只有 36 个事件，且集中在两网边界；(2) 未确认两个网络是否交换或导入彼此的拾取——若有，i 型的高度一致可能部分来自复制；(3) 双方都可能在同一套显示/滤波习惯下工作，"两机构一致"不等于"接近真值"；(4) 这是机构间差异，同一分析员前后两次的差异（分析员内）未测；(5) 未按 SNR 分层（没有下载波形）。

### 3. 数据集标签错误

Aguilar Suarez & Beroza, "Pervasive Label Errors in Seismological Machine Learning Datasets", arXiv:2511.09805（2025-11-12）[5]：
- 方法：PhaseNet + EQTransformer 集成，与数据集标签比较；作者承认这些模型本身在含错标签上训练，可能偏向与训练数据一致。
- 规模：8 个数据集（Iquique、ETHZ、PNW、TXED、STEAD、INSTANCE、AQ2009、CEED）约 860 万个样本，平均 3.9%。"未标注地震"一项的比例：Iquique 3.84%、ETHZ 2.58%、PNW 2.15%、TXED 1.49%、STEAD 0.01%、INSTANCE 7.98%、AQ2009 6.92%、CEED 6.12%。"噪声样本含地震"：STEAD 208/235,426（人工复查后去掉 14 个）、INSTANCE 1.92%、PNW 0.87%、TXED <0.01%。
- 到时错误：只把与集成相差 >2 s 的标为可疑，"We identified only a few such examples"，详细分析留待以后。
- 作者另提到（同组在准备中的工作）ML 目录与 ComCat 相比约有 10% 的到时被 ML 模型漏掉。
- SCEDC 数据集未单独检查（与 CEED 重复）。
- 对本项目：该文说明大的标签错误（漏标、错标事件）在加州数据集里以百分之几的量级存在，选参考事件时应检查窗口内是否有未编目事件；但它**不提供**0.01–0.3 s 量级的到时噪声估计。

### 4. 半合成 / 真实噪声叠加的评估

| 工作 | 做法 | 与设计稿 T3 的关系 |
|---|---|---|
| Zhu, Mousavi & Beroza 2019, DeepDenoiser（IEEE TGRS 57(11), 9476–9488）[6] | 训练/测试：NCSN HN* 通道 56,345 条高 SNR 地震记录 + 179,233 条非地震记录，随机相加得到不同 SNR；对比实验：一条 BW.RTSH EHZ 记录，**取事件前 30 s 同一通道噪声，缩放后叠加**，扫描 SNR，测 STA/LTA 拾取时间的变化（4 dB 延迟 0.5 s，更低拾不到；去噪后 2 dB 仍准确） | 核心做法已有先例，但只用于单条记录和 STA/LTA，目标是评估去噪，不是拾取基准 |
| Mousavi et al. 2020（EQTransformer）[3] | 训练增强：加随机水平高斯噪声、插入第二个事件、平移、加间断、去通道 | 用高斯噪声，不是同台真实噪声；不是评估 |
| Münchmeyer et al. 2022 / SeisBench [4] | 训练增强：加高斯噪声（p=0.5）、插入间断、去通道等 | 同上 |
| Ross et al. 2018 [1] | 按实测 SNR 分组报告误差 | 真实 SNR，没有已知真值 |
| Tepp et al. 2025 [12] | 实测 SNR 与时间精度相关性弱 | 提醒：SNR 不是唯一决定拾取难度的变量 |

可能的其他先例（凭记忆的线索，**均未核实**）：Küperkoch et al. 2010（GJI，高阶统计拾取器）和 Sleeman & van Eck 1999 的合成测试；Diehl et al. 2009b 的 S 拾取器测试；用 STEAD 噪声样本做增强或评估的工作。**待做**：补一次正式新颖性检索。

结论：设计稿"没找到用真实噪声做这类基准的已发表工作"需要改写。可以主张的新意是：(a) 用同台同通道、事件前紧邻的真实噪声（保留台站噪声谱和非平稳性）；(b) 已知起始来自高 SNR 原记录，并用多方法一致性确认；(c) 在统一 SNR 网格上比较分析员级 agent、多种 DL 拾取器和经典拾取器；(d) 同时报告 P、S 和极性。

### 5. 半合成测试集的具体隐患（推断，供设计用）

1. **"已知起始"本身有误差。** 高 SNR 原记录上的起始仍有 0.01 s 级不确定（i 型 P 两机构 90% 在 0.04 s 内，§2.3）。建议把"真值"定义为原始高 SNR 记录上的拾取（无论谁拾），评估的是"加噪后能否恢复同一时刻"，这样起始误差抵消，测的是噪声鲁棒性，不是绝对准确性。
2. **信号本身含噪声。** 原记录事件前已有噪声，叠加后的总噪声 = 原噪声 + 缩放噪声；SNR 应按实际总噪声计算。原记录 SNR 需足够高（例如 ≥30 dB）才能让最高档 SNR 有意义。
3. **噪声窗与信号的时间关系。** 用事件前噪声叠加到同一记录上，噪声窗不能与原事件的 P 前噪声重叠（否则噪声相关）；可以取同一通道其他时间段（同一小时、无事件）的噪声，并检查窗口内没有未编目事件 [5]。
4. **S 波难以做干净。** S 起始叠在 P 尾波上；加噪只改变环境噪声，不改变 P 尾波，因此 S 的半合成难度与真实低 SNR S 不同。
5. **方向 01 发现**：2013 年以后 SCSN"i、质量 1.0"的拾取多数是自动拾取，选样不要依赖这两个标记。
6. **SNR 定义要统一**：Ross 2018 用拾取前后 0.5 s 峰值比 [1]；DeepDenoiser 用 10 log10 的能量比 [6]；建议用滤波后（如 1–20 Hz）拾取前后固定窗的 RMS 比，并报告所用定义。

## 对本项目的影响

1. **"更准确"与"更一致"的分界（建议写进论文方法）**：
   - 以分析员拾取为参考的指标一律称"与分析员的一致性"（agreement），按层报告：P-i、P-e、S，以及 manual / automatic 参考（方向 01）。
   - 每层给出标签噪声带：P-i 中位 0.01 s / 90% 0.04 s；P-e 中位 0.05 s / 90% 0.30 s；S 中位 0.05 s / 90% 0.30 s（来自本文跨机构对比，待扩大样本后更新）。两个方法的 MAE 差小于该层的中位标签差时，只说"无法区分"；在噪声带以内的改进只说"更一致"。
   - "更准确"只能来自：(a) T3 半合成（恢复已知起始的能力）；(b) 不依赖人工标签的物理一致性（定位残差、Wadati 线性、互相关差分走时，见方向 03）。
   - "比 PhaseNet 更好"可以在与 PhaseNet 独立的参考上做（SCSN 2012 年以前、或只用 manual 拾取、或 NCSN），并用 MSE 分解报告；绝不用含 PhaseNet 拾取的参考。
2. **立刻可做的复核**：把 Advikar 试点的 0.02 s vs 0.04 s 按 P-i / P-e 和 manual / automatic 拆开重算（**待做**）。若差异集中在 automatic 参考或 i 层，就属于噪声带以内。
3. **扩大跨机构对比作为正式的"分析员噪声"测量（待做）**：把重叠带事件扩大到几百个，下载波形，按 SNR 分层；同时检查两网是否交换拾取。可再加一个分析员内实验：请 1–2 位有经验的分析员盲重拾 100–200 个拾取（含原本 i 和 e），一周后再拾一次，得到分析员内差异。
4. **T3 构建建议**：
   - 母本：SCSN 2012 年以前或 NCSN 非 Geysers 终审事件中，manual、权重码 0/1、原始 SNR≥30 dB 的 P（S 单独、谨慎处理）。
   - "真值"：母本拾取；另用 AIC / 互相关在原记录上复核，三者相差 >0.02 s 的剔除。
   - 噪声：同台同通道、无事件的真实噪声段（同一小时内、与母本不重叠），按 −5 到 20 dB 扫描，每档多个噪声实现。
   - 对照：加高斯色噪声（与真实噪声同谱）的版本，检验"真实噪声"是否带来不同结论。
   - 指标：每档 SNR 的偏差、MAE、离群率（>0.1 s、>0.3 s）、漏拾率；agent 与 PhaseNet/EQT/GPD/AIC 同表。
5. **标签错误检查**：选参考事件时用两个以上 DL 拾取器检查窗口内是否有未编目事件，有则剔除或单独标记 [5]。

## 未解决与待核

- **检索不完整**：本方向的 WebSearch 额度在调研早期用尽，只能抓取已知 URL。Zeiler & Velasco 2009、Leonard 2000、Diehl 2009a/b 的正文都没读到（出版社拦截），Freedman 1966、Douglas et al.、Käslin et al. 2018、Diehl et al. 2012 未找到。**待做**：后续会话补搜，或请用户提供 PDF（Zeiler & Velasco 2009 最关键）。NMSOP-2 第 16 章 PDF（GFZ）返回 403。
- **待做**：系统的新颖性检索——"real noise"、"pre-event noise"、"noise injection"、"SNR sweep"、"phase picking robustness" 等关键词，2019–2026。
- 跨机构对比的独立性：SCSN 与 NCSN 是否在 AQMS 层面交换拾取（问 SCSN/NCSN 数据中心）。
- Tepp et al. 2025 图 3、补充图 S1 的具体数值。
- 设计稿中"分析员之间约 0.1–0.2 s"的出处仍不明，建议改为引用本文跨机构对比并标明样本量。

## 参考文献

1. Ross, Z. E., Meier, M.-A., Hauksson, E. (2018). P wave arrival picking and first-motion polarity determination with deep learning. JGR Solid Earth 123(6), 5120–5129. https://doi.org/10.1029/2017JB015251 ；arXiv:1804.08804 [已读原文（arXiv 版）]
2. Zhu, W., Beroza, G. C. (2019). PhaseNet: a deep-neural-network-based seismic arrival-time picking method. GJI 216(1), 261–273（卷期页码凭记忆，Crossref 未返回，待核）. https://doi.org/10.1093/gji/ggy423 ；arXiv:1803.03211 [已读原文（arXiv 版）]
3. Mousavi, S. M., Ellsworth, W. L., Zhu, W., Chuang, L. Y., Beroza, G. C. (2020). Earthquake transformer—an attentive deep-learning model for simultaneous earthquake detection and phase picking. Nature Communications 11, 3952. https://doi.org/10.1038/s41467-020-17591-w [已读原文]
4. Münchmeyer, J., Woollam, J., Rietbrock, A., Tilmann, F., Lange, D., Bornstein, T., et al. (2022). Which picker fits my data? A quantitative evaluation of deep learning based seismic pickers. JGR Solid Earth 127(1), e2021JB023499. https://doi.org/10.1029/2021JB023499 ；arXiv:2110.13671 [已读原文（arXiv 版）]
5. Aguilar Suarez, A. L., Beroza, G. C. (2025). Pervasive label errors in seismological machine learning datasets. arXiv:2511.09805. https://arxiv.org/abs/2511.09805 [已读原文（HTML 版）]
6. Zhu, W., Mousavi, S. M., Beroza, G. C. (2019). Seismic signal denoising and decomposition using deep neural networks. IEEE TGRS 57(11), 9476–9488. https://doi.org/10.1109/TGRS.2019.2926772 ；arXiv:1811.02695 [已读原文（arXiv 版）]
7. NCSN / NCEDC. Hypoinverse-2000 archive ("shadow") format, shadow2000.pdf（表 9 权重码与主观误差）. https://www.ncedc.org/pub/doc/ncsn/shadow2000.pdf [已读原文]
8. Zeiler, C., Velasco, A. A. (2009). Seismogram picking error from analyst review (SPEAR): single-analyst and institution analysis. BSSA 99(5), 2759–2770. https://doi.org/10.1785/0120080131 [未打开原文；元数据经 Crossref 核实]
9. 项目内部笔记：/liufeng1afs/project/03_LLM/Science_Discovery_Agenet/SeismoAgentBench/docs/research/reference/seismology_qc/data_and_picking.md（P1–P4 行，转引 NMSOP-2 第 16 章）[已读原文；为二手转述]
10. Leonard, M. (2000). Comparison of manual and automatic onset time picking. BSSA 90(6), 1384–1390. https://doi.org/10.1785/0120000026 [未打开原文；元数据经 Crossref 核实]
11. Diehl, T., Kissling, E., Husen, S., Aldersons, F. (2009). Consistent phase picking for regional tomography models: application to the greater Alpine region. GJI 176(2), 542–554. https://doi.org/10.1111/j.1365-246X.2008.03985.x [未打开原文；元数据经 Crossref 核实]
12. Tepp, G., Yu, E., Bhaskaran, A., Tam, R., Zhu, W., Newman, Z., Jaski, E., Scheckel, N. (2025). Improvements from incorporating machine learning algorithms into near real-time operational post-processing. Scientific Reports 15, 28938. https://doi.org/10.1038/s41598-025-14491-1 [已读原文]
13. SCEDC 与 NCEDC FDSN event 服务（QuakeML 拾取，本文跨机构对比的数据源）. https://service.scedc.caltech.edu/fdsnws/event/1/query ；https://service.ncedc.org/fdsnws/event/1/query ；NCEDC 月度相位文件 `s3://ncedc-pds/event_phases/` [已读原文，实测]
