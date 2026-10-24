
# Ridgecrest Earthquake Catalog: Expert Workflow Plan

## Objective and scope

Build a traceable, reproducible earthquake catalog from raw continuous waveforms and station metadata through phase picking, association, location, and quality control. The workflow will serve as an expert reference for subsequent agent evaluation, not as unique ground truth.

- **Window:** 2019-07-04 00:00:00 to 2019-07-07 00:00:00 UTC, end exclusive.
- **Inputs:** the currently prepared 41 stations, 117 channels, and corresponding StationXML; freeze the actual file and channel selection before execution.
- **Event region:** latitude 35.45–36.05°, longitude −117.90–−117.20°. Allow margins for association and location; do not restrict station selection to this region.
- **Reference catalogs:** use published catalogs for comparison. Any use of their templates, seed events, or picks belongs to a separate catalog-assisted experiment.

## Current phase

The initial full baseline is complete as provisional v1 in `export/01_baseline/10_validate_catalog/`. Stages 11–20 are comparison, local relocation and diagnostic branches, not successive full-catalog versions. The active objective is to improve and validate absolute location accuracy before publishing another full version. Broad parameter scanning is closed. The fixed station-phase correction experiment is complete (stage 17). It improves withheld timing and horizontal reference agreement but worsens compatible depth agreement, failing its adoption gate. Preserve it as an experimental result; resolve depth/model constraints before another adoption test. Stage 18 explains the shift through correction/depth coupling, but does not identify the physical source of the influential S residuals. The bounded stage-19 waveform review is complete and does not support systematic large late picking in its fixed sample. Retain observations and focus the next bounded intervention on velocity/path and depth constraints. Stage 20 now implements a controlled HK profile experiment under an explicit common +0.7-km ASL depth plane, holding observations and other settings fixed. Its four 147-event branches compare full-data locations and withheld-arrival prediction; model qualification is only an input note. Native SCSN datum reproduction is not claimed. Consult the experiment report for the outcome; no full v2 has been produced.

See [the evolution and organization plan](docs/EVOLUTION.md) for branch status, adoption gates and the current code layout. Scripts and configuration have moved into numbered responsibility groups; existing output paths remain unchanged.

## Existing implementation layout and baseline

Python entry points are grouped under `01_pipeline/`, `02_diagnostics/`, `03_experiments/` and `04_comparison/`; shared YAML lives in `00_config/`. Scripts resolve the expert root independently of their working directory. Outputs remain under the existing `export/<step>/` paths, and documents remain under `docs/`. Retain outputs until explicitly cleaned up.

The first baseline is **PhaseNet picking → GaMMA association and initial locations → NonLinLoc absolute locations**. Start with the local PhaseNet `original` v2 weights, subject to compatibility and inference validation. Use arrival times only for initial GaMMA association; magnitude processing is a separate stage. Preserve common pick/event interfaces so additional absolute-location methods can be compared later. See [README.md](README.md) for step names, implementation status and local dependency findings.

## Workflow

| Stage                       | Main work                                                                                                                                                                                                                                                                                             | Output                                                     |
| --------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------- |
| 1. Fix inputs               | Reuse existing coverage and response checks; confirm channels, orientations, epochs, and gaps. Preserve raw waveforms.                                                                                                                                                                                | Input selection and file versions                          |
| 2. Define processing        | Trial pre-event, mainshock, and coda windows. Select detrending, filtering, normalization, chunking, and buffers according to picker requirements; correct instrument responses separately for physical-amplitude analysis.                                                                           | Processing configuration and short-window validation       |
| 3. Pick phases              | Extract P/S arrival times and confidence information throughout the three days. Handle overlapping chunks and preserve gaps; do not synthesize horizontal components for vertical-only stations.                                                                                                      | Standardized phase-pick table                              |
| 4. Associate and locate     | Select a baseline from the available 1-D velocity models; document the model, depth datum, and travel-time settings. Associate picks and estimate initial event locations.                                                                                                                            | Initial catalog and event–pick associations               |
| 5. Control location quality | Check travel-time residuals, station geometry, pick counts, depth boundaries, and duplicate events. Review outlier picks iteratively and record retention or rejection reasons.                                                                                                                       | Quality-controlled location catalog                        |
| 6. Estimate magnitudes      | Document the magnitude relation and applicability. Use valid response-corrected amplitudes, checking saturation and station consistency. Leave unreliable estimates missing with reasons.                                                                                                             | Magnitudes, contributing station counts, and quality flags |
| 7. Validate results         | Use an initial Shelly/Liu/official comparison during location-quality review; later validate the finalized product against applicable reference catalogs, including Ross. Examine pre/post-mainshock, dense-event, and coda periods; review representative apparent misses and additional detections. | Comparison results and explanations of major differences   |
| 8. Finalize                 | Fix configurations, code, and execution records; verify reproducibility and summarize limitations.                                                                                                                                                                                                    | First expert catalog and concise report                    |

