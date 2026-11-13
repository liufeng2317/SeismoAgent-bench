# 04. 深度学习拾取器在哪里失效

## 要回答的问题

- PhaseNet、EQTransformer、GPD、PhaseNO 等在换区域、换仪器、换震源类型时的泛化和域迁移基准（Münchmeyer et al. 2022 JGR "Which picker fits my data?"；SeisBench 系列论文；Jiang et al.；Park et al.；PickBlue 等 OBS 拾取器；迁移学习论文）。尽量给出退化的量（recall、残差标准差）。
- 有证据的具体失效场景：密集余震序列、事件重叠和主震尾波（Ridgecrest、Kaikoura、2023 土耳其）；海底地震仪（OBS）；井下台；火山事件（长周期、颤动、混合型）；深源和中源俯冲板片事件以及区域震相（Pn/Pg/Sn/Sg 混淆）；低信噪比和缓起震相；强震动或限幅记录；不同采样率和仪器响应；诱发地震；DAS。
- 这些场景里，哪些已知是人工分析员仍然做得更好的，或者在业务上仍然需要分析员的？
- 哪些场景有公开数据和分析员标签，可以真正拿来测试？

决定：进阶 baseline 和高难 baseline 放在哪里，才能显出 agent 的价值。

## 结论摘要

- **同一距离范围内跨区域迁移，退化是"轻度"的；真正失效的是换距离范围、换频带、换传感器平台。** Münchmeyer et al. 2022 在 8 个数据集上做了 336 组交叉评估：区域到区域迁移只有轻度下降，但大残差拾取（>0.45 s）的比例在跨域时普遍升高，"常常高达 10%"；区域模型用到远震数据完全失效（检测 AUC < 0.75，域内为 0.85–0.99）[1]。中国 Yangbi/Maduo 序列上，PhaseNet 和 EQTransformer 的 recall 比原论文报告低 13%–56% [2]。
- **失效最严重、证据最硬的三个场景是：火山长周期事件、海底地震仪、远震或区域震相。** 原版 PhaseNet 在火山 LP 事件上 P 的 F1 从约 0.9 降到约 0.6，S 从约 0.85 降到约 0.35，recall 最低到 P 0.3、S 0.2；重训后 LP 的 F1 提高 0.42（P）和 0.16（S）[3]。陆地训练的 PhaseNet 在 OBS 上的 P 中位绝对偏差是 OBS 专用模型的 5–11 倍，EQTransformer 是 3–7 倍 [4]；OBSTransformer 在 >200 km 处把 P、S recall 分别提高 68% 和 76% [5]。
- **"PhaseNet 在日本表现差"需要分台网看。** Naoi et al. 2024 用 JMA 一元化人工检测值重训 PhaseNet：原版"在日本常规数据上表现欠佳，尤其是海底台"，但对 Hi-net 陆上台的提升"有限"，对 S-net 和 DONET 的提升"显著"；原版相对 JMA 检测值系统性偏晚 [6][7]。也就是说，日本陆上地壳地震未必是 PhaseNet 的失效区，海底台、低频地震和火山区才是。
- **高发生率和事件重叠是公认弱点，但缺少系统的定量基准。** 箱根火山的研究发现，一个检测窗内有多个事件时，小振幅信号常被漏掉，用"一窗两震"的合成数据重训后才找回来 [8]；土耳其双震后的研究直接说早期余震目录"高度不完整且不准确"，原因是余震率高和波形重叠 [9]；Park et al. 2023 指出神经拾取器对输入窗口的微小平移不稳定，会损害目录完整性 [10]。Ridgecrest 和 Kaikoura 上没有找到"PhaseNet 对分析员、按重叠程度分层"的定量研究（未找到）。
- **人工分析员确实更好的场景很窄。** 最新的直接对比（2016 意大利中部序列，52 万条人工复核拾取）发现 PhaseNet 拾取让定位和层析更好、更自洽，95% 的差值在 ±0.5 s 内；但 DL 漏掉了约 4% 的人工拾取（主要是 M<2、低信噪比、短记录），且对 Visso M5.9 主震的解比人工差（RMS 0.39/0.67 s 对 0.20 s）[11]。分析员在业务上仍不可少：SCSN 把 PhaseNet 加进后处理后拾取数增加 2–3 倍，但流程仍以分析员复核收尾 [12]。区域 Pn 震相上，有研究称 DL 仍落后于人类专家 [13]（只读摘要）。
- **跨机构的系统偏差本身就是一个"失效"来源。** 不同机构的拾取习惯不同：NEIC 训练的模型用到 GEOFON 上系统性偏早，反之偏晚 [1]；原版 PhaseNet 相对 JMA 和意大利 BSI 都偏晚 [6][11]。agent 若以某一机构的分析员拾取为真值，必须先估计并扣除这类常数偏差，否则"更准"可能只是"更像这家机构"。
- **有公开分析员标签、可以直接测的场景：** 火山（SeisBench 的 VCSEIS，含 AVO、HVO、NCSN、JMA 的分析员拾取）[3][14]、OBS（SeisBench 的 OBS/PickBlue 数据集，约 9 万条 P、6.3 万条 S 人工拾取）[4][14]、密集余震（Ridgecrest SCEDC；2016 意大利中部 BSI；AQ2009 L'Aquila 余震）[11][14]、区域震相（CREW）[13][14]、诱发地震（piSDL、TXED）[15][14]、太平洋西北含"异类"事件（PNW、PNWExotic）[14]。DAS 和 OBST2024 的标签是自动或半自动生成的，不能当真值 [5][14]。

