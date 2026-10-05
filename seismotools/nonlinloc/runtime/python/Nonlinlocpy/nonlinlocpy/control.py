"""Control-file patching helpers for NonLinLoc."""

from __future__ import annotations

import os
import pickle
from typing import List, Tuple

MARKER_GTSRCE_BEFORE = "# NLL_TEMPLATE_BEFORE_STATIONS"
MARKER_GTSRCE_AFTER = "# NLL_TEMPLATE_AFTER_STATIONS"


def save_control_gtsrce_sections(
    control_file_path: str,
    control_file_name: str = "nlloc.in",
) -> None:
    """Cache control file head/tail around the GTSRCE block.
    
    Args:
        control_file_path (str): control file path.
        control_file_name (str): control file name.
    """

    path = os.path.join(control_file_path, control_file_name)
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        lines = f.readlines()

    i_before = i_after = -1
    for i, ln in enumerate(lines):
        if MARKER_GTSRCE_BEFORE in ln:
            i_before = i
        if MARKER_GTSRCE_AFTER in ln:
            i_after = i
            break
    if i_before < 0 or i_after < 0 or i_after <= i_before:
        raise ValueError(
            f"Missing or invalid GTSRCE template markers in {path} "
            f"({MARKER_GTSRCE_BEFORE!r} / {MARKER_GTSRCE_AFTER!r})."
        )

    part1 = lines[: i_before + 1]
    part2 = lines[i_after:]
    pickle_path = os.path.join(control_file_path, "Part_of_ControlFile.pickle")
    with open(pickle_path, "wb") as fp:
        pickle.dump(part1, fp)
        pickle.dump(part2, fp)


def _replace_line_prefix(lines: List[str], prefix: str, new_line: str) -> None:
    """Replace the first line that starts with ``prefix`` inside an in-memory control file.
    
    Args:
        lines (List[str]): lines.
        prefix (str): prefix.
        new_line (str): new line.
    """

    nl = new_line if new_line.endswith("\n") else new_line + "\n"
    for i, ln in enumerate(lines):
        if ln.startswith(prefix):
            lines[i] = nl
            return
    raise ValueError(f"No line starting with {prefix!r}")


def patch_vggrid_line(control_file_path: str, vggrid_line: str, control_file_name: str = "nlloc.in") -> None:
    """Patch the ``VGGRID`` line in a copied ``nlloc.in`` file.
    
    Args:
        control_file_path (str): control file path.
        vggrid_line (str): vggrid line.
        control_file_name (str): control file name.
    """

    path = os.path.join(control_file_path, control_file_name)
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        lines = f.readlines()
    _replace_line_prefix(lines, "VGGRID", vggrid_line.strip())
    with open(path, "w", encoding="utf-8") as f:
        f.writelines(lines)


def patch_locgrid_line(control_file_path: str, locgrid_line: str, control_file_name: str = "nlloc.in") -> None:
    """Patch the ``LOCGRID`` line in a copied ``nlloc.in`` file.
    
    Args:
        control_file_path (str): control file path.
        locgrid_line (str): locgrid line.
        control_file_name (str): control file name.
    """

    path = os.path.join(control_file_path, control_file_name)
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        lines = f.readlines()
    _replace_line_prefix(lines, "LOCGRID", locgrid_line.strip())
    with open(path, "w", encoding="utf-8") as f:
        f.writelines(lines)


def read_grid_lines_from_file(path: str) -> Tuple[str, str]:
    """Two non-comment lines: VGGRID, LOCGRID.
    
    Args:
        path (str): path.
    
    Returns:
        Tuple[str, str]: Result returned by the function.
    """

    rows: List[str] = []
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        for ln in f:
            t = ln.strip()
            if t and not t.startswith("#"):
                rows.append(t)
    if len(rows) < 2:
        raise ValueError(f"Need at least 2 data lines in {path!r}")
    return rows[0], rows[1]
