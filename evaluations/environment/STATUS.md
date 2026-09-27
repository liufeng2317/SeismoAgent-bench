# Environment implementation record

## 2026-09-28 — input manifest contract defined

The input manifest now has a versioned JSON contract at `evaluations/schemas/input_manifest.schema.json` and an initial Ridgecrest instance at `evaluations/examples/ridgecrest_input_manifest.json`. JSON is the selected format; no YAML variant is maintained. The manifest uses logical entry IDs, absolute source paths, data kind and read-only declaration, with optional waveform metadata and SHA-256. File size does not select a different workflow.

## 2026-09-28 — unified manifest interface selected

Removed the conceptual `small-copy` versus `large-direct-read` split. All tasks now use one manifest of logical input entries. The current trusted backend resolves entries to approved original dtfs paths; a future isolated backend may materialize the same entries into `/input`. File size changes resource accounting only, not task, agent or scorer logic. README and ENVIRONMENT_MODEL now use this single contract.

## 2026-09-28 — canonical environment decision

The current operating model is now **trusted-development**. The canonical workflow is small-copy smoke tests or manifest-based direct reads for large data, followed by a separate trusted scorer. The agent runs as `bench-agent01` in a fresh managed work/output directory. No current workflow applies ACLs or Bubblewrap.

The earlier `run-access`, `run_ridgecrest_read.sh`, ACL transaction, chroot feasibility probes and Bubblewrap probe remain implementation evidence only. They are not the active Ridgecrest runner. The shared-mount limitations and sandbox boundary are now summarized in [README.md](README.md). The next implementation is the small ObsPy read task and its scorer; no more sandbox experiments are required before that.

## 2026-09-28 — environment model fixed for end-to-end development

Selected profile: **trusted-development**. The account runner, curated input bundle, fresh writable run directories, process cleanup and post-run scorer interface are the development path. The agent may still reach other readable project files; answer visibility is not guaranteed. Formal eligibility remains false.

`ENVIRONMENT_MODEL.md` now defines the boundaries, run lifecycle, data handling, runtime promotion path and the distinction between verified chroot capability and unavailable Bubblewrap/ACL isolation. The next implementation should build one small Ridgecrest task through agent output and an external scorer, using copied inputs rather than direct dtfs access. No further sandbox debugging is required before that workflow exists.

## 2026-09-27 — Bubblewrap probe found a platform-path assumption

The first root synthetic probe reached Bubblewrap but failed before starting Python because the script unconditionally requested `/lib64`, which does not exist on this aarch64 Ubuntu image. No real data or permissions were touched. The script now binds `/lib64` only when that directory exists. Root rerun is pending.

## 2026-09-27 — Bubblewrap installed; synthetic probe ready

Operator installed Ubuntu `bubblewrap 0.6.1` at `/usr/bin/bwrap`. Added `check_bwrap.py`, which uses only temporary synthetic files and tests a private user/pid/ipc/uts namespace, curated `/usr`/library visibility, read-only input, writable output and host-marker hiding. It does not bind Ridgecrest data, run an agent or modify project/data permissions. Local syntax check passed; root execution is pending.

## 2026-09-27 — fresh system Python execution passed (current status)

Operator supplied report `execution-root-check-9aaa64401155.json`, 03:53:14 UTC: `passed=true`, exit 0, empty stderr, all 14 runtime checks true and synthetic input unchanged. The new Python executable ran after chroot/UID dropping; XML, sqlite, compression, math and SSL imports passed. Staging used 37,479,495 bytes and 28 shared-library paths. No real data was used. This confirms the loader-permission fix in the actual root-run workflow.

No additional operator action is required for the completed capability checks. README now consolidates the current status and removes obsolete retry instructions from its entry section. Next bounded milestone: inspect the existing scientific runtime, then validate a curated runtime and small real input inside the execution root. Full waveform access, a reusable agent supervisor and model/scorer integration remain unimplemented. The probe is still development-only, not formal evaluation isolation. Historical pending/retry entries below are superseded by this result.

## 2026-09-27 — runtime loader permission bug fixed; root retry pending

Operator report `execution-root-check-a339194bfae8.json` failed with EACCES when executing `/usr/bin/python3`. Reproduced locally: staging copied `/lib/ld-linux-aarch64.so.1` with mode 0444; executing that staged loader also failed with errno 13. `shutil.copyfile` does not preserve executable mode, and the versioned interpreter filename did not match the `.so` suffix rule. This was a staging implementation bug, not evidence that chroot execution is forbidden.

