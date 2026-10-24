#!/usr/bin/env python3
"""Stage 60: Match&Locate detection seeded by the r6 catalog.

Scope ``pilot`` scans one day with a small template set to choose thresholds;
``full`` scans the eight-day window. Steps:

1. templates: greedy spatial cover of the r6 v1 catalog by quality-filtered
   v1 events (DD positions where relocated), picks from stages 02/04 as marks;
2. common inputs -> seismotools/match_and_locate interface/prepare.py;
3. interface/run.py with permissive thresholds;
4. offline merge-threshold sweep scored against the masked references
   (evaluation matcher, 4 s / 15 km) for the scanned days, with the r6 catalog
   of the same days as baseline and the r6 + M&L union.

Outputs: export/r7/60_match_locate/<scope>/{inputs,dataset,run,report.json,summary.md}.
"""
from __future__ import annotations

import argparse
import csv
import importlib.util
import json
import math
import subprocess
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

EXPERT = Path(__file__).resolve().parents[1]
CFG = yaml.safe_load((EXPERT / "00_config" / "match_locate.yaml").read_text())
TOOL = (EXPERT / CFG["tool_root"]).resolve()
sys.path.insert(0, str(TOOL / "runtime" / "python" / "MatchLocatepy"))
from matchlocate_runner import merge_detections, select_templates  # noqa: E402
from matchlocate_runner.native import Detection  # noqa: E402


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _deep_update(base: dict, extra: dict) -> None:
    for key, value in extra.items():
        if isinstance(value, dict) and isinstance(base.get(key), dict):
            _deep_update(base[key], value)
        else:
            base[key] = value


def build_inputs(out: Path, scope: dict) -> dict:
    src = EXPERT / CFG["source_export"]
    tcfg = CFG["templates"]
    events = pd.read_csv(src / "10_validate_catalog" / "events.csv", low_memory=False)
    events = events[events["in_v1_working_catalog"].astype(str).str.lower().isin(["true", "1"])].copy()
    dd = pd.read_csv(src / "52_double_difference" / "relocated_events.csv")
    dd = dd.set_index("event_id")
    rows = []
    for _, e in events.iterrows():
        if e.event_id in dd.index and pd.notna(dd.at[e.event_id, "latitude_dd"]):
            r = dd.loc[e.event_id]
            lat, lon, depth, origin, source = (r.latitude_dd, r.longitude_dd, r.dd_depth_below_sea_level_km,
                                               r.origin_time_dd, "dd")
        else:
            lat, lon, depth, origin, source = (e.latitude, e.longitude, e.depth_below_sea_level_km,
                                               e.origin_time, "nll")
        rows.append({"event_id": e.event_id, "latitude": float(lat), "longitude": float(lon),
                     "depth_km": float(depth), "origin": str(origin), "position": source,
                     "magnitude": None if pd.isna(e.magnitude) else float(e.magnitude),
                     "n_stations": int(e.n_stations), "sigma_z": float(e.posterior_sigma_depth_km)})
    candidates = [r for r in rows if r["n_stations"] >= tcfg["min_stations"]
                  and r["sigma_z"] <= tcfg["max_sigma_depth_km"]]
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

    # template picks: stage-04 association (event, pick, residual) x stage-02 pick times
    chosen_ids = {t["event_id"] for t in templates}
    assoc = pd.read_csv(src / "04_locate_nonlinloc" / "full" / "picks.csv")
    assoc = assoc[assoc.event_id.isin(chosen_ids) & (assoc.residual_s.abs() <= tcfg["pick_max_abs_residual_s"])]
    picks = pd.read_csv(src / "02_pick_phasenet" / "full" / "picks.csv", usecols=["pick_id", "station_id", "time_utc"])
    joined = assoc.merge(picks, on="pick_id", how="inner")
    joined = joined.sort_values("residual_s", key=abs).drop_duplicates(["event_id", "station_id", "phase"])
    joined[["event_id", "station_id", "phase", "time_utc"]].to_csv(out / "picks.csv", index=False, lineterminator="\n")

    stations = pd.read_csv(src / "04_locate_nonlinloc" / "stations.csv").drop_duplicates("station_id")
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
    return {"catalog_events": len(rows), "candidates": len(candidates), "templates": len(templates),
            "covered_fraction": round(chosen["covered_fraction"], 4),
            "template_positions": {k: sum(1 for t in templates if t["position"] == k) for k in ("dd", "nll")},
            "templates_with_magnitude": sum(1 for t in templates if t["magnitude"] is not None),
            "picks": int(len(joined))}


