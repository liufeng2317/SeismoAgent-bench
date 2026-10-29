# Stage 27: Default Codex model routing

## Objective

Allow the Codex adapter to omit `--model` and use the model route selected by
Codex. This separates account/session authentication from explicit model
capacity and makes the CLI behavior match the normal Codex invocation.

## Implemented

- Made `run-codex --model` optional.
- Omitted `--model` from the subprocess command when no model is supplied.
- Kept explicit model selection available for controlled experiments.
- Added a unit test for the default-routing command shape.

## Validation

- Focused tests: `python -m unittest tests.execution.test_codex tests.cli.test_codex -v`
- Result: 7 tests passed.
- Real phase-picking smoke run: campaign `codex_host_smoke_20260929_default`,
  run `run_001`.
- Codex default routing generated `preprocessing.json` and `picks.json`.
- Artifact-contract scorer passed with `contract_compliance = 1.0` and both
  required artifacts present.

## Boundary

The run used host-direct execution and is marked `formal_evaluation_eligible:
false`. The agent could inspect other files under the shared persistent run
root, so this result confirms CLI-to-agent-to-scorer connectivity only. It does
not establish isolation or formal benchmark validity.

## Commit

The implementation and this record are committed separately under the project
implementation constraints.