## 详细发现

### 1. 泛化和域迁移基准

**Münchmeyer et al. 2022（JGR，SeisBench 基准）[1]，已读原文。**

- 6 个模型（BasicPhaseAE、CRED、DPP、EQTransformer、GPD、PhaseNet）、8 个数据集（ETHZ、INSTANCE、Iquique、LenDB、SCEDC、STEAD、GEOFON、NEIC），加经典的 Baer-Kradolfer 拾取器。
- 域内：EQTransformer、GPD、PhaseNet 最好，彼此接近；区域数据集上 P 的 MAE EQTransformer 比 GPD/PhaseNet 低 0.01–0.04 s。三个最佳模型的平均 P MAE：STEAD 0.08 s、ETHZ 0.12 s、SCEDC 0.14 s、Iquique 0.21 s、INSTANCE 0.26 s；远震 GEOFON 0.57 s、NEIC 0.74 s。S 的平均 MAE 比 P 差 25%–60%。
- 远震残差大的原因：缓起、低频、信噪比差（这是设计稿中引用"大残差主要来自低信噪比和缓起"的出处，但原文说的是远震数据集，不是区域数据）。
- 跨域：同一距离范围内跨区域"通常比域内差，但可用"；所有模型在跨域时大残差（>0.45 s/1.5 s）比例上升，"常常高达 10%"，即使 STEAD、INSTANCE 这种跨域表现好的也是如此。作者推测原因是不同数据集的标注习惯不同（有的会漏掉较弱的早到震相，有的没剔除重叠事件）。
- 机构偏差：NEIC 训练的模型用到 GEOFON 上 P 系统性偏早，反之偏晚，说明两家机构判断标准不同。
- 区域到远震：没有一个区域训练的模型在 GEOFON 上检测 AUC 超过 0.75（域内 0.85–0.99）。把 100 Hz 模型当作 20/40 Hz 用（等于把频带下移）可以部分补救，P MAE 降到 0.90–1.01 s，但 >1.5 s 残差比例仍超过 20%–30%。
- 经典拾取器：信噪比好时，调好的 Baer-Kradolfer 与 DL 相当；信噪比差时 DL 明显更好，Baer-Kradolfer 离群值多且偏晚。
- 训练集多样性比规模更重要：INSTANCE 训练的模型跨域最好。

**Jiang et al. 2021（Earthquake Science）[2]，只读摘要。** 2021 年云南漾濞和青海玛多序列上，PhaseNet 的 recall 高于 EQTransformer，但两者的 recall 都比原论文报告值低 13%–56%；作者认为训练时应加入噪声样本。

**Park et al. 2023（SRL）[10]，只读摘要。** 神经拾取器存在"预测不一致"：输入波形做很小的扰动（如滑动窗口的起点不同），结果会显著改变，进而降低目录完整性；用小步长滑动窗口并汇总结果可以显著缓解。后续工作改用训练时平移和抗混叠滤波（Park, Delbridge & Shelly 2024）、Dice loss（Park & Beroza 2025）[只读摘要，未打开原文]。

**Pita-Sllim 等（The Seismic Record 2023，作者待核）[16]，只读摘要。** 用新西兰 Alpine 断层 13 个台站近 9 年、8.5 万多条人工拾取评估 EQTransformer：概率输出与拾取精度相关性有限；有反射或折射震相时首至波更难拾取；参数选择影响很大。会议摘要中 92% 的 EQTransformer 拾取与人工相差 0.25 s 以内。