def call(cmd, log: Path) -> None:
    with log.open("w") as handle:
        handle.write(" ".join(map(str, cmd)) + "\n")
        handle.flush()
        proc = subprocess.run([str(c) for c in cmd], stdout=handle, stderr=subprocess.STDOUT)
    if proc.returncode != 0:
        raise SystemExit(f"failed ({proc.returncode}): see {log}")


def detections_rows(dets, reference):
    return [{"time": reference + timedelta(seconds=d.time_s), "latitude": d.latitude, "longitude": d.longitude,
             "depth_km": d.depth_km, "magnitude": None if math.isnan(d.magnitude) else d.magnitude}
            for d in dets]


def evaluate(out: Path, scope: dict) -> dict:
    comparison = _load("evaluation_comparison", EXPERT.parent / "evaluation" / "scripts" / "plot_evaluation_comparison.py")
    days = [datetime.fromisoformat(d).replace(tzinfo=timezone.utc) for d in scope["days"]]
    in_days = lambda t: any(d <= t < d + timedelta(days=1) for d in days)
    refs, _ = comparison.load_references()
    refs = {r["key"]: comparison.as_record(r["key"], r["label"], r["color"],
                                           [x for x in r["rows"] if in_days(x["time"])]) for r in refs}
    expert, _ = comparison.load_expert("r6")
    r6_rows = [x for x in expert["rows"] if in_days(x["time"]) and comparison._mask_row(x)]
    r6 = comparison.as_record("expert", "r6", "k", r6_rows)

    # per-template detections (depth_km is below sea level) -> sweep of the merge
    tdets = []
    with (out / "run" / "template_detections.csv").open() as handle:
        for r in csv.DictReader(handle):
            tdets.append((r["segment"], Detection(float(r["time_s"]), float(r["latitude"]), float(r["longitude"]),
                                                  float(r["depth_km"]), float(r["magnitude"]), float(r["cc"]),
                                                  float(r["nmad"]), r["template_id"])))
    references = {s: datetime.strptime(s, "%Y%m%d").replace(tzinfo=timezone.utc) for s in {s for s, _ in tdets}}

    def score(rec):
        res = {}
        for name in ("pang", "baker", "uuss"):
            pairs = comparison.match(rec, refs[name])
            res[name] = {"matched": len(pairs), "recall": round(len(pairs) / max(len(refs[name]["rows"]), 1), 4)}
        res["matched_any_reference_fraction"] = round(
            len({i for name in ("pang", "baker", "uuss") for i, *_ in comparison.match(rec, refs[name])})
            / max(len(rec["rows"]), 1), 4)
        return res

    r6_pang = {j for _, j, *_ in comparison.match(r6, refs["pang"])}
    baseline = {"events": len(r6_rows), **score(r6)}
    sweep = []
    sep = float(CFG["run"]["merge"]["min_separation_s"])
    for mad in CFG["sweep"]["mad"]:
        for cc in CFG["sweep"]["cc"]:
            rows = []
            for seg in sorted(references):
                merged = merge_detections([d for s, d in tdets if s == seg], cc, mad, sep)
                rows += [x for x in detections_rows(merged, references[seg]) if comparison._mask_row(x)]
            rows.sort(key=lambda x: x["time"])
            rec = comparison.as_record("ml", "M&L", "k", rows)
            s = score(rec)
            ml_pang = {j for _, j, *_ in comparison.match(rec, refs["pang"])}
            new_vs_r6 = len(rows) - len(comparison.match(rec, r6))
            sweep.append({"mad": mad, "cc": cc, "events": len(rows), **s,
                          "new_vs_r6": new_vs_r6,
                          "pang_union_recall": round(len(r6_pang | ml_pang) / max(len(refs["pang"]["rows"]), 1), 4),
                          "pang_recovered_beyond_r6": len(ml_pang - r6_pang)})
    return {"days": scope["days"], "reference_events": {k: len(v["rows"]) for k, v in refs.items()},
            "r6_baseline": baseline, "sweep": sweep}


