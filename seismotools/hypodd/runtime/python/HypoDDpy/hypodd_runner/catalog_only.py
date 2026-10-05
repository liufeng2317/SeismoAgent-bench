"""High-level function API for catalog-only HypoDD relocation.

This module is the preferred entry point when a task only needs ph2dt/HypoDD
catalog differential times and does not need waveform cross-correlation.
Callers pass explicit function parameters; top-level JSON config files are not
part of the public execution interface.
"""
from __future__ import annotations

import json
import os
import csv
import re
import shutil
import traceback
from dataclasses import dataclass
from typing import Any, Dict, List, Mapping, Optional, Sequence, Set

from obspy import UTCDateTime

from .config import Config
from .errors import (
    ConfigContractError,
    InsufficientDTimeError,
    NativeOutputError,
    NativeProgramError,
    compact_items,
    format_contract_error,
)
from .params import grouped_to_catalog_only_kwargs
from .station_id import station_match_key
from .time_window import TimeWindowPlan, normalize_ot_range, plan_time_windows


@dataclass
class CatalogOnlyResult:
    """Structured result summary for a catalog-only relocation run.

    Attributes
    ----------
    config
        Effective :class:`Config` used for the run, or ``None`` for output-only
        inspection.
    config_path, output_folder, catalog_code
        The generated config path, native output directory, and catalog prefix.
    loc_path, reloc_path, residual_path
        Expected native merged output files.
    loc_rows, reloc_rows, residual_rows
        Non-empty line counts for the native output files.
    log_paths
        Log-like files found under ``output_folder``.
    missing_or_empty
        Required native outputs that are absent or empty.
    """

    config: Optional[Config]
    config_path: str
    output_folder: str
    catalog_code: str
    loc_path: str
    reloc_path: str
    residual_path: str
    loc_rows: int
    reloc_rows: int
    residual_rows: int
    log_paths: List[str]
    missing_or_empty: List[str]

    @property
    def success(self) -> bool:
        """True when required native catalog outputs are present and non-empty."""
        return not self.missing_or_empty

    def as_dict(self) -> Dict[str, Any]:
        """Return a JSON-serializable summary for manifests or debug logs."""
        return {
            "success": self.success,
            "config_path": self.config_path,
            "output_folder": self.output_folder,
            "catalog_code": self.catalog_code,
            "loc_path": self.loc_path,
            "reloc_path": self.reloc_path,
            "residual_path": self.residual_path,
            "loc_rows": self.loc_rows,
            "reloc_rows": self.reloc_rows,
            "residual_rows": self.residual_rows,
            "log_paths": list(self.log_paths),
            "missing_or_empty": list(self.missing_or_empty),
        }


@dataclass
class CatalogOnlyInputCheck:
    """Pre-run input audit for catalog-only relocation.

    ``ok`` is false when blocking input problems are found. Informational
    messages may still be present when ``ok`` is true, for example when PAL input
    is detected and detailed selection checks are deferred until conversion.
    """

    ok: bool
    phase_file: str
    station_file: str
    phase_format: str
    effective_phase_kind: str
    total_events: int
    selected_events: int
    total_picks: int
    selected_picks: int
    station_count: int
    phase_station_count: int
    missing_phase_stations: List[str]
    messages: List[str]
    blocking_messages: List[str]

    def as_dict(self) -> Dict[str, Any]:
        return {
            "ok": self.ok,
            "phase_file": self.phase_file,
            "station_file": self.station_file,
            "phase_format": self.phase_format,
            "effective_phase_kind": self.effective_phase_kind,
            "total_events": self.total_events,
            "selected_events": self.selected_events,
            "total_picks": self.total_picks,
            "selected_picks": self.selected_picks,
            "station_count": self.station_count,
            "phase_station_count": self.phase_station_count,
            "missing_phase_stations": list(self.missing_phase_stations),
            "messages": list(self.messages),
            "blocking_messages": list(self.blocking_messages),
        }


def _format_catalog_precheck_failure(prefix: str, precheck: CatalogOnlyInputCheck) -> str:
    """Return a stable, evidence-first catalog input contract error."""
    context = (
        f"phase_file={precheck.phase_file}\n"
        f"station_file={precheck.station_file}\n"
        f"phase_format={precheck.phase_format}; effective_phase_kind={precheck.effective_phase_kind}\n"
        f"selected_events={precheck.selected_events}; selected_picks={precheck.selected_picks}\n"
        f"station_count={precheck.station_count}; phase_station_count={precheck.phase_station_count}"
    )
    if precheck.missing_phase_stations:
        context += (
            "\nmissing_phase_stations_sample="
            + compact_items(precheck.missing_phase_stations, limit=20)
        )
    return format_contract_error(
        title=f"{prefix} failed.",
        real_error="; ".join(precheck.blocking_messages or precheck.messages),
        context=context,
        expected=(
            "Use a real hypodd_runner event-block phase file and matching station file.\n"
            "Event line: origin_time,lat,lon,depth,mag[,evid]\n"
            "- origin_time must parse; lat/lon/depth must be numeric; evid is optional but must be integer-like when present.\n"
            "- mag may be empty/bad and will be filled with 0.0.\n"
            "Pick line: station_id,ISO_P_pick,ISO_S_pick[,optional_numeric_columns...]\n"
            "- For catalog-only HypoDD, station IDs may be NET.STA or bare STA, and are matched by station code.\n"
            "- Missing P/S pick may be -1, nan, None, null, NA, or empty."
        ),
        minimal_example=(
            "2025-10-01T19:57:32.160000Z,39.315833,141.055000,97.320,0.0,55\n"
            "N.313S,2025-10-01T19:57:40.000000Z,-1,0.000e+00,1.00\n"
            "station.sta row: N.313S,38.590167,142.181667,-573"
        ),
        recommendation=(
            "Fix the specific input contract issue shown in Real error. For large catalogs, "
            "keep using run_catalog_only_auto_time_windows(...) rather than switching to a "
            "single direct native run."
        ),
        avoid=(
            "Do not generate placeholder phase files, drop real picks, switch to pal_hypodd, "
            "or bypass package-supported auto windows unless the real error proves that is required."
        ),
    )


@dataclass
class CatalogOnlyBatchEntry:
    """Status record for one catalog-only batch or time-window run.

    Attributes
    ----------
    batch_id
        Stable id such as ``window_001_20250101_20250102``.
    status
        ``"success"``, ``"failed"``, ``"skipped_empty"`` or another runner
        status.
    input_events
        Number of selected events attempted in this batch/window.
    phase_file, output_folder, config_path
        Source phase input, per-batch native output directory, and generated
        config path when applicable.
    loc_rows, reloc_rows, residual_rows
        Non-empty row counts in native ``.loc``, ``.reloc`` and ``.res`` files.
    error_path, error_signature, failure_kind
        Failure evidence written when status is ``"failed"``.
    ot_range, plan_reason, merged_from
        Time-window planning evidence used by auto-window runs.
    parallel_safe
        Whether this planned window is independent enough for future parallel
        window execution.
    """

    batch_id: str
    status: str
    input_events: int
    phase_file: str
    output_folder: str
    config_path: str
    loc_rows: int = 0
    reloc_rows: int = 0
    residual_rows: int = 0
    error_path: str = ""
    error_signature: str = ""
    failure_kind: str = ""
    ot_range: str = ""
    plan_reason: str = ""
    merged_from: Optional[List[str]] = None
    parallel_safe: bool = True

    def as_dict(self) -> Dict[str, Any]:
        """Return a JSON-serializable batch status record."""
        return {
            "batch_id": self.batch_id,
            "status": self.status,
            "input_events": self.input_events,
            "phase_file": self.phase_file,
            "output_folder": self.output_folder,
            "config_path": self.config_path,
            "loc_rows": self.loc_rows,
            "reloc_rows": self.reloc_rows,
            "residual_rows": self.residual_rows,
            "error_path": self.error_path,
            "error_signature": self.error_signature,
            "failure_kind": self.failure_kind,
            "ot_range": self.ot_range,
            "plan_reason": self.plan_reason,
            "merged_from": list(self.merged_from or []),
            "parallel_safe": self.parallel_safe,
        }


@dataclass
class CatalogOnlyBatchResult:
    """Structured result summary for catalog-only batch/time-window relocation.

    Attributes
    ----------
    output_folder, catalog_code
        Top-level output directory and catalog prefix used for merged native
        files.
    total_input_events
        Number of selected events attempted across non-empty batches/windows.
    success_batches, failed_batches
        Counts of successful and failed batch/window native runs.
    merged_loc_path, merged_reloc_path, merged_residual_path
        Top-level concatenated native outputs, usually
        ``{catalog_code}.loc``, ``{catalog_code}.reloc`` and
        ``{catalog_code}.res``. Empty strings mean no merged file was produced.
    manifest_path, batch_status_csv
        Evidence files recording per-window status, parameters, output folders,
        and failure signatures.
    batches
        Per-batch/window status records. The ``windows`` property is an alias
        used by time-window workflows.
    """

    output_folder: str
    catalog_code: str
    total_input_events: int
    success_batches: int
    failed_batches: int
    merged_loc_path: str
    merged_reloc_path: str
    merged_residual_path: str
    manifest_path: str
    batch_status_csv: str
    batches: List[CatalogOnlyBatchEntry]

    @property
    def success(self) -> bool:
        """True when every batch produced valid native relocation output."""
        return self.success_batches > 0 and self.failed_batches == 0

    @property
    def windows(self) -> List[CatalogOnlyBatchEntry]:
        """Alias for ``batches`` when this result represents time windows."""
        return self.batches

    @property
    def success_windows(self) -> int:
        """Alias for ``success_batches`` in time-window workflows."""
        return self.success_batches

    @property
    def failed_windows(self) -> int:
        """Alias for ``failed_batches`` in time-window workflows."""
        return self.failed_batches

    def as_dict(self) -> Dict[str, Any]:
        """Return a JSON-serializable batch run summary."""
        return {
            "success": self.success,
            "output_folder": self.output_folder,
            "catalog_code": self.catalog_code,
            "total_input_events": self.total_input_events,
            "success_batches": self.success_batches,
            "failed_batches": self.failed_batches,
            "success_windows": self.success_windows,
            "failed_windows": self.failed_windows,
            "merged_loc_path": self.merged_loc_path,
            "merged_reloc_path": self.merged_reloc_path,
            "merged_residual_path": self.merged_residual_path,
            "manifest_path": self.manifest_path,
            "batch_status_csv": self.batch_status_csv,
            "batches": [b.as_dict() for b in self.batches],
            "windows": [b.as_dict() for b in self.windows],
        }


