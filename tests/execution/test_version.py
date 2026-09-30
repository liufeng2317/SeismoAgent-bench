import sys
import unittest

from SeismoAgentBench.execution import probe_executable_version


class ExecutableVersionTests(unittest.TestCase):
    def test_records_version_without_shell_or_secrets(self):
        record = probe_executable_version(sys.executable, ("-V",))
        self.assertEqual(record["status"], "ok")
        self.assertIn("Python", record["version"])
        self.assertNotIn("api_key", record)

    def test_unavailable_executable_is_metadata_only(self):
        record = probe_executable_version("/does/not/exist")
        self.assertEqual(record["status"], "unavailable")


if __name__ == "__main__":
    unittest.main()
