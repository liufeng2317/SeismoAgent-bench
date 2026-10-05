"""CC-only HypoDD/FDTCC public APIs and time-window runners."""
from __future__ import annotations

import csv
import json
import os
import sys
import traceback
from dataclasses import asdict, dataclass
from typing import Any, Dict, Mapping, Optional, Sequence

from . import config as hypodd_config
from .api import default_fdtcc_flags, run_fdtcc_relocation, scaled_layered_velocity_model
from .errors import InsufficientDTimeError
from .params import (
    CCOnlyWindowParams,
    EventSelection,
    FDTCCParams,
    HypoDDInputs,
    HypoDDParams,
    Ph2dtParams,
    RuntimeOptions,
    grouped_to_fdtcc_kwargs,
)
from .time_window import TimeWindowPlan, normalize_ot_range


@dataclass
class CCOnlyWindowEntry:
    """Status record for one CC-only relocation time window.

    A window is successful only when FDTCC produced usable ``dt_*.cc`` evidence
    and HypoDD produced native relocation outputs for that window.

    Attributes
    ----------
    window_id, ot_range
        Stable identifier and normalized time range such as
        ``"20250101-20250102"``.
    status
        ``"success"``, ``"failed"``, ``"skipped_existing"`` or an in-progress
        status used while the runner is writing the manifest.
    output_folder
        Per-window native output directory containing FDTCC logs, ``dt_*.cc``,
        HypoDD logs, and catalog outputs.
    dt_cc_pair_headers, dt_cc_data_lines
        Counts from generated ``dt_*.cc`` files. Very small or zero counts mean
        waveform CC did not provide enough constraints.
    failure_kind, error_signature
        Compact failure classification and first-line error evidence.
    """

    window_id: str
    ot_range: str
    status: str
    output_folder: str
    input_events: int = 0
    dt_cc_pair_headers: int = 0
    dt_cc_data_lines: int = 0
    dtimes_total: Optional[int] = None
    events_after_dtime_match: Optional[int] = None
    clusters: Optional[int] = None
    failure_kind: str = ""
    error_signature: str = ""

    def as_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class CCOnlyWindowResult:
    """Summary for a CC-only auto/time-window relocation run.

    Attributes
    ----------
    output_folder, catalog_code
        Top-level output directory and native catalog prefix.
    status_csv, manifest_json
        Evidence files written after each window. These should be inspected
        before claiming success or changing scientific parameters.
    merged_loc_path, merged_reloc_path, merged_residual_path
        Concatenated native outputs from successful windows.
    windows
        List of :class:`CCOnlyWindowEntry` records. ``success`` is true only
        when at least one window succeeds and no windows fail.
    """

    output_folder: str
    catalog_code: str
    status_csv: str
    manifest_json: str
    merged_loc_path: str
    merged_reloc_path: str
    merged_residual_path: str
    windows: list[CCOnlyWindowEntry]

    @property
    def success_windows(self) -> int:
        return sum(1 for w in self.windows if w.status == "success")

    @property
    def failed_windows(self) -> int:
        return sum(1 for w in self.windows if w.status == "failed")

    @property
    def skipped_windows(self) -> int:
        return sum(1 for w in self.windows if w.status.startswith("skipped"))

    @property
    def success(self) -> bool:
        return self.success_windows > 0 and self.failed_windows == 0

    def as_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "output_folder": self.output_folder,
            "catalog_code": self.catalog_code,
            "status_csv": self.status_csv,
            "manifest_json": self.manifest_json,
            "merged_loc_path": self.merged_loc_path,
            "merged_reloc_path": self.merged_reloc_path,
            "merged_residual_path": self.merged_residual_path,
            "success_windows": self.success_windows,
            "failed_windows": self.failed_windows,
            "skipped_windows": self.skipped_windows,
            "windows": [w.as_dict() for w in self.windows],
        }


def default_cc_only_hypodd_iter_rows() -> tuple[tuple[float, ...], ...]:
    """Return conservative HypoDD iteration rows for CC-only relocation.

    The rows follow native HypoDD order:
    ``NITER WTCCP WTCCS WRCC WDCC WTCTP WTCTS WRCT WDCT DAMP``.
    Catalog-time weights are set to ``-9`` so the final inversion is driven by
    cross-correlation differential times. Use these as a first-pass default,
    then tune damping/cutoffs from the generated ``dt_*.cc`` and residual
    evidence.
    """
    return (
        (8, 1.0, 0.7, 0.03, 8.0, -9.0, -9.0, -9.0, -9.0, 120.0),
        (12, 1.0, 0.7, 0.02, 5.0, -9.0, -9.0, -9.0, -9.0, 80.0),
    )


