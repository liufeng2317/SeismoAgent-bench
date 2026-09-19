# Phase I six-case data audit

审计范围：逐 case 核对 `references/`、`catalogs/`、`analysis/` 和 `REFERENCES_MANIFEST.md`，并检查本地 PDF、XLSX、DOCX、ZIP 的可读性。所有本地 PDF 均通过 `%PDF-` 文件头检查；所有 XLSX/DOCX/ZIP 均通过 ZIP CRC 检查。

## Prague, Oklahoma — `2011_prague_oklahoma`

主目录 `COCHRAN2020_GJIGGAA153` 已闭合，`COCHRAN2020_GJIGGAA153__catalog_primary.txt` 有 8,810 个事件行。`ISKEN2017_BSSA0120160150` 已补充官方 Table S3，包含 13 个高质量重定位余震，适合作为深度/结构校验，不是完整区域目录。McMahon 文章和 dissertation 是结构背景。剩余工作是冻结时间窗、台站和波形量；analysis 中相关 TBD/checklist 仍未回填。

## Kaikōura, New Zealand — `2016_kaikoura_new_zealand`

Lanza 的 XML relocation/source product、Chamberlain 的两个 GrowClust CSV、Tan 的 S10（67,660 events）、S11（46,440 relocated events）和 1,172 个 phase 文件均已归档。Tan 论文描述的最终 41,392-event cluster-filtered set没有独立 CSV；Wiley 还列有尚未下载的 Movie SI-S01，因此 Tan supplement 状态保留 partial。Lanza/Tan 的窗口事件数、台站和波形量仍待冻结窗口后统计。

## Maple Creek, Yellowstone — `2017_maple_creek_yellowstone`

Shelly & Hardebeck 的论文、SI 和 USGS correlation-phase CSV（6,260,580 data rows）完整；Pang 的论文和 SI 完整。但该 phase 文件不是 Pang 所述 3,345-event GrowClust event catalog。Pang 的机器可读目录仍没有确认的公开下载入口，不能用 Shelly phase 产品替代。目标窗口、台站和波形量仍为 TBD。

## Kīlauea, Hawaiʻi — `2018_kilauea_hawaii`

Shelly S1/S2、Wei 375,736-event catalog、Matoza 2021（347,446 starting / 299,966 relocated）、Matoza 2014 LP（12,290 events）和 Lengliné dike-propagation catalog 均已归档且归属清楚。它们覆盖 summit、全岛、LP、dike 等不同空间角色，不能合并成单一 truth catalog。QuakeFlow 只有论文/代码，没有独立公开 Hawaiʻi event catalog，保持 missing 是正确的。主窗口、台站和波形量仍待冻结。

## Ridgecrest, California — `2019_ridgecrest_california`

Shelly 的正式 BSSA 文章已替换此前 poster，并配套 Data S1（34,115 data rows）与 XML metadata；AWR 长时段目录包含 222,864 条 hypocenter CSV data rows 和 4,890 条 moment-tensor rows；Liu 及 Ross 文献也已在位。Shelly 是短期高分辨率目录，AWR 覆盖 2019-04 至 2023-05，不能直接互换。旧的 download checklist 和窗口/台站/波形 TBD 需要在 benchmark window 冻结后更新。

## Magna, Utah — `2020_magna_utah`

Pang 的约 5,739-event high-resolution event catalog 已完整；Baker 的 `BAKER2021_0220200316__catalog_picks.csv` 有 329,611 条 pick/arrival records，不能误称为 329,611 个独立事件。Baker 正式 SRL 论文仍缺本地 PDF，因此该 reference 保持 partial。Pang/Baker 目标窗口、台站和波形量仍待统计。

## 总体结论

1. canonical 目录结构已经基本正确；catalog README 已补齐 `source_ref`。
2. 仍真正缺少机器可读主目录的 reference 是 Maple Pang 和 Hawaiʻi QuakeFlow；不能用相邻研究目录替代。
3. 仍真正缺文章的是 Magna Baker，应优先补 SRL paper PDF。
4. Tan 目录数据已补到 S10/S11/phase 层，但最终 41,392-event 集和 Movie SI 仍缺。
5. 六个 case 的 v1 benchmark window、事件数、空间/深度/震级规则、网络条件和 waveform upper-bound 已回填到各自 analysis；这些值是当前数据准备阶段的冻结基线。
6. 后续只需在实际波形下载后，用 station-day availability 替换目前按连续 3C/100 Hz/int32 计算的 waveform upper-bound，不应重新改变时间窗和 reference 角色。
