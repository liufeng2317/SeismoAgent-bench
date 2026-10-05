#!/usr/bin/env python3
"""Run one local phase-picking model on a three-component NumPy waveform."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve()
ROOT = HERE.parents[1]
SOURCE = ROOT / "source"
WEIGHTS = ROOT / "runtime" / "weights"
sys.path.insert(0, str(SOURCE))


def load_model(name: str):
    import torch
    if name == "phasenet":
        from phase_picking.model.phasenet import PhaseNet
        folder, metadata_name, weights_name = "phasenet", "original.json.v2", "original.pt.v2"
        metadata = json.loads((WEIGHTS / folder / metadata_name).read_text())
        model = PhaseNet(**metadata["model_args"])
    elif name == "eqtransformer":
        from phase_picking.model.eqtransformer import EQTransformer
        folder, metadata_name, weights_name = "eqtransformer", "original_nonconservative.json.v1", "original_nonconservative.pt.v1"
        metadata = json.loads((WEIGHTS / folder / metadata_name).read_text())
        model = EQTransformer(**metadata["model_args"])
    elif name == "dpppickerp":
        from phase_picking.model.dpppickerp import DPPPicker
        folder, metadata_name, weights_name = "dpppickerp", "scedc.json", "scedc.pt"
        metadata = json.loads((WEIGHTS / folder / metadata_name).read_text())
        model = DPPPicker(mode="P")
    else:
        raise ValueError(f"Unsupported model: {name}")
    state = torch.load(WEIGHTS / folder / weights_name, map_location="cpu", weights_only=True)
    model.load_state_dict(state.get("state_dict", state), strict=True)
    model.eval()
    return model, metadata


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-npz", type=Path, required=True, help="NPZ containing data with shape (3, samples)")
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--model", choices=("phasenet", "eqtransformer", "dpppickerp"), default="phasenet")
    parser.add_argument("--sample-rate", type=float, required=True)
    args = parser.parse_args()
    input_path = args.input_npz.expanduser().resolve()
    output_dir = args.output_dir.expanduser().resolve()
    if args.sample_rate <= 0:
        raise ValueError("sample rate must be positive")
    with np.load(input_path) as loaded:
        if "data" not in loaded:
            raise ValueError("input NPZ must contain a 'data' array")
        data = np.asarray(loaded["data"], dtype=np.float32)
    if data.ndim != 2 or data.shape[0] != 3 or data.shape[1] < 10:
        raise ValueError(f"expected data shape (3, samples), got {data.shape}")
    if not np.isfinite(data).all():
        raise ValueError("input waveform contains non-finite values")
    output_dir.mkdir(parents=True, exist_ok=True)
    import torch
    torch.set_num_threads(1)
    model, metadata = load_model(args.model)
    with torch.inference_mode():
        probabilities = model(torch.from_numpy(data)[None])
    probabilities = probabilities.detach().cpu().numpy()
    np.savez_compressed(output_dir / "probabilities.npz", probabilities=probabilities, sample_rate=args.sample_rate)
    # Keep this summary model-agnostic: the case workflow decides thresholds and pick semantics.
    summary = {
        "status": "success",
        "model": args.model,
        "input": str(input_path),
        "input_shape": list(data.shape),
        "output_shape": list(probabilities.shape),
        "sample_rate_hz": args.sample_rate,
        "probability_channels": int(probabilities.shape[1]) if probabilities.ndim >= 2 else None,
        "model_metadata": metadata.get("docstring", "")[:240],
    }
    (output_dir / "run_result.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(json.dumps({"status": "failed", "error": str(exc)}, indent=2), file=sys.stderr)
        raise SystemExit(1)