Fixed staging to preserve source executable intent as read-only mode 0555 (otherwise 0444) for copied native dependencies. Added a regression that actually executes the staged loader with `--verify` against staged Python and checks runtime files remain non-writable and directories traversable. All **15 tests pass** under system Python. No real data or shared permissions were changed. Repeat the same `check_execution_root.py --account bench-agent01 --runtime` command; it creates a fresh unique report and fixture. Full root runtime acceptance remains pending.

## 2026-09-27 — execution-root feasibility passed; fresh Python execution next

Operator supplied successful report `execution-root-check-eb38e32c945a.json` at 03:48:52 UTC: all ten checks true, exit 0, unchanged synthetic input. Chroot, UID/GID/group dropping, no-new-privileges, synthetic input protection/output writing and host-marker hiding passed. This test preloaded Python and did not execute a runtime inside the new root.

Added `check_execution_root.py --runtime` as the next single operator action. It copies trusted system Python, standard-library files and the shared-library dependencies resolved from system binaries into a disposable local root; then chroots, drops privileges and execs `/usr/bin/python3` there. It checks XML, sqlite, compression, math, SSL library loading and input/output boundaries. No pip/conda packages, credentials, host configuration, mounts or real data are included. SSL import is not a network or certificate-store test. System Python is a stepping stone, not the scientific runtime.

Unprivileged staging verification passed: 37,479,474 bytes, 28 shared-library paths, no copied symlinks. Both child programs compile. Actual root runtime execution remains pending; reports are retained, temporary staged files removed. Prior syscall success does not establish complete agent isolation or large-data access.

## 2026-09-27 — failed trial finalized; execution-root probe ready

Operator supplied `ridgecrest-read-pilot-001/result.json`: `state=blocked_or_failed`, errno 95, a finished timestamp, empty shared temporary residue, and no reported cleanup error. Together with the earlier probe-stage traceback, this indicates no shared-path ACL application and no reported recovery requirement. Preserve this failed run; no account reinitialization or ACL recovery is indicated by the supplied evidence.

Prepared `check_execution_root.py`: a root-supervised disposable local fixture tests `chroot`, changing to `/`, dropping UID/GID/supplementary groups, no-new-privileges, synthetic input read-only access, output writing and hiding a synthetic host path. It shares manager locks and refuses pending recovery/active managed processes. Only temporary synthetic fixtures are removed; a root-only JSON report is retained in the managed slot. It installs nothing and changes no project/data permissions.

Syntax and CLI help checked; actual root execution pending. The child loads Python before chroot: a pass establishes syscall/permission feasibility only, not executable/runtime availability inside the new root, scientific tool support, large-data access or a hostile-code sandbox. The user-facing next step is this one probe, not a full environment build.

## 2026-09-27 — shared-filesystem ACL strategy blocked (current status)

The root real-data trial `ridgecrest-read-pilot-001` failed in `check_acl_filesystems`, at `acl_get_fd` on the disposable probe, with errno 95. Shared-path transaction preparation/application had not started. The root-only final result has not been inspected, so successful final cleanup is not claimed from the traceback alone.

Independent non-root probes on newly created disposable files reproduced the storage limitation:

| Location | Filesystem | Device | Native ACL read |
| --- | --- | --- | --- |
| Project `/liufeng1afs` | dtfs | 1048680 | unsupported, errno 95 |
| Data `/ai4earthafs` | dtfs | 1048660 | unsupported, errno 95 |
| Local `/tmp` | overlay | 1048687 | supported |

This is a filesystem/interface limitation, not a missing Python or ACL package. The earlier managed-root synthetic acceptance remains valid but does not extend to either shared mount. Real scientific inputs and project permissions were not modified by the failing ACL support probe. Probe evidence is in ignored `local/filesystem-acl-check.json`.

Stopped the local real-data launcher with an explicit diagnostic. The manager now includes probe path/device in unsupported-ACL errors and, for future failures before shared journal creation, records `acl_state=not_applied` and verifies baseline access where available. Existing historical results are not rewritten. All 14 regression tests pass.

Do not retry under another run ID, install ACL packages as a fix, fall back to broad chmod, or drop private-answer checks. The account-only development runner cannot currently protect the readable project on these mounts. Next design checkpoint: test whether a curated local execution root (for example chroot with privilege dropping) is feasible under this container's actual capabilities, including runtime dependencies and large-data access. This is a candidate, not an implemented or validated sandbox. No agent trial should run before an effective private-data boundary is demonstrated.

