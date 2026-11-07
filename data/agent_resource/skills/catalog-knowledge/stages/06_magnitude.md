# Stage 6: magnitudes

Gate: `run.py --stage magnitude --catalog --picks --waveforms <folder>` (StationXML with responses). Before submission: the recomputation agrees, the largest events have measured magnitudes.

Formulas, units, the Wood-Anderson response and a reference implementation: `../../../magnitude/README.md` and `../../../magnitude/ml_reference.py`. Regional calibrations: `../../../magnitude/calibrations.json`.

## Decisions

**Implementation.**
- *Default:* use the reference implementation or check yours against it on a few events (`ml_reference.py recompute`) before the full run: unit and response errors shift every magnitude by a near-constant amount and show on any event.
- *Calibration:* use the region's distance correction from `calibrations.json` when one exists, and say which; otherwise the IASPEI standard relation.

**Which records to measure.**
- *Do:* choose stations before measuring (distance range, data quality, response), not by the amplitude being measured. An event without a measurable amplitude on the chosen stations has an upper bound, not a magnitude from its loudest station.
- *Window:* the S-train window (to S + max(3 s, 0.5 (S − origin)) + 2 s, as in `ml_reference.py`) for most events; a long window (at least S + max(30 s, 4 (S − P))) only for the largest events, after checking no larger event arrives in it.
- *Why:* in offline tests on three sequences, keeping only records ≥ 3 × the noise made small events 0.1–0.25 units too large; a window to S + 30 s in a busy sequence steepened the scale by up to 0.07 per unit.

**The largest events.** Measure them on unclipped records (far stations, strong-motion channels) with the long window; above about M 6 ML saturates: use a moment magnitude where available and say so. Give every event a magnitude or say why it has none.

## Flags of this stage

`magnitude_recompute` compares catalog magnitudes with a standard local magnitude recomputed from the records. Read its details: `mad`, `offset_trend_per_log10_km`, `station_terms`, `median_station_spread`, `slope_catalog_vs_recomputed`.

| Pattern | Likely cause | Repair |
|---|---|---|
| offset ≈ ±2.7, small spread, no distance trend | mm amplitudes with the nm constant (or the reverse) | one unit chain end to end (`magnitude/README.md` §3) |
| offset ≈ ±3 or ±6 | amplitude in m or µm | fix the conversion |
| offset −1 to −1.5, trend with distance | a one-zero (velocity-input) Wood-Anderson response on displacement, or velocity treated as displacement | two-zero response on displacement, or remove the response to velocity first |
| +0.3 | full peak-to-peak | half peak-to-peak |
| ±0.13 | magnification 2800 vs 2080 | the magnification the formula assumes |
| 0.1–0.4, small spread, no unit signature | regional calibration differs from the standard (not visible as an error) | the region's calibration; report which |
| grows with magnitude | clipping, short window, ML saturation | `largest_events_magnitude`; remeasure the largest events |
| one station term far from the others | that station's metadata (a round factor) | fix or exclude that station |

- `largest_events_magnitude`: the largest events too small or missing (clipping, short window, an event split in two, saturation).
- `slope_catalog_vs_recomputed` clearly below 1, low b-value in both estimates: a compressed scale; check record selection and window (above). What remains is calibration: the standard relation was 0.04–0.12 per unit more compressed than regional calibrations.
- `magnitude_range`, `magnitude_detection`: usually the same unit or response errors.
- `b_positive` near 1 while `standard_b_value` is low: short-term incompleteness early in a sequence, not physics. A low b in both: compressed magnitudes or mixed magnitude types; split by type and detection method.

**Completeness and rates** (no check): after a mainshock of magnitude M the catalog is incomplete above about Mc(M, t) = M − 4.5 − 0.75 log10(t / 1 day). A rate change that affects only small events points to detection (gaps, fewer stations, noise, coda); one at all magnitudes to real seismicity or a magnitude shift.
