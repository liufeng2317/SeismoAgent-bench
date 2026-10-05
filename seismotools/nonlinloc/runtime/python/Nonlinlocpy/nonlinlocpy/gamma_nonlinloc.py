"""Gamma-associated phase catalog to NonLinLoc workflow helpers."""

from __future__ import annotations

import csv
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Dict, Iterable, List, Mapping, Sequence, Tuple

import matplotlib
import numpy as np
import pandas as pd
from obspy import UTCDateTime

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from . import parallel as nll_parallel, utils
from .models import Station
from .workflows import (
    NLLocConfig,
    config_from_dict_dataclass,
    config_from_json_dataclass,
    prepare_1d_control_case,
    prepare_static_assets,
    run_nlloc,
    write_default_dataclass_config_json,
)

INPUTS_DIR = Path("./inputs")
RUN_DIR = Path("./run_case")

# -----------------------------------------------------------------------------
# Configuration and result types
# -----------------------------------------------------------------------------
@dataclass
class ExampleRunConfig:
    """Configuration for running a gamma-NonLinLoc workflow example.
    
    Attributes:
        example_dir (str): example dir.
        run_dir (str | None): run dir.
        nlloc_bin (str): nlloc bin.
        phase_pattern (str): phase pattern.
        min_phases (int): min phases.
        max_events (int): max events.
        horizontal_pad_km (float): horizontal pad km.
        depth_top_km (float): depth top km.
        depth_bottom_pad_km (float): depth bottom pad km.
        horizontal_spacing_km (float): horizontal spacing km.
        depth_spacing_km (float): depth spacing km.
        utm_zone_number (int | None): fixed UTM zone number for cross-zone regions.
        utm_zone_letter (str | None): fixed UTM zone letter for cross-zone regions.
        pick_error_sec (float): pick error sec.
        prepare_only (bool): prepare only.
        output_mode (str): output mode.
        skip_plots (bool): skip plots.
        chunk_size (int): chunk size.
        num_workers (int): num workers.
    """
    example_dir: str = str(INPUTS_DIR)
    run_dir: str | None = str(RUN_DIR)
    nlloc_bin: str = ""
    phase_pattern: str = "phase_*.dat"
    min_phases: int = 4
    max_events: int = 200
    horizontal_pad_km: float = 10.0
    depth_top_km: float = -2.0
    depth_bottom_pad_km: float = 10.0
    horizontal_spacing_km: float = 1.0
    depth_spacing_km: float = 1.0
    utm_zone_number: int | None = None
    utm_zone_letter: str | None = None
    pick_error_sec: float = 0.05
    prepare_only: bool = False
    output_mode: str = "production"
    skip_plots: bool = False
    chunk_size: int = 0
    num_workers: int = 64

@dataclass
class ExampleRunResult:
    """Result object holding paths and stats for a gamma-NonLinLoc run.
    
    Attributes:
        run_dir (str): run dir.
        located_csv (str): located csv.
        n_input_events (int): n input events.
        n_located_events (int): n located events.
        chunk_count (int): chunk count.
        summary_plot (str): summary plot.
        shift_plot (str): shift plot.
        stats_file (str): stats file.
    """
    run_dir: str
    located_csv: str
    n_input_events: int
    n_located_events: int
    chunk_count: int
    summary_plot: str = ""
    shift_plot: str = ""
    stats_file: str = ""

def config_from_dict(config: Mapping[str, Any] | None = None) -> ExampleRunConfig:
    """Create ``ExampleRunConfig`` from a mapping, ignoring unknown keys.
    
    Args:
        config (Mapping[str, Any] | None): config.
    
    Returns:
        ExampleRunConfig: Result returned by the function.
    """
    return config_from_dict_dataclass(ExampleRunConfig, config)


def config_from_json(path: str | Path) -> ExampleRunConfig:
    """Load ``ExampleRunConfig`` from a JSON file.
    
    Args:
        path (str | Path): path.
    
    Returns:
        ExampleRunConfig: Result returned by the function.
    """
    return config_from_json_dataclass(ExampleRunConfig, path)