def build_cc_only_relocation_kwargs(
    *,
    hypo_root: str,
    phase_file: str,
    station_file: str,
    output_folder: str,
    catalog_code: str,
    ot_range: Any,
    lat_range: Sequence[Any],
    lon_range: Sequence[Any],
    waveform_dir_raw: str,
    sac_cache_dir: str,
    max_depth_km: float = 90.0,
    vp_km_s: float = 6.2,
    vp_vs_ratio: float = 1.75,
    num_workers: int = 1,
    delete_waveform_temp: bool = False,
    rebuild_ttdb: bool = False,
    phase_format: str = "auto",
    dep_corr: float = 0.0,
    num_grids: Sequence[Any] = (1, 1),
    xy_pad: Sequence[Any] = (0.05, 0.05),
    keep_grids: bool = False,
    hypodd_iphase: int = 3,
    hypodd_maxdist: float = 180.0,
    hypodd_minobs_cc: int = 4,
    hypodd_mod_ratio: float = 1.75,
    hypodd_mod_top: Optional[Sequence[Any]] = None,
    hypodd_mod_vel: Optional[Sequence[Any]] = None,
    ph2dt_minwght: float = 0.0,
    ph2dt_maxdist: float = 180.0,
    ph2dt_maxoffset: float = 20.0,
    ph2dt_mnb: int = 12,
    ph2dt_limobs_pair: int = 8,
    ph2dt_minobs_pair: int = 6,
    ph2dt_maxobs_pair: int = 40,
    fdtcc_miniseed_filename_template: str = "{network}.{station}.{day}.{next_day}.mseed",
    fdtcc_sac_pre_sec: float = 120.0,
    fdtcc_sac_post_sec: float = 300.0,
    fdtcc_sac_export_backend: str = "process",
    fdtcc_sac_show_progress: bool = False,
    fdtcc_cleanup_input_lists: bool = True,
    fdtcc_flags: Optional[Mapping[str, Any]] = None,
    fdtcc_velocity_layer: Optional[Sequence[Any]] = None,
    fdtcc_velocity_vp: Optional[Sequence[Any]] = None,
    fdtcc_velocity_vs: Optional[Sequence[Any]] = None,
) -> Dict[str, Any]:
    """Build flat keyword arguments for CC-only relocation public APIs.

    This helper is useful when a script starts from simple path/scalar values
    instead of grouped parameter objects. It returns a dictionary accepted by
    ``run_cc_only_relocation(...)`` or by ``run_cc_only_auto_time_windows(...)``
    after adding window controls.

    Parameters
    ----------
    hypo_root
        HYPODD source/build root containing ``ph2dt/ph2dt`` and
        ``hypoDD/hypoDD``.
    phase_file, station_file
        Prepared event-block phase file and station coordinate table. Station
        ids must match waveform metadata. For FDTCC/CC, provide real network
        information through ``NET.STA``, separate network/station columns, or
        ``station_default_network`` only when that network is known and matches
        waveform files.
    output_folder, catalog_code
        Output directory and prefix for native files.
    ot_range, lat_range, lon_range
        Event selection. ``ot_range`` may be a ``YYYYMMDD-YYYYMMDD`` string or
        a two-value date/time sequence; latitude/longitude ranges are two-value
        numeric sequences.
    waveform_dir_raw, sac_cache_dir
        Raw MiniSEED root and reusable FDTCC SAC cache/output directory.
    max_depth_km, vp_km_s, vp_vs_ratio
        First-pass FDTCC travel-time table bounds and velocity scaling when
        explicit FDTCC velocity arrays are not supplied.
    fdtcc_flags
        Optional FDTCC flag mapping. If omitted, ``default_fdtcc_flags`` is
        used.
    num_workers, delete_waveform_temp, rebuild_ttdb, phase_format
        Runtime/FDTCC preparation controls for generated kwargs.
    dep_corr, num_grids, xy_pad, keep_grids
        HypoDD preprocessing grid and retention controls.
    hypodd_iphase, hypodd_maxdist, hypodd_minobs_cc, hypodd_mod_ratio,
    hypodd_mod_top, hypodd_mod_vel
        HypoDD inversion and velocity-model controls for CC-only relocation.
    ph2dt_minwght, ph2dt_maxdist, ph2dt_maxoffset, ph2dt_mnb,
    ph2dt_limobs_pair, ph2dt_minobs_pair, ph2dt_maxobs_pair
        ph2dt pairing controls used to build event pairs before FDTCC.
    fdtcc_miniseed_filename_template, fdtcc_sac_pre_sec,
    fdtcc_sac_post_sec, fdtcc_sac_export_backend,
    fdtcc_sac_show_progress, fdtcc_cleanup_input_lists
        FDTCC waveform export and native input-list controls.
    fdtcc_velocity_layer, fdtcc_velocity_vp, fdtcc_velocity_vs
        Optional explicit FDTCC velocity arrays. When omitted, the helper
        derives a scaled model from ``vp_km_s`` and ``vp_vs_ratio``.

    Returns
    -------
    dict
        Flat kwargs with CC-only settings: ``hypodd_idata=1``, catalog weights
        disabled, FDTCC input preparation enabled, and waveform/SAC settings
        populated.

    Example
    -------
    ```python
    kwargs = build_cc_only_relocation_kwargs(
        hypo_root=hypo_root,
        phase_file=phase_file,
        station_file=station_file,
        output_folder=out_dir,
        catalog_code="demo_cc",
        ot_range=("2025-01-01", "2025-01-08"),
        lat_range=(38.0, 40.0),
        lon_range=(140.0, 143.0),
        waveform_dir_raw=waveform_root,
        sac_cache_dir=f"{out_dir}/sac_cache",
    )
    result_cfg = run_cc_only_relocation(**kwargs)
    ```
    """
    if fdtcc_velocity_layer is None or fdtcc_velocity_vp is None:
        layer, vp, vs = scaled_layered_velocity_model(
            vp_km_s=vp_km_s,
            vp_vs_ratio=vp_vs_ratio,
        )
    else:
        layer = [float(v) for v in fdtcc_velocity_layer]
        vp = [float(v) for v in fdtcc_velocity_vp]
        if fdtcc_velocity_vs is None:
            vs = [round(float(v) / float(vp_vs_ratio), 3) for v in vp]
        else:
            vs = [float(v) for v in fdtcc_velocity_vs]
    if not (len(layer) == len(vp) == len(vs)):
        raise ValueError("FDTCC velocity layer, Vp, and Vs arrays must have the same length")

    return {
        "hypo_root": hypo_root,
        "phase_file": phase_file,
        "station_file": station_file,
        "output_folder": output_folder,
        "catalog_code": catalog_code,
        "ot_range": ot_range,
        "lat_range": lat_range,
        "lon_range": lon_range,
        "phase_format": phase_format,
        "dep_corr": dep_corr,
        "num_grids": tuple(num_grids),
        "xy_pad": tuple(xy_pad),
        "num_workers": int(num_workers),
        "keep_grids": bool(keep_grids),
        "hypodd_iphase": int(hypodd_iphase),
        "hypodd_maxdist": float(hypodd_maxdist),
        "hypodd_minobs_cc": int(hypodd_minobs_cc),
        "hypodd_mod_ratio": float(hypodd_mod_ratio),
        "hypodd_mod_top": tuple(hypodd_mod_top) if hypodd_mod_top is not None else tuple(layer),
        "hypodd_mod_vel": tuple(hypodd_mod_vel) if hypodd_mod_vel is not None else tuple(vp),
        "ph2dt_minwght": float(ph2dt_minwght),
        "ph2dt_maxdist": float(ph2dt_maxdist),
        "ph2dt_maxoffset": float(ph2dt_maxoffset),
        "ph2dt_mnb": int(ph2dt_mnb),
        "ph2dt_limobs_pair": int(ph2dt_limobs_pair),
        "ph2dt_minobs_pair": int(ph2dt_minobs_pair),
        "ph2dt_maxobs_pair": int(ph2dt_maxobs_pair),
        "fdtcc_velocity_layer": layer,
        "fdtcc_velocity_vp": vp,
        "fdtcc_velocity_vs": vs,
        "waveform_dir_raw": os.path.abspath(waveform_dir_raw),
        "keep_waveform_temp": not bool(delete_waveform_temp),
        "fdtcc_prepare_inputs": True,
        "fdtcc_rebuild_ttdb": bool(rebuild_ttdb),
        "fdtcc_wave_dir_mode": "miniseed",
        "fdtcc_miniseed_filename_template": fdtcc_miniseed_filename_template,
        "fdtcc_sac_pre_sec": float(fdtcc_sac_pre_sec),
        "fdtcc_sac_post_sec": float(fdtcc_sac_post_sec),
        "fdtcc_sac_export_backend": fdtcc_sac_export_backend,
        "fdtcc_sac_show_progress": bool(fdtcc_sac_show_progress),
        "fdtcc_waveform_temp_basename": os.path.abspath(sac_cache_dir),
        "fdtcc_flags": (
            dict(fdtcc_flags)
            if fdtcc_flags is not None
            else default_fdtcc_flags(max_depth_km=max_depth_km)
        ),
        "fdtcc_cleanup_input_lists": bool(fdtcc_cleanup_input_lists),
    }


