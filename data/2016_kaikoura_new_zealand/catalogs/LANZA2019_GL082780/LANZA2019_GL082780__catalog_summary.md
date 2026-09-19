# LANZA2019_GL082780 — catalog summary and local audit

## Product identity

| Field | Value |
|---|---|
| Source | Lanza et al. (2019), DOI [10.1029/2019GL082780](https://doi.org/10.1029/2019GL082780) |
| Product | Data Set S1: relocated hypocenters and P/S arrival picks |
| Format | QuakeML 1.2 XML; source-native file retained |
| Local file | `raw/grl59060-sup-0003-ds01.xml` |
| SHA-256 | `c87a16de4fb28be7cd873b03e93b3d410c6e2237d7ed443affbe798670fbd478` |
| Article-reported final clustered count | 2,013 HypoDD events |
| Local HypoDD-origin count | 2,012 (one-event discrepancy; unresolved) |
| Local event-object count | 2,655 unique event IDs |

The XML is not an independent operational catalog. It is the release product
of a reviewed-event, REST/kpick, simul2014, and HypoDD relocation workflow. Its
event IDs are local QuakeML IDs (`smi:local/2017p...`) and should not be joined
to GeoNet/Tan/Chamberlain IDs by string equality.

## Event and origin structure

| Audit item | Result |
|---|---:|
| `event` objects | 2,655 |
| Unique event `publicID` values | 2,655; no exact duplicate IDs |
| `SIMUL` origin objects | 2,655 |
| `HypoDD` origin objects | 2,012 |
| Events with two origins | 2,012 |
| Events with only SIMUL origin | 643 |
| Events with explicit `preferredOriginID` | 2,012 |
| Events without `preferredOriginID` | 643; their sole SIMUL origin is used in the local audit |
| Magnitude elements | 2,655 (one per event) |
| `preferredMagnitudeID` | absent from all event objects |
| Magnitude type | generic `M` in all 2,655 elements; physical scale unresolved |

When both origins exist, the article says the HypoDD origin is preferred. The
local XML implements that through `preferredOriginID`. For the 643 SIMUL-only
events, no preferred-origin link is serialized. A normalization script should
record `origin_method` explicitly and should not fill missing preferred IDs with
an invented identifier.

## Local ranges

The following ranges use the selected/preferred origin where available and the
sole SIMUL origin otherwise. Depth is converted from QuakeML metres to positive
downward kilometres.

| Field | Full local range |
|---|---:|
| Origin time (UTC) | 2016-11-13T11:02:56.460000Z – 2017-05-13T18:03:47.100000Z |
| Latitude | −43.28217 – −40.08467° |
| Longitude | 172.06067 – 175.26200°E |
| Depth | −0.94 – 164.12 km |
| Generic `M` value | 2.2 – 7.4 |
| Pick-time uncertainty | 0.02 – 0.55 s where populated |

The full spatial/depth ranges are wider than the main-paper selection rectangle
because the XML retains SIMUL-only and poorly constrained origins. Sixteen
preferred/sole origins have negative depth and 35 have depth >=50 km. These are
not deleted from the source file; they require an explicit benchmark mask.

By origin method:

| Origin method | Events | Depth range (km) | Generic `M` range |
|---|---:|---:|---:|
| HypoDD preferred | 2,012 | 0.045–41.389 | 2.2–7.4 |
| SIMUL only/fallback | 643 | −0.94–164.12 | 2.6–6.7 |

HypoDD origins do not carry a `quality` child in this XML. SIMUL origins do
carry `usedPhaseCount`, `standardError`, `azimuthalGap`, and `minimumDistance`;
those fields must not be interpreted as HypoDD quality values.

## Pick and station fields

| Field | Local result |
|---|---:|
| P picks (`phaseHint=P`) | 110,810 |
| S picks (`phaseHint=S`) | 72,149 |
| Total picks | 182,959 |
| Pick method IDs | All `smi:local/REST` |
| Evaluation mode | Automatic in serialized picks |
| Unique station codes | 81 |
| Arrival links | Origins link to picks through `arrival/pickID`; arrival `phase` is serialized as `None` in the local XML, so use pick `phaseHint` for P/S labels |
| Pick uncertainty | `time/uncertainty`, seconds; 0.02–0.55 s in populated elements |

The Text SI reports 114,140 high-quality P and 73,783 high-quality S picks after
REST+kpick QC. The XML totals are lower and do not label kpick picks separately.
This is a release-level discrepancy, not a reason to append synthetic rows.

Table S1 independently lists 81 stations: 24 STREWN temporary stations and 57
GeoNet entries. It does not establish station-day availability; temporary and
strong-motion gaps must be obtained from waveform metadata if network-aware
scoring is required.

## Construction lineage and quality rules

The paper/SI workflow is:

```text
2,768 GeoNet-reviewed events (approximately M_L >= 3)
    → REST automatic onset/picking
    → kpick additional S/P picks
    → uncertainty, residual, and P–S pairing QC
    → simul2014 fixed 3-D velocity-model locations (2,655)
    → HypoDD 3-D, <=10 km pair separation and CC >0.65
    → 100 bootstrap relocation repetitions
    → QuakeML event/origin/magnitude/pick release
```

Important reported filters and products:

- Text S1: 3 of 2,768 inputs fail REST; 2,765 are picked/located by REST.
- Main §4.1: 2,655 simul2014 locations; 110 poor-depth events are not carried
  into the clustered interpretation.
- Main §4.2: 1,359,256 phase differential times and 187,138 waveform
  cross-correlation differential times; ~24% of events are discarded by the
  10-km clustering condition; article reports 2,013 HypoDD events.
- Main §4.2/Text S5: waveform cross-correlation uses 1–20 Hz, 1-s P/S windows
  beginning 0.2 s before picks; threshold >0.65 is a relocation link rule, not
  a detection completeness threshold.
- Text S4: most estimated simul2014 model-related absolute uncertainties are
  below 2 km under an assumed slowness uncertainty of ~0.02 s/km.

## Frozen benchmark masks

The Kaikōura case uses the half-open UTC window:

```text
2016-12-01T00:00:00Z <= origin_time < 2016-12-09T00:00:00Z
```

The common spatial/depth mask is:

```text
-43.5 <= latitude <= -41.2
172.0 <= longitude <= 175.2
0 <= depth_km <= 60
```

Applying these rules to the local XML gives:

| Mask stage | Event count | Origin-method split | Range summary |
|---|---:|---|---|
| Time only | 123 | 110 HypoDD + 13 SIMUL | depth 1.921–75.91 km; generic `M` 2.2–5.8 |
| Time + spatial/depth mask | **122** | 110 HypoDD + 12 SIMUL | lat −42.92922–−41.56183; lon 172.76817–175.18033; depth 1.921–37.01 km; generic `M` 2.2–5.8 |
| Time + mask + generic `M >= 3` sensitivity only | 120 | 110 HypoDD + 10 SIMUL | Magnitude type remains unresolved; do not use as canonical count |

The paper describes the selected input as `M_L >= 3`, but the distributed
QuakeML preserves only generic `M` and includes two common-mask values below 3.
The canonical benchmark label is therefore **122 released XML events under the
common mask**, with the `M >= 3` count retained only as a sensitivity audit.

## Benchmark role

| Dimension | Assessment |
|---|---|
| Quality tier | Q1 for high-quality absolute/relative location and relocation geometry; Q3 for completeness/small-event recall |
| Primary role | Location, 3-D relocation, relative geometry, and uncertainty calibration |
| Secondary role | Structural/fault-connectivity reference against Tan SUGAR and Chamberlain GrowClust |
| Suitable metrics | Matched-event time/epicenter/depth residuals; relative geometry; clustering; uncertainty-aware scores |
| Unsuitable metrics | Universal detection recall, rate completeness, magnitude-of-completeness, or a blanket event-existence truth score |
| Independence | Medium–high relative to a generic agent; lower when the agent uses the same GeoNet/STREWN waveforms, picks, or templates |
| Main caveats | Generic magnitude type; article/XML HypoDD count mismatch; SI/XML pick mismatch; no station-day availability; method-dependent outliers |

## Provenance and related files

- Paper reading: `../../references/LANZA2019_GL082780/paper/LANZA2019_GL082780__paper_reading.md`
- Supplement notes: `../../references/LANZA2019_GL082780/supplement/LANZA2019_GL082780__supplement_notes.md`
- Paper PDF SHA-256: `efbff3c2516dabbb1d26c1dd97e612ac06822322b27b1a844c301b08e0cd93e0`
- Text SI SHA-256: `19b7c2e8ff6d22826b0b4ac7a2c9a0746a77ddf5ce03e1b4c70402ae50e0cf41`
- Table S1 SHA-256: `1711333f28b6c60cd87305450e68b824ecc3a7ddc24ea7c266118a85ee770384`
- QuakeML SHA-256: `c87a16de4fb28be7cd873b03e93b3d410c6e2237d7ed443affbe798670fbd478`

