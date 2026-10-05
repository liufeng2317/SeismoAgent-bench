"""Configuration model for the HypoDD/FDTCC relocation API.

Generated task scripts should use the public function-parameter APIs, such as
``run_catalog_only_relocation``, ``run_fdtcc_relocation``, or
``run_cc_only_relocation``. :class:`Config` remains an internal bridge between
those public functions and the native ph2dt/HypoDD runner.

Important: built-in defaults are demo placeholders. Real relocation tasks must
override at least ``hypo_root``, ``fsta``, ``fpha``, ``output_folder``,
``ctlg_code``, ``ot_range``, ``lat_range``, and ``lon_range`` with values derived
from the current data. Do not copy the default Ridgecrest/demo time or spatial
bounds into a new task; ``mk_pha`` applies those bounds before ``ph2dt`` and can
filter all events if they are wrong.

Example::

    cfg = Config(
        ctlg_code="test", fpha="./pha.dat", output_folder="./out", cc_engine="fdtcc"
    )
"""
from __future__ import annotations

import os
from copy import deepcopy
from typing import Any, Dict, Mapping

from obspy import UTCDateTime

def _current_dir() -> str:
    """Return this package directory for default template paths."""
    return os.path.dirname(os.path.abspath(__file__))


def _default_hypodd_mod_top():
    """Default 1-D model layer tops from ``template/hypoDD.inp`` (km)."""
    return (
        0.0, 2.0, 4.0, 6.0, 8.0, 10.0, 12.0, 14.0,
        18.0, 22.0, 30.0, 35.0, 40.0, 44.0,
    )


def _default_hypodd_mod_vel():
    """Default 1-D model layer Vp values from ``template/hypoDD.inp`` (km/s)."""
    return (
        4.46, 4.68, 5.01, 5.33, 5.50, 5.60, 5.69,
        6.16, 6.52, 6.86, 7.38, 7.38, 7.61, 7.72,
    )


def _default_hypodd_iter_rows():
    """Default HypoDD iteration rows from the packaged template."""
    return (
        (4, -9.0, -9.0, -9.0, -9.0, 1.0, 0.5, 6.0, 20.0, 120.0),
        (8, -9.0, -9.0, -9.0, -9.0, 0.7, 0.3, 4.0, 15.0, 80.0),
    )


