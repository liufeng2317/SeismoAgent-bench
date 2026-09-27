# Per-trial access design for local development tests

Decision date: 2026-09-27. This is the selected **near-term development workflow**, following the request to avoid provisioning external workers for now. The formal-evaluation limitations in [the architecture review](ARCHITECTURE_REVIEW.md) remain; an external executor is not a prerequisite for developing this local workflow.

## Access contract

One dedicated account, one active trial, one managed workspace. Do not use the project owner's account. The root supervisor controls permissions and records; the agent runs without root or supplementary groups.

| Resource | Intended target-account access | Lifetime |
| --- | --- | --- |
| Explicit waveform/station/model input files | `r--` | Temporary named-user access ACL |
| Explicit input directories | `r-x`; descendants only when explicitly selected | Same |
| Approved tool/runtime files | `r--`, plus `x` only on files already executable | Fixed approved access or temporary named-user ACL |
| Ancestors needed to reach a selected path | `--x` only where effective traversal is missing | Temporary if needed; no recursive ancestor grant |
| Managed `work/`, `output/`, `home/`, `tmp/` | Read/write/traverse; owned by the slot UID | Active run only |
| Private answers, expert results, grader and old runs | Inaccessible | Pre-existing protection checked before launch |
| Controller policies, ACL journal, logs and status | Root-controlled | Retained for review/recovery |

The supervisor selects `cwd=work/`; cwd is not a filesystem restriction. Data remains at its real absolute path. Large waveform files are not copied, linked to broaden scope, or changed in ownership. Small task instructions and allowed documentation may use the existing curated bundle copy.

Native ACL writes use `acl_set_fd` on file descriptors opened without symlink traversal. Numeric access ACLs are journaled; a matching full before-state is restored only if the current ACL is exactly the expected after-state (or already restored). No unsupported-filesystem chmod fallback is used.

Use a stable default workspace root `/var/lib/seismoagentbench/slots/<account>/runs/<run_id>`. A run ID selects a new directory; callers cannot choose an arbitrary existing writable directory. This keeps cleanup and result sealing bounded. Additional storage roots can be a later administrator-configured feature, not an unrestricted agent argument.

## Configuration and preview available now

Copy [access.example.json](access.example.json) to ignored `local/access.json`. Replace placeholders with existing **canonical physical paths**. List files individually for a narrow time window; use `recursive: true` only for a deliberately curated subtree. Recursive scopes include every existing file and directory, so do not point them at the entire project or the mixed tool/document snapshot.

```bash
mkdir -p evaluations/environment/local
python3 evaluations/environment/manage.py plan-access \
  --config evaluations/environment/local/access.json \
  --output evaluations/environment/local/access-plan.json
```

This standard-library command requires no root. It expands the explicit file scope, records device/inode identities, distinguishes read from execute permissions, lists ancestor traversal candidates and computes the managed workspace path. It rejects grant/private-scope overlap, links/special files, overly broad filesystem roots and invalid account/run names. It reads directory metadata, not waveform contents.

**The preview does not grant access.** It does not establish target-UID permissions, ACL support or mask safety. Its report explicitly sets `permissions_modified=false`, `acl_application_implemented=true` and `formal_evaluation_eligible=false`. If the current caller cannot enumerate a selected subtree, planning fails rather than silently omitting files. Files added or replaced after planning invalidate the eventual application manifest; the application phase must revalidate.

The existing `policy.example.json` is a different, already-supported interface: it audits `allow_read` and `deny_read` without changing permissions. `run` rejects unknown policy fields, so a temporary-grant configuration cannot be silently mistaken for applied access. The current `run` command still requires permissions to exist beforehand.

## Implemented execution transaction

Implemented by `manage.py run-access` and `acl_transaction.py`. Temporary-file ACL tests pass; root cross-user and real shared-storage validation remain pending.

