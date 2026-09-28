from pathlib import Path
import unittest

from SeismoAgentBench.execution import CodexCommandError, CodexCommandSpec


class CodexCommandTests(unittest.TestCase):
    def test_builds_a_host_direct_json_command(self):
        spec = CodexCommandSpec(
            codex_bin="/opt/codex/bin/codex",
            model="gpt-6-astra",
            working_dir="/tmp/seismo-run/work",
            prompt="Read BENCH_INPUT_MANIFEST and write output files.",
        )
        self.assertEqual(spec.argv(), [
            "/opt/codex/bin/codex", "exec", "--json", "--ephemeral",
            "--skip-git-repo-check", "--model", "gpt-6-astra",
            "-C", "/tmp/seismo-run/work", "-c", 'model_reasoning_effort="medium"',
            "--dangerously-bypass-approvals-and-sandbox",
            "Read BENCH_INPUT_MANIFEST and write output files.",
        ])
        record = spec.record()
        self.assertFalse(record["credentials_included"])
        self.assertTrue(record["host_direct"])

    def test_rejects_relative_working_directory(self):
        with self.assertRaises(CodexCommandError):
            CodexCommandSpec("codex", "gpt-6-astra", "relative", "test")

    def test_rejects_unknown_reasoning_effort(self):
        with self.assertRaises(CodexCommandError):
            CodexCommandSpec("codex", "gpt-6-astra", "/tmp/work", "test", reasoning_effort="turbo")


if __name__ == "__main__":
    unittest.main()
