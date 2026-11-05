import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from tests.task_helpers import write_input_manifest, write_task_package

SECRET = "secret-token-do-not-record"


class ClaudeCliTests(unittest.TestCase):
    def test_run_claude_injects_env_file_credentials_and_records_provenance(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            task = base / "task.json"
            manifest = base / "manifest.json"
            fake = base / "fake-claude"
            env_file = base / "claude.env"
            run_root = base / "runs"
            write_task_package(task, {
                "task_id": "claude-cli-smoke", "version": "1",
                "input_requirements": [{"id": "metadata", "data_type": "metadata", "required": True}],
                "evaluation": {"scorers": [{"name": "artifact-contract", "version": "1"}]},
                "output_artifacts": [{"id": "result", "path": "result.json", "kind": "json", "required": True}],
            }, "smoke")
            write_input_manifest(manifest, {
                "schema_version": 1, "case_id": "synthetic", "entries": [
                    {"id": "metadata", "path": "/tmp/metadata.json", "type": "file", "notes": "metadata"}
                ],
            })
            # The fake agent fails unless the env-file credentials reached it.
            fake.write_text(
                "#!" + sys.executable + "\n"
                "import json, os, pathlib\n"
                "assert os.environ.get('ANTHROPIC_BASE_URL'), 'missing ANTHROPIC_BASE_URL'\n"
                "assert os.environ.get('ANTHROPIC_AUTH_TOKEN'), 'missing ANTHROPIC_AUTH_TOKEN'\n"
                "print(json.dumps({'type': 'assistant', 'message': {'content': [{'type': 'text', 'text': 'OK'}]}}), flush=True)\n"
                "pathlib.Path(os.environ['BENCH_OUTPUT'], 'result.json').write_text(json.dumps({'ok': True}))\n",
                encoding="utf-8",
            )
            fake.chmod(0o755)
            env_file.write_text(
                "ANTHROPIC_BASE_URL=https://glm.example/api/anthropic\n"
                f"ANTHROPIC_AUTH_TOKEN={SECRET}\n", encoding="utf-8")
            command = [sys.executable, "-m", "SeismoAgentBench", "run-claude",
                       "--task", str(task), "--manifest", str(manifest),
                       "--agent-name", "claude-smoke", "--agent-version", "1",
                       "--run-root", str(run_root), "--run-id", "run-001",
                       "--claude-bin", str(fake), "--model", "glm-5.3",
                       "--max-turns", "5", "--env-file", str(env_file),
                       "--prompt", "write the result artifact"]
            result = subprocess.run(command, capture_output=True, text=True, check=False)
            self.assertEqual(result.returncode, 0, result.stderr)
            payload = json.loads(result.stdout)
            run = run_root / "run-001"
            self.assertEqual(payload["run"]["state"], "completed")
            self.assertEqual(payload["claude"]["provenance"], "provenance.json")
            self.assertTrue(payload["claude"]["authentication"]["env_file_configured"])
            self.assertNotIn("codex_home_configured", payload["claude"]["authentication"])
            provenance = json.loads((run / "record/provenance.json").read_text())
            self.assertEqual(provenance["command"]["kind"], "claude")
            self.assertEqual(provenance["launcher"]["model"], "glm-5.3")
            self.assertEqual(provenance["launcher"]["max_turns"], 5)
            self.assertEqual(provenance["launcher"]["prompt_via"], "stdin")  # the prompt is not on argv
            self.assertEqual(provenance["launcher"]["argv"][-1], "--dangerously-skip-permissions")
            self.assertIn("--dangerously-skip-permissions", provenance["launcher"]["argv"])
            for record_file in (run / "record").iterdir():
                self.assertNotIn(SECRET, record_file.read_text(errors="replace"),
                                 f"credential leaked into {record_file.name}")

    def test_run_claude_requires_an_env_file_for_authentication(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            task = base / "task.json"
            write_task_package(task, {
                "task_id": "claude-env-required", "version": "1",
                "input_requirements": [{"id": "metadata", "data_type": "metadata", "required": True}],
                "output_artifacts": [{"id": "result", "path": "result.json", "kind": "json", "required": True}],
            }, "smoke")
            command = [sys.executable, "-m", "SeismoAgentBench", "run-claude",
                       "--task", str(task),
                       "--agent-name", "claude-smoke", "--agent-version", "1",
                       "--run-root", str(base / "runs"), "--run-id", "run-001",
                       "--claude-bin", "/nonexistent/claude"]
            result = subprocess.run(command, capture_output=True, text=True, check=False)
            self.assertEqual(result.returncode, 2, result.stdout)
            payload = json.loads(result.stderr)
            self.assertEqual(payload["state"], "cli_error")
            self.assertIn("env-file", payload["error"])


if __name__ == "__main__":
    unittest.main()
