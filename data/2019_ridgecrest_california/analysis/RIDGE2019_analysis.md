# RIDGE2019 — 案例设计与 Source 准备

当前阶段为**候选科学设计与资料整理**。时窗未冻结（`not_frozen`），既有原始波形已复制至统一外部存储并接入 case，候选三天已完成逐点解码与初步质量检查，尚未冻结为共同输入。**速度模型获取暂时暂停**，已收集资料和未解决项保留；评测实现另行组织。

本文维护跨来源结论和唯一的准备进度表。参数、原始证据、下载记录及逐条核验结果通过文末入口查阅。

## 1. 案例目标与候选范围

核心问题：在相同连续波形和台站元数据条件下，能否稳定构建 Ridgecrest 地震目录，尤其是在 Mw 6.4、Mw 7.1 后事件密集和尾波显著的时段？当前先准备可追溯的观测、模型和参考产品，不指定任何一个发表目录为完整真值。

| 条件 | 当前方案 |
|---|---|
| 时间 | `[2019-07-04 00:00:00, 2019-07-07 00:00:00) UTC`，共 72 小时 |
| 水平范围 | 纬度 `[35.45, 36.05]`，经度 `[-117.90, -117.20]`，含边界 |
| 深度 | 各目录原生数值 `[0, 20] km`；基准未统一，暂不解释为统一物理深度范围 |
| Mw 6.4 锚点 | 官方事件 `ci38443183`，07-04 17:33:49.000 UTC |
| Mw 7.1 锚点 | 官方事件 `ci38457511`，07-06 03:19:53.040 UTC |
| 分阶段 | Mw 6.4 前、Mw 6.4 后首小时、两震间剩余时段、Mw 7.1 后首小时、后续时段；各段左闭右开 |
| 待定 | 最终台站/通道集合、波形前后缓冲、处理分块和异常时段策略 |

共同输入需要落实到 **network/station/location/channel × 有效时间段**，同时记录采样率、缺口/重叠、响应和载荷哈希。同站数或同文件体积不足以保证公平；速度模型、预处理、模板和种子目录也需单列。Ross 使用至 7 月 25 日的模板，Shelly 也使用后续取得的模板资料，不能仅裁剪输出时窗就视为三天独立输入实验或实时结果。

未来任务以离线目录构建为起点，保留事件时间、唯一标识、位置、深度基准和震级类型，以及震相关联和处理记录。原始波形条件与提供目录/震相的辅助条件应分开；目标参考目录及其提取答案归参考侧管理。具体评分、指导条件和资源预算留待评测阶段确定。

## 2. 参考目录与主要结论

本地核验覆盖 7 个目录产品和 1 个震相产品；事件产品解析错误为 0，哈希符合配置。以下事件数采用第 1 节候选筛选，详细统计见 [reference_audit.json](reference_audit.json)。

| 产品 | 全量记录 | 候选筛选后 | 用途与主要限制 |
|---|---:|---:|---|
| [Shelly Data S1](../data/catalogs/SHELLY2020_0220190309/README.md) | 34,091 | 7,716 | 密集检测、相对结构参考；不代表完整真值 |
| [Liu Table S1](../data/catalogs/LIU2020_GL086189/README.md) | 15,445 | 6,242 | 拾取—关联路线的交叉核验；无原生事件 ID 和逐事件不确定度 |
| [Ross QTM 全部](../data/catalogs/ROSS2019_SCIENCE/README.md) | 111,918 | 12,768 | 同时包含初始位置和成功重定位记录 |
| Ross `nbranch > 1` | 46,512 | 6,463 | 空间比较采用此重定位子集，不是另一独立目录 |
| [AWR v2 hypocenters](../data/catalogs/AWR2025_CALTECHDATA/README.md) | 222,864 | 5,737 | 长期方法学辅助；`magnitude_gamma` 保留原义 |
| AWR v2 moment tensors | 4,890 | 254 | 机制解辅助，不混入事件检测目录 |
| [官方 full 快照](../data/catalogs/USGS_SCSN_COMCAT_2019/README.md) | 17,959 | 6,563 | 与候选窗口快照分别保留 |
| 官方候选窗口快照 | 6,566 | 6,566 | 含地震 6,564、quarry blast 2；比较图只用地震 |

影响后续使用的限制归并如下：

