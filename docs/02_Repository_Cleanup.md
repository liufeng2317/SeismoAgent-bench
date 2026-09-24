# Repository cleanup — 2026-09-24

本轮目标：减少前期整理产生的重复入口和可丢弃副本，同时保留科学证据、原始数据、运行入口和工作区中已有的未提交工作。操作基于当前工作区，没有重置 Git、重跑目录处理或改动科学筛选参数。

## 必要性判断与处理

| 文件类型 | 判断 | 本次处理 |
|---|---|---|
| 原始论文、补充材料、科学数据发布包、canonical catalog | 必须保留，支持来源追溯和复现 | 保留；两份完全相同的 S10/S11 supplement 表改成指向 canonical catalog 的相对符号链接 |
| 阅读笔记、extraction JSON、schema | 分别承担人工解释、机器记录和格式约束，不能相互替代 | 保留；更新迁移后的证据路径，科学字段不变 |
| MinerU full.md、页码/model/content JSON、图片 | 支持页码证据、图片引用及 Markdown 重新同步 | 保留；修复 5 份补充材料 sidecar 的 51 处原有图片路径错误 |
| MinerU 输出目录中的同字节源 PDF | 冗余副本 | SHA-256 核对后删除，原始 paper/supplement PDF 保留 |
| MinerU 传输 ZIP | 与已展开输出重复 | ZIP 内每个文件与解压文件逐项校验后删除；原始科研发布 ZIP 不在清理范围 |
| catalog README 与独立 catalog summary | 同一产品存在多个手工维护入口 | 25 份 summary 并入 catalog README；generated analysis 继续单独保留 |
| README_legacy.txt | 有独特的作者字段说明，内容不可丢弃 | 4 份原文（仅去除行末空白）完整嵌入 catalog README 的 Original release notes，删除独立副本 |
| case processing index | 与 case analysis、catalog audit 重复，且部分窗口相互冲突 | 6 份索引的案例专属处理说明并入 case analysis；通用规则集中到 data/README.md；重复数值表使用 catalog 审查入口 |
| 全局重复状态表/备份规则 | 重复维护容易漂移 | 备份规则并入 data/README.md；删除重复跨案例审查文件，精简 registry 和 reference manifest |
| 硬编码 extraction 创建脚本、已完成的一次性迁移 | 内容已在经过后续修订的 JSON 中；重跑会覆盖修订 | 删除 6 个历史脚本；保留可复用质量归一化与链接维护工具 |
| 单条与批量 extraction 校验 | 大量重复；旧单条校验器实际仅适用于 TAN | 合并为 validate_all_extractions.py，同时支持单文件与批量调用，并保留 TAN 产品边界检查 |
| __pycache__、.DS_Store、__MACOSX | 非科学产物，可重新生成或无用途 | 删除 |
| legacy/corrected catalog、不同 origin、不同 mask、v1/v2 图件 | 可能表达不同科学含义，不能仅凭相似名称删除 | 保留；清理不替代科学筛选或版本决策 |

## 统一后的入口

- [项目说明](../README.md)：目的、阶段与运行入口。
- [案例注册表](01_1_Case_details.md)：案例角色与 case analysis 导航，不再复制完整窗口数值表。
- [文献清单](../data/REFERENCES_MANIFEST.md)：文献与补充材料可用性、未解决问题及 extraction 导航。
- [目录清单](../data/CATALOGS_MANIFEST.md)：由 full-product JSON 生成的单位明确的统计。
- [数据组织规则](../data/README.md)：保留策略、命名、备份和处理产物规则。
- `data/<case>/catalogs/<catalog>/README.md`：人工维护的来源、字段、质量、原文说明。
- `data/<case>/catalogs/<catalog>/analysis/catalog_analysis.md`：脚本生成的处理报告。

目录清单生成器同步修复：读取 selection/product 元数据，覆盖 `event_full_v1.json` 等不同命名；不再把 phase 行数写到事件列，不按最大行数推断主参考；保留不同产品/版本的独立行。`ready` 只表示存在非空完整事件或原生相对事件统计，不等于科学评测就绪。

