#!/usr/bin/env python3
"""Real-data checks of the seismotools interfaces on benchmark case products.

These checks read expert products and waveforms of the benchmark cases, so they
live outside ``seismotools/``: Agents in the ``tools`` arm read the tool
library, and the library must not point them at case products. The synthetic
and upstream-example checks stay in
``seismotools/support/tools_usage_validation/``; this module imports their
helpers. One JSON report per tool is printed (``--tool``).
"""
from __future__ import annotations

import argparse
import importlib
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "seismotools/support/tools_usage_validation"))
PY = sys.executable
RIDGECREST = ROOT / "workflows/tasks/2019_ridgecrest_california/expert/export"
RIDGECREST_WAVES = ROOT / "data/2019_ridgecrest_california/data/waveforms/data"
PRAGUE_TASK = ROOT / "workflows/tasks/2011_prague_oklahoma"
PRAGUE = PRAGUE_TASK / "expert/export/r2"
PRAGUE_WAVES = ROOT / "data/2011_prague_oklahoma/data/waveforms/data"
PRAGUE_HOURS = (pd.Timestamp("2011-11-11T00:00Z"), pd.Timestamp("2011-11-11T06:00Z"))


def tool(name: str):
    """The tool's validation module (synthetic checks and run helpers)."""
    return importlib.import_module(f"validate_{name}")


def prague_stations_model(tmp: Path) -> dict:
    """Write the r2 stations (sensor elevation) and 1-D model; return the r2 association settings."""
    st = pd.read_csv(PRAGUE / "03_associate_gamma/full/stations.csv")
    st.assign(elevation_m=st.elevation_m - st.sensor_depth_m)[["station_id", "latitude", "longitude", "elevation_m"]] \
        .to_csv(tmp / "prague_stations.csv", index=False)
    inputs = json.loads((PRAGUE / "03_associate_gamma/full/inputs.json").read_text())
    (tmp / "prague_model.txt").write_text("".join(f"{r['top_of_layer_km']} {r['vp_km_s']} {r['vs_km_s']}\n"
                                                 for r in inputs["model_source"]["rows"]))
    return inputs["settings"]


def prague_r2_events(n_events: int) -> pd.DataFrame:
    """n_events r2 stage-04 locations with >= 10 stations, evenly spaced in event id."""
    ref = pd.read_csv(PRAGUE / "04_locate_nonlinloc/full/events.csv")
    ref = ref[(ref.status == "LOCATED") & (ref.n_stations >= 10)].sort_values("event_id")
    return ref.iloc[np.linspace(0, len(ref) - 1, n_events).astype(int)].set_index("event_id")


def prague_arrivals(tmp: Path, event_ids) -> None:
    p = pd.read_csv(PRAGUE / "03_associate_gamma/full/picks.csv", keep_default_na=False)
    p[p.event_id.isin(event_ids)][["event_id", "pick_id", "station_id", "phase", "time_utc"]] \
        .to_csv(tmp / "prague_arrivals.csv", index=False)


def associator_vs_gamma(name: str, cfg_from_settings, workers: int) -> dict:
    """Six hours of Prague PhaseNet picks: an associator against the GaMMA r2 association."""
    with tempfile.TemporaryDirectory(prefix=f"{name}-case-") as tmp:
        tmp = Path(tmp)
        t0, t1 = PRAGUE_HOURS
        p = pd.read_csv(PRAGUE / "02_pick_phasenet/full/picks.csv")
        pt = pd.to_datetime(p.time_utc, utc=True, format="ISO8601")
        p[(pt >= t0) & (pt < t1)][["pick_id", "station_id", "phase", "time_utc", "probability"]] \
            .to_csv(tmp / "prague_picks.csv", index=False)
        s = prague_stations_model(tmp)
        out = tool(name).run(tmp, "prague", tmp / "prague_picks.csv", tmp / "prague_stations.csv",
                             tmp / "prague_model.txt", cfg_from_settings(s), workers)
        e = pd.read_csv(out / "events.csv")
    e["t"] = pd.to_datetime(e.time_utc, utc=True)
    g = pd.read_csv(PRAGUE / "03_associate_gamma/full/events.csv")
    g["t"] = pd.to_datetime(g.origin_time, utc=True, format="ISO8601")
    g = g[(g.t >= t0) & (g.t < t1)]

    def frac(a, b):
        hit = [((np.abs((b.t - r.t).dt.total_seconds()) <= 2) &
                (np.hypot((b.latitude - r.latitude) * 111.195, (b.longitude - r.longitude) * 90.6) <= 10)).any()
               for r in a.itertuples()]
        return round(float(np.mean(hit)), 3) if hit else float("nan")
    res = {"window": [str(t0), str(t1)], "gamma_events": len(g), f"{name}_events": len(e),
           f"gamma_matched_by_{name}": frac(g, e), "gamma_10_stations_matched": frac(g[g.n_stations >= 10], e),
           f"{name}_matched_by_gamma": frac(e, g)}
    assert 0.7 <= len(e) / len(g) <= 1.3 and res["gamma_10_stations_matched"] >= 0.9, res
    return res


