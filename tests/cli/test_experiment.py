import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

class ExperimentCliTests(unittest.TestCase):
    def test_plan_experiment_outputs_units_without_running_them(self):
        with tempfile.TemporaryDirectory() as tmp:
            spec = Path(tmp) / "experiment.yaml"
            spec.write_text(
                "experiment_id: smoke\noutput_root: /tmp/runs\nconcurrency: 1\n"
                "agents:\n  - id: demo\n    name: demo-agent\n    version: '1'\n    config: agent.yaml\n    command: [python, agent.py]\n"
                "tasks:\n  - id: task\n    task_spec: task.json\n    input_manifest: manifest.json\n    variants: [base]\n",
                encoding="utf-8",
            )
            result = subprocess.run([sys.executable, "-m", "SeismoAgentBench", "plan-experiment",
                                     "--spec", str(spec)], capture_output=True, text=True, check=False)
            self.assertEqual(result.returncode, 0, result.stderr)
            payload = json.loads(result.stdout)
            self.assertEqual(len(payload["units"]), 1)
            self.assertEqual(payload["units"][0]["agent_id"], "demo")


if __name__ == "__main__":
    unittest.main()