**PhaseNet 原论文 [17]，已读原文。** 在 NCEDC 测试集上，不同仪器类型（宽频、短周期、加速度计 HN*、井下短周期 DP* 等）表现稳健，作者认为模型学到了共同特征。注意这是域内（同一台网）测试，不是跨域证据。

### 2. 具体失效场景

#### 2.1 密集余震、事件重叠和主震尾波

| 证据 | 内容 | 来源 |
|---|---|---|
| 箱根火山（Kim et al. 2023） | 区域重训模型远好于原版；但一个检测窗内有多个事件时，小振幅信号常被漏掉；构造"一窗两震"训练数据重训后找回 | [8] 只读摘要 |
| 土耳其 2023 双震 AutoQuake 研究 | 早期余震目录"高度不完整且不准确"，原因是余震率高和重叠波形造成的高背景振幅；模板匹配已被证明能显著提高早期完整性 | [9] 只读摘要，作者待核 |
| 土耳其 2023（Becker et al.，SRL） | PhaseNet + GENIE 关联的目录可靠定位事件数多于 AFAD 常规目录和 PhaseNet + GaMMA 目录，约为 AFAD 的 5 倍 | [18] 只读摘要，作者顺序待核 |
| Ridgecrest 合成测试（GaMMA 相关补充材料） | 每分钟 30 个事件的高度重叠合成数据上，PhaseNet 难以准确拾取 | [19] 只读检索片段，原文未打开 |
| PhaseNet 原论文图 | 8 个事件间隔 6 s 叠加，PhaseNet 仍能分开拾取（演示性例子，非统计） | [17] 已读原文 |
| 2016 意大利中部（Cianetti et al. 2026） | 连续波形 1 天内 DL 流程找到 5,315 个事件，约为 BSI 的 4 倍，召回 99% BSI 事件；但 Visso M5.9 主震的 DL 解差于人工 | [11] 已读原文（前半部分） |
| 2021 玛多 | DL 检测可能漏掉低信噪比事件并产生误检，是早期目录不完整的原因之一 | [20] 只读检索片段 |

要点：(1) 对 M≥2.5 的事件（本项目关心的），重叠的主要后果是**漏拾小事件的震相、把邻近事件的震相错配**，而不是对孤立大信号拾错。(2) 主震本身也可能是难点（限幅、宽频带、破裂持续时间长），Visso 一例说明 DL 对大事件不一定比人工好。(3) 未找到 Ridgecrest 或 Kaikoura 上按"距主震时间"或"重叠程度"分层、PhaseNet 对分析员的定量统计。Kaikoura 相关研究未找到。

#### 2.2 海底地震仪（OBS）

- PickBlue（Bornstein et al. 2024）[4]，已读原文主要部分：15 个 OBS 部署、13,190 个事件、355 台站，约 9 万条 P、6.3 万条 S 人工拾取。PickBlue 的中位绝对偏差 P 0.05 s、S 0.12 s，S 约为 P 的两倍。陆地训练的 PhaseNet，P 的偏差是带水听器 OBS 模型的 5–11 倍；陆地 EQTransformer 为 3–7 倍；陆地 PhaseNet 偏晚，陆地 EQTransformer 偏早。OBS 难的原因：水柱混响、船舶和海洋生物噪声、自由下落造成的倾斜噪声和未知水平向方位（影响基于偏振的 S 拾取）、水平分量噪声大使 S 信噪比低、S 与 P 尾波和基底/Moho 转换波重叠。
- OBSTransformer（Niksejel & Zhang 2024）[5]，只读摘要：陆地模型用到 OBS"性能显著下降"；迁移学习后 >200 km 处 P、S recall 分别提高 68% 和 76%。其训练标签由 4 个 ML 拾取器加 AIC 的一致性自动生成，不是人工拾取。
- 日本 S-net、DONET：Naoi et al. 2024 指出原版 PhaseNet 在海底台上表现尤其差，重训提升显著 [6][7]。

#### 2.3 井下台

- 未找到针对"井下台本身"作为变量的 DL 拾取器评估。PhaseNet 原论文的 NCEDC 测试集含 DP*（井下极短周期）类台站，表现与其他类型相近 [17]。
- 日本 Hi-net 是井下高灵敏度台网（训练知识，[待核]），而 Naoi et al. 2024 发现原版 PhaseNet 在 Hi-net 上重训提升有限 [6][7]。推断：井下台的低噪声反而有利，井下本身不是主要失效因素；可能的问题是井下记录的上下行波干涉和与地表台不同的频率特征（推断，无文献）。
- 微地震井中阵列（压裂监测）有迁移学习研究，但那是勘探尺度，与本项目无关 [21]。