def write_default_config_json(path: str | Path) -> Path:
    """Write a default JSON config file that can be edited before running.
    
    Args:
        path (str | Path): path.
    
    Returns:
        Path: Result returned by the function.
    """
    return write_default_dataclass_config_json(ExampleRunConfig(), path)


# -----------------------------------------------------------------------------
# Input records and parsing helpers
# -----------------------------------------------------------------------------
@dataclass
class EventPick:
    """Stores a pick (phase time) for an event at a station.
    
    Attributes:
        station_id (str): station id.
        phase (str): phase.
        pick_time (UTCDateTime): pick time.
    """
    station_id: str
    phase: str
    pick_time: UTCDateTime


@dataclass
class EventRecord:
    """Complete event record with hypocenter and all picks/phases.
    
    Attributes:
        event_index (int): event index.
        origin_time (UTCDateTime): origin time.
        latitude (float): latitude.
        longitude (float): longitude.
        depth_km (float): depth km.
        magnitude (float): magnitude.
        picks (List[EventPick]): picks.
    """
    event_index: int
    origin_time: UTCDateTime
    latitude: float
    longitude: float
    depth_km: float
    magnitude: float
    picks: List[EventPick]

def load_station_rows(station_path: Path) -> List[Dict[str, str]]:
    """Load station metadata rows from a CSV into a list of dicts.
    
    Args:
        station_path (Path): station path.
    
    Returns:
        List[Dict[str, str]]: Result returned by the function.
    """
    with station_path.open("r", encoding="utf-8", errors="replace", newline="") as f:
        rows = list(csv.DictReader(f))
    if not rows:
        raise ValueError(f"No station rows found in {station_path}")
    return rows

def parse_gamma_phase_files(phase_files: Sequence[Path], min_phases: int) -> List[EventRecord]:
    """Parse a list of gamma phase CSV/flatfiles into EventRecord objects.
    
    Args:
        phase_files (Sequence[Path]): phase files.
        min_phases (int): min phases.
    
    Returns:
        List[EventRecord]: Result returned by the function.
    """
    events: List[EventRecord] = []
    event_index = 0

    for phase_file in sorted(phase_files):
        current: EventRecord | None = None
        with phase_file.open("r", encoding="utf-8", errors="replace") as f:
            for raw_line in f:
                line = raw_line.strip()
                if not line:
                    continue
                parts = [p.strip() for p in line.split(",")]

                if len(parts) == 5 and "T" in parts[0]:
                    if current is not None and len(current.picks) >= min_phases:
                        events.append(current)
                    event_index += 1
                    current = EventRecord(
                        event_index=event_index,
                        origin_time=UTCDateTime(parts[0]),
                        latitude=float(parts[1]),
                        longitude=float(parts[2]),
                        depth_km=float(parts[3]),
                        magnitude=float(parts[4]) if parts[4] else float("nan"),
                        picks=[],
                    )
                    continue

                if len(parts) != 4 or current is None:
                    continue

                station_id, p_pick, s_pick, _ = parts
                if p_pick != "-1":
                    current.picks.append(
                        EventPick(station_id=station_id, phase="P", pick_time=UTCDateTime(p_pick))
                    )
                if s_pick != "-1":
                    current.picks.append(
                        EventPick(station_id=station_id, phase="S", pick_time=UTCDateTime(s_pick))
                    )

        if current is not None and len(current.picks) >= min_phases:
            events.append(current)

    return events

def sanitize_station_label(text: str) -> str:
    """Clean station identifier to be ASCII alphanumeric for NonLinLoc.
    
    Args:
        text (str): text.
    
    Returns:
        str: Result returned by the function.
    """
    cleaned = re.sub(r"[^A-Za-z0-9]", "", text).upper()
    return cleaned or "STA"

