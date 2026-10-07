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

MODEL_CHANNELS = {"phasenet": 3, "eqtransformer": 3, "dpppickerp": 1}


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


def load_config(path: Path | None) -> dict:
    if path is None:
        return {}
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("phase-picking config must be a JSON object")
    return value


def normalize_output(output):
    """Convert model-specific outputs to (batch, channels, samples)."""
    import torch
    if isinstance(output, (tuple, list)):
        output = torch.stack(list(output), dim=1)
    elif output.ndim == 2:
        output = output[:, None, :]
    return output


def metadata_labels(metadata: dict, model_name: str):
    if model_name == "dpppickerp":
        return ["P"]
    return metadata.get("phases") or metadata.get("model_args", {}).get("phases")


def metadata_components(metadata: dict, model_name: str):
    if model_name == "dpppickerp":
        return "Z"
    return metadata.get("component_order") or metadata.get("model_args", {}).get("component_order")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-npz", type=Path, required=True, help="NPZ containing data with shape (channels, samples)")
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--model", choices=tuple(MODEL_CHANNELS), default=None)
    parser.add_argument("--sample-rate", type=float, default=None)
    parser.add_argument("--config", type=Path, default=None, help="Optional JSON settings")
    parser.add_argument("--threads", type=int, default=None, help="CPU threads for model inference")
    parser.add_argument("--overwrite", action="store_true", help="Replace existing interface outputs")
    args = parser.parse_args()
    input_path = args.input_npz.expanduser().resolve()
    output_dir = args.output_dir.expanduser().resolve()
    result_path = output_dir / "run_result.json"
    try:
        settings = load_config(args.config)
        model_name = args.model or settings.get("model", "phasenet")
        sample_rate = args.sample_rate if args.sample_rate is not None else settings.get("sample_rate_hz")
        threads = args.threads if args.threads is not None else settings.get("threads", 1)
        if model_name not in MODEL_CHANNELS:
            raise ValueError(f"unsupported model: {model_name}")
        if sample_rate is None or float(sample_rate) <= 0:
            raise ValueError("sample rate must be positive")
        if int(threads) <= 0:
            raise ValueError("threads must be positive")
        with np.load(input_path) as loaded:
            if "data" not in loaded:
                raise ValueError("input NPZ must contain a 'data' array")
            data = np.asarray(loaded["data"], dtype=np.float32)
        expected_channels = MODEL_CHANNELS[model_name]
        if data.ndim != 2 or data.shape[0] != expected_channels or data.shape[1] < 10:
            raise ValueError(f"{model_name} expects data shape ({expected_channels}, samples), got {data.shape}")
        if not np.isfinite(data).all():
            raise ValueError("input waveform contains non-finite values")
        model, metadata = load_model(model_name)
        expected_samples = getattr(model, "in_samples", None)
        if expected_samples is not None and data.shape[1] != expected_samples:
            raise ValueError(
                f"{model_name} requires exactly {expected_samples} samples per inference window; "
                f"got {data.shape[1]}. Use run_continuous.py for longer waveforms."
            )
        output_dir.mkdir(parents=True, exist_ok=True)
        if not args.overwrite and any(output_dir.iterdir()):
            raise ValueError(f"output directory is not empty; choose a new directory or use --overwrite: {output_dir}")
        import torch
        torch.set_num_threads(int(threads))
        with torch.inference_mode():
            probabilities = normalize_output(model(torch.from_numpy(data)[None]))
        probabilities = probabilities.detach().cpu().numpy()
        np.savez_compressed(output_dir / "probabilities.npz", probabilities=probabilities, sample_rate=float(sample_rate))
        summary = {
            "status": "success", "interface_version": 2, "model": model_name,
            "inputs": {"waveform": str(input_path)}, "input_shape": list(data.shape),
            "output_shape": list(probabilities.shape), "sample_rate_hz": float(sample_rate),
            "threads": int(threads), "probability_channels": int(probabilities.shape[1]) if probabilities.ndim >= 2 else None,
            "phase_labels": metadata_labels(metadata, model_name),
            "component_order": metadata_components(metadata, model_name),
            "window_samples": expected_samples, "model_metadata": metadata.get("docstring", "")[:240],
            "outputs": {"probabilities": str(output_dir / "probabilities.npz"), "run_result": str(result_path)},
        }
        result_path.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(summary, indent=2))
        return 0
    except Exception as exc:
        summary = {"status": "failed", "interface_version": 2, "input": str(input_path), "output_dir": str(output_dir), "error": str(exc)}
        if args.overwrite or not result_path.exists():
            output_dir.mkdir(parents=True, exist_ok=True)
            result_path.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(summary, indent=2), file=sys.stderr)
        return 1


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(json.dumps({"status": "failed", "error": str(exc)}, indent=2), file=sys.stderr)
        raise SystemExit(1)
