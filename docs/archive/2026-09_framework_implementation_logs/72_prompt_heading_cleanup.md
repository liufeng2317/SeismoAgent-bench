# Prompt heading cleanup

## Implemented

- Removed the renderer-only `Task instructions` heading that appeared directly
  above the task prompt's first heading.
- Kept one consistent hierarchy: document title, task title, task sections,
  then generated input/output/runtime sections.
- Added a regression assertion for the generated heading structure.

## Validation

The rendered Ridgecrest prompt now starts with `#`, `##`, then `### Objective`;
the prompt and workflow tests passed.
