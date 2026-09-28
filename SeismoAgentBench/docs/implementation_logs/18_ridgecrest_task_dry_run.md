# Ridgecrest task infrastructure dry run

## Status

Complete.

## Commit

| Git ID | Implemented content | Validation |
| --- | --- | --- |
| `2b5fd5c` | Added a CLI dry-run regression for the Ridgecrest task package using an empty synthetic catalog and the two-event smoke reference. | 4 Ridgecrest package tests and 83 full-suite tests passed. |

## Result

The real case task, manifest, reference manifest and scientific scoring path are connected. The dry run is an infrastructure check only: it does not read waveforms, run scientific tools or claim catalog quality.
