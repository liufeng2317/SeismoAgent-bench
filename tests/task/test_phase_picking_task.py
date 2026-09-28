import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from SeismoAgentBench.task import load_json, validate_manifest, validate_task


PACKAGE = Path(__file__).resolve().parents[2] / "tasks" / "2019_ridgecrest_california" / "phase_picking"


class PhasePickingTaskTests(unittest.TestCase):
    def test_task_and_manifest_are_valid(self):
        task = validate_task(load_json(PACKAGE / "task.json"))
        manifest = validate_manifest(load_json(PACKAGE / "input_manifest.json"), task=task)
        self.assertEqual(task["task_id"], "ridgecrest_2019_phase_picking")
        self.assertEqual(len(manifest["entries"]), 4)

    def test_baseline_runs_through_cli_and_writes_picks(self):
        with tempfile.TemporaryDirectory() as tmp:
            run_root = Path(tmp) / "runs"
            command = [sys.executable, "-m", "SeismoAgentBench", "run-agent",
                       "--task", str(PACKAGE / "task.json"),
                       "--manifest", str(PACKAGE / "input_manifest.json"),
                       "--agent-name", "ridgecrest-phase-picking-baseline",
                       "--agent-version", "1",
                       "--run-root", str(run_root),
                       "--run-id", "phase-001",
                       "--", sys.executable, str(PACKAGE / "baseline_agent.py")]
            result = subprocess.run(command, capture_output=True, text=True, check=False)
            self.assertEqual(result.returncode, 0, result.stderr)
            payload = json.loads(result.stdout)
            self.assertEqual(payload["run"]["state"], "scored")
            picks = json.loads((run_root / "phase-001/output/picks.json").read_text())
            self.assertGreater(len(picks["picks"]), 0)
            preprocessing = json.loads((run_root / "phase-001/output/preprocessing.json").read_text())
            self.assertEqual(len(preprocessing["traces"]), 3)


if __name__ == "__main__":
    unittest.main()