def _require_path(name: str, value: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ConfigContractError(f"{name} must be a non-empty path string")
    return value.strip()


def _hypodd_inc_candidates(hypo_root: str) -> List[str]:
    """Likely ``hypoDD.inc`` locations for a HYPODD source/build tree."""
    root = os.path.abspath(_require_path("hypo_root", hypo_root))
    return [
        os.path.join(root, "include", "hypoDD.inc"),
        os.path.join(os.path.dirname(root), "include", "hypoDD.inc"),
        os.path.join(root, "hypoDD.inc"),
    ]


def _read_active_hypodd_limits(hypo_root: str) -> Dict[str, int]:
    """Parse active Fortran ``parameter(MAXEVE=...)`` values from hypoDD.inc."""
    inc_path = next((p for p in _hypodd_inc_candidates(hypo_root) if os.path.isfile(p)), "")
    if not inc_path:
        return {}
    active_lines: List[str] = []
    with open(inc_path, "r", encoding="utf-8", errors="replace") as f:
        for line in f:
            stripped = line.strip()
            if not stripped:
                continue
            if stripped[0].lower() in {"c", "!"}:
                continue
            active_lines.append(stripped)
    text = " ".join(active_lines)
    out: Dict[str, int] = {}
    for key, value in re.findall(r"\b(MAXEVE|MAXDATA|MAXSTA|MAXCL)\s*=\s*(\d+)", text):
        out[key] = int(value)
    return out


def _check_hypodd_event_limit(
    *,
    hypo_root: str,
    selected_events: int,
) -> None:
    """Fail early when selected events exceed native HypoDD compiled limits."""
    limits = _read_active_hypodd_limits(hypo_root)
    maxeve = limits.get("MAXEVE")
    if maxeve is None or selected_events <= maxeve:
        return
    raise ConfigContractError(
        "HypoDD catalog-only run exceeds the native compiled event limit before "
        f"execution: selected_events={selected_events} > MAXEVE={maxeve} "
        "from hypoDD.inc. For large catalog-only tasks, prefer the public "
        "run_catalog_only_auto_time_windows(...) helper, or otherwise use an "
        "explicit package-supported split with each native window <= MAXEVE. "
        "Alternatively increase MAXEVE in hypoDD.inc and rebuild the native "
        "HypoDD binary as a maintenance task."
    )


def _numeric_pair(
    name: str,
    value: Sequence[Any],
    *,
    cast=float,
    ordered: bool = False,
) -> list:
    try:
        out = [cast(value[0]), cast(value[1])]
    except Exception as exc:
        raise ConfigContractError(f"{name} must be a two-value sequence") from exc
    if ordered and out[0] > out[1]:
        raise ConfigContractError(f"{name} must be ordered as [min, max]")
    return out


def _positive_int_pair(name: str, value: Sequence[Any]) -> List[int]:
    out = _numeric_pair(name, value, cast=int)
    if any(v <= 0 for v in out):
        raise ConfigContractError(f"{name} values must be positive integers")
    return out


def _nonnegative_float_pair(name: str, value: Sequence[Any]) -> List[float]:
    out = _numeric_pair(name, value, cast=float)
    if any(v < 0 for v in out):
        raise ConfigContractError(f"{name} values must be non-negative numbers")
    return out


def _validate_iter_rows(
    rows: Optional[Sequence[Sequence[Any]]],
    default_iter_rows=(
        # NITER, WTCCP, WTCCS, WRCC, WDCC, WTCTP, WTCTS, WRCT, WDCT, DAMP
        (4, 0.0, 0.0, 0.0, 0.0, 1.0, 1.0, 0.50, 10.0, 3.0),
        (8, 0.0, 0.0, 0.0, 0.0, 1.0, 1.0, 0.30, 8.0, 3.0),
    ),
) -> list:
    source = default_iter_rows if rows is None else rows
    out = []
    last_niter = 0
    for index, row in enumerate(source, start=1):
        if len(row) != 10:
            raise ConfigContractError(
                format_contract_error(
                    title="hypodd_runner HypoDD iteration-row contract failed.",
                    real_error=f"iter_rows row {index} has {len(row)} values; expected 10 values.",
                    context=f"bad_row={row!r}",
                    expected="Each row must be: NITER WTCCP WTCCS WRCC WDCC WTCTP WTCTS WRCT WDCT DAMP",
                    minimal_example=(
                        "(4, 0.0, 0.0, 0.0, 0.0, 1.0, 1.0, 0.50, 10.0, 3.0)\n"
                        "(8, 0.0, 0.0, 0.0, 0.0, 1.0, 1.0, 0.30, 8.0, 3.0)"
                    ),
                    recommendation="Use HypoDDParams(iter_rows=None) for the package default, or provide valid 10-value rows.",
                    avoid="Do not invent shorter rows or unsupported fields such as damp/wt/hypodd_iter_rows on the dataclass.",
                )
            )
        try:
            values = [float(x) for x in row]
        except Exception as exc:
            raise ConfigContractError(
                format_contract_error(
                    title="hypodd_runner HypoDD iteration-row contract failed.",
                    real_error=f"iter_rows row {index} contains non-numeric values.",
                    context=f"bad_row={row!r}",
                    expected="Each iter_rows value must be numeric; the first value NITER must be an integer endpoint.",
                    minimal_example="(4, 0.0, 0.0, 0.0, 0.0, 1.0, 1.0, 0.50, 10.0, 3.0)",
                    recommendation="Use HypoDDParams(iter_rows=None) for the package default, or provide numeric rows.",
                )
            ) from exc
        if not values[0].is_integer():
            raise ConfigContractError(
                format_contract_error(
                    title="hypodd_runner HypoDD iteration-row contract failed.",
                    real_error=f"iter_rows row {index} has non-integer NITER={values[0]!r}.",
                    context=f"bad_row={row!r}",
                    expected="The first value NITER must be a positive integer cumulative endpoint.",
                    minimal_example="(4, ...), (8, ...), (12, ...) means cumulative endpoints after 4, 8, and 12 iterations.",
                )
            )
        niter = int(values[0])
        if niter <= 0:
            raise ConfigContractError(
                format_contract_error(
                    title="hypodd_runner HypoDD iteration-row contract failed.",
                    real_error=f"iter_rows row {index} has non-positive NITER={niter}.",
                    context=f"bad_row={row!r}",
                    expected="NITER values must be positive cumulative endpoints.",
                    minimal_example="(4, ...), (8, ...), (12, ...)",
                )
            )
        if niter <= last_niter:
            raise ConfigContractError(
                format_contract_error(
                    title="hypodd_runner HypoDD iteration-row contract failed.",
                    real_error=(
                        f"iter_rows row {index} has NITER={niter}, which is not greater "
                        f"than the previous cumulative endpoint {last_niter}."
                    ),
                    context=f"bad_row={row!r}\nall_rows={list(source)!r}",
                    expected=(
                        "NITER values are cumulative iteration endpoints, not per-stage repeat counts. "
                        "They must be strictly increasing."
                    ),
                    minimal_example=(
                        "Correct: [(4, ...), (8, ...), (12, ...)]\n"
                        "Wrong:   [(8, ...), (8, ...), (8, ...)]"
                    ),
                    recommendation=(
                        "Use HypoDDParams(iter_rows=None) for a stable package default, or change "
                        "repeated per-stage rows into increasing cumulative endpoints."
                    ),
                    avoid=(
                        "Do not switch from run_catalog_only_auto_time_windows(...) to a single direct "
                        "run to work around this; fix iter_rows or leave it as None."
                    ),
                )
            )
        values[0] = niter
        out.append(values)
        last_niter = niter
    return out


def _validate_velocity_model(
    velocity_model_top_km: Optional[Sequence[Any]],
    velocity_model_vp_km_s: Optional[Sequence[Any]],
) -> tuple:
    if velocity_model_top_km is None and velocity_model_vp_km_s is None:
        return None, None
    if velocity_model_top_km is None or velocity_model_vp_km_s is None:
        raise ConfigContractError(
            "velocity_model_top_km and velocity_model_vp_km_s must be provided together"
        )
    try:
        tops = [float(x) for x in velocity_model_top_km]
        vps = [float(x) for x in velocity_model_vp_km_s]
    except Exception as exc:
        raise ConfigContractError(
            format_contract_error(
                title="hypodd_runner velocity-model contract failed.",
                real_error="velocity_model_top_km and velocity_model_vp_km_s must be numeric arrays.",
                context=f"velocity_model_top_km={velocity_model_top_km!r}\nvelocity_model_vp_km_s={velocity_model_vp_km_s!r}",
                expected="Provide equal-length numeric layer tops and Vp values.",
                minimal_example="velocity_model_top_km=[0.0, 5.0, 10.0]\nvelocity_model_vp_km_s=[5.4, 5.8, 6.2]",
                recommendation="Use documented velocity values for the study area, or leave both as None for the package/template default.",
            )
        ) from exc
    if len(tops) != len(vps):
        raise ConfigContractError(
            format_contract_error(
                title="hypodd_runner velocity-model contract failed.",
                real_error="velocity_model_top_km and velocity_model_vp_km_s must have the same length.",
                context=f"len(top)={len(tops)}; len(vp)={len(vps)}",
                expected="Each layer top must have one Vp value.",
                minimal_example="velocity_model_top_km=[0.0, 5.0, 10.0]\nvelocity_model_vp_km_s=[5.4, 5.8, 6.2]",
            )
        )
    if not tops:
        raise ConfigContractError("velocity model must contain at least one layer")
    if any(v <= 0 for v in vps):
        raise ConfigContractError(
            format_contract_error(
                title="hypodd_runner velocity-model contract failed.",
                real_error="velocity_model_vp_km_s values must be positive.",
                context=f"velocity_model_vp_km_s={vps!r}",
                expected="Vp values are positive km/s numbers.",
            )
        )
    if any(tops[i] >= tops[i + 1] for i in range(len(tops) - 1)):
        raise ConfigContractError(
            format_contract_error(
                title="hypodd_runner velocity-model contract failed.",
                real_error="velocity_model_top_km must be strictly increasing.",
                context=f"velocity_model_top_km={tops!r}",
                expected="Layer tops should increase with depth.",
                minimal_example="velocity_model_top_km=[0.0, 5.0, 10.0, 20.0]",
            )
        )
    return tops, vps


def _positive_number(name: str, value: Any) -> float:
    try:
        out = float(value)
    except Exception as exc:
        raise ConfigContractError(f"{name} must be numeric") from exc
    if out <= 0:
        raise ConfigContractError(f"{name} must be > 0")
    return out


def _nonnegative_number(name: str, value: Any) -> float:
    try:
        out = float(value)
    except Exception as exc:
        raise ConfigContractError(f"{name} must be numeric") from exc
    if out < 0:
        raise ConfigContractError(f"{name} must be >= 0")
    return out


def _positive_int(name: str, value: Any) -> int:
    try:
        out = int(value)
    except Exception as exc:
        raise ConfigContractError(f"{name} must be an integer") from exc
    if out <= 0:
        raise ConfigContractError(f"{name} must be > 0")
    return out


def _validate_catalog_only_common_params(
    *,
    phase_format: Any,
    num_grids: Sequence[Any],
    xy_pad: Sequence[Any],
    num_workers: Any,
    hypodd_iter_rows: Optional[Sequence[Sequence[Any]]],
    hypodd_iphase: Any,
    hypodd_maxdist: Any,
    hypodd_minobs_ct: Any,
    ph2dt_minwght: Any,
    ph2dt_maxdist: Any,
    ph2dt_maxoffset: Any,
    ph2dt_mnb: Any,
    ph2dt_limobs_pair: Any,
    ph2dt_minobs_pair: Any,
    ph2dt_maxobs_pair: Any,
    velocity_model_top_km: Optional[Sequence[Any]],
    velocity_model_vp_km_s: Optional[Sequence[Any]],
    vp_vs_ratio: Any,
    hypodd_istart: Any = 2,
    hypodd_isolv: Any = 2,
    hypodd_iclust: Any = 0,
) -> Dict[str, Any]:
    """Validate shared catalog-only API parameters before native execution."""
    fmt = str(phase_format).strip().lower()
    if fmt not in ("auto", "hypodd", "pal"):
        raise ConfigContractError("phase_format must be 'auto', 'hypodd', or 'pal'")
    grids = _positive_int_pair("num_grids", num_grids)
    pads = _nonnegative_float_pair("xy_pad", xy_pad)
    workers = _positive_int("num_workers", num_workers)
    iphase = int(hypodd_iphase)
    if iphase not in (1, 2, 3):
        raise ConfigContractError("hypodd_iphase must be 1 (P), 2 (S), or 3 (P&S)")
    istart = int(hypodd_istart)
    if istart not in (1, 2):
        raise ConfigContractError("hypodd_istart must be 1 or 2")
    isolv = int(hypodd_isolv)
    if isolv not in (1, 2):
        raise ConfigContractError("hypodd_isolv must be 1 or 2")
    iclust = int(hypodd_iclust)
    if iclust < 0:
        raise ConfigContractError("hypodd_iclust must be >= 0")

    minobs_ct = int(hypodd_minobs_ct)
    if minobs_ct < 0:
        raise ConfigContractError("hypodd_minobs_ct must be >= 0")
    ph2dt_mnb_i = _positive_int("ph2dt_mnb", ph2dt_mnb)
    ph2dt_limobs_i = _positive_int("ph2dt_limobs_pair", ph2dt_limobs_pair)
    ph2dt_minobs_i = _positive_int("ph2dt_minobs_pair", ph2dt_minobs_pair)
    ph2dt_maxobs_i = _positive_int("ph2dt_maxobs_pair", ph2dt_maxobs_pair)
    if ph2dt_minobs_i > ph2dt_maxobs_i:
        raise ConfigContractError(
            format_contract_error(
                title="hypodd_runner ph2dt parameter contract failed.",
                real_error=(
                    f"ph2dt_minobs_pair={ph2dt_minobs_i} is greater than "
                    f"ph2dt_maxobs_pair={ph2dt_maxobs_i}."
                ),
                expected="Use minobs_pair <= maxobs_pair for ph2dt event-pair observation limits.",
                minimal_example="Ph2dtParams(minobs_pair=4, maxobs_pair=30)",
            )
        )

    model_top, model_vel = _validate_velocity_model(
        velocity_model_top_km, velocity_model_vp_km_s
    )
    ratio = _positive_number("vp_vs_ratio", vp_vs_ratio)
    if ratio <= 1.0:
        raise ConfigContractError("vp_vs_ratio must be > 1.0")

    return {
        "phase_format": fmt,
        "num_grids": grids,
        "xy_pad": pads,
        "num_workers": workers,
        "hypodd_iter_rows": _validate_iter_rows(hypodd_iter_rows),
        "hypodd_iphase": iphase,
        "hypodd_maxdist": _positive_number("hypodd_maxdist", hypodd_maxdist),
        "hypodd_minobs_ct": minobs_ct,
        "ph2dt_minwght": _nonnegative_number("ph2dt_minwght", ph2dt_minwght),
        "ph2dt_maxdist": _positive_number("ph2dt_maxdist", ph2dt_maxdist),
        "ph2dt_maxoffset": _nonnegative_number("ph2dt_maxoffset", ph2dt_maxoffset),
        "ph2dt_mnb": ph2dt_mnb_i,
        "ph2dt_limobs_pair": ph2dt_limobs_i,
        "ph2dt_minobs_pair": ph2dt_minobs_i,
        "ph2dt_maxobs_pair": ph2dt_maxobs_i,
        "hypodd_istart": istart,
        "hypodd_isolv": isolv,
        "hypodd_iclust": iclust,
        "hypodd_mod_ratio": ratio,
        "hypodd_mod_top": model_top,
        "hypodd_mod_vel": model_vel,
    }


def _split_catalog_line(line: str) -> List[str]:
    codes = line.strip().split(",")
    if len(codes) == 1:
        codes = line.strip().split()
    return [c.strip() for c in codes]


def _iter_data_lines(path: str):
    """Yield non-empty, non-comment input lines with split tokens."""
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        for lineno, line in enumerate(f, start=1):
            if not line.strip() or line.strip().startswith("#"):
                continue
            yield lineno, line, _split_catalog_line(line)


def _read_station_ids(path: str) -> Set[str]:
    from .mk_sta import _collect_nonempty_rows, _looks_like_header, _resolve_header_indices

    with open(path, "r", encoding="utf-8", errors="replace") as f:
        rows = _collect_nonempty_rows(f.readlines())
    if not rows:
        raise ConfigContractError(f"station_file has no non-comment station rows: {path}")
    _line_no0, first_codes = rows[0]
    if _looks_like_header(first_codes):
        sta_i, _lat_i, _lon_i = _resolve_header_indices(first_codes)
        body = rows[1:]
    else:
        sta_i = 0
        body = rows
    station_ids: Set[str] = set()
    for line_no, codes in body:
        if len(codes) <= sta_i:
            raise ConfigContractError(
                f"station_file line {line_no} does not contain a station id"
            )
        station_id = codes[sta_i].strip()
        station_ids.add(station_match_key(station_id))
    if not station_ids:
        raise ConfigContractError(f"station_file has no usable station ids: {path}")
    return station_ids


def _read_hypodd_phase_summary(
    path: str,
    *,
    ot_range: str,
    lat_range: Sequence[float],
    lon_range: Sequence[float],
) -> Dict[str, Any]:
    from .mk_pha import _is_missing_pick
    from .pha_format import looks_like_event_header_line

    ot_min, ot_max = [UTCDateTime(date) for date in ot_range.split("-")]
    lat_min, lat_max = [float(x) for x in lat_range]
    lon_min, lon_max = [float(x) for x in lon_range]
    total_events = 0
    selected_events = 0
    total_picks = 0
    selected_picks = 0
    station_ids: Set[str] = set()
    selected_station_ids: Set[str] = set()
    current_event_selected = False
    current_event_seen = False

    for lineno, line, codes in _iter_data_lines(path):
        if looks_like_event_header_line(codes):
            total_events += 1
            ot = UTCDateTime(codes[0])
            lat, lon = float(codes[1]), float(codes[2])
            current_event_selected = (
                ot_min < ot < ot_max
                and lat_min < lat <= lat_max
                and lon_min < lon <= lon_max
            )
            current_event_seen = True
            if current_event_selected:
                selected_events += 1
            continue
        if len(codes) < 3:
            raise ConfigContractError(
                f"phase_file line {lineno}: pick row must have station_id,P_pick,S_pick"
            )
        if not current_event_seen:
            raise ConfigContractError(
                f"phase_file line {lineno}: pick row appears before any valid event header"
            )
        station_ids.add(station_match_key(codes[0]))
        pick_count = int(not _is_missing_pick(codes[1])) + int(not _is_missing_pick(codes[2]))
        total_picks += pick_count
        if current_event_selected:
            selected_picks += pick_count
            selected_station_ids.add(station_match_key(codes[0]))

    if total_events == 0:
        raise ConfigContractError(f"phase_file has no valid event headers: {path}")
    return {
        "total_events": total_events,
        "selected_events": selected_events,
        "total_picks": total_picks,
        "selected_picks": selected_picks,
        "phase_station_ids": station_ids,
        "selected_phase_station_ids": selected_station_ids,
    }


def _event_selected(
    codes: Sequence[str],
    *,
    ot_range: str,
    lat_range: Sequence[float],
    lon_range: Sequence[float],
) -> bool:
    """Return true if an event-header token list passes time/spatial windows."""
    ot_min, ot_max = [UTCDateTime(date) for date in ot_range.split("-")]
    lat_min, lat_max = [float(x) for x in lat_range]
    lon_min, lon_max = [float(x) for x in lon_range]
    ot = UTCDateTime(codes[0])
    lat, lon = float(codes[1]), float(codes[2])
    return (
        ot_min < ot < ot_max
        and lat_min < lat <= lat_max
        and lon_min < lon <= lon_max
    )


def _selected_hypodd_event_blocks(
    phase_file: str,
    *,
    ot_range: str,
    lat_range: Sequence[float],
    lon_range: Sequence[float],
) -> List[List[str]]:
    """Return selected event blocks from a HypoDD-ready phase file."""
    from .pha_format import looks_like_event_header_line

    blocks: List[List[str]] = []
    current_block: List[str] = []
    current_selected = False
    seen_event = False

    with open(phase_file, "r", encoding="utf-8", errors="replace") as f:
        for lineno, line in enumerate(f, start=1):
            if not line.strip() or line.strip().startswith("#"):
                continue
            if "\x00" in line:
                raise ConfigContractError(
                    f"phase_file line {lineno} contains NUL bytes; the phase file is "
                    "corrupted or was incompletely written. Regenerate the phase file "
                    "before planning/running relocation."
                )
            codes = _split_catalog_line(line)
            if looks_like_event_header_line(codes):
                if current_block and current_selected:
                    blocks.append(current_block)
                current_block = [line]
                current_selected = _event_selected(
                    codes,
                    ot_range=ot_range,
                    lat_range=lat_range,
                    lon_range=lon_range,
                )
                seen_event = True
                continue
            if not seen_event:
                raise ConfigContractError(
                    f"phase_file line {lineno}: pick row appears before any valid event header"
                )
            if current_selected:
                current_block.append(line)

    if current_block and current_selected:
        blocks.append(current_block)
    return blocks


def _selected_hypodd_event_times(
    phase_file: str,
    *,
    ot_range: str,
    lat_range: Sequence[float],
    lon_range: Sequence[float],
) -> List[UTCDateTime]:
    """Return origin times for selected HypoDD-ready event headers."""
    from .pha_format import looks_like_event_header_line

    times: List[UTCDateTime] = []
    seen_event = False
    with open(phase_file, "r", encoding="utf-8", errors="replace") as f:
        for lineno, line in enumerate(f, start=1):
            if not line.strip() or line.strip().startswith("#"):
                continue
            codes = _split_catalog_line(line)
            if looks_like_event_header_line(codes):
                seen_event = True
                if _event_selected(
                    codes,
                    ot_range=ot_range,
                    lat_range=lat_range,
                    lon_range=lon_range,
                ):
                    times.append(UTCDateTime(codes[0]))
                continue
            if not seen_event:
                raise ConfigContractError(
                    f"phase_file line {lineno}: pick row appears before any valid event header"
                )
            if len(codes) < 3:
                raise ConfigContractError(
                    f"phase_file line {lineno}: pick row must have station_id,P_pick,S_pick"
                )
    return times


def plan_catalog_only_time_windows(
    *,
    phase_file: str,
    ot_range: Any,
    lat_range: Sequence[Any],
    lon_range: Sequence[Any],
    phase_format: str = "auto",
    base: str = "month",
    window_days: Optional[int] = None,
    min_events_per_window: int = 100,
    max_events_per_window: Optional[int] = None,
    window_prefix: str = "window",
) -> List[TimeWindowPlan]:
    """Plan catalog-only HypoDD time windows from a phase file.

    Parameters
    ----------
    phase_file
        Event-block phase file, or PAL/PALM-style phase table when
        ``phase_format`` permits conversion.
    ot_range, lat_range, lon_range
        Time and spatial bounds used before counting events in each window.
    phase_format
        ``"auto"``, ``"hypodd"``, or ``"pal"``.
    base, window_days
        Base window size: monthly, daily, or fixed ``window_days`` when
        ``base="days"``.
    min_events_per_window, max_events_per_window
        Merge sparse windows until the minimum is reached; reject a planned
        window above the maximum when supplied.
    window_prefix
        Prefix used when assigning stable window IDs.

    The planner reads the effective HypoDD-ready phase file, applies the same
    time and spatial selection used by the runner, merges sparse neighboring
    windows, and rejects windows that exceed ``max_events_per_window``. The
    returned :class:`TimeWindowPlan` records why each window exists and whether
    it was merged from smaller base windows.
    """
    phase_file = os.path.abspath(_require_path("phase_file", phase_file))
    normalized_ot_range = normalize_ot_range(ot_range)
    normalized_lat_range = _numeric_pair("lat_range", lat_range, cast=float, ordered=True)
    normalized_lon_range = _numeric_pair("lon_range", lon_range, cast=float, ordered=True)

    from .phase_convert import prepare_phase_file

    phase_result = prepare_phase_file(phase_file, phase_format)
    event_times = _selected_hypodd_event_times(
        phase_result.effective_path,
        ot_range=normalized_ot_range,
        lat_range=normalized_lat_range,
        lon_range=normalized_lon_range,
    )
    if not event_times:
        raise ConfigContractError(
            "No events remain for catalog-only time-window planning after "
            "ot_range/lat_range/lon_range filtering."
        )
    return plan_time_windows(
        event_times,
        base=base,
        window_days=window_days,
        min_events_per_window=min_events_per_window,
        max_events_per_window=max_events_per_window,
        window_prefix=window_prefix,
    )


def _chunk_blocks(blocks: Sequence[List[str]], max_events_per_batch: int) -> List[List[List[str]]]:
    """Split event blocks into event-count limited chunks."""
    if max_events_per_batch <= 0:
        raise ConfigContractError("max_events_per_batch must be a positive integer")
    return [
        list(blocks[i : i + max_events_per_batch])
        for i in range(0, len(blocks), max_events_per_batch)
    ]


def _write_phase_blocks(path: str, blocks: Sequence[Sequence[str]]) -> str:
    """Write selected event blocks to a phase file and return the absolute path."""
    path = os.path.abspath(path)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        for block in blocks:
            for line in block:
                f.write(line if line.endswith("\n") else line + "\n")
    return path


def _failure_signature(tb_text: str) -> str:
    """Return the final non-empty traceback line as a compact failure signature."""
    for line in reversed(tb_text.splitlines()):
        line = line.strip()
        if line:
            return line[:500]
    return "unknown failure"


def _classify_failure_kind(exc: BaseException, tb_text: str) -> str:
    """Classify failures into stable categories for manifests and debugging."""
    lower_tb = tb_text.lower()
    if (
        "empty hypodd native" in lower_tb
        or "native relocated catalog has no parseable rows" in lower_tb
        or "native original catalog has no parseable rows" in lower_tb
        or "native relocated catalog is invalid" in lower_tb
        or "native original catalog is invalid" in lower_tb
    ):
        return "empty_native_output"
    if "exceeds the native compiled event limit" in lower_tb or "increase maxeve" in lower_tb:
        return "native_scale_limit"
    if isinstance(exc, InsufficientDTimeError) or "InsufficientDTimeError" in tb_text:
        return "insufficient_dtimes"
    if isinstance(exc, NativeProgramError) or "NativeProgramError" in tb_text:
        return "native_program"
    if isinstance(exc, NativeOutputError) or "NativeOutputError" in tb_text:
        return "native_output_missing"
    if isinstance(exc, ConfigContractError) or "ConfigContractError" in tb_text:
        return "config_contract"
    return "unexpected_exception"


def check_catalog_only_inputs(
    *,
    phase_file: str,
    station_file: str,
    ot_range: Any,
    lat_range: Sequence[Any],
    lon_range: Sequence[Any],
    phase_format: str = "auto",
) -> CatalogOnlyInputCheck:
    """Audit catalog-only inputs before running native ph2dt/HypoDD.

    Parameters
    ----------
    phase_file, station_file
        Existing phase and station input files.
    ot_range
        Time range as ``'YYYYMMDD-YYYYMMDD'`` or a two-value date sequence.
    lat_range, lon_range
        Selection windows as ``[min, max]``.
    phase_format
        ``'auto'``, ``'hypodd'``, or ``'pal'``.

    Returns
    -------
    CatalogOnlyInputCheck
        Counts, station consistency, and messages describing the precheck.

    The check is intentionally lightweight and does not run native programs. For
    HypoDD-ready phase files it verifies parseability, selected event/pick counts,
    and station-id consistency. PAL input is classified but not converted here.
    """
    phase_file = os.path.abspath(_require_path("phase_file", phase_file))
    station_file = os.path.abspath(_require_path("station_file", station_file))
    if not os.path.exists(phase_file):
        raise ConfigContractError(f"phase_file does not exist: {phase_file}")
    if not os.path.exists(station_file):
        raise ConfigContractError(f"station_file does not exist: {station_file}")

    normalized_ot_range = normalize_ot_range(ot_range)
    normalized_lat_range = _numeric_pair("lat_range", lat_range, cast=float, ordered=True)
    normalized_lon_range = _numeric_pair("lon_range", lon_range, cast=float, ordered=True)
    phase_format = str(phase_format).strip().lower()
    if phase_format not in ("auto", "hypodd", "pal"):
        raise ConfigContractError("phase_format must be 'auto', 'hypodd', or 'pal'")

    station_ids = _read_station_ids(station_file)
    messages: List[str] = []
    blocking_messages: List[str] = []
    effective_phase_kind = "unknown"

    from .phase_convert import (
        file_has_hypodd_event_header,
        file_looks_like_pal_phase,
        phase_input_format_help,
    )

    has_hypodd_header = file_has_hypodd_event_header(phase_file)
    looks_pal = file_looks_like_pal_phase(phase_file)
    if phase_format == "hypodd" or (phase_format == "auto" and has_hypodd_header):
        effective_phase_kind = "hypodd"
        summary = _read_hypodd_phase_summary(
            phase_file,
            ot_range=normalized_ot_range,
            lat_range=normalized_lat_range,
            lon_range=normalized_lon_range,
        )
    elif phase_format == "pal" or (phase_format == "auto" and looks_pal):
        effective_phase_kind = "pal"
        messages.append(
            "PAL/PALM phase input detected; detailed event/station selection check is "
            "deferred until hypodd_runner converts the phase file during execution."
        )
        summary = {
            "total_events": 0,
            "selected_events": 0,
            "total_picks": 0,
            "selected_picks": 0,
            "phase_station_ids": set(),
            "selected_phase_station_ids": set(),
        }
    else:
        raise ConfigContractError(
            "Could not classify phase_file as hypodd_runner event-block input or PAL input. "
            "Check phase_format and the first non-comment data line.\n"
            f"{phase_input_format_help()}"
        )

    phase_station_ids = summary["phase_station_ids"]
    selected_phase_station_ids = summary["selected_phase_station_ids"]
    missing_phase_stations = sorted(phase_station_ids - station_ids)
    if effective_phase_kind == "hypodd":
        missing_phase_stations = sorted(selected_phase_station_ids - station_ids)
        if summary["selected_events"] == 0:
            blocking_messages.append(
                "No events remain after ot_range/lat_range/lon_range filtering."
            )
        if summary["selected_picks"] == 0:
            blocking_messages.append("No phase picks remain after event selection.")
        if missing_phase_stations:
            blocking_messages.append(
                f"{len(missing_phase_stations)} phase station id(s) are absent from station_file."
            )
        messages.extend(blocking_messages)

    ok = not blocking_messages
    return CatalogOnlyInputCheck(
        ok=ok,
        phase_file=phase_file,
        station_file=station_file,
        phase_format=phase_format,
        effective_phase_kind=effective_phase_kind,
        total_events=int(summary["total_events"]),
        selected_events=int(summary["selected_events"]),
        total_picks=int(summary["total_picks"]),
        selected_picks=int(summary["selected_picks"]),
        station_count=len(station_ids),
        phase_station_count=len(phase_station_ids),
        missing_phase_stations=missing_phase_stations[:50],
        messages=messages,
        blocking_messages=blocking_messages,
    )


def build_catalog_only_config(
    *,
    hypo_root: str,
    phase_file: str,
    station_file: str,
    output_folder: str,
    catalog_code: str,
    ot_range: Any,
    lat_range: Sequence[Any],
    lon_range: Sequence[Any],
    velocity_model_top_km: Optional[Sequence[Any]] = None,
    velocity_model_vp_km_s: Optional[Sequence[Any]] = None,
    vp_vs_ratio: float = 1.73,
    phase_format: str = "auto",
    num_grids: Sequence[Any] = (1, 1),
    xy_pad: Sequence[Any] = (0.0, 0.0),
    num_workers: int = 1,
    keep_grids: bool = True,
    hypodd_iter_rows: Optional[Sequence[Sequence[Any]]] = None,
    hypodd_iphase: int = 3,
    hypodd_maxdist: float = 120.0,
    hypodd_minobs_ct: int = 0,
    ph2dt_minwght: float = 0.0,
    ph2dt_maxdist: float = 120.0,
    ph2dt_maxoffset: float = 50.0,
    ph2dt_mnb: int = 10,
    ph2dt_limobs_pair: int = 8,
    ph2dt_minobs_pair: int = 4,
    ph2dt_maxobs_pair: int = 30,
    dep_corr: float = 0.0,
    hypodd_istart: int = 2,
    hypodd_isolv: int = 2,
    hypodd_iclust: int = 0,
) -> Dict[str, Any]:
    """Return a complete, validated config dictionary for catalog-only runs.

    Parameters
    ----------
    hypo_root
        Path containing the local HYPODD ``ph2dt`` and ``hypoDD`` binaries.
    phase_file, station_file
        Existing hypodd_runner/PAL phase file and station file.
    output_folder, catalog_code
        Native run output directory and output prefix.
    ot_range, lat_range, lon_range
        Event selection windows for ``mk_pha``.
    velocity_model_top_km, velocity_model_vp_km_s, vp_vs_ratio
        Optional 1-D HypoDD velocity model. Tops and Vp arrays must be supplied
        together with equal length.
    phase_format
        ``'auto'``, ``'hypodd'``, or ``'pal'``.
    num_grids, xy_pad, num_workers, keep_grids
        Grid execution controls.
    hypodd_iter_rows, hypodd_iphase, hypodd_maxdist, hypodd_minobs_ct,
    hypodd_istart, hypodd_isolv, hypodd_iclust
        Core HypoDD controls for catalog-only relocation.
    ph2dt_minwght, ph2dt_maxdist, ph2dt_maxoffset, ph2dt_mnb,
    ph2dt_limobs_pair, ph2dt_minobs_pair, ph2dt_maxobs_pair
        ph2dt event-pair/link controls.
    dep_corr
        Constant depth correction passed through to the pipeline before native
        input generation.

    Returns
    -------
    dict
        Full config dictionary accepted by :class:`Config`.

    The returned dictionary uses the existing full pipeline config schema, but
    exposes only the parameters normally needed for catalog-only ph2dt/HypoDD.
    It sets ``cc_engine='none'`` and ``hypodd_idata=2`` so generated code does
    not need waveform/FDTCC keys.
    """
    common = _validate_catalog_only_common_params(
        phase_format=phase_format,
        num_grids=num_grids,
        xy_pad=xy_pad,
        num_workers=num_workers,
        hypodd_iter_rows=hypodd_iter_rows,
        hypodd_iphase=hypodd_iphase,
        hypodd_maxdist=hypodd_maxdist,
        hypodd_minobs_ct=hypodd_minobs_ct,
        ph2dt_minwght=ph2dt_minwght,
        ph2dt_maxdist=ph2dt_maxdist,
        ph2dt_maxoffset=ph2dt_maxoffset,
        ph2dt_mnb=ph2dt_mnb,
        ph2dt_limobs_pair=ph2dt_limobs_pair,
        ph2dt_minobs_pair=ph2dt_minobs_pair,
        ph2dt_maxobs_pair=ph2dt_maxobs_pair,
        velocity_model_top_km=velocity_model_top_km,
        velocity_model_vp_km_s=velocity_model_vp_km_s,
        vp_vs_ratio=vp_vs_ratio,
        hypodd_istart=hypodd_istart,
        hypodd_isolv=hypodd_isolv,
        hypodd_iclust=hypodd_iclust,
    )
    precheck = check_catalog_only_inputs(
        phase_file=phase_file,
        station_file=station_file,
        ot_range=ot_range,
        lat_range=lat_range,
        lon_range=lon_range,
        phase_format=common["phase_format"],
    )
    if not precheck.ok:
        raise ConfigContractError(
            _format_catalog_precheck_failure("Catalog-only input precheck", precheck)
        )
    if precheck.effective_phase_kind == "hypodd":
        _check_hypodd_event_limit(
            hypo_root=hypo_root,
            selected_events=precheck.selected_events,
        )
    config = {
        "hypo_root": os.path.abspath(_require_path("hypo_root", hypo_root)),
        "hypoDD_inp_template": os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "template", "hypoDD.inp"
        ),
        "hypoDD_ph2dt_template": os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "template", "ph2dt.inp"
        ),
        "hypodd_inp_mode": "programmatic",
        "ctlg_code": str(catalog_code).strip(),
        "output_folder": os.path.abspath(_require_path("output_folder", output_folder)),
        "fsta": os.path.abspath(_require_path("station_file", station_file)),
        "fpha": os.path.abspath(_require_path("phase_file", phase_file)),
        "dep_corr": float(dep_corr),
        "ot_range": normalize_ot_range(ot_range),
        "lat_range": _numeric_pair("lat_range", lat_range, cast=float, ordered=True),
        "lon_range": _numeric_pair("lon_range", lon_range, cast=float, ordered=True),
        "num_grids": common["num_grids"],
        "xy_pad": common["xy_pad"],
        "num_workers": common["num_workers"],
        "keep_grids": bool(keep_grids),
        "hypodd_idata": 2,
        "hypodd_iphase": common["hypodd_iphase"],
        "hypodd_maxdist": common["hypodd_maxdist"],
        "hypodd_minobs_cc": 0,
        "hypodd_minobs_ct": common["hypodd_minobs_ct"],
        "hypodd_istart": common["hypodd_istart"],
        "hypodd_isolv": common["hypodd_isolv"],
        "hypodd_iter_rows": common["hypodd_iter_rows"],
        "hypodd_mod_ratio": common["hypodd_mod_ratio"],
        "hypodd_mod_top": common["hypodd_mod_top"],
        "hypodd_mod_vel": common["hypodd_mod_vel"],
        "hypodd_iclust": common["hypodd_iclust"],
        "hypodd_dt_cc_per_grid": False,
        "ph2dt_minwght": common["ph2dt_minwght"],
        "ph2dt_maxdist": common["ph2dt_maxdist"],
        "ph2dt_maxoffset": common["ph2dt_maxoffset"],
        "ph2dt_mnb": common["ph2dt_mnb"],
        "ph2dt_limobs_pair": common["ph2dt_limobs_pair"],
        "ph2dt_minobs_pair": common["ph2dt_minobs_pair"],
        "ph2dt_maxobs_pair": common["ph2dt_maxobs_pair"],
        "ph2dt_inp_mode": "programmatic",
        "phase_format": str(phase_format).strip().lower(),
        "cc_engine": "none",
        "fdtcc_velocity_nd": None,
        "fdtcc_miniseed_root": None,
        "waveform_dir_raw": None,
        "fdtcc_miniseed_filename_template": None,
        "fdtcc_sac_pre_sec": 120.0,
        "fdtcc_sac_post_sec": 300.0,
        "fdtcc_sac_export_backend": "process",
        "fdtcc_cleanup_sac_waveforms": True,
        "keep_waveform_temp": False,
        "fdtcc_wave_dir_mode": "miniseed",
        "fdtcc_waveform_temp_basename": "waveform_temp",
        "fdtcc_prepare_inputs": False,
        "fdtcc_rebuild_ttdb": False,
    }
    if not config["ctlg_code"]:
        raise ConfigContractError("catalog_code must be a non-empty string")
    Config(**config)
    return config


