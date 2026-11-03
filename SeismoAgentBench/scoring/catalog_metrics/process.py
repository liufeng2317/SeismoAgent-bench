"""Completion, consistency (L0) and process/cost (L6) metrics from a run directory."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd

URL = re.compile(r"https?://[^\s\"'\\)<>\]]+")


def _json(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def contract_status(work: Path, contract: dict) -> dict:
    """Required artifacts present with their required columns (L0 ``completed``)."""
    missing = []
    for item in contract.get("artifacts", []):
        if not item.get("required"):
            continue
        path = work / item["path"]
        if not path.is_file():
            missing.append(f"{item['path']}: missing")
            continue
        columns = (item.get("schema") or {}).get("required_columns")
        if columns:
            header = set(pd.read_csv(path, nrows=0).columns)
            lost = sorted(set(columns) - header)
            if lost:
                missing.append(f"{item['path']}: missing columns {', '.join(lost)}")
    return {"completed": not missing, "problems": missing}


def consistency(catalog: pd.DataFrame, picks: pd.DataFrame) -> dict:
    """Fraction of rows passing each internal check (L0 ``consistency``)."""
    out = {}
    linked = picks[picks.event_id.astype(str).str.strip() != ""]
    ids = set(catalog.event_id.astype(str))
    out["pick_event_ids_exist"] = round(float(linked.event_id.astype(str).isin(ids).mean()), 4) if len(linked) else None
    live = linked[linked.status.astype(str).str.strip().str.lower() != "rejected"] if "status" in linked else linked
    phase = live.phase.astype(str).str.upper().str[0]
    counts = pd.DataFrame({"n": live.groupby("event_id").size(),
                           "p": live[phase == "P"].groupby("event_id").size(),
                           "s": live[phase == "S"].groupby("event_id").size()}).fillna(0)
    rows = catalog.set_index(catalog.event_id.astype(str))
    rows = rows[rows.status.astype(str).str.lower() != "rejected"] if "status" in rows else rows
    agree = []
    for col, key in (("n_picks", "n"), ("n_p_picks", "p"), ("n_s_picks", "s")):
        stated = pd.to_numeric(rows.get(col), errors="coerce")
        actual = counts[key].reindex(rows.index).fillna(0)
        agree.append(stated.eq(actual))
    out["pick_counts_agree"] = round(float(np.logical_and.reduce(agree).mean()), 4) if len(rows) else None
    lat, lon = (pd.to_numeric(catalog[c], errors="coerce") for c in ("latitude", "longitude"))
    out["coordinates_valid"] = round(float((lat.isna() | lat.between(-90, 90)).mean()
                                           * (lon.isna() | lon.between(-180, 180)).mean()), 4) if len(catalog) else None
    return out


def process_metrics(run_dir: Path, leakage_patterns: Iterable[str], review_patterns: Iterable[str] = ()) -> dict:
    """Cost, time and leakage flags from ``record/`` (L6); review patterns list accesses to check by hand."""
    record = run_dir / "record"
    result = _json(record / "run_result.json")
    usage = _json(record / "usage_summary.json")
    timeline = _json(record / "timeline.json")
    totals = usage.get("usage", {})
    out = {"state": result.get("state"), "exit_code": result.get("exit_code"),
           "elapsed_s": result.get("elapsed_s"), "cost_usd": usage.get("total_cost_usd"),
           "turns": usage.get("turns"), "input_tokens": totals.get("input_tokens"),
           "cached_input_tokens": totals.get("cached_input_tokens"), "output_tokens": totals.get("output_tokens"),
           "compactions": usage.get("event_counts", {}).get("system/compact_boundary"),
           "long_tool_runs": len(timeline.get("tool_runs_over_300s", [])) if timeline else None}
    if out["elapsed_s"] is None and result.get("started_at") and result.get("finished_at"):
        span = pd.Timestamp(result["finished_at"]) - pd.Timestamp(result["started_at"])
        out["elapsed_s"] = round(span.total_seconds(), 1)  # records written before elapsed_s existed
    out["leakage"] = scan_transcript(record / "execution.jsonl", leakage_patterns, run_dir, review_patterns)
    return out


def tool_inputs(path: Path):
    """Yield (line number, JSON text) of every tool call the Agent made (its accesses)."""
    with path.open(encoding="utf-8", errors="replace") as handle:
        for number, line in enumerate(handle, 1):
            if '"tool_use"' not in line:
                continue
            try:
                event = json.loads(line)
            except json.JSONDecodeError:
                continue
            message = event.get("message") if event.get("type") == "assistant" else None
            for item in (message or {}).get("content") or []:
                if isinstance(item, dict) and item.get("type") == "tool_use":
                    yield number, json.dumps(item.get("input"), ensure_ascii=False)


ABSOLUTE_PATH = re.compile(r"(?<![\w.])/(?:[\w.@+-]+/){2,}[\w.@+-]*")


def scan_transcript(path: Path, patterns: Iterable[str], run_dir: Path | None = None,
                    review_patterns: Iterable[str] = ()) -> dict:
    """URLs and paths the Agent accessed (tool-call inputs) and hits of the withheld-product patterns.

    Text that only appears in tool results (fetched documents, listings) is
    not an access and is not scanned.
    """
    compiled = [(p, re.compile(p, re.IGNORECASE)) for p in patterns]
    review = [(p, re.compile(p, re.IGNORECASE)) for p in review_patterns]
    if not path.is_file():
        return {"scanned": False, "flag": None, "urls": [], "outside_paths": [], "hits": {}, "review": {}}
    urls, outside, hits, to_review = set(), set(), {}, {}
    own = str(run_dir.resolve()) if run_dir is not None else None
    for number, text in tool_inputs(path):
        urls.update(m.rstrip(".,;") for m in URL.findall(text))
        for found in ABSOLUTE_PATH.findall(URL.sub(" ", text.replace("\\/", "/"))):
            if own is None or not found.startswith(own):
                outside.add("/".join(found.split("/")[:7]))
        for raw, rx in compiled:
            if rx.search(text):
                hits.setdefault(raw, []).append(number)
        for raw, rx in review:
            if rx.search(text):
                to_review.setdefault(raw, []).append(number)
    # review: accesses that may or may not be a withheld product (a catalogue page read for its velocity
    # model, a target paper fetched by URL); they do not set the flag and are checked by hand.
    return {"scanned": True, "flag": bool(hits), "urls": sorted(urls), "outside_paths": sorted(outside),
            "hits": {k: {"calls": len(v), "first_line": v[0]} for k, v in hits.items()},
            "review": {k: {"calls": len(v), "first_line": v[0]} for k, v in to_review.items()}}
