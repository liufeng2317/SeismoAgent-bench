# Stage 43: Standard task entrypoint name

- **Goal:** use one predictable entrypoint name for executable workflow task packages.
- **Implemented:** renamed the standalone phase-picking baseline from `baseline_agent.py` to `main.py` and updated its test and task documentation.
- **Boundary:** expert-case scripts and multi-baseline scientific case utilities retain their descriptive names; this convention applies to the standalone task package entrypoint.
- **Validation:** phase-picking task tests passed and `git diff --check` passed.
