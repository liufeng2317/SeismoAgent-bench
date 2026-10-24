#!/usr/bin/env python3
"""Convert the upstream ``example_CCdistribution`` into the interface dataset layout.

Upstream setup: template 2012-09-02 03:24:13.12 (M 3.0) scans the waveforms of
the 03:33:51.61 event (M 2.3), both resampled to 1,000 Hz, on a 201 x 201
horizontal grid (+-0.01 deg at 0.0001 deg, depth fixed), S phase only, window
4/1/3 s, N(*MAD) >= 12, with ``-O3`` writing the stacked CC of every node and
sample above threshold (``CCdistribution.out``) for location-resolution plots.

The "continuous" segment is the 03:33:51.61 event's own cut (SAC reference =
its origin), so this example also exercises segments that are not days.
The archive is untrusted data: verified, extracted into a new empty
directory with member paths checked, nothing executed.
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
sys.path.insert(0, str(HERE.parents[1] / "workflow"))
from matchlocate_runner.dataset import ChannelPhase, Template, write_channels, write_templates  # noqa: E402
from prepare_upstream_example import ARCHIVE_SHA256, PREFIX, safe_extract  # noqa: E402

TEMPLATE = "20120902032413.12"
SEGMENT = "20120902033351.61"
CONFIG = {
    "search": {"units": "deg", "half_lat_deg": 0.01, "half_lon_deg": 0.01, "half_depth_km": 0.0,
               "step_lat_deg": 0.0001, "step_lon_deg": 0.0001, "step_depth_km": 1.0},
    "window": {"length_s": 4.0, "before_s": 1.0, "after_s": 3.0},
    "detection": {"cc_threshold": 0.0, "mad_threshold": 12.0, "min_separation_s": 6.0},
    "merge": {"engine": "python", "cc_threshold": 0.0, "mad_threshold": 12.0, "min_separation_s": 6.0},
    "min_channels": 1,
    "output_mode": 3,
}


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
    safe_extract(args.archive, PREFIX + "example_CCdistribution/", data / "archive")
    example = data / "archive" / PREFIX / "example_CCdistribution"
    (data / "trace").mkdir()
    safe_extract(example / "Trace" / "20120902.zip", "", data / "trace")
    traces = data / "trace" / "20120902"

    dataset = args.dataset_dir.resolve()
    (dataset / "continuous" / SEGMENT).mkdir(parents=True)
    (dataset / "templates" / TEMPLATE).mkdir(parents=True)
    rows = []
    for spec in (example / "Template" / "INPUT" / TEMPLATE).read_text().splitlines():
        station, _t, slowness, mark, phase = spec.split()
        source = example / "Template" / TEMPLATE / station
        if phase != "S" or not source.is_file() or not (traces / station).is_file():
            continue
        template_link = dataset / "templates" / TEMPLATE / f"{station}.sac"
        if not template_link.exists():
            template_link.symlink_to(source)
            (dataset / "continuous" / SEGMENT / f"{station}.sac").symlink_to(traces / station)
        horizontal, vertical = slowness.split("/")
        rows.append(ChannelPhase(TEMPLATE, station, phase, int(mark), float(horizontal), float(vertical)))
    date, clock, lat, lon, depth, _m, mag = (example / "catalog.dat").read_text().split()
    y, mo, d = date.split("/")
    write_templates(dataset / "templates.csv",
                    [Template(TEMPLATE, f"{y}-{mo}-{d}T{clock}Z", float(lat), float(lon), float(depth), float(mag))])
    write_channels(dataset / "channels.csv", rows)
    (dataset / "config.json").write_text(json.dumps(CONFIG, indent=2) + "\n")
    print(json.dumps({"dataset": str(dataset), "template": TEMPLATE, "segment": SEGMENT, "channel_rows": len(rows),
                      "upstream_ccdistribution": str(example / "CCdistribution.out")}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
