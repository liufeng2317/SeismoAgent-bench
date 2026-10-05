#!/usr/bin/env python3
"""Parse a minimal catalog differential-time input with native hypoDD."""
from __future__ import annotations

import json
import os
import subprocess
import shutil
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BIN = ROOT / "seismotools" / "hypodd" / "bin" / "hypoDD"
EXPORT = Path(os.environ.get("RIDGECREST_EXPORT_ROOT", str(ROOT / "workflows/tasks/2019_ridgecrest_california/expert/export/01_baseline")))


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
    source = ROOT / "workflows/tasks/2019_ridgecrest_california/expert/export/06_full_catalog/53_native_double_difference/hypodd_ct"
    blocks, event_ids, current = [], set(), []
    with (source / "dt.ct").open() as handle:
        for line in handle:
            if line.startswith("#") and current:
                blocks.append(current)
                if len(blocks) == 2:
                    break
                current = []
            if not current and line.startswith("#"):
                event_ids.update(map(int, line.split()[1:3]))
            current.append(line)
    if len(blocks) < 2:
        blocks.append(current)
    event_lines = [line for line in (source / "event.dat").read_text().splitlines()
                   if int(line.split()[-1]) in event_ids]
    with tempfile.TemporaryDirectory(prefix="ridgecrest-hypodd-") as tmp:
        work = Path(tmp)
        (work / "event.dat").write_text("\n".join(event_lines) + "\n")
        shutil.copy2(source / "station.dat", work / "station.dat")
        (work / "dt.ct").write_text("".join("".join(block) for block in blocks))
        (work / "dt.cc").write_text("")
        shutil.copy2(source / "hypoDD.inp", work / "hypoDD.inp")
        real_result = subprocess.run([str(BIN), "hypoDD.inp"], cwd=work, text=True,
                                     stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                     check=True)
        assert (work / "hypoDD.loc").is_file() and "# events =" in real_result.stdout
    print(json.dumps({"status": "pass", "tool": "hypoDD",
                      "smoke": {"catalog_differential_times_parsed": True, "relocation_started": True,
                                 "note": "one-station synthetic input is intentionally underdetermined"},
                      "ridgecrest": {"event_pairs": len(blocks), "events_parsed": len(event_lines),
                                     "mode": "CT", "note": "bounded replay of real differential-time input"}}))


if __name__ == "__main__":
    main()
