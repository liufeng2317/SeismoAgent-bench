# 05. 日本数据和本地拾取器

## 要回答的问题

- 数据获取：NIED MOWLAS 各台网（Hi-net、F-net、KiK-net/K-NET、S-net、DONET、V-net）的连续波形怎么拿（HinetPy、注册、使用条款、非日本研究者能否注册、再分发限制、数据量/请求限制）。JMA 台网和火山观测数据。
- 标签：JMA 一元化目录是否公开到时（検測値 / phase）数据和初动极性？格式、时间范围、拾取方式和复核（自动 vs 人工）、质量标记、JMA 处理流程的已知变化（2016 年 PF 法自动化、2020 年接入 S-net 等）。日本还有哪些带标签的数据集（类 INSTANCE 数据集、Naoi et al.、基于 Hi-net 的 ML 数据集、东北大学目录等）。
- 用日本数据训练的拾取器：Naoi et al. 2024（用 JMA 拾取训练的神经网络拾取器，需核实）、Tokuda/Uchide、Kubo、Mizutani、Shimoda、Hi-net 训练的 PhaseNet/EQT 变体、S-net/OBS 拾取器。它们在日本数据上和原版 PhaseNet/EQT 权重相比如何？
- PhaseNet / EQTransformer（原版权重）在日本表现差的证据：具体差在哪里（Hi-net 井下 100 Hz 短周期、S-net 海底、火山、深部板内、台网几何差的海域地震、2024 能登序列、2011 余震）？量化。如果证据弱或表现其实不错，要明说。
- 速度模型（JMA2001、三维模型），以及适合做测试集的候选序列/时间窗（震群、火山、海域、2024 能登），各自有无标签。

## 结论摘要

- **“PhaseNet 在日本失效”的说法证据不足，需要改写。** 唯一的大样本量化对比（Naoi et al. 2024，2013 年和 2022 年共 222 万条测试波形，以 JMA 人工到时为真值）显示：原版 PhaseNet 在 Hi-net 和大学台网上“相对较好”，主要问题是 (a) 拾取整体比 JMA 晚（P 约 +0.02–0.03 s，S 约 +0.04–0.05 s，按图 7 目读）；(b) 在 JMA 自有台、F-net（宽频带、原始波形、远距离）、DONET 和 S-net（海底）上明显差；(c) S 波比 P 波差。按 p≥0.5 计，原版 P 拾取数只比日本版少 7.0%，S 少 4.0% [1]。EQTransformer 原版在 2000 年鸟取余震（Hi-net 18 台）上与 JMA 人工到时相比 MAE≈0.06 s、标准差≈0.08 s、平均偏差≈0.01 s，检测事件数约为 JMA 的 2 倍（作者自评）[14]。箱根火山震群上，原版 PhaseNet 的 F1 为 P 0.823 / S 0.641，本地训练模型为 0.860 / 0.755，走时残差“几乎无差别”[15]。所以：陆上 Hi-net 地壳地震上原版权重“差一些但能用”；真正差的是海底台、宽频带台、S 波、震群里的重叠事件。
- **日本本地训练的拾取器已经公开，而且已进 SeisBench。** SeisBench 0.11.5 的 PhaseNet 权重列表里有 `jma`、`jma_wc`（Naoi et al. 2024，JMA 2014–2021 年 610 万条波形训练）、`phasenet_sn`（Suzuki et al. 2025 Science，S-net+陆地台训练）和 `volpick`（火山地震）[3][4][17]。PhaseNeXt（Naoi et al. 2026，2002–2023 年 2450 万条波形）权重在 GitHub（GPL-3.0）[2][3]。所以日本 baseline 的对照组**必须**包含 `jma`/`jma_wc`（陆上）和 `phasenet_sn`（S-net），否则“PhaseNet 失效、agent 修复”的结论会被审稿人一句“换成 Naoi 的权重就行”驳倒。
- **JMA 公开到时数据，但标签有三个坑。** (1) 发布有约 1.5–2 年延迟：2024 年 1–12 月数据 2026-10-14 才上线，目前最新是 2024-12 [5]。(2) 自 2016-04 引入 PF 自动处理后，只有超过阈值 Mth（陆上及近岸 1.7，远海增至 3.5，深度 >150 km 更高）的地震才“全面人工复核”（K 级），以下为“简单复核”（k）或“纯自动”（A）[7]。(3) 即使 K 级事件也不全是人工拾取：本文统计 2024-01 文件，K 级事件的 P 初至中 40.3% 带“自动拾取”标记，S 中 31.1%；2013-04（PF 之前）分别为 23.1% 和 17.8% [9]。“人工复核”≠“人工逐条拾取”，自动拾取经分析员接受后保留。
- **JMA 到时数据里实际上没有初动极性。** 格式定义了 N-S/E-W/U-D 三分量的初动方向和振幅字段 [6]，但本文检查 2005-10、2013-04、2024-01 三个月共约 115 万条观测记录，这些字段**全部为空** [9]。机制解文件只给节面解和台数，不给逐台极性 [8]。因此日本不能直接拿 JMA 数据做极性标签；极性评测要另找来源（如 Hara et al. 2019、Uchide 的深度学习极性目录 [待核]）或自己人工标注。
- **波形获取对外国研究者没有明文限制，但禁止再分发。** NIED 注册只要求姓名、单位、邮箱和用途，条款不区分国籍；要求向 NIED 报告成果、在论文中致谢并引用 DOI；“严禁复制和再分发”，波形和震源信息都在禁止之列，派生数据是否可公开条款未写明 [10][11]。Hi-net 服务器每次请求限 ≤60 分钟、通道数×时长 ≤12000 通道·分钟（Hi-net 约 24000 通道时每次只能取约 5 分钟），只保留最近 150 个请求，HinetPy 自动切分 [12]。基准测试只能发布事件列表和下载脚本，不能发布波形。
- **速度模型现成：** JMA 定位 1997-10 至 2020-09 用 JMA2001 走时表；2020-09-01 起陆上台用 JMA2001A，海底台按区域用 JMA2020A/B/C，并有台站校正；走时表、台站表和台站校正表都可从 JMA 下载 [5][7]。
- **最能体现 agent 价值的日本子场景（推断）：** 2024 年 1 月能登序列早期（同一个月 2.8 万个事件，大量重叠波形，M≥1.7 的事件几乎全部 K 级有人工到时）[9]；S-net 海域小震（日本版拾取器也缺高置信训练标签，但同样缺评测标签）[2]；M≥4 的大事件（日本版拾取器随震级增大而变差）[1]；低频地震（LFE，日本版异常率 P≈15%、S≈20%）[1]。

