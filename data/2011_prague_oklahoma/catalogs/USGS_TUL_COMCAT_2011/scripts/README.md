# Local catalog processing — USGS_TUL_COMCAT_2011

The catalog-local parser reads the native files without modifying them and
writes normalized/phase-sample tables, statistics and compact PNG figures under
`../analysis/`.

```bash
python scripts/run_catalog_analysis.py
```

The frozen selector is `[2011-11-11T00:00:00Z, 2011-11-19T00:00:00Z)`.
Event products retain both `time_only` and the rounded common Prague mask;
McMahon phase rows use their parent E-record origin time because the release P
schema omits an hour token. Default output is minimal benchmark-first PNG
(300 dpi); use `--full-plots` only for exploratory diagnostics. No SVG files
are generated.
