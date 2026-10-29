# Configuration layout

Agent and execution environment settings are kept in separate YAML files.

- `agents/` defines the Agent harness, model, reasoning effort and authentication mode. An executable path and version command may be supplied by a launcher when a CLI needs an override; they do not select Python, Conda, network access or package installation.
- `environments/` defines the execution mode, Python interpreter and environment policies. The selected interpreter is probed at launch and its actual version and Conda environment are written to the runtime context.
- `prompts/` contains framework-provided instructions used to render the Agent prompt.

Run scripts pass the Agent file with `--agent-config` and the environment file with `--environment-config`. Both configuration snapshots are stored under the run's `control/` directory.

Authentication paths are supplied at launch, for example with `--codex-home`, and are not stored in the shared Agent configuration. The default executable version probe uses `--version` when no override is declared.

## Evaluation environment setup

- `environments/seismoagent_eval.yaml` selects the Python interpreter of the `seismoagent_eval` Conda environment that Agents use.
- `environments/seismoagent_eval.requirements.txt` pins the direct Python dependencies of that environment (numerical processing, tables, plotting, ObsPy, file formats, GIS tables, HTTP, progress). The versions match the installed environment. Install them only into the writable evaluation environment, never into the protected `seismoagent` environment: `/liufeng1afs/software/miniconda3/envs/seismoagent_eval/bin/python -m pip install -r SeismoAgentBench/configs/environments/seismoagent_eval.requirements.txt`. Task tools such as PhaseNet, GaMMA or NonLinLoc come from `seismotools/`, not from this file.
- `environments/install_host_tools.sh` installs the Ubuntu/Debian command-line tools Agents use to inspect files and record runs (`file`, `tree`, `jq`, archive utilities, `curl`, `wget`, `rsync`, process tools, `git`, basic build support). It changes only system packages, is idempotent, and runs as root: `sudo bash SeismoAgentBench/configs/environments/install_host_tools.sh`.
