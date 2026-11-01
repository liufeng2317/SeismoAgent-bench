"""Status probes and forensic closure for run records.

These helpers operate on a run directory after (or during) execution. They
never launch an agent and never touch ``work/`` content; they only read
records, close out records the runner abandoned, and remove runtime roots
the runner no longer owns.
"""

from __future__ import annotations

from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
import shutil
import socket
import tempfile
from typing import Any

from SeismoAgentBench.execution.runner import preserve_runtime_home
from SeismoAgentBench.reporting.transcript import summarize_usage

_LIVE_STATES = {"preparing", "running"}
_LOG_PREFIX = re.compile(r"^\[(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?)Z\]")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _write(path: Path, value: Any) -> None:
    """Write JSON atomically: a reader never sees a truncated file while the heartbeat rewrites it."""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    tmp.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(tmp, path)


def _read_json(path: Path) -> dict[str, Any] | None:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return value if isinstance(value, dict) else None


def _parse_iso(value: Any) -> datetime | None:
    if not isinstance(value, str) or not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def _runner_pid_alive(run: Path) -> bool | None:
    """Decide runner liveness from record/runner.pid; None when undecidable."""
    record = _read_json(run / "record" / "runner.pid")
    if not record or not isinstance(record.get("pid"), int) or record["pid"] <= 0:
        return None
    hostname = record.get("hostname")
    if isinstance(hostname, str) and hostname != socket.gethostname():
        return None
    pid = record["pid"]
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    start = record.get("process_start_time")
    if isinstance(start, int):
        try:
            fields = Path(f"/proc/{pid}/stat").read_text(encoding="utf-8").rsplit(")", 1)[1].split()
            if int(fields[19]) != start:
                return False  # pid was reused by an unrelated process
        except (OSError, ValueError, IndexError):
            return None
    return True


def _last_log_timestamp(log: Path) -> str | None:
    try:
        with log.open("rb") as stream:
            stream.seek(0, os.SEEK_END)
            size = stream.tell()
            stream.seek(max(0, size - 8192))
            tail = stream.read()
    except OSError:
        return None
    stamp = None
    for line in tail.decode("utf-8", errors="replace").splitlines():
        match = _LOG_PREFIX.match(line)
        if match:
            stamp = match.group(1) + "Z"
    return stamp


def _contract_artifacts(run: Path) -> list[dict[str, Any]]:
    contract = _read_json(run / "control" / "output_contract.json") or {}
    artifacts: list[dict[str, Any]] = []
    for entry in contract.get("artifacts") or []:
        if not isinstance(entry, dict) or not isinstance(entry.get("path"), str):
            continue
        artifacts.append({
            "id": entry.get("id"),
            "path": entry["path"],
            "present": (run / "work" / entry["path"]).exists(),
        })
    return artifacts


def run_status(run_dir: str | Path) -> dict[str, Any]:
    """Read-only probe of one run directory for monitoring loops."""
    run = Path(run_dir)
    result = _read_json(run / "record" / "run_result.json")
    if result is None:
        raise ValueError(f"no readable record/run_result.json under {run}")
    state = result.get("state")
    log = run / "record" / "execution.log"
    last_event_at = _last_log_timestamp(log) or result.get("heartbeat_at")
    started = _parse_iso(result.get("started_at"))
    finished = _parse_iso(result.get("finished_at"))
    reference = finished or datetime.now(timezone.utc)
    elapsed_s = round((reference - started).total_seconds(), 1) if started else None
    idle_s = None
    if state in _LIVE_STATES:
        parsed = _parse_iso(last_event_at)
        if parsed:
            idle_s = round((datetime.now(timezone.utc) - parsed).total_seconds(), 1)
    try:
        log_bytes = log.stat().st_size
    except OSError:
        log_bytes = None
    return {
        "schema_version": 1,
        "run_dir": str(run),
        "run_id": result.get("run_id"),
        "state": state,
        "started_at": result.get("started_at"),
        "finished_at": result.get("finished_at"),
        "heartbeat_at": result.get("heartbeat_at"),
        "last_event_at": last_event_at,
        "elapsed_s": elapsed_s,
        "seconds_since_last_event": idle_s,
        "timeout_s": result.get("timeout_s"),
        "runner_pid_alive": _runner_pid_alive(run),
        "execution_log_bytes": log_bytes,
        "artifacts": _contract_artifacts(run),
        "probed_at": _now(),
    }


def _newest_work_mtime(work: Path) -> str | None:
    newest: float | None = None
    for dirpath, _dirnames, filenames in os.walk(work, followlinks=False):
        for name in filenames:
            try:
                mtime = (Path(dirpath) / name).stat().st_mtime
            except OSError:
                continue
            if newest is None or mtime > newest:
                newest = mtime
    if newest is None:
        return None
    return datetime.fromtimestamp(newest, timezone.utc).isoformat()


def _remove_stale_runtime_roots(run_id: Any, record: Path) -> list[str]:
    if not isinstance(run_id, str) or not run_id:
        return []
    removed = []
    for candidate in Path(tempfile.gettempdir()).glob(f"seismoagentbench-{run_id}-*"):
        if candidate.is_dir():
            preserve_runtime_home(candidate, record)
            shutil.rmtree(candidate, ignore_errors=True)
            removed.append(candidate.name)
    return removed


def finalize_run(run_dir: str | Path, *, force: bool = False) -> dict[str, Any]:
    """Close out a run record whose runner died without finishing it.

    Marks the run ``interrupted`` with ``failure_reason: runner_lost``,
    recovers partial usage from the execution log, sets ``finished_at`` from
    the newest file under ``work/`` and removes the orphaned runtime root.
    Refuses a run whose runner pid still looks alive unless ``force``.
    """
    run = Path(run_dir)
    record = run / "record"
    result = _read_json(record / "run_result.json")
    if result is None:
        raise ValueError(f"no readable record/run_result.json under {run}")
    if result.get("state") not in _LIVE_STATES:
        raise ValueError(f"run state {result.get('state')!r} is not live; nothing to finalize")
    if _runner_pid_alive(run) and not force:
        raise ValueError("runner process appears alive; stop it first or pass --force")
    result["state"] = "interrupted"
    result["failure_reason"] = "runner_lost"
    result["closed_by"] = "finalize"
    result["finalized_at"] = _now()
    finished_at = _newest_work_mtime(run / "work")
    if finished_at is not None:
        result["finished_at"] = finished_at
    _write(record / "usage_summary.json", summarize_usage(record / "execution.jsonl"))
    result["usage_summary"] = "record/usage_summary.json"
    result["usage_summary_partial"] = True
    removed = _remove_stale_runtime_roots(result.get("run_id"), record)
    _write(record / "run_result.json", result)
    report = dict(result)
    report["stale_runtime_roots_removed"] = removed
    return report