六个 processing.yaml 原本都声明 `not_frozen`。入口文档按这个状态解释已有窗口统计；案例和目录审查中的历史“frozen”数值保留，并标记为探索性历史。本轮未重新选择正式时间、空间、深度范围。

## 清理规模

工作区文件由 2,663 个降至 2,517 个，净减少 146 个；净释放约 377 MB（约 360 MiB），不计 `.git` 与 `.env`。

下表是被删除或替换的原文件字节数；合并进 README 的文本不应计作同等净空间节省。主要空间收益来自 PDF 副本、MinerU 传输 ZIP 和重复 XLSX 载荷。统计不包括 `.git` 历史对象，也未读取或修改 `.env`。

| 处理原因 | 文件数 | 原字节数 |
|---|---:|---:|
| 已逐项核验的 MinerU ZIP | 28 | 198,184,023 |
| Python 缓存及 OS 元数据 | 49 | 1,125,311 |
| 备份策略合并 | 1 | 1,217 |
| MinerU 中的同字节 PDF 副本 | 28 | 167,737,826 |
| 案例索引合并 | 6 | 25,315 |
| 目录摘要合并 | 25 | 117,455 |
| 一次性创建/迁移脚本 | 6 | 101,148 |
| 重复 XLSX 替换为相对链接 | 2 | 10,019,525 |
| 重复跨案例审查 | 1 | 6,502 |
| 重复校验器合并 | 1 | 3,441 |
| 原始发布说明合并 | 4 | 8,885 |

## 合并与删除清单

下列路径为操作前路径；合并项给出保留内容的入口。缓存/OS 文件按类型统计，不另建逐文件清单。可丢弃传输包与重复 PDF 的列表用于区分它们和保留的原始科研归档。

### 已逐项核验的 MinerU ZIP

