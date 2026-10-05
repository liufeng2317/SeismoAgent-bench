"""Build hypodd_runner phase/station inputs from simple CSV tables.

The public preparation helper accepts common source-column aliases so agents can
normalize raw catalog tables without hand-writing one-off parsers:

- event id: ``event_id``, ``evid``, ``id``.
- origin time: ``origin_time``, ``time``, ``ot``, ``datetime``.
- event latitude/longitude/depth: ``latitude``/``lat``,
  ``longitude``/``lon``/``lng``, ``depth_km``/``depth``/``dep``.
- magnitude: ``magnitude``, ``mag``, ``ml``.
- station id: ``station_id``, ``station_code``, ``network.station``,
  ``station``, ``sta``.
- P/S pick times: ``p_pick_time``/``p_time``/``tp``/``p`` and
  ``s_pick_time``/``s_time``/``ts``/``s``.
- station elevation/network: ``elevation_m``/``elev_m``/``elevation``/``elev``
  and ``network``/``net``.

Use ``column_map`` for source files that use different names. Table-specific
keys such as ``event.latitude``, ``pick.station_id`` and ``station.longitude``
override generic keys.
"""
from __future__ import annotations

import csv
import json
import os
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Set, Tuple

from .station_id import split_station_id, station_match_key


_EVENT_ID_NAMES = ("event_id", "evid", "id")
_ORIGIN_TIME_NAMES = ("origin_time", "time", "ot", "datetime")
_LAT_NAMES = ("latitude", "lat")
_LON_NAMES = ("longitude", "lon", "lng")
_DEPTH_NAMES = ("depth_km", "depth", "dep")
_MAG_NAMES = ("magnitude", "mag", "ml")
_STATION_NAMES = ("station_id", "station_code", "network.station", "station", "sta")
_P_PICK_NAMES = ("p_pick_time", "p_time", "tp", "p")
_S_PICK_NAMES = ("s_pick_time", "s_time", "ts", "s")
_ELEV_NAMES = ("elevation_m", "elev_m", "elevation", "elev")
_NETWORK_NAMES = ("network", "net")


@dataclass
class HypoddInputBuildResult:
    """Summary returned by :func:`build_hypodd_inputs`.

    Attributes
    ----------
    phase_path, station_path
        Absolute paths to generated package-ready ``phase.dat`` and
        ``station.sta`` files.
    event_count, pick_row_count, station_count
        Row counts read from the source event, pick, and station CSV tables.
    filled_magnitudes
        Number of event rows whose missing/bad magnitude was written as ``0.0``.
    defaulted_station_networks
        Number of station identifiers that received ``station_default_network``.
        For catalog-only runs this is usually ``0`` because bare station codes
        are acceptable when station and phase files match.
    manifest_path
        Path to ``input_preparation_manifest.json`` when ``write_manifest=True``.
    warnings
        Non-blocking preparation issues, such as unused stations or events with
        no picks. Blocking issues raise when ``strict=True``.
    """

    phase_path: str
    station_path: str
    event_count: int
    pick_row_count: int
    station_count: int
    filled_magnitudes: int
    defaulted_station_networks: int
    manifest_path: str = ""
    warnings: Optional[List[str]] = None

    def as_dict(self) -> Dict[str, object]:
        return {
            "phase_path": self.phase_path,
            "station_path": self.station_path,
            "event_count": self.event_count,
            "pick_row_count": self.pick_row_count,
            "station_count": self.station_count,
            "filled_magnitudes": self.filled_magnitudes,
            "defaulted_station_networks": self.defaulted_station_networks,
            "manifest_path": self.manifest_path,
            "warnings": list(self.warnings or []),
        }


def _norm_name(name: str) -> str:
    return str(name).strip().lower().replace(" ", "_")


def _resolve_column(
    row: Mapping[str, str],
    names: Sequence[str],
    *,
    column_map: Optional[Mapping[str, str]] = None,
    canonical: Optional[str] = None,
    context: Optional[str] = None,
) -> Optional[str]:
    norm_to_key = {_norm_name(k): k for k in row.keys()}
    if column_map and canonical:
        map_keys = []
        if context:
            map_keys.extend([f"{context}.{canonical}", f"{context}_{canonical}"])
        map_keys.append(canonical)
        for map_key in map_keys:
            mapped = column_map.get(map_key)
            if mapped:
                key = norm_to_key.get(_norm_name(mapped))
                if key is None:
                    raise ValueError(
                        f"column_map maps {map_key!r} to {mapped!r}, but that column is "
                        f"not present. available_columns={list(row.keys())!r}"
                    )
                return key
    for name in names:
        key = norm_to_key.get(_norm_name(name))
        if key is not None:
            return key
    return None


