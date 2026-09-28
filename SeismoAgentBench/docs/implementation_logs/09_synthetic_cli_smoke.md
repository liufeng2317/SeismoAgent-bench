# Synthetic CLI smoke fixture

## Status

Complete.

## Commit

| Git ID | Implemented content | Validation |
| --- | --- | --- |
| `bc25167` | Added a versioned synthetic task, manifest and deterministic agent fixture, with a CLI smoke test covering the complete run layout. | 3 CLI tests and 59 full-suite tests passed. |

## Result

The external CLI now has a reusable, data-free regression fixture. It verifies task validation, agent execution, output validation, contract scoring and all required run records without using a scientific case or private reference data.