def run_cc_only_relocation(
    *,
    inputs: Optional[HypoDDInputs] = None,
    selection: Optional[EventSelection] = None,
    ph2dt: Optional[Ph2dtParams] = None,
    hypodd: Optional[HypoDDParams] = None,
    fdtcc: Optional[FDTCCParams] = None,
    runtime: Optional[RuntimeOptions] = None,
    overrides: Optional[Mapping[str, Any]] = None,
    hypo_root: Optional[str] = None,
    phase_file: Optional[str] = None,
    station_file: Optional[str] = None,
    output_folder: Optional[str] = None,
    catalog_code: Optional[str] = None,
    ot_range: Any = None,
    lat_range: Optional[Sequence[Any]] = None,
    lon_range: Optional[Sequence[Any]] = None,
    fdtcc_flags: Optional[Mapping[str, Any]] = None,
    fdtcc_binary: Optional[str] = None,
    fdtcc_cleanup_input_lists: bool = True,
    fdtcc_timeout_sec: Optional[float] = None,
    phase_format: str = "auto",
    fdtcc_velocity_nd: Optional[str] = None,
    fdtcc_velocity_layer: Optional[Sequence[Any]] = None,
    fdtcc_velocity_vp: Optional[Sequence[Any]] = None,
    fdtcc_velocity_vs: Optional[Sequence[Any]] = None,
    fdtcc_velocity_vp_vs_ratio: float = 1.73,
    waveform_dir_raw: Optional[str] = None,
    fdtcc_miniseed_root: Optional[str] = None,
    fdtcc_miniseed_filename_template: Optional[str] = None,
    fdtcc_sac_pre_sec: float = 120.0,
    fdtcc_sac_post_sec: float = 300.0,
    fdtcc_sac_export_backend: str = "process",
    fdtcc_sac_show_progress: bool = False,
    fdtcc_wave_dir_mode: str = "miniseed",
    fdtcc_waveform_temp_basename: str = "waveform_temp",
    station_default_network: Optional[str] = None,
    keep_waveform_temp: bool = False,
    fdtcc_prepare_inputs: bool = True,
    fdtcc_rebuild_ttdb: bool = False,
    dep_corr: float = 0.0,
    num_grids: Sequence[Any] = (1, 1),
    xy_pad: Sequence[Any] = (0.0, 0.0),
    num_workers: int = 1,
    keep_grids: bool = False,
    hypodd_iphase: int = 3,
    hypodd_maxdist: float = 100.0,
    hypodd_minobs_cc: int = 4,
    hypodd_istart: int = 2,
    hypodd_isolv: int = 2,
    hypodd_iter_rows: Optional[Sequence[Sequence[Any]]] = None,
    hypodd_mod_ratio: float = 1.75,
    hypodd_mod_top: Optional[Sequence[Any]] = None,
    hypodd_mod_vel: Optional[Sequence[Any]] = None,
    hypodd_iclust: int = 0,
    hypodd_dt_cc_per_grid: bool = True,
    ph2dt_minwght: float = 0.0,
    ph2dt_maxdist: float = 70.0,
    ph2dt_maxoffset: float = 5.0,
    ph2dt_mnb: int = 10,
    ph2dt_limobs_pair: int = 8,
    ph2dt_minobs_pair: int = 4,
    ph2dt_maxobs_pair: int = 30,
) -> hypodd_config.Config:
    """Run FDTCC + HypoDD relocation using only CC differential times.

    Prefer grouped parameter objects in new scripts. The flat keyword interface
    is kept for existing examples and compatibility.

    Required grouped inputs
    -----------------------
    ``inputs``
        ``HypoDDInputs(hypo_root, phase_file, station_file, output_folder,
        catalog_code)``.
    ``selection``
        ``EventSelection(ot_range, lat_range, lon_range, phase_format="auto")``.
    ``fdtcc``
        ``FDTCCParams`` with waveform source/cache and velocity/flag settings.

    Key behavior
    ------------
    The function forces CC-only HypoDD mode by setting ``hypodd_idata=1`` and
    ``hypodd_minobs_ct=0``. Catalog ``dt.ct`` may still be generated during
    preparation, but it is not the success evidence for CC-only relocation.
    Success requires non-empty ``dt_*.cc`` and native HypoDD outputs.

    Flat keyword parameters
    -----------------------
    ``overrides`` applies final updates after grouped parameters. The flat API
    accepts the same path/selection/FDTCC/runtime/HypoDD/ph2dt parameters as
    ``run_fdtcc_relocation``, including ``fdtcc_flags``, ``fdtcc_binary``,
    ``fdtcc_cleanup_input_lists``, ``fdtcc_timeout_sec``, ``phase_format``,
    ``fdtcc_velocity_nd``, ``fdtcc_velocity_layer``, ``fdtcc_velocity_vp``,
    ``fdtcc_velocity_vs``, ``fdtcc_velocity_vp_vs_ratio``,
    ``waveform_dir_raw``, ``fdtcc_miniseed_root``,
    ``fdtcc_miniseed_filename_template``, ``fdtcc_sac_pre_sec``,
    ``fdtcc_sac_post_sec``, ``fdtcc_sac_export_backend``,
    ``fdtcc_sac_show_progress``, ``fdtcc_wave_dir_mode``,
    ``fdtcc_waveform_temp_basename``, ``station_default_network``,
    ``keep_waveform_temp``, ``fdtcc_prepare_inputs``, ``fdtcc_rebuild_ttdb``,
    ``dep_corr``, ``num_grids``, ``xy_pad``, ``num_workers``, ``keep_grids``,
    ``hypodd_iphase``, ``hypodd_maxdist``, ``hypodd_minobs_cc``,
    ``hypodd_istart``, ``hypodd_isolv``, ``hypodd_iter_rows``,
    ``hypodd_mod_ratio``, ``hypodd_mod_top``, ``hypodd_mod_vel``,
    ``hypodd_iclust``, ``hypodd_dt_cc_per_grid``, ``ph2dt_minwght``,
    ``ph2dt_maxdist``, ``ph2dt_maxoffset``, ``ph2dt_mnb``,
    ``ph2dt_limobs_pair``, ``ph2dt_minobs_pair``, and
    ``ph2dt_maxobs_pair``.

    Example
    -------
    ```python
    cfg = run_cc_only_relocation(
        inputs=inputs,
        selection=selection,
        ph2dt=ph2dt,
        hypodd=HypoDDParams(iter_rows=default_cc_only_hypodd_iter_rows()),
        fdtcc=fdtcc,
        runtime=runtime,
    )
    ```
    """
    if any(group is not None for group in (inputs, selection, ph2dt, hypodd, fdtcc, runtime)):
        kwargs = grouped_to_fdtcc_kwargs(
            inputs=inputs,
            selection=selection,
            ph2dt=ph2dt,
            hypodd=hypodd,
            fdtcc=fdtcc,
            runtime=runtime,
            overrides=overrides,
        )
        kwargs["hypodd_idata"] = 1
        kwargs["hypodd_minobs_ct"] = 0
        kwargs["stop_after_cc"] = False
        if kwargs.get("hypodd_iter_rows") is None:
            kwargs["hypodd_iter_rows"] = default_cc_only_hypodd_iter_rows()
        return run_fdtcc_relocation(**kwargs)

    missing = [
        name
        for name, value in {
            "hypo_root": hypo_root,
            "phase_file": phase_file,
            "station_file": station_file,
            "output_folder": output_folder,
            "catalog_code": catalog_code,
            "ot_range": ot_range,
            "lat_range": lat_range,
            "lon_range": lon_range,
        }.items()
        if value is None
    ]
    if missing:
        raise TypeError(
            "run_cc_only_relocation() missing required parameters: "
            + ", ".join(missing)
            + ". Pass grouped parameter objects or the flat keyword API."
        )

    return run_fdtcc_relocation(
        hypo_root=hypo_root,
        phase_file=phase_file,
        station_file=station_file,
        output_folder=output_folder,
        catalog_code=catalog_code,
        ot_range=ot_range,
        lat_range=lat_range,
        lon_range=lon_range,
        fdtcc_flags=fdtcc_flags,
        fdtcc_binary=fdtcc_binary,
        fdtcc_cleanup_input_lists=fdtcc_cleanup_input_lists,
        fdtcc_timeout_sec=fdtcc_timeout_sec,
        phase_format=phase_format,
        fdtcc_velocity_nd=fdtcc_velocity_nd,
        fdtcc_velocity_layer=fdtcc_velocity_layer,
        fdtcc_velocity_vp=fdtcc_velocity_vp,
        fdtcc_velocity_vs=fdtcc_velocity_vs,
        fdtcc_velocity_vp_vs_ratio=fdtcc_velocity_vp_vs_ratio,
        waveform_dir_raw=waveform_dir_raw,
        fdtcc_miniseed_root=fdtcc_miniseed_root,
        fdtcc_miniseed_filename_template=fdtcc_miniseed_filename_template,
        fdtcc_sac_pre_sec=fdtcc_sac_pre_sec,
        fdtcc_sac_post_sec=fdtcc_sac_post_sec,
        fdtcc_sac_export_backend=fdtcc_sac_export_backend,
        fdtcc_sac_show_progress=fdtcc_sac_show_progress,
        fdtcc_wave_dir_mode=fdtcc_wave_dir_mode,
        fdtcc_waveform_temp_basename=fdtcc_waveform_temp_basename,
        station_default_network=station_default_network,
        keep_waveform_temp=keep_waveform_temp,
        fdtcc_prepare_inputs=fdtcc_prepare_inputs,
        fdtcc_rebuild_ttdb=fdtcc_rebuild_ttdb,
        stop_after_cc=False,
        dep_corr=dep_corr,
        num_grids=num_grids,
        xy_pad=xy_pad,
        num_workers=num_workers,
        keep_grids=keep_grids,
        hypodd_idata=1,
        hypodd_iphase=hypodd_iphase,
        hypodd_maxdist=hypodd_maxdist,
        hypodd_minobs_cc=hypodd_minobs_cc,
        hypodd_minobs_ct=0,
        hypodd_istart=hypodd_istart,
        hypodd_isolv=hypodd_isolv,
        hypodd_iter_rows=(
            hypodd_iter_rows
            if hypodd_iter_rows is not None
            else default_cc_only_hypodd_iter_rows()
        ),
        hypodd_mod_ratio=hypodd_mod_ratio,
        hypodd_mod_top=hypodd_mod_top,
        hypodd_mod_vel=hypodd_mod_vel,
        hypodd_iclust=hypodd_iclust,
        hypodd_dt_cc_per_grid=hypodd_dt_cc_per_grid,
        ph2dt_minwght=ph2dt_minwght,
        ph2dt_maxdist=ph2dt_maxdist,
        ph2dt_maxoffset=ph2dt_maxoffset,
        ph2dt_mnb=ph2dt_mnb,
        ph2dt_limobs_pair=ph2dt_limobs_pair,
        ph2dt_minobs_pair=ph2dt_minobs_pair,
        ph2dt_maxobs_pair=ph2dt_maxobs_pair,
    )


