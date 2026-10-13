# Ridgecrest prompt variants

A minimal single-factor family built around the experiment's research
questions. Every arm shares the same input, output schema and scoring; each
arm differs from the control (`min`) by exactly one factor, so score deltas
attribute to that factor and nothing else.

## Research questions → variants

| Question | Contrast | Arm |
|---|---|---|
| Q1. Can a general-purpose agent complete seismic monitoring on its own and reach expert-level results? | `min` vs the expert reference (`expert/` workflow) | `min` |
| Q2. Do expert tools matter? | `tools` vs `min` | `tools` |
| Q3. Does expert experience matter? | `guided` vs `min` | `guided` |
| Q4. Is RIS needed in a feedback-driven workflow? | `ris` vs `min` — future arm, design pending | — |

The expert level in Q1 is not a prompt variant: it is the result of the
`expert/` scientific workflow (and published references), used as the scoring
benchmark for every arm.

## Variant matrix

| Variant | Task spec | Differs from `min` by | Guidance | Scope | Tool policy | Contract |
|---|---|---|---|---|---|---|
| `min` | `task_min.json` | — (control arm) | minimal | unspecified | unspecified | min |
| `tools` | `task_tools.json` | + `### Tools`: local PhaseNet / GaMMA / NonLinLoc / hypoDD with validated usage docs | minimal | unspecified | local provided | min |
| `guided` | `task_guided.json` | + expert scaffolding: fixed three-day window, pipeline stages, QC gates, tuning discipline, report | expert-scaffolded | fixed window | neutral public | default |

Contracts: `output_contract_min.json` (picks + catalog) and
`output_contract.json` (picks + catalog + report.md).

## Design decisions

- **Scope.** `min` and `tools` deliberately do not state a processing window:
  self-scoping is part of what Q1 measures, and adding a window to `tools`
  would confound the Q2 contrast. `guided`'s fixed window
  `[2019-07-04T00:00:00Z, 2019-07-07T00:00:00Z)` is itself part of the
  expert-experience treatment. All arms are scored on the same evaluation
  window, so differences in processed scope do not break comparability of the
  scores.
- **What ships with tools.** The `tools` arm carries the tools' validated
  usage notes (the PhaseNet example, the 100 Hz resampling rule) because they
  are part of the tool package. The legacy variant's workflow mandates
  (mandatory stage ordering, execution/repair rules) were deliberately not
  carried over — those are guidance, not tools.
- **Contracts.** `min` and `tools` use the same two-artifact contract so the
  Q2 contrast changes output requirements not at all; `guided` adds
  `report.md` because reporting discipline is part of expert experience.
- **One factor per contrast.** Agent, harness and model are replication
  dimensions (run the same arm across `claude` / `codex` and models), not
  variants.

## Validity conditions common to every variant

- No existing Ridgecrest catalogs, published picks, known locations or other
  reference products may be used to construct or tune the result.
- Values must not be fabricated; empty-but-honest is always acceptable.
- The framework boundary rules (read-only input view, writable `$BENCH_OUTPUT`,
  no reference/hidden materials) apply to all variants via `framework.md`.

## Scoring wiring status

All task specs declare `evaluation.scorers` and reference a machine-checkable
`output_contract`, so `python -m SeismoAgentBench evaluate` validates CSV
columns (`artifact-contract@1`) out of the box. `phase-picking-basic@1` is
declared and will be recorded as `skipped` until a reference picks CSV is
passed via `--pick-reference`.

Two wiring gaps are known and deliberate:

1. **Event-level catalog scoring** (`catalog-basic@1`) is not declared because
   that scorer requires the framework's JSON catalog artifact, while the task
   contract uses `catalog.csv`. Wiring it needs either a CSV catalog scorer or
   a declared conversion step.
2. **Column-name mismatch in `phase-picking-basic@1`**: the scorer reads
   `station`, `phase`, `arrival_time_utc`
   (`SeismoAgentBench/scoring/picks.py` REQUIRED_COLUMNS) while the task
   contract uses `station_id` and `time_utc`. Before scoring, a thin adapter
   must map `station_id` → `station` and `time_utc` → `arrival_time_utc`.
   The reference picks CSV must be authored in the scorer's column vocabulary.

## Cost and sequencing

Fixed-window guidance (`guided`) and, in practice, the self-scoped arms
process days of waveform data (≈5 GB for three days) on CPU-only hardware
and fit the default budget. The 2026-10-13 legacy-baseline claude run
completed a self-scoped three-day build in 3 h 09 m / $19.45, which doubles
as the pipeline-validation record.

1. `min` — capability baseline (Q1), scored against the expert reference.
2. `tools`, `guided` — each vs `min`, same agent and model; repeat key cells
   at least twice before attributing deltas to the factor.
3. `ris` — after the feedback-loop design is settled.

When comparing variants, prefer same agent, same model, same reasoning effort
and `RUN_ID` timestamps close together.

## Running

```bash
cd workflows/tasks/2019_ridgecrest_california
VARIANT=min bash run.sh                      # min is the default
AGENT=claude VARIANT=tools bash run.sh       # any arm through Claude Code
```

Runs land in `runs/<variant>/<harness>/<model>/<timestamp>/` (one experiment
factor per path segment) with the usual control/work/record layout. The
runner accepts any `task_<variant>.json` present in this directory, so the
future `ris` arm will not require editing `run.sh`. Historical runs under
`runs/base/` used the retired legacy baseline prompt (preserved in that run's
`control/agent_prompt.md`).

## Retired variants

`base_standard`, `base_notools`, `base_full`, the legacy `base`, the legacy
two-hour `tools`, and earlier drafts (`pubtools`, `staged`) are archived under
`attic/` with rebuild recipes in `attic/README.md`.
