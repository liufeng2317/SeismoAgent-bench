#!/usr/bin/env python3
"""Summarise outputs/velocity_from_data/*.json: does a model built from the data beat the generic column?

Rules compared per case (pass = |dt| <= 0.3 s, |dz| <= 1 km, shift <= 1 km, the trusted-catalog gates):
generic (scale 1, no corrections); station corrections only (scale 1, last iteration); minimum misfit
(the scale and iteration with the lowest median RMS, as VELEST chooses); minimum misfit among the last
iterations only; and the best step in hindsight (lowest |dt|/0.3 + |dz| + shift, using the references).
"""
from __future__ import annotations

import json
from pathlib import Path

HERE = Path(__file__).resolve().parent


def err(s: dict) -> float:
    return abs(s["dt_s"]) / 0.3 + abs(s["dz_km"]) + max(0.0, s["shift_km"] - 1.0)


def fmt(s: dict) -> str:
    ok = abs(s["dt_s"]) <= 0.3 and abs(s["dz_km"]) <= 1.0 and s["shift_km"] <= 1.0
    return (f"x{s['scale']:.2f} it{s['iteration']}  rms {s['median_rms_s']:.3f}  dt {s['dt_s']:+.2f}  dz {s['dz_km']:+.2f}  "
            f"shift {s['shift_km']:.2f}  {'PASS' if ok else '-'}")


def main() -> None:
    for f in sorted((HERE / "outputs/velocity_from_data").glob("*.json")):
        r = json.loads(f.read_text())
        st = [s for s in r["steps"] if s.get("dt_s") is not None and s.get("dz_km") is not None]
        last = max(s["iteration"] for s in st)
        unit = [s for s in st if s["scale"] == 1.0]          # variants with a reduced scale range have none
        rules = {}
        if unit:
            rules["generic"] = next(s for s in unit if s["iteration"] == 0)
            rules["station corrections"] = max(unit, key=lambda s: s["iteration"])
        rules.update({
            "minimum misfit": min(st, key=lambda s: s["median_rms_s"]),
            "minimum misfit, corrected": min((s for s in st if s["iteration"] == last), key=lambda s: s["median_rms_s"]),
            "best in hindsight": min(st, key=err),
        })
        scales = sorted({s["scale"] for s in st})
        print(f"{f.stem}  (scales {scales[0]:.2f}-{scales[-1]:.2f}, damping {r.get('damping', 1.0)}, cap {r.get('cap_s')})")
        for k, s in rules.items():
            print(f"  {k:26s} {fmt(s)}")


if __name__ == "__main__":
    main()
