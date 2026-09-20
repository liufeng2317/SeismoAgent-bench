# Phase I Case References

本文件记录 6 个 benchmark case 的参考文献下载状态。当前版本用于断点续传和后续人工核验；只有通过文件头检查的文件才标记为“已下载”。

**Case naming convention:** all case identifiers in tables use the canonical lowercase directory slug `year_region_place` (for example, `2017_maple_creek_yellowstone` and `2018_kilauea_hawaii`). Human-readable place names are provided only in the display-name column.

## Canonical organization

每个来源使用稳定的 `SOURCE_ID` 文件夹：`<case>/references/<SOURCE_ID>/` 只保存论文和 supplement；`<case>/catalogs/<CATALOG_ID>/` 保存 benchmark 核心目录、原始 archive 和 schema。论文、supplement 和 catalog 通过 `source_ref` 绑定。完整规则见 [`data/README.md`](./README.md)。

## 状态概览

| Canonical Case ID | 目录 | 主要参考文献 | 当前状态 |
|---|---|---|---|
| `2019_ridgecrest_california` | [`references`](./2019_ridgecrest_california/references) | Ross et al. (2019); Shelly (2020) | 已下载 2 篇 PDF |
| `2011_prague_oklahoma` | [`references`](./2011_prague_oklahoma/references) | Cochran et al. (2020), DOI [10.1093/gji/ggaa153](https://doi.org/10.1093/gji/ggaa153); McMahon et al. (2017), DOI [10.1002/2017GL072944](https://doi.org/10.1002/2017GL072944); Isken & Mooney (2017), DOI [10.1785/0120160150](https://doi.org/10.1785/0120160150) | Cochran 与 McMahon 两个目录、相关文章和 Isken auxiliary table 已归档 |
| `2020_magna_utah` | [`references`](./2020_magna_utah/references) | Pang et al. (2020), DOI [10.1029/2020GL089798](https://doi.org/10.1029/2020GL089798); Baker et al. (2021), DOI [10.1785/0220200316](https://doi.org/10.1785/0220200316) | Pang paper/catalog 已解析；Pang S1 与 Baker article PDF 仍缺失；Baker pick-level catalog 已下载并校验 |
| `2017_maple_creek_yellowstone` | [`references`](./2017_maple_creek_yellowstone/references) | Shelly & Hardebeck (2019), DOI [10.1029/2018GL081607](https://doi.org/10.1029/2018GL081607) | 核心期刊文章、补充材料和相关开放文章均已下载 |
| `2018_kilauea_hawaii` | [`references`](./2018_kilauea_hawaii/references) | Shelly & Thelen (2019), DOI [10.1029/2019GL085636](https://doi.org/10.1029/2019GL085636); Wei et al. (2022), DOI [10.1029/2021EA001979](https://doi.org/10.1029/2021EA001979) | Matoza、Shelly 和 Wei 的论文、补充材料及主要目录均已本地归档并校验 |
| `2016_kaikoura_new_zealand` | [`references`](./2016_kaikoura_new_zealand/references) | Lanza et al. (2019), DOI [10.1029/2019GL082780](https://doi.org/10.1029/2019GL082780); Tan et al. (2024), DOI [10.1029/2024JB028735](https://doi.org/10.1029/2024JB028735); Chamberlain et al. (2021), DOI [10.1029/2021JB022304](https://doi.org/10.1029/2021JB022304) | Lanza/Tan/Chamberlain source bundles、paper reading 和可用目录审计已开始归档 |

## 已核验文件

- [`ROSS2019_SCIENCE__paper.pdf`](./2019_ridgecrest_california/references/ROSS2019_SCIENCE/paper/ROSS2019_SCIENCE__paper.pdf) — Ross et al. (2019), *Science*, DOI [10.1126/science.aaz0109](https://doi.org/10.1126/science.aaz0109)。
- [`SHELLY2020_0220190309__paper.pdf`](./2019_ridgecrest_california/references/SHELLY2020_0220190309/paper/SHELLY2020_0220190309__paper.pdf) — Shelly (2020), DOI [10.1785/0220190309](https://doi.org/10.1785/0220190309)。
- [`McMahon2017_Prague_Dissertation.pdf`](./2011_prague_oklahoma/references/MCMAHON2017_DISSERTATION/paper/McMahon2017_Prague_Dissertation.pdf) — 与 Prague aftershock sequence 相关的作者学位论文全文。
- [`MapleCreek_Related_OpenArticle.pdf`](./2017_maple_creek_yellowstone/references/MAPLE_RELATED_OPEN/paper/MapleCreek_Related_OpenArticle.pdf) — Maple Creek 相关开放文章版本。
- [`USGS2019_SCIENCE_OVERVIEW__paper.pdf`](./2018_kilauea_hawaii/references/USGS2019_SCIENCE_OVERVIEW/paper/USGS2019_SCIENCE_OVERVIEW__paper.pdf) — USGS 托管的 Kīlauea 2018 eruption and summit collapse Science 概览文章，文件头已验证为 PDF。
- `2011_prague_oklahoma/references` 中已新增 McMahon et al. (2017) 期刊文章，DOI [10.1002/2017GL072944](https://doi.org/10.1002/2017GL072944)。
- `2017_maple_creek_yellowstone/references` 中已新增 Shelly & Hardebeck (2019) 期刊文章及 supplementary information，DOI [10.1029/2018GL081607](https://doi.org/10.1029/2018GL081607)。
- `2020_magna_utah/references` 中已保存 Pang et al. (2020) 核心文章，DOI [10.1029/2020GL089798](https://doi.org/10.1029/2020GL089798)。
- `2016_kaikoura_new_zealand/references/LANZA2019_GL082780/`、`TAN2024_JB028735/` 和 `CHAMBERLAIN2021_JB022304/` 中已保存三篇核心文章，DOI 分别为 [10.1029/2019GL082780](https://doi.org/10.1029/2019GL082780) 和 [10.1029/2024JB028735](https://doi.org/10.1029/2024JB028735)。
- `2016_kaikoura_new_zealand/references/CHAMBERLAIN2021_JB022304/` 已完成论文方法提取；修正版 GrowClust CSV 的窗口统计和 legacy-versus-corrected lineage 审计见 [`CHAMBERLAIN2021_JB022304__catalog_summary.md`](./2016_kaikoura_new_zealand/catalogs/CHAMBERLAIN2021_JB022304/CHAMBERLAIN2021_JB022304__catalog_summary.md)。
- `2016_kaikoura_new_zealand/references/LANZA2019_GL082780/` 已完成论文、SI 和 Data Set S1 QuakeML 审计；QuakeML 的 131.6 MB 本地文件不进入 Git，checksum 与窗口统计见 [`LANZA2019_GL082780__catalog_summary.md`](./2016_kaikoura_new_zealand/catalogs/LANZA2019_GL082780/LANZA2019_GL082780__catalog_summary.md)。

## Per-reference readiness matrix

该矩阵是后续人工复查和补下载的入口。`N/A` 表示该 source 的角色本身不要求对应文件；`missing` 表示应该有但目前没有；`partial` 表示 source 的部分材料已准备好，但 reference/supplement/catalog 三者尚未闭合。每行的 `Review note` 同时记录文章—目录是否对齐、目录实际角色和需要调整的地方。

为便于直接定位本地文件，矩阵中的 Case 简称与实际数据目录对应如下：

| Canonical Case ID | Display name | Actual directory |
|---|---|---|
| `2011_prague_oklahoma` | Prague, Oklahoma | `data/2011_prague_oklahoma/` |
| `2016_kaikoura_new_zealand` | Kaikōura, New Zealand | `data/2016_kaikoura_new_zealand/` |
| `2017_maple_creek_yellowstone` | Maple Creek, Yellowstone | `data/2017_maple_creek_yellowstone/` |
| `2018_kilauea_hawaii` | Kīlauea, Hawaiʻi | `data/2018_kilauea_hawaii/` |
| `2019_ridgecrest_california` | Ridgecrest, California | `data/2019_ridgecrest_california/` |
| `2020_magna_utah` | Magna, Utah | `data/2020_magna_utah/` |

| Canonical Case ID | Source ID | Reference | Supplement | Catalog | Overall | Review note |
|---|---|---:|---:|---:|---|---|
| 2011_prague_oklahoma | `COCHRAN2020_GJIGGAA153` | ✅ [paper](./2011_prague_oklahoma/references/COCHRAN2020_GJIGGAA153/paper/) | ✅ [supplement](./2011_prague_oklahoma/references/COCHRAN2020_GJIGGAA153/supplement/) | ✅ [catalog](./2011_prague_oklahoma/catalogs/COCHRAN2020_GJIGGAA153/) | ✅ ready | Paper, fault products and core catalog are present. |
| 2011_prague_oklahoma | `MCMAHON2017_GL072944` | ✅ [paper](./2011_prague_oklahoma/references/MCMAHON2017_GL072944/paper/) | — | ✅ [catalog](./2011_prague_oklahoma/catalogs/MCMAHON2017_GL072944/) | ✅ ready | Official USGS 5,446-event subspace-detection/relocation catalog and metadata are now staged. Paper/catalog extraction is complete in [`paper_reading`](./2011_prague_oklahoma/references/MCMAHON2017_GL072944/paper/MCMAHON2017_GL072944__paper_reading.md) and [`catalog_summary`](./2011_prague_oklahoma/catalogs/MCMAHON2017_GL072944/MCMAHON2017_GL072944__catalog_summary.md). Use as an independent secondary to Cochran; do not merge event rows. McMahon SI/Table S1–S2 are still missing. |
| 2011_prague_oklahoma | `MCMAHON2017_DISSERTATION` | ✅ [paper](./2011_prague_oklahoma/references/MCMAHON2017_DISSERTATION/paper/) | — | — | ✅ context-ready | Dissertation used as structural context; MinerU parsing failed and no catalog product is expected. |
| 2011_prague_oklahoma | `ISKEN2017_BSSA0120160150` | ✅ [paper](./2011_prague_oklahoma/references/ISKEN2017_BSSA0120160150/paper/) | ✅ [supplement/table](./2011_prague_oklahoma/catalogs/ISKEN2017_BSSA0120160150/) | ✅ [catalog](./2011_prague_oklahoma/catalogs/ISKEN2017_BSSA0120160150/) | ✅ ready | Official BSSA Table S3 downloaded and normalized: 13 relocated aftershocks with hypocenters, errors, RMS and Mw. Paper/catalog extraction is complete in [`paper_reading`](./2011_prague_oklahoma/references/ISKEN2017_BSSA0120160150/paper/ISKEN2017_BSSA0120160150__paper_reading.md) and [`catalog_summary`](./2011_prague_oklahoma/catalogs/ISKEN2017_BSSA0120160150/ISKEN2017_BSSA0120160150__catalog_summary.md). Source: [BSSA supplement](https://www.seismosoc.org/Publications/BSSA_html/bssa_107-2/2016150-esupp/2016150_esupp_Table_S3.html). |
| 2016_kaikoura_new_zealand | `LANZA2019_GL082780` | ✅ [paper](./2016_kaikoura_new_zealand/references/LANZA2019_GL082780/paper/) · [paper_reading](./2016_kaikoura_new_zealand/references/LANZA2019_GL082780/paper/LANZA2019_GL082780__paper_reading.md) | ✅ [supplement](./2016_kaikoura_new_zealand/references/LANZA2019_GL082780/supplement/) · [notes](./2016_kaikoura_new_zealand/references/LANZA2019_GL082780/supplement/LANZA2019_GL082780__supplement_notes.md) | ✅ [catalog](./2016_kaikoura_new_zealand/catalogs/LANZA2019_GL082780/) · [summary](./2016_kaikoura_new_zealand/catalogs/LANZA2019_GL082780/LANZA2019_GL082780__catalog_summary.md) | ✅ ready | Text SI and Table S1 remain under `references/.../supplement/`; Data Set S1 QuakeML is correctly separated under `catalogs/LANZA2019_GL082780/raw/` (local-only, 131.6 MB; SHA-256 `c87a16de4fb28be7cd873b03e93b3d410c6e2237d7ed443affbe798670fbd478`). Audit: 2,655 event objects, 2,012 HypoDD origins, 123 time-only / 122 common-mask rows; magnitude type generic `M`. |
| 2016_kaikoura_new_zealand | `TAN2024_JB028735` | ✅ [paper](./2016_kaikoura_new_zealand/references/TAN2024_JB028735/paper/) · [paper_reading](./2016_kaikoura_new_zealand/references/TAN2024_JB028735/paper/TAN2024_JB028735__paper_reading.md) | ✅ [supplement](./2016_kaikoura_new_zealand/references/TAN2024_JB028735/supplement/) | ✅ [catalog](./2016_kaikoura_new_zealand/catalogs/TAN2024_JB028735/) · [catalog_summary](./2016_kaikoura_new_zealand/catalogs/TAN2024_JB028735/TAN2024_JB028735__catalog_summary.md) | ✅ ready | Benchmark-required SI PDF and Tables S09–S12 are local, with S10/S11 and 1,165 `.dat` phase files (1,172 ZIP entries including metadata) from Zenodo [10.5281/zenodo.10937462](https://doi.org/10.5281/zenodo.10937462). The optional Wiley Movie SI-S01 is not local; the paper's final 41,392-event cluster-filtered set is not separately released, so S11 remains the documented intermediate product. Frozen common-mask counts: S10 9,720; S11 6,955 (6,973 time-only). |
| 2016_kaikoura_new_zealand | `CHAMBERLAIN2021_JB022304` | ✅ [paper](./2016_kaikoura_new_zealand/references/CHAMBERLAIN2021_JB022304/paper/) · [paper_reading](./2016_kaikoura_new_zealand/references/CHAMBERLAIN2021_JB022304/paper/CHAMBERLAIN2021_JB022304__paper_reading.md) | —* | ✅ [catalog](./2016_kaikoura_new_zealand/catalogs/CHAMBERLAIN2021_JB022304/) · [catalog_summary](./2016_kaikoura_new_zealand/catalogs/CHAMBERLAIN2021_JB022304/CHAMBERLAIN2021_JB022304__catalog_summary.md) | ✅ ready | Corrected CSV is canonical (33,328 unique IDs; SHA-256 `6f00695585998c365a81132a60bc3c7ebe058abdd352e8d8d8f802489559137a`). Legacy Zenodo CSV (34,704 rows) is retained for provenance only because it has 1,375 duplicate IDs and one malformed row. Paper reports 27,431 GrowClust relocations; relocation-status subset is not explicitly encoded locally. *The corrected Zenodo code/QuakeML archive is not separately staged; acquire it only if exact relocation membership or focal-mechanism reproduction is required. |
| 2017_maple_creek_yellowstone | `PANG2019_GL082376` | ✅ [paper](./2017_maple_creek_yellowstone/references/PANG2019_GL082376/paper/) | ✅ [supplement](./2017_maple_creek_yellowstone/references/PANG2019_GL082376/supplement/) | ⬜ missing | ◐ partial | **Correction:** the [USGS 2025 correlation-phase release](https://doi.org/10.5066/P13JCJ2I) is the Shelly & Hardebeck product archived under `SHELLY2019_GL081607`, not a Pang catalog. Pang's 3,345-event GrowClust table still has no confirmed public machine-readable release. |
| 2017_maple_creek_yellowstone | `SHELLY2019_GL081607` | ✅ [paper](./2017_maple_creek_yellowstone/references/SHELLY2019_GL081607/paper/) | ✅ [supplement](./2017_maple_creek_yellowstone/references/SHELLY2019_GL081607/supplement/) | ✅ [catalog](./2017_maple_creek_yellowstone/catalogs/SHELLY2019_GL081607/) | ✅ ready | ✅ Article, `source_ref`, CSV and XML are aligned. This is Shelly & Hardebeck's correlation-derived phase-arrival product, not Pang's GrowClust catalog. |
| 2017_maple_creek_yellowstone | `MAPLE_RELATED_OPEN` | ✅ [paper](./2017_maple_creek_yellowstone/references/MAPLE_RELATED_OPEN/paper/) | — | — | ✅ context-ready | Open context article only. |
| 2018_kilauea_hawaii | `LENGLINE2021_EPSL116653` | ✅ [paper](./2018_kilauea_hawaii/references/LENGLINE2021_EPSL116653/paper/) | ✅ [supplement](./2018_kilauea_hawaii/references/LENGLINE2021_EPSL116653/supplement/) | ✅ [catalog](./2018_kilauea_hawaii/catalogs/LENGLINE2021_EPSL116653/) | ✅ ready | Paper/SI and `loc_events.txt` dike-propagation catalog are present. |
| 2018_kilauea_hawaii | `MATOZA2021_EA001253` | ✅ [paper](./2018_kilauea_hawaii/references/MATOZA2021_EA001253/paper/) | — | ✅ [catalog](./2018_kilauea_hawaii/catalogs/MATOZA2021_EA001253/) | ✅ ready | Article PDF and island-wide catalog are present. |
| 2018_kilauea_hawaii | `MATOZA2014_GL059819` | ✅ [paper](./2018_kilauea_hawaii/references/MATOZA2014_GL059819/paper/) | — | ✅ [catalog](./2018_kilauea_hawaii/catalogs/MATOZA2014_GL059819/) | ✅ ready | Article PDF and LP summit catalog are present. |
| 2018_kilauea_hawaii | `USGS2019_SCIENCE_OVERVIEW` | ✅ [paper](./2018_kilauea_hawaii/references/USGS2019_SCIENCE_OVERVIEW/paper/) | — | — | ✅ context-ready | Context paper, not a benchmark catalog. |
| 2018_kilauea_hawaii | `SHELLY2019_GL085636` | ✅ [paper](./2018_kilauea_hawaii/references/SHELLY2019_GL085636/paper/) · [paper_reading](./2018_kilauea_hawaii/references/SHELLY2019_GL085636/paper/SHELLY2019_GL085636__paper_reading.md) | ✅ [supplement](./2018_kilauea_hawaii/references/SHELLY2019_GL085636/supplement/) | ✅ [catalog](./2018_kilauea_hawaii/catalogs/SHELLY2019_GL085636/) · [summary](./2018_kilauea_hawaii/catalogs/SHELLY2019_GL085636/SHELLY2019_GL085636__catalog_summary.md) | ✅ ready | S1=44,188 and S2=43,950 event products are aligned with the article; common summit-mask counts are 1,883/1,877 (time-only 1,902/1,896). The 607.96 MB phase-arrival CSV (8,582,492 rows; SHA-256 `be6bab5bca8dff5355d763495ac2f9a5c54d157f80b0f315095e3d3caf1d8dc4`) is local-only and auxiliary; station-day/run metadata still needs extraction. |
| 2018_kilauea_hawaii | `WEI2022_EA001979` | ✅ [paper](./2018_kilauea_hawaii/references/WEI2022_EA001979/paper/) · [paper_reading](./2018_kilauea_hawaii/references/WEI2022_EA001979/paper/WEI2022_EA001979__paper_reading.md) | ✅ [supplement](./2018_kilauea_hawaii/references/WEI2022_EA001979/supplement/) | ✅ [catalog](./2018_kilauea_hawaii/catalogs/WEI2022_EA001979/) · [summary](./2018_kilauea_hawaii/catalogs/WEI2022_EA001979/WEI2022_EA001979__catalog_summary.md) | ✅ ready | Data Set S1 has 375,736 rows with no explicit event ID; frozen summit mask gives 2,369 rows, of which 1,930 have numeric magnitudes. SI PDF is local but not yet independently text-extracted; Dryad DOI remains the provenance link. |
| 2018_kilauea_hawaii | `QUAKEFLOW_GJI_GGAC355` | ✅ [paper](./2018_kilauea_hawaii/references/QUAKEFLOW_GJI_GGAC355/paper/) | — | ⬜ missing | ◐ partial | Local GJI paper and catalog-evaluation document are archived. The paper/code are public ([GJI DOI](https://doi.org/10.1093/gji/ggac355), [QuakeFlow repo](https://github.com/AI4EPS/QuakeFlow), [Zenodo code DOI](https://doi.org/10.5281/zenodo.7023970)), but no dedicated downloadable Hawaii QuakeFlow event-catalog file/DOI was identified; do not substitute HVO/USGS or other catalogs. |
| 2019_ridgecrest_california | `LIU2020_GL086189` | ✅ [paper](./2019_ridgecrest_california/references/LIU2020_GL086189/paper/) | ✅ [supplement](./2019_ridgecrest_california/references/LIU2020_GL086189/supplement/) | ✅ [catalog](./2019_ridgecrest_california/catalogs/LIU2020_GL086189/) | ✅ ready | Paper, SI and Table S1 are present. |
| 2019_ridgecrest_california | `AWR2025_CALTECHDATA` | ✅ [paper](./2019_ridgecrest_california/references/AWR2025_CALTECHDATA/paper/) | — | ✅ [catalog](./2019_ridgecrest_california/catalogs/AWR2025_CALTECHDATA/) | ✅ ready | Atterholt, Wilding & Ross (2025), DOI [10.1093/gji/ggaf001](https://doi.org/10.1093/gji/ggaf001). Local hypocenter and moment-tensor catalogs are present; provenance: [SCEDC alternate catalog](https://stp2.gps.caltech.edu/data/alt-2025-atterholt.html), [CaltechDATA DOI](https://doi.org/10.22002/5af05-cah73). |
| 2019_ridgecrest_california | `ROSS2019_SCIENCE` | ✅ [paper](./2019_ridgecrest_california/references/ROSS2019_SCIENCE/paper/) | — | ✅ [catalog](./2019_ridgecrest_california/catalogs/ROSS2019_SCIENCE/) | ✅ ready | Article-associated QTM/GrowClust archive downloaded from the official SCEDC page; use SCSN hypocenter for the Mw 7.1 mainshock depth. |
| 2019_ridgecrest_california | `SHELLY2020_0220190309` | ✅ [paper](./2019_ridgecrest_california/references/SHELLY2020_0220190309/paper/) | — | ✅ [catalog](./2019_ridgecrest_california/catalogs/SHELLY2020_0220190309/) | ✅ ready | Correct journal article and article-associated Data S1 hypocenter catalog plus XML metadata are present. The former PDF was a poster and is retained under `context/`; the 2025 USGS correlation-phase CSV remains auxiliary. Official DOI: [10.1785/0220190309](https://doi.org/10.1785/0220190309). |
| 2020_magna_utah | `PANG2020_GL089798` | ✅ [paper](./2020_magna_utah/references/PANG2020_GL089798/paper/) · [paper_reading](./2020_magna_utah/references/PANG2020_GL089798/paper/PANG2020_GL089798__paper_reading.md) | ⬜ missing | ✅ [catalog](./2020_magna_utah/catalogs/PANG2020_GL089798/) · [summary](./2020_magna_utah/catalogs/PANG2020_GL089798/PANG2020_GL089798__catalog_summary.md) | ◐ partial | ISC archive is byte-aligned and audited (5,739 unique event IDs). The article lists Supporting Information S1, but it is not local; the catalog audit records article/local population differences (2,103 vs 2,144 routine; 5,501 vs 3,595 Template-Matching labels; 5,623 relocation count not encoded). |
| 2020_magna_utah | `BAKER2021_0220200316` | ⬜ missing | — | ✅ [catalog](./2020_magna_utah/catalogs/BAKER2021_0220200316/) · [summary](./2020_magna_utah/catalogs/BAKER2021_0220200316/BAKER2021_0220200316__catalog_summary.md) | ◐ partial | Baker article PDF is genuinely missing locally (no project copy found), so no paper_reading note is fabricated. ISC catalog and `source_ref` align: 329,611 pick rows / 5,885 events, SHA-256 `103ff3f3a91b19baf64ae56e1ece5193fa373ca4491819cff77cb3dceab750d1`. Obtain the DOI [10.1785/0220200316](https://doi.org/10.1785/0220200316) PDF before freezing detector/deployment/QC claims. |

## Official operational baseline snapshots

These are Q3 operational exports, not research truth catalogs and not article-linked references. Each case now keeps both a `*_full` acquisition snapshot covering the article/sequence span and a `*_benchmark` snapshot matching the frozen benchmark window. Queries are split into time chunks and de-duplicated by event ID to avoid silent service limits; parameters and download timestamps are recorded in each catalog README.

| Case ID | Provider/source | Local snapshot | Rows |
|---|---|---|---:|
| `2011_prague_oklahoma` | USGS ANSS ComCat / `locationSource=tul` | [`USGS_TUL_COMCAT_2011`](./2011_prague_oklahoma/catalogs/USGS_TUL_COMCAT_2011/) | full 71; benchmark 11 |
| `2016_kaikoura_new_zealand` | GeoNet event service | [`GEONET_2016_KAIKOURA`](./2016_kaikoura_new_zealand/catalogs/GEONET_2016_KAIKOURA/) | full 15,948; benchmark 1,507 |
| `2017_maple_creek_yellowstone` | USGS ANSS ComCat / UUSS-WY source | [`USGS_UUSS_COMCAT_2017`](./2017_maple_creek_yellowstone/catalogs/USGS_UUSS_COMCAT_2017/) | full 9; benchmark 5 |
| `2018_kilauea_hawaii` | USGS ComCat / HVO-HV source | [`USGS_HVO_COMCAT_2018`](./2018_kilauea_hawaii/catalogs/USGS_HVO_COMCAT_2018/) | full 40,095; benchmark 496 |
| `2019_ridgecrest_california` | USGS ANSS ComCat / SCSN-CI source | [`USGS_SCSN_COMCAT_2019`](./2019_ridgecrest_california/catalogs/USGS_SCSN_COMCAT_2019/) | full 17,959; benchmark 6,566 |
| `2020_magna_utah` | USGS ANSS ComCat / UUSS source | [`USGS_UUSS_COMCAT_2020`](./2020_magna_utah/catalogs/USGS_UUSS_COMCAT_2020/) | full 2,078; benchmark 1,432 |

- `2016_kaikoura_new_zealand/catalogs/CHAMBERLAIN2021_JB022304/CHAMBERLAIN2021_JB022304__catalog_growclust_corrected_focal_mechanisms.csv` — canonical corrected product，33,328 个唯一事件；SHA-256 `6f00695585998c365a81132a60bc3c7ebe058abdd352e8d8d8f802489559137a`。Legacy Zenodo CSV 的 SHA-256 为 `b2f7c6e60198b309274051764b564a5a544ae039e45a142e2e31034e0068fc2b`，仅作 provenance 比较。
- `2016_kaikoura_new_zealand/catalogs/LANZA2019_GL082780/raw/grl59060-sup-0003-ds01.xml` — Data Set S1 QuakeML，131.6 MB，本地保留但按 `.gitignore` 不提交；SHA-256 `c87a16de4fb28be7cd873b03e93b3d410c6e2237d7ed443affbe798670fbd478`。
- `2020_magna_utah/catalogs/BAKER2021_0220200316/BAKER2021_0220200316__catalog_picks.csv` — ISC dataset [10.31905/LGR1456Y](https://doi.org/10.31905/LGR1456Y)，329,611 行 records；SHA-256 `103ff3f3a91b19baf64ae56e1ece5193fa373ca4491819cff77cb3dceab750d1`。
- `2020_magna_utah/catalogs/PANG2020_GL089798/PANG2020_GL089798__catalog_primary.txt` — ISC Pang high-resolution catalog [10.31905/9IE6PAF2](https://doi.org/10.31905/9IE6PAF2)，5,739 个唯一事件；SHA-256 `e26957771d2ad607c610fd91d211eac3bb32297d8ec3225fe1d8e9a83d5cb48a`；原始 archive 位于同目录 `raw/`。
- `2020_magna_utah/catalogs/PANG2020_GL089798/PANG2020_GL089798__catalog_summary.md` — strict v1 common-mask audit: 4,162 rows / 4,101 with `Mc > -4`; seven in-window non-canonical timestamp rows are excluded under strict parsing.
- `2020_magna_utah/catalogs/BAKER2021_0220200316/BAKER2021_0220200316__catalog_summary.md` — pick-level audit: 329,611 rows / 5,885 events; frozen common-mask subset 3,712 events / 161,567 picks.
- `2018_kilauea_hawaii/catalogs/MATOZA2021_EA001253/MATOZA2021_EA001253__catalog_islandwide.txt` — Matoza island-wide catalog（347,446 starting / 299,966 relocated events）；原始 ZIP 位于同目录 `raw/`。
- `2018_kilauea_hawaii/catalogs/MATOZA2014_GL059819/MATOZA2014_GL059819__catalog_lp_summit.txt` — Matoza LP summit catalog（12,290 events）；原始 ZIP 位于同目录 `raw/`。
- `2018_kilauea_hawaii/references/LENGLINE2021_EPSL116653/paper/Lengline2021_Kilauea_EPSL.pdf` — author/open repository copy of *Tracking dike propagation leading to the 2018 Kīlauea eruption*, DOI [10.1016/j.epsl.2020.116653](https://doi.org/10.1016/j.epsl.2020.116653); PDF header verified.
- 旧版重复 catalog 和无效代理下载残片已于 2026-09-19 清理；canonical catalog 与 raw archive 均保留在 `catalogs/<CATALOG_ID>/`。Tan Zenodo phase archive 的解压目录仍带有少量 `.DS_Store`/`__MACOSX` 元数据，不参与 catalog 读取，待集中清理。

## 下载说明

- 目录结构已为 6 个 case 建立；论文和 supplement 放入 `references/<SOURCE_ID>/`，核心目录和原始 archive 放入 `catalogs/<CATALOG_ID>/`。
- 目前没有使用无法核验的镜像或疑似错误页面。
- 对返回 HTTP 403 的出版商文件，下一步应通过浏览器会话下载，或寻找作者手稿、机构仓储和正式数据发布页中的可公开版本；下载后需要再次检查文件类型和 DOI 元数据。

## Audit and download notes

前面的 `Per-reference readiness matrix` 已合并原 Online audit additions 的逐条 reference 和本地状态信息；各 source 的角色与 DOI 由 source README、case analysis 和 DOI 链接维护。以下只保留优先级、状态约定和下载日志，避免出现两套相互漂移的状态表。

### Download priority

1. Verify and, if directly available from an authoritative release, acquire the Prague McMahon secondary catalog;
2. Verify whether a machine-readable Pang Maple Creek catalog actually exists before attempting any download;
3. Complete only confirmed Kaikōura source tables and catalog products;
4. Acquire the confirmed Ridgecrest Ross/SCEDC QTM catalog and Baker article PDF;
5. Use confirmed Kīlauea HVO/USGS baseline and Wei/Shelly products; do not label QuakeFlow output without an original release;
6. Keep routine catalogs as baselines only when a stable event-query or data-release export can be frozen and cited.

### Status convention

- `online-verified`: official paper/data page confirmed; local file may still be absent.
- `download-pending`: download URL/DOI identified; file must be acquired and header/metadata checked.
- `catalog-pending`: paper is known, but the actual event table or supplement still needs to be located.
- `local-verified`: file downloaded, file type/DOI/schema checked, and linked from the case analysis.

### Download attempt log

**Attempt date:** 2026-09-19

Using the proxy credentials from the project `.env` via an explicit per-command proxy URL, the Pang ISC Magna catalog, two Matoza Kīlauea products, an open Lengliné paper copy, and the GFZ-public Isken accepted manuscript were downloaded and verified. The Wei Dryad API metadata, Shelly USGS data-release page, and Wiley supporting-file listings were also verified online; their file-stream endpoints returned HTTP 403/anti-bot responses through the proxy, so no HTML error pages were retained as data. This is a historical log of the proxy attempts; current authoritative status is the matrix above.

When a browser/session-based download route is available, prioritize rows marked `⬜ missing` or `◐ partial` in the matrix and run a file-header/DOI/schema check before changing any status to `local-verified`.
