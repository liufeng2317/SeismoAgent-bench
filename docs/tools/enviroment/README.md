# Linux environment tools

`install_linux_tools.sh` installs the common Ubuntu/Debian command-line tools used by SeismoAgentBench Agents to inspect files, prepare data and record runs. The package set includes `file`, `find`, `stat`, `du`, `readlink`, `realpath`, `tree`, `jq`, archive utilities, `curl`, `wget`, `rsync`, process tools, `git` and basic build support.

The script changes only the host system package set. It does not install Python packages or modify the `seismoagent` or `seismoagent_eval` Conda environments. Run it as root on Ubuntu/Debian:

```bash
sudo bash docs/tools/enviroment/install_linux_tools.sh
```

The installer is idempotent: rerunning it only verifies or updates the same package set. Review the package list before using it on a production worker.
