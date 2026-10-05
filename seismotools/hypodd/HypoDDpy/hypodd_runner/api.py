"""Function-parameter API for the HypoDD/FDTCC relocation pipeline.

Generated task scripts should import from the top-level ``hypodd_runner`` package
and call functions directly. For new scripts, prefer grouped parameter classes
such as ``HypoDDInputs``, ``EventSelection``, ``Ph2dtParams``, ``HypoDDParams``,
``FDTCCParams``, and ``RuntimeOptions`` so scientific settings are not mixed
with file paths and execution controls. For catalog-only relocation, use
``hypodd_runner.run_catalog_only_relocation``. For waveform cross-correlation
relocation, use ``hypodd_runner.run_fdtcc_relocation``.
For relocation that should use only waveform cross-correlation differential
times, use ``hypodd_runner.run_cc_only_relocation``.

Real runs must provide task-specific config values for ``hypo_root``, ``fsta``,
``fpha``, ``output_folder``, ``ctlg_code``, ``ot_range``, ``lat_range``, and
``lon_range``. Demo defaults are not valid task parameters. A successful run
should leave real ph2dt/HypoDD evidence in the output directory, such as
``ph2dt.log``, ``hypoDD.log``, ``*.loc``, ``*.reloc``, ``*.pha``, and ``*.res``;
empty files, diagnostics, or skipped execution are not relocation success.
"""
from __future__ import annotations

import os
import sys
from typing import Any, Dict, Mapping, Optional, Sequence

from . import config as hypodd_config
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
from .time_window import normalize_ot_range


_FLAT_FDTCC_PARAMETER_NAMES = {
    "hypo_root",
    "phase_file",
    "station_file",
    "output_folder",
    "catalog_code",
    "ot_range",
    "lat_range",
    "lon_range",
    "fdtcc_flags",
    "fdtcc_binary",
    "fdtcc_timeout_sec",
    "fdtcc_velocity_nd",
    "fdtcc_velocity_layer",
    "fdtcc_velocity_vp",
    "fdtcc_velocity_vs",
    "waveform_dir_raw",
    "fdtcc_miniseed_root",
    "fdtcc_miniseed_filename_template",
    "station_default_network",
    "hypodd_iter_rows",
    "hypodd_mod_top",
    "hypodd_mod_vel",
}


def default_fdtcc_flags(max_depth_km: float = 90.0) -> Dict[str, float | int]:
    """Return a conservative FDTCC flag template for function-style CC runs.

    Parameters
    ----------
    max_depth_km
        Maximum event depth used when FDTCC builds/searches its travel-time
        table. This is a bound for CC preparation, not a HypoDD relocation
        depth constraint.

    The returned mapping is a starting point, not a universal scientific
    optimum. Callers should adjust window lengths, thresholds, and search ranges
    for their waveform sampling rate, region, and event spacing.
    """
    return {
        "p_window_before_sec": 0.3,
        "p_window_after_sec": 1.5,
        "p_max_shift_sec": 0.5,
        "s_window_before_sec": 0.5,
        "s_window_after_sec": 2.0,
        "s_max_shift_sec": 0.7,
        "sample_interval_sec": 0.01,
        "cc_threshold": 0.7,
        "snr_threshold": 0.2,
        "max_abs_pick_diff_sec": 2.0,
        "max_distance_deg": 1.5,
        "max_depth_km": float(max_depth_km),
        "distance_step_deg": 0.02,
        "depth_step_km": 2.0,
        "bandpass_low_hz": 2.0,
        "bandpass_high_hz": 15.0,
        "input_format": 0,
        "pass_event_sel_path": 1,
        "pass_dt_ct_path": 1,
        "pass_phase_dat_path": 1,
    }


