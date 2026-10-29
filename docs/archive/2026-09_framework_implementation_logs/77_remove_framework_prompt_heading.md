# Remove framework prompt heading

## Implemented

- Removed the framework-owned `# SeismoAgentBench Task` heading from rendered agent prompts.
- Rendered the task title as the single top-level heading: `# Task: <title>`.
- Added regression checks for the heading and CLI prompt output.

## Validation

- Targeted task and workflow tests passed.
- Full test suite passed after updating the old CLI assertion.
