# hypoDD

One native implementation supports two configurations: **CT** (catalog differential arrival times) and **CT+CC** (catalog plus waveform cross-correlation differential times). It is independent of the case-local Joint DD solver.

The local distribution supplies manuals and utilities. `source/src/hypoDD` and `source/include` use the files actually built for Ridgecrest stage 53, including its capacity header: MAXEVE=7000, MAXDATA=3715827, MAXSTA=100, MAXCL=7000. These are memory capacities, not scientific thresholds or generic limits suitable for every case. Changes require a separate recorded build.

```bash
python seismotools/build_native.py --tool hypodd --jobs 4
```

The build uses gfortran with `-O2 -std=legacy -fallow-argument-mismatch`, producing `bin/hypoDD`. Inputs: event/station files, `dt.ct`, optionally `dt.cc`, and a control file. Outputs include `hypoDD.reloc`, logs and event membership. CC measurement itself belongs to preprocessing and is not implemented by this native solver.

See the [original README](source/README) and [bundled manual](source/doc/hypoDD.pdf). Control examples and executed constraints remain in the [stage 53 report](../../workflows/tasks/2019_ridgecrest_california/expert/export/06_full_catalog/53_native_double_difference/README.md) and [case runner](../../workflows/tasks/2019_ridgecrest_california/expert/01_pipeline/53_native_double_difference.py). Keep CT/CC weights, differential-time sign/origin convention, velocity layers and exclusions explicit. Existing expert CT and CT+CC runs start independently from NLL, not from the Joint DD candidate.
