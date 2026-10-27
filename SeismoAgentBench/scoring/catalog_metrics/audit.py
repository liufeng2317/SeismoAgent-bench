"""Blind audit of unsupported events (docs/framework/03_EVALUATION_METRICS.md §5 L1)."""

from __future__ import annotations

import math
from pathlib import Path

import numpy as np
import pandas as pd

from .tables import Population

AUDIT_SIZE = 50
AUDIT_SEED = 20261027
LABELS = ("earthquake", "not_earthquake", "undecidable")
SAMPLE_FILE = "audit_sample.csv"
LABEL_FILE = "audit_labels.csv"


def sample_unsupported(cand: Population, index: np.ndarray, *, size: int = AUDIT_SIZE,
                       seed: int = AUDIT_SEED) -> pd.DataFrame:
    """Stratified random sample of unsupported events (strata: ``n_picks`` terciles)."""
    events = cand.events.iloc[index].copy()
    picks = events.n_picks
    if picks.notna().sum() >= 3 and picks.nunique() >= 3:
        events["stratum"] = pd.qcut(picks.rank(method="first"), 3, labels=False)
    else:
        events["stratum"] = 0
    events["stratum"] = events["stratum"].fillna(-1).astype(int)
    rng = np.random.default_rng(seed)
    if len(events) <= size:
        chosen = events
    else:
        counts = events.stratum.value_counts().sort_index()
        quota = np.floor(counts / counts.sum() * size).astype(int)
        for stratum in (counts / counts.sum() * size - quota).sort_values(ascending=False).index:
            if quota.sum() >= size:
                break
            quota[stratum] += 1
        parts = [g.iloc[rng.choice(len(g), size=int(quota[s]), replace=False)]
                 for s, g in events.groupby("stratum") if quota[s] > 0]
        chosen = pd.concat(parts)
    chosen = chosen.sort_values("time")
    stamps = pd.to_datetime(chosen.time, unit="s", utc=True)
    return pd.DataFrame({"event_id": chosen.event_id.to_numpy(),
                         "origin_time_utc": stamps.dt.strftime("%Y-%m-%dT%H:%M:%S.%fZ").to_numpy(),
                         "latitude": chosen.latitude.to_numpy(), "longitude": chosen.longitude.to_numpy(),
                         "depth_km": chosen.depth_km.to_numpy(), "n_picks": chosen.n_picks.to_numpy(),
                         "stratum": chosen.stratum.to_numpy(), "label": ""})


def wilson(k: int, n: int, z: float = 1.96) -> tuple[float, float]:
    if n == 0:
        return (0.0, 1.0)
    p = k / n
    centre = (p + z * z / (2 * n)) / (1 + z * z / n)
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / (1 + z * z / n)
    return (max(0.0, centre - half), min(1.0, centre + half))


def audited_false_rate(labels_path: Path, unsupported_fraction: float | None) -> dict | None:
    """``(1 - union_support) x p_false`` from reviewed labels; None until a review exists."""
    if not labels_path.is_file() or unsupported_fraction is None:
        return None
    labels = pd.read_csv(labels_path, dtype=str, keep_default_na=False).label.str.strip().str.lower()
    unknown = sorted(set(labels) - set(LABELS) - {""})
    if unknown:
        raise ValueError(f"{labels_path}: unknown labels {unknown}")
    counts = {name: int((labels == name).sum()) for name in LABELS}
    decided = counts["earthquake"] + counts["not_earthquake"]
    if decided == 0:
        return {"counts": counts, "p_false": None, "rate": None}
    p = counts["not_earthquake"] / decided
    lo, hi = wilson(counts["not_earthquake"], decided)
    return {"counts": counts, "p_false": round(p, 4),
            "rate": round(unsupported_fraction * p, 4),
            "rate_ci95": [round(unsupported_fraction * lo, 4), round(unsupported_fraction * hi, 4)]}
