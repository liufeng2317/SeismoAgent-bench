# 2011 Prague, Oklahoma — expert monitoring pipeline

Manual expert port of the Maple Creek/Magna monitoring workflow to the 2011
Prague aftershock sequence, stable-network window 2011-11-11 → 11-19 (five
days after the Mw 5.7 mainshock of 2011-11-06, which is outside the window).
Produces the case's expert reference catalog, tuned round by round against
the case references; round log and gates in `PLAN.md`.

## Layout

```
00_config/    config.yaml, association.yaml, nonlinloc.yaml, validation.yaml
01_pipeline/  01 → 02 → 03 → 04 → 09 → 10 + run_round.sh
04_comparison/ 05_match_references (round feedback; after 04, before 09)
export/<rN>/  per-round outputs (git-ignored)
logs/<rN>/    per-round stage logs
```

Copied from the Maple Creek expert tree (which already carries step velocity
layering, iterated NLL station delays, empty no-data blocks and the
component-alignment fix); stages 45/52/60 are ported when a round needs them.

## References (all located; stage 05 hard-gated counts)

| Reference | Masked | Role |
|---|---|---|
| Cochran et al. (2020) | 2,078 | primary: template-enhanced, relocated, Keranen model |
| McMahon et al. (2017) | 2,343 | independent subspace detection + Bayesloc |
| Isken & Mooney (2017) Table S3 | 6 | M>3 manual relocations; minute-precision times → 60 s / 5 km location anchor only |
| ComCat | 11 | operational (us, M≥1.6); genuinely sparse in 2011, not a query error |

Mask: the window plus the Cochran window envelope widened to three decimals
(35.452–35.558 N, −96.873…−96.733), depth −3…20 km. Gates 4 s / 15 km.

## Case-specific choices

- **Velocity model**: Keranen et al. (2013), the model Cochran used —
  published only as GSA DR 2013191 Figure DR1; extracted exactly from the
  PDF's vector content (`data/2011_prague_oklahoma/scripts/models/
  digitize_keranen2013_dr1.py`), checked against the figure's separate Vp/Vs
  panel. Constant-velocity layers (`velocity_layering: step`); datum = mean
  station elevation 0.28 km.
- **Mainshock**: `config.mainshock.in_window: false` — stages 05/09/10 make no
  mainshock identity check and defer no event.
- **Stations**: 22 three-component sites — ZQ RAMP LC09–LC16, LC18 (250 Hz;
  DH, and CN accelerometers at LC09/LC10), GS OK020–022 and OK FNO (100 Hz HH),
  nine TA sites (40 Hz BH). ZQ LC01–LC08 have no public waveforms; ZQ.LC17 is
  excluded (`channel_policy.exclude_stations`, placeholder latitude 35.0000).
- **Picking**: `picking.resample_to_hz: 100` — explicit FFT resampling of the
  250/40 Hz input to PhaseNet's rate in stage 02 (start times kept, so the
  components stay on one grid). Thresholds 0.2/0.2 (Magna r5).
- **Magnitude**: Hutton–Boore provisional; numerical check GS.OK021.00.HHE;
  TA 40 Hz traces are below stage 09's rate floor.
