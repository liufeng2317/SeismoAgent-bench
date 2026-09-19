# MCMAHON2017_GL072944 — catalog summary and reproducible audit

## Provenance

- Source article: McMahon et al. (2017), DOI [10.1002/2017GL072944](https://doi.org/10.1002/2017GL072944)
- Official release: USGS ScienceBase DOI [10.5066/F7FJ2FNT](https://doi.org/10.5066/F7FJ2FNT)
- Core file: `raw/MCMAHON2017_GL072944__catalog_subspace_5446events.txt`
- Metadata: `raw/MCMAHON2017_GL072944__metadata.xml`
- Native format: event/phase text file with `E` and `P` records
- SHA-256: `f9259a512b883f1dcd3cb368ccc2753e1f8bf0ec8665d2b34ef74858874509a`; do not modify the raw file

## Native record structure

The local audit finds:

- **5,446 `E` records**, each with 12 whitespace-separated tokens:

  ```text
  E event_id year month day hour minute second latitude longitude depth magnitude
  ```

- **82,537 `P` records**, each with 10 whitespace-separated tokens in the local
  file. The XML metadata describes a full year/month/day/hour/minute/second
  phase timestamp, but the distributed rows visibly contain only five temporal
  values after the phase code (`year month day minute second`). This discrepancy
  must be resolved from the official release documentation before using phase
  timestamps as an independent time axis.
- 5,446 unique event IDs; every event has at least five phase rows in the local
  release (minimum 5, maximum 72, mean about 15.2 phase rows/event).
- The full release contains 108 unique network/station combinations. The paper's
  detection workflow refers to 31 stations; the broader release includes phase
  observations from additional network codes and should not be reduced without
  documenting the station selection.

## Local event audit

| Field | Value |
|---|---|
| E rows / unique IDs | 5,446 / 5,446 |
| Event time range | 2011-11-05 07:12:44.310 to 2011-12-05 22:40:33.9144 UTC |
| Latitude | 35.376253–35.633400°N |
| Longitude | −96.934000–−96.544800°E |
| Depth | 0.4–14.4 km |
| Magnitude | −2.176413–5.6; type/calibration unresolved |
| Phase rows | 82,537 |
| Exact duplicate E rows | Not yet stored as a machine audit; compute before release |

The metadata declares a nominal coverage of 2011-11-04 to 2011-12-05 and a
spatial bounding box of west −96.889958, east −96.563892, south 35.376253,
north 35.589586. The local event extrema should be retained separately because
some rows extend beyond the metadata bounding box and the first local event is
on 2011-11-05.

## Construction and quality

```text
Initial McNamara catalog
  → 998 manually reviewed events for detector construction
  → station-specific S-phase multichannel subspace templates
  → continuous correlation on 31 stations
  → S-arrival association
  → Bayesloc with McNamara velocity model
  → uncertainty filtering / merge with original large-event P/S arrivals
  → USGS E/P release
```

The article reports 577,040 detected S arrivals, 191,100 arrivals associated
into 20,788 events observed at five or more stations, and 21,786 located events.
The paper's final uncertainty-filtered count is 5,262; the distributed 5,446-E
release is a broader product that includes records excluded from that final
paper count. Keep both numbers in manifests.

## Frozen Prague window

The canonical case rule is
`2011-11-11T00:00:00Z ≤ origin_time < 2011-11-19T00:00:00Z`.
Applying only this rule to local `E` origin times yields:

| Field | Value |
|---|---:|
| Events | 2,384 |
| Latitude | 35.376253–35.566070°N |
| Longitude | −96.908400–−96.570300°E |
| Depth | 0.5086–10.2712 km |
| Magnitude | −2.133371–4.0; type unresolved |
| Phase rows referenced by selected event IDs | 37,171 |

Do not apply Cochran's tighter spatial/depth envelope to McMahon until the
case-level common-mask decision is explicitly recorded. The 2,384 count is a
McMahon-local time-only audit, not the expected count after cross-catalog
matching.

## Benchmark role

- **Q2 primary/secondary enhanced-detection reference:** independent subspace
  detector and Bayesloc workflow relative to Cochran's template/GrowClust path.
- **Metric-specific Q1 location anchor:** use only for records satisfying the
  published uncertainty criteria and with the 5,262-versus-5,446 release
  lineage made explicit.
- **Not ground truth:** shared waveform archives, an inherited initial catalog,
  changing station availability, and S-phase-only detection create dependence
  and selection bias.

## Required follow-up

1. Download and archive McMahon Supporting Information S1, Table S1/S2, and Data
   Sets S1/S2.
2. Verify the P-record timestamp schema against the official release metadata.
3. Record SHA-256 and exact release version.
4. Derive row-level uncertainty/quality fields if present in the official
   machine-readable release; the current E file does not expose them.
5. Generate catalog map, depth section, daily count, magnitude distribution, and
   phase-count plots under the catalog product directory without modifying the
   raw file.
