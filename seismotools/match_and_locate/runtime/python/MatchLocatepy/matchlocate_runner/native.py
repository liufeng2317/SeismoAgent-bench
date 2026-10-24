"""MatchLocate2 native file formats, grid arithmetic and command construction.

Conventions follow the native program exactly:

* ``INPUT.in``: first line is the row count, then one row per correlated
  channel-phase: ``template_sac trace_sac dt_dgc/dt_dh mark phase``. ``dt_dgc``
  is the horizontal slowness in s/degree (the program measures epicentral
  change in great-circle degrees) and ``dt_dh`` the vertical slowness in s/km
  (positive when a deeper source arrives later). ``mark`` is the SAC time-mark
  index carrying the phase travel time in the template (1 -> t1, 2 -> t2).
* The grid has ``int(2*half/step + 1)`` nodes per axis starting at
  ``center - half``; a zero half-width gives a single node (the matched-filter
  case) but the step must still be non-zero.
* ``EventCase.out`` rows: ``index time lat lon depth mag cc nmad`` where
  ``time`` is the detected origin time in seconds relative to the continuous
  traces' reference (o = 0).
"""
from __future__ import annotations

import bisect
import dataclasses
import math
from pathlib import Path
from typing import Iterable, List, Optional, Sequence

KM_PER_DEG = 6371.0 * math.pi / 180.0
MAX_NATIVE_PATH = 255          # template/trace paths are read into char[256]
SELECTFINAL_MAX_ROWS = 100000  # NPEVE in SelectFinal.c


@dataclasses.dataclass(frozen=True)
class InputRow:
    template_path: str
    trace_path: str
    slowness_h_s_per_deg: float
    slowness_v_s_per_km: float
    mark: int
    phase: str


def write_input_file(path, rows: Sequence[InputRow]) -> None:
    lines = [str(len(rows))]
    for row in rows:
        for value in (row.template_path, row.trace_path, row.phase):
            if not value or any(ch.isspace() for ch in value):
                raise ValueError(f"INPUT.in fields must be non-empty and contain no whitespace: {value!r}")
        for value in (row.template_path, row.trace_path):
            if len(value) > MAX_NATIVE_PATH:
                raise ValueError(f"path longer than {MAX_NATIVE_PATH} characters: {value}")
        if row.mark not in range(10):
            raise ValueError(f"SAC time mark must be 0-9, got {row.mark}")
        lines.append(f"{row.template_path} {row.trace_path} "
                     f"{row.slowness_h_s_per_deg:.6f}/{row.slowness_v_s_per_km:.6e} "
                     f"{row.mark} {row.phase}")
    Path(path).write_text("\n".join(lines) + "\n", encoding="ascii")


def native_axis_count(half: float, step: float) -> int:
    """Node count exactly as MatchLocate2 computes it: (int)(2*half/step + 1)."""
    return int(2.0 * half / step + 1.0)


@dataclasses.dataclass(frozen=True)
class SearchGrid:
    """Grid half-widths and steps in native units (degrees, degrees, km)."""
    half_lat_deg: float
    half_lon_deg: float
    half_depth_km: float
    step_lat_deg: float
    step_lon_deg: float
    step_depth_km: float

    def __post_init__(self) -> None:
        for name in ("step_lat_deg", "step_lon_deg", "step_depth_km"):
            if not getattr(self, name) > 0:
                raise ValueError(f"{name} must be positive (the native grid divides by it)")
        for name in ("half_lat_deg", "half_lon_deg", "half_depth_km"):
            if getattr(self, name) < 0:
                raise ValueError(f"{name} must be non-negative")

    @classmethod
    def from_km(cls, latitude: float, half_width_km: float, step_km: float,
                half_depth_km: float, step_depth_km: float) -> "SearchGrid":
        """Square horizontal grid with the same node spacing in km on both axes.

        Half-widths are rounded to whole steps so the grid is symmetric about
        the template and the node count is what ``native_axis_count`` reports.
        """
        if step_km <= 0 or step_depth_km <= 0:
            raise ValueError("grid steps must be positive")
        n_h = int(round(half_width_km / step_km))
        n_z = int(round(half_depth_km / step_depth_km))
        dlat = step_km / KM_PER_DEG
        dlon = step_km / (KM_PER_DEG * math.cos(math.radians(latitude)))
        return cls(n_h * dlat, n_h * dlon, n_z * step_depth_km, dlat, dlon, step_depth_km)

    def formatted(self) -> tuple:
        """-R and -I strings whose parsed values give the intended node counts."""
        values = []
        for half, step in ((self.half_lat_deg, self.step_lat_deg),
                           (self.half_lon_deg, self.step_lon_deg),
                           (self.half_depth_km, self.step_depth_km)):
            n = int(round(half / step))
            step_s, half_s = f"{step:.10g}", f"{half:.10g}"
            step_v = float(step_s)
            if native_axis_count(float(half_s), step_v) != 2 * n + 1:
                # The native count truncates 2*half/step + 1; printing the two
                # values separately can lose a node (seen: 8 instead of 9
                # columns for a km grid converted to degrees). Derive the
                # half-width from the printed step plus 1e-4 of a step: exactly
                # 2n + 1 nodes, grid shifted by ~1e-4 step. Values that already
                # give the right count are passed unchanged.
                half_s = f"{n * step_v + 1e-4 * step_v:.10f}" if n else "0"
            if native_axis_count(float(half_s), step_v) != 2 * n + 1:
                raise AssertionError(f"grid axis {half}/{step}: native count != {2 * n + 1}")
            values.append((half_s, step_s))
        r = "/".join(v[0] for v in values)
        i = "/".join(v[1] for v in values)
        return r, i

    def node_count(self) -> int:
        r, i = self.formatted()
        halves = [float(x) for x in r.split("/")]
        steps = [float(x) for x in i.split("/")]
        n = 1
        for half, step in zip(halves, steps):
            n *= native_axis_count(half, step)
        return n


