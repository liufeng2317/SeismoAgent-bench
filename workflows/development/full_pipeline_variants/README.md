# Full-pipeline checker arms (S2c, S3)

The formal comparison runs the whole pipeline: picking, association, template matching, location, relocation and magnitudes (decided 2026-11-05; the detection gap sits in the front end, which the back-end tier keeps fixed, `docs/research/progress/checker_validation/10_template_threshold.md`). `build_full_variants.py` builds two arms of every case from its tools arm:

| Arm | Stage | Adds over the arm above | Contract | Use |
|---|---|---|---|---|
| `tools` | S1 | the seismotools library (`TOOLS_BASE_PATH`); the checker is not in it | `output_contract_min.json` | existing |
| `checker` | S2c | the catalog checker (`CHECKER_PATH`, `seismo_checker/`), the catalog-checker skill, the checker contract | `output_contract_checker.json` | built; run only for an ablation |
| `knowledge` | S3 | the catalog-knowledge skill and the magnitude resource | `output_contract_checker.json` | main experiment |

The prompts are the case's `prompt_tools.md` with the checker section of `../backend_tier_b/build_backend_variants.py` inserted after `### Tools` and the two checker files added to the required outputs, so both tiers present the checker in the same words. Files per case, in `workflows/tasks/<case>/`: `prompt_<arm>.md`, `task_<arm>.json`, `input_<arm>.json`, `output_contract_checker.json` (a copy of the back-end one). Rerun the script after changing `prompt_tools.md`, the checker section or the skills' location.

```bash
cd workflows/tasks/<case>
AGENT=claude VARIANT=knowledge bash run.sh   # 48-hour budget, like tools
```

The checker and the knowledge skill are those of git tag `checker-v1.3`. Before the arms are run, `../smoke_end_to_end/run.sh <case> knowledge <a completed tools run>` checks the package without a model.
