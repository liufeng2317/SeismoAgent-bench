# Pilot batch first, full run second

Picking, association, location, relocation and template matching over weeks of continuous data take hours each. A mistake found after the full run costs the whole run. Most mistakes, however, show on a small part of the data. Work in two levels.

## 1. Pilot level: is the code right, and what will a change do?

Choose the batch with `seismotools/checker/interface/pilot.py`, not by hand:

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

- **code and tool use**: units (nm vs mm vs m; km vs m), sign and datum conventions (depth below sea level vs below the station or the model datum; station elevations), instrument response and Wood-Anderson response, column names and time formats. These errors affect every event alike, so the pilot shows them as clearly as the full run. Compare a few values with an independent computation (for magnitudes: `../../magnitude/ml_reference.py recompute`).
- **checker, item checks**: run the checker with `--pilot`. Checks of scope `item` (picks, Wadati, travel-time fit, S−P depth, magnitudes recomputed) are judged; checks of scope `population` are reported without a verdict.
- **run time**: time per event or per hour of data, extrapolated to the full run.
- **candidates**: run each candidate on the same pilot and compare their medians (how far depths and origin times move). Drop candidates that fail item checks; keep the rest for the full run.

What a pilot cannot tell you: the distribution of the full catalog (pile-ups at one depth, thin depth layers, completeness, b-value, isolated events), and therefore whether a candidate is better. Two candidates that look the same on 300 events can differ clearly on the full catalog, and the other way round.

## 2. Full level: is it right, and do we adopt it?

1. Freeze the code and the parameters chosen at the pilot level.
2. Run the full data.
3. Run the checker on the full products without `--pilot`; with two candidates, run it on both and use `compare.py` (see [`../playbooks/decide_between_candidates.md`](../playbooks/decide_between_candidates.md)).
4. Compare the full result with what the pilot predicted (median shifts). A large difference means the change acts differently on different events (e.g. events pinned at a bound move far more than the rest); look at those events before adopting.
5. Record which decisions were taken at which level, and why.
