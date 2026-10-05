#!/usr/bin/env python3
"""Prepare explicit-input files for the Japan CC-only hypodd_runner example.

This helper exposes one function, ``prepare_jma_cc_only_inputs``. The generated
phase times are theoretical P/S arrivals; they only anchor FDTCC waveform
windows. The final relocation should use CC-only HypoDD settings supplied by the
caller.
"""

from __future__ import annotations

import math
import os
from dataclasses import dataclass
from pathlib import Path
from time import perf_counter

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class PreparedCcOnlyInputs:
    """Input files and metadata prepared for a CC-only relocation run."""

    run_dir: Path
    input_dir: Path
    output_dir: Path
    station_file: Path
    phase_file: Path
    event_csv: Path
    lon_range: list[float]
    lat_range: list[float]
    n_events: int
    n_stations: int


def haversine_km_array(lon1, lat1, lon2, lat2) -> np.ndarray:
    """Vectorized great-circle distance in kilometers."""
    radius_km = 6371.0
    lon1 = np.asarray(lon1, dtype=float)
    lat1 = np.asarray(lat1, dtype=float)
    lon2 = np.asarray(lon2, dtype=float)
    lat2 = np.asarray(lat2, dtype=float)
    p1 = np.radians(lat1)
    p2 = np.radians(lat2)
    dp = np.radians(lat2 - lat1)
    dl = np.radians(lon2 - lon1)
    a = np.sin(dp / 2.0) ** 2 + np.cos(p1) * np.cos(p2) * np.sin(dl / 2.0) ** 2
    return 2.0 * radius_km * np.arcsin(np.sqrt(a))


def resolve_circle_selection(
    *,
    main_earthquake_csv: str,
    main_index: str,
    center_lon: float | None,
    center_lat: float | None,
    radius_km: float,
) -> tuple[float, float, float]:
    """Return circle center/radius from explicit center or main-earthquake CSV."""
    if center_lon is not None and center_lat is not None:
        return float(center_lon), float(center_lat), float(radius_km)

    main_csv = Path(main_earthquake_csv)
    main = pd.read_csv(main_csv)
    required = {"index", "lat", "lon"}
    missing = required.difference(main.columns)
    if missing:
        raise ValueError(f"{main_csv} is missing required columns: {sorted(missing)}")

    key = str(main_index or "").strip()
    if key:
        hit = main.loc[main["index"].astype(str) == key]
        if hit.empty:
            raise ValueError(f"main_index={key!r} not found in {main_csv}")
        row = hit.iloc[0]
        return float(row["lon"]), float(row["lat"]), float(radius_km)
    return float(main["lon"].mean()), float(main["lat"].mean()), float(radius_km)


def selection_bounds(
    *,
    lon_range: tuple[float, float] | list[float],
    lat_range: tuple[float, float] | list[float],
    selection_mode: str,
    main_earthquake_csv: str,
    main_index: str,
    center_lon: float | None,
    center_lat: float | None,
    radius_km: float,
) -> tuple[list[float], list[float]]:
    """Return lon/lat bounds for box selection or circle prefiltering."""
    if selection_mode == "circle":
        lon0, lat0, radius = resolve_circle_selection(
            main_earthquake_csv=main_earthquake_csv,
            main_index=main_index,
            center_lon=center_lon,
            center_lat=center_lat,
            radius_km=radius_km,
        )
        lat_pad = radius / 111.32
        lon_pad = radius / (111.32 * math.cos(math.radians(lat0)))
        return [lon0 - lon_pad, lon0 + lon_pad], [lat0 - lat_pad, lat0 + lat_pad]
    return [float(lon_range[0]), float(lon_range[1])], [float(lat_range[0]), float(lat_range[1])]


