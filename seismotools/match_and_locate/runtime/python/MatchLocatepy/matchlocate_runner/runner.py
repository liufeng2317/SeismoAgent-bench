"""Run MatchLocate2 over a prepared dataset: one native job per (segment, template).

Each job runs in ``<output>/jobs/<segment>/<template_id>/`` with two short
symlinks (``T`` -> template folder, ``C`` -> continuous segment folder) so
native paths stay well below the 255-character limit. A job keeps
``INPUT.in``, ``EventCase.out``, ``native.log``, ``job.json`` and any native
diagnostic files (``-O1/2/3``); ``resume`` skips jobs whose ``job.json``
reports success. Native times are relative to the segment's SAC reference
time, which is read from the headers. Detections of all jobs are merged with
the SelectFinal rule: the Python port works on absolute times across all
segments (overlapping segments are handled); ``merge.engine = "native"`` runs
the SelectFinal binary once per segment.
"""
from __future__ import annotations

import copy
import csv
import dataclasses
import datetime as _dt
import json
import math
import os
import shutil
import subprocess
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Callable, Dict, Iterable, List, Optional, Sequence, Tuple

from . import dataset as ds
from .native import (Detection, DetectionParams, InputRow, SearchGrid, build_command,
                     merge_detections, parse_eventcase, parse_selectfinal, write_input_file,
                     write_selectfinal_input)

DEFAULT_CONFIG: Dict = {
    "search": {"units": "km", "half_width_km": 1.0, "step_km": 0.25,
               "half_depth_km": 1.0, "step_depth_km": 0.5},
    "window": {"length_s": 4.0, "before_s": 1.0, "after_s": 3.0},
    "detection": {"cc_threshold": 0.0, "mad_threshold": 12.0, "min_separation_s": 6.0},
    "merge": {"engine": "python", "cc_threshold": 0.3, "mad_threshold": 12.0, "min_separation_s": 6.0},
    "min_channels": 9,
    "output_mode": 0,
}
DETECTION_FIELDS = ["detection_id", "origin_time_utc", "latitude", "longitude", "depth_km", "depth_model_km",
                    "magnitude", "cc", "nmad", "template_id", "segment", "time_s", "self_detection"]
TEMPLATE_DETECTION_FIELDS = ["segment", "template_id", "origin_time_utc", "time_s", "latitude", "longitude",
                             "depth_km", "depth_model_km", "magnitude", "cc", "nmad"]
JOB_FIELDS = ["segment", "template_id", "status", "reason", "n_rows", "n_detections", "grid_nodes",
              "runtime_s", "returncode"]
_EPOCH = _dt.datetime(1970, 1, 1, tzinfo=_dt.timezone.utc)


def merge_config(base: Dict, override: Optional[Dict]) -> Dict:
    out = copy.deepcopy(base)
    for key, value in (override or {}).items():
        if isinstance(value, dict) and isinstance(out.get(key), dict):
            out[key] = merge_config(out[key], value)
        else:
            out[key] = value
    return out


def grid_for(search: Dict, template: ds.Template) -> SearchGrid:
    units = search.get("units", "km")
    if units == "km":
        return SearchGrid.from_km(template.latitude, float(search["half_width_km"]), float(search["step_km"]),
                                  float(search["half_depth_km"]), float(search["step_depth_km"]))
    if units == "deg":
        return SearchGrid(float(search["half_lat_deg"]), float(search["half_lon_deg"]),
                          float(search["half_depth_km"]), float(search["step_lat_deg"]),
                          float(search["step_lon_deg"]), float(search["step_depth_km"]))
    raise ValueError(f"search.units must be 'km' or 'deg', got {units!r}")


def detection_params(config: Dict) -> DetectionParams:
    w, d = config["window"], config["detection"]
    return DetectionParams(float(w["length_s"]), float(w["before_s"]), float(w["after_s"]),
                           float(d["cc_threshold"]), float(d["mad_threshold"]),
                           float(d["min_separation_s"]), int(config.get("output_mode", 0)))


