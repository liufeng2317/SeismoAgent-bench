"""Relocate a sample of the catalog's events with generic velocity models and compare.

The catalog's own picks are relocated with every generic model of ``velocity.py`` (and CRUST1.0 with
the Wadati Vp/Vs of the catalog's own picks) through ``seismotools/nonlinloc/interface/locate.py``.
For each model the median depth and origin-time difference catalog − model are reported, and the
catalog's position relative to the spread of the models: a catalog whose depths or origin times lie
outside the range all generic models span depends on its velocity model more than the plausible
range of models explains. The models are generic; none is assumed correct.
"""

from __future__ import annotations

import json
import math
import os
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd

from .checks import Check, Data, _skip
from .velocity import regional_models, with_vpvs

LOCATE = Path(__file__).resolve().parents[3] / "nonlinloc/interface/locate.py"
ENSEMBLE_DEFAULTS = {"ensemble_events": 100, "ensemble_min_phases": 8, "ensemble_min_s": 2,
                     "ensemble_depth_margin_km": 1.0, "ensemble_time_margin_s": 0.3,
                     "ensemble_outside_share_max": 0.5, "ensemble_workers": 8, "ensemble_timeout_s": 3600}


def _sample(d: Data, c: dict) -> pd.DataFrame:
    p = d.picks
    counts = p.groupby("event_id").phase.agg(n="size", n_s=lambda x: int((x == "S").sum()))
    ok = counts[(counts.n >= c["ensemble_min_phases"]) & (counts.n_s >= c["ensemble_min_s"])]
    ev = d.events[d.events.event_id.isin(ok.index) & d.events[["latitude", "longitude", "depth_km"]].notna().all(axis=1)]
    ev = ev.assign(n=ev.event_id.map(ok.n)).sort_values(["n", "time"], ascending=[False, True])
    return ev.head(c["ensemble_events"])


def _model_rows(rows: list, ref_elev_km: float) -> list[tuple[float, float, float]]:
    """Layer tops relative to the reference elevation; the layer containing it starts at 0."""
    rel = [(z + ref_elev_km, vp, vs) for z, vp, vs in rows]
    above = [r for r in rel if r[0] <= 0]
    below = [r for r in rel if r[0] > 0]
    first = (0.0, *above[-1][1:]) if above else (0.0, *below[0][1:])
    return [first] + below


def _locate(work: Path, name: str, rows: list, ref_elev: float, depth_bottom: float, c: dict) -> pd.DataFrame | None:
    out = work / name
    (work / f"{name}_model.txt").write_text("".join(f"{z:.3f} {vp:.3f} {vs:.3f}\n" for z, vp, vs in _model_rows(rows, ref_elev)))
    config = {"reference_elevation_km": ref_elev, "velocity_layering": "step",
              "region": None, "grid_depth_km": [-1.0, depth_bottom + 10.0]}
    config = {k: v for k, v in config.items() if v is not None}
    (work / f"{name}_config.json").write_text(json.dumps(config))
    cmd = [sys.executable, "-I", str(LOCATE), "--arrivals", str(work / "arrivals.csv"), "--stations", str(work / "stations.csv"),
           "--velocity-model", str(work / f"{name}_model.txt"), "--config", str(work / f"{name}_config.json"),
           "--output-dir", str(out), "--workers", str(c["ensemble_workers"]), "--quiet", "--overwrite"]
    try:
        subprocess.run(cmd, check=False, capture_output=True, timeout=c["ensemble_timeout_s"])
    except subprocess.TimeoutExpired:
        return None
    if not (out / "events.csv").is_file():
        return None
    ev = pd.read_csv(out / "events.csv")
    ev = ev[ev.status == "LOCATED"].copy()
    ev["depth_bsl"] = ev.depth_km - ref_elev
    ev["t"] = (pd.to_datetime(ev.origin_time_utc, utc=True, format="ISO8601") - pd.Timestamp(0, tz="UTC")).dt.total_seconds()
    return ev[["event_id", "depth_bsl", "t", "latitude", "longitude", "rms_s"]]


