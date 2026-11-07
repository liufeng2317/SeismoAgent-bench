#!/usr/bin/env python3
"""Check a submission before ending the run: the same things the scorer verifies, in a few seconds.

Checks, in the output directory (default ``$BENCH_OUTPUT``):

- ``catalog.csv`` and ``picks.csv`` are at its top level (not in a subdirectory) and have the required columns
  of the output contract (``$BENCH_OUTPUT_CONTRACT`` when set);
- ``checker/final/checker_report.json`` exists and was made from the submitted files (the sha256 the report
  records for ``catalog`` and ``picks`` equals that of the files now in place);
- ``checker/dispositions.json`` has one entry for every flag of that report, each ``fixed`` or ``justified``;
  a ``justified`` entry has ``evidence``; a ``fixed`` entry has ``what_changed`` and a ``report_before``
  (relative to the output directory) that exists and holds the flag;
- a warning when a ``work/`` subdirectory holds its own ``catalog.csv`` (products written one level too deep).

Usage: check_submission.py [--output-dir $BENCH_OUTPUT]. Exit status 0 when every check passes, 1 otherwise.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
from pathlib import Path


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def required_columns(contract: Path | None) -> dict:
    default = {"catalog.csv": ["event_id", "origin_time_utc", "latitude", "longitude", "depth_km", "magnitude", "status"],
               "picks.csv": ["pick_id", "event_id", "station_id", "phase", "time_utc", "status"]}
    if contract is None or not contract.is_file():
        return default
    out = {}
    for art in json.loads(contract.read_text()).get("artifacts", []):
        cols = (art.get("schema") or {}).get("required_columns")
        if cols:
            out[art["path"]] = cols
    return out or default


def entries(dispositions) -> list[dict]:
    if isinstance(dispositions, dict):
        dispositions = dispositions.get("dispositions", dispositions)
    if isinstance(dispositions, dict):  # keyed by flag_id
        return [dict(flag_id=k, **v) if isinstance(v, dict) else {"flag_id": k, "disposition": v} for k, v in dispositions.items()]
    return list(dispositions)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--output-dir", type=Path, default=Path(os.environ.get("BENCH_OUTPUT", ".")))
    a = ap.parse_args()
    out = a.output_dir.resolve()
    contract = Path(os.environ["BENCH_OUTPUT_CONTRACT"]) if os.environ.get("BENCH_OUTPUT_CONTRACT") else None
    problems, warnings = [], []
    for name, cols in required_columns(contract).items():
        f = out / name
        if not f.is_file():
            problems.append(f"{name}: missing at the top of {out}")
            continue
        with f.open(newline="") as fh:
            header = next(csv.reader(fh), [])
        missing = [c for c in cols if c not in header]
        if missing:
            problems.append(f"{name}: missing columns {missing}")
    if (out / "work" / "catalog.csv").is_file():
        warnings.append("work/catalog.csv exists: the submission is read from the top of the output directory, not from work/")
    report_path = out / "checker/final/checker_report.json"
    flags = []
    if not report_path.is_file():
        problems.append("checker/final/checker_report.json: missing")
    else:
        report = json.loads(report_path.read_text())
        flags = [f.get("flag_id") for f in report.get("flags", [])]
        for key, name in (("catalog", "catalog.csv"), ("picks", "picks.csv")):
            rec = (report.get("inputs") or {}).get(key) or {}
            if (out / name).is_file() and rec.get("sha256") and rec["sha256"] != sha256(out / name):
                problems.append(f"checker/final/checker_report.json was not made from the submitted {name} (sha256 differs): rerun the checker on the final files")
    disp_path = out / "checker/dispositions.json"
    if flags and not disp_path.is_file():
        problems.append("checker/dispositions.json: missing")
    elif disp_path.is_file():
        given = {e.get("flag_id"): e for e in entries(json.loads(disp_path.read_text()))}
        for flag in flags:
            e = given.get(flag)
            if e is None:
                problems.append(f"{flag}: no disposition")
            elif e.get("disposition") == "justified" and not e.get("evidence"):
                problems.append(f"{flag}: justified without evidence (give numbers, files or an experiment)")
            elif e.get("disposition") == "fixed":
                if not e.get("what_changed"):
                    problems.append(f"{flag}: fixed without what_changed")
                before = Path(str(e.get("report_before") or ""))
                before = before if before.is_absolute() else out / before
                try:
                    held = flag in {f.get("flag_id") for f in json.loads(before.read_text()).get("flags", [])}
                except (OSError, json.JSONDecodeError, IsADirectoryError):
                    held = False
                if not held:
                    problems.append(f"{flag}: fixed, but report_before (relative to {out}) does not exist or does not hold the flag")
            elif e.get("disposition") not in ("fixed", "justified"):
                problems.append(f"{flag}: disposition must be fixed or justified")
    for w in warnings:
        print(f"WARNING {w}")
    for p in problems:
        print(f"PROBLEM {p}")
    print("OK: the submission passes these checks" if not problems else f"{len(problems)} problem(s)")
    return 0 if not problems else 1


if __name__ == "__main__":
    raise SystemExit(main())