def scaled_layered_velocity_model(
    *,
    vp_km_s: float = 6.2,
    vp_vs_ratio: float = 1.75,
    reference_vp_km_s: float = 6.2,
    layer_tops_km: Optional[Sequence[Any]] = None,
    reference_vp_layers_km_s: Optional[Sequence[Any]] = None,
) -> tuple[list[float], list[float], list[float]]:
    """Return ``(layer_tops, vp, vs)`` arrays for direct FDTCC parameters.

    Parameters
    ----------
    vp_km_s
        Target representative Vp used to scale the reference Vp layers.
    vp_vs_ratio
        Vp/Vs ratio used to derive Vs from the scaled Vp layers.
    reference_vp_km_s
        Representative Vp for the reference model before scaling.
    layer_tops_km, reference_vp_layers_km_s
        Optional paired arrays. They must have the same length; if omitted, a
        conservative layered default is used.

    This helper avoids requiring a separate velocity JSON file for common
    function-style examples. ``vp_km_s`` scales the reference Vp layers; Vs is
    derived from ``vp_vs_ratio``.
    """
    layer_tops = (
        list(layer_tops_km)
        if layer_tops_km is not None
        else [0.0, 5.0, 10.0, 20.0, 35.0, 50.0, 80.0]
    )
    reference_vp = (
        list(reference_vp_layers_km_s)
        if reference_vp_layers_km_s is not None
        else [5.4, 5.8, 6.2, 6.6, 7.2, 7.6, 8.0]
    )
    if len(layer_tops) != len(reference_vp):
        raise ValueError("layer_tops_km and reference_vp_layers_km_s must have the same length")
    if float(reference_vp_km_s) <= 0:
        raise ValueError("reference_vp_km_s must be positive")
    if float(vp_vs_ratio) <= 0:
        raise ValueError("vp_vs_ratio must be positive")
    scale = float(vp_km_s) / float(reference_vp_km_s)
    vp = [round(float(v) * scale, 3) for v in reference_vp]
    vs = [round(float(v) / float(vp_vs_ratio), 3) for v in vp]
    return [float(v) for v in layer_tops], vp, vs


def run_config(
    cfg: hypodd_config.Config,
    *,
    phase_format: Optional[str] = None,
) -> hypodd_config.Config:
    """Run relocation from an existing internal :class:`Config` object.

    This is a compatibility/debugging entry point. New task scripts should
    usually call ``run_catalog_only_relocation(...)``,
    ``run_fdtcc_relocation(...)`` or ``run_cc_only_relocation(...)`` with
    grouped parameter objects instead of constructing ``Config`` directly.

    Parameters
    ----------
    cfg
        Fully populated ``hypodd_runner.config.Config`` instance. It must
        already contain real paths for ``hypo_root``, phase/station inputs,
        output folder, catalog code, time/space bounds, native parameters, and
        any FDTCC waveform settings.
    phase_format
        Optional override for ``cfg.phase_format``. Use ``"auto"`` for most
        agent-generated runs unless the input format is known exactly.

    Returns
    -------
    Config
        The same config object after native ph2dt/HypoDD/FDTCC execution.

    Example
    -------
    ```python
    cfg = Config({...})  # internal/debug use only
    run_config(cfg, phase_format="auto")
    ```
    """
    from .run_hypoDD import run_hypodd_pipeline

    if phase_format is not None:
        cfg.phase_format = str(phase_format).strip().lower()
    run_hypodd_pipeline(cfg)
    return cfg


