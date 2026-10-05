"""Build a REAL-format ``ttdb.txt`` for FDTCC using ObsPy TauP.

The output columns match those in ``FDTCC.c`` and the upstream demo ``taup_tt.py``:

    gdist(deg) dep(km) ptime stime prayp srayp phslow shslow pphase sphase

Pipeline overview:

1. ObsPy requires the velocity model to be described in a file on disk. The function `build_taup_model` only accepts a file path pointing to a ``.nd`` or ``.tvel`` file (it does not support in-memory depth/Vp arrays).
2. The `build_taup_model` function writes a ``<stem>.npz`` file alongside the provided model file. This file is then loaded from its absolute path (important due to Linux filesystem case sensitivity with ObsPy).
3. `TauPyModel.get_travel_times` is evaluated on a grid defined by depth × distance (with depth as the outer loop, distance as the inner loop—matching the legacy demo). Each resulting row is written to ``ttdb.txt``.

Main entry points:

* If you already have a ``.nd`` file: use the function `write_ttdb_for_fdtcc`.
* If you have layered depth and Vp (optionally Vs): use `write_simple_layers_to_nd` to generate a ``.nd`` file, then call `write_ttdb_for_fdtcc`. Or, call `write_ttdb_from_simple_velocity` to do both steps in one.

Sampling of (``dep_*``, ``dist_step_deg``, ``n_dist``) should match FDTCC's ``-G`` argument (``trx``, ``trh``, ``tdx``, ``tdh``).
"""
from __future__ import annotations

import argparse
import math
import os
from pathlib import Path
from typing import List, Optional, Sequence, Tuple


from obspy.taup import TauPyModel
from obspy.taup.taup_create import build_taup_model


def rho_from_vp_brocher(vp_km_s: float) -> float:
    """
    Isotropic density (g/cm^3) from P velocity (km/s).

    Brocher (2005) BSSA eq. 1; intended for crustal :math:`V_p \\lesssim 8.5`
    km/s. Values are clamped to a small positive minimum for stability.
    """
    x = max(float(vp_km_s), 0.05)
    rho = (
        1.6612 * x
        - 0.472 * x**2
        + 0.0671 * x**3
        - 0.0043 * x**4
        + 0.000106 * x**5
    )
    return float(max(rho, 1.0))