#### 2.4 火山事件

- Zhong & Tan 2024（GRL）[3]，已读原文：汇编阿拉斯加、夏威夷、日本、北加州、喀斯喀特的火山事件，标签来自分析员。原版 PhaseNet 和 EQTransformer 的 precision、recall、F1 随频率指数下降而系统性下降：PhaseNet P 的 F1 从约 0.9 降到约 0.6，S 从约 0.85 降到约 0.35；recall 下降更多，最低 P 0.3、S 0.2。作者说明这种下降不是信噪比差异造成的。重训后 LP 的 F1 为 P 0.90、S 0.86，比原版 EQTransformer 高 0.42 和 0.16；VT 上的提升只有 0.11 和 0.05。在未参与训练的喀斯喀特火山上，原版模型对 LP 的 F1 只有 0.37–0.61，重训模型为 0.71–0.76。在日本南海槽构造低频地震上，重训模型比原版高 0.22–0.49（P）和 0.08–0.31（S），F1 约 0.8。重训 EQTransformer 的残差 2σ：LP 为 P 0.38 s、S 0.46 s；VT 为 0.21 s、0.32 s。
- Lapins et al. 2021（JGR）[22]，只读摘要：Nabro 火山上用约 2,500 条波形迁移学习 GPD，小样本时明显优于从头训练，检测数多于人工目录。
- 箱根（Kim et al. 2023）[8]：火山区重训模型远好于原版。
- 颤动（tremor）：未找到"对颤动拾取 P/S 到时"的 DL 评估；颤动本身通常没有清晰的 P/S 起始，一般用包络相关或分类方法处理，不属于拾取问题（推断）。
- 混合型事件（hybrid）：未找到单独评估。

#### 2.5 深源/中源板片事件和区域震相

- Aguilar Suarez & Beroza 2025（Seismica）[13]，只读摘要：现有 ML 拾取器"主要针对近震记录"；他们在 CREW（160 万条波形、320 万个标注到时）上训练了能在 20° 内拾取首至 P/S、并区分 Pn/Pg/Sn/Sg 的模型，并与近震训练的模型对比（具体数字未读到）。
- 2025 年 Sensors 上关于区域 Pn 拾取的论文称，DL 方法"往往落后于人类专家，尤其在较大震中距（如 Pn，约 200–2000 km）"[23]，只读检索片段。
- 汤加深源地震（PhaseNet-TF，GJI 2024）[24]：OBS 加陆地台记录深源地震，作者开发时频域拾取器，称比 PhaseNet 的 S 拾取好得多，目录事件数是人工目录的 10 倍以上。只读摘要，没有找到"原版 PhaseNet 在深源事件上失败多少"的数字。
- 未找到专门量化中源/深源事件上 P/S 误标或 S 拾取退化的研究（未找到）。推断：对本项目（近震网络、地壳事件为主）影响有限；但在日本东北和关东，中源板片事件很多，台站-事件距离和入射角与训练数据差别大，值得在日本 baseline 中单独分层。

#### 2.6 低信噪比和缓起震相

- Münchmeyer et al. 2022：远震数据中缓起、低频、低信噪比是大残差的主因；区域数据中，信噪比差时 DL 比经典方法好 [1]。
- Zhong & Tan 2024：低频（缓起）比低信噪比更能解释火山 LP 上的失败 [3]。
- Cianetti et al. 2026：DL 漏掉的约 4% 人工拾取中，1.4% 归因于低信噪比，1% 是人工质量最差的 Q4 拾取，1.5% 是记录太短 [11]。
- Ross et al. 2018（极性 CNN）：低信噪比时网络倾向于不给结论，recall 下降而 precision 基本不变 [25]（详见方向 06）。
- 试点：agent 在缓起 P 上比 PhaseNet 准约 2 倍，在清晰起始上持平（试点报告，非文献）。

#### 2.7 强震动和限幅记录

- PhaseNet 原论文在加速度计（HN*）上表现与速度计相近 [17]（域内）。
- GPD 原论文称对"非常大的地震"这种训练集中很少的情况仍然稳健 [26]，只读摘要。
- Cianetti et al. 2026：Visso M5.9 的 DL 解 RMS 0.39/0.67 s，人工 0.20 s [11]，原因原文未在已读部分说明。
- 针对限幅（clipping）记录的 DL 拾取评估：未找到。

