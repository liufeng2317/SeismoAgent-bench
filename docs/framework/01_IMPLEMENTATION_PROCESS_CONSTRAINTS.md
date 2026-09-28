# Implementation process constraints

These rules apply to every SeismoAgentBench implementation step.

## Required cycle

```text
Define → Implement → Validate → Confirm → Commit → Plan next
```

### 1. Define

Before editing, state:

- one concrete objective;
- scope and files involved;
- expected input and output;
- validation command;
- stopping condition.

### 2. Implement

- Change only what the objective requires.
- Do not mix unrelated refactoring or formatting.
- Do not add speculative modules, parameters or tests.
- Record new issues as separate follow-up items.

### 3. Validate

Run the smallest reliable check for the change, such as:

- syntax/import checks;
- focused tests;
- deterministic smoke runs;
- schema or artifact checks;
- scientific comparison when scientific output changes.

Record the command and result. Inspect the relevant output, not only the exit code.

### 4. Confirm and stop

Mark the step as one of:

- **complete** — objective and stopping condition are satisfied;
- **blocked** — a specific external dependency prevents validation;
- **follow-up** — the objective is complete and a separate issue remains.

Do not continue tuning after the stopping condition is met.

### 5. Commit

After confirmation:

```bash
git status --short
git diff --check
git add <files-for-this-step>
git commit -m "<verified change>"
```

Each commit MUST:

- contain only the completed step;
- exclude large data, generated caches, credentials, personal information and unrelated changes;
- describe the resulting behavior.

### 6. Plan the next step

Only after the commit, record:

- what was established;
- what remains necessary;
- the next single objective;
- why further tuning is not yet required.

## Minimal step record

```text
Objective:
Scope:
Inputs / outputs:
Validation:
Result:
Decision:
Commit:
Next step:
```

An implementation step is complete only when the objective is defined, the result is validated, the decision is recorded and the focused Git commit exists.

## Backlog commit rule

Before starting a new implementation phase, review all uncommitted work. Group it into small logical commits by function or document, and commit the groups separately. Do not commit large scientific data, raw waveforms, generated bulk products, credentials, personal information or local runtime state. Check the staged file list and `git diff --cached` before each commit.
