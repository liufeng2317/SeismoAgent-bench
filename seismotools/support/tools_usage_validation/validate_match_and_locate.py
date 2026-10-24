#!/usr/bin/env python3
"""Validate the local Match&Locate package: Python layer, native build, synthetic and upstream data."""
from __future__ import annotations

import json
import math
import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
TOOL = ROOT / "seismotools" / "match_and_locate"
BIN = TOOL / "runtime" / "bin"
PY = sys.executable
ARCHIVE = Path(os.environ.get("MATCHLOCATE_ARCHIVE", "/liufeng1afs/software/Download/MatchLocate2-master.zip"))
sys.path.insert(0, str(TOOL / "runtime" / "python" / "MatchLocatepy"))

from matchlocate_runner import (KM_PER_DEG, LayeredModel, SearchGrid, first_arrival,  # noqa: E402
                                merge_detections, parse_eventcase, parse_selectfinal, read_sac_header,
                                select_templates, write_selectfinal_input)


def check_traveltime() -> dict:
    homo = LayeredModel((0.0,), (6.0,), (3.5,))
    worst = 0.0
    for d, z in ((0.0, 5.0), (3.0, 8.0), (20.0, 10.0), (40.0, 2.0)):
        ray = first_arrival(homo, "P", d, z)
        r = math.hypot(d, z)
        worst = max(worst, abs(ray.travel_time_s - r / 6.0), abs(ray.p_s_per_km - d / (6.0 * r)),
                    abs(ray.dtdz_s_per_km - z / (6.0 * r)))
    layered = LayeredModel((0.0, 1.5, 17.1), (3.4, 5.9, 6.4), (1.97, 3.41, 3.70))
    fd = 0.0
    for d, z in ((5.0, 9.0), (25.0, 12.0), (60.0, 15.0)):
        h = 1e-4
        ray = first_arrival(layered, "S", d, z)
        dtd = (first_arrival(layered, "S", d + h, z).travel_time_s - first_arrival(layered, "S", d - h, z).travel_time_s) / (2 * h)
        dtz = (first_arrival(layered, "S", d, z + h).travel_time_s - first_arrival(layered, "S", d, z - h).travel_time_s) / (2 * h)
        fd = max(fd, abs(dtd - ray.p_s_per_km), abs(dtz - ray.dtdz_s_per_km))
    head = first_arrival(LayeredModel((0.0, 10.0), (6.0, 8.0), (3.5, 4.6)), "P", 150.0, 5.0)
    expected = 150.0 / 8.0 + (15.0) * math.sqrt(1 / 36 - 1 / 64)
    assert worst < 1e-9 and fd < 1e-5 and head.kind == "head:1" and abs(head.travel_time_s - expected) < 1e-9
    grid = SearchGrid.from_km(40.75, 1.0, 0.25, 1.0, 0.5)
    assert grid.node_count() == 9 * 9 * 5
    assert SearchGrid(0, 0, 0, 0.005, 0.005, 1.0).node_count() == 1
    return {"homogeneous_max_abs_error": worst, "layered_derivative_vs_fd_max": fd, "head_wave": head.kind,
            "grid_nodes_1km_025": grid.node_count()}


def check_select() -> dict:
    # Two tight clusters 5 km apart: radius 1 km needs one template per cluster.
    catalog = [{"event_id": f"e{i}", "latitude": 35.0 + (i % 2) * 0.045, "longitude": -117.0, "depth_km": 8.0,
                "magnitude": 1.0 + i / 10} for i in range(10)]
    chosen = select_templates(catalog, catalog, radius_km=1.0)
    assert len(chosen["templates"]) == 2 and chosen["covered_fraction"] == 1.0
    return {"clusters": 2, "templates": len(chosen["templates"]), "covered_fraction": chosen["covered_fraction"]}


def check_sac_reader(sac_path: Path) -> dict:
    from obspy.io.sac import SACTrace
    ours, ref = read_sac_header(sac_path), SACTrace.read(str(sac_path), headonly=True)
    pairs = {"delta": (ours.delta, ref.delta), "b": (ours.b, ref.b), "o": (ours.o, ref.o), "t1": (ours.t[1], ref.t1),
             "t2": (ours.t[2], ref.t2), "evdp": (ours.evdp, ref.evdp), "user0": (ours.user0, ref.user0),
             "npts": (ours.npts, ref.npts)}
    bad = {k: v for k, v in pairs.items() if (v[0] is None) != (v[1] is None) or (v[0] is not None and abs(v[0] - v[1]) > 1e-6)}
    assert not bad, bad
    assert ours.reference is not None and abs((ours.reference.timestamp()) - ref.reftime.timestamp) < 1e-6
    return {"file": sac_path.name, "fields_checked": sorted(pairs)}


