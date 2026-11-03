"""Multi-event NonLinLoc catalog location (``interface/locate.py``).

Generalised from per-event NonLinLoc runs: one local aeqd frame, P and S
travel-time grids computed once per station (``GRID2D``), one ``NLLoc`` run per
event (arrival group) in a thread pool, fixed station delays (``LOCDELAY``)
optional. Depths are km below ``reference_elevation_km``; station z is that
reference minus the station elevation.
"""
from __future__ import annotations

import copy
import math
import os
import re
import shutil
import subprocess
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any, Dict, List, Mapping, Tuple

import numpy as np
import pandas as pd
from pyproj import Proj

LOCATION_METHODS = ("EDT_OT_WT", "EDT", "GAU_ANALYTIC")
DEFAULT_CONFIG: Dict[str, Any] = {
    "reference_elevation_km": 0.0,
    "projection_center": None,          # [lon, lat]; default: station centroid
    "region": None,                     # {latitude: [a, b], longitude: [a, b], depth_km: [top, bottom]}
    "region_pad_km": 20.0,              # default region: station box + pad, depth [highest station, 30]
    "velocity_layering": "step",        # rows are constant layers (step) or nodes of a linear profile
    "grid_spacing_km": 0.5,             # travel-time grid spacing
    "grid_depth_km": [-3.0, 40.0],      # travel-time grid depth range
    "location_method": "EDT_OT_WT",
    "min_phases": 4,
    "min_s_phases": -1,
    "pick_error_s": {"P": 0.10, "S": 0.20},
    "model_error_s": 0.10,              # LOCGAU sigma
    "search": {"min_node_km": 0.1, "max_nodes": 50000, "samples": 2000},
    "locgrid_counts": [121, 121, 101],
    "per_event_timeout_s": 180,
    "keep_raw": False,                  # keep per-event NLLoc files (failures are always kept)
}


def merge_config(user: Mapping[str, Any] | None) -> Dict[str, Any]:
    cfg = copy.deepcopy(DEFAULT_CONFIG)
    for k, v in (user or {}).items():
        if k not in cfg:
            raise ValueError(f"unknown config key: {k}")
        cfg[k] = {**cfg[k], **v} if isinstance(cfg[k], dict) and isinstance(v, dict) else v
    if cfg["location_method"] not in LOCATION_METHODS:
        raise ValueError(f"location_method must be one of {LOCATION_METHODS}")
    if cfg["velocity_layering"] not in ("step", "linear"):
        raise ValueError("velocity_layering must be step or linear")
    return cfg


def read_velocity(path: Path) -> List[Tuple[float, float, float]]:
    rows = []
    for line in Path(path).read_text().splitlines():
        line = line.split("#", 1)[0].strip()
        if line:
            z, vp, vs = map(float, line.split()[:3])
            rows.append((z, vp, vs))
    if not rows or any(b[0] <= a[0] for a, b in zip(rows, rows[1:])):
        raise ValueError("velocity model: need rows of increasing depth_km vp_km_s vs_km_s")
    return rows


def layer_lines(rows, layering: str, grid_top: float) -> List[str]:
    out = []
    if grid_top < rows[0][0]:
        out.append(f"LAYER {grid_top} {rows[0][1]:.10f} 0 {rows[0][2]:.10f} 0 2.7 0")
    for i, (z, vp, vs) in enumerate(rows):
        gp = gs = 0.0
        if layering == "linear" and i + 1 < len(rows):
            dz = rows[i + 1][0] - z
            gp, gs = (rows[i + 1][1] - vp) / dz, (rows[i + 1][2] - vs) / dz
        out.append(f"LAYER {z} {vp:.10f} {gp:.10f} {vs:.10f} {gs:.10f} 2.7 0")
    return out


def _execute(binary: Path, control: Path, cwd: Path, log: Path, timeout: float) -> None:
    with log.open("w") as f:
        proc = subprocess.run([str(binary), os.path.relpath(control, cwd)], cwd=cwd, stdout=f,
                              stderr=subprocess.STDOUT, timeout=timeout)
    if proc.returncode:
        raise RuntimeError(f"{binary.name} returned {proc.returncode}; see {log}")


def _tokens(body: str, prefix: str) -> List[str]:
    return next(x for x in body.splitlines() if x.startswith(prefix + " ")).split()[1:]


def _pairs(body: str, prefix: str) -> Dict[str, str]:
    a = _tokens(body, prefix)
    return dict(zip(a[::2], a[1::2]))


