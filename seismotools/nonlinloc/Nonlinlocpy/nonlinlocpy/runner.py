"""Execution and run-directory cleanup helpers for NonLinLoc."""

from __future__ import annotations

import os
import shutil
import subprocess
from typing import Optional


def clear_obs_and_loc(
    control_file_path: str,
    obs_basename: str = "All.obs",
    loc_backup_dir: Optional[str] = None,
    *,
    clear_obs_file: bool = True,
) -> None:
    """Delete obs file if requested, then reset ``loc/`` or move prior outputs to backup.
    
    Args:
        control_file_path (str): control file path.
        obs_basename (str): obs basename.
        loc_backup_dir (Optional[str]): loc backup dir.
        clear_obs_file (bool): clear obs file.
    """

    script = os.getcwd()
    if clear_obs_file:
        obs_dir = os.path.join(control_file_path, "obs")
        if os.path.isdir(obs_dir):
            fp = os.path.join(obs_dir, obs_basename)
            if os.path.isfile(fp):
                os.chdir(obs_dir)
                os.remove(obs_basename)
    loc_dir = os.path.join(control_file_path, "loc")
    if os.path.isdir(loc_dir):
        if loc_backup_dir is None:
            shutil.rmtree(loc_dir)
            os.mkdir(loc_dir)
        else:
            os.chdir(control_file_path)
            subprocess.run(f"mv ./loc/* {loc_backup_dir}", shell=True, check=False)
            subprocess.run("rm -r ./loc", shell=True, check=False)
            os.mkdir("loc")
    os.chdir(script)


def reset_loc_directory(
    control_file_path: str,
    loc_backup_dir: Optional[str] = None,
) -> None:
    """Only clear ``loc/`` while keeping ``obs/``.
    
    Args:
        control_file_path (str): control file path.
        loc_backup_dir (Optional[str]): loc backup dir.
    """

    clear_obs_and_loc(
        control_file_path,
        loc_backup_dir=loc_backup_dir,
        clear_obs_file=False,
    )


def run_nlloc_bin(
    nlloc_bin_dir: str,
    control_file_path: str,
    control_file_name: str = "nlloc.in",
) -> None:
    """Run the ``NLLoc`` executable inside the given run directory.
    
    Args:
        nlloc_bin_dir (str): nlloc bin dir.
        control_file_path (str): control file path.
        control_file_name (str): control file name.
    """

    if nlloc_bin_dir and nlloc_bin_dir not in os.environ.get("PATH", ""):
        os.environ["PATH"] = nlloc_bin_dir + os.pathsep + os.environ.get("PATH", "")
    script = os.getcwd()
    try:
        os.chdir(control_file_path)
        subprocess.run(["NLLoc", control_file_name], check=False)
    finally:
        os.chdir(script)