def run_fdtcc_relocation(
    *,
    inputs: Optional[HypoDDInputs] = None,
    selection: Optional[EventSelection] = None,
    ph2dt: Optional[Ph2dtParams] = None,
    hypodd: Optional[HypoDDParams] = None,
    fdtcc: Optional[FDTCCParams] = None,
    runtime: Optional[RuntimeOptions] = None,
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
    stop_after_cc: bool = False,
    dep_corr: float = 0.0,
    num_grids: Sequence[Any] = (1, 1),
    xy_pad: Sequence[Any] = (0.0, 0.0),
    num_workers: int = 1,
    keep_grids: bool = True,
    hypodd_idata: int = 2,
    hypodd_iphase: int = 3,
    hypodd_maxdist: float = 100.0,
    hypodd_minobs_cc: int = 0,
    hypodd_minobs_ct: int = 0,
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
    """Run the full HypoDD + FDTCC workflow from explicit function parameters.

    This is the preferred public entry point for FDTCC waveform cross-correlation
    relocation. It keeps task scripts parameter-driven instead of requiring them
    to build a JSON-shaped dictionary.

    Parameters
    ----------
    hypo_root
        Path containing the local HYPODD ``ph2dt`` and ``hypoDD`` binaries.
    phase_file, station_file
        Input phase and station files for this task.
    output_folder, catalog_code
        Native run output directory and output prefix.
    fdtcc_flags
        Optional mapping of FDTCC runtime flags, using readable names such as
        ``p_window_before_sec``, ``cc_threshold``, ``max_distance_deg``, and
        ``depth_step_km``.
    ot_range, lat_range, lon_range
        Event selection windows for ``mk_pha``.
    fdtcc_velocity_nd, fdtcc_velocity_layer, fdtcc_velocity_vp,
    fdtcc_velocity_vs, fdtcc_velocity_vp_vs_ratio, waveform_dir_raw,
    fdtcc_miniseed_root
        FDTCC input-preparation controls. ``waveform_dir_raw`` may point to a
        raw MiniSEED store or a prebuilt FDTCC SAC tree; with a velocity model
        the package prepares REAL station/ttdb inputs automatically. Direct
        velocity parameters avoid writing a separate velocity JSON: provide
        ``fdtcc_velocity_layer`` and ``fdtcc_velocity_vp`` arrays; optionally
        provide ``fdtcc_velocity_vs`` or derive Vs from
        ``fdtcc_velocity_vp_vs_ratio``.
    station_default_network
        Optional network code used only when station files contain bare station
        IDs and FDTCC REAL ``station.dat`` must be generated. For CC/FDTCC runs,
        network information must be explicit before native execution: prefer
        real ``NET.STA`` IDs or separate ``network``/``station`` columns. Use this
        parameter only when the supplied network code matches the waveform
        file/inventory convention; otherwise FDTCC may build valid-looking inputs
        but find no matching waveforms.
    stop_after_cc
        If true, stop after ph2dt + FDTCC produce ``dt_*.cc`` files and do not
        run the HypoDD relocation inversion. This is useful when the task only
        needs waveform cross-correlation differential-time products.
    inputs, selection, ph2dt, hypodd, fdtcc, runtime
        Optional grouped public parameter objects. Use either these groups or
        the flat keyword API in one call, not both.
    fdtcc_binary, fdtcc_cleanup_input_lists, fdtcc_timeout_sec
        Native FDTCC executable override, input-list cleanup policy, and
        optional timeout in seconds.
    phase_format
        ``"auto"``, ``"hypodd"``, or ``"pal"`` phase input interpretation.
    fdtcc_miniseed_filename_template, fdtcc_sac_pre_sec, fdtcc_sac_post_sec,
    fdtcc_sac_export_backend, fdtcc_sac_show_progress
        Waveform-to-SAC export controls used during FDTCC input preparation.
    fdtcc_wave_dir_mode, fdtcc_waveform_temp_basename, keep_waveform_temp,
    fdtcc_prepare_inputs, fdtcc_rebuild_ttdb
        FDTCC waveform/cache/input-preparation controls.
    dep_corr, num_grids, xy_pad, num_workers, keep_grids
        Event-depth correction, spatial grid split/padding, worker count, and
        per-grid intermediate retention controls.
    hypodd_idata, hypodd_iphase, hypodd_maxdist, hypodd_minobs_cc,
    hypodd_minobs_ct, hypodd_istart, hypodd_isolv, hypodd_iter_rows,
    hypodd_mod_ratio, hypodd_mod_top, hypodd_mod_vel, hypodd_iclust,
    hypodd_dt_cc_per_grid
        Native HypoDD inversion, weighting, velocity-model, and CC-file routing
        controls.
    ph2dt_minwght, ph2dt_maxdist, ph2dt_maxoffset, ph2dt_mnb,
    ph2dt_limobs_pair, ph2dt_minobs_pair, ph2dt_maxobs_pair
        Native ph2dt catalog differential-time pairing controls.

    Returns
    -------
    config.Config
        Effective configuration after the run.
    """
    if any(group is not None for group in (inputs, selection, ph2dt, hypodd, fdtcc, runtime)):
        flat_values = {
            "hypo_root": hypo_root,
            "phase_file": phase_file,
            "station_file": station_file,
            "output_folder": output_folder,
            "catalog_code": catalog_code,
            "ot_range": ot_range,
            "lat_range": lat_range,
            "lon_range": lon_range,
            "fdtcc_flags": fdtcc_flags,
            "fdtcc_binary": fdtcc_binary,
            "fdtcc_timeout_sec": fdtcc_timeout_sec,
            "fdtcc_velocity_nd": fdtcc_velocity_nd,
            "fdtcc_velocity_layer": fdtcc_velocity_layer,
            "fdtcc_velocity_vp": fdtcc_velocity_vp,
            "fdtcc_velocity_vs": fdtcc_velocity_vs,
            "waveform_dir_raw": waveform_dir_raw,
            "fdtcc_miniseed_root": fdtcc_miniseed_root,
            "fdtcc_miniseed_filename_template": fdtcc_miniseed_filename_template,
            "station_default_network": station_default_network,
            "hypodd_iter_rows": hypodd_iter_rows,
            "hypodd_mod_top": hypodd_mod_top,
            "hypodd_mod_vel": hypodd_mod_vel,
        }
        mixed = [name for name in _FLAT_FDTCC_PARAMETER_NAMES if flat_values[name] is not None]
        if mixed:
            raise TypeError(
                "run_fdtcc_relocation() received grouped parameter objects and "
                f"flat parameters ({', '.join(sorted(mixed))}). Use one style per "
                "call so parameters are not silently ignored."
            )
        grouped_kwargs = grouped_to_fdtcc_kwargs(
            inputs=inputs,
            selection=selection,
            ph2dt=ph2dt,
            hypodd=hypodd,
            fdtcc=fdtcc,
            runtime=runtime,
        )
        return run_fdtcc_relocation(**grouped_kwargs)

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
            "run_fdtcc_relocation() missing required flat parameters: "
            + ", ".join(missing)
            + ". Pass either grouped parameter objects or the flat keyword API."
        )

    if station_default_network is not None and str(station_default_network).strip():
        print(
            "hypodd_runner: FDTCC station_default_network="
            f"{str(station_default_network).strip()!r}; ensure it matches the "
            "waveform file/inventory network convention.",
            file=sys.stderr,
            flush=True,
        )
    params = {
        "hypo_root": os.path.abspath(str(hypo_root)),
        "ctlg_code": str(catalog_code).strip(),
        "output_folder": os.path.abspath(str(output_folder)),
        "fsta": os.path.abspath(str(station_file)),
        "fpha": os.path.abspath(str(phase_file)),
        "phase_format": str(phase_format).strip().lower(),
        "dep_corr": float(dep_corr),
        "ot_range": normalize_ot_range(ot_range),
        "lat_range": list(lat_range),
        "lon_range": list(lon_range),
        "num_grids": list(num_grids),
        "xy_pad": list(xy_pad),
        "ph2dt_inp_mode": "programmatic",
        "ph2dt_minwght": float(ph2dt_minwght),
        "ph2dt_maxdist": float(ph2dt_maxdist),
        "ph2dt_maxoffset": float(ph2dt_maxoffset),
        "ph2dt_mnb": int(ph2dt_mnb),
        "ph2dt_limobs_pair": int(ph2dt_limobs_pair),
        "ph2dt_minobs_pair": int(ph2dt_minobs_pair),
        "ph2dt_maxobs_pair": int(ph2dt_maxobs_pair),
        "hypodd_inp_mode": "programmatic",
        "hypodd_idata": int(hypodd_idata),
        "hypodd_iphase": int(hypodd_iphase),
        "hypodd_maxdist": float(hypodd_maxdist),
        "hypodd_minobs_cc": int(hypodd_minobs_cc),
        "hypodd_minobs_ct": int(hypodd_minobs_ct),
        "hypodd_istart": int(hypodd_istart),
        "hypodd_isolv": int(hypodd_isolv),
        "hypodd_iter_rows": hypodd_iter_rows,
        "hypodd_mod_ratio": float(hypodd_mod_ratio),
        "hypodd_mod_top": hypodd_mod_top,
        "hypodd_mod_vel": hypodd_mod_vel,
        "hypodd_iclust": int(hypodd_iclust),
        "hypodd_dt_cc_per_grid": bool(hypodd_dt_cc_per_grid),
        "cc_engine": "fdtcc",
        "fdtcc_flags": dict(fdtcc_flags) if fdtcc_flags is not None else {},
        "fdtcc_binary": os.path.abspath(fdtcc_binary) if fdtcc_binary else None,
        "fdtcc_cleanup_input_lists": bool(fdtcc_cleanup_input_lists),
        "fdtcc_timeout_sec": (
            float(fdtcc_timeout_sec) if fdtcc_timeout_sec is not None else None
        ),
        "fdtcc_velocity_nd": (
            os.path.abspath(fdtcc_velocity_nd) if fdtcc_velocity_nd else None
        ),
        "fdtcc_velocity_layer": (
            list(fdtcc_velocity_layer) if fdtcc_velocity_layer is not None else None
        ),
        "fdtcc_velocity_vp": (
            list(fdtcc_velocity_vp) if fdtcc_velocity_vp is not None else None
        ),
        "fdtcc_velocity_vs": (
            list(fdtcc_velocity_vs) if fdtcc_velocity_vs is not None else None
        ),
        "fdtcc_velocity_vp_vs_ratio": float(fdtcc_velocity_vp_vs_ratio),
        "fdtcc_miniseed_root": (
            os.path.abspath(fdtcc_miniseed_root) if fdtcc_miniseed_root else None
        ),
        "waveform_dir_raw": (
            os.path.abspath(waveform_dir_raw) if waveform_dir_raw else None
        ),
        "fdtcc_miniseed_filename_template": fdtcc_miniseed_filename_template,
        "fdtcc_sac_pre_sec": float(fdtcc_sac_pre_sec),
        "fdtcc_sac_post_sec": float(fdtcc_sac_post_sec),
        "fdtcc_sac_export_backend": str(fdtcc_sac_export_backend).strip().lower(),
        "fdtcc_sac_show_progress": bool(fdtcc_sac_show_progress),
        "fdtcc_wave_dir_mode": str(fdtcc_wave_dir_mode).strip().lower(),
        "fdtcc_waveform_temp_basename": str(fdtcc_waveform_temp_basename),
        "fdtcc_station_default_network": station_default_network,
        "keep_waveform_temp": bool(keep_waveform_temp),
        "fdtcc_prepare_inputs": bool(fdtcc_prepare_inputs),
        "fdtcc_rebuild_ttdb": bool(fdtcc_rebuild_ttdb),
        "stop_after_cc": bool(stop_after_cc),
        "num_workers": int(num_workers),
        "keep_grids": bool(keep_grids),
    }
    return run_config(hypodd_config.Config(**params))


_CC_ONLY_EXPORTS = {
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
}


def __getattr__(name: str) -> Any:
    """Lazily preserve old ``hypodd_runner.api`` CC-only imports."""
    if name in _CC_ONLY_EXPORTS:
        from . import cc_only

        return getattr(cc_only, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = [
    "CCOnlyWindowEntry",
    "CCOnlyWindowParams",
    "CCOnlyWindowResult",
    "EventSelection",
    "FDTCCParams",
    "HypoDDInputs",
    "HypoDDParams",
    "Ph2dtParams",
    "RuntimeOptions",
    "build_cc_only_relocation_kwargs",
    "default_cc_only_hypodd_iter_rows",
    "default_fdtcc_flags",
    "grouped_to_fdtcc_kwargs",
    "plan_cc_only_time_windows",
    "run_config",
    "run_cc_only_auto_time_windows",
    "run_cc_only_relocation",
    "run_cc_only_time_windows",
    "run_fdtcc_cc_only_relocation",
    "run_fdtcc_relocation",
    "scaled_layered_velocity_model",
]
