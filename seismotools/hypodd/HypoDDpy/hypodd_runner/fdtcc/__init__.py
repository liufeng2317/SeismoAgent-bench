"""Python wrapper for the FDTCC executable (HypoDD ``dt.cc`` via SAC / REAL tables)."""

from .build_ttdb import (
    rho_from_vp_brocher,
    write_simple_layers_to_nd,
    write_ttdb_for_fdtcc,
    write_ttdb_from_simple_velocity,
)
from .runner import (
    FDTCCCliFlags,
    FDTCCInputPaths,
    FDTCCResult,
    build_fdtcc_argv,
    copy_dt_cc_to,
    dt_cc_nonempty,
    fdtcc_flags_from_mapping,
    resolve_fdtcc_binary,
    run_fdtcc,
    summarize_dt_cc,
)

__all__ = [
    "rho_from_vp_brocher",
    "write_simple_layers_to_nd",
    "write_ttdb_for_fdtcc",
    "write_ttdb_from_simple_velocity",
    "FDTCCCliFlags",
    "FDTCCInputPaths",
    "FDTCCResult",
    "build_fdtcc_argv",
    "copy_dt_cc_to",
    "dt_cc_nonempty",
    "fdtcc_flags_from_mapping",
    "resolve_fdtcc_binary",
    "run_fdtcc",
    "summarize_dt_cc",
]
