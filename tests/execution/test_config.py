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
                "harness: codex\nmodel: null\nruntime:\n  mode: host-direct\n",
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

    def test_accepts_executable_version_and_auth_metadata(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "agent.yaml"
            source.write_text(
                "harness: codex\nexecutable: codex\nversion_command: [--version]\n"
                "auth:\n  mode: external_profile\nruntime: {}\n",
                encoding="utf-8",
            )
            config = load_agent_config(source)
            self.assertEqual(config["auth"]["mode"], "external_profile")

    def test_rejects_legacy_runtime_fields(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "agent.yaml"
            source.write_text("harness: codex\nconfig:\n  reasoning_effort: low\n", encoding="utf-8")
            with self.assertRaises(AgentConfigError):
                load_agent_config(source)

    def test_rejects_unknown_auth_metadata(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "agent.yaml"
            source.write_text("harness: codex\nauth:\n  mode: external_profile\n  profile: old\n", encoding="utf-8")
            with self.assertRaises(AgentConfigError):
                load_agent_config(source)

    def test_rejects_unknown_auth_mode(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "agent.yaml"
            source.write_text("harness: codex\nauth:\n  mode: token_file\n", encoding="utf-8")
            with self.assertRaises(AgentConfigError):
                load_agent_config(source)


if __name__ == "__main__":
    unittest.main()
