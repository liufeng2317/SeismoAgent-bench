from __future__ import annotations

import csv
import math
import os
import shutil
import time
from pathlib import Path
from typing import Dict, List, Protocol, Sequence, Tuple

from .models import Station, utm


class EventLike(Protocol):
    """Minimal event protocol required by grid-building helpers.
    
    Attributes:
        latitude (float): latitude.
        longitude (float): longitude.
        depth_km (float): depth km.
    """

    latitude: float
    longitude: float
    depth_km: float


def load_velocity_depths(velocity_path: Path) -> List[float]:
    """Read the depth column from a whitespace 1-D velocity model file.
    
    Args:
        velocity_path (Path): velocity path.
    
    Returns:
        List[float]: Result returned by the function.
    """

    depths: List[float] = []
    with velocity_path.open("r", encoding="utf-8", errors="replace") as f:
        for line in f:
            row = line.strip()
            if not row or row.startswith("#"):
                continue
            parts = row.split()
            depths.append(float(parts[0]))
    if not depths:
        raise ValueError(f"No usable velocity rows found in {velocity_path}")
    return depths


def build_run_directory(run_dir: Path) -> None:
    """Create a fresh run directory with standard NonLinLoc subdirectories.
    
    Args:
        run_dir (Path): run dir.
    """

    if run_dir.exists():
        try:
            shutil.rmtree(run_dir)
        except OSError:
            for _ in range(3):
                for child in run_dir.iterdir():
                    if child.is_dir():
                        shutil.rmtree(child, ignore_errors=True)
                    else:
                        try:
                            child.unlink()
                        except FileNotFoundError:
                            pass
                        except OSError:
                            pass
                time.sleep(0.2)
                try:
                    shutil.rmtree(run_dir)
                    break
                except OSError:
                    continue
            else:
                backup_dir = run_dir.with_name(f"{run_dir.name}_stale_{int(time.time())}")
                run_dir.rename(backup_dir)
                print(f"[WARN] Existing run directory was busy; moved it to: {backup_dir}")
    run_dir.mkdir(parents=True, exist_ok=True)
    for subdir in ("model", "time", "obs", "loc"):
        (run_dir / subdir).mkdir(exist_ok=True)


def replace_control_line(control_path: Path, prefix: str, new_line: str) -> None:
    """Replace the first control-file line that starts with ``prefix``.
    
    Args:
        control_path (Path): control path.
        prefix (str): prefix.
        new_line (str): new line.
    """

    with control_path.open("r", encoding="utf-8", errors="replace") as f:
        lines = f.readlines()

    replaced = False
    normalized = new_line if new_line.endswith("\n") else new_line + "\n"
    for i, line in enumerate(lines):
        if line.startswith(prefix):
            lines[i] = normalized
            replaced = True
            break

    if not replaced:
        raise ValueError(f"Could not find control line starting with {prefix!r} in {control_path}")

    with control_path.open("w", encoding="utf-8") as f:
        f.writelines(lines)


def patch_lochypout_line(control_path: Path) -> None:
    """Normalize ``LOCHYPOUT`` to the package's default per-event output mode.
    
    Args:
        control_path (Path): control path.
    """

    replace_control_line(control_path, "LOCHYPOUT", "LOCHYPOUT SAVE_NLLOC_ALL SAVE_HYPOINV_SUM")


def ensure_locmeth_line(control_path: Path, locmeth_line: str) -> None:
    """Insert a ``LOCMETH`` block before ``LOCHYPOUT`` if one is missing.
    
    Args:
        control_path (Path): control path.
        locmeth_line (str): locmeth line.
    """

    with control_path.open("r", encoding="utf-8", errors="replace") as f:
        lines = f.readlines()

    if any(line.startswith("LOCMETH") for line in lines):
        return

    insert_at = None
    for i, line in enumerate(lines):
        if line.startswith("LOCHYPOUT"):
            insert_at = i
            break

    if insert_at is None:
        raise ValueError(f"Could not find LOCHYPOUT section in {control_path}")

    block = [
        "# ========================================================================\n",
        "# LOCMETH - Location Method\n",
        "# inserted by nonlinlocpy.utils.ensure_locmeth_line\n",
        "#\n",
        locmeth_line if locmeth_line.endswith("\n") else locmeth_line + "\n",
        "\n",
    ]
    lines[insert_at:insert_at] = block

    with control_path.open("w", encoding="utf-8") as f:
        f.writelines(lines)


