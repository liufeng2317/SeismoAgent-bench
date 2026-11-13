# 06. 极性和 S 波拾取

## 要回答的问题

- 初动极性机器学习模型的现状：Ross et al. 2018（BSSA）极性 CNN、Uchide 2020（日本）、Hara et al.、DiTingMotion（2023）、PolarCAP、Zhao et al.、SeisPolarity（核实它是什么）、Cheng et al. 2023 SCSN 震源机制；按起始类型报告的、相对分析员的精度。分析员的极性错误率。极性质量如何影响震源机制（HASH、SKHASH）。
- S 波拾取：为什么难；各方法及其实测增益：旋转到 R/T、偏振滤波（Ross & Ben-Zion 2014；Diehl et al. 2009 S 拾取）、Wadati 图一致性、多台站方法；机器学习 S 拾取相对分析员的表现。
- agent 应该有哪些 S 拾取和极性工具（优先开源 Python），极性基线用哪个。

决定：agent 工具箱补哪些工具；极性基线选谁。

## 结论摘要

- **极性 CNN 在"已知分析员 P 到时"的条件下，与分析员一致率约 95%–99%，这已经碰到分析员标签本身的噪声上限。** Ross et al. 2018：precision 上为 97%、下为 93%，recall 约 80%，另外给出了分析员没给的 27% 极性 [1]；Hara et al. 2019：97.9%（250 Hz）/ 95.4%（100 Hz），跨区域差约 2% [2]；DiTingMotion：约 97.8% [3]；CFM：97.4% / 96.3% [4]；RPNet：保留集 recall 99% [5]。而 Hardebeck & Shearer 2002 用相似事件簇估计 SCSN 分析员极性的不一致率：**清晰起始约 10%，缓起约 20%** [6]。所以试点的"与分析员约 95% 一致"已接近可测上限，用分析员标签无法再证明 agent 更好。
- **最大的误差来源是 P 到时不准和缓起，而不是分类器本身。** DiTingMotion 在 Ridgecrest：用人工 P 到时时准确率 89.9%（上）/ 89.0%（下），用 PhaseNet（Liu et al. 2020）的到时降到 71.3% / 74.6%，人为加 ±0.05 s 扰动时为 81.8% / 80.3% [3]；缓起数据上约 83%–85.6% [3]。RPNet 训练时加 ±0.5 s 随机平移，在日本 Hi-net 上到时偏差 ±0.4 s 时 recall 仍 >97.5% [5]。agent 的极性质量会直接受它自己 P 拾取的影响。
- **极性质量对震源机制的影响是"可容忍但有门槛"的。** HASH 默认允许约 10% 的极性错误；合成测试中加入 10% 极性错误和 1 km 深度扰动后，A/B 级解中 60% 在真解 20° 内、80% 在 30° 内 [6]。Ross 2018 用 CNN 极性使高质量解数量几乎翻倍、错配极性更少 [1]；Cheng et al. 2023 用同一 CNN 加 S/P 振幅比，南加州目录多出 40% 的解，并且与波形矩张量更一致 [7]。
- **"Ross et al. 2018 (BSSA) 极性 CNN"出处有误：** 极性 CNN 发表在 JGR Solid Earth（doi:10.1029/2017JB015251）[1]；同年 BSSA 那篇是 GPD 震相检测 [8]。DiTingMotion 发表在 Frontiers in Earth Science 2023，作者 Zhao 等——用户列表里的"Zhao et al."很可能就是 DiTingMotion 本身 [3]。
- **SeisPolarity 是一个 2025 年 10 月建立的个人开源项目（GitHub Chuan1937，PyPI `seispolarity` 0.1.4，BSD-3），统一封装 7 个极性模型（Ross、EQPolarity、DiTingMotion、CFM、RPNet、PolarCAP、APP）和 5 个数据集，没有论文、没有基准数字，11 颗星** [9]。可以用来快速调用权重，但不应把它作为"极性基线"的出处；基线应引用原模型论文，并自己核对权重是否与原版一致。
- **S 波拾取比 P 难，DL 和经典方法都如此。** PhaseNet：S 的残差标准差 83 ms 对 P 的 52 ms，F1 0.80 对 0.90 [10]；Münchmeyer et al. 2022：S 的平均 MAE 比 P 差 25%–60% [11]；PickBlue（OBS）：S 中位偏差约为 P 的两倍 [12]。原因：S 不是首至波，起始埋在 P 尾波里，还有 S-P 转换波等干扰 [10][12]。
- **经典 S 工具的实测增益：** Ross et al. 2016（偏振滤波去掉 P 能量 + STA/LTA + 峰度）在 ANZA 台网对 11,353 条人工 S 拾取，75% 在 0.16 s 以内，有 P 拾取时 92% 能拾到 S [13]；Diehl et al. 2009 结合三种方法（STA/LTA、偏振检测、AR-AIC），精度与参考拾取相当、给出不确定度，阿尔卑斯 552 个事件得到约 2500 个误差上限 0.27 s 的 S 震相 [14]。**单独"旋转到 R/T"带来多少增益，没有找到定量研究**（未找到）。Wadati 检查是常规做法，PyLoT 有现成实现，但"Vp/Vs 1.6–1.9"这个报警范围没有权威出处 [15]。
- **工具建议：** 极性主基线用 Ross et al. 2018 CNN（SCSN 训练，与 Ridgecrest/南加州同域，是 SCSN 精化机制目录所用的模型 [7]）；日本和跨域用 RPNet 作第二基线（专门针对到时偏差稳健，并在 Hi-net 上测过）[5]；震源机制用 SKHASH（Python，支持带权 ML 极性、互相关一致极性和 S/P 比，并报告逐台错配和台站极性反转）[16]。S 拾取工具：ObsPy 旋转和偏振分析、偏振滤波、AR-AIC，加 Wadati 和"定位后 S 残差"检查。

