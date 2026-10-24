#!/usr/bin/env python3
"""Empirical false-alarm rate of a stage-60 Match&Locate run by channel shuffling.

Every continuous channel of the run's dataset is circularly shifted by its
own random lag (at least ``--min-shift`` s), which destroys the inter-channel
coherence that real events produce while keeping each channel's amplitude
and spectral statistics. The same templates, parameters and grid are then
run on the shifted data; detections there are false alarms by construction.
Comparing per-threshold counts with the real run gives an estimate of the
false-detection fraction that does not depend on the completeness of any
reference catalog.

Writes <run-root>_null<seed>/{dataset,run,null_report.json}.
"""
from __future__ import annotations

import argparse
import csv
import json
import shutil
import subprocess
import sys
from pathlib import Path

import numpy as np
from obspy.io.sac import SACTrace

EXPERT = Path(__file__).resolve().parents[1]
TOOL = EXPERT.parents[3] / "seismotools" / "match_and_locate"
sys.path.insert(0, str(TOOL / "runtime" / "python" / "MatchLocatepy"))
from matchlocate_runner import merge_detections  # noqa: E402
from matchlocate_runner.native import Detection  # noqa: E402


def load(path: Path, segments=None):
    with path.open() as handle:
        return [Detection(float(r["time_s"]), float(r["latitude"]), float(r["longitude"]), float(r["depth_km"]),
                          float(r["magnitude"]), float(r["cc"]), float(r["nmad"]), r["template_id"])
                for r in csv.DictReader(handle) if not segments or r["segment"] in segments]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-root", type=Path, required=True)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--min-shift", type=float, default=600.0)
    parser.add_argument("--jobs", type=int, default=8)
    parser.add_argument("--threads", type=int, default=8)
    parser.add_argument("--mad", default="8,8.5,9,9.5,10,11,12,14")
    parser.add_argument("--cc", default="0,0.1,0.15,0.2")
    parser.add_argument("--separation", type=float, default=4.0)
    parser.add_argument("--segments", default="", help="comma-separated subset of continuous segments (default all)")
    args = parser.parse_args()
    src = args.run_root.resolve()
    wanted = [x for x in args.segments.split(",") if x]
    out = src.parent / (f"{src.name}_null{args.seed}" + (f"_{'_'.join(wanted)}" if wanted else ""))
    ds = out / "dataset"
    if out.exists():
        shutil.rmtree(out)
    ds.mkdir(parents=True)
    for name in ("templates.csv", "channels.csv", "config.json", "dataset.json"):
        if (src / "dataset" / name).is_file():
            shutil.copy2(src / "dataset" / name, ds / name)
    (ds / "templates").symlink_to((src / "dataset" / "templates").resolve(), target_is_directory=True)
    rng = np.random.default_rng(args.seed)
    shifts = {}
    for seg_dir in sorted((src / "dataset" / "continuous").iterdir()):
        if wanted and seg_dir.name not in wanted:
            continue
        (ds / "continuous" / seg_dir.name).mkdir(parents=True)
        for f in sorted(seg_dir.glob("*.sac")):
            tr = SACTrace.read(str(f))
            n = tr.npts
            k = int(rng.integers(int(args.min_shift / tr.delta), n - int(args.min_shift / tr.delta)))
            tr.data = np.roll(tr.data, k)
            tr.write(str(ds / "continuous" / seg_dir.name / f.name), byteorder="little")
            shifts[f"{seg_dir.name}/{f.stem}"] = round(k * tr.delta, 2)
    cmd = [sys.executable, "-I", str(TOOL / "interface" / "run.py"), "--input-dir", str(ds), "--output-dir",
           str(out / "run"), "--jobs", str(args.jobs), "--threads", str(args.threads), "--quiet"]
    with (out / "run.log").open("w") as log:
        rc = subprocess.run(cmd, stdout=log, stderr=subprocess.STDOUT).returncode
    if rc != 0:
        raise SystemExit(f"null run failed; see {out / 'run.log'}")
    real, null = load(src / "run" / "template_detections.csv", wanted), load(out / "run" / "template_detections.csv", wanted)
    table = []
    for mad in (float(x) for x in args.mad.split(",")):
        for cc in (float(x) for x in args.cc.split(",")):
            nr = len(merge_detections(real, cc, mad, args.separation))
            nn = len(merge_detections(null, cc, mad, args.separation))
            table.append({"mad": mad, "cc": cc, "real": nr, "null": nn,
                          "estimated_false_fraction": round(nn / nr, 4) if nr else None})
    report = {"run_root": str(src), "seed": args.seed, "min_shift_s": args.min_shift, "segments": wanted or "all",
              "channel_shifts_s": shifts, "table": table}
    (out / "null_report.json").write_text(json.dumps(report, indent=2) + "\n")
    print("mad  cc   real  null  est.false")
    for t in table:
        print(f"{t['mad']:<4} {t['cc']:<4} {t['real']:5d} {t['null']:5d}  {t['estimated_false_fraction']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
