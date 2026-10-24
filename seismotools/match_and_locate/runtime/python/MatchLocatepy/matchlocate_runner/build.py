"""Build a prepared Match&Locate dataset from common case inputs (requires ObsPy).

Inputs: MiniSEED waveforms, a station table, a template-event table, optional
picks and a layered velocity model. Output: the dataset layout consumed by
``interface/run.py`` plus ``dataset.json`` (provenance, depth datum) and
``prepare_report.json`` (every template and channel-phase kept or dropped,
with the reason).

Work is split into independent (channel, day) tasks: each reads the raw day
once, processes it, writes the continuous file when the day is scanned, and
cuts every template of that day from the same processed trace — so templates
and continuous data always share processing. Event-window segments are
processed with padding and trimmed. Which events serve as templates is the
caller's decision (see ``select.select_templates`` for a helper).
"""
from __future__ import annotations

import csv
import dataclasses
import datetime as _dt
import hashlib
import json
import math
import os
import re
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

from .dataset import ChannelPhase, Template, write_channels, write_templates
from .traveltime import LayeredModel, epicentral_km, first_arrival

DEFAULT_PREPARE: Dict = {
    "processing": {"sampling_rate": 50.0, "freqmin": 2.0, "freqmax": 10.0, "corners": 4, "zerophase": True},
    "segments": {"days": [], "windows": []},
    "channels": {"families": ["HH", "BH", "EH", "HN", "EN", "SH"], "P": ["Z"], "S": ["N", "E", "1", "2"]},
    "window": {"length_s": 2.0, "before_s": 0.3, "after_s": 1.7},
    "selection": {"max_distance_km": 100.0, "min_snr": 3.0, "noise_s": 5.0, "min_rows": 9,
                  "exclude_p_overlapping_s": True},
    "marks": {"source": "picks_then_model"},
    "depth": {"input_reference": "model_datum", "model_datum_elevation_km": None},
    "run": {},
}
_TOKEN = re.compile(r"^[A-Za-z0-9._-]+$")
_EXTENSIONS = {".mseed", ".miniseed", ".ms", ".msd"}
_DAY_S = 86400.0


def merge_settings(base: Dict, override: Optional[Dict]) -> Dict:
    from .runner import merge_config
    return merge_config(base, override)


# ---------------------------------------------------------------- input tables

def read_stations(path) -> Dict[str, Dict]:
    out = {}
    with Path(path).open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            sid = row["station_id"].strip()
            if sid.count(".") != 1:
                raise ValueError(f"station_id must be NET.STA: {sid!r}")
            elev = (row.get("elevation_m") or "").strip()
            out[sid] = {"latitude": float(row["latitude"]), "longitude": float(row["longitude"]),
                        "elevation_m": float(elev) if elev else 0.0}
    return out


def read_events(path) -> List[Dict]:
    from obspy import UTCDateTime
    out = []
    with Path(path).open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            eid = row["event_id"].strip()
            if not _TOKEN.match(eid):
                raise ValueError(f"event_id must match [A-Za-z0-9._-]+: {eid!r}")
            mag = (row.get("magnitude") or "").strip()
            out.append({"event_id": eid, "origin": UTCDateTime(row["origin_time_utc"]),
                        "latitude": float(row["latitude"]), "longitude": float(row["longitude"]),
                        "depth_km": float(row["depth_km"]), "magnitude": float(mag) if mag else None})
    ids = [e["event_id"] for e in out]
    if len(set(ids)) != len(ids):
        raise ValueError("duplicate event_id in templates table")
    return out


def read_picks(path) -> Dict[Tuple[str, str, str], float]:
    """(event_id, station_id, phase) -> UTC timestamp (float seconds)."""
    from obspy import UTCDateTime
    out = {}
    if not path:
        return out
    with Path(path).open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            phase = row["phase"].strip().upper()[:1]
            if phase in ("P", "S"):
                out[(row["event_id"].strip(), row["station_id"].strip(), phase)] = UTCDateTime(row["time_utc"]).timestamp
    return out


def read_velocity_model(path, key: Optional[str] = None) -> Tuple[LayeredModel, Dict]:
    """CSV (top_of_layer_km, vp_km_s, vs_km_s), a JSON row list, or a JSON
    registry {"models": {key: {"rows": [...]}}} selected with ``key``."""
    path = Path(path)
    if path.suffix.lower() == ".csv":
        with path.open(newline="", encoding="utf-8") as handle:
            rows = list(csv.DictReader(handle))
        return LayeredModel.from_rows(rows), {"path": str(path), "rows": rows}
    data = json.loads(path.read_text())
    if isinstance(data, dict) and "models" in data:
        if key is None:
            raise ValueError(f"{path} holds several models; pass --model-key ({sorted(data['models'])})")
        rows = data["models"][key]["rows"]
    elif isinstance(data, dict) and "rows" in data:
        rows = data["rows"]
    else:
        rows = data
    return LayeredModel.from_rows(rows), {"path": str(path), "key": key, "rows": rows}


