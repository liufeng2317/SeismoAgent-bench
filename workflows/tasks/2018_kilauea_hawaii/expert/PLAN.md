# Kilauea 2018 summit expert pipeline — round plan

Same round mechanics as Magna, Maple Creek and Prague: round identity =
config `round` + `export_root`, one behavioural knob per round, previous
rounds immutable, never tune to force reference agreement. Task = the frozen
summit box (19.30–19.50 N, −155.40…−155.15), window 2018-05-01 → 05-09.
Feedback: stage 05 against Shelly & Thelen (2019) S1 (primary), Wei et al.
(2022), Matoza et al. (2021) relocated rows and ComCat/HVO.

## Data preparation (2026-10-23)

- Velocity model: HVO operational HYPOINVERSE model (Klein linear-gradient
  family) transcribed from HVO Summary 101 (USGS OFR 02-157, page 19): Vp
  1.9 / 6.5 / 6.9 / 8.3 km/s at 0 / 4.6 / 15 / ≥16.5 km with linear
  interpolation (registered `hvo_klein_linear`; Vs = Vp/1.78 after Shelly &
  Thelen). Native representation is the ramp → `velocity_layering: linear`.
- 25 HV stations, all 100 Hz, all within ~15 km of the summit; five EH sites
  vertical-only (P only, Z copied onto N/E).
- Masked reference counts (depth −3…20 km): Shelly 1,902, Wei 3,627 (the
  analysis audit's 2,369 used depth ≥ 0; many Wei summit depths are
  negative), Matoza 1,020 (nbranch > 1), ComCat 496.
- Mw 6.9 (2018-05-04 22:32:54) is in the window but outside the summit box:
  `mainshock.in_window: false`.

## Round log

### r1 (2026-10-23) — baseline port

- 02: 203,469 picks (P 125,953), 800 blocks. 03 pilot: 2 events in the
  low-rate window, 56 in the 22:45–23:00 window after the Mw 6.9.
- 03/04: 5,864 GaMMA events, 5,082 LOCATED; 1,152 at a depth bound (≈ 0 km);
  2,762 in the comparison scope (box), v1 1,807.
- 05:

| Reference | Masked | Matched (v1) | median \|dt\| | epicentral | dZ (MAD) |
|---|---|---|---|---|---|
| Shelly | 1,902 | 0.514 (0.416) | 0.21 s | 0.75 km | +0.62 (0.60) |
| Wei | 3,627 | 0.560 (0.401) | 0.22 s | 1.37 km | +1.95 (1.23) |
| Matoza | 1,020 | 0.841 (0.670) | 0.25 s | 1.13 km | +0.12 (1.00) |
| ComCat | 496 | 0.897 (0.720) | 0.11 s | 1.09 km | +1.08 (0.65) |

Diagnosis — pre-Mw-6.9 recall vs Shelly is 0.10 (first 48 h after 0.60,
later 0.75). 81 % of the missed pre-mainshock Shelly events have no GaMMA
event within 4 s, although a median of 9 stations picked them and 83 % of
those picks *are* associated: 412 absorbing events sit at longitude
−154.90 — the eastern edge of the association bounds, ~40 km east — with
origins 4.3 s earlier than Shelly's. With every station inside ~15 km of the
summit, a distant early source and a nearby later one fit the moveout almost
equally, and GaMMA drifts summit events to the bound (the lower East Rift
eruption began on 05-03, so distant activity is real and frequent).

### r2 — knob: association bounds restricted to the summit
(lon −155.65…−154.90 → −155.50…−155.05, lat 19.10–19.70 → 19.25–19.55)