- `data/2011_prague_oklahoma/references/ISKEN2017_BSSA0120160150/parsed/paper/mineru/ISKEN2017_BSSA0120160150__paper.zip`
- `data/2011_prague_oklahoma/references/COCHRAN2020_GJIGGAA153/parsed/paper/mineru/COCHRAN2020_GJIGGAA153__paper.zip`
- `data/2011_prague_oklahoma/references/MCMAHON2017_GL072944/parsed/paper/mineru/MCMAHON2017_GL072944__paper.zip`
- `data/2016_kaikoura_new_zealand/references/CHAMBERLAIN2021_JB022304/parsed/paper/mineru/CHAMBERLAIN2021_JB022304__paper.zip`
- `data/2016_kaikoura_new_zealand/references/LANZA2019_GL082780/parsed/paper/mineru/LANZA2019_GL082780__paper.zip`
- `data/2016_kaikoura_new_zealand/references/TAN2024_JB028735/parsed/paper/mineru/TAN2024_JB028735__paper.zip`
- `data/2016_kaikoura_new_zealand/references/TAN2024_JB028735/parsed/supplement/mineru/2024jb028735-sup-0001-supporting information si-s01.zip`
- `data/2018_kilauea_hawaii/references/SHELLY2019_GL085636/parsed/paper/mineru/SHELLY2019_GL085636__paper.zip`
- `data/2018_kilauea_hawaii/references/SHELLY2019_GL085636/parsed/supplement/mineru/Shelly2019_Kilauea_Figure_SI.zip`
- `data/2018_kilauea_hawaii/references/USGS2019_SCIENCE_OVERVIEW/parsed/paper/mineru/USGS2019_SCIENCE_OVERVIEW__paper.zip`
- `data/2018_kilauea_hawaii/references/WEI2022_EA001979/parsed/paper/mineru/WEI2022_EA001979__paper.zip`
- `data/2018_kilauea_hawaii/references/WEI2022_EA001979/parsed/supplement/mineru/Wei2022_Kilauea_SI.zip`
- `data/2018_kilauea_hawaii/references/LENGLINE2021_EPSL116653/parsed/paper/mineru/LENGLINE2021_EPSL116653__paper.zip`
- `data/2018_kilauea_hawaii/references/LENGLINE2021_EPSL116653/parsed/supplement/mineru/1-s2.0-S0012821X20305975-mmc2.zip`
- `data/2018_kilauea_hawaii/references/MATOZA2021_EA001253/parsed/paper/mineru/MATOZA2021_EA001253__paper.zip`
- `data/2018_kilauea_hawaii/references/MATOZA2014_GL059819/parsed/paper/mineru/MATOZA2014_GL059819__paper.zip`
- `data/2018_kilauea_hawaii/references/QUAKEFLOW_GJI_GGAC355/parsed/paper/mineru/QUAKEFLOW_GJI_GGAC355__evaluation.zip`
- `data/2018_kilauea_hawaii/references/QUAKEFLOW_GJI_GGAC355/parsed/paper/mineru/QUAKEFLOW_GJI_GGAC355__paper.zip`
- `data/2017_maple_creek_yellowstone/references/PANG2019_GL082376/parsed/paper/mineru/PANG2019_GL082376__paper.zip`
- `data/2017_maple_creek_yellowstone/references/PANG2019_GL082376/parsed/supplement/mineru/Pang2019_MapleCreek_SI.zip`
- `data/2017_maple_creek_yellowstone/references/SHELLY2019_GL081607/parsed/paper/mineru/SHELLY2019_GL081607__paper.zip`
- `data/2017_maple_creek_yellowstone/references/SHELLY2019_GL081607/parsed/supplement/mineru/Shelly2019_MapleCreek_SI.zip`
- `data/2017_maple_creek_yellowstone/references/MAPLE_RELATED_OPEN/parsed/paper/mineru/MAPLE_RELATED_OPEN__paper.zip`
- `data/2019_ridgecrest_california/references/LIU2020_GL086189/parsed/paper/mineru/LIU2020_GL086189__paper.zip`
- `data/2019_ridgecrest_california/references/ROSS2019_SCIENCE/parsed/paper/mineru/ROSS2019_SCIENCE__paper.zip`
- `data/2019_ridgecrest_california/references/SHELLY2020_0220190309/parsed/paper/mineru/SHELLY2020_0220190309__paper.zip`
- `data/2019_ridgecrest_california/references/AWR2025_CALTECHDATA/parsed/paper/mineru/AWR2025_CALTECHDATA__paper.zip`
- `data/2020_magna_utah/references/PANG2020_GL089798/parsed/paper/mineru/PANG2020_GL089798__paper.zip`

### 备份策略合并

- `data/REMOTE_BACKUP_POLICY.md` → [保留位置](../data/README.md)

### MinerU 中的同字节 PDF 副本