def check_phasenet() -> dict:
    """One forward pass on 30 s of Ridgecrest three-component data."""
    from obspy import UTCDateTime, read
    import torch
    model = tool("phasenet").load_model()
    start = UTCDateTime("2019-07-05T00:00:00Z")
    real = []
    for component in ("HHZ", "HHN", "HHE"):
        path = RIDGECREST_WAVES / "CI.CCC" / f"CI.CCC..{component}__20190705T000000Z__20190706T000000Z.mseed"
        trace = read(str(path))[0].copy().trim(start, start + 30, pad=True, fill_value=0)
        if trace.stats.sampling_rate != 100:
            trace.resample(100)
        real.append(trace.data[:3001])
    waveform = torch.from_numpy(np.stack(real).astype("float32"))[None]
    with torch.inference_mode():
        prediction = model(waveform)
    assert waveform.shape == (1, 3, 3001)
    assert prediction.shape == (1, 3, 3001) and torch.isfinite(prediction).all()
    return {"station": "CI.CCC", "window_start": str(start), "input_shape": list(waveform.shape),
            "channels": ["HHZ", "HHN", "HHE"]}


def check_gamma() -> dict:
    """GaMMA re-associates the picks of the largest well-recorded Ridgecrest baseline event."""
    import contextlib
    import io
    tool("gamma")  # puts the bundled GaMMA source on sys.path
    from gamma.utils import association
    folder = RIDGECREST / "01_baseline/03_associate_gamma/full"
    picks = pd.read_csv(folder / "picks.csv", keep_default_na=False)
    stations = pd.read_csv(folder / "stations.csv")
    counts = picks[picks.event_id != ""].groupby("event_id").agg(n=("pick_id", "size"), ns=("station_id", "nunique"))
    selected = counts[(counts.n >= 10) & (counts.ns >= 6)].sort_values("n", ascending=False).index[0]
    sel = picks[picks.event_id == selected]
    converted = pd.DataFrame({"timestamp": pd.to_datetime(sel.time_utc, utc=True), "amp": 1.0,
                              "id": sel.instrument_id, "type": sel.phase, "prob": sel.probability})
    config = {"use_amplitude": False, "use_dbscan": False, "ncpu": 1,
              "dims": ["x(km)", "y(km)", "z(km)"], "vel": {"p": 6.0, "s": 3.46},
              "min_picks_per_eq": 10, "min_p_picks_per_eq": 4,
              "min_s_picks_per_eq": 3, "min_stations": 6, "oversample_factor": 2,
              "covariance_prior": [3.0], "max_sigma11": 1.5,
              "bfgs_bounds": [(-200, 200), (-200, 200), (-5, 35), (None, None)],
              "x(km)": [-200, 200], "y(km)": [-200, 200], "z(km)": [-5, 35]}
    with contextlib.redirect_stdout(io.StringIO()):
        events, assignments = association(converted, stations[["id", "x(km)", "y(km)", "z(km)"]], config, method="BGMM")
    assert events and assignments
    return {"source_event": str(selected), "input_picks": len(converted), "events": len(events),
            "assignments": len(assignments)}


def check_pyocto() -> dict:
    return associator_vs_gamma("pyocto", lambda s: {
        "region": {"latitude": s["latitude_bounds"], "longitude": s["longitude_bounds"], "depth_km": s["depth_bounds_km"]},
        "reference_elevation_km": s["reference_elevation_km"], "velocity_layering": s["velocity_layering"],
        "associator": {"n_picks": s["min_picks_per_eq"], "n_p_picks": s["min_p_picks_per_eq"],
                       "n_s_picks": s["min_s_picks_per_eq"]}}, 8)


