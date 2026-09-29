import json
from pathlib import Path
import tempfile
import unittest

from SeismoAgentBench.reporting import write_environment_record, write_evaluation_report


RESULT = {
    "run_id": "run-001",
    "task_id": "task-001",
    "task_version": "1",
    "state": "completed",
    "execution_profile": "trusted-development",
    "formal_evaluation_eligible": False,
}


class ReportingTests(unittest.TestCase):
    def test_records_do_not_copy_process_environment(self):
        with tempfile.TemporaryDirectory() as tmp:
            run = Path(tmp)
            (run / "work").mkdir(parents=True)
            write_environment_record(run, RESULT)
            write_evaluation_report(run, RESULT)
            environment = json.loads((run / "record/environment.json").read_text())
            self.assertNotIn("environment", environment)
            report = json.loads((run / "evaluation/report.json").read_text())
            self.assertEqual(report["agent"], None)
            self.assertNotIn("agent_command", report["records"])


if __name__ == "__main__":
    unittest.main()