def make_station_alias_map(station_ids: Iterable[str]) -> Dict[str, str]:
    """Create mapping from original station IDs to unique NonLinLoc-safe aliases.
    
    Args:
        station_ids (Iterable[str]): station ids.
    
    Returns:
        Dict[str, str]: Result returned by the function.
    """
    alias_map: Dict[str, str] = {}
    used: Dict[str, str] = {}

    for station_id in sorted(set(station_ids)):
        suffix = station_id.split(".")[-1]
        candidates = [
            sanitize_station_label(suffix),
            sanitize_station_label(station_id),
            sanitize_station_label(station_id.replace(".", "")),
        ]

        alias = ""
        for base in candidates:
            base = base[:6]
            if base and base not in used:
                alias = base
                break

        if not alias:
            base = sanitize_station_label(suffix)[:4] or "STA"
            for i in range(1, 100):
                candidate = f"{base[:4]}{i:02d}"[:6]
                if candidate not in used:
                    alias = candidate
                    break

        if not alias:
            raise RuntimeError(f"Could not assign a unique alias for station {station_id}")

        alias_map[station_id] = alias
        used[alias] = station_id

    return alias_map

def build_station_objects(
    station_rows: Sequence[Dict[str, str]],
    alias_map: Dict[str, str],
    used_station_ids: Sequence[str],
) -> List[Station]:
    """Build list of Station objects, renamed to use NonLinLoc-safe aliases.
    
    Args:
        station_rows (Sequence[Dict[str, str]]): station rows.
        alias_map (Dict[str, str]): alias map.
        used_station_ids (Sequence[str]): used station ids.
    
    Returns:
        List[Station]: Result returned by the function.
    """
    used = set(used_station_ids)
    stations: List[Station] = []
    seen_aliases: set[str] = set()

    for row in station_rows:
        station_id = row["station_id"].strip()
        if station_id not in used:
            continue
        alias = alias_map[station_id]
        if alias in seen_aliases:
            continue
        stations.append(
            Station(
                station_id=alias,
                lon=float(row["longitude"]),
                lat=float(row["latitude"]),
                elev_m=float(row["elevation_m"]),
            )
        )
        seen_aliases.add(alias)

    if not stations:
        raise ValueError("No stations matched between phase files and stations_gamma.csv")

    return stations

def format_obs_lines_for_events(
    events: Sequence[EventRecord],
    alias_map: Dict[str, str],
    pick_error_sec: float,
) -> List[str]:
    """Format a set of event picks for input to NonLinLoc in NLLOC_OBS format.
    
    Args:
        events (Sequence[EventRecord]): events.
        alias_map (Dict[str, str]): alias map.
        pick_error_sec (float): pick error sec.
    
    Returns:
        List[str]: Result returned by the function.
    """
    lines: List[str] = []
    err_mag = f"{pick_error_sec:.2e}"

    for event in events:
        for pick in event.picks:
            alias = alias_map[pick.station_id][:6].ljust(6)
            phase = pick.phase[:6].ljust(6)
            t = pick.pick_time
            yyyymmdd = f"{t.year:04d}{t.month:02d}{t.day:02d}"
            hhmm = f"{t.hour:02d}{t.minute:02d}"
            sec = t.second + t.microsecond / 1_000_000.0
            lines.append(
                f"{alias}    ?    ?    ? {phase} ? {yyyymmdd} {hhmm}   {sec:7.4f} "
                f"GAU  {err_mag} -1.00e+00 -1.00e+00 -1.00e+00\n"
            )
        lines.append("!END_EVENT\n")

    lines.append("!END_FILE\n")
    return lines

def write_station_alias_csv(
    output_path: Path,
    station_rows: Sequence[Dict[str, str]],
    alias_map: Dict[str, str],
) -> None:
    """Write a CSV table mapping station IDs to NonLinLoc-safe aliases.
    
    Args:
        output_path (Path): output path.
        station_rows (Sequence[Dict[str, str]]): station rows.
        alias_map (Dict[str, str]): alias map.
    """
    rows = []
    for row in station_rows:
        station_id = row["station_id"].strip()
        if station_id in alias_map:
            rows.append(
                {
                    "alias": alias_map[station_id],
                    "station_id": station_id,
                    "network": row.get("network", ""),
                    "station": row.get("station", ""),
                    "longitude": row.get("longitude", ""),
                    "latitude": row.get("latitude", ""),
                    "elevation_m": row.get("elevation_m", ""),
                }
            )
    pd.DataFrame(rows).to_csv(output_path, index=False)

