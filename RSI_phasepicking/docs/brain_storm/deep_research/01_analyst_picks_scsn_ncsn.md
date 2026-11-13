# 01. SCSN / NCSN 分析员拾取的产生过程

## 要回答的问题

- SCSN（Caltech/USGS Pasadena）和 NCSN（USGS Menlo Park / Berkeley，NCEDC）各自对哪些事件、哪些台站做人工计时？震级门槛、距离限制、复核状态字段，以及政策随时间怎样变化（例如 SCEDC 目录变更历史中的 2013 年改用自动拾取后处理、2015 年全部事件复核、2023 年 M<3 改用 PhaseNet 代替 STA/LTA）。逐条核实设计稿 §3.1 中的日期。
- 存档的相位文件如何编码拾取质量：SCEDC STP 相位格式（起始 i/e、极性 c/d、质量 1.0/0.8/0.5 及其与 Hypoinverse 权重码的对应——查 STP 手册），NCEDC 相位 / Hypoinverse 存档格式及权重码。具体从哪里下载（S3 路径、FDSN event 服务、STP）？能否区分分析员计时和自动拾取？
- ML 进入业务流程后（SCSN、NCSN），参考拾取向 PhaseNet/ML 拾取器偏多少？有没有已发表的评估（如 Tepp et al. 2025 Sci. Rep.；Zhou et al. SCEC 2026；USGS/Caltech 关于业务化 ML 的报告）？
- 南、北加州哪些时段、哪些震级范围给出的分析员标签最干净，适合做基准？Ridgecrest 2019 复核完成度（07-04/05 100%，07-06 97%，07-07 23%，之后约 10–12%）是否正确（SCEDC 2019 catalog_status 文件）？

影响的决定：基础 baseline 用哪段时间、什么震级；标签能不能当真值。

## 结论摘要

- **设计稿 §3.1 的四个日期和 Ridgecrest 完成度都对，但"目录无法区分人工计时"这一条已经过时。** 变更历史原文：2013-04-23 公告（自 2013 年 3 月 Anza 序列起生效）"最近 5–10 个台站精确计时，约 100 km 以外的拾取多数不收"；2015-01-01 起不再逐个人工计时，M≥2.5 或初检不合格的事件做完整人工分析，自动解 RMS≥0.4 或深度/震级异常的也做；2023-12-08 公告 M<3 后处理改用 PhaseNet，自动解自 2023-11-06 起使用 [1]。2019 catalog_status 文件逐日核对：07-04、07-05 为 100.0，07-06 为 97.0，07-07 为 23.4，07-08 至 07-10 为 11.5 / 9.9 / 12.0；未复核事件的最大震级每天都 ≤2.44 [2]。**但 SCEDC 的 FDSN event 服务（QuakeML，`includearrivals=true`）给每个拾取标了 `evaluationMode` = manual / automatic**，事件级也有 automatic/preliminary 与 manual/final 之分 [3][本文实测]。ComCat 也不是"全部标 reviewed"：未复核的 Ridgecrest 事件在 ComCat 中 `status=automatic` [4][本文实测]。
- **SCSN"已终审"事件里有大量拾取的时间就是自动拾取器给出的。** 实测抽样（每组 25–40 个事件）：2012 年终审事件 P 拾取 99% 为 manual；2014 年 76%；Ridgecrest 2019-07-04 至 06 为 80%（S 96%）；2021 年 68%；2024 年全区 45%（S 56%）；Ridgecrest/Coso 区 2020–2023 年 M≥2.5 只有 48%，2025–2026 年 M2.5–3 为 57%（S 79%）[本文实测，§详细发现 1.3]。**自动拾取恰好集中在最近台站和最高质量档**：质量 1.0（不确定度 0.03 s）的 P 拾取 2021 年 96%、2024 年 95% 是 automatic；Ridgecrest/Coso M2.5–3 的最近 5 个台站 P 拾取只有 46% 是 manual。合理解释是分析员看过后保留了清晰的自动拾取（推断）。
- **2023-11 之后 M<3 事件里保留下来的自动拾取主要是 PhaseNet 拾取**（hypoPN 也会保留部分实时 pickEW 拾取 [5]），所以参考标签对 PhaseNet 有直接的"自己和自己比"偏向，而且偏向集中在最清晰的震相上。Tepp et al. 2025 证实：hypoPN 用 PhaseNet 替换 pickEW，拾取约多 1 倍（P 约 +50%，S 约 +200–300%），PhaseNet 的质量档由 phase score 阈值映射而来（0.98/0.95/0.85/0.5，后改 0.97/0.93/0.6/0.5），分析员"保留或调整"自动拾取 [5]。**更早也有 PhaseNet 拾取进入目录**：2020-01 积压的 1,064 个事件中 476 个（45%）直接用 hypoPN 结果终审；2020-04-06/07 和 04-12/15 的 364 个积压事件由分析员从 hypoPN 拾取开始复核；2023-09-29 业务测试 93 个事件 [5]。设计稿"练习池 2020-01 至 2023-10 无 PhaseNet 偏向"需要剔除这些日期。
- **STP/S3 相位文件的质量值是 Hypoinverse 权重码的映射，不是 STP 手册写的"采样点数"。** STP 手册（v1.01，2007，PDF 第 34 页）写 1.0/0.8/0.5/0.3/0.0 对应 0/1/2/3/>3 个采样点的不确定度 [6]；实际文件中出现的是 1.0/0.8/0.5/0.2。逐拾取与 QuakeML 比对：1.0↔0.03 s、0.8↔0.06 s、0.5↔0.15 s、0.2↔0.30 s，且 1.0/0.8 总是 i、0.5/0.2 总是 e（分析员拾取）[本文实测]。AQMS 模式文档给出的映射是权重码 0/1/2/3/4 → 1.00/0.75/0.50/0.25/0.00 [7]，0.8 和 0.2 是 0.75 和 0.25 取一位小数的结果（推断）。因此"质量 1.0、起始 i"等价于 Hypoinverse 权重码 0，不是独立的两个条件。
- **NCSN 的情况不同：已复核事件的拾取几乎全是分析员拾取，但大量事件根本不复核。** NCEDC 月度 Hypoinverse 相位文件（`s3://ncedc-pds/event_phases/YYYY/YYYY.MM.phase.Z`）的摘要行第 164 列是复核标记 A/I/H/F，与 QuakeML 的 preliminary / reviewed / final 对应；相位行第 109 列数据源 J（Jiggle）/R（实时）[8][本文实测]。NC 权威区（去掉 The Geysers）2019、2022、2025-03、2025-07、2026-06 各月几乎 100% 终审，终审事件 P 拾取 99% 来自 J；The Geysers M<1 只有约 20–29% 复核，M1–2.5 从约 60%（2019、2022）降到 1–10%（2025–2026）[本文实测]。2025-10 月度文件中 NC 区 M1–2.5 只有 9% 复核，抽查的 12 个至今仍是 preliminary（原因未核实）。NCSN 的 S 拾取很少，S/P 约 0.14–0.15 [本文实测]。没有找到 NCSN 在业务流程中使用 ML 拾取器的证据（未找到，不等于没有）。
- **最干净的标签**：南加州是 2012 年及以前（逐个人工计时，P 99% manual）或 2013-03 至 2023-10 中只取 `evaluationMode=manual` 的拾取，并剔除上面列出的 hypoPN 测试日期；北加州是 NC 权威区、非 Geysers、`F` 标记的事件。设计稿 T1（2019-07-04 至 06）没有 PhaseNet 偏向，但约 20–29% 的 P 拾取是 STA/LTA 自动拾取，必须按 `evaluationMode` 拆开评估。**标签只能当"参考"，不能当真值**：不同网络的 i/e 判读习惯差别很大（SCSN 分析员 P 拾取中 i 占 19–44%，NCSN 约 58%），且 SCSN 分析员几乎不给权重码 0 [本文实测]。