def plan_cc_only_time_windows(
    *,
    phase_file: str,
    ot_range: Any,
    lat_range: Sequence[Any],
    lon_range: Sequence[Any],
    phase_format: str = "auto",
    base: str = "day",
    window_days: Optional[int] = None,
    min_events_per_window: int = 300,
    max_events_per_window: Optional[int] = None,
    window_prefix: str = "ccwin",
) -> list[TimeWindowPlan]:
    """Plan CC-only relocation windows from a HypoDD-ready phase file.

    Parameters
    ----------
    phase_file
        Event-block phase file containing event headers and pick rows.
    ot_range, lat_range, lon_range
        Selection applied before planning. Only selected event origin times are
        counted.
    phase_format
        ``"auto"`` for normal use; can be set to a known package-supported
        phase format for debugging.
    base, window_days
        Calendar split. ``base="day"`` or ``"month"`` are common; set
        ``window_days`` for fixed day-length windows.
    min_events_per_window, max_events_per_window
        Sparse windows are merged when possible; windows are not allowed to
        exceed ``max_events_per_window``.
    window_prefix
        Prefix for generated ``TimeWindowPlan.window_id`` values.

    Returns
    -------
    list[TimeWindowPlan]
        Planned windows with normalized ``ot_range``, event counts, merge
        reasons, and stable ids.
    """
    from .catalog_only import _numeric_pair, _require_path, _selected_hypodd_event_times
    from .phase_convert import prepare_phase_file
    from .time_window import plan_time_windows

    phase_path = os.path.abspath(_require_path("phase_file", phase_file))
    normalized_ot_range = normalize_ot_range(ot_range)
    normalized_lat_range = _numeric_pair("lat_range", lat_range, cast=float, ordered=True)
    normalized_lon_range = _numeric_pair("lon_range", lon_range, cast=float, ordered=True)
    phase_result = prepare_phase_file(phase_path, phase_format)
    event_times = _selected_hypodd_event_times(
        phase_result.effective_path,
        ot_range=normalized_ot_range,
        lat_range=normalized_lat_range,
        lon_range=normalized_lon_range,
    )
    if not event_times:
        raise ValueError("No events remain for CC-only time-window planning.")
    return plan_time_windows(
        event_times,
        base=base,
        window_days=window_days,
        min_events_per_window=min_events_per_window,
        max_events_per_window=max_events_per_window,
        start=normalized_ot_range.split("-")[0],
        end=normalized_ot_range.split("-")[1],
        window_prefix=window_prefix,
    )