- `data/2011_prague_oklahoma/references/ISKEN2017_BSSA0120160150/parsed/paper/mineru/ISKEN2017_BSSA0120160150__paper/ISKEN2017_BSSA0120160150__paper.pdf` → [保留位置](../data/2011_prague_oklahoma/references/ISKEN2017_BSSA0120160150/paper/ISKEN2017_BSSA0120160150__paper.pdf)
- `data/2011_prague_oklahoma/references/COCHRAN2020_GJIGGAA153/parsed/paper/mineru/COCHRAN2020_GJIGGAA153__paper/COCHRAN2020_GJIGGAA153__paper.pdf` → [保留位置](../data/2011_prague_oklahoma/references/COCHRAN2020_GJIGGAA153/paper/COCHRAN2020_GJIGGAA153__paper.pdf)
- `data/2011_prague_oklahoma/references/MCMAHON2017_GL072944/parsed/paper/mineru/MCMAHON2017_GL072944__paper/MCMAHON2017_GL072944__paper.pdf` → [保留位置](../data/2011_prague_oklahoma/references/MCMAHON2017_GL072944/paper/MCMAHON2017_GL072944__paper.pdf)
- `data/2016_kaikoura_new_zealand/references/CHAMBERLAIN2021_JB022304/parsed/paper/mineru/CHAMBERLAIN2021_JB022304__paper/CHAMBERLAIN2021_JB022304__paper.pdf` → [保留位置](../data/2016_kaikoura_new_zealand/references/CHAMBERLAIN2021_JB022304/paper/CHAMBERLAIN2021_JB022304__paper.pdf)
- `data/2016_kaikoura_new_zealand/references/LANZA2019_GL082780/parsed/paper/mineru/LANZA2019_GL082780__paper/LANZA2019_GL082780__paper.pdf` → [保留位置](../data/2016_kaikoura_new_zealand/references/LANZA2019_GL082780/paper/LANZA2019_GL082780__paper.pdf)
- `data/2016_kaikoura_new_zealand/references/TAN2024_JB028735/parsed/paper/mineru/TAN2024_JB028735__paper/TAN2024_JB028735__paper.pdf` → [保留位置](../data/2016_kaikoura_new_zealand/references/TAN2024_JB028735/paper/TAN2024_JB028735__paper.pdf)
- `data/2016_kaikoura_new_zealand/references/TAN2024_JB028735/parsed/supplement/mineru/2024jb028735-sup-0001-supporting information si-s01/2024jb028735-sup-0001-supporting information si-s01.pdf` → [保留位置](../data/2016_kaikoura_new_zealand/references/TAN2024_JB028735/supplement/2024jb028735-sup-0001-supporting%20information%20si-s01.pdf)
- `data/2018_kilauea_hawaii/references/SHELLY2019_GL085636/parsed/paper/mineru/SHELLY2019_GL085636__paper/SHELLY2019_GL085636__paper.pdf` → [保留位置](../data/2018_kilauea_hawaii/references/SHELLY2019_GL085636/paper/SHELLY2019_GL085636__paper.pdf)
- `data/2018_kilauea_hawaii/references/SHELLY2019_GL085636/parsed/supplement/mineru/Shelly2019_Kilauea_Figure_SI/Shelly2019_Kilauea_Figure_SI.pdf` → [保留位置](../data/2018_kilauea_hawaii/references/SHELLY2019_GL085636/supplement/Shelly2019_Kilauea_Figure_SI.pdf)
- `data/2018_kilauea_hawaii/references/USGS2019_SCIENCE_OVERVIEW/parsed/paper/mineru/USGS2019_SCIENCE_OVERVIEW__paper/USGS2019_SCIENCE_OVERVIEW__paper.pdf` → [保留位置](../data/2018_kilauea_hawaii/references/USGS2019_SCIENCE_OVERVIEW/paper/USGS2019_SCIENCE_OVERVIEW__paper.pdf)
- `data/2018_kilauea_hawaii/references/WEI2022_EA001979/parsed/supplement/mineru/Wei2022_Kilauea_SI/Wei2022_Kilauea_SI.pdf` → [保留位置](../data/2018_kilauea_hawaii/references/WEI2022_EA001979/supplement/Wei2022_Kilauea_SI.pdf)
- `data/2018_kilauea_hawaii/references/WEI2022_EA001979/parsed/paper/mineru/WEI2022_EA001979__paper/WEI2022_EA001979__paper.pdf` → [保留位置](../data/2018_kilauea_hawaii/references/WEI2022_EA001979/paper/WEI2022_EA001979__paper.pdf)
- `data/2018_kilauea_hawaii/references/LENGLINE2021_EPSL116653/parsed/paper/mineru/LENGLINE2021_EPSL116653__paper/LENGLINE2021_EPSL116653__paper.pdf` → [保留位置](../data/2018_kilauea_hawaii/references/LENGLINE2021_EPSL116653/paper/LENGLINE2021_EPSL116653__paper.pdf)
- `data/2018_kilauea_hawaii/references/LENGLINE2021_EPSL116653/parsed/supplement/mineru/1-s2.0-S0012821X20305975-mmc2/1-s2.0-S0012821X20305975-mmc2.pdf` → [保留位置](../data/2018_kilauea_hawaii/references/LENGLINE2021_EPSL116653/supplement/1-s2.0-S0012821X20305975-mmc2.pdf)
- `data/2018_kilauea_hawaii/references/MATOZA2021_EA001253/parsed/paper/mineru/MATOZA2021_EA001253__paper/MATOZA2021_EA001253__paper.pdf` → [保留位置](../data/2018_kilauea_hawaii/references/MATOZA2021_EA001253/paper/MATOZA2021_EA001253__paper.pdf)
- `data/2018_kilauea_hawaii/references/MATOZA2014_GL059819/parsed/paper/mineru/MATOZA2014_GL059819__paper/MATOZA2014_GL059819__paper.pdf` → [保留位置](../data/2018_kilauea_hawaii/references/MATOZA2014_GL059819/paper/MATOZA2014_GL059819__paper.pdf)
- `data/2018_kilauea_hawaii/references/QUAKEFLOW_GJI_GGAC355/parsed/paper/mineru/QUAKEFLOW_GJI_GGAC355__paper/QUAKEFLOW_GJI_GGAC355__paper.pdf` → [保留位置](../data/2018_kilauea_hawaii/references/QUAKEFLOW_GJI_GGAC355/paper/QUAKEFLOW_GJI_GGAC355__paper.pdf)
- `data/2018_kilauea_hawaii/references/QUAKEFLOW_GJI_GGAC355/parsed/paper/mineru/QUAKEFLOW_GJI_GGAC355__evaluation/QUAKEFLOW_GJI_GGAC355__evaluation.pdf` → [保留位置](../data/2018_kilauea_hawaii/references/QUAKEFLOW_GJI_GGAC355/paper/QUAKEFLOW_GJI_GGAC355__evaluation.pdf)
- `data/2017_maple_creek_yellowstone/references/PANG2019_GL082376/parsed/paper/mineru/PANG2019_GL082376__paper/PANG2019_GL082376__paper.pdf` → [保留位置](../data/2017_maple_creek_yellowstone/references/PANG2019_GL082376/paper/PANG2019_GL082376__paper.pdf)
- `data/2017_maple_creek_yellowstone/references/PANG2019_GL082376/parsed/supplement/mineru/Pang2019_MapleCreek_SI/Pang2019_MapleCreek_SI.pdf` → [保留位置](../data/2017_maple_creek_yellowstone/references/PANG2019_GL082376/supplement/Pang2019_MapleCreek_SI.pdf)
- `data/2017_maple_creek_yellowstone/references/SHELLY2019_GL081607/parsed/paper/mineru/SHELLY2019_GL081607__paper/SHELLY2019_GL081607__paper.pdf` → [保留位置](../data/2017_maple_creek_yellowstone/references/SHELLY2019_GL081607/paper/SHELLY2019_GL081607__paper.pdf)
- `data/2017_maple_creek_yellowstone/references/SHELLY2019_GL081607/parsed/supplement/mineru/Shelly2019_MapleCreek_SI/Shelly2019_MapleCreek_SI.pdf` → [保留位置](../data/2017_maple_creek_yellowstone/references/SHELLY2019_GL081607/supplement/Shelly2019_MapleCreek_SI.pdf)
- `data/2017_maple_creek_yellowstone/references/MAPLE_RELATED_OPEN/parsed/paper/mineru/MAPLE_RELATED_OPEN__paper/MAPLE_RELATED_OPEN__paper.pdf` → [保留位置](../data/2017_maple_creek_yellowstone/references/MAPLE_RELATED_OPEN/paper/MAPLE_RELATED_OPEN__paper.pdf)
- `data/2019_ridgecrest_california/references/LIU2020_GL086189/parsed/paper/mineru/LIU2020_GL086189__paper/LIU2020_GL086189__paper.pdf` → [保留位置](../data/2019_ridgecrest_california/references/LIU2020_GL086189/paper/LIU2020_GL086189__paper.pdf)
- `data/2019_ridgecrest_california/references/ROSS2019_SCIENCE/parsed/paper/mineru/ROSS2019_SCIENCE__paper/ROSS2019_SCIENCE__paper.pdf` → [保留位置](../data/2019_ridgecrest_california/references/ROSS2019_SCIENCE/paper/ROSS2019_SCIENCE__paper.pdf)
- `data/2019_ridgecrest_california/references/SHELLY2020_0220190309/parsed/paper/mineru/SHELLY2020_0220190309__paper/SHELLY2020_0220190309__paper.pdf` → [保留位置](../data/2019_ridgecrest_california/references/SHELLY2020_0220190309/paper/SHELLY2020_0220190309__paper.pdf)
- `data/2019_ridgecrest_california/references/AWR2025_CALTECHDATA/parsed/paper/mineru/AWR2025_CALTECHDATA__paper/AWR2025_CALTECHDATA__paper.pdf` → [保留位置](../data/2019_ridgecrest_california/references/AWR2025_CALTECHDATA/paper/AWR2025_CALTECHDATA__paper.pdf)
- `data/2020_magna_utah/references/PANG2020_GL089798/parsed/paper/mineru/PANG2020_GL089798__paper/PANG2020_GL089798__paper.pdf` → [保留位置](../data/2020_magna_utah/references/PANG2020_GL089798/paper/PANG2020_GL089798__paper.pdf)

