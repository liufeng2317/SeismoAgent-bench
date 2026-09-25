# Benchmark source organization

## Catalog-level review

Use [`CATALOGS_MANIFEST.md`](CATALOGS_MANIFEST.md) for a single cross-case view of full-product counts, explicit units, and links to catalog audits and exploratory figures.

Use [`OFFICIAL_BASELINE_AUDIT.md`](OFFICIAL_BASELINE_AUDIT.md) to verify the USGS/GeoNet baseline downloads and distinguish routine-catalog sparsity from acquisition errors.

All six cases use the same source layout under `benchmark_source/`. Case-level `scripts/` exists only when there are executable case-level tools; empty placeholders are unnecessary. The ignored waveform directory is a local reservation, not evidence of downloaded observations.

```text
<case>/references/<SOURCE_ID>/
    paper/          # article or author manuscript
    supplement/     # supplementary tables, figures, movies

<case>/data/catalogs/<CATALOG_ID>/
    raw/             # original catalog archive, when available
    # extracted, benchmark-readable catalog files and README/schema

<case>/data/waveforms/  # local continuous waveform payloads, ignored by Git
<case>/analysis/        # scientific design, processing config and reference audit
<case>/scripts/         # case-level tools
```

`SOURCE_ID`/`CATALOG_ID` is the stable association key between a paper and its catalog. The `references` layer contains only literature and supplementary material; the `catalogs` layer is the core benchmark input and contains raw archives plus extracted catalog files. A catalog README must state `source_ref: <SOURCE_ID>`. Do not place benchmark catalog tables inside `supplement/`, even when the publisher delivered them in the same ZIP.

## Naming convention

- Case directories use lowercase `year_region_place` slugs; `references/` and `catalogs/` are always plural.
- Every paper in `references/<SOURCE_ID>/paper/` is named `<SOURCE_ID>__paper.pdf`. Additional article files use the same prefix and a role suffix (for example, `__evaluation.pdf` or `__poster.pdf`).
- Supplementary files retain their publisher/original basename inside `supplement/`, because those names encode table, figure, and SI identifiers.
- The benchmark-readable catalog at the catalog root is named `<SOURCE_ID>__catalog_<role>.<ext>` (for example, `__catalog_primary.txt`, `__catalog_S1.txt`, or `__catalog_hypocenters_v2.csv`). Supporting catalog products use the same source prefix and a descriptive role suffix.
- Original archives and extracted publisher batches retain their original names under `raw/`, `raw_article/`, or `supplement/`; these are provenance files and are not renamed for readability.
- Each catalog directory contains one authored `README.md` for provenance, field audits, interpretation and original release notes. `analysis/catalog_analysis.md` is the generated processing report, not a second authored source of truth.

## Evidence gate for additional references

An additional reference or catalog is promoted into the readiness matrix only when its identity and data product are independently verified by at least one authoritative source: a DOI/data-release landing page, a publisher supplement listing, an institutional archive, or a directly downloadable file whose metadata matches the article. A paper mention, search result, or similarly named catalog is not sufficient. Unverified candidates remain outside the canonical matrix until this gate is passed; they are not represented by repeated review-note additions.

## Official operational baseline policy

Each case may include one `official_operational` baseline. This baseline does not require a catalog-construction article: it is the authoritative routine catalog produced by the regional network or agency, used only for operational detection/coverage comparison (Q3), not as the high-resolution scientific truth catalog. Each baseline keeps a full sequence-span export and an exploratory benchmark-window export. To make the six cases comparable, every baseline must be obtained through an official FDSN/ComCat-style query or agency data release and archived with the same metadata: provider/network, query URL or release DOI, UTC query time, recorded time/space/depth filters, returned row count, and the canonical merged service export.

The provisional provider mapping is:

| Case | Official operational provider | Network/source | Role |
|---|---|---|---|
| `2011_prague_oklahoma` | USGS ANSS ComCat | `net=us`, `locationSource=tul` in returned snapshot | Q3 routine baseline |
| `2016_kaikoura_new_zealand` | GeoNet | GeoNet event service | Q3 routine baseline |
| `2017_maple_creek_yellowstone` | University of Utah Seismograph Stations | WY / UUSS | Q3 routine baseline |
| `2018_kilauea_hawaii` | Hawaiian Volcano Observatory / USGS | HV / ComCat | Q3 routine baseline |
| `2019_ridgecrest_california` | Southern California Seismic Network | CI / SCEDC / ComCat | Q3 routine baseline |
| `2020_magna_utah` | University of Utah Seismograph Stations | UUSS | Q3 routine baseline |