def _count_dt_cc(path: str) -> tuple[int, int]:
    headers = 0
    data_lines = 0
    if not os.path.isfile(path):
        return headers, data_lines
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        for line in f:
            text = line.strip()
            if not text:
                continue
            if text.startswith("#"):
                headers += 1
            else:
                data_lines += 1
    return headers, data_lines


def _parse_int_after_equals(line: str) -> Optional[int]:
    if "=" not in line:
        return None
    tail = line.rsplit("=", 1)[-1].strip().split()
    if not tail:
        return None
    try:
        return int(tail[0])
    except Exception:
        return None


def _summarize_cc_window_outputs(output_folder: str) -> Dict[str, Any]:
    summary: Dict[str, Any] = {
        "dt_cc_pair_headers": 0,
        "dt_cc_data_lines": 0,
        "dtimes_total": None,
        "events_after_dtime_match": None,
        "clusters": None,
    }
    for name in os.listdir(output_folder) if os.path.isdir(output_folder) else []:
        if name.startswith("dt_") and name.endswith(".cc"):
            h, d = _count_dt_cc(os.path.join(output_folder, name))
            summary["dt_cc_pair_headers"] += h
            summary["dt_cc_data_lines"] += d
    log_path = os.path.join(output_folder, "0-0.hypoDD")
    if os.path.isfile(log_path):
        with open(log_path, "r", encoding="utf-8", errors="replace") as f:
            for line in f:
                if "# dtimes total" in line:
                    summary["dtimes_total"] = _parse_int_after_equals(line)
                elif "# events after dtime match" in line:
                    summary["events_after_dtime_match"] = _parse_int_after_equals(line)
                elif "# clusters" in line:
                    summary["clusters"] = _parse_int_after_equals(line)
    return summary


