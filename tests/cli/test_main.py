import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


TASK = {
    "task_id": "cli-smoke",
    "version": "1",
    "objective": "Run a synthetic CLI task.",
    "input_kinds": ["metadata"],
    "output_artifacts": [{"id": "result", "path": "result.json", "kind": "json", "required": True}],
    "scorer": {"name": "artifact-contract", "version": "1"},
}
MANIFEST = {"schema_version": 1, "case_id": "synthetic_case", "entries": [
    {"id": "metadata", "path": "/tmp/metadata.json", "kind": "metadata", "read_only": True}
]}


class CliTests(unittest.TestCase):
    def test_run_agent_command_returns_json_and_zero_on_scored(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            task = base / "task.json"
            manifest = base / "manifest.json"
            root = base / "runs"
            task.write_text(json.dumps(TASK), encoding="utf-8")
            manifest.write_text(json.dumps(MANIFEST), encoding="utf-8")
            code = "import json,os; open(os.path.join(os.environ['BENCH_OUTPUT'],'result.json'),'w').write(json.dumps({'ok': True}))"
            command = [sys.executable, "-m", "SeismoAgentBench", "run-agent", "--task", str(task),
                       "--manifest", str(manifest), "--agent-name", "cli-agent", "--agent-version", "1",
                       "--run-root", str(root), "--run-id", "run-001", "--", sys.executable, "-c", code]
            result = subprocess.run(command, capture_output=True, text=True, check=False)
            self.assertEqual(result.returncode, 0, result.stderr)
            payload = json.loads(result.stdout)
            self.assertEqual(payload["run"]["state"], "scored")
            self.assertTrue((root / "run-001/agent_command.json").is_file())

    def test_failed_agent_returns_nonzero_worker_status(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            task = base / "task.json"
            manifest = base / "manifest.json"
            root = base / "runs"
            task.write_text(json.dumps(TASK), encoding="utf-8")
            manifest.write_text(json.dumps(MANIFEST), encoding="utf-8")
            command = [sys.executable, "-m", "SeismoAgentBench", "run-agent", "--task", str(task),
                       "--manifest", str(manifest), "--agent-name", "cli-agent", "--agent-version", "1",
                       "--run-root", str(root), "--run-id", "run-002", "--", sys.executable, "-c", "raise SystemExit(4)"]
            result = subprocess.run(command, capture_output=True, text=True, check=False)
            self.assertEqual(result.returncode, 3)
            self.assertEqual(json.loads(result.stdout)["run"]["state"], "execution_failed")


if __name__ == "__main__":
    unittest.main()