## 详细发现

### 1. 哪些事件、哪些台站由分析员计时

#### 1.1 SCSN 政策时间线（全部取自 SCEDC 目录变更历史原文 [1]）

| 日期 | 内容（原文要点） | 设计稿 §3.1 对应说法 | 核实结果 |
|---|---|---|---|
| 2013 年 4 月以前 | "made every reasonable effort to place every impulsive pick at the correct time, and some emergent picks as well" | 未提 | 即使 2013 年以前，缓起震相也只计时"一部分" |
| 2013-04-23 公告（自 2013-03 Anza 序列起生效） | 更多依赖后处理自动拾取器；"Nearest 5 to 10 stations are accurately timed"；约 100 km 以外的拾取大多不收（视地区）；M≥2.5 "get the same attention as before"；事件可处于 I（intermediate）或 F（finalized）状态，I 表示以后再复核 | "2013-04 起" | 正确；补充：生效时间是 2013 年 3 月 Anza 序列 |
| 2015-01-01 | 不再强制逐个人工计时；每个事件仍由地震学家复核，但相当一部分只做目视检查后终审；"All events M2.5 or greater or those failing the initial summary inspection, will undergo full, manual analysis"；自动解 RMS≥0.4 或深度/震级异常的完整分析；"There is no identification in the catalog for which events have been manually timed" | "2015-01 起……目录没有字段区分" | 日期和内容正确；"无字段区分"指目录文件，拾取级的 QuakeML 有 `evaluationMode`（见 1.3） |
| 2023-09-10 | 发布 catalog_status 文件；"2019 Ridgecrest sequence ... remains largely unreviewed below M2.5" | 未提 | 文件逐日更新 [2] |
| 2023-12-08 公告 | M<3 事件后处理的拾取器由 STA/LTA 换成 PhaseNet；"Automatic solutions using the new post-processing setup began on November 6"，PDL 发布自 11 月 10 日 | "2023-11 起" | 正确 |

Tepp et al. 2025 补充了后处理的细节 [5]：
- 实时系统（Earthworm/AQMS，pickEW 为 STA/LTA）产生事件；**M<3** 的事件送入后处理模块 hypomag，在约 1–2 分钟窗口内重拾，只保留理论到时 ±1.5 s 内的拾取，再用 Hypoinverse 重定位。hypoPN 就是把 hypomag 中的 pickEW 换成 PhaseNet。
- hypoPN 自 test 5 起删除 100 km 以外的拾取（理由是小事件远台拾取质量差、常被删除）。
- PhaseNet 的 phase score 映射到 0–4 质量码；只有质量 0 和 1 的 P 拾取用于极性。PhaseNet 的 S 拾取一律放在第一个水平分量上，P 放在垂直分量上。
- 从 2024-11-18 起 ST-Proc（PhaseNet + GaMMA）处理子网触发，把漏检事件补进目录，送分析员复核。

#### 1.2 Ridgecrest 2019 复核完成度（核对 SCEDC 2019.catalog_status.csv [2]）

`pct_complete` = 终审事件 / (终审 + 未复核 + 部分复核)。

