#!/usr/bin/env python3
"""Stage 60: Match&Locate detection seeded by the stage-52 working catalog.

Port of the Kaikoura stage 60 (Kilauea / Prague / Maple Creek / Magna PLAN.md r7).
Ridgecrest has no round tree: templates come from the stage-10 v1 baseline
with stage-52 double-difference positions, the union base is the stage-52
working catalog, and references are read through the task evaluation module
(``evaluation/scripts/plot_evaluation_comparison.py``). Scope ``pilot`` scans one day
with a small template set; ``full`` scans the eight-day window. Steps:

1. inputs: greedy spatial cover of the v1 catalog by quality-filtered v1
   events (stage-52 DD positions), associated NLL picks as template marks;
2. seismotools/match_and_locate interface/prepare.py;
3. interface/run.py with permissive thresholds;
4. evaluate: N×MAD sweep of the merged detections on the scanned days,
   scored like stage 05 (references read through its readers and mask) —
   Shelly, Liu, Ross (nbranch > 1) and ComCat at 4 s / 15 km — for M&L alone, the source
   catalog and their union;
5. export: final threshold, union with the source catalog (new events only),
   chained relative magnitudes -> export/<catalog-round>/60_catalog.

Outputs: <export_root>/<scope>[_tag]/{inputs,dataset,run,report.json,summary.md}.
"""
from __future__ import annotations

import argparse
import bisect
import csv
import importlib.util
import json
import math
import subprocess
import sys
import time
from typing import Optional
from datetime import datetime, timedelta, timezone
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

EXPERT = Path(__file__).resolve().parents[1]
CFG = yaml.safe_load((EXPERT / "00_config" / "match_locate.yaml").read_text())
VAL = yaml.safe_load((EXPERT / "00_config" / "validation.yaml").read_text())
MAIN = yaml.safe_load((EXPERT / "00_config" / "config.yaml").read_text())
WINDOW = MAIN["candidate_window"]
TOOL = (EXPERT / CFG["tool_root"]).resolve()
sys.path.insert(0, str(TOOL / "runtime" / "python" / "MatchLocatepy"))
from matchlocate_runner import merge_detections, select_templates  # noqa: E402
from matchlocate_runner.native import Detection  # noqa: E402


def _deep_update(base: dict, extra: dict) -> None:
    for key, value in extra.items():
        if isinstance(value, dict) and isinstance(base.get(key), dict):
            _deep_update(base[key], value)
        else:
            base[key] = value


# ---------------------------------------------------------------- references
def utc(s) -> datetime:
    return pd.Timestamp(s).tz_convert("UTC").to_pydatetime() if pd.Timestamp(s).tzinfo else \
        pd.Timestamp(s).tz_localize("UTC").to_pydatetime()


def in_box(r) -> bool:
    """The evaluation comparison box (validation.yaml = native_comparison_bounds)."""
    return (VAL["latitude_bounds"][0] <= r["latitude"] <= VAL["latitude_bounds"][1] and
            VAL["longitude_bounds"][0] <= r["longitude"] <= VAL["longitude_bounds"][1])


EVAL = None
SCORED = ["shelly", "liu", "ross_relocated", "official_earthquake"]
GATES = (4.0, 15.0)                      # the evaluation matcher's gates


def load_references(days):
    """Masked references from the task evaluation module, on the given days."""
    global EVAL
    if EVAL is None:
        spec = importlib.util.spec_from_file_location(
            "evaluation", EXPERT.parent / "evaluation" / "scripts" / "plot_evaluation_comparison.py")
        EVAL = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(EVAL)
    _, _, published, _ = EVAL.house.load_data(EVAL.CASE)
    in_days = lambda t: any(d <= t < d + timedelta(days=1) for d in days)
    refs = {}
    for p in published:
        if p["key"] in SCORED:
            rows = [{"time": r["time"], "latitude": r["latitude"], "longitude": r["longitude"]} for r in p["rows"]
                    if r["latitude"] is not None and in_days(r["time"])]
            refs[p["key"]] = sorted(rows, key=lambda r: r["time"])
    return refs


