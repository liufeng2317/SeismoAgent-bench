import json
from pathlib import Path
import sys
import tempfile
import unittest
from tests.task_helpers import write_task_package

from SeismoAgentBench.execution import ExecutionError, run_command


TASK = {
    "task_id": "runner-smoke",
    "version": "1",
    "task_prompt_file": "task_prompt.md",
    "output_contract": "output_contract.json",
    "input_requirements": [{"id": "metadata", "data_type": "metadata", "required": True}],
    "evaluation": {"scorers": [{"name": "noop", "version": "1"}]},
    "output_artifacts": [{"id": "result", "path": "result.json", "kind": "json", "required": True}],
}
MANIFEST = {"schema_version": 1, "case_id": "synthetic_case", "entries": [
    {"id": "metadata", "path": "/tmp/metadata.json", "data_type": "metadata", "format": "JSON", "read_only": True}
]}


class RunnerTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name) / "runs"
        self.root.mkdir()
        self.task = Path(self.tmp.name) / "task.json"
        self.manifest = Path(self.tmp.name) / "manifest.json"
        write_task_package(self.task, TASK, "Test execution records.")
        self.manifest.write_text(json.dumps(MANIFEST), encoding="utf-8")

    def tearDown(self):
        self.tmp.cleanup()

    def test_prompt_only_task_runs_without_manifest_or_output_contract(self):
        task = Path(self.tmp.name) / "prompt_only.json"
        task.write_text(json.dumps({
            "task_id": "prompt-only",
            "version": "1",
            "task_prompt_file": "prompt.md",
        }), encoding="utf-8")
        (task.parent / "prompt.md").write_text("Produce the task result.\n", encoding="utf-8")
        code = "import os,pathlib; assert 'BENCH_INPUT_MANIFEST' not in os.environ; pathlib.Path(os.environ['BENCH_OUTPUT'],'result.txt').write_text('ok')"
        result = run_command(task, None, [sys.executable, "-c", code], self.root, "prompt-only", timeout=10)
        run = self.root / "prompt-only"
        self.assertEqual(result["state"], "completed")
        self.assertFalse((run / "control/input_manifest.json").exists())
        self.assertFalse((run / "control/output_contract.json").exists())
        self.assertTrue((run / "work/result.txt").is_file())

    def test_completed_run_writes_context_and_log(self):
        code = "import json,os,pathlib; assert pathlib.Path(os.environ['BENCH_WORK']) == pathlib.Path.cwd(); pathlib.Path(os.environ['BENCH_OUTPUT'],'result.json').write_text(json.dumps({'ok': True}))"
        result = run_command(self.task, self.manifest, [sys.executable, "-c", code], self.root, "run-001", timeout=10)
        run = self.root / "run-001"
        self.assertEqual(result["state"], "completed")
        self.assertFalse(result["formal_evaluation_eligible"])
        self.assertTrue((run / "control/task_spec.json").is_file())
        self.assertTrue((run / "control/input_manifest.json").is_file())
        self.assertTrue((run / "control/output_contract.json").is_file())
        self.assertTrue((run / "control/task_prompt.md").is_file())
        self.assertNotIn("output_artifacts", json.loads((run / "control/task_spec.json").read_text()))
        self.assertTrue((run / "record/execution.log").is_file())
        self.assertEqual(json.loads((run / "work/result.json").read_text())["ok"], True)
        self.assertTrue((run / "record/run_result.json").is_file())
        self.assertFalse((run / "agent/task_spec.json").exists())

    def test_declared_inputs_are_linked_into_run_input_view(self):
        source_dir = Path(self.tmp.name) / "waveforms"
        source_dir.mkdir()
        source_file = Path(self.tmp.name) / "stations.xml"
        source_file.write_text("station", encoding="utf-8")
        manifest = {
            "schema_version": 1,
            "case_id": "synthetic_case",
            "entries": [
                {"id": "waveforms", "path": str(source_dir), "link_path": "waveforms", "path_type": "directory",
                 "data_type": "waveform", "format": "miniSEED", "read_only": True},
                {"id": "stations", "path": str(source_file), "link_path": "station.xml", "path_type": "file",
                 "data_type": "station_metadata", "format": "StationXML", "read_only": True},
                {"id": "metadata", "path": str(source_file), "link_path": "metadata.json", "path_type": "file",
                 "data_type": "metadata", "format": "JSON", "read_only": True},
            ],
        }
        manifest_path = Path(self.tmp.name) / "links-manifest.json"
        manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
        code = (
            "import os,pathlib; p=pathlib.Path(os.environ['BENCH_INPUT']); "
            "assert p.is_dir(); assert (p/'waveforms').is_symlink(); "
            "assert (p/'station.xml').is_symlink(); "
            "assert pathlib.Path(os.environ['BENCH_OUTPUT'],'result.txt').write_text('ok')"
        )
        result = run_command(self.task, manifest_path, [sys.executable, "-c", code],
                             self.root, "run-links", timeout=10)
        self.assertEqual(result["state"], "completed")
        run = self.root / "run-links"
        self.assertTrue((run / "work/input/waveforms").is_symlink())
        self.assertTrue((run / "work/input/station.xml").is_symlink())

    def test_nonzero_command_is_recorded(self):
        result = run_command(self.task, self.manifest, [sys.executable, "-c", "raise SystemExit(7)"], self.root, "run-002", timeout=10)
        self.assertEqual(result["state"], "execution_failed")
        self.assertEqual(result["failure_reason"], "nonzero_exit")
        self.assertEqual(result["exit_code"], 7)

    def test_capacity_failure_is_retryable(self):
        code = "print('Selected model is at capacity', flush=True); raise SystemExit(1)"
        result = run_command(self.task, self.manifest, [sys.executable, "-c", code], self.root, "run-capacity", timeout=10)
        self.assertEqual(result["state"], "execution_retryable")
        self.assertEqual(result["failure_reason"], "capacity")
        self.assertTrue(result["retryable"])

    def test_usage_limit_is_not_retryable(self):
        code = "print(\"You've hit your usage limit\", flush=True); raise SystemExit(1)"
        result = run_command(self.task, self.manifest, [sys.executable, "-c", code], self.root, "run-limit", timeout=10)
        self.assertEqual(result["state"], "execution_failed")
        self.assertEqual(result["failure_reason"], "usage_limit")
        self.assertFalse(result["retryable"])

    def test_retryable_run_can_be_resumed_and_archives_previous_attempt(self):
        first = [sys.executable, "-c", "print('Selected model is at capacity', flush=True); raise SystemExit(1)"]
        result = run_command(self.task, self.manifest, first, self.root, "run-resume", timeout=10)
        self.assertEqual(result["state"], "execution_retryable")
        code = "import json,os,pathlib; pathlib.Path(os.environ['BENCH_OUTPUT'],'result.json').write_text(json.dumps({'ok': True}))"
        resumed = run_command(self.task, self.manifest, [sys.executable, "-c", code], self.root,
                              "run-resume", timeout=10, resume=True)
        self.assertEqual(resumed["state"], "completed")
        run = self.root / "run-resume"
        self.assertTrue((run / "attempts/attempt-001/record/execution.log").is_file())
        self.assertTrue((run / "work/result.json").is_file())

    def test_timeout_kills_command(self):
        result = run_command(self.task, self.manifest, [sys.executable, "-c", "import time; time.sleep(10)"], self.root, "run-003", timeout=0.1)
        self.assertEqual(result["state"], "execution_timeout")
        self.assertEqual(result["failure_reason"], "timeout")

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
