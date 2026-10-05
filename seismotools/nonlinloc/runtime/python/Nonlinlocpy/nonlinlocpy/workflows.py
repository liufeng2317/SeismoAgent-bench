"""User-facing workflow helpers for common NonLinLoc runs."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
from dataclasses import asdict, dataclass
from importlib import resources
from pathlib import Path
from typing import Any, Dict, List, Mapping, Sequence, Type, TypeVar

from . import control, stations as nll_stations, utils, velocity
from .hyp import parse_hyp_solutions
from .observations import convert_simple_pick_file_to_nlloc_obs
from .runner import clear_obs_and_loc, reset_loc_directory, run_nlloc_bin
from .utils import write_solution_csv

ConfigT = TypeVar("ConfigT")


def config_from_dict_dataclass(
    config_cls: Type[ConfigT],
    config: Mapping[str, Any] | None = None,
) -> ConfigT:
    """Create a dataclass config object from a mapping, ignoring unknown keys.
    
    Args:
        config_cls (Type[ConfigT]): config cls.
        config (Mapping[str, Any] | None): config.
    
    Returns:
        ConfigT: Result returned by the function.
    """

    config = dict(config or {})
    allowed = set(config_cls.__dataclass_fields__)  # type: ignore[attr-defined]
    filtered = {key: value for key, value in config.items() if key in allowed}
    unknown = sorted(set(config) - allowed)
    if unknown:
        print(f"[WARN] Ignoring unknown config keys: {unknown}")
    return config_cls(**filtered)


def config_from_json_dataclass(config_cls: Type[ConfigT], path: str | Path) -> ConfigT:
    """Load a dataclass config object from a JSON file.
    
    Args:
        config_cls (Type[ConfigT]): config cls.
        path (str | Path): path.
    
    Returns:
        ConfigT: Result returned by the function.
    """

    with Path(path).open("r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, dict):
        raise ValueError(f"Expected a JSON object in {path}")
    return config_from_dict_dataclass(config_cls, data)


def write_default_dataclass_config_json(config: Any, path: str | Path) -> Path:
    """Write a dataclass config object to an editable JSON file.
    
    Args:
        config (Any): config.
        path (str | Path): path.
    
    Returns:
        Path: Result returned by the function.
    """

    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(asdict(config), indent=2), encoding="utf-8")
    return output_path


def copy_template_control_file(run_dir: Path) -> Path:
    """Copy the package NonLinLoc control-file template into a run directory.
    
    Args:
        run_dir (Path): run dir.
    
    Returns:
        Path: Result returned by the function.
    """

    target = run_dir / "nlloc.in"
    template_resource = resources.files("nonlinlocpy").joinpath("template", "nlloc.in")
    with resources.as_file(template_resource) as template_path:
        shutil.copy2(template_path, target)
    return target


def run_vel2grid_for_wave(
    run_dir: Path,
    nlloc_bin_dir: str,
    wave_type: str,
    control_file_name: str = "nlloc.in",
) -> None:
    """Run ``Vel2Grid`` for one wave type after patching ``VGTYPE``.
    
    Args:
        run_dir (Path): run dir.
        nlloc_bin_dir (str): nlloc bin dir.
        wave_type (str): wave type.
        control_file_name (str): control file name.
    """

    control_path = run_dir / control_file_name
    utils.replace_control_line(control_path, "VGTYPE", f"VGTYPE {wave_type}")
    env = os.environ.copy()
    if nlloc_bin_dir:
        env["PATH"] = nlloc_bin_dir + os.pathsep + env.get("PATH", "")
    subprocess.run(["Vel2Grid", control_file_name], cwd=run_dir, env=env, check=True)


def prepare_static_assets(
    nlloc_bin: str,
    run_dir: Path,
    stations: Sequence[Any],
    utm_zone_number: int | None = None,
    utm_zone_letter: str | None = None,
) -> str:
    """Run ``Vel2Grid`` for P/S and ``Grid2Time`` for a prepared run directory.
    
    Args:
        nlloc_bin (str): nlloc bin.
        run_dir (Path): run dir.
        stations (Sequence[Any]): stations.
        utm_zone_number (int | None): Optional fixed UTM zone number.
        utm_zone_letter (str | None): Optional fixed UTM zone letter.
    
    Returns:
        str: Result returned by the function.
    """

    nlloc_bin_dir = utils.resolve_nlloc_bin_dir(nlloc_bin)
    print(f"[INFO] Using NonLinLoc binaries from: {nlloc_bin_dir}")

    print("[INFO] Running Vel2Grid for P")
    run_vel2grid_for_wave(run_dir, nlloc_bin_dir, "P")

    print("[INFO] Running Vel2Grid for S")
    run_vel2grid_for_wave(run_dir, nlloc_bin_dir, "S")

    print("[INFO] Running Grid2Time for P and S")
    nll_stations.apply_stations_wgs84(
        nlloc_bin_dir,
        str(run_dir),
        stations,
        utm_zone_number=utm_zone_number,
        utm_zone_letter=utm_zone_letter,
    )
    return nlloc_bin_dir


def prepare_1d_control_case(
    *,
    run_dir: Path,
    velocity_path: Path,
    stations: Sequence[Any],
    events: Sequence[Any],
    horizontal_pad_km: float,
    depth_top_km: float,
    depth_bottom_pad_km: float,
    horizontal_spacing_km: float,
    depth_spacing_km: float,
    utm_zone_number: int | None = None,
    utm_zone_letter: str | None = None,
) -> tuple[Path, str, str]:
    """Create a prepared run directory and patch a 1-D velocity NonLinLoc case.
    
    Args:
        run_dir (Path): run dir.
        velocity_path (Path): velocity path.
        stations (Sequence[Any]): stations.
        events (Sequence[Any]): events.
        horizontal_pad_km (float): horizontal pad km.
        depth_top_km (float): depth top km.
        depth_bottom_pad_km (float): depth bottom pad km.
        horizontal_spacing_km (float): horizontal spacing km.
        depth_spacing_km (float): depth spacing km.
        utm_zone_number (int | None): Optional fixed UTM zone number.
        utm_zone_letter (str | None): Optional fixed UTM zone letter.
    
    Returns:
        tuple[Path, str, str]: Result returned by the function.
    """

    utils.build_run_directory(run_dir)
    control_path = copy_template_control_file(run_dir)

    layer_lines = velocity.read_depth_vp_vs_columns(str(velocity_path))
    velocity.replace_vel2grid_layer_block(str(run_dir), layer_lines)
    utils.ensure_locmeth_line(control_path, "LOCMETH EDT_OT_WT 9999.0 4 -1 -1 -1 6 -1.0 1")
    utils.patch_lochypout_line(control_path)

    velocity_depths = utils.load_velocity_depths(velocity_path)
    vggrid_line, locgrid_line = utils.compute_grid_lines(
        stations=stations,
        events=events,
        velocity_depths=velocity_depths,
        horizontal_pad_km=horizontal_pad_km,
        depth_top_km=depth_top_km,
        depth_bottom_pad_km=depth_bottom_pad_km,
        horizontal_spacing_km=horizontal_spacing_km,
        depth_spacing_km=depth_spacing_km,
        utm_zone_number=utm_zone_number,
        utm_zone_letter=utm_zone_letter,
    )
    control.patch_vggrid_line(str(run_dir), vggrid_line)
    control.patch_locgrid_line(str(run_dir), locgrid_line)
    return control_path, vggrid_line, locgrid_line


@dataclass
class NLLocConfig:
    """Configuration for the common prepared-directory NonLinLoc workflow.
    
    Attributes:
        nlloc_bin (str): nlloc bin.
        control_dir (str): control dir.
        date (str): date.
        picks (str): picks.
        output_csv (str): output csv.
        obs_basename (str): obs basename.
        skip_obs (bool): skip obs.
        skip_clear_loc (bool): skip clear loc.
    """

    nlloc_bin: str
    control_dir: str
    date: str = ""
    picks: str = ""
    output_csv: str = "located_events.csv"
    obs_basename: str = "All.obs"
    skip_obs: bool = False
    skip_clear_loc: bool = False


def _resolve_output_csv(control_dir: str, output_csv: str) -> Path:
    """Resolve a CSV path relative to the run directory unless already absolute.
    
    Args:
        control_dir (str): control dir.
        output_csv (str): output csv.
    
    Returns:
        Path: Result returned by the function.
    """

    path = Path(output_csv)
    if path.is_absolute():
        return path
    control_path = Path(control_dir)
    try:
        path.relative_to(control_path)
        return path
    except ValueError:
        return control_path / path


def run_nlloc(config: NLLocConfig) -> List[Dict[str, Any]]:
    """Run a prepared NonLinLoc case from a simple pick table and return parsed solutions.
    
    Args:
        config (NLLocConfig): config.
    
    Returns:
        List[Dict[str, Any]]: Result returned by the function.
    """

    if not config.skip_obs:
        if len(config.date) < 12:
            raise ValueError("date must be at least YYYYMMDDHHMM (12 chars) when writing obs from picks")
        if not config.picks:
            raise ValueError("picks is required unless skip_obs=True")
        d8, hm = config.date[:8], config.date[8:12]
        clear_obs_and_loc(config.control_dir, obs_basename=config.obs_basename)
        convert_simple_pick_file_to_nlloc_obs(
            config.control_dir,
            config.picks,
            d8,
            hm,
            obs_basename=config.obs_basename,
        )
    elif not config.skip_clear_loc:
        reset_loc_directory(config.control_dir)

    run_nlloc_bin(config.nlloc_bin, config.control_dir)
    solutions = parse_hyp_solutions(config.control_dir)
    if config.output_csv:
        write_solution_csv(_resolve_output_csv(config.control_dir, config.output_csv), solutions)
    return solutions


SimpleNLLocConfig = NLLocConfig
run_simple_nlloc = run_nlloc