## 详细发现

### 1. 初动极性机器学习模型

| 模型 | 出处 | 训练数据 | 报告的精度（相对分析员） | 评估条件 | 阅读状态 |
|---|---|---|---|---|---|
| Ross CNN | Ross, Meier & Hauksson 2018, JGR [1] | SCSN，约 250 万条有 U/D 的记录 | precision 上 0.97、下 0.93；recall 0.80/0.81；SNR>10 时 precision 约 98%，SNR>10 时 recall 约 87%；另有 236,237 条（约 27%）分析员未给的极性 | 在分析员 P 到时处截窗；三类输出（上/下/未知），不确定时倾向输出"未知" | 已读原文 |
| Hara et al. | Hara, Fukahata & Iio 2019, EPS [2] | 日本山阴、近畿北部，约 13 万条 250 Hz 和 4 万条 100 Hz | 97.9%（250 Hz）、95.4%（100 Hz）；跨区域差约 2%；训练样本少于 1 万时明显变差 | 假设分析员 P 到时已知 | 只读摘要 |
| Uchide | Uchide 2020, GJI [17] | 先用全日本中强震训练，再用两个区域的微震重训 | 摘要未给极性精度；置信度阈值按震源机制整体质量来选；约 11 万个浅源微震的机制 | — | 只读摘要 |
| DiTingMotion | Zhao, Xiao, Zhang, Yang, Tang, Chen 2023, Front. Earth Sci. [3] | DiTing（中国，64 万条）和 SCSN-FMP（约 484 万条） | 两个测试集约 97.3%–97.9%；缓起约 83%–85.6%；Ridgecrest：人工到时 89.9%/89.0%，PhaseNet 到时 71.3%/74.6%，±0.05 s 扰动 81.8%/80.3% | 测试时强制二选一（上/下） | 已读原文（全文摘录） |
| CFM | Messuti et al. 2023, Front. Earth Sci. [4] | 14 万多条，火山和构造区（意大利） | 两个独立测试集 97.4%、96.3%；能纠正 92% 的错标波形 | — | 只读摘要 |
| PolarCAP | Chakraborty et al. 2022, AI in Geosciences [18] | INSTANCE，13 万多条 | 约 3.3 万条未见测试集上准确率 0.98 | — | 只读摘要（作者列表各来源不一致，待核） |
| EQPolarity | Chen 等（年份待核）[19] | 南加州训练，迁移到得州 | 得州数据上原模型 95.43%，迁移后 98.82% | 仅垂直分量 | 只读检索片段 |
| RPNet | Han, Kim & Sheen 2025, SRL [5] | 美国西部和意大利 | 保留集上下 recall 均 99%；日本 Hi-net 上到时偏差 ±0.40 s 时 recall >97.5%；熊本序列机制接近 JMA 人工解，Kagan 角和极性错配优于先前模型 | 训练时 ±0.5 s 随机平移；上下类平衡；Monte Carlo dropout 给不确定度 | 只读摘要 |
| PhaseNet+ | Zhu, Song, Wang, Münchmeyer 2025, arXiv:2506.06939 [20] | 加州 | 上/下与 Ross CNN"相当或更好"；把约 50%–60% 的"未知"重新分为上或下；具体数字只在图里 | 极性取在模型自己的到时处 | 已读原文（HTML，文字部分） |

