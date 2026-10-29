# Generic catalog output contract

## Status

Complete.

## Commit

| Git ID | Implemented content | Validation |
| --- | --- | --- |
| `2af791c` | Added a versioned generic earthquake catalog schema and structural validator, and connected `kind: catalog` artifacts to it. | Catalog, CLI and full-suite checks passed; 67 full-suite tests passed. |

## Result

Agents now have one case-independent catalog output shape covering event identity, origin time, latitude, longitude, depth, optional magnitude and uncertainty fields, and optional P/S picks. The contract validates structure only and does not define scientific quality or reference matching.
