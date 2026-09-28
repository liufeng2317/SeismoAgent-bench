# Stage 45: Input type and file format contract

- **Goal:** distinguish the semantic role of an input from the physical format used to store it.
- **Implemented:** replaced task-level `input_kinds` with `input_types`; changed manifest entries from `kind` to `data_type`; added required `format` metadata; registered `station_metadata` as the semantic role for StationXML; updated schemas, validators, fixtures, task manifests and runtime readers.
- **Validation:** focused task, phase-picking and Ridgecrest package tests passed (16 tests); the full test suite passed (109 tests).
- **Git:** `6f07ca9` (`Separate input data roles from file formats`).