def run(cmd, **kw):
    return subprocess.run(cmd, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, **kw)


def main() -> None:
    report = {"tool": "match_and_locate", "binaries": sorted(p.name for p in BIN.iterdir()) if BIN.is_dir() else []}
    for name in ("MatchLocate2", "SelectFinal"):
        assert (BIN / name).is_file() and os.access(BIN / name, os.X_OK), f"missing {name}; run build_native.py"
    report["traveltime"] = check_traveltime()
    report["select_templates"] = check_select()

    with tempfile.TemporaryDirectory(prefix="matchlocate-validation-") as tmp:
        work = Path(tmp)
        inputs = work / "inputs"
        r = run([PY, "-I", str(TOOL / "examples/smoke/make_synthetic.py"), "--output-dir", str(inputs)])
        assert r.returncode == 0, r.stdout
        r = run([PY, "-I", str(TOOL / "interface/prepare.py"), "--waveforms", str(inputs / "waveforms"),
                 "--stations", str(inputs / "stations.csv"), "--templates", str(inputs / "templates.csv"),
                 "--picks", str(inputs / "picks.csv"), "--velocity-model", str(inputs / "velocity_model.csv"),
                 "--config", str(inputs / "prepare_config.json"), "--output-dir", str(work / "ds"),
                 "--workers", "4", "--quiet"])
        assert r.returncode == 0, r.stdout[-2000:]
        prepared = json.loads((work / "ds" / "prepare_result.json").read_text())
        report["prepare"] = {k: prepared[k] for k in ("status", "templates_kept", "rows_kept", "segments",
                                                      "stations_used", "task_errors")}
        report["sac_reader"] = check_sac_reader(next((work / "ds" / "templates" / "T0").glob("*.sac")))
        r = run([PY, "-I", str(TOOL / "interface/run.py"), "--input-dir", str(work / "ds"), "--output-dir",
                 str(work / "run"), "--threads", "4", "--quiet"])
        assert r.returncode == 0, r.stdout[-2000:]
        r = run([PY, "-I", str(TOOL / "examples/smoke/check_synthetic.py"), "--inputs-dir", str(inputs),
                 "--run-dir", str(work / "run")])
        synthetic = json.loads(r.stdout)
        assert r.returncode == 0, r.stdout
        # Day-segment preparation (data cover 20 min of the day; the rest is
        # zero-filled) scanned as a plain matched filter (one grid node): the
        # three co-located events must be found, the two offset ones must not.
        config = json.loads((inputs / "prepare_config.json").read_text())
        config["segments"] = {"days": ["2020-01-01"]}
        config["run"]["search"] = {"units": "km", "half_width_km": 0.0, "step_km": 0.25,
                                   "half_depth_km": 0.0, "step_depth_km": 0.25}
        (work / "day_config.json").write_text(json.dumps(config))
        r = run([PY, "-I", str(TOOL / "interface/prepare.py"), "--waveforms", str(inputs / "waveforms"),
                 "--stations", str(inputs / "stations.csv"), "--templates", str(inputs / "templates.csv"),
                 "--picks", str(inputs / "picks.csv"), "--velocity-model", str(inputs / "velocity_model.csv"),
                 "--config", str(work / "day_config.json"), "--output-dir", str(work / "day_ds"),
                 "--workers", "8", "--quiet"])
        assert r.returncode == 0, r.stdout[-2000:]
        r = run([PY, "-I", str(TOOL / "interface/run.py"), "--input-dir", str(work / "day_ds"), "--output-dir",
                 str(work / "day_run"), "--threads", "16", "--quiet"])
        assert r.returncode == 0, r.stdout[-2000:]
        r = run([PY, "-I", str(TOOL / "examples/smoke/check_synthetic.py"), "--inputs-dir", str(inputs),
                 "--run-dir", str(work / "day_run")])
        mf = json.loads(r.stdout)
        found = [e["truth_time_s"] for e in mf["events"] if e["detected"]]
        assert found == [120.0, 330.0, 790.0] and not mf["extra_detections"], mf
        report["day_segment_matched_filter"] = {"status": "pass", "detected_truth_times_s": found,
                                                "missed_offset_events_s": [560.0, 1000.0]}
        report["synthetic"] = {"status": synthetic["status"], "events": len(synthetic["events"]),
                               "max_abs_dt_s": max(abs(e["dt_s"]) for e in synthetic["events"]),
                               "max_horizontal_error_km": max(e["horizontal_error_km"] for e in synthetic["events"]),
                               "max_abs_depth_error_km": max(abs(e["depth_error_km"]) for e in synthetic["events"]),
                               "magnitude_errors": [e["magnitude_error"] for e in synthetic["events"]]}

        if not ARCHIVE.is_file():
            report["upstream_hinet"] = {"status": "skipped", "reason": f"archive not found: {ARCHIVE}"}
        else:
            r = run([PY, "-I", str(TOOL / "examples/workflow/prepare_upstream_example.py"), "--archive", str(ARCHIVE),
                     "--data-dir", str(work / "hinet_data"), "--dataset-dir", str(work / "hinet")])
            assert r.returncode == 0, r.stdout
            outputs = {}
            for threads, jobs in ((1, 14), (8, 4)):
                out = work / f"hinet_run_t{threads}"
                r = run([PY, "-I", str(TOOL / "interface/run.py"), "--input-dir", str(work / "hinet"), "--output-dir",
                         str(out), "--jobs", str(jobs), "--threads", str(threads), "--quiet"])
                assert r.returncode == 0, r.stdout[-2000:]
                outputs[threads] = out
            same = all((outputs[1] / "jobs" / d.relative_to(outputs[8] / "jobs") / "EventCase.out").read_bytes()
                       == (d / "EventCase.out").read_bytes() for d in (outputs[8] / "jobs" / "20120902").iterdir())
            assert same, "thread count changed native output"
            r = run([PY, "-I", str(TOOL / "examples/workflow/compare_reference.py"), "--run-dir", str(outputs[1])])
            comparison = json.loads(r.stdout)
            assert r.returncode == 0, r.stdout
            rows = []
            for d in sorted((outputs[1] / "jobs" / "20120902").iterdir()):
                rows += parse_eventcase(d / "EventCase.out", template_id=d.name)
            merge_dir = work / "merge"
            merge_dir.mkdir()
            write_selectfinal_input(merge_dir / "Allevents", rows)
            run([str(BIN / "SelectFinal"), "-H0.3/12.0", "-D6.0", "Allevents"], cwd=merge_dir, check=True)
            native = [(f"{d.time_s:.3f}", d.template_id) for d in parse_selectfinal(merge_dir / "Allevents.final")]
            python = [(f"{d.time_s:.3f}", d.template_id) for d in merge_detections(rows, 0.3, 12.0, 6.0)]
            assert native == python, "python merge differs from native SelectFinal"
            report["upstream_hinet"] = {"status": "pass", "threads_1_vs_8_identical": same,
                                        "merge_python_equals_native": True, "final_events": len(native),
                                        "comparison": comparison}

            # Second upstream example: per-node CC distribution (-O3) on a
            # non-day segment whose SAC reference is the scanned event's origin.
            r = run([PY, "-I", str(TOOL / "examples/ccdistribution/prepare_ccdistribution_example.py"), "--archive",
                     str(ARCHIVE), "--data-dir", str(work / "ccd_data"), "--dataset-dir", str(work / "ccd")])
            assert r.returncode == 0, r.stdout
            r = run([PY, "-I", str(TOOL / "interface/run.py"), "--input-dir", str(work / "ccd"), "--output-dir",
                     str(work / "ccd_run"), "--threads", "16", "--quiet"])
            assert r.returncode == 0, r.stdout[-2000:]
            r = run([PY, "-I", str(TOOL / "examples/ccdistribution/compare_ccdistribution.py"), "--run-dir",
                     str(work / "ccd_run"), "--upstream-ccdistribution",
                     str(work / "ccd_data/archive/MatchLocate2-master/example_CCdistribution/CCdistribution.out")])
            ccd = json.loads(r.stdout)
            assert r.returncode == 0, r.stdout
            report["upstream_ccdistribution"] = {k: ccd[k] for k in ("status", "checks", "rows", "cc_abs_diff_max",
                                                                     "nmad_abs_diff_median", "nmad_abs_diff_max")}
    report["status"] = "pass"
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
