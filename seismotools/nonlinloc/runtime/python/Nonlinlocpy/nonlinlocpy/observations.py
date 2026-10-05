"""Observation and pick-file helpers for NonLinLoc."""

from __future__ import annotations

import os
from typing import List, Optional, Sequence, Tuple

import numpy as np

from .models import PhasePick


def _station_code6(s: str) -> str:
    """Trim a station code to at most 6 characters for NLLoc text formats.
    
    Args:
        s (str): s.
    
    Returns:
        str: Result returned by the function.
    """

    t = s.strip()
    if len(t) > 6:
        return t[:6]
    return t


def load_simple_pick_table(
    path: str,
    columns: Tuple[int, int, int] = (0, 1, 2),
    *,
    first_motion_col: Optional[int] = None,
) -> List[PhasePick]:
    """Read ``station_id phase time_sec [first_motion]`` rows from a whitespace table.
    
    Args:
        path (str): path.
        columns (Tuple[int, int, int]): columns.
        first_motion_col (Optional[int]): first motion col.
    
    Returns:
        List[PhasePick]: Result returned by the function.
    """

    out: List[PhasePick] = []
    si, pi, ti = columns
    required_max = max(columns) if first_motion_col is None else max(columns + (first_motion_col,))
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        for lineno, line in enumerate(f, start=1):
            row = line.strip()
            if not row or row.startswith("#"):
                continue
            parts = row.split()
            if len(parts) <= required_max:
                raise ValueError(
                    f"Invalid pick row at {path}:{lineno}: expected columns "
                    f"station_id phase time_sec [first_motion], got {row!r}"
                )
            fm = "?"
            if first_motion_col is not None:
                fm = parts[first_motion_col]
            out.append(PhasePick(parts[si], parts[pi], float(parts[ti]), fm))
    return out


def format_nlloc_obs_lines(
    picks: Sequence[PhasePick],
    yyyymmdd: str,
    hhmm: str,
    *,
    err_mag: str = "2.00e-02",
    unused_numeric: str = "-1.00e+00",
) -> List[str]:
    """Format picks as official ``NLLOC_OBS`` phase lines.
    
    Args:
        picks (Sequence[PhasePick]): picks.
        yyyymmdd (str): yyyymmdd.
        hhmm (str): hhmm.
        err_mag (str): err mag.
        unused_numeric (str): unused numeric.
    
    Returns:
        List[str]: Result returned by the function.
    """

    if len(yyyymmdd) != 8 or len(hhmm) != 4:
        raise ValueError("yyyymmdd must be 8 chars, hhmm 4 chars (e.g. 19940217, 2216)")

    lines: List[str] = []
    tail = f"GAU  {err_mag} {unused_numeric} {unused_numeric} {unused_numeric}\n"
    for p in picks:
        sid = _station_code6(p.station_id)[:6].ljust(6)
        ph = (p.phase.strip()[:6]).ljust(6)
        fm = (p.first_motion or "?")[0]
        sec = p.time_sec
        lines.append(f"{sid}    ?    ?    ? {ph} {fm} {yyyymmdd} {hhmm}   {sec:7.4f} {tail}")
    lines.append("!END_EVENT\n")
    lines.append("!END_FILE\n")
    return lines


def write_nlloc_obs_file(
    control_file_path: str,
    content_lines: Sequence[str],
    obs_basename: str = "All.obs",
    mode: str = "w",
) -> str:
    """Write ``obs/<obs_basename>`` under a NonLinLoc run directory.
    
    Args:
        control_file_path (str): control file path.
        content_lines (Sequence[str]): content lines.
        obs_basename (str): obs basename.
        mode (str): mode.
    
    Returns:
        str: Result returned by the function.
    """

    d = os.path.join(control_file_path, "obs")
    os.makedirs(d, exist_ok=True)
    path = os.path.join(d, obs_basename)
    with open(path, mode, encoding="utf-8") as f:
        f.writelines(content_lines)
    return path


def convert_simple_pick_file_to_nlloc_obs(
    control_file_path: str,
    simple_pick_path: str,
    yyyymmdd: str,
    hhmm: str,
    *,
    obs_basename: str = "All.obs",
    mode: str = "w",
    columns: Tuple[int, int, int] = (0, 1, 2),
    first_motion_col: Optional[int] = None,
    err_mag: str = "2.00e-02",
    unused_numeric: str = "-1.00e+00",
) -> str:
    """Convert a simple pick table to ``obs/<obs_basename>`` in ``NLLOC_OBS`` format.
    
    Args:
        control_file_path (str): control file path.
        simple_pick_path (str): simple pick path.
        yyyymmdd (str): yyyymmdd.
        hhmm (str): hhmm.
        obs_basename (str): obs basename.
        mode (str): mode.
        columns (Tuple[int, int, int]): columns.
        first_motion_col (Optional[int]): first motion col.
        err_mag (str): err mag.
        unused_numeric (str): unused numeric.
    
    Returns:
        str: Result returned by the function.
    """

    picks = load_simple_pick_table(
        simple_pick_path,
        columns=columns,
        first_motion_col=first_motion_col,
    )
    lines = format_nlloc_obs_lines(
        picks,
        yyyymmdd,
        hhmm,
        err_mag=err_mag,
        unused_numeric=unused_numeric,
    )
    return write_nlloc_obs_file(
        control_file_path,
        lines,
        obs_basename=obs_basename,
        mode=mode,
    )


def filter_arrivals_by_phase_median(
    picks: Sequence[PhasePick],
    max_deviation_sec: float,
) -> List[PhasePick]:
    """Drop picks that deviate more than ``max_deviation_sec`` from phase-wise median time.
    
    Args:
        picks (Sequence[PhasePick]): picks.
        max_deviation_sec (float): max deviation sec.
    
    Returns:
        List[PhasePick]: Result returned by the function.
    """

    p_group = [p for p in picks if p.phase.upper().startswith("P")]
    s_group = [p for p in picks if p.phase.upper().startswith("S")]

    def filt(group: List[PhasePick]) -> List[PhasePick]:
        """Filter one phase group by median absolute time deviation.

        Args:
            group (List[PhasePick]): Picks for one phase family.

        Returns:
            List[PhasePick]: Picks within the allowed median deviation.
        """
        if not group:
            return []
        med = float(np.median([p.time_sec for p in group]))
        return [p for p in group if abs(p.time_sec - med) < max_deviation_sec]

    return filt(p_group) + filt(s_group)
