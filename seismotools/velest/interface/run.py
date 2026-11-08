#!/usr/bin/env python3
"""Minimum 1-D velocity model with VELEST (simultaneous mode): hypocentres, layer velocities and station corrections.

Inputs use the conventions of the other locators of seismotools:

- ``--arrivals`` CSV: ``event_id, station_id, phase (P/S), time_utc`` (optional ``weight`` 0-4, 0 = best);
- ``--events`` CSV: starting hypocentres ``event_id, origin_time_utc, latitude, longitude, depth_km`` (km below sea level);
- ``--stations`` CSV: ``station_id, latitude, longitude, elevation_m``;
- ``--model`` text: one row per layer, ``top_km vp_km_s [vs_km_s]`` (top in km below sea level, negative above it);
  without a Vs column, ``--vpvs`` gives Vs.

The events used are selected by data quality (``--min-p``, ``--min-s``, ``--max-gap``), best first, up to
``--max-events`` (VELEST's limit is 658). The model's top is raised above the highest station if needed (VELEST
needs every station inside its first layer). Station codes are mapped to four-character aliases internally.

Outputs in ``--output-dir``: ``model_final.txt`` (``top_km vp_km_s vs_km_s``), ``station_corrections.csv``
(``station_id, p_correction_s, s_correction_s``; the reference station keeps a P correction of zero),
``events_final.csv`` (relocated hypocentres), ``summary.json`` (selection, RMS per iteration, reference station,
the starting and final models) and the native files in ``velest/``.

A single run is not a minimum 1-D model: run several starting models and check that the results converge and
that perturbed hypocentres return (``interface/stability.py``).
"""
from __future__ import annotations

import argparse
import json
import math
import re
import shutil
import subprocess
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
BINARY = HERE.parent / "runtime" / "bin" / "velest"
MAX_EVENTS = 650  # VELEST: IEQ = 658
MAX_STATIONS = 640  # VELEST: IST = 650
MAX_OBS = 180  # VELEST: MAXOBSPEREVENT


def read_model(path: Path, vpvs: float | None) -> list[tuple[float, float, float]]:
    rows = []
    for line in Path(path).read_text().splitlines():
        parts = line.split("#")[0].split()
        if len(parts) < 2:
            continue
        z, vp = float(parts[0]), float(parts[1])
        if len(parts) > 2 and parts[2].lower() != "nan":
            vs = float(parts[2])
        elif vpvs:
            vs = vp / vpvs
        else:
            raise SystemExit(f"{path}: no Vs column and no --vpvs")
        rows.append((z, vp, vs))
    rows.sort()
    return rows


def azimuth_gap(lat: float, lon: float, slat: np.ndarray, slon: np.ndarray) -> float:
    az = np.sort(np.degrees(np.arctan2((slon - lon) * np.cos(np.radians(lat)), slat - lat)) % 360)
    if len(az) < 2:
        return 360.0
    return float(max(np.diff(az).max(), 360 - az[-1] + az[0]))


def select_events(arr: pd.DataFrame, ev: pd.DataFrame, st: pd.DataFrame, a) -> pd.DataFrame:
    counts = arr.groupby(["event_id", "phase"]).size().unstack(fill_value=0)
    ev = ev.join(counts, on="event_id").fillna({"P": 0, "S": 0})
    ev = ev[(ev.P >= a.min_p) & (ev.S >= a.min_s)].copy()
    sxy = st.set_index("station_id")[["latitude", "longitude"]]
    gaps = []
    for _, e in ev.iterrows():
        s = sxy.loc[sxy.index.intersection(arr.station_id[(arr.event_id == e.event_id) & (arr.phase == "P")])]
        gaps.append(azimuth_gap(e.latitude, e.longitude, s.latitude.to_numpy(), s.longitude.to_numpy()))
    ev["gap_deg"] = gaps
    ev = ev[ev.gap_deg <= a.max_gap]
    ev["score"] = ev.P + 0.5 * ev.S - ev.gap_deg / 60.0
    return ev.sort_values("score", ascending=False).head(min(a.max_events, MAX_EVENTS))


