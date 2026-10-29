"""Read a catalog, its picks and the station metadata into plain tables.

The checker reads the benchmark output contract: ``catalog.csv`` (event_id,
origin_time_utc, latitude, longitude, depth_km below sea level, magnitude, ...)
and ``picks.csv`` (pick_id, event_id, station_id NET.STA, phase, time_utc, ...).
Stations come from StationXML (a file or a directory of files) or from a CSV
with station_id, latitude, longitude and elevation_m.
"""

from __future__ import annotations

import xml.etree.ElementTree as ET
from pathlib import Path

import numpy as np
import pandas as pd

KM_PER_DEG = 111.195


def _seconds(values: pd.Series) -> np.ndarray:
    text = values.astype(str).str.strip().str.replace(" ", "T", regex=False)
    text = text.str.replace(r"(\.\d{6})\d+", r"\1", regex=True)
    stamps = pd.to_datetime(text, utc=True, errors="coerce", format="ISO8601")
    return ((stamps - pd.Timestamp(0, tz="UTC")).dt.total_seconds()).to_numpy(dtype=float)


def read_catalog(path: Path) -> pd.DataFrame:
    raw = pd.read_csv(path, dtype=str, keep_default_na=False)
    status = raw.get("status", pd.Series([""] * len(raw))).str.strip().str.lower()
    raw = raw[status != "rejected"].reset_index(drop=True)
    out = pd.DataFrame({"event_id": raw["event_id"].astype(str), "time": _seconds(raw["origin_time_utc"])})
    for col in ("latitude", "longitude", "depth_km", "magnitude"):
        out[col] = pd.to_numeric(raw[col], errors="coerce") if col in raw else np.nan
    return out[np.isfinite(out.time)].reset_index(drop=True)


def read_picks(path: Path) -> pd.DataFrame:
    raw = pd.read_csv(path, dtype=str, keep_default_na=False)
    status = raw.get("status", pd.Series([""] * len(raw))).str.strip().str.lower()
    raw = raw[status != "rejected"]
    out = pd.DataFrame({"event_id": raw["event_id"].astype(str).str.strip(),
                        "station_id": raw["station_id"].astype(str).str.strip(),
                        "phase": raw["phase"].astype(str).str.strip().str.upper().str[0],
                        "time": _seconds(raw["time_utc"])})
    return out[np.isfinite(out.time) & out.phase.isin(["P", "S"])].reset_index(drop=True)


def _stationxml(path: Path) -> list[dict]:
    rows = []
    for _, elem in ET.iterparse(path, events=("end",)):
        if elem.tag.rsplit("}", 1)[-1] != "Network":
            continue
        net = elem.get("code")
        for sta in elem:
            if sta.tag.rsplit("}", 1)[-1] != "Station":
                continue
            values = {child.tag.rsplit("}", 1)[-1]: child.text for child in sta}
            try:
                rows.append({"station_id": f"{net}.{sta.get('code')}", "latitude": float(values["Latitude"]),
                             "longitude": float(values["Longitude"]), "elevation_m": float(values.get("Elevation") or 0)})
            except (KeyError, TypeError, ValueError):
                continue
        elem.clear()
    return rows


def read_stations(path: Path) -> pd.DataFrame:
    path = Path(path)
    if path.is_dir():
        files = sorted(p for p in path.rglob("*") if p.suffix.lower() in (".xml", ".stationxml"))
        rows = [r for f in files for r in _stationxml(f)]
    elif path.suffix.lower() in (".xml", ".stationxml"):
        rows = _stationxml(path)
    else:
        table = pd.read_csv(path)
        rows = table[["station_id", "latitude", "longitude", "elevation_m"]].to_dict("records")
    stations = pd.DataFrame(rows, columns=["station_id", "latitude", "longitude", "elevation_m"])
    # A station has several epochs in StationXML; keep the median position per code.
    return stations.groupby("station_id", as_index=False).median()


def local_km(lat, lon, lat0: float, lon0: float):
    x = (np.asarray(lon, dtype=float) - lon0) * KM_PER_DEG * np.cos(np.radians(lat0))
    y = (np.asarray(lat, dtype=float) - lat0) * KM_PER_DEG
    return x, y
