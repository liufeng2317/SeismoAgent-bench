# SeismoAgentBench 六案例数据清单

**统计日期：2026-10-30。** 波形和台站数来自各案例 `data/waveforms/waveform_inventory.json`（2026-09-26 至 10-12 生成）和 `data/waveforms/stations/station_inventory.json`；Ridgecrest 元数据台站数来自 `analysis/station_preparation.json`；catalog 行数来自各 catalog README 和产品文件；文献数是 2026-10-30 列出 `data/<case>/references/*` 的结果；仓库容量是同日 `du -sb data/20*` 的结果。

本文档先给出六个案例的横向总览，再按 case 列出地震信息、观测数据、研究 catalog、official operational catalog 和证据入口。六案时间窗已于 2026-10-28 随 metrics v1 冻结（各 `data/<case>/analysis/processing.yaml` 中 `window_status: frozen` 和 `window_freeze`，metrics v2 沿用）；评测窗、难度分级和主参考只在 [00_Case_Registry.md](00_Case_Registry.md) 中给出，本文不再重复。评测样本以各任务的 `workflows/tasks/<case>/expert/00_config/validation.yaml` 为准；本文的窗口内统计使用数据层掩膜，只作描述。

## 统计口径与共同规则

- 波形容量按实际文件字节统计，GiB 使用 `2^30` bytes。窗口内文件指至少有一个 header 采样时刻落在窗口内的文件，容量是整文件字节，不是裁剪后的字节。
- “波形台站”指至少有一个本地 MiniSEED 文件的 `network.station`；“元数据/设计台站”指 StationXML 或论文设计集合，两者不可混用。
- 六个任务的输入都是该案例的整个波形根目录（`workflows/tasks/<case>/input.json`），台站由 Agent 自选。波形和 StationXML 位于 `data/<case>/data/waveforms` 软链接指向的外部归档；清单 JSON 是本地状态依据。
- catalog 按原生产品和单位统计。event、relative event、phase pick、focal mechanism 以及同一事件群的不同版本都不相加，也不能横向相加为“参考事件总数”。
- `ready` 只表示本地产品存在且可解析。文件名中的 `benchmark`（official catalog 的窗口快照）和清单 JSON 中的 `candidate` 字段是冻结前沿用的名称，其时间范围与冻结后的数据窗相同。
- official operational catalog 是 Q3 常规网络基线，不替代研究目录；只有 Maple Creek 把 ComCat（UUSS）用作主参考（见 [00_Case_Registry.md](00_Case_Registry.md)）。

## 跨案例总览

### 波形与台站

窗口指数据窗；除 Ridgecrest 外，本地波形全部落在数据窗内，Ridgecrest 的数据窗是 `[2019-07-04 00:00, 07-07 00:00) UTC`。

| Case | MiniSEED 文件 | 容量 | 波形台站 | 元数据/设计台站 | Channel epochs | 说明 |
|---|---:|---:|---:|---:|---:|---|
| Prague | 552 | 7,504,932,352 B（6.990 GiB） | 23 | 31 | 446 | 31 是 McMahon 设计集合；ZQ LC01–LC08 只有 StationXML |
| Kaikōura | 1,359 | 12,313,116,160 B（11.467 GiB） | 53 | 81 | 507 | 81 是 Lanza Table S1 设计集合；其余站没有本地速度波形 |
| Maple Creek | 560 | 4,414,311,936 B（4.111 GiB） | 27 | 27 | 616 | Shelly phase-manifest 台站均有波形 |
| Kīlauea | 520 | 6,946,877,952 B（6.470 GiB） | 25 | 25 | 94 | Shelly phase-manifest 台站均有波形 |
| Ridgecrest | 3,107；窗口内 360 | 37,839,508,992 B（35.241 GiB）；窗口内 4,945,348,096 B（4.606 GiB） | 57；窗口内 42 | 区域发现 404；窗口内 255 | 4,509；窗口内 4,011 | 外部归档含数据窗外数据 |
| Magna | 1,184 | 10,859,513,344 B（10.114 GiB） | 47 | 47 | 148 | 47 站是可用性策略选出的下载 superset |
| **合计** | **7,282；窗口内 4,535** | **79,878,260,736 B（74.392 GiB）；窗口内 46,984,099,840 B（43.757 GiB）** | 不跨案例去重 | — | — | — |