def _dedupe_pairs(a_rows, b_rows, dt_max=2.0, d_max=5.0):
    """Greedy one-to-one (distance, dt) pairing with tight gates, for catalog merging."""
    import bisect
    times = [r["time"] for r in b_rows]
    cand = []
    for i, ra in enumerate(a_rows):
        lo = bisect.bisect_left(times, ra["time"] - timedelta(seconds=dt_max))
        hi = bisect.bisect_right(times, ra["time"] + timedelta(seconds=dt_max))
        for j in range(lo, hi):
            rb = b_rows[j]
            d = math.hypot((ra["latitude"] - rb["latitude"]) * 111.195,
                           (ra["longitude"] - rb["longitude"]) * 111.195 * math.cos(math.radians(ra["latitude"])))
            dt = abs((rb["time"] - ra["time"]).total_seconds())
            if d <= d_max:
                cand.append((d, dt, i, j))
    cand.sort()
    used_a, used_b, pairs = set(), set(), []
    for d, dt, i, j in cand:
        if i not in used_a and j not in used_b:
            used_a.add(i), used_b.add(j), pairs.append((i, j))
    return pairs


def chain_magnitudes(out: Path, final_rows: list, window_s: float = 0.5) -> dict:
    """Relative magnitudes for every detection, including templates without ML.

    MatchLocate2 writes ``user0 + median log10(amplitude ratio)``; for a
    template without magnitude user0 is undefined (-12345), so the log ratio
    L is recovered from the native output either way. Templates without ML
    get a magnitude from detections of their own event by templates with one
    (median of M_T1 + L, two passes); each final event then gets the median
    of M_T + L over all templates that detected it within ``window_s``.
    """
    from matchlocate_runner.native import parse_eventcase
    templates = pd.read_csv(out / "dataset" / "templates.csv")
    mag = {r.template_id: float(r.magnitude) for r in templates.itertuples() if pd.notna(r.magnitude)}
    known0 = set(mag)
    origin = {r.template_id: pd.Timestamp(r.origin_time_utc) for r in templates.itertuples()}
    rows = []                                          # (abs time, template, log ratio)
    for job in (out / "run" / "jobs").glob("*/*"):
        f = job / "EventCase.out"
        if not f.is_file():
            continue
        ref = pd.Timestamp(datetime.strptime(job.parent.name, "%Y%m%d").replace(tzinfo=timezone.utc))
        for d in parse_eventcase(f, template_id=job.name):
            lr = d.magnitude + 12345.0 if d.magnitude < -1000 else d.magnitude - mag.get(job.name, float("nan"))
            rows.append((ref + pd.Timedelta(seconds=d.time_s), job.name, lr))
    det = pd.DataFrame(rows, columns=["time", "template_id", "log_ratio"]).sort_values("time").reset_index(drop=True)
    times = det.time.to_numpy()
    tol = np.timedelta64(int(window_s * 1e9), "ns")

    def around(t):
        lo, hi = np.searchsorted(times, np.datetime64(t.tz_convert(None)) - tol), \
            np.searchsorted(times, np.datetime64(t.tz_convert(None)) + tol, side="right")
        return det.iloc[lo:hi]

    det["time"] = det.time.dt.tz_convert(None)
    times = det.time.to_numpy()
    for _ in range(2):
        for tid in templates.template_id:
            if tid in mag:
                continue
            near = around(origin[tid])
            vals = [mag[t] + lr for t, lr in zip(near.template_id, near.log_ratio) if t != tid and t in mag]
            if vals:
                mag[tid] = float(np.median(vals))
    result = []
    for r in final_rows:
        near = around(pd.Timestamp(r["time"]))
        vals = [mag[t] + lr for t, lr in zip(near.template_id, near.log_ratio) if t in mag and np.isfinite(lr)]
        result.append((float(np.median(vals)) if vals else None, len(vals)))
    return {"per_event": result, "templates_with_ml": len(known0),
            "templates_after_chain": len(mag), "templates_total": int(len(templates))}


