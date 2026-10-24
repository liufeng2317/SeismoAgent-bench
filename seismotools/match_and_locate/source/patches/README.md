# Local patches to MatchLocate2 2.0

`support/build_native.py --tool match_and_locate` copies `../upstream/src/`
into `runtime/build/`, applies these patches in file-name order with
`patch -p1` and compiles (0006 touches SelectFinal.c only, so its position
before 0007 does not matter). `../upstream/` itself is never modified.

| Patch | File | Kind | Change |
| --- | --- | --- | --- |
| 0001 | MatchLocate2.c | correctness | `median`/`MAD` were globals written and read inside the OpenMP shift-and-stack loop, so N(*MAD) of one grid node could be computed with another node's statistics. They are now thread-local and passed explicitly. |
| 0002 | MatchLocate2.c | correctness | `-O3` (CC distribution output) checked `fp1` instead of `fp2` after opening the output file. |
| 0003 | MatchLocate2.c | correctness | `Mag()` initialised the peak amplitude with the signed first sample (a negative first sample could leave a smaller peak) and freed only the last trace's buffers, leaking two windows per trace per detection. |
| 0004 | MatchLocate2.c | correctness | Candidates above threshold were written into a per-node buffer of `2 × duration` entries without a bound check; a low threshold could overrun the heap silently. Overflow now stops with exit code 3 and a message. |
| 0005 | MatchLocate2.c | performance, output-identical | Each grid node copied every shifted correlogram into an `ntrace × npts` double matrix before stacking, and found the median and MAD with two full `qsort` calls. The stack now accumulates directly (same per-sample summation order) and the two order statistics use quickselect (same values). |
| 0007 | MatchLocate2.c | robustness | Median and MAD were taken over every stack sample. Where no channel has data (zero-filled gaps, a day only partly covered) the stack is exactly 0; when such samples are the majority, median = MAD = 0, the threshold becomes 0 and every sample passes (found with a day of which 20 min had data: the unpatched program would overrun its buffer, see 0004). Exact-zero samples are now left out of the statistics, and a node with no data or MAD = 0 yields no candidates. On complete data no stack sample is exactly 0, so outputs are unchanged. |
| 0006 | SelectFinal.c | correctness | The merge reads into static arrays of `NPEVE = 100000` rows without a bound check; more rows now stop with exit code 3. (The Python merge in `matchlocate_runner.native.merge_detections` has no row limit.) |

## Evidence (upstream Hi-net example, 14 templates, 2026-10-21)

* Unpatched upstream build: single-threaded and 32-thread runs differ from
  each other and from the shipped upstream outputs only in the N(*MAD) column
  (and in detections whose N(*MAD) crosses the threshold) — the race of 0001.
* Patches 0001–0004 at 32 threads and 1 thread: byte-identical to the
  unpatched single-threaded output, all 14 templates.
* All six patches, built by `build_native.py` with the project flags (`-O2
  -std=gnu99 -fopenmp -ffp-contract=off`): byte-identical to the unpatched
  single-threaded output for all 14 templates at 1 and 32 threads (direct
  native calls) and at 4 threads (through `interface/run.py`).
* Speed (patch 0005): all 14 templates 638 s → 179 s single-threaded and
  55 s → 9.3 s with 32 threads. For one template (21 traces, 2,000 s at
  100 Hz, 441 nodes) shift-and-stack drops 39.8 s → 7.4 s single-threaded;
  correlation (5.5 s) is unchanged and becomes the larger share.

* With 0007 added (2026-10-21): example 1 at 32 threads, and example 2
  (EventCase plus the 394,621-row CCdistribution.out), byte-identical to the
  unpatched single-threaded output.

## Not built

* `MatchLocate2.1.c` (adds `-B` band-pass) calls SAC's `xapiir` from libsac,
  which is not installed here, and leaves `low`/`high` uninitialised when `-B`
  is omitted. Filtering belongs to the data-preparation stage, where templates
  and continuous data are processed identically (`matchlocate_runner.prepare`).
* `ccsacc` (plotting helper) also links libsac.