def model_ensemble(d: Data, config: dict, vpvs: float | None, workdir: Path | None = None) -> tuple[list[Check], dict]:
    c = {**ENSEMBLE_DEFAULTS, **config}
    exp_z = f"catalog depth inside the range of generic-model relocations ± {c['ensemble_depth_margin_km']} km for ≥ {1 - c['ensemble_outside_share_max']:.0%} of sampled events"
    exp_t = f"catalog origin time inside the range of generic-model relocations ± {c['ensemble_time_margin_s']} s for ≥ {1 - c['ensemble_outside_share_max']:.0%} of sampled events"
    sample = _sample(d, c)
    if len(sample) < 20:
        why = f"{len(sample)} events with ≥ {c['ensemble_min_phases']} phases and ≥ {c['ensemble_min_s']} S picks"
        return [_skip("model_ensemble_depth", "space", "share", exp_z, len(sample), why),
                _skip("model_ensemble_time", "time", "share", exp_t, len(sample), why)], {}
    models = regional_models(np.r_[d.stations.latitude, sample.latitude.median()], np.r_[d.stations.longitude, sample.longitude.median()])
    if vpvs and 1.5 <= vpvs <= 2.1:
        models["crust1_wadati_vpvs"] = {"rows": with_vpvs(models["crust1"]["rows"], vpvs),
                                        "source": f"CRUST1.0 with the catalog's Wadati Vp/Vs {vpvs:.2f}", "columns": None}
    ref_elev = math.ceil(float(d.stations.elevation_m.max()) / 100.0) / 10.0
    depth_bottom = max(30.0, float(np.nanpercentile(d.events.depth_km, 95)) * 1.5)
    tmp = tempfile.TemporaryDirectory(prefix="checker-ensemble-") if workdir is None else None
    work = Path(tmp.name) if tmp else Path(workdir)
    work.mkdir(parents=True, exist_ok=True)
    picks = d.picks[d.picks.event_id.isin(sample.event_id)].drop_duplicates(["event_id", "station_id", "phase"])
    pd.DataFrame({"event_id": picks.event_id, "pick_id": np.arange(len(picks)).astype(str), "station_id": picks.station_id,
                  "phase": picks.phase, "time_utc": pd.to_datetime(picks.time, unit="s", utc=True).dt.strftime("%Y-%m-%dT%H:%M:%S.%fZ")}
                 ).to_csv(work / "arrivals.csv", index=False)
    d.stations[["station_id", "latitude", "longitude", "elevation_m"]].to_csv(work / "stations.csv", index=False)
    per_model, located = {}, {}
    for name, m in models.items():
        ev = _locate(work, name, m["rows"], ref_elev, depth_bottom, c)
        if ev is None or not len(ev):
            per_model[name] = {"located": 0, "source": m["source"]}
            continue
        j = sample.merge(ev, on="event_id")
        located[name] = j.set_index("event_id")
        per_model[name] = {"source": m["source"], "located": int(len(j)),
                           "median_depth_catalog_minus_model_km": round(float(np.median(j.depth_km - j.depth_bsl)), 3),
                           "median_origin_catalog_minus_model_s": round(float(np.median(j.time - j.t)), 3),
                           "median_rms_s": round(float(np.median(j.rms_s)), 3),
                           "model": [list(r) for r in m["rows"] if r[0] <= 50]}
    if tmp:
        tmp.cleanup()
    if len(located) < 3:
        why = f"only {len(located)} generic models produced locations"
        return [_skip("model_ensemble_depth", "space", "share", exp_z, len(sample), why),
                _skip("model_ensemble_time", "time", "share", exp_t, len(sample), why)], {"models": per_model}
    common = sorted(set.intersection(*[set(v.index) for v in located.values()]))
    zs = np.array([[located[m].loc[e, "depth_bsl"] for m in located] for e in common])
    ts = np.array([[located[m].loc[e, "t"] for m in located] for e in common])
    cat = sample.set_index("event_id").loc[common]
    excess_z = np.maximum(cat.depth_km.to_numpy() - zs.max(axis=1), 0) - np.maximum(zs.min(axis=1) - cat.depth_km.to_numpy(), 0)
    excess_t = np.maximum(cat.time.to_numpy() - ts.max(axis=1), 0) - np.maximum(ts.min(axis=1) - cat.time.to_numpy(), 0)
    out_z = float((np.abs(excess_z) > c["ensemble_depth_margin_km"]).mean())
    out_t = float((np.abs(excess_t) > c["ensemble_time_margin_s"]).mean())
    med_z, med_t = float(np.median(excess_z)), float(np.median(excess_t))
    fz, ft = out_z > c["ensemble_outside_share_max"], out_t > c["ensemble_outside_share_max"]
    names = ", ".join(located)
    checks = [
        Check("model_ensemble_depth", "space", out_z, "share", exp_z, len(common), fz,
              (f"For {out_z:.0%} of {len(common)} relocated events the catalog depth lies more than {c['ensemble_depth_margin_km']} km "
               f"{'below' if med_z > 0 else 'above'} every relocation with the generic models ({names}); median excess {med_z:+.2f} km.") if fz else None,
              {"median_excess_km": round(med_z, 3), "models_spread_km_median": round(float(np.median(zs.max(axis=1) - zs.min(axis=1))), 3)}),
        Check("model_ensemble_time", "time", out_t, "share", exp_t, len(common), ft,
              (f"For {out_t:.0%} of {len(common)} relocated events the catalog origin time lies more than {c['ensemble_time_margin_s']} s "
               f"{'after' if med_t > 0 else 'before'} every relocation with the generic models ({names}); median excess {med_t:+.2f} s.") if ft else None,
              {"median_excess_s": round(med_t, 3), "models_spread_s_median": round(float(np.median(ts.max(axis=1) - ts.min(axis=1))), 3)}),
    ]
    figure = {"catalog_depth": cat.depth_km.to_numpy(), "catalog_time": cat.time.to_numpy(),
              "models": {m: {"depth": zs[:, i], "time": ts[:, i]} for i, m in enumerate(located)}}
    return checks, {"models": per_model, "reference_elevation_km": ref_elev, "sampled_events": int(len(sample)),
                    "common_events": len(common), "_figure": figure}
