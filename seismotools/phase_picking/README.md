# Phase-picking models

Copied from TRACE-1.1 `library/ai_module/phase_picking/model`, preserving all modules needed by its original `__init__.py`. This is the implementation actually imported by the expert pipeline, not a fresh upstream PhaseNet installation.

| Model | Local weights and metadata under `weights/` | Expert use |
| --- | --- | --- |
| PhaseNet | `phasenet/original.pt.v2`, `original.json.v2` | Baseline continuous P/S, 100 Hz real ZNE; thresholds 0.3/0.3 |
| DPPPicker P | `dpppickerp/scedc.pt`, `scedc.json` | Conditional vertical-only P, 1000-sample windows; first threshold crossing, not peak time |
| EQTransformer | `eqtransformer/original_nonconservative.pt.v1`, matching JSON | Qualified missing S, differential-only in the retained fit |

Model inputs are real waveform samples with the component order/sample rate required by the model. Outputs are probabilities/picks; calibration, association and valid continuous-window selection remain the caller's responsibility. Preserve model metadata normalization, filtering, overlap and blinding. Do not synthesize missing components or bridge real gaps.

Dependencies: PyTorch, SeisBench utilities, ObsPy, NumPy and the observed environment in `../environment.txt`. Run `python seismotools/check_tools.py --imports` from the project root to validate CPU loading of the copied models. It does not run waveform inference or qualify new weights.

The authoritative case usage is in [02_pick_phasenet.py](../../workflows/tasks/2019_ridgecrest_california/expert/01_pipeline/02_pick_phasenet.py), [42_vertical_p.py](../../workflows/tasks/2019_ridgecrest_california/expert/03_experiments/08_vertical_observations/42_vertical_p.py) and [46_qualify_eqtransformer.py](../../workflows/tasks/2019_ridgecrest_california/expert/03_experiments/11_alternative_picker/46_qualify_eqtransformer.py). These are usage references, not generic wrappers copied into this package.

## Original inference documentation

Copied usage references: [PhaseNet](docs/inference/phasenet.py), [EQTransformer](docs/inference/eqtransformer.py), [DPPPicker P](docs/inference/dpppickerp.py), and the [inference notebook](docs/01_inference_test.ipynb). The other top-level inference examples are preserved alongside them.

These scripts explain `classify`/`annotate` and custom inference conventions, but contain original host/device assumptions (including `torch_npu` imports). They are reference examples, **not CPU-compatible replacement launchers**. The expert's CPU implementation and tool loading check remain the tested interfaces. Notebook outputs are cleared; no inference, data fetch or remote service was run when copying documentation.