def match(rows, ref, dt_max, d_max=None):
    """Greedy one-to-one pairs (i, j): smallest normalized cost first; d_max None = time only."""
    times = [r["time"] for r in ref]
    cand = []
    for i, a in enumerate(rows):
        lo = bisect.bisect_left(times, a["time"] - timedelta(seconds=dt_max))
        hi = bisect.bisect_right(times, a["time"] + timedelta(seconds=dt_max))
        for j in range(lo, hi):
            dt = abs((ref[j]["time"] - a["time"]).total_seconds())
            if d_max is None:
                cand.append((dt / dt_max, i, j))
                continue
            d = math.hypot((a["latitude"] - ref[j]["latitude"]) * 111.195,
                           (a["longitude"] - ref[j]["longitude"]) * 111.195 * math.cos(math.radians(a["latitude"])))
            if d <= d_max:
                cand.append((math.hypot(dt / dt_max, d / d_max), i, j))
    cand.sort()
    used_i, used_j, pairs = set(), set(), []
    for _, i, j in cand:
        if i not in used_i and j not in used_j:
            used_i.add(i), used_j.add(j), pairs.append((i, j))
    return pairs


def score(rows, refs):
    """Stage-05 primary gates per scored reference."""
    dt, dd = GATES
    out = {"events": len(rows)}
    for name, ref in refs.items():
        n = len(match(rows, ref, dt, dd))
        out[f"{name}_matched"], out[f"{name}_recall"] = n, round(n / max(len(ref), 1), 4)
    return out


def base_rows():
    """The stage-52 working catalog (DD positions) in the window."""
    e = pd.read_csv(EXPERT / CFG["source"]["catalog"], low_memory=False)
    w0, w1 = utc(WINDOW["start_utc"]), utc(WINDOW["end_utc"])
    rows = [{"time": utc(r.origin_time), "latitude": r.latitude, "longitude": r.longitude,
             "depth_km": r.depth_below_sea_level_km, "event_id": r.event_id, "location_source": "dd",
             "magnitude": None if pd.isna(r.magnitude) else float(r.magnitude),
             "magnitude_source": "" if pd.isna(r.magnitude) else "source_ml"}
            for r in e.itertuples() if pd.notna(r.latitude)]
    return sorted([r for r in rows if w0 <= r["time"] < w1], key=lambda r: r["time"])


def source_catalog():
    """The union base in the comparison box."""
    return [r for r in base_rows() if in_box(r)]


