# Liu et al. (2020) — paper reading and catalog-construction audit

## Identity and evidence status

| Field | Extracted information | Evidence / status |
|---|---|---|
| Authors | Min Liu, Miao Zhang, Weiqiang Zhu, William L. Ellsworth, Hongyi Li | Article title block |
| Title | *Rapid Characterization of the July 2019 Ridgecrest, California, Earthquake Sequence From Raw Seismic Data Using Machine-Learning Phase Picker* | Article title |
| Journal / DOI | *Geophysical Research Letters* 47, e2019GL086189; DOI [10.1029/2019GL086189](https://doi.org/10.1029/2019GL086189) | Article citation block |
| Article type | Research article that constructs REAL, VELEST and hypoDD catalogs from continuous waveforms without using the routine catalog as an event prior | Abstract; Section 2 |
| Associated materials | Supporting Information S1, Table S1, Movies S1–S2; local SI DOCX and Table S1 are present | Article front matter; local files |
| Parse status | MinerU paper parse plus direct XML text extraction of the local SI DOCX | Local files |

## Scientific scope and observation conditions

- Sequence: Ridgecrest Mw 6.4 and Mw 7.1 sequence; the analysis covers 4–9
  July 2019 (first six days; article abstract and Section 2).
- Initial routine comparison: SCSN reported 1,708 events before the Mw 7.1 and
  5,717 aftershocks through 9 July, 7,425 total (MinerU line 56).
- Waveform network: 41 permanent and four temporary stations within 120 km of
  the Mw 7.1 mainshock (MinerU line 56; SI Fig. S1). The article does not give
  a single fixed channel count or sample rate; preserve the station geometry and
  changing availability rather than inventing a volume.
- Initial velocity model: Coso regional 1-D model from travel-time inversion and
  well logs (MinerU line 56).

## Catalog-construction workflow

```text
continuous IRIS/SCEDC waveforms
    → PhaseNet P/S probability picks (threshold 0.5)
    → REAL association and grid-search initial locations
    → VELEST absolute relocation + station corrections
    → hypoDD relative relocation with filtered high-probability picks
    → Table S1 final hypoDD event catalog

REAL events + horizontal waveforms/response
    → local magnitude (Hutton–Boore amplitude relation; already discussed for REAL)
```

### Picking and association

- PhaseNet was applied to vertical or three-component waveforms; the paper uses
  a 0.5 pick-probability threshold (MinerU line 58; SI Fig. S2).
- REAL searches a 0.4° horizontal region with 0.02° grid spacing and depths 0–20
  km at 2-km spacing, using stations within 100 km. Events require at least
  five P picks and 13 total P+S picks (MinerU line 58).
- The initial REAL catalog contains 16,563 events and 195,869 P plus 204,349 S
  arrival times (MinerU line 60). These are intermediate article populations,
  not the local Table S1 row count.

### Absolute and relative location

- VELEST refines the full REAL catalog using 1,633 events with at least 30 high-
  quality picks (probability >0.8) to update the velocity model and station
  corrections. Events are retained when station gap <200° and travel-time residual
  <0.6 s, yielding 16,112 relocated events (MinerU line 60).
- hypoDD then uses stations within 80 km, picks close to the main P/S travel-time
  trends (SI Text S2), and phase probabilities >0.7 as weights. The paper reports
  15,445 final hypoDD events (MinerU lines 60, 107).
- The paper explicitly says the workflow is independent of the routine catalog
  as an event prior, although the routine catalog is used for comparison and the
  SCSN/SCEDC waveform lineage is shared.

### Magnitude and known omissions

- Local magnitudes are estimated from deconvolved horizontal amplitudes and a
  Wood–Anderson response using Hutton–Boore attenuation (SI Text S1).
- SI Text S3 documents why 884 routine events are missed by the strict workflow:
  insufficient picks, depth outside 20 km, close events collapsed into a five-
  second window, coda burial, or large station gap/residual. This is a useful
  completeness label, not evidence of false events in the final catalog.
- The authors caution that magnitudes differ from SCSN, especially above ML 4,
  because of magnitude formulas, station selection (<100 km), and coda effects
  (SI Text S1).

## Reported populations and local alignment

| Processing stage | Article value | Local evidence |
|---|---:|---|
| SCSN routine comparison | 7,425 in Section 2 (1,708 + 5,717); the Conclusion says 7,743 | Article Sections 2 and 5; internal article discrepancy retained |
| REAL associated catalog | 16,563 | Article Section 2 |
| VELEST relocated catalog | 16,112 | Article Section 2 |
| hypoDD final catalog | 15,445 | Table S1 has 15,445 rows |
| Associated P/S arrivals | 195,869 / 204,349 | Article Section 2 |

The local Table S1 is therefore the final hypoDD event product, not the larger
REAL or VELEST intermediate catalog. It has no explicit event identifier or
uncertainty columns; row identity is the complete origin-time/coordinate record.
The article itself gives two routine-catalog comparison counts (7,425 in Section 2
versus 7,743 in the Conclusion); neither number should be substituted for the
15,445-row Table S1 product.

## Benchmark interpretation

| Dimension | Decision |
|---|---|
| Quality tier | **Q2** independent automatic catalog; metric-specific Q1-like relative geometry for well-constrained hypoDD events, but no per-event uncertainty in Table S1 |
| Role | Independent-method secondary for raw-waveform detection, association and end-to-end catalog construction |
| Suitable metrics | Detection/association recall, event-time and fault-geometry comparison, method independence, magnitude bias analysis |
| Unsuitable metric | Direct magnitude ranking against Shelly/Ross without harmonizing ML/Mw scales; universal completeness under coda saturation |
| Independence | Higher than Shelly/Ross at the algorithm level because the event prior is not the routine catalog; waveform archive and SCSN comparison remain shared |
| Canonical local input | `data/catalogs/LIU2020_GL086189/LIU2020_GL086189__catalog_tableS1.txt` |

## Candidate Ridgecrest benchmark window (not frozen)

Using the case-wide rule
`2019-07-04T00:00:00Z <= origin_time < 2019-07-07T00:00:00Z`, latitude
35.45–36.05°N, longitude −117.90–−117.20°, depth 0–20 km:

| Field | Time-only selection | Common mask |
|---|---:|---:|
| Rows | 6,329 | 6,242 |
| Time range | 2019-07-04 00:56:37.520–2019-07-06 23:59:30.040 UTC | same |
| Latitude | 35.330306–36.271517°N | 35.503996–36.047262°N |
| Longitude | −117.979354–−117.234489°E | −117.883626–−117.275936°E |
| Depth | 0.001–14.126 km | 0.002–14.126 km |
| Magnitude | −0.20–5.50 | −0.20–5.50 |

## Local provenance and next actions

- Paper: `LIU2020_GL086189__paper.pdf`
- Parsed paper: `LIU2020_GL086189__paper__mineru.md`
- SI: `../../supplement/Liu2020_Ridgecrest_SI.docx`
- Table S1: `../../../../data/catalogs/LIU2020_GL086189/LIU2020_GL086189__catalog_tableS1.txt`
- Open action: preserve/locate the separate Movies and any station inventory if
  waveform-volume reproduction is needed; the local SI DOCX contains figures and
  text but does not provide a machine-readable station-day manifest.

## Coso initial-model table supplied by user

The user supplied an image identified as Feng & Lees (1998), Table 1, “Coso regional velocity model”. Its 12 rows of P-depth, P velocity and S velocity have been transcribed into `data/models/velocity_models.json`, entry `liu_coso_initial` (case-relative path). Both velocities are explicitly tabulated; S velocity is not derived from a fixed ratio. The image does not establish depth datum or interpolation conventions. The image remains in the conversation, not an archived local source file. Liu §2 cites this initial model, but the actual input-file identity remains unverified. This table does not provide the model or station corrections subsequently inverted by VELEST.

## Supporting-information cross-check from user-supplied text

The supplied Texts S1–S3 and figure captions agree with the corresponding local SI extraction on the processing parameters below; they are merged here without duplicating the full SI or author contact details. The supplied text contains captions, not the figure images or numerical model files.

| Stage / source | Verified detail | Interpretation limit |
|---|---|---|
| Magnitude, Text S1 | Horizontal maximum amplitudes after instrument-response removal and theoretical Wood–Anderson convolution; Hutton–Boore attenuation; station epicentral distance <100 km | REAL magnitudes are already discussed; magnitude estimation is not proven to occur only after hypoDD |
| Magnitude window, Text S1 | Start at P−0.5 s; duration 2×predicted(S−P) | End is start plus duration; S–P predictions require a model. Station aggregation and response settings remain unspecified |
| hypoDD picks, Text S2 | Epicentral distance <80 km; reject P/S deviations >0.8/>1.2 s from the main travel-time trends | Trends are not explicitly defined as theoretical-model residuals. Probability >0.7 comes from the main paper, not this SI paragraph |
| REAL omissions, Text S3 | ≥5 P and ≥13 total picks; limited depth search; keep most reliable event within 5 s | 5 s is a competing-detection window, not an event-matching tolerance |
| VELEST QC, Text S3 | Station gap <200° and travel-time residual <0.6 s | SI does not define the residual aggregation formula; do not automatically call it RMS |

SI reports 884 missed routine events (about 12%): insufficient picks, out-of-range depth, close events, coda burial and poor geometry/residuals. It identifies 359 routine events with fewer than 13 picks and 113 missed routine events deeper than 20 km; these are not demonstrated to be disjoint partitions of the 884, so they must not be summed into an exhaustive attribution. Magnitude differences above 4 are attributed to possible formula/type differences, restricted station distances and coda effects, not a universal correction to apply to our catalogs.

No VELEST-updated velocity table or station corrections occur in the supplied text. Figures S5/S16 concern travel-time trends; the 5.74 km/s line in Fig. S17 is illustrative. The separate `Ridgecrest2019catalog.txt` is the final event catalog, not a velocity table. Coso initial-model values remain those independently transcribed from the Feng & Lees table supplied earlier.
