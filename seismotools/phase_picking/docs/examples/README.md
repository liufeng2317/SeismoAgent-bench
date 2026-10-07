# Phase-picking usage guidance

This directory contains concise guidance for using the validated phase-picking examples. The executable Python examples are kept once in [`../../examples/`](../../examples/); this directory does not duplicate their code.

- PhaseNet: [`../../examples/phasenet.py`](../../examples/phasenet.py). Prefer `model.classify` for direct P/S picks and peak probabilities; use `model.annotate` when probability sequences are needed.
- EQTransformer: [`../../examples/eqtransformer.py`](../../examples/eqtransformer.py).
- DPPPicker: [`../../examples/dpppickerp.py`](../../examples/dpppickerp.py) and [`../../examples/dpppickers.py`](../../examples/dpppickers.py).
- Other bundled models: see the corresponding Python file in [`../../examples/`](../../examples/).

These examples define model-specific input order, model loading, preprocessing and output interpretation. Read the relevant example before adapting a workflow. For the stable NumPy interface and its input/output contracts, see [`../../interface/`](../../interface/). The smoke test is [`../../examples/smoke/run.sh`](../../examples/smoke/run.sh).
