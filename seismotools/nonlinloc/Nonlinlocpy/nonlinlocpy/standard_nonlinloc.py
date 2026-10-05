"""Standard/native NonLinLoc workflow helpers."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, List, Mapping

from . import observations, stations as nll_stations
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
class StandardRunConfig:
    """Configuration for a standard (native) NonLinLoc workflow run.
    
    Attributes:
        input_dir (str): input dir.
        run_dir (str): run dir.
        nlloc_bin (str): nlloc bin.
        date (str): date.
        utm_zone_number (int | None): fixed UTM zone number for cross-zone regions.
        utm_zone_letter (str | None): fixed UTM zone letter for cross-zone regions.
        use_native_obs (bool): use native obs.
        prepare_only (bool): prepare only.
    """
    input_dir: str = str(INPUTS_DIR)
    run_dir: str = str(RUN_DIR)
    nlloc_bin: str = ""
    date: str = "201907040234"
    utm_zone_number: int | None = None
    utm_zone_letter: str | None = None
    use_native_obs: bool = False
    prepare_only: bool = False


@dataclass
class StandardRunResult:
    """Result summary for a standard NonLinLoc run.
    
    Attributes:
        run_dir (str): run dir.
        located_csv (str): located csv.
        n_located_events (int): n located events.
    """
    run_dir: str
    located_csv: str = ""
    n_located_events: int = 0


@dataclass
class EventGuess:
    """A seed guess for event centroid location (used for grid estimation).
    
    Attributes:
        latitude (float): latitude.
        longitude (float): longitude.
        depth_km (float): depth km.
    """
    latitude: float
    longitude: float
    depth_km: float


def config_from_dict(config: Mapping[str, Any] | None = None) -> StandardRunConfig:
    """Create ``StandardRunConfig`` from a mapping, ignoring unknown keys.
    
    Args:
        config (Mapping[str, Any] | None): config.
    
    Returns:
        StandardRunConfig: Result returned by the function.
    """
    return config_from_dict_dataclass(StandardRunConfig, config)


def config_from_json(path: str | Path) -> StandardRunConfig:
    """Load ``StandardRunConfig`` from a JSON file.
    
    Args:
        path (str | Path): path.
    
    Returns:
        StandardRunConfig: Result returned by the function.
    """
    return config_from_json_dataclass(StandardRunConfig, path)


def write_default_config_json(path: str | Path) -> Path:
    """Write a default JSON config that can be edited before running.
    
    Args:
        path (str | Path): path.
    
    Returns:
        Path: Result returned by the function.
    """
    return write_default_dataclass_config_json(StandardRunConfig(), path)


# -----------------------------------------------------------------------------
# Main standard/native workflow
# -----------------------------------------------------------------------------
def prepare_standard_example(config: StandardRunConfig) -> tuple[Path, List[Station]]:
    """Prepare directories, config, and required files for a standard NonLinLoc run.
    
    Args:
        config (StandardRunConfig): config.
    
    Returns:
        tuple[Path, List[Station]]: Result returned by the function.
    """
    input_dir = Path(config.input_dir)
    run_dir = Path(config.run_dir)

    velocity_path = input_dir / "velocity_model_1d.txt"
    station_path = input_dir / "stations_native.txt"
    picks_path = input_dir / "picks_simple.txt"
    native_obs_path = input_dir / "event.obs"

    if not velocity_path.exists():
        raise FileNotFoundError(f"Missing velocity model: {velocity_path}")
    if not station_path.exists():
        raise FileNotFoundError(f"Missing station table: {station_path}")
    if config.use_native_obs:
        if not native_obs_path.exists():
            raise FileNotFoundError(f"Missing native NonLinLoc obs file: {native_obs_path}")
    elif not picks_path.exists():
        raise FileNotFoundError(f"Missing simple picks file: {picks_path}")

    stations = nll_stations.load_stations_native_table(str(station_path))
    if not stations:
        raise ValueError(f"No stations were loaded from {station_path}")

    event_guess = EventGuess(
        latitude=36.124940,
        longitude=-117.711110,
        depth_km=4.380,
    )
    _, vggrid_line, locgrid_line = prepare_1d_control_case(
        run_dir=run_dir,
        velocity_path=velocity_path,
        stations=stations,
        events=[event_guess],
        horizontal_pad_km=10.0,
        depth_top_km=-2.0,
        depth_bottom_pad_km=10.0,
        horizontal_spacing_km=1.0,
        depth_spacing_km=1.0,
        utm_zone_number=config.utm_zone_number,
        utm_zone_letter=config.utm_zone_letter,
    )

    if config.use_native_obs:
        obs_lines = native_obs_path.read_text(encoding="utf-8").splitlines(keepends=True)
        observations.write_nlloc_obs_file(str(run_dir), obs_lines, obs_basename="All.obs")

    print(f"[INFO] Standard input directory: {input_dir}")
    print(f"[INFO] Standard run directory: {run_dir}")
    print(f"[INFO] Stations loaded: {len(stations)}")
    print(f"[INFO] VGGRID:  {vggrid_line}")
    print(f"[INFO] LOCGRID: {locgrid_line}")
    return run_dir, stations


def run_standard_example(
    config: StandardRunConfig,
    run_dir: Path,
    stations: List[Station],
) -> StandardRunResult:
    """Execute the standard NonLinLoc run pipeline.
    
    Args:
        config (StandardRunConfig): config.
        run_dir (Path): run dir.
        stations (List[Station]): stations.
    
    Returns:
        StandardRunResult: Result returned by the function.
    """
    nlloc_bin_dir = prepare_static_assets(
        config.nlloc_bin,
        run_dir,
        stations,
        utm_zone_number=config.utm_zone_number,
        utm_zone_letter=config.utm_zone_letter,
    )
    print("[INFO] Running NLLoc")
    located_csv = run_dir / "located_events.csv"
    solutions = run_nlloc(
        NLLocConfig(
            nlloc_bin=nlloc_bin_dir,
            control_dir=str(run_dir),
            date=config.date,
            picks=str(Path(config.input_dir) / "picks_simple.txt"),
            output_csv=located_csv.name,
            skip_obs=config.use_native_obs,
        )
    )
    print(f"[INFO] Located events parsed: {len(solutions)}")
    if solutions:
        first = solutions[0]
        print(
            "[INFO] First solution: "
            f"lat={first.get('lat')} lon={first.get('lon')} depth_km={first.get('depth_km')}"
        )
    print(f"[INFO] Event table: {located_csv}")
    return StandardRunResult(
        run_dir=str(run_dir),
        located_csv=str(located_csv),
        n_located_events=len(solutions),
    )


# -----------------------------------------------------------------------------
# Main workflow
# -----------------------------------------------------------------------------
def run_standard_workflow(config: StandardRunConfig | Mapping[str, Any]) -> StandardRunResult:
    """Full workflow to prepare inputs and execute the standard NonLinLoc run.
    
    Args:
        config (StandardRunConfig | Mapping[str, Any]): config.
    
    Returns:
        StandardRunResult: Result returned by the function.
    """
    if not isinstance(config, StandardRunConfig):
        config = config_from_dict(config)

    run_dir, stations = prepare_standard_example(config)
    if config.prepare_only:
        print("[INFO] Preparation finished. Skipping NonLinLoc execution.")
        return StandardRunResult(run_dir=str(run_dir))
    return run_standard_example(config, run_dir, stations)