仓库内六个 `data/<case>/` 目录（论文、catalog、派生统计和脚本）合计 2,930,139,440 B（约 2.93 GB），不含波形软链接指向的外部载荷。

### Catalog 就绪状态

各产品的行数、单位和角色见下文各 case 的“研究 catalog”和“Official catalog”表。

| Case | Catalog source 目录 | Ready / Partial / Missing | 关键限制 |
|---|---:|---|---|
| Prague | 4 | 4 / 0 / 0 | 三个研究事件产品时空范围重叠，不求和 |
| Kaikōura | 4 | 4 / 0 / 0 | 版本、质量条件和事件群不同 |
| Maple Creek | 3 | 1 / 1 / 1 | Pang 2019 事件表本地没有；Shelly 只有 phase pick 和由其派生的 time-only 检测事件表 |
| Kīlauea | 6 | 6 / 0 / 0 | 时间、空间和事件类型定义不同 |
| Ridgecrest | 5 | 5 / 0 / 0 | 深度基准、重定位子集和版本需分开 |
| Magna | 3 | 3 / 0 / 0 | Baker 正文 PDF 和 Pang S1 本地没有 |

### 文献与附件资产

PDF 按 `.gitignore`（`**/paper/*.pdf`、`**/supplement/*.pdf`）只存在于本地。Extraction JSON 存在不代表状态为 verified，也不能替代论文正文或原始附件。

| Case | Reference bundles | Paper 文件 | 顶层 supplement | Extraction JSON | 缺项与说明 |
|---|---:|---:|---:|---:|---|
| Prague | 5 | 4 | 5 | 4 | 缺 McMahon 2017 Supporting Information（含 Table S1）和 Isken 2017 Table S1；`KERANEN2013_G34045` 只有 supplement，是 Cochran 1-D 速度模型的来源 |
| Kaikōura | 3 | 3 | 7 | 3 | 可选补充 Tan Movie SI；Chamberlain `code/` 目前只放了 1-D 速度模型文件 |
| Maple Creek | 3 | 3 | 2 | 3 | `MAPLE_RELATED_OPEN` 是 Nevada Sheldon 论文，只作背景；Pang 2019 事件表未公开 |
| Kīlauea | 8 | 9 | 4 | 7 | `QUAKEFLOW_GJI_GGAC355` 有正文和 evaluation 两个 PDF；`HVO2002_OFR02157` 只有正文（HVO 速度模型来源），没有 extraction |
| Ridgecrest | 4 | 4 | 7 | 4 | 无缺项；Ross Science DC1 在本地；supplement 中含 Hutton 2010、Feng & Lees 1998、Hauksson 2000 原文 |
| Magna | 3 | 2 | 0 | 2 | 缺 Baker 2021 正文 PDF 和 Pang 2020 S1；`BJARNASON_PECHMANN_1989_BSSA` 只有正文 PDF，没有 README |
| **合计** | **26** | **25** | **25** | **23** | — |

### 未完成事项（open）

1. Maple Creek：Pang 2019 的 3,345 事件机器可读表未公开，本地没有；取得前不能做 Shelly–Pang 事件级比较。
2. 文献附件：McMahon 2017 SI（出版商渠道不可取，31 站集合已按规则重建）、Isken 2017 Table S1、Baker 2021 正文 PDF、Pang 2020 S1。
3. Kīlauea 和 Ridgecrest 的 official full 快照与窗口快照分两次下载，不严格嵌套；如需严格嵌套，应在同一次下载中重取两个快照。
4. 六个 `waveform_inventory.json` 的 `candidate.status` 仍是冻结前写入的 `not_frozen`，重建清单时应改为冻结状态。
5. Maple Creek `USGS_UUSS_COMCAT_2017/analysis/catalog_analysis.md` 及其统计仍是 2026-10-22 修正查询框之前生成的，需要重跑 catalog 分析脚本。

## 1. Prague, Oklahoma 2011

### 案例与观测

