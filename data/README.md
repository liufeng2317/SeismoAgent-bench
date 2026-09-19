# Data organization

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
- Each catalog directory contains `README.md`; legacy notes, when retained, use `README_legacy.txt` and are not the canonical metadata file.

## Evidence gate for additional references

An additional reference or catalog is promoted into the readiness matrix only when its identity and data product are independently verified by at least one authoritative source: a DOI/data-release landing page, a publisher supplement listing, an institutional archive, or a directly downloadable file whose metadata matches the article. A paper mention, search result, or similarly named catalog is not sufficient. Unverified candidates remain outside the canonical matrix until this gate is passed; they are not represented by repeated review-note additions.

## Official operational baseline policy

Each case may include one `official_operational` baseline. This baseline does not require a catalog-construction article: it is the authoritative routine catalog produced by the regional network or agency, used only for operational detection/coverage comparison (Q3), not as the high-resolution scientific truth catalog. Each baseline keeps a full sequence-span export and a frozen benchmark-window export. To make the six cases comparable, every baseline must be obtained through an official FDSN/ComCat-style query or agency data release and archived with the same metadata: provider/network, query URL or release DOI, UTC query time, frozen time/space/depth filters, returned row count, and the canonical merged service export.

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