def export(out: Path, scope: dict, catalog_round: str = "") -> dict:
    """Final-threshold M&L catalog, union with the round catalog (new events only), period scores.

    Default: union with the source round (r6) -> <out>/catalog (the r7 catalog).
    With catalog_round (e.g. r8): the round's own stage-10 catalog and DD layer
    form the base, and each M&L event is shifted by its detecting template's
    position change between the source round and that round (M&L locates
    relative to the template) -> export/<catalog_round>/60_catalog.
    """
    comparison = _load("evaluation_comparison", EXPERT.parent / "evaluation" / "scripts" / "plot_evaluation_comparison.py")
    final = CFG.get("final", {"mad_threshold": 9.0, "cc_threshold": 0.0})
    sep = float(final.get("min_separation_s", CFG["run"]["merge"]["min_separation_s"]))
    by_segment = {}
    with (out / "run" / "template_detections.csv").open() as handle:
        for r in csv.DictReader(handle):
            by_segment.setdefault(r["segment"], []).append(Detection(
                float(r["time_s"]), float(r["latitude"]), float(r["longitude"]), float(r["depth_km"]),
                float(r["magnitude"]), float(r["cc"]), float(r["nmad"]), r["template_id"]))
    ml = []
    for seg in sorted(by_segment):
        ref = datetime.strptime(seg, "%Y%m%d").replace(tzinfo=timezone.utc)
        for d in merge_detections(by_segment[seg], float(final["cc_threshold"]), float(final["mad_threshold"]), sep):
            ml.append({"time": ref + timedelta(seconds=d.time_s), "latitude": d.latitude, "longitude": d.longitude,
                       "depth_km": d.depth_km, "magnitude": None if math.isnan(d.magnitude) else d.magnitude,
                       "cc": d.cc, "nmad": d.nmad, "template_id": d.template_id})
    ml.sort(key=lambda r: r["time"])
    chain = chain_magnitudes(out, ml)
    for r, (m, n) in zip(ml, chain["per_event"]):
        r["magnitude_native"] = r["magnitude"]
        r["magnitude"], r["n_magnitude_templates"] = m, n
    expert, _ = comparison.load_expert("r6")
    r6 = sorted(expert["rows"], key=lambda r: r["time"])   # round catalog as scored so far (NLL positions)
    # r7 catalog rows for the r6 events: DD positions where relocated, else NLL
    src = EXPERT / (f"export/{catalog_round}" if catalog_round else CFG["source_export"])
    r6df = pd.read_csv(src / "10_validate_catalog/events.csv", low_memory=False)
    dd = pd.read_csv(src / "52_double_difference/relocated_events.csv").set_index("event_id")
    prior = src / "45_depth_prior/events.csv"
    unresolved = set(pd.read_csv(prior).query("depth_unresolved").event_id) if prior.is_file() else set()
    # DD acceptance only for new round catalogs (r7 stays reproducible as built)
    max_dz = (float(yaml.safe_load((EXPERT / "00_config" / "double_difference.yaml").read_text())
                    .get("max_vertical_shift_km", math.inf)) if catalog_round else math.inf)
    r6_dd = []
    for e in r6df.itertuples():
        if e.event_id in dd.index:
            d = dd.loc[e.event_id]
            t, lat, lon, z, how = d.origin_time_dd, d.latitude_dd, d.longitude_dd, d.dd_depth_below_sea_level_km, "dd"
            if abs(d.dd_depth_below_sea_level_km - d.depth_below_sea_level_km) > max_dz:
                t, lat, lon, z, how = (d.origin_time_nll, d.latitude_nll, d.longitude_nll,
                                       d.depth_below_sea_level_km, "dd_rejected")
        else:
            t, lat, lon, z, how = e.origin_time, e.latitude, e.longitude, e.depth_below_sea_level_km, "nll"
        if pd.isna(lat):
            continue
        t = pd.Timestamp(t).round("us").to_pydatetime()
        if not comparison.W0 <= t < comparison.W1:
            continue
        has_ml = pd.notna(e.magnitude)
        r6_dd.append({"time": t, "latitude": float(lat), "longitude": float(lon), "depth_km": float(z),
                      "magnitude": float(e.magnitude) if has_ml else None, "event_id": e.event_id,
                      "location_source": how + ("_depth_unresolved" if e.event_id in unresolved else ""),
                      "magnitude_source": "r6_ml" if has_ml else ""})
    r6_dd.sort(key=lambda r: r["time"])
    shifted_templates = 0
    if catalog_round:
        # move each M&L event with its template: delta = template position in this
        # round - template position used by the run (dataset/templates.csv)
        base = {r["event_id"]: r for r in r6_dd}
        tpl = pd.read_csv(out / "dataset" / "templates.csv").set_index("template_id")
        delta = {}
        for tid, t in tpl.iterrows():
            b = base.get(tid)
            if b is not None:
                delta[tid] = (b["latitude"] - t.latitude, b["longitude"] - t.longitude,
                              b["depth_km"] - (t.depth_km - float(CFG["model_datum_elevation_km"])))
        shifted_templates = sum(1 for d in delta.values() if abs(d[2]) > 0.05 or abs(d[0]) > 5e-4 or abs(d[1]) > 5e-4)
        for r in ml:
            d = delta.get(r["template_id"])
            if d is not None:
                r["latitude"] += d[0]; r["longitude"] += d[1]; r["depth_km"] += d[2]
    pairs = _dedupe_pairs(ml, r6_dd)
    in_r6 = {i for i, _ in pairs}
    for i, j in pairs:
        if r6_dd[j]["magnitude"] is None and ml[i]["magnitude"] is not None:
            r6_dd[j]["magnitude"], r6_dd[j]["magnitude_source"] = ml[i]["magnitude"], "ml_chain"
    new = [r for i, r in enumerate(ml) if i not in in_r6]
    new_rows = [{**r, "event_id": f"ml_{k:06d}", "location_source": "ml", "magnitude_source": "ml_chain"
                 if r["magnitude"] is not None else ""} for k, r in enumerate(new, 1)]
    base_label = catalog_round or "r6"
    union = sorted([{**r, "source": base_label} for r in r6_dd] + [{**r, "source": "ml"} for r in new_rows],
                   key=lambda r: r["time"])
    catalog = (EXPERT / f"export/{catalog_round}/60_catalog") if catalog_round else out / "catalog"
    catalog.mkdir(parents=True, exist_ok=True)
    with (catalog / "ml_events.csv").open("w", newline="") as h:
        w = csv.writer(h, lineterminator="\n")
        w.writerow(["origin_time_utc", "latitude", "longitude", "depth_bsl_km", "magnitude",
                    "n_magnitude_templates", "magnitude_native", "cc", "nmad", "template_id", "in_r6"])
        for i, r in enumerate(ml):
            w.writerow([r["time"].isoformat(), r["latitude"], r["longitude"], r["depth_km"],
                        "" if r["magnitude"] is None else round(r["magnitude"], 3), r["n_magnitude_templates"],
                        "" if r["magnitude_native"] is None else r["magnitude_native"], r["cc"], r["nmad"],
                        r["template_id"], i in in_r6])
    with (catalog / ("catalog_events.csv" if catalog_round else "r6_plus_ml_events.csv")).open("w", newline="") as h:
        w = csv.writer(h, lineterminator="\n")
        w.writerow(["event_id", "origin_time_utc", "latitude", "longitude", "depth_bsl_km", "magnitude",
                    "magnitude_source", "location_source", "source", "ml_cc", "ml_nmad", "ml_template_id"])
        for r in union:
            w.writerow([r["event_id"], r["time"].isoformat(), r["latitude"], r["longitude"], r["depth_km"],
                        "" if r.get("magnitude") is None else round(r["magnitude"], 3), r["magnitude_source"],
                        r["location_source"], r["source"], r.get("cc", ""), r.get("nmad", ""),
                        r.get("template_id", "")])

    refs, _ = comparison.load_references()
    ms = datetime.fromisoformat(str(yaml.safe_load((EXPERT / "00_config" / "config.yaml").read_text())
                                    ["mainshock"]["time_utc"]).replace("Z", "+00:00"))
    periods = {"all": (comparison.W0, comparison.W1), "pre_mainshock": (comparison.W0, ms),
               "first_48h": (ms, ms + timedelta(hours=48)), "later": (ms + timedelta(hours=48), comparison.W1)}
    scores = {}
    for name, (t0, t1) in periods.items():
        sel = lambda rows: [r for r in rows if t0 <= r["time"] < t1 and comparison._mask_row(r)]
        pops = {"r6": sel(r6), "ml": sel(ml), "r6_plus_ml": sel(union)}
        scores[name] = {}
        for ref in refs:
            rr = comparison.as_record(ref["key"], ref["label"], ref["color"],
                                      [x for x in ref["rows"] if t0 <= x["time"] < t1])
            for pname, rows in pops.items():
                rec = comparison.as_record(pname, pname, "k", rows)
                m = len(comparison.match(rec, rr))
                scores[name].setdefault(pname, {"events": len(rows)})[ref["key"]] = {
                    "matched": m, "recall": round(m / max(len(rr["rows"]), 1), 4)}
            scores[name].setdefault("reference_events", {})[ref["key"]] = len(rr["rows"])
    return {"final_threshold": final, "ml_events": len(ml), "ml_in_r6": len(in_r6), "ml_new": len(new),
            "magnitudes": {k: chain[k] for k in ("templates_with_ml", "templates_after_chain", "templates_total")}
            | {"events_with_magnitude": sum(r["magnitude"] is not None for r in ml)},
            "catalog_round": catalog_round or CFG["source_export"], "templates_shifted": shifted_templates,
            "r6_events": len(r6), "union_events": len(union), "dedupe_gates": {"dt_s": 2.0, "epicentral_km": 5.0},
            "union_location_sources": {k: sum(r["location_source"] == k for r in union) for k in ("dd", "dd_rejected", "nll", "ml")},
            "union_magnitude_sources": {k: sum(r["magnitude_source"] == k for r in union) for k in ("r6_ml", "ml_chain", "")},
            "scores": scores}


