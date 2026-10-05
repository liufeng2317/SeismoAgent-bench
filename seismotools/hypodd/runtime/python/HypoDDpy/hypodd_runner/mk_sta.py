"""Convert flexible CSV/space station tables into HypoDD ``hypoDD_station.dat`` (STA LAT LON)."""
import os
from typing import List, Optional, Tuple

try:
    from .station_id import station_code
except ImportError:  # pragma: no cover - legacy direct-script execution
    from station_id import station_code


def _split_line(line: str) -> List[str]:
    line = line.strip()
    if not line:
        return []
    codes = line.split(",")
    if len(codes) == 1:
        codes = line.split()
    return [c.strip() for c in codes]


def _normalize_header_name(s: str) -> str:
    return s.strip().lower().replace(" ", "_")


def _looks_like_header(codes: List[str]) -> bool:
    """True if this line is a column header, not a station row."""
    if len(codes) < 3:
        return True
    try:
        if "." in codes[0] and len(codes) >= 3:
            float(codes[1])
            float(codes[2])
            return False
    except (ValueError, IndexError):
        pass
    blob = ",".join(c.lower() for c in codes)
    keys = (
        "latitude",
        "longitude",
        "elevation",
        "depth",
        "gain",
        "network",
        "station",
        "lat",
        "lon",
    )
    return any(k in blob for k in keys)


def _resolve_header_indices(
    header_codes: List[str],
    *,
    lat_names=frozenset({"latitude", "lat", "stla"}),
    lon_names=frozenset({"longitude", "lon", "long", "lng", "stlo"}),
    sta_names_order=(
        "network.station",
        "network_station",
        "net.sta",
        "net_sta",
        "ns",
        "kstnm",
        "station",
        "sta",
        "site",
    ),
) -> Tuple[int, int, int]:
    """Resolve station, latitude, and longitude columns from a header row."""
    norm = [_normalize_header_name(h) for h in header_codes]
    sta_i: Optional[int] = None
    for name in sta_names_order:
        if name in norm:
            sta_i = norm.index(name)
            break
    if sta_i is None:
        sta_i = 0
    lat_i = next((i for i, h in enumerate(norm) if h in lat_names), None)
    lon_i = next((i for i, h in enumerate(norm) if h in lon_names), None)
    if lat_i is None or lon_i is None:
        raise ValueError(
            "Station file header must name latitude and longitude columns "
            f"(e.g. latitude, longitude); got {header_codes!r}"
        )
    return sta_i, lat_i, lon_i


def _collect_nonempty_rows(lines: List[str]) -> List[Tuple[int, List[str]]]:
    """(1-based line number, split tokens) for each non-empty, non-comment line."""
    out: List[Tuple[int, List[str]]] = []
    for i, line in enumerate(lines, start=1):
        if line.strip().startswith("#"):
            continue
        codes = _split_line(line)
        if not codes:
            continue
        out.append((i, codes))
    return out


def mk_sta(in_sta_file, output_folder):
    """
    Create a station file for HypoDD from an input CSV-like station file.

    Parameters
    ----------
    in_sta_file : str
        Path to the input station file. Supports:

        * **Header row** — column names are matched case-insensitively, order-free.
          Recognized names include ``network.station`` / ``network_station`` / ``sta`` /
          ``station`` / ``kstnm`` for station IDs, and ``latitude`` / ``lat``,
          ``longitude`` / ``lon``, etc.
        * **No header** — each line: ``station_id, latitude, longitude, ...``.
          ``station_id`` may be ``NET.STA`` or a bare station code. Native HypoDD
          uses only the station code.
    output_folder : str
        Directory where ``hypoDD_station.dat`` is written.

    Examples
    --------
    >>> mk_sta('example_pal.sta', 'output_folder')
    """
    fout = open(os.path.join(output_folder, "hypoDD_station.dat"), "w")
    done_list = []
    with open(in_sta_file, encoding="utf-8", errors="replace") as f:
        lines = f.readlines()

    rows = _collect_nonempty_rows(lines)
    if not rows:
        fout.close()
        raise ValueError(f"No non-comment lines in '{in_sta_file}'")

    _line_no0, first_codes = rows[0]
    if _looks_like_header(first_codes):
        sta_i, lat_i, lon_i = _resolve_header_indices(first_codes)
        body = rows[1:]
    else:
        sta_i, lat_i, lon_i = 0, 1, 2
        body = rows

    for line_no, codes in body:
        line_repr = ",".join(codes)
        try:
            need = max(sta_i, lat_i, lon_i) + 1
            if len(codes) < need:
                raise IndexError(f"need at least {need} columns, got {len(codes)}")
            ns = codes[sta_i]
            lat, lon = float(codes[lat_i]), float(codes[lon_i])
            sta = station_code(ns)
            if sta in done_list:
                continue
            done_list.append(sta)
            fout.write("{} {} {}\n".format(sta, lat, lon))
        except Exception as e:
            fout.close()
            raise ValueError(
                f"Error parsing line {line_no} in '{in_sta_file}': {line_repr!r}.\n"
                "With header: name columns station/network.station, latitude, longitude. "
                "Without header: station_id,latitude,longitude,... where station_id may be "
                "NET.STA or a bare station code.\n"
                f"Original error: {e}"
            ) from e
    fout.close()
    return