## Execution principles

- Complete a short-window end-to-end trial before processing all three days. Do not expand general-purpose data screening.
- Response removal and filtering cannot repair saturation. Handle suspect intervals according to their intended use; do not discard an entire station because of a local anomaly.
- Set picking and association parameters on development windows before examining the remaining periods. Agreement with reference catalogs is not the sole tuning objective.
- Unmatched reference events are not automatically misses or false detections. Interpret depth datums and magnitude types separately.
- Differential travel times and relative relocation are optional second-stage enhancements, not requirements for the first catalog.

## Deliverables

1. **Event catalog:** event ID, UTC origin time, latitude, longitude, depth and datum, magnitude and type, station/pick counts, residuals, uncertainties where estimable, and quality flags.
2. **Phase table:** event ID, station/channel, P/S type, arrival time, confidence information, location residual, and usage status.
3. **Reproducibility materials:** input versions, processing configuration, execution code, and a concise results report. Keep expert-workflow materials in this directory, separate from agent-visible inputs.

The first version is complete when the three-day workflow runs successfully, events and picks are traceable, results are reproducible, and major differences and limitations are documented. Maximizing event counts or exactly reproducing a published catalog is not a completion criterion.

Stage-20 outcome: HK reduces withheld RMS by 11.1% and improves horizontal reference agreement, but increases the Shelly depth discrepancy by 29.9% and p90 posterior depth sigma by 11.3%. It fails promotion; retain v1 and close this fixed trial.

## Stage 60 — Match&Locate (2026-10-24)

Motivation: a cross-case review found Ridgecrest the only case whose expert
catalog recalls the references less well than the references recall each
other (expert vs Shelly 0.612, Ross 0.574, Liu 0.751, ComCat 0.641; Shelly
alone recovers 75.0 % of Ross and 82.3 % of Liu). Shelly and Ross are
template-matching catalogs; this catalog had no detection stage beyond the
picker. `01_pipeline/60_match_locate.py` + `00_config/match_locate.yaml`,
ported from Kaikōura: templates are v1 events (≥ 10 stations, σz ≤ 2 km) at
their stage-52 double-difference positions, marked with their NLL-associated
picks; the union base is the stage-52 working catalog (6,520); references and
gates (4 s / 15 km, comparison box) come from the task evaluation module, so
stage-60 scores equal the evaluation layer's. Shelly Table 1 is used as the
expert's GaMMA/NLL runs used it (linear interpolation), densified into
0.25 km constant sublayers; stations within 40 km (median v1 event: 12).
Outputs: `export/07_match_locate/`.

Pilot (07-05, 20 templates by station count): at N×MAD 9.5 the union
recovers Shelly 58.0 → 70.6 %, Ross 53.3 → 65.8 %, Liu 73.7 → 77.3 %,
ComCat 63.4 → 70.9 % (1,253 new events); 9.4 s per template-day.
Full run: 1 km cover → 1,235 templates (95 % of v1; 0.5 km would be 2,462
and ~19 h), three days. Threshold from a null run, as in every other case.

Result (2026-10-25): **adopted.** Full run: 1,061 of 1,235 templates kept,
3,183 jobs, 2.5 h. Null run (07-05 + 07-06, channel circular shift): false
fraction 77 % at N×MAD 8, 26 % at 8.5, 4.2 % at 9, **0.3 % at 9.5**, 0.04 %
at 10 → final 9.5. Final separation **4 s**, not Magna's 6 s: on the null
days 4 s keeps 9,717 detections (6 s: 7,745) with the same 23 null ones
(0.24 %) — 6 s merged real events in the aftershock coda. Catalog
`export/07_match_locate/60_catalog/catalog_events.csv`: **16,686 events**
(6,520 stage-52 + 10,166 M&L); magnitudes chained from 424 ML templates to
981 of 1,061.

| | stage 52 | M&L | **union** | other refs' best recall of it |
|---|---|---|---|---|
| Shelly | 0.612 | 0.856 | **0.910** | 0.629 (Ross) |
| Liu | 0.751 | 0.887 | **0.950** | 0.823 (Shelly) |
| Ross (nbranch > 1) | 0.574 | 0.872 | **0.910** | 0.750 (Shelly) |
| ComCat | 0.641 | 0.808 | **0.877** | 0.735 (Shelly) |

