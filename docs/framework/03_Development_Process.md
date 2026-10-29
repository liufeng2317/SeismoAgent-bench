# Development Process

This document states how a change to SeismoAgentBench is made, validated and committed.

## 1. Cycle

```text
Define → Implement → Validate → Confirm → Commit
```

### 1.1 Define

Before editing, state one concrete objective, the files involved, the validation command and the stopping condition.

### 1.2 Implement

- Change only what the objective requires.
- Do not mix in unrelated refactoring or formatting.
- Do not add speculative modules, parameters or tests.
- Note new issues as separate follow-up items.

### 1.3 Validate

Run the smallest reliable check for the change: an import check, a focused test, a deterministic smoke run, a schema or artifact check, or a scientific comparison when scientific output changes. Inspect the relevant output, not only the exit code.

### 1.4 Confirm

Mark the change as one of:

- **complete**: the objective and the stopping condition are met;
- **blocked**: a named external dependency prevents validation;
- **follow-up**: the objective is met and a separate issue remains.

Stop tuning once the stopping condition is met.

### 1.5 Commit

```bash
git status --short
git diff --check
git add <files-for-this-change>
git diff --cached
git commit
```

Each commit contains only the completed change and excludes large data, generated caches, credentials, personal information and unrelated edits.

## 2. Record of a change

The commit message is the record of a change. Its subject names the change; its body says what changed, why, and how it was validated (the command or comparison and its result). No separate implementation log is kept.

The step records written in September 2026 are archived at `docs/archive/2026-09_framework_implementation_logs/`. They are history only and are not updated.

## 3. Uncommitted work

Before starting a new phase, review all uncommitted work, group it into small logical commits by function or document, and commit the groups separately. Check the staged file list and `git diff --cached` before each commit. Never commit scientific data, raw waveforms, generated bulk products, run directories, credentials, personal information or local runtime state.