要点：

- 所有高精度数字都是**在分析员 P 到时处**评估的（Ross、Hara、DiTingMotion 主测试）。只有 DiTingMotion 的 Ridgecrest 测试和 RPNet 的平移测试量化了"到时不准"的影响：用 PhaseNet 到时会掉 15–18 个百分点 [3]，而用平移增强训练的 RPNet 基本不掉 [5]。
- 缓起起始上，DiTingMotion 约 83%–85% [3]；Ross CNN 低信噪比时主要表现为 recall 下降（输出"未知"），precision 基本不变 [1]。
- "比分析员更好"的说法都是间接的：Ross 2018 用"机制错配更少"支持 [1]；Hara 2019 用极性分布图"看起来"支持 [2]；CFM 能纠正 92% 人为错标 [4]。

### 2. 分析员极性错误率

- Hardebeck & Shearer 2002（BSSA，HASH 原论文）[6]，已读原文：在 Northridge 地区相似事件簇中，同一台站对同一簇事件的极性应当相同；校正已知台站极性反转后，**10% 的清晰（impulsive）极性和 20% 的缓起（emergent）极性不一致**，作者把这当作 SCSN 数据的近似极性错误率。
- Ross et al. 2018 引用这一结果，称"人工极性只有约 80%–90% 正确" [1]。
- Yang, Hauksson & Shearer 2012 的南加州机制目录中，极性随机错误比例"一般小于 5%" [21]（只读检索片段，数据集与 2002 年不同）。
- 推断：如果把"10%/20%"当作分析员标签噪声，那么在一个清晰/缓起各半的测试集上，任何方法与分析员的一致率上限约为 85%–90%；试点报告的 92%–95% 说明测试集以清晰起始为主，或者分析员给极性时本身已经做了筛选（只在有把握时给）。这一点需要在评估中按起始类型分层。

### 3. 极性质量对震源机制的影响（HASH / SKHASH）

- HASH 的做法：在极性、射线离源角（由定位和速度模型误差扰动）的预期误差范围内生成一组可接受解，用解的离散程度定质量 A–D；默认允许错配的清晰极性为 10%（或最小错配 + 5%）[6]。
- 稳定性：原文示例中，一个极性翻转就能把解变成完全不同的断层类型（台站少时）；对极性稳定的解仍可能对定位和速度模型不稳定 [6]。
- 合成测试：10% 极性错误 + 1 km 深度误差 + 用 1D 模型近似 3D 结构，A/B 级解（占 40%）中 60% 在真解 20° 内、80% 在 30° 内；平均角差 A 级 18°、B 级 22°、C 级 23°、D 级 28° [6]。
- 增加极性数量的收益大于提高单个极性精度：Ross 2018 CNN 使高质量机制数接近翻倍，错配率 >30% 的事件更少、<10% 的事件接近两倍 [1]；Cheng et al. 2023 多出 40% 的机制，更接近矩张量解 [7]；Skoumal 等用校正和补全（imputed）极性使机制不确定度平均降低约 13°，良好约束的机制数约为 6 倍 [22]（只读检索片段）。
- PhaseNet+ 用于四川威远诱发地震密集台阵：38,518 个事件中由预测极性和 S/P 比算出 20,740 个机制，其中 4,399 个高质量，与已有矩张量解一致 [28]。
- SKHASH（Skoumal, Hardebeck & Shearer 2024, SRL）[16]：Python 版 HASH；可输入带权重的 P 极性（传统、ML、互相关一致或补全）和 S/P 振幅比；报告逐台和整体的极性、S/P 错配，便于发现台站极性反转等元数据问题；PyPI 版本 1.1.5。
- 推断：对 agent 而言，"极性错配"可以像定位残差一样作为物理反馈——某台极性与最佳机制不符，就回去重看该台起始；但单事件内这个信号很弱（台站少时最优解本身会迁就错误极性），更可靠的是跨事件的台站级统计（如某台长期错配，可能是极性反转）。

