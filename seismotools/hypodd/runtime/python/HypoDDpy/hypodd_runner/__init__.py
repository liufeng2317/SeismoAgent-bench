"""HypoDD + ph2dt + optional FDTCC relocation package.

Generated task scripts should use the public Python entry points exported here,
especially :func:`run_catalog_only_relocation` for catalog-only runs and
:func:`run_fdtcc_relocation` for waveform cross-correlation runs. Use
:func:`run_cc_only_relocation` when the final HypoDD inversion should use only
FDTCC ``dt.cc`` observations. Lower-level modules such as ``run_hypoDD``,
``ph2dt``, ``hypodd``, and ``fdtcc.runner`` are pipeline internals unless the
task explicitly asks for package debugging.
"""

from .api import (
    default_fdtcc_flags,
    run_config,
    run_fdtcc_relocation,
    scaled_layered_velocity_model,
)
from .params import (
    CCOnlyWindowParams,
    EventSelection,
    FDTCCParams,
    HypoDDInputs,
    HypoDDParams,
    Ph2dtParams,
    RuntimeOptions,
    grouped_to_catalog_only_kwargs,
    grouped_to_fdtcc_kwargs,
)
from .cc_only import (
    CCOnlyWindowEntry,
    CCOnlyWindowResult,
    build_cc_only_relocation_kwargs,
    default_cc_only_hypodd_iter_rows,
    plan_cc_only_time_windows,
    run_cc_only_auto_time_windows,
    run_cc_only_relocation,
    run_cc_only_time_windows,
    run_fdtcc_cc_only_relocation,
)
from .catalog_only import (
    build_catalog_only_config,
    CatalogOnlyBatchEntry,
    CatalogOnlyBatchResult,
    CatalogOnlyResult,
    CatalogOnlyInputCheck,
    plan_catalog_only_time_windows,
    check_catalog_only_inputs,
    inspect_catalog_only_outputs,
    require_catalog_only_native_outputs,
    run_catalog_only_auto_time_windows,
    run_catalog_only_batches,
    run_catalog_only_relocation,
    run_catalog_only_time_windows,
)
from .time_window import TimeWindowPlan, plan_time_windows
from .phase_convert import PhaseFileResult, prepare_phase_file
from .input_builder import HypoddInputBuildResult, build_hypodd_inputs
from .errors import (
    ConfigContractError,
    HypoddRunnerError,
    InsufficientDTimeError,
    NativeOutputError,
    NativeProgramError,
)

__all__ = [
    "HypoddRunnerError",
    "ConfigContractError",
    "InsufficientDTimeError",
    "NativeOutputError",
    "NativeProgramError",
    "CatalogOnlyBatchEntry",
    "CatalogOnlyBatchResult",
    "CatalogOnlyResult",
    "CatalogOnlyInputCheck",
    "CCOnlyWindowEntry",
    "CCOnlyWindowParams",
    "CCOnlyWindowResult",
    "TimeWindowPlan",
    "PhaseFileResult",
    "HypoddInputBuildResult",
    "HypoDDInputs",
    "EventSelection",
    "Ph2dtParams",
    "HypoDDParams",
    "FDTCCParams",
    "RuntimeOptions",
    "build_cc_only_relocation_kwargs",
    "default_cc_only_hypodd_iter_rows",
    "default_fdtcc_flags",
    "grouped_to_catalog_only_kwargs",
    "grouped_to_fdtcc_kwargs",
    "build_hypodd_inputs",
    "build_catalog_only_config",
    "plan_time_windows",
    "plan_catalog_only_time_windows",
    "plan_cc_only_time_windows",
    "check_catalog_only_inputs",
    "run_config",
    "run_cc_only_auto_time_windows",
    "run_cc_only_relocation",
    "run_cc_only_time_windows",
    "run_fdtcc_cc_only_relocation",
    "run_fdtcc_relocation",
    "run_catalog_only_auto_time_windows",
    "run_catalog_only_batches",
    "run_catalog_only_relocation",
    "run_catalog_only_time_windows",
    "prepare_phase_file",
    "inspect_catalog_only_outputs",
    "require_catalog_only_native_outputs",
    "scaled_layered_velocity_model",
]