#### 2.8 采样率和仪器响应

- 模型只认样点位置，不认物理时间：把 100 Hz 训练的模型用到 20/40 Hz 数据上等于把频带下移，这在远震上反而有帮助 [1]。推断：反过来，若输入未重采样到模型的采样率，频带会错位。SeisBench 在 annotate 时会重采样到模型采样率（训练知识，[待核]）。
- 极性分类：250 Hz 数据比 100 Hz 数据准几个百分点（Hara et al. 2019）[27]。
- 仪器响应作为单独变量的评估：未找到。

#### 2.9 诱发地震

- Heuel et al. 2025（Seismica，piSDL）[15]，已读原文前部：已发表的 PhaseNet 模型用到诱发地震数据上"只检测到少数事件"，已训练的 PhaseNet"无法超过成熟的常规流程"；用 17 万条诱发地震波形加本地噪声重训后，在法国 Rittershoffen 地热场比机构目录多检测出最多 62% 的事件。诱发数据的特点是震源距短、信噪比低、事件小；负信噪比常来自落在前一个事件尾波中的震相。
- 本项目只做天然地震，诱发地震可作为参考，不建议作为 baseline。

#### 2.10 DAS

- PhaseNet-DAS（Zhu et al. 2023）[28]，只读摘要：常规地震数据上优化的模型"难以处理 DAS 数据"，原因是超密空间采样、未知耦合、高噪声和缺少人工标签；交通信号与地震信号相似，导致原版 PhaseNet 大量误检。他们用 PhaseNet 加 GaMMA 生成伪标签训练 PhaseNet-DAS。
- DAS 没有分析员标签，也不符合"单道看图的分析员"设定，不建议纳入。

### 3. 分析员在哪里仍然更好或业务上仍被需要

| 场景 | 证据 | 结论强度 |
|---|---|---|
| 大事件（主震） | Visso M5.9：人工 RMS 0.20 s，DL 0.39/0.67 s [11] | 单例 |
| 小事件、低信噪比、短记录 | DL 漏掉约 4% 人工拾取，主要是 M<2 [11] | 中 |
| 区域 Pn 等远距离震相 | DL 落后于人类专家（摘要表述）[23] | 弱（只读摘要） |
| 火山 LP、OBS、诱发 | 原版模型 recall 很低；重训后才可用 [3][4][15] | 强，但对比对象是重训模型，不是分析员 |
| 业务复核 | SCSN 加入 PhaseNet 后处理后，拾取数增加 2–3 倍、精度略好于 STA/LTA，流程仍以分析员复核结束；ST-Proc 在 65–70% 含事件的触发中正确检测到事件，误报约 5% [12] | 强 |
| 反例：DL 比人工更自洽 | 2016 意大利中部：DL 拾取使相对定位误差约减半，层析 RMS 降约 15% [11]；Ross 2018 和 PhaseNet 论文都展示了分析员拾错的例子 [17][25] | 强 |

要点：在常规台网、地壳地震、中等信噪比这个"主战场"上，最新证据是 DL 拾取已经不比人工差，甚至更自洽 [11]。分析员（以及 agent）的价值更可能体现在：(a) 原版模型的域外数据；(b) 大事件和重叠；(c) 质量判断（何时不给拾取、何时降权）和对整个事件的一致性检查。

### 4. 公开数据和分析员标签（可直接测）

SeisBench 当前收录的数据集（从源码 `seisbench/data/__init__.py` 和各数据集文件的文档字符串核实）[14]：

| 场景 | 数据集 | 标签来源 | 适合做真值？ |
|---|---|---|---|
| 火山 VT/LP | VCSEIS（Zhong & Tan 2024：阿拉斯加、夏威夷、北加州、喀斯喀特；论文中还含日本）| 分析员 [3] | 是 |
| OBS | OBS（PickBlue，Bornstein et al.）| 人工 [4] | 是 |
| OBS | OBST2024（Niksejel & Zhang）| 多拾取器一致性自动标注 [5] | 否 |
| 密集余震 | AQ2009（L'Aquila 2009 余震，INGV）| [待核] | 待核 |
| 密集余震 | 2016 意大利中部 BSI（INGV，非 SeisBench）| 人工复核 [11] | 是 |
| 密集余震 | Ridgecrest（SCEDC，本地已有）| 分析员（07-04 至 07-06 复核率 ≥97%，见设计稿）| 是 |
| 区域震相 | CREW（Aguilar Suarez & Beroza）| [待核：可能来自目录到时] | 待核 |
| 诱发 | piSDL；TXED（Texas）| piSDL 部分人工 [15]；TXED [待核] | 部分 |
| 异类事件、加速度计 | PNW、PNWExotic、PNWAccelerometers（Ni et al. 2023）| PNSN 分析员 [待核] | 是（待核） |
| 台湾 | CWA（CWASN 和 TSMIP）| [待核] | 待核 |
| 加州统一 | CEED（Zhu et al. 2025）| NCEDC/SCEDC 分析员 | 是 |
| DAS | MLSubDAS | 半自动，文档警告标注不完整 | 否 |
| 远震深度震相 | ISC_EHB_DepthPhases | ISC-EHB | 与本项目无关 |
| 日本 | JMA 一元化检测值（非 SeisBench，见方向 05）| JMA 人工 | 是，获取方式见方向 05 |

