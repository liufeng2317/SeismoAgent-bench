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

In addition to the two legacy variants above, this package ships a canonical
family of five **base-variant prompts** organized as a three-phase experiment
(see `VARIANTS.md`): `base_standard` (fixed three-day window; the control arm
and pipeline-validation run), `base_min` / `base_guided` (guidance-axis
endpoints), `base_notools` (tool-axis floor; legacy `tools` is the ceiling),
and `base_full` (full-archive flagship). Each is a `task_base_*.json` +
`prompt_base_*.md` pair with a machine-checkable output contract. The runner
accepts any of them via `VARIANT=<name> bash run.sh`.

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
runs/<name>/   # any packaged base variant (see VARIANTS.md)
```

Use `bash run.sh` for the baseline or `VARIANT=<name> bash run.sh` for any
packaged variant. `AGENT=claude bash run.sh` runs the same variants through
the Claude Code CLI instead of Codex; it authenticates from
`SeismoAgentBench/configs/agents/claude.env` (chmod 600, git-ignored;
`ANTHROPIC_BASE_URL` and `ANTHROPIC_AUTH_TOKEN`) — `CLAUDE_ENV_FILE`,
`CLAUDE_BIN`, `CLAUDE_MODEL`, `CLAUDE_MAX_TURNS` and `CLAUDE_EXTRA_PATH`
override the defaults. Override `RUN_ID` and `TIMEOUT` when needed.

`main.py` is a deterministic infrastructure baseline for checking task
execution and catalog generation. It is not a scientific detector, phase
picker, or location solution. The expert scientific workflow remains under
`expert/` and is not part of the Agent task interface.

Large waveform files, source catalogs and generated analysis products remain in
the external data store and are not copied into Git.
