# SeismoAgentBench Benchmark Workflow Specification

## 1. Purpose

This document specifies the standard workflow for running and evaluating seismic-data analysis agents with SeismoAgentBench. It defines the required stages, interfaces, artifacts and status semantics. Implementations may use different execution technologies, but they must preserve these contracts.

The specification is dataset-independent. Dataset-specific data, task instructions, reference products and scientific parameters are supplied through versioned task packages and input manifests.

## 2. Workflow

The required workflow is:

```text
Task registration
      ↓
Input manifest validation
      ↓
Execution preparation
      ↓
Agent and tool execution
      ↓
Artifact validation
      ↓
Scoring
      ↓
Metric aggregation
      ↓
Reporting and provenance capture
```

The stages are ordered. A stage must not consume artifacts that its predecessor has not declared valid. Logging and provenance are recorded throughout the workflow.

## 3. Stage requirements

### 3.1 Task registration

A task specification MUST declare:

- `task_id` and task version;
- Agent-facing task prompt;
- the Agent-facing task prompt;
- optional structured input requirements;
- optional output hints or schemas;
- permitted tool capabilities;
- execution limits;
- scorer name and scorer version;
- metric definitions;
- failure handling policy.

A task specification MUST NOT contain private reference products or depend on a particular agent implementation.

The task prompt is the primary task contract and defines the scientific
objective, inputs and expected outputs. A task package MAY provide an
`input_manifest.json` for machine-readable input details and MAY provide an
`output_contract.json` for optional structural checks. Neither file is
required for a task to run.

**Input:** task specification.  
**Output:** validated, versioned task record.

### 3.2 Input manifest validation

When supplied, an input manifest MUST be versioned and MUST provide stable
logical entry IDs. Each entry MUST declare its semantic `data_type`, physical
`format`, source or resolved path and read-only intent. A task without a
manifest describes its inputs directly in the task prompt.

The controller MUST validate:

- manifest schema and version;
- unique entry IDs;
- path existence and file type;
- read-only declarations;
- compatibility with task requirements;
- consistency of declared metadata where checked.

**Input:** task record and input manifest.  
**Output:** resolved manifest and validation record.

### 3.3 Execution preparation

The execution backend MUST:

- allocate an immutable `run_id`;
- create the run record and declared work areas;
- select and record an execution profile;
- prepare the declared runtime;
- apply timeout and resource policies where supported;
- expose the standard run context to the agent.

The standard context MUST provide equivalent values for:

```text
BENCH_TASK_SPEC
BENCH_INPUT_MANIFEST
BENCH_WORK
BENCH_OUTPUT
```

A backend MAY copy, mount or directly resolve manifest entries. This implementation choice MUST NOT alter the task or agent contract.

**Input:** validated task and manifest.  
**Output:** prepared run context and environment record.

### 3.4 Agent and tool execution

The agent MUST receive the task contract and manifest through the run context. It MUST write declared products below `BENCH_OUTPUT`.

Tools MUST be invoked through registered adapters when adapter support is available. An adapter MUST record:

- executable or package identity;
- version;
- arguments and parameters;
- model or auxiliary-file identity;
- start/end time;
- exit status;
- stdout/stderr locations.

A process exit status describes execution state only. It MUST NOT be interpreted as a scientific score.

**Input:** run context.  
**Output:** agent artifacts, tool records and execution log.

### 3.5 Artifact validation

The controller MUST validate agent products before scoring. It MUST check:

- required artifacts exist;
- artifacts are inside the declared output area;
- file and structured-data schemas are valid;
- required provenance fields are present;
- output does not overwrite task, manifest or run-control records.

Invalid or incomplete products MUST receive an explicit artifact-validation failure. They MUST NOT be silently repaired.

**Input:** agent artifacts and task output contract.  
**Output:** validated artifact set or artifact failure record.

### 3.6 Scoring

An external scorer MAY run after Agent execution. It MUST be separate from the
Agent command and MUST read the task prompt, Agent outputs and authorized
reference products. The framework does not require a scorer or impose a
universal output format.

A scorer MUST record:

