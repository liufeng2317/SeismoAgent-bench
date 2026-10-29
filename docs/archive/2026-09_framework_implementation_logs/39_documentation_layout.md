# Stage 39: Documentation layout separation

- **Goal:** keep project research records separate from reusable framework documentation.
- **Implemented:** moved research and case-design documents to `docs/research/`; moved benchmark workflow, run-contract, schemas and implementation logs to `docs/framework/`; added documentation indexes at `docs/README.md` and `docs/framework/README.md`.
- **References:** updated repository, script, case-analysis and generated-analysis references to the new paths.
- **Validation:** no legacy root documentation paths remain in the maintained project files; `git diff --check` passed; the full test suite passed.