本地仓库旁边还有 2018 Kīlauea 的 benchmark 目录（git status 中可见 `benchmark_source/2018_kilauea_hawaii/`，当前工作树中不存在），可能可以复用夏威夷火山数据（推断，需向负责人确认）。

## 对本项目的影响

**1. 进阶 baseline（Ridgecrest）应按"重叠程度"分层，而不是只按日期。**
- 对 T1（2019-07-04 至 07-06）的每个拾取，用 QTM 或 Ross 2019 模板匹配目录计算"前后 ±30 s 内是否有其他事件"和"距主震时间"，分成孤立 / 轻度重叠 / 严重重叠三层，分别报告 agent 与 PhaseNet 的误差和 recall。只有这样才能检验"agent 在重叠上更好"这个说法；目前没有任何文献给出 Ridgecrest 上按重叠分层的 DL 对分析员统计，这本身就是贡献点。
- 加入 PhaseNet 小步长滑动窗口汇总（Park et al. 2023 的做法）作为增强 baseline，避免 agent 的优势只是来自对 PhaseNet 默认设置不稳定性的修补 [10]。
- 主震和 M≥5 事件单独列出（Visso 例子提示 DL 可能更差 [11]）。

**2. 高难 baseline 不要笼统地放"日本"，要放在日本的已知失效子场景，并且必须带日本本地训练的模型。**
- 证据表明原版 PhaseNet 在 Hi-net 陆上台的劣势有限 [6][7]；如果高难 baseline 是 Hi-net 地壳地震，agent 相对 PhaseNet 的优势可能不大，而相对 Naoi 的 JMA 重训模型很可能没有优势。
- 推荐的日本子场景（按证据强弱）：S-net/DONET 海底台 [6]；低频地震 [3][6]；火山区（V-net 或 JMA 火山台）[3][8]；中源板片事件（推断，无直接证据，作为探索层）。
- 对照组必须包含 Naoi et al. 2024 的 JMA 重训 PhaseNet 和 PhaseNetWC [6]（方向 05 核实可获取性）；否则"PhaseNet 在日本失效"是稻草人。

**3. 准备一个公开、可复现的"失效区"备选：火山（VCSEIS / 夏威夷）。**
- 理由：失效证据最硬（原版 recall 最低 0.3/0.2）[3]；分析员标签公开；有重训模型可作强 baseline；与"天然地震"的项目范围一致；缓起震相正是试点中 agent 优势最大的地方。
- 风险：LP 事件的"真值"本身更不确定（分析员对缓起起始分歧大）；需要按频率指数分层报告，并检查 agent 是否只在 VT 上有效。
- OBS（PickBlue 数据集）是第二备选，但其 S 拾取需要水平向方位，agent 的 R/T 旋转工具在方位未知时失效 [4]。

**4. 评估时显式处理机构偏差。**
- 每个 baseline 先估计 PhaseNet 和 agent 相对该机构分析员的中位偏差，同时报告"原始误差"和"扣除常数偏差后的离散度（MAD）"。原版 PhaseNet 相对 JMA 和 BSI 都偏晚 [6][11]，NEIC 对 GEOFON 有系统差 [1]；不处理的话，agent 在日本的"优势"可能只是它没有 NCEDC 训练带来的偏晚。

**5. 不建议作为 baseline 的场景：** 远震（超出单台近震分析员设定）；DAS（无分析员标签）[28]；诱发（项目范围外，可作附录）[15]；OBST2024、MLSubDAS（标签是自动生成的）[5][14]。