def load_events(
    *,
    catalog: str,
    start: str,
    end: str,
    lon_range: tuple[float, float] | list[float],
    lat_range: tuple[float, float] | list[float],
    selection_mode: str,
    main_earthquake_csv: str,
    main_index: str,
    center_lon: float | None,
    center_lat: float | None,
    radius_km: float,
    max_depth_km: float,
    min_mag: float | None,
    max_events: int,
) -> tuple[pd.DataFrame, list[float], list[float]]:
    """Load and filter catalog events for the requested time/space window."""
    df = pd.read_csv(catalog)
    df["datetime"] = pd.to_datetime(df["datetime"], errors="coerce")
    lon_bounds, lat_bounds = selection_bounds(
        lon_range=lon_range,
        lat_range=lat_range,
        selection_mode=selection_mode,
        main_earthquake_csv=main_earthquake_csv,
        main_index=main_index,
        center_lon=center_lon,
        center_lat=center_lat,
        radius_km=radius_km,
    )
    mask = (
        (df["datetime"] >= pd.Timestamp(start))
        & (df["datetime"] < pd.Timestamp(end))
        & (df["lon"] >= lon_bounds[0])
        & (df["lon"] <= lon_bounds[1])
        & (df["lat"] >= lat_bounds[0])
        & (df["lat"] <= lat_bounds[1])
        & (df["dep"] >= 0.0)
        & (df["dep"] <= float(max_depth_km))
    )
    if selection_mode == "circle":
        lon0, lat0, radius = resolve_circle_selection(
            main_earthquake_csv=main_earthquake_csv,
            main_index=main_index,
            center_lon=center_lon,
            center_lat=center_lat,
            radius_km=radius_km,
        )
        dist = haversine_km_array(df["lon"].to_numpy(), df["lat"].to_numpy(), lon0, lat0)
        mask &= pd.Series(dist, index=df.index) <= radius
    if min_mag is not None:
        mask &= df["mag"] >= float(min_mag)

    out = df.loc[mask].copy()
    out = out.sort_values(["mag", "datetime"], ascending=[False, True])
    if max_events and max_events > 0:
        out = out.head(int(max_events))
    out = out.sort_values("datetime").reset_index(drop=True)
    out["evid"] = range(1, len(out) + 1)
    return out, lon_bounds, lat_bounds


def scan_waveform_station_ids_for_days(waveform_root: Path, days: list[str]) -> dict[str, set[str]]:
    """Scan MiniSEED day folders and return available NET.STA station ids."""
    by_day: dict[str, set[str]] = {}
    for day in days:
        ids: set[str] = set()
        day_dir = waveform_root / day
        if day_dir.is_dir():
            for path in day_dir.iterdir():
                if not path.name.endswith(".mseed"):
                    continue
                parts = path.name.split(".")
                if len(parts) >= 2:
                    ids.add(f"{parts[0]}.{parts[1]}")
        by_day[day] = ids
    return by_day


def waveform_station_ids(
    waveform_root: Path,
    days: list[str],
    *,
    inventory_path: Path | None,
    rebuild: bool,
) -> set[str]:
    """Return waveform-available station ids, using a small CSV cache."""
    ids: set[str] = set()
    days_set = set(days)
    inventory = pd.DataFrame(columns=["day", "station_id"])
    if inventory_path is not None and inventory_path.is_file() and not rebuild:
        inventory = pd.read_csv(inventory_path, dtype={"day": str, "station_id": str})
        hit = inventory.loc[inventory["day"].isin(days_set)]
        ids.update(hit["station_id"].dropna().astype(str).unique())
    cached_days = set(inventory["day"].dropna().astype(str).unique()) if not inventory.empty else set()
    missing_days = sorted(days_set.difference(cached_days)) if not rebuild else sorted(days_set)
    if missing_days:
        scanned = scan_waveform_station_ids_for_days(waveform_root, missing_days)
        rows = [
            {"day": day, "station_id": station_id}
            for day, station_ids in scanned.items()
            for station_id in sorted(station_ids)
        ]
        if rows:
            fresh = pd.DataFrame(rows)
            ids.update(fresh["station_id"].unique())
            if inventory_path is not None:
                inventory_path.parent.mkdir(parents=True, exist_ok=True)
                merged = fresh if rebuild or inventory.empty else pd.concat(
                    [inventory.loc[~inventory["day"].isin(missing_days)], fresh],
                    ignore_index=True,
                )
                merged.sort_values(["day", "station_id"]).to_csv(inventory_path, index=False)
    return ids