def _field(
    row: Mapping[str, str],
    names: Sequence[str],
    *,
    required: bool = True,
    column_map: Optional[Mapping[str, str]] = None,
    canonical: Optional[str] = None,
    context: Optional[str] = None,
) -> str:
    key = _resolve_column(
        row,
        names,
        column_map=column_map,
        canonical=canonical,
        context=context,
    )
    if key is not None:
        return str(row.get(key, "")).strip()
    if required:
        raise ValueError(
            "Input table is missing a required column. "
            f"Tried aliases={list(names)!r}; available_columns={list(row.keys())!r}. "
            "Rename/map the task table columns before calling build_hypodd_inputs(...)."
        )
    return ""


def _read_csv_rows(path: str) -> List[Dict[str, str]]:
    with open(path, newline="", encoding="utf-8") as f:
        return [dict(r) for r in csv.DictReader(f)]


def _missing(value: object) -> bool:
    return str(value).strip().lower() in {"", "-1", "nan", "none", "null", "na"}


def _normalize_pick_time(value: str) -> str:
    return "-1" if _missing(value) else str(value).strip()


def _normalize_mag(value: str) -> Tuple[str, bool]:
    text = str(value).strip()
    if not text:
        return "0.0", True
    try:
        float(text)
    except ValueError:
        return "0.0", True
    return text, False


def _station_id_from_row(
    row: Mapping[str, str],
    *,
    default_network: Optional[str],
    column_map: Optional[Mapping[str, str]] = None,
    context: str = "station",
) -> Tuple[str, bool]:
    sta_raw = _field(
        row,
        _STATION_NAMES,
        column_map=column_map,
        canonical="station_id",
        context=context,
    )
    net_raw = _field(
        row,
        _NETWORK_NAMES,
        required=False,
        column_map=column_map,
        canonical="network",
        context=context,
    )
    if "." not in sta_raw and net_raw:
        sta_raw = f"{net_raw}.{sta_raw}"
    net, sta = split_station_id(sta_raw, default_network=default_network)
    original_station = _field(
        row,
        _STATION_NAMES,
        column_map=column_map,
        canonical="station_id",
        context=context,
    )
    defaulted = "." not in original_station and not net_raw and bool(net)
    return f"{net}.{sta}" if net else sta, defaulted


def _group_picks_by_event(
    rows: Iterable[Mapping[str, str]],
    *,
    default_network: Optional[str],
    column_map: Optional[Mapping[str, str]] = None,
) -> Tuple[Dict[str, List[Tuple[str, str, str]]], int, int]:
    grouped: Dict[str, List[Tuple[str, str, str]]] = {}
    pick_rows = 0
    defaulted_networks = 0
    for row in rows:
        event_id = _field(
            row,
            _EVENT_ID_NAMES,
            column_map=column_map,
            canonical="event_id",
            context="pick",
        )
        station_id, defaulted = _station_id_from_row(
            row,
            default_network=default_network,
            column_map=column_map,
            context="pick",
        )
        p_pick = _normalize_pick_time(
            _field(
                row,
                _P_PICK_NAMES,
                required=False,
                column_map=column_map,
                canonical="p_pick_time",
                context="pick",
            )
        )
        s_pick = _normalize_pick_time(
            _field(
                row,
                _S_PICK_NAMES,
                required=False,
                column_map=column_map,
                canonical="s_pick_time",
                context="pick",
            )
        )
        grouped.setdefault(event_id, []).append((station_id, p_pick, s_pick))
        pick_rows += 1
        defaulted_networks += int(defaulted)
    return grouped, pick_rows, defaulted_networks


def _parseable_time(value: str) -> bool:
    text = str(value).strip()
    if _missing(text):
        return False
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        datetime.fromisoformat(text)
        return True
    except ValueError:
        pass
    for fmt in ("%Y%m%d%H%M%S.%f", "%Y%m%d%H%M%S", "%Y-%m-%d %H:%M:%S"):
        try:
            datetime.strptime(str(value).strip(), fmt)
            return True
        except ValueError:
            continue
    return False


def _has_real_pick(p_pick: str, s_pick: str) -> bool:
    return not _missing(p_pick) or not _missing(s_pick)


