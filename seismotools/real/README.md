# REAL

REAL (Rapid Earthquake Association and Location; Zhang, Ellsworth & Beroza
2019, *SRL* 90, 2276) associates picks by counting P and S arrivals inside
theoretical travel-time windows on a grid around the station with the
initiating pick, then refines the best node (simulated annealing). It is the
associator of the LOC-FLOW workflow.

```text
real/
├── source/upstream/   # REAL.c (MIT) at a pinned commit (see source/README.md)
├── runtime/bin/REAL   # built locally (not committed)
├── interface/         # run.py and its contract (interface/README.md)
├── examples/smoke/    # synthetic known-answer run
└── metadata.json
```

```bash
python seismotools/support/build_native.py --tool real
python seismotools/real/interface/run.py --picks picks.csv --stations stations.csv \
  --velocity-model model.txt --output-dir OUT [--config config.json]
```

The adapter builds REAL's travel-time table from a 1-D model (first arrivals,
head waves included), writes REAL's station and pick files, runs it on time
chunks with a buffer and returns the same `events.csv` / `assignments.csv`
contract as the GaMMA and PyOcto interfaces. Use the project Python
environment (pandas, pyrocko). Every setting and its REAL flag:
[interface/README.md](interface/README.md).

Validation (`support/tools_usage_validation/validate_real.py`): table against
analytic half-space times and slopes; the shared synthetic case (40/40
events, all true picks on the right event, no false pick absorbed), also
across midnight (two chunks, no duplicates); six Prague hours against the
GaMMA association (97.5 % of GaMMA events with ≥ 10 stations; 97.6 % of REAL
events confirmed by GaMMA — more conservative than PyOcto).