| 日期（UTC） | pct_complete | 未复核 | 部分复核 | 未复核事件最大震级 |
|---|---|---|---|---|
| 07-03 | 100.0 | 0 | 0 | — |
| 07-04 | 100.0 | 0 | 0 | — |
| 07-05 | 100.0 | 0 | 0 | — |
| 07-06 | 97.0 | 85 | 14 | 2.14 |
| 07-07 | 23.4 | 952 | 52 | 2.44 |
| 07-08 | 11.5 | 1344 | 70 | 2.44 |
| 07-09 | 9.9 | 1611 | 131 | 2.40 |
| 07-10 | 12.0 | 1538 | 77 | 2.44 |
| 07-13 至 07-30 | 5–13 | 400–700/天 | — | ≤2.44 |
| 08 月 | 11–26 | 约 200–400/天 | — | ≤2.39 |
| 09-13 起 | 50–73 | — | — | — |
| 11-01 起 | 93–99 | — | — | — |

- 设计稿的数字全部正确。补充：2019 年共有 144 天低于 100%；未复核事件全部 <M2.5，与 [1] 的说法一致。
- 其他年份：2015–2024 年几乎全部 100%（2015 年 2 天、2017 年 1 天例外）；**2025 年 38 天、2026 年（截至 11 月）62 天低于 100%**，未复核事件最大震级多为 M1.0–1.45（如 2026-01-16 至 01-21、05-09 至 05-28、09-12），说明 2025 年秋季以后部分 M<1.5 事件没有复核 [2][本文统计]。原因未查到（待核）。
- 抽查 2019-07-08 的 25 个事件：16 个 automatic/preliminary（所有拾取 automatic），8 个 manual/final，1 个 manual/reviewed（拾取全部 automatic）[本文实测]。
- ComCat：`ci38481439`（2019-07-08，M1.7）、`ci38481399`（M2.16）`status=automatic`；已复核的 `ci37239028` 为 `reviewed` [4]。**设计稿"ComCat 把所有事件都标为 reviewed"不正确。**
- M7.1 主震 `ci38457511`：95 个拾取（P 79、S 16），其中 7 个 P 为 automatic；M6.4 `ci38443183`：259 个拾取，其中 152 个 automatic（多数无 onset，像是实时拾取）[本文实测]。设计稿"M7.1 只有 95 个拾取（P 79、S 16）"正确。

#### 1.3 终审事件中 manual / automatic 拾取的比例（本文实测）

方法（本文自做分析）：用 SCEDC FDSN event 服务按年份随机抽事件（`random.seed(0)`，本地事件 `eq`/`l`），取 `includearrivals=true` 的 QuakeML，统计每个拾取的 `evaluationMode`；距离排序用 QuakeML arrival 的 `distance`。样本小（每组 25–40 个事件，约 700–3,400 个拾取），数字是量级，不是精确估计。脚本：`scripts/01_02_analyst_picks/`：`sample_scedc.py`、`sample_scedc_rc.py`、`tab.py`、`dist_rank.py`。

| 样本 | 事件 | 终审事件中 P 拾取 manual 比例 | S manual 比例 | 质量 1.0（0.03 s）P 拾取中 automatic 比例 |
|---|---|---|---|---|
| 2012 全区 | 25 | 0.99 | 0.99 | 8%（5/61） |
| 2014 全区 | 25 | 0.76 | 0.88 | 71%（56/79） |
| 2019-07-04 至 06 全区 | 40 | 0.80 | 0.96 | 79%（112/142） |
| 2021 全区 | 40 | 0.68 | 0.88 | 96%（136/142） |
| 2021 全区 M≥2.5 | 25 | 0.69 | 0.96 | 90%（389/434） |
| 2024 全区 | 40 | 0.45 | 0.56 | 95%（168/176） |
| 2024 全区 M≥2.5 | 25 | 0.67 | 0.89 | 85%（279/327） |
| Ridgecrest/Coso 2020-01 至 2023-10，M1–2.5 | 40 | 0.53 | 0.80 | 92%（220/239） |
| Ridgecrest/Coso 2020-01 至 2023-10，M≥2.5 | 40 | 0.48 | 0.90 | 90%（630/698，另有 142 个无 onset 的 automatic） |
| Ridgecrest/Coso 2025-01 至 2026-10，M2.5–3 | 40 | 0.57 | 0.79 | 81%（377/468） |
| Ridgecrest/Coso 2025-01 至 2026-10，M≥3 | 14 | 0.69 | 0.88 | 55%（134/242） |

按台站距离排序（每组前 25 个事件）：

| 样本 | P manual：最近 1–5 台 | 6–10 台 | >10 台 | S manual：最近 1–5 台 |
|---|---|---|---|---|
| Ridgecrest/Coso 2025–26 M2.5–3 | 0.46 | 0.45 | 0.58 | 0.71 |
| Ridgecrest/Coso 2020–23 M1–2.5 | 0.42 | 0.53 | 0.64 | 0.71 |
| Ridgecrest/Coso 2020–23 M≥2.5 | 0.48 | 0.40 | 0.47 | 0.88 |
| Ridgecrest 2019-07-04 至 06 | 0.71 | 0.76 | 0.77 | 0.94 |

