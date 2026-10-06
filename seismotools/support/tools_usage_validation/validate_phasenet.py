#!/usr/bin/env python3
"""Run one CPU PhaseNet forward pass with the bundled local weights."""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import numpy as np
from obspy import UTCDateTime, read

ROOT = Path(__file__).resolve().parents[3]
TOOL = ROOT / "seismotools" / "phase_picking"
DATA = Path(os.environ.get("RIDGECREST_DATA_ROOT", "/ai4earthafs/liufeng/ScienceDiscovery/SeismoAgentBench/data/2019_ridgecrest_california/waveforms"))
os.environ["SEISBENCH_CACHE_ROOT"] = str(TOOL / "cache")
sys.path.insert(0, str(TOOL / "source"))

import torch
from phase_picking.model.phasenet import PhaseNet


def main() -> None:
    torch.manual_seed(42)
    torch.set_num_threads(1)
    base = TOOL / "runtime" / "weights" / "phasenet"
    metadata = json.loads((base / "original.json.v2").read_text())
    model = PhaseNet(**metadata["model_args"])
    state = torch.load(base / "original.pt.v2", map_location="cpu", weights_only=True)
    model.load_state_dict(state.get("state_dict", state), strict=True)
    model.eval()
    # Three-component, 100 Hz, 30.01 s synthetic window.
    waveform = torch.randn(1, 3, 3001)
    with torch.inference_mode():
        probabilities = model(waveform)
    assert probabilities.shape == (1, 3, 3001)
    assert torch.isfinite(probabilities).all()
    assert np.allclose(probabilities.sum(dim=1).numpy(), 1.0, atol=1e-5)
    real_start = UTCDateTime("2019-07-05T00:00:00Z")
    real = []
    station_dir = DATA / "data" / "CI.CCC"
    for component in ("HHZ", "HHN", "HHE"):
        path = station_dir / f"CI.CCC..{component}__20190705T000000Z__20190706T000000Z.mseed"
        trace = read(str(path))[0].copy().trim(real_start, real_start + 30, pad=True, fill_value=0)
        if trace.stats.sampling_rate != 100:
            trace.resample(100)
        real.append(trace.data[:3001])
    real_waveform = torch.from_numpy(np.stack(real).astype("float32"))[None]
    with torch.inference_mode():
        real_prediction = model(real_waveform)
    assert real_waveform.shape == (1, 3, 3001)
    assert real_prediction.shape == (1, 3, 3001) and torch.isfinite(real_prediction).all()
    print(json.dumps({"status": "pass", "tool": "PhaseNet", "device": "cpu",
                      "smoke": {"input_shape": list(waveform.shape), "output_shape": list(probabilities.shape)},
                      "ridgecrest": {"station": "CI.CCC", "window_start": str(real_start),
                                     "input_shape": list(real_waveform.shape), "channels": ["HHZ", "HHN", "HHE"]}}, indent=2))


if __name__ == "__main__":
    main()