def write_initial_event_csv(output_path: Path, events: Sequence[EventRecord]) -> None:
    """Write a CSV containing the initial event catalog.
    
    Args:
        output_path (Path): output path.
        events (Sequence[EventRecord]): events.
    """
    pd.DataFrame(
        [
            {
                "event_index": event.event_index,
                "origin_time": str(event.origin_time),
                "latitude": f"{event.latitude:.6f}",
                "longitude": f"{event.longitude:.6f}",
                "depth_km": f"{event.depth_km:.3f}",
                "magnitude": f"{event.magnitude:.3f}",
                "n_picks": len(event.picks),
            }
            for event in events
        ]
    ).to_csv(output_path, index=False)

# -----------------------------------------------------------------------------
# Diagnostics
# -----------------------------------------------------------------------------
def merge_catalogs(located: pd.DataFrame, initial: pd.DataFrame) -> pd.DataFrame:
    """Merge relocated and original catalogs for diagnostic plotting/statistics.
    
    Args:
        located (pd.DataFrame): located.
        initial (pd.DataFrame): initial.
    
    Returns:
        pd.DataFrame: Result returned by the function.
    """
    located = located.copy()
    initial = initial.copy()

    if "origin_time" in located.columns:
        located["origin_time_loc"] = pd.to_datetime(located["origin_time"], utc=True, errors="coerce")
    else:
        date_part = pd.to_numeric(located["origin_yyyymmdd"], errors="coerce").round().astype("Int64").astype(str)
        date_part = date_part.str.replace("<NA>", "", regex=False).str.zfill(8)
        time_part = located["origin_hhmmss"].astype(str).str.zfill(10)
        located["origin_time_loc"] = pd.to_datetime(
            date_part + time_part, format="%Y%m%d%H%M%S.%f", utc=True, errors="coerce"
        )
    initial["origin_time_init"] = pd.to_datetime(initial["origin_time"], utc=True, errors="coerce")
    located["origin_time_loc_key"] = located["origin_time_loc"].astype("int64")
    initial["origin_time_init_key"] = initial["origin_time_init"].astype("int64")

    located_by_order = located.dropna(subset=["lat", "lon", "depth_km"]).reset_index(drop=True)
    initial_by_order = initial.dropna(subset=["latitude", "longitude", "depth_km"]).reset_index(drop=True)
    located = located_by_order.dropna(subset=["origin_time_loc"]).sort_values("origin_time_loc_key")
    initial = initial_by_order.dropna(subset=["origin_time_init"]).sort_values(
        "origin_time_init_key"
    )

    merged = pd.merge_asof(
        initial,
        located,
        left_on="origin_time_init_key",
        right_on="origin_time_loc_key",
        direction="nearest",
        tolerance=int(pd.Timedelta(seconds=30).value),
    )
    merged = merged.dropna(subset=["lat", "lon", "depth_km_y"]).copy()
    if merged.empty:
        n_pair = min(len(initial_by_order), len(located_by_order))
        if n_pair == 0:
            raise ValueError("No relocations could be matched because one catalog is empty.")
        merged = initial_by_order.head(n_pair).reset_index(drop=True).copy()
        located_ordered = located_by_order.head(n_pair).reset_index(drop=True)
        merged["depth_km_x"] = merged["depth_km"]
        merged["lat"] = located_ordered["lat"]
        merged["lon"] = located_ordered["lon"]
        merged["depth_km_y"] = located_ordered["depth_km"]
        merged["origin_time_loc"] = located_ordered["origin_time_loc"]
        merged["origin_time_loc_key"] = located_ordered["origin_time_loc_key"]

    merged = merged.rename(
        columns={
            "origin_time": "origin_time_text",
            "origin_time_init": "origin_time",
            "latitude": "lat_init",
            "longitude": "lon_init",
            "depth_km_x": "dep_init",
            "lat": "lat_reloc",
            "lon": "lon_reloc",
            "depth_km_y": "dep_reloc",
        }
    )
    lat_ref = np.deg2rad(merged["lat_init"].mean())
    dx = (merged["lon_reloc"] - merged["lon_init"]) * 111.0 * np.cos(lat_ref)
    dy = (merged["lat_reloc"] - merged["lat_init"]) * 111.0
    merged["horizontal_shift_km"] = np.sqrt(dx**2 + dy**2)
    merged["vertical_shift_km"] = merged["dep_reloc"] - merged["dep_init"]
    return merged

