# GrowClust

GrowClust (Trugman & Shearer 2017, *SRL* 88, 379) relocates earthquakes by
hierarchical cluster growth: event pairs are joined in order of their
cross-correlation similarity, and each growing cluster is relocated with an
L1 (robust) misfit on the differential times. It is the relative relocation
method used by, e.g., Ross et al. (2019) for Ridgecrest, and an alternative
to hypoDD (L2, damped least squares) on the same `dt.cc` data.

```text
growclust/
├── source/upstream/      # Fortran 90 SRC/ (GPL-3.0) at a pinned commit (see source/README.md)
├── runtime/bin/growclust # built locally (not committed)
├── interface/            # run.py and its contract (interface/README.md)
├── examples/smoke/       # synthetic cluster with exact differential times
└── metadata.json
```

```bash
python seismotools/support/build_native.py --tool growclust
python seismotools/cross_correlation/interface/run.py --events E.csv --arrivals A.csv \
  --waveforms WAVES --output-dir CC                       # ccdt: dt.cc + event_ids.csv
python seismotools/growclust/interface/run.py --events E.csv --stations S.csv \
  --dtcc CC --velocity-model model.txt --output-dir OUT [--config config.json]
```

GrowClust uses only waveform cross-correlation differential times (no
catalog dt.ct), so relocations need enough CC data per event pair; set
`ngoodmin` for sparse data (interface/README.md). Use the project Python
environment.

Validation (`support/tools_usage_validation/validate_growclust.py`): the
local build reproduces the upstream Spanish Springs example exactly (1,616
events); on a synthetic 60-event cluster perturbed by 0.5 km with exact
differential times, relative positions are recovered to 13 m horizontally
(53 m 3-D); on six Prague hours (ccdt + GrowClust, `ngoodmin 4`) inter-event
distances agree twice as well with Cochran's catalog as the NLL input
(0.30 → 0.15 km).
