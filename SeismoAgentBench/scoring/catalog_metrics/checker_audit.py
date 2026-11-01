"""Checker contract (S2c, S3): verify the submitted checker report and the disposition of every flag.

The contract adds ``work/checker/final/checker_report.json`` (the checker on the submitted products)
and ``work/checker/dispositions.json`` (one ``fixed`` or ``justified`` entry per flag). The scorer
re-runs the same checker on the submitted files and reports:

- whether the submitted report was made on the submitted files (input SHA-256);
- whether its flags agree with the re-run;
- per flag of the re-run: disposed or not, ``fixed`` while the flag is still present, ``justified``
  without evidence;
- how often the Agent ran the checker (reports under ``work/checker/``).

It does not judge whether a justification is right; that is read against the scores.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
CHECKER = ROOT / "seismotools/checker/interface/run.py"
REPORT = "checker/final/checker_report.json"
DISPOSITIONS = "checker/dispositions.json"


def required(contract: dict) -> bool:
    return any(a.get("kind") in ("checker_report", "checker_dispositions") for a in contract.get("artifacts", []))


def _sha256(path: Path) -> str | None:
    if not path.is_file():
        return None
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def checker_version() -> str | None:
    try:
        return subprocess.run(["git", "-C", str(ROOT), "log", "-1", "--format=%H", "--", "seismotools/checker"],
                              capture_output=True, text=True, check=True).stdout.strip() or None
    except (OSError, subprocess.CalledProcessError):
        return None


def rerun(work: Path, out: Path, submitted: dict, python: str = sys.executable) -> dict | None:
    """The checker on the submitted files, with the stage and optional inputs of the submitted report."""
    stage = submitted.get("stage") or "all"
    inputs = submitted.get("inputs") or {}
    cmd = [python, "-W", "ignore", str(CHECKER), "--stage", stage, "--catalog", str(work / "catalog.csv"),
           "--picks", str(work / "picks.csv"), "--stations", str(work / "input/waveforms/stations"),
           "--output-dir", str(out), "--no-figures"]
    if stage in ("data", "magnitude", "all") or "waveforms" in inputs:
        cmd += ["--waveforms", str(work / "input/waveforms/data")]
    before = inputs.get("catalog_before", {}).get("path")
    if before:
        b = Path(before)
        b = b if b.is_absolute() else work / b
        if b.is_file():
            cmd += ["--catalog-before", str(b)]
    try:
        subprocess.run(cmd, check=True, capture_output=True, text=True, timeout=3 * 3600)
    except (OSError, subprocess.CalledProcessError, subprocess.TimeoutExpired) as exc:
        return {"error": f"{type(exc).__name__}: {str(exc)[:300]}"}
    return json.loads((out / "checker_report.json").read_text())


def audit(work: Path, out_dir: Path) -> dict:
    report_path, disp_path = work / REPORT, work / DISPOSITIONS
    res: dict = {"checker_version": checker_version(), "report_present": report_path.is_file(),
                 "dispositions_present": disp_path.is_file(),
                 "checker_runs": len(list((work / "checker").rglob("checker_report.json"))) if (work / "checker").is_dir() else 0}
    if not report_path.is_file():
        return res
    submitted = json.loads(report_path.read_text())
    sub_inputs = submitted.get("inputs") or {}
    res["report_on_submission"] = {k: (sub_inputs.get(k) or {}).get("sha256") == _sha256(work / f)
                                   for k, f in (("catalog", "catalog.csv"), ("picks", "picks.csv"))}
    again = rerun(work, out_dir / "checker_rerun", submitted)
    if again is None or "error" in (again or {}):
        res["rerun_error"] = (again or {}).get("error")
        return res
    flags_sub = {f["flag_id"] for f in submitted.get("flags", [])}
    flags_now = {f["flag_id"] for f in again.get("flags", [])}
    res["flags"] = sorted(flags_now)
    res["flags_agree"] = flags_sub == flags_now
    res["flags_only_in_submitted"] = sorted(flags_sub - flags_now)
    res["flags_only_in_rerun"] = sorted(flags_now - flags_sub)
    entries = []
    if disp_path.is_file():
        try:
            entries = json.loads(disp_path.read_text())
        except json.JSONDecodeError as exc:
            res["dispositions_error"] = str(exc)[:200]
    by_flag = {e.get("flag_id"): e for e in entries if isinstance(e, dict) and e.get("flag_id")}
    res["entries_without_flag_id"] = sum(1 for e in entries if not (isinstance(e, dict) and e.get("flag_id")))
    rows = []
    for fid in sorted(flags_now):
        e = by_flag.get(fid)
        kind = (e or {}).get("disposition")
        rows.append({"flag_id": fid, "disposition": kind,
                     "problem": None if e else "no disposition",
                     **({"problem": "fixed but the flag is still raised"} if kind == "fixed" else {}),
                     **({"problem": "justified without evidence"} if kind == "justified" and not str(e.get("evidence") or "").strip() else {}),
                     **({"problem": f"unknown disposition {kind!r}"} if e and kind not in ("fixed", "justified") else {})})
    fixed_gone, fixed_verified = [], []
    for e in entries:
        if not (isinstance(e, dict) and e.get("disposition") == "fixed" and e.get("flag_id") not in flags_now):
            continue
        fixed_gone.append(e.get("flag_id"))
        before = Path(str(e.get("report_before") or ""))
        before = before if before.is_absolute() else work / before
        try:  # the earlier report must exist and must hold the flag
            if e.get("flag_id") in {f["flag_id"] for f in json.loads(before.read_text()).get("flags", [])}:
                fixed_verified.append(e.get("flag_id"))
        except (OSError, json.JSONDecodeError, IsADirectoryError):
            pass
    res["dispositions"] = rows
    res["fixed_flags_gone"] = sorted(fixed_gone)
    res["fixed_flags_verified"] = sorted(fixed_verified)  # the earlier report named in the entry holds the flag
    res["counts"] = {"flags": len(flags_now),
                     "disposed": sum(r["disposition"] is not None for r in rows),
                     "justified": sum(r["disposition"] == "justified" for r in rows),
                     "fixed_earlier": len(fixed_gone), "fixed_earlier_verified": len(fixed_verified),
                     "problems": sum(r["problem"] is not None for r in rows) + res["entries_without_flag_id"]}
    res["complete"] = bool(res["report_on_submission"].get("catalog") and res["report_on_submission"].get("picks")
                           and res["flags_agree"] and res["counts"]["problems"] == 0)
    return res