# -------------------------------------------------------------------- inputs
def build_inputs(out: Path, scope: dict) -> dict:
    src = CFG["source"]
    tcfg = CFG["templates"]
    events = pd.read_csv(EXPERT / src["events"], low_memory=False)
    events = events[events["in_v1_working_catalog"].astype(str).str.lower().isin(["true", "1"])]
    # stage-52 DD positions replace the NLL ones where available
    dd = pd.read_csv(EXPERT / src["catalog"], low_memory=False).set_index("event_id")
    for col in ("latitude", "longitude", "depth_below_sea_level_km", "origin_time"):
        events[col] = events.event_id.map(dd[col]).fillna(events[col]) if col != "origin_time" else \
            events.event_id.map(dd[col]).where(events.event_id.isin(dd.index), events[col])
    rows = [{"event_id": e.event_id, "latitude": float(e.latitude), "longitude": float(e.longitude),
             "depth_km": float(e.depth_below_sea_level_km), "origin": str(e.origin_time),
             "position": "dd" if e.event_id in dd.index else "nll",
             "magnitude": None if pd.isna(e.magnitude) else float(e.magnitude),
             "n_stations": int(e.n_stations), "sigma_z": float(e.posterior_sigma_depth_km)}
            for e in events.itertuples()]
    candidates = [r for r in rows if r["n_stations"] >= tcfg["min_stations"]
                  and r["sigma_z"] <= tcfg["max_sigma_depth_km"]]
    if tcfg.get("require_location_quality"):
        good, _ = location_quality()
        candidates = [r for r in candidates if r["event_id"] in good]
    chosen = select_templates(rows, candidates, radius_km=tcfg["cover_radius_km"],
                              max_templates=scope["max_templates"], rank=lambda r: r["n_stations"])
    templates = chosen["templates"]
    out.mkdir(parents=True, exist_ok=True)
    with (out / "templates.csv").open("w", newline="") as h:
        w = csv.writer(h, lineterminator="\n")
        w.writerow(["event_id", "origin_time_utc", "latitude", "longitude", "depth_km", "magnitude"])
        for t in templates:
            origin = pd.Timestamp(t["origin"]).tz_convert("UTC").strftime("%Y-%m-%dT%H:%M:%S.%fZ")
            w.writerow([t["event_id"], origin, t["latitude"], t["longitude"], t["depth_km"],
                        "" if t["magnitude"] is None else t["magnitude"]])
    chosen_ids = {t["event_id"] for t in templates}
    assoc = pd.read_csv(EXPERT / src["assoc_picks"])
    assoc = assoc[assoc.event_id.isin(chosen_ids) & (assoc.residual_s.abs() <= tcfg["pick_max_abs_residual_s"])]
    picks = pd.read_csv(EXPERT / src["picks"], usecols=["pick_id", "station_id", "time_utc"])
    joined = assoc.merge(picks, on="pick_id", how="inner")
    joined = joined.sort_values("residual_s", key=abs).drop_duplicates(["event_id", "station_id", "phase"])
    joined[["event_id", "station_id", "phase", "time_utc"]].to_csv(out / "picks.csv", index=False, lineterminator="\n")
    stations = pd.read_csv(EXPERT / src["stations"]).drop_duplicates("station_id")
    stations[["station_id", "latitude", "longitude", "elevation_m"]].to_csv(out / "stations.csv", index=False,
                                                                           lineterminator="\n")
    config = {
        "processing": CFG["prepare"]["processing"], "channels": CFG["prepare"]["channels"],
        "window": CFG["window"], "selection": CFG["prepare"]["selection"], "marks": CFG["prepare"]["marks"],
        "segments": {"days": scope["days"]},
        "depth": {"input_reference": "sea_level", "model_datum_elevation_km": CFG["model_datum_elevation_km"]},
        "run": {**CFG["run"], "window": CFG["window"]},
    }
    (out / "prepare_config.json").write_text(json.dumps(config, indent=2) + "\n")
    write_velocity_model(out / "velocity_model.json")
    return {"catalog_events": len(rows), "candidates": len(candidates), "templates": len(templates),
            "covered_fraction": round(chosen["covered_fraction"], 4),
            "templates_with_magnitude": sum(1 for t in templates if t["magnitude"] is not None),
            "picks": int(len(joined))}


def write_velocity_model(path: Path) -> None:
    """Registry model as tool rows; a linear-gradient model is densified into
    constant sublayers at the mid-depth velocity down to ``densify_to_km``
    (default: the last point); deeper rows stay as published layers."""
    vm = CFG["velocity_model"]
    rows = json.loads((EXPERT / vm["registry"]).read_text())["models"][vm["key"]]["rows"]
    if vm.get("layering", "step") == "linear":
        z = np.array([float(r["top_of_layer_km"]) for r in rows])
        vp, vs = (np.array([float(r[k]) for r in rows]) for k in ("vp_km_s", "vs_km_s"))
        bottom = float(vm.get("densify_to_km", z[-1]))
        tops = np.arange(z[0], bottom, float(vm["sublayer_km"]))
        mid = np.minimum(tops + float(vm["sublayer_km"]) / 2, bottom)
        deep = [r for r in rows if float(r["top_of_layer_km"]) >= bottom]
        rows = [{"top_of_layer_km": round(float(t), 4), "vp_km_s": round(float(np.interp(m, z, vp)), 4),
                 "vs_km_s": round(float(np.interp(m, z, vs)), 4)} for t, m in zip(tops, mid)]
        rows += deep or [{"top_of_layer_km": bottom, "vp_km_s": float(np.interp(bottom, z, vp)),
                          "vs_km_s": float(np.interp(bottom, z, vs))}]
    path.write_text(json.dumps({"key": vm["key"], "layering": vm.get("layering", "step"), "rows": rows}, indent=1) + "\n")


def call(cmd, log: Path) -> None:
    with log.open("w") as handle:
        handle.write(" ".join(map(str, cmd)) + "\n")
        handle.flush()
        proc = subprocess.run([str(c) for c in cmd], stdout=handle, stderr=subprocess.STDOUT)
    if proc.returncode != 0:
        raise SystemExit(f"failed ({proc.returncode}): see {log}")