要点：
- 2013 年以后，终审事件里 automatic 拾取的比例逐步升高；**最近台站、最清晰（权重码 0）的 P 拾取最可能是自动拾取**。这与"最近 5–10 个台站精确计时"不矛盾：分析员看过后认为自动拾取已经准确就不改（推断；`evaluationMode=automatic` 只说明时间值来自算法，不说明分析员没看过）。
- 每个终审事件都至少有一部分 manual 拾取（2012、Ridgecrest 07-04 至 06、M≥2.5 各组没有"全 automatic"的终审事件）；2021、2024 年全区 M<2.5 的样本中分别有 4/40、11/40 个终审事件的拾取全部是 automatic，符合 2015 年政策"部分事件只做目视检查"[1]。
- 自动拾取的来源随时间变化：2013-03 至 2023-11-05 是实时 pickEW 或 hypomag 的 STA/LTA；2023-11-06 起 M<3 事件是 PhaseNet（hypoPN）；M≥3 事件不进后处理，保留的自动拾取来自实时 pickEW [5]。
- 无 onset（`-`）的 automatic 拾取多见于 M≥3 和实时系统，像是实时拾取器直接写入的（推断）。

#### 1.4 NCSN（本文实测，基于 NCEDC 月度相位文件和 FDSN event 服务）

NCEDC 月度相位文件包含 NCSS 系统处理的全部事件，**包括 NC 权威区以外的事件**（南加州、内华达等，大多不复核）。按区域和 Md 统计第 164 列复核标记（I/H/F 视为已复核）：

| 月份 | NC 区（非 Geysers）M<1 | M1–2.5 | M≥2.5 | Geysers M<1 | Geysers M1–2.5 | 区外 M≥2.5 |
|---|---|---|---|---|---|---|
| 2019-06 | 1.00（67） | 1.00（202） | 1.00（26） | 0.22（1214） | 0.61（250） | 0.25（52） |
| 2022-03 | 1.00（60） | 0.99（280） | 0.97（33） | 0.19（1454） | 0.58（296） | 0.38（45） |
| 2025-03 | 1.00（76） | 1.00（314） | 1.00（48） | 0.28（1621） | 0.10（582） | 0.23（52） |
| 2025-07 | 0.99（106） | 1.00（294） | 0.97（34） | 0.28（1109） | 0.01（386） | 0.35（63） |
| 2025-10 | 0.28（213） | 0.09（360） | 0.15（34） | 0.01（896） | 0.00（492） | 0.10（51） |
| 2026-06 | 1.00（88） | 1.00（458） | 1.00（33） | 0.29（1232） | 0.03（508） | 0.30（61） |

（括号内为事件数；"NC 区"粗略定义为 36.5–42°N、125–119.5°W，Geysers 为 38.7–38.9°N、122.95–122.65°W。）

- NC 权威区非 Geysers 的事件几乎全部终审，**没有像 SCSN 那样按 M2.5 分档**。The Geysers 大部分小事件不复核。
- 2025-10 是例外：S3 文件 2025-12-19 更新，NC 区仍有 84% 为 A；用 FDSN 抽查其中 12 个，至今仍是 preliminary。原因未核实（推断：可能与 2025 年 10–11 月美国联邦政府停摆有关，待核）。做 NC 基准时应避开 2025-10/11。
- 终审事件的拾取来源：2019-06 中 P 9,104 个来自 J、47 个来自 R；2026-06 中 21,326 个 J、260 个 R；S 全部来自 J [本文实测]。FDSN QuakeML 的 `evaluationMode` 与之一致：2018、2022、2025、2026 抽样中终审事件 P 拾取 manual 比例为 0.83（2018）、0.97、0.99–1.00、1.00 [本文实测]。自动事件只有 P 拾取（实时拾取器不出 S），onset 为空。
- **跨网络 i/e 习惯差异**（本文自做分析，详见方向 02 §2.3）：同一事件、同一台站上 SCSN 与 NCSN 分析员的 P 拾取（36 个事件、308 对），onset 标记不一致的有 117 对，其中 111 对是 SCSN 记 e、NCSN 记 i。
- **NCSN 的 S 拾取很少**：终审事件 S/P 约 1,247/9,151 = 0.14（2019-06）、3,156/21,586 = 0.15（2026-06）。
- 没有找到 NCSN 业务化 ML 拾取的公告或论文；在相位文件和 QuakeML 中也没有看到新的数据源代码（未找到，由于本次检索额度用尽，未能系统搜索，见"未解决与待核"）。

### 2. 质量编码、下载渠道、能否区分人工与自动

#### 2.1 SCEDC STP / S3 相位格式

S3 路径：`s3://scedc-pds/event_phases/YYYY/YYYY_DOY/<evid>.phase`（us-west-2，公开，无需请求方付费）[9][本文实测]。示例（`37222356`，2019-07-04 M3.63）：

```
  37222356 eq  l 2019/07/04,17:35:46.340   35.6937   -117.4370   7.65  3.63  l 0.8
	CI    CLC HHZ --   35.8157  -117.5975   775.0 P d. i  0.8   19.84   3.774
	CI    CLC HHE --   35.8157  -117.5975   775.0 S .. e  0.5   19.84   6.044
```

STP 手册（v1.01，2007-04-23）PHASE 命令说明（PDF 第 34 页，手册页码 31）[6]：
- 字段：net, station, channel, (loc), lat, lon, elevation, phase, first-motion, signal onset quality, quality-of-pick, epicentral distance, time after origin。
- onset：i = impulsive，e = emergent，w = weak。
- first motion：第一位为短周期（c 压缩 / d 拉张 / . 空），第二位为长周期（u / r / .）。
- quality of pick："Uncertainty of 0 samples is indicated by 1.0, 1 sample 0.8, 2 samples 0.5, 3 samples 0.3, >3 samples 0.0"。
- 摘要行最后一个数是"solution/location quality [0.0,1.0]"，旧的 A/B/C/D 对应 [0.8,1.0]/[0.6,0.8]/[0.4,0.6]/[0.0,0.4]（同手册 EVENT 命令，PDF 第 33 页）。

