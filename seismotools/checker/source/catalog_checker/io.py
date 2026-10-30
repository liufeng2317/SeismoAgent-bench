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
    out["probability"] = pd.to_numeric(raw["probability"], errors="coerce").to_numpy() if "probability" in raw else np.nan
    return out[np.isfinite(out.time) & out.phase.isin(["P", "S"])].reset_index(drop=True)


def read_waveform_index(path: Path) -> pd.DataFrame:
    """Station-days with data from MiniSEED file names ``NET.STA.LOC.CHA__<start>__<end>.mseed``."""
    rows = []
    for f in Path(path).rglob("*.mseed"):
        seed, _, rest = f.name.partition("__")
        parts = seed.split(".")
        if len(parts) < 4 or not rest:
            continue
        start = rest.split("__")[0]
        try:
            day = pd.Timestamp(start[:8]).value // 10**9
        except ValueError:
            continue
        rows.append({"station_id": f"{parts[0]}.{parts[1]}", "channel": parts[3], "day": float(day)})
    return pd.DataFrame(rows, columns=["station_id", "channel", "day"])


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


def _channel_rows(path: Path) -> list[dict]:
    rows = []
    for _, elem in ET.iterparse(path, events=("end",)):
        if elem.tag.rsplit("}", 1)[-1] != "Network":
            continue
        net = elem.get("code")
        for sta in elem:
            if sta.tag.rsplit("}", 1)[-1] != "Station":
                continue
            for cha in sta:
                if cha.tag.rsplit("}", 1)[-1] != "Channel":
                    continue
                values = {child.tag.rsplit("}", 1)[-1]: child for child in cha}
                response = values.get("Response")
                sens = None if response is None else next((e for e in response if e.tag.rsplit("}", 1)[-1] == "InstrumentSensitivity"), None)

                def num(key):
                    try:
                        return float(values[key].text)
                    except (KeyError, TypeError, ValueError):
                        return np.nan

                rows.append({"station_id": f"{net}.{sta.get('code')}", "location": cha.get("locationCode") or "",
                             "channel": cha.get("code"), "start": cha.get("startDate"), "end": cha.get("endDate"),
                             "azimuth": num("Azimuth"), "dip": num("Dip"), "sample_rate": num("SampleRate"),
                             "has_response": sens is not None})
        elem.clear()
    return rows


def read_channels(path: Path) -> pd.DataFrame:
    """Channel epochs from StationXML (empty for a stations CSV): orientation, sample rate, response present."""
    path = Path(path)
    files = (sorted(p for p in path.rglob("*") if p.suffix.lower() in (".xml", ".stationxml")) if path.is_dir()
             else [path] if path.suffix.lower() in (".xml", ".stationxml") else [])
    rows = [r for f in files for r in _channel_rows(f)]
    cols = ["station_id", "location", "channel", "start", "end", "azimuth", "dip", "sample_rate", "has_response"]
    return pd.DataFrame(rows, columns=cols)


def _file_span(name: str) -> tuple[float, float] | None:
    parts = name.split("__")
    if len(parts) < 3:
        return None
    try:
        return (pd.Timestamp(parts[1]).value / 1e9, pd.Timestamp(parts[2].split(".")[0]).value / 1e9)
    except ValueError:
        return None


def read_waveform_streams(path: Path) -> tuple[pd.DataFrame, tuple[float, float] | None, str]:
    """One row per (file, NSLC): coverage, gaps and sample rates from MiniSEED headers.

    Uses ``waveform_inventory.json`` (in the folder or its parent) when present, otherwise reads the
    headers with ObsPy. Returns the table, the processing window when the inventory states one, and
    the source used.
    """
    path = Path(path)
    cols = ["file", "seed_id", "station_id", "location", "channel", "component", "file_start", "file_end",
            "sample_rate", "n_rates", "coverage_s", "gap_s", "overlap_s", "first", "last"]
    for inv_path in (path / "waveform_inventory.json", path.parent / "waveform_inventory.json"):
        if inv_path.is_file():
            import json
            inv = json.loads(inv_path.read_text())
            rows = []
            for f in inv.get("files", []):
                span = _file_span(Path(f["path"]).name)
                for s in f.get("streams", []):
                    first, last = _seconds(pd.Series([s["start_utc"], s["last_sample_utc"]]))
                    rates = s.get("sample_rates_hz") or [np.nan]
                    rows.append({"file": str(inv_path.parent / f["path"]), "seed_id": s["seed_id"],
                                 "station_id": f"{s['network']}.{s['station']}", "location": s["location"],
                                 "channel": s["channel"], "component": s["channel"][-1],
                                 "file_start": span[0] if span else first, "file_end": span[1] if span else last,
                                 "sample_rate": float(max(rates)), "n_rates": len(rates),
                                 "coverage_s": float(s.get("coverage_seconds") or 0), "gap_s": float(s.get("gap_seconds") or 0),
                                 "overlap_s": float(s.get("overlap_seconds") or 0), "first": first, "last": last})
            cand = inv.get("candidate") or {}
            window = None
            if cand.get("start_utc") and cand.get("end_utc"):
                window = tuple(_seconds(pd.Series([cand["start_utc"], cand["end_utc"]])))
            return pd.DataFrame(rows, columns=cols), window, inv_path.name
    from obspy import read
    rows = []
    for f in sorted(path.rglob("*.mseed")):
        try:
            st = read(str(f), headonly=True)
        except Exception:
            continue
        span = _file_span(f.name)
        for seed in sorted({tr.id for tr in st}):
            trs = sorted((tr for tr in st if tr.id == seed), key=lambda tr: tr.stats.starttime)
            t0 = [float(tr.stats.starttime.timestamp) for tr in trs]
            t1 = [float(tr.stats.endtime.timestamp) + tr.stats.delta for tr in trs]
            cover, gap, over, end = 0.0, 0.0, 0.0, None
            for a, b in zip(t0, t1):
                if end is None:
                    cover, end = b - a, b
                    continue
                if a > end:
                    gap += a - end
                    cover += b - a
                else:
                    over += min(b, end) - a
                    cover += max(b - end, 0.0)
                end = max(end, b)
            net, sta, loc, cha = seed.split(".")
            rates = sorted({tr.stats.sampling_rate for tr in trs})
            rows.append({"file": str(f), "seed_id": seed, "station_id": f"{net}.{sta}", "location": loc, "channel": cha,
                         "component": cha[-1], "file_start": span[0] if span else min(t0), "file_end": span[1] if span else max(t1),
                         "sample_rate": float(max(rates)), "n_rates": len(rates), "coverage_s": cover, "gap_s": gap,
                         "overlap_s": over, "first": min(t0), "last": max(t1)})
    return pd.DataFrame(rows, columns=cols), None, "miniseed headers"
