# Maple S3 run: why a quarter of the locations are more than 5 km off (2026-11-07)

The first formal S3 run of Maple Creek (`knowledge`, 20261105T225355Z, checker 1.4) fixed the magnitude errors of S1 but matched only 0.73 of the ComCat events. The missing matches are not missed detections: 155 of the 157 unmatched ComCat events have a candidate event within 4 s, located more than 5 km away (median about 10 km). This record finds the step that caused it, offline, from the run's own intermediate products.

## Which step

Every NonLinLoc run of the Agent scored against ComCat (gates 4 s and 30 km for the distance distribution; the scorer's gates are 2 s and 5 km):

| Location run | Events | Pairs (2 s, 5 km) | Epicentre offset, median / 90 % | > 5 km | Origin time | Median depth (ComCat 5.2 km) |
|---|---|---|---|---|---|---|
| Preliminary, step layers (rejected) | 1,614 | 393 | 4.51 / 5.76 km | 33 % | +1.21 s | 2.01 km (interface pile) |
| Preliminary, linear gradient (adopted, D2) | 1,610 | 582 | 1.09 / 2.70 km | 1.2 % | +0.98 s | 5.07 km |
| Final, pass 1 (final association) | 3,422 | 387 | 3.30 / 11.41 km | 30 % | +1.41 s | 4.54 km |
| Final, pass 2 (+ station delays) | 3,418 | 406 | 3.12 / 10.59 km | 27 % | +1.41 s | 4.58 km |
| Final arrivals without the vertical-only stations (this test) | 3,423 | 527 | 2.12 / 4.28 km | 5.9 % | +1.22 s | 4.72 km |

The model change of D2 (step layers to a linear gradient, to remove the 2-km interface pile flagged by the checker) was right: it removed the pile and brought the epicentres within about 1 km of ComCat. The degradation came later, in the final location, whose configuration is identical to the preliminary one. What changed is the input: the final arrivals add P picks of the eight vertical-only stations (WY.YHH, YHB, YDC, YGC, YWB, MCID, YPM, YLT; 1,600–3,000 picks each), picked with DPPPicker at probability 0.3 to answer the checker's `silent_stations` flag (8 of 27 stations without picks, all vertical-only).

## Why

- These picks are poor: 46 % of their P residuals exceed 0.5 s and 30 % exceed 1 s, against 15 % and 9 % for the three-component stations. In the Agent's own pilot (D1) only 66 % of DPP picks at 0.3 matched a PhaseNet pick at a neighbouring station.
- They make up a median 40 % of each event's picks. The Agent's argument in D1 was that noise picks cannot create events (the associator needs three stations with P and S); it did not consider that noise picks attach to real events and pull their locations.
- Relocating the final arrivals without these stations, with the Agent's configuration, model and stations file, brings the share of events more than 5 km off from 30 % to 5.9 % and the scorer's pairs from 387 to 527. The rest of the gap to the preliminary location comes from other differences of the final association (more, weaker events).
- The origin-time bias (+1.0 to +1.4 s) is there from the first location and does not depend on these picks: it comes from the velocity model (layer C, unchanged by this finding).

## What the checker saw

- `silent_stations` flagged the eight stations, correctly (they were unused), and the knowledge skill says vertical-only stations are often left unused. The Agent added them.
- `station_residual_spread` (1.4, report-only) listed two of the eight (YLT, YPM; MAD 0.74 and 0.71 s); the other six (MAD 0.19–0.31 s) stayed just below the limit, max(0.2 s, 3 × the network median 0.105 s) = 0.31 s, while three-component stations have 0.08–0.11 s. Report-only measurements need no disposition, and the Agent did not act on it.
- No check compares locations with and without a newly added group of picks.

## Lessons for the next development iteration

1. A flag that asks for more data (`silent_stations`) can lead the Agent to add bad data. The fix of a symptom needs its own check: after adding picks from a new picker or station group, compare the locations with and without them and compare their residual spread with the other stations'.
2. Noise picks do not have to create events to do harm: attached to real events they move them. Knowledge should say this where it discusses picker thresholds.
3. The residual-spread check found the problem stations only in part, because the limit is relative to a network median that the problem stations themselves raise; a limit relative to the three-component stations or to the stations used before the change would have listed all eight.

Script: inline analysis in this session (arrival sets `work/work/locate/arrivals_{prelim,final}.csv` of the run; relocation with `seismotools/nonlinloc/interface/locate.py` and the run's `nll_final_p1/config.json`).
