# SeismoAgentBench 六案例详细信息

本文档按 case 组织地震信息、观测数据、研究 catalog、official operational catalog、文献状态和已知限制。跨案例统计见 [CASES_SUMMARY.md](CASES_SUMMARY.md)。所有窗口和统计目前均属于准备/审计阶段，`window_status` 仍为 `not_frozen`。

## 共同规则

- `full` 是来源或序列范围的完整本地快照；`candidate`/`benchmark` 是当前候选窗口的历史快照，不代表正式冻结。
- official catalog 只用于常规网络覆盖比较，不替代研究目录。
- product count 始终带单位；事件、相对事件、pick、机制解及不同版本不合并计数。
- 波形和 StationXML 位于案例 `data/waveforms` 指向的外部归档；清单 JSON 是本地状态依据。

## 1. Prague, Oklahoma 2011

### 案例与观测

| 字段 | 信息 |
|---|---|
| 关键事件 | Mw 5.7，2011-11-06 03:53:10 UTC；诱发/触发序列 |
| 候选窗 | `[2011-11-11, 2011-11-19) UTC`，主震后相对稳定台网阶段 |
| 任务 | 高灵敏检测、关联、定位 QC、临时/永久混合台网鲁棒性 |
| 台站 | 31 站设计集合：18 ZQ + 3 GS + 9 TA + 1 OK；446 channel epochs |
| 本地波形 | 23 站、552 文件、7,504,932,352 B；E/N/Z 各 184 |
| 主要限制 | 31 站元数据集合不能写成 31 站波形已全部下载 |

### 研究 catalog

| Source | 状态 | 产品与单位 | Full rows | 角色/限制 |
|---|---|---|---:|---|
| [COCHRAN2020_GJIGGAA153](../../data/2011_prague_oklahoma/data/catalogs/COCHRAN2020_GJIGGAA153/README.md) | ready | `events_primary` / event | 8,811 | 高分辨率主参考之一 |
| [ISKEN2017_BSSA0120160150](../../data/2011_prague_oklahoma/data/catalogs/ISKEN2017_BSSA0120160150/README.md) | ready | `events_relocated` / event | 13 | 结构锚点，不是完备目录 |
| [MCMAHON2017_GL072944](../../data/2011_prague_oklahoma/data/catalogs/MCMAHON2017_GL072944/README.md) | ready | `events_subspace` / event；`phase_arrivals` / phase pick | 5,446；82,537 | 检测/关联参考；事件与 pick 分开 |

### Official catalog

| 字段 | 信息 |
|---|---|
| Source | [USGS_TUL_COMCAT_2011](../../data/2011_prague_oklahoma/data/catalogs/USGS_TUL_COMCAT_2011/README.md) |
| Provider / role | USGS ANSS ComCat，TUL/US；Q3 routine baseline |
| Files | [`operational_full.csv`](../../data/2011_prague_oklahoma/data/catalogs/USGS_TUL_COMCAT_2011/USGS_TUL_COMCAT_2011__catalog_operational_full.csv) · [`operational_benchmark.csv`](../../data/2011_prague_oklahoma/data/catalogs/USGS_TUL_COMCAT_2011/USGS_TUL_COMCAT_2011__catalog_operational_benchmark.csv) |
| Full / candidate | 71 / 11 events；unique IDs 71 / 11；无重复 |
| Source fields | network `us:71`；location source `tul:64, us:7`；均为 earthquake |
| 结论 | 小行数符合常规目录稀疏性，不是截断证据；不能替代研究目录 |

### 文献与证据入口

- 4 个 reference bundles、4 篇 paper、4 个顶层 supplement、4 个 extraction JSON；明确缺少 McMahon Table S1。
- [Case README](../../data/2011_prague_oklahoma/README.md) · [Scientific analysis](../../data/2011_prague_oklahoma/analysis/PRAGUE2011_analysis.md) · [Waveform inventory](../../data/2011_prague_oklahoma/data/waveforms/waveform_inventory.json) · [Station inventory](../../data/2011_prague_oklahoma/data/waveforms/stations/station_inventory.json)

## 2. Kaikōura, New Zealand 2016

### 案例与观测

