# Standard GaMMA interface

`run.py` is the stable project entry point for associating phase picks. It
accepts two small CSV tables, applies the local GaMMA implementation, and
writes event and pick-assignment tables below a writable output directory.

```bash
python seismotools/gamma/interface/run.py \
  --picks picks.csv \
  --stations stations.csv \
  --output-dir /path/to/writable-run
```

Input and output columns are defined in [input_schema.json](input_schema.json)
and [output_schema.json](output_schema.json). Optional configuration fields are
listed in [config_schema.json](config_schema.json). A JSON configuration can be
passed with `--config`; nested overrides are merged with the defaults. The
interface does not perform event location or consume reference catalogs.

Every input pick appears in `assignments.csv`. Associated rows contain an event
index and probability; unassociated rows have a null event index, zero
probability and `assignment_status=unassigned`. If output files already exist,
the command fails rather than silently replacing them; pass `--overwrite` only
when replacement is intentional. A failed run writes a `run_result.json` with
`status=failed` and the error message.