| 字段 | 信息 |
|---|---|
| 关键事件 | Mw 5.7，2011-11-06 03:53:10 UTC；诱发/触发序列；评测窗是主震后台网相对稳定的阶段 |
| 任务 | 高灵敏检测、关联、定位 QC、临时/永久混合台网鲁棒性 |
| 台站规则 | `processing.yaml` 的 `station_policy`：按规则重建 McMahon 设计集合，18 ZQ（RAMP LC01–LC18）+ 3 GS（OK020–OK022）+ 9 TA（距主震最近的 9 站）+ 1 OK（FNO） |
| 本地波形 | ZQ LC09–LC18、3 个 GS、OK FNO 和 9 个 TA 站有波形；E/N/Z 各 184 |
| 主要限制 | 震中附近最近的 LC01–LC08 只有 StationXML，与论文台站数比较时必须注明 |

### 研究 catalog

| Source | 状态 | 产品与单位 | Full rows | 角色/限制 |
|---|---|---|---:|---|
| [COCHRAN2020_GJIGGAA153](../../data/2011_prague_oklahoma/data/catalogs/COCHRAN2020_GJIGGAA153/README.md) | ready | `events_primary` / event | 8,811 | 主参考（检测与定位） |
| [ISKEN2017_BSSA0120160150](../../data/2011_prague_oklahoma/data/catalogs/ISKEN2017_BSSA0120160150/README.md) | ready | `events_relocated` / event | 13 | 结构锚点，不是完备目录 |
| [MCMAHON2017_GL072944](../../data/2011_prague_oklahoma/data/catalogs/MCMAHON2017_GL072944/README.md) | ready | `events_subspace` / event；`phase_arrivals` / phase pick | 5,446；82,537 | 检测/关联参考；事件与 pick 分开 |

### Official catalog

| 字段 | 信息 |
|---|---|
| Source | [USGS_TUL_COMCAT_2011](../../data/2011_prague_oklahoma/data/catalogs/USGS_TUL_COMCAT_2011/README.md) |
| Provider / role | USGS ANSS ComCat，TUL/US；Q3 常规基线 |
| Files | [`operational_full.csv`](../../data/2011_prague_oklahoma/data/catalogs/USGS_TUL_COMCAT_2011/USGS_TUL_COMCAT_2011__catalog_operational_full.csv) · [`operational_benchmark.csv`](../../data/2011_prague_oklahoma/data/catalogs/USGS_TUL_COMCAT_2011/USGS_TUL_COMCAT_2011__catalog_operational_benchmark.csv) |
| Full / 窗口快照 | 71 / 11 events；无重复 ID；窗口快照是 full 的子集 |
| Source fields | network `us:71`；location source `tul:64, us:7`；均为 earthquake |
| 结论 | 行数少符合常规目录的稀疏性，不是截断；不能替代研究目录 |

### 证据入口

[Case README](../../data/2011_prague_oklahoma/README.md) · [Scientific analysis](../../data/2011_prague_oklahoma/analysis/PRAGUE2011_analysis.md) · [processing.yaml](../../data/2011_prague_oklahoma/analysis/processing.yaml) · [Waveform inventory](../../data/2011_prague_oklahoma/data/waveforms/waveform_inventory.json) · [Station inventory](../../data/2011_prague_oklahoma/data/waveforms/stations/station_inventory.json)

## 2. Kaikōura, New Zealand 2016

### 案例与观测

| 字段 | 信息 |
|---|---|
| 主震 | Mw 7.8，2016-11-13 UTC（新西兰当地 11-14）；不在评测窗内 |
| 窗内锚点 | GeoNet `2016p913880`，2016-12-04 03:15:47 UTC，operational M 5.5；Lanza M 5.8 |
| 任务 | 复杂多断层条件下的绝对/相对定位、三维模型和变化台网 |
| 台站规则 | Lanza Table S1：57 NZ（GeoNet 永久台网）+ 24 STREWN 临时站（EarthScope 网络代码 Z1）；NZ 波形取自 GeoNet，Z1 取自 EarthScope |
| 本地波形 | E/N/Z 各 453；53 站都有速度通道（EH 36 站、HH 17 站），其中 4 个 NZ 站另有 HN 强震通道 |
| 主要限制 | 设计集合中其余站是 strong-motion-only 或没有适用速度通道，本地没有它们的波形 |

