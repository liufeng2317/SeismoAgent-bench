# Case information-collection standard

What to record for every benchmark case and its reference catalogs, how to choose the primary reference, and what to verify before a case is used. Moved from the research plan v0.2, Part III, on 2026-10-29. The resulting records are the case analyses under `data/<case>/analysis/` indexed in [`CASE_REGISTRY.md`](../CASE_REGISTRY.md); literature extraction follows [`INFORMATION_EXTRACTION_SCHEMA.md`](INFORMATION_EXTRACTION_SCHEMA.md).

## 1. Information-collection standard

Each detailed benchmark case should be documented in three layers.

### A. Case information

This section describes the earthquake sequence itself, independent of any particular target catalog.

| Field | Required information |
|---|---|
| **Case ID** | Stable benchmark identifier |
| **Case / sequence name** | Standard scientific name |
| **Region** | Geographic setting |
| **Tectonic / volcanic context** | Strike-slip, normal faulting, subduction, volcanic, induced, etc. |
| **Sequence type** | Mainshock–aftershock, swarm, foreshock sequence, volcanic sequence, etc. |
| **Key event(s)** | Mainshock / largest event and important milestones |
| **Scientific significance** | Why the sequence is scientifically important |
| **Full study span** | Time range of the published reference study |
| **Recommended benchmark window** | Compact interval actually proposed for benchmarking |
| **Reason for window selection** | Scientific importance + computational practicality |
| **Network context** | Permanent / temporary / dense / sparse / changing network |
| **Raw waveform source** | SCEDC, EarthScope/IRIS, GeoNet, NIED, EIDA, agency archive, etc. |
| **Routine catalog / phase availability** | Operational inputs that may be used in assisted conditions |
| **Expected difficulty** | Low / Medium / High |
| **Primary benchmark role** | Detection, association, location, relocation, workflow recovery, etc. |

### B. Reference catalog information

A case may have one to three reference products. Each should be documented separately.

| Field | Required information |
|---|---|
| **Catalog name / label** | Stable name for the reference |
| **Priority** | Primary / Secondary / Baseline / Auxiliary |
| **Reference type** | Detection, phase, absolute location, relative location, structural, completeness, etc. |
| **Reference paper** | Authors, year, journal, DOI |
| **Public data release** | Repository and DOI/URL |
| **Catalog span** | Full published target interval |
| **Catalog size** | Number of events in the distributed/full reference |
| **Magnitude range / completeness** | If documented |
| **Stations / channels** | Number used in the reference workflow |
| **Waveform source** | Data center / network |
| **Waveform type** | Continuous, event waveform, template waveform, nodal, etc. |
| **Initial catalog source** | Routine catalog / analyst catalog / template set |
| **Phase-pick source** | Manual, automatic, neural, correlation-derived |
| **Detection method** | Template matching, subspace, ML, operational detection |
| **Association method** | GaMMA, REAL, clustering, custom method, manual |
| **Absolute-location method** | Hypoinverse, NonLinLoc, Bayesloc, VELEST, etc. |
| **Relative-relocation method** | hypoDD, GrowClust, cross-correlation DD, etc. |
| **Velocity model** | 1-D / 3-D / calibrated / station corrections |
| **Manual QC / expert review** | Type and extent of human review |
| **Uncertainty / QC products** | Formal error, bootstrap, quality classes, residuals, filtering thresholds |
| **Catalog open access?** | Yes / registration / restricted |
| **Raw waveform open access?** | Yes / registration / restricted / unclear |
| **Phase data open access?** | Yes / No / partial |
| **Reference quality** | Provisional High / Medium / Low |
| **Reference independence** | High / Medium / Low |
| **Why considered reliable** | Short evidence-based justification |
| **Best benchmark use** | What dimension this product should score |
| **Main limitation** | What cannot be inferred from it |

### C. Benchmark suitability

| Field | Required information |
|---|---|
| **Recommended?** | Yes / Maybe / No |
| **Primary target** | Selected high-quality reference |
| **Secondary references** | Other 0–2 reference products |
| **Baseline** | Routine operational catalog |
| **Suggested Agent input** | Raw-only / routine-catalog-assisted / phase-assisted |
| **Benchmark window** | Frozen compact interval |
| **Target event count in window** | Recomputed from the actual reference file |
| **Active station/channel count** | Recomputed for the benchmark interval |
| **Approximate waveform volume** | Computed from real request |
| **Expected compute cost** | Low / Medium / High |
| **Main capability tested** | Principal benchmark purpose |
| **Main benchmark risk** | Leakage, data access, method overlap, network changes, etc. |
| **Overall assessment** | Short recommendation |

## 2. Rules for selecting the primary reference

When several high-quality catalogs exist for the same sequence, choose the primary reference according to the benchmark dimension, not simply by event count.

A preferred primary reference should have as many of the following as possible:

1. strong expert acceptance;
2. high-quality picking / waveform correlation / relocation;
3. explicit QC and uncertainty information;
4. public catalog files;
5. transparent methods;
6. good overlap with the proposed compact benchmark window;
7. reasonable independence from the Agent workflow.

Secondary catalogs should be preserved when they offer:

- a different processing methodology;
- stronger absolute-location information;
- stronger relative-location information;
- an independent event-detection view;
- phase-level reference data;
- structural or uncertainty constraints.

## 3. Required verification before benchmark freeze

| Check | Why it matters |
|---|---|
| **Subset each reference catalog to the exact benchmark window and region** | Determines the actual target-event count for the benchmark task. |
| **Extract the active station/channel list for the compact interval** | Prevents full-study station counts from being incorrectly applied to the short benchmark window. |
| **Estimate waveform volume from the actual request** | Makes storage and compute costs reproducible. |
| **Download a small waveform sample from every required network** | Confirms current practical data access. |
| **Inspect reference catalog schemas and stable IDs** | Required for event matching, duplicate handling, and phase comparison. |
| **Reconcile publication and release counts** | Prevents ambiguous target definitions. |
| **Document method overlap between Agent tools and each reference** | Separates independent evaluation from workflow reproduction. |
| **Freeze what information is hidden from the Agent** | Prevents target leakage. |
| **Freeze the Agent input condition** | Raw-only and assisted tasks must remain distinct. |
| **Assign an evaluation role to every reference product** | Detection, phase timing, absolute location, relative location, and uncertainty should not be scored against one undifferentiated target. |