@dataclasses.dataclass(frozen=True)
class DetectionParams:
    window_s: float
    before_s: float
    after_s: float
    cc_threshold: float
    mad_threshold: float
    min_separation_s: float
    output_mode: int = 0

    def __post_init__(self) -> None:
        if self.window_s <= 0 or self.before_s < 0 or self.after_s <= 0:
            raise ValueError("window/before/after must be positive (before may be 0)")
        if self.window_s > self.before_s + self.after_s + 1e-9:
            # The template is cut over [mark-before, mark+after]; a longer CC
            # window would read past the native template buffer.
            raise ValueError("window_s must not exceed before_s + after_s")
        if self.output_mode not in (0, 1, 2, 3):
            raise ValueError("output_mode must be 0, 1, 2 or 3")


def build_command(binary, center: Sequence[float], grid: SearchGrid,
                  params: DetectionParams, input_name: str = "INPUT.in") -> List[str]:
    lat, lon, depth = center
    r, i = grid.formatted()
    return [str(binary),
            f"-F{lat:.6f}/{lon:.6f}/{depth:.4f}",
            f"-R{r}", f"-I{i}",
            f"-T{params.window_s}/{params.before_s}/{params.after_s}",
            f"-H{params.cc_threshold}/{params.mad_threshold}",
            f"-D{params.min_separation_s}",
            f"-O{params.output_mode}",
            input_name]


@dataclasses.dataclass(frozen=True)
class Detection:
    time_s: float
    latitude: float
    longitude: float
    depth_km: float
    magnitude: float
    cc: float
    nmad: float
    template_id: str = ""


def parse_eventcase(path, template_id: str = "") -> List[Detection]:
    """Parse a native EventCase.out (one template, one continuous segment)."""
    rows = []
    for line in Path(path).read_text().splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        parts = line.split()
        if len(parts) < 8:
            raise ValueError(f"{path}: malformed EventCase row: {line!r}")
        rows.append(Detection(*(float(v) for v in parts[1:8]), template_id=template_id))
    return rows


def write_selectfinal_input(path, rows: Iterable[Detection]) -> int:
    n = 0
    with Path(path).open("w", encoding="ascii") as handle:
        for d in rows:
            if not d.template_id or any(ch.isspace() for ch in d.template_id):
                raise ValueError(f"template ids must be non-empty without whitespace: {d.template_id!r}")
            handle.write(f"{d.time_s:.3f} {d.latitude:.4f} {d.longitude:.4f} {d.depth_km:.2f} "
                         f"{d.magnitude:.2f} {d.cc:.4f} {d.nmad:.4f} {d.template_id}\n")
            n += 1
    if n > SELECTFINAL_MAX_ROWS:
        raise ValueError(f"native SelectFinal holds at most {SELECTFINAL_MAX_ROWS} rows; got {n}")
    return n


def parse_selectfinal(path) -> List[Detection]:
    rows = []
    for line in Path(path).read_text().splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        parts = line.split()
        rows.append(Detection(*(float(v) for v in parts[1:8]), template_id=parts[8]))
    return rows


def merge_detections(rows: Iterable[Detection], cc_threshold: float, mad_threshold: float,
                     min_separation_s: float) -> List[Detection]:
    """Python port of SelectFinal's selection (no NPEVE row limit).

    Candidates passing ``nmad >= mad_threshold and cc >= cc_threshold`` are
    visited in decreasing N(*MAD); a candidate is kept when it is more than
    ``min_separation_s`` from every kept event, or when cc == 1.0 (a template's
    self-detection is always kept). The result is sorted by time. Values are
    compared after the same text rounding the native merge reads, so feed it
    rows parsed from native output.
    """
    candidates = [d for d in rows if d.nmad >= mad_threshold and d.cc >= cc_threshold]
    candidates.sort(key=lambda d: -d.nmad)
    kept: List[Detection] = []
    kept_times: List[float] = []
    for d in candidates:
        pos = bisect.bisect_left(kept_times, d.time_s)
        isolated = True
        for neighbor in (pos - 1, pos):
            if 0 <= neighbor < len(kept_times) and abs(d.time_s - kept_times[neighbor]) <= min_separation_s:
                isolated = False
        if isolated or d.cc == 1.0:
            kept_times.insert(pos, d.time_s)
            kept.insert(pos, d)
    return kept