def _count_nonempty_lines(path: str) -> int:
    if not os.path.exists(path) or os.path.getsize(path) == 0:
        return 0
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        return sum(1 for line in f if line.strip())


def _catalog_log_paths(output_folder: str) -> List[str]:
    patterns = (
        "ph2dt.log",
        "hypoDD.log",
        "*.hypoDD",
        "*.ph2dt",
        "*.log",
        "*.err",
        "*.out",
        "*.stderr",
    )
    hits = []
    for pattern in patterns:
        import glob

        hits.extend(glob.glob(os.path.join(output_folder, pattern)))
    return sorted({os.path.abspath(p) for p in hits if os.path.isfile(p)})


def inspect_catalog_only_outputs(
    output_folder: str,
    catalog_code: str,
    *,
    config: Optional[Config] = None,
    config_path: Optional[str] = None,
) -> CatalogOnlyResult:
    """Inspect native catalog-only outputs and return a structured summary.

    Parameters
    ----------
    output_folder, catalog_code
        Native output directory and catalog prefix.
    config, config_path
        Optional effective config and generated JSON path to attach to the
        returned result.

    Returns
    -------
    CatalogOnlyResult
        Output paths, line counts, log paths, and missing/empty required files.
    """
    output_folder = os.path.abspath(output_folder)
    catalog_code = str(catalog_code).strip()
    loc_path = os.path.join(output_folder, f"{catalog_code}.loc")
    reloc_path = os.path.join(output_folder, f"{catalog_code}.reloc")
    residual_path = os.path.join(output_folder, f"{catalog_code}.res")
    required = [loc_path, reloc_path]
    missing_or_empty = [
        path for path in required if (not os.path.exists(path) or os.path.getsize(path) == 0)
    ]
    return CatalogOnlyResult(
        config=config,
        config_path=os.path.abspath(config_path) if config_path else "",
        output_folder=output_folder,
        catalog_code=catalog_code,
        loc_path=loc_path,
        reloc_path=reloc_path,
        residual_path=residual_path,
        loc_rows=_count_nonempty_lines(loc_path),
        reloc_rows=_count_nonempty_lines(reloc_path),
        residual_rows=_count_nonempty_lines(residual_path),
        log_paths=_catalog_log_paths(output_folder),
        missing_or_empty=missing_or_empty,
    )