def load_stations(
    *,
    stations: str,
    waveform_root: str,
    waveform_station_inventory: str,
    rebuild_waveform_station_inventory: bool,
    start: str,
    end: str,
    events: pd.DataFrame,
    lon_range: list[float],
    lat_range: list[float],
    station_pad_deg: float | None,
    max_stations: int,
) -> pd.DataFrame:
    """Load stations and keep only stations with waveform files in the selected days."""
    rows = []
    with open(stations, encoding="utf-8", errors="replace") as fh:
        for line in fh:
            text = line.strip()
            if not text or text.startswith("#"):
                continue
            tokens = text.split()
            if len(tokens) < 5:
                continue
            try:
                rows.append(
                    {
                        "station_id": tokens[1],
                        "lat": float(tokens[2]),
                        "lon": float(tokens[3]),
                        "elev_m": float(tokens[4]),
                    }
                )
            except ValueError:
                continue
    sta = pd.DataFrame(rows)
    if sta.empty:
        raise RuntimeError(f"No stations parsed from {stations}")

    days = sorted(
        {
            day.strftime("%Y%m%d")
            for day in pd.date_range(start, pd.Timestamp(end) - pd.Timedelta(days=1), freq="D")
        }
    )
    available = waveform_station_ids(
        Path(waveform_root),
        days,
        inventory_path=Path(waveform_station_inventory).resolve() if waveform_station_inventory else None,
        rebuild=bool(rebuild_waveform_station_inventory),
    )
    sta = sta.loc[sta["station_id"].isin(available)].copy()

    if station_pad_deg is not None:
        pad = float(station_pad_deg)
        sta = sta.loc[
            (sta["lon"] >= lon_range[0] - pad)
            & (sta["lon"] <= lon_range[1] + pad)
            & (sta["lat"] >= lat_range[0] - pad)
            & (sta["lat"] <= lat_range[1] + pad)
        ].copy()

    center_lon = float(events["lon"].median())
    center_lat = float(events["lat"].median())
    sta["dist_to_event_center_km"] = haversine_km_array(
        sta["lon"].to_numpy(),
        sta["lat"].to_numpy(),
        center_lon,
        center_lat,
    )
    sta = sta.sort_values("dist_to_event_center_km")
    if max_stations and max_stations > 0:
        sta = sta.head(int(max_stations))
    return sta.reset_index(drop=True)


def write_station_file(stations: pd.DataFrame, path: Path) -> None:
    """Write hypodd_runner station CSV with NET.STA ids and coordinates."""
    with path.open("w", encoding="utf-8") as fh:
        fh.write("network.station,latitude,longitude,elevation\n")
        for _, row in stations.iterrows():
            fh.write(f"{row.station_id},{row.lat:.5f},{row.lon:.5f},{row.elev_m:.1f}\n")


def write_phase_file(events: pd.DataFrame, stations: pd.DataFrame, path: Path, vp: float, vs: float) -> None:
    """Write event blocks with theoretical P/S picks for FDTCC window anchoring."""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_name(path.name + ".tmp")
    station_ids = stations["station_id"].astype(str).to_numpy()
    station_lon = stations["lon"].to_numpy(dtype=float)
    station_lat = stations["lat"].to_numpy(dtype=float)
    station_elev = stations["elev_m"].to_numpy(dtype=float)
    expected_lines = int(len(events) * (len(stations) + 1))
    with tmp_path.open("w", encoding="utf-8", newline="\n") as fh:
        for event in events.itertuples(index=False):
            origin = pd.Timestamp(event.datetime)
            origin_text = origin.strftime("%Y-%m-%dT%H:%M:%S.%fZ")
            fh.write(f"{origin_text},{event.lat:.5f},{event.lon:.5f},{event.dep:.3f},{event.mag:.2f},{int(event.evid)}\n")
            horizontal = haversine_km_array(float(event.lon), float(event.lat), station_lon, station_lat)
            dz = float(event.dep) + np.maximum(-station_elev / 1000.0, 0.0)
            ray = np.hypot(horizontal, dz)
            p_times = pd.to_datetime(origin + pd.to_timedelta(ray / vp, unit="s")).strftime("%Y-%m-%dT%H:%M:%S.%fZ")
            s_times = pd.to_datetime(origin + pd.to_timedelta(ray / vs, unit="s")).strftime("%Y-%m-%dT%H:%M:%S.%fZ")
            fh.writelines(
                f"{station_id},{p_time},{s_time}\n"
                for station_id, p_time, s_time in zip(station_ids, p_times, s_times)
            )
        fh.flush()
        os.fsync(fh.fileno())
    os.replace(tmp_path, path)
    data = path.read_bytes()
    nul_count = data.count(b"\x00")
    if nul_count:
        raise RuntimeError(f"Generated phase file contains {nul_count} NUL byte(s): {path}")
    line_count = data.count(b"\n")
    if line_count != expected_lines:
        raise RuntimeError(
            f"Generated phase file line count mismatch: expected {expected_lines}, got {line_count}: {path}"
        )


