"""Time-window normalization helpers for public HypoDD/FDTCC APIs."""
from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date, datetime
from typing import Any, List, Optional, Sequence, Tuple

from obspy import UTCDateTime


_DATE_ONLY_RE = re.compile(r"^\d{4}(?:[-/]?\d{2}){2}$")


@dataclass
class TimeWindowPlan:
    """Planned time window with diagnostics for safe independent execution.

    ``event_count`` is the number of selected events expected in this window.
    ``merged_from`` records the base windows that were merged to avoid sparse
    windows. ``parallel_safe`` is true because planned windows are disjoint and
    should write to separate output directories.
    """

    window_id: str
    start: str
    end: str
    ot_range: str
    event_count: int
    merged_from: List[str]
    reason: str
    parallel_safe: bool = True

    def as_tuple(self) -> Tuple[str, str]:
        """Return ``(start, end)`` in date-string form."""
        return self.start, self.end

    def as_dict(self) -> dict:
        """Return a JSON-serializable plan summary."""
        return {
            "window_id": self.window_id,
            "start": self.start,
            "end": self.end,
            "ot_range": self.ot_range,
            "event_count": self.event_count,
            "merged_from": list(self.merged_from),
            "reason": self.reason,
            "parallel_safe": self.parallel_safe,
        }


def _is_date_only_value(value: Any) -> bool:
    """Return true when ``value`` expresses a calendar date without time of day."""
    if isinstance(value, datetime):
        return False
    if isinstance(value, date):
        return True
    if isinstance(value, str):
        text = value.strip()
        if _DATE_ONLY_RE.match(text):
            return True
        return "T" not in text and ":" not in text and len(text) <= 10
    return False


def _to_utc(value: Any) -> UTCDateTime:
    if isinstance(value, UTCDateTime):
        return value
    return UTCDateTime(value)


def _floor_date_yyyymmdd(value: Any) -> str:
    """Floor a supported date/datetime value to ``YYYYMMDD``."""
    return _to_utc(value).strftime("%Y%m%d")


def _ceil_date_yyyymmdd(value: Any) -> str:
    """Ceil a supported date/datetime value to a day-boundary ``YYYYMMDD``.

    Date-only inputs are already day boundaries and are kept unchanged. Datetime
    inputs with any non-zero time component are rounded up to the next day.
    """
    utc = _to_utc(value)
    if _is_date_only_value(value):
        return utc.strftime("%Y%m%d")
    at_midnight = (
        utc.hour == 0
        and utc.minute == 0
        and utc.second == 0
        and utc.microsecond == 0
    )
    if at_midnight:
        return utc.strftime("%Y%m%d")
    return (UTCDateTime(utc.year, utc.month, utc.day) + 86400).strftime("%Y%m%d")


def _split_range_string(text: str) -> Tuple[str, str]:
    """Split common human-readable range strings into start/end tokens."""
    stripped = text.strip()
    if re.match(r"^\d{8}-\d{8}$", stripped):
        return stripped[:8], stripped[9:]

    separators = (" to ", " TO ", " To ", " until ", " UNTIL ", " - ", "..", ",", ";", "~", "至")
    for sep in separators:
        if sep in stripped:
            left, right = stripped.split(sep, 1)
            if left.strip() and right.strip():
                return left.strip(), right.strip()
    raise ValueError(
        "ot_range must be 'YYYYMMDD-YYYYMMDD', a two-value date sequence, "
        "or a range string using separators such as ' to ', ' - ', ',', '~', or '至'"
    )


def normalize_ot_range(ot_range: Any) -> str:
    """Normalize public time-window input to ``YYYYMMDD-YYYYMMDD``.

    Parameters
    ----------
    ot_range
        String range or two-value date/time sequence.

    Accepted forms include:
    - ``"20190704-20190707"``
    - ``("2019-07-04", "2019-07-07")``
    - ``(UTCDateTime(...), UTCDateTime(...))``
    - ``(datetime.datetime(...), datetime.datetime(...))``

    The start value is floored to its calendar date. The end value is ceiled to
    the next calendar date only when it contains a non-midnight time of day.
    """
    if isinstance(ot_range, str):
        start, end = _split_range_string(ot_range)
    else:
        try:
            start, end = ot_range
        except Exception as exc:
            raise ValueError(
                "ot_range must be 'YYYYMMDD-YYYYMMDD' or a two-value date sequence"
            ) from exc

    normalized = f"{_floor_date_yyyymmdd(start)}-{_ceil_date_yyyymmdd(end)}"
    ot_min, ot_max = [UTCDateTime(part) for part in normalized.split("-")]
    if ot_min >= ot_max:
        raise ValueError(f"Invalid ot_range '{normalized}': start must be before end")
    return normalized