def _default_config_dict(
    hypo_root: str = "/liufeng1afs/project/03_LLM/Science_Discovery_Agenet/software/hypoDD/HYPODD/src",
    hypoDD_inp_template: str = None,
    hypoDD_ph2dt_template: str = None,
    hypodd_inp_mode: str = "programmatic",
    ctlg_code: str = "eg_pal_ct",
    output_folder: str = None,
    fsta: str = "./example_pal.sta",
    fpha: str = "./eg_pal_hyp_full.pha",
    dep_corr: float = 0,
    ot_range: str = "20190704-20190707",
    lat_range: list[float] = None,
    lon_range: list[float] = None,
    num_grids: list[int] = None,
    xy_pad: list[float] = None,
    num_workers: int = 32,
    keep_grids: bool = False,
    hypodd_idata: int = 2,
    hypodd_iphase: int = 3,
    hypodd_maxdist: float = 100.0,
    hypodd_minobs_cc: int = 0,
    hypodd_minobs_ct: int = 0,
    hypodd_istart: int = 2,
    hypodd_isolv: int = 2,
    hypodd_iter_rows: list[tuple[int, float, float, float, float, float, float, float, float, float]] = None,
    hypodd_mod_ratio: float = 1.75,
    hypodd_mod_top: list[float] = None,
    hypodd_mod_vel: list[float] = None,
    hypodd_iclust: int = 0,
    hypodd_dt_cc_per_grid: bool = True,
    ph2dt_minwght: float = 0.0,
    ph2dt_maxdist: float = 70.0,
    ph2dt_maxoffset: float = 5.0,
    ph2dt_mnb: int = 10,
    ph2dt_limobs_pair: int = 8,
    ph2dt_minobs_pair: int = 4,
    ph2dt_maxobs_pair: int = 30,
    ph2dt_inp_mode: str = "programmatic",
    phase_format: str = "auto",
    cc_engine: str = "fdtcc",
    fdtcc_flags: dict = None,
    fdtcc_binary: str = None,
    fdtcc_cleanup_input_lists: bool = True,
    fdtcc_timeout_sec: float = None,
    fdtcc_velocity_nd: str = None,
    fdtcc_velocity_layer: list[float] = None,
    fdtcc_velocity_vp: list[float] = None,
    fdtcc_velocity_vs: list[float] = None,
    fdtcc_velocity_vp_vs_ratio: float = 1.73,
    fdtcc_miniseed_root: str = None,
    waveform_dir_raw: str = None,
    fdtcc_miniseed_filename_template: str = None,
    fdtcc_sac_pre_sec: float = 120.0,
    fdtcc_sac_post_sec: float = 300.0,
    fdtcc_sac_export_backend: str = "process",
    fdtcc_sac_show_progress: bool = False,
    fdtcc_cleanup_sac_waveforms: bool = True,
    keep_waveform_temp: bool = False,
    fdtcc_wave_dir_mode: str = "miniseed",
    fdtcc_waveform_temp_basename: str = "waveform_temp",
    fdtcc_station_default_network: str = None,
    fdtcc_prepare_inputs: bool = True,
    fdtcc_rebuild_ttdb: bool = False,
    stop_after_cc: bool = False,
) -> Dict[str, Any]:
    """
    Demo placeholders only. Public API users should override the path, time,
    spatial, and catalog fields for each real task before running relocation.
    """
    if hypoDD_inp_template is None:
        hypoDD_inp_template = os.path.join(_current_dir(), "template/hypoDD.inp")
    if hypoDD_ph2dt_template is None:
        hypoDD_ph2dt_template = os.path.join(_current_dir(), "template/ph2dt.inp")
    if output_folder is None:
        output_folder = os.path.join(_current_dir(), "data", "output")
    if lat_range is None:
        lat_range = [35.45, 36.05]
    if lon_range is None:
        lon_range = [-117.8, -117.25]
    if num_grids is None:
        num_grids = [1, 1]
    if xy_pad is None:
        xy_pad = [0.06, 0.05]
    if hypodd_iter_rows is None:
        hypodd_iter_rows = _default_hypodd_iter_rows()
    if hypodd_mod_top is None:
        hypodd_mod_top = _default_hypodd_mod_top()
    if hypodd_mod_vel is None:
        hypodd_mod_vel = _default_hypodd_mod_vel()

    return {
        "hypo_root": hypo_root,
        "hypoDD_inp_template": hypoDD_inp_template,
        "hypoDD_ph2dt_template": hypoDD_ph2dt_template,
        "hypodd_inp_mode": hypodd_inp_mode,
        "ctlg_code": ctlg_code,
        "output_folder": output_folder,
        "fsta": fsta,
        "fpha": fpha,
        "dep_corr": dep_corr,
        "ot_range": ot_range,
        "lat_range": lat_range,
        "lon_range": lon_range,
        "num_grids": num_grids,
        "xy_pad": xy_pad,
        "num_workers": num_workers,
        "keep_grids": keep_grids,
        "hypodd_idata": hypodd_idata,
        "hypodd_iphase": hypodd_iphase,
        "hypodd_maxdist": hypodd_maxdist,
        "hypodd_minobs_cc": hypodd_minobs_cc,
        "hypodd_minobs_ct": hypodd_minobs_ct,
        "hypodd_istart": hypodd_istart,
        "hypodd_isolv": hypodd_isolv,
        "hypodd_iter_rows": hypodd_iter_rows,
        "hypodd_mod_ratio": hypodd_mod_ratio,
        "hypodd_mod_top": hypodd_mod_top,
        "hypodd_mod_vel": hypodd_mod_vel,
        "hypodd_iclust": hypodd_iclust,
        "hypodd_dt_cc_per_grid": hypodd_dt_cc_per_grid,
        "ph2dt_minwght": ph2dt_minwght,
        "ph2dt_maxdist": ph2dt_maxdist,
        "ph2dt_maxoffset": ph2dt_maxoffset,
        "ph2dt_mnb": ph2dt_mnb,
        "ph2dt_limobs_pair": ph2dt_limobs_pair,
        "ph2dt_minobs_pair": ph2dt_minobs_pair,
        "ph2dt_maxobs_pair": ph2dt_maxobs_pair,
        "ph2dt_inp_mode": ph2dt_inp_mode,
        # auto | hypodd | pal — see phase_convert.prepare_phase_file
        "phase_format": phase_format,
        # "fdtcc" (only supported)
        "cc_engine": cc_engine,
        "fdtcc_flags": fdtcc_flags,
        "fdtcc_binary": fdtcc_binary,
        "fdtcc_cleanup_input_lists": fdtcc_cleanup_input_lists,
        "fdtcc_timeout_sec": fdtcc_timeout_sec,
        # Auto FDTCC (no manual station.dat / ttdb / wave_dir): velocity model + MiniSEED root
        "fdtcc_velocity_nd": fdtcc_velocity_nd,
        # Direct velocity model for FDTCC ttdb generation.
        # layer length may equal len(vp) (layer tops) or len(vp)+1 (interfaces).
        # If fdtcc_velocity_vs is omitted, Vs is derived as Vp / fdtcc_velocity_vp_vs_ratio.
        "fdtcc_velocity_layer": fdtcc_velocity_layer,
        "fdtcc_velocity_vp": fdtcc_velocity_vp,
        "fdtcc_velocity_vs": fdtcc_velocity_vs,
        "fdtcc_velocity_vp_vs_ratio": fdtcc_velocity_vp_vs_ratio,
        "fdtcc_miniseed_root": fdtcc_miniseed_root,
        # Raw waveform root (MiniSEED) used to export temporary FDTCC SAC trees.
        # This is independent from ttdb build; only affects ``fdtcc_wave_dir_mode=miniseed``.
        "waveform_dir_raw": waveform_dir_raw,
        "fdtcc_miniseed_filename_template": fdtcc_miniseed_filename_template,
        "fdtcc_sac_pre_sec": fdtcc_sac_pre_sec,
        "fdtcc_sac_post_sec": fdtcc_sac_post_sec,
        "fdtcc_sac_export_backend": fdtcc_sac_export_backend,
        "fdtcc_sac_show_progress": fdtcc_sac_show_progress,
        "fdtcc_cleanup_sac_waveforms": fdtcc_cleanup_sac_waveforms,
        # Convenience toggle:
        # - keep_waveform_temp=true => keep output/waveform_temp (do not delete)
        # - keep_waveform_temp=false (default) => delete output/waveform_temp
        # Internally maps to fdtcc_cleanup_sac_waveforms.
        "keep_waveform_temp": keep_waveform_temp,
        # fdtcc_config wave_dir: "miniseed" = raw day-volumed MiniSEED root -> output/waveform_temp_* then delete
        # "fdtcc_sac" = wave_dir is already FDTCC -F1 SAC tree (no export, no temp delete)
        "fdtcc_wave_dir_mode": fdtcc_wave_dir_mode,
        "fdtcc_waveform_temp_basename": fdtcc_waveform_temp_basename,
        "fdtcc_station_default_network": fdtcc_station_default_network,
        # Embed in run_hypoDD: REAL station from fsta; ttdb from velocity keys when set
        "fdtcc_prepare_inputs": fdtcc_prepare_inputs,
        "fdtcc_rebuild_ttdb": fdtcc_rebuild_ttdb,
        "stop_after_cc": stop_after_cc,
    }


