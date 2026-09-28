"""Small waveform-driven baseline for the Ridgecrest smoke task.

The agent reads MiniSEED through ObsPy, ranks non-overlapping ten-second
vertical-component amplitude windows, and writes those windows as candidate
events at the recording station.  This is deliberately a data-access and
event-candidate baseline; it is not a phase picker or an earthquake locator.
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


def _manifest() -> dict:
    return json.loads(Path(os.environ["BENCH_INPUT_MANIFEST"]).read_text(encoding="utf-8"))


def _station_coordinates(entries: list[dict], stationxml: Path) -> tuple[float, float]:
    entry = next(item for item in entries if item.get("kind") == "waveform")
    network, station = entry["network"], entry["station"]
    inventory = read_inventory(str(stationxml), format="STATIONXML")
    selected = inventory.select(network=network, station=station)
    for net in selected:
        for sta in net:
            return float(sta.latitude), float(sta.longitude)
    raise RuntimeError(f"station {network}.{station} is absent from StationXML")


def _candidates(entries: list[dict]) -> list[tuple[UTCDateTime, float]]:
    vertical = [item for item in entries if item.get("kind") == "waveform"
                and str(item.get("channel", "")).endswith("Z")]
    if not vertical:
        vertical = [item for item in entries if item.get("kind") == "waveform"]
    windows: list[tuple[UTCDateTime, float]] = []
    for entry in vertical:
        stream = read(entry["path"])
        for trace in stream:
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
                                float(scores[index])))
    windows.sort(key=lambda item: (-item[1], item[0]))
    selected: list[tuple[UTCDateTime, float]] = []
    for candidate in windows:
        if all(abs(float(candidate[0] - previous[0])) >= SEPARATION_SECONDS
               for previous in selected):
            selected.append(candidate)
        if len(selected) == MAX_EVENTS:
            break
    return sorted(selected, key=lambda item: item[0])


def main() -> None:
    manifest = _manifest()
    entries = manifest["entries"]
    stationxml = Path(next(item["path"] for item in entries if item.get("kind") == "stationxml"))
    latitude, longitude = _station_coordinates(entries, stationxml)
    candidates = _candidates(entries)
    events = []
    for index, (origin, score) in enumerate(candidates, start=1):
        origin_datetime = origin.datetime.replace(tzinfo=timezone.utc)
        events.append({
            "event_id": f"waveform-baseline-{index:03d}",
            "origin_time": origin_datetime.isoformat(timespec="milliseconds").replace("+00:00", "Z"),
            "latitude": latitude,
            "longitude": longitude,
            "depth_km": 0.0,
            "location_method": "station-amplitude-baseline",
            "picks": [],
            "magnitude": float(np.log10(max(score, 1.0))),
            "magnitude_type": "log10-rms-proxy",
        })
    output = Path(os.environ["BENCH_OUTPUT"])
    output.mkdir(parents=True, exist_ok=True)
    catalog = {
        "schema_version": 1,
        "catalog_id": "ridgecrest-waveform-baseline-v1",
        "description": (
            "Waveform-driven infrastructure baseline using vertical-component "
            "ten-second amplitude windows; not a scientific locator."
        ),
        "events": events,
    }
    (output / "catalog.json").write_text(
        json.dumps(catalog, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


if __name__ == "__main__":
    main()