## 详细发现

### 1. 波形数据获取

**台网与可获取范围。** HinetPy 内置的网络代码表列出了可通过 NIED 网站下载连续波形的网络及起始日期（下表来自 HinetPy 源码 `header.py`）[12]：

| 网络 | HinetPy 代码 | 通道数（表中值） | 网站可取起始日期 |
|---|---|---|---|
| NIED Hi-net（井下短周期，100 Hz） | 0101 | 2336 | 2004-04-01 |
| NIED F-net（宽频带） | 0103 | 438 | 2004-04-01 |
| NIED S-net（速度） | 0120 | 450 | 2016-08-15 |
| NIED DONET1 / DONET2（宽频带） | 0402 / 0403 | 132 / 174 | 2016-04-01 |
| NIED N-net（速度） | 0150 | 108 | 2024-07-01 |
| NIED MeSO-net | 0131（2017-04 后）/ 0231 | 900 | 2008-05-16 |
| NIED V-net（各火山，如 010501 十胜岳…010514 雾岛山） | 0105xx | 22–57 / 火山 | 2010-04-01 |
| JMA 台网 | 0301 | 872 | 2004-04-01 |
| JMA 火山观测网（如 030230 箱根山、030243 樱岛等） | 0302xx | 6–66 / 火山 | 2010-12-01 |
| 大学台网（北大、东北大、东大、京大、九大、名大等） | 0201–0209 | 13–316 | 2004-04-01 |
| AIST、GSI、东京都、神奈川温泉地学研究所等 | 0501、0601、07xx | — | 2004-04-01 起 |

- 数据格式为 WIN32，加纯文本通道表；HinetPy 可转 SAC 和 SAC 零极点响应 [12]。
- 所有时间是 JST（UTC+9）[12]。
- Naoi et al. 说明常规观测波形“一般为 100 Hz”，仪器在各机构之间不同 [1]。
- Hi-net 登录页面称网站可取 2004-04-01 以后的数据，更早或更长的数据走另一下载渠道（来自检索摘要）[未打开原文]。这意味着 2000 年鸟取余震这类老序列不能直接用 HinetPy 拿；EQTransformer 论文的鸟取数据是 NIED 研究人员帮忙获取的 [14]。
- K-NET/KiK-net 是强震网，按触发记录事件波形，不是连续数据（训练知识 [待核]）；做拾取基准时应以 Hi-net 为主（KiK-net 井下与 Hi-net 共址）。
- 数据量：一则 JpGU 2022 摘要称 Hi-net 连续波形每月约 600–800 GB [32][只读摘要]。

**请求限制。** HinetPy 源码注释列出 Hi-net 服务器三条限制：单次记录长度 ≤60 min；通道数 × 记录长度 ≤12000 min；只保留最近 150 个请求。以 Hi-net 约 24000 通道计（三分量），单次只能取约 5 分钟，HinetPy 将长请求切成小块再合并 [12]。官方条款页未写速率限制 [10][11]。推断：取一个序列 30 天、100 个台（300 通道）约需 30×24×60/40 ≈ 1080 次请求，可行但慢；全网多年回溯不现实，应按事件窗口取数据。

**注册与条款。**
- 下载波形必须注册个人 ID 和密码；只看图像不需要 [10]。注册信息为姓名、单位、邮箱和用途（检索摘要）[11]。
- 条款中**没有**针对国外用户的限制条款 [11]；注册页也未写资格要求 [10]。现实中大量国外团队使用 Hi-net（如 EQTransformer 论文）[14]。但能否顺利获批未找到书面说明 → 建议尽早用机构邮箱申请（“未找到”明确的资格规则）。
- 必须向 NIED 报告研究成果（寄论文或报告）；论文须致谢数据机构并引用对应 DOI [10][11]。
- “严禁复制和再分发”；条款对数据的定义包括“由其派生的数据”，波形和震源信息都在禁止之列；商业用途需报告 [10][11]。条款没有专门提到 ML 训练或公开派生数据集（如拾取） [11]。推断：发布我们自己的 agent 拾取/重定位结果大概率可以（Suzuki et al. 2025 就把 PhaseNetSN 拾取放到 Zenodo，CC BY 4.0 [17]），但发布 JMA 到时或 NIED 波形片段不行；需邮件向 NIED 确认。
- 这也解释了为什么日本没有 STEAD/INSTANCE 那样公开的波形 ML 数据集：Naoi、Suzuki 等都只公开模型权重，不公开训练波形 [1][2][17]。

### 2. 标签：JMA 一元化目录的到时数据

