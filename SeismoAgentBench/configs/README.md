# Configuration layout

Agent and execution environment settings are kept in separate YAML files.

- `agents/` defines the Agent harness, model, reasoning effort and authentication mode. An executable path and version command may be supplied by a launcher when a CLI needs an override; they do not select Python, Conda, network access or package installation.
- `environments/` defines the execution mode, Python interpreter and environment policies. The selected interpreter is probed at launch and its actual version and Conda environment are written to the runtime context.
- `prompts/` contains framework-provided instructions used to render the Agent prompt.

Run scripts pass the Agent file with `--agent-config` and the environment file with `--environment-config`. Both configuration snapshots are stored under the run's `control/` directory.

Authentication paths are supplied at launch, for example with `--codex-home`, and are not stored in the shared Agent configuration. The default executable version probe uses `--version` when no override is declared.