# ---------------------------------------------------------------- detections
def read_detections(out: Path):
    by_segment = {}
    with (out / "run" / "template_detections.csv").open() as handle:
        for r in csv.DictReader(handle):
            by_segment.setdefault(r["segment"], []).append(Detection(
                float(r["time_s"]), float(r["latitude"]), float(r["longitude"]), float(r["depth_km"]),
                float(r["magnitude"]), float(r["cc"]), float(r["nmad"]), r["template_id"]))
    return by_segment


def merged_rows(by_segment, cc, mad, sep):
    rows = []
    for seg in sorted(by_segment):
        ref = datetime.strptime(seg, "%Y%m%d").replace(tzinfo=timezone.utc)
        for d in merge_detections(by_segment[seg], cc, mad, sep):
            rows.append({"time": ref + timedelta(seconds=d.time_s), "latitude": d.latitude, "longitude": d.longitude,
                         "depth_km": d.depth_km, "magnitude": None if math.isnan(d.magnitude) else d.magnitude,
                         "cc": d.cc, "nmad": d.nmad, "template_id": d.template_id})
    return sorted(rows, key=lambda r: r["time"])


def evaluate(out: Path, scope: dict) -> dict:
    days = [datetime.fromisoformat(d).replace(tzinfo=timezone.utc) for d in scope["days"]]
    in_days = lambda t: any(d <= t < d + timedelta(days=1) for d in days)
    refs = load_references(days)
    base = [r for r in source_catalog() if in_days(r["time"])]
    by_segment = read_detections(out)
    sep = float(CFG["run"]["merge"]["min_separation_s"])
    sweep = []
    for mad in CFG["sweep"]["mad"]:
        ml = [r for r in merged_rows(by_segment, 0.0, mad, sep) if in_box(r)]
        new = [ml[i] for i in sorted(set(range(len(ml))) - {i for i, _ in dedupe_pairs(ml, base)})]
        union = sorted(base + new, key=lambda r: r["time"])
        sweep.append({"mad": mad, "ml": score(ml, refs), "new_vs_source": len(new), "union": score(union, refs)})
    return {"days": scope["days"], "reference_events": {k: len(v) for k, v in refs.items()},
            "source_baseline": score(base, refs), "sweep": sweep}


def dedupe_pairs(a_rows, b_rows, dt_max=2.0, d_max=5.0):
    """Same event in two catalogs: tight gates, as in the Magna catalog merge."""
    return match(a_rows, b_rows, dt_max, d_max)


# -------------------------------------------------------------------- export
def chain_magnitudes(out: Path, final_rows: list, window_s: float = 0.5) -> dict:
    """Relative magnitudes for every detection (Magna stage 60 scheme).

    MatchLocate2 writes ``user0 + median log10(amplitude ratio)``; for a
    template without magnitude user0 is -12345, so the log ratio L is
    recovered either way. Templates without ML get M from detections of their
    own event by templates with one (two passes); each final event gets the
    median of M_T + L over all templates that detected it within window_s.
    """
    from matchlocate_runner.native import parse_eventcase
    templates = pd.read_csv(out / "dataset" / "templates.csv")
    mag = {r.template_id: float(r.magnitude) for r in templates.itertuples() if pd.notna(r.magnitude)}
    known0 = set(mag)
    origin = {r.template_id: pd.Timestamp(r.origin_time_utc).tz_convert(None) for r in templates.itertuples()}
    rows = []
    for job in (out / "run" / "jobs").glob("*/*"):
        f = job / "EventCase.out"
        if not f.is_file():
            continue
        ref = pd.Timestamp(datetime.strptime(job.parent.name, "%Y%m%d"))
        for d in parse_eventcase(f, template_id=job.name):
            lr = d.magnitude + 12345.0 if d.magnitude < -1000 else d.magnitude - mag.get(job.name, float("nan"))
            rows.append((ref + pd.Timedelta(seconds=d.time_s), job.name, lr))
    det = pd.DataFrame(rows, columns=["time", "template_id", "log_ratio"]).sort_values("time").reset_index(drop=True)
    times = det.time.to_numpy()
    tol = np.timedelta64(int(window_s * 1e9), "ns")

    def around(t):
        t = np.datetime64(pd.Timestamp(t).tz_convert(None) if pd.Timestamp(t).tzinfo else pd.Timestamp(t))
        return det.iloc[np.searchsorted(times, t - tol):np.searchsorted(times, t + tol, side="right")]

    for _ in range(2):
        for tid in templates.template_id:
            if tid not in mag:
                near = around(origin[tid])
                vals = [mag[t] + lr for t, lr in zip(near.template_id, near.log_ratio) if t != tid and t in mag]
                if vals:
                    mag[tid] = float(np.median(vals))
    result = []
    for r in final_rows:
        near = around(r["time"])
        vals = [mag[t] + lr for t, lr in zip(near.template_id, near.log_ratio) if t in mag and np.isfinite(lr)]
        result.append((float(np.median(vals)) if vals else None, len(vals)))
    return {"per_event": result, "templates_with_ml": len(known0),
            "templates_after_chain": len(mag), "templates_total": int(len(templates))}


