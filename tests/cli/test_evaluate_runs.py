import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


class EvaluateRunsTests(unittest.TestCase):
    def test_evaluate_runs_returns_completion_summary(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            task = base / "task.json"
            manifest = base / "manifest.json"
            task.write_text(json.dumps({
                "task_id": "summary-task", "version": "1", "objective": "summary",
                "input_kinds": ["metadata"],
                "output_artifacts": [{"id": "result", "path": "result.json", "kind": "json", "required": True}],
                "scorer": {"name": "artifact-contract", "version": "1"},
            }), encoding="utf-8")
            manifest.write_text(json.dumps({
                "schema_version": 1, "case_id": "synthetic", "entries": [
                    {"id": "metadata", "path": "/tmp/metadata", "kind": "metadata", "read_only": True}
                ],
            }), encoding="utf-8")
            root = base / "runs"
            code = "import json,os; open(os.path.join(os.environ['BENCH_OUTPUT'],'result.json'),'w').write('{}')"
            run = subprocess.run([
                sys.executable, "-m", "SeismoAgentBench", "run-agent",
                "--task", str(task), "--manifest", str(manifest),
                "--agent-name", "summary-agent", "--agent-version", "1",
                "--run-root", str(root), "--run-id", "run-001", "--",
                sys.executable, "-c", code,
            ], capture_output=True, text=True, check=False)
            self.assertEqual(run.returncode, 0, run.stderr)
            result = subprocess.run([
                sys.executable, "-m", "SeismoAgentBench", "evaluate-runs",
                "--run-dir", str(root / "run-001"),
            ], capture_output=True, text=True, check=False)
            self.assertEqual(result.returncode, 0, result.stderr)
            payload = json.loads(result.stdout)
            self.assertEqual(payload["summary"]["total_runs"], 1)
            self.assertEqual(payload["summary"]["scored_runs"], 1)
            self.assertEqual(payload["summary"]["completed_fraction"], 1.0)


if __name__ == "__main__":
    unittest.main()
