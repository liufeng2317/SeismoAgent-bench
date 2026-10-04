#!/usr/bin/env python3
"""Generate a tiny NonLinLoc grid and run the three native stages."""
from __future__ import annotations

import json
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BIN = ROOT / "seismotools" / "nonlinloc" / "bin"


def run(binary: Path, control: Path, cwd: Path) -> str:
    result = subprocess.run([str(binary), control.name], cwd=cwd,
                            text=True, stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT, check=True)
    return result.stdout


def main() -> None:
    with tempfile.TemporaryDirectory(prefix="nll-validation-") as tmp:
        work = Path(tmp)
        (work / "vg.in").write_text("""CONTROL 1 54321
TRANS NONE
VGOUT model
VGGRID 2 5 5 0 0 0 1 1 1 SLOW_LEN
LAYER 0 5.0 0 3.0 0 2.7 0
VGTYPE P
""")
        (work / "gt.in").write_text("""CONTROL 1 54321
TRANS NONE
GTFILES model time P
GTMODE GRID2D ANGLES_NO
GT_PLFD 1.e-3 0
GTSRCE S0001 XYZ 0 0 0 0
""")
        (work / "obs").write_text("S0001 ? ? ? P ? 19700101 0000 1.0000 GAU 0.1 -1 -1 -1\n!END_EVENT\n!END_FILE\n")
        (work / "nll.in").write_text("""CONTROL 1 54321
TRANS NONE
GTSRCE S0001 XYZ 0 0 0 0
LOCFILES obs NLLOC_OBS ./time solution
LOCSEARCH OCT 1 1 1 0.1 100 10 0 0
LOCGRID 5 5 5 0 0 0 1 1 1 PROB_DENSITY SAVE
LOCMETH EDT_OT_WT 9999 2 -1 3 0 0 0 0 0
LOCHYPOUT SAVE_NLLOC_ALL
LOCGAU 0.1 0
LOCQUAL2ERR 0.1 0.2 0.5 1 999
LOCPHASEID P P
""")
        run(BIN / "Vel2Grid", work / "vg.in", work)
        run(BIN / "Grid2Time", work / "gt.in", work)
        nll_output = run(BIN / "NLLoc", work / "nll.in", work)
        assert (work / "model.P.mod.buf").is_file()
        assert (work / "time.P.S0001.time.buf").is_file()
        assert "events read" in nll_output
        print(json.dumps({"status": "pass", "tool": "NonLinLoc",
                          "velocity_grid": True, "travel_time_grid": True,
                          "locator_started": True,
                          "note": "one-station synthetic input is intentionally underdetermined"}))


if __name__ == "__main__":
    main()