**6. 要加的对照：** 每个失效场景都放"原版模型 / 域内重训模型 / agent / agent+重训模型初值"四组。如果 agent 只赢原版、输给重训模型，结论应写成"agent 是在没有本地训练数据时的替代方案"，而不是"agent 优于深度学习"。

## 未解决与待核

- Ridgecrest、Kaikoura 早期余震中 PhaseNet 对分析员、按重叠程度分层的定量研究：未找到。可自己在 T1 上做。
- 土耳其 AutoQuake 论文和 Becker et al. 的作者、期刊、具体数字未能打开（ResearchGate 403），需核对。
- Naoi et al. 2024 的 Hi-net/S-net/DONET 具体 precision-recall 数值和偏晚的毫秒数：只读到摘要和日文研究集会摘要，Springer 页面无法访问；方向 05 应读全文。
- Aguilar Suarez & Beroza 2025 中原版 PhaseNet/EQTransformer 在区域距离上的数值：未读到。
- Cianetti et al. 2026 中 Visso 主震 DL 解变差的原因（限幅？尾波？台站数？）：原文后半部分未读。
- AQ2009、CREW、TXED、PNW、CWA 的标签是否为人工复核：需逐个读数据集论文。
- SeisBench 在 annotate 时是否自动重采样：查文档确认（readthedocs 本次无法访问）。
- PhaseNO 在本项目各场景上的表现：本次未检索到专门的域迁移评估。
- 本轮 WebSearch 额度在后期用尽，Kaikoura、限幅记录、井下台、Shelly 相对极性等条目未能进一步检索，标为"未找到"的项中有一部分是"未检索充分"，下一轮可补。
- 需要问负责人：`benchmark_source/2018_kilauea_hawaii/` 的数据是否可用，是否含 HVO 分析员拾取。

## 参考文献

