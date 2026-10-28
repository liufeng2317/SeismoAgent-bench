#!/usr/bin/env python3
"""Validate NonLinLoc: native stages, the v2 adapter (smoke regression, location
methods) and the v3 catalog locator (synthetic known answers)."""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
BIN = ROOT / "seismotools" / "nonlinloc" / "runtime" / "bin"
PYTHON_PACKAGE = ROOT / "seismotools" / "nonlinloc" / "runtime" / "python" / "Nonlinlocpy"

# The bundled Python interface is intentionally kept next to the native
# NonLinLoc package rather than installed into the host environment.
sys.path.insert(0, str(PYTHON_PACKAGE))
from nonlinlocpy import NLLocConfig, resolve_nlloc_bin_dir  # noqa: E402
from nonlinlocpy.workflows import copy_template_control_file  # noqa: E402
from nonlinlocpy.runner import run_nlloc_bin  # noqa: E402

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent))
from synthetic_events import make_case, write_case  # noqa: E402

TOOL = ROOT / "seismotools" / "nonlinloc"
PY = sys.executable
# v2 smoke solution (examples/smoke with config.json) before the 2026-10 changes
SMOKE_SOLUTION = {"lat": 36.12129630306454, "lon": -117.6320737732665, "depth_km": 1.82812}


native_logs: list[str] = []


def run_package_runner(binary_dir: Path, work: Path) -> None:
    """Exercise the Python runner while capturing native child-process output."""
    log_path = work / "nonlinlocpy.log"
    sys.stdout.flush()
    saved_stdout, saved_stderr = os.dup(1), os.dup(2)
    try:
        with log_path.open("w") as stream:
            os.dup2(stream.fileno(), 1)
            os.dup2(stream.fileno(), 2)
            run_nlloc_bin(str(binary_dir), str(work), "nll.in")
    finally:
        os.dup2(saved_stdout, 1)
        os.dup2(saved_stderr, 2)
        os.close(saved_stdout)
        os.close(saved_stderr)
    native_logs.append("$ Nonlinlocpy.run_nlloc_bin NLLoc nll.in\n" + log_path.read_text())


def run(binary: Path, control: Path, cwd: Path) -> str:
    result = subprocess.run([str(binary), control.name], cwd=cwd,
                            text=True, stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT, check=True)
    native_logs.append(f"$ {binary.name} {control.name} (cwd={cwd})\n{result.stdout}")
    return result.stdout


def epi_km(lat1, lon1, lat2, lon2):
    return np.hypot((np.asarray(lat1) - lat2) * 111.195,
                    (np.asarray(lon1) - lon2) * 111.195 * np.cos(np.radians(np.asarray(lat2))))


def locate(tmp: Path, name: str, arrivals: Path, stations: Path, model: Path, config: dict,
           delays: Path | None = None) -> pd.DataFrame:
    cfg = tmp / f"{name}.json"
    cfg.write_text(json.dumps(config))
    cmd = [PY, "-I", str(TOOL / "interface/locate.py"), "--arrivals", str(arrivals), "--stations", str(stations),
           "--velocity-model", str(model), "--output-dir", str(tmp / name), "--config", str(cfg),
           "--bin-dir", str(BIN), "--workers", "16", "--quiet"]
    if delays is not None:
        cmd += ["--station-delays", str(delays)]
    subprocess.run(cmd, check=True, capture_output=True)
    assert json.loads((tmp / name / "run_result.json").read_text())["status"] == "success"
    return pd.read_csv(tmp / name / "events.csv").set_index("event_id")


def check_smoke_regression(tmp: Path) -> dict:
    """v2 adapter: the smoke example (with its grid_center config) reproduces the earlier solution."""
    out = {}
    for method in ("EDT_OT_WT", "EDT", "GAU_ANALYTIC"):
        cfg = json.loads((TOOL / "examples/smoke/config.json").read_text())
        cfg["location_method"] = method
        (tmp / f"smoke_{method}.json").write_text(json.dumps(cfg))
        subprocess.run([PY, "-I", str(TOOL / "interface/run.py"), "--input-dir", str(TOOL / "examples/smoke/inputs"),
                        "--output-dir", str(tmp / f"smoke_{method}"), "--config", str(tmp / f"smoke_{method}.json"),
                        "--bin-dir", str(BIN)], check=True, capture_output=True)
        row = pd.read_csv(tmp / f"smoke_{method}" / "located_events.csv").iloc[0]
        out[method] = {"lat": float(row.lat), "lon": float(row.lon), "depth_km": float(row.depth_km)}
    d = out["EDT_OT_WT"]
    out["default_unchanged"] = all(abs(d[k] - SMOKE_SOLUTION[k]) < 1e-6 for k in SMOKE_SOLUTION)
    assert out["default_unchanged"], out
    return out