**发布范围与延迟。** JMA《地震月报（カタログ編）》/Seismological Bulletin of Japan 公开震源、到时、节面解、CMT、烈度、海啸数据 [5]。到时数据按月 zip 下载：1997 年 10–12 月、1998–2024 年各月 [5]。更新历史显示：2024 年 1–12 月数据于 2026-10-14 公开，2023 年 4–12 月于 2025-12-15 公开 [5]——发布延迟约 1.5–2 年。2024-01 的 zip 约 16 MB（解压约 80 MB）[9]。另有台站表、走时表、台站校正表下载 [5]。

**格式（96 字节定长记录）** [6]：
- 每个事件：震源记录 → 注释 → 若干观测记录（行首 `_`）→ 结束记录。
- 观测记录：6 字符台站码、仪器类型（如 `h` = 井下高灵敏度速度计即 Hi-net，`k`/`l` = S-net 海床下/海床上，`r` = 其他 OBS，`w` = 宽频带等）、第一相名和到时（秒 F4.2，即 0.01 s 精度）、第二相名和到时、三分量最大振幅、三分量初动方向和振幅字段、持续时间、第 92 列第一相标记、第 93 列第二相标记、第 96 列权重（0 = 不参与定位）。
- 相名用 I/E 前缀表示脉冲/缓起（IP、EP、ES 等）[7]——这本身是一种“起跳清晰度”标签，可用于分析 agent 在缓起震相上的表现。
- 第 92 列标记含义：大写 = 高可靠，小写 = 低可靠；A–L 为“自动拾取”（A 原始波形、B/C 高通、X/E/F/W 带通、H/I/J 低通等），M–Z 为“人工拾取”（M 原始波形、N 高通 0.5 s、Q 带通 0.1–0.5 s 等）[6]。注意 Naoi et al. 把“大写”统称为“经人工处理的高置信度”[1]，而格式文档区分了“自动-高可靠”和“人工-高可靠”[6]。

**事件分级与 PF 法（2016-04）** [7][2]：
- K = 高精度（人工、仔细检查）；S = 低精度（人工、仔细检查）；k = 中精度（人工，简单复核）；s = 低精度（人工）；A = 中精度（自动）；a = 低精度（自动）；N = 未定/固定；F = 远震。
- 2016-04 起采用 PF 法（Tamaribuchi et al. 2016）自动定位。M > Mth 的事件“全面检查定位和自动震相，并人工拾取”（与 2016-03 前相同）；M ≤ Mth 的事件只“简单检查”，部分人工拾取（k）或不人工拾取（A）。Mth 在陆上及近岸为 1.7，向远海增至 3.5；深度 >150 km 时 Mth 更大；东海地区原先阈值更低，2018-03-22 统一 [7]。
- 2018-03-22 起对南海海槽深部低频地震启用匹配滤波（MF）法，MF 事件一律归入自动类 [7]。
- 2020-09-01 起 JMA 定位纳入 S-net 和 DONET2，并启用新走时表 [7][1]。DONET 每个节点只读一台 [1]。
- Naoi et al. 2026 还发现 2016-04/05（熊本地震后）和 2016-11 下旬（福岛县冲 M7.4 后）有少量处理例外 [2]。

**本文对公开文件的实际统计** [9]（用 JMA 2024-01、2013-04、2005-10 三个月的到时文件，列号按格式文档）：

| 统计项 | 2013-04（PF 前） | 2024-01（含能登） |
|---|---|---|
| 事件数及分级 | K 12515，S 336 | A 19056，K 13393，k 8899，a 2228，s 962，S 298 |
| K 级事件 P 初至：人工 / 自动标记 | 76.9% / 23.1%（n=190034） | 59.7% / 40.3%（n=242948） |
| K 级事件第二相 S：人工 / 自动标记 | 82.2% / 17.8%（n=156336） | 68.9% / 31.1%（n=196503） |
| 初动方向字段非空的观测记录 | 0 / 231559 | 0 / 727347 |

- 2005-10 文件的 194749 条观测记录，初动字段也全部为空。
- 能登区域（36.6–38.0°N，136–138°E）2024-01：共约 2.83 万个事件，其中 K 11268、A 9077、k 6094。M≥3 的 1617 个和 1.7≤M<3 的 9624 个几乎全部为 K/S；M<1.7 的 1.59 万个中 K 只有 161 个，其余为 A/k/a/s。1 月 1 日几乎全部是 K（1201 个）。
- 解读：JMA 公开到时能当“分析员标签”的范围是 M≥Mth 的事件；即使是这些事件，也有 30–40% 的到时是分析员接受的自动拾取，不是人工重拾。用 JMA 到时评测 agent 时，应同时报告“人工标记子集”的结果。

**初动极性。** 格式里有三分量初动方向字段 [6]，但在 2005、2013、2024 的样本月里全部为空 [9]。用户指南说明大地震的节面解由 P 波初动极性求得 [7]，但机制文件只给 P/T/N 轴、节面、得分和台数，不含逐台极性 [8]。结论：**JMA 公开数据不能直接提供台站级极性标签**（我们只抽查了 3 个月，其余月份未查，但三个相隔近 20 年的月份全为空，推断整体如此）。替代来源：Hara et al. 2019 用深度学习判定西日本 P 波初动极性 [22]（未打开原文，训练标签来源待核）；Uchide 的日本小地震极性/机制目录 [待核，因检索额度耗尽未能核实]。

