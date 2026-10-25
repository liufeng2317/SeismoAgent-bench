#!/usr/bin/env python3
"""Stage 60: Match&Locate detection seeded by the source-round catalog.

Port of the Magna stage 60 (its PLAN.md r7). Scope ``pilot`` scans one day
with a small template set; ``full`` scans the eight-day window. Steps:

1. inputs: greedy spatial cover of the source v1 catalog by quality-filtered
   v1 events (NLL positions), associated picks as template marks;
2. seismotools/match_and_locate interface/prepare.py;
3. interface/run.py with permissive thresholds;
4. evaluate: N×MAD sweep of the merged detections on the scanned days,
   scored like stage 05 — ComCat (4 s / 15 km) and Shelly (origin time only,
   1 s, with a shifted-reference chance count) — for M&L alone, the source
   catalog and their union;
5. export: final threshold, union with the source catalog (new events only),
   chained relative magnitudes -> export/<round>/60_catalog.

Outputs: <export_root>/<scope>[_tag]/{inputs,dataset,run,report.json,summary.md}.
"""
from __future__ import annotations

import argparse
import bisect
import csv
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
VAL = yaml.safe_load((EXPERT / "00_config" / "validation.yaml").read_text())
MAIN = yaml.safe_load((EXPERT / "00_config" / "config.yaml").read_text())
CASE = (EXPERT / MAIN["case_root"]).resolve()
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
    return (VAL["region"]["latitude_bounds"][0] <= r["latitude"] <= VAL["region"]["latitude_bounds"][1] and
            VAL["region"]["longitude_bounds"][0] <= r["longitude"] <= VAL["region"]["longitude_bounds"][1])


def load_references(days):
    """ComCat (located) and Shelly (time only) rows on the given days, stage-05 cohort."""
    in_days = lambda t: any(d <= t < d + timedelta(days=1) for d in days)
    spec = VAL["references"]
    cc = pd.read_csv(CASE / spec["comcat"]["path"])
    cc = cc[cc.type.eq("earthquake") & cc.depth.between(*VAL["depth_bounds_km"])]
    comcat = [{"time": utc(r.time), "latitude": r.latitude, "longitude": r.longitude}
              for r in cc.itertuples()]
    comcat = sorted([r for r in comcat if in_days(r["time"]) and in_box(r)], key=lambda r: r["time"])
    sh = pd.read_csv(CASE / spec["shelly"]["path"], usecols=["origin_time_utc"])
    shelly = sorted([{"time": utc(t)} for t in sh.origin_time_utc if in_days(utc(t))], key=lambda r: r["time"])
    return {"comcat": comcat, "shelly": shelly}


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
    """Stage-05 gates: ComCat primary, Shelly time-only primary + shifted control."""
    located = VAL["matching"]["primary"]
    timed = VAL["matching"]["time_only"]
    shift = timedelta(seconds=timed["control_shift_s"])
    comcat = len(match(rows, refs["comcat"], located[0], located[1]))
    shelly = len(match(rows, refs["shelly"], timed["primary"][0]))
    chance = len(match(rows, [{"time": r["time"] + shift} for r in refs["shelly"]], timed["primary"][0]))
    n_c, n_s = max(len(refs["comcat"]), 1), max(len(refs["shelly"]), 1)
    return {"events": len(rows), "comcat_matched": comcat, "comcat_recall": round(comcat / n_c, 4),
            "shelly_matched": shelly, "shelly_chance": chance, "shelly_recall": round(shelly / n_s, 4),
            "shelly_recall_net": round((shelly - chance) / n_s, 4)}


def source_catalog():
    """The source round's complete catalog (NLL positions), in window and box."""
    e = pd.read_csv(EXPERT / CFG["source_export"] / "10_validate_catalog" / "events.csv", low_memory=False)
    rows = [{"time": utc(r.origin_time), "latitude": r.latitude, "longitude": r.longitude,
             "depth_km": r.depth_below_sea_level_km, "magnitude": None if pd.isna(r.magnitude) else r.magnitude,
             "event_id": r.event_id} for r in e.itertuples() if pd.notna(r.latitude)]
    w0, w1 = utc(VAL["window"]["start_utc"]), utc(VAL["window"]["end_utc"])
    return sorted([r for r in rows if w0 <= r["time"] < w1 and in_box(r)], key=lambda r: r["time"])


