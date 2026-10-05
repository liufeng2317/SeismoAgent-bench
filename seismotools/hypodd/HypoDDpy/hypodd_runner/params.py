"""Grouped public parameters for hypodd_runner workflows.

These dataclasses are a light public layer over the existing internal
``Config`` bridge. They keep task scripts readable by grouping parameters by
meaning: input files, event selection, ph2dt pairing, HypoDD inversion, FDTCC
cross-correlation, and runtime controls.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Mapping, Optional, Sequence


def _drop_none(values: Mapping[str, Any]) -> Dict[str, Any]:
    """Return a plain dict without keys whose value is ``None``."""
    return {key: value for key, value in values.items() if value is not None}


@dataclass(frozen=True)
class HypoDDInputs:
    """Required file and naming inputs shared by HypoDD workflows.

    Constructor fields
    ------------------
    ``HypoDDInputs(hypo_root, phase_file, station_file, output_folder, catalog_code)``

    Parameters
    ----------
    hypo_root
        HYPODD source/build root containing ``ph2dt/ph2dt`` and
        ``hypoDD/hypoDD``.
    phase_file, station_file
        Prepared phase/event file and station file consumed by hypodd_runner.
    output_folder
        Directory where native ph2dt/HypoDD/FDTCC outputs are written.
    catalog_code
        Prefix for merged native files such as ``{catalog_code}.reloc``.
    """

    hypo_root: str
    phase_file: str
    station_file: str
    output_folder: str
    catalog_code: str

    def to_kwargs(self) -> Dict[str, Any]:
        return {
            "hypo_root": self.hypo_root,
            "phase_file": self.phase_file,
            "station_file": self.station_file,
            "output_folder": self.output_folder,
            "catalog_code": self.catalog_code,
        }


@dataclass(frozen=True)
class EventSelection:
    """Event selection and phase-format controls applied before ph2dt.

    Constructor fields
    ------------------
    ``EventSelection(ot_range, lat_range, lon_range, dep_corr=0.0, phase_format="auto")``

    ``ot_range``, ``lat_range``, and ``lon_range`` define the event subset
    written into native ph2dt/HypoDD inputs. Wrong bounds commonly produce empty
    ``dt_*.ct`` files, so keep them explicit in task scripts.
    """

    ot_range: Any
    lat_range: Sequence[Any]
    lon_range: Sequence[Any]
    dep_corr: float = 0.0
    phase_format: str = "auto"

    def to_kwargs(self) -> Dict[str, Any]:
        return {
            "ot_range": self.ot_range,
            "lat_range": self.lat_range,
            "lon_range": self.lon_range,
            "dep_corr": self.dep_corr,
            "phase_format": self.phase_format,
        }


@dataclass(frozen=True)
class Ph2dtParams:
    """Catalog differential-time pairing parameters for ph2dt.

    Constructor fields
    ------------------
    ``Ph2dtParams(minwght=0.0, maxdist=70.0, maxoffset=5.0, mnb=10, limobs_pair=8, minobs_pair=4, maxobs_pair=30)``

    Field names mirror the native ph2dt/HypoDD parameter names to make log and
    template cross-checking easier:

    - ``minwght``: minimum phase weight.
    - ``maxdist``: maximum event-station distance considered by ph2dt.
    - ``maxoffset``: maximum event-pair separation.
    - ``mnb``: nearest-neighbor event-pair target.
    - ``limobs_pair``, ``minobs_pair``, ``maxobs_pair``: per-pair observation
      count controls.

    Do not pass unsupported fields such as ``minobs_station``,
    ``maxobs_station``, ``minpair``, ``maxsep_ct`` or ``maxsep_cc``.
    """

    minwght: float = 0.0
    maxdist: float = 70.0
    maxoffset: float = 5.0
    mnb: int = 10
    limobs_pair: int = 8
    minobs_pair: int = 4
    maxobs_pair: int = 30

    def to_kwargs(self) -> Dict[str, Any]:
        return {
            "ph2dt_minwght": self.minwght,
            "ph2dt_maxdist": self.maxdist,
            "ph2dt_maxoffset": self.maxoffset,
            "ph2dt_mnb": self.mnb,
            "ph2dt_limobs_pair": self.limobs_pair,
            "ph2dt_minobs_pair": self.minobs_pair,
            "ph2dt_maxobs_pair": self.maxobs_pair,
        }


@dataclass(frozen=True)
class HypoDDParams:
    """HypoDD inversion, weighting, and velocity-model parameters.

    Constructor fields
    ------------------
    ``HypoDDParams(idata=2, iphase=3, maxdist=100.0, minobs_cc=0, minobs_ct=0, istart=2, isolv=2, iter_rows=None, mod_ratio=1.75, mod_top=None, mod_vel=None, iclust=0, dt_cc_per_grid=True)``

    ``iter_rows`` contains rows of
    ``NITER WTCCP WTCCS WRCC WDCC WTCTP WTCTS WRCT WDCT DAMP``. These rows are
    scientific inversion controls, not just runtime options: choose them from
    the study region, station geometry, event-window size, phase quality,
    differential-time link density, and residual behavior. Do not rely on
    ``iter_rows=None`` merely because it is the API default for a real
    scientific relocation; treat it as a package fallback or smoke-test default
    unless a short validation run shows it is suitable for the current data.
    ``NITER`` values are cumulative endpoints, not per-stage repeat counts: use
    increasing values such as ``4, 8, 12``. Repeated endpoints such as ``8, 8,
    8`` are invalid.

    Typical catalog-only starting values are data dependent, so treat ranges as
    diagnostics rather than defaults. Total iteration endpoints often end near
    ``8-20`` for first scientific runs. Catalog weights commonly decrease
    between stages when residuals stabilize, but the exact ``WTCTP``/``WTCTS``
    balance should follow P/S quality and coverage. Residual cutoffs (``WRCT``)
    and pair-distance cutoffs (``WDCT``) must be set from the native residual
    distribution, event spacing, and link distances; published/templates and
    validated regional examples may differ by orders of magnitude. LSQR damping
    is also problem dependent: small local tests may tolerate small values,
    while larger or weakly conditioned regional windows may require values in
    the tens to hundreds. Validate damping from convergence, condition numbers,
    residual changes, air-quake counts, and relocation shifts.

    The shorter field names intentionally mirror native HypoDD names:
    ``idata``, ``iphase``, ``istart``, ``isolv``, and ``iclust``. Velocity-model
    fields are ``mod_top`` (layer tops), ``mod_vel`` (layer Vp), and
    ``mod_ratio`` (global Vp/Vs).

    Do not pass unsupported fields such as ``hypodd_iter_rows``, ``damp`` or
    ``wt`` to this dataclass. Use ``iter_rows`` for native iteration rows.

    For catalog-only relocation, :meth:`to_catalog_only_kwargs` intentionally
    ignores ``idata``, ``minobs_cc`` and ``dt_cc_per_grid`` because catalog-only
    runs force catalog differential-time mode internally. For FDTCC workflows,
    keep ``dt_cc_per_grid=True``; ``cc_engine="fdtcc"`` uses per-grid
    ``dt_*.cc`` files and does not support shared ``dt.cc`` mode.
    """

    idata: int = 2
    iphase: int = 3
    maxdist: float = 100.0
    minobs_cc: int = 0
    minobs_ct: int = 0
    istart: int = 2
    isolv: int = 2
    iter_rows: Optional[Sequence[Sequence[Any]]] = None
    mod_ratio: float = 1.75
    mod_top: Optional[Sequence[Any]] = None
    mod_vel: Optional[Sequence[Any]] = None
    iclust: int = 0
    dt_cc_per_grid: bool = True

    def to_fdtcc_kwargs(self) -> Dict[str, Any]:
        return {
            "hypodd_idata": self.idata,
            "hypodd_iphase": self.iphase,
            "hypodd_maxdist": self.maxdist,
            "hypodd_minobs_cc": self.minobs_cc,
            "hypodd_minobs_ct": self.minobs_ct,
            "hypodd_istart": self.istart,
            "hypodd_isolv": self.isolv,
            "hypodd_iter_rows": self.iter_rows,
            "hypodd_mod_ratio": self.mod_ratio,
            "hypodd_mod_top": self.mod_top,
            "hypodd_mod_vel": self.mod_vel,
            "hypodd_iclust": self.iclust,
            "hypodd_dt_cc_per_grid": self.dt_cc_per_grid,
        }

    def to_catalog_only_kwargs(self) -> Dict[str, Any]:
        return {
            "hypodd_iphase": self.iphase,
            "hypodd_maxdist": self.maxdist,
            "hypodd_minobs_ct": self.minobs_ct,
            "hypodd_istart": self.istart,
            "hypodd_isolv": self.isolv,
            "hypodd_iter_rows": self.iter_rows,
            "velocity_model_top_km": self.mod_top,
            "velocity_model_vp_km_s": self.mod_vel,
            "vp_vs_ratio": self.mod_ratio,
            "hypodd_iclust": self.iclust,
        }


@dataclass(frozen=True)
class FDTCCParams:
    """Waveform cross-correlation and FDTCC input-preparation parameters.

    Constructor fields
    ------------------
    ``FDTCCParams(flags={}, velocity_nd=None, velocity_layer=None,
    velocity_vp=None, velocity_vs=None, velocity_vp_vs_ratio=1.73,
    waveform_dir_raw=None, miniseed_root=None,
    miniseed_filename_template=None, sac_pre_sec=120.0, sac_post_sec=300.0,
    sac_export_backend="process", sac_show_progress=False,
    wave_dir_mode="miniseed", waveform_temp_basename="waveform_temp",
    station_default_network=None, keep_waveform_temp=False,
    prepare_inputs=True, rebuild_ttdb=False, binary=None,
    cleanup_input_lists=True, timeout_sec=None, stop_after_cc=False)``

    Use this group only when waveform cross-correlation should run. Catalog-only
    workflows should omit it. ``waveform_dir_raw`` points to the raw waveform
    source (or prebuilt SAC tree, depending on ``wave_dir_mode``), while
    ``waveform_temp_basename`` controls the temporary/reused FDTCC SAC tree
    name. ``flags`` is a mapping containing FDTCC search windows, thresholds,
    and travel-time table bounds; omit it or pass ``{}`` for package defaults,
    but do not pass ``None``.
    """

    flags: Mapping[str, Any] = field(default_factory=dict)
    velocity_nd: Optional[str] = None
    velocity_layer: Optional[Sequence[Any]] = None
    velocity_vp: Optional[Sequence[Any]] = None
    velocity_vs: Optional[Sequence[Any]] = None
    velocity_vp_vs_ratio: float = 1.73
    waveform_dir_raw: Optional[str] = None
    miniseed_root: Optional[str] = None
    miniseed_filename_template: Optional[str] = None
    sac_pre_sec: float = 120.0
    sac_post_sec: float = 300.0
    sac_export_backend: str = "process"
    sac_show_progress: bool = False
    wave_dir_mode: str = "miniseed"
    waveform_temp_basename: str = "waveform_temp"
    station_default_network: Optional[str] = None
    keep_waveform_temp: bool = False
    prepare_inputs: bool = True
    rebuild_ttdb: bool = False
    binary: Optional[str] = None
    cleanup_input_lists: bool = True
    timeout_sec: Optional[float] = None
    stop_after_cc: bool = False

    def to_kwargs(self) -> Dict[str, Any]:
        return _drop_none(
            {
                "fdtcc_flags": dict(self.flags),
                "fdtcc_binary": self.binary,
                "fdtcc_cleanup_input_lists": self.cleanup_input_lists,
                "fdtcc_timeout_sec": self.timeout_sec,
                "fdtcc_velocity_nd": self.velocity_nd,
                "fdtcc_velocity_layer": self.velocity_layer,
                "fdtcc_velocity_vp": self.velocity_vp,
                "fdtcc_velocity_vs": self.velocity_vs,
                "fdtcc_velocity_vp_vs_ratio": self.velocity_vp_vs_ratio,
                "waveform_dir_raw": self.waveform_dir_raw,
                "fdtcc_miniseed_root": self.miniseed_root,
                "fdtcc_miniseed_filename_template": self.miniseed_filename_template,
                "fdtcc_sac_pre_sec": self.sac_pre_sec,
                "fdtcc_sac_post_sec": self.sac_post_sec,
                "fdtcc_sac_export_backend": self.sac_export_backend,
                "fdtcc_sac_show_progress": self.sac_show_progress,
                "fdtcc_wave_dir_mode": self.wave_dir_mode,
                "fdtcc_waveform_temp_basename": self.waveform_temp_basename,
                "station_default_network": self.station_default_network,
                "keep_waveform_temp": self.keep_waveform_temp,
                "fdtcc_prepare_inputs": self.prepare_inputs,
                "fdtcc_rebuild_ttdb": self.rebuild_ttdb,
                "stop_after_cc": self.stop_after_cc,
            }
        )


@dataclass(frozen=True)
class RuntimeOptions:
    """Execution controls that are not scientific model parameters.

    Constructor fields
    ------------------
    ``RuntimeOptions(num_grids=(1, 1), xy_pad=(0.0, 0.0), num_workers=1, keep_grids=True)``

    Do not pass unsupported fields such as ``keep_intermediate`` or
    ``retain_intermediate`` to this dataclass.
    """

    num_grids: Sequence[Any] = (1, 1)
    xy_pad: Sequence[Any] = (0.0, 0.0)
    num_workers: int = 1
    keep_grids: bool = True

    def to_kwargs(self) -> Dict[str, Any]:
        return {
            "num_grids": self.num_grids,
            "xy_pad": self.xy_pad,
            "num_workers": self.num_workers,
            "keep_grids": self.keep_grids,
        }


@dataclass(frozen=True)
class CCOnlyWindowParams:
    """Time-window planning and rerun controls for CC-only workflows.

    Constructor fields
    ------------------
    ``CCOnlyWindowParams(base="day", window_days=None,
    min_events_per_window=300, max_events_per_window=None,
    window_prefix="ccwin", continue_on_error=True, skip_existing=False)``

    Keep these controls separate from scientific parameters. They decide how a
    selected catalog is split and whether existing window products may be reused;
    they do not change phase parsing, FDTCC settings, or HypoDD inversion
    weights.
    """

    base: str = "day"
    window_days: Optional[int] = None
    min_events_per_window: int = 300
    max_events_per_window: Optional[int] = None
    window_prefix: str = "ccwin"
    continue_on_error: bool = True
    skip_existing: bool = False

    def to_kwargs(self) -> Dict[str, Any]:
        return _drop_none(
            {
                "base": self.base,
                "window_days": self.window_days,
                "min_events_per_window": self.min_events_per_window,
                "max_events_per_window": self.max_events_per_window,
                "window_prefix": self.window_prefix,
                "continue_on_error": self.continue_on_error,
                "skip_existing": self.skip_existing,
            }
        )


def grouped_to_fdtcc_kwargs(
    *,
    inputs: Optional[HypoDDInputs] = None,
    selection: Optional[EventSelection] = None,
    ph2dt: Optional[Ph2dtParams] = None,
    hypodd: Optional[HypoDDParams] = None,
    fdtcc: Optional[FDTCCParams] = None,
    runtime: Optional[RuntimeOptions] = None,
    overrides: Optional[Mapping[str, Any]] = None,
) -> Dict[str, Any]:
    """Merge grouped parameters into kwargs accepted by FDTCC relocation.

    Parameters
    ----------
    inputs, selection, ph2dt, hypodd, fdtcc, runtime
        Optional grouped public parameter objects. Each non-None object is
        converted with its ``to_kwargs`` method.
    overrides
        Optional final keyword overrides. These values replace keys produced by
        grouped objects.

    ``overrides`` is intended for rare compatibility cases. Prefer setting the
    appropriate dataclass field directly in new scripts.
    """
    merged: Dict[str, Any] = {}
    for group in (inputs, selection, runtime, ph2dt):
        if group is not None:
            merged.update(group.to_kwargs())
    if hypodd is not None:
        merged.update(hypodd.to_fdtcc_kwargs())
    if fdtcc is not None:
        merged.update(fdtcc.to_kwargs())
    if overrides:
        merged.update(_drop_none(dict(overrides)))
    return merged


def grouped_to_catalog_only_kwargs(
    *,
    inputs: Optional[HypoDDInputs] = None,
    selection: Optional[EventSelection] = None,
    ph2dt: Optional[Ph2dtParams] = None,
    hypodd: Optional[HypoDDParams] = None,
    runtime: Optional[RuntimeOptions] = None,
    overrides: Optional[Mapping[str, Any]] = None,
) -> Dict[str, Any]:
    """Merge grouped parameters into kwargs accepted by catalog-only relocation.

    Parameters
    ----------
    inputs, selection, ph2dt, hypodd, runtime
        Optional grouped public parameter objects. ``fdtcc`` is intentionally
        absent because catalog-only relocation does not use waveform CC inputs.
    overrides
        Optional final keyword overrides. These values replace keys produced by
        grouped objects.

    ``overrides`` is intended for rare compatibility cases. Prefer setting the
    appropriate dataclass field directly in new scripts.
    """
    merged: Dict[str, Any] = {}
    for group in (inputs, selection, runtime, ph2dt):
        if group is not None:
            merged.update(group.to_kwargs())
    if hypodd is not None:
        merged.update(hypodd.to_catalog_only_kwargs())
    if overrides:
        merged.update(_drop_none(dict(overrides)))
    return merged