def require_catalog_only_native_outputs(
    output_folder: str,
    catalog_code: str,
    *,
    config: Optional[Config] = None,
    config_path: Optional[str] = None,
) -> CatalogOnlyResult:
    """Return output summary or raise if required native catalogs are missing/empty.

    Parameters
    ----------
    output_folder, catalog_code
        Native output directory and catalog prefix to inspect.
    config, config_path
        Optional effective config object and generated config path to attach to
        the returned summary.

    Required native catalog outputs are ``{catalog_code}.loc`` and
    ``{catalog_code}.reloc``. Placeholder CSV files are not accepted as success.
    """
    result = inspect_catalog_only_outputs(
        output_folder,
        catalog_code,
        config=config,
        config_path=config_path,
    )
    if not result.success:
        joined = ", ".join(os.path.basename(p) for p in result.missing_or_empty)
        raise NativeOutputError(
            "HypoDD did not produce valid native catalog outputs. "
            f"Missing or empty: {joined}. Inspect ph2dt/HypoDD logs in "
            f"{os.path.abspath(output_folder)}; do not create synthetic catalog CSV files."
        )
    return result


def run_catalog_only_relocation(**kwargs: Any) -> CatalogOnlyResult:
    """Run catalog-only ph2dt/HypoDD relocation from function parameters.

    Parameters
    ----------
    **kwargs
        Keyword arguments accepted by :func:`build_catalog_only_config`, such
        as ``hypo_root``, ``phase_file``, ``station_file``, ``output_folder``,
        ``catalog_code``, ``ot_range``, ``lat_range``, ``lon_range``, and
        optional HypoDD/ph2dt controls.

        The function also accepts grouped dictionaries commonly emitted by
        agents: ``inputs`` (paths), ``selection`` (time/lat/lon windows),
        ``ph2dt`` (ph2dt controls), ``hypodd`` (HypoDD controls), and
        ``runtime`` (grid/worker/output controls). Explicit top-level keyword
        arguments override values from those groups.

    Returns
    -------
    CatalogOnlyResult
        Structured result summary for the completed native run.

    The native run is controlled by direct function parameters and
    :class:`Config(**params)`, not by re-reading JSON.

    Examples
    --------
    >>> result = run_catalog_only_relocation(
    ...     hypo_root="/path/to/HYPODD",
    ...     phase_file="phase.dat",
    ...     station_file="station.sta",
    ...     output_folder="reloc_out",
    ...     catalog_code="aomori",
    ...     ot_range=["2019-01-01T00:00:00", "2019-01-02T00:00:00"],
    ...     lat_range=[40.0, 41.5],
    ...     lon_range=[140.0, 142.0],
    ... )
    """
    if any(
        key in kwargs
        for key in ("inputs", "selection", "ph2dt", "hypodd", "runtime")
    ):
        grouped_keys = {"inputs", "selection", "ph2dt", "hypodd", "runtime"}
        grouped = {key: kwargs.pop(key, None) for key in grouped_keys}
        kwargs = grouped_to_catalog_only_kwargs(
            inputs=grouped.get("inputs"),
            selection=grouped.get("selection"),
            ph2dt=grouped.get("ph2dt"),
            hypodd=grouped.get("hypodd"),
            runtime=grouped.get("runtime"),
            overrides=kwargs,
        )
    config_dict = build_catalog_only_config(**kwargs)

    from .api import run_config

    cfg = Config(**config_dict)
    run_config(cfg)
    return require_catalog_only_native_outputs(
        cfg.output_folder,
        cfg.ctlg_code,
        config=cfg,
        config_path="",
    )