def write_diagnostic_plots(run_dir: Path) -> tuple[Path, Path, Path]:
    """Generate diagnostic plots and a stats file for a processed NonLinLoc run.
    
    Args:
        run_dir (Path): run dir.
    
    Returns:
        tuple[Path, Path, Path]: Result returned by the function.
    """
    paths = {
        "located": run_dir / "located_events.csv",
        "initial": run_dir / "initial_events.csv",
        "stations": run_dir / "station_alias_map.csv",
    }
    missing = [str(path) for path in paths.values() if not path.exists()]
    if missing:
        raise FileNotFoundError("Required plot inputs are missing:\n" + "\n".join(missing))

    located = pd.read_csv(paths["located"])
    initial = pd.read_csv(paths["initial"])
    stations = pd.read_csv(paths["stations"])
    merged = merge_catalogs(located, initial)
    summary_path = run_dir / "nonlinloc_summary.png"
    shift_path = run_dir / "nonlinloc_shift_vectors.png"
    stats_path = run_dir / "nonlinloc_plot_stats.txt"

    fig, axes = plt.subplots(2, 2, figsize=(14, 11))
    panels = [
        (axes[0, 0], "lon", "lat", "Longitude", "Latitude", "Map View", False),
        (axes[0, 1], "lon", "dep", "Longitude", "Depth (km)", "Longitude-Depth Section", True),
        (axes[1, 0], "lat", "dep", "Latitude", "Depth (km)", "Latitude-Depth Section", True),
    ]
    for ax, x, y, xlabel, ylabel, title, invert_y in panels:
        ax.scatter(merged[f"{x}_init"], merged[f"{y}_init"], s=22, c="#4C78A8", alpha=0.7, label="Initial")
        ax.scatter(merged[f"{x}_reloc"], merged[f"{y}_reloc"], s=22, c="#E45756", alpha=0.7, label="Relocated")
        if title == "Map View":
            ax.scatter(stations["longitude"], stations["latitude"], marker="^", s=55, c="black", label="Stations")
        if invert_y:
            ax.invert_yaxis()
        ax.set(xlabel=xlabel, ylabel=ylabel, title=title)
        ax.legend()

    ax = axes[1, 1]
    ax.hist(merged["horizontal_shift_km"], bins=20, color="#72B7B2", alpha=0.85)
    ax.set_xlabel("Horizontal Shift (km)")
    ax.set_ylabel("Count")
    ax.set_title("Relocation Shift Distribution")

    fig.tight_layout()
    fig.savefig(summary_path, dpi=220)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(10, 8))
    ax.scatter(stations["longitude"], stations["latitude"], marker="^", s=60, c="black", label="Stations")
    ax.scatter(merged["lon_init"], merged["lat_init"], s=18, c="#4C78A8", alpha=0.75, label="Initial")
    ax.quiver(
        merged["lon_init"],
        merged["lat_init"],
        merged["lon_reloc"] - merged["lon_init"],
        merged["lat_reloc"] - merged["lat_init"],
        angles="xy",
        scale_units="xy",
        scale=1,
        color="#E45756",
        width=0.0022,
        alpha=0.8,
        label="Shift",
    )
    ax.set_xlabel("Longitude")
    ax.set_ylabel("Latitude")
    ax.set_title("Initial-to-Relocated Shift Vectors")
    ax.legend()
    fig.tight_layout()
    fig.savefig(shift_path, dpi=220)
    plt.close(fig)

    lines = [
        f"Number of compared events: {len(merged)}",
        f"Mean horizontal shift (km): {merged['horizontal_shift_km'].mean():.4f}",
        f"Median horizontal shift (km): {merged['horizontal_shift_km'].median():.4f}",
        f"Max horizontal shift (km): {merged['horizontal_shift_km'].max():.4f}",
        f"Mean vertical shift (km): {merged['vertical_shift_km'].mean():.4f}",
        f"Median vertical shift (km): {merged['vertical_shift_km'].median():.4f}",
        f"Max abs vertical shift (km): {merged['vertical_shift_km'].abs().max():.4f}",
    ]
    stats_path.write_text("\n".join(lines), encoding="utf-8")
    return summary_path, shift_path, stats_path

