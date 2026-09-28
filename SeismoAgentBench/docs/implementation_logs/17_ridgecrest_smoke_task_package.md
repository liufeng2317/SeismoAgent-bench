# Ridgecrest smoke task package

## Status

Complete.

## Commit

| Git ID | Implemented content | Validation |
| --- | --- | --- |
| `c0fd23e` | Added the first Ridgecrest task, four-entry waveform/StationXML manifest, two-event USGS/SCSN smoke reference and task-package documentation. Shallow task discovery avoids scanning expert exports. | 12 task tests and 82 full-suite tests passed. |

## Result

Ridgecrest can now be addressed through the standard task and reference interfaces without copying waveform data. The bundled reference is explicitly limited to the M6.4 and M7.1 smoke events and is not a full-sequence benchmark reference.
