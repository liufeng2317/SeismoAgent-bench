"""Velocity model helpers for NonLinLoc control files."""

from __future__ import annotations

import os
from typing import List, Sequence, Tuple, Union

VELO_LAYER_HEADER = "# model layers (LAYER depth, Vp_top, Vp_grad, Vs_top, Vs_grad, p_top, p_grad)"
VELO_LAYER_END = "# END of Vel2Grid control file statements"
VELO_TAIL_SKIP = 5


def layers_1d_to_vel2grid_lines(
    depth_km: Sequence[float],
    vp_kms: Sequence[float],
    vs_kms: Sequence[float],
    vp_grad: Union[Sequence[float], float] = 0.0,
    vs_grad: Union[Sequence[float], float] = 0.0,
    rho: Union[Sequence[float], float] = 2.7,
    rho_grad: Union[Sequence[float], float] = 0.0,
) -> List[str]:
    """1-D layered model to ``LAYER`` lines for Vel2Grid.
    
    Args:
        depth_km (Sequence[float]): depth km.
        vp_kms (Sequence[float]): vp kms.
        vs_kms (Sequence[float]): vs kms.
        vp_grad (Union[Sequence[float], float]): vp grad.
        vs_grad (Union[Sequence[float], float]): vs grad.
        rho (Union[Sequence[float], float]): rho.
        rho_grad (Union[Sequence[float], float]): rho grad.
    
    Returns:
        List[str]: Result returned by the function.
    """

    n = len(depth_km)
    if len(vp_kms) != n or len(vs_kms) != n:
        raise ValueError("depth_km, vp_kms, vs_kms must match in length")

    def ex(v: Union[Sequence[float], float]) -> List[float]:
        """Expand a scalar or sequence value to one value per velocity layer.

        Args:
            v (Union[Sequence[float], float]): Scalar or per-layer values.

        Returns:
            List[float]: One value per model layer.
        """
        if isinstance(v, (int, float)):
            return [float(v)] * n
        if len(v) != n:
            raise ValueError("per-layer lists must match depth length")
        return [float(x) for x in v]

    vpg, vsg, rh, rhg = ex(vp_grad), ex(vs_grad), ex(rho), ex(rho_grad)
    out: List[str] = []
    for i in range(n):
        out.append(
            f"LAYER  {depth_km[i]:.4f}  {vp_kms[i]:.6f}  {vpg[i]:.6f}  "
            f"{vs_kms[i]:.6f}  {vsg[i]:.6f}  {rh[i]:.6f}  {rhg[i]:.6f}\n"
        )
    return out


def read_depth_vp_vs_columns(
    path: str,
    columns: Tuple[int, int, int] = (0, 1, 2),
) -> List[str]:
    """Whitespace table ``depth vp vs`` to ``LAYER`` lines.
    
    Args:
        path (str): path.
        columns (Tuple[int, int, int]): columns.
    
    Returns:
        List[str]: Result returned by the function.
    """

    d, v, s = [], [], []
    di, pi, si = columns
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            p = line.split()
            if len(p) <= max(columns):
                continue
            d.append(float(p[di]))
            v.append(float(p[pi]))
            s.append(float(p[si]))
    return layers_1d_to_vel2grid_lines(d, v, s)


def replace_vel2grid_layer_block(
    control_file_path: str,
    layer_lines: Sequence[str],
    control_file_name: str = "nlloc.in",
) -> None:
    """Replace the ``LAYER`` list in the Vel2Grid section.
    
    Args:
        control_file_path (str): control file path.
        layer_lines (Sequence[str]): layer lines.
        control_file_name (str): control file name.
    """

    path = os.path.join(control_file_path, control_file_name)
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        lines = f.readlines()

    i_h = i_e = -1
    for i, ln in enumerate(lines):
        if VELO_LAYER_HEADER in ln:
            i_h = i
        if VELO_LAYER_END in ln:
            i_e = i
            break
    if i_h < 0 or i_e < 0:
        raise ValueError(f"Vel2Grid layer markers not found in {path!r}")

    tail = i_e - VELO_TAIL_SKIP
    if tail <= i_h:
        raise ValueError("Invalid Vel2Grid section boundaries")

    normed = [x if x.endswith("\n") else x + "\n" for x in layer_lines]
    with open(path, "w", encoding="utf-8") as fw:
        fw.writelines(lines[: i_h + 1] + normed + lines[tail:])
