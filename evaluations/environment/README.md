# SeismoAgentBench evaluation environment

## Current decision

The current host uses **trusted-development** mode. It is intended to run one complete task/agent/scorer workflow while the sandbox backend is unavailable. It is **not** a formal adversarial evaluation environment.

Every development report must contain:

```json
{
  "execution_profile": "trusted-development",
  "formal_evaluation_eligible": false,
  "answer_visibility_protection": "not_guaranteed"
}
```

Do not use the old ACL launcher or the Bubblewrap probe for current task execution. ACLs are unsupported on the project/data dtfs mounts, and Bubblewrap cannot create the required mount namespace inside this outer Docker worker.

## The one current workflow

```text
1. Select a task and a small public input manifest.
2. Copy small smoke-test inputs into the run's input/ directory.
3. Start the agent as bench-agent01.
4. Run the agent in its work/ directory.
5. Save output/, logs, exit status and environment metadata.
6. Run the trusted scorer after the agent exits.
7. Save score/score.json and the provenance record.
```

The agent always receives an input manifest. The manifest is the single task/data interface regardless of file size. Its contract is defined by [input_manifest.schema.json](../schemas/input_manifest.schema.json), and the initial Ridgecrest instance is [ridgecrest_input_manifest.json](../examples/ridgecrest_input_manifest.json). In the current trusted-development backend, entries point to approved original paths under `/ai4earthafs`; the agent reads them without copying gigabytes for every run. This is a procedural allowlist only and does not prevent the agent from reading other world-readable paths.

## Run layout

The root supervisor creates:

```text
/var/lib/seismoagentbench/slots/bench-agent01/runs/<run-id>/
  input/       # optional materialized view of manifest entries, read-only
  work/        # agent current directory, writable
  output/      # agent products, writable
  home/        # temporary HOME, writable
  tmp/         # temporary files, writable
  execution.log
  result.json
  manifest.json
  score/       # trusted scorer output, created after agent exit
```

The agent runs as `bench-agent01`, with `work/` as its current directory and these variables:

```text
BENCH_INPUT
BENCH_WORK
BENCH_OUTPUT
```

The agent writes products such as `output/catalog.json`. The scorer is a separate trusted command. It starts after the agent exits, reads the agent output and private reference data, and writes `score/score.json`. The scorer is not put in `input/` and is not part of the agent command.

## Data policy

Use one input contract:

```json
{
  "case": "2019_ridgecrest_california",
  "entries": [
    {
      "id": "CI.CCC.HHZ.20190704",
      "path": "/ai4earthafs/liufeng/ScienceDiscovery/SeismoAgentBench/data/2019_ridgecrest_california/waveforms/data/CI.CCC/CI.CCC..HHZ__20190704T000000Z__20190705T000000Z.mseed",
      "kind": "waveform",
      "read_only": true
    }
  ]
}
```

The agent consumes logical entry IDs and paths from this manifest. A future isolated backend may remap the same entries into `/input`, but the task, agent interface and scorer do not change. File size affects resource accounting only; it does not select a different workflow. The original data is never modified. Do not use recursive `chmod`, `chown`, temporary ACLs or whole-project copies. A symlink to an external path does not create isolation.

The first Ridgecrest task uses one StationXML file and three CI.CCC MiniSEED files through exactly this manifest interface. It can later be expanded to the complete waveform set by changing the manifest entries only.

## Runtime policy

Do not create a Conda environment for every evaluation user. First inspect and freeze the existing `seismoagent` environment. The agent may use that approved runtime in development mode. If package installation is needed, use a separate trial environment or snapshot so the baseline is not modified; record `conda list --explicit` and `pip freeze` before and after the run.

The verified chroot tests prove only that basic Python can run after a root change and UID drop. They do not validate ObsPy, PhaseNet, GaMMA, NonLinLoc or HypoDD inside an isolated root. The next scientific check is a small ObsPy MiniSEED/StationXML read.

## What the current runner provides

- dedicated non-root account;
- fresh run directories;
- curated small input bundles;
- sanitized environment variables;
- wall-clock timeout;
- process-group cleanup;
- retained logs and run metadata;
- separate post-run scoring interface.

## What it does not provide

- guaranteed hiding of expert/reference files;
- network isolation;
- kernel or mount isolation;
- aggregate CPU, memory or PID quotas;
- protection against a deliberately hostile agent;
- formal benchmark eligibility.

## Formal evaluation boundary

Formal evaluation requires a worker with a functioning isolation backend, such as an externally managed container/VM or a worker where mount namespaces and resource controls are available. The task manifest, agent entry point, scorer and provenance schema developed here should be reused there; only the execution backend changes.

## Current evidence

See [ENVIRONMENT_MODEL.md](ENVIRONMENT_MODEL.md) for the detailed model and [STATUS.md](STATUS.md) for verification evidence and historical experiments. The current status is:

- dedicated account: passed;
- synthetic account lifecycle: passed;
- chroot capability probe: passed;
- fresh system Python in chroot: passed;
- dtfs POSIX ACL: unsupported;
- Bubblewrap mount sandbox: blocked by outer Docker;
- scientific runtime smoke: pending;
- end-to-end agent/scorer task: pending.