# ------------------------------------------------------------- waveform index

def index_waveforms(root, workers: int = 1) -> Dict[str, List[Tuple[float, float, str]]]:
    """trace id -> [(start, end, path)] from MiniSEED headers."""
    files = sorted(str(p) for p in Path(root).rglob("*") if p.is_file() and p.suffix.lower() in _EXTENSIONS)
    if not files:
        raise ValueError(f"no MiniSEED files (*.mseed, *.miniseed, *.ms, *.msd) under {root}")
    index: Dict[str, List[Tuple[float, float, str]]] = {}
    with ProcessPoolExecutor(max_workers=max(1, workers)) as pool:
        for path, spans in zip(files, pool.map(_header_spans, files, chunksize=16)):
            for tid, start, end in spans:
                index.setdefault(tid, []).append((start, end, path))
    return index


def _header_spans(path: str):
    from obspy import read
    return [(tr.id, tr.stats.starttime.timestamp, tr.stats.endtime.timestamp) for tr in read(path, headonly=True)]


def choose_channels(index: Dict, stations: Dict[str, Dict], channels_cfg: Dict) -> Dict[str, Dict[str, str]]:
    """Per station: the first family (in preference order) with a vertical and,
    if present, horizontals; returns {station_id: {component: trace_id}}."""
    chosen = {}
    for sid in stations:
        candidates = [tid for tid in index if tid.rsplit(".", 2)[0] == sid]
        for family in channels_cfg["families"]:
            fam = sorted(t for t in candidates if t.split(".")[3][:2] == family)
            if not fam:
                continue
            location = sorted({t.split(".")[2] for t in fam})[0]
            comps = {t.split(".")[3][2]: t for t in fam if t.split(".")[2] == location}
            if any(c in comps for c in channels_cfg["P"] + channels_cfg["S"]):
                chosen[sid] = comps
                break
    return chosen


# ---------------------------------------------------------------- the plan

@dataclasses.dataclass
class RowPlan:
    template_id: str
    channel: str              # trace id, also the dataset file stem
    station_id: str
    phase: str
    mark: int
    travel_time_s: float
    mark_source: str
    distance_km: float
    slowness_h_s_per_deg: float
    slowness_v_s_per_km: float
    p_time_s: float           # model or picked P time (noise window anchor)
    status: str = "planned"
    reason: str = ""
    snr: Optional[float] = None


def plan_rows(events: List[Dict], stations: Dict, chosen: Dict, model: LayeredModel, picks: Dict,
              cfg: Dict, depth_offset_km: float, datum_km: Optional[float]) -> Tuple[List[RowPlan], Dict]:
    sel, win, marks_cfg = cfg["selection"], cfg["window"], cfg["marks"]
    rows, dropped = [], {}
    for e in events:
        zs = e["depth_km"] + depth_offset_km
        for sid, comps in sorted(chosen.items()):
            st = stations[sid]
            zr = 0.0 if datum_km is None else datum_km - st["elevation_m"] / 1000.0
            dist = epicentral_km(st["latitude"], st["longitude"], e["latitude"], e["longitude"])
            if dist > sel["max_distance_km"]:
                continue
            rays = {ph: first_arrival(model, ph, dist, zs, zr) for ph in ("P", "S")}
            times = {}
            for ph in ("P", "S"):
                pick = picks.get((e["event_id"], sid, ph))
                use_pick = pick is not None and marks_cfg["source"] in ("picks_then_model", "picks_only")
                if use_pick:
                    times[ph] = (pick - e["origin"].timestamp, "pick")
                elif marks_cfg["source"] != "picks_only":
                    times[ph] = (rays[ph].travel_time_s, "model")
            for ph, comp_list, mark in (("P", cfg["channels"]["P"], 1), ("S", cfg["channels"]["S"], 2)):
                if ph not in times:
                    dropped.setdefault(e["event_id"], []).append(f"{sid} {ph}: no pick (marks.source=picks_only)")
                    continue
                if ph == "P" and sel["exclude_p_overlapping_s"] and "S" in times:
                    if times["S"][0] - times["P"][0] < win["length_s"] - win["before_s"]:
                        dropped.setdefault(e["event_id"], []).append(f"{sid} P: window reaches S (S-P too short)")
                        continue
                for comp in comp_list:
                    if comp not in comps:
                        continue
                    tt, source = times[ph]
                    rows.append(RowPlan(e["event_id"], comps[comp], sid, ph, mark, tt, source, dist,
                                        rays[ph].slowness_h_s_per_deg, rays[ph].dtdz_s_per_km,
                                        times.get("P", (rays["P"].travel_time_s, "model"))[0]))
    return rows, dropped