- scorer name and version;
- reference identity;
- matching and tolerance policy;
- per-item scores;
- diagnostics;
- scorer status.

Scientific metrics MAY include detection, association, phase-pick, location, depth, magnitude, uncertainty and output-completeness measures, depending on the task contract.

**Input:** task record, validated artifacts and authorized references.  
**Output:** versioned score record.

### 3.7 Metric aggregation

The aggregation component MUST combine scores according to the task metric definition. It SHOULD provide both instance-level and benchmark-level results. Aggregation MUST preserve the distinction between missing, failed and valid scores.

**Input:** score records.  
**Output:** metric summary.

### 3.8 Reporting and provenance

A run report MUST distinguish at least:

```text
validation_failed
execution_failed
execution_timeout
artifact_invalid
scoring_failed
scored
```

A report MUST preserve:

```text
task_spec.json
input_manifest.json
environment.json
agent_command.json
execution.log
output/
score/score.json
run_result.json
```

Provenance SHOULD include tool versions, parameters, model identities, source identities, timestamps and execution profile. Private reference contents MUST NOT be copied into public reports.

## 4. Required run artifacts

```text
<run-root>/
  task_spec.json
  input_manifest.json
  environment.json
  agent_command.json
  execution.log
  output/
  artifacts.json
  score/
    score.json
  run_result.json
  evaluation_report.json
```

Run directories MUST be uniquely identified and MUST NOT be silently overwritten. A rerun MUST receive a new `run_id`.

## 5. Package responsibilities

```text
SeismoAgentBench/                 # reusable workflow implementation
  task/                           # task specifications and input manifests
  execution/                      # run control and execution backends
  workflow/                       # end-to-end stage orchestration
  agent/                          # agent entry points and tool adapters
  scoring/                        # output validation, scoring and metrics
  reporting/                      # run artifacts and provenance reports
  utils/                          # small cross-cutting utilities only

workflows/tasks/<instance>/                 # task packages and instance configuration
data/<instance>/      # instance data and source evidence
seismotools/                      # versioned scientific-tool snapshots
```

Generic modules MUST NOT contain instance-specific paths, catalogs, expert answers, station lists or plotting rules.

The package is organized by stable workflow responsibilities rather than by every conceptual object:

| Module | Responsibility | Excludes |
| --- | --- | --- |
| `task/` | Task records, output contracts, input manifests and validation | Agent implementation and reference answers |
| `execution/` | Run creation, runtime preparation, backend dispatch and limits | Scientific scoring rules |
| `workflow/` | Ordered execution, artifact validation and score-record orchestration | Scientific algorithms and reference comparisons |
| `agent/` | Agent entry points and adapters for approved scientific tools | Private references and aggregate metrics |
| `scoring/` | Output-contract checks, scientific scorers and metric aggregation | Process launching and environment setup |
| `reporting/` | Run summaries, provenance and exportable reports | Instance-specific analysis scripts |
| `utils/` | Small utilities shared by more than one stable module | Workflow stages and catch-all domain logic |

Schemas live with the module that owns the contract until their size and reuse justify a separate package. A generic `core/` directory is not created in advance; shared identifiers and errors remain with the owning module until a real cross-module dependency exists. Command-line entry points are thin wrappers and do not require a separate `cli/` package at the start.

The following areas remain outside the reusable control library:

| Area | Responsibility |
| --- | --- |
| `workflows/tasks/<instance>/` | Task instructions, instance configuration and instance-level scorers |
| `data/<instance>/` | Source data, reference evidence and instance-specific preparation scripts |
| `seismotools/` | Versioned scientific-tool source, documentation and runtime assets |

Only create a module when it has an implemented responsibility and at least one stable caller. Do not create empty directories for anticipated features.

## 6. Conformance criteria

An implementation conforms to this specification when it:

1. validates versioned task and input contracts;
2. uses immutable task and run identifiers;
3. exposes the standard run context;
4. separates agent execution from artifact validation and scoring;
5. records explicit failure states;
6. produces the required run artifacts;
7. preserves tool and environment provenance;
8. supports a replaceable execution backend without changing task or scorer contracts.
