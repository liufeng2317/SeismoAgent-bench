# McMahon et al. (2017) — paper reading and catalog-construction audit

## Identity and evidence status

| Field | Extracted information | Evidence / status |
|---|---|---|
| Authors | Nicole D. McMahon, Richard C. Aster, William L. Yeck, Daniel E. McNamara, Harley M. Benz | PDF title block |
| Citation | “Spatiotemporal evolution of the 2011 Prague, Oklahoma, aftershock sequence revealed using subspace detection and relocation” | PDF title block |
| Journal | *Geophysical Research Letters*, 44, 7149–7158 | PDF citation block |
| DOI | [10.1002/2017GL072944](https://doi.org/10.1002/2017GL072944) | DOI / landing page |
| Publication | Received 2017-02-03; accepted 2017-06-29; online 2017-07-05; published 2017-07-18 | PDF citation block |
| Article type | Research letter with a new subspace-detection and Bayesloc relocation catalog | Sections 2–4 |
| Associated release | USGS ScienceBase catalog, DOI [10.5066/F7FJ2FNT](https://doi.org/10.5066/F7FJ2FNT) | Article acknowledgements; local README |
| Supplement status | Not locally staged; Table S1/S2 and Data Sets S1/S2 are still needed for exact detector/station parameters | Manifest gap |

The paper is a genuine catalog-construction paper. It is methodologically
independent of the later Cochran template-matched catalog in its detector and
locator family, but both products use overlapping Prague waveform archives and
related starting catalogs. They must remain separate reference layers.

## Scientific scope and observations

- Sequence: induced/triggered 2011 Prague, Oklahoma sequence; Mw 4.8
  foreshock, Mw 5.7 mainshock on 2011-11-06, and Mw 4.8 largest aftershock.
- Study waveform interval: 2011-11-04 through 2011-12-05. The last temporary
  stations became fully operational on 2011-11-11.
- Network: 21 temporary stations (18 Oklahoma RAMP ZQ and 3 USGS GS), plus 9
  EarthScope Transportable Array TA stations and 1 Oklahoma Seismic Network OK
  station, giving 31 stations used in the subspace workflow. Temporary stations
  were approximately 0.7–14.7 km from the mainshock epicentre.
- Initial catalog: 998 events in the month after the foreshock, manually
  identified, located, and reviewed, based on the McNamara et al. initial
  catalog.
- Scientific target: lower the magnitude of completeness and resolve the
  spatiotemporal geometry of the Meeker–Prague/Wilzetta fault system, including
  shallow Arbuckle Group seismicity.

## Catalog-construction workflow

```text
998 manually reviewed initial events
    → S-phase multichannel subspace detectors
    → station-specific continuous correlation (4 Nov–5 Dec, or station deployment start)
    → S-arrival-time estimation
    → arrival-time association (≥5 stations for the retained located set)
    → supplement large events with original P/S arrivals
    → Bayesloc hypocenter estimation using McNamara velocity model
    → uncertainty filtering and relocation/final catalog merge
    → relative magnitudes and completeness/temporal analyses
```

### Detector construction and detection

- Detectors were built exclusively for S phases because they were relatively
  simple and high amplitude in this deployment.
- Each station used between 11 and 91 multichannel templates to represent 90%
  of observed waveform energy. A total of 14,150 events identified on the 31
  stations was reduced to 1,116 subspace templates (92% fewer templates).
- Continuous data were cross-correlated from each temporary station's operation
  start, and from 2011-11-04 for permanent stations, through 2011-12-05.
- The paper says the detection threshold was deliberately high but does not
  expose the exact numerical threshold in the main text. The missing Table S1 /
  supporting files are required before reproducing this parameter exactly.
- Subspace detectors are less sensitive to Mw > 3 events because large-source
  durations differ from the small-event templates. The original catalog's P/S
  arrivals were therefore merged back into the enhanced product.

### Association, location, and magnitude

- S detections were associated with an arrival-time associator. The article
  reports 191,100 S arrivals associated into 20,788 events observed at five or
  more stations.
- Bayesloc was used for hypocenter estimation with the McNamara et al. (2015)
  velocity model.
- Detected-event magnitudes were estimated relative to the nearest original
  catalog neighbor at each station and averaged across stations. The release
  does not provide a clearly named magnitude type in its headerless E records;
  retain `magnitude_type = unresolved` until the supplement/release metadata is
  checked.
- The article reports 21,786 located events, of which 5,176 had estimated
  epicentral uncertainty below 0.5 km and depth uncertainty below 1 km. After
  excluding 184 original-catalog events that failed the final uncertainty
  constraints, the paper reports a final 5,262-event catalog.
- The local USGS release has 5,446 E records because it retains the broader
  released event/phase product. Do not replace the paper's 5,262 count with the
  release count without recording this lineage difference.

## Article and local-release audit

| Aspect | Article-reported value | Local release / interpretation |
|---|---|---|
| Event product | 5,262 final paper catalog events | 5,446 E records; 82,537 P phase rows |
| Detection/association | 577,040 S arrivals; 191,100 arrivals in 20,788 events at ≥5 stations | Every released E ID has at least one associated P row; local release retains the broader product |
| Quality filter | Epicentral uncertainty <0.5 km and depth uncertainty <1 km | XML metadata repeats the same completeness/accuracy constraints |
| Completeness | Mc ≈ 0.8; b ≈ 0.52 for the complete catalog | Magnitude field is numeric but type/calibration remains unresolved |
| Network | 31 stations, with changing deployment availability | Full release contains station/network codes; station-day availability must be preserved |
| Independence | Subspace + Bayesloc, not template matching + GrowClust | Shared waveform/archive and initial-catalog lineage still reduce independence |

## Benchmark interpretation

| Dimension | Decision |
|---|---|
| Quality tier | **Q2** enhanced detection/relocation reference; the uncertainty-filtered subset is a metric-specific **Q1 location/QC anchor** |
| Primary use | Compare event support, S-phase-only detection, association, absolute hypocenter quality, and network-transition robustness |
| Secondary use | Cross-check Cochran's template-matched population without merging event IDs |
| Not suitable for | Universal completeness truth, independent magnitude truth, or a single absolute reference across all time/network conditions |
| Main bias | S-phase-only detectors can miss large events; original P/S events are merged back; station availability evolves until 11 November |

## Prague v1 benchmark window

The case-level canonical interval is the half-open UTC window
`2011-11-11T00:00:00Z ≤ origin_time < 2011-11-19T00:00:00Z`, chosen after the
temporary network became fully operational. A local audit of the E records gives:

| Field | Value |
|---|---:|
| McMahon events in time-only window | 2,384 |
| Event time range inside window | 2011-11-11 00:03:45.251 to 2011-11-18 23:53:13.538 UTC |
| Latitude | 35.376253–35.566070°N |
| Longitude | −96.908400–−96.570300°E |
| Depth | 0.5086–10.2712 km |
| Magnitude | −2.133371–4.0; type unresolved |
| Referenced phase rows by event ID | 37,171 |

These are local-file audit values, not new article claims. The McMahon spatial
extent is broader than the Cochran time-window envelope; applying a common
spatial mask is a separate case-level operation.

## Local provenance and open actions

- Paper PDF: `data/2011_prague_oklahoma/references/MCMAHON2017_GL072944/paper/MCMAHON2017_GL072944__paper.pdf`
- MinerU text: `data/2011_prague_oklahoma/references/MCMAHON2017_GL072944/paper/mineru/MCMAHON2017_GL072944__paper/full.md`
- Catalog README: `data/2011_prague_oklahoma/catalogs/MCMAHON2017_GL072944/README.md`
- Catalog release: `data/2011_prague_oklahoma/catalogs/MCMAHON2017_GL072944/raw/MCMAHON2017_GL072944__catalog_subspace_5446events.txt`
- Metadata: `data/2011_prague_oklahoma/catalogs/MCMAHON2017_GL072944/raw/MCMAHON2017_GL072944__metadata.xml`
- Required next acquisition: McMahon Supporting Information S1, Table S1/S2, and Data Sets S1/S2 if exact detector thresholds, station/sample-rate metadata, or per-event uncertainty fields are needed.