@dataclasses.dataclass
class Job:
    segment: str
    template: ds.Template
    rows: List[ds.ChannelPhase]
    grid: SearchGrid
    status: str = "planned"
    reason: str = ""


def plan_jobs(root: Path, config: Dict, segments: Sequence[str], templates: Sequence[ds.Template],
              channels: Sequence[ds.ChannelPhase]) -> List[Job]:
    by_template: Dict[str, List[ds.ChannelPhase]] = {}
    for row in channels:
        by_template.setdefault(row.template_id, []).append(row)
    min_rows = int(config.get("min_channels", 1))
    jobs = []
    for segment in segments:
        available = {p.stem for p in (root / "continuous" / segment).glob("*.sac")}
        for t in templates:
            rows = [r for r in by_template.get(t.template_id, []) if r.channel in available]
            job = Job(segment, t, rows, grid_for(config["search"], t))
            if len(rows) < min_rows:
                job.status, job.reason = "skipped", f"{len(rows)} usable rows < min_channels {min_rows}"
            jobs.append(job)
    return jobs


def _iso(t: _dt.datetime) -> str:
    return t.strftime("%Y-%m-%dT%H:%M:%S.") + f"{t.microsecond // 1000:03d}Z"


def run_job(job: Job, root: Path, out: Path, binary: Path, params: DetectionParams,
            threads: int, resume: bool) -> Dict:
    folder = out / "jobs" / job.segment / job.template.template_id
    record_path = folder / "job.json"
    base = {"segment": job.segment, "template_id": job.template.template_id, "n_rows": len(job.rows),
            "grid_nodes": job.grid.node_count()}
    if job.status == "skipped":
        return {**base, "status": "skipped", "reason": job.reason, "n_detections": 0,
                "runtime_s": 0.0, "returncode": None}
    if resume and record_path.is_file():
        record = json.loads(record_path.read_text())
        if record.get("status") == "success":
            return record
    if folder.exists():
        shutil.rmtree(folder)
    folder.mkdir(parents=True)
    links = {"T": (root / "templates" / job.template.template_id).resolve(),
             "C": (root / "continuous" / job.segment).resolve()}
    for name, target in links.items():
        (folder / name).symlink_to(target, target_is_directory=True)
    write_input_file(folder / "INPUT.in", [
        InputRow(f"T/{r.channel}.sac", f"C/{r.channel}.sac", r.slowness_h_s_per_deg,
                 r.slowness_v_s_per_km, r.mark, r.phase) for r in job.rows])
    t = job.template
    command = build_command(binary, (t.latitude, t.longitude, t.depth_km), job.grid, params)
    env = dict(os.environ, OMP_NUM_THREADS=str(threads))
    start = time.time()
    with (folder / "native.log").open("w") as log:
        log.write(" ".join(command) + "\n")
        log.flush()
        proc = subprocess.run(command, cwd=folder, env=env, stdout=log, stderr=subprocess.STDOUT)
    record = {**base, "runtime_s": round(time.time() - start, 3), "returncode": proc.returncode,
              "command": command}
    if proc.returncode == 0 and (folder / "EventCase.out").is_file():
        record.update(status="success", reason="",
                      n_detections=len(parse_eventcase(folder / "EventCase.out")))
    else:
        reason = "native exit 3: candidate buffer overflow (raise thresholds)" if proc.returncode == 3 \
            else f"native exit {proc.returncode}" + ("" if (folder / "EventCase.out").is_file() else ", no EventCase.out")
        record.update(status="failed", reason=reason, n_detections=0)
    for name in links:
        (folder / name).unlink()
    record_path.write_text(json.dumps(record, indent=2) + "\n")
    return record


