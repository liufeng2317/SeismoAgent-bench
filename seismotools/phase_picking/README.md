# Phase-picking models

This tool package contains the local PhaseNet, EQTransformer and DPPPicker
model implementation used by the project. It is a model-inference resource,
not a complete event detector or association workflow.

## Directory layout

```text
phase_picking/
├── source/                 # Python model implementations
├── runtime/weights/        # Local model weights and metadata
├── interface/              # Stable CPU inference entry points and contracts
├── examples/                  # Validated model examples and interface smoke test
├── docs/{core,examples}/   # Method notes and model reference examples
├── metadata.json            # Tool and interface identity
├── cache/                  # Local SeisBench cache (ignored runtime files)
└── README.md
```

The three bundled model choices are:

| Model | Runtime weights | Intended use |
| --- | --- | --- |
| PhaseNet | `runtime/weights/phasenet/original.pt.v2` | N/P/S probability inference |
| DPPPicker P | `runtime/weights/dpppickerp/scedc.pt` | Vertical-component P refinement |
| EQTransformer | `runtime/weights/eqtransformer/original_nonconservative.pt.v1` | Alternative P/S inference |

The bundled metadata defines component order as E/N/Z for PhaseNet, Z/N/E for
EQTransformer, and one vertical Z channel for DPPPicker P. Always use the order
reported by the selected model metadata rather than assuming one order for all
models.

## Standard interface

`interface/run.py` performs one deterministic CPU model inference on a prepared
NumPy waveform. `interface/run_continuous.py` applies overlapping model windows
to a longer waveform. Both write `probabilities.npz` and `run_result.json`; the
interface does not impose a universal threshold or pick-time convention.

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
export PYTHON=/path/to/the/configured/phase-picking-python
bash seismotools/phase_picking/examples/smoke/run.sh /tmp/phase-picking-smoke
```

The examples use `PYTHON` when it is set and otherwise use `python`. The
selected interpreter must provide Torch and the scientific dependencies.

For model-specific inference conventions, see the validated Python examples in [examples](examples/) and the concise usage guidance in [docs/examples](docs/examples/).


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

The Python files in `examples/` describe the validated `classify`/`annotate`
conventions. They are model-usage references rather than benchmark launchers;
the `docs/examples/` directory contains guidance and links, not duplicate code.

## Validation

From the project root, run:

```bash
conda run -n seismoagent python seismotools/support/tools_usage_validation/validate_phasenet.py
```

This loads the local CPU weights and performs both a synthetic forward pass and
a bounded Ridgecrest waveform inference. It verifies executable model plumbing,
not scientific equivalence of a complete catalog.
