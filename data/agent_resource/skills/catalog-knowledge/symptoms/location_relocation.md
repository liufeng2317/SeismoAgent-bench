# Location and relative relocation

Start every location problem by reading `depth_constraint` in the checker report: the share of events with an S pick at a station closer than 1.4 × the focal depth, the GT-like geometry share (≥ 10 stations, azimuthal gap < 110°, secondary gap < 160°, nearest station < 30 km), and the make-up of the most common depth. A correctly timed S within 1.4 focal depths constrains depth to about ±1.5 km; without it, a few percent of velocity error moves depths by several km while the formal errors stay small.

## Depth pile-ups

**`depth_single_value` / `depth_at_edges` — many events at one depth.** Read the `depth_constraint` details first, and pass the location set-up to the checker (`run.py --location-setup setup.json` with interfaces, search bounds, grid spacing and origin, trial depth, all in km below sea level) so that `pile_against_setup` reports the distance of the pile to each feature.

| Make-up of the pile | Most likely cause | Tier | Evidence / experiment | Repair |
|---|---|---|---|---|
| a round value (whole or half km), events with or without constraint | a fixed depth or the locator's trial/default depth | A | the value equals a depth in your configuration; those events did not converge or depth was held fixed | free the depth, or flag those events as depth-fixed in the catalog; never fix depth silently |
| at the top or bottom of the search region; events without depth constraint | the search bounds | A | the value equals a bound in `pile_against_setup` | widen the bounds; check that the reference elevation equals the model datum and that the search starts at it |
| at the shallowest depth, many events, S−P depths deeper (`sp_depth_offset`) | near-surface velocity too fast, or the datum wrong (events pushed above the model top) | B | relocate the piled events with the reference elevation at the model datum and the depth search starting there; then with a slow surface layer if the geology has one (sediment, basin fill, volcanic deposits) | the set-up that removes the pile without moving the constrained events |
| at or next to a layer interface (within one grid spacing); mostly poorly constrained events | the step representation of the model: poorly constrained events are trapped at the interface, and a coarse travel-time grid moves the pile to the grid node next to it | B | relocate the piled events plus a random 200 others with (a) the same model as a linear gradient between its nodes and (b) a finer travel-time grid (0.1 km). An artefact disperses with (a) and moves onto the interface with (b) | build both full candidates (gradient version; step version judged without the pile checks) and compare each with the current catalog — which representation is better differs between regions |
| not round, not at a set-up feature, mostly constrained events | the velocity model, or real structure | B/C | relocate with another model (`--model-ensemble` measures how far depths depend on the model); compare with S−P depths | see `../playbooks/decide_between_candidates.md` and `not_visible.md` |

**`depth_layers` — thin depth slices with many more events than their neighbours.** Same causes as interface piles; with a correct layered model they also form at its interfaces, so this check alone cannot rank two models. Use the interface experiment above.
- Real seismicity can also concentrate at one depth. Before changing the model or its representation to remove a slice, check whether the events in it are well constrained (S within 1.4 focal depths, many picks) and whether their S−P depths agree with the slice; a slice of well-constrained events that S−P times confirm is structure, not an artefact.

## Depth and origin-time offsets

**`sp_depth_offset` — depths implied by S−P times at stations closer than the source differ from catalog depths.** Tier B. S−P depths depend on Vp/Vs and on S picks, not on the absolute velocity, so they are an independent check of depth.
- Causes: velocity model too fast or slow near the sources; wrong depth datum (depths below the surface reported as below sea level, or the reverse); S picks late or early (converted phases picked as S make depths wrong by km while errors shrink); origin times biased.
- Evidence: an offset equal to the station elevation or the model datum points to the datum (tier A); an offset that grows with depth points to the velocity; an offset that comes only from a few stations points to their S picks.
- Below its limit the sign of the difference is not reliable: velocity structure alone moves it by about 1 km.
- The check reads catalog depths as kilometres below sea level (the output convention). Depths from a locator that measures them below a reference elevation, or that puts stations at the model's top (HypoInverse CRH), differ by about one station elevation: convert before reading the check.
- Its scale comes from the distant stations' S−P times; where the near-surface Vp/Vs differs strongly from deeper down, the implied depths carry an offset of up to a kilometre or more. Do not drop station corrections or change Vp/Vs only to remove this flag; test the change on the other evidence first (Wadati origin times, the depth distribution, the residuals).

**`wadati_origin_spread` — origin times from the event's own S−P times scatter about the catalog origin times.** Tier B: wrong S picks, Vp/Vs of the model unlike that of the data, or unstable locations. Compare the model's Vp/Vs with the data's Wadati Vp/Vs (`wadati_origin_offset` details: `median_vpvs`); relocate with Vs scaled to it.

**Origin times early or late as a whole, depths deep or shallow as a whole.** Tier C when all stations agree: see `not_visible.md`.

## Horizontal structure

**`isolated_events` — events far from all others.** Tier B: false associations (check their picks: few picks, picks from distant stations only), events outside the network with poor geometry (gap > 180°), or real isolated seismicity. Large events must not be removed by a location-quality rule: the largest events are often isolated early in a sequence and have the worst geometry for their first picks.

**`events_outside_network` (reported).** Real seismicity can lie outside; locations there have large, elongated errors in the direction away from the network. Report them with their errors; do not shift them.

## Relative relocation (double difference, cluster-based)

**`relocation_shift` — the catalog moved as a whole during relative relocation.** Tier B. Relative relocation should not move the centroid by more than the absolute location error. Causes: a few events with many links dominating, absolute times weighted too strongly, a different velocity model or reference elevation in the relocation than in the absolute location. Evidence: compare the models and datums of the two steps; relocate with catalog differential times only, with cross-correlation times only, and with both.

**`relocation_thinning` — local structure much thinner after relocation.** Tier B.
- Causes: real sharpening; or collapse by over-weighted cross-correlation times, too few observations per pair, poorly conditioned clusters (hypoDD: condition number far above 40–80).
- Evidence: bootstrap the residuals (50–100 resamples) or jackknife by station: real structure keeps its width; an artefact changes; streaks whose bootstrap ellipses are elongated along the streak are artefacts. Check that every pair has ≥ 8 observations and that differential times from templates (detections that inherit their template's location) are not in the catalog differential times.

**`relocation_large_moves` — many events moved by more than 5 km.** Tier B: poorly linked events (few neighbours, weak links), events far from their cluster, or a wrong pick set. Relocate those events alone with a different starting location; events that move back were unstable.

**`relocated_share` low — few events with enough picks were moved.** Tier A/B: linking thresholds too strict (minimum links, maximum separation), cross-correlation computed for a subset only, events outside the clusters. Not an error when the events are small and isolated.
- Do not loosen the linking thresholds only to raise the share. Events relocated on too few differential times move to wrong places and scatter the catalog; the tools' READMEs say which minimum numbers of links are safe. If you wrote an adoption rule for the relocation settings, keep it unless an experiment shows the stricter setting is wrong; justify the flag with the number of events that lack enough links instead.
