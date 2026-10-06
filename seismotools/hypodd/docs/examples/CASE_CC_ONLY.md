# CASE_CC_ONLY

Generic CC-only HypoDD relocation case for `hypodd_runner`.

Use this case when the final HypoDD inversion should use waveform cross-correlation differential times only. The main public APIs are:

- `build_cc_only_relocation_kwargs(...)`
- `plan_cc_only_time_windows(...)`
- `run_cc_only_auto_time_windows(...)`
- `run_cc_only_relocation(...)`

This mode should produce non-empty `dt_*.cc`, successful HypoDD native outputs, and window status/manifest files for auto-window runs.

The corresponding detailed RAG summaries are:

- `CASE_CC_ONLY_config_summary.md`
- `CASE_CC_ONLY_core_usage_summary.md`
- `CASE_CC_ONLY_file_summary.md`
- `CASE_CC_ONLY_plotting_usage_summary.md`

Do not claim CC-only relocation succeeded from waveform conversion, FDTCC execution without usable CC links, empty native outputs, or plots alone.
