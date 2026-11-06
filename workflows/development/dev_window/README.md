# Development window: a fast loop for the checker and the knowledge

The formal full-pipeline runs take 6–17 h each over 3–8 days of data; with one run at a time a round of the formal design took about a week, too slow to improve the checker and the knowledge between rounds (decided 2026-11-07). The development loop runs the same arms over one day around the mainshock, from 2 h before to 22 h after it, up to three runs at a time (the provider's limit). The formal experiment is run once, with the full window, after the loop has converged and the material is frozen again.

## Arms

- `dev_tools`: the formal `tools` arm (S1) with only the processing window changed.
- `dev_knowledge`: the formal `knowledge` arm (S3) with only the processing window changed.

The input is the same as in the formal arms; the prompt already says that the input may contain waveforms beyond the window. `build_dev_variants.py` writes `prompt_dev_<arm>.md`, `task_dev_<arm>.json` and `input_dev_<arm>.json` in every task package from the formal files, so it must be rerun after any change to `prompt_tools.md` or `prompt_knowledge.md`. `run.sh` gives `dev_*` a 12-hour budget.

```bash
python workflows/development/dev_window/build_dev_variants.py
cd workflows/tasks/<case> && AGENT=claude VARIANT=dev_knowledge bash run.sh
```

## Windows

Defined in each case's `evaluation/metrics.yaml` (`development_window`):

| Case | Window (UTC) | Anchor | Primary location reference, pairs of the human-in-loop final |
|---|---|---|---|
| Prague | 2011-11-14 03:31 – 11-15 03:31 | M 3.2, the largest event of the data window (the Mw 5.7 precedes it by eight days) | Cochran, 263 |
| Magna | 2020-03-18 11:09 – 03-19 11:09 | Mw 5.7 | Pang, 1,775 |
| Maple Creek | 2017-06-15 22:48 – 06-16 22:48 | Mw 4.4 | ComCat, 287 |
| Kīlauea | 2018-05-04 20:32 – 05-05 20:32 | Mw 6.9 (outside the summit box) | Shelly, 495 |
| Ridgecrest | 2019-07-06 01:19 – 07-07 00:00 | Mw 7.1; the end is cut at the end of the data window (20.7 h after) | Shelly, 2,774 |
| Kaikōura | 2016-12-04 01:15 – 12-05 01:15 | M 5.5, the largest event of the data window | Lanza, 17 |

Kaikōura's primary location reference has fewer than 30 pairs in the window, so its time and space criteria are `insufficient` in this loop; magnitude, completeness and the stability criteria are still judged.

## Scoring

The scorer treats every variant whose name starts with `dev_` as a development run: the references, the human-in-loop catalogs and the candidate are cut to the window, and the trust thresholds read the human-in-loop final over the same window (`evaluation/human_in_loop/metrics_baseline_development.json`, `python -m SeismoAgentBench.scoring.catalog_metrics baseline --task-dir <case> --window development`). Development runs are left out of the formal score table; `summary` lists them as their own variants.