**日本其他带标签数据。**
- 未找到类似 INSTANCE/STEAD 的公开日本波形 ML 数据集；STEAD 本身不含日本数据 [14]。原因见上文再分发禁令。
- Zenodo 上有若干公开拾取/目录：Suzuki et al. 2025 的 PhaseNetSN 拾取（7.5 GB 原始拾取、2.0 GB 已关联拾取）和 2016–2021 东北日本震源目录 [17]；Takahashi et al. 2026 能登临时台网的 46252 个余震重定位目录（2024-04 至 06）[24]；Yang et al. 能登 19 天余震目录（CC BY 4.0，未说明方法）[33]。这些是机器拾取或重定位结果，不是分析员标签。
- 箱根温泉地学研究所有 1995–2021 年约 3 万个事件的人工 P/S 拾取，用于 Kim et al. 2023，未公开 [15]。
- 京都大学“满点（Manten）”台网和 0.1 满点余震台网的人工拾取用于 SegPhase 训练（250 Hz、2–4.5 Hz 检波器），未见公开 [16]。

### 3. 用日本数据训练的拾取器

| 模型 | 训练数据 | 获取方式 | 与原版的对比 |
|---|---|---|---|
| PhaseNet-J / PhaseNetWC-J（Naoi et al. 2024）[1] | JMA 一元化 2014–2021，610 万条三分量波形（K 级大写标记），含 LFE；100 Hz，不滤波 | SeisBench `PhaseNet.from_pretrained("jma")` / `"jma_wc"` [4]；GitHub JMAuniPicker（GPL-3.0）[3] | 全部台网 PR 曲线都优于原版，消除了原版的延迟偏差；台网间差异变小 |
| PhaseNeXt-S / -M（Naoi et al. 2026）[2] | JMA 2002–2012 + 2014–2023，2445 万条（K 2261 万 + k 186 万），只用普通地震 | GitHub（2026-08-28 更新权重；4096 采样点窗口）[3] | 2013 年测试集 PR 优于 PhaseNetWC-J，S 波提升最明显；在 JMA 流程中检出事件约为 JMA 目录的 3.5 倍 |
| PhaseNetSN（Suzuki et al. 2025, Science）[17] | S-net 海底 + 陆地台（JpGU 2024 摘要称 435566 个海底到时 + 287256 个陆地到时）| SeisBench `phasenet_sn` [4]；Zenodo [17] | 新目录检出事件约为以往 6 倍（新闻稿）；与原版的逐条量化对比未找到 |
| SegPhase（Katoh et al. 2025）[16] | 满点台网 250 Hz、Hi-net 100 Hz 等五个区域的人工拾取 | 论文 | 与“在同一数据上训练的 PhaseNet”比，与人工拾取一致率高约 11%，连续数据检出多约 15%；P MAE 0.03 s / RMSE 0.06 s，S 0.06 / 0.10 s。对比对象不是原版权重 |
| 箱根模型（Kim et al. 2023）[15] | 箱根 1999–2020 年约 22 万条波形（200 Hz 降到 100 Hz） | 未见公开 | 见第 4 节 |
| S-net 迁移学习（Uchide, SSA 2025 海报）[18] | 以 Naoi PhaseNet 为初值，用 S-net 数据迁移学习，用加速度计重力分量校正姿态 | 未见公开 | 到时精度高于其他模型，但 OBSTransformer、PickBlue 的检出率更高；无具体数字 |
| PickNet（Wang et al. 2019）[21] | 约 74 万条日本（Hi-net）波形，VGG-16 改型 | [待核] | EQTransformer 论文把它作为比较对象 [14] |
| VolPick（Zhong & Tan 2024）[26] | 火山构造和长周期地震（全球，是否含日本未核） | SeisBench `volpick` [4] | — |

- Naoi 版 PhaseNet 结构与原版完全相同（268443 参数），WC 版 1070899 参数；在两块 A40 上训练约 80 h [1]。
- Naoi 版在 JMA 日常流程（PF 法关联）中，12 月 31 日一天检出 1642 个事件，常规自动流程为 911 个，JMA 目录为 636 个；多出的 1105 个“超额”事件中，人工核查有 871 个是未知的本地小震 [1]。
- 局限（作者自述）：随震级增大性能下降（训练集小震多）；训练集中不存在的新台站性能稍低；LFE 不如普通地震 [1]。PF 法后 S-net 小震没有高置信标签，可能导致对 S-net 小震性能偏低；PhaseNeXt 的 2013 年测试集不含 S-net/DONET2，因此 S-net 上的提升未被评估 [2]。
- “Tokuda”“Mizutani”“Shimoda”“Kubo”名下的拾取器：因检索额度耗尽，未能核实，记为“未找到”。Kubo, Naoi & Kano 2024 是日本 ML 地震学综述 [27]，可能列有更多日本拾取器（未打开原文）。

### 4. 原版 PhaseNet / EQTransformer 在日本表现差的证据

**(a) Naoi et al. 2024：全国、分台网的大样本对比** [1]
- 测试集：2013 年全年（PF 前，全部人工复核，小震多）+ 2022 年 1–9 月；222 万条波形，每条只含一个 JMA P 和一个 S 拾取 [1]。
- 判定：|r| ≤ 0.1 s 且 p ≥ pth 为 TP [1]。
- p≥0.5 时，原版拾取 P 1935241 个、S 1654177 个；日本版 P 2071432 个（+7.0%）、S 1720897 个（+4.0%）[1]。
- 原版相对 JMA 系统性偏晚，所有台网都如此；日本版消除了这一偏差 [1]。按图 7 目读（近似值）：全部数据原版 P 中位残差约 +0.02–0.03 s，S 约 +0.04–0.05 s；F-net P 约 +0.07 s；S-net S 约 +0.08 s。
- PR 曲线（图 8 目读，近似）：P 波在召回约 0.9 时，原版精度约 0.86，日本版约 0.93–0.95；S 波在召回约 0.78 时，原版精度约 0.73，日本版约 0.83 [1]。
- 分台网：原版在 JMA、F-net、DONET、S-net 上“明显欠佳”，在 Hi-net 和大学台网上“相对较好”[1]。JMA 台和 F-net 即使重训后仍最差，作者归因于这两类台站离震中更远（JMA 优先保留远台和离岛台）、F-net 是宽频带原始波形、受微震噪声影响，而不是模型能力 [1]。
- 注意：0.1 s 容差下，+0.03–0.05 s 的系统偏差本身就会把一部分原版拾取判为 FP。所以原版的“差”有一部分来自拾取约定（JMA 拾取习惯 vs 北加州分析员习惯）而不是漏拾（推断）。