def location_quality():
    """Event ids passing ``location_quality`` (internal criteria only: stage-52 CC links, NLL azimuthal gap
    and horizontal sigma), and the failing ids with their reason. None when the block is absent."""
    q = CFG.get("location_quality")
    if not q:
        return None, {}
    ev = pd.read_csv(EXPERT / CFG["source"]["events"], low_memory=False).set_index("event_id")
    links = pd.read_csv(EXPERT / CFG["source"]["catalog"], low_memory=False).set_index("event_id").cc_all_edges
    ids = links.index
    n_links = links.fillna(0)
    gap = ids.map(ev.azimuth_gap_deg).to_numpy(dtype=float)
    sx = ids.map(ev.posterior_sigma_x_km).to_numpy(dtype=float)
    reason = np.where(n_links.to_numpy() < q["min_cc_links"], "no_waveform_neighbours",
             np.where(~(gap <= q["max_gap_deg"]), "azimuthal_gap",
             np.where(~(sx <= q["max_sigma_x_km"]), "horizontal_sigma", "ok")))
    good = set(ids[reason == "ok"])
    return good, {e: r for e, r in zip(ids, reason) if r != "ok"}


def merged_with_close_events(detections, cc: float, mad: float, sep: float, close: Optional[dict]):
    """merged_rows at ``sep``; with ``close`` = {min_separation_s, min_templates}, also keep events that
    only a finer separation resolves (closer than ``sep`` to a stronger detection) when at least
    ``min_templates`` distinct templates detect them within +-0.5 s. At Ridgecrest such additions
    are ~87 % real with >= 3 templates, ~29 % with one (PhaseNet P picks at the template's stations
    vs a +1 s control; PLAN.md stage 60)."""
    base = merged_rows(detections, cc, mad, sep)
    if not close:
        return base, 0
    fine = merged_rows(detections, cc, mad, float(close["min_separation_s"]))
    times, tids = [], []
    for seg, v in detections.items():
        ref = datetime.strptime(seg, "%Y%m%d").replace(tzinfo=timezone.utc).timestamp()
        for d in v:
            if d.nmad >= mad and d.cc >= cc:
                times.append(ref + d.time_s)
                tids.append(d.template_id)
    order = np.argsort(times)
    times, tids = np.asarray(times)[order], np.asarray(tids)[order]
    kept = np.array(sorted(r["time"].timestamp() for r in base))
    extra = []
    for r in fine:
        t = r["time"].timestamp()
        i = np.searchsorted(kept, t)
        if min(abs(kept[i - 1] - t) if i > 0 else 9e9, abs(kept[i] - t) if i < len(kept) else 9e9) <= 0.01:
            continue
        lo, hi = np.searchsorted(times, t - 0.5), np.searchsorted(times, t + 0.5)
        if len(set(tids[lo:hi])) >= int(close["min_templates"]):
            extra.append(r)
    return sorted(base + extra, key=lambda r: r["time"]), len(extra)


