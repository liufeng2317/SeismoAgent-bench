"""Build REAL-format ``station.dat`` for FDTCC (lon lat NET STA COMP elev_km)."""
from __future__ import annotations

import os
from typing import Callable, Iterable, Optional

try:
    from ..station_id import split_station_id
except ImportError:  # pragma: no cover - legacy direct-script execution
    from station_id import split_station_id


def default_vertical_comp(net: str) -> str:
    """PB → EHZ (typical short-period); other networks → HHZ."""
    return "EHZ" if net.strip().upper() == "PB" else "HHZ"


def _split_line(line: str) -> list[str]:
    line = line.strip()
    if not line:
        return []
    codes = line.split(",")
    if len(codes) == 1:
        codes = line.split()
    return [c.strip() for c in codes]


def _normalize_header_name(s: str) -> str:
    return s.strip().lower().replace(" ", "_")


def _looks_like_header(codes: list[str]) -> bool:
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
        "network",
        "station",
        "lat",
        "lon",
    )
    return any(k in blob for k in keys)


def _collect_nonempty_rows(lines: Iterable[str]) -> list[tuple[int, list[str]]]:
    rows: list[tuple[int, list[str]]] = []
    for line_no, line in enumerate(lines, start=1):
        if line.strip().startswith("#"):
            continue
        codes = _split_line(line)
        if codes:
            rows.append((line_no, codes))
    return rows


def _resolve_header_indices(
    header_codes: list[str],
    *,
    lat_names=frozenset({"latitude", "lat", "stla"}),
    lon_names=frozenset({"longitude", "lon", "long", "lng", "stlo"}),
    elev_names=frozenset({"elevation", "elev", "elevation_m", "elev_m", "stel"}),
    net_names=frozenset({"network", "net"}),
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
) -> tuple[int, int, int, Optional[int], Optional[int]]:
    """Resolve station, optional network, lat/lon, and optional elevation columns."""
    norm = [_normalize_header_name(h) for h in header_codes]
    net_i = next((i for i, h in enumerate(norm) if h in net_names), None)
    sta_i = None
    for name in sta_names_order:
        if name in norm:
            sta_i = norm.index(name)
            break
    if sta_i is None:
        sta_i = 0
    lat_i = next((i for i, h in enumerate(norm) if h in lat_names), None)
    lon_i = next((i for i, h in enumerate(norm) if h in lon_names), None)
    elev_i = next((i for i, h in enumerate(norm) if h in elev_names), None)
    if lat_i is None or lon_i is None:
        raise ValueError(
            "Station file header must name latitude and longitude columns "
            f"(e.g. latitude, longitude); got {header_codes!r}"
        )
    return sta_i, lat_i, lon_i, elev_i, net_i


def _iter_station_records(
    fsta_path: str,
    *,
    default_network: Optional[str] = None,
) -> Iterable[tuple[str, str, float, float, float]]:
    """Yield ``(network, station, lat, lon, elevation_m)`` from flexible station tables."""
    with open(fsta_path, encoding="utf-8", errors="replace") as f:
        rows = _collect_nonempty_rows(f.readlines())
    if not rows:
        raise ValueError(f"No non-comment station rows in {fsta_path!r}")

    _line0, first = rows[0]
    if _looks_like_header(first):
        sta_i, lat_i, lon_i, elev_i, net_i = _resolve_header_indices(first)
        body = rows[1:]
    else:
        sta_i, lat_i, lon_i, elev_i, net_i = 0, 1, 2, 3, None
        body = rows

    for line_no, codes in body:
        try:
            need = max(sta_i, lat_i, lon_i) + 1
            if len(codes) < need:
                raise IndexError(f"need at least {need} columns, got {len(codes)}")
            ns = codes[sta_i].strip()
            if net_i is not None and net_i < len(codes) and "." not in ns:
                ns = f"{codes[net_i].strip()}.{ns}"
            net, sta = split_station_id(
                ns,
                default_network=default_network,
                require_network=True,
            )
            lat = float(codes[lat_i])
            lon = float(codes[lon_i])
            elev_m = 0.0
            if elev_i is not None and elev_i < len(codes) and codes[elev_i] != "":
                elev_m = float(codes[elev_i])
            yield net, sta, lat, lon, elev_m
        except Exception as e:
            raise ValueError(
                f"Error parsing line {line_no} in {fsta_path!r}: {','.join(codes)!r}. "
                "Supported FDTCC station formats: header with network.station/latitude/"
                "longitude/elevation; header with separate network and station columns; "
                "or no-header NET.STA,lat,lon[,elevation_m]. For CC/FDTCC, bare station "
                "codes require station_default_network so REAL station.dat can contain "
                "NET and STA before native execution. station_default_network must match "
                "the waveform file/inventory network convention; do not use it as a "
                "blind placeholder. "
                f"Original error: {e}"
            ) from e


def write_real_station_dat_from_fsta(
    fsta_path: str,
    out_path: str,
    *,
    vertical_comp: Optional[Callable[[str], str]] = None,
    default_network: Optional[str] = None,
) -> str:
    """
    Parse HypoDD / mk_sta station tables → REAL file.

    One line per row: ``longitude latitude NET STA COMP elev_km``.

    Parameters
    ----------
    fsta_path
        Same input as :func:`mk_sta.mk_sta`. Supports a header row with
        ``network.station`` / ``latitude`` / ``longitude`` / optional
        ``elevation`` columns, or a no-header legacy table:
        ``NET.STA,lat,lon[,elevation_m]``.
    out_path
        Destination path (parent dirs created).
    vertical_comp
        ``net -> "HHZ"|"EHZ"|…``; default :func:`default_vertical_comp`.
    default_network
        Network code to use for bare station IDs. Leave unset to require real
        network information from ``NET.STA`` or a separate ``network`` column.
        Use only when the value matches the waveform file/inventory convention.

    Returns
    -------
    str
        Absolute path to ``out_path``.
    """
    vc = vertical_comp or default_vertical_comp
    out_abs = os.path.abspath(out_path)
    os.makedirs(os.path.dirname(out_abs) or ".", exist_ok=True)

    lines: list[str] = []
    seen: set[str] = set()
    for net, sta, lat, lon, elev_m in _iter_station_records(
        fsta_path,
        default_network=default_network,
    ):
        if sta in seen:
            continue
        seen.add(sta)
        comp = vc(net)
        elev_km = elev_m / 1000.0
        lines.append(f"{lon:.6f} {lat:.6f} {net} {sta} {comp} {elev_km:.4f}\n")

    with open(out_abs, "w", encoding="utf-8") as out:
        out.writelines(lines)
    return out_abs