# ------------------------------------------------------------------- tasks

def _read_raw(index_entries, start, end):
    from obspy import Stream, read, UTCDateTime
    st = Stream()
    for s, e, path in index_entries:
        if e >= start and s <= end:
            st += read(path, starttime=UTCDateTime(start), endtime=UTCDateTime(end))
    return st


def _task(args) -> Dict:
    """One channel over one day (or one event window); failures are reported, not raised."""
    try:
        return _task_inner(args)
    except Exception as exc:  # recorded per task so one bad channel-day cannot stop the build
        channel, start, cuts = args[0], args[2], args[9]
        reason = f"task error: {type(exc).__name__}: {exc}"
        return {"channel": channel, "start": start, "error": reason,
                "rows": [{**cut["key"], "status": "dropped", "reason": reason} for cut in cuts]}


def _task_inner(args) -> Dict:
    """One channel over one day (or one event window): process, write, cut."""
    (channel, entries, start, length, pad, write_path, reference, station, processing, cuts) = args
    from obspy import UTCDateTime
    from .prepare import (Processing, cut_template, process_continuous, window_snr, write_continuous_sac,
                          zero_fraction)
    proc = Processing(**processing)
    raw = _read_raw(entries, start - pad, start + length + pad)
    raw = raw.select(id=channel)
    result = {"channel": channel, "start": start, "rows": []}
    if len(raw) == 0:
        result["error"] = "no waveform data"
        for cut in cuts:
            result["rows"].append({**cut["key"], "status": "dropped", "reason": "no waveform data"})
        return result
    tr = process_continuous(raw, proc, UTCDateTime(start - pad), length + 2 * pad)
    if pad:
        tr = tr.slice(UTCDateTime(start), UTCDateTime(start) + length - tr.stats.delta * 0.5)
    if write_path:
        write_continuous_sac(tr, write_path, reference=UTCDateTime(reference), station_lat=station["latitude"],
                             station_lon=station["longitude"], station_elev_m=station["elevation_m"])
    for cut in cuts:
        origin = UTCDateTime(cut["origin"])
        try:
            info = cut_template(tr, origin, pre_s=cut["pre_s"], post_s=cut["post_s"], marks=cut["marks"],
                                event_lat=cut["event_lat"], event_lon=cut["event_lon"],
                                event_depth_km=cut["event_depth_km"], magnitude=cut["magnitude"],
                                station_lat=station["latitude"], station_lon=station["longitude"],
                                station_elev_m=station["elevation_m"], path=cut["path"], event_name=cut["event"])
        except ValueError as exc:
            for key in cut["row_keys"]:
                result["rows"].append({**key, "status": "dropped", "reason": f"template cut: {exc}"})
            continue
        noise_end = origin + cut["p_time_s"]
        for key, mark_index in zip(cut["row_keys"], cut["row_marks"]):
            arrival = origin + info.marks[mark_index] - cut["before_s"]
            gap = zero_fraction(tr, arrival, cut["length_s"])
            if gap > 0.05:
                result["rows"].append({**key, "status": "dropped",
                                       "reason": f"gap in template window ({gap:.0%} zero-filled)"})
                continue
            snr = window_snr(tr, arrival, signal_s=cut["length_s"], noise_s=cut["noise_s"],
                             gap_s=0.5 + max(0.0, (arrival - noise_end)))
            result["rows"].append({**key, "status": "cut", "snr": None if math.isnan(snr) else round(snr, 3),
                                   "snap_offset_s": info.snap_offset_s})
    return result


# ------------------------------------------------------------------ driver

def _sha256(path) -> Optional[str]:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest() if path else None


