# Output artifact validation

## Status

Complete.

## Commit

| Git ID | Implemented content | Validation |
| --- | --- | --- |
| `ba02ef9` | Added relative output paths to the task contract and a read-only validator for required files, safe paths, regular-file status and basic JSON readability. | 6 task tests, 5 execution tests and 5 artifact-validation tests passed. |

## Result

The framework can now check whether an agent run produced the files declared by its task. The check records artifact identifiers, relative paths, kinds and byte sizes. It does not judge scientific quality and is not yet connected automatically to the execution runner.
