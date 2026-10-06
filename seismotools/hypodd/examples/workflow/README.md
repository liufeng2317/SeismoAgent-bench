# hypoDD workflow example

This example prepares two synthetic events, one station and one catalog differential times (`dt.ct`), then runs the native hypoDD CT interface. It demonstrates
the minimum native input set and the expected relocation outputs.

Run it with:

```bash
bash seismotools/hypodd/examples/workflow/run.sh /tmp/hypodd-workflow
```

The example is intentionally underdetermined and only checks the input/output
plumbing. Real relocation requires a suitable event cluster, station geometry
and validated differential times. CT+CC additionally requires `dt.cc`.

The output path must not already exist; choose a new temporary path for each run.
