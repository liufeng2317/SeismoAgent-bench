# Basic catalog scientific scorer

## Status

Complete.

## Commit

| Git ID | Implemented content | Validation |
| --- | --- | --- |
| `033fbbb` | Added event-level catalog metrics for detection precision/recall/F1, origin-time error, horizontal location error and depth error using the reference matching interface. | 21 scoring tests and 76 full-suite tests passed. |

## Result

The framework now has a first scientific scorer that produces transparent per-match diagnostics. It does not aggregate across tasks, score magnitudes, or define a universal catalog quality rank.