These baselines are not promoted to a reference paper/catalog pair unless a frozen export has been archived. A generic service homepage alone is not considered downloaded data.

## Remote data backup policy

The GitHub repository contains the small and medium-sized canonical catalog
products needed to inspect and reproduce the benchmark setup. Source papers,
supplements, raw archives, MinerU bundles, and machine-scale phase-arrival
tables remain local or are retrieved from their authoritative release pages.

### Stored in GitHub

- existing versioned canonical research catalogs; new large payloads stay local;
- existing versioned official full and benchmark operational snapshots;
- catalog README files, schemas, and provenance metadata;
- small auxiliary tables required to understand a reference product.

New additions should remain below 1 MiB per file; larger generated statistics and waveform payloads remain local. A directory move may reuse an existing Git blob without adding a new large data version.

### Not stored in ordinary Git

- `.env`, API keys, proxy credentials, and runtime logs;
- source PDFs and publisher supplements;
- MinerU ZIPs, duplicated PDFs, model caches, and extracted images;
- raw correlation-phase tables and waveform archives;
- any single file larger than 100 MB.

Files excluded from GitHub remain recoverable through the links and provenance
records in `REFERENCES_MANIFEST.md` and the catalog README files. If Git LFS or
a research data repository is enabled later, the excluded files can be added as
a separate data release without changing the source/catalog identifiers.

## Processing and output policy

- `analysis/processing.yaml` records case product declarations and `window_status`; all six cases currently say `not_frozen`. Earlier selections, statistics and plots remain exploratory. A filename containing `benchmark` does not imply a formal freeze.
- `data/catalogs/<CATALOG_ID>/README.md` is the single authored catalog entry point. Keep DOI, source-file checksums, native schema, release discrepancies and original publisher notes there.
- `data/catalogs/<CATALOG_ID>/scripts/` holds executable native parsers. `analysis/{derived,stats,figures}/` contains reproducible products; generated `catalog_analysis.md` documents those runs. Do not copy the same statistics into additional hand-maintained indices.
- Path bases are explicit: `catalog_dir` and script-entry paths are relative to the case root; a product `source_path` is relative to its catalog directory. Ridgecrest `reference_audit.sources[].path` and `phase_source.path` are relative to the case root. Preserve these distinctions until the configuration schema is unified.
- Local sequential `event_id` values such as `E000001` are scoped to `source_ref/product_id`. Preserve `native_event_id`; cross-catalog identity requires a crosswalk. Phase `match_id`/`template_id` values are not located event IDs.
- Keep event, relative-coordinate, phase/pick and focal-mechanism products separate. Separate release versions, coordinate bases, and official query snapshots are not redundant just because they overlap.
- Use compact PNG figures for inspection. Keep existing v1/v2 and alternate-mask figures until scientific equivalence and all callers have been checked; this cleanup does not choose a new scientific window or plot policy.
- Preserve source PDFs, original data archives, canonical catalogs, structured extraction JSON, reading notes, OCR page/model JSON and referenced images. OCR evidence and machine-readable extraction have different functions.
- MinerU transport ZIPs can be discarded only after every member is verified against extracted files. Byte-identical PDFs copied into MinerU output can be removed when the original PDF is retained. Keep `full.md` for parser resynchronization.
- For identical publisher tables that also serve as canonical catalogs, keep one payload under `data/catalogs/` and a relative symlink under `supplement/` so original names and converter discovery still work. Current S10/S11 aliases are local-only, like the ignored XLSX payloads.
- Delete Python caches and operating-system metadata; never treat `.env` or source data as disposable runtime clutter.
- Do not add one-time scripts that hardcode a second copy of reviewed extraction JSON. Edit the canonical records with evidence, then run the reusable validator.

The consolidation decisions and removed-file inventory are recorded in [repository cleanup](../docs/02_Repository_Cleanup.md).

## 目录结构评估与后续调整

当前六个案例已统一为以下职责划分。顶层只保留项目入口、全局方法文档、案例资料和共享工具，暂不为尚未实现的实验系统建立空目录。

