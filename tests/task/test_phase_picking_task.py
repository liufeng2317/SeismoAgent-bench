import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from SeismoAgentBench.task import load_json, load_task, validate_manifest, validate_task


PACKAGE = Path(__file__).resolve().parents[2] / "tasks" / "2019_ridgecrest_california_phasepicking"


class PhasePickingTaskTests(unittest.TestCase):
    def test_task_and_manifest_are_valid(self):
        task = validate_task(load_json(PACKAGE / "task.json"))
        resolved = load_task(PACKAGE / "task.json")
        manifest = validate_manifest(load_json(PACKAGE / "input_manifest.json"), task=task)
        self.assertEqual(task["task_id"], "ridgecrest_2019_phase_picking")
        self.assertEqual([item["id"] for item in resolved["output_artifacts"]],
                         ["task_plan", "preprocessing_figure", "picks", "pick_examples"])
        self.assertEqual(len(manifest["entries"]), 2)
        self.assertEqual(manifest["entries"][0]["path_type"], "directory")

    def test_baseline_runs_through_cli_and_writes_picks(self):
        with tempfile.TemporaryDirectory() as tmp:
            run_root = Path(tmp) / "runs"
            manifest = load_json(PACKAGE / "input_manifest.json")
            manifest["entries"][0]["path"] = (
                "/ai4earthafs/liufeng/ScienceDiscovery/SeismoAgentBench/data/"
                "2019_ridgecrest_california/waveforms/data/CI.CCC/"
                "CI.CCC..HHZ__20190705T000000Z__20190706T000000Z.mseed"
            )
            manifest["entries"][0]["path_type"] = "file"
            manifest_path = Path(tmp) / "input_manifest.json"
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
            command = [sys.executable, "-m", "SeismoAgentBench", "run-agent",
                       "--task", str(PACKAGE / "task.json"),
                       "--manifest", str(manifest_path),
                       "--agent-name", "ridgecrest-phase-picking-baseline",
                       "--agent-version", "1",
                       "--run-root", str(run_root),
                       "--run-id", "phase-001",
                       "--", sys.executable, str(PACKAGE / "main.py")]
            result = subprocess.run(command, capture_output=True, text=True, check=False)
            self.assertEqual(result.returncode, 0, result.stderr)
            payload = json.loads(result.stdout)
            self.assertEqual(payload["run"]["state"], "completed")
            evaluated = subprocess.run([sys.executable, "-m", "SeismoAgentBench", "evaluate",
                                        "--run-dir", str(run_root / "phase-001")],
                                       capture_output=True, text=True, check=False)
            self.assertEqual(evaluated.returncode, 0, evaluated.stderr)
            picks = (run_root / "phase-001/agent/output/picks.csv").read_text()
            self.assertIn("station_id,channel,phase,arrival_time", picks)
            self.assertTrue((run_root / "phase-001/agent/output/task_plan.json").is_file())
            self.assertTrue((run_root / "phase-001/agent/output/preprocessing_figure.png").is_file())
            examples = json.loads((run_root / "phase-001/agent/output/pick_examples.json").read_text())
            self.assertIn("examples", examples)


if __name__ == "__main__":
    unittest.main()