def _write_batch_status_csv(path: str, batches: Sequence[CatalogOnlyBatchEntry]) -> str:
    """Write compact batch status rows without embedding long tracebacks."""
    path = os.path.abspath(path)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    fieldnames = [
        "batch_id",
        "status",
        "input_events",
        "phase_file",
        "output_folder",
        "config_path",
        "loc_rows",
        "reloc_rows",
        "residual_rows",
        "error_path",
        "error_signature",
        "failure_kind",
        "ot_range",
        "plan_reason",
        "merged_from",
        "parallel_safe",
    ]
    with open(path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for entry in batches:
            writer.writerow(entry.as_dict())
    return path


def _concat_existing_files(paths: Sequence[str], out_path: str) -> str:
    """Concatenate existing non-empty text files into ``out_path``."""
    out_path = os.path.abspath(out_path)
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as fout:
        for path in paths:
            if not path or not os.path.exists(path) or os.path.getsize(path) == 0:
                continue
            with open(path, "r", encoding="utf-8", errors="replace") as fin:
                for line in fin:
                    fout.write(line)
    return out_path


def _write_batch_manifest(path: str, result: CatalogOnlyBatchResult) -> str:
    """Write a JSON batch manifest and return its path."""
    path = os.path.abspath(path)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(result.as_dict(), f, indent=2, sort_keys=True)
        f.write("\n")
    return path


def _write_batch_manifest_with_extra(
    path: str,
    result: CatalogOnlyBatchResult,
    *,
    extra: Optional[Dict[str, Any]] = None,
) -> str:
    """Write a batch manifest with optional top-level diagnostic sections."""
    path = os.path.abspath(path)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    payload = result.as_dict()
    if extra:
        payload.update(extra)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, sort_keys=True)
        f.write("\n")
    return path


