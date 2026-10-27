# Maple Creek 2017 prompt variants

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
`expert/` scientific workflow (six documented rounds; see `expert/PLAN.md`)
and the two references the case has — ComCat/UUSS operational events
(located) and the Shelly & Hardebeck (2019) detections derived from their
phase release (origin times only; Pang 2019 and Shelly's event tables are
unpublished) — used as the scoring benchmark for every arm.

## Variant matrix

| Variant | Task spec | Differs from `min` by | Guidance | Scope | Tool policy | Contract |
|---|---|---|---|---|---|---|
| `min` | `task_min.json` | — (control arm) | minimal | unspecified | unspecified | min |
| `tools` | `task_tools.json` | + `### Tools`: local PhaseNet; GaMMA / PyOcto / REAL; NonLinLoc / HypoInverse; hypoDD / GrowClust / ccdt (picking; association; location; relocation) with validated usage docs | minimal | unspecified | local provided | min |
| `guided` | `task_guided.json` | + expert scaffolding: fixed eight-day window, pipeline stages, QC gates, tuning discipline, report | expert-scaffolded | fixed window | neutral public | default |

Contracts: `output_contract_min.json` (picks + catalog) and
`output_contract.json` (picks + catalog + report.md) — identical to the
Ridgecrest contracts (the output schema is case-independent).

## Design decisions

- **Scope.** `min` and `tools` deliberately do not state a processing
  window: self-scoping is part of what Q1 measures, and adding a window to
  `tools` would confound the Q2 contrast. `guided`'s fixed window
  `[2017-06-11T00:00:00Z, 2017-06-19T00:00:00Z)` (daily files 2017-06-11
  through 2017-06-18) is itself part of the expert-experience treatment.
  All arms are scored on the same evaluation window, so differences in
  processed scope do not break comparability of the scores.
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

- No existing Maple Creek 2017 catalogs, published picks, known locations or other
  reference products may be used to construct or tune the result.
- Values must not be fabricated; empty-but-honest is always acceptable.
- The framework boundary rules (read-only input view, writable `$BENCH_OUTPUT`,
  no reference/hidden materials) apply to all variants via `framework.md`.

## Scoring wiring status

All task specs declare `evaluation.scorers` and reference a machine-checkable
`output_contract`, so `python -m SeismoAgentBench evaluate` validates CSV
columns (`artifact-contract@1`) out of the box. `phase-picking-basic@1` is
declared and will be recorded as `skipped` until a reference picks CSV is
passed via `--pick-reference`. The same two wiring gaps as the Ridgecrest
case apply and are deliberate: no event-level `catalog-basic@1` scorer for
the CSV contract, and a column-name adapter
(`station_id`→`station`, `time_utc`→`arrival_time_utc`) needed before
`phase-picking-basic@1` runs. Event-level scoring in practice goes through
`evaluation/scripts/evaluate_run.py` (greedy 4 s / 15 km matcher against
the expert catalog and ComCat; origin time only, 1 s, against Shelly, with a
60-s shifted-reference chance count; see `evaluation/README.md`).

## Cost and sequencing

The window is eight days / ~4.4 GB of MiniSEED, on CPU-only hardware. No
Maple Creek agent run has completed yet; the first `min` run also sets the
empirical cost record for this case.

1. `min` — capability baseline (Q1), scored against the expert reference.
2. `tools`, `guided` — each vs `min`, same agent and model; repeat key cells
   at least twice before attributing deltas to the factor.
3. `ris` — after the feedback-loop design is settled.

When comparing variants, prefer same agent, same model, same reasoning effort
and `RUN_ID` timestamps close together.

## Running

```bash
cd workflows/tasks/2017_maple_creek_yellowstone
VARIANT=min bash run.sh                      # min is the default
AGENT=claude VARIANT=tools bash run.sh       # any arm through Claude Code
```

Runs land in `runs/<variant>/<harness>/<model>/<timestamp>/` (one experiment
factor per path segment) with the usual control/work/record layout. The
runner accepts any `task_<variant>.json` present in this directory, so the
future `ris` arm will not require editing `run.sh`.
