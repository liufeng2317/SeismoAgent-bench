#!/usr/bin/env python3
"""Run bounded real-data checks against the Ridgecrest case artifacts."""
from __future__ import annotations

import contextlib
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd
from obspy import UTCDateTime, read, read_inventory

ROOT = Path(__file__).resolve().parents[2]
DATA = Path(os.environ.get("RIDGECREST_DATA_ROOT", "/ai4earthafs/liufeng/ScienceDiscovery/SeismoAgentBench/data/2019_ridgecrest_california/waveforms"))
EXPORT = Path(os.environ.get("RIDGECREST_EXPORT_ROOT", str(ROOT / "workflows/tasks/2019_ridgecrest_california/expert/export/01_baseline")))


def phase_net_check(report: dict) -> None:
    os.environ["SEISBENCH_CACHE_ROOT"] = str(ROOT / "seismotools/phase_picking/cache")
    sys.path.insert(0, str(ROOT / "seismotools/phase_picking/source"))
    import torch
    from phase_picking.model.phasenet import PhaseNet
    station = "CI.CCC"
    day = DATA / "data" / station
    start = UTCDateTime("2019-07-05T00:00:00Z")
    traces = []
    for component in ("HHZ", "HHN", "HHE"):
        path = day / f"{station}..{component}__20190705T000000Z__20190706T000000Z.mseed"
        trace = read(str(path))[0].copy().trim(start, start + 30, pad=True, fill_value=0)
        if trace.stats.sampling_rate != 100:
            trace.resample(100)
        traces.append(trace.data[:3001])
    waveform = np.stack(traces).astype("float32")
    assert waveform.shape == (3, 3001)
    model_dir = ROOT / "seismotools/phase_picking/weights/phasenet"
    meta = json.loads((model_dir / "original.json.v2").read_text())
    model = PhaseNet(**meta["model_args"])
    state = torch.load(model_dir / "original.pt.v2", map_location="cpu", weights_only=True)
    model.load_state_dict(state.get("state_dict", state), strict=True)
    model.eval()
    with torch.inference_mode():
        prediction = model(torch.from_numpy(waveform[None]))
    assert prediction.shape == (1, 3, 3001) and torch.isfinite(prediction).all()
    report["phasenet_real"] = {"status": "pass", "station": station, "window_start": str(start), "samples": 3001, "channels": ["HHZ", "HHN", "HHE"]}


def gamma_check(report: dict) -> None:
    sys.path.insert(0, str(ROOT / "seismotools/gamma/source"))
    from gamma.utils import association
    folder = EXPORT / "03_associate_gamma/full"
    picks = pd.read_csv(folder / "picks.csv", keep_default_na=False)
    stations = pd.read_csv(folder / "stations.csv")
    counts = picks[picks.event_id != ""].groupby("event_id").agg(n=("pick_id", "size"), ns=("station_id", "nunique"))
    selected = counts[(counts.n >= 10) & (counts.ns >= 6)].sort_values("n", ascending=False).index[0]
    selected_picks = picks[picks.event_id == selected].copy()
    converted = pd.DataFrame({"timestamp": pd.to_datetime(selected_picks.time_utc, utc=True), "amp": 1.0, "id": selected_picks.instrument_id, "type": selected_picks.phase, "prob": selected_picks.probability})
    station_table = stations[["id", "x(km)", "y(km)", "z(km)"]]
    config = {"use_amplitude": False, "use_dbscan": False, "ncpu": 1, "dims": ["x(km)", "y(km)", "z(km)"], "vel": {"p": 6.0, "s": 3.46}, "min_picks_per_eq": 10, "min_p_picks_per_eq": 4, "min_s_picks_per_eq": 3, "min_stations": 6, "oversample_factor": 2, "covariance_prior": [3.0], "max_sigma11": 1.5, "bfgs_bounds": [(-200, 200), (-200, 200), (-5, 35), (None, None)], "x(km)": [-200, 200], "y(km)": [-200, 200], "z(km)": [-5, 35]}
    with contextlib.redirect_stdout(io.StringIO()):
        events, assignments = association(converted, station_table, config, method="BGMM")
    assert events and assignments
    report["gamma_real"] = {"status": "pass", "source_event": str(selected), "input_picks": len(converted), "events": len(events), "assignments": len(assignments)}


def nonlinloc_check(report: dict) -> None:
    source_root = EXPORT / "04_locate_nonlinloc"
    source_event = source_root / "events_raw/gamma_0000001"
    binary = ROOT / "seismotools/nonlinloc/bin/NLLoc"
    with tempfile.TemporaryDirectory(prefix="ridgecrest-nll-") as tmp:
        base = Path(tmp) / "run"
        event = base / "events_raw/gamma_0000001"
        event.mkdir(parents=True)
        (base / "grids").symlink_to(source_root / "grids", target_is_directory=True)
        for name in ("control.in", "input.obs"):
            shutil.copy2(source_event / name, event / name)
        result = subprocess.run([str(binary), "control.in"], cwd=event, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=True)
        solutions = list(event.glob("solution.*.loc.hyp"))
        assert solutions and "1 events located" in result.stdout
    report["nonlinloc_real"] = {"status": "pass", "source_event": "gamma_0000001", "located_events": 1}


def hypodd_check(report: dict) -> None:
    source = ROOT / "workflows/tasks/2019_ridgecrest_california/expert/export/06_full_catalog/53_native_double_difference/hypodd_ct"
    binary = ROOT / "seismotools/hypodd/bin/hypoDD"
    blocks, event_ids, current = [], set(), []
    with (source / "dt.ct").open() as handle:
        for line in handle:
            if line.startswith("#") and current:
                blocks.append(current)
                if len(blocks) == 2:
                    break
                current = []
            if not current and line.startswith("#"):
                event_ids.update(map(int, line.split()[1:3]))
            current.append(line)
    if len(blocks) < 2:
        blocks.append(current)
    event_lines = [line for line in (source / "event.dat").read_text().splitlines() if int(line.split()[-1]) in event_ids]
    with tempfile.TemporaryDirectory(prefix="ridgecrest-hypodd-") as tmp:
        work = Path(tmp)
        (work / "event.dat").write_text("\n".join(event_lines) + "\n")
        shutil.copy2(source / "station.dat", work / "station.dat")
        (work / "dt.ct").write_text("".join("".join(block) for block in blocks))
        (work / "dt.cc").write_text("")
        shutil.copy2(source / "hypoDD.inp", work / "hypoDD.inp")
        result = subprocess.run([str(binary), "hypoDD.inp"], cwd=work, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=True)
        assert (work / "hypoDD.loc").is_file() and "# events =" in result.stdout
    report["hypodd_real"] = {"status": "pass", "event_pairs": len(blocks), "events_parsed": len(event_lines), "mode": "CT", "note": "bounded replay of real differential-time input"}


def main() -> None:
    inventory = read_inventory(str(DATA / "stations/earthscope.stationxml"))
    report = {"status": "pass", "data_root": str(DATA), "stationxml_networks": len(inventory.networks), "stationxml_stations": sum(len(n.stations) for n in inventory.networks)}
    phase_net_check(report)
    gamma_check(report)
    nonlinloc_check(report)
    hypodd_check(report)
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