```text
SeismoAgentBench/
├── README.md                         # 项目入口
├── docs/                             # 研究方案、案例选择、提取约定、历史整理说明
├── scripts/                          # 跨案例下载、解析、验证与清单入口
├── SeismoAgentBench/                 # 项目专业代码与通用工具
│   └── utils/source_prepare/         # 来源整理工具子包
├── tests/                            # 共享代码测试
└── benchmark_source/
    ├── README.md                     # 组织规范与结构评估（本文件）
    ├── REFERENCES_MANIFEST.md        # 文献/来源就绪状态
    ├── CATALOGS_MANIFEST.md          # 自动生成的产品清单
    ├── OFFICIAL_BASELINE_AUDIT.md    # 官方快照核验
    └── <case>/
        ├── README.md                # 导航；不复制统计或科学结论
        ├── analysis/                # 案例级设计、配置、跨目录核验
        │   ├── <CASE>_analysis.md
        │   └── processing.yaml
        ├── data/
        │   ├── catalogs/<SOURCE_ID>/
        │   │   ├── README.md        # 来源、字段、版本、质量限制
        │   │   ├── <source files>   # 现有规范化命名的来源文件
        │   │   ├── raw/             # 原始发布包，按需存在
        │   │   ├── scripts/         # 产品专属解析器，按需存在
        │   │   └── analysis/        # derived / stats / figures / 生成报告
        │   └── waveforms/           # 本地载荷，Git 忽略
        ├── references/<SOURCE_ID>/
        │   ├── paper/               # 论文原件
        │   ├── supplement/          # 保留出版物原名的附件
        │   └── parsed/              # paper / supplement / extraction
        └── scripts/                 # 案例级核验工具，按需存在
```

上图中的 `raw/`、`scripts/` 和文献附件按实际内容创建，不要求每个来源都有空目录。`analysis/` 分别位于案例和产品下是有意的：前者保存科学设计及跨产品结论，后者保存单一产品的可复算结果。

### 各案例的结构判断

| 案例 | 当前应保留的组织差异 | 后续优先改进 |
|---|---|---|
| [Prague](2011_prague_oklahoma/README.md) | 主事件、重定位、子空间事件及震相分产品保存 | 配置产品条目较详细，可作为统一产品字段的候选样例 |
| [Kaikōura](2016_kaikoura_new_zealand/README.md) | GrowClust 多版本、S10/S11、震相和机制解分别保存 | 统一脚本路径字段；来源表软链接只保留一份载荷；此次已修复 S12 配置路径与附件定位 |
| [Maple Creek](2017_maple_creek_yellowstone/README.md) | 缺失或仅辅助资料的来源仍保留说明入口 | 保持 missing/partial 状态显式可见，不以空目录或表行数推定事件就绪 |
| [Kīlauea](2018_kilauea_hawaii/README.md) | 相对坐标、近似绝对坐标、LP 与不同目录版本分开 | 大型生成统计留在本地；未来精简统计前先确认其使用方 |
| [Ridgecrest](2019_ridgecrest_california/README.md) | 案例级核验脚本和一个跨参考审计 JSON | 作为首个精细案例推进；台站/波形清单建立后再定义运行输入与隐藏参考的导出规则 |
| [Magna](2020_magna_utah/README.md) | 拾取表、重定位事件、ISC 档案及官方快照分开 | 补齐机器可读的产品路径和单位声明，保持记录单位清晰 |

### 真正值得继续调整的项目

1. **逐个迁移来源配置契约。** Ridgecrest 已试用下述 `schema_version: 2` 来源登记表；其余五个案例仍使用旧配置。Prague、Maple、Kīlauea 的 `catalogs[].script`、Kaikōura 的 `catalogs[].parser` 路径和 Magna 的角色声明需要逐产品核验后再迁移。登记表中的 `parser` 是解析器标识，不是可直接执行的路径。
2. **逐步提取共享解析与绘图工具。** 24 个 `run_catalog_analysis.py` 中存在反复出现的日期解析、校验和、筛选、统计和绘图函数；例如 12 个脚本定义了 `finite_float`。先核实行为差异并建立回归样例，再把相同部分提取成共享模块，来源专属字段解析仍留在产品目录。暂不把整个项目重构为软件包。
3. **未来分开维护来源资料与实际实验输入。** `benchmark_source/` 包含目标目录和答案证据，不能整体挂载给受测 Agent。实验运行器实现时，再定义可追溯的输入导出、评测参考和运行产物目录，并控制文件访问；仅改文件夹名字不能防止答案泄漏。
4. **台站信息应跟随观测数据建立。** 开始波形准备时，在案例 `data/` 下增加台站/通道清单、响应、可用性与缺口记录；现在不创建没有内容的 `stations/`、`metadata/` 或 `runs/`。波形存储位置可以是外部数据盘，配置记录位置，Git 保存小型清单与来源。
5. **保持原始材料和派生产物边界。** 已有来源文件可继续保留在 catalog 根目录，原始发布包留在 `raw/` 或 `raw_article/`；不为外观整齐再次移动全部载荷。生成统计、图件和标准化事件表继续放在产品 `analysis/` 下，不能混入来源原件。

不建议继续拆分更多手工状态报告，或立即重命名所有 v1/v2 图件与统计。当前三个全局清单分别回答来源是否就绪、有哪些产品、官方快照是否符合查询条件，职责不同；保留它们，并通过案例 README 导航，比复制多份进度表更易维护。

