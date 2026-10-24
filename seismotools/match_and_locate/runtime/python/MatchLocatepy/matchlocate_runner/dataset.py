"""Prepared Match&Locate dataset layout, tables and validation.

Layout consumed by ``interface/run.py``::

    <dataset>/
      templates.csv                     template_id, origin_time_utc, latitude,
                                        longitude, depth_km, magnitude
      channels.csv                      template_id, channel, phase, mark,
                                        slowness_h_s_per_deg, slowness_v_s_per_km
      templates/<template_id>/<channel>.sac
      continuous/<segment_id>/<channel>.sac
      config.json                       optional default parameters

``channel`` is the file stem shared by a template file and its continuous
counterpart (for example ``UU.AVE.01.ENE``); one template channel may carry
several rows (for example P on t1 and S on t2).

A continuous segment is any folder of continuous files scanned together:
normally one UTC day (``segment_id = YYYYMMDD``, reference = day start), but
a short window around a known event works the same way. Files of one segment
must share sampling interval and begin time (the native program checks
both) and one SAC reference time, and have ``o = 0``; detected origin times
are reported relative to that reference.
"""
from __future__ import annotations

import csv
import dataclasses
import datetime as _dt
import re
from pathlib import Path
from typing import Dict, Iterable, List, Optional

from .sacheader import read_sac_header

TEMPLATE_FIELDS = ["template_id", "origin_time_utc", "latitude", "longitude", "depth_km", "magnitude"]
CHANNEL_FIELDS = ["template_id", "channel", "phase", "mark", "slowness_h_s_per_deg", "slowness_v_s_per_km"]
_TOKEN = re.compile(r"^[A-Za-z0-9._-]+$")


@dataclasses.dataclass(frozen=True)
class Template:
    template_id: str
    origin_time_utc: str
    latitude: float
    longitude: float
    depth_km: float
    magnitude: Optional[float]


@dataclasses.dataclass(frozen=True)
class ChannelPhase:
    template_id: str
    channel: str
    phase: str
    mark: int
    slowness_h_s_per_deg: float
    slowness_v_s_per_km: float


def _token(value: str, what: str) -> str:
    if not _TOKEN.match(value or ""):
        raise ValueError(f"{what} must match [A-Za-z0-9._-]+: {value!r}")
    return value


def write_templates(path, templates: Iterable[Template]) -> None:
    with Path(path).open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=TEMPLATE_FIELDS, lineterminator="\n")
        writer.writeheader()
        for t in templates:
            row = dataclasses.asdict(t)
            row["magnitude"] = "" if t.magnitude is None else t.magnitude
            writer.writerow(row)


def write_channels(path, rows: Iterable[ChannelPhase]) -> None:
    with Path(path).open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=CHANNEL_FIELDS, lineterminator="\n")
        writer.writeheader()
        for r in rows:
            writer.writerow(dataclasses.asdict(r))


def read_templates(path) -> List[Template]:
    out = []
    with Path(path).open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            mag = row.get("magnitude", "").strip()
            out.append(Template(_token(row["template_id"], "template_id"), row["origin_time_utc"],
                                float(row["latitude"]), float(row["longitude"]), float(row["depth_km"]),
                                float(mag) if mag else None))
    ids = [t.template_id for t in out]
    if len(set(ids)) != len(ids):
        raise ValueError("duplicate template_id in templates.csv")
    return out


def read_channels(path) -> List[ChannelPhase]:
    out = []
    with Path(path).open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            out.append(ChannelPhase(_token(row["template_id"], "template_id"), _token(row["channel"], "channel"),
                                    _token(row["phase"], "phase"), int(row["mark"]),
                                    float(row["slowness_h_s_per_deg"]), float(row["slowness_v_s_per_km"])))
    return out


def list_segments(root) -> List[str]:
    base = Path(root) / "continuous"
    return sorted(p.name for p in base.iterdir() if p.is_dir() and _TOKEN.match(p.name)) if base.is_dir() else []


def validate_segment(root, segment: str, channels: Optional[Iterable[str]] = None) -> Dict:
    """Header checks MatchLocate2 would otherwise fail on (or silently misuse)."""
    folder = Path(root) / "continuous" / segment
    files = sorted(folder.glob("*.sac"))
    if channels is not None:
        wanted = set(channels)
        files = [f for f in files if f.stem in wanted]
    errors, deltas, begins, ends, references = [], set(), [], [], []
    for f in files:
        h = read_sac_header(f)
        if h.byte_order != "<":
            errors.append(f"{f.name}: big-endian SAC; the native reader expects host (little-endian) order")
        if h.o is None or abs(h.o) > 1e-6:
            errors.append(f"{f.name}: o must be 0 (got {h.o})")
        if h.reference is None:
            errors.append(f"{f.name}: SAC reference time (nz*) undefined")
        else:
            references.append(h.reference)
        deltas.add(round(h.delta, 9))
        begins.append(h.b)
        ends.append(h.e)
    if not files:
        errors.append("no .sac files")
    if references and (max(references) - min(references)).total_seconds() > 1e-3:
        errors.append(f"SAC reference times differ ({min(references)} .. {max(references)}); "
                      "use one reference per segment")
    if len(deltas) > 1:
        errors.append(f"mixed sampling intervals {sorted(deltas)}")
    if begins and max(begins) - min(begins) > 1e-3:
        errors.append(f"begin times differ by {max(begins) - min(begins):.4f} s (native limit 1e-3 s)")
    return {"segment": segment, "files": len(files),
            "reference_utc": min(references).isoformat() if references else None,
            "delta": next(iter(deltas)) if len(deltas) == 1 else None,
            "begin_s": min(begins) if begins else None, "end_s": min(ends) if ends else None,
            "errors": errors}


def segment_reference(root, segment: str) -> _dt.datetime:
    """SAC reference time shared by the segment's continuous files."""
    first = next((Path(root) / "continuous" / segment).glob("*.sac"))
    reference = read_sac_header(first).reference
    if reference is None:
        raise ValueError(f"continuous/{segment}: SAC reference time undefined")
    return reference


def validate_template(root, template: Template, rows: List[ChannelPhase], window_before_s: float,
                      window_after_s: float) -> List[str]:
    errors = []
    folder = Path(root) / "templates" / template.template_id
    for r in rows:
        f = folder / f"{r.channel}.sac"
        if not f.is_file():
            errors.append(f"{template.template_id}/{r.channel}: missing template file")
            continue
        h = read_sac_header(f)
        if h.byte_order != "<":
            errors.append(f"{f.name}: big-endian SAC")
        if h.o is None or abs(h.o) > 1e-6:
            errors.append(f"{template.template_id}/{r.channel}: template o must be 0 at the origin")
        mark = h.mark(r.mark)
        if mark is None:
            errors.append(f"{template.template_id}/{r.channel}: t{r.mark} undefined for {r.phase}")
            continue
        if h.b > mark - window_before_s + 1e-6 or h.e < mark + window_after_s - 1e-6:
            errors.append(f"{template.template_id}/{r.channel}: t{r.mark} window "
                          f"[{mark - window_before_s:.2f}, {mark + window_after_s:.2f}] not inside [{h.b:.2f}, {h.e:.2f}]")
        for name, value in (("evla", h.evla), ("evlo", h.evlo), ("evdp", h.evdp), ("stla", h.stla), ("stlo", h.stlo)):
            if value is None:
                errors.append(f"{template.template_id}/{r.channel}: SAC header {name} undefined")
    return errors
