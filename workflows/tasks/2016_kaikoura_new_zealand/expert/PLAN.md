# Kaikōura 2016 expert pipeline — round plan

Same round mechanics as Magna, Maple Creek, Prague and Kīlauea: round
identity = config `round` + `export_root`, one behavioural knob per round,
previous rounds immutable, never tune to force reference agreement. Task =
the frozen common mask (−43.5…−41.2 N, 172.0…175.2 E, depth −3…60 km),
window 2016-12-01 → 12-09 (two weeks after the Mw 7.8). Feedback: stage 05
against Tan et al. (2024) SUGAR S10 (detection primary), Lanza et al. (2019)
HypoDD (location primary), Chamberlain et al. (2021) corrected GrowClust and
GeoNet operational.

## Data preparation (2026-10-23)

- Velocity model: Chamberlain et al. (2021) 1-D average of the NZ3D model
  over their study region (`vzmodel.txt` from their code release, GitHub raw
  at commit ec0ae1f; registered `chamberlain2021_nz3d_avg_1d`, 25 rows, depth
  below sea level). Gradient-like node model → `velocity_layering: linear`;
  datum 0.0 km.
- Stations: GeoNet NZ (HH/EH) + EarthScope Z1 temporary deployment; two
  StationXML files merged by stage 09. 53 instruments. Four NZ stations split
  their metadata epochs on 2016-12-08 with identical geometry: stages 01/03
  accept split epochs when geometry is identical and the epochs contiguous.
- Masked reference counts: Tan 9,720, Lanza 122, Chamberlain 2,260 (depth m →
  km), GeoNet 1,507 (earthquake + unknown types). Anchor: GeoNet M5.5
  2016p913880 (2016-12-04 03:15:47), in window.

## Round log

### r1 (2026-10-23/24) — baseline port

- 02: first attempt failed on 18 day-boundary blocks (NZ.OKCZ, WAZ, PAWZ,
  TSZ, WEL): 100 Hz GeoNet day files change sample phase at midnight, so the
  components no longer share one grid. Fix: with `picking.resample_to_hz`
  set, target-rate traces off the absolute grid (> 1e-3 sample) are also
  Lanczos-interpolated onto it (the Prague TA path); `resample_to_hz: 100`.
  02 rerun from scratch: 419,126 picks (P 218,214), 1,696 blocks.
- 03: 5,233 events; 98,980 of 419,126 picks associated (24 %); median 8
  stations; median GaMMA RMS 0.42 s. 04: 5,220 LOCATED, median RMS 0.39 s,
  145 at a depth bound. Comparison scope 4,758; v1 1,898.
- 05:

| Reference | Masked | Matched (v1) | median \|dt\| | epicentral | dZ (MAD) |
|---|---|---|---|---|---|
| Tan | 9,720 | 0.366 (0.168) | 0.42 s | 3.99 km | +3.08 (3.09) |
| Lanza | 122 | 0.828 (0.549) | 0.53 s | 4.04 km | −0.10 (1.52) |
| Chamberlain | 2,260 | 0.563 (0.272) | 0.53 s | 4.52 km | +2.81 (2.65) |
| GeoNet | 1,507 | 0.782 (0.518) | 0.41 s | 3.53 km | −3.78 (5.97) |

Reference-vs-reference (same 4 s / 15 km matcher): Chamberlain–Lanza
epicentral p50 1.2 km, Tan–Lanza 1.7, Tan–Chamberlain 2.3, GeoNet–others
3.2–4.3 km; origin-time offsets between references reach 0.6 s
(Lanza − Chamberlain +0.63 s), so |dt| is not diagnostic here. Our 4.0 km vs
Lanza is far from the 1.2 km the 3-D-model catalogs reach between themselves;
with a single 1-D average over ~200 km and RMS 0.39 s, station terms are the
first lever.

### r2 — knob: iterated NLL station delays (`station_delays.iterations: 2`)

