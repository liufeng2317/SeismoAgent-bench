"""Standard event tables and the cohort mask (docs/framework/02_Catalog_Metrics.md §1)."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Mapping

import numpy as np
import pandas as pd

KM_PER_DEG = 111.195
UNCERTAINTY_COLUMNS = ("horizontal_uncertainty_km", "depth_uncertainty_km", "origin_time_uncertainty_s")
NUMERIC_COLUMNS = ("latitude", "longitude", "depth_km", "magnitude", "n_picks") + UNCERTAINTY_COLUMNS
STANDARD_COLUMNS = ("event_id", "time") + NUMERIC_COLUMNS + ("magnitude_type", "status")
ROLES = frozenset("DLSMP")


@dataclass
class Population:
    """One catalog prepared for scoring.

    ``events`` holds the standard columns sorted by ``time`` (float seconds
    since the Unix epoch, UTC); ``depth_km`` is below sea level when
    ``depth_known`` and is otherwise ignored by every depth metric.
    """

    key: str
    events: pd.DataFrame
    roles: frozenset = frozenset()
    depth_known: bool = True
    time_only: bool = False
    gates: tuple | None = None  # reference-specific gates (coarse origin times)
    primary_gates: tuple | None = None  # the case's primary gates when this population is the reference side
    notes: dict = field(default_factory=dict)

    @property
    def located(self) -> np.ndarray:
        e = self.events
        return np.isfinite(e.latitude.to_numpy()) & np.isfinite(e.longitude.to_numpy())


def epoch_seconds(values: Any) -> np.ndarray:
    """ISO 8601 strings or datetimes to float UTC epoch seconds (NaN where unparseable)."""
    series = pd.Series(values)
    if pd.api.types.is_datetime64_any_dtype(series):
        stamps = series.dt.tz_localize("UTC") if series.dt.tz is None else series.dt.tz_convert("UTC")
    else:
        text = series.astype(str).str.strip().str.replace(" ", "T", regex=False)
        # pandas rejects more than nine fractional digits; keep microseconds.
        text = text.str.replace(r"(\.\d{6})\d+", r"\1", regex=True)
        stamps = pd.to_datetime(text, utc=True, errors="coerce", format="ISO8601")
    seconds = (stamps - pd.Timestamp(0, tz="UTC")).dt.total_seconds()
    return seconds.to_numpy(dtype=float)


def standardize(frame: pd.DataFrame, *, depth_offset_km: float = 0.0) -> pd.DataFrame:
    """Copy ``frame`` into the standard columns.

    ``frame`` needs ``time`` (string or datetime) and may carry any other
    standard column. ``depth_offset_km`` is added to ``depth_km`` to reach
    the sea-level datum (e.g. minus the surface elevation for depths below
    the surface).
    """
    out = pd.DataFrame(index=range(len(frame)))
    src = frame.reset_index(drop=True)
    out["event_id"] = src["event_id"].astype(str) if "event_id" in src else [str(i) for i in range(len(src))]
    out["time"] = epoch_seconds(src["time"])
    for column in NUMERIC_COLUMNS:
        out[column] = pd.to_numeric(src[column], errors="coerce") if column in src else np.nan
        out[column] = out[column].where(np.isfinite(out[column]))
    out["depth_km"] = out["depth_km"] + depth_offset_km
    out["magnitude_type"] = src["magnitude_type"].fillna("").astype(str) if "magnitude_type" in src else ""
    out["status"] = src["status"].fillna("").astype(str).str.strip().str.lower() if "status" in src else ""
    return out.sort_values("time", kind="mergesort").reset_index(drop=True)


def read_candidate_catalog(path: str | Path) -> tuple[pd.DataFrame, dict]:
    """Read an Agent ``catalog.csv``; drop rejected and time-less rows (§1)."""
    raw = pd.read_csv(path, dtype=str, keep_default_na=False)
    if "origin_time_utc" not in raw:
        raise ValueError(f"{path}: no origin_time_utc column")
    frame = raw.rename(columns={"origin_time_utc": "time"}).replace({"": np.nan})
    events = standardize(frame)
    rejected = events.status.eq("rejected").to_numpy()
    timeless = ~np.isfinite(events.time.to_numpy())
    notes = {"rows": int(len(events)), "rejected": int(rejected.sum()),
             "unparseable_time": int((timeless & ~rejected).sum()),
             "accepted": int(events.status.eq("accepted").sum()),
             "uncertain": int(events.status.eq("uncertain").sum())}
    keep = ~rejected & ~timeless
    return events[keep].reset_index(drop=True), notes


def in_mask(events: pd.DataFrame, mask: Mapping[str, Any], *, depth_known: bool = True) -> np.ndarray:
    """Cohort mask: half-open window always; box where located; depth where known (§1)."""
    t = events.time.to_numpy()
    inside = (t >= mask["start"]) & (t < mask["end"])
    lat, lon = events.latitude.to_numpy(), events.longitude.to_numpy()
    located = np.isfinite(lat) & np.isfinite(lon)
    box = ((lat >= mask["latitude"][0]) & (lat <= mask["latitude"][1])
           & (lon >= mask["longitude"][0]) & (lon <= mask["longitude"][1]))
    inside &= ~located | box
    if depth_known:
        z = events.depth_km.to_numpy()
        inside &= ~np.isfinite(z) | ((z >= mask["depth_bsl_km"][0]) & (z <= mask["depth_bsl_km"][1]))
    return inside


def local_xyz(events: pd.DataFrame, center: tuple[float, float]) -> np.ndarray:
    """Equirectangular km about ``center`` (lon, lat); depth (km) as the third axis."""
    lon0, lat0 = center
    x = (events.longitude.to_numpy() - lon0) * KM_PER_DEG * np.cos(np.radians(lat0))
    y = (events.latitude.to_numpy() - lat0) * KM_PER_DEG
    return np.column_stack([x, y, events.depth_km.to_numpy()])