# -----------------------------------------------------------------------------
# NonLinLoc chunking and main workflow
# -----------------------------------------------------------------------------
def prepare_chunk_run_dir(
    base_run_dir: Path,
    chunk_run_dir: Path,
    chunk_events_list: Sequence[EventRecord],
    alias_map: Dict[str, str],
    pick_error_sec: float,
) -> None:
    """Prepare a run directory for a chunk of events, copying static assets and writing chunked obs/events files.
    
    Args:
        base_run_dir (Path): base run dir.
        chunk_run_dir (Path): chunk run dir.
        chunk_events_list (Sequence[EventRecord]): chunk events list.
        alias_map (Dict[str, str]): alias map.
        pick_error_sec (float): pick error sec.
    """
    utils.build_run_directory(chunk_run_dir)
    nll_parallel.copy_static_assets(base_run_dir, chunk_run_dir, static_files=("nlloc.in", "Zone_info.pickle", "Part_of_ControlFile.pickle", "station_alias_map.csv"))
    obs_lines = format_obs_lines_for_events(chunk_events_list, alias_map, pick_error_sec)
    nll_parallel.write_chunk_obs_file(chunk_run_dir, obs_lines, obs_basename="All.obs")
    write_initial_event_csv(chunk_run_dir / "initial_events.csv", chunk_events_list)

def run_parallel_chunks_for_example(
    args: Any,
    run_dir: Path,
    events: Sequence[EventRecord],
    alias_map: Dict[str, str],
) -> List[Dict[str, object]]:
    """Split the event set into chunks and run NonLinLoc in parallel, merging the results.
    
    Args:
        args (Any): args.
        run_dir (Path): run dir.
        events (Sequence[EventRecord]): events.
        alias_map (Dict[str, str]): alias map.
    
    Returns:
        List[Dict[str, object]]: Result returned by the function.
    """
    config = nll_parallel.ParallelNLLocConfig(
        base_run_dir=str(run_dir),
        nlloc_bin_dir=utils.resolve_nlloc_bin_dir(args.nlloc_bin),
        chunk_size=args.chunk_size,
        num_workers=args.num_workers,
        output_mode=args.output_mode,
        chunk_root_dir=str(run_dir / "chunks"),
        merged_output_path=str(run_dir / "located_events.csv"),
        static_files=("nlloc.in", "Zone_info.pickle", "Part_of_ControlFile.pickle", "station_alias_map.csv"),
    )
    chunk_lists = nll_parallel.chunk_sequence(events, args.chunk_size)

    print(
        f"[INFO] Prepared {len(chunk_lists)} chunk run directories "
        f"(chunk_size={args.chunk_size}, workers={args.num_workers})"
    )

    result = nll_parallel.run_parallel_nlloc_workflow(
        items=events,
        config=config,
        prepare_chunk_inputs=lambda chunk_run_dir, chunk_list: prepare_chunk_run_dir(
            run_dir,
            chunk_run_dir,
            chunk_list,
            alias_map,
            args.pick_error_sec,
        ),
        on_chunk_completed=lambda chunk_result: print(
            f"[INFO] Completed {Path(chunk_result.chunk_run_dir).name}: {chunk_result.n_solutions} solutions"
        ),
    )
    print(f"[INFO] Chunked NLLoc finished: {result.n_solutions} merged solutions across {result.n_chunks} chunks")
    return nll_parallel.merge_solution_csvs([Path(path) for path in result.chunk_run_dirs], run_dir / "located_events.csv")

