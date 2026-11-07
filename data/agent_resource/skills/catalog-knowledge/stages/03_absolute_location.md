# Stage 3: absolute location

Gate: `run.py --stage location --catalog catalog.csv --picks picks.csv --stations ... --location-setup setup.json` (`setup.json`: interfaces, search bounds, grid spacing and origin, trial depth, in km below sea level). Copy the locator's uncertainties and residuals into the optional columns (`horizontal_uncertainty_km`, `depth_uncertainty_km`; picks `residual_s`). Before template matching: depth piles explained or repaired, a depth flag above its limit corrected in its direction, unconstrained depths reported as expectations, events beyond the network rejected.

## Contents
- Decisions: velocity model; datum and search; station corrections; events unconstrained in depth; S−P depth flag; Vp/Vs from the data; events beyond the network
- Flags: depth piles; origin times; horizontal structure; the locator's uncertainties and residuals

## Decisions

**Velocity model.** Read `../reference/not_visible.md` before choosing.
- *Default:* a published 1-D model of the region, with only values you read in a source (table, text, or a figure digitised with its axes checked). Name the source.
- *Not:* a model rebuilt from memory or a verbal description must not carry the published model's name.
- *No regional model obtainable:* a generic column (CRUST1.0 at the stations) with the near-surface procedure of `../reference/not_visible.md`; say so.
- *Use it as built:* a stack of constant layers stays layered; a node model stays a gradient. Compare the other representation only as a candidate.

**Datum and depth search.** Find what the model's depths are measured from (sea level, mean station elevation, surface); use it as the reference elevation and start the depth search there (at the stations' mean level when the model's top is the surface). Report depths in km below sea level. A HypoInverse CRH model puts stations at the model's top; CRE models and NonLinLoc honour station elevations; relative relocators put every station at depth 0. Convert before comparing.

**Station corrections.** Once the model is chosen, compute per-station, per-phase corrections from at least about 10 picks each, remove the network median of each phase, relocate with them and report the change. Delays all of one sign and similar size hide a model error: their mean should be near zero.

**Events unconstrained in depth.**
- *Applies:* many events at the top or bottom of the depth search (`depth_single_value` or `depth_at_edges`, `pile_against_setup` names the bound), and the piled events lack depth constraint: no S pick within 1.4 focal depths, a distant nearest station, a large depth uncertainty.
- *Do:* first check that the search starts at the model's datum. Then report the expectation hypocentre for these events: `scripts/expectation_hypocentres.py --events <locator events.csv> --catalog catalog.csv --output ... --changes ...`. Keep the maximum-likelihood depth for constrained events. Say in the record how many events changed.
- *Why:* the maximum-likelihood point of a flat depth likelihood ends at the edge of the grid; the expectation (mean of the location PDF) is the standard value to report. This corrects how the depth is reported; it is not tuning.
- *Example:* 178 events at the top of the grid (10.8 % of a catalog) without depth constraint; with expectation hypocentres the largest share at one depth fell to 1.3 %.

**S−P depth flag** (`sp_depth_offset`: depths implied by S−P times at stations closer than the source against catalog depths).
- *Applies:* above its limit (1.5 km). Below it the sign is not reliable: velocity structure alone moves it by about 1 km.
- *Direction:* above the limit the direction has been right every time it was checked against a published catalog (three runs, 1.7–2.7 km). Correct the catalog in that direction.
- *How:* look for the cause in this order: (1) datum: an offset equal to the station elevation or the model datum; (2) near-surface velocity: a slow surface layer missing (basin fill, sediments, volcanic deposits), candidates built from the geology (`../reference/not_visible.md`); (3) S picks of a few stations: the offset comes from those stations only. Relocate with each candidate.
- *Judge by:* the geology and `compare.py` on the full products; check that depths moved the flagged way. The flag gives the direction, not the size: do not choose the candidate that brings the offset to zero.
- *Not:* do not dismiss the flag because a candidate fits the picks worse; do not absorb it with station delays (delays of one sign on each side of a fault or basin edge are path terms and cannot explain a catalog-wide depth offset); do not scale Vp/Vs only to remove it (next rule).
- *Example:* a catalog flagged 2.7 km too shallow was 1.8 km too shallow against the published catalog. Scaling Vs until the offset fell to 0.2 km moved the depths 2.9 km, leaving them 1.2 km too deep.

