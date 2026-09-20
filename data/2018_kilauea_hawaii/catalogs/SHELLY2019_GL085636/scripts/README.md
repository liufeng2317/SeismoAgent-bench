# Local catalog processing — SHELLY2019_GL085636

This script is intentionally local to `SHELLY2019_GL085636`. It reads native files without modifying them and writes normalized tables, statistics and figures under `../analysis/`.

```bash
python scripts/run_catalog_analysis.py
```

Products are kept separate; phase/pick rows are never interpreted as event counts. The benchmark selector uses the half-open UTC window `[2018-05-01, 2018-05-09)` and the common summit mask only when the product has latitude, longitude and depth.

## Reproducibility and runtime

The parser treats timezone-naive native timestamps as UTC. Large phase products are cached by the raw-file SHA-256 after the first stream; reruns reuse `analysis/stats/` unless `--force` is supplied. Use `--only <product_id>` for a targeted product.

## Compact output policy

The default parser profile is `minimal`: it uses the frozen benchmark selection,
creates publication-oriented PNG figures only, and keeps statistics for products
that are historical or redundant for the benchmark. Use `--full-plots` only when
an exploratory diagnostic is needed. No SVG files are generated.

