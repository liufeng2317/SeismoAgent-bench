"""Normalize line-delimited Agent events into an auditable trajectory."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def _timestamp() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def _short(value: Any, limit: int = 4000) -> str:
    text = str(value or "").replace("\x00", "")
    if len(text) > limit:
        return text[:limit] + " ... [truncated; see execution.jsonl]"
    return text


def _human_summary(raw: Any) -> str:
    if not isinstance(raw, dict):
        return f"raw_event value={_short(raw)}"
    event_type = raw.get("type", "unknown")
    item = raw.get("item")
    if event_type in {"thread.started", "turn.started", "turn.completed"}:
        return str(event_type)
    if isinstance(item, dict):
        item_type = item.get("type", "unknown")
        if item_type == "agent_message":
            return f"agent_message: {_short(item.get('text'))}"
        if item_type == "command_execution":
            details = f"command_execution: {item.get('command', '')}"
            if item.get("status") is not None or item.get("exit_code") is not None:
                details += f" [status={item.get('status', 'unknown')} exit_code={item.get('exit_code')}]"
            output = _short(item.get("aggregated_output"))
            return details + (f"\n{output}" if output else "")
        if item_type in {"reasoning", "analysis"}:
            return "reasoning: [redacted]"
        return f"{event_type} item_type={item_type}"
    return f"{event_type} fields={','.join(sorted(str(key) for key in raw))}"


def write_human_log(raw_log_path: str | Path, human_log_path: str | Path) -> int:
    """Render raw JSONL/console output as a timestamped human-readable log."""
    source = Path(raw_log_path)
    target = Path(human_log_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    with source.open(encoding="utf-8", errors="replace") as raw_stream, target.open("w", encoding="utf-8") as output:
        for line in raw_stream:
            count += 1
            text = line.rstrip("\n")
            try:
                event = json.loads(text)
            except json.JSONDecodeError:
                summary = f"stdout: {_short(text)}"
            else:
                summary = _human_summary(event)
            output.write(f"[{_timestamp()}] {summary}\n")
    return count


def _event(raw: dict[str, Any], sequence: int) -> dict[str, Any]:
    kind = raw.get("type")
    result: dict[str, Any] = {
        "schema_version": 1,
        "sequence": sequence,
        "event_type": kind if isinstance(kind, str) else "unknown",
    }
    if kind in {"thread.started", "turn.started", "turn.completed"}:
        for key in ("thread_id", "usage"):
            if key in raw:
                result[key] = raw[key]
        return result
    item = raw.get("item")
    if not isinstance(item, dict):
        result["event_type"] = "raw_event"
        result["fields"] = sorted(raw)
        return result
    item_type = item.get("type")
    if item.get("id") is not None:
        result["item_id"] = item["id"]
    if item_type == "agent_message":
        result["event_type"] = "agent_message"
        result["text"] = str(item.get("text", ""))
    elif item_type == "command_execution":
        result["event_type"] = "tool_call" if kind == "item.started" else "tool_result"
        for key in ("command", "status", "exit_code", "aggregated_output"):
            if key in item:
                result[key if key != "aggregated_output" else "output"] = item[key]
    elif item_type in {"reasoning", "analysis"}:
        # Deliberate boundary: do not persist hidden chain-of-thought content.
        result["event_type"] = "reasoning_redacted"
        result["item_type"] = item_type
    else:
        result["event_type"] = "item"
        result["item_type"] = str(item_type or "unknown")
        if "status" in item:
            result["status"] = item["status"]
    return result


def write_transcript(log_path: str | Path, transcript_path: str | Path) -> dict[str, int]:
    """Parse JSONL Agent output and write the stable transcript schema.

    Non-JSON lines remain visible as ``log_line`` events. The raw execution
    log is never replaced, so parser changes cannot destroy provenance.
    """
    counts: dict[str, int] = {}
    sequence = 0
    target = Path(transcript_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    with Path(log_path).open(encoding="utf-8", errors="replace") as source, target.open("w", encoding="utf-8") as output:
        for line in source:
            sequence += 1
            text = line.rstrip("\n")
            try:
                raw = json.loads(text)
            except json.JSONDecodeError:
                normalized = {"schema_version": 1, "sequence": sequence,
                              "event_type": "log_line", "text": text}
            else:
                normalized = _event(raw, sequence) if isinstance(raw, dict) else {
                    "schema_version": 1, "sequence": sequence,
                    "event_type": "raw_event", "value": raw,
                }
            event_type = normalized["event_type"]
            counts[event_type] = counts.get(event_type, 0) + 1
            output.write(json.dumps(normalized, ensure_ascii=False, sort_keys=True) + "\n")
    return counts