**Vp/Vs from the data.**
- *Applies:* the model's Vp/Vs differs from the data's Wadati Vp/Vs (`wadati_origin_offset` details: `median_vpvs`), and origin times scatter (`wadati_origin_spread`).
- *Do:* recompute the Wadati Vp/Vs from stations closer than about twice the focal depth. Use it when it is within crustal values (about 1.65–1.85).
- *Not:* a Wadati Vp/Vs outside that range is often biased by refracted first arrivals at distant stations or emergent P; some regions do have such values, so if it stays outside the range when recomputed from near stations, use it only with independent support (published Vp/Vs of the region, the geology), not to remove a flag.

**Events beyond the network.**
- *Do:* `scripts/drop_beyond_network.py --checker $CHECKER_PATH --catalog ... --stations ... --output ...` sets events more than 10 km outside the station hull to `rejected`. Say how many in the record.
- *Why:* beyond the network an event is seen from one side only; its distance and depth trade off and the data cannot constrain it. In recorded catalogs such events almost never belonged to the sequence studied, and published catalogs contain almost none of them. A small formal error outside the network does not make the location trustworthy.

## Flags of this stage

### Depth piles (`depth_single_value`, `depth_at_edges`, `depth_layers`)

Read `depth_constraint` first (share with an S within 1.4 focal depths, geometry, make-up of the most common depth) and pass `--location-setup` so `pile_against_setup` gives the distance of the pile to each set-up feature.

| Make-up of the pile | Likely cause | Experiment | Repair |
|---|---|---|---|
| a round value; events with or without constraint | fixed or trial depth | the value is a depth in your configuration | free the depth or flag those events as depth-fixed |
| top or bottom of the search; unconstrained events | the search bounds, or a flat depth likelihood | the value is a bound in `pile_against_setup` | search from the model datum; expectation hypocentres (above) |
| shallowest depth; S−P depths deeper | near surface too fast, or wrong datum | relocate the pile with the right datum, then with a slow surface layer if the geology has one | the set-up that removes the pile without moving constrained events |
| at a layer interface (within one grid spacing); poorly constrained events | step representation traps events; a coarse grid moves the pile to the node next to the interface | relocate the pile plus 200 random events as a linear gradient between the nodes, and with a 0.1 km grid: an artefact disperses with the gradient and moves onto the interface with the fine grid | build both full candidates and compare (`../reference/pilot_and_compare.md` §3) |
| not round, not at a set-up feature; constrained events | the model, or real structure | relocate with other models (`--model-ensemble` measures the sensitivity); compare with S−P depths | see `../reference/not_visible.md`; real seismicity can concentrate at one depth when S−P depths confirm it |

`depth_layers` (thin slices with many more events than their neighbours) has the causes of interface piles; a correct layered model forms slices at its interfaces too, so this check alone cannot rank two models.

### Origin times

`wadati_origin_spread`: wrong S picks, a model Vp/Vs unlike the data's, or unstable locations (rule above). `wadati_origin_offset` flags only beyond 1.5 s; an origin-time offset shared by all events is not visible to any check (`../reference/not_visible.md`).

### Horizontal structure

`isolated_events`: false associations (few picks, distant stations only), events outside the network (gap > 180°), or real isolated seismicity. Never remove the largest events by a location-quality rule: early in a sequence they are often isolated and have the worst geometry.

### The locator's uncertainties and residuals (reported)

- `location_uncertainty`: the horizontal uncertainty ranks badly located events (offline: area under the ROC curve 0.62–0.98; removing the 10 % most uncertain halved the share of bad events in most tests). Use it, with gap and number of phases, to mark poorly constrained events; state the rule. Its size is not the catalog's error: it leaves out the velocity model.
- RMS does not rank location quality (worse than chance in six of ten tests: well-recorded events have the largest RMS).
- `station_residual_spread`: a station whose residuals scatter more than the stations with S picks: wrong coordinates or elevation, timing, wrong picks, or a path the 1-D model lacks. Check metadata, timing against neighbours and a sample of picks first; decide with a with/without comparison. `p_only_median_mad_s` against `reference_median_mad_s`: a P-only group scattering several times more is a shared picker or channel problem (stage 1).
