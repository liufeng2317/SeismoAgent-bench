# Deciding between two candidate products

Use this before adopting any change: another velocity model or layering, another locator or location method, other picking or association parameters, a filter that removes events, new magnitude code.

## 1. Compare like with like

1. Build both products from the same input (same picks for a location change, same waveforms for a picking change) over the full data.
2. Run the checker with the same stage and the same inputs on each:
   `run.py --stage location --catalog current.csv --picks picks.csv --stations ... --output-dir chk/current`
   `run.py --stage location --catalog candidate.csv --picks picks.csv --stations ... --output-dir chk/candidate`
3. `compare.py --before chk/current/checker_report.json --after chk/candidate/checker_report.json --change velocity_model --output compare.json`
   (`--change`: velocity_model, location_method, picks, association, event_selection, relocation, magnitude, other.)

Before running, write down what you will adopt: e.g. "adopt the candidate if compare says `better`, or if the experiment in §3 shows the only worsening is a representation artefact".

## 2. Reading the verdict

| Verdict | Meaning | Next |
|---|---|---|
| `better` | at least one check improves, none worsens | adopt, unless flags remain (`flags_after`): a candidate that still fails is less wrong, not right; look for what still causes those flags |
| `worse` | at least one check worsens, none improves | keep the current product, unless the worsening is one of the artefacts in §3 — then run that experiment first |
| `mixed` | some checks improve and others worsen | do not count checks; run the experiment of §3 that separates the explanations |
| `uncertain` | the improvement comes only from shares while the candidate drops events | restrict both catalogs to their common events, re-run the checker on both and compare again |
| `no_difference` | nothing changes beyond the noise | keep the simpler or better-documented product; the checker cannot tell them apart, so state which you chose and why |

The verdict says which product the checks prefer, not that either is right. If every candidate still fails the same checks, look for better knowledge (a regional velocity model, station corrections, a different locator) rather than choosing the least bad.

## 3. Experiments that separate the explanations

Run the experiment on the events concerned (for a pile-up: the events in the pile, plus a random 200 others for contrast). This is a diagnostic subset, not a pilot: it is chosen because of the symptom.

**A pile-up at one depth, or thin depth layers, appears with a layered velocity model.**
- Explanations: (a) a representation artefact: with step layers, poorly constrained events collect at a layer interface; with a coarse travel-time grid (e.g. 0.5 km) the pile sits at the grid node next to the interface, so it may look as if it were not on an interface; (b) the model is wrong for these events.
- Experiment: relocate the piled events with the same model as a linear gradient between its nodes (`velocity_layering: linear`, or densified nodes), and separately with a finer travel-time grid (0.1 km).
- Reading: if the pile disperses with the linear model, or moves onto the interface with the finer grid, it is (a). Then build both full candidates — the linear representation, and the step model judged without this check — and compare each with the current product: the representation also changes origin times and the share of events that leave the region, and which representation is better differs from model to model. If the pile stays where it was with both, it is (b).
- Check the piled events' quality too (number of phases, azimuthal gap, RMS): piles made of poorly constrained events point to (a); well-recorded events in a pile point to (b).

**A pile-up at the shallowest depth or at the top of the search region.**
- Explanations: the reference elevation is not the model's datum (events are pushed above it); the depth search starts at the wrong level; the near-surface velocity is too fast (a slow surface layer such as basin fill is missing).
- Experiment: check that the location's reference elevation equals the model datum and that the depth search starts there; compare the catalog with the depths implied by S−P times at stations closer than the source depth (checker `sp_depth_offset`, independent of the model); if a slow surface layer is plausible from the geology, try a model with one.
- Reading: a pile that goes away with the right datum was a usage error. A pile that remains while S−P depths say the events are deeper points to the near-surface velocity.

**S−P depths improve but pile-ups or layers worsen** (the candidate model moves depths the right way on average but cannot fit some events).
- Experiment: as above for the pile; also look at RMS per event and residuals per station for the piled events.
- Reading: if the pile is a representation artefact, adopt the candidate in its linear form. If not, neither model is right: look for a model with the missing structure.

**Origin-time scatter (Wadati spread) worsens with a new model.**
- Explanations: the model's Vp/Vs differs from that of the data.
- Experiment: compare the model's Vp/Vs with the Wadati Vp/Vs of the picks (checker report, `wadati` details); relocate with Vs scaled to the data's Vp/Vs.

**Lower travel-time residual (RMS).** Do not use it to choose a model: a model can fit the picks better and still put the events in the wrong place. A model with more freedom fits better by construction.

## 4. Record

For each decision: the candidates, the checker reports, the compare verdict, the experiment and its result, the rule written beforehand, and the decision. The record is part of the output.
