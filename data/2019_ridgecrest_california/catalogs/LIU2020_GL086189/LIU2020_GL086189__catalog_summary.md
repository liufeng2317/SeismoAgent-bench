# LIU2020_GL086189 — catalog summary and reproducible audit

## Provenance and schema

- Source article: Liu et al. (2020), DOI [10.1029/2019GL086189](https://doi.org/10.1029/2019GL086189).
- Article product: Table S1, the final hypoDD catalog from the PhaseNet → REAL →
  VELEST → hypoDD workflow.
- Local file: `LIU2020_GL086189__catalog_tableS1.txt`.
- Native header: `yr mo day hr min sec lat lon dep mag`.
- There is no explicit event ID, station count, phase count or uncertainty
  column. Treat each complete row as one event and retain the origin-time and
  coordinate tuple as the reproducibility key.

| File | Bytes | Data rows | Duplicate origin times | SHA-256 |
|---|---:|---:|---:|---|
| `LIU2020_GL086189__catalog_tableS1.txt` | 1,003,989 | 15,445 | 0 | `8582363962b168c8034e339a8859407fb2ed63fc83eb4e01ac9d88546583cd88` |

## Full catalog audit

| Field | Range / value |
|---|---|
| Origin time | 2019-07-04 00:56:37.520–2019-07-09 23:59:40.560 UTC |
| Latitude | 35.330306–36.271517°N |
| Longitude | −117.979354–−117.234489°E |
| Depth | 0.001–14.126 km |
| Magnitude | −0.20–5.50 (local magnitude scale from SI Text S1) |
| Negative magnitudes | 2 rows |
| Missing/non-numeric fields | None detected |
| Event IDs | Not supplied; 15,445 unique origin times |

The file is a final hypoDD event table, not a phase-pick table. The article's
16,563-event REAL and 16,112-event VELEST populations are intermediate and are
not present as separate local files.

## Frozen benchmark-window audit

Rule: half-open UTC time interval 2019-07-04 through 2019-07-07, common latitude
35.45–36.05°N, longitude −117.90–−117.20°, depth 0–20 km.

| Field | Time-only | Common mask |
|---|---:|---:|
| Rows | 6,329 | 6,242 |
| Time range | 2019-07-04 00:56:37.520–2019-07-06 23:59:30.040 UTC | same |
| Latitude | 35.330306–36.271517°N | 35.503996–36.047262°N |
| Longitude | −117.979354–−117.234489°E | −117.883626–−117.275936°E |
| Depth | 0.001–14.126 km | 0.002–14.126 km |
| Magnitude | −0.20–5.50 | −0.20–5.50 |

## Quality and comparison notes

- **Tier:** Q2 independent-method research catalog; use as a strong
  method-specific secondary, not a universal truth set.
- The strict minimum of five P and 13 total picks, <200° station gap and <0.6 s
  VELEST residual, and hypoDD pick filtering improve location quality but create
  documented omissions (SI Text S3).
- Magnitudes are not directly interchangeable with SCSN, Shelly or Ross without
  scale harmonization; the authors document systematic differences above ML 4.
- The source file is small enough to version, but the SI DOCX and any future
  normalized derivative should retain the original checksum and row order.

## Local outputs

- Paper reading: `../../references/LIU2020_GL086189/paper/LIU2020_GL086189__paper_reading.md`
- SI: `../../references/LIU2020_GL086189/supplement/Liu2020_Ridgecrest_SI.docx`
- Case synthesis: `../../analysis/RIDGE2019_analysis.md`