1. Münchmeyer, J., et al.（完整作者列表待核）(2022). Which picker fits my data? A quantitative evaluation of deep learning based seismic pickers. JGR Solid Earth, 127, e2021JB023499. https://doi.org/10.1029/2021JB023499 ；arXiv:2110.13671 [已读原文]
2. Jiang, C., Fang, L., Fan, L., Li, B. (2021). Comparison of the earthquake detection abilities of PhaseNet and EQTransformer with the Yangbi and Maduo earthquakes. Earthquake Science, 34(5), 425–435. [只读摘要]
3. Zhong, Y., Tan, Y. J. (2024). Deep-learning-based phase picking for volcano-tectonic and long-period earthquakes. GRL, 51, e2024GL108438. https://doi.org/10.1029/2024GL108438 [已读原文]
4. Bornstein, T., et al.（完整作者列表待核）(2024). PickBlue: Seismic phase picking for ocean bottom seismometers with deep learning. Earth and Space Science. https://doi.org/10.1029/2023EA003332 ；arXiv:2304.06635 [已读原文（ar5iv 版主要部分）]
5. Niksejel, A., Zhang, M. (2024). OBSTransformer: a deep-learning seismic phase picker for OBS data using automated labelling and transfer learning. GJI, ggae049. https://doi.org/10.1093/gji/ggae049 [只读摘要]
6. Naoi, M., Tamaribuchi, K., Shimojo, K., Katoh, S., Ohyanagi, S. (2024). Neural phase picker trained on the Japan Meteorological Agency unified earthquake catalog. Earth, Planets and Space. https://doi.org/10.1186/s40623-024-02091-8 [只读摘要]
7. 直井誠・溜渕功史・大柳修慧・加藤慎也 (2023). 一元化震源データを利用した深層学習検測器の再学習の試み. 東京大学地震研究所共同利用研究集会 2023 要旨. https://wwweic.eri.u-tokyo.ac.jp/viewdoc/SOKUJI-yosoku/download/2023/2023_16_naoi.pdf [已读原文]
8. Kim, A., Nakamura, Y., Yukutake, Y., Uematsu, H., Abe, Y. (2023). Development of a high-performance seismic phase picker using deep learning in the Hakone volcanic area. Earth, Planets and Space. https://doi.org/10.1186/s40623-023-01840-5 [只读摘要]
9. （作者待核）Performance of AI-based phase picking and event association methods after the large 2023 Mw 7.8 and 7.6 Türkiye doublet. https://www.researchgate.net/publication/380991253 [只读检索片段，未打开原文]
10. Park, Y., Beroza, G. C., Ellsworth, W. L. (2023). A mitigation strategy for the prediction inconsistency of neural phase pickers. SRL. https://doi.org/10.1785/0220230003 [只读摘要]
11. Cianetti, S., Lomax, A., Michelini, A., Giunchi, C. (2026). Which is better: deep-learning or manual seismic arrival-time picking? GJI, 244(3), ggaf494. https://doi.org/10.1093/gji/ggaf494 [已读原文（前 10 万字符）]
12. Tepp, G., Yu, E., Bhaskaran, A., Tam, R., Zhu, W., Newman, Z., Jaski, E., Scheckel, N. (2025). Improvements from incorporating machine learning algorithms into near real-time operational post-processing. Scientific Reports. https://doi.org/10.1038/s41598-025-14491-1 [只读摘要]
13. Aguilar Suarez, A. L., Beroza, G. C. (2025). Picking regional seismic phase arrival times with deep learning. Seismica, 4(1). https://doi.org/10.26443/seismica.v4i1.1431 [只读摘要]
14. SeisBench 源码，`seisbench/data/__init__.py` 及各数据集文件（main 分支，2026-11-13 读取）. https://github.com/seisbench/seisbench [已读原文]
15. Heuel, J., Maurer, V., Frietsch, M., Rietbrock, A. (2025). Picking induced seismicity with deep learning (piSDL). Seismica, 4(2). https://doi.org/10.26443/seismica.v4i2.1579 [已读原文（前部）]
16. （作者待核，含 Pita-Sllim, O. D.）(2023). Parametric testing of EQTransformer's performance against a high-quality, manually picked catalog for reliable and accurate seismic phase picking. The Seismic Record. https://doaj.org/article/80cd39d2e84a46588c5474543949723e [只读摘要]
17. Zhu, W., Beroza, G. C. (2019). PhaseNet: a deep-neural-network-based seismic arrival-time picking method. GJI（卷页待核）；arXiv:1803.03211 [已读原文]
18. Becker, D., McBrearty, I. W., Beroza, G. C., Martínez-Garzón, P.（作者顺序待核）. 2023 Kahramanmaraş 余震 ML 目录（PhaseNet + GENIE / GaMMA）. SRL. [只读检索片段，未打开原文]
19. Zhu, W., et al.（作者、年份、期刊待核）. Earthquake phase association using a Bayesian Gaussian mixture model. arXiv:2109.09008（Ridgecrest 重叠波形补充测试）[只读检索片段]
20. Enhancing completeness and forecasting of early post-mainshock sequences: A case study of the 2021 Qinghai Maduo MS7.4 earthquake. https://pmc.ncbi.nlm.nih.gov/articles/PMC13378022/ [只读检索片段，作者未核]
21. Abdullin, A. 等 (2025). MicroPhaseNO: adapting an earthquake-trained phase neural operator for microseismic monitoring. arXiv:2512.13197 [只读摘要]
22. Lapins, S., et al.（完整作者列表待核）(2021). A little data goes a long way: automating seismic phase arrival picking at Nabro volcano with transfer learning. JGR Solid Earth. https://doi.org/10.1029/2021JB021910 [只读摘要]
23. （作者未核）(2025). Test-time augmentations and quality controls for improving regional seismic phase picking. Sensors. https://pmc.ncbi.nlm.nih.gov/articles/PMC12693796/ [只读检索片段]
24. Xi, Z. 等（作者待核）(2024). Deep learning for deep earthquakes: insights from OBS observations of the Tonga subduction zone. GJI. https://obsicpublications.whoi.edu/content/deep-learning-deep-earthquakes-insights-obs-observations-tonga-subduction-zone [只读摘要]
25. Ross, Z. E., Meier, M.-A., Hauksson, E. (2018). P wave arrival picking and first-motion polarity determination with deep learning. JGR Solid Earth. https://doi.org/10.1029/2017JB015251 ；arXiv:1804.08804 [已读原文]
26. Ross, Z. E., Meier, M.-A., Hauksson, E., Heaton, T. H. (2018). Generalized seismic phase detection with deep learning. BSSA. https://doi.org/10.1785/0120180080 [只读摘要]
27. Hara, S., Fukahata, Y., Iio, Y. (2019). P-wave first-motion polarity determination of waveform data in western Japan using deep learning. Earth, Planets and Space, 71, 127. https://doi.org/10.1186/s40623-019-1111-x [只读摘要]
28. Zhu, W., Biondi, E., Li, J., Yin, J., Ross, Z. E., Zhan, Z. (2023). Seismic arrival-time picking on distributed acoustic sensing data using semi-supervised learning. Nature Communications. https://doi.org/10.1038/s41467-023-43355-3 [只读摘要]