class CatalogLocator:
    def __init__(self, stations: pd.DataFrame, velocity_rows, cfg: Dict[str, Any], bin_dir: Path, out: Path):
        self.cfg, self.bin, self.out = cfg, Path(bin_dir), Path(out)
        st = stations.copy()
        if not st.station_id.is_unique:
            raise ValueError("station_id must be unique")
        lon0, lat0 = cfg["projection_center"] or (float(st.longitude.mean()), float(st.latitude.mean()))
        self.proj = Proj(proj="aeqd", lon_0=lon0, lat_0=lat0, datum="WGS84", units="km")
        self.center = [float(lon0), float(lat0)]
        st["x"], st["y"] = self.proj(st.longitude.to_numpy(), st.latitude.to_numpy())
        st["z"] = cfg["reference_elevation_km"] - st.elevation_m / 1000.0
        st["alias"] = [f"S{i:04d}" for i in range(1, len(st) + 1)]
        self.st = st.set_index("station_id")
        self.station_of = dict(zip(st.alias, st.station_id))
        reg = cfg["region"]
        if reg is None:
            pad = cfg["region_pad_km"]
            xb, yb = (st.x.min() - pad, st.x.max() + pad), (st.y.min() - pad, st.y.max() + pad)
            # search from the land surface: stations above the reference elevation have z < 0, and a search
            # that starts at the reference elevation pins shallow events to its top
            zb = (min(0.0, math.floor(float(st.z.min()) / cfg["grid_spacing_km"]) * cfg["grid_spacing_km"]), 30.0)
        else:
            corners = np.array([self.proj(lo, la) for lo in reg["longitude"] for la in reg["latitude"]])
            xb, yb = (corners[:, 0].min(), corners[:, 0].max()), (corners[:, 1].min(), corners[:, 1].max())
            zb = tuple(reg["depth_km"])
        self.bounds = (xb, yb, zb)
        g0, g1 = cfg["grid_depth_km"]
        if not (g0 <= zb[0] and zb[1] <= g1 and g0 <= st.z.min()):
            raise ValueError("grid_depth_km must contain the region depths and the stations")
        corners = np.array([(x, y) for x in xb for y in yb])
        self.radius = float(np.max(np.hypot(corners[:, None, 0] - st.x.to_numpy()[None],
                                            corners[:, None, 1] - st.y.to_numpy()[None]))) + 10.0
        self.layers = layer_lines(velocity_rows, cfg["velocity_layering"], g0)
        self.sources = [f"GTSRCE {r.alias} XYZ {r.x:.8f} {r.y:.8f} {r.z:.8f} 0" for r in st.itertuples()]

    # ------------------------------------------------------------------ grids
    def build_grids(self) -> None:
        cfg, grids = self.cfg, self.out / "grids"
        grids.mkdir(parents=True, exist_ok=True)
        h = cfg["grid_spacing_km"]
        g0, g1 = cfg["grid_depth_km"]
        base = ("CONTROL 1 54321\nTRANS NONE\nVGOUT model\n"
                f"VGGRID 2 {int(math.ceil(self.radius / h)) + 1} {int(round((g1 - g0) / h)) + 1} 0 0 {g0} {h} {h} {h} SLOW_LEN\n"
                + "\n".join(self.layers) + "\n")
        for phase in ("P", "S"):
            control = grids / f"{phase}.in"
            control.write_text(base + f"VGTYPE {phase}\nGTFILES model time {phase}\nGTMODE GRID2D ANGLES_NO\n"
                               "GT_PLFD 1.e-3 0\n" + "\n".join(self.sources) + "\n")
            _execute(self.bin / "Vel2Grid", control, grids, grids / f"{phase}_velocity.log", 600)
            _execute(self.bin / "Grid2Time", control, grids, grids / f"{phase}_travel.log", 600)
            if len(list(grids.glob(f"time.{phase}.*.time.buf"))) != len(self.st):
                raise RuntimeError(f"Grid2Time did not write one {phase} grid per station")

    def control_text(self, delays: pd.DataFrame | None) -> str:
        cfg = self.cfg
        (x0, x1), (y0, y1), (z0, z1) = self.bounds
        nx, ny, nz = cfg["locgrid_counts"]
        # NLL 7 octree uses (N-1)*spacing in x/y but N*spacing in z
        dx, dy, dz = (x1 - x0) / (nx - 1), (y1 - y0) / (ny - 1), (z1 - z0) / nz
        s = cfg["search"]
        text = ("CONTROL 1 54321\nTRANS NONE\n" + "\n".join(self.sources) + "\nLOCSIG seismotools nonlinloc locate\n"
                f"LOCGRID {nx} {ny} {nz} {x0} {y0} {z0} {dx} {dy} {dz} PROB_DENSITY SAVE\n"
                f"LOCSEARCH OCT 10 10 5 {s['min_node_km']} {s['max_nodes']} {s['samples']} 0 0\n"
                f"LOCMETH {cfg['location_method']} 9999 {cfg['min_phases']} -1 {cfg['min_s_phases']} -1 100 -1 1\n"
                "LOCHYPOUT SAVE_NLLOC_ALL\n"
                f"LOCGAU {cfg['model_error_s']} 0\nLOCQUAL2ERR .1 .2 .5 1 999\nLOCPHASEID P P\nLOCPHASEID S S\n"
                "LOCANGLES ANGLES_NO 5\n")
        if delays is not None and len(delays):
            for r in delays.itertuples():
                if r.station_id not in self.st.index:
                    raise ValueError(f"station delay for unknown station {r.station_id}")
                n = int(getattr(r, "n_picks", 1) or 1)
                text += f"LOCDELAY {self.st.at[r.station_id, 'alias']} {r.phase} {n} {float(r.delay_s):.4f}\n"
        return text

    # ----------------------------------------------------------------- events
    def locate_one(self, event_id: str, arr: pd.DataFrame, common: str) -> Tuple[dict, List[dict]]:
        cfg = self.cfg
        folder = self.out / "events_raw" / re.sub(r"[^A-Za-z0-9_.-]", "_", str(event_id))
        folder.mkdir(parents=True, exist_ok=True)
        lines = []
        for r in arr.itertuples():
            t = r.t
            err = r.uncertainty_s if "uncertainty_s" in arr and pd.notna(r.uncertainty_s) else cfg["pick_error_s"][r.phase]
            lines.append(f"{self.st.at[r.station_id, 'alias']:6s} ? ? ? {r.phase} ? {t:%Y%m%d} {t:%H%M} "
                         f"{t.second + t.microsecond / 1e6:.4f} GAU {err:.4f} -1 -1 -1")
        # explicit terminators avoid the C reader's char/EOF issue
        (folder / "input.obs").write_text("\n".join(lines) + "\n!END_EVENT\n!END_FILE\n")
        (folder / "control.in").write_text(common + "\nLOCFILES input.obs NLLOC_OBS ../../grids/time solution\n")
        _execute(self.bin / "NLLoc", folder / "control.in", folder, folder / "run.log", cfg["per_event_timeout_s"])
        hyps = [p for p in folder.glob("solution.*.grid0.loc.hyp") if ".sum." not in p.name]
        if len(hyps) != 1:
            raise RuntimeError(f"expected one .hyp, found {len(hyps)}; see {folder / 'run.log'}")
        row, links = self.parse_hyp(hyps[0], event_id, arr)
        if not cfg["keep_raw"]:          # cleanup must not fail a located event (network file systems)
            shutil.rmtree(folder, ignore_errors=True)
        return row, links

    def parse_hyp(self, path: Path, event_id: str, arr: pd.DataFrame) -> Tuple[dict, List[dict]]:
        body = path.read_text()
        status = re.match(r'NLLOC\s+"[^"]*"\s+"([^"]+)"', body).group(1)
        h, q, s = _pairs(body, "HYPOCENTER"), _pairs(body, "QUALITY"), _pairs(body, "STATISTICS")
        geo = _tokens(body, "GEOGRAPHIC")
        year, month, day, hour, minute = map(int, geo[1:6])
        origin = pd.Timestamp(year=year, month=month, day=day, hour=hour, minute=minute, tz="UTC") + \
            pd.Timedelta(seconds=float(geo[6]))
        x, y, z = (float(h[k]) for k in ("x", "y", "z"))
        lon, lat = self.proj(x, y, inverse=True)
        cxx, cxy, cyy, czz = (float(s[k]) for k in ("CovXX", "XY", "YY", "ZZ"))
        erh = math.sqrt(max(np.linalg.eigvalsh(np.array([[cxx, cxy], [cxy, cyy]])).max(), 0.0))
        key = {(self.st.at[r.station_id, "alias"], r.phase): r for r in arr.itertuples()}
        links, inside = [], False
        for line in body.splitlines():
            if line.startswith("PHASE "):
                inside = True
                continue
            if line.startswith("END_PHASE"):
                inside = False
            if not inside or " > " not in line:
                continue
            a, b = (part.split() for part in line.split(" > "))
            r = key[(a[0], a[4])]
            links.append({"event_id": event_id, "pick_id": r.pick_id, "station_id": r.station_id, "phase": r.phase,
                          "residual_s": float(b[1]), "weight": float(b[2]), "predicted_travel_time_s": float(b[0])})
        row = {"event_id": event_id, "status": status, "origin_time_utc": origin.strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
               "latitude": lat, "longitude": lon, "depth_km": z, "rms_s": float(q["RMS"]), "n_phases": int(q["Nphs"]),
               "n_stations": int(arr.station_id.nunique()), "gap_deg": float(q["Gap"]), "erh_km": erh,
               "erz_km": math.sqrt(max(czz, 0.0)), "x_km": x, "y_km": y,
               "expect_x_km": float(s["ExpectX"]), "expect_y_km": float(s["Y"]), "expect_depth_km": float(s["Z"]),
               "sigma_x_km": math.sqrt(max(cxx, 0.0)), "sigma_y_km": math.sqrt(max(cyy, 0.0)),
               "sigma_depth_km": math.sqrt(max(czz, 0.0))}
        return row, links