def project_points_to_utm(
    lat_lon_pairs: Sequence[Tuple[float, float]],
    zone_number: int | None = None,
    zone_letter: str | None = None,
) -> Tuple[List[float], List[float], int, str]:
    """Project latitude/longitude pairs into one shared UTM zone.
    
    Args:
        lat_lon_pairs (Sequence[Tuple[float, float]]): lat lon pairs.
        zone_number (int | None): Optional fixed UTM zone number.
        zone_letter (str | None): Optional fixed UTM zone letter.
    
    Returns:
        Tuple[List[float], List[float], int, str]: Result returned by the function.
    """

    if zone_number is not None:
        if zone_letter is None:
            zone_letter = "N"
        try:
            from pyproj import Transformer

            epsg = 32600 + int(zone_number) if str(zone_letter).upper() >= "N" else 32700 + int(zone_number)
            transformer = Transformer.from_crs("EPSG:4326", f"EPSG:{epsg}", always_xy=True)
            eastings: List[float] = []
            northings: List[float] = []
            for lat, lon in lat_lon_pairs:
                east, north = transformer.transform(float(lon), float(lat))
                eastings.append(float(east))
                northings.append(float(north))
            if not eastings:
                raise ValueError("No coordinates were provided for UTM projection.")
            return eastings, northings, int(zone_number), str(zone_letter)
        except ImportError:
            pass

    eastings: List[float] = []
    northings: List[float] = []
    force_zone = zone_number is not None
    selected_zone_number: int | None = int(zone_number) if zone_number is not None else None
    selected_zone_letter: str | None = str(zone_letter) if zone_letter is not None else None

    for lat, lon in lat_lon_pairs:
        if force_zone:
            east, north, this_zone_number, this_zone_letter = utm.from_latlon(
                float(lat),
                float(lon),
                force_zone_number=selected_zone_number,
                force_zone_letter=selected_zone_letter,
            )
        else:
            east, north, this_zone_number, this_zone_letter = utm.from_latlon(float(lat), float(lon))
        if selected_zone_number is None:
            selected_zone_number = int(this_zone_number)
            selected_zone_letter = str(this_zone_letter)
        elif int(this_zone_number) != selected_zone_number or str(this_zone_letter) != selected_zone_letter:
            raise ValueError(
                "Coordinates fall into multiple UTM zones. Set `utm_zone_number` and "
                "`utm_zone_letter` in the workflow config to use a fixed zone."
            )
        eastings.append(float(east))
        northings.append(float(north))

    if selected_zone_number is None or selected_zone_letter is None:
        raise ValueError("No coordinates were provided for UTM projection.")

    return eastings, northings, selected_zone_number, selected_zone_letter