- **深度与大震位置：** Shelly 深度参考面约为海拔 0.7 km，位置更接近 hypocentroid；存在异常深度记录，保留原值。官方 Mw 7.1 深度误差很大，Ross 也明确其大震深度不可靠。深度基准和不确定度解决前，不做绝对深度准确性判断。
- **身份与版本：** 同时间记录不自动合并；Liu 派生 ID 应包含来源版本与行号。官方 full 与候选快照存在 ID 差异，且均为事后修订快照。AWR v2 的 222,864/4,890 与论文的 214,467/4,892 不同，保持版本区分。
- **震相语义：** Shelly 辅助表全量约 570 万条到时，与 Data S1 的事件映射未核实；到时行数、模板 ID、检测 ID 都不能直接当成事件数或完整输入台站证据。
- **比较边界：** 各目录共享观测谱系，但检测、筛选和重定位方法不同；记录数、原生震级分布和未匹配事件不能直接解释为性能优劣。阶段边界附近的记录需先核对事件身份。

现有双向唯一对应诊断（`1 s / 5 km`）中，Shelly—Liu、Shelly—Ross、Shelly—官方和 Liu—官方的水平距离中位数约为 0.25–0.47 km。它描述产品一致性，不是真值定位误差；未对应或歧义记录保留为待核。完整阈值扫描、阶段计数和同时间 ID 明细保存在核验 JSON。

## 3. 观测、方法与模型

### 台站与波形输入

以下结论依据原始论文和附件。台站元数据来自现时服务返回的历史有效期描述；**有效期相交不等于实际波形连续覆盖**。

| 工作 | 原文输入范围 | 当前名单核验与缺口 |
|---|---|---|
| [Shelly](../references/SHELLY2020_0220190309/parsed/paper/SHELLY2020_0220190309__paper_reading.md) | SCEDC 短周期/宽频带；按可用 E/N/Z 分量，100 samples/s、2–12 Hz；模板扫描 7 月 3–18 日 | 辅助表全时段 30 站、候选三天 24 站；**均不是已确认的论文完整名单** |
| [Liu](../references/LIU2020_GL086189/parsed/paper/LIU2020_GL086189__paper_reading.md) | 主震 120 km 内 41 永久站 + 4 临时站，研究 7 月 4–9 日 | Fig. S1 已确认 45 个标识，其中 41 站在候选窗口有有效通道；GS.CA01–CA04 的返回有效期均晚于窗口末端 |
| [Ross](../references/ROSS2019_SCIENCE/parsed/paper/ROSS2019_SCIENCE__paper_reading.md) | SCEDC、主震 80 km 内 EH/HH，2–15 Hz；模板为 7 月 4–25 日主震 60 km 内 SCSN 事件 | 现有元数据筛出 29 个规则候选站；实际站名、通道和历史 SCEDC 波形可用性仍未确认 |
| [AWR](../references/AWR2025_CALTECHDATA/parsed/paper/AWR2025_CALTECHDATA__paper_reading.md) | 2019-04 至 2023-05，200 × 200 km 内 66 台三分量宽频带；检测使用 Z/N | 补图确认 CI/GS/NN/PB/ZY，未列站名；66 是长期台阵规模，18 是神经网络图规模，三天实际集合未知 |

Shelly 辅助表的 24 站均在 Liu 的 41 个窗口内有效站中，但不能据此冻结共同输入。区域元数据发现的 255 个窗口内站也不能直接补入任何论文名单。Liu 的 REAL <100 km、hypoDD <80 km 条件属于事件—台站筛选，不是主震选站半径。

原始 StationXML 共享保存在 `data/waveforms/stations/`，各工作的选择依据集中在 `station_inventory.json` 的 `catalogs/<source_id>` 字段。目前只有 Liu 和 Shelly 辅助子集导出了独立 XML；Ross 规则候选通过同一清单的 `ross_channel_candidates` 引用共享通道记录，AWR/Ross/官方实际名单仍未解决。清单、有效期和查询记录见 [station_preparation.json](station_preparation.json)；实际通道选择还需检查响应、坐标差异及覆盖。

### 目录构建与速度模型

| 工作 | 方法链 | 模型准备状态 |
|---|---|---|
| Shelly | 常规事件模板 → 检测与差分走时 → hypoDD | Table 1 的 10 层 Vp 已整理；Vs 按文中 Vp/Vs=1.73 推导 |
| Liu | PhaseNet → REAL → VELEST → hypoDD | Feng & Lees Coso 初始模型的 12 行 Vp/Vs 已由原文核实；**VELEST 更新模型和台站修正仍缺** |
| Ross | SCSN 模板初定位/hypoDD → QTM → GrowClust | 已取得 Hauksson 原文及 SCEDC SoCal 三维候选；**具体版本、原生格式与实际输入对应，以及一维预测/GrowClust 模型仍待核** |
| AWR | PhaseNO → GaMMA → HypoSVI/台站项 → GrowClust | SCSN/UCVM HK 实现与 HypoSVI 示例已取得；**实际平滑模型和台站项仍缺** |