## 通用 source 架构：Ridgecrest 试点

这一层只维护资料来源、文件、版本、解析与核验。**评测代码和评测配置后续放到独立目录**，不在这里添加运行器、评分器、实验条件、资源预算或冻结审批。案例原有科学说明保留为背景；source 工具不依赖其中的评测就绪判断。

数据仍采用现有案例目录；项目代码统一放在 [SeismoAgentBench/](../SeismoAgentBench/README.md)，其中 source 整理工具位于 [utils/source_prepare/](../SeismoAgentBench/utils/source_prepare/)，来源契约测试放在 [tests/](../tests/)。不复制原始文件，也不为每个来源再增加一份登记 YAML。

```text
analysis/processing.yaml
  ├── source_groups             来源说明和产品所属关系
  ├── sources                   产品键 → 路径、版本、单位、解析器、SHA-256
  └── reference_audit            按产品键引用的核验规则，不重复写路径/哈希
             │
             ├── SeismoAgentBench/utils/source_prepare/sources.py   契约校验、文件盘点、分段/子集
             ├── 案例 scripts/                原生列解析、来源特有核验
             └── SeismoAgentBench/utils/source_prepare/catalog.py  时间/空间筛选与目录对应诊断
                          ↓
                analysis/reference_audit.json
```

### 来源配置 v2

| 字段 | 含义与维护规则 |
|---|---|
| `schema_version` / `case_id` | 明确来源契约版本和案例身份；旧配置不隐式升级 |
| `source_groups.<SOURCE_ID>` | 来源级角色说明及唯一 catalog README 入口；DOI、原始下载地址和方法细节继续由 README 维护 |
| `sources.<product_key>.source_ref` | 关联来源组；同一来源可包含多个文件产品 |
| `path` | 从案例根目录出发的相对路径；不允许逃逸到案例外部，案例内软链接可用 |
| `expected_sha256` | 本地发布版本的文件级指纹；不把文件名当作版本证明 |
| `version` | 可核实的版本标签；未声明发布编号时明确以 SHA-256 固定本地文件 |
| `unit` | `event`、`relative_event`、`phase_pick` 或 `focal_mechanism`；不统称事件数 |
| `format` / `parser` | 文件容器与原生解析器标识分别声明；仅通过校验不意味着任意解析器已实现 |
| `reference_audit` | 可选的案例核验配置：选择哪些源、派生子集、时间分段及目录对应诊断参数 |

Ridgecrest 目前登记 5 个来源组和 8 个文件产品。Ross 重定位子集是源目录的筛选结果，不另复制一个原始文件；Shelly 震相表按 pick 计数；AWR 机制解与事件目录分开登记。派生记录的可追溯身份应包含产品键、源文件哈希和源行号，原生事件 ID 单独保留，不凭时间自动合并事件。

路径和哈希只在 `sources` 登记一次，核验配置通过产品键引用。`reference_audit.json` 是带配置哈希的生成结果，可以重新计算，不是第二份手工登记表。不要额外提交每次文件盘点的完整副本。

### 使用方式与边界

在仓库根目录运行，使用现有 Python 3.10+ 和 PyYAML 环境：

```bash
python -B -m SeismoAgentBench.utils.source_prepare validate-sources --case-dir benchmark_source/2019_ridgecrest_california
python -B -m SeismoAgentBench.utils.source_prepare inventory --case-dir benchmark_source/2019_ridgecrest_california
python -B -m SeismoAgentBench.utils.source_prepare validate-sources --case-dir benchmark_source/2019_ridgecrest_california --verify-files
python -B benchmark_source/2019_ridgecrest_california/scripts/catalogs/audit_references.py
```

前两个命令不读取全部大文件计算哈希：资料登记有效与本地载荷已下载是两个状态。`--verify-files` 才执行 SHA-256 核验，发现本地缺失或内容不符时以非零状态退出。目录统计仍由案例解析器完成；登记表校验不会虚构记录数、波形覆盖、完备性或科学质量。

通用代码已通过一个不包含任何评测字段的合成案例测试。当前真实案例接入范围只有 Ridgecrest；下一步按同一契约逐个登记其余案例的文件产品，再逐步迁移共享解析函数。已有 catalog 专属处理脚本暂时保留，避免未经验证地替换不同来源的科学处理规则。

来源相关自动化回归统一在 `tests/source_prepare/`，案例目录不再保存重复测试。详细范围与新增原则见 [测试维护规则](../tests/AGENTS.md)；完整源文件核验继续使用本节列出的显式命令。