### 案例索引合并

- `data/2011_prague_oklahoma/analysis/catalog_processing_index.md` → [保留位置](../data/2011_prague_oklahoma/analysis/PRAGUE2011_analysis.md)
- `data/2016_kaikoura_new_zealand/analysis/catalog_processing_index.md` → [保留位置](../data/2016_kaikoura_new_zealand/analysis/KAIKOURA2016_analysis.md)
- `data/2017_maple_creek_yellowstone/analysis/catalog_processing_index.md` → [保留位置](../data/2017_maple_creek_yellowstone/analysis/MAPLE2017_analysis.md)
- `data/2018_kilauea_hawaii/analysis/catalog_processing_index.md` → [保留位置](../data/2018_kilauea_hawaii/analysis/KILAUEA2018_analysis.md)
- `data/2019_ridgecrest_california/analysis/catalog_processing_index.md` → [保留位置](../data/2019_ridgecrest_california/analysis/RIDGE2019_analysis.md)
- `data/2020_magna_utah/analysis/catalog_processing_index.md` → [保留位置](../data/2020_magna_utah/analysis/MAGNA2020_analysis.md)

### 目录摘要合并

- `data/2011_prague_oklahoma/catalogs/COCHRAN2020_GJIGGAA153/COCHRAN2020_GJIGGAA153__catalog_summary.md` → [保留位置](../data/2011_prague_oklahoma/catalogs/COCHRAN2020_GJIGGAA153/README.md)
- `data/2011_prague_oklahoma/catalogs/ISKEN2017_BSSA0120160150/ISKEN2017_BSSA0120160150__catalog_summary.md` → [保留位置](../data/2011_prague_oklahoma/catalogs/ISKEN2017_BSSA0120160150/README.md)
- `data/2011_prague_oklahoma/catalogs/MCMAHON2017_GL072944/MCMAHON2017_GL072944__catalog_summary.md` → [保留位置](../data/2011_prague_oklahoma/catalogs/MCMAHON2017_GL072944/README.md)
- `data/2011_prague_oklahoma/catalogs/USGS_TUL_COMCAT_2011/USGS_TUL_COMCAT_2011__catalog_summary.md` → [保留位置](../data/2011_prague_oklahoma/catalogs/USGS_TUL_COMCAT_2011/README.md)
- `data/2016_kaikoura_new_zealand/catalogs/CHAMBERLAIN2021_JB022304/CHAMBERLAIN2021_JB022304__catalog_summary.md` → [保留位置](../data/2016_kaikoura_new_zealand/catalogs/CHAMBERLAIN2021_JB022304/README.md)
- `data/2016_kaikoura_new_zealand/catalogs/GEONET_2016_KAIKOURA/GEONET_2016_KAIKOURA__catalog_summary.md` → [保留位置](../data/2016_kaikoura_new_zealand/catalogs/GEONET_2016_KAIKOURA/README.md)
- `data/2016_kaikoura_new_zealand/catalogs/LANZA2019_GL082780/LANZA2019_GL082780__catalog_summary.md` → [保留位置](../data/2016_kaikoura_new_zealand/catalogs/LANZA2019_GL082780/README.md)
- `data/2016_kaikoura_new_zealand/catalogs/TAN2024_JB028735/TAN2024_JB028735__catalog_summary.md` → [保留位置](../data/2016_kaikoura_new_zealand/catalogs/TAN2024_JB028735/README.md)
- `data/2017_maple_creek_yellowstone/catalogs/PANG2019_GL082376/PANG2019_GL082376__catalog_summary.md` → [保留位置](../data/2017_maple_creek_yellowstone/catalogs/PANG2019_GL082376/README.md)
- `data/2017_maple_creek_yellowstone/catalogs/SHELLY2019_GL081607/SHELLY2019_GL081607__catalog_summary.md` → [保留位置](../data/2017_maple_creek_yellowstone/catalogs/SHELLY2019_GL081607/README.md)
- `data/2017_maple_creek_yellowstone/catalogs/USGS_UUSS_COMCAT_2017/USGS_UUSS_COMCAT_2017__catalog_summary.md` → [保留位置](../data/2017_maple_creek_yellowstone/catalogs/USGS_UUSS_COMCAT_2017/README.md)
- `data/2018_kilauea_hawaii/catalogs/LENGLINE2021_EPSL116653/LENGLINE2021_EPSL116653__catalog_summary.md` → [保留位置](../data/2018_kilauea_hawaii/catalogs/LENGLINE2021_EPSL116653/README.md)
- `data/2018_kilauea_hawaii/catalogs/MATOZA2014_GL059819/MATOZA2014_GL059819__catalog_summary.md` → [保留位置](../data/2018_kilauea_hawaii/catalogs/MATOZA2014_GL059819/README.md)
- `data/2018_kilauea_hawaii/catalogs/MATOZA2021_EA001253/MATOZA2021_EA001253__catalog_summary.md` → [保留位置](../data/2018_kilauea_hawaii/catalogs/MATOZA2021_EA001253/README.md)
- `data/2018_kilauea_hawaii/catalogs/SHELLY2019_GL085636/SHELLY2019_GL085636__catalog_summary.md` → [保留位置](../data/2018_kilauea_hawaii/catalogs/SHELLY2019_GL085636/README.md)
- `data/2018_kilauea_hawaii/catalogs/USGS_HVO_COMCAT_2018/USGS_HVO_COMCAT_2018__catalog_summary.md` → [保留位置](../data/2018_kilauea_hawaii/catalogs/USGS_HVO_COMCAT_2018/README.md)
- `data/2018_kilauea_hawaii/catalogs/WEI2022_EA001979/WEI2022_EA001979__catalog_summary.md` → [保留位置](../data/2018_kilauea_hawaii/catalogs/WEI2022_EA001979/README.md)
- `data/2019_ridgecrest_california/catalogs/AWR2025_CALTECHDATA/AWR2025_CALTECHDATA__catalog_summary.md` → [保留位置](../data/2019_ridgecrest_california/catalogs/AWR2025_CALTECHDATA/README.md)
- `data/2019_ridgecrest_california/catalogs/LIU2020_GL086189/LIU2020_GL086189__catalog_summary.md` → [保留位置](../data/2019_ridgecrest_california/catalogs/LIU2020_GL086189/README.md)
- `data/2019_ridgecrest_california/catalogs/ROSS2019_SCIENCE/ROSS2019_SCIENCE__catalog_summary.md` → [保留位置](../data/2019_ridgecrest_california/catalogs/ROSS2019_SCIENCE/README.md)
- `data/2019_ridgecrest_california/catalogs/SHELLY2020_0220190309/SHELLY2020_0220190309__catalog_summary.md` → [保留位置](../data/2019_ridgecrest_california/catalogs/SHELLY2020_0220190309/README.md)
- `data/2019_ridgecrest_california/catalogs/USGS_SCSN_COMCAT_2019/USGS_SCSN_COMCAT_2019__catalog_summary.md` → [保留位置](../data/2019_ridgecrest_california/catalogs/USGS_SCSN_COMCAT_2019/README.md)
- `data/2020_magna_utah/catalogs/BAKER2021_0220200316/BAKER2021_0220200316__catalog_summary.md` → [保留位置](../data/2020_magna_utah/catalogs/BAKER2021_0220200316/README.md)
- `data/2020_magna_utah/catalogs/PANG2020_GL089798/PANG2020_GL089798__catalog_summary.md` → [保留位置](../data/2020_magna_utah/catalogs/PANG2020_GL089798/README.md)
- `data/2020_magna_utah/catalogs/USGS_UUSS_COMCAT_2020/USGS_UUSS_COMCAT_2020__catalog_summary.md` → [保留位置](../data/2020_magna_utah/catalogs/USGS_UUSS_COMCAT_2020/README.md)

