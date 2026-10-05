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
and [output_schema.json](output_schema.json). A JSON configuration can be
passed with `--config`; otherwise conservative single-process defaults are
used. The interface does not perform event location or consume reference
catalogs.