def aliases(stations: list[str]) -> dict[str, str]:
    letters = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    out = {}
    for i, s in enumerate(sorted(stations)):
        out[s] = letters[i // 260 % 26] + letters[i // 10 % 26] + f"{i % 10}" + "X"  # four characters, unique
    return out


def lat_str(v: float) -> str:
    return f"{abs(v):7.4f}{'N' if v >= 0 else 'S'}"


def lon_str(v: float) -> str:  # VELEST: longitude West positive; written as absolute value with E/W
    return f"{abs(v):8.4f}{'E' if v >= 0 else 'W'}"


def write_inputs(d: Path, ev: pd.DataFrame, arr: pd.DataFrame, st: pd.DataFrame, model, ref: str, alias: dict, a):
    # station list: the reference station gets the highest ICC number (VELEST keeps its P correction fixed)
    order = [s for s in st.station_id if s != ref] + [ref]
    lines = ["(a4,f7.4,a1,1x,f8.4,a1,1x,i4,1x,i1,1x,i3,1x,f5.2,2x,f5.2)"]
    srow = st.set_index("station_id")
    for icc, s in enumerate(order, start=1):
        r = srow.loc[s]
        lines.append(f"{alias[s]}{lat_str(r.latitude)} {lon_str(r.longitude)} {int(round(r.elevation_m)):4d} 1 {icc:3d}  0.00   0.00")
    lines.append("")
    (d / "stations.sta").write_text("\n".join(lines) + "\n")
    # model: P block then S block; vdamp 1.0 everywhere
    def block(title, idx):
        rows = [f" {len(model):2d}        vel,depth,vdamp,phase (f5.2,5x,f7.2,2x,f7.3,3x,a1)"]
        for i, m in enumerate(model):
            rows.append(f"{m[idx]:5.2f}     {m[0]:7.2f}  {1.0:7.3f}" + (f"            {title}" if i == 0 else ""))
        return rows
    (d / "model.mod").write_text("\n".join([" starting model (seismotools/velest)"] + block("P-VELOCITY MODEL", 1) + block("S-VELOCITY MODEL", 2)) + "\n")
    # earthquakes in CNV: header (3i2,1x,2i2,1x,f5.2,1x,f7.4,a1,1x,f8.4,a1,1x,f7.2,2x,f5.2), phases 6(a4,a1,i1,f6.2)
    out = []
    for _, e in ev.iterrows():
        t0 = pd.Timestamp(e.origin_time_utc)
        sec = t0.second + t0.microsecond / 1e6
        out.append(f"{t0.year % 100:02d}{t0.month:02d}{t0.day:02d} {t0.hour:02d}{t0.minute:02d} {sec:5.2f} "
                   f"{lat_str(e.latitude)} {lon_str(e.longitude)} {e.depth_km:7.2f}  {0.0:5.2f}")
        p = arr[arr.event_id == e.event_id].copy()
        p["tt"] = (p.time - t0).dt.total_seconds()
        p = p[(p.tt > 0) & (p.tt < 999.0)].sort_values("tt").head(MAX_OBS)
        cells = [f"{alias[r.station_id]}{r.phase}{int(r.weight)}{r.tt:6.2f}" for r in p.itertuples()]
        for i in range(0, len(cells), 6):
            out.append("".join(cells[i:i + 6]))
        out.append("")
    out.append("9999")
    (d / "events.cnv").write_text("\n".join(out) + "\n")
    olat, olon = float(ev.latitude.mean()), float(ev.longitude.mean())
    zmin = -float(st.elevation_m.max()) / 1000.0
    cmn = f"""******* CONTROL-FILE FOR PROGRAM  V E L E S T  (28-SEPT1993) *******
*** written by seismotools/velest/interface/run.py
*** next line contains a title (printed on output):
seismotools velest run
***  olat       olon   icoordsystem      zshift   itrial ztrial    ised
 {olat:8.4f}   {-olon:9.4f}      0            0.000      0     0.00       0
*** neqs   nshot   rotate
   {len(ev):4d}      0      0.0
*** isingle   iresolcalc
       0          0
*** dmax    itopo    zmin     veladj    zadj   lowveloclay
   {a.dmax:6.1f}     0   {zmin:6.2f}       {a.veladj:4.2f}    {a.zadj:4.2f}       {int(a.low_velocity)}
*** nsp    swtfac   vpvs       nmod
     {2 if a.use_s else 1}      {a.swtfac:4.2f}    {a.vpvs_ratio:5.3f}        1
***   othet   xythet    zthet    vthet   stathet
      {a.damping[0]:4.2f}    {a.damping[1]:4.2f}      {a.damping[2]:4.2f}     {a.damping[3]:4.2f}     {a.damping[4]:4.2f}
*** nsinv   nshcor   nshfix     iuseelev    iusestacorr
       {0 if a.no_station_corrections else 1}       0       0           1            0
*** iturbo    icnvout   istaout   ismpout
       1         1         2         0
*** irayout   idrvout   ialeout   idspout   irflout   irfrout   iresout
       0         0         0         0         0         0         0
*** delmin   ittmax   invertratio
    0.010      {a.iterations:02d}          {a.invert_ratio}
*** Modelfile:
model.mod
*** Stationfile:
stations.sta
*** Seismofile:

*** File with region names:

*** File with region coordinates:

*** File #1 with topo data:

*** File #2 with topo data:

*** DATA INPUT files:
*** File with Earthquake data:
events.cnv
*** File with Shot data:

*** OUTPUT files:
*** Main print output file:
velest.out
*** File with single event locations:

*** File with final hypocenters in *.cnv format:
final.cnv
*** File with new station corrections:
final.sta
*** File with summary cards (e.g. for plotting):

*** File with raypoints:

*** File with derivatives:

*** File with ALEs:

*** File with Dirichlet spreads:

*** File with reflection points:

*** File with refraction points:

*** File with residuals:

******* END OF THE CONTROL-FILE FOR PROGRAM  V E L E S T  *******
"""
    (d / "velest.cmn").write_text(cmn)


def parse_model(text: str) -> list[list[tuple[float, float]]]:
    """Last P and S model blocks of the main output: rows (velocity, top depth)."""
    blocks = re.findall(r"Velocity model\s+\d+\n((?:\s+[-\d.]+\s+[-\d.]+\s+[-\d.]+.*\n)+)", text)
    parsed = [[(float(r.split()[0]), float(r.split()[2])) for r in b.strip("\n").split("\n")] for b in blocks]
    return parsed


def parse_cnv(path: Path) -> pd.DataFrame:
    rows = []
    for line in path.read_text().splitlines():
        m = re.match(r"(\d{2})(\d{2})(\d{2}) (\d{2})([ \d]\d) ([ \d]\d\.\d\d) ([ \d]+\.\d+)([NS]) ([ \d]+\.\d+)([EW]) +([-\d.]+)", line)
        if not m:
            continue
        yy, mo, dd, hh, mi, ss, lat, ns, lon, ew, z = m.groups()
        sec = float(ss)
        t = pd.Timestamp(year=2000 + int(yy) if int(yy) < 70 else 1900 + int(yy), month=int(mo), day=int(dd),
                         hour=int(hh), minute=int(mi.strip() or 0)) + pd.Timedelta(seconds=sec)
        rows.append({"origin_time_utc": t.strftime("%Y-%m-%dT%H:%M:%S.%fZ"), "latitude": float(lat) * (1 if ns == "N" else -1),
                     "longitude": float(lon) * (1 if ew == "E" else -1), "depth_km": float(z)})
    return pd.DataFrame(rows)


def parse_sta(path: Path, back: dict) -> pd.DataFrame:
    rows = []
    for line in path.read_text().splitlines()[1:]:
        if len(line) < 46 or line[:4] not in back:
            continue
        rows.append({"station_id": back[line[:4]], "p_correction_s": float(line[34:39]), "s_correction_s": float(line[41:46])})
    return pd.DataFrame(rows)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--arrivals", type=Path, required=True)
    ap.add_argument("--events", type=Path, required=True)
    ap.add_argument("--stations", type=Path, required=True)
    ap.add_argument("--model", type=Path, required=True)
    ap.add_argument("--vpvs", type=float, help="Vs = Vp / vpvs when the model has no Vs column")
    ap.add_argument("--output-dir", type=Path, required=True)
    ap.add_argument("--max-events", type=int, default=500)
    ap.add_argument("--min-p", type=int, default=8)
    ap.add_argument("--min-s", type=int, default=2)
    ap.add_argument("--max-gap", type=float, default=180.0)
    ap.add_argument("--use-s", action="store_true", help="invert P and S (nsp 2); default P only")
    ap.add_argument("--swtfac", type=float, default=0.5, help="weight of S relative to P")
    ap.add_argument("--vpvs-ratio", type=float, default=1.73, help="VELEST vpvs parameter")
    ap.add_argument("--iterations", type=int, default=9)
    ap.add_argument("--invert-ratio", type=int, default=1)
    ap.add_argument("--damping", type=float, nargs=5, default=[0.01, 0.01, 0.01, 1.0, 0.1],
                    metavar=("OTHET", "XYTHET", "ZTHET", "VTHET", "STATHET"))
    ap.add_argument("--no-station-corrections", action="store_true")
    ap.add_argument("--veladj", type=float, default=0.2)
    ap.add_argument("--zadj", type=float, default=5.0)
    ap.add_argument("--dmax", type=float, default=200.0)
    ap.add_argument("--low-velocity", action="store_true", help="allow low-velocity layers")
    ap.add_argument("--reference-station", help="default: the station with the most P picks among the most central third")
    ap.add_argument("--timeout", type=int, default=3600)
    a = ap.parse_args()
    if not BINARY.is_file():
        raise SystemExit(f"{BINARY} missing: python seismotools/support/build_native.py --tool velest")
    arr = pd.read_csv(a.arrivals, dtype={"event_id": str, "station_id": str})
    arr = arr[arr.phase.isin(["P", "S"] if a.use_s else ["P"])].copy()
    arr["time"] = pd.to_datetime(arr.time_utc, utc=True, format="mixed").dt.tz_localize(None)
    arr["weight"] = (pd.to_numeric(arr["weight"], errors="coerce").fillna(0).clip(0, 4).astype(int)
                     if "weight" in arr else 0)
    ev = pd.read_csv(a.events, dtype={"event_id": str}).dropna(subset=["latitude", "longitude", "depth_km"])
    ev["origin_time_utc"] = pd.to_datetime(ev.origin_time_utc, utc=True, format="mixed").dt.tz_localize(None)
    st = pd.read_csv(a.stations, dtype={"station_id": str})
    st = st[st.station_id.isin(arr.station_id)].drop_duplicates("station_id")
    arr = arr[arr.station_id.isin(st.station_id)]
    model = read_model(a.model, a.vpvs)
    top_needed = -float(st.elevation_m.max()) / 1000.0 - 0.5
    if model[0][0] > top_needed:  # every station must lie inside the first layer
        model[0] = (round(top_needed, 2), model[0][1], model[0][2])
    sel = select_events(arr, ev, st, a)
    if len(sel) < 20:
        raise SystemExit(f"only {len(sel)} events pass the selection; relax --min-p/--min-s/--max-gap")
    arr = arr[arr.event_id.isin(sel.event_id)]
    st = st[st.station_id.isin(arr.station_id)]
    if len(st) > MAX_STATIONS:
        raise SystemExit(f"{len(st)} stations exceed VELEST's limit {MAX_STATIONS}")
    if a.reference_station:
        ref = a.reference_station
    else:
        cy, cx = float(st.latitude.median()), float(st.longitude.median())
        st = st.assign(dist=np.hypot(st.latitude - cy, (st.longitude - cx) * math.cos(math.radians(cy))))
        central = st[st.dist <= st.dist.quantile(1 / 3)]
        npk = arr[arr.phase == "P"].groupby("station_id").size()
        ref = npk.reindex(central.station_id).idxmax()
    alias = aliases(list(st.station_id))
    d = a.output_dir / "velest"
    if d.exists():
        shutil.rmtree(d)
    d.mkdir(parents=True)
    write_inputs(d, sel, arr, st, model, ref, alias, a)
    proc = subprocess.run([str(BINARY)], cwd=d, capture_output=True, text=True, timeout=a.timeout)
    (d / "stdout.log").write_text(proc.stdout + proc.stderr)
    text = (d / "velest.out").read_text(errors="ignore") if (d / "velest.out").is_file() else ""
    if "End of program VELEST" not in proc.stdout + proc.stderr or not (d / "final.cnv").is_file():
        raise SystemExit(f"VELEST did not finish; see {d / 'stdout.log'} and {d / 'velest.out'}")
    blocks = parse_model(text)
    rms = [float(x) for x in re.findall(r"RMS RESIDUAL=\s+([-\d.]+)", text)]
    back = {v: k for k, v in alias.items()}
    p_final = blocks[-2] if a.use_s and len(blocks) >= 2 else blocks[-1]
    s_final = blocks[-1] if a.use_s and len(blocks) >= 2 else [(m[2], m[0]) for m in model]
    rows = [f"{z:.3f} {vp:.3f} {vs:.3f}" for (vp, z), (vs, _) in zip(p_final, s_final)]
    a.output_dir.mkdir(parents=True, exist_ok=True)
    (a.output_dir / "model_final.txt").write_text("\n".join(rows) + "\n")
    parse_sta(d / "final.sta", back).to_csv(a.output_dir / "station_corrections.csv", index=False)
    fin = parse_cnv(d / "final.cnv")
    if len(fin) == len(sel):
        fin.insert(0, "event_id", sel.event_id.to_numpy())
    fin.to_csv(a.output_dir / "events_final.csv", index=False)
    summary = {"events_selected": int(len(sel)), "stations": int(len(st)), "reference_station": ref,
               "phases": "P and S" if a.use_s else "P", "rms_by_iteration_s": rms,
               "starting_model": [list(m) for m in model], "final_model": [[z, vp] for vp, z in p_final],
               "events_final_matched_by_order": len(fin) == len(sel)}
    (a.output_dir / "summary.json").write_text(json.dumps(summary, indent=1) + "\n")
    print(json.dumps({k: summary[k] for k in ("events_selected", "stations", "reference_station", "rms_by_iteration_s")}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
