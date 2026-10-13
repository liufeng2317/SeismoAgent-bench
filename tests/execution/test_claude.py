import unittest

from SeismoAgentBench.execution import ClaudeCommandError, ClaudeCommandSpec


class ClaudeCommandTests(unittest.TestCase):
    def test_builds_a_host_direct_print_command(self):
        spec = ClaudeCommandSpec(
            claude_bin="/opt/claude/bin/claude",
            model="glm-5.3",
            working_dir="/tmp/seismo-run/work",
            prompt="Read BENCH_INPUT_MANIFEST and write output files.",
        )
        self.assertEqual(spec.argv(), [
            "/opt/claude/bin/claude", "--print", "--verbose",
            "--output-format", "stream-json", "--model", "glm-5.3",
            "--dangerously-skip-permissions",
            "Read BENCH_INPUT_MANIFEST and write output files.",
        ])
        record = spec.record()
        self.assertFalse(record["credentials_included"])
        self.assertTrue(record["host_direct"])

    def test_rejects_relative_working_directory(self):
        with self.assertRaises(ClaudeCommandError):
            ClaudeCommandSpec("claude", "glm-5.3", "relative", "test")

    def test_rejects_invalid_max_turns(self):
        for value in (0, -1, True, "many"):
            with self.subTest(value=value):
                with self.assertRaises(ClaudeCommandError):
                    ClaudeCommandSpec("claude", None, "/tmp/work", "test", max_turns=value)

    def test_can_use_endpoint_default_model_routing(self):
        spec = ClaudeCommandSpec("/opt/claude/bin/claude", None, "/tmp/work", "test",
                                 max_turns=40, bypass_permissions=False)
        argv = spec.argv()
        self.assertNotIn("--model", argv)
        self.assertNotIn("--dangerously-skip-permissions", argv)
        self.assertEqual(argv[-1], "test")
        self.assertEqual(spec.record()["max_turns"], 40)


if __name__ == "__main__":
    unittest.main()