**(b) EQTransformer 原版在鸟取（2000，Hi-net）** [14]
- 5 周连续数据，18 个台（JMA 当时用 57 台）；JMA 分析员在 57 台上拾取 279104 个 P+S，EQT 在 18 台上拾取 401566 个；约 4.2 万个共同台站拾取的差值标准差约 0.08 s，MAE 约 0.06 s，平均偏差约 0.01 s，S 略好；用不到 1/3 的台检测并定位了约 2 倍的事件。
- STEAD 不含日本数据，所以这是真正的跨区域测试。但这是模型作者自己的评测 [14]。
- 结论：对 Hi-net 内陆地壳余震序列，EQT 原版权重表现不错。

**(c) 箱根火山（Kim et al. 2023，预印本数字）** [15]
- 验证集 F1：原版 P 0.832、S 0.707；本地从零训练 P 0.870、S 0.782。
- 2019-05-18/20 震群测试（5559 条波形、441 个事件，阈值 0.6）：原版 P 0.823、S 0.641；本地模型 P 0.860、S 0.755。三种模型相对人工拾取的走时差“几乎没有差别”。
- 失败模式：窗口内有多个振幅差别很大的事件时，原版只拾大事件、完全不响应小事件。
- 结论：火山震群上原版 S 波明显变差，P 波差距小；拾取精度没有变差，主要是漏拾。

**(d) S-net 海底台**
- Naoi et al. 2024：原版在 S-net、DONET 上明显差，重训后与 Hi-net 相当（在测试集覆盖的震级范围内）[1]。
- JpGU 2020 一则摘要（SSS05-P06）在 2017-01 的 695 条 S-net 波形上报告 PhaseNet 精度 81.4%、召回 81.3%（数字来自检索摘要，未打开原文，是否原版权重待核）[19]。
- S-net 没有万向节，竖直分量不保证竖直，需按 Takagi et al. 2019 的姿态估计旋转；强震动会改变姿态 [1]。这是一个具体的、可被 agent 识别的数据问题。

**(e) 2024 能登序列**
- Takahashi et al. 2026 用 30 个临时台和“机器学习方法”检测并精定位 46252 个余震（2024-04 至 06）[24]。检索摘要提到 PhaseNet 无法分开两个重叠事件，作者对其改为人工拾取 [只读摘要，具体细节待核]。
- Ross et al.（SPIDER）在能登 2020–2024 年序列上用 PhaseNet + REAL 得到 72669 个事件的初始目录（检索摘要）[25]。
- Kato 2024（2023 年 M6.5 能登）用的是匹配滤波，不是神经网络拾取 [30]。
- 没有找到“原版 PhaseNet 在能登相对 JMA 到时”的量化评测。

**(f) 2011 东北余震、深部板内地震**：未找到针对原版 PhaseNet/EQT 的量化评测（“未找到”）。

**综合判断：** 证据支持“原版权重在日本**特定子集**上明显变差”，不支持“在日本整体失效”。按证据强度排序：海底台（S-net/DONET）> 宽频带原始波形（F-net）和远台/离岛台 > 火山震群 S 波和重叠事件 > 全国系统性 0.02–0.05 s 延迟 > Hi-net 内陆地壳地震（差距小）。而且这些差距大部分已被公开的日本版权重补上 [1][2]。

### 5. 速度模型

- JMA 定位用预先计算的一维走时表（球对称分层）。1997-10 至 2020-09 主要用 JMA2001（Ueno et al. 2002）；千岛附近浅震另用 Ichikawa (1978) 表；震中距 ≥2000 km 用 J-B 表 [7][29]。
- 2020-09-01 起：陆上台 JMA2001A，海沟陆侧坡 JMA2020A，日本海沟外缘隆起 JMA2020B，南海海槽 JMA2020C；台站高程范围陆上 −4000 至 +3900 m、海底 −8000 至 0 m [7]。OBS 台下有未固结沉积层（Vp = 1.8 km/s，Vp/Vs = 3.0），观测走时比模型晚 [7]。
- 台站走时校正按 Shinohara et al. 2012 的方法计算，台站校正表可下载 [7][5]。
- 定位加权：P 权重随最近台距离变化，S 权重为 P 的 1/3；残差大的台不参与；不稳定时固定震中、按 1 km 步长扫深度 [7]。
- 三维模型：NIED 的全国三维层析模型（Matsubara 等）为训练知识，因检索额度耗尽未核实 [待核]。能登有用三维速度结构重定位 2005–2024-01 共 42583 个 JMA 事件的研究（EPS 2025，s40623-025-02227-4）[31][只读摘要]。
- 推断：agent 的定位器可以直接用 JMA2001A + JMA 台站校正（Hypoinverse/NonLinLoc 需要把走时表转成分层模型或网格），与 JMA 的残差定义（O−C）保持一致，便于和 JMA 公布的到时残差对照。

### 6. 候选测试序列与标签可得性

