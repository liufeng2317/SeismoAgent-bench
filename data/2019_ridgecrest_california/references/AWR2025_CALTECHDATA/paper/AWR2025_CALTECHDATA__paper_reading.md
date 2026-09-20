# Atterholt, Wilding & Ross (2025) — paper reading and catalog-construction audit

## Identity and evidence status

| Field | Extracted information | Evidence / status |
|---|---|---|
| Authors | James Atterholt, John D. Wilding, Zachary E. Ross | Article title block |
| Title | *The evolution of fault orientation in the 2019 Ridgecrest earthquake sequence with a new long-term catalogue of seismicity and moment tensors* | Article title |
| Journal / DOI | *Geophysical Journal International* 240, 1579–1592; DOI [10.1093/gji/ggaf001](https://doi.org/10.1093/gji/ggaf001) | Article citation |
| Catalog release | Article supplementary “AWR Catalogs.zip”; current local Version 2 provenance is CaltechDATA DOI [10.22002/5af05-cah73](https://doi.org/10.22002/5af05-cah73). The article data-availability text also names DOI [10.22002/f40da-hww21](https://doi.org/10.22002/f40da-hww21); preserve both rather than assuming they are byte-identical. | MinerU lines 210–218; local README |
| Article type | Genuine catalog-construction and stress/fault-orientation research article, not merely a review | Summary and construction section |
| Parse status | MinerU parse is complete; the local release is audited separately below | Local files |

## Scientific scope and observation conditions

- Sequence: Ridgecrest 2019, with a catalog spanning April 2019–May 2023 and
  therefore covering the foreshock, mainshock, aftershock and multi-year
  recovery periods (article summary and local release README).
- Continuous data: 66 three-component broadband stations from multiple networks,
  selected within a broad 200 × 200 km region; April 2019–May 2023. Vertical and
  north/horizontal components were used for detection, with a >1 Hz high-pass
  filter. The neural spatial graph used 18 stations (MinerU line 33).
- The long-term product is not directly equivalent to Shelly/Ross/Liu's compact
  July window: it optimizes multi-year coverage and includes changing network
  availability.

## Catalog-construction workflow

```text
continuous multi-network waveforms
    → PhaseNO P/S arrival detection
    → GaMMA association (≥15 picks, ≤2 s phase error, 10-s subwindows)
    → amplitude-based magnitude estimates
    → HypoSVI absolute locations + eight station-term iterations
    → waveform cross-correlation differential times
    → GrowClust relative relocation (CC ≥0.65; ≥6 differential observations/pair)
    → retained hypocenter catalog
    → Bayesian P-amplitude moment-tensor inversion
    → strike/dip/rake uncertainty and quality filtering
    → hypocenter and moment-tensor CSV products
```

### Hypocenter catalog

- GaMMA association yields 326,345 events (MinerU line 33).
- HypoSVI uses a smoothed Hadley–Kanamori Southern California velocity model
  and source-specific station terms; 90% of retained non-relocated events have
  horizontal uncertainty <700 m and vertical uncertainty <1 km (MinerU line 35).
- GrowClust uses a minimum cross-correlation coefficient of 0.65 and at least
  six differential-time observations per event pair. The article reports
  214,467 retained relocated events (MinerU line 35); the local Version 2 CSV
  contains 222,864 rows, indicating a release/version difference that must be
  preserved rather than silently reconciled.

### Moment-tensor catalog

- Automated signed P-wave amplitudes provide 226,615 measurements for 45,684
  events. A minimum of 15 measured amplitudes gives 7,645 candidate inversions;
  strike/dip/rake standard deviations <7.5° retain 4,892 solutions in the
  article (MinerU line 44).
- The local Version 2 moment-tensor CSV has 4,890 rows; every local row has
  `n_picks_used >= 15` and all three reported angular standard deviations <7.5°.
  The two-row discrepancy is documented as a release-version difference.

## Reported products and limitations

| Product/stage | Article value | Local Version 2 audit |
|---|---:|---:|
| GaMMA associated events | 326,345 | Not separately released |
| Article final relocated hypocenters | 214,467 | Local hypocenter CSV: 222,864 rows |
| P-amplitude measurements | 226,615 / 45,684 events | Not separately released |
| Candidate moment-tensor inversions | 7,645 | Not separately released |
| Article accepted moment tensors | 4,892 | Local CSV: 4,890 rows |
| Hypocenter span | April 2019–May 2023 | 2019-04-04–2023-05-01 UTC |
| Moment-tensor span | Long-term sequence | 2019-04-07–2023-04-21 UTC |

The article's products are high-density and methodologically sophisticated, but
not universal truth catalogs. Detection, station coverage, and uncertainty vary
through the multi-year interval; the workflow also overlaps conceptually with
modern Agent pipelines (PhaseNO/GaMMA/HypoSVI/GrowClust).

## Benchmark interpretation

| Dimension | Decision |
|---|---|
| Quality tier | **Q2** long-term methodological auxiliary overall; metric-specific **Q1** for accepted relative geometry and moment-tensor uncertainty fields |
| Role | Long-duration relocation/focal-mechanism cross-check and stress-orientation auxiliary; not the Phase-I primary short-window target |
| Suitable metrics | Long-term event-rate evolution, relative geometry, moment-tensor uncertainty/calibration, method comparison |
| Unsuitable metric | Direct event-count ranking against Shelly/Liu/Ross without harmonizing release version, time span, detection threshold and magnitude scale |
| Independence | Medium–Low for algorithmic benchmarking because PhaseNO/GaMMA/HypoSVI/GrowClust overlap with likely Agent components; high value as a documented research reference |
| Network condition | 66 broadband 3C stations selected in a broad region, with changing availability from 2019–2023; exact station-day inventory remains to be extracted from SI Fig. S1 |

## Frozen Ridgecrest benchmark window

Applying the case-wide time/space/depth rule to the local Version 2 products
(`2019-07-04T00:00:00Z <= time < 2019-07-07T00:00:00Z`, 35.45–36.05°N,
−117.90–−117.20°, depth 0–20 km):

| Product | Time-only rows | Common-mask rows | Common-mask ranges |
|---|---:|---:|---|
| Hypocenters | 5,842 | 5,737 | lat 35.505180–36.050000; lon −117.877930–−117.267740; depth 0.692–14.732 km; γ-mag 0.056–4.585 |
| Moment tensors | 258 | 254 | lat 35.548390–36.038930; lon −117.847810–−117.366030; depth 0.921–12.866 km; magnitude 1.874–4.115 |

The hypocenter catalog has 78 negative-depth rows over the full release and two
duplicate origin times; IDs are unique. The local moment-tensor catalog has 4,890
unique IDs and no duplicate times. `magnitude_gamma` is the release's gamma-based
amplitude magnitude and must not be relabeled as ML or Mw.

## Local provenance and next actions

- Paper: `AWR2025_CALTECHDATA__paper.pdf`
- Parsed paper: `AWR2025_CALTECHDATA__paper__mineru.md`
- Local catalogs: `../../../../catalogs/AWR2025_CALTECHDATA/`
- Provenance: [CaltechDATA 10.22002/5af05-cah73](https://doi.org/10.22002/5af05-cah73),
  article release DOI [10.22002/f40da-hww21](https://doi.org/10.22002/f40da-hww21)
- Open actions: archive the exact article supplementary ZIP or a release manifest,
  and extract station-day metadata from SI Fig. S1 before freezing waveform
  volume or claiming byte-level reproduction of the 214,467/4,892 article counts.
