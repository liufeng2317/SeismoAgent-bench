# Ridgecrest base-prompt variants

This package ships a **canonical family of five base variants** plus two
legacy controls, organized as a three-phase experiment. Every variant is one
canonical prompt with one or two well-defined modules changed, so that score
differences between runs can be attributed to a specific factor — agent
capability, prompt guidance, or tool policy — instead of a mixed bag of
wording changes.

## Experiment logic

```
Phase 0  pipeline validation   base_standard                      1–2 cheap runs
Phase 1  factor matrix         every axis at fixed-window scope    same scoring population
           guidance axis       base_min  <  base_standard  <  base_guided
           tool axis           base_notools  <  base_standard  <  legacy tools (+)
           agent axis          base_standard × { agents, models, reasoning efforts }
Phase 2  flagship             base_full                          full archive, best ideas
```

**Why every factor variant uses the fixed window.** All guided comparisons run
inside `[2019-07-04T00:00:00Z, 2019-07-07T00:00:00Z)` (daily files
2019-07-04/05/06, ≈5 GB): same event population, low compute cost, and the
run fits the default budget, so differences reflect the factor under test
rather than how much archive happened to be reached. `base_full` is the only
full-archive variant (≈36 GB); its scope section instructs the agent to
complete and checkpoint the core window before extending, keeping it
comparable on the window subpopulation too.

`base_min` is the one deliberate exception on scope: stating a window would
itself be guidance, so the floor variant leaves scope unspecified and lets
self-bounding be part of what is measured.

## Variant matrix

| Variant | Task spec | Role | Guidance | Scope | Tool policy | Contract |
|---|---|---|---|---|---|---|
| `base_standard` | `task_base_standard.json` | control arm + phase 0 | professional | fixed window | neutral public | standard |
| `base_min` | `task_base_min.json` | guidance floor | minimal | unspecified | unspecified | min |
| `base_guided` | `task_base_guided.json` | guidance ceiling | expert-scaffolded | fixed window | neutral public | standard |
| `base_notools` | `task_base_notools.json` | tool floor | professional | fixed window | classical only | standard |
| `base_full` | `task_base_full.json` | full-archive flagship | professional | full archive (core first) | neutral public | standard |
| `base` (legacy) | `task.json` | framework-behaviour control | original knowledge-light | full archive | unspecified (de facto open) | none — prose only |
| `tools` (legacy) | `task_tools.json` | tool ceiling | fixed chain | fixed 2-hour window | curated local snapshots | none — prose only |

Contracts: `output_contract_min.json` (picks + catalog) and
`output_contract_standard.json` (picks + catalog + report.md).

## Contrasts and what they isolate

- **Guidance axis** — `base_min` vs `base_standard` vs `base_guided`: the value
  of prompt engineering itself (contract precision, scope ruling, checkpoint
  discipline) and of expert process knowledge (pipeline stages, QC gates,
  tuning discipline). Zero Ridgecrest facts anywhere on this axis.
- **Tool axis** — `base_notools` vs `base_standard` vs legacy `tools`:
  classical-only methods vs anything public (neutral framing) vs curated
  local snapshots with a mandated chain.
- **Agent axis** — hold `base_standard` fixed, vary agent/model/effort.
  `base_min` doubles as the bare-capability probe.
- **Scope/cost axis** — `base_standard` vs `base_full`: what the same guidance
  buys when the archive is 7× larger and the budget is not.

## Module map (for recombination)

The professional-guidance prompts (`standard`, `guided`, `notools`, `full`)
are assembled from stable sections. To build a new combination (for example a
guided full-archive run), copy the closest prompt and replace only the
relevant section:

- `### Processing scope` — fixed window / full archive with core-first
  priority. The window section is shared verbatim by `standard`, `guided` and
  `notools`; keep it verbatim when recombining.
- `### Tool policy` — neutral public / classical-only (see `notools`) /
  public-ecosystem-encouraged (retired draft in `attic/`).
- `### Suggested workflow structure` — present only in `guided`.
- `### Workflow discipline`, `### Reproducibility`, `### Required scientific
  outputs`, `### Inspection and visualization`, `### Final report` — shared
  verbatim across the professional-guidance family, with two declared
  exceptions: `full` says "declared processing scope" where the window
  variants say "declared window" (its scope genuinely is the archive), and
  `guided` adds two scaffold-relevant enrichments (a checkpoint example in
  `Workflow discipline`, a quality-control bullet in `Final report`).

Keep the shared sections verbatim-identical between variants; attribution
breaks silently when unrelated wording drifts. Retired variants and their
rebuild recipes are documented in `attic/README.md`.

## Validity conditions common to every variant

- No existing Ridgecrest catalogs, published picks, known locations or other
  reference products may be used to construct or tune the result.
- Values must not be fabricated; empty-but-honest is always acceptable.
- The framework boundary rules (read-only input view, writable `$BENCH_OUTPUT`,
  no reference/hidden materials) apply to all variants via `framework.md`.

## Scoring wiring status

All canonical task specs declare `evaluation.scorers` and reference a
machine-checkable `output_contract`, so `python -m SeismoAgentBench evaluate`
validates CSV columns (`artifact-contract@1`) out of the box.
`phase-picking-basic@1` is declared and will be recorded as `skipped` until a
reference picks CSV is passed via `--pick-reference`.

Two wiring gaps are known and deliberate:

1. **Event-level catalog scoring** (`catalog-basic@1`) is not declared because
   that scorer requires the framework's JSON catalog artifact, while the task
   contract (and every prompt, legacy included) uses `catalog.csv`. Wiring it
   needs either a CSV catalog scorer or a declared conversion step.
2. **Column-name mismatch in `phase-picking-basic@1`**: the scorer reads
   `station`, `phase`, `arrival_time_utc`
   (`SeismoAgentBench/scoring/picks.py` REQUIRED_COLUMNS) while the task
   contract uses `station_id` and `time_utc`. Before scoring, a thin adapter
   must map `station_id` → `station` and `time_utc` → `arrival_time_utc`
   (channel is deliberately not part of the scorer key; rows with
   `status=rejected` are ignored by the scorer, which matches the contract's
   non-rejected counting rule). The reference picks CSV must be authored in the
   scorer's column vocabulary.

The legacy `base`/`tools` task specs intentionally keep their original shape
(no contract, no scorers) as controls for the framework-behaviour delta.

## Cost and recommended sequencing

Fixed-window variants (`standard`, `guided`, `notools`, and `min` in
practice) process ≈5 GB on CPU-only hardware and fit the default four-hour
budget. `base_full` processes ≈36 GB and needs `TIMEOUT` raised.

1. `base_standard` × 1–2 — phase 0: validates contract, scoring and the run
   record end to end, cheaply; the repeats also calibrate run-to-run variance.
2. Phase 1 matrix — guidance axis (`base_min`, `base_guided`), tool axis
   (`base_notools`, legacy `tools`), agent axis (`base_standard` across
   models). Repeat key cells at least twice before attributing deltas to the
   variant.
3. `base_full` — phase 2 flagship, with the best-performing configuration
   ideas from phase 1 (recombine modules per the map above if needed).

When comparing variants, prefer same agent, same model, same reasoning effort
and `RUN_ID` timestamps close together.

## Running

```bash
cd workflows/tasks/2019_ridgecrest_california
VARIANT=base_standard bash run.sh         # any canonical or legacy variant
VARIANT=base_full TIMEOUT=86400 bash run.sh
```

Runs land in `runs/<variant>/` with the usual control/work/record layout.
The runner accepts any `task_<variant>.json` present in this directory, so
new recombinations do not require editing `run.sh`.
