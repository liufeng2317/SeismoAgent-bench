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

### r5 — P-only events admitted; templates covered per period (pre/post Mw 6.9)

Miss diagnosis of r4 (2026-10-26) on the 784 pre-mainshock Shelly events
(recall 0.198):

- Not template density: 62 % lie within 0.5 km of a template, yet those are
  recalled at only 0.27. Of 151 eligible pre-mainshock box events (v1,
  ≥ 10 stations), only 29 became templates — the greedy cover was won by
  post-mainshock collapse events at the same place, whose waveforms differ.
- Not location: time-only matching (4 s) recalls 0.28 (+60 s control 0.04).
  In this period the lower-ERZ intrusion also produced events: r3
  associated 1,739 pre-mainshock events, only 332 inside the summit box.
- Pick support: 60 % of the missed events have PhaseNet P picks at ≥ 6
  stations within 15 km (+60 s control 1 %), but S picks are almost absent
  (median 0), so the r1–r4 minima (10 picks, 3 S) dropped them.

Knobs (one round, measured stage by stage):

1. Association: `association.yaml` min 6 picks / 6 P / 0 S / 6 stations
   (r1–r4: 10 / 4 / 3 / 6), and NonLinLoc `LOCMETH` minimum phases 10 → 6
   and minimum S 3 → none (`nonlinloc.yaml` `min_phases`, `min_s_phases`;
   the first attempt left NLL at 10/3 and every P-only event failed).
   Stage 03: 5,864 → 6,591 events (box 2,762 → 3,059); the 280 P-only box
   events match some reference in 50 % of cases (+60 s control 7.5 %).
   Stage 05 (full catalog, box): Shelly 0.514 → 0.527, Wei 0.560 → 0.597,
   Matoza 0.841 → 0.862, ComCat 0.897 → 0.907; v1 subsets unchanged
   (P-only events rarely pass v1).
2. Stage 60: `templates.split_utc` = Mw 6.9 origin — the greedy cover runs
   separately per period. 511 templates (r4 400), 66 pre-mainshock (r4 29).
   Prepare kept 420; 3,360 jobs, 3.8 h.

Null run (05-02 + 05-06, channel circular shift, 6 s): 7.7 % false at
N×MAD 9, **1.2 % at 9.5**, 0.14 % at 10. By day, at 9.5: 05-02 (pre-
mainshock) 2.7 % (5 of 183), 05-06 0.8 % (5 of 648); at 10: 0.7 % / 0.
Final threshold stays 9.5 (Kaikōura r4 accepted 1.4 %); the pre-mainshock
false share is higher but rests on 5 null events.

Result (2026-10-26): **not adopted as exported.** r5 catalog
`export/r5/60_catalog/catalog_events.csv` (9,130 events) box-scores
Shelly 0.716 (pre-Mw 6.9 0.376), Wei 0.698, Matoza 0.903, ComCat 0.938
(r4: 0.641 / 0.196 / 0.667 / 0.867 / 0.917), but the pre-mainshock gain is
one mislocated template. 162 of the 182 pre-mainshock M&L matches to Shelly
come from `gamma_0000094`, an event admitted by knob 1 (2 S picks; 10
stations, gap 165°, NLL σx 1.0 km, RMS 0.51 s). Its detections are real
(|dt| to Shelly 0.36 s), but they inherit its position ~6 km SE of the
Shelly pre-mainshock cluster: a false cluster of ~160 events. Pre-mainshock
M&L matches lie 5.9 km from Shelly (r4 2.1 km). The off-fault metric
(0.23 % → 0.33 %) misses it because the offset stays inside the dense summit.

Without that template's detections: Shelly 0.631 (pre 0.173), Wei 0.692,
Matoza 0.886, ComCat 0.929. With the Ridgecrest template rule (gap ≤ 150°,
σx ≤ 0.8 km; 151 of 420 templates fail, 10 of 53 pre-mainshock), approximated
by dropping their detections without a re-merge: 0.620 / 0.661 / 0.875 / 0.915.
The period-split templates add almost nothing; knob 1 helps Wei, Matoza and
ComCat slightly. The evaluation layer stays on r4.

### r6 — stage 62 template relocation (CC double difference): rejected; final stays r4

`01_pipeline/62_template_relocation.py` relocates the r5 box events (3,203,
all 420 kept templates) with hypoDD on pick (dt.ct) and ccdt (dt.cc)
differential times; HVO model as 0.5/1-km constant layers; Ridgecrest
cc3_d1 weighting; acceptance by ≥ 6 CC links, no limit on the move.

1. Nearest-neighbour pairs only (8 km, 40): `gamma_0000094` got no CC data —
   its nearest neighbours are the events around its wrong position.
   Relocated set moved ~1 km south (hypoDD ignores station elevations): a
   frame change (Wei 1.42 → 1.05 km, Shelly 0.78 → 0.86 km).
2. Plus co-detection pairs (a template with the located events its own
   detections coincide with, ±1.5 s; +5,843 pairs) and the NLL frame kept
   (median displacement of quality-passing relocated events removed): 374
   templates relocated; template offsets p90 vs Shelly 3.04 → 2.25 km, vs Wei
   3.64 → 2.62 km; all events vs Shelly 0.78 → 0.95 km, vs Wei 1.42 → 1.14 km.
   `gamma_0000094` moved 3 km further from the Shelly cluster, then left the
   solution. Its 92 co-detected partners (73 pre-mainshock) sit at the same
   wrong place: median 1.8 km from it, 6.3 km from Shelly's pre-mainshock
   cluster, gap 220°, σx 1.5 km. The whole pre-mainshock family is
   mislocated together (small events picked on one side of the network);
   relative relocation keeps a shared bias, so it cannot fix this.
