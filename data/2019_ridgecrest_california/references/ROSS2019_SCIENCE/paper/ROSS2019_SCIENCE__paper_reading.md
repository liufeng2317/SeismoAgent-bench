# Ross et al. (2019) — paper reading and QTM catalog audit

## Identity and evidence status

| Field | Extracted information | Evidence / status |
|---|---|---|
| Authors | Zachary E. Ross et al. | Article title block |
| Title | *Hierarchical interlocked orthogonal faulting in the 2019 Ridgecrest earthquake sequence* | Science article |
| Journal / DOI | *Science* 366(6463), 346–351; DOI [10.1126/science.aaz0109](https://doi.org/10.1126/science.aaz0109) | Article citation |
| Article type | Research article that constructs/uses a high-resolution template-matched and relocated seismicity catalog to resolve fault geometry, alongside geodetic and rupture analyses | Main text and Data availability |
| Catalog release | Official SCEDC QTM Ridgecrest catalog: [SCEDC QTM page](https://scedc.caltech.edu/data/qtm-ridgecrest.html) | Official column definition and archive link |
| Supplement | Science DC1 (Materials and Methods, Figs. S1–S19, Tables S1–S4) is referenced by the paper but is not currently local; detailed reproduction parameters therefore remain incomplete | Article lines 129, 177–179 |

## Scientific scope and observation conditions

- Sequence: Mw 6.4 foreshock on 2019-07-04 followed by Mw 7.1 mainshock
  about 34 h later. The article discusses the first 21 days, during which more
  than 111,000 events with M>0.5 occurred (main text).
- Local QTM archive span: 2019-07-04 03:14:14.128 through 2019-07-25
  14:59:51.550 UTC; it contains 111,918 rows including events that did not
  achieve a multi-event GrowClust relocation.
- Network: Southern California Seismic Network (SCSN; CI) and SCEDC waveform/
  parametric archive. The main article does not provide a single station count
  in the local parse; waveform lineage is shared with Shelly and the operational
  baseline.
- Scientific target: multiscale orthogonal faulting, rupture geometry and
  relation to surface deformation. It is especially strong for structural
  comparison, not for a universal absolute hypocenter truth set.

## Catalog-construction interpretation

The article states that its comprehensive relocated seismicity catalog was
constructed with template matching and had nominal relative resolution of about
100 m horizontally and 350 m vertically (main text, paragraph before Fig. 2).
The detailed Materials and Methods are in the missing Science DC1; therefore the
local evidence supports the following conservative chain:

```text
SCSN/SCEDC routine event waveforms
    → template matching / hidden-event detection
    → differential-time measurement
    → clustered relative relocation (GrowClust-format release)
    → QTM catalog with initial and relocated locations, QC and error fields
```

Do not infer unrecorded detection thresholds or station numbers from the main
article alone. The SCEDC release itself is authoritative for the event-level
field meanings and relocation indicator.

## Reported products and limitations

- The main article reports more than 111,000 M>0.5 events over the first 21 days;
  the local archive has 111,918 rows over 4–25 July, consistent with that scope
  but not a claim that every row satisfies M>0.5.
- The catalog includes both initial (`latC`, `lonC`, `depC`) and relocated
  (`latR`, `lonR`, `depR`) locations. `nbranch > 1` marks a successfully
  relocated solution; `nbranch = 1` rows retain only an initial/operational
  location (SCEDC QTM page).
- The Science paper warns that the Mw 7.1 mainshock depth is poorly constrained
  in QTM and recommends the SCSN hypocenter for that event.
- The article's structural conclusions are well supported by the relocated
  subset, but event-level absolute-location and completeness claims require the
  initial/relocated distinction and SCSN comparison.

## Benchmark interpretation

| Dimension | Decision |
|---|---|
| Quality tier | **Q1** for relative fault geometry and relocation diagnostics; **Q2–Q3** for absolute locations of unrelocated rows and the Mw 7.1 mainshock |
| Role | Secondary structural/relocation reference against Shelly and Liu; not the sole primary event target |
| Suitable metrics | Relative geometry, cluster membership, differential-time support, location-error calibration, fault-network reconstruction |
| Unsuitable metric | Treating all 111,918 rows as equally relocated or using QTM Mw 7.1 depth as absolute truth |
| Independence | Medium: shares SCSN/SCEDC waveform lineage with Shelly and routine baseline, but uses a distinct template/cluster relocation product |
| Supplement status | Missing locally; acquire DC1 before exact method reproduction |

## Local provenance and next actions

- Paper: `ROSS2019_SCIENCE__paper.pdf`
- Parsed paper: `ROSS2019_SCIENCE__paper__mineru.md`
- Official archive: `../../../../catalogs/ROSS2019_SCIENCE/raw/ROSS2019_SCIENCE__catalog_qtm.tar.gz`
- Case synthesis: `../../analysis/RIDGE2019_analysis.md`
- Required follow-up: download and archive Science DC1, then extract exact
  template, differential-time and relocation parameters from its Materials and
  Methods. Keep the SCEDC QTM page as the authoritative schema source.
