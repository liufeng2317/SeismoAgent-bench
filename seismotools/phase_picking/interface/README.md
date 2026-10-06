# Standard phase-picking interface

`run.py` runs one bundled model on one fixed-size three-component NumPy window in
CPU mode. For the bundled PhaseNet model the window is 3001 samples, the input
component order is E/N/Z, and the probability channels are Noise/P/S. It records
probabilities without imposing a universal threshold or pick-time convention.

```bash
python seismotools/phase_picking/interface/run.py \
  --input-npz waveform.npz \
  --output-dir /tmp/phase-picking-smoke \
  --model phasenet \
  --sample-rate 100
```

The input and output contracts are in [input_schema.json](input_schema.json) and
[output_schema.json](output_schema.json). Case workflows may convert MiniSEED
to this input representation and then apply their documented preprocessing,
thresholding and pick extraction.

For waveforms longer than one model window, use `run_continuous.py`. It applies
overlapping 3001-sample windows (1500-sample overlap by default), merges the
probabilities back onto the full input time axis, and records the window count.
Do not use only the first window as a substitute for full time coverage.
