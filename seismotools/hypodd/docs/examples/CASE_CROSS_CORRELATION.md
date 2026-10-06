# CASE_CROSS_CORRELATION

Generic HypoDD relocation case with FDTCC waveform cross-correlation constraints for `hypodd_runner`.

Use this case only when waveform data, station metadata, and FDTCC travel-time/threshold settings are available and cross-correlation should contribute to the relocation. The public entry point is `run_fdtcc_relocation(...)` with grouped parameter classes:

- `HypoDDInputs`
- `EventSelection`
- `Ph2dtParams`
- `HypoDDParams`
- `FDTCCParams`
- `RuntimeOptions`

This mode should produce catalog differential times (`dt_*.ct`), waveform cross-correlation differential times (`dt_*.cc`), and non-empty HypoDD native outputs.

The corresponding detailed RAG summaries are:

- `CASE_CROSS_CORRELATION_config_summary.md`
- `CASE_CROSS_CORRELATION_core_usage_summary.md`
- `CASE_CROSS_CORRELATION_file_summary.md`
- `CASE_CROSS_CORRELATION_plotting_usage_summary.md`

Do not claim waveform CC was used unless non-empty `dt_*.cc` files and FDTCC execution evidence exist.
