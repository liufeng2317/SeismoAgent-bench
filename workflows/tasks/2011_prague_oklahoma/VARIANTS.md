# Prague 2011 prompt variants

A minimal single-factor family built around the experiment's research
questions, mirroring the Ridgecrest case. Every arm shares the same input,
output schema and scoring; each arm differs from the control (`min`) by
exactly one factor, so score deltas attribute to that factor and nothing
else.

## Research questions → variants

| Question | Contrast | Arm |
|---|---|---|
| Q1. Can a general-purpose agent complete seismic monitoring on its own and reach expert-level results? | `min` vs the expert reference (`expert/` workflow) | `min` |
| Q2. Do expert tools matter? | `tools` vs `min` | `tools` |
| Q3. Does expert experience matter? | `guided` vs `min` | `guided` |
| Q4. Is RIS needed in a feedback-driven workflow? | `ris` vs `min` — future arm, design pending | — |

The expert level in Q1 is not a prompt variant: it is the result of the
`expert/` scientific workflow (three documented rounds; see `expert/PLAN.md`)
and the case references — Cochran et al. (2020) template-enhanced catalog
(primary), McMahon et al. (2017) subspace-detection catalog, Isken & Mooney
(2017) M>3 relocations (location anchor) and ComCat — used as the scoring
benchmark for every arm.

## Variant matrix

| Variant | Task spec | Differs from `min` by | Guidance | Scope | Tool policy | Contract |
|---|---|---|---|---|---|---|
| `min` | `task_min.json` | — (control arm) | minimal | stated window | unspecified | min |
| `tools` | `task_tools.json` | + `### Tools`: local PhaseNet; GaMMA / PyOcto / REAL; NonLinLoc / HypoInverse; hypoDD / GrowClust / ccdt; Match&Locate (picking; association; location; relocation; template matching) with validated usage docs | minimal | stated window | local provided | min |
| `guided` | `task_guided.json` | + expert scaffolding: fixed eight-day window, pipeline stages, QC gates, tuning discipline, report | expert-scaffolded | fixed window | neutral public | default |

Contracts: `output_contract_min.json` (picks + catalog) and
`output_contract.json` (picks + catalog + report.md) — identical to the
Ridgecrest contracts (the output schema is case-independent).

## Design decisions

- **Scope.** Every arm states the processing window
  `[2011-11-11T00:00:00Z, 2011-11-19T00:00:00Z)`: it is part of the task definition, not expert
  guidance, and the supplied `waveform_inventory.json` names it anyway.
  Before 2026-10-28 `min` and `tools` left it to self-scoping; an
  unstated window measured whether the Agent read the inventory (and,
  where the input holds more days than the window, how much budget it
  spent outside it) rather than scientific judgement. `guided` adds the
  daily-file mapping and the margin rule. All arms are scored on the
  same evaluation window.
- **What ships with tools.** The `tools` arm carries the tools' validated
  usage notes (the PhaseNet example, the 100 Hz resampling rule) because
  they are part of the tool package, not guidance. The tool paths are the
  same shared `seismotools/` library as the Ridgecrest case.
- **Contracts.** `min` and `tools` use the same two-artifact contract so the
  Q2 contrast changes output requirements not at all; `guided` adds
  `report.md` because reporting discipline is part of expert experience.
- **One factor per contrast.** Agent, harness and model are replication
  dimensions (run the same arm across `claude` / `codex` and models), not
  variants.

## Validity conditions common to every variant

- No existing Prague 2011 catalogs, published picks, known locations or other
  reference products may be used to construct or tune the result.
- Values must not be fabricated; empty-but-honest is always acceptable.
- The framework boundary rules (read-only input view, writable `$BENCH_OUTPUT`,
  no reference/hidden materials) apply to all variants via `framework.md`.

## Scoring wiring status

Every task spec declares `artifact-contract@1` and `catalog-metrics@1`, so
`python -m SeismoAgentBench evaluate --run-dir <run>` validates the CSV
contract and scores the run with the pre-registered metrics v1
(`docs/framework/03_EVALUATION_METRICS.md`; case configuration in
`evaluation/metrics_v1.yaml`): detection, location, structure and magnitude
against every reference in its assigned roles, by magnitude class, plus
process, leakage and the unsupported-event audit sample. Configurations are
aggregated with `python -m SeismoAgentBench.scoring.catalog_metrics summary
--task-dir <this task>` (see `evaluation/README.md`). Runs started before
2026-10-28 carry the earlier scorer declaration in their control snapshot
and are scored with the summary command.

## Cost and sequencing

The window is eight days / ~7 GB of MiniSEED, on CPU-only hardware. No
Prague agent run has completed yet; the first `min` run also sets the
empirical cost record for this case.

1. `min` — capability baseline (Q1), scored against the expert reference.
2. `tools`, `guided` — each vs `min`, same agent and model; repeat key cells
   at least twice before attributing deltas to the factor.
3. `ris` — after the feedback-loop design is settled.

When comparing variants, prefer same agent, same model, same reasoning effort
and `RUN_ID` timestamps close together.

## Running

```bash
cd workflows/tasks/2011_prague_oklahoma
VARIANT=min bash run.sh                      # min is the default
AGENT=claude VARIANT=tools bash run.sh       # any arm through Claude Code
```

Runs land in `runs/<variant>/<harness>/<model>/<timestamp>/` (one experiment
factor per path segment) with the usual control/work/record layout. The
runner accepts any `task_<variant>.json` present in this directory, so the
future `ris` arm will not require editing `run.sh`.