### 4. S 波拾取

#### 4.1 为什么难

- S 不是首至波，起始从 P 尾波的散射波中出现 [10]。
- OBS 水平分量噪声大；S 与 P 尾波以及基底/Moho 的 Sp 转换波重叠；方位未知时偏振方法难用 [12]。
- 远震/大数据集中 S 只在信噪比好时才被标注，导致 S 统计"看起来"不差，这是选择偏差 [11]。
- 区域距离上 Sn/Sg 混淆（见方向 04）[23]。
- 推断：浅层低速层强烈时 S 在垂直分量上也有能量，转换波 Sp 可能被误当 P 后的"S"；剪切波分裂会使两水平分量起始不同。

#### 4.2 机器学习 S 拾取相对分析员

| 来源 | P | S |
|---|---|---|
| PhaseNet（NCEDC 测试集）[10] | F1 0.896；残差均值 2.1 ms、标准差 51.5 ms | F1 0.801；均值 3.3 ms、标准差 82.9 ms |
| Münchmeyer et al. 2022（区域数据集平均）[11] | — | S 平均 MAE 比 P 差 25%–60%（INSTANCE 例外，S 略好于 P，可能因 P 标签质量较差） |
| PickBlue（OBS）[12] | 中位绝对偏差 0.05 s | 0.12 s |
| Zhong & Tan 2024（火山 LP，原版 PhaseNet）[24] | F1 降到约 0.6 | F1 降到约 0.35，recall 最低 0.2 |
| 试点（SCSN 28 事件，误差中位数）| agent 0.02 s | agent 0.06–0.09 s，落后 EQTransformer（0.05 s），与 PhaseNet（0.07 s）相当 |

PhaseNet 原论文在 S 拾取上相对 AR 拾取器提升最大（F1 0.80 对 0.17）[10]；SCSN 业务中引入 PhaseNet 后，S 拾取数增加最多 [25]。即 DL 的主要贡献是"多拾到 S"，而 S 的计时精度仍比 P 差。

#### 4.3 经典方法和实测增益

- **偏振滤波**：Ross & Ben-Zion 2014（GJI）用偏振分析和相关滤波器去掉 P 能量，再用 STA/LTA 和峰度检测锁定 S 到时，在 Parkfield 和 Hayward 断层数据上验证"表现良好"（摘要无数字）[26]。Ross et al. 2016（BSSA 106: 2013–2022）的改进版在 ANZA 台网一个月数据上，对 11,353 条人工拾取：75% 在 0.16 s 内；有 P 时 92% 能拾到 S；全年数据检出 11,197 个事件，震源位置平均改进 1 km 以上 [13]（只读摘要）。同组 AGU 摘要称 S:P 拾取比提高 650% 以上 [13]。
- **Diehl et al. 2009（BSSA 99(3): 1906–1920，作者 Diehl, Deichmann, Kissling, Husen；不是 Aldersons）**：组合 STA/LTA、偏振检测（Cichowicz 1993 型特征函数）和 AR-AIC 三种方法，由三者的一致性估计时间不确定度和震相识别可靠度；与人工参考拾取相比平均精度相当，但更多拾取被降到低质量档；阿尔卑斯 552 个事件、震中距 ≤150 km，得到约 2500 个误差上限 0.27 s 的 S 震相 [14]。补充材料提到"旋转分量是增强 S 起始的常用做法" [14]。
- **R/T 旋转**：作为预处理被普遍使用 [14]，但没有找到单独量化"旋转前后 S 拾取误差"的研究（未找到）。推断：旋转的收益取决于定位精度和近台入射角；对近震源台站，SH 在 T 分量上与 P 分离更好，但对方位未知的 OBS 不可用。
- **Wadati 图一致性**：S-P 时间对 P 走时应近似为直线，斜率给出 Vp/Vs−1；偏离直线的 S 拾取视为离群。现成实现：PyLoT 的 `wadaticheck` [15]。一个矿震研究的 Vp/Vs 峰值在 1.62–1.63，但很多事件给出不合理的斜率，说明需要对斜率加约束 [15]。设计稿中"1.6–1.9"这个范围没有找到权威出处，应改为由本区域定位结果（VELEST 或重定位目录）给出的 Vp/Vs 及其离散度。
- **多台站方法**：PhaseNO 等多台站模型 [未打开原文，未核实其 S 增益]；从关联到定位的一致性（定位后 S 残差）本身就是一种多台站检查。