def run_catalog_only_batches(
    *,
    max_events_per_batch: int = 9000,
    batch_dir_name: str = "batches",
    batch_prefix: str = "batch",
    allow_partial: bool = False,
    **kwargs: Any,
) -> CatalogOnlyBatchResult:
    """Run catalog-only relocation in independent event-count batches.

    This is a legacy/fallback split mode. Generated agent scripts should prefer
    :func:`run_catalog_only_auto_time_windows`, which keeps the original
    phase/station files and narrows ``ot_range`` per window. Use this batch
    helper only when an explicit task requires event-count chunks and accepts
    generated per-batch phase files.

    Parameters
    ----------
    max_events_per_batch
        Maximum selected events written to each batch phase file.
    batch_dir_name
        Subdirectory under ``output_folder`` that stores per-batch runs.
    batch_prefix
        Prefix used for generated batch ids.
    allow_partial
        If false, any failed batch raises :class:`NativeOutputError` after
        writing the manifest and compact status table. If true, partial merged
        outputs are returned with ``success=False``.
    **kwargs
        Keyword arguments accepted by :func:`build_catalog_only_config`.

    Returns
    -------
    CatalogOnlyBatchResult
        Batch manifest, compact status table, merged output paths, and per-batch
        status records.

    Raises
    ------
    ConfigContractError
        If inputs are invalid or no selected event blocks are available.
    NativeOutputError
        If all batches fail to produce valid native outputs.
    """
    output_folder = os.path.abspath(_require_path("output_folder", kwargs.get("output_folder")))
    catalog_code = str(kwargs.get("catalog_code", "")).strip()
    if not catalog_code:
        raise ConfigContractError("catalog_code must be a non-empty string")
    os.makedirs(output_folder, exist_ok=True)

    phase_file = _require_path("phase_file", kwargs.get("phase_file"))
    station_file = _require_path("station_file", kwargs.get("station_file"))
    phase_format = str(kwargs.get("phase_format", "auto")).strip().lower()
    ot_range = normalize_ot_range(kwargs.get("ot_range"))
    lat_range = _numeric_pair("lat_range", kwargs.get("lat_range"), cast=float, ordered=True)
    lon_range = _numeric_pair("lon_range", kwargs.get("lon_range"), cast=float, ordered=True)

    precheck = check_catalog_only_inputs(
        phase_file=phase_file,
        station_file=station_file,
        ot_range=ot_range,
        lat_range=lat_range,
        lon_range=lon_range,
        phase_format=phase_format,
    )
    if not precheck.ok:
        raise ConfigContractError(
            _format_catalog_precheck_failure("Catalog-only batch input precheck", precheck)
        )
    limits = _read_active_hypodd_limits(kwargs.get("hypo_root", ""))
    maxeve = limits.get("MAXEVE")
    if maxeve is not None and int(max_events_per_batch) > maxeve:
        raise ConfigContractError(
            "Catalog-only batch size exceeds the native HypoDD compiled event "
            f"limit: max_events_per_batch={int(max_events_per_batch)} > MAXEVE={maxeve} "
            "from hypoDD.inc. Set max_events_per_batch <= MAXEVE. For large "
            "catalog-only tasks, run_catalog_only_auto_time_windows(...) is "
            "usually the safer public entry point. Rebuilding native HypoDD "
            "with a larger MAXEVE is a separate maintenance task."
        )

    from .phase_convert import prepare_phase_file

    phase_result = prepare_phase_file(phase_file, phase_format)
    effective_phase_file = phase_result.effective_path

    blocks = _selected_hypodd_event_blocks(
        effective_phase_file,
        ot_range=ot_range,
        lat_range=lat_range,
        lon_range=lon_range,
    )
    if not blocks:
        raise ConfigContractError("No selected event blocks are available for batching")

    chunks = _chunk_blocks(blocks, int(max_events_per_batch))
    batch_root = os.path.join(output_folder, batch_dir_name)
    batches: List[CatalogOnlyBatchEntry] = []
    successful_results: List[CatalogOnlyResult] = []

    for index, chunk in enumerate(chunks, start=1):
        batch_id = f"{batch_prefix}_{index:03d}"
        batch_output = os.path.join(batch_root, batch_id)
        batch_phase = _write_phase_blocks(os.path.join(batch_output, "batch_phase.dat"), chunk)
        batch_kwargs = dict(kwargs)
        batch_kwargs.update(
            {
                "phase_file": batch_phase,
                "output_folder": batch_output,
                "catalog_code": catalog_code,
                "phase_format": "hypodd",
            }
        )
        try:
            result = run_catalog_only_relocation(
                **batch_kwargs,
            )
            successful_results.append(result)
            batches.append(
                CatalogOnlyBatchEntry(
                    batch_id=batch_id,
                    status="success",
                    input_events=len(chunk),
                    phase_file=batch_phase,
                    output_folder=batch_output,
                    config_path="",
                    loc_rows=result.loc_rows,
                    reloc_rows=result.reloc_rows,
                    residual_rows=result.residual_rows,
                )
            )
        except Exception as exc:
            tb_text = traceback.format_exc()
            error_path = os.path.join(batch_output, "failure_traceback.txt")
            os.makedirs(batch_output, exist_ok=True)
            with open(error_path, "w", encoding="utf-8") as f:
                f.write(tb_text)
            batches.append(
                CatalogOnlyBatchEntry(
                    batch_id=batch_id,
                    status="failed",
                    input_events=len(chunk),
                    phase_file=batch_phase,
                    output_folder=batch_output,
                    config_path="",
                    error_path=error_path,
                    error_signature=_failure_signature(tb_text),
                    failure_kind=_classify_failure_kind(exc, tb_text),
                )
            )

    merged_loc_path = _concat_existing_files(
        [r.loc_path for r in successful_results],
        os.path.join(output_folder, f"{catalog_code}.loc"),
    )
    merged_reloc_path = _concat_existing_files(
        [r.reloc_path for r in successful_results],
        os.path.join(output_folder, f"{catalog_code}.reloc"),
    )
    merged_residual_path = _concat_existing_files(
        [r.residual_path for r in successful_results],
        os.path.join(output_folder, f"{catalog_code}.res"),
    )
    status_csv = _write_batch_status_csv(
        os.path.join(output_folder, "batch_status.csv"),
        batches,
    )
    manifest_path = os.path.join(output_folder, "batch_manifest.json")
    result = CatalogOnlyBatchResult(
        output_folder=output_folder,
        catalog_code=catalog_code,
        total_input_events=len(blocks),
        success_batches=sum(1 for b in batches if b.status == "success"),
        failed_batches=sum(1 for b in batches if b.status == "failed"),
        merged_loc_path=merged_loc_path,
        merged_reloc_path=merged_reloc_path,
        merged_residual_path=merged_residual_path,
        manifest_path=os.path.abspath(manifest_path),
        batch_status_csv=status_csv,
        batches=batches,
    )
    _write_batch_manifest(manifest_path, result)

    if not result.success:
        first_error = next((b.error_signature for b in batches if b.error_signature), "")
    if result.success:
        return result
    if allow_partial and result.success_batches > 0:
        return result
    if result.success_batches == 0:
        raise NativeOutputError(
            "All catalog-only HypoDD batches failed; no valid merged relocation output "
            f"was produced. batch_status_csv={status_csv}; manifest={manifest_path}; "
            f"first_error={first_error}. Inspect the per-batch failure_traceback/native "
            "logs recorded in the manifest; do not replace failed windows with "
            "placeholder or unchanged catalogs."
        )
    raise NativeOutputError(
        "Catalog-only HypoDD batch relocation produced only partial results. "
        f"success_batches={result.success_batches}; failed_batches={result.failed_batches}; "
        f"batch_status_csv={status_csv}; manifest={manifest_path}; first_error={first_error}"
    )


