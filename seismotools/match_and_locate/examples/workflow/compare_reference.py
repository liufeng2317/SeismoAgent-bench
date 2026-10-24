#!/usr/bin/env python3
"""Compare an interface run of the upstream example with the upstream outputs.

Upstream per-template outputs (``example/20120902/<template>``) and the final
catalog (``example/MultipleTemplate/DetectedFinal.dat``) were produced by a
multi-threaded build whose N(*MAD) column carries the OpenMP race fixed by
patch 0001. The comparison therefore requires:

* time, latitude, longitude, depth, magnitude and CC identical (at the native
  output precision) for every detection reported at the same time on both
  sides;
* N(*MAD) differences reported, not required to vanish;
* remaining rows paired within ``--pair-window`` seconds (default: the 6 s
  native de-duplication window): the race perturbs
  N(*MAD), so the in-window peak that wins the native de-duplication (and with
  it the reported time and grid node) can change for the same event;
* rows still unpaired to have N(*MAD) within ``--race-band`` of the 12.0
  threshold (the race can move a detection across it).
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve()
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT / "runtime" / "python" / "MatchLocatepy"))
from matchlocate_runner.native import parse_eventcase  # noqa: E402

UPSTREAM = ROOT / "source" / "upstream" / "example"
FIELDS = ("latitude", "longitude", "depth_km", "magnitude", "cc")
FORMATS = {"latitude": "{:.4f}", "longitude": "{:.4f}", "depth_km": "{:.2f}", "magnitude": "{:.2f}", "cc": "{:.4f}"}


def compare(ours, ref, threshold, band, pair_window):
    a = {f"{d.time_s:.3f}": d for d in ours}
    b = {f"{d.time_s:.3f}": d for d in ref}
    common = sorted(set(a) & set(b))
    mismatched = [k for k in common
                  if any(FORMATS[f].format(getattr(a[k], f)) != FORMATS[f].format(getattr(b[k], f)) for f in FIELDS)]
    left = sorted(set(a) - set(b), key=float)
    right = sorted(set(b) - set(a), key=float)
    pairs = []
    for k in left:
        near = [r for r in right if abs(float(r) - float(k)) <= pair_window]
        if near:
            r = min(near, key=lambda x: abs(float(x) - float(k)))
            right.remove(r)
            pairs.append((k, r))
    paired_left = {k for k, _ in pairs}
    only = [(k, a[k].nmad, "ours") for k in left if k not in paired_left] + [(k, b[k].nmad, "upstream") for k in right]
    unexplained = [o for o in only if abs(o[1] - threshold) > band]
    dn = [abs(a[k].nmad - b[k].nmad) for k in common]
    return {"ours": len(a), "upstream": len(b), "common": len(common), "field_mismatches": mismatched,
            "race_shifted_pairs": len(pairs),
            "race_shift_max_s": round(max((abs(float(k) - float(r)) for k, r in pairs), default=0.0), 3),
            "one_sided": sorted(only), "unexplained_one_sided": unexplained,
            "nmad_abs_diff_max": round(max(dn), 4) if dn else 0.0,
            "nmad_abs_diff_median": round(sorted(dn)[len(dn) // 2], 4) if dn else 0.0}


def read_detected_final(path):
    rows = []
    for line in path.read_text().splitlines():
        if line.startswith("#") or not line.strip():
            continue
        p = line.split()
        hh, mm, ss = p[2].split(":")
        t = int(hh) * 3600 + int(mm) * 60 + float(ss)
        rows.append(type("D", (), dict(time_s=t, latitude=float(p[3]), longitude=float(p[4]), depth_km=float(p[5]),
                                       magnitude=float(p[6]), cc=float(p[7]), nmad=float(p[8]), template_id=p[9])))
    return rows


def read_detections_csv(path):
    import csv
    rows = []
    with path.open() as handle:
        for r in csv.DictReader(handle):
            rows.append(type("D", (), dict(time_s=float(r["time_s"]), latitude=float(r["latitude"]),
                                           longitude=float(r["longitude"]), depth_km=float(r["depth_km"]),
                                           magnitude=float(r["magnitude"]), cc=float(r["cc"]),
                                           nmad=float(r["nmad"]), template_id=r["template_id"])))
    return rows


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--race-band", type=float, default=0.25)
    parser.add_argument("--pair-window", type=float, default=6.0,
                        help="seconds; the native de-duplication window (-D)")
    args = parser.parse_args()
    report = {"per_template": {}}
    ok = True
    ours_by_template = {}
    for ref_path in sorted((UPSTREAM / "20120902").iterdir()):
        ours = parse_eventcase(args.run_dir / "jobs" / "20120902" / ref_path.name / "EventCase.out")
        ours_by_template[ref_path.name] = {f"{d.time_s:.3f}": d for d in ours}
        result = compare(ours, parse_eventcase(ref_path), 12.0, args.race_band, args.pair_window)
        ok &= not result["field_mismatches"] and not result["unexplained_one_sided"]
        report["per_template"][ref_path.name] = result
    ours_final = read_detections_csv(args.run_dir / "detections.csv")
    upstream_final = read_detected_final(UPSTREAM / "MultipleTemplate" / "DetectedFinal.dat")
    final = compare(ours_final, upstream_final, 12.0, args.race_band, args.pair_window)
    # Several templates can detect one event at the same time; the merge keeps
    # the largest N(*MAD), so race-perturbed values can select another
    # template. Explained when our own detection by the upstream-selected
    # template matches the upstream row field for field.
    upstream_at = {f"{d.time_s:.3f}": d for d in upstream_final}
    template_choice = []
    for key in final["field_mismatches"]:
        ref = upstream_at[key]
        mine = ours_by_template.get(ref.template_id, {}).get(key)
        if mine is not None and all(FORMATS[f].format(getattr(mine, f)) == FORMATS[f].format(getattr(ref, f))
                                    for f in FIELDS):
            template_choice.append(key)
    final["race_template_choice"] = template_choice
    final["field_mismatches"] = [k for k in final["field_mismatches"] if k not in template_choice]
    ok &= not final["field_mismatches"] and not final["unexplained_one_sided"]
    report["final_catalog"] = final
    totals = report["per_template"].values()
    report["summary"] = {
        "status": "pass" if ok else "fail",
        "per_template_common": sum(r["common"] for r in totals),
        "per_template_field_mismatches": sum(len(r["field_mismatches"]) for r in totals),
        "per_template_race_shifted_pairs": sum(r["race_shifted_pairs"] for r in totals),
        "per_template_race_shift_max_s": max(r["race_shift_max_s"] for r in totals),
        "per_template_unpaired_near_threshold": sum(len(r["one_sided"]) for r in totals),
        "final_common": final["common"], "final_ours": final["ours"], "final_upstream": final["upstream"],
        "final_field_mismatches": len(final["field_mismatches"]),
        "final_race_template_choice": len(final["race_template_choice"]),
        "final_race_shifted_pairs": final["race_shifted_pairs"],
        "nmad_abs_diff_max": max([r["nmad_abs_diff_max"] for r in totals] + [final["nmad_abs_diff_max"]]),
    }
    print(json.dumps(report["summary"], indent=2))
    (args.run_dir / "upstream_comparison.json").write_text(json.dumps(report, indent=2) + "\n")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