### 5. 工具和基线候选

| 用途 | 工具 | 状态 | 说明 |
|---|---|---|---|
| R/T 旋转 | ObsPy `Stream.rotate('NE->RT', back_azimuth=...)` | 成熟 | 训练知识，[待核 API 细节] |
| 偏振分析 | ObsPy `obspy.signal.polarization`（flinn、vidale、pm 等）| 成熟 | 训练知识，[待核] |
| AR-AIC S 拾取 | ObsPy `obspy.signal.trigger.ar_pick`（同时给 P 和 S，S 用水平分量）| 成熟 | 训练知识，[待核] |
| Wadati 检查 | PyLoT `wadaticheck` [15]，或自己写 L1 拟合（几十行）| 可用 | 建议自己写，Vp/Vs 用本区域值 |
| DL S 概率曲线 | SeisBench 的 PhaseNet、EQTransformer、PickBlue 等（`annotate` 输出概率）| 成熟 | 让 agent 看 S 概率曲线作为提示，而不是直接给拾取 |
| 极性 CNN 统一接口 | SeisPolarity（PyPI `seispolarity` 0.1.4）[9] | 早期个人项目 | 7 个模型 + 预训练权重（HuggingFace/ModelScope），无论文无基准 |
| 极性（稳健到时偏差）| RPNet（GitHub jongwon-han/RPNet，MIT）[5] | 已发表，有代码 | 直接输出 SKHASH 输入；v0.1.0 加了 S/P 比；训练模块未发布 |
| 极性 + 拾取一体 | PhaseNet+（AI4EPS/EQNet 中 `phasenet_plus.py`）[20] | 预印本 + 代码 | 极性取在自身到时处 |
| DiTingMotion + 机制流程 | DiTing-FOCALFLOW（GitHub mingzhaochina）[3] | 已发表，有代码 | — |
| 震源机制 | SKHASH（PyPI 1.1.5，code.usgs.gov/esc/SKHASH）[16] | 成熟，USGS | 支持 ML 极性权重、一致极性、S/P 比 |
| 训练/评估数据 | SeisBench `Ross2018JGRFM`（SCSN 极性数据集）[27]；CEED（加州）[27] | 成熟 | 可做极性基线的独立测试 |

SeisBench 主模型列表中没有极性模型（核对源码 `seisbench/models/__init__.py`）[27]；Zenodo 上有一个"First Motion Polarity classification model (SeisBench implementation)"记录（record 18938888）[未打开原文]。

## 对本项目的影响

**1. 极性基线：主用 Ross et al. 2018 CNN，次用 RPNet；DiTingMotion 可选。**
- Ross CNN 与 SCSN/Ridgecrest 同域（SCSN 训练），也是 Cheng et al. 2023 南加州精化机制目录所用的模型 [1][7]，是最自然的"台网级"基线。权重来源优先用原作者或 SCEDC 发布的版本；如通过 SeisPolarity 调用，先在 SeisBench `Ross2018JGRFM` 的一个子集上复现论文的 precision ≈ 0.97/0.93，确认权重一致。
- RPNet 用于日本 baseline 和"到时不准"测试：它是唯一明确在 Hi-net 上做过测试、并专门对到时偏差稳健的模型 [5]。
- 设计稿 B7 中写的"Ross 2018 (BSSA)"应改为 JGR（doi:10.1029/2017JB015251）；"可通过 SeisPolarity 封装调用"应标注为"第三方封装，需核对权重"。