def collect(out: Path, records: Iterable[Dict], magnitudes: Dict[str, Optional[float]]) -> List[Tuple[str, Detection]]:
    """(segment, Detection) rows of every successful job; NaN magnitude when the
    template magnitude is unknown (the native value would be meaningless)."""
    rows: List[Tuple[str, Detection]] = []
    for r in records:
        if r.get("status") != "success":
            continue
        path = out / "jobs" / r["segment"] / r["template_id"] / "EventCase.out"
        for d in parse_eventcase(path, template_id=r["template_id"]):
            if magnitudes.get(r["template_id"]) is None:
                d = dataclasses.replace(d, magnitude=math.nan)
            rows.append((r["segment"], d))
    return rows


def _write_csv(path: Path, fields: List[str], rows: Iterable[Dict]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def _merge_native(out: Path, segment_rows: Dict[str, List[Detection]], merge: Dict,
                  binary: Path) -> List[Tuple[str, Detection]]:
    folder = out / "merge"
    folder.mkdir(exist_ok=True)
    result = []
    for segment, rows in sorted(segment_rows.items()):
        name = f"Allevents_{segment}"
        write_selectfinal_input(folder / name, rows)
        subprocess.run([str(binary), f"-H{merge['cc_threshold']}/{merge['mad_threshold']}",
                        f"-D{merge['min_separation_s']}", name], cwd=folder, check=True,
                       stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
        result += [(segment, d) for d in parse_selectfinal(folder / f"{name}.final")]
    return result


def _merge_python(collected: List[Tuple[str, Detection]], references: Dict[str, _dt.datetime],
                  merge: Dict) -> List[Tuple[str, Detection]]:
    """SelectFinal rule on absolute times so detections from different (possibly
    overlapping) segments are de-duplicated against each other."""
    # Integer milliseconds keep the |dt| <= separation test exact (native times
    # carry three decimals), so a single segment merges exactly like SelectFinal.
    shifted, origin = [], {}
    for segment, d in collected:
        offset_ms = round((references[segment] - _EPOCH).total_seconds() * 1000)
        a = dataclasses.replace(d, time_s=float(offset_ms + round(d.time_s * 1000)))
        shifted.append(a)
        origin[id(a)] = (segment, d)
    kept = merge_detections(shifted, float(merge["cc_threshold"]), float(merge["mad_threshold"]),
                            round(float(merge["min_separation_s"]) * 1000))
    return [origin[id(a)] for a in kept]


def run_dataset(input_dir, output_dir, config: Dict, bin_dir, *, jobs: int = 1, threads: int = 1,
                segments: Optional[Sequence[str]] = None, template_ids: Optional[Sequence[str]] = None,
                resume: bool = False, progress: Optional[Callable[[Dict, int, int], None]] = None) -> Dict:
    root, out, bin_dir = Path(input_dir), Path(output_dir), Path(bin_dir)
    binary = bin_dir / "MatchLocate2"
    if not (binary.is_file() and os.access(binary, os.X_OK)):
        raise ValueError(f"missing or non-executable MatchLocate2: {binary}")
    params = detection_params(config)
    templates = ds.read_templates(root / "templates.csv")
    channels = ds.read_channels(root / "channels.csv")
    if template_ids:
        wanted = set(template_ids)
        unknown = wanted - {t.template_id for t in templates}
        if unknown:
            raise ValueError(f"unknown template ids: {sorted(unknown)}")
        templates = [t for t in templates if t.template_id in wanted]
    all_segments = ds.list_segments(root)
    segments = list(segments) if segments else all_segments
    missing = sorted(set(segments) - set(all_segments))
    if missing:
        raise ValueError(f"no continuous/<segment> folder for {missing}")
    if not segments:
        raise ValueError("no continuous segments found")

    errors: List[str] = []
    segment_checks = [ds.validate_segment(root, segment) for segment in segments]
    for check in segment_checks:
        errors += [f"continuous/{check['segment']}: {e}" for e in check["errors"]]
    rows_by_template: Dict[str, List[ds.ChannelPhase]] = {}
    for r in channels:
        rows_by_template.setdefault(r.template_id, []).append(r)
    for t in templates:
        errors += ds.validate_template(root, t, rows_by_template.get(t.template_id, []),
                                       params.before_s, params.after_s)
    if errors:
        raise ValueError("dataset validation failed:\n  " + "\n  ".join(errors[:50])
                         + (f"\n  ... {len(errors) - 50} more" if len(errors) > 50 else ""))
    references = {s: ds.segment_reference(root, s) for s in segments}
    # Datasets built by interface/prepare.py record how their depths (km below
    # the velocity-model datum) relate to the input catalog's depth reference.
    meta_path = root / "dataset.json"
    depth_offset = float(json.loads(meta_path.read_text()).get("depth_offset_km", 0.0)) if meta_path.is_file() else 0.0

    plan = plan_jobs(root, config, segments, templates, channels)
    out.mkdir(parents=True, exist_ok=True)
    (out / "config.json").write_text(json.dumps(config, indent=2) + "\n")
    records = []
    with ThreadPoolExecutor(max_workers=max(1, jobs)) as pool:
        futures = [pool.submit(run_job, job, root, out, binary, params, threads, resume) for job in plan]
        for n, future in enumerate(as_completed(futures), 1):
            record = future.result()
            records.append(record)
            with (out / "progress.jsonl").open("a") as handle:
                handle.write(json.dumps({k: record.get(k) for k in JOB_FIELDS}) + "\n")
            if progress:
                progress(record, n, len(futures))
    records.sort(key=lambda r: (r["segment"], r["template_id"]))
    _write_csv(out / "jobs.csv", JOB_FIELDS, ({k: r.get(k) for k in JOB_FIELDS} for r in records))

    magnitudes = {t.template_id: t.magnitude for t in templates}
    collected = collect(out, records, magnitudes)

    def origin(segment: str, d: Detection) -> str:
        return _iso(references[segment] + _dt.timedelta(seconds=d.time_s))

    _write_csv(out / "template_detections.csv", TEMPLATE_DETECTION_FIELDS, (
        {"segment": segment, "template_id": d.template_id, "origin_time_utc": origin(segment, d),
         "time_s": f"{d.time_s:.3f}", "latitude": d.latitude, "longitude": d.longitude,
         "depth_km": round(d.depth_km - depth_offset, 4), "depth_model_km": d.depth_km,
         "magnitude": d.magnitude, "cc": d.cc, "nmad": d.nmad} for segment, d in collected))

    merge = config["merge"]
    if merge.get("engine", "python") == "native":
        segment_rows: Dict[str, List[Detection]] = {}
        for segment, d in collected:
            segment_rows.setdefault(segment, []).append(d)
        final = _merge_native(out, segment_rows, merge, bin_dir / "SelectFinal")
    else:
        final = _merge_python(collected, references, merge)
    final.sort(key=lambda sd: references[sd[0]] + _dt.timedelta(seconds=sd[1].time_s))
    _write_csv(out / "detections.csv", DETECTION_FIELDS, (
        {"detection_id": i, "origin_time_utc": origin(segment, d), "latitude": d.latitude,
         "longitude": d.longitude, "depth_km": round(d.depth_km - depth_offset, 4), "depth_model_km": d.depth_km,
         "magnitude": d.magnitude, "cc": d.cc,
         "nmad": d.nmad, "template_id": d.template_id, "segment": segment, "time_s": f"{d.time_s:.3f}",
         "self_detection": d.cc == 1.0} for i, (segment, d) in enumerate(final, 1)))

    status_counts: Dict[str, int] = {}
    for r in records:
        status_counts[r["status"]] = status_counts.get(r["status"], 0) + 1
    return {"segments": segments, "templates": len(templates), "jobs": status_counts,
            "depth_offset_km": depth_offset,
            "template_detections": len(collected), "detections": len(final),
            "segment_checks": segment_checks, "failed_jobs": [
                {k: r.get(k) for k in ("segment", "template_id", "reason")} for r in records if r["status"] == "failed"]}
