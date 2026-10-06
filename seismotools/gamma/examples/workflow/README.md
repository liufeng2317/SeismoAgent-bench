# GaMMA workflow example

This example creates a small synthetic pick table and station table, calls the
project GaMMA adapter, and checks the event and assignment outputs. It shows
the minimum input preparation required by the adapter:

- picks: `timestamp`, `station_id`, `phase`, and optional `pick_id`, `probability`;
- stations: `station_id`, `x_km`, `y_km`, `z_km`;
- outputs: `events.csv`, `assignments.csv`, `run_result.json`; the assignment
  table contains one row for every input pick, including unassociated picks.

The implementation is in `run_workflow.py`; `run.sh` is only a thin shell wrapper.

Run it with:

```bash
bash seismotools/gamma/examples/workflow/run.sh /tmp/gamma-workflow
```

The data are synthetic and intentionally small. A successful example validates
file preparation and adapter output handling, not association quality on a
real network.

The output path must not already exist; choose a new temporary path for each run.