# -----------------------------------------------------------------------------
# Main workflow
# -----------------------------------------------------------------------------
def prepare_example(
    args: Any,
) -> Tuple[Path, List[EventRecord], List[Station], Dict[str, str]]:
    """Prepare the entire run directory for a gamma-NonLinLoc workflow example.
    
    Args:
        args (Any): args.
    
    Returns:
        Tuple[Path, List[EventRecord], List[Station], Dict[str, str]]: Result returned by the function.
    """
    requested_dir = Path(args.example_dir)
    example_dir = requested_dir
    velocity_path = example_dir / "velocity.txt"
    station_path = example_dir / "stations_gamma.csv"
    phase_files = sorted(example_dir.glob(args.phase_pattern))

    if not velocity_path.exists() and not station_path.exists() and not phase_files:
        nested_inputs_dir = requested_dir / "inputs"
        if nested_inputs_dir.is_dir():
            example_dir = nested_inputs_dir
            velocity_path = example_dir / "velocity.txt"
            station_path = example_dir / "stations_gamma.csv"
            phase_files = sorted(example_dir.glob(args.phase_pattern))

    run_dir = Path(args.run_dir) if args.run_dir else RUN_DIR

    if not phase_files:
        raise FileNotFoundError(f"No phase files matched {args.phase_pattern!r} in {example_dir}")

    print(f"[INFO] Example directory: {example_dir}")
    print(f"[INFO] Phase files: {len(phase_files)}")

    events = parse_gamma_phase_files(phase_files, min_phases=args.min_phases)
    if args.max_events > 0:
        events = events[: args.max_events]
    if not events:
        raise ValueError("No events remain after phase parsing and min-phases filtering.")

    print(f"[INFO] Events kept: {len(events)}")

    used_station_ids = sorted({pick.station_id for event in events for pick in event.picks})
    station_rows = load_station_rows(station_path)
    alias_map = make_station_alias_map(used_station_ids)
    stations = build_station_objects(station_rows, alias_map, used_station_ids)
    _, vggrid_line, locgrid_line = prepare_1d_control_case(
        run_dir=run_dir,
        velocity_path=velocity_path,
        stations=stations,
        events=events,
        horizontal_pad_km=args.horizontal_pad_km,
        depth_top_km=args.depth_top_km,
        depth_bottom_pad_km=args.depth_bottom_pad_km,
        horizontal_spacing_km=args.horizontal_spacing_km,
        depth_spacing_km=args.depth_spacing_km,
        utm_zone_number=args.utm_zone_number,
        utm_zone_letter=args.utm_zone_letter,
    )

    obs_lines = format_obs_lines_for_events(events, alias_map, args.pick_error_sec)
    obs_path = nll_parallel.write_chunk_obs_file(run_dir, obs_lines, obs_basename="All.obs")

    write_station_alias_csv(run_dir / "station_alias_map.csv", station_rows, alias_map)
    write_initial_event_csv(run_dir / "initial_events.csv", events)

    print(f"[INFO] Run directory prepared: {run_dir}")
    print(f"[INFO] Stations used: {len(stations)}")
    print(f"[INFO] Observation file: {obs_path}")
    print(f"[INFO] Output mode: {args.output_mode}")
    print(f"[INFO] VGGRID:  {vggrid_line}")
    print(f"[INFO] LOCGRID: {locgrid_line}")
    return run_dir, events, stations, alias_map

