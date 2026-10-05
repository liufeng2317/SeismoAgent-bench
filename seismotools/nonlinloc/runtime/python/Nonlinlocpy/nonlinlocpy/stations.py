"""Station table and travel-time setup helpers for NonLinLoc."""

from __future__ import annotations

import os
import pickle
import shutil
import subprocess
from typing import List, Sequence

import numpy as np

from .control import save_control_gtsrce_sections
from .models import Station
from .utils import project_points_to_utm


def apply_stations_wgs84(
    nlloc_bin_dir: str,
    control_file_path: str,
    stations: Sequence[Station],
    control_file_name: str = "nlloc.in",
    utm_zone_number: int | None = None,
    utm_zone_letter: str | None = None,
) -> None:
    """Write ``GTSRCE`` lines, save UTM origin metadata, and run ``Grid2Time`` for P and S.
    
    Args:
        nlloc_bin_dir (str): nlloc bin dir.
        control_file_path (str): control file path.
        stations (Sequence[Station]): stations.
        control_file_name (str): control file name.
        utm_zone_number (int | None): Optional fixed UTM zone number.
        utm_zone_letter (str | None): Optional fixed UTM zone letter.
    """

    if nlloc_bin_dir and nlloc_bin_dir not in os.environ.get("PATH", ""):
        os.environ["PATH"] = nlloc_bin_dir + os.pathsep + os.environ.get("PATH", "")

    save_control_gtsrce_sections(control_file_path, control_file_name)
    pkl = os.path.join(control_file_path, "Part_of_ControlFile.pickle")
    with open(pkl, "rb") as fp:
        part1 = pickle.load(fp)
        part2 = pickle.load(fp)

    lat = np.array([float(s.lat) for s in stations], dtype=float)
    lon = np.array([float(s.lon) for s in stations], dtype=float)
    east_list, north_list, zone_number, zone_letter = project_points_to_utm(
        list(zip(lat.tolist(), lon.tolist())),
        zone_number=utm_zone_number,
        zone_letter=utm_zone_letter,
    )
    east = np.asarray(east_list, dtype=float)
    north = np.asarray(north_list, dtype=float)
    x0 = float(np.min(east))
    y0 = float(np.min(north))
    x_km = (east - x0) / 1000.0
    y_km = (north - y0) / 1000.0
    elev_km = [float(s.elev_m) / 1000.0 for s in stations]

    with open(os.path.join(control_file_path, "Zone_info.pickle"), "wb") as fp:
        pickle.dump(zone_number, fp)
        pickle.dump(zone_letter, fp)
        pickle.dump(x0, fp)
        pickle.dump(y0, fp)

    gtsrce: List[str] = []
    for i, s in enumerate(stations):
        lab = s.station_id.strip()
        gtsrce.append(f"GTSRCE {lab} XYZ {x_km[i]} {y_km[i]} 0 {elev_km[i]}\n")

    ctl = os.path.join(control_file_path, control_file_name)
    with open(ctl, "w", encoding="utf-8") as fw:
        fw.writelines(part1 + gtsrce + part2)

    _run_grid2time_ps(control_file_path, control_file_name)


def _run_grid2time_ps(control_file_path: str, control_file_name: str) -> None:
    """Run ``Grid2Time`` for both P and S travel-time tables inside one run directory.
    
    Args:
        control_file_path (str): control file path.
        control_file_name (str): control file name.
    """

    script = os.getcwd()
    try:
        os.chdir(control_file_path)
        tdir = "time"
        if os.path.exists(tdir):
            shutil.rmtree(tdir)
        os.mkdir(tdir)
        subprocess.run(["Grid2Time", control_file_name], check=True)

        base, ext = os.path.splitext(control_file_name)
        sname = f"{base}_S{ext}"
        if os.path.exists(sname):
            os.remove(sname)
        with open(control_file_name, "r", encoding="utf-8", errors="replace") as fr:
            rows = fr.readlines()
        for i, row in enumerate(rows):
            if "GTFILES  ./model/layer" in row:
                rows[i] = row[:-2] + "S\n"
        with open(sname, "w", encoding="utf-8") as fw:
            fw.writelines(rows)
        subprocess.run(["Grid2Time", sname], check=True)
        if os.path.exists(sname):
            os.remove(sname)
    finally:
        os.chdir(script)


def load_stations_native_table(path: str) -> List[Station]:
    """Read ``station_id lon lat elev_m`` rows from a whitespace table.
    
    Args:
        path (str): path.
    
    Returns:
        List[Station]: Result returned by the function.
    """

    out: List[Station] = []
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            p = line.split()
            if len(p) < 4:
                continue
            out.append(Station(p[0], float(p[1]), float(p[2]), float(p[3])))
    return out
