# Implementation 59: Provenance record consolidation

- Git commit: `bad5c65`
- Goal: remove duplicate command records from new runs while preserving raw logs and structured trajectories.
- Change: new runs write one `record/provenance.json` containing Agent identity, launcher details and references to control/environment files. Codex prompts are represented by a control-file reference rather than duplicated in command records. Legacy command files remain readable for older runs.
- Check: focused Agent-contract and transcript tests passed; compilation and diff checks passed. The existing CLI subprocess smoke tests remain environment-sensitive and were not treated as passing.
