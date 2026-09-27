# Minimal raw-waveform shape screening

Internal source diagnostic only; not ground-truth labels and not intended as agent input.

Scanned 351 files / 117 channels in [2019-07-04T00:00:00.000000Z, 2019-07-07T00:00:00.000000Z). Scored 3,032,615 contiguous non-overlapping 10-second windows (3,032,615,000 samples). Short tails and fragments under 10 s are omitted; prior full-sample integrity checks still apply. No response removal, filtering, resampling, padding, repair or raw-file writes. Decode warnings: 0.

[Seven diagnostic windows](05_shape_screening.png) ([PDF](05_shape_screening.pdf)) and [one row per channel](shape_screening.csv). The table retains only each channel's strongest candidate for each statistic, with exact source path and time; it is not an exhaustive anomaly inventory.

- Plateau score: fraction of 0.2-s bins whose range is at most 3% of the containing 10-s range and whose mean is at least 25% of that range away from the 10-s mean. Constant windows score zero because prior QC checks exact constant runs. This detects approximate elevated platforms, but pulses, steps and genuine signal shapes can also score highly.
- Jump score: largest absolute sample increment divided by RMS increment within the same 10 s. It ranks isolated changes, including legitimate sharp arrivals; it is not a timing-error or corruption verdict.
- These dimensionless scores rank within-channel morphology. No universal pass/fail threshold or cross-instrument physical-amplitude comparison is used. Scores depend on window alignment and do not prove absence of saturation.
- The figure takes the two highest-ranked distinct stations per metric, plus fixed CI.CCC..HHZ windows for both large earthquakes and a background comparison. The background window is a comparison, not a certified noise-only interval. Jump plots are centered on the strongest increment (CSV times remain the original scoring-window starts). Axes use independent raw-count scales.

This bounded screen is sufficient for a first source review. Keep the established gap and saturation concerns available internally; do not delete stations or synthesize labels from these scores. Further processing choices remain part of the agent task.