**实测与手册不符**：现行文件中出现的拾取质量是 1.0 / 0.8 / 0.5 / 0.2（没有 0.3）。对 5 个事件（2019、2024、2026 年共 300 余个拾取）逐一与 QuakeML 对照 [本文实测]：

| 相位文件 quality | 相位文件 onset | QuakeML `time/uncertainty` | QuakeML onset | 推断的 Hypoinverse 权重码 |
|---|---|---|---|---|
| 1.0 | i | 0.03 s | impulsive | 0 |
| 0.8 | i | 0.06 s | impulsive | 1 |
| 0.5 | e（分析员）；PhaseNet 拾取也可能是 i | 0.15 s | emergent / impulsive | 2 |
| 0.2 | e | 0.30 s | emergent | 3 |

- AQMS/NCEDC 参数模式（PI v1.5.8）Arrival.quality 的定义："Hypoinverse station archive card (columns 17 and 50): 0 or 5 → 1.00; 1 or 6 → 0.75; 2 or 7 → 0.50; 3 or 8 → 0.25; 4 or 9 → 0.00" [7]。0.8、0.2 应是 0.75、0.25 四舍五入到一位小数（推断，与实测完全吻合）。**设计稿"1.0/0.8/0.5 大概对应 0/1/2"是对的，再加 0.2 对应 3。**手册的"采样点数"解释已不适用。
- 同一模式中 `qual`（onset）的定义明确写着"denotes the sharpness of the onset ... does not denote timing accuracy"；`rflag` 取 A（automatic）/ H（reviewed by human）/ F（finalized）；`deltim` 是到时标准差（秒）[7]。QuakeML 中的 `evaluationMode` 很可能由 `rflag` 导出（推断）。
- 对分析员拾取，SCSN 的 onset 与权重码是锁定的：i 只配 0/1，e 只配 2/3。PhaseNet 拾取的质量来自 phase score 阈值 [5]，所以 2024 年以后出现"i + 0.5"这样的组合（例：`41570072` 有 6 个 i/0.5 automatic 拾取）[本文实测]。
- STP 格式本身**没有** manual/automatic 字段。

#### 2.2 SCEDC 其他渠道

- FDSN event 服务 `https://service.scedc.caltech.edu/fdsnws/event/1/query?eventid=<id>&includearrivals=true` 返回 QuakeML：每个 pick 有 `time/value`、`time/uncertainty`、`onset`、`polarity`、`evaluationMode`（manual/automatic）、`evaluationStatus`；每个 arrival 有残差、台站校正、时间权重、离源角 [3][本文实测]。按时间窗查询时 `format=text`，不支持 `eventtype` 参数（实测返回 400）。
- catalog_status 文件：`https://service.scedc.caltech.edu/ftp/catalogs/catalog_status/YYYY.catalog_status.csv`，每日更新 [2]。
- SCEDC 网页目录检索也提供"Hypoinverse phase"格式输出 [10]；其中是否带有数据源/复核标记未核实。
- ComCat 的 `phase-data` 产品对 CI 事件也存在 [4]；其中 QuakeML 是否同样保留 `evaluationMode` 未核实（推断：应与 SCEDC 一致）。

#### 2.3 NCEDC 格式与渠道

- S3：`s3://ncedc-pds/event_phases/YYYY/YYYY.MM.phase.Z`（us-east-2，Hypoinverse 格式，Unix compress，月度文件，每日更新；实测最近几个月的文件在月末后 1–2 个月才定稿）[8]。也有 `earthquake_catalogs/NCEDC/YYYY.ehpcsv` 和 `event_waveforms/YYYY/YYYY.DOY/NC.<evid>.<NCSN|NCSS>.ms` [8]。
- FDSN event：`https://service.ncedc.org/fdsnws/event/1/query?eventid=<id>&includearrivals=true`，时间参数必须带 `T00:00:00`（实测）。
- 格式说明：shadow2000.pdf（Hypoinverse-2000 存档格式）[11]。相位行第 14–15 列 P remark（如 IP/EP），16 列初动（U/D），17 列 P 权重码，47–48 列 S remark，50 列 S 权重码，109 列数据源。摘要行第 163 列为版本号；**第 164 列实测为复核标记 A/I/H/F**（shadow2000.pdf 写的是"origin instance"版本字母，实际内容已变；与 QuakeML preliminary/reviewed/final 的对应由本文抽查 4 个事件确认）。
- NCSN 权重码的含义（shadow2000.pdf 表 9）[11]：

| 权重码 | 施加权重 | 分析员设想的主观误差 | 形式误差 |
|---|---|---|---|
| 0 | 1.0 | 0.02 s | 0.10 s |
| 1 | 0.5 | 0.10 s | 0.20 s |
| 2 | 0.2 | 0.20 s | 0.50 s |
| 3 | 0.1 | 0.30 s | 1.00 s |
| 4–9 | 0.0 | — | — |

  文档说明"The assignment is made by the analyst or picker software and depends on the impulsiveness or emergence of the waveform"[11]。实测 NCSN 分析员也把 I 配 0/1、E 配 2/3（2026-06 终审：IP0 6,167、IP1 6,124、EP2 6,698、EP3 2,126；S 几乎只有 IS1 和 ES2）。
