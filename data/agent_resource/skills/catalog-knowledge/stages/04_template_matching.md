# Stage 4: template matching

Gate: `run.py --stage location` on the catalog with the detections merged. Before relocation: detections merged and marked, threshold justified by a null test.

## Decisions

**Run it for a sequence.**
- *Default:* required. Most of a sequence catalog's completeness comes from template matching, not from the picker: in offline tests on six recorded sequences, analyst catalogs with template matching held 1.4–11 times the events of their own picker-based catalogs; without the detections they recovered 0.72–0.98 of what an independent catalog recovers, against 0.99–1.85 with them.
- *Not run only when* there are too few usable templates (well-located events with clear waveforms at enough stations). Say how many and why.
- *Compute:* count the cores with `python -c 'import os; print(os.cpu_count())'` and look at the load average (`uptime`); `nproc` can report 1 under a restricted CPU affinity, and a cgroup `cpu.max` of `max` means no CPU limit. Run detections in parallel within the free cores. Lower the template count or the search grid before dropping the stage for time.

**Merge the detections into the submitted catalog.**
- *Do:* deduplicate against the picked events (same event within a second or two), give each new detection its own magnitude (relative to its template, or measured) and its location (the template's, or relocated), and mark it (for example `n_picks` = 0 and a method in your record). Detections without picks do not count against `events_with_few_picks`.
- *Not:* a run used only as a cross-check adds nothing to the catalog.

**Threshold from a null test.**
- *Do:* run the same templates on time-reversed or time-shifted data; detections there are false. Run the null test over a range of thresholds and keep the lowest one whose false rate is below 1–2 % of detections.
- *Not:* do not pick a high threshold to be safe. The false rate falls steeply with the threshold, and so do real detections: in the same tests the false fraction was 3.5–11 % at 9 × MAD and 0.5–1.5 % at 9.5 × MAD; raising the threshold by half a MAD unit cost up to 20 % of the detections, and near 16 × MAD 36–79 % of all events were lost. Published thresholds (8–15 × MAD) do not transfer between setups.

**Check the detections.**
- One template with far more detections than the others (a noise burst, a teleseism, a blast) dominates the false detections: look at its waveform; drop or re-cut it.
- In the coda of a large event many templates correlate with the coda: low-correlation detections there are suspect; detections larger than their template need their own magnitude and location.
- Blasts: many detections of one template in daytime working hours, few at night or at weekends, low high-to-low-frequency amplitude ratio.

**Events hidden in a mainshock's coda.** In the first minutes after a large event pickers and associators miss aftershocks, including magnitude 4 and more after a magnitude 7. Template matching with templates of the sequence, a lower picker threshold on high-frequency records, or far stations whose coda is weaker recover part of them. Mark the period as incomplete with Mc(M, t) = M − 4.5 − 0.75 log10(t / 1 day) (about M − 2.9 after ten minutes, M − 3.5 after an hour).
