# Reference manifest and event matching

## Status

Complete.

## Commit

| Git ID | Implemented content | Validation |
| --- | --- | --- |
| `e3e1f75` | Added a versioned reference manifest, read-only reference catalog loading and deterministic one-to-one event matching with time, horizontal-distance and optional depth tolerances. | 19 scoring tests and 74 full-suite tests passed. |

## Result

Reference catalogs can now be identified by role and version and matched to candidate catalogs without copying reference contents or assigning a scientific score. Matching diagnostics preserve offsets and unmatched event IDs for later scorers.