| 字段 | 信息 |
|---|---|
| 主震 | Mw 7.8，2016-11-13 UTC / 新西兰当地 11-14；不在当前 12 月窗口内 |
| 窗内锚点 | GeoNet `2016p913880`，2016-12-04 03:15:47 UTC，operational M 5.5；Lanza M 5.8 |
| 候选窗 | `[2016-12-01, 2016-12-09) UTC` |
| 任务 | 复杂多断层条件下的绝对/相对定位、三维模型和变化台网 |
| 台站 | Lanza Table S1 共 81 站：57 NZ + 24 STREWN/Z1；507 channel epochs |
| 本地波形 | 53 站、1,359 文件、12,313,116,160 B；E/N/Z 各 453 |
| 主要限制 | 设计集合含 strong-motion-only 或无适用速度通道的站；81 不是已下载速度波形站数 |

### 研究 catalog

| Source | 状态 | 产品与单位 | Full rows | 角色/限制 |
|---|---|---|---:|---|
| [CHAMBERLAIN2021_JB022304](../../data/2016_kaikoura_new_zealand/data/catalogs/CHAMBERLAIN2021_JB022304/README.md) | ready | corrected / event；legacy / event | 33,328；34,704 | corrected 为 canonical；legacy 仅作版本对照 |
| [LANZA2019_GL082780](../../data/2016_kaikoura_new_zealand/data/catalogs/LANZA2019_GL082780/README.md) | ready | preferred origins / event | 2,655 | 绝对/相对定位与不确定度参考 |
| [TAN2024_JB028735](../../data/2016_kaikoura_new_zealand/data/catalogs/TAN2024_JB028735/README.md) | ready | S10 / event；S11 / event；associated phase；mechanism | 67,660；46,440；1,382,337；55 | 检测、重定位中间产品、pick 和机制解分别使用 |

### Official catalog

| 字段 | 信息 |
|---|---|
| Source | [GEONET_2016_KAIKOURA](../../data/2016_kaikoura_new_zealand/data/catalogs/GEONET_2016_KAIKOURA/README.md) |
| Provider / role | GeoNet / GNS；Q3 operational baseline |
| Files | [`operational_full.txt`](../../data/2016_kaikoura_new_zealand/data/catalogs/GEONET_2016_KAIKOURA/GEONET_2016_KAIKOURA__catalog_operational_full.txt) · [`operational_benchmark.txt`](../../data/2016_kaikoura_new_zealand/data/catalogs/GEONET_2016_KAIKOURA/GEONET_2016_KAIKOURA__catalog_operational_benchmark.txt) |
| Full query | `[2016-11-13, 2017-05-14)`，15,948 unique events，无重复 |
| Candidate | `[2016-12-01, 2016-12-09)`，1,507 unique events，无重复 |
| Full event types | earthquake 5,399；unknown 10,548；not locatable 1 |
| 结论 | 保留 GeoNet 原生 ID、类型与震级标签；不能替代 Lanza/Tan 重定位目录 |

### 文献与证据入口

- 3 个 bundles、3 篇 paper、7 个顶层 supplement、3 个 extraction JSON；Tan Movie SI 和 Chamberlain 附加包按复现需求补充。
- [Case README](../../data/2016_kaikoura_new_zealand/README.md) · [Scientific analysis](../../data/2016_kaikoura_new_zealand/analysis/KAIKOURA2016_analysis.md) · [Window anchor](../../data/2016_kaikoura_new_zealand/analysis/mainshock_anchor.json) · [Waveform inventory](../../data/2016_kaikoura_new_zealand/data/waveforms/waveform_inventory.json)

## 3. Maple Creek, Yellowstone 2017

### 案例与观测

| 字段 | 信息 |
|---|---|
| 最大事件 | `uu60203137`，2017-06-16 00:48:46.940 UTC；UUSS/paper Mw 4.4，ComCat ML 4.36 |
| 候选窗 | `[2017-06-11, 2017-06-19) UTC` |
| 任务 | 混合永久/临时台网下的 swarm 检测与定位 |
| 台站与波形 | 27 个 phase-manifest 台站全部有波形；616 channel epochs |
| 本地波形 | 560 文件、4,414,311,936 B；E 96、N 96、Z 240、1/2 各 64 |
| 核心限制 | 当前没有本地就绪的研究 event-level catalog |

### 研究 catalog

