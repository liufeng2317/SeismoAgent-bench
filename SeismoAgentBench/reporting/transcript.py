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


# Claude Code streams high-frequency progress events while the model thinks
# (for example thinking_tokens every few milliseconds). The raw JSONL keeps
# every event; the human log keeps only signal events.
_PROGRESS_EVENT_SUBTYPES = {"thinking_tokens"}


def _content_kinds(content: Any) -> list[str]:
    if not isinstance(content, list):
        return []
    return [block["type"] for block in content
            if isinstance(block, dict) and isinstance(block.get("type"), str)]


def _human_summary(raw: Any) -> str | None:
    if not isinstance(raw, dict):
        return f"raw_event value={_short(raw)}"
    event_type = raw.get("type", "unknown")
    if event_type == "console.line":
        return f"stdout: {_short(raw.get('text'))}"
    if event_type == "system":
        subtype = raw.get("subtype")
        if subtype in _PROGRESS_EVENT_SUBTYPES:
            return None
        label = f"system/{subtype}" if isinstance(subtype, str) else "system"
        if isinstance(raw.get("status"), str):
            return f"{label} {raw['status']}"
        return label
    if event_type == "assistant":
        message = raw.get("message")
        if not isinstance(message, dict):
            return "assistant"
        kinds: list[str] = []
        text = None
        content = message.get("content")
        if isinstance(content, list):
            for block in content:
                if not isinstance(block, dict) or not isinstance(block.get("type"), str):
                    continue
                kinds.append(block["type"])
                if block["type"] == "text" and text is None:
                    text = block.get("text")
        detail = f"assistant [{message.get('model', 'unknown')}] {'+'.join(kinds) if kinds else 'empty'}"
        return f"{detail}: {_short(text, 160)}" if text else detail
    if event_type == "user":
        content = raw.get("message", {}).get("content") if isinstance(raw.get("message"), dict) else None
        if isinstance(content, str):
            return f"user: {_short(content, 160)}"
        kinds = _content_kinds(content)
        return f"user {'+'.join(kinds)}" if kinds else "user"
    if event_type == "result":
        usage = raw.get("usage") if isinstance(raw.get("usage"), dict) else {}
        parts = [f"result {raw.get('subtype', 'unknown')}"]
        if isinstance(raw.get("num_turns"), int):
            parts.append(f"turns={raw['num_turns']}")
        for key, label in (("input_tokens", "in"), ("output_tokens", "out"),
                           ("cache_read_input_tokens", "cached")):
            if isinstance(usage.get(key), int):
                parts.append(f"{label}={usage[key]}")
        cost = raw.get("total_cost_usd")
        if isinstance(cost, (int, float)):
            parts.append(f"cost=${cost:.2f}")
        return " ".join(parts)
    if event_type == "tool_progress":
        detail = f"tool_progress {raw.get('tool_name', 'unknown')}"
        elapsed = raw.get("elapsed_time_seconds")
        if isinstance(elapsed, (int, float)):
            detail += f" elapsed={elapsed}s"
        return detail
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
            if summary is None:
                continue
            for fragment in summary.splitlines() or [""]:
                output.write(f"[{_timestamp()}] {fragment}\n")
    return count