def _sample(values: Iterable[object], limit: int = 20) -> List[object]:
    return list(values)[:limit]


def _validate_prepared_tables(
    *,
    event_rows: Sequence[Mapping[str, str]],
    station_rows: Sequence[Mapping[str, str]],
    grouped_picks: Mapping[str, Sequence[Tuple[str, str, str]]],
    column_map: Optional[Mapping[str, str]],
    station_default_network: Optional[str],
) -> Tuple[Dict[str, Any], List[str], List[str]]:
    event_ids: List[str] = [
        _field(row, _EVENT_ID_NAMES, column_map=column_map, canonical="event_id", context="event")
        for row in event_rows
    ]
    duplicate_event_ids = sorted({eid for eid in event_ids if event_ids.count(eid) > 1})
    event_id_set: Set[str] = set(event_ids)
    pick_event_ids = set(grouped_picks.keys())
    picks_without_events = sorted(pick_event_ids - event_id_set)
    events_without_picks = sorted(eid for eid in event_ids if eid not in pick_event_ids)
    events_without_real_picks = sorted(
        eid
        for eid in event_ids
        if eid in grouped_picks and not any(_has_real_pick(p, s) for _sta, p, s in grouped_picks[eid])
    )

    event_time_failures = []
    numeric_failures = []
    for row in event_rows:
        eid = _field(row, _EVENT_ID_NAMES, column_map=column_map, canonical="event_id", context="event")
        origin_time = _field(
            row,
            _ORIGIN_TIME_NAMES,
            column_map=column_map,
            canonical="origin_time",
            context="event",
        )
        if not _parseable_time(origin_time):
            event_time_failures.append(eid)
        for canonical, names in (
            ("latitude", _LAT_NAMES),
            ("longitude", _LON_NAMES),
            ("depth_km", _DEPTH_NAMES),
        ):
            try:
                float(_field(row, names, column_map=column_map, canonical=canonical, context="event"))
            except ValueError:
                numeric_failures.append(f"{eid}:{canonical}")

    station_ids = []
    duplicate_station_ids = []
    for row in station_rows:
        station_id, _defaulted = _station_id_from_row(
            row,
            default_network=station_default_network,
            column_map=column_map,
            context="station",
        )
        station_ids.append(station_match_key(station_id))
    station_id_set = set(station_ids)
    duplicate_station_ids = sorted({sid for sid in station_ids if station_ids.count(sid) > 1})

    phase_station_ids = sorted(
        {
            station_match_key(station_id)
            for pick_rows in grouped_picks.values()
            for station_id, _p_pick, _s_pick in pick_rows
        }
    )
    missing_phase_stations = sorted(set(phase_station_ids) - station_id_set)
    unused_stations = sorted(station_id_set - set(phase_station_ids))

    warnings: List[str] = []
    errors: List[str] = []
    if duplicate_event_ids:
        errors.append(f"duplicate event ids: {_sample(duplicate_event_ids)}")
    if picks_without_events:
        errors.append(f"pick rows reference missing event ids: {_sample(picks_without_events)}")
    if missing_phase_stations:
        errors.append(f"pick rows reference stations absent from stations table: {_sample(missing_phase_stations)}")
    if event_time_failures:
        errors.append(f"unparseable event origin times for event ids: {_sample(event_time_failures)}")
    if numeric_failures:
        errors.append(f"non-numeric event coordinate/depth fields: {_sample(numeric_failures)}")
    if events_without_picks:
        warnings.append(f"events with no pick rows: {_sample(events_without_picks)}")
    if events_without_real_picks:
        warnings.append(f"events with pick rows but no real P/S arrivals: {_sample(events_without_real_picks)}")
    if duplicate_station_ids:
        warnings.append(f"duplicate station codes after NET.STA normalization: {_sample(duplicate_station_ids)}")
    if unused_stations:
        warnings.append(f"station rows not referenced by picks: {_sample(unused_stations)}")

    summary = {
        "event_count": len(event_rows),
        "pick_event_count": len(pick_event_ids),
        "station_count": len(station_rows),
        "phase_station_count": len(phase_station_ids),
        "duplicate_event_ids": len(duplicate_event_ids),
        "duplicate_station_ids": len(duplicate_station_ids),
        "picks_without_events": len(picks_without_events),
        "events_without_picks": len(events_without_picks),
        "events_without_real_picks": len(events_without_real_picks),
        "missing_phase_stations": len(missing_phase_stations),
        "unused_stations": len(unused_stations),
        "event_time_parse_failures": len(event_time_failures),
        "event_numeric_failures": len(numeric_failures),
        "missing_phase_stations_sample": _sample(missing_phase_stations),
        "picks_without_events_sample": _sample(picks_without_events),
        "events_without_picks_sample": _sample(events_without_picks),
        "events_without_real_picks_sample": _sample(events_without_real_picks),
    }
    return summary, warnings, errors


