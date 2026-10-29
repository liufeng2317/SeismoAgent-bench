# SeismoAgentBench 六案例数据总览

**统计日期：2026-10-15。** 本文档只做六个案例的横向比较；每个案例的地震、观测、研究 catalog、official catalog 和文献详情统一见 [CASE_DETAILS.md](CASE_DETAILS.md)。六案时间窗已于 2026-10-28 随 metrics v1 冻结（`window_status: frozen`）；本文统计使用数据层掩膜，评测样本以各任务的 `validation.yaml` 为准。

## 统计口径

- 波形统计来自各案例外部归档的 `waveform_inventory.json`；容量按实际文件字节统计，GiB 使用 `2^30` bytes。
- “波形台站”指至少存在一个本地 MiniSEED 文件的 `network.station`；“元数据/设计台站”是 StationXML 或论文设计范围，两者不可混用。
- catalog 按原生产品和单位统计。`event`、`relative_event`、`phase_pick`、`focal_mechanism` 以及同一事件群的不同版本均不相加。
- `ready` 仅表示本地产品存在且可解析，不表示正式 benchmark 真值已经冻结。
- official operational catalog 是 Q3 覆盖基线，不是高分辨率研究真值。

## 1. 案例与候选窗

| Case | 地震/序列 | 关键事件 | 当前候选窗（UTC，左闭右开） | 主要评测方向 |
|---|---|---|---|---|
| [Prague 2011](CASE_DETAILS.md#1-prague-oklahoma-2011) | 诱发/触发地震序列 | Mw 5.7，2011-11-06 03:53:10 | `2011-11-11`–`11-19` | 检测、关联、定位 QC、变化台网 |
| [Kaikōura 2016](CASE_DETAILS.md#2-kaikōura-new-zealand-2016) | 复杂多断层主震—余震序列 | Mw 7.8，2016-11-13 UTC | `2016-12-01`–`12-09` | 绝对/相对定位、三维模型、临时台网 |
| [Maple Creek 2017](CASE_DETAILS.md#3-maple-creek-yellowstone-2017) | Yellowstone swarm | 最大 Mw 4.4，2017-06-16 | `2017-06-11`–`06-19` | swarm 检测与定位 |
| [Kīlauea 2018](CASE_DETAILS.md#4-kīlauea-hawaiʻi-2018) | 火山—构造混合序列 | Mw 6.9，2018-05-04 22:32:54.650 | `2018-05-01`–`05-09` | 高事件率、火山监测、台站可用性 |
| [Ridgecrest 2019](CASE_DETAILS.md#5-ridgecrest-california-2019) | 双主震序列 | Mw 6.4 / Mw 7.1 | `2019-07-04`–`07-07` | 大震后高事件率目录构建 |
| [Magna 2020](CASE_DETAILS.md#6-magna-utah-2020) | 城市主震—余震序列 | Mw 5.7，2020-03-18 13:09:31.530 | `2020-03-18`–`03-26` | 永久台网目录构建、pick 条件对比 |

## 2. 波形与台站统计

| Case | MiniSEED 文件 | 容量 | 波形台站 | 元数据/设计台站 | Channel epochs / 说明 |
|---|---:|---:|---:|---:|---|
| Prague | 552 | 7,504,932,352 B（6.990 GiB） | 23 | 31 | 446；31 是设计集合，不是已下载数 |
| Kaikōura | 1,359 | 12,313,116,160 B（11.467 GiB） | 53 | 81 | 507；含未获得适用速度通道的站 |
| Maple Creek | 560 | 4,414,311,936 B（4.111 GiB） | 27 | 27 | 616；phase-manifest 台站均有波形 |
| Kīlauea | 520 | 6,946,877,952 B（6.470 GiB） | 25 | 25 | 94；phase-manifest 台站均有波形 |
| Ridgecrest | 3,107；候选窗 360 | 37,839,508,992 B（35.241 GiB）；候选窗 4.605 GiB | 57；候选窗 42 | 区域发现 404；候选窗元数据 255 | 4,509；最终共同输入尚未冻结 |
| Magna | 1,184 | 10,859,513,344 B（10.114 GiB） | 47 | 47 | 148；47 站是下载 superset |
| **合计** | **7,282；候选窗 4,535** | **79,878,260,736 B（74.392 GiB）；候选窗 43.757 GiB** | 不跨案例去重 | — | — |

仓库 `data/<case>/` 内的论文、catalog、派生统计和脚本约 2.92 GB，不包含波形软链接指向的外部载荷。

## 3. Catalog 就绪状态

| Case | Catalog source 目录 | Ready / Partial / Missing | 研究事件类产品 | Phase / 其他产品 | 关键限制 |
|---|---:|---|---|---|---|
| Prague | 4 | 4 / 0 / 0 | Cochran 8,811；Isken 13；McMahon 5,446 | McMahon 82,537 picks | 三个事件产品重叠，不求和 |
| Kaikōura | 4 | 4 / 0 / 0 | Chamberlain 33,328 corrected / 34,704 legacy；Lanza 2,655；Tan S10 67,660 / S11 46,440 | Tan 1,382,337 picks；55 mechanisms | 版本、质量条件和事件群不同 |
| Maple Creek | 3 | 1 / 1 / 1 | Pang 3,345-event 表本地缺失；Shelly event tables 缺失 | Shelly 6,260,580 picks | 当前没有就绪的研究 event catalog |
| Kīlauea | 6 | 6 / 0 / 0 | Lengliné 6,327 relative；Matoza14 12,290；Matoza21 347,446；Shelly S1 44,188 / S2 43,950；Wei 375,736 | Shelly 8,582,492 picks | 时间、空间和事件类型定义不同 |
| Ridgecrest | 5 | 5 / 0 / 0 | AWR 222,864；Liu 15,445；Ross 111,918；Shelly 34,091 | AWR 4,890 MT；Shelly 5,703,270 picks | 深度基准、重定位子集和版本需分开 |
| Magna | 3 | 3 / 0 / 0 | Baker 5,885 collapsed events；Pang 5,739 | Baker 329,611 picks | Baker paper、Pang S1 仍缺 |

这里的行数是各原生产品的 full-product 数量，不能横向相加为“参考事件总数”。完整产品角色、文件和统计链接见 [CASE_DETAILS.md](CASE_DETAILS.md)。

## 4. Official operational catalog

| Case | Provider | Full rows | Candidate-window snapshot | Duplicate IDs | Full/窗口关系 | 当前结论 |
|---|---|---:|---:|---:|---|---|
| Prague | USGS ANSS ComCat / TUL | 71 | 11 | 0 | subset | 可作为稀疏 Q3 基线 |
| Kaikōura | GeoNet / GNS | 15,948 | 1,507 | 0 | 独立筛选导出 | 通过本地范围和唯一性核验 |
| Maple Creek | USGS ANSS ComCat / UUSS-WY | 9 | 5 | 0 | subset | **空间窗不覆盖 Mw 4.4 锚点，需重取** |
| Kīlauea | USGS ComCat / HVO-HV | 40,095 | 496 | 0 | 窗口有 1 个 ID 不在 full | 保留服务端历史修订差异 |
| Ridgecrest | USGS ANSS ComCat / SCSN-CI | 17,959 | 6,566 | 0 | 窗口有 3 个 ID 不在 full | 保留服务端历史修订差异 |
| Magna | USGS ANSS ComCat / UUSS | 2,078 | 1,432 | 0 | subset | 通过本地范围和唯一性核验 |

## 5. 文献与附件资产

| Case | Reference bundles | Paper 文件 | 顶层 supplement | Extraction JSON | 明确缺项 |
|---|---:|---:|---:|---:|---|
| Prague | 4 | 4 | 4 | 4 | McMahon 2017 Table S1 |
| Kaikōura | 3 | 3 | 7 | 3 | 可选 Tan Movie SI；Chamberlain code/QuakeML 包按需补 |
| Maple Creek | 3 | 3 | 2 | 3 | event-level catalog 产品缺失，文献本身已在本地 |
| Kīlauea | 7 | 8 | 4 | 7 | 无统一必需附件缺项；按复现目标逐 source 审核 |
| Ridgecrest | 4 | 4 | 7 | 4 | 无；Ross Science DC1 已在本地 |
| Magna | 2 | 1 | 0 | 2 | Baker 2021 正文、Pang 2020 S1 |
| **合计** | **23** | **23** | **24** | **23** | — |

`Extraction JSON` 存在不代表状态为 verified，也不能替代论文正文或原始附件。

## 6. 冻结前优先事项

1. 修正 Maple Creek official baseline 的空间范围，并取得可信的 event-level 研究目录。
2. 决定 Prague 31 站设计集合与 23 站实际波形集合之间的正式输入规则。
3. 明确 Kaikōura velocity-only 与 strong-motion 扩展条件。
4. 冻结 Ridgecrest 的共同台站/通道集合，并严格区分三天候选窗和更大的外部归档。
5. 将 Magna 47 站下载 superset 与 Pang 论文的 39 站条件分开命名和评测。
6. 六案完成科学审查后统一更新 `window_status`，再重新计算冻结统计。

## 数据入口

- [按案例详细信息](CASE_DETAILS.md)
- [数据目录组织规则](../../data/README.md)
- [六个案例原始数据目录](../../data/)
