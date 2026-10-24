# 2017 Maple Creek, Yellowstone — expert monitoring pipeline

Manual expert port of the Magna/Ridgecrest monitoring workflow to the
2017 Maple Creek swarm (Mw 4.4 on 2017-06-16, eight-day window
2017-06-11 → 06-19). This directory produces the case's expert reference
catalog and tunes it round by round against the case references. It is the
human baseline for the agent benchmark; round log and gates in `PLAN.md`.

## Layout

```
00_config/    config.yaml (round identity, windows, mainshock anchor, channel
              policy, tools), association.yaml (GaMMA), nonlinloc.yaml (NLL),
              validation.yaml (reference cohort, matching gates, quality)
01_pipeline/  01_prepare_inputs → 02_pick_phasenet → 03_associate_gamma →
              04_locate_nonlinloc → 09_estimate_magnitude → 10_validate_catalog
              + run_round.sh (sequential round driver)
04_comparison/ 05_match_references — expert-vs-reference matching, the round
              feedback stage (runs after 04 full, before 09)
export/<rN>/  per-round outputs (git-ignored, immutable once recorded)
logs/<rN>/    per-round stage logs
```

Later Magna stages (45 depth prior, 52 double difference, 60 Match&Locate,
06 ML calibration) are ported when a round needs them, not up front.

## Running a round

```
./01_pipeline/run_round.sh                     # full DAG for the round in 00_config
./01_pipeline/run_round.sh 03_pilot 04_pilot   # diagnostic subsets, gated manually
```

Pilot scopes: quiet window 06-11 02:00–02:10Z and the mainshock window
06-16 00:45–01:00Z.

## References (no published research event table exists)

Pang et al. (2019)'s 3,345-event table and Shelly & Hardebeck (2019)'s event
catalog are unpublished. The cohort is therefore:

- **ComCat/UUSS operational** (located): 626 reviewed events in the window,
  query box corrected 2026-10-22 to the swarm footprint
  (`data/2017_maple_creek_yellowstone/data/catalogs/USGS_UUSS_COMCAT_2017`).
  Matched at 4 s / 15 km like Magna and Ridgecrest; depths compared on one
  datum (below the local surface).
- **Shelly detections** (time only): 18,062 window events derived from the
  USGS phase-arrival release (origin = median of arrival − travel time from
  the swarm centroid; duplicate match_ids merged; 0.11 s MAD vs ComCat;
  `.../SHELLY2019_GL081607/scripts/derive_detection_events.py`). Matched on
  origin time alone at 1 s; a 60-s shifted-reference control counts chance
  coincidences, reported next to the raw recall.

## Case-specific choices (vs Magna)

- **Velocity model**: UUSS Yellowstone 1-D (Pang et al. 2019 SI Table S1,
  tabulated Vp and Vs; `data/.../data/models/velocity_models.json`). Datum not
  stated in the source; taken as the 2.3 km ASL mean surface, which is also
  ComCat's depth reference.
- **Channels**: three-component HH/EH, one instrument per site
  (`site_family_preference: [HH, EH]`). 17 sites in r1; six PB borehole
  sites have 1/2 horizontals rotated with StationXML. Since r3 the
  vertical-only WY EH sites join as a P-only input condition (25 instruments;
  YGC 6 km, YHB 13 km, YHH 14 km). Deferred: the 40 Hz BH sites (FLWY, LKWY,
  H17A BH).
- **Rounds so far** (PLAN.md): r2 step (constant-velocity) layers in GaMMA
  and NLL (`association.yaml velocity_layering`; the linear ramp made origins
  +0.47 s late); r3 vertical-only WY sites (`channel_policy.
  vertical_only_families`); r4 Z copied onto N/E for them
  (`picking.vertical_only_horizontals: copy_z`, ~3x the picks); r5 iterated
  NLL station delays (`nonlinloc.yaml station_delays`); r6 stage 60
  Match&Locate; r7 denser templates (519, N×MAD 9.25). r7: ComCat recall
  0.994, Shelly 0.521 net of chance, M&L positions within 0.49 km of NLL.
- **Picking**: PhaseNet thresholds 0.2/0.2 carried over from Magna r5.
- **Magnitude**: Hutton–Boore (1987) provisional ML; numerical response check
  on WY.YMC.01.EHE.
- **Stage 02 fixes vs the Magna copy**: the pilot path pre-imports SeisBench
  before spawning workers (concurrent first imports wrote a NUL-filled
  `cache/config.json`); component alignment checks the sample phase (start mod
  delta) and trims to the nearest sample, because WY.YMR's components differ
  by 1 µs in phase and `trim(nearest_sample=False)` then picked different
  samples.
