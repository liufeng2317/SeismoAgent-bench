# Upstream Hi-net example through the standard interface

This example replays the MatchLocate2 distribution's own example (14 templates
of a 2012 Hi-net sequence, 7 stations x 3 components, 2,000 s of continuous
data on 2012-09-02) through `interface/run.py` and compares the result with
the outputs shipped upstream, which are stored in this package under
`source/upstream/example/`.

```bash
bash seismotools/match_and_locate/examples/workflow/run.sh \
  /liufeng1afs/software/Download/MatchLocate2-master.zip
```

The archive (sha256 `543b6bc9…ad19`, upstream commit `bac5ccb`) is verified,
then extracted into a new empty directory
(`runtime/example_data/upstream_hinet/data`, git-ignored) with member paths
checked; nothing from it is executed. `prepare_upstream_example.py` links the
extracted SAC files into the interface layout and writes the upstream
`PROC_MatchLocate.pl` parameters as `config.json`: single phase S, search
±0.05°/±0.05°/0 km at 0.005°/0.005°/1 km (441 nodes, depth fixed), window
4/1/3 s, detection N(*MAD) ≥ 12 with 6 s separation, merge CC ≥ 0.30 and
N(*MAD) ≥ 12.

## Expected result

`compare_reference.py` passes when (run on 2026-10-21 with the patched build):

| Check | Result |
| --- | --- |
| Single-template detections reported at the same time on both sides | 1,179 |
| … with any difference in time, location, depth, magnitude or CC | 0 |
| Final catalog events (ours / upstream) | 140 / 140, 139 identical |

Every remaining difference is attributable to the upstream outputs having
been produced by a multi-threaded build with the N(*MAD) data race fixed by
patch 0001 (see `source/patches/README.md`): N(*MAD) values differ by a median
0.003–0.020 and at most 1.37; for 17 events a different peak inside the 6 s
de-duplication window wins (reported times up to 4.8 s apart); 7 detections
within 0.25 of the threshold cross it; and once the final merge selects
another template for the same event. The patched build reproduces the
original program's single-threaded output byte for byte at any thread count.

Runtime: about 35 s with `--jobs 14 --threads 4` on the Kunpeng-920 host.