def run_example(
    args: Any,
    run_dir: Path,
    events: Sequence[EventRecord],
    stations: Sequence[Station],
    alias_map: Dict[str, str],
) -> List[Dict[str, Any]]:
    """Run NonLinLoc on a group of events using prepared inputs and stations.
    
    Args:
        args (Any): args.
        run_dir (Path): run dir.
        events (Sequence[EventRecord]): events.
        stations (Sequence[Station]): stations.
        alias_map (Dict[str, str]): alias map.
    
    Returns:
        List[Dict[str, Any]]: Result returned by the function.
    """
    prepare_static_assets(
        args.nlloc_bin,
        run_dir,
        stations,
        utm_zone_number=args.utm_zone_number,
        utm_zone_letter=args.utm_zone_letter,
    )

    use_chunked = args.chunk_size > 0 and len(events) > args.chunk_size
    if use_chunked:
        print("[INFO] Running NLLoc in chunked mode")
        solutions = run_parallel_chunks_for_example(args, run_dir, events, alias_map)
    else:
        nlloc_bin_dir = utils.resolve_nlloc_bin_dir(args.nlloc_bin)
        print("[INFO] Running NLLoc")
        solutions = run_nlloc(
            NLLocConfig(
                nlloc_bin=nlloc_bin_dir,
                control_dir=str(run_dir),
                output_csv="located_events.csv",
                skip_obs=True,
            )
        )
        if args.output_mode == "production":
            if solutions:
                utils.cleanup_production_outputs(run_dir)
            else:
                print(
                    "[WARN] Production cleanup skipped because no located events were parsed. "
                    "Per-event files were kept in loc/ for debugging."
                )
    print(f"[INFO] Located events parsed: {len(solutions)}")
    if solutions:
        first = solutions[0]
        print(
            "[INFO] First solution: "
            f"lat={first.get('lat')} lon={first.get('lon')} depth_km={first.get('depth_km')}"
        )
    if args.output_mode == "production" and solutions:
        print("[INFO] Production cleanup finished: per-event loc files were pruned.")
    if solutions and not args.skip_plots:
        summary_path, shift_path, stats_path = write_diagnostic_plots(run_dir)
        print(f"[INFO] Summary figure: {summary_path}")
        print(f"[INFO] Shift figure: {shift_path}")
        print(f"[INFO] Plot stats: {stats_path}")
    return list(solutions)

def run_example_workflow(config: ExampleRunConfig) -> ExampleRunResult:
    """End-to-end run of the gamma-NonLinLoc workflow example.
    
    Args:
        config (ExampleRunConfig): config.
    
    Returns:
        ExampleRunResult: Result returned by the function.
    """
    args = SimpleNamespace(**asdict(config))
    run_dir, events, stations, alias_map = prepare_example(args)
    if args.prepare_only:
        return ExampleRunResult(
            run_dir=str(run_dir),
            located_csv=str(run_dir / "located_events.csv"),
            n_input_events=len(events),
            n_located_events=0,
            chunk_count=max(1, len(nll_parallel.chunk_sequence(events, args.chunk_size))),
        )

    solutions = run_example(args, run_dir, events, stations, alias_map)
    return ExampleRunResult(
        run_dir=str(run_dir),
        located_csv=str(run_dir / "located_events.csv"),
        n_input_events=len(events),
        n_located_events=len(solutions),
        chunk_count=max(1, len(nll_parallel.chunk_sequence(events, args.chunk_size))),
        summary_plot=str(run_dir / "nonlinloc_summary.png") if (run_dir / "nonlinloc_summary.png").exists() else "",
        shift_plot=str(run_dir / "nonlinloc_shift_vectors.png")
        if (run_dir / "nonlinloc_shift_vectors.png").exists()
        else "",
        stats_file=str(run_dir / "nonlinloc_plot_stats.txt") if (run_dir / "nonlinloc_plot_stats.txt").exists() else "",
    )