def _date_text(value: Any) -> str:
    """Return a date-only ``YYYY-MM-DD`` string."""
    return _to_utc(value).strftime("%Y-%m-%d")


def _month_start(value: Any) -> UTCDateTime:
    utc = _to_utc(value)
    return UTCDateTime(utc.year, utc.month, 1)


def _next_month(value: Any) -> UTCDateTime:
    utc = _to_utc(value)
    if utc.month == 12:
        return UTCDateTime(utc.year + 1, 1, 1)
    return UTCDateTime(utc.year, utc.month + 1, 1)


def _day_start(value: Any) -> UTCDateTime:
    utc = _to_utc(value)
    return UTCDateTime(utc.year, utc.month, utc.day)


def _next_base_boundary(value: UTCDateTime, *, base: str, window_days: Optional[int]) -> UTCDateTime:
    if base == "month":
        return _next_month(value)
    if base == "day":
        return value + 86400
    if base == "days":
        if window_days is None or int(window_days) <= 0:
            raise ValueError("window_days must be a positive integer when base='days'")
        return value + int(window_days) * 86400
    raise ValueError("base must be 'month', 'day', or 'days'")


def _floor_base_boundary(value: UTCDateTime, *, base: str) -> UTCDateTime:
    if base == "month":
        return _month_start(value)
    if base in {"day", "days"}:
        return _day_start(value)
    raise ValueError("base must be 'month', 'day', or 'days'")


def _base_windows(
    start: UTCDateTime,
    end: UTCDateTime,
    *,
    base: str,
    window_days: Optional[int],
) -> List[Tuple[UTCDateTime, UTCDateTime]]:
    windows: List[Tuple[UTCDateTime, UTCDateTime]] = []
    current = start
    while current < end:
        next_end = _next_base_boundary(current, base=base, window_days=window_days)
        windows.append((current, min(next_end, end)))
        current = next_end
    return windows


def _event_count(times: Sequence[UTCDateTime], start: UTCDateTime, end: UTCDateTime) -> int:
    return sum(1 for time in times if start < time < end)