Median epicentral vs Shelly / Liu / Ross / ComCat: 0.62 / 0.80 / 0.75 /
0.83 km. Ridgecrest now exceeds the reference-to-reference recall like the
other five cases. The task evaluation layer reads this union (depths below
sea level + 0.7 km).

## Stage 62 — cross-correlation relocation pilot (2026-10-25)

Motivation: the stage-60 union is less sharp than Shelly/Ross (fault-normal
width 1.58 km vs 0.85): its 10,166 M&L events sit on 4,975 template grid
nodes and were never relocated. `01_pipeline/62_cc_relocation.py`: CC
differential times from the new `seismotools/cross_correlation` (ccdt),
hypoDD with the stage-14 control `cc3_d1` (and a variant with a final
CC-dominated set). Pilot day 07-05: 6,814 events (2,476 picked + 4,338 M&L).
Sharpness metric: median local thickness (minor-axis SD of each event's 20
nearest neighbours, map view) — orientation-free; the single-strike
fault-normal width mixes the NE and NW faults of that day and was dropped.

Findings:
1. **Template-derived catalog times must not enter dt.ct.** Two detections
   of one template get catalog dt = 0 at every station, and hypoDD collapses
   them onto the template (M&L thickness 0.05 km, a third of Shelly's — an
   artifact). dt.ct now comes from picks only; M&L events rely on CC alone.
2. Dropping such links leaves weakly constrained events that diverge; rows
   with overflow, > 3 km horizontal shift, depth outside 0–25 km or > 1 s
   origin change are treated as not relocated (they keep their M&L position).

| 07-05 | relocated | vs Shelly | vs Liu | vs Ross | thickness M&L / picked |
|---|---|---|---|---|---|
| before | — | 0.518 km | 0.660 | 0.767 | 0.18 (grid-stacked) / 0.31 |
| CC 3 km / 30 nbrs, CC ≥ 0.7 | 4,201 | 0.360 | 0.518 | 0.688 | 0.35 / 0.31 |
| CC 5 km / 80 nbrs, CC ≥ 0.6, CC² | 4,596 | **0.254** | **0.387** | 0.664 | 0.33 / 0.30 |
| Shelly / Ross / Liu thickness | | | | | 0.16 / 0.16 / 0.27 |

(epicentral medians of matched pairs, same events before and after.)
Accuracy improves strongly with CC density; sharpness does not reach
Shelly's: per-event scatter of ~0.2–0.3 km remains. CC data are the limit —
332k accepted measurements (~50 per event) vs Shelly's ~700 per event.

Three-day run (2026-10-25; `--scope full`, CC 5 km / 80 neighbours,
CC ≥ 0.6, CC² weights, dt.ct from picks only, control cc3_d1): 16,686
events, 778,824 accepted CC times (246,379 linked pairs), 2.40 M pick
differences; hypoDD MAXEVE raised to the event count. 11,093 relocations
accepted (picked 6,056 / 6,520; M&L 5,037 / 10,166); 5,008 not in the
hypoDD output, 585 rejected as diverged.

| 3 days | vs Shelly | vs Liu | vs Ross | thickness picked / M&L |
|---|---|---|---|---|
| before | 0.616 km | 0.801 | 0.748 | 0.337 / 0.263 (grid-stacked) |
| cc3_d1 | 0.458 | 0.468 | 0.809 | 0.333 / 0.390 |
| cc3_d1 + CC-dominated set | 0.505 | 0.556 | 0.878 | 0.315 / 0.380 |
| Shelly / Ross / Liu thickness | | | | 0.193 / 0.197 / 0.283 |

What the relocation changes is the *frame*, not the sharpness: hypoDD with
the Shelly Table-1 layered model (no station elevations) moves the catalog
~0.35 km SW, toward Shelly and Liu, away from Ross (3-D model). Removing that
centroid shift worsened agreement with Shelly (pilot day 0.25 → 0.52 km), so
no correction is applied. Local thickness of the same events before/after,
by CC links: ≥ 50 links 0.222 → 0.255 km; 20–50 0.529 → 0.575; < 20
~0.9–1.0 → slightly more. Even well-linked events end slightly more
scattered than their stage-52 joint-DD positions. Relocated M&L events lose
their grid stacking but reach only the picked events' scatter level.
Conclusion: with ~50–150 CC times per event, hypoDD does not reach Shelly /
Ross sharpness (~0.19 km); not adopted into the evaluation layer pending a
decision (GrowClust — Ross's L1 cluster-wise method — is the remaining
untested lever).
