# Stage 2: association

Gate: `run.py --stage association --catalog events.csv --picks picks.csv` (locations may still be missing). Before location: flags handled.

## Decisions

**Association settings.**
- *Do:* tune the minimum picks and stations per event, the time window and the velocity on the pilot's busiest windows (`reference/pilot_and_compare.md`). Common minima: at least 4 P and 7 picks in total, or at least 4 stations with both P and S.
- *Not:* do not lower the minima to raise the number of events; events built from coincident noise picks are false. Keep few-pick events in a separate list rather than deleting them silently.

**A low share of associated picks.**
- *Not an error by itself:* published workflows associate as few as 12–19 % of their picks with a low picker threshold. A very low share with a high picker threshold points to an associator set for the wrong region, velocity or time window.

## Flags of this stage

| Flag | Likely causes | Evidence | Repair |
|---|---|---|---|
| `duplicate_events` with shared picks (`details.pairs_sharing_picks`) | the same event entered twice: overlapping windows, two associators' outputs concatenated | pairs share picks | merge on shared picks |
| `duplicate_events` without shared picks | real doublets (common early in sequences), or one event split in two | the union of the picks fits one origin; the halves come from different stations | merge only if one origin fits |
| `events_with_few_picks` | low association threshold; small network; real small events near one station | few-pick events near one or two stations, at noisy times or outside the network are suspect; look at a random sample of their waveforms | raise the minima; keep a separate list. Events without any pick (template-matching detections) are not counted here |
| `association_busy_hours` | the associator saturates when events are seconds apart; picker misses in coda | in busy hours picks per event and the unassociated share rise | rerun one busy hour with a smaller window or another associator and compare the event count |
| `associated_share` low | see above | | |

**Picks off their event's travel-time curve** (no check; read single events' residuals after location): picks from another event, a wrong phase label, or a station with a wrong position. Outliers from one station point to its position or clock; spread outliers to association. Relocate a few events without them.
