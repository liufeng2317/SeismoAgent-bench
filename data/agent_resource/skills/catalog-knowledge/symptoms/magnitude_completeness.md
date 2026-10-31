# Magnitude and completeness

Formulas, units, the Wood-Anderson response and a reference implementation: [`../../../magnitude/README.md`](../../../magnitude/README.md). Regional calibrations: [`../../../magnitude/calibrations.json`](../../../magnitude/calibrations.json).

## Magnitude offsets

**`magnitude_recompute` — catalog magnitudes differ from a standard local magnitude recomputed from the records.** Read the details: `mad` (spread of the difference), `offset_trend_per_log10_km` (how the difference changes with distance), `station_terms` and `median_station_spread`.

| Pattern | Most likely cause | Tier | Evidence | Repair |
|---|---|---|---|---|
| offset ≈ −2.7 or +2.7, small spread, no trend with distance | amplitude in mm used with the nm constant (or the reverse) | A | the offset equals log10(2080 × 10⁻⁶) to within 0.1 | use one unit chain end to end (`magnitude/README.md` §3) |
| offset ≈ ±3 or ±6, small spread | amplitude in m or µm instead of nm (or mm) | A | offset equals a power of ten | fix the unit conversion |
| offset about −1 to −1.5, trend with distance (smaller at far stations or the reverse) | a Wood-Anderson response with one zero (velocity input) applied to displacement, or a velocity or acceleration record treated as displacement | A | the offset changes with frequency, so with distance and magnitude | apply the two-zero displacement response to displacement, or remove the response to velocity first |
| offset +0.3, small spread | full peak-to-peak instead of half | A | | half peak-to-peak |
| offset ±0.13 | WA magnification 2800 vs 2080 | A | | use the magnification the formula assumes |
| offset 0.1–0.4, small spread, no unit signature | the regional calibration differs from the standard relation | C | cannot be separated from a calibration error without independent magnitudes | use the calibration of the region (`calibrations.json`); report which one |
| offset grows with magnitude (large events too small) | clipping, a window that ends before the S maximum, saturation of ML above about 6 | A/B | `largest_events_magnitude`; recompute the largest events from far, unclipped records with a long window | see below |
| one station term far from the others | that station's metadata (gain, units, sensitivity frequency) | A | the term is a round factor (0.3 for ×2, 1 for ×10) | fix or exclude that station |

**`largest_events_magnitude` — the largest events have magnitudes too small, or none.** Tier A/B.
- Causes: near records clipped; amplitude window too short for a long S train; the event split into several events; ML saturating above about M 6 (use a moment magnitude for the largest events where available and say so).
- Repair: measure large events on unclipped records (far stations, strong-motion channels), with a window of at least S + max(30 s, 4 × (S − P)); give every catalog event a magnitude or flag why it has none.

**`magnitude_range`, `magnitude_detection` — magnitudes implausibly low or high for what the stations detect.** Usually the same unit or response errors as above (`magnitude_detection` moves by the same amount as the magnitude offset). Recompute a few events with `magnitude/ml_reference.py recompute`.

## Completeness and the magnitude distribution

**`b_value` low next to `b_positive` near 1 (both reported).** Tier B: the standard b-value is lowered by changing completeness early in a sequence (short-term aftershock incompleteness), not by physics. b-positive uses magnitude differences of consecutive events and is robust to it.
- A low b in both: magnitude compression (a magnitude scale that grows too slowly with size: where ML grows 1.5 times faster than Mw for small events, b in ML is two thirds of b in Mw), or mixed magnitude types. Split the distribution by magnitude type and by detection method and compare.

**Missing events after the largest events.** After a mainshock of magnitude M the catalog is incomplete for hours: completeness is about Mc(M, t) = M − 4.5 − 0.75 log10(t / 1 day) (about M − 2.9 after ten minutes, M − 3.5 after an hour). Missing events above that curve are a failure of the workflow; in the first minutes of the mainshock's coda even large aftershocks are hidden from pickers and simple scans (see `not_visible.md`).

**Rate changes (`rate_after_largest`, daily counts).** Tier B.
- A change that affects only small events (and disappears above the completeness magnitude) points to detection: data gaps, fewer stations, noise, coda, associator saturation.
- A change at all magnitudes points to real seismicity — or to a magnitude shift (processing or calibration change on that date). Compare the frequency–magnitude distributions before and after: a shift moves the whole curve, a rate change moves it up or down.

**`day_night_ratio` (reported; needs ≥ 14 days of events).** A daytime excess in larger events points to blasting (check daytime working hours and weekdays; blasts have low high-to-low-frequency amplitude ratios). A night-time excess in small events only points to daytime noise hiding small events — a detection limit, not an error.