# -------------------------------------------------------------------- inputs
def build_inputs(out: Path, scope: dict) -> dict:
    src = EXPERT / CFG["source_export"]
    tcfg = CFG["templates"]
    events = pd.read_csv(src / "10_validate_catalog" / "events.csv", low_memory=False)
    events = events[events["in_v1_working_catalog"].astype(str).str.lower().isin(["true", "1"])]
    rows = [{"event_id": e.event_id, "latitude": float(e.latitude), "longitude": float(e.longitude),
             "depth_km": float(e.depth_below_sea_level_km), "origin": str(e.origin_time), "position": "nll",
             "magnitude": None if pd.isna(e.magnitude) else float(e.magnitude),
             "n_stations": int(e.n_stations), "sigma_z": float(e.posterior_sigma_depth_km)}
            for e in events.itertuples()]
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
            "templates_with_magnitude": sum(1 for t in templates if t["magnitude"] is not None),
            "picks": int(len(joined))}


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


CC_LINKS = EXPERT / CFG["export_root"] / "cc_links"


def cc_links(workers: int) -> dict:
    """Waveform CC link count per source event (seismotools/cross_correlation, pairs within 3 km,
    30 nearest neighbours, default acceptance): an event without any is not similar to any neighbour.
    Writes <export_root>/cc_links/cc_links.csv."""
    src = EXPERT / CFG["source_export"]
    CC_LINKS.mkdir(parents=True, exist_ok=True)
    v = pd.read_csv(src / "10_validate_catalog" / "events.csv", low_memory=False)
    v = v[v.latitude.notna()]
    v[["event_id", "origin_time", "latitude", "longitude", "depth_below_sea_level_km"]].rename(
        columns={"origin_time": "origin_time_utc", "depth_below_sea_level_km": "depth_km"}).to_csv(
        CC_LINKS / "events.csv", index=False)
    a = pd.read_csv(src / "04_locate_nonlinloc" / "full" / "picks.csv")
    a = a[a.residual_s.abs() <= 0.5].merge(
        pd.read_csv(src / "02_pick_phasenet" / "full" / "picks.csv", usecols=["pick_id", "station_id", "time_utc"]),
        on="pick_id")
    a[["event_id", "station_id", "phase", "time_utc"]].drop_duplicates(["event_id", "station_id", "phase"]).to_csv(
        CC_LINKS / "arrivals.csv", index=False)
    (CC_LINKS / "ccdt_config.json").write_text(json.dumps(
        {"pairs": {"max_distance_km": 3.0, "max_neighbors": 30}, "write_rejected": False}))
    tool = TOOL.parent / "cross_correlation" / "interface" / "run.py"
    call([sys.executable, "-I", tool, "--events", CC_LINKS / "events.csv", "--arrivals", CC_LINKS / "arrivals.csv",
          "--waveforms", (EXPERT / CFG["waveforms"]).resolve(), "--output-dir", CC_LINKS / "ccdt",
          "--config", CC_LINKS / "ccdt_config.json", "--workers", workers, "--overwrite", "--quiet"],
         CC_LINKS / "ccdt.log")
    m = pd.read_csv(CC_LINKS / "ccdt" / "measurements.csv")
    n = pd.concat([m.event_id_1, m.event_id_2]).value_counts()
    v["cc_links"] = v.event_id.map(n).fillna(0).astype(int)
    v[["event_id", "cc_links"]].to_csv(CC_LINKS / "cc_links.csv", index=False)
    return {"events": len(v), "with_links": int((v.cc_links > 0).sum()), "dt_lines": int(len(m))}


