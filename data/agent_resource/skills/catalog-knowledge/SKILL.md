---
name: catalog-knowledge
description: Workflow and decision rules for building an earthquake catalog from continuous waveforms - the stages in order (picks, association, absolute location, template matching, relative relocation, magnitudes, submission), what to do by default at each, which catalog-checker stage gates it and what must hold before moving on, when to deviate, and scripts for the error-prone steps. Use from the start of a catalog task and whenever a checker flag appears or a change to a product is considered.
---

# Building an earthquake catalog

Follow the stages in order. Each ends with a checker run (`CHECKER_PATH/interface/run.py --stage <stage>`); handle its flags as the stage file says before the next stage uses the products. Copy the checklist into your notes and tick it off; record every decision with its evidence.

```
Catalog progress:
- [ ] 0 Plan and pilot: data inspected; settings tried on a pilot batch       -> reference/pilot_and_compare.md
- [ ] 1 Picks: three-component stations picked; any added pick group tested   -> stages/01_picks.md
- [ ] 2 Association: events formed; association flags handled                 -> stages/02_association.md
- [ ] 3 Absolute location: model chosen from regional knowledge; depth flags
        handled; unconstrained depths reported as expectations; events beyond
        the network rejected                                                  -> stages/03_absolute_location.md
- [ ] 4 Template matching: run, threshold from a null test, detections merged -> stages/04_template_matching.md
- [ ] 5 Relative relocation: run where events are dense; frame checked        -> stages/05_relative_relocation.md
- [ ] 6 Magnitudes: standard implementation, units verified, regional calibration -> stages/06_magnitude.md
- [ ] 7 Submission: checker --stage all on the final files; a disposition with
        evidence for every flag; check_submission.py passes                   -> stages/07_submission.md
```

| Stage | Default | Checker gate | Before moving on | Deviate only when |
|---|---|---|---|---|
| 0 Plan and pilot | inspect stations, channels, gaps; try picking, association and location settings on a pilot batch (`pilot.py`) | `--stage data`; `--pilot` runs | code and units verified on the pilot; settings frozen for the full run | — |
| 1 Picks | a deep-learning picker on three-component records | `--stage picks` | every station without picks explained; a pick group added for silent stations passed `scripts/compare_pick_groups.py` | a group whose residual spread is several times the others' is left out |
| 2 Association | settings tuned on the pilot for the sequence's event rate | `--stage association` | flags handled | — |
| 3 Absolute location | a published regional model with its datum and representation; probabilistic location with the search starting at the stations' level; station corrections | `--stage location` | depth piles explained or repaired; a depth flag above its limit corrected in its direction; `scripts/expectation_hypocentres.py` for events unconstrained in depth; `scripts/drop_beyond_network.py` | no regional model can be obtained: generic model with the near-surface procedure, said so |
| 4 Template matching | required for a sequence: templates from located events, threshold from a null test, detections merged into the catalog | `--stage location` on the merged catalog | detections merged and marked as detections | too few usable templates; say how many and why |
| 5 Relative relocation | where events are dense: cross-correlation and catalog differential times with hypoDD or GrowClust | `--stage relocation` | frame shift and large moves explained | events sparse or too few links; say so |
| 6 Magnitudes | the reference implementation in `../../magnitude/`, regional calibration | `--stage magnitude` | recomputation agrees; largest events measured | — |
| 7 Submission | `--stage all` on the files you submit | `check_submission.py` of the catalog-checker skill | it passes | — |

## Principles

1. **A flag is a symptom, not a verdict, and flags differ in how much they tell.** Some flags reliably mean an error (fix them); others are weak (investigate once and report). `reference/flag_reliability.md` says which is which. Never change a product only to make a check pass.
2. **A flag gives a direction, not a correction.** Do not adopt a change because it brings a checker measurement to its expected value: several wrong changes do that too. Judge a change by independent evidence (geology, near-station S−P times, independent catalogs or events) and by `compare.py` on the full products.
3. **Write the adoption rule before the experiment**, then keep it. If you break it, say why in the record.
4. **Prepare on a pilot, decide on the full run** (`reference/pilot_and_compare.md`).
5. **Fit is not evidence of location.** Lower residuals or RMS do not show that events are better placed; a model with more freedom fits better by construction.
6. **A fix is a change too.** Data, picks or events added to answer a flag can bring new errors; test them like any other change.

## Where things are

- Stage files: `stages/01_picks.md` … `stages/07_submission.md`, each with the decision rules and the flags of that stage.
- `reference/flag_reliability.md`: how much each flag tells you and how to act on it.
- `reference/pilot_and_compare.md`: pilot batches, `compare.py`, experiments that separate the causes of a symptom.
- `reference/not_visible.md`: errors no check sees (the velocity model on average, the near surface, building a 1-D model from the data, the horizontal frame, the magnitude level, timing). Read it before choosing a velocity model.
- `scripts/`: `compare_pick_groups.py`, `expectation_hypocentres.py`, `drop_beyond_network.py` (run with `--help`).
- Magnitudes: `../../magnitude/README.md` and `ml_reference.py`.