def export(out: Path, scope: dict, catalog_round: str) -> dict:
    final = CFG["final"]
    good, failed = location_quality()
    detections = read_detections(out)
    if good is not None:
        # templates failing the rule do not place events; their detections leave the merge
        detections = {seg: [d for d in v if d.template_id in good] for seg, v in detections.items()}
    ml, n_close = merged_with_close_events(detections, float(final["cc_threshold"]), float(final["mad_threshold"]),
                                           float(final["min_separation_s"]), final.get("close_events"))
    chain = chain_magnitudes(out, ml)
    for r, (m, n) in zip(ml, chain["per_event"]):
        r["magnitude_native"], r["magnitude"], r["n_magnitude_templates"] = r["magnitude"], m, n
    w0, w1 = utc(WINDOW["start_utc"]), utc(WINDOW["end_utc"])
    base = base_rows()
    low = [r for r in base if r["event_id"] in failed]
    base = [r for r in base if r["event_id"] not in failed]
    pairs = dedupe_pairs(ml, base)
    for i, j in pairs:
        if base[j]["magnitude"] is None and ml[i]["magnitude"] is not None:
            base[j]["magnitude"], base[j]["magnitude_source"] = ml[i]["magnitude"], "ml_chain"
    in_base = {i for i, _ in pairs}
    new = [{**r, "event_id": f"ml_{k:06d}", "location_source": "ml",
            "magnitude_source": "ml_chain" if r["magnitude"] is not None else ""}
           for k, r in enumerate((r for i, r in enumerate(ml) if i not in in_base), 1)]
    union = sorted(base + new, key=lambda r: r["time"])
    dest = EXPERT / "export" / catalog_round / "60_catalog"
    dest.mkdir(parents=True, exist_ok=True)
    fields = ["event_id", "origin_time_utc", "latitude", "longitude", "depth_bsl_km", "magnitude",
              "magnitude_source", "location_source", "ml_cc", "ml_nmad", "ml_template_id"]
    with (dest / "catalog_events.csv").open("w", newline="") as h:
        w = csv.writer(h, lineterminator="\n")
        w.writerow(fields)
        for r in union:
            w.writerow([r["event_id"], r["time"].isoformat(), r["latitude"], r["longitude"], r["depth_km"],
                        "" if r["magnitude"] is None else round(r["magnitude"], 3), r["magnitude_source"],
                        r["location_source"], r.get("cc", ""), r.get("nmad", ""), r.get("template_id", "")])
    if good is not None:
        # picked events failing the rule, unless an M&L event (from a passing template) took their place
        taken = {j for _, j in dedupe_pairs(ml, low)}
        with (dest / "low_quality_events.csv").open("w", newline="") as h:
            w = csv.writer(h, lineterminator="\n")
            w.writerow(["event_id", "origin_time_utc", "latitude", "longitude", "depth_bsl_km", "reason",
                        "redetected_by_ml"])
            for j, r in enumerate(low):
                w.writerow([r["event_id"], r["time"].isoformat(), r["latitude"], r["longitude"], r["depth_km"],
                            failed[r["event_id"]], j in taken])
    days = [w0 + timedelta(days=k) for k in range((w1 - w0).days)]
    refs = load_references(days)
    boxed = lambda rows: [r for r in rows if in_box(r)]
    return {"final_threshold": final, "location_quality": CFG.get("location_quality"),
            "picked_failing_quality": len(low), "close_events_added": n_close, "ml_events": len(ml), "ml_in_source": len(in_base), "ml_new": len(new),
            "union_events": len(union), "catalog": str(dest.relative_to(EXPERT)),
            "magnitudes": {k: chain[k] for k in ("templates_with_ml", "templates_after_chain", "templates_total")},
            "scores": {"source": score(boxed(base), refs), "ml": score(boxed(ml), refs),
                       "union": score(boxed(union), refs)}}


