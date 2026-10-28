# Ridgecrest earthquake-catalog task

This directory is the complete runnable task package for the 2019 Ridgecrest
catalog-construction case. Its public task interface consists of the task
definitions, prompts, input declaration and runner:

```text
input.json        # read-only source folder declaration
task_min.json     # Q1 control arm: minimal instructions
task_tools.json   # Q2 arm: control + local expert tools
task_guided.json  # Q3 arm: control + expert scaffolding
prompt_min.md     # minimal-instruction prompt and output schema
prompt_tools.md   # prompt with local seismological tools exposed
prompt_guided.md  # prompt with expert workflow scaffolding
run.sh            # agent entry point; select VARIANT=min|tools|guided
```

The three variants form a minimal single-factor experiment around the
research questions (see `VARIANTS.md`): whether a general-purpose agent can
reach expert-level results on its own (`min`, scored against the `expert/`
workflow reference), whether expert tools matter (`tools` vs `min`), and
whether expert experience matters (`guided` vs `min`). A fourth arm for the
feedback-loop question (`ris`) will be added when its design is settled.
Retired variants live under `attic/`.

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
limitations are described in each variant prompt and enforced by the
machine-checkable output contracts (`output_contract_min.json`,
`output_contract.json`). `prompt_tools.md` exposes the local seismotools library — PhaseNet;
GaMMA, PyOcto and REAL (association); NonLinLoc and HypoInverse (absolute
location); hypoDD, GrowClust and ccdt (relative relocation); Match&Locate
(template matching) — while leaving
method selection to the Agent. Each run records the seismotools commit in
its provenance (`tools`).
Runs before 2026-10-27 used the earlier tools prompt, which listed only
PhaseNet, GaMMA, NonLinLoc and hypoDD. Match&Locate was added on 2026-10-28.

The runner's wall-clock budget defaults to twenty-four hours (`tools`
forty-eight, because its science stages alone ran ~18 h in the first
completed run). Override with `TIMEOUT`, in seconds, when a different
processing budget is needed; the budget is also rendered into the agent's
runtime context so the agent can plan against the deadline.

By default `run.sh` starts the runner detached in its own session
(`setsid`), so closing the launching terminal cannot kill a multi-hour run;
the runner log lands next to the run tree as
`runs/<variant>/<harness>/<model>/runner-<RUN_ID>.log` and live events keep
streaming to `<run>/record/execution.log`. Set `DETACH=0` for the previous
attached, streaming behavior. Two probes close the observability gap:

```bash
# periodic status probe (state, elapsed, idle seconds, artifact presence)
/liufeng1afs/software/miniconda3/envs/seismoagent_eval/bin/python -m SeismoAgentBench status --run-dir <run>
# forensic closure when a runner died without writing a final state
/liufeng1afs/software/miniconda3/envs/seismoagent_eval/bin/python -m SeismoAgentBench finalize --run-dir <run>
```

Run outputs are separated by experiment factor, one factor per path segment:

```text
runs/<variant>/<harness>/<model>/<timestamp>/
# e.g. runs/min/claude/glm-5.3/20260113T093000Z/
```

The timestamp leaf is one attempt of that configuration (override `RUN_ID`
for a custom leaf name). The model segment defaults to the agent config's
`model` line; `CLAUDE_MODEL` / `CODEX_MODEL` override it and are passed to
the CLI as `--model`.

`bash run.sh` runs the default `min` variant; `VARIANT=<name> bash run.sh`
selects any packaged variant. The Agent is Claude Code by default
(`AGENT=codex bash run.sh` selects Codex); Claude authenticates from
`SeismoAgentBench/configs/agents/claude.env` (chmod 600, git-ignored;
`ANTHROPIC_BASE_URL` and `ANTHROPIC_AUTH_TOKEN`) — `CLAUDE_ENV_FILE`,
`CLAUDE_BIN`, `CLAUDE_MODEL`, `CLAUDE_MAX_TURNS` and `CLAUDE_EXTRA_PATH`
override the defaults. Override `RUN_ID` and `TIMEOUT` when needed.

`attic/main.py` is the retired deterministic infrastructure baseline that
exercised task execution and catalog generation without an agent. The expert
scientific workflow remains under `expert/` and is not part of the Agent task
interface.

Large waveform files, source catalogs and generated analysis products remain in
the external data store and are not copied into Git.