def _concat_existing_text_files(paths: Sequence[str], out_path: str) -> str:
    """Concatenate existing non-empty text files into ``out_path``."""
    out_path = os.path.abspath(out_path)
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as fout:
        for path in paths:
            if not path or not os.path.isfile(path) or os.path.getsize(path) == 0:
                continue
            with open(path, "r", encoding="utf-8", errors="replace") as fin:
                for line in fin:
                    fout.write(line)
    return out_path


def _merge_cc_window_native_outputs(result: CCOnlyWindowResult) -> None:
    """Merge successful CC-only window native outputs into top-level files."""
    success_outputs = [
        w.output_folder
        for w in result.windows
        if w.status in {"success", "skipped_existing"}
    ]
    prefix = result.catalog_code
    result.merged_loc_path = _concat_existing_text_files(
        [os.path.join(out, f"{prefix}.loc") for out in success_outputs],
        os.path.join(result.output_folder, f"{prefix}.loc"),
    )
    result.merged_reloc_path = _concat_existing_text_files(
        [os.path.join(out, f"{prefix}.reloc") for out in success_outputs],
        os.path.join(result.output_folder, f"{prefix}.reloc"),
    )
    result.merged_residual_path = _concat_existing_text_files(
        [os.path.join(out, f"{prefix}.res") for out in success_outputs],
        os.path.join(result.output_folder, f"{prefix}.res"),
    )


def _write_cc_window_result(result: CCOnlyWindowResult) -> None:
    os.makedirs(result.output_folder, exist_ok=True)
    _merge_cc_window_native_outputs(result)
    rows = [w.as_dict() for w in result.windows]
    fieldnames = list(CCOnlyWindowEntry("", "", "", "").as_dict().keys())
    with open(result.status_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)
    with open(result.manifest_json, "w", encoding="utf-8") as f:
        json.dump(result.as_dict(), f, indent=2)


