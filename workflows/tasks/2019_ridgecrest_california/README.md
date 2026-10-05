# Ridgecrest earthquake-catalog task

This directory is the complete runnable task package for the 2019 Ridgecrest
catalog-construction case. Its public task interface consists of the task
definitions, prompts, input declaration, baseline entry point and runner:

```text
input.json        # read-only source folder declaration
task.json         # clean baseline task metadata
task_tools.json   # task metadata using the tools prompt
prompt_base.md    # clean baseline Agent prompt and output requirements
prompt_tools.md   # optional prompt with local seismological tools exposed
main.py           # deterministic baseline entry point
run.sh            # Codex entry point; select VARIANT=base or tools
```

The source folder declared in `input.json` is linked read-only during a run as:

```text
$BENCH_OUTPUT/input/waveforms/
├── data/
└── stations/
```

The Agent must discover the available files, state its processing scope and
methods, and write a reproducible candidate catalog and supporting results
under `$BENCH_OUTPUT`. The default runner uses the separate
`seismoagent_eval` environment so that package installation does not modify the
shared `seismoagent` environment. The required catalog format and scientific
limitations are described in `prompt_base.md`; no separate output-contract file
is needed. `prompt_tools.md` is an optional variant that exposes the local
PhaseNet, GaMMA, NonLinLoc and hypoDD sources while leaving method selection to
the Agent.

The default runner allows up to four hours for the complete Agent run. Override
this with `TIMEOUT`, in seconds, when a different processing budget is needed.

Run outputs are separated by prompt variant:

```text
runs/base/     # clean baseline prompt
runs/tools/    # tools-enabled prompt
```

Use `bash run.sh` for the baseline or `VARIANT=tools bash run.sh` for the
tools-enabled task. Override `RUN_ID` and `TIMEOUT` when needed.

`main.py` is a deterministic infrastructure baseline for checking task
execution and catalog generation. It is not a scientific detector, phase
picker, or location solution. The expert scientific workflow remains under
`expert/` and is not part of the Agent task interface.

Large waveform files, source catalogs and generated analysis products remain in
the external data store and are not copied into Git.
