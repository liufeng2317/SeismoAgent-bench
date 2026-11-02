# Tool checks on benchmark case data

Real-data checks of the `seismotools/` interfaces on expert products and
waveforms of the benchmark cases. They were moved out of
`seismotools/support/tools_usage_validation/` on 2026-10-28: Agents in the
`tools` arm read the tool library, and the library must not point them at
expert products, reference catalogs or case observations. The library keeps
its synthetic and upstream-example checks; [validate_cases.py](validate_cases.py)
imports their helpers.

```bash
bash workflows/development/tools_case_validation/run_all.sh          # all tools
python workflows/development/tools_case_validation/validate_cases.py --tool nonlinloc
```

Outputs go to the ignored `outputs/` directory. Run these checks after a
change to a tool and before a formal run, together with the library's own
`seismotools/support/tools_usage_validation/run_all.sh`.

| Tool | Check |
| --- | --- |
| `phasenet` | One forward pass on 30 s of Ridgecrest three-component data (CI.CCC). |
| `gamma` | Re-association of the largest well-recorded Ridgecrest baseline event's picks. |
| `pyocto` | Six Prague hours of r2 PhaseNet picks against the GaMMA r2 association (count ratio 0.7–1.3, ≥ 90 % of GaMMA events with ≥ 10 stations recovered). |
| `real` | The same six Prague hours (same criteria). |
| `nonlinloc` | One stored Ridgecrest baseline event relocated with its grids; `locate.py` with the Prague r2 settings and station delays reproduces 50 r2 locations (median < 0.1 km, depth < 0.2 km). |
| `hypoinverse` | The same 50 Prague events against the NonLinLoc r2 locations (median epicentre < 0.5 km, depth < 1 km; Keranen model inversions clipped with `lvz_policy`). |
| `hypodd` | Two Ridgecrest catalog (CT) event-pair blocks replayed with native hypoDD. |
| `cross_correlation` | Well-picked Ridgecrest events: accepted CC dt match PhaseNet pick differences (median < 10 ms, MAD < 30 ms, robust slope within 5 %, < 10 % beyond 0.1 s). |
| `growclust` | ccdt (with the DH/CN families) + GrowClust (`ngoodmin` 4) on six Prague hours: inter-event distances of same-cluster pairs agree with Cochran at least 30 % better than the NLL input. |
