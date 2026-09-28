# Stage 28: Project view of run outputs

## Objective

Make large run outputs easy to inspect from the project directory without
copying them into Git or duplicating data.

## Implemented

Created the local symbolic link:

```text
SeismoAgentBench/runs
  -> /ai4earthafs/liufeng/ScienceDiscovery/SeismoAgentBench/runs
```

The target remains the canonical storage location. The link is machine
specific and is intentionally ignored by Git.

## Validation

The link resolves to the canonical run root and exposes the completed default
Codex smoke run and its `run_result.json`.

## Recreate on another host

```bash
ln -s /ai4earthafs/liufeng/ScienceDiscovery/SeismoAgentBench/runs \
  /liufeng1afs/project/03_LLM/Science_Discovery_Agenet/SeismoAgentBench/runs
```
