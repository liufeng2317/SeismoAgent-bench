# Isken & Mooney (2017) relocated hypocenters

- `source_ref`: `ISKEN2017_BSSA0120160150`

- Source article: Isken & Mooney (2017), BSSA, DOI [10.1785/0120160150](https://doi.org/10.1785/0120160150).
- Official supplement: [BSSA electronic supplement](https://www.seismosoc.org/Publications/BSSA_html/bssa_107-2/2016150-esupp/).
- Original table: [`Table S3`](https://www.seismosoc.org/Publications/BSSA_html/bssa_107-2/2016150-esupp/2016150_esupp_Table_S3.html).
- `ISKEN2017_BSSA0120160150__catalog_relocated_tableS3.csv` is a normalized CSV transcription of the official HTML table.
- `ISKEN2017_BSSA0120160150__source_tableS3.html` is the downloaded official source page; retain it for provenance.
- Detailed catalog audit: [`README.md`](README.md).

The table contains 13 aftershocks from the 2011 Oklahoma sequence, relocated with a gradient half-space model. Fields include origin time, latitude, longitude, depth, horizontal/depth errors, RMS residual, and Mw. It is a small high-quality relocation reference, not a complete regional earthquake catalog.
- Local processing report: [`analysis/catalog_analysis.md`](analysis/catalog_analysis.md).

## Local catalog audit

> Earlier window/mask statistics are exploratory. Current freeze status is defined by the case `analysis/processing.yaml`, which is `not_frozen`; retained historical “frozen” wording does not override it.

### Provenance

- Source: Isken & Mooney (2017), “Relocated Hypocenters and Structural
  Analysis from Waveform Modeling of Aftershocks from the 2011 Prague,
  Oklahoma, Earthquake Sequence,” *Bulletin of the Seismological Society of
  America*, 107(2), 553–562.
- DOI / landing page: [10.1785/0120160150](https://doi.org/10.1785/0120160150)
- Official supplement: [BSSA electronic supplement](https://www.seismosoc.org/Publications/BSSA_html/bssa_107-2/2016150-esupp/)
- Specific product: official **Table S3**, “Relocations of 13 Aftershocks from
  the 2011 Oklahoma Earthquake Sequence Based on a Gradient, Half-Space Model.”
- Source HTML: `ISKEN2017_BSSA0120160150__source_tableS3.html`
- Normalized CSV: `ISKEN2017_BSSA0120160150__catalog_relocated_tableS3.csv`
- Native format: HTML table; local derivative is comma-separated UTF-8 with one
  row per selected aftershock and a header.
- SHA-256 of normalized CSV: `a8a6df207ff71395d6201fac2bf79693481fbcee9c487aa3f1ca1ad8a2c35199`

The HTML source and CSV were checked row by row. The CSV is a normalized
transcription for analysis; the HTML remains the authority for labels (`ERH`,
`ERZ`, `Rms`, and `M_w`) and the original time/number formatting.

### Schema and local audit

| Field | Type / unit | Audit result |
|---|---|---|
| `no` | integer, article row number | 1–13; unique only within this table |
| `time_utc` | ISO-8601 normalized from UTC source | 13 unique second-precision times |
| `latitude_deg` | decimal degrees | 35.452–35.546°N |
| `longitude_deg` | decimal degrees | −96.897 to −96.737°E |
| `depth_km` | km | 4.63–10.08 |
| `erh_km` | ERH/lateral error, km | 0.1 for all rows |
| `erz_km` | ERZ/depth error, km | 0.1–0.2 |
| `rms_s` | RMS residual, s | 0.03–0.05; mean 0.0431 |
| `Mw` | moment magnitude, as table label | 3.1–3.4 |

| Audit item | Result |
|---|---|
| Data rows | **13** |
| Header fields | 9 |
| Unique row numbers | 13 |
| Duplicate times | 0 |
| Exact duplicate rows | 0 |
| Missing cells / parse failures | 0 in current CSV |
| Time range | 2011-11-11 19:19:00 to 2011-12-09 16:46:00 UTC |
| Geographic range | 35.452–35.546°N; −96.897 to −96.737°E |
| Depth range | 4.63–10.08 km |
| Magnitude range | Mw 3.1–3.4 |

These statistics are measurements of the local derivative. The paper's Figure
1 caption describes the selected aftershocks as lying between 11 November and
31 December 2011; the actual distributed Table S3 rows end on 9 December.
Keep those statements separate.

### Construction and quality interpretation

The article does not publish a complete automatic catalog in this product. Its
selection/relocation chain is:

```text
selected `M_L > 3` aftershocks from the Prague sequence
  → manual P/S picks at 19 nearby stations
  → 1-D gradient velocity model based largely on Toth et al. (2012)
  → HYPOINVERSE 2000 hypocenter relocation
  → 25–34 P/S arrivals per event and RMS residual checks
  → Table S3 with location errors and Mw
```

The article reports RMS residuals of 0.03–0.05 s (mean approximately 0.04 s)
and prose location uncertainties “on the order of 1 km”; Table S3 separately
reports ERH 0.1 km and ERZ 0.1–0.2 km. These may be different formal error
definitions or rounded summaries. Until the electronic model/metadata files
are staged, do not collapse them into a single accuracy number.

The article's 2-D `sofi2D` finite-difference experiments are downstream
waveform interpretation. They test whether coda scattering from heterogeneous
Pennsylvanian layers is compatible with the relocated depths; they are not
additional catalog rows or inclusion filters.

### Frozen-window cross-reference

The Prague v1 core selector is the half-open UTC interval:

```text
2011-11-11T00:00:00Z ≤ origin_time < 2011-11-19T00:00:00Z
```

Applying time only to this 13-row table retains **7 events** (rows 1–7). The
remaining rows 8–13 occur after the core window. The seven rows are a sparse
location/structure anchor, not a replacement for the 2,078-event Cochran
primary population. No additional spatial/depth clipping is applied here;
cross-catalog matching should use an explicit tolerance and preserve one-to-
many/ambiguous matches for review.

### Benchmark role

| Dimension | Decision |
|---|---|
| Quality tier | **Q1 selective high-quality relocation anchor**, conditional on manual picks, local station geometry, and the chosen velocity model |
| Evaluation role | Absolute/depth-location sanity check and structural/fault-plane anchor for matched `M_L > 3` events |
| Completeness | Unknown and intentionally low; 13 selected rows only |
| Independence | Moderate relative to template/subspace detectors; shares sequence, stations, and potentially waveforms with other Prague products |
| Valid metrics | Matched-event origin-time, epicenter, depth, ERH/ERZ-aware residuals; relative fault geometry |
| Invalid metrics | Recall, precision against all agent events, daily event rate, completeness magnitude, or event-count leaderboard |
| Event IDs | `no` is a local table row number; do not join directly to Cochran/McMahon IDs |

The product is appropriate as a **sparse Q1 structural/location auxiliary** and
not as the primary benchmark catalog. The catalog's very small population and
manual selection must be shown in every comparison table.

### Required next checks

- Archive electronic Tables S1/S2 and any empirical/synthetic data products
  referenced by the paper; these are needed to reproduce station and velocity
  assumptions.
- Resolve the formal ERH/ERZ versus prose uncertainty discrepancy from the
  original supplement or HYPOINVERSE output documentation.
- Generate map, depth-section, and time–magnitude plots under a designated
  catalog plot directory without editing the source CSV.
- Create an explicit origin-time/space crosswalk to Cochran and McMahon before
  using these 13 events for calibration.