def check_synthetic(tmp: Path) -> dict:
    """v3 locator: noise-free half-space hypocentres for all methods; one 2 s outlier: EDT beats GAU."""
    res = {}
    for label, opts in (("exact", {}), ("outlier", {"outlier_s": 2.0})):
        case = make_case(seed=1, **opts)
        d = write_case(case, tmp / f"syn_{label}")
        case["picks"][case["picks"].event_id.astype(str) != ""].to_csv(d / "arrivals.csv", index=False)
        truth = case["events"].set_index("event_id")
        for method in ("GAU_ANALYTIC", "EDT", "EDT_OT_WT"):
            cfg = {"location_method": method, "grid_spacing_km": 0.25, "projection_center": case["projection_center"],
                   "region": {"latitude": [35.3, 35.7], "longitude": [-97.25, -96.75], "depth_km": [0, 20]}}
            e = locate(tmp, f"syn_{label}_{method}", d / "arrivals.csv", d / "stations.csv", d / "velocity_model.txt",
                       cfg).loc[truth.index]
            dh = epi_km(e.latitude, e.longitude, truth.latitude, truth.longitude)
            dt = (pd.to_datetime(e.origin_time_utc) - pd.to_datetime(truth.origin_time_utc)).dt.total_seconds()
            res[f"{label}_{method}"] = {"located": int((e.status == "LOCATED").sum()),
                                        "max_epi_km": round(float(dh.max()), 3),
                                        "max_abs_depth_km": round(float((e.depth_km - truth.depth_km).abs().max()), 3),
                                        "max_abs_origin_s": round(float(dt.abs().max()), 4),
                                        "outlier_event_epi_km": round(float(dh.iloc[0]), 3)}
    for method in ("GAU_ANALYTIC", "EDT", "EDT_OT_WT"):
        r = res[f"exact_{method}"]
        assert r["located"] == 40 and r["max_epi_km"] < 0.1 and r["max_abs_depth_km"] < 0.15 \
            and r["max_abs_origin_s"] < 0.02, (method, r)
    assert res["outlier_EDT"]["outlier_event_epi_km"] < res["outlier_GAU_ANALYTIC"]["outlier_event_epi_km"], res
    return res


def main() -> None:
    # Validate the bundled Python interface independently of the native run.
    # Hide PATH temporarily so this specifically exercises the package's
    # sibling ``seismotools/nonlinloc/runtime/bin`` fallback.
    original_path = os.environ.get("PATH", "")
    os.environ["PATH"] = ""
    try:
        resolved_bin = Path(resolve_nlloc_bin_dir(""))
    finally:
        os.environ["PATH"] = original_path
    assert resolved_bin.resolve() == BIN.resolve()
    assert NLLocConfig(nlloc_bin=str(BIN), control_dir=".").nlloc_bin == str(BIN)

    with tempfile.TemporaryDirectory(prefix="nll-validation-") as tmp:
        work = Path(tmp)
        (work / "vg.in").write_text("""CONTROL 1 54321
TRANS NONE
VGOUT model
VGGRID 2 5 5 0 0 0 1 1 1 SLOW_LEN
LAYER 0 5.0 0 3.0 0 2.7 0
VGTYPE P
""")
        (work / "gt.in").write_text("""CONTROL 1 54321
TRANS NONE
GTFILES model time P
GTMODE GRID2D ANGLES_NO
GT_PLFD 1.e-3 0
GTSRCE S0001 XYZ 0 0 0 0
""")
        (work / "obs").write_text("S0001 ? ? ? P ? 19700101 0000 1.0000 GAU 0.1 -1 -1 -1\n!END_EVENT\n!END_FILE\n")
        (work / "nll.in").write_text("""CONTROL 1 54321
TRANS NONE
GTSRCE S0001 XYZ 0 0 0 0
LOCFILES obs NLLOC_OBS ./time solution
LOCSEARCH OCT 1 1 1 0.1 100 10 0 0
LOCGRID 5 5 5 0 0 0 1 1 1 PROB_DENSITY SAVE
LOCMETH EDT_OT_WT 9999 2 -1 3 0 0 0 0 0
LOCHYPOUT SAVE_NLLOC_ALL
LOCGAU 0.1 0
LOCQUAL2ERR 0.1 0.2 0.5 1 999
LOCPHASEID P P
""")
        run(BIN / "Vel2Grid", work / "vg.in", work)
        run(BIN / "Grid2Time", work / "gt.in", work)
        nll_output = run(BIN / "NLLoc", work / "nll.in", work)
        assert (work / "model.P.mod.buf").is_file()
        assert (work / "time.P.S0001.time.buf").is_file()
        assert "events read" in nll_output
        # Exercise the package runner and packaged control template against
        # the same temporary case. The runner is deliberately followed by
        # output assertions because its public helper preserves the native
        # executable's output rather than returning a parsed solution.
        template_dir = work / "template-check"
        template_dir.mkdir()
        template = copy_template_control_file(template_dir)
        assert template.is_file()
        run_package_runner(BIN, work)
        assert list(work.glob("*.loc.hyp"))
    with tempfile.TemporaryDirectory(prefix="nll-v3-") as tmp:
        smoke = check_smoke_regression(Path(tmp))
        synthetic = check_synthetic(Path(tmp))
    log_dir = Path(os.environ.get("VALIDATION_LOG_DIR", str(Path(__file__).resolve().parent / "outputs")))
    log_dir.mkdir(parents=True, exist_ok=True)
    (log_dir / "validate_nonlinloc.native.log").write_text("\n\n".join(native_logs))
    print(json.dumps({"status": "pass", "tool": "NonLinLoc",
                      "python": {"package_import": True,
                                 "default_bin_resolution": True,
                                 "config_api": True,
                                 "template_resource": True},
                      "smoke": {"velocity_grid": True, "travel_time_grid": True, "locator_started": True,
                                 "note": "one-station synthetic input is intentionally underdetermined"},
                      "adapter_v2_smoke_methods": smoke,
                      "locate_v3_synthetic": synthetic}, indent=2))


if __name__ == "__main__":
    main()
