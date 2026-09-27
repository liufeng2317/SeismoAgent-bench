import json
from pathlib import Path
import sys
import tempfile
import unittest

from SeismoAgentBench.execution import ExecutionError, run_command


TASK = {
    "task_id": "runner-smoke",
    "version": "1",
    "objective": "Test execution records.",
    "input_kinds": ["metadata"],
    "output_artifacts": [{"id": "result", "path": "result.json", "kind": "json", "required": True}],
    "scorer": {"name": "noop", "version": "1"},
}
MANIFEST = {"schema_version": 1, "case_id": "synthetic_case", "entries": [
    {"id": "metadata", "path": "/tmp/metadata.json", "kind": "metadata", "read_only": True}
]}


class RunnerTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name) / "runs"
        self.root.mkdir()
        self.task = Path(self.tmp.name) / "task.json"
        self.manifest = Path(self.tmp.name) / "manifest.json"
        self.task.write_text(json.dumps(TASK), encoding="utf-8")
        self.manifest.write_text(json.dumps(MANIFEST), encoding="utf-8")

    def tearDown(self):
        self.tmp.cleanup()

    def test_completed_run_writes_context_and_log(self):
        code = "import json,os,pathlib; assert pathlib.Path(os.environ['BENCH_WORK']) == pathlib.Path.cwd(); pathlib.Path(os.environ['BENCH_OUTPUT'],'result.json').write_text(json.dumps({'ok': True}))"
        result = run_command(self.task, self.manifest, [sys.executable, "-c", code], self.root, "run-001", timeout=10)
        run = self.root / "run-001"
        self.assertEqual(result["state"], "completed")
        self.assertFalse(result["formal_evaluation_eligible"])
        self.assertTrue((run / "task_spec.json").is_file())
        self.assertTrue((run / "input_manifest.json").is_file())
        self.assertTrue((run / "execution.log").is_file())
        self.assertEqual(json.loads((run / "output/result.json").read_text())["ok"], True)

    def test_nonzero_command_is_recorded(self):
        result = run_command(self.task, self.manifest, [sys.executable, "-c", "raise SystemExit(7)"], self.root, "run-002", timeout=10)
        self.assertEqual(result["state"], "command_failed")
        self.assertEqual(result["exit_code"], 7)

    def test_timeout_kills_command(self):
        result = run_command(self.task, self.manifest, [sys.executable, "-c", "import time; time.sleep(10)"], self.root, "run-003", timeout=0.1)
        self.assertEqual(result["state"], "timeout")

    def test_invalid_inputs_are_rejected_before_run_directory(self):
        bad = dict(TASK); bad["task_id"] = ""
        self.task.write_text(json.dumps(bad), encoding="utf-8")
        with self.assertRaises(ExecutionError):
            run_command(self.task, self.manifest, [sys.executable, "-c", "pass"], self.root, "run-004")
        self.assertFalse((self.root / "run-004").exists())

    def test_run_id_cannot_be_reused(self):
        command = [sys.executable, "-c", "pass"]
        run_command(self.task, self.manifest, command, self.root, "run-005")
        with self.assertRaises(ExecutionError):
            run_command(self.task, self.manifest, command, self.root, "run-005")


if __name__ == "__main__":
    unittest.main()