- 注意：NCSN 的施加权重（1.0/0.5/0.2/0.1）与 AQMS 模式的 quality（1.00/0.75/0.50/0.25）不同；QuakeML 不确定度在两边都是 0.03/0.06/0.15/0.30 s（实测），说明 FDSN 服务用同一张表从权重码换算（推断）。所以 QuakeML 的不确定度是"码"，不是测量值。

#### 2.4 能否区分分析员计时和自动拾取

| 网络 | 字段 | 可信度 |
|---|---|---|
| SCSN | QuakeML pick `evaluationMode`（FDSN event / 可能 ComCat） | 实测与 2015、2023 年政策变化方向一致；可以区分"时间值来自算法"与"分析员给出/修改过"，**不能**区分"分析员看过并接受"与"没看过" |
| SCSN | 事件级 `evaluationStatus` final vs preliminary；catalog_status | 只到事件级 |
| SCSN | STP/S3 phase 文件 | 无此字段 |
| NCSN | 月度 Hypoinverse 文件摘要行第 164 列 A/I/H/F；相位行第 109 列 J/R；QuakeML `evaluationMode` | 已复核事件中几乎全是 J/manual；无法判断 Jiggle 中被分析员直接保留的实时拾取是否也记为 J（待核） |

### 3. 参考拾取向 PhaseNet 的偏向有多大

- **Tepp et al. 2025** [5]（Sci. Rep. 15:28938，已读全文）：
  - 6 次测试（表 1）：test 1（2023-04 已终审的 1,116 个事件，离线）；test 2（2020-04-06/07，183 个积压事件）、test 3（2020-04-12/15，181 个）由分析员从 hypoPN 结果开始复核并终审；test 4（2023-09-29，93 个，业务系统）；test 5（2023-11-08 至 17，226 个，业务系统）；test 6（2024-01 至 02，1,903 个）。
  - 积压测试：2020-01 的 1,064 个"hypomag 结果不够好、需要调整才能终审"的事件，用 hypoPN 重跑后 476 个（45%，每天 17–70%）直接终审。
  - 拾取比较：PhaseNet/hypoPN 拾取约为 hypomag 的 2 倍，被删或改到另一分量的比例稍高；漏拾少得多。与最终分析员拾取的时间差，PhaseNet 的中位数略好、均值和标准差更好，S 的改善更大。正文没有给出秒数（只在图 3d–f 中），本文未从图中读数。
  - 分类方式是"retained（analyst keeps or adjusts automatic pick on the same channel）/ deletion / miss"——论文自己的统计也把"保留未改"计为与分析员一致，等于承认最终标签中含有原样保留的 PhaseNet 拾取。
  - 质量映射阈值：test 1–5 为 phase score 0.98/0.95/0.85/0.5，test 6 为 0.97/0.93/0.6/0.5；<0.5 不用。调整后 P 拾取在质量 0/1/2 间大致均匀分布。
  - 计时复核实验：分析员复核 hypoPN 事件平均快约 30 s；"Adding new picks typically takes analysts about the same time as adjusting existing picks"。
- **本文实测给出偏向的规模**（§1.3）：Ridgecrest/Coso 2025–2026 年 M2.5–3 终审事件中 43% 的 P、21% 的 S 拾取是 automatic，最近 5 个台站的 P 拾取中达 54%；2024 年全区（多为 M<2）P 55%、S 44%。这些 automatic 拾取主要来自 hypoPN（PhaseNet）；hypoPN 会"replace ... or else retain"实时拾取 [5]，所以其中也有少量实时 pickEW 拾取（如 2025 M2.5–3 样本中 43 个无 onset 的 automatic P，推断为实时拾取）。对这些拾取，PhaseNet 与"参考"的差为零或接近零（取决于 SCSN 的 PhaseNet 版本与 SeisBench `scedc` 权重的差别，未核实）。**这正是 Advikar 试点测试集（2026-07 至 09，M≥2.5）的情况**；试点中 PhaseNet 在 M2.5–3 事件上的得分会被抬高（推断，方向确定，幅度取决于抽中多少 automatic 拾取）。
- 剩下的 manual 拾取也有锚定效应：分析员从 PhaseNet 拾取开始"保留或调整"[5]，小幅偏差可能不被修正（推断，没有找到定量研究）。
- **Zhou et al. SCEC 2026**（设计稿说"四种拾取器共识编目"）：未找到原文，无法核实（本次 WebSearch 额度在调研早期用尽）。
- Ross et al. 2018 [12] 用 2000–2017 年 SCSN"人工"P 拾取训练 CNN；按本文实测，2013 年以后的终审拾取中有约 20–30% 是 STA/LTA 自动拾取，所以 SCSN 训练集和 SeisBench 的 SCEDC 数据集都混有自动拾取（推断）。

### 4. 哪些时段、震级的标签最干净