def locate_catalog(arrivals: pd.DataFrame, stations: pd.DataFrame, velocity_path: Path, out: Path,
                   bin_dir: Path, config: Mapping[str, Any] | None = None, delays: pd.DataFrame | None = None,
                   workers: int = 8, log=print) -> Dict[str, Any]:
    cfg = merge_config(config)
    arr = arrivals.copy()
    missing = {"event_id", "pick_id", "station_id", "phase", "time_utc"} - set(arr.columns)
    if missing:
        raise ValueError(f"arrivals: missing columns {sorted(missing)}")
    if not set(arr.phase) <= {"P", "S"}:
        raise ValueError("arrivals: phase must be P or S")
    if arr.duplicated(["event_id", "station_id", "phase"]).any():
        raise ValueError("arrivals: duplicate (event_id, station_id, phase)")
    unknown = set(arr.station_id) - set(stations.station_id)
    if unknown:
        raise ValueError(f"arrivals: stations not in the station table: {sorted(unknown)[:5]}")
    arr["t"] = pd.to_datetime(arr.time_utc, utc=True, format="ISO8601")
    loc = CatalogLocator(stations, read_velocity(velocity_path), cfg, bin_dir, out)
    t0 = time.monotonic()
    loc.build_grids()
    common = loc.control_text(delays)
    groups = {k: g for k, g in arr.groupby("event_id", sort=False)}
    rows, links, failed = [], [], []
    with ThreadPoolExecutor(max_workers=max(1, workers)) as pool:
        futures = {pool.submit(loc.locate_one, k, g, common): k for k, g in groups.items()}
        for i, f in enumerate(as_completed(futures), 1):
            try:
                row, ph = f.result()
                rows.append(row)
                links += ph
            except Exception as exc:  # recorded; the event folder is kept
                failed.append({"event_id": futures[f], "error": repr(exc)})
            if i % 500 == 0 or i == len(futures):
                log(f"[{i}/{len(futures)}] located {len(rows)}, failed {len(failed)}, {time.monotonic() - t0:.0f} s")
    ev = pd.DataFrame(rows, columns=["event_id", "status", "origin_time_utc", "latitude", "longitude", "depth_km",
                                     "rms_s", "n_phases", "n_stations", "gap_deg", "erh_km", "erz_km", "x_km",
                                     "y_km", "expect_x_km", "expect_y_km", "expect_depth_km", "sigma_x_km",
                                     "sigma_y_km", "sigma_depth_km"]).sort_values("origin_time_utc")
    ev.to_csv(out / "events.csv", index=False)
    pd.DataFrame(links, columns=["event_id", "pick_id", "station_id", "phase", "residual_s", "weight",
                                 "predicted_travel_time_s"]).to_csv(out / "arrivals.csv", index=False)
    pd.DataFrame(failed, columns=["event_id", "error"]).to_csv(out / "failures.csv", index=False)
    if not cfg["keep_raw"] and not failed and (out / "events_raw").exists():
        shutil.rmtree(out / "events_raw", ignore_errors=True)
    (x0, x1), (y0, y1), (z0, z1) = loc.bounds
    return {"config": cfg, "events_in": len(groups), "located": int((ev.status == "LOCATED").sum()),
            "parsed": len(ev), "failed": len(failed), "seconds": round(time.monotonic() - t0, 1),
            "projection_center": loc.center,
            "search_box_km": {"x": [x0, x1], "y": [y0, y1], "depth": [z0, z1]}, "travel_time_radius_km": loc.radius}
