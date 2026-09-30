# Stage 89: Ridgecrest five-file task interface

The Ridgecrest catalog task now exposes one compact runnable interface:

```text
input.json, task.json, task_prompt.md, main.py, run.sh
```

- `input.json` declares the read-only waveform root.
- `task.json` contains structured metadata and input requirements.
- `task_prompt.md` is the source of task procedure and output requirements.
- `main.py` is the deterministic catalog baseline.
- `run.sh` launches the Codex workflow with the configured agent profile.

The obsolete duplicate baseline entry points and standalone output-contract file
were removed. Output requirements remain in the prompt, consistent with the
workflow-test task interface.

Validation: task/input loading, baseline catalog validation, shell syntax and
89 framework tests passed.
