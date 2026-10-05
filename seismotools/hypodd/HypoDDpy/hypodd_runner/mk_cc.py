"""Build HypoDD cross-correlation differential-time file ``dt.cc``.

``ph2dt`` only produces **catalog** differential times (``dt.ct``): for each event
pair and station it writes two absolute times ``t1``, ``t2``; HypoDD uses ``t1-t2``.

**Cross-correlation** delays are **not** computed by ph2dt. You obtain them from
waveforms (e.g. ObsPy time-domain cross-correlation on P/S windows), then write
``dt.cc`` in the format HypoDD reads in ``getdata.f``:

- **Pair header** (line starting with ``#``): four fields —
  ``#``, ``cusp_id_1``, ``cusp_id_2``, ``otc`` (origin-time correction in seconds).
  HypoDD subtracts ``otc`` from each following ``dt`` for that pair.
  If ``otc`` equals ``-999`` (within 0.001), the **entire pair is skipped**.
  For a first run with uncorrected CC lags, use ``otc=0.0``.
- **Data lines** (no ``#``): ``station``, ``dt_sec``, ``weight``, ``phase``
  (``P`` or ``S``). ``station`` must match ``hypoDD_station.dat`` (same short code
  as in ``mk_sta``, up to 7 characters).

Event IDs must be the same **cusp ids** as in ``event.dat`` / your phase file.

Workflow sketch (outside this module):

1. Choose event pairs (often neighbors within a few km, same as ph2dt linking).
2. For each pair, station, and phase: cut aligned windows, band-pass, compute
   lag (e.g. ``numpy.correlate`` / ObsPy); ``dt_sec`` is the differential delay
   (seconds) consistent with HypoDD sign convention (see Waldhauser, 2001).
3. Assign a weight (e.g. normalized correlation coefficient).
4. Call :func:`write_dt_cc` (or append lines with :func:`format_dt_cc_pair_header`
   and :func:`format_dt_cc_data_line`).

References: HypoDD user guide (USGS OFR 01-113); ``source/src/hypoDD/getdata.f``.
"""
from __future__ import annotations

import os
from typing import Iterable, List, Mapping, Sequence, TextIO, Tuple, Union

Row = Tuple[str, float, float, str]
PairInput = Mapping[str, Union[int, float, Sequence[Row]]]


def format_dt_cc_pair_header(cusp1: int, cusp2: int, otc: float = 0.0) -> str:
    """One ``#`` line: ``# cusp1 cusp2 otc`` (free format, matches ``getdata.f``)."""
    return f"# {int(cusp1):9d} {int(cusp2):9d} {float(otc):.6f}\n"


def format_dt_cc_data_line(
    station: str, dt_sec: float, weight: float, phase: str
) -> str:
    """
    One observation: station, CC lag (s), weight, P or S.

    Parameters
    ----------
    station
        Station code matching native ``hypoDD_station.dat``.
    dt_sec
        Cross-correlation differential delay in seconds.
    weight
        Observation weight, commonly a correlation coefficient or derived
        confidence weight.
    phase
        Phase code: ``"P"`` or ``"S"``.

    Layout is similar to ph2dt's ``dt.ct`` body but with a **single** time column
    instead of two absolute times.
    """
    sta = station.strip()[:7].ljust(7)
    ph = phase.strip().upper()
    if ph not in ("P", "S"):
        raise ValueError(f"phase must be 'P' or 'S', got {phase!r}")
    return f"{sta} {float(dt_sec):7.3f} {float(weight):6.4f} {ph}\n"


def write_dt_cc(
    out_path: str,
    pairs: Sequence[PairInput],
    *,
    mode: str = "w",
) -> None:
    """
    Write a full ``dt.cc`` file.

    Parameters
    ----------
    out_path
        Output path (e.g. ``.../dt_0-0.cc`` next to ``dt_0-0.ct``).
    pairs
        Each element is a mapping with keys:

        - ``cusp1`` (int), ``cusp2`` (int)
        - ``otc`` (float, optional): default ``0.0``
        - ``rows`` (sequence of ``(station, dt_sec, weight, phase)``)

    mode
        ``"w"`` or ``"a"`` (append).
    """
    d = os.path.dirname(os.path.abspath(out_path))
    if d:
        os.makedirs(d, exist_ok=True)
    with open(out_path, mode, encoding="utf-8") as fh:
        for p in pairs:
            c1 = int(p["cusp1"])
            c2 = int(p["cusp2"])
            otc = float(p.get("otc", 0.0))
            rows: Sequence[Row] = p["rows"]  # type: ignore[assignment]
            fh.write(format_dt_cc_pair_header(c1, c2, otc))
            for station, dt_sec, weight, phase in rows:
                fh.write(format_dt_cc_data_line(station, dt_sec, weight, phase))


def filter_pairs_for_grid(
    pairs: Sequence[PairInput], evid_set: set,
) -> List[dict]:
    """
    Keep only pairs whose both cusp ids are in ``evid_set`` (e.g. one grid from
    ``evid_lists[i][j]`` as a set of ints).
    """
    out: List[dict] = []
    for p in pairs:
        c1, c2 = int(p["cusp1"]), int(p["cusp2"])
        if c1 in evid_set and c2 in evid_set:
            out.append(dict(p))
    return out


def write_dt_cc_per_grid(
    output_folder: str,
    pairs: Sequence[PairInput],
    evid_lists,
    num_grids: Sequence[int],
) -> None:
    """
    Write ``dt_{i}-{j}.cc`` for each grid, same indexing as ``mk_pha`` / ph2dt.

    Parameters
    ----------
    output_folder
        Directory where per-grid ``dt_{i}-{j}.cc`` files are written.
    pairs
        Sequence of pair mappings accepted by :func:`write_dt_cc`. Each mapping
        must contain ``cusp1``, ``cusp2``, and ``rows``; optional ``otc``
        defaults to ``0.0``.
    evid_lists
        Nested structure ``evid_lists[i][j]`` -> list of event ids (ints).
    num_grids
        ``(nx, ny)`` like ``config.num_grids``.
    """
    for i in range(num_grids[0]):
        for j in range(num_grids[1]):
            evs = evid_lists[i][j]
            if hasattr(evs, "tolist"):
                evs = evs.tolist()
            evid_set = {int(e) for e in evs}
            sub = filter_pairs_for_grid(pairs, evid_set)
            path = os.path.join(output_folder, f"dt_{i}-{j}.cc")
            write_dt_cc(path, sub)


def append_pair(
    fh: TextIO,
    cusp1: int,
    cusp2: int,
    otc: float,
    rows: Iterable[Row],
) -> None:
    """Write one pair block to an open text file (streaming / large catalogs).

    Parameters
    ----------
    fh
        Open text file handle positioned where the pair block should be written.
    cusp1, cusp2
        Event IDs for the HypoDD pair header.
    otc
        Origin-time correction in seconds for the pair header.
    rows
        Iterable of ``(station, dt_sec, weight, phase)`` observations.
    """
    fh.write(format_dt_cc_pair_header(cusp1, cusp2, otc))
    for station, dt_sec, weight, phase in rows:
        fh.write(format_dt_cc_data_line(station, dt_sec, weight, phase))
