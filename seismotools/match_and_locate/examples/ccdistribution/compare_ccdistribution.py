#!/usr/bin/env python3
"""Compare an interface run of the CC-distribution example with the upstream outputs.

``CCdistribution.out`` rows are (time, lat, lon, depth, CC, N*MAD) for every
node and sample above the per-node threshold. The CC column does not depend
on the upstream N(*MAD) race (patch 0001), so it must agree exactly on every
row present on both sides; N(*MAD) and the per-node thresholds do depend on
it, so the row sets may differ slightly and the reported detection may sit
on a neighbouring sample. Pass requires:

* identical CC on all common rows, and common rows >= ``--min-common`` of
  each side;
* one detection on each side, the same event: |dt| <= 0.01 s, horizontal
  offset <= 2 grid steps, same depth and magnitude;
* both reported samples present in both outputs with identical CC;
* our reported sample is the maximum N(*MAD) row of our own output (the
  native de-duplication rule).
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

TEMPLATE = "20120902032413.12"
SEGMENT = "20120902033351.61"
STEP_DEG = 0.0001


def load(path: Path) -> dict:
    rows = {}
    with path.open() as handle:
        for line in handle:
            if line.startswith("#") or not line.strip():
                continue
            t, la, lo, z, cc, nmad = line.split()
            rows[(t, la, lo, z)] = (float(cc), float(nmad))
    return rows


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--upstream-ccdistribution", type=Path, required=True,
                        help="example_CCdistribution/CCdistribution.out from the extracted archive")
    parser.add_argument("--min-common", type=float, default=0.97)
    args = parser.parse_args()
    job = args.run_dir / "jobs" / SEGMENT / TEMPLATE
    ours, upstream = load(job / "CCdistribution.out"), load(args.upstream_ccdistribution)
    common = set(ours) & set(upstream)
    cc_diff = max((abs(ours[k][0] - upstream[k][0]) for k in common), default=float("inf"))
    nmad_diff = sorted(abs(ours[k][1] - upstream[k][1]) for k in common)

    mine = parse_eventcase(job / "EventCase.out")
    ref = parse_eventcase(ROOT / "source" / "upstream" / "example_CCdistribution" / "20120902" / TEMPLATE)
    key = lambda d: (f"{d.time_s:.3f}", f"{d.latitude:.4f}", f"{d.longitude:.4f}", f"{d.depth_km:.4f}")
    checks = {"one_detection_each": len(mine) == 1 and len(ref) == 1}
    detection = {}
    if checks["one_detection_each"]:
        a, b = mine[0], ref[0]
        ka, kb = key(a), key(b)
        detection = {"ours": dict(zip(("time_s", "lat", "lon", "depth_km"), ka), magnitude=a.magnitude, cc=a.cc, nmad=a.nmad),
                     "upstream": dict(zip(("time_s", "lat", "lon", "depth_km"), kb), magnitude=b.magnitude, cc=b.cc, nmad=b.nmad),
                     "ours_sample_in_upstream_output": upstream.get(ka),
                     "upstream_sample_in_our_output": ours.get(kb)}
        checks["same_event"] = (abs(a.time_s - b.time_s) <= 0.01 + 1e-9
                                and abs(a.latitude - b.latitude) <= 2 * STEP_DEG + 1e-9
                                and abs(a.longitude - b.longitude) <= 2 * STEP_DEG + 1e-9
                                and a.depth_km == b.depth_km and a.magnitude == b.magnitude)
        checks["reported_samples_same_cc_both_sides"] = (
            ka in ours and ka in upstream and kb in ours and kb in upstream
            and ours[ka][0] == upstream[ka][0] and ours[kb][0] == upstream[kb][0])
        best = max(ours.items(), key=lambda kv: kv[1][1])[0]
        checks["ours_reports_own_max_nmad"] = best == ka
    checks["cc_identical_on_common_rows"] = cc_diff == 0.0
    checks["common_fraction_ok"] = (len(common) >= args.min_common * len(ours)
                                    and len(common) >= args.min_common * len(upstream))
    ok = all(checks.values())
    report = {"status": "pass" if ok else "fail", "checks": checks,
              "rows": {"ours": len(ours), "upstream": len(upstream), "common": len(common)},
              "cc_abs_diff_max": cc_diff,
              "nmad_abs_diff_median": round(nmad_diff[len(nmad_diff) // 2], 4) if nmad_diff else None,
              "nmad_abs_diff_max": round(nmad_diff[-1], 4) if nmad_diff else None,
              "detection": detection}
    print(json.dumps(report, indent=2))
    (args.run_dir / "upstream_ccdistribution_comparison.json").write_text(json.dumps(report, indent=2) + "\n")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
