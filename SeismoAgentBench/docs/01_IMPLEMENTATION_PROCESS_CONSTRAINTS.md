# Project implementation process constraints

## Purpose

These rules define how SeismoAgentBench is implemented and reviewed. They keep each change bounded, verifiable and traceable, and prevent implementation work from turning into open-ended investigation.

The rules apply to framework code, execution backends, task adapters, scientific-tool integrations and evaluation utilities. They do not replace scientific quality-control procedures for a specific dataset.

## Required cycle for every implementation step

Every step follows this cycle:

```text
Define objective
      ↓
Implement bounded change
      ↓
Validate result
      ↓
Confirm completion
      ↓
Commit the change
      ↓
Analyze the next step
```

No step is considered complete until its validation and Git record are complete.

### 1. Define the objective before implementation

Before editing code, record a short objective that states:

- the concrete behavior to add or correct;
- the files or module boundary involved;
- the expected input and output;
- the validation method;
- the explicit stopping condition.

The objective must describe one bounded change. “Improve the benchmark” or “continue debugging” is not a sufficient objective.

### 2. Implement only the bounded change

During implementation:

- modify only files needed for the objective;
- preserve existing scientific data and private reference material;
- avoid creating speculative modules, configuration fields or test frameworks;
- do not mix refactoring, formatting and unrelated fixes into the same step;
- do not expand the scope because a nearby improvement is possible.

If a new issue is discovered, record it as a candidate next step instead of silently expanding the current change.

### 3. Validate the result

Validation must match the objective and should be the smallest check that provides reliable evidence. Depending on the change, use:

- syntax or import checks;
- focused unit or integration tests;
- a deterministic CLI smoke run;
- schema and path validation;
- an artifact or provenance inspection;
- a scientific comparison when the change affects scientific output.

Validation must report both the command and its result. A successful command is not enough when the objective concerns scientific content; the relevant output must also be inspected.

### 4. Confirm completion and stop

After validation, explicitly decide whether the objective is complete:

- **complete:** the stated behavior works and the stopping condition is met;
- **blocked:** a specific external dependency prevents validation;
- **follow-up:** the objective works, but a separate improvement is identified.

Do not continue tuning after the stopping condition is met. A new hypothesis, parameter scan or visualization is a new implementation step.

### 5. Commit the verified change

After confirmation, create a focused Git commit:

```bash
git status --short
git diff --check
git add <files-for-this-step>
git commit -m "<imperative description of the verified change>"
```

Commit requirements:

- include only files belonging to the completed step;
- use a message describing the resulting behavior;
- do not commit large waveform/catalog files, generated caches, credentials, personal information or local environment reports;
- do not include unrelated pre-existing modifications;
- retain failed experiments only when they are needed to explain a reproducible boundary; otherwise keep them ignored or remove them deliberately.

If a commit cannot be created, record the reason and leave the working tree status explicit. Do not claim the step is Git-complete.

### 6. Analyze the next step after the commit

Only after the commit is verified should the next step be selected. The next-step note should state:

- what the completed step established;
- what remains necessary for the workflow goal;
- the single most important unresolved dependency;
- the next bounded objective;
- why deeper tuning is not yet justified.

The next step must follow the dependency order of the workflow. It must not be chosen only because a new diagnostic or parameter is available.

## Scope and convergence rules

### One primary question per step

Each step answers one primary implementation question. Supporting checks are allowed only when they are required to establish that answer.

### No indefinite tuning

Parameter scans, alternative tools and repeated plots stop when:

- the predefined comparison is complete;
- the result is sufficient to choose the next implementation decision; or
- the evidence shows that the question cannot be resolved with the current inputs.

Further exploration becomes a separately scoped step with its own objective and commit.

### Preserve parallel alternatives explicitly

When multiple implementations are scientifically meaningful, keep them as named alternatives and record their comparison. Do not silently replace the baseline or call a candidate result final before validation.

### Separate engineering and scientific conclusions

Every report must distinguish:

- implementation status;
- environment or tool availability;
- validation evidence;
- scientific quality or interpretation.

Passing a runner test does not establish scientific validity. A scientific improvement does not establish execution reproducibility unless the run is recorded.

## Minimum step record

For non-trivial steps, keep a short record in the relevant documentation or run directory:

```text
Objective:
Scope:
Inputs:
Expected outputs:
Validation command(s):
Observed result:
Completion decision:
Commit:
Next bounded step:
```

The record should point to generated artifacts rather than copying large data into Git.

## Definition of done

An implementation step is done only when:

1. the objective was stated before implementation;
2. the bounded change was made;
3. the relevant validation passed or was explicitly blocked;
4. the result and limitations were confirmed;
5. the focused Git commit exists;
6. the next step is separately defined.

This process is the default control mechanism for project implementation. Any exception must be recorded with its reason and scope.
