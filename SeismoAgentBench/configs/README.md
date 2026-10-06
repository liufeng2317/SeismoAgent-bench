# Configuration layout

Agent and execution environment settings are kept in separate YAML files.

- `agents/` defines the Agent harness, executable, model, reasoning effort and authentication mode. It does not select Python, Conda, network access or package installation.
- `environments/` defines the execution mode, Python interpreter and environment policies. The selected interpreter is probed at launch and its actual version and Conda environment are written to the runtime context.
- `prompts/` contains framework-provided instructions used to render the Agent prompt.

Run scripts pass the Agent file with `--agent-config` and the environment file with `--environment-config`. Both configuration snapshots are stored under the run's `control/` directory.