| Source | 状态 | 产品与单位 | Full rows | 角色/限制 |
|---|---|---|---:|---|
| [PANG2019_GL082376](../../data/2017_maple_creek_yellowstone/data/catalogs/PANG2019_GL082376/README.md) | missing | event catalog | — | 论文报告 3,345 events；机器可读表未取得 |
| [SHELLY2019_GL081607](../../data/2017_maple_creek_yellowstone/data/catalogs/SHELLY2019_GL081607/README.md) | partial | phase arrivals / phase pick | 6,260,580 | 本地 release 是 phase-only，不是文章 event tables |

### Official catalog

| 字段 | 信息 |
|---|---|
| Source | [USGS_UUSS_COMCAT_2017](../../data/2017_maple_creek_yellowstone/data/catalogs/USGS_UUSS_COMCAT_2017/README.md) |
| Provider / role | USGS ANSS ComCat / UUSS-WY；Q3 baseline |
| Files | [`operational_full.csv`](../../data/2017_maple_creek_yellowstone/data/catalogs/USGS_UUSS_COMCAT_2017/USGS_UUSS_COMCAT_2017__catalog_operational_full.csv) · [`operational_benchmark.csv`](../../data/2017_maple_creek_yellowstone/data/catalogs/USGS_UUSS_COMCAT_2017/USGS_UUSS_COMCAT_2017__catalog_operational_benchmark.csv) |
| Full / candidate | 9 / 5 events；无重复；candidate 是 full 子集 |
| Source fields | network/location source `uu:9`；均为 earthquake |
| **范围问题** | 当前查询空间窗为 44.45–44.75°N、110.55–110.15°W，不覆盖 Mw 4.4 锚点 44.7813°N、111.0332°W |
| 结论 | 现有文件只代表旧查询历史；正式冻结前必须修正范围并重新下载 |

### 文献与证据入口

- 3 个 bundles、3 篇 paper、2 个顶层 supplement、3 个 extraction JSON；文献就绪不代表 event catalog 就绪。
- [Case README](../../data/2017_maple_creek_yellowstone/README.md) · [Scientific analysis](../../data/2017_maple_creek_yellowstone/analysis/MAPLE2017_analysis.md) · [Mainshock anchor](../../data/2017_maple_creek_yellowstone/analysis/mainshock_anchor.json) · [Waveform inventory](../../data/2017_maple_creek_yellowstone/data/waveforms/waveform_inventory.json)

## 4. Kīlauea, Hawaiʻi 2018

### 案例与观测

| 字段 | 信息 |
|---|---|
| 关键事件 | `hv70116556`，2018-05-04 22:32:54.650 UTC，Mw 6.9，19.3182°N、154.9997°W、5.81 km |
| 候选窗 | `[2018-05-01, 2018-05-09) UTC` |
| 任务 | 喷发起始高事件率、火山/构造混合事件、逐日台站可用性 |
| 台站与波形 | 25 个 Shelly phase-manifest HV 站全部有波形；94 channel epochs |
| 本地波形 | 520 文件、6,946,877,952 B；E/N 各 160、Z 200 |
| 可用性 | 65 个 EH/HH epochs × 8 天 × 4 探针全部存在；采样时刻存在不等于绝对连续 |

### 研究 catalog

| Source | 状态 | 产品与单位 | Full rows | 角色/限制 |
|---|---|---|---:|---|
| [LENGLINE2021_EPSL116653](../../data/2018_kilauea_hawaii/data/catalogs/LENGLINE2021_EPSL116653/README.md) | ready | relative event | 6,327 | ERZ 相对坐标辅助产品 |
| [MATOZA2014_GL059819](../../data/2018_kilauea_hawaii/data/catalogs/MATOZA2014_GL059819/README.md) | ready | LP event | 12,290 | 1986–2009 历史 LP；2018 窗内为 0 |
| [MATOZA2021_EA001253](../../data/2018_kilauea_hawaii/data/catalogs/MATOZA2021_EA001253/README.md) | ready | event | 347,446 | 全岛 starting/relocated 字段需分开解释 |
| [SHELLY2019_GL085636](../../data/2018_kilauea_hawaii/data/catalogs/SHELLY2019_GL085636/README.md) | ready | S1 / event；S2 / event；phase pick | 44,188；43,950；8,582,492 | summit 主/次参考与辅助 pick |
| [WEI2022_EA001979](../../data/2018_kilauea_hawaii/data/catalogs/WEI2022_EA001979/README.md) | ready | event | 375,736 | 更大时空范围、变化观测集合 |

### Official catalog

