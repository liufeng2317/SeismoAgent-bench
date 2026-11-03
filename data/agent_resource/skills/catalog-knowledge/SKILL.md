---
name: catalog-knowledge
description: Procedural knowledge for building an earthquake catalog from continuous waveforms - how to test a workflow on a pilot batch before the full run, how to decide between two candidate products with the catalog checker, what each checker symptom can mean and which experiment separates the causes, and which errors no check can see. Use when planning a catalog workflow, when a checker flag appears, or before adopting any change to a product.
---

# Catalog knowledge

This skill holds what an analyst knows before looking at the data: how to organise the work so that long computations are not wasted, and how to turn checker symptoms into decisions. It complements the tools in `seismotools/` (the checker is `seismotools/checker/interface/run.py`, with `compare.py` and `pilot.py` beside it). Read only the file you need.

| When | Read |
|---|---|
| Planning the workflow; before any long computation | [`protocol/pilot_then_full.md`](protocol/pilot_then_full.md) |
| About to adopt a change to a product (model, locator, parameters, filters) | [`playbooks/decide_between_candidates.md`](playbooks/decide_between_candidates.md) |
| `compare.py` says `mixed` or `uncertain`, or a change raises a depth pile-up or layers | [`playbooks/decide_between_candidates.md`](playbooks/decide_between_candidates.md) §3 |
| A checker flag or measurement you need to explain: candidate causes, the experiment that separates them, the repair | [`symptoms/README.md`](symptoms/README.md), then the file for the stage |
| Errors no check can see (velocity model on average: its datum, layers or nodes, and how to constrain the near surface without a regional model; magnitude calibration level; events in a mainshock's coda) — read before choosing a velocity model and before computing magnitudes | [`symptoms/not_visible.md`](symptoms/not_visible.md) |
| Local magnitudes: formulas, units, calibration | [`../../magnitude/README.md`](../../magnitude/README.md) |

Three rules hold throughout:

1. **Symptoms are not verdicts.** A checker flag says a product is outside an expected range; it does not say why. Do not explain a flag away in words: find the cause with an experiment, or report the flag with the evidence that it is not an error.
2. **Decide on the full run, prepare on a pilot.** A pilot batch shows errors of code and tool use and predicts what a change will do; whether to adopt the change is decided on the full products.
3. **Write the adoption rule before running the experiment.** State what result would make you adopt the candidate, then run it. Record the decision and its evidence.
4. **Choose the velocity model from what is known about the region, not from fit.** Lower residuals or checker measurements closer to their expected values (S−P depths, Wadati origin times, travel-time intercept, depth distribution) do not show that a model places events better; use them to check a model, not to select it (`symptoms/not_visible.md`).