| 候选 | 时间窗 | 波形 | JMA 到时标签 | 原版 PhaseNet 已知问题 | 备注 |
|---|---|---|---|---|---|
| 2024 能登半岛 Mw7.5 早期余震 | 2024-01-01 至 01-07 | Hi-net、JMA、大学、F-net（N-net 2024-07 才有网站数据，不可用） | 有（2026-10 已公开）；能登区域 1 月 K 级 11268 个，M≥1.7 基本全为 K [9] | 重叠事件（检索摘要）[24] | 最能展示“分析员式判断”；标签充分 |
| 2020–2023 能登震群 | 2020-12 至 2023-12 | Hi-net、JMA、大学 | 有；陆上 Mth=1.7 [7] | 未找到量化 | 流体驱动震群，深度 10–15 km（训练知识 [待核]）|
| 2016 熊本序列 | 2016-04 | Hi-net 等 | 有，但正处 PF 法刚引入、有处理例外 [2] | 未找到 | 标签政策不稳定，慎用 |
| 2022-03-16 福岛县冲 M7.4 及余震 | 2022-03 | S-net（JMA 已用）、Hi-net | 有，但海域 Mth 高（至 3.5）[7]；Naoi 2022 测试集中 S-net 占 17.9% [1] | 原版在 S-net 上明显差 [1] | 海底场景的最佳候选；需同时对照 `phasenet_sn` 和 `jma` |
| 箱根火山震群（2019；2015 年活动为训练知识 [待核]） | 2019-05-18/20 等 | V-net/JMA 火山网/温泉地学研究所 | JMA 一元化可能只收录部分火山事件 [待核]；箱根人工拾取未公开 [15] | S 波 F1 低、漏拾重叠小震 [15] | 标签获取难 |
| 低频地震（LFE） | 任意 | Hi-net | JMA 有 LFE 事件类型标记 [1] | 原版偏晚；日本版异常率 P≈15%、S≈20%（0.2 s 容差）[1] | 难度高、标签有噪声 |
| 2000 鸟取余震 | 2000-10/11 | 网站不可直接取（2004-04 前）| 有 | EQT 原版表现好 [14] | 可作“原版也行”的对照，但取数难 |

## 对本项目的影响

1. **日本 baseline 可行，但叙事要改。** 把“PhaseNet 在日本失效”改为“原版权重在日本海底台、宽频带台、S 波和重叠事件上明显变差；本地重训的权重补上了大部分，但在大事件、重叠事件、LFE 和缺标签的海域小震上仍有缺口”。设计稿里任何“日本 PhaseNet 失效”的表述，在没有我们自己的量化前都应删除或标注为待验证。
2. **对照组（必须）：** 原版 PhaseNet、原版 EQTransformer、SeisBench `jma`（必须）、`jma_wc`、海域场景加 `phasenet_sn`；有余力加 PhaseNeXt-M（GitHub 权重，注意输入 4096 采样点、UNE 通道顺序）。Agent 从 `jma` 的拾取出发再修正，才是公平的“agent 增益”。
3. **先做一个低成本的“失败地图”实验（1–2 周）：** 用 2024-01 能登序列 K 级事件（约 1.1 万个）和 2022-03 福岛县冲事件，在每个台网（Hi-net / JMA / F-net / S-net / 大学）× 相位（P/S）× 震级档上，比较原版 vs `jma` vs `phasenet_sn` 相对 JMA 人工标记子集（第 92/93 列 M–Z）的 MAE、偏差和召回。只有在 `jma` 仍然明显差的格子里，agent 才有展示空间。
4. **系统偏差要单独处理。** 原版相对 JMA 偏晚 0.02–0.05 s [1]。如果评测用 JMA 标签，agent 什么都不做、只学会“整体提前 0.03 s”也能涨分；而用定位残差做反馈时，全台一致的偏差会被发震时刻吸收、看不出来（推断）。建议：报告去偏后的 MAE 和原始 MAE；把“学到拾取约定”与“真正修正错误拾取”分开计分。
5. **标签分层。** JMA K 级事件中 30–40% 的到时是分析员接受的自动拾取 [9]。评测时把“人工拾取子集”作为主指标，全部 K 级作为次指标；k/A 级事件（M<Mth）只能做自洽性评测（定位残差、与相邻台一致性），不能当真值。
6. **极性评测不能用 JMA 数据。** 公开到时文件里极性字段为空 [9]。日本的极性实验要么去掉，要么另找标签（Hara et al. 2019 / Uchide 的极性数据 [待核]），要么请日本合作者人工标注小样本。不要把加州 pilot 的“极性 95% 一致”外推到日本。
7. **数据合规。** 不发布 NIED 波形和 JMA 到时；只发布事件 ID 列表、下载与预处理脚本（HinetPy）、我们自己的拾取和定位结果；论文中引用 NIED 各台网 DOI 并向 NIED 报告。尽早注册 Hi-net 账号（各成员个人账号），并发邮件确认“发布派生拾取”是否允许。
8. **最能体现 agent 价值的日本子场景（推断，按优先级）：**
   - 2024-01-01 至 01-07 能登早期余震：事件密集、波形重叠，单窗口模型的已知弱点 [15][24]，又有大量 K 级标签 [9]。
   - S-net 海域事件（2022-03 福岛县冲）：姿态未校正、沉积层导致的 S 波延迟等可解释问题适合 agent 的视觉判断和残差推理 [1][7]；但小震没有人工标签，只能用 M≥Mth 的事件评测。
   - M≥4 的较大事件：日本版拾取器随震级变差 [1]，每个事件人工拾取成本也低，适合展示“分析员式”判断。
   - 不建议首选：Hi-net 内陆中小地壳地震（原版和日本版都已经不错，agent 的空间小）；火山（标签难拿）。
