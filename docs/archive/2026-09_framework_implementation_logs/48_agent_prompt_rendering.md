# Stage 48: Agent prompt rendering

- **Goal:** provide Codex with one complete, auditable Markdown task input without turning the scientific method into a fixed workflow.
- **Implemented:** added `render_agent_prompt`; `run-codex` now renders task metadata, declared inputs, output requirements, runtime paths and constraints automatically; optional `--prompt` text is appended as additional instructions; each run stores the rendered prompt at `control/agent_prompt.md`.
- **Validation:** prompt and Codex CLI tests passed (13 tests); the full test suite passed (111 tests).
- **Git:** `adc87fb` (`Render complete Agent-facing task prompts`).
