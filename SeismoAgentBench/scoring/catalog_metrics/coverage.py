"""Station coverage of a case: the convex hull of the supplied stations, widened by a buffer.

Events outside it lie beyond the network, where locations are poorly constrained; on recorded runs
almost none of them belong to the sequence (research doc 04 §10.8). The ``inside_region`` criterion
judges the share of located events outside the coverage; the share outside the scoring mask, which also
counts real regional events inside the network, is reported only. The coverage is computed once per
case from the StationXML under the input's ``stations/`` folder and cached in ``evaluation/``.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np

COVERAGE_FILE = "station_coverage.json"
BUFFER_KM = 10.0
KM_PER_DEG = 111.195


def _station_positions(task_dir: Path) -> list[tuple[str, float, float]]:
    from obspy import read_inventory
    manifest = json.loads((task_dir / "input.json").read_text(encoding="utf-8"))
    root = next(Path(e["path"]) for e in manifest["entries"] if e["id"] == "waveform_data_root")
    seen: dict[str, list[tuple[float, float]]] = {}
    for f in sorted((root / "stations").rglob("*")):
        if f.suffix.lower() not in (".xml", ".stationxml"):
            continue
        for net in read_inventory(str(f)):
            for sta in net:
                seen.setdefault(f"{net.code}.{sta.code}", []).append((sta.latitude, sta.longitude))
    return [(k, float(np.median([p[0] for p in v])), float(np.median([p[1] for p in v]))) for k, v in sorted(seen.items())]


def station_coverage(task_dir: Path) -> dict:
    path = task_dir / "evaluation" / COVERAGE_FILE
    if path.is_file():
        return json.loads(path.read_text(encoding="utf-8"))
    from scipy.spatial import ConvexHull
    stations = _station_positions(task_dir)
    lat0 = float(np.mean([s[1] for s in stations]))
    lon0 = float(np.mean([s[2] for s in stations]))
    xy = np.array([_local(s[1], s[2], lat0, lon0) for s in stations])
    hull = xy[ConvexHull(xy).vertices]
    cov = {"stations": len(stations), "centre": [lat0, lon0], "buffer_km": BUFFER_KM,
           "hull_km": [[round(float(x), 3), round(float(y), 3)] for x, y in hull],
           "note": "convex hull of the supplied stations in km east/north of centre; events farther than buffer_km "
                   "outside it count as outside the station coverage"}
    path.write_text(json.dumps(cov, indent=1) + "\n", encoding="utf-8")
    return cov


def _local(lat, lon, lat0, lon0):
    return ((np.asarray(lon, dtype=float) - lon0) * KM_PER_DEG * np.cos(np.radians(lat0)),
            (np.asarray(lat, dtype=float) - lat0) * KM_PER_DEG)


def outside_coverage(lat, lon, cov: dict) -> np.ndarray:
    """True where an epicentre lies more than the buffer outside the station hull (NaN positions: False)."""
    from shapely.geometry import Point, Polygon
    area = Polygon(cov["hull_km"]).buffer(cov["buffer_km"])
    x, y = _local(lat, lon, *cov["centre"])
    return np.array([bool(np.isfinite(a) and np.isfinite(b) and not area.contains(Point(a, b))) for a, b in zip(x, y)])