### 研究 catalog

| Source | 状态 | 产品与单位 | Full rows | 角色/限制 |
|---|---|---|---:|---|
| [CHAMBERLAIN2021_JB022304](../../data/2016_kaikoura_new_zealand/data/catalogs/CHAMBERLAIN2021_JB022304/README.md) | ready | corrected / event；legacy / event | 33,328；34,704 | 检测主参考用 corrected；legacy 仅作版本对照 |
| [LANZA2019_GL082780](../../data/2016_kaikoura_new_zealand/data/catalogs/LANZA2019_GL082780/README.md) | ready | preferred origins / event | 2,655 | 定位主参考；绝对/相对定位与不确定度 |
| [TAN2024_JB028735](../../data/2016_kaikoura_new_zealand/data/catalogs/TAN2024_JB028735/README.md) | ready | S10 / event；S11 / event；associated phase；mechanism | 67,660；46,440；1,382,337；55 | 检测上限参考；重定位中间产品、pick 和机制解分别使用 |

### Official catalog

| 字段 | 信息 |
|---|---|
| Source | [GEONET_2016_KAIKOURA](../../data/2016_kaikoura_new_zealand/data/catalogs/GEONET_2016_KAIKOURA/README.md) |
| Provider / role | GeoNet / GNS；Q3 常规基线 |
| Files | [`operational_full.txt`](../../data/2016_kaikoura_new_zealand/data/catalogs/GEONET_2016_KAIKOURA/GEONET_2016_KAIKOURA__catalog_operational_full.txt) · [`operational_benchmark.txt`](../../data/2016_kaikoura_new_zealand/data/catalogs/GEONET_2016_KAIKOURA/GEONET_2016_KAIKOURA__catalog_operational_benchmark.txt) |
| Full 查询 | `[2016-11-13, 2017-05-14)`，15,948 unique events，无重复 |
| 窗口快照 | 1,507 unique events，无重复；单独导出，所有 ID 都在 full 中 |
| Full event types | earthquake 5,399；unknown 10,548；not locatable 1 |
| 结论 | 保留 GeoNet 原生 ID、类型与震级标签；不能替代 Lanza/Tan 重定位目录 |

### 证据入口

[Case README](../../data/2016_kaikoura_new_zealand/README.md) · [Scientific analysis](../../data/2016_kaikoura_new_zealand/analysis/KAIKOURA2016_analysis.md) · [processing.yaml](../../data/2016_kaikoura_new_zealand/analysis/processing.yaml) · [Window anchor](../../data/2016_kaikoura_new_zealand/analysis/mainshock_anchor.json) · [Waveform inventory](../../data/2016_kaikoura_new_zealand/data/waveforms/waveform_inventory.json)

## 3. Maple Creek, Yellowstone 2017

### 案例与观测

| 字段 | 信息 |
|---|---|
| 最大事件 | `uu60203137`，2017-06-16 00:48:46.940 UTC；UUSS/论文 Mw 4.4，ComCat ML 4.36 |
| 任务 | 混合永久/临时台网下的 swarm 检测与定位 |
| 台站规则 | Shelly phase release 在窗内出现的 network-station；channel/location 按 EarthScope 元数据核对 |
| 本地波形 | E 96、N 96、Z 240、1/2 各 64 |
| 主要限制 | Pang 2019 事件表本地没有；Shelly 派生检测事件只有发震时刻，没有位置 |

### 研究 catalog

| Source | 状态 | 产品与单位 | Full rows | 角色/限制 |
|---|---|---|---:|---|
| [PANG2019_GL082376](../../data/2017_maple_creek_yellowstone/data/catalogs/PANG2019_GL082376/README.md) | missing | event catalog | — | 论文报告 3,345 events；机器可读表未公开，本地没有 |
| [SHELLY2019_GL081607](../../data/2017_maple_creek_yellowstone/data/catalogs/SHELLY2019_GL081607/README.md) | partial | phase arrivals / phase pick；派生 detection events / event（time-only） | 6,260,580；93,162（窗内 18,062） | 检测上限参考，只按发震时刻匹配；派生表由 `scripts/derive_detection_events.py` 生成；文章的 15,912 和 30,411 事件表本地没有 |

