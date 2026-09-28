# Versioned task registry

## Status

Complete.

## Commit

| Git ID | Implemented content | Validation |
| --- | --- | --- |
| `45fb087` | Added explicit task registration, `task_id@version` lookup, stable records and directory discovery for `task.json` files. | 9 task tests and 62 full-suite tests passed. |

## Result

Tasks can now be selected by stable identity and version while reusing the existing task validator. Duplicate identities and ambiguous version lookups fail explicitly; manifests and non-task JSON files are not registered.