def compute_grid_lines(
    stations: Sequence[Station],
    events: Sequence[EventLike],
    velocity_depths: Sequence[float],
    horizontal_pad_km: float,
    depth_top_km: float,
    depth_bottom_pad_km: float,
    horizontal_spacing_km: float,
    depth_spacing_km: float,
    utm_zone_number: int | None = None,
    utm_zone_letter: str | None = None,
) -> Tuple[str, str]:
    """Compute ``VGGRID`` and ``LOCGRID`` lines from stations, events, and spacing rules.
    
    Args:
        stations (Sequence[Station]): stations.
        events (Sequence[EventLike]): events.
        velocity_depths (Sequence[float]): velocity depths.
        horizontal_pad_km (float): horizontal pad km.
        depth_top_km (float): depth top km.
        depth_bottom_pad_km (float): depth bottom pad km.
        horizontal_spacing_km (float): horizontal spacing km.
        depth_spacing_km (float): depth spacing km.
        utm_zone_number (int | None): Optional fixed UTM zone number for wide regions.
        utm_zone_letter (str | None): Optional fixed UTM zone letter.
    
    Returns:
        Tuple[str, str]: Result returned by the function.
    """

    station_lat_lon = [(s.lat, s.lon) for s in stations]
    east_sta, north_sta, zone_number, zone_letter = project_points_to_utm(
        station_lat_lon,
        zone_number=utm_zone_number,
        zone_letter=utm_zone_letter,
    )
    x0 = float(min(east_sta))
    y0 = float(min(north_sta))

    event_lat_lon = [(ev.latitude, ev.longitude) for ev in events]
    east_evt, north_evt, evt_zone_number, evt_zone_letter = project_points_to_utm(
        event_lat_lon,
        zone_number=zone_number,
        zone_letter=zone_letter,
    )
    if evt_zone_number != zone_number or evt_zone_letter != zone_letter:
        raise ValueError("Event and station coordinates fall into different UTM zones.")

    event_x = [(e - x0) / 1000.0 for e in east_evt]
    event_y = [(n - y0) / 1000.0 for n in north_evt]
    sta_x = [(e - x0) / 1000.0 for e in east_sta]
    sta_y = [(n - y0) / 1000.0 for n in north_sta]

    xmin = min(event_x) - horizontal_pad_km
    xmax = max(event_x) + horizontal_pad_km
    ymin = min(event_y) - horizontal_pad_km
    ymax = max(event_y) + horizontal_pad_km

    zmin = depth_top_km
    zmax = max(max(ev.depth_km for ev in events) + depth_bottom_pad_km, max(velocity_depths) + 5.0)

    nx = int(math.ceil((xmax - xmin) / horizontal_spacing_km)) + 1
    ny = int(math.ceil((ymax - ymin) / horizontal_spacing_km)) + 1
    nz = int(math.ceil((zmax - zmin) / depth_spacing_km)) + 1

    corners = [(xmin, ymin), (xmin, ymax), (xmax, ymin), (xmax, ymax)]
    radial_max = 0.0
    for sx, sy in zip(sta_x, sta_y):
        for cx, cy in corners:
            radial_max = max(radial_max, math.hypot(cx - sx, cy - sy))

    vg_ny = int(math.ceil((radial_max + horizontal_pad_km) / horizontal_spacing_km)) + 1
    vg_nz = nz

    vggrid_line = (
        f"VGGRID  2  {vg_ny}  {vg_nz}  0.0  0.0  {zmin:.3f}  "
        f"{horizontal_spacing_km:.3f}  {horizontal_spacing_km:.3f}  {depth_spacing_km:.3f}  SLOW_LEN"
    )
    locgrid_line = (
        f"LOCGRID  {nx}  {ny}  {nz}  {xmin:.3f}  {ymin:.3f}  {zmin:.3f}  "
        f"{horizontal_spacing_km:.3f}  {horizontal_spacing_km:.3f}  {depth_spacing_km:.3f}  "
        "PROB_DENSITY  SAVE"
    )
    return vggrid_line, locgrid_line


def write_solution_csv(output_path: Path, solutions: Sequence[Dict[str, object]]) -> None:
    """Write the default compact event table used by this package.
    
    Args:
        output_path (Path): output path.
        solutions (Sequence[Dict[str, object]]): solutions.
    """

    write_compact_solution_csv(output_path, solutions)


def _build_origin_time_text(row: Dict[str, object]) -> str:
    """Build a single ISO-like ``origin_time`` string from split date/time fields.
    
    Args:
        row (Dict[str, object]): row.
    
    Returns:
        str: Result returned by the function.
    """

    ymd = str(row.get("origin_yyyymmdd", "") or "")
    hms = str(row.get("origin_hhmmss", "") or "")
    if not ymd:
        return ""
    if not hms:
        return ymd
    if "." in hms:
        hhmmss, frac = hms.split(".", 1)
        hhmmss = hhmmss.zfill(6)
        return f"{ymd[:4]}-{ymd[4:6]}-{ymd[6:8]}T{hhmmss[:2]}:{hhmmss[2:4]}:{hhmmss[4:6]}.{frac}Z"
    hhmmss = hms.zfill(6)
    return f"{ymd[:4]}-{ymd[4:6]}-{ymd[6:8]}T{hhmmss[:2]}:{hhmmss[2:4]}:{hhmmss[4:6]}Z"


