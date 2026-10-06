#!/usr/bin/env python3
"""Run a bundled phase-picking model over a long waveform using overlapping windows."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

try:  # Support both package imports and direct script execution.
    from .run import load_model
except ImportError:  # pragma: no cover - exercised by the CLI entry point.
    from run import load_model


def window_starts(samples: int, window_samples: int, overlap_samples: int) -> list[int]:
    """Return window starts that cover every input sample exactly once or more."""
    if samples <= 0:
        raise ValueError("waveform must contain at least one sample")
    if window_samples <= 0 or overlap_samples < 0 or overlap_samples >= window_samples:
        raise ValueError("require window_samples > overlap_samples >= 0")
    if samples <= window_samples:
        return [0]
    step = window_samples - overlap_samples
    starts = list(range(0, samples - window_samples + 1, step))
    last = samples - window_samples
    if starts[-1] != last:
        starts.append(last)
    return starts


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-npz", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--model", choices=("phasenet", "eqtransformer", "dpppickerp"), default="phasenet")
    parser.add_argument("--sample-rate", type=float, required=True)
    parser.add_argument("--window-samples", type=int, default=3001)
    parser.add_argument("--overlap-samples", type=int, default=1500)
    args = parser.parse_args()

    with np.load(args.input_npz.expanduser().resolve()) as loaded:
        if "data" not in loaded:
            raise ValueError("input NPZ must contain a 'data' array")
        data = np.asarray(loaded["data"], dtype=np.float32)
    if data.ndim != 2 or data.shape[0] != 3 or data.shape[1] == 0:
        raise ValueError(f"expected data shape (3, samples), got {data.shape}")
    if not np.isfinite(data).all():
        raise ValueError("input waveform contains non-finite values")
    if args.sample_rate <= 0:
        raise ValueError("sample rate must be positive")

    import torch
    torch.set_num_threads(1)
    model, metadata = load_model(args.model)
    expected = getattr(model, "in_samples", args.window_samples)
    if args.window_samples != expected:
        raise ValueError(f"window-samples must equal the model window size {expected}")
    starts = window_starts(data.shape[1], args.window_samples, args.overlap_samples)
    output = np.zeros((1, 3, data.shape[1]), dtype=np.float64)
    counts = np.zeros(data.shape[1], dtype=np.float64)
    with torch.inference_mode():
        for start in starts:
            chunk = data[:, start:start + args.window_samples]
            valid = chunk.shape[1]
            if valid < args.window_samples:
                chunk = np.pad(chunk, ((0, 0), (0, args.window_samples - valid)), mode="edge")
            probabilities = model(torch.from_numpy(chunk)[None]).detach().cpu().numpy()
            end = min(start + args.window_samples, data.shape[1])
            output[:, :, start:end] += probabilities[:, :, :end - start]
            counts[start:end] += 1
    output /= counts[None, None, :]

    out = args.output_dir.expanduser().resolve()
    out.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(out / "probabilities.npz", probabilities=output.astype("float32"),
                        sample_rate=args.sample_rate, window_samples=args.window_samples,
                        overlap_samples=args.overlap_samples, window_count=len(starts))
    summary = {
        "status": "success", "model": args.model,
        "input_shape": list(data.shape), "output_shape": list(output.shape),
        "sample_rate_hz": args.sample_rate, "window_samples": args.window_samples,
        "overlap_samples": args.overlap_samples, "window_count": len(starts),
        "phase_labels": metadata.get("model_args", {}).get("phases"),
        "component_order": metadata.get("model_args", {}).get("component_order"),
    }
    (out / "run_result.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