def build_dataset(*, waveforms, stations_csv, templates_csv, velocity_model, output_dir, config: Dict,
                  picks_csv=None, model_key: Optional[str] = None, workers: int = 1,
                  progress=None) -> Dict:
    from obspy import UTCDateTime
    cfg = merge_settings(DEFAULT_PREPARE, config)
    out = Path(output_dir)
    if out.exists() and any(out.iterdir()):
        raise ValueError(f"{out} must be new or empty")
    out.mkdir(parents=True, exist_ok=True)
    stations = read_stations(stations_csv)
    events = read_events(templates_csv)
    picks = read_picks(picks_csv)
    model, model_info = read_velocity_model(velocity_model, model_key)
    depth_cfg = cfg["depth"]
    datum_km = depth_cfg.get("model_datum_elevation_km")
    if depth_cfg["input_reference"] == "sea_level":
        if datum_km is None:
            raise ValueError("depth.input_reference = sea_level needs depth.model_datum_elevation_km")
        depth_offset = float(datum_km)
    elif depth_cfg["input_reference"] == "model_datum":
        depth_offset = 0.0
    else:
        raise ValueError("depth.input_reference must be 'sea_level' or 'model_datum'")

    days = [UTCDateTime(d) for d in cfg["segments"].get("days", [])]
    days = sorted({UTCDateTime(d.year, d.month, d.day).timestamp for d in days})
    windows = [{"segment_id": w["segment_id"], "start": UTCDateTime(w["start"]).timestamp,
                "end": UTCDateTime(w["end"]).timestamp} for w in cfg["segments"].get("windows", [])]
    for w in windows:
        if not _TOKEN.match(w["segment_id"]) or w["end"] <= w["start"]:
            raise ValueError(f"bad window segment {w}")
    if not days and not windows:
        raise ValueError("segments: give days and/or windows to scan")

    index = index_waveforms(waveforms, workers)
    chosen = choose_channels(index, stations, cfg["channels"])
    rows, dropped_plan = plan_rows(events, stations, chosen, model, picks, cfg, depth_offset, datum_km)
    win, sel = cfg["window"], cfg["selection"]

    # template cuts grouped by (channel, template day)
    cuts: Dict[Tuple[str, float], List[Dict]] = {}
    by_tc: Dict[Tuple[str, str], List[RowPlan]] = {}
    for r in rows:
        by_tc.setdefault((r.template_id, r.channel), []).append(r)
    events_by_id = {e["event_id"]: e for e in events}
    for (tid, channel), rs in by_tc.items():
        e = events_by_id[tid]
        marks = {r.mark: r.travel_time_s for r in rs}
        lo, hi = min(marks.values()), max(marks.values())
        day0 = UTCDateTime(e["origin"].year, e["origin"].month, e["origin"].day).timestamp
        (out / "templates" / tid).mkdir(parents=True, exist_ok=True)
        cuts.setdefault((channel, day0), []).append({
            "event": tid, "origin": e["origin"].timestamp, "marks": marks,
            "pre_s": 2.0 + max(0.0, win["before_s"] - lo), "post_s": hi + win["after_s"] + 2.0,
            "event_lat": e["latitude"], "event_lon": e["longitude"], "event_depth_km": e["depth_km"] + depth_offset,
            "magnitude": e["magnitude"], "path": str(out / "templates" / tid / f"{channel}.sac"),
            "p_time_s": rs[0].p_time_s, "before_s": win["before_s"], "length_s": win["length_s"],
            "noise_s": sel["noise_s"],
            "row_keys": [{"template_id": tid, "channel": channel, "phase": r.phase} for r in rs],
            "row_marks": [r.mark for r in rs], "key": {"template_id": tid, "channel": channel, "phase": "*"}})

    processing = {k: cfg["processing"][k] for k in ("sampling_rate", "freqmin", "freqmax", "corners", "zerophase")}
    channel_station = {tid: sid for sid, comps in chosen.items() for tid in comps.values()}
    tasks = []
    day_set = set(days) | {d for (_, d) in cuts}
    for channel, sid in sorted(channel_station.items()):
        entries = index.get(channel, [])
        for day0 in sorted(day_set):
            scan = day0 in days
            day_cuts = cuts.get((channel, day0), [])
            if not scan and not day_cuts:
                continue
            seg = UTCDateTime(day0).strftime("%Y%m%d")
            write_path = None
            if scan:
                (out / "continuous" / seg).mkdir(parents=True, exist_ok=True)
                write_path = str(out / "continuous" / seg / f"{channel}.sac")
            tasks.append((channel, entries, day0, _DAY_S, 0.0, write_path, day0, stations[sid], processing, day_cuts))
        for w in windows:
            (out / "continuous" / w["segment_id"]).mkdir(parents=True, exist_ok=True)
            pad = 4 * 5.0 + 10.0
            tasks.append((channel, entries, w["start"], w["end"] - w["start"], pad,
                          str(out / "continuous" / w["segment_id"] / f"{channel}.sac"), w["start"],
                          stations[sid], processing, []))

    results = []
    with ProcessPoolExecutor(max_workers=max(1, workers)) as pool:
        for n, res in enumerate(pool.map(_task, tasks), 1):
            results.append(res)
            if progress:
                progress(res, n, len(tasks))

    # apply gates
    state = {(r.template_id, r.channel, r.phase): r for r in rows}
    for res in results:
        for row in res["rows"]:
            phases = [row["phase"]] if row["phase"] != "*" else ["P", "S"]
            for ph in phases:
                r = state.get((row["template_id"], row["channel"], ph))
                if r is None:
                    continue
                if row["status"] == "dropped":
                    r.status, r.reason = "dropped", row["reason"]
                else:
                    r.snr = row.get("snr")
                    if r.snr is None or r.snr < sel["min_snr"]:
                        r.status, r.reason = "dropped", f"snr {r.snr} < {sel['min_snr']}"
                    else:
                        r.status = "kept"
    kept_templates, report_templates = [], []
    for e in events:
        rs = [r for r in rows if r.template_id == e["event_id"]]
        kept = [r for r in rs if r.status == "kept"]
        status = "kept" if len(kept) >= sel["min_rows"] else "dropped"
        report_templates.append({"event_id": e["event_id"], "status": status,
                                 "reason": "" if status == "kept" else f"{len(kept)} kept rows < min_rows {sel['min_rows']}",
                                 "rows_planned": len(rs), "rows_kept": len(kept),
                                 "plan_notes": dropped_plan.get(e["event_id"], []),
                                 "rows": [{"channel": r.channel, "phase": r.phase, "status": r.status,
                                           "reason": r.reason, "snr": r.snr, "mark_source": r.mark_source,
                                           "distance_km": round(r.distance_km, 3),
                                           "travel_time_s": round(r.travel_time_s, 3)} for r in rs]})
        folder = out / "templates" / e["event_id"]
        if status == "kept":
            kept_templates.append(e)
            keep_files = {r.channel for r in kept}
            for f in folder.glob("*.sac"):
                if f.stem not in keep_files:
                    f.unlink()
        elif folder.exists():
            for f in folder.glob("*.sac"):
                f.unlink()
            folder.rmdir()

    write_templates(out / "templates.csv", [
        Template(e["event_id"], str(e["origin"]), e["latitude"], e["longitude"],
                 e["depth_km"] + depth_offset, e["magnitude"]) for e in kept_templates])
    kept_ids = {e["event_id"] for e in kept_templates}
    write_channels(out / "channels.csv", [
        ChannelPhase(r.template_id, r.channel, r.phase, r.mark, r.slowness_h_s_per_deg, r.slowness_v_s_per_km)
        for r in rows if r.status == "kept" and r.template_id in kept_ids])
    (out / "config.json").write_text(json.dumps(cfg.get("run", {}), indent=2) + "\n")
    segments = [UTCDateTime(d).strftime("%Y%m%d") for d in days] + [w["segment_id"] for w in windows]
    meta = {
        "interface": "match_and_locate prepare", "created_utc": _dt.datetime.now(_dt.timezone.utc).isoformat(timespec="seconds"),
        "inputs": {"waveforms": str(waveforms), "stations_csv": str(stations_csv), "stations_sha256": _sha256(stations_csv),
                   "templates_csv": str(templates_csv), "templates_sha256": _sha256(templates_csv),
                   "picks_csv": str(picks_csv) if picks_csv else None, "picks_sha256": _sha256(picks_csv),
                   "velocity_model": model_info},
        "settings": cfg,
        "depth_offset_km": depth_offset,
        "depth_note": "dataset depths (templates.csv, SAC evdp, search grid) = input depth + depth_offset_km "
                      "(km below the velocity-model datum); run.py reports depth_km back in the input reference",
        "segments": segments, "stations_used": {sid: comps for sid, comps in sorted(chosen.items())},
    }
    (out / "dataset.json").write_text(json.dumps(meta, indent=2) + "\n")
    report = {"templates_in": len(events), "templates_kept": len(kept_templates),
              "rows_kept": sum(1 for r in rows if r.status == "kept" and r.template_id in kept_ids),
              "segments": segments, "stations_used": len(chosen),
              "task_errors": [{"channel": r["channel"], "start": UTCDateTime(r["start"]).isoformat(), "error": r["error"]}
                              for r in results if r.get("error")],
              "templates": report_templates}
    (out / "prepare_report.json").write_text(json.dumps(report, indent=2) + "\n")
    return report
