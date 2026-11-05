# Framework implementation logs (archived, September 2026)

History only. These are the stage records written while the benchmark framework was built (2026-09-29 to 2026-09-30, Codex era). They are superseded: the current framework is described in [`docs/framework/`](../../framework/), and since October 2026 each change is recorded in its commit message ([`04_Development_Process.md`](../../framework/04_Development_Process.md)). Records may describe behaviour, file names or harnesses that no longer exist (for example a flat run layout, `main.py` task entry points, or "no Claude adapter").

Numbering: there is no stage 35, and stage 81 has two records.

| Stage | Record | Title |
| --- | --- | --- |
| 00 | [00_framework_foundation.md](00_framework_foundation.md) | Framework foundation |
| 01 | [01_output_artifact_validation.md](01_output_artifact_validation.md) | Output artifact validation |
| 02 | [02_legacy_evaluation_cleanup.md](02_legacy_evaluation_cleanup.md) | Legacy evaluation cleanup |
| 03 | [03_deterministic_artifact_scorer.md](03_deterministic_artifact_scorer.md) | Deterministic artifact scorer |
| 04 | [04_end_to_end_task_workflow.md](04_end_to_end_task_workflow.md) | End-to-end task workflow |
| 05 | [05_agent_entrypoint_contract.md](05_agent_entrypoint_contract.md) | Agent entrypoint contract |
| 06 | [06_run_provenance_records.md](06_run_provenance_records.md) | Run provenance records |
| 07 | [07_workflow_failure_states.md](07_workflow_failure_states.md) | Workflow failure states |
| 08 | [08_external_worker_cli.md](08_external_worker_cli.md) | External worker CLI |
| 09 | [09_synthetic_cli_smoke.md](09_synthetic_cli_smoke.md) | Synthetic CLI smoke fixture |
| 10 | [10_versioned_task_registry.md](10_versioned_task_registry.md) | Versioned task registry |
| 11 | [11_generic_catalog_output_contract.md](11_generic_catalog_output_contract.md) | Generic catalog output contract |
| 12 | [12_scientific_tool_adapter_contract.md](12_scientific_tool_adapter_contract.md) | Scientific tool adapter contract |
| 13 | [13_reference_manifest_matching.md](13_reference_manifest_matching.md) | Reference manifest and event matching |
| 14 | [14_basic_catalog_scientific_scorer.md](14_basic_catalog_scientific_scorer.md) | Basic catalog scientific scorer |
| 15 | [15_catalog_metric_aggregation.md](15_catalog_metric_aggregation.md) | Transparent catalog metric aggregation |
| 16 | [16_optional_scientific_workflow_scoring.md](16_optional_scientific_workflow_scoring.md) | Optional scientific workflow scoring |
| 17 | [17_ridgecrest_smoke_task_package.md](17_ridgecrest_smoke_task_package.md) | Ridgecrest smoke task package |
| 18 | [18_ridgecrest_task_dry_run.md](18_ridgecrest_task_dry_run.md) | Ridgecrest task infrastructure dry run |
| 19 | [19_deterministic_baseline_agent.md](19_deterministic_baseline_agent.md) | Deterministic baseline agent |
| 20 | [20_waveform_baseline_agent.md](20_waveform_baseline_agent.md) | Waveform-driven baseline agent |
| 21 | [21_phase_picking_task.md](21_phase_picking_task.md) | Phase-picking task |
| 22 | [22_codex_host_direct_command.md](22_codex_host_direct_command.md) | Codex host-direct command layer |
| 23 | [23_codex_host_direct_adapter.md](23_codex_host_direct_adapter.md) | Codex host-direct adapter |
| 24 | [24_run_layout.md](24_run_layout.md) | Persistent run layout |
| 25 | [25_retryable_failures.md](25_retryable_failures.md) | Retryable provider failures |
| 26 | [26_bounded_resume.md](26_bounded_resume.md) | Bounded capacity resume |
| 27 | [27_default_model_routing.md](27_default_model_routing.md) | Stage 27: Default Codex model routing |
| 28 | [28_project_run_link.md](28_project_run_link.md) | Stage 28: Project view of run outputs |
| 29 | [29_compact_run_layout.md](29_compact_run_layout.md) | Stage 29: Compact run layout |
| 30 | [30_run_contract_ownership.md](30_run_contract_ownership.md) | Stage 30: Run contract ownership layout |
| 31 | [31_external_evaluation_command.md](31_external_evaluation_command.md) | Stage 31: External evaluation command |
| 32 | [32_agent_config_snapshot.md](32_agent_config_snapshot.md) | Stage 32: Agent runtime configuration snapshot |
| 33 | [33_experiment_spec_planning.md](33_experiment_spec_planning.md) | Stage 33: Experiment specification planning |
| 34 | [34_serial_experiment_execution.md](34_serial_experiment_execution.md) | Stage 34: Serial experiment execution |
| 36 | [36_framework_tree_cleanup.md](36_framework_tree_cleanup.md) | Stage 36: Framework tree cleanup |
| 37 | [37_agent_workflow_boundary.md](37_agent_workflow_boundary.md) | Stage 37: Agent workflow boundary cleanup |
| 38 | [38_evaluate_run_module.md](38_evaluate_run_module.md) | Stage 38: Dedicated evaluation workflow module |
| 39 | [39_documentation_layout.md](39_documentation_layout.md) | Stage 39: Documentation layout separation |
| 40 | [40_smoke_reference_fixture.md](40_smoke_reference_fixture.md) | Stage 40: Smoke reference fixture separation |
| 41 | [41_standalone_phase_picking_case.md](41_standalone_phase_picking_case.md) | Stage 41: Standalone phase-picking workflow case |
| 42 | [42_task_local_run_view.md](42_task_local_run_view.md) | Stage 42: Task-local run view |
| 43 | [43_standard_task_entrypoint.md](43_standard_task_entrypoint.md) | Stage 43: Standard task entrypoint name |
| 44 | [44_agent_task_prompt_contract.md](44_agent_task_prompt_contract.md) | Stage 44: Agent task prompt contract |
| 45 | [45_input_type_format_contract.md](45_input_type_format_contract.md) | Stage 45: Input type and file format contract |
| 46 | [46_external_output_contract.md](46_external_output_contract.md) | Stage 46: External output contract |
| 47 | [47_folder_phase_picking_task.md](47_folder_phase_picking_task.md) | Stage 47: Folder-based phase-picking task |
| 48 | [48_agent_prompt_rendering.md](48_agent_prompt_rendering.md) | Stage 48: Agent prompt rendering |
| 49 | [49_task_run_script.md](49_task_run_script.md) | Stage 49: Task-local run script |
| 50 | [50_codex_executable_resolution.md](50_codex_executable_resolution.md) | Stage 50: Codex executable resolution |
| 51 | [51_unique_default_run_id.md](51_unique_default_run_id.md) | Stage 51: Unique default run ID |
| 52 | [52_phase_picking_runtime.md](52_phase_picking_runtime.md) | Implementation 52: Phase-picking runtime |
| 53 | [53_single_agent_work_root.md](53_single_agent_work_root.md) | Implementation 53: Single Agent work root |
| 54 | [54_codex_work_path_fix.md](54_codex_work_path_fix.md) | Implementation 54: Codex work path fix |
| 55 | [55_reproducible_task_artifact.md](55_reproducible_task_artifact.md) | Implementation 55: Reproducible task artifact |
| 56 | [56_phase_pick_scientific_scorer.md](56_phase_pick_scientific_scorer.md) | Implementation 56: Phase-pick scientific scorer |
| 57 | [57_control_snapshot_separation.md](57_control_snapshot_separation.md) | Implementation 57: Control snapshot separation |
| 58 | [58_structured_agent_transcript.md](58_structured_agent_transcript.md) | Implementation 58: Structured Agent transcript |
| 59 | [59_provenance_record_consolidation.md](59_provenance_record_consolidation.md) | Implementation 59: Provenance record consolidation |
| 60 | [60_markdown_task_prompt.md](60_markdown_task_prompt.md) | Implementation 60: Markdown task prompt |
| 61 | [61_provenance_interface_cleanup.md](61_provenance_interface_cleanup.md) | Implementation 61: Provenance interface cleanup |
| 62 | [62_generic_artifact_schema.md](62_generic_artifact_schema.md) | Implementation 62: Generic declared artifact schemas |
| 63 | [63_canonical_task_metadata.md](63_canonical_task_metadata.md) | Implementation 63: Canonical task metadata |
| 64 | [64_explicit_experiment_harness.md](64_explicit_experiment_harness.md) | Implementation 64: Explicit experiment harness |
| 65 | [65_unit_batch_result_records.md](65_unit_batch_result_records.md) | Implementation 65: Unit and batch result records |
| 66 | [66_scorer_registry.md](66_scorer_registry.md) | Implementation 66: Scorer registry |
| 67 | [67_scorer_handler_dispatch.md](67_scorer_handler_dispatch.md) | Implementation 67: Scorer handler dispatch |
| 68 | [68_repeatable_external_evaluation.md](68_repeatable_external_evaluation.md) | Repeatable external evaluation |
| 69 | [69_core_test_suite_cleanup.md](69_core_test_suite_cleanup.md) | Core test suite cleanup |
| 70 | [70_phase_picking_prompt_contract.md](70_phase_picking_prompt_contract.md) | Phase-picking prompt contract |
| 71 | [71_prompt_rendering_boundaries.md](71_prompt_rendering_boundaries.md) | Prompt rendering boundaries |
| 72 | [72_prompt_heading_cleanup.md](72_prompt_heading_cleanup.md) | Prompt heading cleanup |
| 73 | [73_prompt_first_task_contract.md](73_prompt_first_task_contract.md) | Prompt-first task contract |
| 74 | [74_explicit_task_input_paths.md](74_explicit_task_input_paths.md) | Explicit task input paths |
| 75 | [75_task_output_visualization_plan.md](75_task_output_visualization_plan.md) | Task output visualization plan |
| 76 | [76_runtime_prompt_simplification.md](76_runtime_prompt_simplification.md) | Runtime prompt simplification |
| 77 | [77_remove_framework_prompt_heading.md](77_remove_framework_prompt_heading.md) | Remove framework prompt heading |
| 78 | [78_run_input_view.md](78_run_input_view.md) | Run-local input view |
| 79 | [79_configured_input_links.md](79_configured_input_links.md) | Unified input configuration |
| 80 | [80_unified_input_json.md](80_unified_input_json.md) | Unified input JSON |
| 81 | [81_agent_runtime_profiles.md](81_agent_runtime_profiles.md) | Stage 81: Agent runtime profiles and executable versions |
| 81 | [81_task_input_root.md](81_task_input_root.md) | Task input root |
| 82 | [82_external_auth_profiles.md](82_external_auth_profiles.md) | Stage 82: External authentication profiles |
| 83 | [83_live_execution_logs.md](83_live_execution_logs.md) | Stage 83: Live execution logs |
| 84 | [84_framework_config_location.md](84_framework_config_location.md) | Stage 84: Framework configuration location |
| 85 | [85_codex_auth_copy.md](85_codex_auth_copy.md) | Stage 85: Per-run Codex authentication copy |
| 86 | [86_data_directory_migration.md](86_data_directory_migration.md) | Data directory migration |
| 87 | [87_workflow_directory_organization.md](87_workflow_directory_organization.md) | Stage 87: Workflow directory organization |
| 88 | [88_ridgecrest_task_contract_cleanup.md](88_ridgecrest_task_contract_cleanup.md) | Stage 88: Ridgecrest catalog task contract cleanup |
| 89 | [89_ridgecrest_five_file_task_interface.md](89_ridgecrest_five_file_task_interface.md) | Stage 89: Ridgecrest five-file task interface |
