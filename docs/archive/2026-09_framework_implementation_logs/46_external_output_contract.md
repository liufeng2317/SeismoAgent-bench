# Stage 46: External output contract

- **Goal:** separate task metadata, concrete input instances and required output definitions.
- **Implemented:** kept `input_manifest.json` as the concrete data-instance manifest; added `output_contract.json` to the Ridgecrest catalog and phase-picking task packages; added contract validation and resolution through `load_task`; updated the runner and task registry to use the resolved contract; added the output-contract schema and documentation.
- **Validation:** focused execution and task tests passed (16 tests); the full test suite passed (109 tests).
- **Git:** `0545d3a` (`Separate task output contract`).
