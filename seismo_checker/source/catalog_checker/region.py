"""The region a catalog can be trusted in: the station coverage, and a region given by the user.

The station coverage is the convex hull of the stations, widened by a buffer. Outside it the network
sees an event from one side only, and locations, above all distances and depths, are poorly
constrained. A region given by the user (for example in the task) is kept as given; events outside it
are not wrong, but they are outside what was asked for.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from .io import local_km

REGION_DEFAULTS = {"coverage_buffer_km": 10.0}


def station_coverage(stations: pd.DataFrame, buffer_km: float = REGION_DEFAULTS["coverage_buffer_km"]) -> dict:
    """Convex hull of the stations (lat/lon and km about the network centre), the buffer and the aperture."""
    from scipy.spatial import ConvexHull
    st = stations.dropna(subset=["latitude", "longitude"])
    lat0, lon0 = float(st.latitude.median()), float(st.longitude.median())
    x, y = local_km(st.latitude, st.longitude, lat0, lon0)
    xy = np.c_[x, y]
    if len(xy) < 3:
        raise ValueError("station coverage needs at least three stations")
    v = ConvexHull(xy).vertices
    aperture = float(np.max(np.hypot(xy[:, None, 0] - xy[None, :, 0], xy[:, None, 1] - xy[None, :, 1])))
    return {"stations": int(len(st)), "centre": [lat0, lon0], "buffer_km": float(buffer_km),
            "aperture_km": round(aperture, 2),
            "hull": [[round(float(la), 5), round(float(lo), 5)] for la, lo in zip(st.latitude.to_numpy()[v], st.longitude.to_numpy()[v])],
            "hull_km": [[round(float(a), 3), round(float(b), 3)] for a, b in xy[v]]}


def km_outside_coverage(lat, lon, cov: dict) -> np.ndarray:
    """Distance (km) of each epicentre outside the station hull: 0 inside, NaN without a position."""
    from shapely.geometry import Point, Polygon
    hull = Polygon(cov["hull_km"])
    x, y = local_km(lat, lon, *cov["centre"])
    return np.array([hull.exterior.distance(Point(a, b)) * (not hull.contains(Point(a, b)))
                     if np.isfinite(a) and np.isfinite(b) else np.nan for a, b in zip(x, y)])


def classify(events: pd.DataFrame, cov: dict, region: dict | None = None) -> pd.DataFrame:
    """Per event: km outside the station hull, inside the coverage (hull + buffer), inside the given region."""
    out = pd.DataFrame({"event_id": events.event_id.to_numpy()})
    dist = km_outside_coverage(events.latitude, events.longitude, cov)
    out["km_outside_station_hull"] = np.round(dist, 2)
    out["inside_station_coverage"] = pd.array([None if not np.isfinite(v) else bool(v <= cov["buffer_km"]) for v in dist],
                                              dtype="boolean")
    if region is not None:
        lat, lon = events.latitude.to_numpy(dtype=float), events.longitude.to_numpy(dtype=float)
        inside = ((lat >= region["latitude"][0]) & (lat <= region["latitude"][1])
                  & (lon >= region["longitude"][0]) & (lon <= region["longitude"][1]))
        known = np.isfinite(lat) & np.isfinite(lon)
        out["inside_given_region"] = pd.array([bool(i) if k else None for i, k in zip(inside, known)], dtype="boolean")
    return out