def run_catalog_only_time_windows(
    *,
    time_windows: Sequence[Any],
    time_window_dir_name: str = "time_windows",
    window_prefix: str = "window",
    num_window_workers: int = 1,
    allow_partial: bool = False,
    continue_on_error: bool = False,
    verbose: bool = False,
    planning_evidence: Optional[Dict[str, Any]] = None,
    **kwargs: Any,
) -> CatalogOnlyBatchResult:
    """Run catalog-only relocation by repeatedly narrowing ``ot_range``.

    This is the preferred batching mode when a full catalog exceeds native
    HypoDD limits such as ``MAXEVE``. Each time window calls
    :func:`run_catalog_only_relocation` with the original phase/station files and
    a narrower ``ot_range``. It does not rewrite selected event blocks into
    synthetic batch phase files.

    Parameters
    ----------
    time_windows
        Sequence of time ranges accepted by :func:`normalize_ot_range`, for
        example ``[("2025-10-01", "2025-11-01"), ("2025-11-01", "2025-12-01")]``.
    time_window_dir_name
        Subdirectory under ``output_folder`` that stores per-window native runs.
    window_prefix
        Prefix used for generated window ids.
    num_window_workers
        Reserved for future window-level parallel execution. The current
        implementation requires ``1`` so native output and logging remain
        deterministic.
    allow_partial
        If false, any failed non-empty window raises :class:`NativeOutputError`
        after writing status and manifest files.
    continue_on_error
        If false, stop after the first failed non-empty window once its
        traceback has been written. If true, continue through remaining windows
        and report aggregate success/failure at the end.
    verbose
        If true, print one line for every selected window. By default only
        compact plan/failure summaries are printed; full window details are
        preserved in the manifest/status files.
    planning_evidence
        Optional dictionary written to ``time_window_manifest.json`` under the
        ``planning`` key. Use this for auto-planned windows.
    **kwargs
        Keyword arguments accepted by :func:`build_catalog_only_config`.

    Returns
    -------
    CatalogOnlyBatchResult
        Per-window status, merged native outputs, and manifest paths.
    """
    if not time_windows:
        raise ConfigContractError("time_windows must contain at least one ot_range")
    if int(num_window_workers) != 1:
        raise ConfigContractError(
            "num_window_workers is reserved for future window-level parallelism; "
            "the current stable implementation requires num_window_workers=1. "
            "Use package-internal num_workers for each native run."
        )

    output_folder = os.path.abspath(_require_path("output_folder", kwargs.get("output_folder")))
    catalog_code = str(kwargs.get("catalog_code", "")).strip()
    if not catalog_code:
        raise ConfigContractError("catalog_code must be a non-empty string")
    os.makedirs(output_folder, exist_ok=True)

    phase_file = _require_path("phase_file", kwargs.get("phase_file"))
    station_file = _require_path("station_file", kwargs.get("station_file"))
    phase_format = str(kwargs.get("phase_format", "auto")).strip().lower()
    lat_range = _numeric_pair("lat_range", kwargs.get("lat_range"), cast=float, ordered=True)
    lon_range = _numeric_pair("lon_range", kwargs.get("lon_range"), cast=float, ordered=True)
    _validate_catalog_only_common_params(
        phase_format=phase_format,
        num_grids=kwargs.get("num_grids", (1, 1)),
        xy_pad=kwargs.get("xy_pad", (0.0, 0.0)),
        num_workers=kwargs.get("num_workers", 1),
        hypodd_iter_rows=kwargs.get("hypodd_iter_rows"),
        hypodd_iphase=kwargs.get("hypodd_iphase", 3),
        hypodd_maxdist=kwargs.get("hypodd_maxdist", 120.0),
        hypodd_minobs_ct=kwargs.get("hypodd_minobs_ct", 0),
        ph2dt_minwght=kwargs.get("ph2dt_minwght", 0.0),
        ph2dt_maxdist=kwargs.get("ph2dt_maxdist", 120.0),
        ph2dt_maxoffset=kwargs.get("ph2dt_maxoffset", 50.0),
        ph2dt_mnb=kwargs.get("ph2dt_mnb", 10),
        ph2dt_limobs_pair=kwargs.get("ph2dt_limobs_pair", 8),
        ph2dt_minobs_pair=kwargs.get("ph2dt_minobs_pair", 4),
        ph2dt_maxobs_pair=kwargs.get("ph2dt_maxobs_pair", 30),
        velocity_model_top_km=kwargs.get("velocity_model_top_km"),
        velocity_model_vp_km_s=kwargs.get("velocity_model_vp_km_s"),
        vp_vs_ratio=kwargs.get("vp_vs_ratio", 1.73),
        hypodd_istart=kwargs.get("hypodd_istart", 2),
        hypodd_isolv=kwargs.get("hypodd_isolv", 2),
        hypodd_iclust=kwargs.get("hypodd_iclust", 0),
    )

    window_root = os.path.join(output_folder, time_window_dir_name)
    batches: List[CatalogOnlyBatchEntry] = []
    successful_results: List[CatalogOnlyResult] = []
    total_input_events = 0

    for index, raw_window in enumerate(time_windows, start=1):
        if isinstance(raw_window, TimeWindowPlan):
            ot_range = raw_window.ot_range
            window_id = raw_window.window_id
            plan_reason = raw_window.reason
            merged_from = list(raw_window.merged_from)
            parallel_safe = bool(raw_window.parallel_safe)
        else:
            ot_range = normalize_ot_range(raw_window)
            safe_range = ot_range.replace("-", "_")
            window_id = f"{window_prefix}_{index:03d}_{safe_range}"
            plan_reason = "manual_window"
            merged_from = [ot_range]
            parallel_safe = True
        window_output = os.path.join(window_root, window_id)
        selected_events = 0
        try:
            precheck = check_catalog_only_inputs(
                phase_file=phase_file,
                station_file=station_file,
                ot_range=ot_range,
                lat_range=lat_range,
                lon_range=lon_range,
                phase_format=phase_format,
            )
            if not precheck.ok:
                raise ConfigContractError(
                    _format_catalog_precheck_failure(
                        "Catalog-only time-window input precheck", precheck
                    )
                )
            if precheck.selected_events == 0:
                batches.append(
                    CatalogOnlyBatchEntry(
                        batch_id=window_id,
                        status="skipped_empty",
                    input_events=0,
                    phase_file=os.path.abspath(phase_file),
                    output_folder=window_output,
                    config_path="",
                    error_signature=f"no selected events for ot_range={ot_range}",
                    failure_kind="empty_window",
                    ot_range=ot_range,
                    plan_reason=plan_reason,
                        merged_from=merged_from,
                        parallel_safe=parallel_safe,
                    )
                )
                continue

            selected_events = precheck.selected_events
            total_input_events += selected_events
            _check_hypodd_event_limit(
                hypo_root=kwargs.get("hypo_root", ""),
                selected_events=selected_events,
            )
            if verbose:
                print(
                    "Catalog-only time window selected: "
                    f"window_id={window_id}, "
                    f"ot_range={ot_range}, "
                    f"selected_events={precheck.selected_events}, "
                    f"selected_picks={precheck.selected_picks}, "
                    f"plan_reason={plan_reason}, "
                    f"output_folder={window_output}",
                    flush=True,
                )
            window_kwargs = dict(kwargs)
            window_kwargs.update(
                {
                    "ot_range": ot_range,
                    "output_folder": window_output,
                    "catalog_code": catalog_code,
                }
            )
            result = run_catalog_only_relocation(
                **window_kwargs,
            )
            successful_results.append(result)
            batches.append(
                CatalogOnlyBatchEntry(
                    batch_id=window_id,
                    status="success",
                    input_events=selected_events,
                    phase_file=os.path.abspath(phase_file),
                    output_folder=window_output,
                    config_path="",
                    loc_rows=result.loc_rows,
                    reloc_rows=result.reloc_rows,
                    residual_rows=result.residual_rows,
                    ot_range=ot_range,
                    plan_reason=plan_reason,
                    merged_from=merged_from,
                    parallel_safe=parallel_safe,
                )
            )
        except Exception as exc:
            tb_text = traceback.format_exc()
            os.makedirs(window_output, exist_ok=True)
            error_path = os.path.join(window_output, "failure_traceback.txt")
            with open(error_path, "w", encoding="utf-8") as f:
                f.write(tb_text)
            batches.append(
                CatalogOnlyBatchEntry(
                    batch_id=window_id,
                    status="failed",
                    input_events=selected_events,
                    phase_file=os.path.abspath(phase_file),
                    output_folder=window_output,
                    config_path="",
                    error_path=error_path,
                    error_signature=_failure_signature(tb_text),
                    failure_kind=_classify_failure_kind(exc, tb_text),
                    ot_range=ot_range,
                    plan_reason=plan_reason,
                    merged_from=merged_from,
                    parallel_safe=parallel_safe,
                )
            )
            if not continue_on_error:
                status_csv = _write_batch_status_csv(
                    os.path.join(output_folder, "time_window_status.csv"),
                    batches,
                )
                manifest_path = os.path.join(output_folder, "time_window_manifest.json")
                partial_result = CatalogOnlyBatchResult(
                    output_folder=output_folder,
                    catalog_code=catalog_code,
                    total_input_events=total_input_events,
                    success_batches=sum(1 for b in batches if b.status == "success"),
                    failed_batches=sum(1 for b in batches if b.status == "failed"),
                    merged_loc_path="",
                    merged_reloc_path="",
                    merged_residual_path="",
                    manifest_path=os.path.abspath(manifest_path),
                    batch_status_csv=status_csv,
                    batches=batches,
                )
                manifest_extra = {"planning": planning_evidence} if planning_evidence else None
                _write_batch_manifest_with_extra(manifest_path, partial_result, extra=manifest_extra)
                failure_kind = _classify_failure_kind(exc, tb_text)
                failure_signature = _failure_signature(tb_text)
                raise NativeOutputError(
                    "Catalog-only HypoDD time-window relocation stopped at the "
                    "first failed window because continue_on_error=False. "
                    f"failed_window={window_id}; status_csv={status_csv}; "
                    f"manifest={manifest_path}; failure_kind={failure_kind}; "
                    f"error_signature={failure_signature}. "
                    f"Primary evidence: failure_traceback={error_path}. "
                    "Use that traceback as an index into the native window outputs/logs. "
                    "Do not infer the cause from the failure_kind alone, and do not "
                    "reduce events, alter phase parsing, or tune ph2dt/HypoDD parameters "
                    "unless the native evidence in this failed window supports that action."
                ) from exc

    merged_loc_path = _concat_existing_files(
        [r.loc_path for r in successful_results],
        os.path.join(output_folder, f"{catalog_code}.loc"),
    )
    merged_reloc_path = _concat_existing_files(
        [r.reloc_path for r in successful_results],
        os.path.join(output_folder, f"{catalog_code}.reloc"),
    )
    merged_residual_path = _concat_existing_files(
        [r.residual_path for r in successful_results],
        os.path.join(output_folder, f"{catalog_code}.res"),
    )
    status_csv = _write_batch_status_csv(
        os.path.join(output_folder, "time_window_status.csv"),
        batches,
    )
    manifest_path = os.path.join(output_folder, "time_window_manifest.json")
    result = CatalogOnlyBatchResult(
        output_folder=output_folder,
        catalog_code=catalog_code,
        total_input_events=total_input_events,
        success_batches=sum(1 for b in batches if b.status == "success"),
        failed_batches=sum(1 for b in batches if b.status == "failed"),
        merged_loc_path=merged_loc_path,
        merged_reloc_path=merged_reloc_path,
        merged_residual_path=merged_residual_path,
        manifest_path=os.path.abspath(manifest_path),
        batch_status_csv=status_csv,
        batches=batches,
    )
    manifest_extra = {"planning": planning_evidence} if planning_evidence else None
    _write_batch_manifest_with_extra(manifest_path, result, extra=manifest_extra)

    if result.success:
        return result
    first_error = next((b.error_signature for b in batches if b.error_signature), "")
    failure_kinds = sorted({b.failure_kind for b in batches if b.failure_kind})
    failure_kind_text = ",".join(failure_kinds) if failure_kinds else "unknown"
    if allow_partial and result.success_batches > 0:
        return result
    if result.success_batches == 0:
        raise NativeOutputError(
            "All catalog-only HypoDD time windows failed or were empty; no valid "
            f"merged relocation output was produced. status_csv={status_csv}; "
            f"manifest={manifest_path}; failure_kinds={failure_kind_text}; "
            f"first_error={first_error}. Inspect per-window failure_traceback/native "
            "logs recorded in the manifest; do not replace failed windows with "
            "placeholder or unchanged catalogs."
        )
    if failure_kinds and set(failure_kinds).issubset({"insufficient_dtimes", "empty_window"}):
        raise NativeOutputError(
            "Catalog-only HypoDD time-window relocation produced partial scientific "
            "coverage: some sparse or empty windows had no usable differential-time "
            "observations. This is usually addressed by merging sparse windows or "
            "relaxing ph2dt pairing constraints, not by changing the phase-file "
            "format. "
            f"success_windows={result.success_windows}; failed_windows={result.failed_windows}; "
            f"status_csv={status_csv}; manifest={manifest_path}; "
            f"failure_kinds={failure_kind_text}; first_error={first_error}"
        )
    raise NativeOutputError(
        "Catalog-only HypoDD time-window relocation produced only partial results. "
        f"success_windows={result.success_windows}; failed_windows={result.failed_windows}; "
        f"status_csv={status_csv}; manifest={manifest_path}; "
        f"failure_kinds={failure_kind_text}; first_error={first_error}"
    )