### Official catalog

ComCat（UUSS）是本案例检测、定位和震级的主参考（`workflows/tasks/2017_maple_creek_yellowstone/evaluation/metrics.yaml`）。

| 字段 | 信息 |
|---|---|
| Source | [USGS_UUSS_COMCAT_2017](../../data/2017_maple_creek_yellowstone/data/catalogs/USGS_UUSS_COMCAT_2017/README.md) |
| Provider | USGS ANSS ComCat / UUSS |
| Files | [`operational_full.csv`](../../data/2017_maple_creek_yellowstone/data/catalogs/USGS_UUSS_COMCAT_2017/USGS_UUSS_COMCAT_2017__catalog_operational_full.csv) · [`operational_benchmark.csv`](../../data/2017_maple_creek_yellowstone/data/catalogs/USGS_UUSS_COMCAT_2017/USGS_UUSS_COMCAT_2017__catalog_operational_benchmark.csv) |
| 查询框 | 2026-10-22 修正为震群范围外扩约 3 km：44.70–44.84°N、111.13–110.93°W，深度 −3 至 20 km（相对当地地表）；旧查询框位于震群以东约 40 km，已作废 |
| Full / 窗口快照 | full `[2017-06-11, 2017-09-15)` 2,447 events / 窗口 626 events；无重复 ID；窗口快照是 full 的子集，包含 Mw 4.4 锚点 `uu60203137` |
| Source fields | network 均为 `uu`，status 均为 reviewed，均为 earthquake |

### 证据入口

[Case README](../../data/2017_maple_creek_yellowstone/README.md) · [Scientific analysis](../../data/2017_maple_creek_yellowstone/analysis/MAPLE2017_analysis.md) · [processing.yaml](../../data/2017_maple_creek_yellowstone/analysis/processing.yaml) · [Mainshock anchor](../../data/2017_maple_creek_yellowstone/analysis/mainshock_anchor.json) · [Waveform inventory](../../data/2017_maple_creek_yellowstone/data/waveforms/waveform_inventory.json)

## 4. Kīlauea, Hawaiʻi 2018

### 案例与观测

| 字段 | 信息 |
|---|---|
| 关键事件 | `hv70116556`，2018-05-04 22:32:54.650 UTC，Mw 6.9，19.3182°N、154.9997°W、5.81 km |
| 任务 | 喷发起始高事件率、火山/构造混合事件、逐日台站可用性 |
| 台站规则 | Shelly phase release 在窗内出现的 HV 站，加逐日 dataselect 探针审计 |
| 本地波形 | E/N 各 160、Z 200 |
| 可用性 | 65 个通道（HH 48、EH 17）× 8 天 × 4 个时刻的探针（共 2,080 次）全部有数据；采样时刻有数据不等于全天连续 |

### 研究 catalog

| Source | 状态 | 产品与单位 | Full rows | 角色/限制 |
|---|---|---|---:|---|
| [LENGLINE2021_EPSL116653](../../data/2018_kilauea_hawaii/data/catalogs/LENGLINE2021_EPSL116653/README.md) | ready | relative event | 6,327 | ERZ 相对坐标辅助产品 |
| [MATOZA2014_GL059819](../../data/2018_kilauea_hawaii/data/catalogs/MATOZA2014_GL059819/README.md) | ready | LP event | 12,290 | 1986–2009 历史 LP；2018 窗内为 0 |
| [MATOZA2021_EA001253](../../data/2018_kilauea_hawaii/data/catalogs/MATOZA2021_EA001253/README.md) | ready | event | 347,446 | 全岛 starting/relocated 字段需分开解释 |
| [SHELLY2019_GL085636](../../data/2018_kilauea_hawaii/data/catalogs/SHELLY2019_GL085636/README.md) | ready | S1 / event；S2 / event；phase pick | 44,188；43,950；8,582,492 | 主参考（summit）与辅助 pick |
| [WEI2022_EA001979](../../data/2018_kilauea_hawaii/data/catalogs/WEI2022_EA001979/README.md) | ready | event | 375,736 | 更大时空范围、变化观测集合 |

