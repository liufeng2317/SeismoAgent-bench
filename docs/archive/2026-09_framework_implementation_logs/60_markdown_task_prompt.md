# Implementation 60: Markdown task prompt

- Git commit: `89272cd`
- Goal: make long task instructions easy for humans to read and maintain without weakening the structured task contract.
- Change: tasks may declare `task_prompt_file`; the loader reads that relative Markdown file with priority over an inline prompt. New run controls snapshot the resolved text as `control/task_prompt.md`, while `task_spec.json` retains only the prompt-file reference. Inline prompts remain supported for legacy tasks.
- Check: task validation, prompt rendering, runner snapshot, compilation and diff checks passed.