def run_catalog_only_auto_time_windows(
    *,
    inputs: Optional[Any] = None,
    selection: Optional[Any] = None,
    ph2dt: Optional[Any] = None,
    hypodd: Optional[Any] = None,
    runtime: Optional[Any] = None,
    overrides: Optional[Mapping[str, Any]] = None,
    time_window_base: str = "month",
    base: Optional[str] = None,
    time_window_days: Optional[int] = None,
    min_events_per_window: int = 100,
    max_events_per_window: Optional[int] = None,
    time_window_dir_name: str = "time_windows",
    window_prefix: str = "window",
    num_window_workers: int = 1,
    clean_output: bool = False,
    allow_partial: bool = False,
    continue_on_error: Optional[bool] = None,
    verbose: bool = False,
    **kwargs: Any,
) -> CatalogOnlyBatchResult:
    """Plan and run catalog-only relocation in safe time windows.

    Parameters
    ----------
    inputs, selection, ph2dt, hypodd, runtime
        Optional grouped public parameter objects matching
        ``run_catalog_only_relocation``.
    overrides
        Optional final keyword overrides after grouped objects are expanded.
    time_window_base, base, time_window_days
        Base time-window controls. ``base`` is an alias for
        ``time_window_base``.
    min_events_per_window, max_events_per_window
        Event-count controls used when planning windows.
    time_window_dir_name, window_prefix, num_window_workers
        Per-window output directory name, window ID prefix, and worker count.
    clean_output
        Remove an existing time-window output tree before running.
    allow_partial, continue_on_error
        Partial-failure policy. ``continue_on_error`` is an alias for
        ``allow_partial``.
    verbose
        Print per-window progress to stderr.
    **kwargs
        Flat catalog-only kwargs such as ``phase_file``, ``station_file``,
        ``output_folder``, ``catalog_code``, ``ot_range``, ``lat_range``, and
        ``lon_range``.

    This high-level entry point is intended for full catalogs that may exceed
    native HypoDD limits. It plans disjoint ``ot_range`` windows from the phase
    file, merges sparse neighboring windows, applies the active ``MAXEVE`` limit
    when available, and then runs each planned window with
    :func:`run_catalog_only_time_windows`.
    Start with the coarsest scientifically meaningful base, usually the default
    monthly base. Shrink to daily or fixed-day windows only when a coarser
    planned window itself exceeds the active event/data limit or native evidence
    shows the window is too dense.

    New scripts may pass the public grouped parameter objects
    (``inputs``, ``selection``, ``ph2dt``, ``hypodd``, ``runtime``), matching
    :func:`run_catalog_only_relocation`. The function expands them internally
    before planning windows. The ``base`` and ``continue_on_error`` aliases are
    accepted for consistency with the public RAG examples; they map to
    ``time_window_base`` and ``allow_partial`` respectively.
    """
    if any(group is not None for group in (inputs, selection, ph2dt, hypodd, runtime)):
        grouped_kwargs = grouped_to_catalog_only_kwargs(
            inputs=inputs,
            selection=selection,
            ph2dt=ph2dt,
            hypodd=hypodd,
            runtime=runtime,
            overrides=overrides,
        )
        grouped_kwargs.update(kwargs)
        kwargs = grouped_kwargs

    if base is not None:
        time_window_base = str(base)
    if continue_on_error is not None:
        allow_partial = bool(continue_on_error)

    phase_file = _require_path("phase_file", kwargs.get("phase_file"))
    hypo_root = _require_path("hypo_root", kwargs.get("hypo_root"))
    output_folder = os.path.abspath(_require_path("output_folder", kwargs.get("output_folder")))
    if clean_output and os.path.isdir(output_folder):
        shutil.rmtree(output_folder)
    os.makedirs(output_folder, exist_ok=True)
    if max_events_per_window is None:
        max_events_per_window = _read_active_hypodd_limits(hypo_root).get("MAXEVE")

    plans = plan_catalog_only_time_windows(
        phase_file=phase_file,
        ot_range=kwargs.get("ot_range"),
        lat_range=kwargs.get("lat_range"),
        lon_range=kwargs.get("lon_range"),
        phase_format=kwargs.get("phase_format", "auto"),
        base=time_window_base,
        window_days=time_window_days,
        min_events_per_window=min_events_per_window,
        max_events_per_window=max_events_per_window,
        window_prefix=window_prefix,
    )
    print(
        "Catalog-only auto time-window plan: "
        f"windows={len(plans)}, "
        f"min_events_per_window={int(min_events_per_window)}, "
        f"max_events_per_window={max_events_per_window}, "
        f"base={time_window_base}. "
        "Per-window details are recorded in time_window_manifest.json.",
        flush=True,
    )
    if verbose:
        for plan in plans:
            print(
                "  - "
                f"{plan.window_id}: ot_range={plan.ot_range}, "
                f"event_count={plan.event_count}, "
                f"reason={plan.reason}, "
                f"merged_from={plan.merged_from}",
                flush=True,
            )

    planning_evidence = {
        "mode": "auto_time_windows",
        "base": time_window_base,
        "window_days": time_window_days,
        "min_events_per_window": int(min_events_per_window),
        "max_events_per_window": max_events_per_window,
        "num_window_workers": int(num_window_workers),
        "clean_output": bool(clean_output),
        "phase_file": os.path.abspath(phase_file),
        "ot_range": normalize_ot_range(kwargs.get("ot_range")),
        "lat_range": _numeric_pair("lat_range", kwargs.get("lat_range"), cast=float, ordered=True),
        "lon_range": _numeric_pair("lon_range", kwargs.get("lon_range"), cast=float, ordered=True),
        "planned_windows": [plan.as_dict() for plan in plans],
    }
    return run_catalog_only_time_windows(
        time_windows=plans,
        time_window_dir_name=time_window_dir_name,
        window_prefix=window_prefix,
        num_window_workers=num_window_workers,
        allow_partial=allow_partial,
        continue_on_error=allow_partial,
        verbose=verbose,
        planning_evidence=planning_evidence,
        **kwargs,
    )