def check_real() -> dict:
    return associator_vs_gamma("real", lambda s: {
        "reference_elevation_km": s["reference_elevation_km"], "velocity_layering": s["velocity_layering"],
        "region": {"latitude": s["latitude_bounds"], "longitude": s["longitude_bounds"], "depth_km": s["depth_bounds_km"]},
        "thresholds": {"np0": s["min_p_picks_per_eq"], "ns0": s["min_s_picks_per_eq"], "nps0": s["min_picks_per_eq"]}}, 16)


def check_nonlinloc(n_events: int = 50) -> dict:
    """A stored Ridgecrest baseline event relocated by NLLoc; the catalog locator with the Prague r2
    stage-04 settings and station delays reproduces 50 r2 events."""
    nl = tool("nonlinloc")
    source_root = RIDGECREST / "01_baseline/04_locate_nonlinloc"
    source_event = source_root / "events_raw/gamma_0000001"
    with tempfile.TemporaryDirectory(prefix="ridgecrest-nll-") as tmp:
        base = Path(tmp) / "run"
        event = base / "events_raw/gamma_0000001"
        event.mkdir(parents=True)
        (base / "grids").symlink_to(source_root / "grids", target_is_directory=True)
        for name in ("control.in", "input.obs"):
            shutil.copy2(source_event / name, event / name)
        output = nl.run(nl.BIN / "NLLoc", event / "control.in", event)
        assert list(event.glob("solution.*.loc.hyp")) and "1 events located" in output
    ref = prague_r2_events(n_events)
    with tempfile.TemporaryDirectory(prefix="prague-nll-") as tmp:
        tmp = Path(tmp)
        prague_arrivals(tmp, ref.index)
        s = prague_stations_model(tmp)
        st = pd.read_csv(PRAGUE / "03_associate_gamma/full/stations.csv")
        dl = pd.read_csv(PRAGUE / "04_locate_nonlinloc/full/station_delays.csv")
        dl.assign(station_id=dl.instrument_id.map(dict(zip(st.id, st.station_id))))[
            ["station_id", "phase", "delay_s", "n_picks"]].to_csv(tmp / "prague_delays.csv", index=False)
        cfg = {"reference_elevation_km": s["reference_elevation_km"], "projection_center": s["projection_center"],
               "region": {"longitude": s["longitude_bounds"], "latitude": s["latitude_bounds"],
                          "depth_km": s["depth_bounds_km"]},
               "velocity_layering": s["velocity_layering"], "grid_spacing_km": 0.25, "grid_depth_km": [-3.0, 35.0],
               "location_method": "GAU_ANALYTIC", "min_phases": 10, "min_s_phases": 3,
               "pick_error_s": {"P": 0.10, "S": 0.20}, "model_error_s": 0.30,
               "search": {"min_node_km": 0.1, "max_nodes": 50000, "samples": 2000}}
        e = nl.locate(tmp, "prague", tmp / "prague_arrivals.csv", tmp / "prague_stations.csv", tmp / "prague_model.txt",
                      cfg, tmp / "prague_delays.csv").loc[ref.index]
    dh = nl.epi_km(e.latitude, e.longitude, ref.latitude, ref.longitude)
    dz = (e.depth_km - ref.depth_km).abs()
    out = {"ridgecrest_replay": {"source_event": "gamma_0000001", "located_events": 1},
           "prague_r2": {"events": n_events, "located": int((e.status == "LOCATED").sum()),
                         "median_epi_km": round(float(np.median(dh)), 4), "max_epi_km": round(float(dh.max()), 4),
                         "median_abs_depth_km": round(float(dz.median()), 4), "max_abs_depth_km": round(float(dz.max()), 4)}}
    p = out["prague_r2"]
    assert p["located"] == n_events and p["median_epi_km"] < 0.1 and p["median_abs_depth_km"] < 0.2, out
    return out


