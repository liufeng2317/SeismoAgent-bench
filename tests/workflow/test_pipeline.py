import json
from pathlib import Path
import sys
import tempfile
import unittest

from SeismoAgentBench.workflow import run_task


TASK = {
    "task_id": "pipeline-smoke",
    "version": "1",
    "objective": "Run a synthetic end-to-end task.",
    "input_kinds": ["metadata"],
    "output_artifacts": [{"id": "result", "path": "result.json", "kind": "json", "required": True}],
    "scorer": {"name": "artifact-contract", "version": "1"},
}
MANIFEST = {"schema_version": 1, "case_id": "synthetic_case", "entries": [
    {"id": "metadata", "path": "/tmp/metadata.json", "kind": "metadata", "read_only": True}
]}


class PipelineTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        base = Path(self.tmp.name)
        self.root = base / "runs"
        self.root.mkdir()
        self.task = base / "task.json"
        self.manifest = base / "manifest.json"
        self.task.write_text(json.dumps(TASK), encoding="utf-8")
        self.manifest.write_text(json.dumps(MANIFEST), encoding="utf-8")

    def tearDown(self):
        self.tmp.cleanup()

    def test_success_runs_validation_and_score(self):
        code = "import json,os; open(os.path.join(os.environ['BENCH_OUTPUT'],'result.json'),'w').write(json.dumps({'ok': True}))"
        result = run_task(self.task, self.manifest, [sys.executable, "-c", code], self.root, "run-001", timeout=10)
        run = self.root / "run-001"
        self.assertEqual(result["run"]["state"], "scored")
        self.assertEqual(result["score"]["metrics"]["contract_compliance"], 1.0)
        self.assertTrue((run / "artifacts.json").is_file())
        self.assertTrue((run / "score/score.json").is_file())

    def test_missing_required_output_is_not_scored(self):
        result = run_task(self.task, self.manifest, [sys.executable, "-c", "pass"], self.root, "run-002", timeout=10)
        self.assertEqual(result["run"]["state"], "artifact_invalid")
        self.assertIsNone(result["score"])
        self.assertFalse((self.root / "run-002/score").exists())

    def test_command_failure_is_not_scored(self):
        result = run_task(self.task, self.manifest, [sys.executable, "-c", "raise SystemExit(9)"], self.root, "run-003", timeout=10)
        self.assertEqual(result["run"]["state"], "command_failed")
        self.assertIsNone(result["score"])


if __name__ == "__main__":
    unittest.main()
