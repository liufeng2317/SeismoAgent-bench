# BAKER2021_0220200316 — local pick-level catalog audit

## Provenance and evidence status

| Field | Value |
|---|---|
| Source reference | Baker et al. (2021), *Monitoring the 2020 Magna, Utah, Earthquake Sequence with Nodal Seismometers and Machine Learning* |
| Article DOI | [10.1785/0220200316](https://doi.org/10.1785/0220200316) |
| Data release | ISC dataset [10.31905/LGR1456Y](https://doi.org/10.31905/LGR1456Y) |
| Original archive | [`raw/ISC_catalogForISC.zip`](./raw/ISC_catalogForISC.zip) |
| Archive contents | `catalogForISC/README.txt` and `catalogForISC/magna2020MLCatalog.csv` |
| Local file | [`BAKER2021_0220200316__catalog_picks.csv`](./BAKER2021_0220200316__catalog_picks.csv) |
| Local-file SHA-256 | `103ff3f3a91b19baf64ae56e1ece5193fa373ca4491819cff77cb3dceab750d1` |
| Archive inner-file identity | Byte-for-byte identical to `magna2020MLCatalog.csv` inside the ISC ZIP |
| Article PDF | **Missing locally.** No paper reading note is created until the verified PDF is obtained; catalog statistics below are file-level audits, not a substitute for article extraction. |

The release is a **pick-level** CSV.  Event-level fields are repeated on each
pick row, so the 329,611 rows must not be counted as 329,611 earthquakes.
`event_number` and `catalog_evid` each identify 5,885 events in this local copy;
all rows within either key have consistent origin/location/magnitude fields.

## Row, event, and field audit

| Field | Local result |
|---|---|
| Pick rows | **329,611** |
| Header fields | 28 |
| Unique `event_number` | **5,885** (range 0–13,984; gaps are expected per ISC README) |
| Unique `catalog_evid` | **5,885**, no missing; one-to-one with `event_number` in this copy |
| Picks per event | 10–364; median 36; mean 56.01 |
| Origin-time range | 2020-03-18 13:09:31.390–2020-04-29 17:41:46.790 UTC |
| Arrival-time range | 2020-03-18 13:09:33.830–2020-04-29 17:41:54.280 UTC |
| Event latitude | 40.4445–40.9786667°N |
| Event longitude | −112.3006667–−111.8111667°E |
| Event depth | −3.41–19.89 km (source convention) |
| `magnitude` | −9.99–5.70; −9.99 occurs for 806 event rows after event-level collapse |
| `magnitude_type` | Event-level: `Mxc` 3,100; `d` 1,223; `l` 753; `h` 16; `w` 3; missing 790 |
| `Mj` | Independent calibration field; −9.99 for 5,249 of 5,885 event rows |
| Phase rows | 141,972 P and 187,639 S |
| Networks | `UU`: 326,969 rows; `GS`: 2,642 rows |
| Station codes | 207 total: 205 under `UU`, 2 under `GS` (`UT01`, `UT02`) |
| Channel codes | 6 (`EHN`, `EHZ`, `ENN`, `ENZ`, `HHN`, `HHZ`) |

The article-level rounded values of approximately 142,000 P picks and 188,000 S
picks agree with the local file.  The local release ends on 29 April rather
than the article's broad 18 March–30 April study description; preserve the
local endpoint and do not add a synthetic 30 April row.

### Source-native field semantics

The archive README defines the principal fields as follows:

- `event_number` is a local event counter; its maximum is not the number of
  retained events because quality-control filtering leaves gaps.
- `network`, `station`, `channel`, `phase`, `arrival_time`, and
  `static_correction` describe each P/S pick.
- `event_latitude`, `event_longitude`, `event_depth`, `origin_time`,
  `azimuthal_gap`, `n_weighted_residuals`, `n_first_motions`, and `rms` are
  HypoInverse2000 location/QC fields repeated on each pick.
- `magnitude` and `magnitude_type` may originate from the UUSS catalog or a
  cross-correlation catalog; source types include `w`, `l`, `d`, `h`, and
  `Mxc`.  They are not one homogeneous magnitude scale.
- `catalog_evid` is the corresponding UUSS/cross-correlation event ID.
- `Mj` is an independent James Holt calibration field and is sparse; `-9.99`
  is a source sentinel, not a measured negative magnitude.

No field in this release directly labels “temporary node” versus “permanent
station”.  The article's 180 three-component 5-Hz Magseis deployment must
therefore be retained as article metadata, while the local 205 `UU` station
codes plus two `GS` codes are the observed pick inventory.  These counts are
not interchangeable.

## Frozen benchmark window audit

The common Magna v1 window is
`2020-03-18T00:00:00Z <= origin_time < 2020-03-26T00:00:00Z`, with:

```text
40.69 <= latitude <= 40.84°N
-112.14 <= longitude <= -111.94°E
-1.3 <= depth_km <= 13.1
```

Event counts are computed after collapsing to one row per `event_number`; pick
counts are retained separately.

| Selection | Events | Pick rows | P / S | UU / GS rows | Stations | Event magnitude range |
|---|---:|---:|---:|---:|---:|---:|
| Time only | 3,782 | 164,276 | 68,525 / 95,751 | 164,211 / 65 | 201 | −9.99–5.70 |
| Time + common spatial/depth mask | **3,712** | **161,567** | 67,377 / 94,190 | 161,503 / 64 | 201 | −9.99–5.70 |
| Time + mask + `magnitude > −4` | 3,351 | 150,379 | 62,681 / 87,698 | 150,323 / 56 | 201 | −1.0888675–5.70 |

For the recommended common mask, the event ranges are latitude
40.6905–40.8285°N, longitude −112.1396667–−111.9463333°E, and depth
0.1–13.1 km.  The local release has no missing `magnitude` values at the CSV
row level, but `-9.99` is a source sentinel; the `magnitude > -4` row is a
sensitivity subset, not a new normalized magnitude scale.

## Catalog role and comparison rules

- **Role:** secondary ML/pick-level catalog and nodal-array condition.  It is
  especially useful for pick timing, association density, and event recovery
  under a dense temporary deployment.
- **Quality tier:** Q2 for ML picks/association and network-specific detection;
  Q3 as an operational baseline.  It is not Q1 absolute truth merely because
  it has many picks.
- **Do not merge with Pang:** Pang uses a 39-station/226-channel permanent
  waveform subset and matched filtering; Baker combines UUSS and nodal/other
  pick streams and publishes repeated pick rows.  Keep separate observation
  conditions and score event-level and pick-level tasks separately.
- **Magnitude caution:** compare source-native fields only after selecting a
  common scale or treating magnitude as auxiliary.  `Mxc`, `d`, `l`, `h`, `w`,
  and `Mj` have different provenance.
- **Article gap:** obtain the Baker PDF before recording exact detector,
  association, deployment, and QC parameters as article facts.  The local
  `README_legacy.txt` is provenance metadata, not a substitute for the paper.

No event-level normalized CSV is generated by this audit.  A future derived
file should retain the first pick row per `event_number`, add an explicit
`pick_count`, and preserve the source row hash/event crosswalk.
