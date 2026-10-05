# Standard phase-picking interface

`run.py` runs one bundled model on a three-component NumPy waveform in CPU
mode. It is deliberately a model execution interface: it records probabilities
without imposing a universal threshold or pick-time convention.

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
