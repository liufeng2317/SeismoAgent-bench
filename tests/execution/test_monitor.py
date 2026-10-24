import json
import os
from pathlib import Path
import socket
import tempfile
import unittest

from SeismoAgentBench.execution.monitor import finalize_run, run_status


def _proc_start_ticks(pid: int) -> int:
    fields = Path(f"/proc/{pid}/stat").read_text(encoding="utf-8").rsplit(")", 1)[1].split()
    return int(fields[19])


class MonitorTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.run = Path(self.tmp.name) / "runs" / "abandoned"
        record = self.run / "record"
        (self.run / "work").mkdir(parents=True)
        record.mkdir(parents=True)
        (self.run / "control").mkdir()
        (record / "run_result.json").write_text(json.dumps({
            "run_id": "abandoned",
            "state": "running",
            "started_at": "2026-10-15T02:03:20+00:00",
            "timeout_s": 86400,
        }), encoding="utf-8")
        (self.run / "control" / "output_contract.json").write_text(json.dumps({
            "schema_version": 1,
            "artifacts": [{"id": "result", "path": "result.json", "kind": "json", "required": True}],
        }), encoding="utf-8")
        (self.run / "work" / "result.json").write_text('{"ok": true}', encoding="utf-8")
        (record / "execution.log").write_text(
            "[2026-10-15T02:03:22.207Z] system/init\n"
            "[2026-10-15T08:34:00.000Z] tool_progress Bash elapsed=120s\n", encoding="utf-8")
        (record / "execution.jsonl").write_text(
            '{"type": "system", "subtype": "init"}\n', encoding="utf-8")

    def tearDown(self):
        self.tmp.cleanup()

    def _write_pid(self, pid: int, ticks: int) -> None:
        (self.run / "record" / "runner.pid").write_text(json.dumps({
            "pid": pid,
            "hostname": socket.gethostname(),
            "process_start_time": ticks,
            "recorded_at": "2026-10-15T02:03:20+00:00",
        }), encoding="utf-8")

    def test_status_reports_dead_runner_artifacts_and_last_event(self):
        self._write_pid(999999999, 12345)
        status = run_status(self.run)
        self.assertEqual(status["state"], "running")
        self.assertFalse(status["runner_pid_alive"])
        self.assertEqual(status["last_event_at"], "2026-10-15T08:34:00.000Z")
        self.assertIsInstance(status["seconds_since_last_event"], (int, float))
        self.assertEqual(status["artifacts"],
                         [{"id": "result", "path": "result.json", "present": True}])

    def test_finalize_closes_abandoned_record_and_cleans_runtime_root(self):
        self._write_pid(999999999, 12345)
        stale = Path(tempfile.mkdtemp(prefix="seismoagentbench-abandoned-"))
        report = finalize_run(self.run)
        self.assertEqual(report["state"], "interrupted")
        self.assertEqual(report["failure_reason"], "runner_lost")
        self.assertIn("finished_at", report)
        self.assertFalse(stale.exists())
        self.assertIn(report["stale_runtime_roots_removed"][0], stale.name)
        usage = json.loads((self.run / "record" / "usage_summary.json").read_text(encoding="utf-8"))
        self.assertEqual(usage["schema_version"], 1)
        closed = json.loads((self.run / "record" / "run_result.json").read_text(encoding="utf-8"))
        self.assertEqual(closed["state"], "interrupted")
        with self.assertRaises(ValueError):
            finalize_run(self.run)  # no longer live

    def test_finalize_refuses_live_runner_without_force(self):
        self._write_pid(os.getpid(), _proc_start_ticks(os.getpid()))
        with self.assertRaises(ValueError):
            finalize_run(self.run)
        # A reused pid (same number, different start time) must read as dead.
        self._write_pid(os.getpid(), _proc_start_ticks(os.getpid()) + 1)
        report = finalize_run(self.run)
        self.assertEqual(report["state"], "interrupted")


if __name__ == "__main__":
    unittest.main()