**2. 极性评估必须拆成"计时"和"判读"两部分。**
- 同一组台站上跑四种条件：(a) 分析员 P 到时 + 模型极性；(b) agent 自己的 P 到时 + 模型极性；(c) 分析员 P 到时处截图给 agent 判极性；(d) agent 全流程。DiTingMotion 的结果表明，(a) 和 (b) 之间可能差 15 个百分点以上 [3]。不拆开的话，agent 的极性优势或劣势分不清来自哪一步。
- 按起始类型（分析员 i/e 或权重）分层报告；在清晰起始上，任何方法与分析员的一致率都会接近 95%，没有区分度。

**3. 用分析员标签无法证明 agent 极性更好，需要一个不依赖分析员的指标。**
- 推荐两个"物理"指标：(a) SKHASH 给出的极性错配率和机制质量等级（对同一事件、同一组台站，比较 agent 极性和基线极性得到的机制）[16]；(b) 相似事件簇内同台站极性的一致性（Hardebeck & Shearer 2002 的方法）[6]。在 Ridgecrest 上还可以和 Cheng et al. 2023 的机制目录比 Kagan 角 [7]。
- 这两个指标也可以作为 A-physics 组的反馈信号之一，但单事件内信号弱，适合跨事件的台站级统计。

**4. S 波工具：补"偏振滤波 + R/T 旋转 + AR-AIC 候选 + Wadati/残差检查"，并把它们做成对照。**
- 试点中 S 是 agent 的弱项（落后 EQTransformer），而试点自己的教训"先在两个水平分量上、暂定起点前至少 1 s 的宽窗里检查"与文献一致（S 起始埋在 P 尾波里）[10]。
- 建议工具：
  1. `rotate_rt`：按定位反方位角旋转到 Z/R/T 并作图；
  2. `polarization_filter`：Ross & Ben-Zion 型的去 P 能量滤波后的 S 特征函数图 [13][26]；
  3. `s_candidates`：AR-AIC（ObsPy）和 DL S 概率曲线给出的 2–3 个候选时刻，标在图上；
  4. `wadati_check`：用本区域 Vp/Vs（来自 VELEST 或重定位目录）做 L1 拟合，报告离群台站；
  5. 定位后的 S 残差（已有的定位残差反馈）。
- 做成消融：有/无旋转、有/无偏振滤波、有/无 DL 概率提示，各跑一遍，看 S 误差和 recall 的变化。文献里没有旋转单独的增益数字，这个消融本身有价值。
- Wadati 报警阈值不要写死"1.6–1.9"，改用区域 Vp/Vs 的均值 ± 若干倍离散度。

**5. 对 S 的期望要现实。** S 的分析员标签噪声大于 P（方向 02 应给出具体数字），PhaseNet 的 S 标准差约 83 ms [10]。建议主指标用 S 的 recall 和"0.2 s 内命中率"，而不只看中位误差；同时报告定位后 S 残差的离散度。

## 未解决与待核

- Ross 2018 CNN 原始权重的官方获取方式（SCEDC 还是作者 GitHub）以及 SeisPolarity 中的"Ross (SCSN)"权重是否与原版一致：待核。
- SeisPolarity 中"APP"指哪个模型：README 未给出处，待核。
- Uchide 2020 的极性准确率数字：只读到摘要，未找到。
- PolarCAP 的作者列表（Chakraborty 等 vs Rümpker 等）和 DOI：来源不一致，待核。
- EQPolarity 的发表年份和期刊：待核。
- Yang et al. 2012 "<5%" 极性随机错误的原文语境：未打开原文。
- Skoumal 等 2023（校正和补全极性）原文和 Shelly 等的互相关相对极性方法：本轮 WebSearch 额度用尽，未能检索；对"跨事件极性一致性"这一物理指标很关键，下一轮应补。
- R/T 旋转对 S 拾取精度的单独增益：未找到定量研究。
- PhaseNO 等多台站模型对 S 的增益：未核实。
- 分析员 S 拾取的不确定度（如 Zeiler & Velasco 2009 等）：属方向 02，此处未展开。
- ObsPy 函数名和参数为训练知识，需在环境里实际调用确认。

