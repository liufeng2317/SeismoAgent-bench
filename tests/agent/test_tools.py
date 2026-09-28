import unittest

from SeismoAgentBench.agent import ToolRecordError, ToolRunRecord, ToolSpec


class ToolRecordTests(unittest.TestCase):
    def test_tool_and_run_records_are_serializable(self):
        tool = ToolSpec(
            name="phase-picker",
            version="1.0",
            executable="phase-picker",
            parameters={"threshold": 0.5},
            model_id="model-v1",
            auxiliary_files=("models/model.bin",),
        )
        record = ToolRunRecord(
            tool=tool,
            status="completed",
            started_at="2026-01-01T00:00:00Z",
            finished_at="2026-01-01T00:00:01Z",
            exit_code=0,
            stdout_path="logs/tool.stdout",
            stderr_path="logs/tool.stderr",
        ).record()
        self.assertEqual(record["tool"]["model_id"], "model-v1")
        self.assertEqual(record["status"], "completed")

    def test_invalid_tool_identity_and_parameters_are_rejected(self):
        with self.assertRaises(ToolRecordError):
            ToolSpec("bad name", "1", "tool")
        with self.assertRaises(ToolRecordError):
            ToolSpec("tool", "1", "tool", parameters={"bad": object()})

    def test_invalid_status_and_exit_code_are_rejected(self):
        tool = ToolSpec("tool", "1", "tool")
        with self.assertRaisesRegex(ToolRecordError, "status"):
            ToolRunRecord(tool, "running")
        with self.assertRaisesRegex(ToolRecordError, "exit_code"):
            ToolRunRecord(tool, "failed", exit_code="1")


if __name__ == "__main__":
    unittest.main()
