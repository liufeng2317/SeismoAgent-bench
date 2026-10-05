import json
from pathlib import Path
import tempfile
import unittest

from SeismoAgentBench.reporting.transcript import (summarize_usage, write_event_jsonl,
                                                   write_human_log, write_transcript)


class TranscriptTests(unittest.TestCase):
    def test_normalizes_public_events_and_redacts_reasoning(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            log = root / "execution.log"
            log.write_text("\n".join([
                json.dumps({"type": "thread.started", "thread_id": "t1"}),
                json.dumps({"type": "item.completed", "item": {"id": "m1", "type": "agent_message", "text": "done"}}),
                json.dumps({"type": "item.completed", "item": {"id": "r1", "type": "reasoning", "text": "private"}}),
                "plain log line",
            ]) + "\n", encoding="utf-8")
            counts = write_transcript(log, root / "transcript.jsonl")
            rows = [json.loads(line) for line in (root / "transcript.jsonl").read_text().splitlines()]
            self.assertEqual(counts["agent_message"], 1)
            self.assertEqual(rows[1]["text"], "done")
            self.assertNotIn("private", (root / "transcript.jsonl").read_text())
            self.assertEqual(rows[-1]["event_type"], "log_line")

    def test_human_log_has_timestamps_and_readable_event_summaries(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            raw = root / "execution.jsonl"
            raw.write_text(json.dumps({
                "type": "item.completed",
                "item": {"type": "agent_message", "text": "finished"},
            }) + "\nplain output\n", encoding="utf-8")
            write_human_log(raw, root / "execution.log")
            lines = (root / "execution.log").read_text(encoding="utf-8").splitlines()
            self.assertRegex(lines[0], r"^\[\d{4}-\d{2}-\d{2}T.*Z\] agent_message: finished$")
            self.assertIn("stdout: plain output", lines[1])

    def test_event_log_is_strict_jsonl_for_plain_process_output(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            raw = root / "execution.raw.log"
            raw.write_text("plain output\n{" + '"type":"turn.started"' + "}\n", encoding="utf-8")
            write_event_jsonl(raw, root / "execution.jsonl")
            rows = [json.loads(line) for line in (root / "execution.jsonl").read_text().splitlines()]
            self.assertEqual(rows[0], {"type": "console.line", "text": "plain output"})
            self.assertEqual(rows[1]["type"], "turn.started")

    def test_summarizes_provider_usage_without_private_content(self):
        with tempfile.TemporaryDirectory() as tmp:
            log = Path(tmp) / "execution.jsonl"
            log.write_text("\n".join([
                json.dumps({"type": "turn.completed", "usage": {
                    "input_tokens": 10, "output_tokens": 4,
                    "cached_input_tokens": 2, "total_tokens": 14,
                }}),
                json.dumps({"type": "turn.completed", "usage": {
                    "prompt_tokens": 3, "completion_tokens": 5,
                    "reasoning_tokens": 1,
                }}),
            ]) + "\n", encoding="utf-8")
            summary = summarize_usage(log)
            self.assertEqual(summary["turns"], 2)
            self.assertEqual(summary["usage_events"], 2)
            self.assertEqual(summary["usage"]["input_tokens"], 13)
            self.assertEqual(summary["usage"]["output_tokens"], 9)
            self.assertEqual(summary["usage"]["cached_input_tokens"], 2)
            self.assertEqual(summary["usage"]["reasoning_tokens"], 1)


if __name__ == "__main__":
    unittest.main()
