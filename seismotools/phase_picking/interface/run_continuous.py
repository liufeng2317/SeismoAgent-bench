#!/usr/bin/env python3
"""Run a bundled phase-picking model over a long waveform using overlapping windows."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

try:  # Support both package imports and direct script execution.
    from .run import load_model, metadata_components, metadata_labels, normalize_output
except ImportError:  # pragma: no cover - exercised by the CLI entry point.
    from run import load_model, metadata_components, metadata_labels, normalize_output

MODEL_CHANNELS = {"phasenet": 3, "eqtransformer": 3, "dpppickerp": 1}


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
    parser.add_argument("--model", choices=tuple(MODEL_CHANNELS), default=None)
    parser.add_argument("--sample-rate", type=float, default=None)
    parser.add_argument("--window-samples", type=int, default=None)
    parser.add_argument("--overlap-samples", type=int, default=None)
    parser.add_argument("--config", type=Path, default=None, help="Optional JSON settings")
    parser.add_argument("--threads", type=int, default=None)
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()
    input_path = args.input_npz.expanduser().resolve()
    out = args.output_dir.expanduser().resolve()
    result_path = out / "run_result.json"
    try:
        settings = {}
        if args.config:
            settings = json.loads(args.config.read_text(encoding="utf-8"))
            if not isinstance(settings, dict):
                raise ValueError("phase-picking config must be a JSON object")
        model_name = args.model or settings.get("model", "phasenet")
        sample_rate = args.sample_rate if args.sample_rate is not None else settings.get("sample_rate_hz")
        if sample_rate is None or float(sample_rate) <= 0:
            raise ValueError("sample rate must be positive")
        threads = args.threads if args.threads is not None else settings.get("threads", 1)
        if int(threads) <= 0:
            raise ValueError("threads must be positive")
        with np.load(input_path) as loaded:
            if "data" not in loaded:
                raise ValueError("input NPZ must contain a 'data' array")
            data = np.asarray(loaded["data"], dtype=np.float32)
        expected_channels = MODEL_CHANNELS.get(model_name)
        if expected_channels is None:
            raise ValueError(f"unsupported model: {model_name}")
        if data.ndim != 2 or data.shape[0] != expected_channels or data.shape[1] == 0:
            raise ValueError(f"{model_name} expects data shape ({expected_channels}, samples), got {data.shape}")
        if not np.isfinite(data).all():
            raise ValueError("input waveform contains non-finite values")
        import torch
        torch.set_num_threads(int(threads))
        model, metadata = load_model(model_name)
        expected = getattr(model, "in_samples", None)
        window_samples = args.window_samples if args.window_samples is not None else settings.get("window_samples", expected or 3001)
        overlap_samples = args.overlap_samples if args.overlap_samples is not None else settings.get("overlap_samples", window_samples // 2)
        if expected is not None and window_samples != expected:
            raise ValueError(f"window-samples must equal the model window size {expected}")
        starts = window_starts(data.shape[1], int(window_samples), int(overlap_samples))
        output = None
        counts = np.zeros(data.shape[1], dtype=np.float64)
        with torch.inference_mode():
            for start in starts:
                chunk = data[:, start:start + window_samples]
                valid = chunk.shape[1]
                if valid < window_samples:
                    chunk = np.pad(chunk, ((0, 0), (0, window_samples - valid)), mode="edge")
                probabilities = normalize_output(model(torch.from_numpy(chunk)[None])).detach().cpu().numpy()
                if output is None:
                    output = np.zeros((probabilities.shape[0], probabilities.shape[1], data.shape[1]), dtype=np.float64)
                end = min(start + window_samples, data.shape[1])
                output[:, :, start:end] += probabilities[:, :, :end - start]
                counts[start:end] += 1
        output /= counts[None, None, :]
        out.mkdir(parents=True, exist_ok=True)
        if not args.overwrite and any(out.iterdir()):
            raise ValueError(f"output directory is not empty; choose a new directory or use --overwrite: {out}")
        np.savez_compressed(out / "probabilities.npz", probabilities=output.astype("float32"),
                            sample_rate=float(sample_rate), window_samples=int(window_samples),
                            overlap_samples=int(overlap_samples), window_count=len(starts))
        summary = {
            "status": "success", "interface_version": 2, "model": model_name,
            "inputs": {"waveform": str(input_path)}, "input_shape": list(data.shape), "output_shape": list(output.shape),
            "sample_rate_hz": float(sample_rate), "threads": int(threads), "window_samples": int(window_samples),
            "overlap_samples": int(overlap_samples), "window_count": len(starts),
            "phase_labels": metadata_labels(metadata, model_name),
            "component_order": metadata_components(metadata, model_name),
            "outputs": {"probabilities": str(out / "probabilities.npz"), "run_result": str(result_path)},
        }
        result_path.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(summary, indent=2))
        return 0
    except Exception as exc:
        summary = {"status": "failed", "interface_version": 2, "input": str(input_path), "output_dir": str(out), "error": str(exc)}
        if args.overwrite or not result_path.exists():
            out.mkdir(parents=True, exist_ok=True)
            result_path.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(summary, indent=2), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
