import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from tests.task_helpers import write_task_package


class CodexCliTests(unittest.TestCase):
    def test_run_codex_can_select_executable_and_model_from_agent_config(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            task = base / "task.json"
            manifest = base / "manifest.json"
            config = base / "agent.yaml"
            fake = base / "fake-codex"
            run_root = base / "runs"
            write_task_package(task, {
                "task_id": "codex-config-smoke", "version": "1",
                "input_requirements": [{"id": "metadata", "data_type": "metadata", "required": True}],
                "output_artifacts": [{"id": "result", "path": "result.json", "kind": "json", "required": True}],
            }, "smoke")
            manifest.write_text(json.dumps({"schema_version": 1, "case_id": "synthetic",
                "entries": [{"id": "metadata", "path": "/tmp/metadata.json", "type": "file"}]}),
                encoding="utf-8")
            fake.write_text(
                "#!" + sys.executable + "\n"
                "import json, os, pathlib\n"
                "pathlib.Path(os.environ['BENCH_OUTPUT'], 'result.json').write_text(json.dumps({'ok': True}))\n",
                encoding="utf-8")
            fake.chmod(0o755)
            config.write_text(
                f"harness: codex\nexecutable: {fake}\nmodel: config-model\n"
                "version_command: [--version]\nconfig:\n  reasoning_effort: low\n",
                encoding="utf-8")
            command = [sys.executable, "-m", "SeismoAgentBench", "run-codex",
                       "--task", str(task), "--manifest", str(manifest),
                       "--agent-name", "codex-config", "--agent-version", "1",
                       "--run-root", str(run_root), "--run-id", "run-001",
                       "--agent-config", str(config)]
            result = subprocess.run(command, capture_output=True, text=True, check=False)
            self.assertEqual(result.returncode, 0, result.stderr)
            payload = json.loads(result.stdout)
            self.assertEqual(payload["run"]["state"], "completed")
            self.assertEqual(payload["codex"]["executable_version"]["status"], "unavailable")
            provenance = json.loads((run_root / "run-001/record/provenance.json").read_text())
            self.assertEqual(provenance["launcher"]["model"], "config-model")
            self.assertEqual(provenance["launcher"]["reasoning_effort"], "low")

    def test_run_codex_uses_host_direct_adapter_and_captures_execution_records(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            task = base / "task.json"
            manifest = base / "manifest.json"
            fake = base / "fake-codex"
            run_root = base / "runs"
            write_task_package(task, {
                "task_id": "codex-cli-smoke", "version": "1",
                "input_requirements": [{"id": "metadata", "data_type": "metadata", "required": True}],
                "evaluation": {"scorers": [{"name": "artifact-contract", "version": "1"}]},
                "output_artifacts": [{"id": "result", "path": "result.json", "kind": "json", "required": True}],
            }, "smoke")
            manifest.write_text(json.dumps({
                "schema_version": 1, "case_id": "synthetic", "entries": [
                    {"id": "metadata", "path": "/tmp/metadata.json", "type": "file", "notes": "metadata"}
                ],
            }), encoding="utf-8")
            fake.write_text(
                "#!" + sys.executable + "\n"
                "import json, os, pathlib\n"
                "print(json.dumps({'type': 'item.completed', 'item': {'type': 'agent_message', 'text': 'OK'}}), flush=True)\n"
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
            self.assertEqual(payload["codex"]["execution_log"], "execution.log")
            self.assertEqual(payload["codex"]["execution_jsonl"], "execution.jsonl")
            self.assertEqual(payload["codex"]["provenance"], "provenance.json")
            self.assertIn("CODEX_HOME", payload["codex"]["injected_environment_keys"])
            event_log = [json.loads(line) for line in (run / "record/execution.jsonl").read_text().splitlines()]
            self.assertTrue(any(item.get("item", {}).get("type") == "agent_message" for item in event_log))
            self.assertTrue((run / "record/provenance.json").is_file())
            provenance = json.loads((run / "record/provenance.json").read_text())
            self.assertEqual(provenance["launcher"]["argv"][-1], "<BENCH_AGENT_PROMPT>")
            prompt = (run / "control/agent_prompt.md").read_text()
            self.assertIn("# Task: codex-cli-smoke", prompt)
            self.assertNotIn("# SeismoAgentBench Task", prompt)
            self.assertIn("## Runtime context", prompt)
            self.assertIn("## Structured output hints", prompt)
            self.assertIn("write the result artifact", prompt)
            self.assertNotIn("external-codex-home", (run / "record/provenance.json").read_text())

    def test_run_codex_supports_canonical_campaign_layout(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            task = base / "task.json"
            manifest = base / "manifest.json"
            fake = base / "fake-codex"
            root = base / "runs"
            write_task_package(task, {
                "task_id": "layout-task", "version": "1",
                "input_requirements": [{"id": "metadata", "data_type": "metadata", "required": True}],
                "evaluation": {"scorers": [{"name": "artifact-contract", "version": "1"}]},
                "output_artifacts": [{"id": "result", "path": "result.json", "kind": "json", "required": True}],
            }, "smoke")
            manifest.write_text(json.dumps({
                "schema_version": 1, "case_id": "synthetic", "entries": [
                    {"id": "metadata", "path": "/tmp/metadata.json", "type": "file", "notes": "metadata"}
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
            write_task_package(task, {
                "task_id": "retry-task", "version": "1",
                "input_requirements": [{"id": "metadata", "data_type": "metadata", "required": True}],
                "evaluation": {"scorers": [{"name": "artifact-contract", "version": "1"}]},
                "output_artifacts": [{"id": "result", "path": "result.json", "kind": "json", "required": True}],
            }, "smoke")
            manifest.write_text(json.dumps({
                "schema_version": 1, "case_id": "synthetic", "entries": [
                    {"id": "metadata", "path": "/tmp/metadata.json", "type": "file", "notes": "metadata"}
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