def write_simple_layers_to_nd(
    out_path: str,
    depth_interfaces_km: Sequence[float],
    vp_km_s: Sequence[float],
    vs_km_s: Sequence[float],
    *,
    planet_radius_km: float = 6371.0,
    mantle_vp_km_s: Optional[float] = None,
    mantle_vs_km_s: Optional[float] = None,
    rho_g_cm3: Optional[Sequence[float]] = None,
    mantle_q_fracs: Optional[Tuple[float, float]] = None,
    qp: float = 1456.0,
    qs: float = 600.0,
) -> Path:
    """
    Write an ObsPy **nd** velocity file from layer tops, ``Vp``, and ``Vs``.

    Each layer has **constant** velocity between consecutive **interfaces**
    (depth below surface, km). The first interface must be ``0.0`` (surface).

    ObsPy treats the **last depth** in the file as Earth radius (see
    :meth:`obspy.taup.velocity_model.VelocityModel.read_nd_file`). For shallow
    stacks, use ``planet_radius_km=6371`` (default) and optional
    ``mantle_*`` to append a constant mantle column so TauP geometry stays
    correct.

    Parameters
    ----------
    depth_interfaces_km
        Strictly increasing depths; length ``L+1`` with ``L`` layers.
        Example: ``(0, 5, 15, 35)`` → layers ``0–5``, ``5–15``, ``15–35`` km.
    vp_km_s, vs_km_s
        Length ``L``; velocities in each layer (``Vs < Vp``).
    planet_radius_km
        Depth at model bottom (typically 6371 km).
    mantle_vp_km_s, mantle_vs_km_s
        If the deepest interface is shallower than ``planet_radius_km``, extend
        with a mantle column using these velocities. Defaults: last crust/lid
        layer values.
    rho_g_cm3
        Optional density per layer (``L`` values). If omitted, densities come
        from :func:`rho_from_vp_brocher` using layer ``Vp``.
    qp, qs
        Attenuation (written to the file; ObsPy may override with defaults
        internally for travel times).

    Returns
    -------
    pathlib.Path
        Absolute path to the written file.
    """
    z = [float(x) for x in depth_interfaces_km]
    vp = [float(x) for x in vp_km_s]
    vs = [float(x) for x in vs_km_s]
    if z[0] != 0.0:
        raise ValueError("depth_interfaces_km[0] must be 0.0 (surface).")
    if len(z) < 2:
        raise ValueError("Need at least two interfaces (surface + base).")
    l_ = len(z) - 1
    if len(vp) != l_ or len(vs) != l_:
        raise ValueError(
            "vp_km_s and vs_km_s must have length len(depth_interfaces_km) - 1."
        )
    for i in range(l_):
        if vs[i] <= 0 or vs[i] >= vp[i]:
            raise ValueError(f"Layer {i}: require 0 < Vs < Vp.")
        if z[i + 1] <= z[i]:
            raise ValueError("depth_interfaces_km must be strictly increasing.")

    if rho_g_cm3 is not None:
        rho_layers = [float(x) for x in rho_g_cm3]
        if len(rho_layers) != l_:
            raise ValueError("rho_g_cm3 must have one value per layer.")
    else:
        rho_layers = [rho_from_vp_brocher(vp[i]) for i in range(l_)]

    rows: List[Tuple[float, float, float, float, float, float]] = []

    def _emit(d: float, p: float, s: float, r: float, qpi: float, qsi: float) -> None:
        rows.append((d, p, s, r, qpi, qsi))

    cur_vp, cur_vs, cur_r = vp[0], vs[0], rho_layers[0]
    _emit(z[0], cur_vp, cur_vs, cur_r, qp, qs)
    for i in range(l_):
        d1 = z[i + 1]
        _emit(d1, cur_vp, cur_vs, cur_r, qp, qs)
        if i < l_ - 1:
            if vp[i + 1] != cur_vp or vs[i + 1] != cur_vs:
                cur_vp = vp[i + 1]
                cur_vs = vs[i + 1]
                cur_r = rho_layers[i + 1]
                _emit(d1, cur_vp, cur_vs, cur_r, qp, qs)

    d_bot = z[-1]
    if d_bot > float(planet_radius_km) + 1e-6:
        raise ValueError(
            f"Last interface {d_bot} km exceeds planet_radius_km={planet_radius_km}."
        )

    vpm = float(mantle_vp_km_s) if mantle_vp_km_s is not None else vp[-1]
    vsm = float(mantle_vs_km_s) if mantle_vs_km_s is not None else vs[-1]
    if vsm <= 0 or vsm >= vpm:
        raise ValueError("Mantle: require 0 < Vs < Vp.")

    rhom = rho_from_vp_brocher(vpm)
    mq = mantle_q_fracs
    qp_m, qs_m = (mq[0], mq[1]) if mq is not None else (qp, qs)

    pr = float(planet_radius_km)
    if pr > d_bot + 1e-6:
        last_p, last_s, last_r = rows[-1][1], rows[-1][2], rows[-1][3]
        if vpm != last_p or vsm != last_s or abs(rhom - last_r) > 1e-6:
            rows.append((d_bot, vpm, vsm, rhom, qp_m, qs_m))
        rows.append((pr, vpm, vsm, rhom, qp_m, qs_m))

    out_p = Path(os.path.abspath(out_path))
    out_p.parent.mkdir(parents=True, exist_ok=True)
    with out_p.open("w", encoding="utf-8") as fh:
        for d, p, s, r, qpi, qsi in rows:
            fh.write(
                f"{d:8.2f} {p:10.5f} {s:10.5f} {r:10.5f} {qpi:9.1f} {qsi:9.1f}\n"
            )
    return out_p


