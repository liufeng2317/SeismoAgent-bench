# Stage 88: Ridgecrest catalog task contract cleanup

- Replaced the old per-waveform `input_manifest.json` with the current compact
  `input.json` contract. The task now links the complete read-only `waveforms`
  folder into `input/waveforms/` and lets the Agent discover its contents.
- Updated the task identifier, title, summary, input requirements and prompt to
  describe catalog construction rather than a smoke subset.
- Made `task_prompt.md` the primary human-readable specification for discovery,
  planning, reproducible processing, uncertainty and required catalog output.
  The separate `output_contract.json` remains only as the machine-readable
  catalog-scoring hint.
- Updated the waveform baseline to read the run-local input folder instead of
  assuming manifest entries for individual files.

Validation:

- Task and input contracts validated with existing source paths.
- `python -B -m unittest discover -s tests -v`: 89 tests passed.
- Modified Python files compile successfully and `git diff --check` passes.
