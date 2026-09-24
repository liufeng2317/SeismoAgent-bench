# Data organization

## Catalog-level review

Use [`CATALOGS_MANIFEST.md`](./CATALOGS_MANIFEST.md) for a single cross-case view of full-product counts, explicit units, and links to catalog audits and exploratory figures.

Use [`OFFICIAL_BASELINE_AUDIT.md`](./OFFICIAL_BASELINE_AUDIT.md) to verify the USGS/GeoNet baseline downloads and distinguish routine-catalog sparsity from acquisition errors.

Each case uses two complementary layers:

```text
<case>/references/<SOURCE_ID>/
    paper/          # article or author manuscript
    supplement/     # supplementary tables, figures, movies

<case>/catalogs/<CATALOG_ID>/
    raw/             # original catalog archive, when available
    # extracted, benchmark-readable catalog files and README/schema
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

- canonical research catalogs smaller than GitHub's 100 MB single-file limit;
- official full and benchmark operational snapshots;
- catalog README files, schemas, and provenance metadata;
- small auxiliary tables required to understand a reference product.

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
- `catalogs/<CATALOG_ID>/README.md` is the single authored catalog entry point. Keep DOI, source-file checksums, native schema, release discrepancies and original publisher notes there.
- `catalogs/<CATALOG_ID>/scripts/` holds executable native parsers. `analysis/{derived,stats,figures}/` contains reproducible products; generated `catalog_analysis.md` documents those runs. Do not copy the same statistics into additional hand-maintained indices.
- Local sequential `event_id` values such as `E000001` are scoped to `source_ref/product_id`. Preserve `native_event_id`; cross-catalog identity requires a crosswalk. Phase `match_id`/`template_id` values are not located event IDs.
- Keep event, relative-coordinate, phase/pick and focal-mechanism products separate. Separate release versions, coordinate bases, and official query snapshots are not redundant just because they overlap.
- Use compact PNG figures for inspection. Keep existing v1/v2 and alternate-mask figures until scientific equivalence and all callers have been checked; this cleanup does not choose a new scientific window or plot policy.
- Preserve source PDFs, original data archives, canonical catalogs, structured extraction JSON, reading notes, OCR page/model JSON and referenced images. OCR evidence and machine-readable extraction have different functions.
- MinerU transport ZIPs can be discarded only after every member is verified against extracted files. Byte-identical PDFs copied into MinerU output can be removed when the original PDF is retained. Keep `full.md` for parser resynchronization.
- For identical publisher tables that also serve as canonical catalogs, keep one payload under `catalogs/` and a relative symlink under `supplement/` so original names and converter discovery still work. Current S10/S11 aliases are local-only, like the ignored XLSX payloads.
- Delete Python caches and operating-system metadata; never treat `.env` or source data as disposable runtime clutter.
- Do not add one-time scripts that hardcode a second copy of reviewed extraction JSON. Edit the canonical records with evidence, then run the reusable validator.

The consolidation decisions and removed-file inventory are recorded in [repository cleanup](../docs/02_Repository_Cleanup.md).
