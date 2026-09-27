# Evaluation environment architecture review

Reviewed: 2026-09-27. Scope: the local account manager and the intended arbitrary-code seismic agent evaluation. This is a design review, not evidence that a production executor has been deployed.

Current user-selected development track: [per-trial account access](ACCESS_DESIGN.md). The recommendations below concern formal evaluation; provisioning an external worker is deferred while the local prototype is designed.

## Decision

**Do not adopt `manage.py` as the formal benchmark harness or isolation backend.** Retain it as a development-only account/permission utility. Its successful command/smoke results are not publishable scientific evaluation results or certification of isolation. Do not expand an account pool as the next infrastructure step.

Use versioned, backend-independent tasks and a maintained evaluation harness, with an explicitly selected fresh executor per trial. Harbor is the preferred first integration for terminal/code tasks; Inspect is an alternative if the existing TRACE agent integration is substantially easier there. Neither is installed or integrated by this review. Choose one after a single end-to-end task/adapter proof, not both at once.

There is no universal conference rule requiring Docker or a particular harness. The recommendation is based on the inspected benchmarks below and on the requirements of this project's arbitrary Python/shell access. Restricted function-call benchmarks can use different execution designs. Containerization alone also does not prove data isolation, reproducibility or scientific validity.

## Primary-source evidence

- [SWE-bench harness](https://www.swebench.com/SWE-bench/reference/harness/): Docker-based environments for applying patches and running tests. This describes its evaluation harness, not necessarily every agent's development process.
- [AstaBench setup](https://github.com/allenai/asta-bench#setup): the general framework may be installed without Docker, but its sandboxed code-execution tasks still require a supported sandbox. The README describes custom sandbox integration through Inspect; non-Docker installation is not equivalent to no execution isolation.
- [Inspect sandboxing](https://inspect.aisi.org.uk/sandboxing.html): per-sample execution environments and configurable resource management, separate from the agent/model layer.
- [Harbor task format](https://docs.harborframework.com/core-concepts/tasks/overview): instruction, environment specification, reference solution and verifier; independent, isolated and versioned tasks. A backend-supported specification is required; a task-format example does not establish that our current server supports it.
- [Terminal-Bench-Science execution](https://github.com/harbor-framework/terminal-bench-science#running-the-benchmark): run reference solutions to check the executor before agent trials; supports external execution through Harbor. Its use of an external provider illustrates that the controller need not run nested Docker locally.

These sources establish implementation patterns, not a claim that every top-conference benchmark uses identical isolation or scoring.

## Audit of the current code

| Requirement for this project | Actual implementation | Assessment |
| --- | --- | --- |
| Restricted filesystem view | `probe()` checks only named allow/deny paths using target-UID access; other readable host paths remain available | Not a filesystem allowlist; possible expert/reference leakage through unlisted paths |
| Fresh complete trial state | New HOME/work/tmp/output; `outside_files()` scans only three temporary roots | Useful partial reset; cannot prove absence of other persistent state or network-side artifacts |
| Frozen executable environment | Absolute host executable paths and a public bundle copy | No immutable full runtime, build digest or content-addressed input manifest in run records |
| Hard resource budgets | Wall timeout, FD limit, core-dump disable and thread environment defaults | No aggregate CPU/memory/PID/disk quotas; environment variables can be overridden |
| Process lifecycle | Managed-UID scan and SIGKILL after the initial process group | Best effort; no cgroup-scoped atomic teardown or verification that every descendant has stopped |
| Network/model boundary | Host network inherited; parent secrets not inherited | No controlled egress, model gateway or accounting of remote capabilities |
| Grading boundary | Access-probe inputs and documentation propose a separate scorer | Scientific grader not implemented; no frozen reference/metric contract |
| Agent reproducibility | Command, timestamps, exit status and stdout log | Missing model/scaffold/prompt identity, tool-call trajectory, model usage and run-attempt protocol |
| Root/admin robustness | Small custom privileged script, minimal tests | Actual root smoke unexecuted; not an audited general-purpose sandbox |

Additionally, bundle filtering is a pre-copy check, not a content review or a defense against concurrent source replacement. Directory read checks do not recursively establish child-file permissions. These limitations should not be repaired indefinitely by adding ad hoc checks to this manager.

## Recommended deployment without Docker-in-Docker

```text
Current development container: trusted evaluation controller
    task/prompt versions, orchestration, model accounting, private scorer
                          |
              restricted execution service
                          |
    fresh per-trial worker on an external platform
    versioned runtime + permitted read-only observations/tools/docs
    new writable workspace + enforced resource/network policy
                          |
               collect declared output artifacts
                          |
           private deterministic scientific grading
```

Preferred backend: the existing server/platform administrator starts a clean sibling container per trial **outside** the current container. An independent remote VM/worker is an alternative if the platform cannot do this. These require external platform capability; neither is assumed available yet. Do not mount a host Docker socket into agent-accessible execution or make the agent a Docker administrator.

For large waveform data, expose only the approved case/time selection read-only, on a data-local worker where possible. Do not mount the whole shared project or expert directory. Account permissions remain useful inside the worker but do not replace worker reset. RAG and provider-side tools must obey the same information policy as shell access.

If no fresh managed executor is available, continue developing task schemas, scoring and tiny command tests locally. Label those development trials and do not silently relax the formal-run requirements. A future non-container backend may qualify by demonstrating equivalent controls; Docker itself is not the requirement.

## Stable contract before backend implementation

Keep five artifacts independent of host usernames and account-manager paths:

1. **Task**: immutable instruction, input schema, output schema, permitted tools/docs and scientific scope.
2. **Environment**: exact build recipe/runtime identity, tool/weight identities and permitted data manifests; architecture stated explicitly.
3. **Trial**: task/environment/agent/model/prompt versions, all resource and model budgets, repeat index, network/document condition and timestamps.
4. **Artifacts**: agent trajectory, commands/errors, result files, resource/model usage and provenance; secrets excluded.
5. **Scoring**: private references, versioned deterministic metrics, rejection conditions and treatment of missing/failed events; no reference-score feedback during a held-out attempt.

Suggested task layout follows Harbor (`instruction.md`, `task.toml`, `environment/`, `solution/`, `tests/`). Solutions and verifiers belong to the controller-side task package; the entire directory must not automatically be mounted into the agent worker. These paths are an architecture proposal, not already-created runnable tasks.

## Go/no-go acceptance before formal agent runs

- Rebuild one environment from its pinned specification and record its identity and architecture.
- Run a known feasible reference implementation on the selected input subset, then check that deliberately invalid outputs fail verification.
- From agent code, verify approved input readability, input immutability and inaccessibility of private answers, grader and other trial state.
- Verify clean restart and teardown including detached processes, caches and persistent writable volumes.
- Exercise enforced CPU/memory/PID/disk/time policies and record failure classification without destabilizing unrelated jobs.
- Verify network/provider-tool policy and retain complete model/tool usage records.
- Repeat the reference run, distinguish expected numerical tolerance from environment failure, then run repeated agent trials under a fixed configuration.

This checklist is specific to our intended benchmark contract, not an asserted universal conference standard. None of these full-backend acceptance checks has been passed by the existing unprivileged regression tests.

## Immediate next step

Determine whether the outer platform can launch a disposable sibling worker with data-local read-only inputs, or whether a remote worker must be used. In parallel, specify one small Ridgecrest task and its private scorer in a backend-independent format. Do not spend the next phase implementing more user-account isolation machinery.