def event_file_stem(start: str, end: str) -> str:
    """Return a stable selected-event CSV stem from a half-open time interval."""
    start_time = pd.Timestamp(start)
    last_day = pd.Timestamp(end) - pd.Timedelta(days=1)
    if start_time.strftime("%Y%m%d") == last_day.strftime("%Y%m%d"):
        return f"selected_jma_events_{start_time.strftime('%Y%m%d')}"
    return f"selected_jma_events_{start_time.strftime('%Y%m%d')}_{last_day.strftime('%Y%m%d')}"


def prepare_jma_cc_only_inputs(
    *,
    catalog: str,
    stations: str,
    waveform_root: str,
    run_dir: str,
    start: str,
    end: str,
    lon_range: tuple[float, float] | list[float],
    lat_range: tuple[float, float] | list[float],
    main_earthquake_csv: str,
    waveform_station_inventory: str,
    selection_mode: str = "box",
    center_lon: float | None = None,
    center_lat: float | None = None,
    radius_km: float = 300.0,
    main_index: str = "",
    max_depth_km: float = 90.0,
    min_mag: float | None = None,
    max_events: int = 0,
    max_stations: int = 0,
    station_pad_deg: float | None = None,
    vp_km_s: float = 6.2,
    vs_km_s: float = 3.55,
    rebuild_waveform_station_inventory: bool = False,
) -> PreparedCcOnlyInputs:
    """Prepare station, phase, and selected-event files from explicit parameters."""
    t0 = perf_counter()
    run_path = Path(run_dir).resolve()
    input_dir = run_path / "input"
    output_dir = run_path / "output"
    input_dir.mkdir(parents=True, exist_ok=True)
    output_dir.mkdir(parents=True, exist_ok=True)

    events, lon_bounds, lat_bounds = load_events(
        catalog=catalog,
        start=start,
        end=end,
        lon_range=lon_range,
        lat_range=lat_range,
        selection_mode=selection_mode,
        main_earthquake_csv=main_earthquake_csv,
        main_index=main_index,
        center_lon=center_lon,
        center_lat=center_lat,
        radius_km=radius_km,
        max_depth_km=max_depth_km,
        min_mag=min_mag,
        max_events=max_events,
    )
    if events.empty:
        raise RuntimeError("No JMA events after filtering.")
    print(f"Loaded selected events: {len(events)} ({perf_counter() - t0:.1f}s)")

    t_station = perf_counter()
    station_frame = load_stations(
        stations=stations,
        waveform_root=waveform_root,
        waveform_station_inventory=waveform_station_inventory,
        rebuild_waveform_station_inventory=rebuild_waveform_station_inventory,
        start=start,
        end=end,
        events=events,
        lon_range=lon_bounds,
        lat_range=lat_bounds,
        station_pad_deg=station_pad_deg,
        max_stations=max_stations,
    )
    if station_frame.empty:
        raise RuntimeError("No waveform-available stations after filtering.")
    print(f"Prepared stations: {len(station_frame)} ({perf_counter() - t_station:.1f}s)")

    station_file = input_dir / "station.sta"
    write_station_file(station_frame, station_file)
    phase_file = input_dir / "phase_theoretical_jma.pha"
    t_phase = perf_counter()
    write_phase_file(events, station_frame, phase_file, vp_km_s, vs_km_s)
    print(
        f"Wrote theoretical phase file: {len(events)} events x {len(station_frame)} stations "
        f"({perf_counter() - t_phase:.1f}s)"
    )

    event_csv = input_dir / f"{event_file_stem(start, end)}.csv"
    events[["evid", "datetime", "lat", "lon", "dep", "mag"]].to_csv(event_csv, index=False)
    station_frame.to_csv(input_dir / "selected_waveform_stations.csv", index=False)

    print(f"Selected events: {len(events)}")
    print(f"Selected stations: {len(station_frame)}")
    print(f"Wrote: {event_csv}")
    print(f"Wrote: {phase_file}")
    print(f"Wrote: {station_file}")
    return PreparedCcOnlyInputs(
        run_dir=run_path,
        input_dir=input_dir,
        output_dir=output_dir,
        station_file=station_file,
        phase_file=phase_file,
        event_csv=event_csv,
        lon_range=lon_bounds,
        lat_range=lat_bounds,
        n_events=len(events),
        n_stations=len(station_frame),
    )


if __name__ == "__main__":
    raise SystemExit("Import prepare_jma_cc_only_inputs from run_jma_cc_only.py; edit parameters there.")
