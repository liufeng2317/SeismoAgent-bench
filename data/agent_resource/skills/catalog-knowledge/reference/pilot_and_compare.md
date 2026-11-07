# Pilot batches, comparing candidates, attributing a symptom

## Contents
1. Pilot level: is the code right, and what will a change do?
2. Full level: is it right, and do we adopt it?
3. Comparing two candidates with `compare.py`, and experiments that separate causes
4. How far a cause can be established

Picking, association, location, relocation and template matching over weeks of continuous data take hours each. A mistake found after the full run costs the whole run. Most mistakes, however, show on a small part of the data. Work in two levels.

## 1. Pilot level: is the code right, and what will a change do?

Choose the batch with `CHECKER_PATH/interface/pilot.py`, not by hand:

- before any catalog exists (picking and association settings): `pilot.py windows --waveforms ... --stations ... [--picks first_pass_picks.csv] --extract`;
- once a first catalog exists (velocity model, locator, relocation, magnitude code): `pilot.py events --catalog ... --picks ...`.

A pilot has three parts. Use each for its own question:

| Part | Share | Use it for |
|---|---|---|
| representative | 60 % | the effect of a change on the whole catalog: median shift of depth and origin time, share of events located, run time per event |
| busiest | 20 % | behaviour at the highest event rate: missed or merged events, association time, memory |
| largest | 20 % | clipped records, long S trains, magnitudes of the largest events |

Do not use "the best-recorded events" as a stand-in for the catalog: they can move in the opposite direction from the full catalog when the model changes.

On the pilot, check:

- **code and tool use**: units (nm vs mm vs m; km vs m), sign and datum conventions (depth below sea level vs below the station or the model datum; station elevations), instrument response and Wood-Anderson response, column names and time formats. These errors affect every event alike, so the pilot shows them as clearly as the full run. Compare a few values with an independent computation (for magnitudes: `../../../magnitude/ml_reference.py recompute`).
- **checker, item checks**: run the checker with `--pilot`. Checks of scope `item` (picks, Wadati, travel-time fit, S−P depth, magnitudes recomputed) are judged; checks of scope `population` are reported without a verdict.
- **run time**: time per event or per hour of data, extrapolated to the full run.
- **candidates**: run each candidate on the same pilot and compare their medians (how far depths and origin times move). Drop candidates that fail item checks; keep the rest for the full run.

What a pilot cannot tell you: the distribution of the full catalog (pile-ups at one depth, thin depth layers, completeness, b-value, isolated events), and therefore whether a candidate is better. Two candidates that look the same on 300 events can differ clearly on the full catalog, and the other way round.

## 2. Full level: is it right, and do we adopt it?

1. Freeze the code and the parameters chosen at the pilot level.
2. Run the full data.
3. Run the checker on the full products without `--pilot`; with two candidates, run it on both and use `compare.py` (§3).
4. Compare the full result with what the pilot predicted (median shifts). A large difference means the change acts differently on different events (e.g. events pinned at a bound move far more than the rest); look at those events before adopting.
5. Record which decisions were taken at which level, and why.

## 3. Comparing two candidates

Use this before adopting any change: another velocity model or representation, another locator or method, other picking or association parameters, added picks, a filter that removes events, new magnitude code.

1. Build both products from the same input (same picks for a location change, same waveforms for a picking change) over the full data.
2. Run the checker with the same stage and inputs on each (`--output-dir chk/current`, `--output-dir chk/candidate`).
3. `compare.py --before chk/current/checker_report.json --after chk/candidate/checker_report.json --change <velocity_model|location_method|picks|association|event_selection|relocation|magnitude|other> --output compare.json`.

Write down beforehand what you will adopt and on what evidence.

| Verdict | Meaning | Next |
|---|---|---|
| `better` | at least one check improves, none worsens | adopt, unless flags remain: a candidate that still fails is less wrong, not right |
| `worse` | at least one check worsens, none improves | keep the current product, unless the worsening is one of the artefacts below; then run that experiment |
| `mixed` | some improve, some worsen | do not count checks; run the experiment that separates the explanations |
| `uncertain` | the improvement comes only from shares while the candidate drops events | restrict both to their common events and compare again |
| `no_difference` | nothing changes beyond the noise | keep the simpler or better-documented product and say why |

The verdict says which product the checks prefer, not that either is right. If every candidate fails the same checks, look for better knowledge (a regional model, station corrections, another locator) rather than the least bad candidate.

**Experiments that separate the causes** (run on the events concerned plus a random 200 others for contrast):

- *A pile at one depth or thin layers with a layered model:* relocate as a linear gradient between the model's nodes and, separately, with a 0.1 km travel-time grid. A representation artefact disperses with the gradient and moves onto the interface with the fine grid; then build both full candidates and compare. A pile that stays with both points to the model. Piles of poorly constrained events (few phases, large gap and uncertainty, no S within 1.4 focal depths) point to the representation; well-recorded events in a pile to the model.
- *A pile at the shallowest depth or the search top:* check that the reference elevation equals the model datum and that the search starts there; compare with S−P depths at near stations; if the geology has a slow surface layer, try a model with one. A pile that goes away with the right datum was a usage error.
- *S−P depths improve but piles or layers worsen:* if the pile is a representation artefact, adopt the candidate in its gradient form; otherwise neither model is right.
- *Origin-time scatter worsens with a new model:* compare the model's Vp/Vs with the data's Wadati Vp/Vs (rules in `../stages/03_absolute_location.md`).
- *A candidate with lower RMS:* not a reason to adopt it; a model can fit better and place events worse.

Record for each decision: the candidates, the reports, the verdict, the experiment, the rule written beforehand and the decision.

## 4. How far a cause can be established

- **A, from the data:** the error has a signature of its own (a round value, a quantised offset, one station or phase, a step in time). A cheap check settles it. Repair it.
- **B, with an experiment:** several causes give the same symptom; one controlled change (another representation, another grid, one station or phase left out, one period reprocessed) separates them. Write down what each cause predicts, then run it.
- **C, not without external information:** the error is shared by all stations or events and absorbed by origin times, station terms or the magnitude constant. No check sees it: `not_visible.md`.

Two habits: keep a record of what produced every product (code, parameters, model, inputs), since most causes are found by asking what changed; and do not take formal errors or RMS as evidence that a product is right.