All entries below are historical; prior statements that the real-data launcher is ready are superseded by this storage result.

## 2026-09-27 — real private-path disclosure confirmed; temporary restriction prepared

Operator preflight at 03:34:04 UTC confirmed all four selected inputs readable/non-writable, but both private directories and both actual catalog files readable by `bench-agent01`. Current policy therefore failed. No agent was launched.

Added optional `restrict_roots` to the access configuration: named-UID `---` on explicit directory roots, journaled/restored by the same ACL transaction as grants. Restrictions reject public-grant/managed-state overlap and are checked for lack of read/write/traverse access before command launch. Other principals' ACL entries are preserved. Regression suite: **14 tests passed**, including directory restriction restoration and overlap rejection. Actual cross-UID restriction is still root-pending.

The local Ridgecrest configuration restricts the entire physical project root during the trial, covering its expert files, reference files, docs and Git history through that path. The small public bundle is copied into the managed run before restriction. No original waveform data is copied. Local `run_ridgecrest_read.sh` runs a stdlib-only read of three MiniSEED headers and StationXML, with ACL probes on the two affected filesystem devices. Header identifiers and CI.CCC presence in StationXML were independently checked as the development owner; this is not target-UID acceptance. A disposable `.evaluation_acl_probe` directory was created alongside the external case waveforms for filesystem probing; no scientific file permissions changed.

Pending: root execution of this prepared trial and verification of `completed`, `acl_state=restored`, `baseline_access_restored=true`. The project becomes readable again after restoration by design. Known or unknown answer copies outside this project, network access and full scientific runtime validation remain outside this trial's guarantee.

## 2026-09-27 — real-data scope prepared; private-path preflight pending

Prepared ignored `local/ridgecrest-access.json` and `local/ridgecrest-access-plan.json`: CI.CCC HHE/HHN/HHZ for 2019-07-04 plus the physical StationXML, four files totaling 94,228,026 bytes. Scope preview passed; files were not copied or modified. Expert stage-52 working catalog and Liu Table S1 (and their parent roots) are explicit deny checks.

The selected answer files have other-readable mode bits. This suggests a possible disclosure through traversable ancestors, not proof of effective UID access. Added root-only `preflight-access` to report actual managed-UID current read/write checks without ACL mutation or content reads; it exits 1 if any condition fails. Root output is required before the real trial. The development session cannot use passwordless sudo. No data ACL support claim, agent run or real-data acceptance is made yet. See the current real-data preflight command in [README](README.md).

## 2026-09-27 — root synthetic acceptance passed

Evidence: the operator supplied the complete root-shell output of `init --account bench-agent01` and `smoke-access --account bench-agent01`. Account creation succeeded and the final `Root ACL smoke passed` line was present. This entry records operator-provided output; the root-only artifacts have not been independently inspected from the development account.

| Run ID | Expected and observed state | ACL state | Baseline access restored | Shared temporary residue |
| --- | --- | --- | --- | --- |
| `acl-smoke-9b563eb693ab-normal` | `completed`, exit 0 | `restored` | true | none |
| `acl-smoke-9b563eb693ab-failure` | `command_failed`, intentional exit 7 | `restored` | true | none |
| `acl-smoke-9b563eb693ab-timeout` | `timeout`, intentional 1-second limit | `restored` | true | none |

The synthetic acceptance verifies cross-UID input read access without write access, tool execution, private-answer denial, previous-output denial and restoration on completion, failure and timeout. Retained runs are under `/var/lib/seismoagentbench/slots/bench-agent01/runs/`; do not repeat account initialization.

Next bounded milestone: prepare one small real-data trial with explicit waveform/station files and private-answer paths, preview its scope, then validate ACL support on the affected filesystems and read the selected inputs under the managed UID. Real scientific-data permissions, scientific runtime usability and real expert/reference denial remain unverified. No agent or scientific workflow has run. The profile remains **development-account**, with `formal_evaluation_eligible=false`.

The entries below are historical implementation checkpoints, not the current acceptance status.

## 2026-09-27 — ACL transactions implemented; root acceptance pending

Implemented `acl_transaction.py` (native libacl, pinned no-symlink file descriptors, durable atomic journals, pre-syscall intent, mask refusal, exact verified restoration and conflict detection). Added `run-access`, `recover-access`, global serial locking, unfinished-journal blocking, per-filesystem disposable support probes, UID access baseline/after records and managed-process teardown before restore. `smoke-access` provides normal/failure/timeout acceptance using only synthetic files.

