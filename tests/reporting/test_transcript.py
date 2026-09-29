import json
from pathlib import Path
import tempfile
import unittest

from SeismoAgentBench.reporting.transcript import write_transcript


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


if __name__ == "__main__":
    unittest.main()