def write_event_jsonl(raw_log_path: str | Path, event_log_path: str | Path) -> int:
    """Convert mixed process output into strict JSON Lines."""
    source = Path(raw_log_path)
    target = Path(event_log_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    with source.open(encoding="utf-8", errors="replace") as raw_stream, target.open("w", encoding="utf-8") as output:
        for line in raw_stream:
            count += 1
            text = line.rstrip("\n")
            try:
                event = json.loads(text)
            except json.JSONDecodeError:
                event = {"type": "console.line", "text": text}
            output.write(json.dumps(event, ensure_ascii=False, sort_keys=True) + "\n")
    return count


def append_execution_line(line: bytes | str, event_stream: Any, human_stream: Any) -> None:
    """Append one process-output line to the live JSONL and human logs."""
    if isinstance(line, bytes):
        text = line.decode("utf-8", errors="replace").rstrip("\r\n")
    else:
        text = line.rstrip("\r\n")
    try:
        event = json.loads(text)
    except json.JSONDecodeError:
        event = {"type": "console.line", "text": text}
    event_stream.write(json.dumps(event, ensure_ascii=False, sort_keys=True) + "\n")
    summary = _human_summary(event)
    if summary is not None:
        for fragment in summary.splitlines() or [""]:
            human_stream.write(f"[{_timestamp()}] {fragment}\n")
    event_stream.flush()
    human_stream.flush()


def summarize_usage(log_path: str | Path) -> dict[str, Any]:
    """Summarize provider usage fields without retaining private reasoning.

    Codex reports usage per turn.completed event; Claude Code streams zero
    usage on assistant messages and reports authoritative totals (turn count,
    per-model token counts, cost) once in the final result event.
    """
    counts: dict[str, int] = {}
    usage_totals = {
        "input_tokens": 0,
        "output_tokens": 0,
        "cached_input_tokens": 0,
        "reasoning_tokens": 0,
        "total_tokens": 0,
    }
    usage_events = 0
    turns = 0
    total_cost_usd: float | None = None
    models: dict[str, dict[str, Any]] = {}
    source = Path(log_path)
    if not source.is_file():
        return {"schema_version": 1, "usage_events": 0, "turns": 0,
                "event_counts": {}, "usage": usage_totals, "models": {},
                "total_cost_usd": None}
    with source.open(encoding="utf-8", errors="replace") as stream:
        for line in stream:
            try:
                event = json.loads(line)
            except json.JSONDecodeError:
                continue
            if not isinstance(event, dict):
                continue
            event_type = event.get("type")
            if event_type == "system" and isinstance(event.get("subtype"), str):
                event_type = f"system/{event['subtype']}"
            if isinstance(event_type, str):
                counts[event_type] = counts.get(event_type, 0) + 1
            if event_type == "turn.completed":
                turns += 1
            if event_type == "result":
                if isinstance(event.get("num_turns"), int):
                    turns = event["num_turns"]
                cost = event.get("total_cost_usd")
                if isinstance(cost, (int, float)):
                    total_cost_usd = float(cost)
                model_usage = event.get("modelUsage")
                if isinstance(model_usage, dict):
                    for name, stats in model_usage.items():
                        if not isinstance(stats, dict):
                            continue
                        models[str(name)] = {
                            "input_tokens": stats.get("inputTokens"),
                            "output_tokens": stats.get("outputTokens"),
                            "cached_input_tokens": stats.get("cacheReadInputTokens"),
                            "reasoning_tokens": stats.get("thinkingTokens"),
                            "cost_usd": stats.get("costUSD"),
                        }
            usage = event.get("usage")
            if not isinstance(usage, dict):
                continue
            usage_events += 1
            aliases = {
                "input_tokens": ("input_tokens", "prompt_tokens"),
                "output_tokens": ("output_tokens", "completion_tokens"),
                "cached_input_tokens": ("cached_input_tokens", "cache_read_input_tokens"),
                "reasoning_tokens": ("reasoning_tokens",),
                "total_tokens": ("total_tokens",),
            }
            for target, keys in aliases.items():
                for key in keys:
                    value = usage.get(key)
                    if isinstance(value, (int, float)):
                        usage_totals[target] += int(value)
                        break
            details = usage.get("output_tokens_details")
            if isinstance(details, dict) and isinstance(details.get("thinking_tokens"), (int, float)):
                usage_totals["reasoning_tokens"] += int(details["thinking_tokens"])
    return {
        "schema_version": 1,
        "usage_events": usage_events,
        "turns": turns,
        "event_counts": counts,
        "usage": usage_totals,
        "models": models,
        "total_cost_usd": total_cost_usd,
    }


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