### Official catalog

| 字段 | 信息 |
|---|---|
| Source | [USGS_HVO_COMCAT_2018](../../data/2018_kilauea_hawaii/data/catalogs/USGS_HVO_COMCAT_2018/README.md) |
| Provider / role | USGS ComCat / HVO-HV；Q3 常规基线 |
| Files | [`operational_full.csv`](../../data/2018_kilauea_hawaii/data/catalogs/USGS_HVO_COMCAT_2018/USGS_HVO_COMCAT_2018__catalog_operational_full.csv) · [`operational_benchmark.csv`](../../data/2018_kilauea_hawaii/data/catalogs/USGS_HVO_COMCAT_2018/USGS_HVO_COMCAT_2018__catalog_operational_benchmark.csv) |
| Full / 窗口快照 | 40,095 / 496 events；无重复 ID |
| Source fields | network `hv:40,079, us:16`；earthquake 40,032、volcanic eruption 62、chemical explosion 1 |
| 关系 | 窗口快照有 1 个 ID 不在单独下载的 full 快照中，记录为服务端历史修订差异 |

### 证据入口

[Case README](../../data/2018_kilauea_hawaii/README.md) · [Scientific analysis](../../data/2018_kilauea_hawaii/analysis/KILAUEA2018_analysis.md) · [processing.yaml](../../data/2018_kilauea_hawaii/analysis/processing.yaml) · [Mainshock anchor](../../data/2018_kilauea_hawaii/analysis/mainshock_anchor.json) · [Availability probe](../../data/2018_kilauea_hawaii/analysis/station_availability_probe.json) · [Waveform inventory](../../data/2018_kilauea_hawaii/data/waveforms/waveform_inventory.json)

## 5. Ridgecrest, California 2019

### 案例与观测

| 字段 | 信息 |
|---|---|
| 锚点 | `ci38443183` Mw 6.4，2019-07-04 17:33:49.000 UTC；`ci38457511` Mw 7.1，2019-07-06 03:19:53.040 UTC |
| 数据窗与评测窗 | 波形窗口统计用数据窗 `[2019-07-04 00:00, 07-07 00:00) UTC`；评测从参考目录的共同起点 2019-07-04T15:35:29.4Z 开始 |
| 任务 | 相同观测条件下的目录构建，重点考察大震后事件密集和尾波干扰 |
| 任务输入 | 整个本地波形根目录（`workflows/tasks/2019_ridgecrest_california/input.json`），台站由 Agent 自选，没有另设共同台站集合 |
| 参考台站子集 | Liu 2020 Fig. S1 标出 45 站，其中 41 站在数据窗内有元数据；Shelly phase release 在窗内 24 站；按 Ross DC1 规则得到的候选 29 站（不是确认的论文台站） |
| 窗口内波形 | 3,227,036,544 samples；E 105、N 105、Z 126、1/2 各 12 |

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
| Provider / role | USGS ANSS ComCat / SCSN-CI；Q3 常规基线 |
| Files | [`operational_full.csv`](../../data/2019_ridgecrest_california/data/catalogs/USGS_SCSN_COMCAT_2019/USGS_SCSN_COMCAT_2019__catalog_operational_full.csv) · [`operational_benchmark.csv`](../../data/2019_ridgecrest_california/data/catalogs/USGS_SCSN_COMCAT_2019/USGS_SCSN_COMCAT_2019__catalog_operational_benchmark.csv) |
| Full / 窗口快照 | 17,959 / 6,566 events；无重复 ID；窗口快照按数据窗（07-04 00:00 起）筛选 |
| Source fields | network `ci:17,956, us:3`；earthquake 17,956、quarry blast 3 |
| 关系 | 窗口快照有 3 个 ID 不在单独下载的 full 快照中，记录为服务端历史修订差异 |

### 证据入口

