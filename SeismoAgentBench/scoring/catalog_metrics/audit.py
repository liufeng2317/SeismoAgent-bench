"""Blind audit of unsupported events (docs/framework/02_Catalog_Metrics.md §5 L1)."""

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


REVIEW_DIR = "audit"
SPOT_CHECK_SIZE = 10


def prepare_review(run_dir: Path, task_dir: Path, *, seed: int = AUDIT_SEED) -> dict:
    """Anonymised review package for a run's audit sample (evaluation/audit/).

    plots/aNN.png show each sampled event with the run's own catalog as context
    (no reference catalog); key.csv maps aNN to event ids and is not opened
    before labelling; labels.csv (all) and spot_check.csv (a random subset for
    a second reviewer) are templates with an empty label column.
    """
    from .audit_plots import input_root, plot_event  # matplotlib/obspy only when reviewing

    ev_dir = run_dir / "evaluation"
    out = ev_dir / REVIEW_DIR
    if (out / "labels.csv").is_file() and pd.read_csv(out / "labels.csv", dtype=str,
                                                       keep_default_na=False).label.str.strip().ne("").any():
        raise ValueError(f"{out}/labels.csv already holds labels; the review is never redrawn")
    sample = pd.read_csv(ev_dir / SAMPLE_FILE)
    rng = np.random.default_rng(seed)
    order = rng.permutation(len(sample))
    key = pd.DataFrame({"audit_id": [f"a{i + 1:02d}" for i in range(len(sample))],
                        "event_id": sample.event_id.to_numpy()[order].astype(str)})
    catalog = pd.read_csv(run_dir / "work" / "catalog.csv", dtype=str, keep_default_na=False)
    context = catalog.rename(columns={"origin_time_utc": "origin_time_utc"})[
        ["event_id", "origin_time_utc", "latitude", "longitude", "depth_km", "magnitude"]].replace({"": np.nan})
    for column in ("latitude", "longitude", "depth_km", "magnitude"):
        context[column] = pd.to_numeric(context[column], errors="coerce")
    context = context.dropna(subset=["origin_time_utc", "latitude", "longitude"])
    root = input_root(task_dir)
    rows = sample.set_index(sample.event_id.astype(str))
    drawn = 0
    for audit_id, event_id in zip(key.audit_id, key.event_id):
        r = rows.loc[event_id]
        event = {"event_id": audit_id, "source_id": event_id, "origin_time_utc": r.origin_time_utc,
                 "latitude": r.latitude, "longitude": r.longitude, "depth_km": r.depth_km, "magnitude": None}
        drawn += bool(plot_event(root, event, context, out / "plots" / f"{audit_id}.png"))
    key.to_csv(out / "key.csv", index=False)
    pd.DataFrame({"audit_id": key.audit_id, "label": ""}).to_csv(out / "labels.csv", index=False)
    spot = rng.choice(key.audit_id, size=min(SPOT_CHECK_SIZE, len(key)), replace=False)
    pd.DataFrame({"audit_id": sorted(spot), "label": ""}).to_csv(out / "spot_check.csv", index=False)
    return {"events": int(len(key)), "plots": drawn, "dir": str(out)}


def _labels(path: Path) -> pd.Series | None:
    if not path.is_file():
        return None
    table = pd.read_csv(path, dtype=str, keep_default_na=False)
    labels = table.set_index("audit_id").label.str.strip().str.lower()
    unknown = sorted(set(labels) - set(LABELS) - {""})
    if unknown:
        raise ValueError(f"{path}: unknown labels {unknown}")
    return labels


def wilson(k: int, n: int, z: float = 1.96) -> tuple[float, float]:
    if n == 0:
        return (0.0, 1.0)
    p = k / n
    centre = (p + z * z / (2 * n)) / (1 + z * z / n)
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / (1 + z * z / n)
    return (max(0.0, centre - half), min(1.0, centre + half))


def audited_false_rate(review_dir: Path, unsupported_fraction: float | None) -> dict | None:
    """``(1 - union_support) x p_false`` from a completed review; None until every sample is labelled."""
    labels = _labels(review_dir / "labels.csv")
    if labels is None or unsupported_fraction is None or labels.eq("").any():
        return None
    counts = {name: int((labels == name).sum()) for name in LABELS}
    decided = counts["earthquake"] + counts["not_earthquake"]
    out = {"counts": counts, "p_false": None, "rate": None}
    if decided:
        p = counts["not_earthquake"] / decided
        lo, hi = wilson(counts["not_earthquake"], decided)
        out.update({"p_false": round(p, 4), "rate": round(unsupported_fraction * p, 4),
                    "rate_ci95": [round(unsupported_fraction * lo, 4), round(unsupported_fraction * hi, 4)]})
    spot = _labels(review_dir / "spot_check.csv")
    if spot is not None and not spot.eq("").any():
        both = spot.index.intersection(labels.index)
        out["spot_check"] = {"events": int(len(both)),
                             "agreement": round(float((spot[both] == labels[both]).mean()), 4) if len(both) else None}
    return out
