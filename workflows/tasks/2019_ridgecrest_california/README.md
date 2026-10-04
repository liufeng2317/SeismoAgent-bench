# Ridgecrest earthquake-catalog task

This directory is the complete runnable task package for the 2019 Ridgecrest
catalog-construction case. Its public task interface is intentionally limited
to five files:

```text
input.json        # read-only source folder declaration
task.json         # structured task metadata
task_prompt.md    # Agent-facing instructions and output requirements
main.py           # deterministic baseline entry point
run.sh            # Codex execution entry point
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
shared `seismoagent` environment. The required catalog format and scientific limitations
are described in `task_prompt.md`; no separate output-contract file is needed.

`main.py` is a deterministic infrastructure baseline for checking task
execution and catalog generation. It is not a scientific detector, phase
picker, or location solution. The expert scientific workflow remains under
`expert/` and is not part of the Agent task interface.

Large waveform files, source catalogs and generated analysis products remain in
the external data store and are not copied into Git.