| 候选 | 优点 | 问题 | 建议用法 |
|---|---|---|---|
| SCSN 2012 年及以前（尤其 2008–2012） | P/S 99% manual；没有 ML | 台网比现在稀；2010 El Mayor-Cucapah 积压到 2013 年仍未完成 [1]；分析员可能对缓起震相只计时一部分 [1] | 最干净的 SCSN 标签源，适合做"与分析员一致性"的主评估 |
| SCSN 2013-03 至 2023-11-05，只取 manual 拾取 | 没有 PhaseNet；仍有大量 manual 拾取 | 需剔除 2020-01、2020-04-06/07、2020-04-12/15、2023-09-29 的 hypoPN 测试日期 [5]；被保留的 STA/LTA 拾取偏向最清晰的震相 | 练习池和门控集；按 `evaluationMode` 过滤 |
| Ridgecrest 2019-07-04 至 06（T1） | 100%/100%/97% 终审；无 PhaseNet | 20–29% 的 P 是 STA/LTA 自动拾取；繁忙时段分析员可能统一给 e/0.5（例：`37239028` 的 40 个拾取全是 e/0.15 s）[本文实测]；事件重叠多 | 主测试集可用，但评估时 manual / automatic 分开报告 |
| Ridgecrest 2019-07-07 以后 | 事件多 | <M2.5 大多未复核 [2] | 不要用作标签 |
| SCSN 2023-11-06 以后 M<3 | 晚于模型训练截止 | 约一半 P 拾取是 PhaseNet | 只用 manual 拾取，并单独报告；不要用于 PhaseNet 对比 |
| SCSN 2023-11-06 以后 M≥3 | 不经 hypoPN [5] | 事件少（Ridgecrest/Coso 2025-01 至 2026-10 只有 14 个 M≥3）；仍有 31% 自动 P（实时 pickEW） | T2 的南加州部分优先用 M≥3 + manual |
| NCSN 权威区非 Geysers 终审事件 | 拾取几乎全是 J/manual；不分震级都复核 | S 拾取少（S/P≈0.15）；2025-10/11 有积压 | T2 的主要来源，尤其 P；S 评估以 SCSN 为主 |

## 对本项目的影响

1. **标签来源改为 QuakeML，而不是 STP/S3 相位文件。** 下载每个事件的 FDSN QuakeML（SCEDC 和 NCEDC），保存 `evaluationMode`、`onset`、`uncertainty`、`polarity`、残差和权重；S3 相位文件只作为备份。所有拾取指标同时报"全部参考拾取"和"仅 manual 拾取"两版。
2. **"与 PhaseNet 比较"必须排除 PhaseNet 自己产生的参考拾取。** 2023-11-06 以后 SCSN M<3 事件中的 automatic 拾取，以及 2020-01、2020-04-06/07、2020-04-12/15、2023-09-29 的事件，一律不进入 PhaseNet 对比集。建议对 Advikar 试点的 28 个事件重新算一次：把 automatic 拾取去掉后，agent 和 PhaseNet 的 MAE 各是多少。
3. **练习池（2020-01 至 2023-10）要剔除上述 hypoPN 测试日期**，并只用 manual 拾取做标签反馈。
4. **T1（2019-07-04 至 06）可以保留为主测试集**，但：(a) 只把 manual 拾取当参考；(b) 单独报告 automatic（STA/LTA）拾取上的一致性，作为"agent 是否学会了模仿 STA/LTA"的诊断；(c) 注意繁忙时段 e/0.5 的统一赋值，i/e 分层在 T1 上信息量有限。
5. **T3（半合成）的选样规则要改。** 设计稿"起始 i、质量 1.0"在 2013 年以后选出的绝大多数是自动拾取（2021 年 96%）。建议：(a) 优先从 2012 年及以前的 SCSN 或 NCSN 终审事件中选 manual、权重码 0 的 P 拾取；(b) 或者不依赖分析员标签，直接用高 SNR 记录上多种方法（分析员、AIC、PhaseNet、互相关对齐）一致的起始时间，再加噪声（见方向 02）。
6. **i/e 和权重码不是独立的分层维度。** 对分析员拾取，i ⇔ 权重码 0/1，e ⇔ 2/3；分层用"权重码 0/1/2/3"一个维度即可。SCSN 和 NCSN 的 i/e 习惯不同（SCSN 分析员 P 拾取中 i 占 19–44%，NCSN 约 58%），跨网络不要合并 i/e 统计。SCSN 分析员几乎不给权重码 0（2021 年 manual P 中仅 6/650），所以 SCSN 的"最高质量"层几乎全是自动拾取。
7. **震级门槛**：SCSN 的"人工完整分析"门槛是 M≥2.5（2015 年政策），但终审 M≥2.5 事件中仍有 30–50% 的 P 拾取是 automatic，门槛不能保证"每个拾取都是人工计时"。M≥3 的事件不经过 hypoPN，PhaseNet 偏向最小。NCSN 不按震级分档（非 Geysers 区全部复核），NC 的 M≥1.5 非 Geysers 事件可以直接用。
8. **"标签能不能当真值"**：不能。可以写"与分析员（manual 拾取）一致性"；"准确性"要靠半合成数据或独立的物理一致性（方向 02、03）。

## 未解决与待核

