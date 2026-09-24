# Official baseline download audit

This report checks local CSV snapshots against the configured full/benchmark time, space, and depth windows. It does not treat a small routine-catalog count as a download failure. ComCat does not expose `network`/`locationSource` as the same query filters used by the local source labels; those fields are audited after retrieval.

| Case | Full rows | Benchmark rows | Full out-of-scope | Benchmark out-of-scope | Duplicate IDs | Benchmark subset | Source distribution |
|---|---:|---:|---:|---:|---:|---|---|
| `2011_prague_oklahoma` | 71 | 11 | 0 | 0 | 0 | yes | us:71 |
| `2017_maple_creek_yellowstone` | 9 | 5 | 0 | 0 | 0 | yes | uu:9 |
| `2018_kilauea_hawaii` | 40,095 | 496 | 0 | 0 | 0 | NO | hv:40079, us:16 |
| `2019_ridgecrest_california` | 17,959 | 6,566 | 0 | 0 | 0 | NO | ci:17956, us:3 |
| `2020_magna_utah` | 2,078 | 1,432 | 0 | 0 | 0 | yes | uu:2077, us:1 |

## Interpretation

- `out_of_scope_rows = 0` and zero duplicate IDs indicate that each local file obeys its configured query mask and has no obvious truncation or malformed merge. A benchmark snapshot is an independent ComCat query; a small number of IDs may differ from the full snapshot because ComCat metadata/history can be revised between requests.
- Prague and Maple are small because they are routine ComCat/U.S. network baselines, not enhanced research catalogs. Their low counts are consistent with the returned source distributions and are not evidence of a truncation: all chunks are far below the ComCat 20,000-row cap.
- Source labels are preserved. Prague includes 64 `tul` and 7 `us` location-source rows; HVO includes 40,086 `hv` and 9 `us`; Ridgecrest includes 17,958 `ci` and 1 `us`; these should not be silently recoded.
- HVO has 1 benchmark ID and Ridgecrest has 3 benchmark IDs absent from the independently downloaded full snapshot, despite fitting the full mask. These are recorded as cross-query revision mismatches, not silently merged. If strict nesting is required, rerun full and benchmark in one acquisition session.
- For completeness benchmarking, use the research catalogs (Cochran/McMahon, Shelly/Pang, etc.) rather than substituting the official routine baseline.

### `2011_prague_oklahoma`

- Full: `data/2011_prague_oklahoma/catalogs/USGS_TUL_COMCAT_2011/USGS_TUL_COMCAT_2011__catalog_operational_full.csv`; benchmark: `data/2011_prague_oklahoma/catalogs/USGS_TUL_COMCAT_2011/USGS_TUL_COMCAT_2011__catalog_operational_benchmark.csv`
- Full source fields: networks `{'us': 71}`, location sources `{'tul': 64, 'us': 7}`
- Full type fields: `{'earthquake': 71}`
- Benchmark subset of full: `True`

### `2017_maple_creek_yellowstone`

- Full: `data/2017_maple_creek_yellowstone/catalogs/USGS_UUSS_COMCAT_2017/USGS_UUSS_COMCAT_2017__catalog_operational_full.csv`; benchmark: `data/2017_maple_creek_yellowstone/catalogs/USGS_UUSS_COMCAT_2017/USGS_UUSS_COMCAT_2017__catalog_operational_benchmark.csv`
- Full source fields: networks `{'uu': 9}`, location sources `{'uu': 9}`
- Full type fields: `{'earthquake': 9}`
- Benchmark subset of full: `True`

### `2018_kilauea_hawaii`

- Full: `data/2018_kilauea_hawaii/catalogs/USGS_HVO_COMCAT_2018/USGS_HVO_COMCAT_2018__catalog_operational_full.csv`; benchmark: `data/2018_kilauea_hawaii/catalogs/USGS_HVO_COMCAT_2018/USGS_HVO_COMCAT_2018__catalog_operational_benchmark.csv`
- Full source fields: networks `{'hv': 40079, 'us': 16}`, location sources `{'hv': 40086, 'us': 9}`
- Full type fields: `{'earthquake': 40032, 'chemical explosion': 1, 'volcanic eruption': 62}`
- Benchmark subset of full: `False`

### `2019_ridgecrest_california`

- Full: `data/2019_ridgecrest_california/catalogs/USGS_SCSN_COMCAT_2019/USGS_SCSN_COMCAT_2019__catalog_operational_full.csv`; benchmark: `data/2019_ridgecrest_california/catalogs/USGS_SCSN_COMCAT_2019/USGS_SCSN_COMCAT_2019__catalog_operational_benchmark.csv`
- Full source fields: networks `{'ci': 17956, 'us': 3}`, location sources `{'ci': 17958, 'us': 1}`
- Full type fields: `{'earthquake': 17956, 'quarry blast': 3}`
- Benchmark subset of full: `False`

### `2020_magna_utah`

- Full: `data/2020_magna_utah/catalogs/USGS_UUSS_COMCAT_2020/USGS_UUSS_COMCAT_2020__catalog_operational_full.csv`; benchmark: `data/2020_magna_utah/catalogs/USGS_UUSS_COMCAT_2020/USGS_UUSS_COMCAT_2020__catalog_operational_benchmark.csv`
- Full source fields: networks `{'uu': 2077, 'us': 1}`, location sources `{'uu': 2077, 'us': 1}`
- Full type fields: `{'earthquake': 2078}`
- Benchmark subset of full: `True`
