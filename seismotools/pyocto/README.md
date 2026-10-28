# PyOcto

PyOcto (Münchmeyer 2024, *Seismica*) is a high-throughput phase associator:
it partitions space and time into octree nodes and refines those whose
predicted arrivals explain enough picks, then locates each event on the node
grid. It handles high event rates and large networks quickly (six hours of
PhaseNet picks of a dense local network, 6,313 picks, in about 20 s).

```text
pyocto/
├── source/{upstream,patches}/  # PyOcto 0.1.9 subset + build patch (see source/README.md)
├── runtime/build/              # built wheel and site-packages (not committed)
├── interface/                  # run.py and its contract (interface/README.md)
├── examples/smoke/             # synthetic known-answer run
└── metadata.json
```

Use the project Python environment (pandas, pyproj and pyrocko are required;
`seismoagent` or `seismoagent_eval`). Build once (offline; the environment is not modified):

```bash
python seismotools/support/build_native.py --tool pyocto
```

Associate:

```bash
python seismotools/pyocto/interface/run.py --picks picks.csv --stations stations.csv \
  --velocity-model model.txt --config config.json --output-dir OUT
```

Inputs, outputs and every configuration key are in
[interface/README.md](interface/README.md). The output contract matches the
GaMMA interface's `assignments.csv` (plus `residual_s`), so the associated
picks can be handed to any locator (for example
`seismotools/nonlinloc/interface/locate.py`).

Validation (`support/tools_usage_validation/validate_pyocto.py`): the
travel-time table against analytic half-space times; the shared synthetic
case with noise, false and dropped picks (40/40 events, ≥ 99 % of true picks
on the right event; 1 and 4 threads identical); on six hours of real
picks it finds 93 % of the GaMMA events, 99 % of those with ≥ 10 stations.
Upstream documentation: https://pyocto.readthedocs.io (version 0.1.9 API).