def _taupy_model_from_nd_file(nd_abs: str, *, verbose_build: bool) -> TauPyModel:
    """
    Run :func:`build_taup_model` beside the ``.nd`` and return :class:`TauPyModel`.

    ObsPy resolves short names to ``site-packages/.../data/<lower>.npz``; we always
    load the ``.npz`` that was written next to the input ``.nd``.
    """
    nd_abs = os.path.abspath(nd_abs)
    if not os.path.isfile(nd_abs):
        raise FileNotFoundError(nd_abs)
    model_dir = os.path.dirname(nd_abs)
    nd_p = Path(nd_abs)
    model_dir_p = Path(model_dir)
    npz_path = model_dir_p / nd_p.with_suffix(".npz").name
    build_taup_model(nd_p, output_folder=model_dir_p, verbose=verbose_build)
    if not npz_path.is_file():
        raise FileNotFoundError(
            f"Expected TauP model after build_taup_model: {npz_path}"
        )
    return TauPyModel(model=str(npz_path.resolve()))


def _write_ttdb_on_grid(
    model: TauPyModel,
    out_path: str,
    *,
    dep_km_min: float,
    dep_km_max: float,
    dep_step_km: float,
    dist_step_deg: float,
    n_dist: int,
    phase_list: Tuple[str, ...],
    verbose: bool,
) -> Tuple[int, int]:
    """Sample ``model`` on a depth×distance grid and write REAL ``ttdb`` lines."""
    depths = _frange(dep_km_min, dep_km_max, dep_step_km)
    dists = [(i + 1) * dist_step_deg for i in range(n_dist)]

    out_dir = os.path.dirname(os.path.abspath(out_path))
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)
    n_written = 0
    n_skipped = 0
    with open(out_path, "w", encoding="utf-8") as fh:
        for dep in depths:
            for dist_deg in dists:
                if verbose:
                    print(dep, dist_deg)
                arrivals = model.get_travel_times(
                    source_depth_in_km=dep,
                    distance_in_degree=dist_deg,
                    phase_list=list(phase_list),
                )
                picked = _pick_ps(arrivals, phase_list)
                if picked is None:
                    n_skipped += 1
                    continue
                (
                    pname,
                    p_time,
                    p_ray_param,
                    p_hslowness,
                    sname,
                    s_time,
                    s_ray_param,
                    s_hslowness,
                ) = picked
                fh.write(
                    "{} {} {} {} {} {} {} {} {} {}\n".format(
                        dist_deg,
                        dep,
                        p_time,
                        s_time,
                        p_ray_param,
                        s_ray_param,
                        p_hslowness,
                        s_hslowness,
                        pname,
                        sname,
                    )
                )
                n_written += 1

    return n_written, n_skipped