def check_hypoinverse(n_events: int = 50) -> dict:
    """The 50 events of check_nonlinloc: HypoInverse vs NonLinLoc (r2 stage 04, with station delays)."""
    ref = prague_r2_events(n_events)
    with tempfile.TemporaryDirectory(prefix="prague-hypoinverse-") as tmp:
        tmp = Path(tmp)
        prague_arrivals(tmp, ref.index)
        prague_stations_model(tmp)
        # the Keranen model has small velocity inversions, which CRH models cannot represent
        out = tool("hypoinverse").run(tmp, "prague", tmp / "prague_arrivals.csv", tmp / "prague_stations.csv",
                                      tmp / "prague_model.txt", {"lvz_policy": "clip"})
        rr = json.loads((out / "run_result.json").read_text())
        e = pd.read_csv(out / "events.csv").set_index("event_id").loc[ref.index]
    dh = np.hypot((e.latitude - ref.latitude) * 111.195, (e.longitude - ref.longitude) * 111.195 *
                  np.cos(np.radians(ref.latitude)))
    dz = e.depth_km - ref.depth_km
    res = {"events": n_events, "located": int((e.status == "LOCATED").sum()), "lvz_clipped": rr["lvz_clipped"],
           "median_epi_vs_nll_km": round(float(dh.median()), 3), "p90_epi_vs_nll_km": round(float(dh.quantile(0.9)), 3),
           "median_abs_depth_vs_nll_km": round(float(dz.abs().median()), 3),
           "median_rms_s": round(float(e.rms_s.median()), 3)}
    assert res["located"] == n_events and res["median_epi_vs_nll_km"] < 0.5 and res["median_abs_depth_vs_nll_km"] < 1.0, res
    return res


def check_hypodd() -> dict:
    """Native hypoDD on the first two event pairs of the Ridgecrest stage-53 catalog dt.ct."""
    hypodd = tool("hypodd")
    source = RIDGECREST / "06_full_catalog/53_native_double_difference/hypodd_ct"
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
    event_lines = [line for line in (source / "event.dat").read_text().splitlines()
                   if int(line.split()[-1]) in event_ids]
    with tempfile.TemporaryDirectory(prefix="ridgecrest-hypodd-") as tmp:
        work = Path(tmp)
        (work / "event.dat").write_text("\n".join(event_lines) + "\n")
        shutil.copy2(source / "station.dat", work / "station.dat")
        (work / "dt.ct").write_text("".join("".join(block) for block in blocks))
        (work / "dt.cc").write_text("")
        shutil.copy2(source / "hypoDD.inp", work / "hypoDD.inp")
        result = subprocess.run([str(hypodd.BIN), "hypoDD.inp"], cwd=work, text=True,
                                stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=True)
        assert (work / "hypoDD.loc").is_file() and "# events =" in result.stdout
    return {"event_pairs": len(blocks), "events_parsed": len(event_lines), "mode": "CT",
            "note": "bounded replay of real differential-time input"}