模型数值与适用性见 [velocity_models.json](../data/models/velocity_models.json)，下载原件位于 `data/models/raw/`。获取记录和手动补充链接集中于 [acquisition_manifest.json](../data/models/acquisition_manifest.json) 的 `files`、`manual_followup`；**当前暂停继续获取**。公开实现、示例和模型引用不自动等同于论文实际配置。各方法阈值、震级计算及质量筛选由上方论文阅读记录和对应 extraction 维护。

### 断层背景

已定位 [Ponti 地表破裂制图](https://www.usgs.gov/data/digital-datasets-documenting-surface-fault-rupture-and-ground-deformation-features-produced)与 [DuRoss 地表位移观测](https://www.usgs.gov/data/surface-displacement-observations-2019-ridgecrest-california-earthquake-sequence)，载荷尚未取得，也未确认与论文 Kendrick 图层的版本对应。后续分别核验实测破裂线、位移观测和区域既有断层；目录推断结构不作为独立验证来源。

## 4. 图件与解释

目录比较沿用候选窗口和原生数值筛选：Ross 用重定位子集，官方只用 earthquake，AWR 用 v2 hypocenters。原生深度和震级尚未统一，图件用于探索性比较。

| 图件 | 内容与图注 | 文件 |
|---|---|---|
| 1：序列概览 | a：Shelly 事件水平分布，颜色表示发震时间；星号为官方 Mw 6.4（7 月 4 日 17:33:49 UTC）、Mw 7.1（7 月 6 日 03:19:53 UTC）震中。b：五个目录按 UTC 整点分箱的小时事件数，纵轴采用含零的对称对数尺度。c：Shelly 经度—原生深度投影，投影包含整个纬度范围，不是沿断层剖面。比例尺为局地近似。 | [PNG](figures/catalog_comparison/01_sequence_overview.png) · [PDF](figures/catalog_comparison/01_sequence_overview.pdf) |
| 2：空间分布比较 | a–e：五个目录使用一致的地图边界、地理纵横比和原生深度色标。星号表示上述两次大震的官方震中。f：同一数值筛选下的记录数。点云密集程度受检测、筛选、重定位和符号遮盖共同影响；图中没有加入断层线或台站位置。 | [PNG](figures/catalog_comparison/02_catalog_spatial_comparison.png) · [PDF](figures/catalog_comparison/02_catalog_spatial_comparison.pdf) |
| 3：分布与对应诊断 | a：原生震级的经验超越比例；b：原生深度经验累积分布；c：五个科学阶段的每小时平均记录数，以阶段时长归一化；d：`1 s / 5 km` 双向唯一对应的水平距离中位数与第 90 百分位，连线不是置信区间。阶段边界沿用核验配置，“later”排除对应大震后的首小时。 | [PNG](figures/catalog_comparison/03_catalog_population_diagnostics.png) · [PDF](figures/catalog_comparison/03_catalog_population_diagnostics.pdf) |

台站分布图：[PNG](figures/station_infomation/station_distribution.png) · [PDF](figures/station_infomation/station_distribution.pdf)。左图为区域分布，右图为序列区放大；蓝色三角表示 Liu 与 Shelly 辅助子集共有的 24 站，橙色为其余 17 个 Liu 有效站，紫色空心菱形为窗口后生效的 4 站，星号为两次大震。该图不是各论文完整台网，也不表示已下载波形。坐标取通道元数据，变体和绘图处理见 [图件清单](figures/station_infomation/station_distribution.json)。

现有图件显示共同的狭长分支形态，以及不同阶段的记录数量和局部散布差异。其原因需要结合观测覆盖、尾波和处理筛选解释，暂不归因于某个算法更优。完整图注保留在本节；分辨率、字体、代码和输入哈希由脚本及 [目录图件清单](figures/catalog_comparison/figure_manifest.json)维护。

### 外部既有波形

外部 `Science2019_Ross_Ridgecrest/data` 的两个目录覆盖相同 50 站，文件名范围为 2019-07-04 至 07-26（右端不含）：`waveforms_raw` 有 3,032 个 MiniSEED 文件、36.781 GB；`waveforms` 有 3,164 个文件、37.724 GB。完整路径及核验范围见 [波形核验清单](figures/waveform_examples/waveform_audit.json)。目录名称不证明这些就是 Ross 论文的精确输入。

两目录共有 3,032 个同名文件；分层抽查 33 对，均与 raw 合并断段、缺口补零后的样本及时间信息一致，其中 8 对原本即样本一致，但文件哈希均不同。新增 132 个 E/N 文件全部核实为 CI.WNM、CI.WRV2、CI.WVP2 同日 Z 分量的副本，不能作为独立水平观测。后续优先从 raw 建立输入清单，保留真实缺口，不能将工作副本的补零和复制分量计入有效观测；尚未逐样本比较全部同名文件。

- [两次大震的原始波形](figures/waveform_examples/mw6_4_mw7_1_raw_examples.png)（[PDF](figures/waveform_examples/mw6_4_mw7_1_raw_examples.pdf)）：CI.CCC、CI.CLC、PB.B918 的垂直分量，各展示发震前 20 s 至后 150 s；零点为发震时刻，不是震相拾取。
- [目录差异对比](figures/waveform_examples/legacy_waveform_directory_comparison.png)（[PDF](figures/waveform_examples/legacy_waveform_directory_comparison.pdf)）：a 为一致波形，b 为 CI.WBP 缺口补零，c 为 CI.WNM 的 Z/E/N 副本重合。两图均使用原生数字计数，未去响应、滤波或归一化；振幅不能直接用于跨仪器物理幅度比较。

只读对比复算脚本：[inspect_existing_waveforms.py](../workflows/data_preparation/figures/inspect_existing_waveforms.py)，参数仍为原 `Science2019_Ross_Ridgecrest/data` 路径。原 raw 的 3,032 个文件已独立复制到统一外部存储，逐文件 SHA-256 校验通过；原数据未改动。case 的整个 `data/waveforms` 目录链接到外部统一目录，包含波形、已迁入的 stations、清单和英文 README；内部实体 `data/` 保存原始波形，保留既有访问路径，无需双向同步。路径、台站/日结构与校验清单入口见 [波形存储说明](../data/waveforms/README.md)。 完整副本尚未裁剪；候选三天按头信息识别出 351 文件、4.768 GB、41 站；外部 `waveform_inventory.json` 统一记录来源、路径、大小、通道、样本数与文件内缺口，替代原两个清单。12 个缺失通道日均已补回；CI.WRC2.HHZ 27.39 s 断档仍在，两家服务本次查询均返回无数据；Liu 的 6 个缺失有效站已补齐，其中 CI.APL 为 HN 加速度通道；Ross 规则候选仍缺 2 站。117 个已观测通道均有采样率/有效期匹配且带响应的元数据，响应数值和远端可补性仍待核验；详见同一清单的 `download_assessment`。

Mw 6.4 和 Mw 7.1 发震前后各 10 分钟的垂直波形已分别按各自震中距排序绘制，提供原始 counts 和去响应速度两版；每道独立归一化，仅用于时序和形态比较。图件与距离表见 [Mw 6.4 波形剖面](figures/waveform_examples/mw6_4_record_section.md) 与 [Mw 7.1 波形剖面](figures/waveform_examples/mw7_1_record_section.md)。

### 候选波形质量检查

351 个文件（约 30.33 亿采样点）已逐点解码，未发现解码警告、非有限值或达到设定阈值的精确恒值段。唯一超过 1 s 的缺口为 CI.WRC2..HHZ 的 27.39 s；另外存在少量短缺口和边界偏移。**CI.CCC、CI.WRC2 的主震 HHZ 波形呈明显近似限幅形态，疑似仪器饱和，尚待响应及仪器动态范围核验；恒值筛查通过不代表无饱和。**

已完成原始波形与去趋势、加窗、2–12 Hz 零相位滤波的片段对比；这是离线诊断参数，未去仪器响应，不直接比较不同仪器的物理振幅，也未改写原始数据。覆盖、质量统计、频谱及主震细节共四组图（PNG/PDF）和指标定义见 [质量检查报告](figures/waveform_quality/README.md)。

仪器响应已进一步核验：现有 `stations/earthscope.stationxml` 覆盖全部 117 个已观测通道，响应有效期和采样率匹配，0.5–20 Hz 数值响应检查全部通过，无需重复下载。已用 ObsPy 对 CCC.HHZ、APL.HNZ、WRC2.HHZ 的主震片段去响应，统一输出 m/s；原始数据不变，疑似饱和标记保留。参数、核验表及图件见 [仪器响应报告](figures/instrument_response/README.md)。此结果不等于仪器动态范围或绝对标定已独立验证。

轻量形态筛查已覆盖 117 通道、351 文件中的 3,032,615 个连续 10 s 窗口，仅计算近似平台与孤立突跳两个指标。代表图显示 FUR.HHE、HAR.HHE 的基线阶跃；CCC.HHZ 在两次大震片段均有近似限幅形态，原因仍未确认。PB.B921/PB.B917 的突跳高分窗口放大后可见后续振荡，不能仅凭突跳分数判为坏数据。方法、通道排名与 7 个诊断窗口见 [轻量筛查](figures/waveform_quality/shape_screening.md)。这些结果仅作内部 source 诊断，不是真值标签，不自动剔除台站，也不预先替 agent 执行去响应或固定预处理。**本轮检查到此结束，保留原始观测及已知缺口即可继续后续案例构建。**

## 5. 准备进度与待办

| 工作项 | 当前状态 | 恢复相关工作时的下一步 |
|---|---|---|
| 参考目录与图件 | 本地核验、比较图已完成 | 来源或候选范围变更后重核；继续解决深度、版本和事件映射问题 |
| 台站名单与响应 | 部分完成，已按工作拆分 | 补 Shelly/AWR 实际名单，核对 Ross 候选的历史来源和通道；不能以 24 站交集代替完整核验 |
| 速度模型 | 已整理可获取资料；**获取暂停** | 按模型清单核实 Liu 更新模型、AWR 平滑版本和 Ross 实际配置 |
| 断层资料 | 已有发布入口，未取得载荷 | 核对 GIS/位移产品、坐标参考系和论文版本对应 |
| 观测范围与覆盖 | 候选 72 小时：41 站、117 通道，最低通道覆盖率 99.988870% | 保留 WRC2 的 27.39 s 缺口标记，核验仪器响应与异常时段 |
| 连续波形 | 候选窗口 351 文件、4.768 GB 已全部解码，无解码错误和非有限值；原始数据未改写 | 优先核查主震期间 HH 波形的疑似饱和，完成响应与处理参数核验后再冻结输入 |

后续重点为明确提供给 agent 的原始数据范围和元数据入口，并将内部诊断材料与任务输入分开。异常识别、去响应及预处理选择保留为 agent 的任务；当前无需为此扩大 source 质检或预先处理全量波形。

## 6. 资料入口与维护

| 内容 | 维护位置 |
|---|---|
| 候选窗口、来源及筛选配置 | [processing.yaml](processing.yaml) |
| 目录数量、重复记录、阶段和对应诊断 | [reference_audit.json](reference_audit.json) |
| 台站名单、有效期与候选筛选 | [station_preparation.json](station_preparation.json) |
| 模型数值、下载记录与待补链接 | [velocity_models.json](../data/models/velocity_models.json) · [acquisition_manifest.json](../data/models/acquisition_manifest.json) |
| 各论文证据、参数和来源版本 | `references/<source_id>/README.md`、`parsed/paper/*_reading.md`、`parsed/extraction/` |
| 各目录的原生字段与产品说明 | `data/catalogs/<source_id>/README.md` |

需要更新派生成果时，从仓库根目录运行相应脚本：

```bash
python -B data/2019_ridgecrest_california/workflows/data_preparation/catalogs/audit_references.py
python -B data/2019_ridgecrest_california/workflows/data_preparation/observations/prepare_station_metadata.py
python -B data/2019_ridgecrest_california/workflows/data_preparation/figures/plot_catalog_comparison.py
python -B data/2019_ridgecrest_california/workflows/data_preparation/figures/plot_station_distribution.py
```

以上调用使用本地原件；原件或配置变化时，先更新相应核验结果，再生成依赖它的图件。案例特有代码按 `workflows/data_preparation/catalogs/`、`workflows/data_preparation/figures/`、`workflows/data_preparation/observations/` 分层；补下载入口和参数见 [脚本说明](../workflows/data_preparation/README.md)，Shell 入口默认直连下载，`--action plan` 仅生成计划。可复用逻辑在公共 `SeismoAgentBench/utils/`。新增资料应更新对应记录及本页状态，正文不追加下载日志、哈希明细或重复参数表。


2026-09-26 补充：LB.DAC 的 HH 三分量三天数据已从 EarthScope 获取，共 9 个日文件，原始采样率 250 Hz。当前候选范围为 360 文件、42 站、120 通道，元数据有效期/采样率/响应均匹配；Ross 规则候选仅 CI.WLH2 尚缺。此前专家流程的 351 文件/41 站输入快照保持不变，新台站须通过独立输入清单和处理记录进入后续实验。详见 [波形归档说明](../data/waveforms/README.md)。