1. **Lock and inspect.** Acquire a global ACL transaction lock plus the account lock. Keep one local trial at a time in version 1. Refuse active UID processes, unresolved recovery journals and known shared temporary residue. Confirm the account does not own shared input/tool paths; owner permissions take precedence over a named-user ACL.
2. **Plan exact targets.** Revalidate canonical paths, types, device/inode identities and private-scope separation. Reject unexpected symlinks, replacements and new files. Determine the minimum missing ancestor traversal rights using checks under the actual UID.
3. **Snapshot before modification.** Record numeric access/default ACLs, owner, group, mode, device/inode and prior effective UID access for every affected path. Write a root-only recovery journal before the first change. Default ACLs and ownership are not modified.
4. **Check ACL behavior.** Verify POSIX ACL support on disposable fixtures on each relevant filesystem first. If unsupported or root-squashed, do not fall back to chmod. Determine how a named-user entry interacts with the ACL mask before applying it.
5. **Apply minimal access.** Set only the dedicated UID's access entry (`r--`, `r-x` or `--x`). Never add write permission to shared inputs/tools. Preserve an existing named entry for later restoration. Do not automatically widen a shared ACL mask: if the required rights cannot be effective without affecting other principals, stop and use an administrator-prepared public staging area or separately reviewed policy.
6. **Audit before launch.** Under the real UID, check every selected input is readable/non-writable, required binaries executable, workspace writable, known private files inaccessible and old runs inaccessible. Include traverse checks; directory listing denial alone does not protect files with known names. Failure rolls back without launching the command.
7. **Run and record.** Use fresh HOME/TMPDIR/cache/work/output, a sanitized environment, recorded command and timeout. No inherited provider keys. Keep the development-only designation and existing limitations.
8. **Stop and restore.** Terminate the trial's remaining processes and verify teardown before account reuse. Seal the root-owned run parent. Restore only journaled permission changes, checking identity and expected post-change ACL before each restoration. Record the final ACL/access checks and preserve artifacts.

Suggested journal states: `planned → applying → active → restoring → restored`, with `recovery_required` for any unresolved restoration or identity conflict. Per-path state must be durable enough to recover partial application. A SIGKILL or host failure cannot be handled by `finally`; startup must detect an unfinished journal and block reuse until explicit recovery succeeds.

The recovery interface is `recover-access --account bench-agent01 --id RUN_ID`. There is no general `chmod -R`, `chown -R`, `setfacl -b`, or automatic deletion of data in this design.

## Restoration semantics

Restoration means returning to the original ACL/access state, **not promising that the data becomes unreadable**. If the UID could already read a world-readable file, removing our entry may leave it readable. Record this baseline rather than claiming that all access was revoked.

Do not blindly restore a whole historical ACL over a concurrent administrator change. Restore our named entry and any transaction-owned mask change only when the current state matches the expected applied state. Otherwise quarantine the account, retain the journal and report the conflict. A snapshot is recovery evidence, not permission to overwrite unrelated changes.

Private-path protection is a separate prerequisite. If the account can already read an expert/reference file, fail the audit and identify it; do not silently modify the entire private project. Named-UID input grants do not create a global allowlist and do not close all world-readable alternate copies.

`setfacl` normally recalculates the mask, which affects the owning group and named user/group entries. Its manual also documents mode-bit fallback on filesystems without ACL support. These are reasons to test support on disposable fixtures and explicitly check masks rather than issue a broad recursive command. [ACL utility documentation](https://man7.org/linux/man-pages/man1/setfacl.1.html).

## Minimal acceptance tests before applying to real data

- On disposable files, grant read access to initially inaccessible data; writes fail, tool execution works, private answer remains inaccessible.
- Restore both a previously absent and a pre-existing named-user entry exactly; another user's effective rights remain unchanged.
- Fail partway through application and verify rollback; simulate an interrupted journal and verify restart refuses new runs until recovery.
- Refuse symlink/inode replacements and ACL conflicts during recovery rather than changing the replacement target.
- Record world-readable baseline access correctly; do not report complete revocation when baseline access remains.
- Verify input immutability, old-output denial and residue handling across two actual UID runs.

Current scope: configuration and read-only preview, native libacl transaction engine, run-access/recover-access and root smoke-access command. Twelve unprivileged tests pass, including actual ACL syscalls on disposable files. Root cross-user and real shared-filesystem validation remain pending. This bounded implementation sequence comes before the first scientific agent trial; container scheduling, account pools and aggregate resource infrastructure remain deferred.
