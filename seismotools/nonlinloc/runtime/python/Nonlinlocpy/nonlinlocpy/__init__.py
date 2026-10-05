"""
User-facing entry points for the nonlinlocpy helpers.

Most users should start with ``run_nlloc`` or ``run_parallel_nlloc_workflow``.
Lower-level building blocks remain available from their implementation modules,
for example ``nonlinlocpy.control``, ``nonlinlocpy.observations``, and
``nonlinlocpy.utils``.
"""

from __future__ import annotations

from importlib import import_module
from typing import Any, Dict, List

from .hyp import parse_hyp_solutions
from .models import PhasePick, Station
from .parallel import ParallelNLLocConfig, ParallelNLLocResult, run_parallel_nlloc_workflow
from .workflows import NLLocConfig, run_nlloc
from .gamma_nonlinloc import ExampleRunConfig, ExampleRunResult, run_example_workflow
from .standard_nonlinloc import StandardRunConfig, StandardRunResult, run_standard_workflow

__all__ = [
    "NLLocConfig",
    "ParallelNLLocConfig",
    "ParallelNLLocResult",
    "PhasePick",
    "Station",
    "ExampleRunConfig",
    "ExampleRunResult",
    "StandardRunConfig",
    "StandardRunResult",
    "parse_hyp_solutions",
    "run_nlloc",
    "run_parallel_nlloc_workflow",
    "run_example_workflow",
    "run_standard_workflow",
]

_LEGACY_EXPORTS: Dict[str, str] = {
    "MARKER_GTSRCE_AFTER": ".control",
    "MARKER_GTSRCE_BEFORE": ".control",
    "apply_stations_wgs84": ".stations",
    "clear_obs_and_loc": ".runner",
    "convert_simple_pick_file_to_nlloc_obs": ".observations",
    "filter_arrivals_by_phase_median": ".observations",
    "format_nlloc_obs_lines": ".observations",
    "layers_1d_to_vel2grid_lines": ".velocity",
    "load_simple_pick_table": ".observations",
    "load_stations_native_table": ".stations",
    "parse_hyp_geographic": ".hyp",
    "patch_locgrid_line": ".control",
    "patch_vggrid_line": ".control",
    "read_depth_vp_vs_columns": ".velocity",
    "read_grid_lines_from_file": ".control",
    "replace_vel2grid_layer_block": ".velocity",
    "reset_loc_directory": ".runner",
    "run_nlloc_bin": ".runner",
    "save_control_gtsrce_sections": ".control",
    "write_nlloc_obs_file": ".observations",
    "ChunkRunResult": ".parallel",
    "chunk_sequence": ".parallel",
    "copy_static_assets": ".parallel",
    "make_standard_chunk_preparer": ".parallel",
    "merge_solution_csvs": ".parallel",
    "prepare_chunk_run_dirs": ".parallel",
    "run_nlloc_chunk": ".parallel",
    "run_parallel_chunks": ".parallel",
    "safe_link_or_copy": ".parallel",
    "write_chunk_obs_file": ".parallel",
    "build_run_directory": ".utils",
    "cleanup_production_outputs": ".utils",
    "compute_grid_lines": ".utils",
    "ensure_locmeth_line": ".utils",
    "load_velocity_depths": ".utils",
    "patch_lochypout_line": ".utils",
    "project_points_to_utm": ".utils",
    "replace_control_line": ".utils",
    "resolve_nlloc_bin_dir": ".utils",
    "write_compact_solution_csv": ".utils",
    "write_solution_csv": ".utils",
    "DirectNLLocConfig": ".run_nlloc_cli",
    "run_direct_nlloc": ".run_nlloc_cli",
    "SimpleNLLocConfig": ".workflows",
    "run_simple_nlloc": ".workflows",
}


def __getattr__(name: str) -> Any:
    """Load advanced legacy helpers on demand without advertising them as the main API.
    
    Args:
        name (str): name.
    
    Returns:
        Any: Result returned by the function.
    """

    module_name = _LEGACY_EXPORTS.get(name)
    if module_name is None:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    value = getattr(import_module(module_name, __name__), name)
    globals()[name] = value
    return value


def __dir__() -> List[str]:
    """Keep interactive discovery focused on the recommended user API.
    
    Returns:
        List[str]: Result returned by the function.
    """

    return sorted(set(__all__))
