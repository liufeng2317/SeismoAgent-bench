# How much a flag tells you

Checked on six analyst catalogs and about forty Agent catalogs whose errors were known from published catalogs. A flag is worth acting on to the degree it separated catalogs with the error from catalogs without it.

| Flag | What it reliably tells you | How to act |
|---|---|---|
| `magnitude_recompute` | a unit, constant or response error in your magnitude code: every such error was flagged, no other catalog was | find and fix the error; do not justify it |
| `depth_single_value` | a pile at one depth: every catalog that piled was flagged | find the cause (stage 3 table); repair or report expectations for unconstrained events |
| `pick_onset_offset`, `duplicate_picks`, `processing_time_shift` | errors with a signature of their own | fix them |
| `sp_depth_offset` above its limit | the direction of a depth error: right in every case above the limit, no better than chance below it | correct in that direction; the value is not the size of the correction |
| `wadati_origin_offset` | only gross origin-time errors (beyond 1.5 s); smaller values did not follow the true origin-time bias | fix a flagged gross error; do not tune the model to its value |
| `depth_layers`, `depth_at_edges` | sometimes a representation artefact, often nothing: they flagged many catalogs with correct depths | run the representation experiment once; if the slices stay, report them |
| `wadati_origin_spread` | weakly related to origin-time errors | check S picks and Vp/Vs once; report |
| `isolated_events`, `events_with_few_picks` | how well events are constrained, not whether they are right | look at a sample; do not lower or raise association settings only to move them |
| `largest_events_magnitude`, `magnitude_detection` | weak beyond the unit errors that `magnitude_recompute` already catches | measure the largest events properly; otherwise report |
| `silent_stations` | stations you do not use, which is a configuration question | find the reason; add their picks only after `scripts/compare_pick_groups.py` |

Two consequences:

1. **Fix the reliable flags; investigate the others once and report.** A weak flag that stays after one honest experiment is justified by that experiment; it is not a reason to keep changing the product.
2. **No flag gives the size of a correction.** Do not adopt a change because a measurement reached its expected value.
