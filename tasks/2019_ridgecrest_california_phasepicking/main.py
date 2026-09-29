"""Deterministic folder-based preprocessing and phase-picking baseline."""

from __future__ import annotations

import csv
from datetime import timezone
import json
import os
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from obspy import UTCDateTime, read, read_inventory
from obspy.signal.trigger import classic_sta_lta, trigger_onset


START = UTCDateTime("2019-07-05T00:00:00Z")
END = UTCDateTime("2019-07-06T00:00:00Z")


def _load_manifest() -> dict:
    path = Path(os.environ["BENCH_INPUT_MANIFEST"])
    return json.loads(path.read_text(encoding="utf-8"))


def _inputs(manifest: dict) -> tuple[list[Path], Path]:
    waveform = next(item for item in manifest["entries"] if item["data_type"] == "waveform")
    station = next(item for item in manifest["entries"] if item["data_type"] == "station_metadata")
    root = Path(waveform["path"])
    files = sorted(root.rglob("*.mseed")) if root.is_dir() else [root]
    selected = [path for path in files if "20190705T000000Z__20190706T000000Z" in path.name]
    if not selected:
        selected = files
    return selected, Path(station["path"])


def _station_coordinates(stationxml: Path) -> dict[str, tuple[float, float]]:
    inventory = read_inventory(str(stationxml), format="STATIONXML")
    result = {}
    for network in inventory:
        for station in network:
            result[f"{network.code}.{station.code}"] = (float(station.latitude), float(station.longitude))
    return result


def _pick_rows(path: Path, output: list[dict], summaries: list[dict], example: dict | None) -> dict | None:
    stream = read(str(path))
    representative = example
    for trace in stream:
        trace.detrend("demean")
        sampling_rate = float(trace.stats.sampling_rate)
        nsta = max(1, int(round(sampling_rate)))
        nlta = max(nsta + 1, int(round(10 * sampling_rate)))
        characteristic = classic_sta_lta(trace.data, nsta, nlta)
        triggers = trigger_onset(characteristic, 3.0, 1.5)
        summaries.append({
            "trace_id": trace.id,
            "source": str(path),
            "sampling_rate_hz": sampling_rate,
            "npts": int(trace.stats.npts),
            "operations": ["demean", "classic_sta_lta"],
            "sta_seconds": 1.0,
            "lta_seconds": 10.0,
            "trigger_on": 3.0,
            "trigger_off": 1.5,
            "trigger_count": len(triggers),
        })
        for index, (start, end) in enumerate(triggers[:20]):
            p = trace.stats.starttime + start / sampling_rate
            s = trace.stats.starttime + end / sampling_rate
            for phase, arrival in (("P", p), ("S", s)):
                arrival_datetime = arrival.datetime.replace(tzinfo=timezone.utc)
                output.append({
                    "station_id": f"{trace.stats.network}.{trace.stats.station}",
                    "channel": trace.stats.channel,
                    "phase": phase,
                    "arrival_time": arrival_datetime.isoformat(timespec="milliseconds").replace("+00:00", "Z"),
                    "confidence": 0.5,
                    "method": "classic_sta_lta_baseline",
                    "source_file": str(path),
                })
        if representative is None:
            seconds = min(len(trace.data) / sampling_rate, 60.0)
            count = max(1, int(seconds * sampling_rate))
            representative = {"trace": trace.copy(), "characteristic": characteristic, "count": count}
    return representative


def _figure(output: Path, coordinates: dict[str, tuple[float, float]], example: dict | None) -> None:
    figure, axes = plt.subplots(1, 2, figsize=(12, 4.5), constrained_layout=True)
    if coordinates:
        latitudes, longitudes = zip(*coordinates.values())
        axes[0].scatter(longitudes, latitudes, s=14, color="#2b6cb0", alpha=0.8)
    axes[0].set_title("Stations in input metadata")
    axes[0].set_xlabel("Longitude (°)")
    axes[0].set_ylabel("Latitude (°)")
    axes[0].grid(alpha=0.25)
    if example is not None:
        trace = example["trace"]
        count = example["count"]
        times = np.arange(count) / float(trace.stats.sampling_rate)
        values = np.asarray(trace.data[:count], dtype=float)
        values -= np.nanmedian(values)
        axes[1].plot(times, values, color="#222222", linewidth=0.5)
        axes[1].set_title(f"Preprocessed example: {trace.id}")
        axes[1].set_xlabel("Time since trace start (s)")
        axes[1].set_ylabel("Demeaned amplitude")
        axes[1].grid(alpha=0.25)
        trigger_axis = axes[1].twinx()
        trigger_axis.plot(times, example["characteristic"][:count], color="#c53030", linewidth=0.6, alpha=0.75)
        trigger_axis.set_ylabel("STA/LTA", color="#c53030")
    figure.savefig(output / "preprocessing_figure.png", dpi=180)
    plt.close(figure)


def main() -> None:
    manifest = _load_manifest()
    files, stationxml = _inputs(manifest)
    coordinates = _station_coordinates(stationxml)
    picks: list[dict] = []
    summaries: list[dict] = []
    example = None
    for path in files:
        example = _pick_rows(path, picks, summaries, example)
    output = Path(os.environ["BENCH_OUTPUT"])
    output.mkdir(parents=True, exist_ok=True)
    plan = {
        "schema_version": 1,
        "time_window": {"start": START.isoformat(), "end": END.isoformat()},
        "steps": ["discover date-matched waveform files", "preprocess traces", "pick P and S arrivals", "inspect outputs"],
        "method": "demean plus classic STA/LTA trigger; S is represented by trigger end time in this baseline",
        "input_files": len(files),
    }
    (output / "task_plan.json").write_text(json.dumps(plan, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (output / "pick_examples.json").write_text(json.dumps({"schema_version": 1, "examples": picks[:10]}, indent=2) + "\n", encoding="utf-8")
    with (output / "picks.csv").open("w", newline="", encoding="utf-8") as handle:
        fields = ["station_id", "channel", "phase", "arrival_time", "confidence", "method", "source_file"]
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(picks)
    _figure(output, coordinates, example)


if __name__ == "__main__":
    main()