Maple Creek r5 settings (min 20 picks, RMS ≤ 0.5 s, gap ≤ 180°, σz ≤ 3 km).
01–03 hardlinked from r1; 04, 05, 09, 10 rerun.

Result (2026-10-24): **adopted.** NLL RMS 0.39 → 0.29 s; epicentral vs
Chamberlain 4.52 → 3.71 km, Tan 3.99 → 3.36, Lanza 4.04 → 3.81, GeoNet
3.53 → 3.41; depth vs Tan +3.1 → +1.9 km, vs Chamberlain +2.8 → +1.4 km;
recall unchanged (v1 count falls 1,898 → 1,290: the `large_locator_shift`
flag inflates once NLL has station terms and GaMMA does not, as at Maple).
The remaining offset is systematic: 2–3 km north of the three 3-D-model
relocations (median dN +1.9…+2.9 km) but +0.3 km vs GeoNet (gap < 180°:
2.7 km), i.e. the 1-D vs 3-D model difference — documented, not tuned.

### r3 — knob: GaMMA `dbscan_eps` 10 → 15 s

Missed GeoNet events get *worse* with magnitude (recall 0.91 at M1.5–2,
0.74 at M > 2). Missed M > 2 events have a median 14 stations with P picks
in the 25 s after origin and 0 % of those picks associated; half have no
expert event within 30 s. Scratch test on the three hours with most misses
(12-04 08Z, 12-08 01Z, 12-01 15Z; GaMMA positions):

| Variant | Events | GeoNet | GeoNet M>2 | Chamberlain | Tan |
|---|---|---|---|---|---|
| r2 (eps 10) | 111 | 0.50 | 6/21 | 0.63 | 0.36 |
| max_sigma11 3.0 | 113 | 0.50 | 6/21 | 0.63 | 0.36 |
| eps 5 | 7 | 0 | 0/21 | 0 | 0 |
| eps 15 | 133 | 0.90 | 18/21 | 0.87 | 0.43 |
| eps 20 | 111 | 0.90 | 19/21 | 0.63 | 0.36 |
| min picks 6 / stations 4 / S 2 | 181 | 0.80 | 15/21 | 0.73 | 0.47 |

Over a 260 km aperture one event's picks span > 40 s; at eps 10 s DBSCAN
splits them into sub-clusters that individually fail the minimum-pick
gates. eps 15 recovers the large events with 22 extra events; 20 starts
merging neighbours (Chamberlain drops back). 01–02 hardlinked from r2;
03–10 rerun with r2's station delays.

Result (2026-10-24): **adopted.** 6,143 LOCATED (r2 5,217); associated
picks 98,980 → 128,612; comparison scope 5,666, v1 2,396.

| Reference | r2 matched | r3 matched (v1) | epicentral r2 → r3 | dZ r3 (MAD) |
|---|---|---|---|---|
| Tan | 0.367 | 0.415 (0.207) | 3.36 → 3.61 km | +0.88 (2.66) |
| Lanza | 0.828 | 0.984 (0.541) | 3.81 → 3.07 km | −1.18 (1.38) |
| Chamberlain | 0.566 | 0.619 (0.303) | 3.71 → 3.96 km | +0.30 (2.44) |
| GeoNet | 0.787 | 0.909 (0.619) | 3.41 → 3.23 km | −6.47 (5.84) |

NLL RMS 0.29 → 0.36 s: the recovered events are the larger, wider-aperture
ones with larger 1-D-model residuals. The remaining gap is small events
(Tan, Chamberlain — both detection catalogs).

Pick-gate test on top of eps 15 (same three hours, scratch, not a round):

| Variant | Events | Tan | Chamberlain | GeoNet |
|---|---|---|---|---|
| eps 15 (r3) | 133 | 82/190 | 26/30 | 27/30 |
| + min picks 8 / stations 5 | 162 | 89/190 | 26/30 | 27/30 |
| + min picks 6 / stations 4 / S 2 | 202 | 97/190 | 29/30 | 27/30 |