def _write_manifest(path: str, manifest: Mapping[str, Any]) -> str:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, sort_keys=True)
        f.write("\n")
    return os.path.abspath(path)


def build_hypodd_inputs(
    *,
    events_csv: str,
    picks_csv: str,
    stations_csv: str,
    output_dir: str,
    phase_filename: str = "phase.dat",
    station_filename: str = "station.sta",
    station_default_network: Optional[str] = None,
    column_map: Optional[Mapping[str, str]] = None,
    write_manifest: bool = True,
    manifest_filename: str = "input_preparation_manifest.json",
    strict: bool = True,
) -> HypoddInputBuildResult:
    """Write hypodd_runner ``phase.dat`` and ``station.sta`` from simple tables.

    Parameters
    ----------
    events_csv
        CSV with event id, origin time, latitude, longitude, depth, and
        magnitude columns. Common aliases such as ``event_id``/``evid`` and
        ``depth_km``/``depth`` are accepted.
    picks_csv
        CSV with event id, station id, P pick, and S pick columns. Missing picks
        may be empty, ``-1``, ``nan``, ``None``, ``null``, or ``NA``.
    stations_csv
        CSV with station id, latitude, longitude, and optional elevation.
    output_dir
        Directory where generated phase, station, and optional manifest files
        are written.
    phase_filename
        File name for the generated hypodd_runner phase file inside
        ``output_dir``. The content is event-block HypoDD/PAL-compatible text,
        not a native ``dt.ct`` differential-time file.
    station_filename
        File name for the generated station CSV-like file inside
        ``output_dir``. Later ``mk_sta`` converts this file to native
        ``hypoDD_station.dat``.
    station_default_network
        Optional network code to prepend to bare station IDs. Leave unset for
        catalog-only runs that intentionally use station-code matching. For
        CC/FDTCC, use this only when the value matches waveform/inventory
        network names.
    column_map
        Optional explicit mapping from canonical names to source CSV columns.
        Canonical names include ``event_id``, ``origin_time``, ``latitude``,
        ``longitude``, ``depth_km``, ``magnitude``, ``station_id``,
        ``p_pick_time``, ``s_pick_time``, ``network`` and ``elevation_m``.
        Table-specific keys such as ``event.latitude``, ``pick.station_id`` or
        ``station.longitude`` override generic keys when source tables use
        different names for similar fields.
        Built-in aliases are:
        ``event_id/evid/id``, ``origin_time/time/ot/datetime``,
        ``latitude/lat``, ``longitude/lon/lng``, ``depth_km/depth/dep``,
        ``magnitude/mag/ml``, ``station_id/station_code/network.station/station/sta``,
        ``p_pick_time/p_time/tp/p``, ``s_pick_time/s_time/ts/s``,
        ``elevation_m/elev_m/elevation/elev``, and ``network/net``.
    write_manifest
        Write a JSON manifest documenting source files, generated paths, row
        counts, warnings, and validation errors.
    manifest_filename
        File name for the JSON manifest inside ``output_dir`` when
        ``write_manifest`` is true.
    strict
        When true, raise before writing native inputs if blocking consistency
        errors are found, such as pick rows referencing absent events/stations.

    Returns
    -------
    HypoddInputBuildResult
        Output paths and row counts.
    """
    out_dir = os.path.abspath(output_dir)
    os.makedirs(out_dir, exist_ok=True)
    phase_path = os.path.join(out_dir, phase_filename)
    station_path = os.path.join(out_dir, station_filename)
    manifest_path = os.path.join(out_dir, manifest_filename)

    event_rows = _read_csv_rows(os.path.abspath(events_csv))
    pick_rows = _read_csv_rows(os.path.abspath(picks_csv))
    station_rows = _read_csv_rows(os.path.abspath(stations_csv))
    grouped, pick_count, defaulted_pick_networks = _group_picks_by_event(
        pick_rows,
        default_network=station_default_network,
        column_map=column_map,
    )
    validation, warnings, errors = _validate_prepared_tables(
        event_rows=event_rows,
        station_rows=station_rows,
        grouped_picks=grouped,
        column_map=column_map,
        station_default_network=station_default_network,
    )
    if strict and errors:
        manifest = {
            "success": False,
            "source_files": {
                "events_csv": os.path.abspath(events_csv),
                "picks_csv": os.path.abspath(picks_csv),
                "stations_csv": os.path.abspath(stations_csv),
            },
            "generated_files": {
                "phase_path": os.path.abspath(phase_path),
                "station_path": os.path.abspath(station_path),
            },
            "column_map": dict(column_map or {}),
            "station_default_network": station_default_network,
            "validation": validation,
            "warnings": warnings,
            "errors": errors,
        }
        if write_manifest:
            os.makedirs(out_dir, exist_ok=True)
            _write_manifest(manifest_path, manifest)
        raise ValueError(
            "Cannot build hypodd_runner inputs because blocking validation errors "
            f"were found: {'; '.join(errors)}. "
            f"manifest={os.path.abspath(manifest_path) if write_manifest else ''}"
        )

    filled_magnitudes = 0
    with open(phase_path, "w", encoding="utf-8") as f:
        for row in event_rows:
            event_id = _field(
                row,
                _EVENT_ID_NAMES,
                column_map=column_map,
                canonical="event_id",
                context="event",
            )
            mag, filled = _normalize_mag(
                _field(
                    row,
                    _MAG_NAMES,
                    required=False,
                    column_map=column_map,
                    canonical="magnitude",
                    context="event",
                )
            )
            filled_magnitudes += int(filled)
            f.write(
                ",".join(
                    [
                        _field(row, _ORIGIN_TIME_NAMES, column_map=column_map, canonical="origin_time", context="event"),
                        _field(row, _LAT_NAMES, column_map=column_map, canonical="latitude", context="event"),
                        _field(row, _LON_NAMES, column_map=column_map, canonical="longitude", context="event"),
                        _field(row, _DEPTH_NAMES, column_map=column_map, canonical="depth_km", context="event"),
                        mag,
                        event_id,
                    ]
                )
                + "\n"
            )
            for station_id, p_pick, s_pick in grouped.get(event_id, []):
                f.write(",".join([station_id, p_pick, s_pick]) + "\n")

    defaulted_station_networks = 0
    with open(station_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["station", "latitude", "longitude", "elevation_m"])
        for row in station_rows:
            station_id, defaulted = _station_id_from_row(
                row,
                default_network=station_default_network,
                column_map=column_map,
                context="station",
            )
            defaulted_station_networks += int(defaulted)
            writer.writerow(
                [
                    station_id,
                    _field(row, _LAT_NAMES, column_map=column_map, canonical="latitude", context="station"),
                    _field(row, _LON_NAMES, column_map=column_map, canonical="longitude", context="station"),
                    _field(row, _ELEV_NAMES, required=False, column_map=column_map, canonical="elevation_m", context="station") or "0.0",
                ]
            )

    manifest_written = ""
    if write_manifest:
        manifest = {
            "success": True,
            "source_files": {
                "events_csv": os.path.abspath(events_csv),
                "picks_csv": os.path.abspath(picks_csv),
                "stations_csv": os.path.abspath(stations_csv),
            },
            "generated_files": {
                "phase_path": os.path.abspath(phase_path),
                "station_path": os.path.abspath(station_path),
            },
            "column_map": dict(column_map or {}),
            "station_default_network": station_default_network,
            "validation": validation,
            "counts": {
                "events": len(event_rows),
                "pick_rows": pick_count,
                "stations": len(station_rows),
                "filled_magnitudes": filled_magnitudes,
                "defaulted_station_networks": defaulted_pick_networks + defaulted_station_networks,
            },
            "warnings": warnings,
            "errors": errors,
        }
        manifest_written = _write_manifest(manifest_path, manifest)

    return HypoddInputBuildResult(
        phase_path=os.path.abspath(phase_path),
        station_path=os.path.abspath(station_path),
        event_count=len(event_rows),
        pick_row_count=pick_count,
        station_count=len(station_rows),
        filled_magnitudes=filled_magnitudes,
        defaulted_station_networks=defaulted_pick_networks + defaulted_station_networks,
        manifest_path=manifest_written,
        warnings=warnings,
    )