### 一次性创建/迁移脚本

- `scripts/03_information_extraction/create_context_extractions.py`
- `scripts/03_information_extraction/create_kilauea_magna_extractions.py`
- `scripts/03_information_extraction/create_quakeflow_context.py`
- `scripts/03_information_extraction/create_remaining_extractions.py`
- `scripts/03_information_extraction/normalize_tan2024_extraction.py`
- `scripts/03_information_extraction/normalize_extraction_records.py`

### 重复 XLSX 替换为相对链接

- `data/2016_kaikoura_new_zealand/references/TAN2024_JB028735/supplement/2024jb028735-sup-0003-table si-s10.xlsx` → [保留位置](../data/2016_kaikoura_new_zealand/catalogs/TAN2024_JB028735/TAN2024_JB028735__catalog_sugar_S10.xlsx)
- `data/2016_kaikoura_new_zealand/references/TAN2024_JB028735/supplement/2024jb028735-sup-0004-table si-s11.xlsx` → [保留位置](../data/2016_kaikoura_new_zealand/catalogs/TAN2024_JB028735/TAN2024_JB028735__catalog_sugar_relocated_S11.xlsx)

### 重复跨案例审查

- `docs/01_2_Case_Data_Audit.md` → [保留位置](../docs/01_1_Case_details.md)