The added events match a reference ~25 % of the time (r3's own: 62 % vs Tan,
the most complete reference) → mostly false; not adopted. Small-event
detection goes to stage 60 Match&Locate, whose false rate a null run
measures (next, after the Kīlauea M&L run frees the CPUs).

### r4 — stage 60 Match&Locate seeded by r3

`00_config/match_locate.yaml` (from Kīlauea): NZ model densified into 0.5 km
constant sublayers down to 60 km (published rows below; the head-wave search
is quadratic in the layer count); `max_distance_km: 80` — the median v1 event
has 1 station within 20 km, 6 within 60, 8 within 80; search ±1 km.

Pilot (12-04, 20 templates by station count, 5 % cover at 1 km): at N×MAD 9,
union Tan 45.0 → 47.2 %, Chamberlain 65.5 → 71.5 %, 239 new events. Null run
(channel circular shift, same templates): **1.1 % false at N×MAD 9**, 0.65 %
at 9.5, 0 at ≥ 10. M&L alone matches Tan for 143/363 boxed detections; of the
rest, 123 have no Tan event within 15 s — the two most prolific templates
(Cape Campbell cluster, −41.69 / 174.24, 145 detections each, median spacing
170 s, CC 0.3 over 30 channels) — real cluster events beyond the references.
Full run: cover 2 km → 803 templates (88 % of v1; 1 km would be 1,350).

Full run (2026-10-24): 803 templates, 708 kept by prepare, 5,664 jobs.
Null run (12-02 + 12-06, channel circular shift, 6 s): false fraction 87 %
at N×MAD 8, 43 % at 8.5, 9.2 % at 9, **1.4 % at 9.5**, 0.3 % at 10 → final
9.5 (inside the 1–2 % Magna/Maple accepted; 10 costs ~1.5 points recall).

r4 catalog `export/r4/60_catalog/catalog_events.csv`: **11,448 events**
(r3 NLL 6,164 + 5,284 M&L); M&L magnitudes chained from 295 ML templates to
519 of 708. Box-scored (stage-05 readers and mask):

| | r3 NLL | M&L | **r4 union** |
|---|---|---|---|
| Tan | 0.414 | 0.302 | **0.492** |
| Lanza | 0.984 | 0.656 | **0.984** |
| Chamberlain | 0.618 | 0.570 | **0.775** |
| GeoNet | 0.907 | 0.587 | **0.915** |

Location by row source (evaluation-layer matcher): vs Chamberlain, M&L rows
3.79 km epicentral / dZ +0.33 (NLL rows 3.95 / +0.33) — as good as picked;
vs Tan 4.99 km (NLL 3.61): small events placed at 2 km-spaced templates.
The 1-D vs 3-D offset (r2) applies to both.

### r5 — denser Match&Locate templates (1 km cover, min 8 stations)

Miss diagnosis of r4 (2026-10-26): missed Tan events have almost no PhaseNet
pick support (median 1 P station within 60 km, +60 s control 0), so only
template matching can add them, and Tan recall falls with the distance to the
nearest r4 template: 0.71 within 0.5 km, 0.66 at 0.5–1 km, 0.56 at 1–2 km,
0.33 at 2–4 km, 0.20 at 4–8 km, 0.12 beyond (35 % of Tan events > 2 km away).
Knob: `templates.cover_radius_km` 2 → 1 and `min_stations` 10 → 8 →
1,635 templates (1,492 kept by prepare, 33,815 rows), 11,936 jobs, 9.4 h.

Null run (12-02 + 12-06, channel circular shift, 6 s): 13.3 % false at N×MAD
9, 1.8 % at 9.5, **0.26 % at 10** → final 10. 9.5 is within the 1–2 %
accepted elsewhere but 10 cuts false detections ~7× for −1.4 (Tan) / −1.1
(Chamberlain) recall points.

Location checks before adoption (the Kīlauea r5 lesson): matched offsets by
row source are as in r4 (vs Tan: M&L 4.5–4.7 km, NLL 3.5 km — the documented
1-D vs 3-D offset); the 1,269 new-event matches to Tan spread over 642
templates (largest 1.2 %; one template with ≥ 10 matches has a median offset
> 8 km, 0.8 % of matches); events > 5 km from every Tan/Chamberlain/Lanza
event 1.21 % → 0.94 %.