9. **时间和资源估计（推断）：** JMA 到时 1 个月文件约 80 MB 解压，可全量处理；能登 1 周 × 约 100 台的 Hi-net 连续数据量约几十 GB，按 HinetPy 限制需约数百次请求，可在几天内完成。

## 未解决与待核

- **初动极性：** 只抽查了 2005-10、2013-04、2024-01 三个月。需要扫描全部月份确认是否有任何时期填写了初动字段；同时向 JMA 确认逐台极性是否另有发布渠道。
- **大写 A–L 的含义：** 格式文档称“自动拾取（高可靠）”，Naoi 称“大写 = 经人工处理”。需向 JMA（Tamaribuchi）或 Naoi 确认：K 级事件中 A/X 标记的到时是否经分析员目视确认。
- **非日本研究者注册：** 条款无国籍限制，但未找到书面资格规则；需要实际申请或邮件 sanction-2026@bosai.go.jp 确认。
- **派生数据发布：** 发布我们自己在 NIED 波形上的拾取是否允许，需 NIED 书面确认。
- **原版 PhaseNet 在能登、2011 东北余震、深部板内地震上的量化表现：** 未找到，需要我们自己做（见“影响”第 3 条）。
- **Naoi 图 7/8 的数值：** 本文为目读近似值。若用于论文，应向作者索取原始数值或自己复现。
- **Hakone 数字：** 来自预印本，正式版可能有修改。
- **因 WebSearch 额度耗尽未能核实：** Uchide 2020 极性/机制目录；Tokuda、Mizutani、Shimoda、Kubo 名下的拾取器；Wang et al. 2019 PickNet 的权重可得性；NIED 三维速度模型（Matsubara 等）；JpGU 2020 S-net 摘要的完整内容；Takahashi et al. 2026 中 PhaseNet 失败细节；JMA 一元化目录是否收录火山区小震（与 JMA 火山监测目录的关系）。可在后续轮次继续检索。
- **问谁：** Naoi Makoto（北大）关于 JMA 标签细节和 PhaseNeXt；Uchide Takahiko（AIST）关于 S-net 迁移学习和极性；Suzuki Rintaro / Uchida Naoki（东北大）关于 PhaseNetSN 的 S-net 评测；Tamaribuchi Koji（JMA）关于 PF 处理和标记含义。

## 参考文献

