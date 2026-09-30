"""Small waveform-driven baseline for the Ridgecrest catalog task.

The baseline reads the run-local read-only ``input/waveforms`` directory,
ranks non-overlapping amplitude windows, and writes candidate events. It is an
infrastructure baseline, not a phase picker or a scientific locator.
"""

from __future__ import annotations

from datetime import timezone
import json
import os
from pathlib import Path

import numpy as np
from obspy import UTCDateTime, read, read_inventory

WINDOW_SECONDS = 10.0
SEPARATION_SECONDS = 30.0
MAX_EVENTS = 3


def _input_root() -> Path:
    return Path(os.environ["BENCH_INPUT"]) / "waveforms"


def _station_coordinates(inventory, network: str, station: str) -> tuple[float, float]:
    selected = inventory.select(network=network, station=station)
    for net in selected:
        for sta in net:
            return float(sta.latitude), float(sta.longitude)
    return float("nan"), float("nan")


def _candidates(data_root: Path) -> list[tuple[UTCDateTime, float, str, str]]:
    inventory = read_inventory(str(data_root / "stations" / "earthscope.stationxml"), format="STATIONXML")
    windows: list[tuple[UTCDateTime, float, str, str]] = []
    for source in sorted((data_root / "data").rglob("*.mseed")):
        for trace in read(str(source)):
            if not str(trace.stats.channel).endswith("Z"):
                continue
            sampling_rate = float(trace.stats.sampling_rate)
            width = max(1, int(round(WINDOW_SECONDS * sampling_rate)))
            values = np.asarray(trace.data, dtype=np.float64)
            values -= np.nanmedian(values)
            count = len(values) // width
            if count == 0:
                continue
            scores = np.sqrt(np.nanmean(values[:count * width].reshape(count, width) ** 2, axis=1))
            for index in np.argsort(scores)[-MAX_EVENTS:]:
                windows.append((trace.stats.starttime + (index + 0.5) * WINDOW_SECONDS,
                                float(scores[index]), str(trace.stats.network), str(trace.stats.station)))
    windows.sort(key=lambda item: (-item[1], item[0]))
    selected = []
    for candidate in windows:
        if all(abs(float(candidate[0] - previous[0])) >= SEPARATION_SECONDS for previous in selected):
            selected.append(candidate)
        if len(selected) == MAX_EVENTS:
            break
    return sorted(selected, key=lambda item: item[0])


def main() -> None:
    data_root = _input_root()
    inventory = read_inventory(str(data_root / "stations" / "earthscope.stationxml"), format="STATIONXML")
    events = []
    for index, (origin, score, network, station) in enumerate(_candidates(data_root), start=1):
        latitude, longitude = _station_coordinates(inventory, network, station)
        events.append({
            "event_id": f"waveform-baseline-{index:03d}",
            "origin_time": origin.datetime.replace(tzinfo=timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z"),
            "latitude": latitude, "longitude": longitude, "depth_km": 0.0,
            "location_method": "station-amplitude-baseline", "picks": [],
            "magnitude": float(np.log10(max(score, 1.0))), "magnitude_type": "log10-rms-proxy",
        })
    output = Path(os.environ["BENCH_OUTPUT"])
    output.mkdir(parents=True, exist_ok=True)
    catalog = {"schema_version": 1, "catalog_id": "ridgecrest-waveform-baseline-v1",
               "description": "Waveform-driven infrastructure baseline; not a scientific locator.",
               "events": events}
    (output / "catalog.json").write_text(json.dumps(catalog, indent=2, sort_keys=True) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
