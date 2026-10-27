import sys
import tempfile
import unittest
from pathlib import Path

from SeismoAgentBench.execution import probe_executable_version, tools_snapshot


class ExecutableVersionTests(unittest.TestCase):
    def test_records_version_without_shell_or_secrets(self):
        record = probe_executable_version(sys.executable, ("-V",))
        self.assertEqual(record["status"], "ok")
        self.assertIn("Python", record["version"])
        self.assertNotIn("api_key", record)

    def test_unavailable_executable_is_metadata_only(self):
        record = probe_executable_version("/does/not/exist")
        self.assertEqual(record["status"], "unavailable")

    def test_tools_snapshot_outside_a_repository_is_null(self):
        with tempfile.TemporaryDirectory() as tmp:
            record = tools_snapshot(Path(tmp))
        self.assertIsNone(record["commit"])
        self.assertIsNone(record["dirty"])

    def test_tools_snapshot_of_the_bundled_library(self):
        record = tools_snapshot()
        if record["commit"] is not None:          # git checkout present
            self.assertRegex(record["commit"], r"^[0-9a-f]{40}$")
            self.assertIsInstance(record["dirty"], bool)


if __name__ == "__main__":
    unittest.main()