3. Export with NLL positions and the full Ridgecrest/Maple location-quality
   rule instead (≥ 1 ccdt CC link, gap ≤ 150°, σx ≤ 0.8 km, for picked events
   and templates; `--positions nll`): 6,392 events, 2,111 picked box events
   and 161 of 420 templates dropped.

| box-scored | r4 | r5 | r6 (quality rule) |
|---|---|---|---|
| Shelly (pre / post) | 0.641 (0.196 / 0.953) | 0.716 (0.376 / 0.954) | 0.583 (0.148 / 0.887) |
| Wei | 0.667 | 0.698 | 0.485 |
| Matoza | 0.867 | 0.903 | 0.645 |
| ComCat | 0.917 | 0.938 | 0.675 |
| epi vs Shelly, all / pre (km) | 0.89 / 1.15 | 1.10 / 5.69 | 0.89 / 0.78 |
| > 1 km from every ref. event | 0.23 % | 0.33 % | 0.03 % |

On the summit, ≥ 1 CC link (ccdt CC ≥ 0.7; most summit pairs come out
anticorrelated or low) and gap ≤ 150° reject many sound events, including
post-mainshock ones (ComCat post 0.955 → 0.680): too blunt here, as on
Kaikōura. **Decision (2026-10-26): the expert catalog stays r4.** The
pre-mainshock gap is an absolute-location limit for small summit events
with one-sided station coverage, not a detection or relocation one. Configs
are back at r4 values; the code options added for r5/r6 (NLL `min_phases`,
`templates.split_utc`, stage 62) default to r4 behaviour.

### r7 (2026-10-27) — NonLinLoc LOCMETH EDT_OT_WT (Prague r5 method)

`nonlinloc.yaml location_method: EDT_OT_WT`. r7 = r3 stages 01–03
(hardlinked) + stage 04 + stage 05; 09/10 not rerun. Stage-04 test on the r3
associations: Shelly epicentral 0.79/3.83 → 0.69/2.49 km, Wei p90 5.73 →
4.75 km, depth MAD 0.61 → 0.52 km. Stage 64 moves the r4 catalog into the r7
frame: 5,090 picked events relocated, 2,359 M&L events shifted with their
templates (template displacement median 0.34 km, p90 3.96 km), 774 kept
(picked events not LOCATED in either round).

| final catalog | Shelly R | epi median / p90 | dZ (MAD) | Wei epi median / p90 | Matoza p90 | ComCat p90 | > 1 km from Shelly ∪ Wei ∪ Matoza (box) |
|---|---|---|---|---|---|---|---|
| r4 | 0.642 | 0.892 / 2.681 | +0.55 (0.58) | 1.571 / 5.786 | 3.739 | 2.667 | 0.23 % |
| **r7** | **0.649** | **0.758** / 3.121 | +0.54 (**0.49**) | **1.456 / 5.209** | **3.078** | **2.580** | **0.19 %** |

Matches beyond 2 km / 5 km fall for every reference (Shelly 243 → 218 /
54 → 50; Wei 1,015 → 976 / 310 → 266). The Shelly p90 rises because of
the pre-Mw 6.9 family (mislocated together under both methods, r5/r6): its
M&L rows move from 2.06 to 3.14 km (median, 68 matches) and its picked
rows' p90 from 5.3 to 8.1 km, while post-mainshock rows improve (picked
0.74/2.47 → 0.67/2.12 km, M&L 1.03/2.47 → 0.79/2.26 km). **Adopted**;
evaluation layer = r7.

## Baseline corrections (2026-10-28) — stages 65, 67

Metrics v1 exposed three pipeline defects shared across cases (user decision 2026-10-28:
unfreeze the expert baselines). Catalog-level rounds, no rerun of stages 01-60:

- **r8** (stage 65, direct ML): 351 picked events with a direct ML
  (≥ 3 stations, MAD ≤ 0.5), 313 adopted (312 had no magnitude);
  direct − chain by direct ML: (1.0, 2.0] -0.03 (n 5), (2.0, 3.0] +0.20 (n 29), (3.0, 3.5] +0.03 (n 4), (3.5, 4.0] -0.41 (n 1).
- **r9** (stage 67, coda ghosts): 49 Match&Locate detections removed (of 299 with M ≥ 1.5); rule from the Ridgecrest blind review.
- Final catalog **r9** (8,174 events) replaces r7 as expert final in `evaluation/metrics_v1.yaml`. Metrics v1, expert final:

| metric | r7 | r9 |
|---|---|---|
| f1_M2 | 0.79 | 0.81 |
| f1_M3 | 0.81 | 0.83 |
| f1_M4 | 0.80 | 0.80 |
| precision_M2 | 0.70 | 0.73 |
| dmag_mean_M4 | 0.05 | 0.05 |
| dmag_slope_per_unit | -0.13 | -0.13 |
| recall_norm | 1.16 | 1.16 |
