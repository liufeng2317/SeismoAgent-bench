# External worker CLI

## Status

Complete.

## Commit

| Git ID | Implemented content | Validation |
| --- | --- | --- |
| `76ffdc9` | Added `python -m SeismoAgentBench run-agent` for passing task, manifest, agent identity, run directory and command arguments to the existing workflow. | 2 CLI tests and 58 full-suite tests passed. |

## Result

An external worker can now invoke the same agent workflow without importing Python modules. Exit code `0` means `scored`; workflow failures return exit code `3`; CLI argument or setup errors return exit code `2`.
