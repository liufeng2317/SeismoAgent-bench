#!/usr/bin/env python3
"""A scripted stand-in for the Agent: exercises the run package, the checker and the contract without a model.

Run by the benchmark runner (``run-agent``) inside a fresh run directory. It
- lists what the run gives the Agent (inputs, skills, tools) into work/smoke/inputs.json;
- submits the products of an earlier completed run (catalog.csv, picks.csv), unchanged;
- runs the checker as the catalog-checker skill asks (``--stage all`` on the submitted files with waveforms and
  StationXML) and runs ``region.py``;
- writes a ``justified`` disposition for every flag, saying that this is a smoke test.
Nothing here is a scientific product.
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--source-run", type=Path, required=True, help="completed run directory whose products are submitted")
    ap.add_argument("--checker", type=Path, required=True, help="seismotools/checker")
    a = ap.parse_args()
    inp, out = Path(os.environ["BENCH_INPUT"]), Path(os.environ["BENCH_OUTPUT"])
    (out / "smoke").mkdir(parents=True, exist_ok=True)
    seen = {"BENCH_INPUT": str(inp), "BENCH_OUTPUT": str(out),
            "input_entries": sorted(p.name for p in inp.iterdir()),
            "skills": sorted(os.path.relpath(os.path.join(d, "SKILL.md"), inp)  # inputs are symlinks: follow them
                             for top in inp.iterdir() if top.name != "waveforms"
                             for d, _, files in os.walk(top, followlinks=True) if "SKILL.md" in files),
            "env": {k: v for k, v in os.environ.items() if k.startswith(("BENCH_", "TOOLS_", "PIP_"))}}
    (out / "smoke/inputs.json").write_text(json.dumps(seen, indent=1))
    for name in ("catalog.csv", "picks.csv"):
        shutil.copyfile(a.source_run / "work" / name, out / name)
    final = out / "checker/final"
    cmd = [sys.executable, "-W", "ignore", str(a.checker / "interface/run.py"), "--stage", "all",
           "--catalog", str(out / "catalog.csv"), "--picks", str(out / "picks.csv"),
           "--stations", str(out / "input/waveforms/stations"), "--waveforms", str(out / "input/waveforms/data"),
           "--output-dir", str(final)]
    r = subprocess.run(cmd, capture_output=True, text=True)
    (out / "smoke/checker.log").write_text(r.stdout + r.stderr)
    if r.returncode != 0:
        print("checker failed", r.returncode, file=sys.stderr)
        return r.returncode
    reg = subprocess.run([sys.executable, "-W", "ignore", str(a.checker / "interface/region.py"), "--catalog",
                          str(out / "catalog.csv"), "--stations", str(out / "input/waveforms/stations"),
                          "--output-dir", str(out / "checker/region")], capture_output=True, text=True)
    (out / "smoke/region.log").write_text(reg.stdout + reg.stderr)
    report = json.loads((final / "checker_report.json").read_text())
    disp = [{"flag_id": f["flag_id"], "disposition": "justified",
             "evidence": "smoke test of the run package: products copied unchanged from an earlier run "
                         f"({a.source_run.name}); see work/smoke/inputs.json"} for f in report.get("flags", [])]
    (out / "checker/dispositions.json").write_text(json.dumps(disp, indent=1))
    print(json.dumps({"flags": [f["flag_id"] for f in report.get("flags", [])], "region_rc": reg.returncode}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