Result (2026-10-23): **rejected.** Shelly 0.515 (v1 0.418), pre-Mw-6.9
v1 recall 0.097 (r1 0.10); LOCATED 3,935 (r1 5,082), 2,023 at the depth
bound. Of 686 missed pre-mainshock Shelly events, the 324 whose P picks were
associated sit at the *new* east bound (−155.05) with origins 2.9 s early.
The missed events are small (Shelly median M 0.49 pre vs 1.22 after) with
~6 picking stations within 12 km and noisy P residuals (median +0.38 s vs
+0.07 s for matched): a detection-threshold limit, not a bounds artifact.
Config restored to r1 (association settings verified against
`export/r1/03_associate_gamma/full/inputs.json`).

### r3 — knob: stage 09 Wood–Anderson prefilter 0.1–0.2 Hz → 0.5–1 Hz

r1 gave ML to 55 of 5,864 events: of 3,644 scheduled station measurements,
3,132 were rejected for SNR < 3 (median SNR 1.0; median WA noise 0.5–2 mm),
the 0.2 Hz corner passing the summit's long-period noise (collapse-period
VLP/tremor, Mw 6.9 coda). `magnitude.prefilter_hz` and
`magnitude.minimum_hypocentral_km` are now config keys of stage 09 (the
10 km gate also removes 12,510 pairs; a later knob). 01–05 hardlinked from r1.

Result (2026-10-24): **adopted, small gain.** Accepted station measurements
482 → 745 of 3,644; provisional ML events 55 → 74. SNR stays low (median
1.16; WA noise peak 0.56 mm ≈ an ML 1.5 background at 12 km): the summit's
continuous seismicity/tremor, not long-period leakage. The larger block is
upstream — 3,940 events carry `location_review` and are deferred before any
amplitude is measured. Magnitudes are left here; M&L chaining fills the rest.
(Only the needed 04 outputs were hardlinked: `events_raw/` holds 123k NLL
files and is not read downstream.)

### r4 — stage 60 Match&Locate seeded by r3

Shelly's catalog is template-matched; the pre-mainshock gap is detection.
`00_config/match_locate.yaml` (from Prague): HVO model densified into 0.2 km
constant sublayers for the tool (it treats rows as constant layers);
`exclude_p_overlapping_s: false` (summit S−P < 1.7 s at most stations);
pilot day 05-02.

Pilots (source r1 templates, 20 by station count): day 05-02 (pre-Mw 6.9)
found almost nothing (N×MAD 9: 6 events) — all 20 templates were post-
mainshock collapse-period events (0.3–1 km under Halemaʻumaʻu, or 2–4 km NW),
none near the pre-mainshock cluster (−155.23, 2.6 km). Day 05-06: union
Shelly 76.2 % → 88.3 % at N×MAD 9 (70 new events), Wei 64.4 → 69.0 %: the
mechanics (densified model, P/S overlap kept) work. Full run: 480 templates
(cover 89 % of v1 at 0.5 km, min 10 stations), 8 days.


Result (2026-10-24): **adopted.** Null run (05-02 + 05-06, channel circular
shift, 6 s separation): false fraction 34 % at N×MAD 8.5, 6.5 % at 9, **0.8 %
at 9.5**, 0 at 10 → final 9.5 (Prague: same). r4 catalog
`export/r4/60_catalog/catalog_events.csv`: 8,223 events (r3 NLL 5,864 +
2,359 M&L); M&L magnitudes chained from 44 ML templates to 336 of 400.
Box-scored (stage-05 readers and mask):

| | r3 NLL | M&L | **r4 union** |
|---|---|---|---|
| Shelly | 0.516 | 0.586 | **0.641** |
| Wei | 0.564 | 0.555 | **0.667** |
| Matoza | 0.844 | 0.761 | **0.867** |
| ComCat | 0.899 | 0.851 | **0.917** |

Split at the Mw 6.9: Shelly post 0.792 → **0.953**, pre 0.124 → 0.196;
Wei post 0.652 → 0.755, pre 0.278 → 0.379. The pre-mainshock gap remains:
templates come from located v1 events, and r3 located few events in the
pre-mainshock cluster (−155.23, 2.6 km), so it has few templates. Candidate
r5: denser/looser templates (Maple r7: min 8 stations, 0.3 km cover).
