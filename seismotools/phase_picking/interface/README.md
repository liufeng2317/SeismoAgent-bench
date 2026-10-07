# Standard phase-picking interface

Read the tool README and the model usage documents under `../docs/` before
choosing preprocessing, windowing, thresholds or pick extraction. The files in
this directory are execution contracts and entry points, not a replacement for
those method documents.

`run.py` runs one bundled model on one fixed-size NumPy window in CPU mode.
PhaseNet uses 3 channels and 3001 samples, EQTransformer uses 3 channels and
6000 samples, and DPPPicker P uses one vertical channel with a variable window.
The bundled weights use E/N/Z for PhaseNet and Z/N/E for EQTransformer; DPPPicker
P uses one vertical Z channel. Labels and output shapes are recorded from model
metadata; no universal threshold or pick-time convention is imposed.

```bash
python seismotools/phase_picking/interface/run.py \
  --input-npz waveform.npz \
  --output-dir /tmp/phase-picking-smoke \
  --model phasenet \
  --sample-rate 100
```

Use `--config config.json` for standard settings such as model, sampling rate,
windowing and CPU thread count. CLI values override the JSON settings. Use
`--overwrite` only when intentionally reusing an output directory.

The input and output contracts are in [input_schema.json](input_schema.json) and
[output_schema.json](output_schema.json). Case workflows may convert MiniSEED
to this input representation and then apply their documented preprocessing,
thresholding and pick extraction.

For waveforms longer than one model window, use `run_continuous.py`. It applies
overlapping windows, merges probabilities back onto the full input time axis,
and records the window count. Do not use only the first window as a substitute
for full time coverage. Its input and output contract is the same as `run.py`.