def write_ttdb_from_simple_velocity(
    out_path: str,
    depth_interfaces_km: Sequence[float],
    vp_km_s: Sequence[float],
    *,
    vs_km_s: Optional[Sequence[float]] = None,
    vp_vs_ratio: float = 1.73,
    velocity_nd_path: Optional[str] = None,
    planet_radius_km: float = 6371.0,
    mantle_vp_km_s: Optional[float] = None,
    mantle_vs_km_s: Optional[float] = None,
    rho_g_cm3: Optional[Sequence[float]] = None,
    mantle_q_fracs: Optional[Tuple[float, float]] = None,
    nd_qp: float = 1456.0,
    nd_qs: float = 600.0,
    dep_km_min: float = 0.0,
    dep_km_max: float = 20.0,
    dep_step_km: float = 2.0,
    dist_step_deg: float = 0.02,
    n_dist: int = 150,
    phase_list: Tuple[str, ...] = ("P", "p", "S", "s"),
    verbose: bool = False,
    verbose_build: bool = False,
) -> Tuple[int, int]:
    """
    Write ``ttdb.txt`` from a **flat-layer** velocity model (no existing ``.nd``).

    This **cannot** skip the ``.nd`` file: :func:`build_taup_model` only reads
    ``.nd``/``.tvel`` from disk. We write a temporary/working ``.nd`` via
    :func:`write_simple_layers_to_nd`, then reuse the same TauP + grid logic as
    :func:`write_ttdb_for_fdtcc`.

    Parameters
    ----------
    vs_km_s
        One ``Vs`` per layer. If omitted, ``Vs = Vp / vp_vs_ratio`` (default
        1.73; HypoDD users often use ~1.7–1.75).
    velocity_nd_path
        Where to save the generated ``.nd``. Default:
        ``<directory of out_path>/velocity_for_fdtcc.nd``.
    verbose_build
        Forwarded to :func:`build_taup_model` (TauP compile; often noisy).
    """
    rv = float(vp_vs_ratio)
    if rv <= 1.0:
        raise ValueError("vp_vs_ratio must be > 1 so Vs < Vp.")
    if vs_km_s is None:
        vs_list = [float(v) / rv for v in vp_km_s]
    else:
        vs_list = [float(v) for v in vs_km_s]

    nd_out = velocity_nd_path or str(
        Path(os.path.abspath(out_path)).parent / "velocity_for_fdtcc.nd"
    )
    write_simple_layers_to_nd(
        nd_out,
        depth_interfaces_km,
        list(vp_km_s),
        vs_list,
        planet_radius_km=planet_radius_km,
        mantle_vp_km_s=mantle_vp_km_s,
        mantle_vs_km_s=mantle_vs_km_s,
        rho_g_cm3=rho_g_cm3,
        mantle_q_fracs=mantle_q_fracs,
        qp=nd_qp,
        qs=nd_qs,
    )
    return write_ttdb_for_fdtcc(
        nd_out,
        out_path,
        dep_km_min=dep_km_min,
        dep_km_max=dep_km_max,
        dep_step_km=dep_step_km,
        dist_step_deg=dist_step_deg,
        n_dist=n_dist,
        phase_list=phase_list,
        verbose=verbose,
        verbose_build=verbose_build,
    )


def _frange(a: float, b: float, step: float) -> List[float]:
    """Inclusive-ish float range [a, b] with positive step."""
    if step <= 0:
        raise ValueError("step must be positive")
    out: List[float] = []
    x = a
    while x <= b + 1e-9 * step:
        out.append(round(x, 9))
        x += step
    return out


def _ray_param_to_factor(ray_param: float) -> float:
    return ray_param * 2.0 * math.pi / 360.0


def _horizontal_slowness(ray_param_factor: float, takeoff_deg: float) -> float:
    """Match legacy Demo ``taup_tt.py`` formula."""
    rad = takeoff_deg * math.pi / 180.0
    t = math.tan(rad)
    if abs(t) < 1e-12:
        raise ValueError(f"takeoff angle too close to 0° ({takeoff_deg})")
    return -1.0 * (ray_param_factor / 111.19) / t