def _config_keys() -> frozenset:
    """Return valid top-level config keys for JSON and keyword inputs."""
    return frozenset(_default_config_dict().keys())


def _hypo_executable_path(hypo_root: str, tool_name: str) -> str:
    """
    Path to the ``hypoDD`` or ``ph2dt`` **binary** under ``hypo_root``.

    - **Flat** (common): ``{hypo_root}/{tool_name}`` is the executable file.
    - **Nested build dir**: ``{hypo_root}/{tool_name}/`` is a directory and the
      binary is ``{hypo_root}/{tool_name}/{tool_name}`` (matches ph2dt's ``join(dir, 'ph2dt')``).
    """
    base = os.path.join(os.path.abspath(hypo_root), tool_name)
    if os.path.isdir(base):
        return os.path.join(base, tool_name)
    return base

class Config(object):
    """
    Configuration for HypoDD / ph2dt workflows.

    Parameters
    ----------
    **kwargs
        Keyword arguments with names from the internal config schema. Public
        callers should normally use the higher-level function APIs instead of
        constructing this class directly.
    """

    def __init__(self, **kwargs: Any) -> None:
        params = deepcopy(_default_config_dict())  # Built-in defaults

        bad = set(kwargs) - _config_keys()
        if bad:
            raise ValueError(f"Unknown config keyword arguments: {sorted(bad)}")
        params.update(kwargs)  # Keyword arguments override after loading

        self._apply_params(params)

    def _apply_params(self, params: Mapping[str, Any]) -> None:
        hypo_root = params["hypo_root"]
        # executable path
        self.hypo_root = hypo_root  # Root for HYPODD source/build directory (contains ph2dt, hypoDD subdirs or executables)
        self.hypoDD_exe = _hypo_executable_path(hypo_root, "hypoDD")  # Absolute path of hypoDD executable
        # ph2dt subdirectory: ph2dt.py executes os.path.join(ph2dt_exe, "ph2dt") to get the true ph2dt binary
        self.ph2dt_exe = os.path.join(self.hypo_root, "ph2dt")

        # template files
        self.hypoDD_inp_template = params["hypoDD_inp_template"]  # Template for hypoDD.inp (used if hypodd_inp_mode=template)
        self.hypoDD_ph2dt_template = params["hypoDD_ph2dt_template"]  # Template for ph2dt.inp (used if ph2dt_inp_mode=template)
        self.hypodd_inp_mode = params["hypodd_inp_mode"]  # 'programmatic': generate by getinp order; 'template': substitute template

        # input and output files
        self.ctlg_code = params["ctlg_code"]  # Output prefix (e.g., ridgecrest → ridgecrest.reloc / .pha)
        self.output_folder = params["output_folder"]  # Output directory for ph2dt, hypoDD, merged/plot outputs
        self.fsta = params["fsta"]  # Station list (input for mk_sta / HypoDD)
        self.fpha = params["fpha"]  # Complete phase catalog (after format conversion, used for mk_pha, ph2dt)
        self.dep_corr = params["dep_corr"]  # Depth correction for output catalog [km], subtracted from hypoDD depth before CSV output
        self.ot_range = params["ot_range"]  # mk_pha time window, format 'YYYYMMDD-YYYYMMDD'
        self.lat_range = list(params["lat_range"])  # mk_pha latitude range [min, max]
        self.lon_range = list(params["lon_range"])  # mk_pha longitude range [min, max]
        self.num_grids = list(params["num_grids"])  # Grid partitioning [nx, ny]; each grid runs ph2dt + hypoDD independently
        self.xy_pad = list(params["xy_pad"])  # Extra padding in lat/lon for each subgrid (degrees)
        self.num_workers = int(params["num_workers"])  # DataLoader parallel worker count (for multi-grid hypoDD)
        self.keep_grids = bool(params["keep_grids"])  # True: keep intermediate files for all grids; False: delete after merge

        # HypoDD parameters
        self.hypodd_idata = int(params["hypodd_idata"])  # 0 synthetic; 1 CC only; 2 catalog only; 3 catalog+CC (may be rewritten by dt.cc existence)
        self.hypodd_iphase = int(params["hypodd_iphase"])  # 1: P; 2: S; 3: P and S
        self.hypodd_maxdist = float(params["hypodd_maxdist"])  # Station selection: max cluster center-station distance (km)
        self.hypodd_minobs_cc = int(params["hypodd_minobs_cc"])  # HypoDD: minimum CC observations per pair (0 = no clustering)
        self.hypodd_minobs_ct = int(params["hypodd_minobs_ct"])  # Catalog diff observations clustering: min per pair
        self.hypodd_istart = int(params["hypodd_istart"])  # 1 single-source initial; 2 network initial
        self.hypodd_isolv = int(params["hypodd_isolv"])  # 1 SVD; 2 LSQR
        ir = params["hypodd_iter_rows"]
        self.hypodd_iter_rows = (
            tuple(ir) if ir is not None else _default_hypodd_iter_rows()
        )  # Each row: NITER, CC P/S weights, CC residual/distance thresholds, cat. P/S weights, cat. thresholds, damping
        self.hypodd_mod_ratio = float(params["hypodd_mod_ratio"])  # 1D model Vp/Vs
        mt = params["hypodd_mod_top"]
        mv = params["hypodd_mod_vel"]
        self.hypodd_mod_top = tuple(mt) if mt is not None else _default_hypodd_mod_top()  # Top depth of each layer (km)
        self.hypodd_mod_vel = tuple(mv) if mv is not None else _default_hypodd_mod_vel()  # Vp of each layer (km/s)
        self.hypodd_iclust = int(params["hypodd_iclust"])  # Relocation cluster ID, 0 means all
        self.hypodd_dt_cc_per_grid = bool(params["hypodd_dt_cc_per_grid"])  # True: dt_i-j.cc per grid; False: root dt.cc

        # ph2dt parameters
        self.ph2dt_minwght = float(params["ph2dt_minwght"])  # ph2dt: minimum pick weight for connected stations
        self.ph2dt_maxdist = float(params["ph2dt_maxdist"])  # ph2dt: max station epicentral distance (km)
        self.ph2dt_maxoffset = float(params["ph2dt_maxoffset"])  # ph2dt: max offset between event pairs (km, weak link threshold)
        self.ph2dt_mnb = int(params["ph2dt_mnb"])  # ph2dt: minimum strong neighbors per event
        self.ph2dt_limobs_pair = int(params["ph2dt_limobs_pair"])  # Minimum common obs for strong event pair connection
        self.ph2dt_minobs_pair = int(params["ph2dt_minobs_pair"])  # Minimum obs for event pair to be written to dt.ct
        self.ph2dt_maxobs_pair = int(params["ph2dt_maxobs_pair"])  # Max obs retained per event pair (clipped after sorting)
        self.ph2dt_inp_mode = params["ph2dt_inp_mode"]  # 'programmatic' / 'template'
        self.phase_format = str(params["phase_format"]).strip().lower()  # auto / hypodd / pal, see phase_convert

        # CC parameters
        self.cc_engine = str(params.get("cc_engine", "fdtcc")).strip().lower()

        def _opt_str(pk: str) -> Optional[str]:
            v = params.get(pk)
            if isinstance(v, str) and v.strip():
                return v.strip()
            return None

        flags = params.get("fdtcc_flags")
        if flags is None:
            self.fdtcc_flags = {}
        elif isinstance(flags, Mapping):
            self.fdtcc_flags = dict(flags)
        else:
            raise ValueError("fdtcc_flags must be a mapping/dict when provided")
        self.fdtcc_binary = _opt_str("fdtcc_binary")
        self.fdtcc_cleanup_input_lists = bool(
            params.get("fdtcc_cleanup_input_lists", True)
        )
        timeout = params.get("fdtcc_timeout_sec")
        self.fdtcc_timeout_sec = float(timeout) if timeout is not None else None

        self.fdtcc_velocity_nd = _opt_str("fdtcc_velocity_nd")
        self.fdtcc_velocity_layer = params.get("fdtcc_velocity_layer")
        self.fdtcc_velocity_vp = params.get("fdtcc_velocity_vp")
        self.fdtcc_velocity_vs = params.get("fdtcc_velocity_vs")
        self.fdtcc_velocity_vp_vs_ratio = float(
            params.get("fdtcc_velocity_vp_vs_ratio", 1.73)
        )
        self.fdtcc_miniseed_root = _opt_str("fdtcc_miniseed_root")
        self.waveform_dir_raw = _opt_str("waveform_dir_raw")
        mt = params.get("fdtcc_miniseed_filename_template")
        if isinstance(mt, str) and mt.strip():
            self.fdtcc_miniseed_filename_template = mt.strip()
        else:
            self.fdtcc_miniseed_filename_template = None
        self.fdtcc_sac_pre_sec = float(params.get("fdtcc_sac_pre_sec", 120.0))
        self.fdtcc_sac_post_sec = float(params.get("fdtcc_sac_post_sec", 300.0))
        self.fdtcc_sac_export_backend = str(
            params.get("fdtcc_sac_export_backend", "process")
        ).strip().lower()
        if self.fdtcc_sac_export_backend not in ("process", "thread"):
            raise ValueError("fdtcc_sac_export_backend must be 'process' or 'thread'")
        self.fdtcc_sac_show_progress = bool(
            params.get("fdtcc_sac_show_progress", False)
        )
        # Primary source of truth for keeping/deleting output/waveform_temp:
        # - keep_waveform_temp=true => keep (no delete)
        # - default => delete
        keep_waveform_temp = bool(params.get("keep_waveform_temp", False))
        if keep_waveform_temp:
            self.fdtcc_cleanup_sac_waveforms = False
        else:
            self.fdtcc_cleanup_sac_waveforms = bool(
                params.get("fdtcc_cleanup_sac_waveforms", True)
            )
        self.fdtcc_prepare_inputs = bool(params.get("fdtcc_prepare_inputs", True))
        self.fdtcc_rebuild_ttdb = bool(params.get("fdtcc_rebuild_ttdb", False))
        self.stop_after_cc = bool(params.get("stop_after_cc", False))
        self.fdtcc_wave_dir_mode = str(
            params.get("fdtcc_wave_dir_mode", "miniseed")
        ).strip().lower()
        wtb = params.get("fdtcc_waveform_temp_basename")
        if isinstance(wtb, str) and wtb.strip():
            self.fdtcc_waveform_temp_basename = wtb.strip()
        else:
            self.fdtcc_waveform_temp_basename = "waveform_temp"
        self.fdtcc_station_default_network = _opt_str("fdtcc_station_default_network")

        self._check_hypodd_params()
        self._check_phase_format()
        self._check_ot_range()
        self._check_lon_range()
        self._check_lat_range()

    def _check_phase_format(self):
        if self.phase_format not in ("auto", "hypodd", "pal"):
            raise ValueError(
                "phase_format must be 'auto', 'hypodd', or 'pal' "
                "(see phase_convert.prepare_phase_file)"
            )

    def _check_hypodd_params(self):
        if self.hypodd_inp_mode not in ("programmatic", "template"):
            raise ValueError("hypodd_inp_mode must be 'programmatic' or 'template'")
        if self.ph2dt_inp_mode not in ("programmatic", "template"):
            raise ValueError("ph2dt_inp_mode must be 'programmatic' or 'template'")
        if self.cc_engine in ("none", "skip", "", None):
            # No waveform CC step.
            pass
        elif self.cc_engine == "fdtcc":
            if self.fdtcc_wave_dir_mode not in ("miniseed", "fdtcc_sac"):
                raise ValueError(
                    "fdtcc_wave_dir_mode must be 'miniseed' or 'fdtcc_sac' "
                    "(raw MiniSEED root vs ready-made FDTCC SAC tree under wave_dir)"
                )
            has_direct_velocity = bool(
                self.fdtcc_velocity_layer is not None or self.fdtcc_velocity_vp is not None
            )
            n_velocity_sources = sum(
                bool(x)
                for x in (
                    self.fdtcc_velocity_nd,
                    has_direct_velocity,
                )
            )
            if n_velocity_sources > 1:
                raise ValueError(
                    "set at most one FDTCC velocity source: fdtcc_velocity_nd, "
                    "or direct fdtcc_velocity_layer/fdtcc_velocity_vp"
                )
            has_velocity = bool(
                self.fdtcc_velocity_nd or has_direct_velocity
            )
            has_auto_waveforms = bool(self.fdtcc_miniseed_root or self.waveform_dir_raw)
            auto_ok = bool(
                has_auto_waveforms
                and has_velocity
                and self.fdtcc_wave_dir_mode == "miniseed"
            )
            if not auto_ok:
                raise ValueError(
                    "cc_engine 'fdtcc' requires waveform_dir_raw/fdtcc_miniseed_root plus "
                    "a velocity model (prefer direct fdtcc_velocity_layer and "
                    "fdtcc_velocity_vp; fdtcc_velocity_nd is also supported)."
                )
            if has_direct_velocity:
                if self.fdtcc_velocity_layer is None or self.fdtcc_velocity_vp is None:
                    raise ValueError(
                        "direct FDTCC velocity needs both fdtcc_velocity_layer and "
                        "fdtcc_velocity_vp"
                    )
                layer = [float(x) for x in self.fdtcc_velocity_layer]
                vp = [float(x) for x in self.fdtcc_velocity_vp]
                if len(layer) not in (len(vp), len(vp) + 1):
                    raise ValueError(
                        "direct FDTCC velocity length mismatch: fdtcc_velocity_layer "
                        "must have len(vp) layer tops or len(vp)+1 interfaces; got "
                        f"layer={len(layer)}, vp={len(vp)}"
                    )
                if self.fdtcc_velocity_vs is not None:
                    vs = [float(x) for x in self.fdtcc_velocity_vs]
                    if len(vs) != len(vp):
                        raise ValueError(
                            "direct FDTCC velocity length mismatch: fdtcc_velocity_vs "
                            f"must match fdtcc_velocity_vp; got vs={len(vs)}, vp={len(vp)}"
                        )
                if self.fdtcc_velocity_vp_vs_ratio <= 1.0:
                    raise ValueError("fdtcc_velocity_vp_vs_ratio must be > 1.0")
            if self.fdtcc_miniseed_root and not has_velocity:
                raise ValueError(
                    "fdtcc_miniseed_root requires an FDTCC velocity model"
                )
            if self.waveform_dir_raw and self.fdtcc_wave_dir_mode != "miniseed":
                raise ValueError(
                    "waveform_dir_raw is only supported with fdtcc_wave_dir_mode='miniseed'"
                )
            if self.waveform_dir_raw and not has_velocity:
                raise ValueError(
                    "waveform_dir_raw requires an FDTCC velocity model"
                )
            if has_velocity and not (
                self.fdtcc_miniseed_root or self.waveform_dir_raw
            ):
                raise ValueError(
                    "FDTCC velocity model needs fdtcc_miniseed_root or waveform_dir_raw "
                    "for automatic input preparation"
                )
        else:
            raise ValueError("cc_engine must be 'fdtcc' or 'none/skip' (cc_auto is not supported).")
        if self.hypodd_idata not in (0, 1, 2, 3):
            raise ValueError("hypodd_idata must be 0, 1, 2, or 3 (see HypoDD getinp.f)")
        if self.hypodd_iphase not in (1, 2, 3):
            raise ValueError("hypodd_iphase must be 1 (P), 2 (S), or 3 (P&S)")
        nlay = len(self.hypodd_mod_top)
        if len(self.hypodd_mod_vel) != nlay:
            raise ValueError("hypodd_mod_top and hypodd_mod_vel must have the same length")
        nset = len(self.hypodd_iter_rows)
        if nset < 1 or nset > 10:
            raise ValueError("hypodd_iter_rows must have between 1 and 10 blocks")
        for row in self.hypodd_iter_rows:
            if len(row) != 10:
                raise ValueError(
                    "each hypodd_iter_rows entry must be "
                    "(NITER, WTCCP, WTCCS, WRCC, WDCC, WTCTP, WTCTS, WRCT, WDCT, DAMP)"
                )

    def _check_ot_range(self):
        try:
            ot_min, ot_max = [UTCDateTime(date) for date in self.ot_range.split("-")]
        except Exception as e:
            raise ValueError(
                f"Invalid ot_range '{self.ot_range}'. "
                f"Expected format: 'YYYYMMDD-YYYYMMDD'. Error: {e}"
            ) from e
        if ot_min >= ot_max:
            raise ValueError("ot_min must be less than ot_max")

    def _check_lon_range(self):
        try:
            lon_min, lon_max = self.lon_range
            if not (isinstance(lon_min, (float, int)) and isinstance(lon_max, (float, int))):
                raise ValueError("lon_range must be a list of two numbers (float or int)")
            lon_min, lon_max = float(lon_min), float(lon_max)
        except Exception as e:
            raise ValueError(f"lon_range must be a list of two floats, error: {e}") from e
        if lon_min >= lon_max:
            raise ValueError("lon_min must be less than lon_max")

    def _check_lat_range(self):
        try:
            lat_min, lat_max = self.lat_range
            if not (isinstance(lat_min, (float, int)) and isinstance(lat_max, (float, int))):
                raise ValueError("lat_range must be a list of two numbers (float or int)")
            lat_min, lat_max = float(lat_min), float(lat_max)
        except Exception as e:
            raise ValueError(f"lat_range must be a list of two floats, error: {e}") from e
        if lat_min >= lat_max:
            raise ValueError("lat_min must be less than lat_max")
