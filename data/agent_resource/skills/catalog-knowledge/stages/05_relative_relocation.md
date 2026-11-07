# Stage 5: relative relocation

Gate: `run.py --stage relocation --catalog relocated.csv --catalog-before located.csv --picks picks.csv [--dtcc dt.cc]`. Before magnitudes: frame shift and large moves explained.

## Decisions

**Run it where events are dense.**
- *Default:* required when many events lie within a few kilometres of each other (a sequence): differential times from waveform cross-correlation and from the catalog, relocated with hypoDD or GrowClust. It sharpens structure that absolute locations blur (off-structure events and horizontal scatter fall).
- *Not run only when* events are sparse or have too few links; say how many events had enough links.

**Keep the absolute frame.**
- *Do:* use the same velocity model and datum as the absolute location. hypoDD and GrowClust put every station at the model's depth 0: give them depths and a model measured from the stations' level and convert back. Compare the relocated centroid with the absolute locations and say which frame the catalog is in.
- *Why:* in offline tests relocation moved the whole catalog by 0.3–2.3 km.

**Linking thresholds.**
- *Do:* use the minimum links and maximum separations the tools' READMEs give as safe; keep events with too few links at their absolute locations.
- *Not:* do not loosen the thresholds to raise the share of relocated events: events relocated on too few differential times move to wrong places and scatter the catalog. Detections that inherit their template's location must not enter the catalog differential times.

## Flags of this stage

| Flag | Likely causes | Evidence | Repair |
|---|---|---|---|
| `relocation_shift` | a few strongly linked events dominate; absolute times weighted too strongly; another model or datum than in the absolute location | compare models and datums; relocate with catalog times only, cross-correlation only, both | same model and datum; reweight |
| `relocation_thinning` | real sharpening; or collapse by over-weighted cross-correlation times, too few observations per pair, poorly conditioned clusters (hypoDD condition number far above 40–80) | bootstrap (50–100 resamples) or jackknife by station: real structure keeps its width; streaks with ellipses along the streak are artefacts; ≥ 8 observations per pair | reweight, require more links |
| `relocation_large_moves` | poorly linked events, events far from their cluster, a wrong pick set | relocate those events alone from another start; events that move back were unstable | keep them at their absolute locations |
| `relocated_share` low (reported) | strict linking thresholds, cross-correlation for a subset only, events outside the clusters | count events lacking links | justify with that count; not an error for small isolated events |
