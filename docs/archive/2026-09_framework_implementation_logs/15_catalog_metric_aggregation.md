# Transparent catalog metric aggregation

## Status

Complete.

## Commit

| Git ID | Implemented content | Validation |
| --- | --- | --- |
| `4df3f98` | Added task-level aggregation for detection, location and depth metrics while preserving source metrics, matching policy and per-event matches. | 23 scoring tests and 78 full-suite tests passed. |

## Result

One scientific score can now be summarized into a stable task-level record without introducing an unsupported composite ranking. Unscored or incomplete inputs are rejected explicitly.
