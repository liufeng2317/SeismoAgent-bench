import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


class CodexCliTests(unittest.TestCase):
    def test_run_codex_uses_host_direct_adapter_and_captures_transcript(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            task = base / "task.json"
            manifest = base / "manifest.json"
            fake = base / "fake-codex"
            run_root = base / "runs"
            task.write_text(json.dumps({
                "task_id": "codex-cli-smoke", "version": "1", "task_prompt": "smoke",
                "input_types": ["metadata"],
                "output_artifacts": [{"id": "result", "path": "result.json", "kind": "json", "required": True}],
                "scorer": {"name": "artifact-contract", "version": "1"},
            }), encoding="utf-8")
            manifest.write_text(json.dumps({
                "schema_version": 1, "case_id": "synthetic", "entries": [
                    {"id": "metadata", "path": "/tmp/metadata.json", "data_type": "metadata", "format": "JSON", "read_only": True}
                ],
            }), encoding="utf-8")
            fake.write_text(
                "#!" + sys.executable + "\n"
                "import json, os, pathlib\n"
                "print(json.dumps({'type': 'assistant', 'text': 'OK'}), flush=True)\n"
                "pathlib.Path(os.environ['BENCH_OUTPUT'], 'result.json').write_text(json.dumps({'ok': True}))\n",
                encoding="utf-8",
            )
            fake.chmod(0o755)
            command = [sys.executable, "-m", "SeismoAgentBench", "run-codex",
                       "--task", str(task), "--manifest", str(manifest),
                       "--agent-name", "codex-smoke", "--agent-version", "1",
                       "--run-root", str(run_root), "--run-id", "run-001",
                       "--codex-bin", str(fake), "--model", "test-model",
                       "--codex-home", "/tmp/external-codex-home",
                       "--prompt", "write the result artifact"]
            result = subprocess.run(command, capture_output=True, text=True, check=False)
            self.assertEqual(result.returncode, 0, result.stderr)
            payload = json.loads(result.stdout)
            run = run_root / "run-001"
            self.assertEqual(payload["run"]["state"], "completed")
            self.assertEqual(payload["codex"]["transcript"], "transcript.jsonl")
            self.assertIn("CODEX_HOME", payload["codex"]["injected_environment_keys"])
            self.assertIn('"text": "OK"', (run / "record/transcript.jsonl").read_text())
            self.assertTrue((run / "record/codex_command.json").is_file())
            prompt = (run / "control/agent_prompt.md").read_text()
            self.assertIn("## Task", prompt)
            self.assertIn("## Input data", prompt)
            self.assertIn("## Required outputs", prompt)
            self.assertIn("write the result artifact", prompt)
            self.assertNotIn("external-codex-home", (run / "record/codex_command.json").read_text())

    def test_run_codex_supports_canonical_campaign_layout(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            task = base / "task.json"
            manifest = base / "manifest.json"
            fake = base / "fake-codex"
            root = base / "runs"
            task.write_text(json.dumps({
                "task_id": "layout-task", "version": "1", "task_prompt": "smoke",
                "input_types": ["metadata"],
                "output_artifacts": [{"id": "result", "path": "result.json", "kind": "json", "required": True}],
                "scorer": {"name": "artifact-contract", "version": "1"},
            }), encoding="utf-8")
            manifest.write_text(json.dumps({
                "schema_version": 1, "case_id": "synthetic", "entries": [
                    {"id": "metadata", "path": "/tmp/metadata.json", "data_type": "metadata", "format": "JSON", "read_only": True}
                ],
            }), encoding="utf-8")
            fake.write_text(
                "#!" + sys.executable + "\n"
                "import json, os, pathlib\n"
                "print(json.dumps({'type': 'assistant', 'text': 'OK'}), flush=True)\n"
                "pathlib.Path(os.environ['BENCH_OUTPUT'], 'result.json').write_text(json.dumps({'ok': True}))\n",
                encoding="utf-8",
            )
            fake.chmod(0o755)
            command = [sys.executable, "-m", "SeismoAgentBench", "run-codex",
                       "--task", str(task), "--manifest", str(manifest),
                       "--agent-name", "codex-smoke", "--agent-version", "1",
                       "--run-root", str(root), "--run-id", "run-001",
                       "--campaign-id", "campaign-001", "--variant", "base",
                       "--codex-bin", str(fake), "--model", "test-model",
                       "--prompt", "write the result artifact"]
            result = subprocess.run(command, capture_output=True, text=True, check=False)
            self.assertEqual(result.returncode, 0, result.stderr)
            unit = root / "layout-task/run-001"
            self.assertTrue((unit / "work/result.json").is_file())
            self.assertEqual(json.loads(result.stdout)["run_layout"]["unit_root"], str(unit))

    def test_run_codex_retries_capacity_with_bounded_attempts(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            task = base / "task.json"
            manifest = base / "manifest.json"
            fake = base / "fake-codex"
            counter = base / "counter"
            run_root = base / "runs"
            task.write_text(json.dumps({
                "task_id": "retry-task", "version": "1", "task_prompt": "smoke",
                "input_types": ["metadata"],
                "output_artifacts": [{"id": "result", "path": "result.json", "kind": "json", "required": True}],
                "scorer": {"name": "artifact-contract", "version": "1"},
            }), encoding="utf-8")
            manifest.write_text(json.dumps({
                "schema_version": 1, "case_id": "synthetic", "entries": [
                    {"id": "metadata", "path": "/tmp/metadata.json", "data_type": "metadata", "format": "JSON", "read_only": True}
                ],
            }), encoding="utf-8")
            fake.write_text(
                "#!" + sys.executable + "\n"
                "import json, os, pathlib\n"
                f"counter=pathlib.Path({str(counter)!r})\n"
                "if not counter.exists():\n"
                " counter.write_text('1')\n"
                " print('Selected model is at capacity', flush=True)\n"
                " raise SystemExit(1)\n"
                "print(json.dumps({'type': 'assistant', 'text': 'OK'}), flush=True)\n"
                "pathlib.Path(os.environ['BENCH_OUTPUT'], 'result.json').write_text(json.dumps({'ok': True}))\n",
                encoding="utf-8",
            )
            fake.chmod(0o755)
            command = [sys.executable, "-m", "SeismoAgentBench", "run-codex",
                       "--task", str(task), "--manifest", str(manifest),
                       "--agent-name", "codex-retry", "--agent-version", "1",
                       "--run-root", str(run_root), "--run-id", "run-001",
                       "--codex-bin", str(fake), "--model", "test-model",
                       "--prompt", "write the result artifact", "--max-attempts", "2"]
            result = subprocess.run(command, capture_output=True, text=True, check=False)
            self.assertEqual(result.returncode, 0, result.stderr)
            unit = run_root / "run-001"
            payload = json.loads(result.stdout)
            self.assertEqual(payload["run"]["state"], "completed")
            self.assertTrue((unit / "attempts/attempt-001/record/execution.log").is_file())
            self.assertTrue((unit / "work/result.json").is_file())


if __name__ == "__main__":
    unittest.main()
