from pathlib import Path
import tempfile
import unittest

from SeismoAgentBench.execution import AgentConfigError, load_agent_config, write_agent_config_snapshot


class AgentConfigTests(unittest.TestCase):
    def test_loads_and_snapshots_non_secret_config(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            source = base / "agent.yaml"
            source.write_text(
                "harness: codex\nmodel: null\nprovider: direct\nconfig:\n  isolation: host-direct\n  api_key: null\n",
                encoding="utf-8",
            )
            config = load_agent_config(source)
            target = write_agent_config_snapshot(base / "run", config)
            self.assertTrue(target.is_file())
            self.assertIn("host-direct", target.read_text(encoding="utf-8"))

    def test_rejects_nonempty_secret_field(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "agent.yaml"
            source.write_text("harness: codex\napi_key: do-not-record\n", encoding="utf-8")
            with self.assertRaises(AgentConfigError):
                load_agent_config(source)

    def test_rejects_unknown_top_level_field(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "agent.yaml"
            source.write_text("harness: codex\nunknown: true\n", encoding="utf-8")
            with self.assertRaises(AgentConfigError):
                load_agent_config(source)


if __name__ == "__main__":
    unittest.main()