| 字段 | 信息 |
|---|---|
| Source | [USGS_HVO_COMCAT_2018](../../data/2018_kilauea_hawaii/data/catalogs/USGS_HVO_COMCAT_2018/README.md) |
| Provider / role | USGS ComCat / HVO-HV；Q3 baseline |
| Files | [`operational_full.csv`](../../data/2018_kilauea_hawaii/data/catalogs/USGS_HVO_COMCAT_2018/USGS_HVO_COMCAT_2018__catalog_operational_full.csv) · [`operational_benchmark.csv`](../../data/2018_kilauea_hawaii/data/catalogs/USGS_HVO_COMCAT_2018/USGS_HVO_COMCAT_2018__catalog_operational_benchmark.csv) |
| Full / candidate | 40,095 / 496；无重复 |
| Source fields | network `hv:40,079, us:16`；earthquake 40,032、volcanic eruption 62、chemical explosion 1 |
| 关系 | candidate 有 1 个 ID 不在独立下载的 full 快照中，记录为服务端历史修订差异 |
| 结论 | 如需严格嵌套，应在同一 acquisition session 重取两个快照 |

### 文献与证据入口

- 7 个 bundles、8 个 paper 文件、4 个顶层 supplement、7 个 extraction JSON。
- [Case README](../../data/2018_kilauea_hawaii/README.md) · [Scientific analysis](../../data/2018_kilauea_hawaii/analysis/KILAUEA2018_analysis.md) · [Mainshock anchor](../../data/2018_kilauea_hawaii/analysis/mainshock_anchor.json) · [Waveform inventory](../../data/2018_kilauea_hawaii/data/waveforms/waveform_inventory.json)

## 5. Ridgecrest, California 2019

### 案例与观测

| 字段 | 信息 |
|---|---|
| 锚点 | `ci38443183` Mw 6.4，2019-07-04 17:33:49.000 UTC；`ci38457511` Mw 7.1，2019-07-06 03:19:53.040 UTC |
| 候选窗 | `[2019-07-04, 2019-07-07) UTC`，72 小时 |
| 任务 | 相同观测条件下的目录构建，重点考察大震后事件密集和尾波干扰 |
| 元数据范围 | 区域发现 404 站/4,509 epochs；候选窗元数据 255 站，不是最终输入 |
| 来源子集 | Liu 45 标识/41 窗内有效；Shelly 24；Ross 规则候选 29；共同集合未冻结 |
| 波形归档 | 57 站、3,107 文件、37,839,508,992 B；包含候选窗外数据 |
| 候选窗波形 | 42 站、360 文件、4,945,348,096 B、3,227,036,544 samples |

### 研究 catalog

| Source | 状态 | 产品与单位 | Full rows | 角色/限制 |
|---|---|---|---:|---|
| [AWR2025_CALTECHDATA](../../data/2019_ridgecrest_california/data/catalogs/AWR2025_CALTECHDATA/README.md) | ready | hypocenter / event；moment tensor | 222,864；4,890 | 长时段辅助产品；保留 release/article 差异 |
| [LIU2020_GL086189](../../data/2019_ridgecrest_california/data/catalogs/LIU2020_GL086189/README.md) | ready | event | 15,445 | 独立重定位参考 |
| [ROSS2019_SCIENCE](../../data/2019_ridgecrest_california/data/catalogs/ROSS2019_SCIENCE/README.md) | ready | event | 111,918 | 仅 `nbranch>1` 是成功重定位子集 |
| [SHELLY2020_0220190309](../../data/2019_ridgecrest_california/data/catalogs/SHELLY2020_0220190309/README.md) | ready | event；phase pick | 34,091；5,703,270 | matched-filter 主参考；pick 表是辅助产品 |

### Official catalog

| 字段 | 信息 |
|---|---|
| Source | [USGS_SCSN_COMCAT_2019](../../data/2019_ridgecrest_california/data/catalogs/USGS_SCSN_COMCAT_2019/README.md) |
| Provider / role | USGS ANSS ComCat / SCSN-CI；Q3 baseline |
| Files | [`operational_full.csv`](../../data/2019_ridgecrest_california/data/catalogs/USGS_SCSN_COMCAT_2019/USGS_SCSN_COMCAT_2019__catalog_operational_full.csv) · [`operational_benchmark.csv`](../../data/2019_ridgecrest_california/data/catalogs/USGS_SCSN_COMCAT_2019/USGS_SCSN_COMCAT_2019__catalog_operational_benchmark.csv) |
| Full / candidate | 17,959 / 6,566；无重复 |
| Source fields | network `ci:17,956, us:3`；earthquake 17,956、quarry blast 3 |
| 关系 | candidate 有 3 个 ID 不在独立下载的 full 快照中，记录为历史修订差异 |
| 结论 | 正式严格嵌套比较需同一 acquisition session 重取 |

