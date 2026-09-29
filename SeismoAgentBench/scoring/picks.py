"""Deterministic scoring for station-level P/S phase picks."""

from __future__ import annotations

import csv
from datetime import datetime, timezone
from pathlib import Path
import re
from statistics import median
from typing import Any, Iterable, Mapping


class PickScoreError(ValueError):
    """Raised when a pick table cannot be scored."""


REQUIRED_COLUMNS = {"station", "phase", "arrival_time_utc"}
PHASES = ("P", "S")


def _parse_time(value: str) -> datetime:
    text = value.strip()
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    # Python versions used by workers differ in how many fractional digits
    # ``fromisoformat`` accepts; normalize to microseconds first.
    match = re.match(r"^(.*?\.)(\d+)([+-]\d\d:\d\d)?$", text)
    if match:
        text = match.group(1) + match.group(2).ljust(6, "0")[:6] + (match.group(3) or "")
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError as exc:
        raise PickScoreError(f"invalid arrival_time_utc: {value!r}") from exc
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def load_picks(path: str | Path) -> list[dict[str, str]]:
    """Load a pick CSV and enforce the small interchange schema."""
    try:
        with Path(path).open(newline="", encoding="utf-8") as handle:
            reader = csv.DictReader(handle)
            columns = set(reader.fieldnames or ())
            missing = sorted(REQUIRED_COLUMNS - columns)
            if missing:
                raise PickScoreError(f"pick CSV is missing columns: {', '.join(missing)}")
            rows = [dict(row) for row in reader]
    except OSError as exc:
        raise PickScoreError(f"cannot read pick CSV {path}: {exc}") from exc
    return rows


def _valid_rows(rows: Iterable[Mapping[str, Any]]) -> list[dict[str, Any]]:
    result = []
    for index, row in enumerate(rows, start=2):
        station = str(row.get("station", "")).strip()
        phase = str(row.get("phase", "")).strip().upper()
        status = str(row.get("status", "picked")).strip().lower()
        if status in {"missing", "rejected", "skipped", ""}:
            continue
        if not station or phase not in PHASES:
            raise PickScoreError(f"invalid station/phase at CSV row {index}")
        result.append({"station": station, "phase": phase,
                       "time": _parse_time(str(row["arrival_time_utc"]))})
    return result


def _summary(errors: list[float]) -> dict[str, float | None]:
    if not errors:
        return {"mean_s": None, "median_s": None, "p90_s": None}
    ordered = sorted(errors)
    p90 = ordered[min(len(ordered) - 1, int(0.9 * (len(ordered) - 1)))]
    return {"mean_s": sum(errors) / len(errors), "median_s": median(errors), "p90_s": p90}


def score_picks(candidate: str | Path | Iterable[Mapping[str, Any]],
                reference: str | Path | Iterable[Mapping[str, Any]], *,
                time_tolerance_s: float = 0.5,
                reference_id: str | None = None) -> dict[str, Any]:
    """Match candidate picks to reference picks by station and phase.

    Matching is one-to-one and deterministic: for each candidate, the nearest
    unused reference arrival for the same station and phase is selected when it
    falls within ``time_tolerance_s``. Channel is intentionally not part of
    the key because channel naming differs across acquisition systems.
    """
    if time_tolerance_s < 0:
        raise PickScoreError("time_tolerance_s must be non-negative")
    candidate_rows = load_picks(candidate) if isinstance(candidate, (str, Path)) else list(candidate)
    reference_rows = load_picks(reference) if isinstance(reference, (str, Path)) else list(reference)
    cand = _valid_rows(candidate_rows)
    ref = _valid_rows(reference_rows)
    unused = set(range(len(ref)))
    errors: dict[str, list[float]] = {phase: [] for phase in PHASES}
    matched_by_phase = {phase: 0 for phase in PHASES}
    matched_keys: set[tuple[str, str]] = set()
    for row in sorted(cand, key=lambda item: (item["station"], item["phase"], item["time"])):
        options = [index for index in unused
                   if ref[index]["station"] == row["station"] and ref[index]["phase"] == row["phase"]]
        if not options:
            continue
        best = min(options, key=lambda index: abs((row["time"] - ref[index]["time"]).total_seconds()))
        error = abs((row["time"] - ref[best]["time"]).total_seconds())
        if error <= time_tolerance_s:
            unused.remove(best)
            phase = row["phase"]
            matched_by_phase[phase] += 1
            errors[phase].append(error)
            matched_keys.add((row["station"], phase))

    per_phase: dict[str, Any] = {}
    for phase in PHASES:
        candidate_count = sum(row["phase"] == phase for row in cand)
        reference_count = sum(row["phase"] == phase for row in ref)
        matched = matched_by_phase[phase]
        precision = matched / candidate_count if candidate_count else 0.0
        recall = matched / reference_count if reference_count else 0.0
        f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
        per_phase[phase] = {"candidate": candidate_count, "reference": reference_count,
                            "matched": matched, "precision": precision, "recall": recall,
                            "f1": f1, "absolute_error_s": _summary(errors[phase])}
    candidate_stations = {row["station"] for row in cand}
    reference_stations = {row["station"] for row in ref}
    station_coverage = (len(candidate_stations & reference_stations) / len(reference_stations)
                        if reference_stations else 0.0)
    return {
        "schema_version": 1,
        "status": "scored",
        "reference_id": reference_id,
        "matching": {"key": ["station", "phase"], "time_tolerance_s": time_tolerance_s,
                      "one_to_one": True},
        "metrics": {"candidate_picks": len(cand), "reference_picks": len(ref),
                    "matched_picks": sum(matched_by_phase.values()),
                    "missing_reference_picks": len(ref) - sum(matched_by_phase.values()),
                    "extra_candidate_picks": len(cand) - sum(matched_by_phase.values()),
                    "station_coverage": station_coverage, "per_phase": per_phase},
    }
