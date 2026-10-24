# 2020 Magna, Utah — expert monitoring pipeline

Manual expert rebuild of the eight-day Ridgecrest monitoring workflow for the
2020-03-18 M5.7 Magna, Utah earthquake sequence. This directory produces the
case's expert reference catalog and, round by round, tunes it against the
three published references. It is the human baseline for the agent benchmark;
see `PLAN.md` for round mechanics and gates.

## Layout

```
00_config/    config.yaml (round identity, windows, mainshock anchor, channel
              policy, tools), association.yaml (GaMMA), nonlinloc.yaml (NLL),
              validation.yaml (reference cohort mask, matching gates, quality)
01_pipeline/  01_prepare_inputs → 02_pick_phasenet → 03_associate_gamma →
              04_locate_nonlinloc → 09_estimate_magnitude → 10_validate_catalog
              + run_round.sh (sequential round driver)
04_comparison/ 05_match_references — expert-vs-reference matching, the round
              feedback stage (runs after 04 full, before 09);
              06_fit_ml_calibration — fits the Utah ML calibration on a
              completed round (feeds the next round's config.yaml);
              07_review_match_locate — waveform review of stage-60 detections;
              08_null_run — channel-shuffled false-alarm estimate for stage 60
export/<rN>/  per-round outputs (immutable once the round is recorded)
logs/<rN>/    per-round stage logs
```

## Running a round

```
cd 01_pipeline
./run_round.sh                 # full DAG for the round named in 00_config
./run_round.sh 03_pilot 04_pilot   # diagnostic subsets, gated manually
```

Pilot scopes cover the quiet window (03-18 02:00–02:10Z) and the mainshock
window (13:05–13:20Z); run them first in a new round before the full pass.

## Case-specific choices (vs Ridgecrest)

- **Velocity model**: Bjarnason & Pechmann (1989) BSSA 79(3) Table 2 Wasatch
  front model (Vp 3.4/5.9/6.4/7.5/7.9 over tops 0/1.5/17.1/28/42 km, Vs via
  Vp/1.73), transcribed from the open-access PDF into
  `data/2020_magna_utah/data/models/velocity_models.json` with full provenance.
  The model's reference datum (1500 m ASL) matches our station-reference
  elevation (1.48 km, mean station elevation) to within 20 m, so layer depths
  carry over without re-datuming. Since r4 the round model adds a Salt Lake
  Valley basin-fill layer (sea level–2 km bsl @ Vp 4.0;
  `bjarnason_pechmann_1989_plus_slv_basinfill2km` in the same registry):
  BP89's 5.9 km/s right below sea level is too fast for the valley fill and
  put the catalog +0.34 s late with a quarter of events pinned at the depth
  grid bound.
- **Channels**: primary three-component families EN/EH; one instrument per site
  (`site_family_preference: [EN, EH]` — UU.WTU carries both epochs). Deferred:
  UU.SHED (HN only), ten EHZ-only EH instruments, UU.NOQ's HH epoch.
- **Picking**: PhaseNet P/S thresholds were lowered 0.3 → 0.2 in r5 (the
  pick threshold is the effective detection floor; ~20% of picks sat at
  probability 0.30–0.40). 0.15 was tested and rejected: gains diminish
  while orphans and unassociated picks keep climbing, and PhaseNet scores
  below ~0.2 are not calibrated precision.
- **Mainshock**: single M5.7 anchor (uu60363602, 2020-03-18T13:09:31.530Z);
  identified at runtime in stages 05/09/10 as the located event nearest the
  anchor within `mainshock.proximity_s`; its magnitude is deferred, its depth
  flagged unresolved.
- **Relocation**: since r6 a double-difference layer (stage 52, config
  `00_config/double_difference.yaml`) re-locates the round catalog with
  hypoDD (CT+CC, control file from the Ridgecrest tuned run): a pick-aligned
  waveform-correlation kernel (RC curve/whiten conventions, two-band gates)
  yields a thin-but-clean CC set (3,303 obs, median CC 0.84 — Magna
  aftershocks are distinct sources, not templates) on top of the catalog
  differential times (242,394 obs). Median epicentral distance to pang drops
  1.42 → 0.85 km and depth MAD 1.07 → 0.81 km after a documented +0.90 km
  datum offset (`depth_datum_offset_km`: hypoDD's flat-layer tracer vs NLL's
  eikonal, spatially uniform, CC layer excluded by a ct-only control). The
  layer reports on its own (`52_double_difference/report.json`); the round
  catalog and v1 stay on NLL positions.
- **Depth prior**: since r8 stage `01_pipeline/45_depth_prior.py` (config
  `depth_prior`) re-weights the NLL posterior of weakly constrained events
  (n_phases < 20 or σz > 2 km) toward the round's own well-constrained median
  depth and writes `45_depth_prior/events.csv`, which stage 05 (and so
  09/10/52) reads instead of the raw stage-04 table. DD relocations that move
  an event more than `max_vertical_shift_km` (double_difference.yaml) are
  rejected at catalog export (velocity-contrast trap, PLAN.md r8).
- **Template detection**: since r7 stage `01_pipeline/60_match_locate.py`
  (config `00_config/match_locate.yaml`) runs Match&Locate
  (`seismotools/match_and_locate`) seeded by the round catalog: 311 templates
  on a 0.5 km spatial cover, ±0.5 km grid, near (≤20 km) SNR≥5 channels, final
  N×MAD 9 with 6 s de-duplication (both set by channel-shuffled null runs and
  a separation sweep). Its `export` step writes the r7 catalog (r6 with DD
  positions + M&L events with M&L positions and chained relative magnitudes);
  `--stage export --catalog-round r8` rebuilds it on another round's
  catalog, shifting each M&L event with its template
  (`export/r8/60_catalog/catalog_events.csv`).
  `--scope pilot|full`, `--tag/--override` for variants; full run ≈3 h.
- **Magnitude**: r1 used provisional Hutton–Boore (1987) southern-California ML;
  r2 replaced it with a Utah calibration fitted on r1 by
  `04_comparison/06_fit_ml_calibration.py` (anchor: UUSS ML on 385 matched
  events; geometric spreading 2.93 and constant refit, HB87 anelastic term
  kept; coefficients live in `00_config/config.yaml` `magnitude.ml_calibration`);
  r3 added per-station corrections (`magnitude.station_corrections`, 31
  stations, n≥20 anchor measurements, entries = fit medians verbatim,
  subtracted in stage 09) — per-event station-ML MAD 0.131 → 0.071.
  Numerical Wood–Anderson recovery is checked on the real UU.AVE.01.ENE
  response every round.

## References

- Pang et al. (2020) GL089798 relocated catalog; Baker & Whidden (2021) pick
  set; UUSS/ComCat operational benchmark. Masked cohort counts are hard gates
  in stage 05 (see `00_config/validation.yaml`).