def summary_md(report: dict) -> str:
    ev = report["evaluation"]
    b = ev["source_baseline"]
    tag = f" [{report['tag']}]" if report.get("tag") else ""
    lines = [f"# Stage 60 Match&Locate — {report['scope']}{tag} ({', '.join(ev['days'])})", "",
             f"Overrides: `{json.dumps(report.get('override') or {})}`", "",
             f"Templates: {report['inputs']['templates']} (cover {report['inputs']['covered_fraction']:.1%} of v1 at "
             f"{CFG['templates']['cover_radius_km']} km); kept by prepare: {report['prepare']['templates_kept']}, "
             f"rows {report['prepare']['rows_kept']}. Native jobs: {report['run']['jobs']}; "
             f"wall {report['timing_s']['run']:.0f} s.", "",
             f"Reference events on these days: {ev['reference_events']}.",
             f"Source catalog: {b['events']} events, " +
             ", ".join(f"{k} {b[k + '_recall']:.1%}" for k in SCORED) + ".", "",
             "| N×MAD | M&L events | " + " | ".join(f"M&L {k}" for k in SCORED) + " | new vs source | union events | " +
             " | ".join(f"union {k}" for k in SCORED) + " |",
             "|" + "---|" * (2 * len(SCORED) + 4)]
    for s in ev["sweep"]:
        m, u = s["ml"], s["union"]
        lines.append(f"| {s['mad']} | {m['events']} | " + " | ".join(f"{m[k + '_recall']:.1%}" for k in SCORED) +
                     f" | {s['new_vs_source']} | {u['events']} | " +
                     " | ".join(f"{u[k + '_recall']:.1%}" for k in SCORED) + " |")
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scope", choices=sorted(CFG["scopes"]), default="pilot")
    parser.add_argument("--stage", choices=["all", "inputs", "prepare", "run", "evaluate", "export"], default="all")
    parser.add_argument("--tag", default="", help="variant name; output goes to <scope>_<tag>")
    parser.add_argument("--catalog-round", default="", help="export step: round that receives 60_catalog (e.g. r6)")
    parser.add_argument("--override", default="{}",
                        help='JSON deep-merged into match_locate.yaml, e.g. \'{"prepare": {"selection": {"max_distance_km": 30}}}\'')
    args = parser.parse_args()
    _deep_update(CFG, json.loads(args.override))
    scope = CFG["scopes"][args.scope]
    out = EXPERT / CFG["export_root"] / (args.scope + (f"_{args.tag}" if args.tag else ""))
    out.mkdir(parents=True, exist_ok=True)
    report_path = out / "report.json"
    report = json.loads(report_path.read_text()) if report_path.is_file() else {}
    report.update({"scope": args.scope, "tag": args.tag, "override": json.loads(args.override), "config": CFG})
    report.setdefault("timing_s", {})
    py = sys.executable
    par = CFG["parallel"]
    steps = ["inputs", "prepare", "run", "evaluate"] if args.stage == "all" else [args.stage]
    for step in steps:
        t0 = time.time()
        if step == "inputs":
            report["inputs"] = build_inputs(out / "inputs", scope)
        elif step == "prepare":
            i = out / "inputs"
            call([py, "-I", TOOL / "interface/prepare.py", "--waveforms", (EXPERT / CFG["waveforms"]).resolve(),
                  "--stations", i / "stations.csv", "--templates", i / "templates.csv", "--picks", i / "picks.csv",
                  "--velocity-model", i / "velocity_model.json", "--config", i / "prepare_config.json",
                  "--output-dir", out / "dataset", "--workers", par["prepare_workers"], "--overwrite", "--quiet"],
                 out / "prepare.log")
            report["prepare"] = json.loads((out / "dataset" / "prepare_result.json").read_text())
        elif step == "run":
            call([py, "-I", TOOL / "interface/run.py", "--input-dir", out / "dataset", "--output-dir", out / "run",
                  "--jobs", par["jobs"], "--threads", par["threads"], "--overwrite", "--quiet"], out / "run.log")
            result = json.loads((out / "run" / "run_result.json").read_text())
            report["run"] = {k: result.get(k) for k in ("status", "jobs", "template_detections", "detections")}
        elif step == "evaluate":
            report["evaluation"] = evaluate(out, scope)
        elif step == "export":
            if not args.catalog_round:
                parser.error("--stage export needs --catalog-round")
            report[f"export_{args.catalog_round}"] = export(out, scope, args.catalog_round)
        report["timing_s"][step] = round(time.time() - t0, 1)
        report_path.write_text(json.dumps(report, indent=2, default=str) + "\n")
        print(f"{step}: done in {report['timing_s'][step]} s", flush=True)
    if "evaluation" in report:
        (out / "summary.md").write_text(summary_md(report))
        print((out / "summary.md").read_text())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
