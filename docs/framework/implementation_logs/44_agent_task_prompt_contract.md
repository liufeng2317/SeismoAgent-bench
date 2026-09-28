# Stage 44: Agent task prompt contract

- **Goal:** make the task specification directly usable as an Agent instruction.
- **Implemented:** replaced the required `objective` field with `task_prompt`; added optional `title` and `summary` metadata; expanded the Ridgecrest catalog and phase-picking prompts with input, output, reproducibility and uncertainty requirements.
- **Validation:** legacy `objective` fields are rejected, relative task metadata remains optional, and all task/CLI/scoring workflows passed in the 108-test suite.
