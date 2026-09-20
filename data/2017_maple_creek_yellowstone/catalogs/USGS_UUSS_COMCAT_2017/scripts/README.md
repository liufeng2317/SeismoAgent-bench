# Local catalog processing — USGS_UUSS_COMCAT_2017

This parser reads native Maple Creek files without modifying them and writes
compact derived tables, statistics and PNG figures under `../analysis/`.

```bash
python scripts/run_catalog_analysis.py
```

Frozen window: `[2017-06-11T00:00:00Z, 2017-06-19T00:00:00Z)`; common event mask:
`44.45–44.75°N`, `-110.55–-110.15°E`, depth `0–15 km`. The Shelly product is
phase-only, so only time selection is applied and phase rows are not event
counts. Default output is benchmark-first 300-dpi PNG; use `--full-plots` only
for exploratory diagnostics. No SVG files are generated.