- **检索不完整**：本方向的 WebSearch 额度在调研早期用尽（与其他方向共享 200 次上限），后续只能抓取已知 URL。以下几项因此未能核实：Zhou et al. SCEC 2026 摘要；NCSN 是否已业务化 ML 拾取（可查 USGS ANSS/NCSS 年报、BSL 年报、SSA 2024–2026 摘要）；SCSN 2025 年秋季以后部分 M<1.5 事件不复核的原因；NCEDC 2025-10 积压的原因。可以在后续会话中补搜。
- `evaluationMode=automatic` 的确切语义：是 AQMS `rflag='A'` 吗？分析员"接受"自动拾取时是否保持 A？建议直接问 SCSN（Ellen Yu 或 Gabrielle Tepp，Tepp et al. 2025 的通讯作者 gtepp@caltech.edu）。
- SCSN 业务 PhaseNet 的权重版本（原始 NCEDC 权重、SCEDC 重训，还是自研）——决定 SeisBench `scedc` 权重的 PhaseNet 与 SCSN 参考拾取的偏向有多强。
- Tepp et al. 2025 图 3d–f 中 PhaseNet / hypomag 相对分析员的时间差数值（只在图中，未读数）；补充材料表 S1/S2。
- NCSN Jiggle 中被直接保留的实时拾取是否标 J；NCSN 是否有类似"最近 N 台精确计时"的规定（未找到书面规则）。
- 本文统计样本小（每组 25–40 个事件）。**待做**：正式选数据前对目标时段做全量统计。脚本已复制到 `scripts/01_02_analyst_picks/`：`sample_scedc.py`（按年份随机抽 SCEDC 事件，存每个拾取的 evaluationMode/onset/uncertainty）、`sample_scedc_rc.py`（同上，限 Ridgecrest/Coso 区）、`sample_ncedc.py`（NCEDC 版）、`tab.py`（按事件状态汇总）、`dist_rank.py`（按台站距离排序统计 manual 比例）、`nc_region.py`（NC 区 / Geysers 按震级的复核状态）、`cmp.py`（S3 相位文件 quality 与 QuakeML 不确定度逐拾取对照）、`qml_summary.py`。NCEDC 月度文件按区域/震级统计复核标记的代码是会话中内联运行的，未单独存档（逻辑：摘要行第 164 列、Md 取第 71–73 列，区域框见 §1.4）。抽样数据（JSON）留在会话临时目录，未复制。
- Hutton et al. 2010 [13] 对 SCSN 权重码历史定义的描述（"0 within one sample, 1 means 2–3 samples"，来自项目已有笔记的转述）与本文实测的 0.03/0.06 s 不完全一致，可能是不同年代的定义，未读原文。

## 参考文献

1. SCEDC. SCSN Catalog Change History（含 2013-04-23、2015-01-01、2023-09-10、2023-12-08 条目）. https://local.scedc.caltech.edu/eq-catalogs/change-history.html [已读原文]
2. SCEDC. Catalog processing status files, `2019.catalog_status.csv` 及 2015–2026 各年. https://service.scedc.caltech.edu/ftp/catalogs/catalog_status/2019.catalog_status.csv [已读原文，全文下载统计]
3. SCEDC FDSN event web service（QuakeML，`includearrivals=true`）. https://service.scedc.caltech.edu/fdsnws/event/1/query [已读原文，实测约 400 个事件]
4. USGS ComCat FDSN event service, GeoJSON `status` 字段（ci38481439、ci38481399、ci37239028、nc75243261、nc75243281）. https://earthquake.usgs.gov/fdsnws/event/1/query [已读原文，实测]
5. Tepp, G., Yu, E., Bhaskaran, A., Tam, R., Zhu, W., Newman, Z., Jaski, E., Scheckel, N. (2025). Improvements from incorporating machine learning algorithms into near real-time operational post-processing. Scientific Reports 15, 28938. https://doi.org/10.1038/s41598-025-14491-1 （Caltech 存档 https://authors.library.caltech.edu/records/961pk-g4n17）[已读原文]
6. SCEDC. Seismogram Transfer Program (STP) Reference Manual, Version 1.01, revised 2007-04-23（PHASE 命令，PDF 第 34 页；EVENT 命令，PDF 第 33 页）. https://scedc.caltech.edu/data/stp/STP_Manual_v1.01.pdf [已读原文]
7. NCEDC. Parametric Information (PI) schema v1.5.8, Arrival 表属性（quality、rflag、qual、fm、deltim）. https://ncedc.org/db/Documents/NewSchemas/PI/v1.5.8/PI.1.5.8/Model1/Tbl7_Attr.htm [已读原文]
8. NCEDC. AWS Public Dataset / cloud data organization（`s3://ncedc-pds`，event_phases 月度 Hypoinverse 文件）. https://ncedc.org/aws-public-dataset.html ；https://ncedc.org/db/cloud.html [已读原文；实测下载 2018–2026 年 21 个月度文件]
9. SCEDC. Cloud hosted archive（`s3://scedc-pds`）. https://local.scedc.caltech.edu/data/cloud.html [未打开原文；S3 路径与内容已实测]
10. SCEDC. Catalog search help（Hypoinverse phase format 选项）. https://local.scedc.caltech.edu/eq-catalogs/catalog-search-help.html [只读摘要（检索结果片段）]
11. NCSN / NCEDC. Hypoinverse-2000 archive ("shadow") format description, shadow2000.pdf（含表 9 权重码与主观误差）. https://www.ncedc.org/pub/doc/ncsn/shadow2000.pdf [已读原文]
12. Ross, Z. E., Meier, M.-A., Hauksson, E. (2018). P wave arrival picking and first-motion polarity determination with deep learning. JGR Solid Earth 123(6), 5120–5129. https://doi.org/10.1029/2017JB015251 ；arXiv:1804.08804 [已读原文（arXiv 版）]
13. Hutton, K., Woessner, J., Hauksson, E. (2010). Earthquake monitoring in southern California for seventy-seven years (1932–2008). BSSA 100(2), 423–446. https://doi.org/10.1785/0120090130 [未打开原文；元数据经 Crossref 核实]
14. NCEDC. Reproducing NCSS catalog locations with Hypoinverse. https://ncedc.org/ncedc/catalog-reproducing-hypoinverse-locations.html [已读原文]
