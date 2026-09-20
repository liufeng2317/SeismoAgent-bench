# Pang et al. (2019) - paper reading and catalog-construction audit

## Identity and evidence status

| Field | Extracted information | Evidence / status |
|---|---|---|
| Authors | Guanning Pang, Keith D. Koper, J. Mark Hale, Relu Burlacu, Jamie Farrell, and Robert B. Smith | PDF title block |
| Title | The 2017-2018 Maple Creek Earthquake Sequence in Yellowstone National Park, USA | PDF title block |
| Journal | Geophysical Research Letters, 46, 4653-4663 (2019) | PDF citation block |
| DOI | https://doi.org/10.1029/2019GL082376 | Article |
| Article type | Research letter that constructs absolute locations and GrowClust relative relocations for a 3,345-event sequence | Abstract and Sections 2-3 |
| Local paper parse | references/PANG2019_GL082376/parsed/PANG2019_GL082376__paper__mineru.md | MinerU output |
| Supplement | references/PANG2019_GL082376/supplement/Pang2019_MapleCreek_SI.pdf | Local PDF; no machine-readable event table found in the local supplement folder |

This is a genuine catalog-construction paper and is methodologically distinct from
Shelly and Hardebeck's template-matching study. It is the most useful independent
secondary location reference for this case, but the 3,345-row event table is not
currently staged locally.

## Scientific scope

- **Sequence:** Maple Creek, Yellowstone; activity began 2017-06-12 and the
  combined sequence is followed through 2018-03-13.
- **Spatial context:** the 2017 activity persisted in an approximately 9 km by
  12 km rectangle east of Hebgen Lake; a separate southern burst reactivated in
  2018.
- **Population:** 3,345 events in the article's absolute catalog.
- **Magnitude:** coda duration Mc from -1.7 to 4.4; estimated completeness Mc about
  0.5; b value 0.96 (paper Section 2).
- **Depth:** more than 97 percent of events are at 6-14 km beneath the local
  surface (mean elevation about 2.3 km).
- **Scientific role:** absolute-location baseline plus high-precision relative
  geometry and VP/VS structure; useful for independent comparison with Shelly.

## Observation and network conditions

- Waveforms and routine phase data came from IRIS/EarthScope and the Yellowstone
  network.
- The paper used 22 local and 2 regional stations (24 total) selected for data
  quality and azimuthal coverage for waveform differential times.
- Network codes listed in the paper are MB, PB, TA, US, and WY.
- Absolute locations were routinely detected by the University of Utah
  Seismograph Stations using HYPOINVERSE and a regional 1-D velocity model.
- The paper does not publish a fixed station-day availability table in the local
  supplement; station count should therefore be treated as the relocation setup,
  not continuous availability during every event.

## Catalog-construction workflow

    UUSS routine detections and phase picks
        -> HYPOINVERSE 1-D absolute locations and coda magnitudes
        -> BCSEIS waveform cross-correlation on P and S windows
        -> approximately 4.4 million differential travel times (73 percent P, 27 percent S)
        -> GrowClust hierarchical relative relocation
        -> bootstrap uncertainty assessment
        -> 3,345-event absolute catalog; 3,257 events successfully GrowClust-relocated

Important numerical details:

- Median absolute-location standard errors are about 500 m horizontal and 730 m
  in depth.
- GrowClust uses event-pair similarity and sequential grid-search relocation.
- One hundred bootstrap runs yield median relative errors of about 62 m horizontal
  and 86 m vertical.
- The 3,345 events include both the 2017 northern cluster and the 2018 southern
  cluster; the article does not define the benchmark's compact June-only subset
  as a separate released file.
- The paper interprets the northern cluster primarily as long-lived aftershocks
  of the 1959 Mw 7.2 Hebgen Lake earthquake and the southern cluster as a
  fluid-influenced swarm.

## Supporting information audit

The local SI is a publisher PDF (12-page document structure) containing figures,
velocity-model/relocation supporting material, and table/figure captions. It is
not a CSV, QuakeML, spreadsheet, or other event-level release. The article and
SI text available locally do not expose a stable URL for a 3,345-row
machine-readable GrowClust table. Therefore:

- Supplement status is **present** for method/context review.
- Catalog status is **missing**, not partial or ready.
- The USGS correlation-phase release under 10.5066/P13JCJ2I must not be
  substituted: its XML identifies Shelly and Hardebeck's Yellowstone phase
  product, not Pang's GrowClust event catalog.
- IRIS waveform access supports reproduction of the method but is not itself a
  downloaded event catalog.

## Benchmark interpretation

| Dimension | Decision |
|---|---|
| Quality tier | Q1/Q2 secondary: strong absolute/relative location, but not an independently reviewed truth set |
| Evaluation role | Independent high-resolution location comparison against Shelly; use for event geometry and location error, not direct phase-pick scoring |
| Method independence | Medium-High relative to Shelly: HYPOINVERSE + BCSEIS + GrowClust versus matched-filter + hypoDD |
| Shared lineage | Same public waveform archives and UUSS routine monitoring; not fully independent in raw observations |
| Current readiness | Paper and SI ready; machine-readable event catalog missing |
| Required next action | Locate the authors' or repository's original 3,345-row catalog, verify DOI/provenance, then apply the frozen common mask |

## Local paths

- Paper PDF: references/PANG2019_GL082376/paper/PANG2019_GL082376__paper.pdf
- Parsed paper: references/PANG2019_GL082376/parsed/PANG2019_GL082376__paper__mineru.md
- Supplement PDF: references/PANG2019_GL082376/supplement/Pang2019_MapleCreek_SI.pdf
- Catalog status note: catalogs/PANG2019_GL082376/PANG2019_GL082376__catalog_summary.md
