"""Normalize line-delimited Agent events into an auditable trajectory."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


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