def write_compact_solution_csv(output_path: Path, solutions: Sequence[Dict[str, object]]) -> None:
    """Write a compact CSV with the most commonly used relocation fields.
    
    Args:
        output_path (Path): output path.
        solutions (Sequence[Dict[str, object]]): solutions.
    """

    fields = [
        "event_id",
        "origin_time",
        "lat",
        "lon",
        "depth_km",
        "rms_sec",
        "used_phase_count",
        "used_station_count",
        "gap_deg",
        "min_dist_km",
        "max_dist_km",
        "median_dist_km",
        "min_horizontal_uncertainty_km",
        "max_horizontal_uncertainty_km",
        "semi_major_axis_km",
        "semi_minor_axis_km",
        "semi_intermediate_axis_km",
        "coord_source",
    ]
    with output_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for index, row in enumerate(solutions, start=1):
            compact_row = {
                "event_id": row.get("hyp_file", f"event_{index:06d}"),
                "origin_time": _build_origin_time_text(row),
                "lat": row.get("lat", ""),
                "lon": row.get("lon", ""),
                "depth_km": row.get("depth_km", ""),
                "rms_sec": row.get("rms_sec", ""),
                "used_phase_count": row.get("used_phase_count", row.get("nphs", "")),
                "used_station_count": row.get("used_station_count", ""),
                "gap_deg": row.get("gap_deg", row.get("az_gap_deg", "")),
                "min_dist_km": row.get("min_dist_km", ""),
                "max_dist_km": row.get("max_dist_km", ""),
                "median_dist_km": row.get("median_dist_km", ""),
                "min_horizontal_uncertainty_km": row.get("min_horizontal_uncertainty_km", ""),
                "max_horizontal_uncertainty_km": row.get("max_horizontal_uncertainty_km", ""),
                "semi_major_axis_km": row.get("semi_major_axis_km", ""),
                "semi_minor_axis_km": row.get("semi_minor_axis_km", ""),
                "semi_intermediate_axis_km": row.get("semi_intermediate_axis_km", ""),
                "coord_source": row.get("coord_source", ""),
            }
            writer.writerow(compact_row)


def cleanup_production_outputs(run_dir: Path) -> None:
    """Prune heavy production outputs while keeping core per-event result files.
    
    Args:
        run_dir (Path): run dir.
    """

    loc_dir = run_dir / "loc"
    if not loc_dir.is_dir():
        return

    keep_names = {
        "last.in",
        "last.stat",
        "last.stat_totcorr",
        "last.stations",
        "last.hdr",
        "last.hyp",
        "last.hypo_inv",
        "realtime_nlloc.in",
    }
    keep_suffixes = {".hdr", ".hyp", ".hypo_inv", ".stat", ".stations"}
    for path in loc_dir.iterdir():
        if path.name in keep_names:
            continue
        if "sum" in path.name:
            continue
        if path.suffix in keep_suffixes:
            continue
        if path.suffix == ".scat":
            try:
                path.unlink()
            except OSError:
                pass
            continue
        if path.is_file():
            try:
                path.unlink()
            except OSError:
                pass


def resolve_nlloc_bin_dir(nlloc_bin_dir: str) -> str:
    """Resolve the NonLinLoc binary directory from input, PATH, or bundled fallback.
    
    Args:
        nlloc_bin_dir (str): nlloc bin dir.
    
    Returns:
        str: Result returned by the function.
    """

    if nlloc_bin_dir:
        return nlloc_bin_dir

    required = ["NLLoc", "Vel2Grid", "Grid2Time"]
    resolved = {name: shutil.which(name) for name in required}
    missing = [name for name, path in resolved.items() if path is None]
    if missing:
        project_bin = Path(__file__).resolve().parents[2] / "native" / "bin"
        project_paths = {name: project_bin / name for name in required}
        if all(path.is_file() for path in project_paths.values()):
            return str(project_bin)

        missing_str = ", ".join(missing)
        raise ValueError(
            "Could not find required NonLinLoc executables on PATH and no bundled fallback was found. "
            f"Missing executables: {missing_str}. Either export them in your shell environment, "
            "pass the project nonlinloc/native/bin directory or another --nlloc-bin path."
        )

    first_path = next(path for path in resolved.values() if path is not None)
    return str(Path(first_path).resolve().parent)