def run_cc_only_time_windows(
    *,
    time_windows: Sequence[Any],
    output_folder: str,
    catalog_code: str,
    continue_on_error: bool = True,
    skip_existing: bool = False,
    time_window_dir_name: str = "windows",
    shared_sac_cache_dir: Optional[str] = None,
    verbose: bool = False,
    **run_kwargs: Any,
) -> CCOnlyWindowResult:
    """Run CC-only relocation in caller-provided independent time windows.

    Parameters
    ----------
    time_windows
        Sequence of ``TimeWindowPlan`` objects or time-range values accepted by
        ``normalize_ot_range``.
    output_folder, catalog_code
        Top-level output directory and native catalog prefix. Per-window native
        files are written under ``time_window_dir_name``.
    continue_on_error
        If false, raise after the first failed window once
        ``cc_window_status.csv`` and ``cc_window_manifest.json`` are written.
    skip_existing
        Reuse a window when its ``{catalog_code}.reloc`` already exists and is
        non-empty. This does not verify that old inputs, FDTCC flags, velocity
        settings, or iteration rows match the current run.
    shared_sac_cache_dir
        Reusable SAC cache passed to each FDTCC run. Defaults to
        ``<output_folder>/sac_cache``.
    time_window_dir_name
        Subdirectory under ``output_folder`` where per-window runs are written.
    verbose
        Print per-window progress to stderr.
    **run_kwargs
        Flat kwargs accepted by ``run_cc_only_relocation``.

    Returns
    -------
    CCOnlyWindowResult
        Manifest/status paths, merged output paths, and per-window evidence.
    """
    out_root = os.path.abspath(output_folder)
    os.makedirs(out_root, exist_ok=True)
    window_root = os.path.join(out_root, time_window_dir_name)
    os.makedirs(window_root, exist_ok=True)
    sac_cache = os.path.abspath(shared_sac_cache_dir or os.path.join(out_root, "sac_cache"))
    status_csv = os.path.join(out_root, "cc_window_status.csv")
    manifest_json = os.path.join(out_root, "cc_window_manifest.json")
    result = CCOnlyWindowResult(
        output_folder=out_root,
        catalog_code=catalog_code,
        status_csv=status_csv,
        manifest_json=manifest_json,
        merged_loc_path=os.path.join(out_root, f"{catalog_code}.loc"),
        merged_reloc_path=os.path.join(out_root, f"{catalog_code}.reloc"),
        merged_residual_path=os.path.join(out_root, f"{catalog_code}.res"),
        windows=[],
    )

    for index, raw_window in enumerate(time_windows, start=1):
        if isinstance(raw_window, TimeWindowPlan):
            window_id = raw_window.window_id
            ot_range = raw_window.ot_range
            input_events = raw_window.event_count
        else:
            ot_range = normalize_ot_range(raw_window)
            window_id = f"ccwin_{index:03d}_{ot_range.replace('-', '_')}"
            input_events = 0
        window_output = os.path.join(window_root, window_id)
        entry = CCOnlyWindowEntry(
            window_id=window_id,
            ot_range=ot_range,
            status="started",
            output_folder=window_output,
            input_events=int(input_events),
        )
        result.windows.append(entry)

        reloc_path = os.path.join(window_output, f"{catalog_code}.reloc")
        if skip_existing and os.path.isfile(reloc_path) and os.path.getsize(reloc_path) > 0:
            entry.status = "skipped_existing"
            entry.__dict__.update(_summarize_cc_window_outputs(window_output))
            _write_cc_window_result(result)
            continue

        kwargs = dict(run_kwargs)
        kwargs.update(
            {
                "output_folder": window_output,
                "catalog_code": catalog_code,
                "ot_range": ot_range,
                "fdtcc_waveform_temp_basename": kwargs.get(
                    "fdtcc_waveform_temp_basename", sac_cache
                ),
                "keep_waveform_temp": kwargs.get("keep_waveform_temp", True),
            }
        )
        if verbose:
            print(
                f"hypodd_runner: CC-only window {window_id}: "
                f"ot_range={ot_range}, expected_events={input_events}, output={window_output}",
                file=sys.stderr,
            )
        try:
            run_cc_only_relocation(**kwargs)
            entry.status = "success"
        except Exception as exc:
            entry.status = "failed"
            entry.failure_kind = (
                "insufficient_cc_connectivity"
                if isinstance(exc, InsufficientDTimeError)
                else exc.__class__.__name__
            )
            entry.error_signature = str(exc).splitlines()[0][:500]
            error_path = os.path.join(window_output, "failure_traceback.txt")
            os.makedirs(window_output, exist_ok=True)
            with open(error_path, "w", encoding="utf-8") as f:
                f.write(traceback.format_exc())
            if not continue_on_error:
                entry.__dict__.update(_summarize_cc_window_outputs(window_output))
                _write_cc_window_result(result)
                raise
        finally:
            entry.__dict__.update(_summarize_cc_window_outputs(window_output))
            _write_cc_window_result(result)

    return result


