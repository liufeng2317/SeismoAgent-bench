#!/usr/bin/env python3
"""Waveform review of stage-60 Match&Locate detections in an N×MAD band.

For each per-template-merged detection with lo <= N×MAD < hi on the scanned
day, the template windows are aligned on the continuous data with the native
linear moveout to the detection's grid node. Per detection it reports, over
the template's ``--top`` highest-weight rows (nearest stations), the
zero-lag CC of each row and the number of rows with CC >= ``--row-cc``.
Detections are split into "matched" (to any masked reference catalog, the
evaluation matcher 4 s / 15 km) and "unmatched"; the distributions of the
coherent-row count separate real events from noise excursions of the stack.

Writes review_<lo>-<hi>.json and review_<lo>-<hi>.png into the run folder.
"""
from __future__ import annotations

import argparse
import csv
import importlib.util
import json
import math
import random
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from obspy.io.sac import SACTrace

EXPERT = Path(__file__).resolve().parents[1]
TOOL = EXPERT.parents[3] / "seismotools" / "match_and_locate"
sys.path.insert(0, str(TOOL / "runtime" / "python" / "MatchLocatepy"))
from matchlocate_runner import epicentral_km, merge_detections  # noqa: E402
from matchlocate_runner.native import KM_PER_DEG, Detection  # noqa: E402


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-root", type=Path, required=True, help="export/r7/60_match_locate/<scope>[_tag]")
    parser.add_argument("--lo", type=float, default=8.0)
    parser.add_argument("--hi", type=float, default=9.0)
    parser.add_argument("--top", type=int, default=6, help="rows per detection (nearest stations)")
    parser.add_argument("--row-cc", type=float, default=0.3)
    parser.add_argument("--plot", type=int, default=8, help="detections plotted per class")
    parser.add_argument("--separation", type=float, default=4.0)
    args = parser.parse_args()
    root = args.run_root
    ds = root / "dataset"
    cmp = _load("evaluation_comparison", EXPERT.parent / "evaluation" / "scripts" / "plot_evaluation_comparison.py")

    templates = {r["template_id"]: r for r in csv.DictReader((ds / "templates.csv").open())}
    rows_by_t = {}
    for r in csv.DictReader((ds / "channels.csv").open()):
        rows_by_t.setdefault(r["template_id"], []).append(r)
    segment = sorted(p.name for p in (ds / "continuous").iterdir())[0]
    day = datetime.strptime(segment, "%Y%m%d").replace(tzinfo=timezone.utc)
    tdets = [Detection(float(r["time_s"]), float(r["latitude"]), float(r["longitude"]), float(r["depth_model_km"]),
                       float(r["magnitude"]), float(r["cc"]), float(r["nmad"]), r["template_id"])
             for r in csv.DictReader((root / "run" / "template_detections.csv").open()) if r["segment"] == segment]
    merged = merge_detections(tdets, 0.0, args.lo, args.separation)
    band = [d for d in merged if d.nmad < args.hi]

    refs, _ = cmp.load_references()
    rows = [{"time": day + timedelta(seconds=d.time_s), "latitude": d.latitude, "longitude": d.longitude,
             "depth_km": d.depth_km - 1.48, "magnitude": None} for d in band]
    rec = cmp.as_record("ml", "ml", "k", rows)
    matched = set()
    for ref in refs:
        rr = cmp.as_record(ref["key"], ref["label"], ref["color"],
                           [x for x in ref["rows"] if day <= x["time"] < day + timedelta(days=1)])
        matched |= {i for i, *_ in cmp.match(rec, rr)}

    cache = {}

    def sac(path):
        if path not in cache:
            cache[path] = SACTrace.read(str(path))
        return cache[path]

    def review(i, d):
        t = templates[d.template_id]
        tl, to, tz = float(t["latitude"]), float(t["longitude"]), float(t["depth_km"])
        out = []
        for r in rows_by_t[d.template_id]:
            tr = sac(ds / "templates" / d.template_id / f"{r['channel']}.sac")
            ct = sac(ds / "continuous" / segment / f"{r['channel']}.sac")
            mark = getattr(tr, f"t{r['mark']}")
            dgc = (epicentral_km(tr.stla, tr.stlo, d.latitude, d.longitude)
                   - epicentral_km(tr.stla, tr.stlo, tl, to)) / KM_PER_DEG
            shift = float(r["slowness_h_s_per_deg"]) * dgc + float(r["slowness_v_s_per_km"]) * (d.depth_km - tz)
            dt = tr.delta
            n = int(round(2.0 / dt))
            a0 = int(round((mark - 0.3 - tr.b) / dt))
            k0 = int(round((d.time_s + mark + shift - 0.3 - ct.b) / dt))
            a, b = tr.data[a0:a0 + n].astype(float), ct.data[k0:k0 + n].astype(float)
            cc = float(a @ b / math.sqrt((a @ a) * (b @ b) + 1e-20)) if len(a) == len(b) == n else float("nan")
            dist = epicentral_km(tr.stla, tr.stlo, tl, to)
            out.append({"channel": r["channel"], "phase": r["phase"], "distance_km": dist, "cc": cc,
                        "template": tr.data[max(a0 - 25, 0):a0 + n + 25], "data": ct.data[k0 - 25:k0 + n + 25]})
        out.sort(key=lambda x: x["distance_km"])
        top = out[:args.top]
        return {"index": i, "time": (day + timedelta(seconds=d.time_s)).isoformat(), "template": d.template_id,
                "nmad": d.nmad, "stack_cc": d.cc, "matched": i in matched,
                "coherent_rows": sum(1 for x in top if x["cc"] >= args.row_cc),
                "top_row_cc": [round(x["cc"], 3) for x in top], "_traces": top}

    reviews = [review(i, d) for i, d in enumerate(band)]
    summary = {}
    for cls in (True, False):
        sel = [r["coherent_rows"] for r in reviews if r["matched"] == cls]
        summary["matched" if cls else "unmatched"] = {
            "detections": len(sel),
            "coherent_rows_histogram": {k: sel.count(k) for k in range(args.top + 1)},
            "median_coherent_rows": float(np.median(sel)) if sel else None,
            "fraction_with_ge3_coherent_rows": round(sum(s >= 3 for s in sel) / len(sel), 3) if sel else None}
    report = {"band": [args.lo, args.hi], "segment": segment, "top_rows": args.top, "row_cc": args.row_cc,
              "summary": summary,
              "detections": [{k: v for k, v in r.items() if k != "_traces"} for r in reviews]}
    stem = f"review_{args.lo:g}-{args.hi:g}"
    (root / f"{stem}.json").write_text(json.dumps(report, indent=2) + "\n")

    random.seed(0)
    picks = (random.sample([r for r in reviews if r["matched"]], min(args.plot, sum(r["matched"] for r in reviews)))
             + random.sample([r for r in reviews if not r["matched"]],
                             min(args.plot, sum(not r["matched"] for r in reviews))))
    cols = 4
    nrow = math.ceil(len(picks) / cols)
    fig, axes = plt.subplots(nrow, cols, figsize=(16, 3.2 * nrow), squeeze=False)
    for ax, r in zip(axes.flat, picks):
        for j, x in enumerate(r["_traces"]):
            for series, color, lw in ((x["data"], "0.45", 0.8), (x["template"], "#C0392B", 0.9)):
                s = np.asarray(series, float)
                if s.size and np.max(np.abs(s)) > 0:
                    ax.plot(np.arange(s.size) * 0.02, s / np.max(np.abs(s)) * 0.45 - j, color=color, lw=lw)
            ax.text(2.55, -j, f"{x['channel'].split('.')[1]} {x['phase']} {x['cc']:.2f}", fontsize=7, va="center")
        ax.set_title(f"{'matched' if r['matched'] else 'UNMATCHED'}  N×MAD {r['nmad']:.1f}  CC {r['stack_cc']:.2f}\n"
                     f"{r['time'][11:22]}  coherent {r['coherent_rows']}/{args.top}", fontsize=8)
        ax.set_yticks([]); ax.set_xlim(0, 3.2); ax.tick_params(labelsize=7)
    for ax in list(axes.flat)[len(picks):]:
        ax.axis("off")
    fig.suptitle(f"{root.name}: detections with {args.lo:g} <= N×MAD < {args.hi:g} on {segment} — template (red) "
                 f"over data (grey), {args.top} nearest rows, window 2 s + 0.5 s margins", fontsize=10)
    fig.tight_layout(rect=(0, 0, 1, 0.97))
    fig.savefig(root / f"{stem}.png", dpi=110)
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