def _pick_ps(
    arrivals: Sequence[object],
    phase_list: Tuple[str, ...],
) -> Optional[
    Tuple[
        str,
        float,
        float,
        float,
        str,
        float,
        float,
        float,
    ]
]:
    """First P/p and first S/s from arrivals; None if either missing."""
    pname = p_time = p_rp = p_hs = None
    sname = s_time = s_rp = s_hs = None
    for arr in arrivals:
        name = getattr(arr, "name", None)
        if name not in phase_list:
            continue
        if name in ("P", "p") and pname is None:
            to = getattr(arr, "takeoff_angle", None)
            if to is None:
                continue
            pname = name
            p_time = float(arr.time)
            p_rp = _ray_param_to_factor(float(arr.ray_param))
            p_hs = _horizontal_slowness(p_rp, float(to))
        if name in ("S", "s") and sname is None:
            to = getattr(arr, "takeoff_angle", None)
            if to is None:
                continue
            sname = name
            s_time = float(arr.time)
            s_rp = _ray_param_to_factor(float(arr.ray_param))
            s_hs = _horizontal_slowness(s_rp, float(to))
        if pname is not None and sname is not None:
            break
    if None in (
        pname,
        p_time,
        p_rp,
        p_hs,
        sname,
        s_time,
        s_rp,
        s_hs,
    ):
        return None
    return (
        str(pname),
        float(p_time),
        float(p_rp),
        float(p_hs),
        str(sname),
        float(s_time),
        float(s_rp),
        float(s_hs),
    )


def write_ttdb_for_fdtcc(
    nd_path: str,
    out_path: str,
    *,
    dep_km_min: float = 0.0,
    dep_km_max: float = 20.0,
    dep_step_km: float = 2.0,
    dist_step_deg: float = 0.02,
    n_dist: int = 150,
    phase_list: Tuple[str, ...] = ("P", "p", "S", "s"),
    verbose: bool = False,
    verbose_build: bool = False,
) -> Tuple[int, int]:
    """
    Build ``ttdb.txt`` from an existing velocity ``.nd`` file using ObsPy TauP.

    Steps: :func:`build_taup_model` → :class:`TauPyModel` → depth×distance grid.

    Default grid matches the historical Demo script (``dep`` 0..20 km step 2;
    ``dist`` ``(1..150)*0.02`` deg). Align FDTCC ``-G`` with this sampling.

    Returns
    -------
    n_written, n_skipped
        Rows written vs skipped (no P+S or numerical failure).
    """
    nd_abs = os.path.abspath(nd_path)
    if not os.path.isfile(nd_abs):
        raise FileNotFoundError(nd_abs)

    model = _taupy_model_from_nd_file(nd_abs, verbose_build=verbose_build)
    return _write_ttdb_on_grid(
        model,
        out_path,
        dep_km_min=dep_km_min,
        dep_km_max=dep_km_max,
        dep_step_km=dep_step_km,
        dist_step_deg=dist_step_deg,
        n_dist=n_dist,
        phase_list=phase_list,
        verbose=verbose,
    )


def main(argv: Optional[Sequence[str]] = None) -> int:
    p = argparse.ArgumentParser(
        description="Build REAL-format ttdb.txt for FDTCC (ObsPy TauP)."
    )
    p.add_argument("--nd", required=True, help="Path to velocity .nd file")
    p.add_argument("-o", "--out", required=True, help="Output ttdb.txt path")
    p.add_argument("--dep-min", type=float, default=0.0)
    p.add_argument("--dep-max", type=float, default=20.0)
    p.add_argument("--dep-step", type=float, default=2.0)
    p.add_argument("--dist-step", type=float, default=0.02, help="deg")
    p.add_argument("--n-dist", type=int, default=150, help="distances (1..n)*step")
    p.add_argument("-v", "--verbose", action="store_true")
    p.add_argument(
        "--verbose-build",
        action="store_true",
        help="Verbose ObsPy build_taup_model (TauP compile)",
    )
    args = p.parse_args(list(argv) if argv is not None else None)

    nw, ns = write_ttdb_for_fdtcc(
        args.nd,
        args.out,
        dep_km_min=args.dep_min,
        dep_km_max=args.dep_max,
        dep_step_km=args.dep_step,
        dist_step_deg=args.dist_step,
        n_dist=args.n_dist,
        verbose=args.verbose,
        verbose_build=args.verbose_build,
    )

    print(f"ttdb: wrote {nw} rows, skipped {ns}", flush=True)
    return 0 if nw > 0 else 1


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
