"""Write checker_report.json and the diagnostic figures."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

from .checks import Check, Data

REPORT_VERSION = 1
DIMENSIONS = ("reality", "time", "space", "strength")


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def build_report(checks: list[Check], d: Data, inputs: dict[str, Path], config: dict) -> dict:
    flags = [c for c in checks if c.flag]
    return {
        "report_version": REPORT_VERSION,
        "generated_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "inputs": {k: {"path": str(v), "sha256": _sha256(v) if Path(v).is_file() else None} for k, v in inputs.items()},
        "counts": {"events": int(len(d.events)), "located_events": int(d.events[["x", "y"]].notna().all(axis=1).sum()),
                   "associated_picks_at_known_stations": int(len(d.picks)), "stations": int(len(d.stations)),
                   "pick_stations_without_metadata": d.unmatched_stations[:50]},
        "summary": {dim: {"checks": sum(c.dimension == dim for c in checks),
                          "flags": sum(c.dimension == dim and c.flag for c in checks)} for dim in DIMENSIONS},
        "flags": [{"flag_id": f"{c.dimension}.{c.id}", "dimension": c.dimension, "symptom": c.symptom,
                   "measured": c.record()["measured"], "unit": c.unit, "expected": c.expected} for c in flags],
        "checks": [c.record() for c in checks],
        "config": config,
        "note": "Symptoms only: each flag states what was measured and the expected range. It does not name a cause or a repair.",
    }


def _plain(value):
    if isinstance(value, np.generic):
        return value.item()
    if isinstance(value, Path):
        return str(value)
    raise TypeError(f"not JSON serialisable: {type(value)}")


def write_report(report: dict, output_dir: Path) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / "checker_report.json"
    path.write_text(json.dumps(report, indent=1, ensure_ascii=False, default=_plain) + "\n", encoding="utf-8")
    return path


def write_figures(d: Data, extras: dict, output_dir: Path) -> list[str]:
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        return []
    fig, ax = plt.subplots(2, 2, figsize=(11, 9))
    e = d.events
    a = ax[0, 0]
    a.scatter(e.x, e.y, s=2, c="tab:blue", alpha=0.4, label="events")
    a.scatter(d.stations.x, d.stations.y, marker="^", s=30, c="k", label="stations")
    a.set(xlabel="east (km)", ylabel="north (km)", title="Events and stations", aspect="equal")
    a.legend(loc="upper right", fontsize=8)
    a = ax[0, 1]
    z = e.depth_km.dropna()
    if len(z):
        a.hist(z, bins=60, color="tab:blue")
    a.set(xlabel="depth below sea level (km)", ylabel="events", title="Depth distribution")
    a = ax[1, 0]
    p = d.picks[(d.picks.phase == "P") & np.isfinite(d.picks.hyp_km)]
    if len(p):
        sel = p.sample(min(len(p), 20000), random_state=0)
        a.scatter(sel.hyp_km, sel.tt, s=1, alpha=0.3, c="tab:gray")
        fit = extras.get("fit")
        if fit:
            xs = np.linspace(0, float(sel.hyp_km.quantile(0.99)), 50)
            a.plot(xs, fit["intercept_s"] + fit["slowness_s_per_km"] * xs, c="tab:red", label="near-distance fit")
            a.legend(fontsize=8)
    a.set(xlabel="hypocentral distance (km)", ylabel="P pick − origin time (s)", title="P travel times")
    a = ax[1, 1]
    w = extras.get("wadati")
    if w is not None and len(w):
        a.hist(np.clip(w.offset_s, -5, 5), bins=60, color="tab:green")
        a.axvline(0, c="k", lw=0.8)
    a.set(xlabel="Wadati origin − catalog origin (s)", ylabel="events", title="Wadati origin-time difference")
    fig.tight_layout()
    path = output_dir / "checker_diagnostics.png"
    fig.savefig(path, dpi=120)
    plt.close(fig)
    return [path.name]
