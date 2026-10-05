"""Recognize event-header vs station-pick lines in phase ``.pha`` files."""
from __future__ import annotations

from typing import Sequence

from obspy import UTCDateTime


def normalize_event_magnitude(value: object, *, default: float = 0.0) -> float:
    """Return a numeric event magnitude, defaulting missing/bad values.

    Parameters
    ----------
    value
        Raw magnitude field from an event header.
    default
        Numeric value used when ``value`` is missing or cannot be parsed.

    JMA-style working catalogs may contain event headers with an empty
    magnitude field. HypoDD needs a numeric magnitude in generated native
    files, but the value is not used as a relocation control parameter. Keep
    the parser permissive and fill a neutral value instead of misclassifying
    the event header as a station-pick row.
    """
    text = "" if value is None else str(value).strip()
    if not text or text.lower() in {"nan", "none", "null", "na"}:
        return float(default)
    try:
        return float(text)
    except Exception:
        return float(default)


def looks_like_event_header_line(codes: Sequence[str]) -> bool:
    """
    True if ``codes`` is a split event header:

    - **With ID** (≥6 columns): ``origin_time, lat, lon, depth, mag, evid`` (integer ``evid`` in last field).
    - **Without ID** (5 columns): ``origin_time, lat, lon, depth, mag`` — parsers assign sequential IDs.

    ``origin_time`` may be compact ``YYYYMMDDHHMMSS.SS`` or ISO-8601.
    ``mag`` may be empty or non-numeric; downstream parsers fill it with 0.0.
    Station pick lines (``station_id, P_time, S_time, ...``) fail the time parse on field 0.
    """
    if len(codes) < 5:
        return False
    try:
        UTCDateTime(str(codes[0]).strip())
    except Exception:
        return False
    try:
        for i in range(1, 4):
            float(str(codes[i]).strip())
    except Exception:
        return False
    if len(codes) == 5:
        return True
    if len(codes) >= 6:
        try:
            int(float(str(codes[-1]).strip()))
        except Exception:
            return False
        return True
    return False
