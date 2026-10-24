#!/usr/bin/env python3
"""Convert the upstream MatchLocate2 Hi-net example into the interface dataset layout.

The upstream archive is treated as untrusted data: it is extracted into a new,
empty directory, only SAC and text files are read, nothing in it is executed,
and member paths are checked before extraction. The resulting dataset links
to the extracted SAC files and reproduces the upstream PROC_MatchLocate.pl
choices: single phase S, search 0.05/0.05/0 deg/deg/km at 0.005/0.005/1,
window 4/1/3 s, detection 0.0/12.0 with 6 s separation, merge 0.30/12.0/6.0.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
import zipfile
from pathlib import Path

HERE = Path(__file__).resolve()
sys.path.insert(0, str(HERE.parents[2] / "runtime" / "python" / "MatchLocatepy"))
from matchlocate_runner.dataset import ChannelPhase, Template, write_channels, write_templates  # noqa: E402

ARCHIVE_SHA256 = "543b6bc9052403ca63a286e6b06c2c806b4872205f8a2be0cb75d6a4e331ad19"
PREFIX = "MatchLocate2-master/"
CONFIG = {
    "search": {"units": "deg", "half_lat_deg": 0.05, "half_lon_deg": 0.05, "half_depth_km": 0.0,
               "step_lat_deg": 0.005, "step_lon_deg": 0.005, "step_depth_km": 1.0},
    "window": {"length_s": 4.0, "before_s": 1.0, "after_s": 3.0},
    "detection": {"cc_threshold": 0.0, "mad_threshold": 12.0, "min_separation_s": 6.0},
    "merge": {"engine": "python", "cc_threshold": 0.30, "mad_threshold": 12.0, "min_separation_s": 6.0},
    "min_channels": 1,
    "output_mode": 0,
}


def safe_extract(archive: Path, members_prefix: str, destination: Path) -> None:
    with zipfile.ZipFile(archive) as zf:
        for info in zf.infolist():
            name = info.filename
            if not name.startswith(members_prefix):
                continue
            target = (destination / name).resolve()
            if name.startswith("/") or ".." in Path(name).parts or not str(target).startswith(str(destination.resolve())):
                raise ValueError(f"unsafe archive member: {name}")
            if (info.external_attr >> 16) & 0o170000 == 0o120000:
                continue                                  # skip symlinks
            zf.extract(info, destination)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", type=Path, required=True, help="MatchLocate2-master.zip")
    parser.add_argument("--data-dir", type=Path, required=True, help="new or empty extraction directory")
    parser.add_argument("--dataset-dir", type=Path, required=True, help="new or empty dataset directory")
    args = parser.parse_args()

    digest = hashlib.sha256(args.archive.read_bytes()).hexdigest()
    if digest != ARCHIVE_SHA256:
        raise SystemExit(f"archive sha256 {digest} != expected {ARCHIVE_SHA256}")
    for folder in (args.data_dir, args.dataset_dir):
        if folder.exists() and any(folder.iterdir()):
            raise SystemExit(f"{folder} must be new or empty")
        folder.mkdir(parents=True, exist_ok=True)
    data = args.data_dir.resolve()
    safe_extract(args.archive, PREFIX + "example/", data / "archive")
    example = data / "archive" / PREFIX / "example"
    raw_templates = data / "templates"
    raw_templates.mkdir()
    safe_extract(example / "Template" / "waveforms-of-templates.zip", "", raw_templates)

    dataset = args.dataset_dir.resolve()
    day = "20120902"
    trace_dir = example / "Trace" / day
    (dataset / "continuous" / day).mkdir(parents=True)
    for trace in sorted(trace_dir.glob("N.*")):
        (dataset / "continuous" / day / f"{trace.name}.sac").symlink_to(trace)

    templates, rows = [], []
    for line in (example / "catalog.dat").read_text().splitlines():
        date, clock, lat, lon, depth, _m, mag = line.split()
        name = date.replace("/", "") + clock.replace(":", "")
        y, mo, d = date.split("/")
        templates.append(Template(name, f"{y}-{mo}-{d}T{clock}Z", float(lat), float(lon), float(depth), float(mag)))
        folder = dataset / "templates" / name
        folder.mkdir(parents=True)
        for spec in (example / "Template" / "INPUT" / name).read_text().splitlines():
            station, _t, slowness, mark, phase = spec.split()
            source = raw_templates / name / station
            if phase != "S" or not source.is_file() or not (trace_dir / station).is_file():
                continue
            link = folder / f"{station}.sac"
            if not link.exists():
                link.symlink_to(source)
            horizontal, vertical = slowness.split("/")
            rows.append(ChannelPhase(name, station, phase, int(mark), float(horizontal), float(vertical)))
    write_templates(dataset / "templates.csv", templates)
    write_channels(dataset / "channels.csv", rows)
    (dataset / "config.json").write_text(json.dumps(CONFIG, indent=2) + "\n")
    print(json.dumps({"dataset": str(dataset), "templates": len(templates), "channel_rows": len(rows),
                      "continuous_files": len(list((dataset / "continuous" / day).glob("*.sac")))}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
