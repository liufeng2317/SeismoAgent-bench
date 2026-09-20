# Phase I six-case data audit

本文件是跨 case 的文件、目录和数据准备审计；逐篇论文的方法提取见各
`references/<SOURCE_ID>/paper/*__paper_reading.md`，逐个目录的字段审计见
`catalogs/<CATALOG_ID>/*__catalog_summary.md`，冻结窗口的解释见各 case 的
`analysis/*_analysis.md`。

## Prague, Oklahoma — `2011_prague_oklahoma`

`COCHRAN2020_GJIGGAA153` 已闭合：本地目录 8,811 行、唯一 ID 8,811，冻结
窗口（2011-11-11T00:00–2011-11-19T00:00 UTC）时间筛选 2,078 行；若使用
显示的四舍五入空间/深度边界则为 2,076 行。全目录震级范围为 −1.36–4.99，
震级类型仍未由 release/SI 确认，不能标成 ML。McMahon 公开 release（5,446
行）和 Isken Table S3（13 个人工重定位事件）作为独立 secondary/structural
reference 保留，不与 Cochran 合并。31 台混合临时/区域台站和实际 station-day
可用性仍待波形阶段确认；25.71264 GB 是 31×3C×100 Hz×int32×8 日的连续上限，
不是已下载体积。

## Kaikōura, New Zealand — `2016_kaikoura_new_zealand`

Lanza、Tan、Chamberlain 的论文、supplement/目录及本地审计均已归档。冻结窗口
（2016-12-01–12-09 UTC）的 common-mask 计数为 Lanza 122、Tan S10 9,720、
Tan S11 6,955（时间-only 6,973）、Chamberlain 2,214；Tan 的 1,165 个 phase
文件也已单独保存。Tan 论文中的最终 41,392-event cluster-filtered 集没有独立
CSV，Wiley Movie SI-S01 仍是可选缺口；Chamberlain CSV 没有明确 relocation
membership 标志。46 个 GeoNet/STREWN 台站和 33.5 GB 连续上限已作为设计条件
记录，实际 station-day/channel 可用性尚未冻结。

## Maple Creek, Yellowstone — `2017_maple_creek_yellowstone`

Shelly & Hardebeck 论文、SI、USGS correlation-phase release 和官方 UUSS baseline
均已归档。8 天冻结窗口（2017-06-11–06-19 UTC）含 23,660 个 phase-associated
IDs；旧的 7 天口径为 22,858。该 CSV/XML 没有 origin time、坐标或 event-level
uncertainty，不能当作 15,912/30,411 个文章事件表。冻结阶段观测到 27 个
network-station pairs，19.6 GB 仅为连续数据设计上限。Pang 的真实 3,345-event
HYPOINVERSE+GrowClust 论文已解析，但机器可读 event table 仍未找到，不能用
Shelly release 代替。

## Kīlauea, Hawaiʻi — `2018_kilauea_hawaii`

Shelly S1/S2、Wei S1、Matoza 2021、Matoza 2014 和 Lengliné 产品均已按来源
分开归档。冻结 summit window（2018-05-01–05-09 UTC；19.30–19.50°N、
−155.40–−155.15°、0–20 km）中，Shelly S1/S2 为 1,883/1,877 common-mask
（time-only 1,902/1,896），Wei 为 2,369 行（其中 1,930 个数值震级）。Matoza
2021 的字段定义必须保留：`latR/lonR/depR`（relocated 坐标）掩膜为 1,130 行、
其中 984 行 `nbranch>1`；`latC/lonC/depC`（starting 坐标）掩膜为 1,190 行、
其中 1,044 行 `nbranch>1`。Lengliné 有 6,049 行时间重叠但只有相对 x/y，
Matoza 2014 为历史 LP 目录且窗口为 0 行。QuakeFlow 只有论文/评估材料和代码，
没有可核验的 Hawaiʻi event-catalog release。HVO 临时台阵的 station-day/channel
inventory 和实际波形体积仍待冻结。

## Ridgecrest, California — `2019_ridgecrest_california`

Shelly Data S1（34,091 行）、Liu Table S1（15,445）、Ross SCEDC QTM
（111,918，其中 46,512 个 `nbranch>1`）和 AWR v2（222,864 hypocenters、
4,890 MT）均已完成 paper/catalog 对齐审计；USGS/SCSN 作为 Q3 baseline 也已
保存。冻结 72 小时窗口（2019-07-04–07-07 UTC；35.45–36.05°N、
−117.90–−117.20°、0–20 km）的 common-mask 计数分别为 Shelly 7,716、Liu
6,242、Ross 12,768（其中 6,463 relocated）、AWR 5,737 hypo/254 MT、SCSN
6,566。不同产品使用不同检测和台站条件，不能按事件数排序；Shelly 论文没有固定
station count，Liu 报告 41 permanent+4 temporary，AWR 使用 66 broadband
3C。Ross Science DC1 仍缺，station-day/channel manifest 和 28.3 GB 连续上限
的实际下载量待补。

## Magna, Utah — `2020_magna_utah`

Pang ISC event catalog（5,739 行/唯一 ID）和 Baker ISC pick release（329,611
pick rows、5,885 个事件）均已完成字段审计。冻结 8 天窗口（2020-03-18–03-26
UTC）的 Pang 严格解析为 4,163 time-only / 4,162 common-mask，其中
`Mc>-4` 分别为 4,102/4,101；Baker 为 3,782/3,712 个事件，对应 164,276/
161,567 picks。Pang 的 39 台/226 channel 条件和 Baker 的 180-node 条件必须
分开；62.5 GB Pang channel 上限和 Baker 的 provisional nodal 上限不是实测
波形量。Pang S1 supplement 与 Baker article PDF 仍缺，故 Baker 维持 partial。

## 总体结论

1. 六个 case 的 canonical 目录结构、paper reading、catalog summary 和
   `analysis/` 冻结记录已经互相对齐；数字以各 case analysis 为准。
2. 仍真正缺少机器可读主目录的是 Maple Pang 和 Hawaiʻi QuakeFlow；不能用相邻
   研究目录替代。
3. 仍缺文章 PDF 的是 Magna Baker；Pang S1、Ross DC1、Tan Movie SI 和部分
   station metadata 是可选/复现级缺口，不应伪造为已下载。
4. 当前 waveform 数字都是可复算的连续数据 upper bound。实际下载前必须生成
   station-day/channel availability、采样率、缺口和 checksum manifest；这不会
   改变已冻结的时间窗或 reference 角色。
