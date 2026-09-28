"""Minimal ObsPy preprocessing and phase-picking baseline."""

from __future__ import annotations

from datetime import timezone
import json
import os
from pathlib import Path

from obspy import read
from obspy.signal.trigger import classic_sta_lta, trigger_onset


def _load_manifest() -> dict:
    path = Path(os.environ["BENCH_INPUT_MANIFEST"])
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> None:
    manifest = _load_manifest()
    waveform_entries = [entry for entry in manifest["entries"] if entry["data_type"] == "waveform"]
    preprocessing = []
    picks = []
    for entry in waveform_entries:
        stream = read(entry["path"])
        for trace in stream:
            trace.detrend("demean")
            sampling_rate = float(trace.stats.sampling_rate)
            nsta = max(1, int(round(sampling_rate)))
            nlta = max(nsta + 1, int(round(10 * sampling_rate)))
            cft = classic_sta_lta(trace.data, nsta, nlta)
            triggers = trigger_onset(cft, 3.0, 1.5)
            preprocessing.append({
                "input_id": entry["id"],
                "trace_id": trace.id,
                "sampling_rate_hz": sampling_rate,
                "npts": int(trace.stats.npts),
                "operations": ["demean", "classic_sta_lta"],
                "sta_seconds": 1.0,
                "lta_seconds": 10.0,
                "trigger_on": 3.0,
                "trigger_off": 1.5,
                "trigger_count": len(triggers),
            })
            for index, (start, _end) in enumerate(triggers[:10]):
                arrival = trace.stats.starttime + start / sampling_rate
                arrival_datetime = arrival.datetime.replace(tzinfo=timezone.utc)
                picks.append({
                    "pick_id": f"{entry['id']}-{trace.stats.channel}-P-{index:04d}",
                    "station_id": f"{trace.stats.network}.{trace.stats.station}",
                    "channel": trace.stats.channel,
                    "phase": "P",
                    "arrival_time": arrival_datetime.isoformat(timespec="milliseconds").replace("+00:00", "Z"),
                    "probability": 0.5,
                    "method": "classic_sta_lta_baseline",
                })
    output = Path(os.environ["BENCH_OUTPUT"])
    output.mkdir(parents=True, exist_ok=True)
    (output / "preprocessing.json").write_text(
        json.dumps({"schema_version": 1, "traces": preprocessing}, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (output / "picks.json").write_text(
        json.dumps({"schema_version": 1, "picks": picks}, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