## 参考文献

1. Ross, Z. E., Meier, M.-A., Hauksson, E. (2018). P wave arrival picking and first-motion polarity determination with deep learning. JGR Solid Earth. https://doi.org/10.1029/2017JB015251 ；arXiv:1804.08804 [已读原文]
2. Hara, S., Fukahata, Y., Iio, Y. (2019). P-wave first-motion polarity determination of waveform data in western Japan using deep learning. Earth, Planets and Space, 71, 127. https://doi.org/10.1186/s40623-019-1111-x [只读摘要]
3. Zhao, M., Xiao, Z., Zhang, M., Yang, Y., Tang, L., Chen, S. (2023). DiTingMotion: A deep-learning first-motion-polarity classifier and its application to focal mechanism inversion. Frontiers in Earth Science. https://doi.org/10.3389/feart.2023.1103914 [已读原文（通过 WebFetch 摘录全文要点）]
4. Messuti, G., Scarpetta, S., Amoroso, O., Napolitano, F., Falanga, M., Capuano, P. (2023). CFM: a convolutional neural network for first-motion polarity classification of seismic records in volcanic and tectonic areas. Frontiers in Earth Science. https://doi.org/10.3389/feart.2023.1223686 [只读摘要]
5. Han, J., Kim, S., Sheen, D.-H. (2025). RPNet: Robust P-wave first-motion polarity determination using deep learning. SRL. https://doi.org/10.1785/0220240384 ；代码 https://github.com/jongwon-han/RPNet [只读摘要 + README]
6. Hardebeck, J. L., Shearer, P. M. (2002). A new method for determining first-motion focal mechanisms. BSSA. https://doi.org/10.1785/0120010200 ；https://igppweb.ucsd.edu/~shearer/mahi/PDF/78SSA02a.pdf [已读原文]
7. Cheng, Y., Hauksson, E., Ben-Zion, Y. (2023). Refined earthquake focal mechanism catalog for southern California derived with deep learning algorithms. JGR Solid Earth, 128, e2022JB025975. https://doi.org/10.1029/2022JB025975 [只读摘要]
8. Ross, Z. E., Meier, M.-A., Hauksson, E., Heaton, T. H. (2018). Generalized seismic phase detection with deep learning. BSSA. https://doi.org/10.1785/0120180080 [只读摘要]
9. SeisPolarity（GitHub Chuan1937/SeisPolarity；PyPI seispolarity 0.1.4，作者 Xingchen He；仓库建于 2025-10-21，最后推送 2026-08-08）. https://github.com/Chuan1937/SeisPolarity [已读原文（README 和 PyPI 元数据）]
10. Zhu, W., Beroza, G. C. (2019). PhaseNet: a deep-neural-network-based seismic arrival-time picking method. GJI；arXiv:1803.03211 [已读原文]
11. Münchmeyer, J., et al. (2022). Which picker fits my data? A quantitative evaluation of deep learning based seismic pickers. JGR Solid Earth. https://doi.org/10.1029/2021JB023499 [已读原文]
12. Bornstein, T., et al. (2024). PickBlue: Seismic phase picking for ocean bottom seismometers with deep learning. Earth and Space Science. https://doi.org/10.1029/2023EA003332 [已读原文（ar5iv 版主要部分）]
13. Ross, Z. E., White, M. C., Vernon, F. L., Ben-Zion, Y. (2016). An improved algorithm for real-time S-wave picking with application to the (augmented) ANZA network in Southern California. BSSA, 106, 2013–2022. https://resolver.caltech.edu/CaltechAUTHORS:20190423-155306054 [只读摘要]
14. Diehl, T., Deichmann, N., Kissling, E., Husen, S. (2009). Automatic S-wave picker for local earthquake tomography. BSSA, 99(3), 1906–1920. https://doi.org/10.1785/0120080019 [只读摘要 + 补充材料检索片段]
15. PyLoT `wadaticheck` 提交记录（Ruhr-Uni Bochum）https://git.geophysik.ruhr-uni-bochum.de/marcel/pylot/commit/aa624c0358661d50459797a59ee04ff3409ee232 ；A Wadati filter for mine-induced seismicity（Penn State）https://pure.psu.edu/en/publications/a-wadati-filter-for-mine-induced-seismicity/ [只读检索片段]
16. Skoumal, R. J., Hardebeck, J. L., Shearer, P. M. (2024). SKHASH: A Python package for computing earthquake focal mechanisms. SRL. https://doi.org/10.1785/0220230329 ；https://code.usgs.gov/esc/SKHASH [只读摘要 + PyPI 说明]
17. Uchide, T. (2020). Focal mechanisms of small earthquakes beneath the Japanese islands based on first-motion polarities picked using deep learning. GJI, 223(3), 1658–1671. https://doi.org/10.1093/gji/ggaa401 [只读摘要]
18. Chakraborty, M., et al.（作者列表待核）(2022). PolarCAP – A deep learning approach for first motion polarity classification of earthquake waveforms. Artificial Intelligence in Geosciences. https://publikationen.ub.uni-frankfurt.de/opus4/files/78286/1-s2.0-S2666544122000247-main.pdf [只读检索片段]
19. Chen, Y. 等（年份、期刊待核）. EQPolarity. https://github.com/chenyk1990/eqpolarity ；PyPI eqpolarity 0.0.0.3 [只读检索片段 + PyPI 元数据]
20. Zhu, W., Song, J., Wang, H., Münchmeyer, J. (2025). Towards end-to-end earthquake monitoring using a multitask deep learning model. arXiv:2506.06939 ；代码 AI4EPS/EQNet `eqnet/models/phasenet_plus.py` [已读原文（HTML 文字部分）]
21. Yang, W., Hauksson, E., Shearer, P. M. (2012). Computing a large refined catalog of focal mechanisms for southern California (1981–2010). BSSA. [只读检索片段]
22. Skoumal, R. J., Hardebeck, J. L., Shelly, D. R.（作者待核）(2023). Using corrected and imputed polarity measurements to improve focal mechanisms in a regional earthquake catalog. JGR Solid Earth. https://www.usgs.gov/publications/using-corrected-and-imputed-polarity-measurements-improve-focal-mechanisms-a-regional [只读检索片段]
23. Aguilar Suarez, A. L., Beroza, G. C. (2025). Picking regional seismic phase arrival times with deep learning. Seismica, 4(1). https://doi.org/10.26443/seismica.v4i1.1431 [只读摘要]
24. Zhong, Y., Tan, Y. J. (2024). Deep-learning-based phase picking for volcano-tectonic and long-period earthquakes. GRL, 51, e2024GL108438. https://doi.org/10.1029/2024GL108438 [已读原文]
25. Tepp, G., Yu, E., Bhaskaran, A., Tam, R., Zhu, W., Newman, Z., Jaski, E., Scheckel, N. (2025). Improvements from incorporating machine learning algorithms into near real-time operational post-processing. Scientific Reports. https://doi.org/10.1038/s41598-025-14491-1 [只读摘要]
26. Ross, Z. E., Ben-Zion, Y. (2014). Automatic picking of direct P, S seismic phases and fault zone head waves. GJI, 199(1), 368–381. https://doi.org/10.1093/gji/ggu267 [只读摘要]
27. SeisBench 源码 `seisbench/models/__init__.py`、`seisbench/data/__init__.py`（main 分支，2026-11-13 读取）. https://github.com/seisbench/seisbench [已读原文]
28. Song, J., Zhu, W., Zi, J., Yang, H., Chu, R. (2025). An enhanced focal mechanism catalog of induced earthquakes in Weiyuan, Sichuan, from dense array data and a multitask deep learning model. The Seismic Record, 5(2), 175–184. https://doi.org/10.1785/0320250004 [已读原文（摘要和引言）]
