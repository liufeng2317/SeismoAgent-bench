#!/usr/bin/env python3
"""Parse a minimal catalog differential-time input with native hypoDD."""
from __future__ import annotations

import json
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BIN = ROOT / "seismotools" / "hypodd" / "bin" / "hypoDD"


def main() -> None:
    with tempfile.TemporaryDirectory(prefix="hypodd-validation-") as tmp:
        work = Path(tmp)
        (work / "event.dat").write_text(
            "20190101 000001 35.0 -117.0 5.0 1.0 0.1 0.1 0.0 1001\n"
            "20190101 000002 35.01 -117.01 5.0 1.0 0.1 0.1 0.0 1002\n")
        (work / "station.dat").write_text("STA01 35.0 -117.0\n")
        (work / "dt.ct").write_text("# 1001 1002\nSTA01 0.0 1.0 1.0 P\n")
        (work / "hypoDD.inp").write_text(
            "missing.cc\ndt.ct\nevent.dat\nstation.dat\n"
            "hypoDD.loc\nhypoDD.reloc\nhypoDD.res\nhypoDD.stares\nhypoDD.srcpar\n"
            "2 3 1000\n0 1\n1 2 1\n"
            "1 0.0 1.0 1.0 100.0 1.0 1.0 1.0 100.0 10.0\n"
            "1 1.73\n0.0\n6.0\n0\n")
        result = subprocess.run([str(BIN), "hypoDD.inp"], cwd=work, text=True,
                                stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                check=True)
        assert (work / "hypoDD.loc").is_file()
        assert "# events =" in result.stdout and "# catalog P dtimes =" in result.stdout
        print(json.dumps({"status": "pass", "tool": "hypoDD",
                          "catalog_differential_times_parsed": True,
                          "relocation_started": True,
                          "note": "one-station synthetic input is intentionally underdetermined"}))


if __name__ == "__main__":
    main()
