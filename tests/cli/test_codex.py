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
                "task_id": "codex-cli-smoke", "version": "1", "objective": "smoke",
                "input_kinds": ["metadata"],
                "output_artifacts": [{"id": "result", "path": "result.json", "kind": "json", "required": True}],
                "scorer": {"name": "artifact-contract", "version": "1"},
            }), encoding="utf-8")
            manifest.write_text(json.dumps({
                "schema_version": 1, "case_id": "synthetic", "entries": [
                    {"id": "metadata", "path": "/tmp/metadata.json", "kind": "metadata", "read_only": True}
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
            self.assertEqual(payload["run"]["state"], "scored")
            self.assertEqual(payload["codex"]["transcript"], "transcript.jsonl")
            self.assertIn("CODEX_HOME", payload["codex"]["injected_environment_keys"])
            self.assertIn('"text": "OK"', (run / "transcript.jsonl").read_text())
            self.assertTrue((run / "codex_command.json").is_file())
            self.assertNotIn("external-codex-home", (run / "codex_command.json").read_text())


if __name__ == "__main__":
    unittest.main()