1. Naoi M, Tamaribuchi K, Shimojo K, Katoh S, Ohyanagi S (2024). Neural phase picker trained on the Japan Meteorological Agency unified earthquake catalog. Earth, Planets and Space 76:150. https://doi.org/10.1186/s40623-024-02091-8 ；预印本 https://doi.org/10.21203/rs.3.rs-4464239/v1 [已读原文：预印本全文及图 7、8；正式版未打开]
2. Naoi M, Shimojo K, Tamaribuchi K (2026). PhaseNeXt: neural phase picker trained on 20-year records to process the JMA-unified data set. Earth, Planets and Space（2026-11-04 在线）. https://doi.org/10.1186/s40623-026-02578-6 ；预印本 https://doi.org/10.21203/rs.3.rs-8174647/v1 [已读原文：预印本全文；正式版未打开]
3. mktnaoi/JMAuniPicker（GitHub README）. https://github.com/mktnaoi/JMAuniPicker [已读原文]
4. SeisBench 0.11.5：`PhaseNet.list_pretrained()` 输出（含 jma、jma_wc、phasenet_sn、volpick）及模型元数据 https://seisbench.gfz.de/mirror/models/v3/phasenet/jma.json.v1 、jma_wc.json.v1、phasenet_sn.json.v1、volpick.json.v1 [已读原文]
5. Japan Meteorological Agency. The Seismological Bulletin of Japan：索引 https://www.data.jma.go.jp/svd/eqev/data/bulletin/index_e.html ；到时数据下载 https://ds.data.jma.go.jp/eqev/data/bulletin/deck_e.html ；更新历史 https://www.data.jma.go.jp/svd/eqev/data/bulletin/update_e.html ；Notes https://www.data.jma.go.jp/svd/eqev/data/bulletin/readme_e.html [已读原文]
6. JMA. Arrival time data record format. https://www.data.jma.go.jp/eqev/data/bulletin/data/format/datfmt_e.html （日文版 datfmt_j.html）[已读原文]
7. JMA. User's guide（catalog notes）. https://www.data.jma.go.jp/svd/eqev/data/bulletin/catalog/notes_e.html [已读原文]
8. JMA. Nodal plane solution record format. https://www.data.jma.go.jp/eqev/data/bulletin/data/format/mecfmt_e.html [已读原文]
9. 本文作者对 JMA 公开到时文件 d202401.zip、d201304.zip、d200510.zip（来源 [5]）的统计（2026-11-13，按 [6] 的列定义解析；脚本在会话 scratchpad，未入库）[一手统计]
10. NIED. Registration（Announcement to Seismic Data Users）. https://hinetwww11.bosai.go.jp/nied/registration/?LANG=en [已读原文]
11. NIED. Terms of Usage for Data of Center for Earthquake, Tsunami and Volcano Observation Research (Provisional Translation). https://www.mowlas.bosai.go.jp/policy/data/?LANG=en [已读原文，经网页摘要工具]
12. Tian D (seisman). HinetPy 文档 https://seisman.github.io/HinetPy/ 及源码 HinetPy/client.py、HinetPy/header.py（GitHub main 分支）[已读原文]
13. Aoi S, Asano Y, Kunugi T et al. (2020). MOWLAS: NIED observation network for earthquake, tsunami and volcano. Earth, Planets and Space 72:126. https://doi.org/10.1186/s40623-020-01250-x [未打开原文]
14. Mousavi SM, Ellsworth WL, Zhu W, Chuang LY, Beroza GC (2020). Earthquake transformer—an attentive deep-learning model for simultaneous earthquake detection and phase picking. Nature Communications 11:3952. https://doi.org/10.1038/s41467-020-17591-w （PMC7415159）[已读原文]
15. Kim A, Nakamura Y, Yukutake Y, Uematsu H, Abe Y (2023). Development of a high-performance seismic phase picker using deep learning in the Hakone volcanic area. Earth, Planets and Space 75:85. https://doi.org/10.1186/s40623-023-01840-5 ；预印本 https://doi.org/10.21203/rs.3.rs-2253946/v1 [已读原文：预印本]
16. Katoh S, Iio Y, Nagao H, Katao H, Sawada M, Tomisaka K (2025). SegPhase: development of arrival time picking models for Japan's seismic network using the hierarchical vision transformer. Earth, Planets and Space 77:118. https://doi.org/10.1186/s40623-025-02249-y ；预印本 v2 https://doi.org/10.21203/rs.3.rs-4291782/v2 [只读摘要 + 部分正文（预印本）]
17. Suzuki R, Uchida N, Zhu W, Beroza GC et al. (2025). The forearc seismic belt: A fluid pathway constraining down-dip megathrust earthquake rupture. Science 389:190–194. https://doi.org/10.1126/science.adt6389 [未打开原文]；数据 Zenodo https://zenodo.org/records/13854225 [已读原文：记录页]；东北大学新闻稿（日文）[只读摘要]
18. Uchide T (2025). Automatic phase picking model for ocean bottom seismic data: PhaseNet model trained using Japanese S-net data. SSA Annual Meeting 2025 海报. https://seismosoc.secure-platform.com/a/gallery/rounds/43/details/12994 [只读摘要]
19. JpGU 2020 SSS05-P06. Evaluation of deep-neural-network-based seismic arrival-time picking method for S-net data（作者未核）. https://confit.atlas.jp/guide/event/jpgu2020/subject/SSS05-P06/date [未打开原文；数字来自检索摘要，待核]
20. JpGU 2021 SCG52-03. Deep-neural-network-based arrival-time picking and earthquake location: application to S-net（作者未核）. https://confit.atlas.jp/guide/event/jpgu2021/subject/SCG52-03/detail?lang=en [未打开原文]
21. Wang J, Xiao Z, Liu C, Zhao D, Yao Z (2019). Deep learning for picking seismic arrival times. Journal of Geophysical Research: Solid Earth 124:6612–6624. https://doi.org/10.1029/2019JB017536 [未打开原文；经 [14] 引用核实书目]
22. Hara S, Fukahata Y, Iio Y (2019). P-wave first-motion polarity determination of waveform data in western Japan using deep learning. Earth, Planets and Space 71. https://doi.org/10.1186/s40623-019-1111-x [未打开原文]
23. Bornstein T, Lange D, Münchmeyer J et al. (2024). PickBlue: Seismic phase picking for ocean bottom seismometers with deep learning. Earth and Space Science 11:e2023EA003332. https://doi.org/10.1029/2023EA003332 [未打开原文]
24. Takahashi, Aoyagi, Yoshida, Kimura, Kurashimo, Sakai (2026). High-precision aftershock distribution highlights the complex fault geometry of the 2024 Mw 7.5 Noto Peninsula earthquake. Geophysical Research Letters. https://doi.org/10.1029/2025GL118413 ；数据 https://zenodo.org/records/15906792 [只读摘要（Crossref 摘要）]
25. Ross ZE, Wilding JD, Azizzadenesheli K, Kato A (2025). SPIDER: Scalable probabilistic inference for differential earthquake relocation. arXiv:2508.12117 [只读摘要]
26. Zhong Y, Tan YJ (2024). Geophysical Research Letters 51:e2024GL108438（VolPick）. https://doi.org/10.1029/2024GL108438 [未打开原文；书目来自 [4]]
27. Kubo H, Naoi M, Kano M (2024). Recent advances in earthquake seismology using machine learning. Earth, Planets and Space 76:36. https://doi.org/10.1186/s40623-024-01982-0 [未打开原文]
28. Tamaribuchi K (2018). Evaluation of automatic hypocenter determination in the JMA unified catalog. Earth, Planets and Space 70. https://doi.org/10.1186/s40623-018-0915-4 [未打开原文]
29. Ueno H, Hatakeyama S, Aketagawa T et al. (2002). Improvement of hypocenter determination procedures in the Japan Meteorological Agency（日文）. Quarterly Journal of Seismology 65:123–134 [未打开原文]
30. Kato A (2024). Implications of fault-valve behavior from immediate aftershocks following the 2023 Mj6.5 earthquake beneath the Noto Peninsula, central Japan. Geophysical Research Letters 51:e2023GL106444. https://doi.org/10.1029/2023GL106444 [只读摘要]
31. （作者未核）(2025). Aftershock distribution of the 2024 Noto Peninsula Earthquake, Japan, determined using a 3D velocity structure and uncertainty quantification. Earth, Planets and Space. https://doi.org/10.1186/s40623-025-02227-4 [只读摘要（检索结果）]
32. JpGU 2022 SSS13-P06（作者未核），Hi-net 连续数据量每月约 600–800 GB 的说法. https://confit.atlas.jp/guide/event/jpgu2022/subject/SSS13-P06/date [只读摘要（检索结果）]
33. Yang S, Sang C, Hu Y, Wang K (2024). The 19-day aftershock catalog following the 2024 Noto Peninsula earthquake. Zenodo. https://doi.org/10.5281/zenodo.11124498 [已读原文：记录页]