[Case README](../../data/2019_ridgecrest_california/README.md) · [Scientific analysis](../../data/2019_ridgecrest_california/analysis/RIDGE2019_analysis.md) · [processing.yaml](../../data/2019_ridgecrest_california/analysis/processing.yaml) · [Station preparation](../../data/2019_ridgecrest_california/analysis/station_preparation.json) · [Waveform inventory](../../data/2019_ridgecrest_california/data/waveforms/waveform_inventory.json)

## 6. Magna, Utah 2020

### 案例与观测

| 字段 | 信息 |
|---|---|
| 主震 | `uu60363602`，2020-03-18 13:09:31.530 UTC，Mw 5.7，40.7510°N、112.0783°W、11.9 km |
| 任务 | 城市永久台网目录构建；与密集 nodal/pick 条件分开评测 |
| 台站规则 | `processing.yaml` 的 `station_policy`：主震 40 km 内、探针显示至少 43/45 天有波形的永久 UU 站和 QB 强震站；不含 nodal/数字代码站和 GS 临时站 |
| 本地波形 | E/N 各 368、Z 448 |
| 主要限制 | 下载 superset 不等于 Pang 论文的 39 站条件，后者没有公开站表；评测时可向 Pang 规则取子集 |

### 研究 catalog

| Source | 状态 | 产品与单位 | Full rows | 角色/限制 |
|---|---|---|---:|---|
| [BAKER2021_0220200316](../../data/2020_magna_utah/data/catalogs/BAKER2021_0220200316/README.md) | ready | collapsed event；phase pick | 5,885；329,611 | 密集 pick/location 参考 |
| [PANG2020_GL089798](../../data/2020_magna_utah/data/catalogs/PANG2020_GL089798/README.md) | ready | event | 5,739 | 主参考（检测与定位） |

### Official catalog

| 字段 | 信息 |
|---|---|
| Source | [USGS_UUSS_COMCAT_2020](../../data/2020_magna_utah/data/catalogs/USGS_UUSS_COMCAT_2020/README.md) |
| Provider / role | USGS ANSS ComCat / UUSS；Q3 常规基线 |
| Files | [`operational_full.csv`](../../data/2020_magna_utah/data/catalogs/USGS_UUSS_COMCAT_2020/USGS_UUSS_COMCAT_2020__catalog_operational_full.csv) · [`operational_benchmark.csv`](../../data/2020_magna_utah/data/catalogs/USGS_UUSS_COMCAT_2020/USGS_UUSS_COMCAT_2020__catalog_operational_benchmark.csv) |
| Full / 窗口快照 | 2,078 / 1,432 events；无重复 ID；窗口快照是 full 的子集 |
| Source fields | network `uu:2,077, us:1`；均为 earthquake |
| 结论 | 保留原生事件 ID、震级类型和 source；不能替代 Pang/Baker 产品 |

### 证据入口

[Case README](../../data/2020_magna_utah/README.md) · [Scientific analysis](../../data/2020_magna_utah/analysis/MAGNA2020_analysis.md) · [processing.yaml](../../data/2020_magna_utah/analysis/processing.yaml) · [Mainshock anchor](../../data/2020_magna_utah/analysis/mainshock_anchor.json) · [Waveform inventory](../../data/2020_magna_utah/data/waveforms/waveform_inventory.json)

## 维护规则

1. 波形或台站内容变化时，先重建对应 inventory，再同时更新总览表和对应 case 节，并更新文首统计日期。
2. catalog 产品变化时，以产品 stats JSON 和 catalog README 为证据更新产品行；禁止从文件行数猜测事件数。
3. official catalog 更新时记录 provider、查询窗、下载时间、SHA-256、唯一 ID 和 full/窗口快照关系。
4. 文献或附件变化时更新文献总览表的数量和缺项；extraction 存在不等于 verified。
5. 窗口已冻结；评测窗或主参考如有变化，只改 [00_Case_Registry.md](00_Case_Registry.md) 和对应任务配置，本文只同步描述性统计。

## 数据入口

- [案例登记表（评测窗、主参考）](00_Case_Registry.md)
- [候选案例池](02_Case_Pool.md)
- [案例记录标准](preparation/01_Case_Record_Standard.md)
- [数据目录组织规则](../../data/README.md)
