# Legacy evaluation cleanup

## Status

Complete.

## Commit

| Git ID | Implemented content | Validation |
| --- | --- | --- |
| `f322c76` | Removed the obsolete ACL, chroot and Bubblewrap development backend and its dedicated tests. Moved the input-manifest schema and Ridgecrest example under `SeismoAgentBench/task/`, and updated repository documentation. | JSON syntax checks passed; all 44 remaining tests passed; no references to the removed backend remain. |

## Result

The repository now has one active implementation path under `SeismoAgentBench/`. The manifest contract remains available with the task module, while historical filesystem-isolation experiments are no longer part of the executable or test surface.
