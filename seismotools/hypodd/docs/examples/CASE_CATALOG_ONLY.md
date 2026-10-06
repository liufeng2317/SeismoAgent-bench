# CASE_CATALOG_ONLY

Generic catalog-only HypoDD relocation case for `hypodd_runner`.

Use this case when waveform cross-correlation is absent or not requested. The public entry point is `run_catalog_only_relocation(...)` with grouped parameter classes:

- `HypoDDInputs`
- `EventSelection`
- `Ph2dtParams`
- `HypoDDParams`
- `RuntimeOptions`

This mode uses catalog differential times from `ph2dt` and should not require waveform directories, FDTCC velocity tables, FDTCC logs, or `dt_*.cc` files.

The corresponding detailed RAG summaries are:

- `CASE_CATALOG_ONLY_config_summary.md`
- `CASE_CATALOG_ONLY_core_usage_summary.md`
- `CASE_CATALOG_ONLY_file_summary.md`
- `CASE_CATALOG_ONLY_plotting_usage_summary.md`

Do not treat input preparation, validation-only runs, empty native outputs, fallback products, or plotting-only artifacts as successful relocation.