Result (2026-10-27): **adopted.** r5 catalog
`export/r5/60_catalog/catalog_events.csv`: 13,426 events. Box-scored
(stage-05 readers and mask, export separation 6 s):

| | r4 | r5 @ 9.5 | **r5 @ 10** |
|---|---|---|---|
| Tan | 0.492 | 0.537 | **0.523** |
| Chamberlain | 0.775 | 0.830 | **0.819** |
| Lanza | 0.984 | 0.984 | **0.984** |
| GeoNet | 0.915 | 0.919 | **0.918** |

Evaluation layer: r5 (Tan 52.3 %, Chamberlain 81.9 %, 3.77 km, dZ +0.20).

### r6 (2026-10-27) — NonLinLoc LOCMETH EDT_OT_WT (Prague r5 method)

`nonlinloc.yaml location_method: EDT_OT_WT`. r6 = r3 stages 01–03
(hardlinked) + stage 04 (two station-delay passes, 36 min) + stage 05; 09/10
not rerun. Stage-04 test on the r3 associations: Chamberlain 3.95/7.45 →
3.78/7.05 km, Tan 3.61/7.56 → 3.46/7.33 km, recall +0.8 / +0.4 points. Stage
64 moves the r5 catalog into the r6 frame: 6,137 picked events relocated,
7,262 M&L events shifted with their templates (template displacement median
0.80 km, p90 3.87 km), 27 kept.

| final catalog | Tan R | epi median / p90 | Chamberlain R | epi median / p90 | dZ (MAD) | Lanza epi median / p90 | GeoNet R |
|---|---|---|---|---|---|---|---|
| r5 | 0.523 | 3.71 / 7.77 | 0.819 | 3.77 / 6.96 | +0.20 (2.53) | 3.17 / 6.34 | 0.918 |
| **r6** | 0.523 | **3.39 / 7.74** | **0.821** | **3.41 / 6.59** | +0.53 (**2.13**) | **3.05 / 6.07** | 0.916 |

M&L rows improve most (vs Lanza 4.75 → 2.49 km, vs Tan 4.51 → 4.10 km).
GeoNet loses 3 matches. The 1-D vs 3-D offset (r2) remains the dominant term.
**Adopted**; evaluation layer = r6.

## Baseline corrections (2026-10-28) — stages 65, 67

Metrics v1 exposed three pipeline defects shared across cases (user decision 2026-10-28:
unfreeze the expert baselines). Catalog-level rounds, no rerun of stages 01-60:

- **r7** (stage 65, direct ML): 544 picked events with a direct ML
  (≥ 3 stations, MAD ≤ 0.5), 278 adopted (273 had no magnitude);
  direct − chain by direct ML: (1.0, 2.0] +0.11 (n 106), (2.0, 3.0] +0.32 (n 155), (3.0, 3.5] +0.24 (n 5), (3.5, 4.0] +1.53 (n 2), (4.0, 5.0] +0.18 (n 3).
- **r8** (stage 67, coda ghosts): 3 Match&Locate detections removed (of 166 with M ≥ 1.5); rule from the Ridgecrest blind review.
- Final catalog **r8** (13,423 events) replaces r6 as expert final in `evaluation/metrics_v1.yaml`. Metrics v1, expert final:

| metric | r6 | r8 |
|---|---|---|
| f1_M2 | 0.93 | 0.93 |
| f1_M3 | 0.98 | 0.95 |
| f1_M4 | 1.00 | 0.94 |
| f1_M5 | – | 1.00 |
| precision_M2 | 0.96 | 0.95 |
| dmag_mean_M4 | -0.25 | -0.11 |
| dmag_mean_M5 | – | -0.10 |
| dmag_slope_per_unit | -0.08 | -0.03 |
| recall_norm | 1.17 | 1.17 |