def check_cross_correlation(n_events: int = 80) -> dict:
    """CC dt of well-picked Ridgecrest events must agree with their pick differential times.

    PhaseNet picks carry their own errors (tens of ms, occasionally more), so
    the criteria are robust: |median(cc - pick)| < 10 ms, MAD < 30 ms, the
    geometric mean of the two Theil-Sen slopes (cc on pick, pick on cc;
    errors on either axis attenuate one of them) within 5 % of 1, and fewer
    than 10 % of measurements more than 0.1 s from the pick difference."""
    from scipy.stats import theilslopes
    ccdt = tool("cross_correlation")
    ev = pd.read_csv(RIDGECREST / "06_full_catalog/52_full_catalog/working_catalog.csv", low_memory=False)
    ev["t"] = pd.to_datetime(ev.origin_time, utc=True, format="ISO8601")
    hour = ev[(ev.t >= "2019-07-05T10:00:00Z") & (ev.t < "2019-07-05T12:00:00Z")]
    assoc = pd.read_csv(RIDGECREST / "01_baseline/04_locate_nonlinloc/full/picks.csv")
    picks = pd.read_csv(RIDGECREST / "02_pick_phasenet/full/picks.csv", usecols=["pick_id", "station_id", "time_utc"])
    p = assoc[assoc.residual_s.abs() <= 0.2].merge(picks, on="pick_id")
    support = p.groupby("event_id").size()
    sel = hour[hour.event_id.isin(support[support >= 20].index)].nsmallest(n_events, "t")
    p = p[p.event_id.isin(sel.event_id)].drop_duplicates(["event_id", "station_id", "phase"])
    with tempfile.TemporaryDirectory(prefix="ridgecrest-ccdt-") as tmp:
        tmp = Path(tmp)
        sel[["event_id", "origin_time", "latitude", "longitude", "depth_below_sea_level_km"]].rename(
            columns={"origin_time": "origin_time_utc", "depth_below_sea_level_km": "depth_km"}).to_csv(
            tmp / "rc_events.csv", index=False)
        p[["event_id", "station_id", "phase", "time_utc"]].to_csv(tmp / "rc_arrivals.csv", index=False)
        # the 2019-07-05 day files of the stations involved, linked into a small tree
        wav = tmp / "rc_waves"
        wav.mkdir()
        for st in p.station_id.unique():
            for f in (RIDGECREST_WAVES / st).glob(f"{st}.*__20190705T000000Z__*.mseed"):
                (wav / f.name).symlink_to(f)
        out = tmp / "rc_run"
        subprocess.run([PY, "-I", str(ccdt.TOOL / "interface/run.py"), "--events", str(tmp / "rc_events.csv"),
                        "--arrivals", str(tmp / "rc_arrivals.csv"), "--waveforms", str(wav), "--output-dir",
                        str(out), "--workers", "8", "--quiet"], check=True, capture_output=True, text=True)
        m = pd.read_csv(out / "measurements.csv")
    m = m[m.status == "accepted"]
    o = dict(zip(sel.event_id, pd.to_datetime(sel.origin_time, utc=True, format="ISO8601")))
    pk = {(r.event_id, r.station_id, r.phase): pd.Timestamp(r.time_utc) for r in p.itertuples()}
    diff, dpk = [], []
    for r in m.itertuples():
        a, b = (r.event_id_1, r.station_id, r.phase), (r.event_id_2, r.station_id, r.phase)
        if a in pk and b in pk:
            d = ((pk[a] - o[r.event_id_1]) - (pk[b] - o[r.event_id_2])).total_seconds()
            dpk.append(d)
            diff.append(r.dt_s - d)
    diff, dpk = np.array(diff), np.array(dpk)
    dcc = dpk + diff
    slope = float(np.sqrt(theilslopes(dcc, dpk)[0] / theilslopes(dpk, dcc)[0])) if len(dpk) > 2 else float("nan")
    med, mad = float(np.median(diff)), float(np.median(np.abs(diff - np.median(diff))))
    outliers = float(np.mean(np.abs(diff) > 0.1)) if len(diff) else float("nan")
    res = {"events": int(len(sel)), "accepted": int(len(m)), "compared_with_picks": int(len(diff)),
           "median_cc_minus_pick_s": round(med, 4), "mad_s": round(mad, 4), "robust_slope": round(slope, 3),
           "fraction_beyond_0p1_s": round(outliers, 3)}
    assert len(diff) >= 200 and abs(med) < 0.01 and mad < 0.03 and abs(slope - 1) < 0.05 and outliers < 0.10, res
    return res


