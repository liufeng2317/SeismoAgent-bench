"""Station identifier helpers shared by HypoDD and FDTCC adapters."""
from __future__ import annotations

from typing import Optional, Tuple


def _clean_token(value: object, field_name: str) -> str:
    text = "" if value is None else str(value).strip()
    if not text:
        raise ValueError(f"{field_name} must be a non-empty station identifier")
    return text


def split_station_id(
    station_id: object,
    *,
    default_network: Optional[str] = None,
    require_network: bool = False,
) -> Tuple[Optional[str], str]:
    """Split ``NET.STA`` or bare ``STA`` into ``(network, station)``.

    Parameters
    ----------
    station_id
        Station identifier as ``NET.STA`` or bare ``STA``.
    default_network
        Optional network inserted for bare station IDs.
    require_network
        Raise for bare station IDs when true.

    Bare station codes are valid for catalog-only HypoDD because native HypoDD
    station/pick files use the station code. FDTCC waveform cross-correlation
    needs a network code before the native run starts, so callers can set
    ``require_network=True`` and optionally provide ``default_network``.
    """
    text = _clean_token(station_id, "station_id")
    if "." in text:
        net, sta = text.split(".", 1)
        net = _clean_token(net, "network")
        sta = _clean_token(sta, "station")
        return net, sta

    sta = text
    if default_network is not None and str(default_network).strip():
        return str(default_network).strip(), sta
    if require_network:
        raise ValueError(
            f"station id {text!r} has no network code. For catalog-only HypoDD this "
            "is acceptable, but FDTCC/CC needs a network code before building REAL "
            "station.dat and waveform inputs. Use NET.STA, provide separate network "
            "and station columns, or pass station_default_network only when that "
            "network matches the waveform file/inventory network convention."
        )
    return None, sta


def station_code(station_id: object) -> str:
    """Return the station component from ``NET.STA`` or bare ``STA``.

    Parameters
    ----------
    station_id
        Station identifier as ``NET.STA`` or bare ``STA``.

    Examples
    --------
    ``station_code("N.STA01")`` returns ``"STA01"`` and
    ``station_code("STA01")`` also returns ``"STA01"``.
    """
    _net, sta = split_station_id(station_id, require_network=False)
    return sta


def station_match_key(station_id: object) -> str:
    """Return the station key used for catalog-only consistency checks.

    Parameters
    ----------
    station_id
        Station identifier as ``NET.STA`` or bare ``STA``.

    Native HypoDD station/pick files use station code rather than network code,
    so catalog-only checks match ``NET.STA`` and ``STA`` by their station
    component. FDTCC/waveform workflows still need real network consistency
    before SAC/REAL input preparation.
    """
    return station_code(station_id)
