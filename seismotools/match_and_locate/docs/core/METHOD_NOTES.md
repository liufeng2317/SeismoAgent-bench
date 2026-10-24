# Match&Locate method notes

What `MatchLocate2.c` (2.0, with the local patches) computes, the
approximations behind it, and what it costs on this host.

## Algorithm as implemented

For one template and one continuous segment with `n` channel-phase rows:

1. **Correlation (once).** For every row, the template window
   `[t_mark − before, t_mark − before + window]` is correlated at zero lag
   with the continuous trace at every sample offset `k` (normalized CC,
   time domain). Result: `n` correlograms of length ≈ segment samples.
2. **Shift and stack (per grid node).** For a node at (lat, lon, depth) the
   row's correlogram is shifted by
   `t_mark + dT/dΔ · (Δ_node − Δ_template) + dT/dz · (z_node − z_template)`,
   with Δ the great-circle distance in degrees and z the depth; the `n`
   shifted correlograms are averaged. Sample index of the stack = origin time.
3. **Per-node statistics.** Median and MAD of that node's stack over the
   whole segment, leaving out samples where the stack is exactly 0 (no data
   on any channel; patch 0007); a sample is a candidate when stack ≥ CC threshold and
   (stack − median)/MAD ≥ N threshold.
4. **De-duplication.** All candidates of all nodes, sorted by N×MAD
   (descending), are kept greedily if farther than `-D` seconds from every
   kept one; the kept sample gives origin time, node location, CC, N×MAD.
5. **Magnitude.** For each row, peak |amplitude| of the detected window over
   the template's; magnitude = template magnitude + median log10 of the ratios.
6. **Merge across templates (SelectFinal).** Same greedy rule over all
   templates' detections with merge thresholds; CC = 1.0 detections (the
   templates themselves) are always kept.

`-R0/0/0` reduces this to a classic matched filter at the template location.

## Approximations and what they mean on a local network

- **Linear moveout.** Relative travel time is linearised about the template.
  For the Magna network (43 stations, 4–39 km from a 10 km deep source) and
  the case's layered model, worst-direction errors per station are:

  | Offset from template | P median / max | S median / max |
  |---|---|---|
  | 0.5 km | 0.9 / 1.8 ms | 1.6 / 3.1 ms |
  | 1.0 km | 3.7 / 7.2 ms | 6.3 / 12.5 ms |
  | 2.0 km | 14.8 / 29.7 ms | 25.6 / 51.3 ms |
  | 3.0 km | 33.7 / 68.6 ms | 58.3 / 118.8 ms |

  With a 2–10 Hz band (quarter period at 5 Hz = 50 ms) a half-width of about
  1–1.5 km per template is safe; 2 km degrades the nearest stations; 3 km is
  not usable. Regional networks (the method's original setting) tolerate much
  larger grids. Compute this for any network with
  `matchlocate_runner.linearisation_error_s`.
- **Station elevation and azimuth.** Moveout depends only on the change of
  epicentral distance and depth; azimuthal and elevation effects enter only
  through those two derivatives.
- **Statistics per node.** N×MAD is evaluated separately at every node, so
  the false-alarm rate at a fixed threshold grows with the number of nodes:
  on a day of synthetic data with 24 injected repeats, the same N×MAD ≥ 9
  gave 24 detections with 1 node, 26 with 75 and 32 with 405.
- **Location resolution** comes from the correlation peak's sensitivity to
  the moveout; it is relative to the template and limited by the grid step
  (synthetic offsets of 0.6–0.8 km were recovered within 6 m on a 0.25 km
  grid). Absolute accuracy is that of the template.
- **Magnitude** is a peak-amplitude ratio: it inherits the template scale
  and reads high at low SNR (+0.22 for a synthetic event with S peaks about
  4× the noise RMS); templates without a magnitude give NaN.

## Cost on this host (Kunpeng-920, aarch64, CPU only)

Measured with the patched build on synthetic day-long data, 30 stations × 3
components = 90 rows (P on Z, S on N/E), 2 s windows, one (day, template) job:

| Rate | Grid | Nodes | Threads | Wall | Peak RSS |
|---|---|---|---|---|---|
| 50 Hz | matched filter | 1 | 4 / 16 / 64 | 38 / 14 / 6.0 s | 4.35 GB |
| 50 Hz | ±0.5 km, 0.25 km step, depth ±0.5 km | 75 | 4 / 64 | 69 / 9.1 s | 4.35–4.95 GB |
| 50 Hz | ±1 km, 0.25 km step, depth ±1 km at 0.5 km | 405 | 4 / 16 / 64 | 177 / 83 / 158 s | 4.35–4.96 GB |

Read as: correlation ≈ 150 core-seconds per job; shift-and-stack ≈ 1.4
core-seconds per node at 4 threads; memory ≈ rows × samples × 12 bytes.
Both scale linearly with rows and samples (100 Hz doubles them).

**The stack is memory-bandwidth bound.** Every node streams all
correlograms (8-byte samples): 90 rows × one day at 50 Hz is 3.1 GB per
node, 1.26 TB for 405 nodes. Beyond ~16 threads a single job stops
speeding up (64 threads was slower than 16 above). The host is shared
(load average ~100 on 192 cores; this cgroup has 64 CPUs spread over five
NUMA nodes), so timings vary between runs; the 16-thread rows of the 1- and
75-node grids also overlapped another job. Plan large runs as several
concurrent jobs of 4–16 threads and measure the aggregate throughput on a
pilot; do not extrapolate from one 64-thread job.

Possible further speed-ups, not implemented: stacking several grid nodes
per pass over a block of samples (the shifts of neighbouring nodes differ by
few samples, so the block stays in cache; output-identical), and FFT or
single-precision correlation (faster but no longer bit-identical to the
upstream program). Before patch 0005 the per-node stack cost was about 5×
higher.