def check_growclust() -> dict:
    """ccdt + GrowClust on six Prague hours of r2 NLL events; inter-event distances against Cochran."""
    from pyproj import Proj
    gc = tool("growclust")
    t0, t1 = PRAGUE_HOURS
    e = pd.read_csv(PRAGUE / "04_locate_nonlinloc/full/events.csv")
    e["t"] = pd.to_datetime(e.origin_time, utc=True, format="ISO8601")
    e = e[(e.status == "LOCATED") & (e.t >= t0) & (e.t < t1)]
    ev = pd.DataFrame({"event_id": e.event_id, "origin_time_utc": e.origin_time, "latitude": e.latitude,
                       "longitude": e.longitude, "depth_km": e.depth_km})
    with tempfile.TemporaryDirectory(prefix="prague-growclust-") as tmp:
        tmp = Path(tmp)
        ev.to_csv(tmp / "prague_events.csv", index=False)
        a = pd.read_csv(PRAGUE / "03_associate_gamma/full/picks.csv", keep_default_na=False)
        a[a.event_id.isin(ev.event_id)][["event_id", "station_id", "phase", "time_utc"]] \
            .to_csv(tmp / "prague_arrivals.csv", index=False)
        wav = tmp / "prague_waveforms"
        wav.mkdir()
        for f in PRAGUE_WAVES.rglob("*__20111111T000000Z__*.mseed"):
            (wav / f.name).symlink_to(f)
        # the near-source ZQ stations record on DH/CN channels, which ccdt's default families leave out
        (tmp / "ccdt.json").write_text(json.dumps({"channels": {"families": ["HH", "EH", "BH", "HN", "EN", "DH", "CN"]}}))
        subprocess.run([PY, "-I", str(gc.CCDT), "--events", str(tmp / "prague_events.csv"), "--arrivals",
                        str(tmp / "prague_arrivals.csv"), "--waveforms", str(wav), "--output-dir", str(tmp / "prague_cc"),
                        "--config", str(tmp / "ccdt.json"), "--workers", "16", "--quiet"], check=True, capture_output=True)
        st = pd.read_csv(PRAGUE / "03_associate_gamma/full/stations.csv")
        st[["station_id", "latitude", "longitude"]].to_csv(tmp / "prague_stations.csv", index=False)
        inputs = json.loads((PRAGUE / "03_associate_gamma/full/inputs.json").read_text())
        (tmp / "prague_model.txt").write_text("".join(f"{r['top_of_layer_km']} {r['vp_km_s']} {r['vs_km_s']}\n"
                                                     for r in inputs["model_source"]["rows"]))
        out = gc.run(tmp, "prague", tmp / "prague_events.csv", tmp / "prague_stations.csv", tmp / "prague_cc",
                     tmp / "prague_model.txt", {"table": {"distance_max_km": 150.0}, "ngoodmin": 4})
        r = pd.read_csv(out / "relocated.csv").set_index("event_id")
        cc = json.loads((tmp / "prague_cc/run_result.json").read_text())
    spec = importlib.util.spec_from_file_location("s60", PRAGUE_TASK / "expert/01_pipeline/60_match_locate.py")
    s60 = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(s60)
    coch = s60.load_references([s60.utc("2011-11-11")])["cochran"]
    nll = ev.set_index("event_id")
    rows = [{"time": s60.utc(t), "latitude": la, "longitude": lo, "id": i}
            for i, t, la, lo in zip(nll.index, nll.origin_time_utc, nll.latitude, nll.longitude)]
    pairs = s60.match(rows, coch, 2.0, 5.0)
    ours = [rows[i]["id"] for i, _ in pairs]
    ref = pd.DataFrame([coch[j] for _, j in pairs])
    proj = Proj(proj="aeqd", lon_0=-96.7725, lat_0=35.5215, datum="WGS84", units="km")

    def xy(lat, lon):
        return np.c_[proj(np.asarray(lon), np.asarray(lat))]
    R = xy(ref.latitude, ref.longitude)
    dr = np.linalg.norm(R[:, None] - R[None], axis=2)
    cid = r.loc[ours, "cluster_id"].to_numpy()
    # pairs (< 3 km apart in Cochran) inside one relocated GrowClust cluster: clusters move as a whole
    same = np.triu(dr < 3.0, 1) & (cid[:, None] == cid[None]) & r.loc[ours, "relocated"].to_numpy()[:, None]
    err = {}
    for lab, df in (("nll", nll), ("growclust", r)):
        X = xy(df.loc[ours, "latitude"], df.loc[ours, "longitude"])
        err[lab] = round(float(np.median(np.abs(np.linalg.norm(X[:, None] - X[None], axis=2) - dr)[same])), 3)
    res = {"events": len(ev), "relocated": int(r.relocated.sum()), "ccdt_pairs": cc.get("pairs_with_dt"),
           "ccdt_dt_lines": cc.get("dt_lines"), "matched_to_cochran": len(ours), "same_cluster_pairs": int(same.sum()),
           "median_interevent_distance_error_km": err}
    assert res["relocated"] >= 0.3 * len(ev) and res["same_cluster_pairs"] >= 100, res
    assert err["growclust"] < 0.7 * err["nll"], res
    return res


CHECKS = {"phasenet": check_phasenet, "gamma": check_gamma, "pyocto": check_pyocto, "real": check_real,
          "nonlinloc": check_nonlinloc, "hypoinverse": check_hypoinverse, "hypodd": check_hypodd,
          "cross_correlation": check_cross_correlation, "growclust": check_growclust}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--tool", required=True, choices=sorted(CHECKS))
    name = parser.parse_args().tool
    os.environ.setdefault("VALIDATION_LOG_DIR", str(Path(__file__).resolve().parent / "outputs"))
    print(json.dumps({"status": "pass", "tool": name, "case": CHECKS[name]()}, indent=2))


if __name__ == "__main__":
    main()
