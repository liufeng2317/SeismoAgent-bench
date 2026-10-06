import unittest
from unittest.mock import patch

from SeismoAgentBench.execution.environment import load_environment_config, probe_runtime


class RuntimeProbeTests(unittest.TestCase):
    def test_loads_environment_config(self):
        import tempfile
        from pathlib import Path
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "environment.yaml"
            source.write_text(
                "mode: host-direct\npython: /opt/miniconda/envs/seismoagent_eval/bin/python\n"
                "network_policy: allowed\npackage_installation: allowed\n",
                encoding="utf-8",
            )
            config = load_environment_config(source)
        self.assertEqual(config["mode"], "host-direct")
        self.assertEqual(config["package_installation"], "allowed")

    def test_selected_conda_interpreter_overrides_launcher_environment(self):
        with patch(
            "SeismoAgentBench.execution.environment._python_info",
            return_value={
                "executable": "/opt/miniconda/envs/seismoagent_eval/bin/python",
                "version": "3.9.25",
            },
        ):
            runtime = probe_runtime(
                "/opt/miniconda/envs/seismoagent_eval/bin/python",
                environment={
                    "CONDA_PREFIX": "/opt/miniconda",
                    "CONDA_DEFAULT_ENV": "base",
                },
            )
        self.assertEqual(runtime["conda_environment"], "seismoagent_eval")
        self.assertEqual(runtime["conda_prefix"], "/opt/miniconda/envs/seismoagent_eval")


if __name__ == "__main__":
    unittest.main()
