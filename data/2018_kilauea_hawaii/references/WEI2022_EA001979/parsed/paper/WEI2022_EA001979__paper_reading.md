# Wei et al. (2022) — paper reading and catalog-construction audit

## Identity and evidence status

| Field | Extracted information | Evidence / status |
|---|---|---|
| Authors | XiaoZhuo Wei, Yang Shen, Jacqueline Caplan-Auerbach, Julia K. Morgan | PDF title block; MinerU `content_list_v2` page 0 |
| Citation | “An Improved Earthquake Catalog During the 2018 Kīlauea Eruption From Combined Onshore and Offshore Seismic Arrays” | PDF title block |
| Journal | *Earth and Space Science*, 9 (2022) | PDF citation block |
| DOI | [10.1029/2021EA001979](https://doi.org/10.1029/2021EA001979) | DOI / landing page |
| Article type | Research article that constructs a new event catalog | Abstract, Sections 2–6 |
| Associated release | Article Data Set S1 / Dryad [10.5061/dryad.np5hqbzw9](https://doi.org/10.5061/dryad.np5hqbzw9) | PDF Data Availability Statement; local README |
| Local paper parse | `parsed/WEI2022_EA001979__paper__mineru.md` | 14-page MinerU `content_list_v2`; page boundaries retained in this note as content-list page anchors |
| Supporting information | `supplement/Wei2022_Kilauea_SI.pdf` | Present locally; Text S1–S11 and Tables S1–S4 are referenced by the paper. The SI PDF has not been independently text-extracted here, so exact SI-only numerical parameters remain provisional. |

This is a genuine catalog-construction paper, not an overview or a method-only
paper. Its product is deliberately broader than the HVO operational catalog and
is methodologically distinct from the summit template-matching catalog of
Shelly & Thelen (2019).

## Scientific scope

- **Sequence:** the 2018 Kīlauea eruption, including summit caldera collapse,
  lower East Rift Zone intrusion/eruption, Puʻu ʻŌʻō activity, and the 4 May
  2018 (M_w 6.9) Kalapana earthquake and offshore aftershocks.
- **Study interval:** 2018-03-01 through 2018-09-30 UTC (Section 2, Table 1;
  MinerU pages 1–2).
- **Spatial scope:** the Island of Hawaiʻi and submarine south flank; the local
  catalog extrema are latitude 18.691332–20.392835°N, longitude
  −156.289628–−154.385413°E, and depth −4.121094–69.853516 km. These are
  file-level extrema, not a recommended benchmark mask.
- **Catalog objective:** improve detection and 3-D location coverage, especially
  in the lower East Rift Zone and offshore area where permanent onshore HVO
  stations have sparse geometry.
- **Completeness target:** the paper estimates \(M_c\) around 1.4, fairly stable
  over the study subperiods (Section 4.2, MinerU page 8). This is a catalog-level
  estimate, not a guarantee of uniform completeness across the changing network.

## Observation and network conditions

The workflow used most publicly available data, downloaded from IRIS, plus
Raspberry Shake data (Section 2, MinerU pages 1–2):

| Network | Role / availability |
|---|---|
| HV | HVO permanent backbone; nominally 2018-03-01–09-30 |
| PT | Pacific Tsunami Warning Center permanent network; nominally full interval |
| IU | Global Seismograph Network stations; nominally full interval |
| Z1 | Rapid-response nodal array; 2018-06-15–07-26 |
| Z6 | Rapid-response OBS array; 2018-07-10–09-16 |
| 4S | Four-station temporary broadband network; starts 2018-07-27 and continues to the study end |
| AM | Raspberry Shake supplementary network; nominally full interval, used in re-association rather than initial STA/LTA detection |

The paper does not provide one fixed station count because the network is
heterogeneous and changes through the eruption. Velocity components were used
where available; accelerometer components were used only when they were the
only choice. Noisy nodal stations and malfunctioning OBS components were
excluded (Section 2 and Text S1, MinerU page 2). This changing observation
condition is a central interpretation constraint: the apparent event-rate jump
around 16–21 June tracks deployment of the Z1 nodal array, and the July decline
tracks its removal (Section 5.1, MinerU page 10).

## Catalog-construction workflow

```text
IRIS/HVO/temporary-network waveforms
    → component-specific bandpass and recursive STA/LTA triggers
    → association from earliest trigger (P=5 km/s, S=3 km/s)
    → polarization/kurtosis automatic P/S picks and SNR filtering
    → NonLinLoc 3-D location with topography mask
    → valid-pick/RMS/weight quality filtering
    → location-based re-association (including AM detections)
    → second NonLinLoc location
    → coda/duration magnitude, or local magnitude for large/overlapping events
    → duplicate-event removal and final catalog
```

### Detection and preprocessing

- OBS traces were zero-phase Butterworth bandpass filtered at 8–12 Hz; other
  records at 8–20 Hz because of the OBS “6 Hz problem” (Section 3.1, MinerU
  page 2).
- Recursive STA/LTA was applied to every component. Standard STA/LTA windows
  were 1 s / 10 s; both were halved for stations within 4 km of the caldera.
  Start threshold was 3.0. End threshold was 1.0 for OBS/isolated stations and
  1.2 for caldera/remaining stations. AM was omitted from this initial step.
- Association began with the earliest triggered station and predicted P/S
  windows using 5 and 3 km/s. Instrument responses were removed before later
  processing (Sections 3.1–3.2, MinerU page 2).

### Automatic phase picking and association

- P was picked on vertical components and S on horizontal components where
  available. A polarization filter and kurtosis-rate picker used a 0.4 s
  polarization window and 0.75 s kurtosis window.
- Three-component picks required SNR ≥16 (P) and ≥8 (S); single-component picks
  used relaxed thresholds of 10 and 5. Picks more than three standard deviations
  from the event's arrival-time mean were removed.
- For intense caldera sequences, arrivals were split when two time-cluster
  centroids differed by more than 1.8 s (unless fewer than three picks), reducing
  assignment of a previous/next event's phase (Text S4, MinerU pages 2–3).

### Location, re-association, and quality control

- NonLinLoc was run with a 3-D velocity model based on Park et al. (2009),
  extended outside the original model space using averaged profiles. (V_p/V_s)
  was fixed at 1.732 and a topography mask prevented locations above the
  physical surface (Section 3.4, MinerU pages 4–5).
- P arrivals initially received the highest NonLinLoc weight and S arrivals the
  next level; weights were adjusted by travel-time misfit (Text S6, MinerU
  page 5). Exact level-to-uncertainty mapping is in SI Table S2 and should be
  checked from the local SI before reproducing it.
- A retained event required at least one valid P arrival, at least four valid
  total arrivals, and RMS misfit below 1 s; a pick was valid when its normalized
  weight remained above 0.2. The RMS criterion could be relaxed for events with
  many arrivals (Section 3.5, MinerU page 5).
- Events were re-associated from the located source time/location, then located
  again. Duplicate events were merged when origin times differed by <1 s and
  latitude/longitude differences were <0.1° (Section 3.6, MinerU page 6).

### Magnitude

- The primary magnitude is coda/duration (M_d), measured on vertical records
  with valid P picks after high-pass filtering above 0.75 Hz and envelope
  smoothing. A station correction of 0.272 was applied.
- If coda duration was not measurable (overlapping events, contaminated noise
  window, or very large events), local magnitude (M_L) was estimated from
  Wood–Anderson-equivalent horizontal amplitudes. The paper's equations are in
  Section 3.6 (MinerU page 6).
- At least two station measurements were needed for an event magnitude and its
  standard deviation; three-standard-deviation outliers were removed. Thus
  missing magnitude is expected in the distributed event table and should not
  be silently treated as a failed location.

## Reported populations and quality

The paper reports the following processing populations (Section 4, MinerU page
7; some terms refer to trigger windows rather than final event rows):

| Stage | Article-reported count |
|---|---:|
| Associated event/trigger population | 650,899 |
| Successfully located | 503,339 |
| Locations used for re-association | 420,963 |
| Re-associated / second-location population | 392,789–392,977 (wording distinguishes re-associated and successfully located) |
| Final published catalog | **375,736 events** |
| Events with a measured magnitude | 308,017 |
| Estimated magnitude of completeness | \(M_c \approx 1.4\) |

The local S1 file has exactly 375,736 data rows and no malformed rows. It has no
explicit event ID; `SourceTime` is unique for every row in this file (0 exact
duplicate timestamps), but timestamp uniqueness is not a physical identity
guarantee.

## Benchmark interpretation

| Dimension | Decision |
|---|---|
| Quality tier | **Q2** broad enhanced-detection and 3-D-location reference. It is not Q1 ground truth because picks are automatic, network coverage changes sharply, offshore OBS quality is lower, and 67,719 rows have no magnitude. |
| Best role | Independent cross-check for detection/association, absolute location, offshore/flank coverage, and robustness to network changes. |
| Not suitable for | Directly ranking summit relative-location methods against Shelly without matching space/time/network; interpreting daily rates without station-deployment covariates; treating all rows as equally precise. |
| Independence | Medium–High relative to Shelly: different STA/LTA + polarization/kurtosis + NonLinLoc workflow versus template matching + differential-time hypoDD. They share public HVO/IRIS waveform sources and compare against some of the same catalogs. |
| Primary comparison | Use Wei as secondary for a deliberately matched spatial/time subset; retain network codes and deployment dates as covariates. |

## Local provenance and open actions

- Paper PDF: `data/2018_kilauea_hawaii/references/WEI2022_EA001979/paper/WEI2022_EA001979__paper.pdf`
- MinerU text: `data/2018_kilauea_hawaii/references/WEI2022_EA001979/parsed/WEI2022_EA001979__paper__mineru.md`
- Supporting information: `data/2018_kilauea_hawaii/references/WEI2022_EA001979/supplement/Wei2022_Kilauea_SI.pdf`
- Catalog README and audit: `data/2018_kilauea_hawaii/catalogs/WEI2022_EA001979/README.md` and `README.md`
- Source release: [Dryad 10.5061/dryad.np5hqbzw9](https://doi.org/10.5061/dryad.np5hqbzw9)

Before reproducing the complete workflow, extract the local SI PDF and record
the exact Text S1–S11/Table S1–S4 parameters. For benchmark v1, the primary
remaining decision is whether to count all 2,369 rows in the common summit mask
or only the 1,930 rows with numeric magnitudes; this note records both, while
the existing case summary used the latter as its legacy event-count field.