def location_quality():
    """Source event ids passing ``location_quality`` (internal criteria only: CC links from
    ``cc_links``, optionally NLL azimuthal gap and horizontal sigma) and the failing ids with a reason.
    None when the block is absent."""
    q = CFG.get("location_quality")
    if not q:
        return None, {}
    ev = pd.read_csv(EXPERT / CFG["source_export"] / "10_validate_catalog" / "events.csv", low_memory=False)
    ev = ev[ev.latitude.notna()].set_index("event_id")
    links = pd.read_csv(CC_LINKS / "cc_links.csv").set_index("event_id").cc_links.reindex(ev.index).fillna(0)
    reason = pd.Series("ok", index=ev.index)
    if "max_sigma_x_km" in q:
        reason[~(ev.posterior_sigma_x_km <= q["max_sigma_x_km"])] = "horizontal_sigma"
    if "max_gap_deg" in q:
        reason[~(ev.azimuth_gap_deg <= q["max_gap_deg"])] = "azimuthal_gap"
    reason[links < q["min_cc_links"]] = "no_waveform_neighbours"
    return set(reason.index[reason == "ok"]), reason[reason != "ok"].to_dict()


def export(out: Path, scope: dict, catalog_round: str) -> dict:
    final = CFG["final"]
    good, failed = location_quality()
    detections = read_detections(out)
    if good is not None:
        # templates failing the rule do not place events; their detections leave the merge
        detections = {seg: [d for d in v if d.template_id in good] for seg, v in detections.items()}
    ml = merged_rows(detections, float(final["cc_threshold"]), float(final["mad_threshold"]),
                     float(final["min_separation_s"]))
    chain = chain_magnitudes(out, ml)
    for r, (m, n) in zip(ml, chain["per_event"]):
        r["magnitude_native"], r["magnitude"], r["n_magnitude_templates"] = r["magnitude"], m, n
    e = pd.read_csv(EXPERT / CFG["source_export"] / "10_validate_catalog" / "events.csv", low_memory=False)
    w0, w1 = utc(VAL["window"]["start_utc"]), utc(VAL["window"]["end_utc"])
    base = sorted([{"time": utc(r.origin_time), "latitude": r.latitude, "longitude": r.longitude,
                    "depth_km": r.depth_below_sea_level_km, "event_id": r.event_id, "location_source": "nll",
                    "magnitude": None if pd.isna(r.magnitude) else float(r.magnitude),
                    "magnitude_source": "" if pd.isna(r.magnitude) else "source_ml"}
                   for r in e.itertuples() if pd.notna(r.latitude) and w0 <= utc(r.origin_time) < w1],
                  key=lambda r: r["time"])
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
            "picked_failing_quality": len(low), "ml_events": len(ml), "ml_in_source": len(in_base), "ml_new": len(new),
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
             f"Source catalog: {b['events']} events, ComCat recall {b['comcat_recall']:.1%}, "
             f"Shelly recall {b['shelly_recall']:.1%} (net {b['shelly_recall_net']:.1%}).", "",
             "| N×MAD | M&L events | M&L ComCat | M&L Shelly net | new vs source | union events | union ComCat | union Shelly | union Shelly net | union chance |",
             "|---|---|---|---|---|---|---|---|---|---|"]
    for s in ev["sweep"]:
        m, u = s["ml"], s["union"]
        lines.append(f"| {s['mad']} | {m['events']} | {m['comcat_recall']:.1%} | {m['shelly_recall_net']:.1%} | "
                     f"{s['new_vs_source']} | {u['events']} | {u['comcat_recall']:.1%} | {u['shelly_recall']:.1%} | "
                     f"{u['shelly_recall_net']:.1%} | {u['shelly_chance']} |")
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scope", choices=sorted(CFG["scopes"]), default="pilot")
    parser.add_argument("--stage", choices=["all", "inputs", "prepare", "run", "evaluate", "export", "cclinks"],
                        default="all")
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
        elif step == "cclinks":
            report["cc_links"] = cc_links(par["prepare_workers"])
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
