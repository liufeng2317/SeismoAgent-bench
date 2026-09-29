import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


FIXTURE = Path(__file__).resolve().parents[1] / "fixtures" / "synthetic_task"


class SyntheticFixtureSmokeTests(unittest.TestCase):
    def test_cli_fixture_produces_complete_run_layout(self):
        with tempfile.TemporaryDirectory() as tmp:
            run_root = Path(tmp) / "runs"
            command = [sys.executable, "-m", "SeismoAgentBench", "run-agent",
                       "--task", str(FIXTURE / "task.json"),
                       "--manifest", str(FIXTURE / "manifest.json"),
                       "--agent-name", "synthetic-fixture-agent",
                       "--agent-version", "1",
                       "--run-root", str(run_root),
                       "--run-id", "smoke-001",
                       "--", sys.executable, str(FIXTURE / "agent.py")]
            result = subprocess.run(command, capture_output=True, text=True, check=False)
            self.assertEqual(result.returncode, 0, result.stderr)
            payload = json.loads(result.stdout)
            self.assertEqual(payload["run"]["state"], "completed")
            run = run_root / "smoke-001"
            evaluated = subprocess.run([sys.executable, "-m", "SeismoAgentBench", "evaluate",
                                        "--run-dir", str(run)], capture_output=True, text=True, check=False)
            self.assertEqual(evaluated.returncode, 0, evaluated.stderr)
            self.assertEqual(json.loads(evaluated.stdout)["run"]["state"], "scored")
            for relative in (
                "control/task_spec.json", "control/input_manifest.json", "control/output_contract.json", "record/environment.json",
                "record/provenance.json", "record/execution.log", "work/catalog.json",
                "record/artifact_manifest.json", "evaluation/score.json", "record/run_result.json",
                "evaluation/report.json",
            ):
                self.assertTrue((run / relative).is_file(), relative)
            self.assertEqual(json.loads((run / "evaluation/score.json").read_text())["status"], "passed")


if __name__ == "__main__":
    unittest.main()
