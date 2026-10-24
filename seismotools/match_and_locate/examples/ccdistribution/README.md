# Upstream CC-distribution example through the standard interface

The second example of the MatchLocate2 distribution: template 2012-09-02
03:24:13.12 (M 3.0) scans the waveforms of the 03:33:51.61 event (M 2.3),
both resampled to 1,000 Hz, on a 201 × 201 horizontal grid (±0.01° at
0.0001°, depth fixed), S phase on 21 channels, window 4/1/3 s, N(*MAD) ≥ 12.
`output_mode = 3` writes the stacked CC of every node and sample above the
per-node threshold (`CCdistribution.out`), which upstream uses to plot the
location resolution.

```bash
bash seismotools/match_and_locate/examples/ccdistribution/run.sh \
  /liufeng1afs/software/Download/MatchLocate2-master.zip
```

The "continuous" segment here is the scanned event's own waveform cut,
whose SAC reference is that event's origin — so this example also checks
segments that are not UTC days (the reported origin is
2012-09-02T03:33:51.564Z = reference − 0.046 s).

`compare_ccdistribution.py` reads the upstream `CCdistribution.out` from the
extracted archive (18.8 MB, not stored in this repository) and the upstream
detection from `source/upstream/example_CCdistribution/20120902/`.

## Expected result (2026-10-21)

| Check | Result |
| --- | --- |
| Rows ours / upstream / common | 394,621 / 395,793 / 390,107 |
| CC difference on common rows | 0 (all identical) |
| Detection, ours | −0.046 s, 37.7894°, 140.0038°, 8.2 km, M 2.25, CC 0.6565, N×MAD 30.0601 |
| Detection, upstream | −0.045 s, 37.7894°, 140.0037°, 8.2 km, M 2.25, CC 0.6646, N×MAD 30.0290 |

Both reported samples are in both outputs with identical CC. The difference
is the N(*MAD) race of the upstream build (patch 0001): our sample's
correct N×MAD is 30.0601 and it is the maximum of our output; upstream
computed 29.9977 for it, so its de-duplication kept the neighbouring
sample (30.0290 on both sides). The race also moves per-node thresholds,
hence the ~1–1.5% one-sided rows; N×MAD differs by a median 0.033 on common
rows. Our output is byte-identical to the original program rebuilt here
and run single-threaded.

Runtime: about 40 s including preparation (`--threads 16`).
