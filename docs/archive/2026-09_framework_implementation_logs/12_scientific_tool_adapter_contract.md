# Scientific tool adapter contract

## Status

Complete.

## Commit

| Git ID | Implemented content | Validation |
| --- | --- | --- |
| `a273f0d` | Added serializable `ToolSpec` and `ToolRunRecord` contracts for tool identity, version, executable, parameters, model/auxiliary-file identity and run status. | 5 agent tests and 70 full-suite tests passed. |

## Result

Scientific tools can now be described and their outcomes recorded through one stable metadata contract. No tool is launched by this module; concrete adapters remain a later, tool-specific step.
