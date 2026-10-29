# Scoring method

How a catalog is scored, from the files an Agent hands in to the trusted-catalog verdict, in the order the scorer works. Written to be read on its own and to serve as the evaluation section of the paper. The formal definitions, with every threshold, are in [`02_Catalog_Metrics.md`](../framework/02_Catalog_Metrics.md) (catalog metrics v2); the current numbers for every case and run are in [`progress/SCORE_TABLE.md`](progress/SCORE_TABLE.md).

## 1. What is scored, and against what

Each run must leave two files in its work folder: `catalog.csv` (one row per event: origin time, latitude, longitude, depth below sea level, magnitude, pick counts, status) and `picks.csv` (one row per phase pick, linked to an event). Rows marked `rejected` are not scored.

A catalog is compared with three kinds of yardstick, never with a single "truth":

- **Reference catalogs.** Each case has several published catalogs, each used only for the roles it supports: D detection, L absolute location, S structure, M magnitude, P phase picks. One D reference and one L reference per case are *primary* and feed the headline numbers; one operational catalog is the *magnitude authority*. Roles per case: [`02_Catalog_Metrics.md`](../framework/02_Catalog_Metrics.md) §3; primaries: [`00_Case_Registry.md`](../data/00_Case_Registry.md).
- **The reference ceiling.** References do not recover each other fully. The ceiling of a reference is the best recall any other reference reaches on it (Prague 0.51, Magna 0.68, Kīlauea 0.49, Ridgecrest 0.64, Kaikōura 0.69; Maple Creek 0.98, where ComCat holds only 626 larger events). Detection is read relative to it.
- **The human-in-loop final.** The catalog we built by steering an Agent workflow by hand, with the references in view, for 7–11 rounds per case. It is the upper bound an Agent is compared with, and every catalog is also matched to it directly.

There is no composite score. The output per run is a profile: a verdict per dimension, the numbers behind it, and completeness reported apart.

## 2. Step by step

### 2.1 Completion