Verified under the current unprivileged file-owner account: **12 tests pass**, including real ACL syscalls, existing/absent named entries, mode restoration, partial failure after mutation, abrupt subprocess exit before a journal update, mask rejection, unsupported-ACL failure, concurrent ACL change and inode replacement. These are not mocked root acceptance results. No real source-data ACLs were changed.

`sudo -n true` still requires a password. Actual dedicated-account creation, cross-UID access and real input filesystem support are unverified. Root user action is limited to:

```bash
cd /liufeng1afs/project/03_LLM/Science_Discovery_Agenet/SeismoAgentBench
/usr/bin/python3 evaluations/environment/manage.py init --account bench-agent01
/usr/bin/python3 evaluations/environment/manage.py smoke-access --account bench-agent01
```

If the account was already correctly initialized, skip init. The final smoke success line is required; intentional command failure/timeout are part of the test. Preserve failures and logs, do not grant broad permissions manually. See the root-action section of [README](README.md).


## 2026-09-27 — per-trial access development design selected

User decision: proceed with a simple local development environment, temporarily grant explicit input/tool access and use a fresh managed writable workspace; defer external workers. [ACCESS_DESIGN.md](ACCESS_DESIGN.md) is the current next-step design. The earlier formal-backend review remains valid for future benchmark claims, but does not block development work.

Implemented now: `access.example.json`, read-only `plan-access` scope expansion, private/grant-overlap and symlink rejection, ancestor traversal candidates, planned workspace and explicit not-applied flags. Existing `run` now rejects unknown permission-policy fields instead of silently ignoring proposed grants. Five unprivileged regression tests passed; no real ACL or account was changed.

Next implementation: journaled ACL application and conservative restoration, tested on disposable fixtures with actual UIDs before real source data. Real filesystem ACL support, root smoke and target-user access remain unverified. Network/cgroup isolation and agent integration remain deferred. The preview is not permission enforcement.


## 2026-09-27 — architecture review supersedes the initial rollout plan

Decision: retain `manage.py` as **development-only**, not the formal benchmark backend. The prior recommendation to proceed directly with account setup is superseded; account expansion is paused. See [review, sources and acceptance criteria](ARCHITECTURE_REVIEW.md). Future manager reports explicitly contain `execution_profile=development-account` and `formal_evaluation_eligible=false`. These labels do not upgrade earlier logs or imply a validated alternative backend.

Next: confirm an externally managed fresh worker (sibling container or remote worker) and define one portable task/scorer. No such service has been provisioned; root account/smoke validation remains unexecuted.


## 2026-09-27 — initial account-isolation implementation

Observed host: Ubuntu 22.04.5, aarch64, current user UID 1000; virtualization detector reports Docker. User/PID/network namespace creation probes succeeded, but mount propagation and private tmpfs mounting failed. User systemd bus is unavailable. These observations do not prove full namespace isolation.

Available management commands: useradd, runuser, setfacl and prlimit. Current session `sudo -n` requires a password. No passwords requested or stored. No account, source-data permission or system configuration was changed.

Delivered:

- Standard-library root manager with dedicated-account creation, serial locking, curated public copies, UID-based access checks, clean per-run directories/environment, timeout/process cleanup and sealed outputs.
- Synthetic two-run smoke command to test read-only public input, private-answer denial and previous-run denial.
- Explicit local policy template and runbook; no broad project ACL changes or automatic source deletion.
- Three unprivileged regression tests passed. Local doctor report is ignored by Git.

Not yet verified: actual root account creation; cross-user smoke; real source/reference ACL denial; runtime usability under the new UID; access beyond the explicit policy paths; shared filesystem ACL behavior; aggregate cgroups, network restriction, agent/model gateway and scientific scoring. No formal benchmark was launched.

Optional development-only commands from the initial plan (not formal rollout):

```bash
sudo /usr/bin/python3 evaluations/environment/manage.py init --account bench-agent01
sudo /usr/bin/python3 evaluations/environment/manage.py smoke --account bench-agent01
```

If those optional development checks are used, review the real permission policy before any local non-agent command; passing does not establish formal readiness. Record the managed run IDs and results here before introducing an agent. Preserve failures as evidence; do not replace this pending status with a claim of successful isolation based only on unit tests.
