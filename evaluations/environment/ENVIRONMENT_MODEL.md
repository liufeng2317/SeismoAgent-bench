# Evaluation environment model

## Selected profile

The current host uses **trusted-development** mode. It is an end-to-end development runner, not a formal adversarial benchmark sandbox.

```text
root supervisor
  ├── prepares a curated public task bundle
  ├── creates /var/lib/seismoagentbench/slots/bench-agent01/runs/<run-id>
  ├── starts the command as bench-agent01
  ├── applies timeout and process cleanup
  ├── retains logs and output
  └── runs the scorer separately after the agent exits
```

The profile is explicitly recorded as:

```json
{
  "execution_profile": "trusted-development",
  "formal_evaluation_eligible": false,
  "answer_visibility_protection": "not_guaranteed"
}
```

This is an intentional temporary operating point. It allows the scientific workflow and scorer interfaces to be developed without claiming that a potentially hostile agent is isolated from the host.

## What is isolated now

`bench-agent01` has no supplementary groups and is never used as root. Each run gets a fresh managed directory:

```text
/var/lib/seismoagentbench/slots/bench-agent01/runs/<run-id>/
  input/       # curated public copy, read-only to the agent
  work/        # writable by the agent
  output/      # writable by the agent
  home/        # writable by the agent
  tmp/         # writable temporary area
  result.json
  execution.log
```

The supervisor sanitizes the environment, starts from `work/`, limits the wall time, kills the process group and records the exit state. Input bundles reject links, special files and obvious private names.

The system-Python chroot probe also passed, but it is only a capability result. The Bubblewrap probe is blocked by the outer Docker mount restrictions. Neither result upgrades the current profile to formal isolation.

## What is deliberately outside the current guarantee

- The dtfs project and data mounts do not support the POSIX ACL interface used for temporary per-user grants.
- The development account may be able to read other world-readable project files, including expert/reference files.
- Network and kernel resources are shared.
- CPU, memory and process quotas are not aggregate-enforced.
- Agent package installation policy is not yet fixed.
- The scientific Conda environment has not been staged and validated inside the execution root.
- The scorer and model gateway are not security-separated services.

Consequently, a development result must not be used as a formal benchmark score.

## Data and answer handling

For every end-to-end Ridgecrest task, create one JSON input manifest. Its contract is [input_manifest.schema.json](../schemas/input_manifest.schema.json), and the initial instance is [ridgecrest_input_manifest.json](../examples/ridgecrest_input_manifest.json). The manifest is the stable interface; it does not change when the number or size of files changes. In the current trusted-development backend, entries point to approved original `/ai4earthafs` paths so multi-GB waveform data is not copied for every run. The first manifest contains one StationXML file and three CI.CCC MiniSEED files:

```text
/var/lib/seismoagentbench/slots/bench-agent01/runs/<run-id>/input/
  earthscope.stationxml
  CI.CCC..HHE__20190704T000000Z__20190705T000000Z.mseed
  CI.CCC..HHN__20190704T000000Z__20190705T000000Z.mseed
  CI.CCC..HHZ__20190704T000000Z__20190705T000000Z.mseed
```

The original dtfs data remains unchanged. The agent receives the manifest through `BENCH_INPUT_MANIFEST` and reads only the listed entries as part of the trusted workflow. A future isolated backend can materialize those same entries into an `input/` directory without changing the manifest schema or agent/scorer logic.

The agent runs as `bench-agent01` with current directory:

```text
/var/lib/seismoagentbench/slots/bench-agent01/runs/<run-id>/work/
```

It can write only its managed `work/`, `output/`, `home/` and `tmp/` areas as configured by the runner. Its expected product is a small result file such as:

```text
output/catalog.json
```

The **scorer** is a separate trusted program. It starts only after the agent exits, and reads `output/catalog.json` together with private reference data. For the first smoke task it checks that the agent reported the expected station, three components, time interval, sample counts and valid JSON. It then writes:

```text
score/score.json
```

The scorer is not part of the agent command and is not copied into `input/`. In trusted-development mode, the separation is procedural rather than a guaranteed security boundary because the host filesystem is shared. The report must retain this limitation.

## Runtime handling

Do not create a separate Conda environment for every test user. First freeze and inspect the existing `seismoagent` environment. For a development run it may be used as the approved command runtime. When the scientific smoke task is stable, create one immutable baseline runtime snapshot and a separate writable trial environment if agent package installation is required.

The immediate runtime test is limited to ObsPy reading a small MiniSEED/StationXML bundle. PhaseNet, GaMMA, NonLinLoc and HypoDD are added only after this basic interface succeeds.

## Run lifecycle

```text
1. prepare task bundle and task metadata
2. create fresh run directories
3. start the agent as bench-agent01
4. capture stdout/stderr, exit code and timeout state
5. seal the agent output
6. run the scorer outside the agent command
7. save score, provenance and environment manifest
8. retain the run record; remove only disposable work material by policy
```

## Promotion boundary

The trusted-development profile can be promoted only after a real isolation backend is available: an externally configured worker, a container with working mount namespaces, or another administrator-approved boundary. At that point the same task bundle, agent entry point, scorer and provenance records should be reused; only the execution backend changes.