The run is first checked against its output contract: both files present with the required columns, internal consistency (every pick's event exists, pick counts agree, coordinates valid). A run without a valid catalog is *not completed*: its detection metrics count as zero in every average, and it is not trusted.

### 2.2 Evaluation cohort

Each case has a fixed cohort mask: a half-open time window, a region box and depth bounds (`workflows/tasks/<case>/expert/00_config/validation.yaml`). The same mask is applied to the references, the final and the Agent's catalog. Agent rows outside it are not scored further, but their share is reported as `out_of_mask_fraction` and judged under event reality (§2.6). They are not counted as false events, because the task states the time window but not the region, so an out-of-region event may be a real regional earthquake.

### 2.3 Event matching

Two catalogs are compared event by event with a one-to-one greedy matcher: every candidate pair within the gates is ranked by epicentral distance, then by time difference, and each event is used at most once.

- **Primary gates:** |Δt| ≤ 2 s and epicentral distance ≤ 5 km. Kaikōura uses 4 s / 15 km, because its 260-km network and the offset between 1-D and 3-D location frames leave even the final's epicentres 1.9 km scattered about the references.
- **Sensitivity gates:** 4 s / 15 km (wider) and 1 s / 3 km (tighter), reported next to the primary result. The tight result is `recall_tight`.
- **Reference-specific gates:** a reference with coarse origin times keeps its own gates (Isken & Mooney at Prague: 60 s / 5 km); a time-only reference (Shelly at Maple Creek) is matched on |Δt| ≤ 1 s alone.

### 2.4 Chance correction

In a dense sequence, events can fall inside the gates by coincidence. The scorer therefore repeats every match against the reference shifted by 60 s; the matches it still finds measure the coincidence rate p at the sequence's own event density. An observed match rate m is m = r + (1 − r) p for a true rate r, because a coincidence only adds a match where no true one exists, so

> r = (m − p) / (1 − p), clipped at 0.

This correction is applied to every recall, to the support of a catalog's events by the references, and to the comparison with the final. Without it, a catalog of random events inside a compact swarm can reach a high raw recall (Maple Creek `min`: 0.91 at 4 s / 15 km, 0.05 at 1 s / 3 km).

### 2.5 Measurements

Each matched comparison yields numbers in five dimensions (full list: [`02_Catalog_Metrics.md`](../framework/02_Catalog_Metrics.md) §5):

| Dimension | Main measurements | Read against |
|---|---|---|
| Detection | chance-corrected recall of each D reference; `recall_norm` = recall of the primary D reference ÷ its ceiling; `recall_tight`; F1 per magnitude class (M ≥ 2, 3, 4, 5 by the magnitude authority) | the ceiling and the final |
| Event reality | `out_of_mask_fraction`; `union_support` (share of the catalog's events matched by any D reference or the final); `precision_final`; the blind-audit false-event rate | the final |
| Time | origin-time difference to the final (median signed bias and its spread); median \|Δt\| to the primary L reference; recall within 1 h after M ≥ 4 events relative to all other times | the final |
| Space | horizontal offset to the final split into a common **shift** and the **scatter** about it; depth difference to the final; the same against the primary L reference; share of epicentres away from every known structure; largest share of events at one depth (fixed-depth or grid-edge pile-ups) | the final |
| Strength | magnitude difference to the magnitude authority: median, spread, and slope against magnitude (a negative slope means large events are compressed); b-value difference; recall of M ≥ 4 events | the final's own values |

Phase picks are scored where manual or correlation picks exist (Magna, Maple Creek): share recovered within 0.5 s and residual MAD.

### 2.6 Trusted-catalog verdict

The verdict answers whether the catalog can be trusted for science, in four steps. Each step passes when all its criteria pass:

1. **Event reality** — few events outside the region (≤ max(10 %, final + 5 %)); few false events in the blind audit (≤ 2 %, *pending* until labelled).
2. **Time** — accuracy: origin times within 0.3 s of the final in the median; stability: their spread ≤ 0.3 s, and detection does not collapse after large events (≥ 0.8 × the final's ratio).
3. **Space** — accuracy: horizontal shift ≤ 1 km and depth difference ≤ 1 km from the final; stability: scatter ≤ max(1 km, the final's own scatter about the reference), events on the known structure (off-structure share ≤ max(5 %, 3 × final)), no depth pile-up (≤ max(5 %, final + 2 %)).
4. **Strength** — accuracy: magnitude offset ≤ the final's offset + 0.2, and every M ≥ 4 (and M ≥ 5) event present; stability: magnitude spread ≤ max(0.3, final + 0.1), no compressed scale (|slope| ≤ max(0.2, |final| + 0.1)).

A catalog is **trusted** when all four steps pass; it is *pending* while only the audit is open. Thresholds are absolute and are relaxed to the final's own value plus a margin wherever the final itself would fail them, so the final always passes. The thresholds were fixed before the verdicts were read and have not been tuned to them.

**Completeness is reported, not judged.** `recall_norm`, `recall_tight`, the share of the final's events recovered (`recall_final`) and the event ratio to the final stand next to the verdict. A catalog that is accurate but incomplete, like an operational catalog, can still be trusted; how much of the final it recovers is a separate result.

### 2.7 Diagnostics

Three analyses explain the numbers without changing them:

- **Blind audit.** From the events no reference or the final supports, 50 are drawn (stratified by pick count, fixed seed) and shown as waveform plots with predicted arrivals but no reference information. A reviewer labels each one earthquake, not an earthquake or undecidable; a second reviewer checks 10. The false-event rate is (1 − `union_support`) × the share labelled "not an earthquake".
- **Component swap.** The Agent's own picks and associations are relocated with the human-in-loop velocity model and locator. Errors that disappear came from the back end (model, locator); errors that remain came from the front end (picking, association).
- **Expert ladder.** Every adopted human-in-loop round is scored the same way, so the step that closed each part of the gap to the final is visible.

### 2.8 Across runs

Each configuration (case × stage × harness × model) is meant to run at least twice. Detection metrics average over all launched runs, with a failed run counted as zero; other metrics average over completed runs and are shown with the completion rate. A run whose transcript shows access to the withheld references is flagged and left out of the means. A run stopped by a defect of the test harness rather than by the Agent carries an `EXCLUDED.md` marker, is left out, and is repeated.

## 3. Worked example: Maple Creek, `tools` run

The Agent used the tool library and handed in 3,957 events. In the cohort its catalog has 3,411 events; the final has 12,422.

- **Completeness (not judged).** `recall_norm` 0.96 (final 0.99): against ComCat's 626 larger events the run looks nearly complete. At 1 s / 3 km, `recall_tight` falls to 0.43 (final 0.95), and the run recovers 22 % of the final's events. The small events, which template matching would add, are missing.
- **Event reality: fails.** 12.7 % of its events are outside the region (limit 10 %); the blind audit is still to be labelled.
- **Time: fails.** Origin times are 1.15 s later than the final's in the median (limit 0.3 s); their spread is small (0.16 s), so the error is systematic, not noise.
- **Space: fails.** The depth is 2.18 km shallower than the final (limit 1 km); the scatter about the final is 1.90 km (limit 1 km); 11.8 % of epicentres lie off the known structure (limit 5 %). The horizontal shift (0.91 km) and the depth pile-up (3.8 %) pass.
- **Strength: fails, narrowly.** The magnitude offset (0.19) and spread (0.37) pass; the slope against magnitude is −0.44 against a limit of 0.41, a slightly compressed scale.
- **Verdict:** not trusted.
- **Component swap.** With the human-in-loop locator, the same picks give a depth difference of −0.31 km, |Δt| of 0.09 s and a shift of 0.15 km from the final. The late, shallow solutions were a back-end choice of velocity model and locator. The picks themselves were sound, which is the kind of error a checker or encoded expert knowledge is meant to catch.

Under metrics v1 the same run scored `recall_norm` 1.12 against the final's 1.15 and passed the draft usability criteria; [`02_Catalog_Metrics.md`](../framework/02_Catalog_Metrics.md) §12 records why v2 replaced v1.

## 4. Reproducing the scores

```bash
python -m SeismoAgentBench.scoring.catalog_metrics baseline --task-dir workflows/tasks/<case>   # references, ceilings, final
python -m SeismoAgentBench evaluate --run-dir <run>                                            # one run: contract + catalog metrics
python -m SeismoAgentBench.scoring.catalog_metrics swap --task-dir workflows/tasks/<case> --run-dir <run>
python -m SeismoAgentBench.scoring.catalog_metrics summary --task-dir workflows/tasks/<case>    # per-configuration summary and exports
python -m SeismoAgentBench.scoring.catalog_metrics table                                       # docs/research/progress/SCORE_TABLE.md
```

The baseline must be scored before runs, because the verdict reads the final's own values from it. The score table is generated from the tracked exports only; regenerate it after every scored run.