### 重复校验器合并

- `scripts/03_information_extraction/validate_extraction.py` → [保留位置](../scripts/03_information_extraction/validate_all_extractions.py)

### 原始发布说明合并

- `data/2018_kilauea_hawaii/catalogs/MATOZA2014_GL059819/README_legacy.txt` → [保留位置](../data/2018_kilauea_hawaii/catalogs/MATOZA2014_GL059819/README.md)
- `data/2018_kilauea_hawaii/catalogs/MATOZA2021_EA001253/README_legacy.txt` → [保留位置](../data/2018_kilauea_hawaii/catalogs/MATOZA2021_EA001253/README.md)
- `data/2020_magna_utah/catalogs/BAKER2021_0220200316/README_legacy.txt` → [保留位置](../data/2020_magna_utah/catalogs/BAKER2021_0220200316/README.md)
- `data/2020_magna_utah/catalogs/PANG2020_GL089798/README_legacy.txt` → [保留位置](../data/2020_magna_utah/catalogs/PANG2020_GL089798/README.md)

## 验证

- 清理前后均运行 extraction 批量校验：23 份记录、0 个错误。JSON 的变化仅为证据文件迁移后的路径替换。
- 正文 MinerU 审查：23 个 PDF、22 个成功解析、22 个稳定 sidecar；原有 dissertation 解析失败状态保留，正文图片无缺失。
- 目录清单重复生成结果一致；6 项回归测试全部通过，覆盖 phase/event、alternate versions、非 full selection。
- 本地 Markdown/HTML 文件与图片引用检查：0 个缺失目标（清理前 55 个）；36 个 Python 文件通过语法检查，Git diff 空白检查通过。
- 原始发布说明忽略行末空白后逐段对照；未重跑波形下载、外部解析服务或科学目录实验。

本地清理前文本备份和完整操作日志另存 `/tmp/sabench_cleanup_backup/`、`/tmp/sabench_cleanup_changes.json`，便于本次会话复核；它们不是长期数据发布或项目运行依赖。已核验的可丢弃二进制副本不另外复制备份，保留的源 PDF、canonical 表与解压结果提供相同内容。
