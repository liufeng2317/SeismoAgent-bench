#!/usr/bin/env python3
"""Run one CPU PhaseNet forward pass with the bundled local weights."""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
TOOL = ROOT / "seismotools" / "phase_picking"
os.environ["SEISBENCH_CACHE_ROOT"] = str(TOOL / "cache")
sys.path.insert(0, str(TOOL / "source"))

import torch
from phase_picking.model.phasenet import PhaseNet


def main() -> None:
    torch.manual_seed(42)
    torch.set_num_threads(1)
    base = TOOL / "weights" / "phasenet"
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
    print(json.dumps({"status": "pass", "tool": "PhaseNet", "device": "cpu",
                      "input_shape": list(waveform.shape),
                      "output_shape": list(probabilities.shape)}))


if __name__ == "__main__":
    main()
