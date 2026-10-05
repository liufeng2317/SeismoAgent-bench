# Phase-picking models

This tool package contains the local PhaseNet, EQTransformer and DPPPicker
model implementation used by the project. It is a model-inference resource,
not a complete event detector or association workflow.

## Directory layout

```text
phase_picking/
├── source/                 # Python model implementations
├── runtime/weights/        # Local model weights and metadata
├── interface/              # Stable CPU inference entry point and contracts
├── examples/smoke/         # Small executable inference example
├── docs/                   # Inference references and notebook
├── cache/                  # Local SeisBench cache (ignored runtime files)
└── README.md
```

The three bundled models are:

| Model | Runtime weights | Intended use |
| --- | --- | --- |
| PhaseNet | `runtime/weights/phasenet/original.pt.v2` | P/S probability inference |
| DPPPicker P | `runtime/weights/dpppickerp/scedc.pt` | Vertical-component P refinement |
| EQTransformer | `runtime/weights/eqtransformer/original_nonconservative.pt.v1` | Alternative P/S inference |

## Standard interface

`interface/run.py` performs one deterministic CPU model inference on a prepared
three-component NumPy waveform. It writes `probabilities.npz` and
`run_result.json`; the interface does not impose a universal threshold or pick
time convention.

```bash
python seismotools/phase_picking/interface/run.py \
  --input-npz waveform.npz \
  --output-dir /path/to/writable-run \
  --model phasenet \
  --sample-rate 100
```

The input and output contracts are documented in
[`interface/input_schema.json`](interface/input_schema.json) and
[`interface/output_schema.json`](interface/output_schema.json). Case workflows
may convert MiniSEED to the NPZ representation, then apply documented
preprocessing, probability thresholds, overlap handling and pick extraction.

Run the local smoke test with:

```bash
bash seismotools/phase_picking/examples/smoke/run.sh /tmp/phase-picking-smoke
```

## Direct Python use

For custom waveform batching, import the local implementation from `source/`:

```python
import sys
sys.path.insert(0, "seismotools/phase_picking/source")
from phase_picking.model.phasenet import PhaseNet
```

Load the matching metadata and state dictionary from `runtime/weights/` and set
the model to evaluation mode. The caller is responsible for channel order,
sampling rate, gaps, normalization, overlap/blinding, thresholds and UTC
conversion. Do not synthesize missing components or bridge real gaps.

The reference scripts in `docs/inference/` describe the original
`classify`/`annotate` conventions. They may contain host-specific imports and
are documentation references rather than benchmark launchers.

## Validation

From the project root, run:

```bash
conda run -n seismoagent python seismotools/tools_usage_validation/validate_phasenet.py
```

This loads the local CPU weights and performs both a synthetic forward pass and
a bounded Ridgecrest waveform inference. It verifies executable model plumbing,
not scientific equivalence of a complete catalog.