### 文献与证据入口

- 4 个 bundles、4 篇 paper、7 个顶层 supplement、4 个 extraction JSON；Ross Science DC1 已在本地。
- [Case README](../../data/2019_ridgecrest_california/README.md) · [Scientific analysis](../../data/2019_ridgecrest_california/analysis/RIDGE2019_analysis.md) · [Station preparation](../../data/2019_ridgecrest_california/analysis/station_preparation.json) · [Waveform inventory](../../data/2019_ridgecrest_california/data/waveforms/waveform_inventory.json)

## 6. Magna, Utah 2020

### 案例与观测

| 字段 | 信息 |
|---|---|
| 主震 | `uu60363602`，2020-03-18 13:09:31.530 UTC，Mw 5.7，40.7510°N、112.0783°W、11.9 km |
| 候选窗 | `[2020-03-18, 2020-03-26) UTC` |
| 任务 | 城市永久台网目录构建；与密集 nodal/pick 条件分开评测 |
| 台站与波形 | 可用性策略选择 47 个永久站；47 站均有波形；148 channel epochs |
| 本地波形 | 1,184 文件、10,859,513,344 B；E/N 各 368、Z 448 |
| 主要限制 | 47 站是下载 superset；Pang 论文的 39 站条件无公开站表 |

### 研究 catalog

| Source | 状态 | 产品与单位 | Full rows | 角色/限制 |
|---|---|---|---:|---|
| [BAKER2021_0220200316](../../data/2020_magna_utah/data/catalogs/BAKER2021_0220200316/README.md) | ready | collapsed event；phase pick | 5,885；329,611 | 密集 pick/location 参考；正文 PDF 缺失 |
| [PANG2020_GL089798](../../data/2020_magna_utah/data/catalogs/PANG2020_GL089798/README.md) | ready | event | 5,739 | 高分辨率重定位参考；S1 supplement 缺失 |

### Official catalog

| 字段 | 信息 |
|---|---|
| Source | [USGS_UUSS_COMCAT_2020](../../data/2020_magna_utah/data/catalogs/USGS_UUSS_COMCAT_2020/README.md) |
| Provider / role | USGS ANSS ComCat / UUSS；Q3 baseline |
| Files | [`operational_full.csv`](../../data/2020_magna_utah/data/catalogs/USGS_UUSS_COMCAT_2020/USGS_UUSS_COMCAT_2020__catalog_operational_full.csv) · [`operational_benchmark.csv`](../../data/2020_magna_utah/data/catalogs/USGS_UUSS_COMCAT_2020/USGS_UUSS_COMCAT_2020__catalog_operational_benchmark.csv) |
| Full / candidate | 2,078 / 1,432 events；无重复；candidate 是 full 子集 |
| Source fields | network `uu:2,077, us:1`；均为 earthquake |
| 结论 | 保留原生事件 ID、震级类型和 source；不能替代 Pang/Baker 产品 |

### 文献与证据入口

- 2 个 bundles、1 篇 paper、无顶层 supplement、2 个 extraction JSON；缺 Baker 正文和 Pang S1。
- [Case README](../../data/2020_magna_utah/README.md) · [Scientific analysis](../../data/2020_magna_utah/analysis/MAGNA2020_analysis.md) · [Mainshock anchor](../../data/2020_magna_utah/analysis/mainshock_anchor.json) · [Waveform inventory](../../data/2020_magna_utah/data/waveforms/waveform_inventory.json)

## 维护规则

1. 波形或台站内容变化时，先重建对应 inventory，再更新本文件和总览。
2. catalog 产品变化时，以产品 stats JSON 和 catalog README 为证据更新产品行；禁止从文件行数猜测事件数。
3. official catalog 更新时记录 provider、查询窗、下载时间、SHA-256、唯一 ID 和 full/candidate 关系。
4. 文献或附件变化时更新对应 case 的资产数量和明确缺项；extraction 存在不等于 verified。
5. 任何 case 冻结窗口前，先解决其“主要限制”，然后重新计算统计并同步 [CASES_SUMMARY.md](CASES_SUMMARY.md)。
