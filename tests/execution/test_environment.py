import unittest
from unittest.mock import patch

from SeismoAgentBench.execution.environment import probe_runtime


class RuntimeProbeTests(unittest.TestCase):
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