def run_cc_only_auto_time_windows(
    *,
    inputs: Optional[HypoDDInputs] = None,
    selection: Optional[EventSelection] = None,
    ph2dt: Optional[Ph2dtParams] = None,
    hypodd: Optional[HypoDDParams] = None,
    fdtcc: Optional[FDTCCParams] = None,
    runtime: Optional[RuntimeOptions] = None,
    windows: Optional[CCOnlyWindowParams] = None,
    overrides: Optional[Mapping[str, Any]] = None,
    phase_file: Optional[str] = None,
    ot_range: Any = None,
    lat_range: Optional[Sequence[Any]] = None,
    lon_range: Optional[Sequence[Any]] = None,
    output_folder: Optional[str] = None,
    catalog_code: Optional[str] = None,
    phase_format: str = "auto",
    base: str = "day",
    window_days: Optional[int] = None,
    min_events_per_window: int = 300,
    max_events_per_window: Optional[int] = None,
    window_prefix: str = "ccwin",
    continue_on_error: bool = True,
    skip_existing: bool = False,
    verbose: bool = False,
    **run_kwargs: Any,
) -> CCOnlyWindowResult:
    """Plan and run CC-only relocation using automatic time/event windows.

    Parameters
    ----------
    inputs, selection, ph2dt, hypodd, fdtcc, runtime, windows
        Optional grouped public parameter objects. ``windows`` supplies
        automatic planning controls.
    overrides
        Optional final keyword overrides after grouped objects are expanded.
    phase_file, ot_range, lat_range, lon_range, output_folder, catalog_code
        Required flat planning/run inputs when grouped objects are not used.
    phase_format
        ``"auto"``, ``"hypodd"``, or ``"pal"``.
    base, window_days, min_events_per_window, max_events_per_window,
    window_prefix
        Automatic time-window planning controls.
    continue_on_error, skip_existing, verbose
        Per-window failure/reuse/progress controls.
    **run_kwargs
        Additional flat kwargs passed to each ``run_cc_only_relocation`` call.

    New scripts should prefer grouped parameter objects plus
    ``CCOnlyWindowParams``:

    ```python
    result = run_cc_only_auto_time_windows(
        inputs=inputs,
        selection=selection,
        ph2dt=ph2dt,
        hypodd=hypodd,
        fdtcc=fdtcc,
        runtime=runtime,
        windows=CCOnlyWindowParams(
            base="day",
            min_events_per_window=300,
            max_events_per_window=1000,
            continue_on_error=False,
        ),
    )
    ```

    The function first plans windows from ``phase_file`` and the selected
    time/space bounds, then calls ``run_cc_only_relocation`` for each window.
    Per-window status and failure evidence are written to
    ``cc_window_status.csv`` and ``cc_window_manifest.json``.
    """
    if any(group is not None for group in (inputs, selection, ph2dt, hypodd, fdtcc, runtime)):
        grouped_kwargs = grouped_to_fdtcc_kwargs(
            inputs=inputs,
            selection=selection,
            ph2dt=ph2dt,
            hypodd=hypodd,
            fdtcc=fdtcc,
            runtime=runtime,
            overrides=overrides,
        )
        if windows is not None:
            grouped_kwargs.update(windows.to_kwargs())
        # The auto-window runner calls run_cc_only_relocation for each window.
        # These keys are enforced by that function and are not part of its flat
        # compatibility signature.
        grouped_kwargs.pop("hypodd_idata", None)
        grouped_kwargs.pop("hypodd_minobs_ct", None)
        grouped_kwargs.pop("stop_after_cc", None)
        grouped_kwargs.update(run_kwargs)
        return run_cc_only_auto_time_windows(**grouped_kwargs)

    missing = [
        name
        for name, value in {
            "phase_file": phase_file,
            "ot_range": ot_range,
            "lat_range": lat_range,
            "lon_range": lon_range,
            "output_folder": output_folder,
            "catalog_code": catalog_code,
        }.items()
        if value is None
    ]
    if missing:
        raise TypeError(
            "run_cc_only_auto_time_windows() missing required parameters: "
            + ", ".join(missing)
            + ". Pass grouped parameter objects or the flat keyword API."
        )

    plans = plan_cc_only_time_windows(
        phase_file=phase_file,
        ot_range=ot_range,
        lat_range=lat_range,
        lon_range=lon_range,
        phase_format=phase_format,
        base=base,
        window_days=window_days,
        min_events_per_window=min_events_per_window,
        max_events_per_window=max_events_per_window,
        window_prefix=window_prefix,
    )
    print(
        "hypodd_runner: CC-only auto-window plan: "
        f"windows={len(plans)}, min_events={min_events_per_window}, "
        f"max_events={max_events_per_window}, base={base}. "
        "Per-window details are recorded in cc_window_manifest.json.",
        file=sys.stderr,
    )
    if verbose:
        for plan in plans:
            print(
                f"  {plan.window_id}: ot_range={plan.ot_range}, "
                f"events={plan.event_count}, reason={plan.reason}",
                file=sys.stderr,
            )
    return run_cc_only_time_windows(
        time_windows=plans,
        output_folder=output_folder,
        catalog_code=catalog_code,
        continue_on_error=continue_on_error,
        skip_existing=skip_existing,
        verbose=verbose,
        phase_file=phase_file,
        lat_range=lat_range,
        lon_range=lon_range,
        phase_format=phase_format,
        **run_kwargs,
    )


run_fdtcc_cc_only_relocation = run_cc_only_relocation


__all__ = [
    "CCOnlyWindowEntry",
    "CCOnlyWindowParams",
    "CCOnlyWindowResult",
    "build_cc_only_relocation_kwargs",
    "default_cc_only_hypodd_iter_rows",
    "plan_cc_only_time_windows",
    "run_cc_only_auto_time_windows",
    "run_cc_only_relocation",
    "run_cc_only_time_windows",
    "run_fdtcc_cc_only_relocation",
]