def plan_time_windows(
    event_times: Sequence[Any],
    *,
    base: str = "month",
    window_days: Optional[int] = None,
    min_events_per_window: int = 100,
    max_events_per_window: Optional[int] = None,
    start: Optional[Any] = None,
    end: Optional[Any] = None,
    window_prefix: str = "window",
) -> List[TimeWindowPlan]:
    """Plan disjoint time windows from event times.

    Parameters
    ----------
    event_times
        Event origin times accepted by ObsPy ``UTCDateTime``.
    base, window_days
        Base window size. Use ``base="month"``, ``base="day"``, or
        ``base="days"`` with positive ``window_days``.
    min_events_per_window, max_events_per_window
        Event-count controls for merging or rejecting windows.
    start, end
        Optional planning bounds. If omitted, the first and last event dates
        define the span.
    window_prefix
        Prefix used for returned window IDs.

    The planner first creates base windows (monthly by default), merges sparse
    neighboring windows until ``min_events_per_window`` is reached, and rejects
    windows that exceed ``max_events_per_window``. Use the coarsest base that
    keeps every native window below the active limit; the planner is not meant
    to create the smallest possible windows. It returns diagnostics so callers
    can log why a window was merged or kept.
    """
    times = sorted(_to_utc(time) for time in event_times)
    if not times:
        raise ValueError("event_times must contain at least one event time")
    min_events = int(min_events_per_window)
    if min_events <= 0:
        raise ValueError("min_events_per_window must be a positive integer")
    max_events = None if max_events_per_window is None else int(max_events_per_window)
    if max_events is not None and max_events <= 0:
        raise ValueError("max_events_per_window must be a positive integer when set")
    if max_events is not None and min_events > max_events:
        raise ValueError("min_events_per_window cannot exceed max_events_per_window")

    start_utc = _to_utc(start) if start is not None else _floor_base_boundary(times[0], base=base)
    end_utc = _to_utc(end) if end is not None else _next_base_boundary(
        _floor_base_boundary(times[-1], base=base),
        base=base,
        window_days=window_days,
    )
    if start_utc >= end_utc:
        raise ValueError("planning start must be before planning end")

    raw_windows = []
    for raw_start, raw_end in _base_windows(
        start_utc,
        end_utc,
        base=base,
        window_days=window_days,
    ):
        count = _event_count(times, raw_start, raw_end)
        raw_windows.append(
            {
                "start": raw_start,
                "end": raw_end,
                "count": count,
                "label": f"{raw_start.strftime('%Y%m%d')}-{raw_end.strftime('%Y%m%d')}",
            }
        )

    plans: List[TimeWindowPlan] = []
    current_start = None
    current_end = None
    current_count = 0
    current_labels: List[str] = []

    def flush(reason: str) -> None:
        nonlocal current_start, current_end, current_count, current_labels
        if current_start is None or current_end is None:
            return
        if max_events is not None and current_count > max_events:
            raise ValueError(
                "Planned time window exceeds max_events_per_window: "
                f"{current_start.strftime('%Y%m%d')}-{current_end.strftime('%Y%m%d')} "
                f"has event_count={current_count} > {max_events}. This limit is "
                "too small for the selected base/window unit; lowering "
                "max_events_per_window will make this failure more likely. Use a "
                "next-smaller planning unit such as base='day' or a smaller "
                "window_days value only when the current coarse unit exceeds the "
                "limit, or increase max_events_per_window while keeping each "
                "native window below compiled MAXEVE. If base='day' "
                "already produces more events than max_events_per_window, the "
                "planner cannot split that day by event count; choose a larger "
                "limit, narrow the scientific selection, or use an explicitly "
                "justified task-specific split. Increasing native MAXEVE requires "
                "rebuilding HypoDD and should be a separate maintenance task."
            )
        index = len(plans) + 1
        start_text = _date_text(current_start)
        end_text = _date_text(current_end)
        ot_range = normalize_ot_range((start_text, end_text))
        plans.append(
            TimeWindowPlan(
                window_id=f"{window_prefix}_{index:03d}_{ot_range.replace('-', '_')}",
                start=start_text,
                end=end_text,
                ot_range=ot_range,
                event_count=current_count,
                merged_from=list(current_labels),
                reason=reason,
            )
        )
        current_start = None
        current_end = None
        current_count = 0
        current_labels = []

    for raw in raw_windows:
        if raw["count"] == 0 and current_start is None:
            continue
        if current_start is None:
            current_start = raw["start"]
            current_end = raw["end"]
            current_count = raw["count"]
            current_labels = [raw["label"]]
        else:
            candidate_count = current_count + raw["count"]
            if (
                max_events is not None
                and raw["count"] > 0
                and candidate_count > max_events
            ):
                reason = (
                    "base_window"
                    if len(current_labels) == 1 and current_count >= min_events
                    else "merged_sparse"
                    if current_count >= min_events
                    else "sparse_kept_to_avoid_max_events"
                )
                flush(reason)
                current_start = raw["start"]
                current_end = raw["end"]
                current_count = raw["count"]
                current_labels = [raw["label"]]
            else:
                current_end = raw["end"]
                current_count = candidate_count
                current_labels.append(raw["label"])

        if current_count >= min_events:
            flush("base_window" if len(current_labels) == 1 else "merged_sparse")

    if current_start is not None:
        if plans and current_count < min_events:
            previous = plans.pop()
            merged_labels = previous.merged_from + current_labels
            merged_count = previous.event_count + current_count
            if max_events is not None and merged_count > max_events:
                plans.append(previous)
                flush("sparse_tail_kept_to_avoid_max_events")
            else:
                start_text = previous.start
                end_text = _date_text(current_end)
                ot_range = normalize_ot_range((start_text, end_text))
                index = len(plans) + 1
                plans.append(
                    TimeWindowPlan(
                        window_id=f"{window_prefix}_{index:03d}_{ot_range.replace('-', '_')}",
                        start=start_text,
                        end=end_text,
                        ot_range=ot_range,
                        event_count=merged_count,
                        merged_from=merged_labels,
                        reason="merged_sparse_tail",
                    )
                )
        else:
            flush("sparse_tail")

    if not plans:
        raise ValueError("No non-empty time windows could be planned")
    return plans