def summary_md(report: dict) -> str:
    b = report["evaluation"]["r6_baseline"]
    tag = f" [{report['tag']}]" if report.get("tag") else ""
    lines = [f"# Stage 60 Match&Locate — {report['scope']}{tag} ({', '.join(report['evaluation']['days'])})", "",
             f"Overrides: `{json.dumps(report.get('override') or {})}`", "",
             f"Templates: {report['inputs']['templates']} (cover {report['inputs']['covered_fraction']:.1%} of v1 at "
             f"{CFG['templates']['cover_radius_km']} km); kept by prepare: {report['prepare']['templates_kept']}, "
             f"rows {report['prepare']['rows_kept']}. Native jobs: {report['run']['jobs']}; "
             f"wall {report['timing_s']['run']:.0f} s.", "",
             f"Reference events in mask on these days: {report['evaluation']['reference_events']}.",
             f"r6 baseline: {b['events']} events, Pang recall {b['pang']['recall']:.1%}, "
             f"matched-any-reference {b['matched_any_reference_fraction']:.1%}.", "",
             "| N×MAD | CC | M&L events | Pang recall | r6 ∪ M&L Pang recall | Pang beyond r6 | new vs r6 | matched any ref |",
             "|---|---|---|---|---|---|---|---|"]
    for s in report["evaluation"]["sweep"]:
        lines.append(f"| {s['mad']} | {s['cc']} | {s['events']} | {s['pang']['recall']:.1%} | "
                     f"{s['pang_union_recall']:.1%} | {s['pang_recovered_beyond_r6']} | {s['new_vs_r6']} | "
                     f"{s['matched_any_reference_fraction']:.1%} |")
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scope", choices=sorted(CFG["scopes"]), default="pilot")
    parser.add_argument("--stage", choices=["all", "inputs", "prepare", "run", "evaluate", "export"], default="all")
    parser.add_argument("--tag", default="", help="variant name; output goes to <scope>_<tag>")
    parser.add_argument("--catalog-round", default="", help="export step: base round for the catalog (e.g. r8)")
    parser.add_argument("--override", default="{}",
                        help='JSON deep-merged into match_locate.yaml, e.g. \'{"prepare": {"selection": {"min_snr": 5}}}\'')
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
    steps = ["inputs", "prepare", "run", "evaluate", "export"] if args.stage == "all" else [args.stage]
    for step in steps:
        t0 = time.time()
        if step == "inputs":
            report["inputs"] = build_inputs(out / "inputs", scope)
        elif step == "prepare":
            i = out / "inputs"
            call([py, "-I", TOOL / "interface/prepare.py", "--waveforms", (EXPERT / CFG["waveforms"]).resolve(),
                  "--stations", i / "stations.csv", "--templates", i / "templates.csv", "--picks", i / "picks.csv",
                  "--velocity-model", (EXPERT / CFG["velocity_model"]["registry"]).resolve(),
                  "--model-key", CFG["velocity_model"]["key"], "--config", i / "prepare_config.json",
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
            key = f"export_{args.catalog_round}" if args.catalog_round else "export"
            report[key] = export(out, scope, args.catalog_round)
        report["timing_s"][step] = round(time.time() - t0, 1)
        report_path.write_text(json.dumps(report, indent=2, default=str) + "\n")
        print(f"{step}: done in {report['timing_s'][step]} s", flush=True)
    if "evaluation" in report:
        (out / "summary.md").write_text(summary_md(report))
        print((out / "summary.md").read_text())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
