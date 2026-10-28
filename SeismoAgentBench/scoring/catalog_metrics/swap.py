"""Component swap: relocate an Agent's own associations with the expert's model and locator.

The Agent's picks and pick-to-event associations are kept; only the absolute
location step is replaced by the expert's: its 1-D velocity model, NonLinLoc
grid, error settings and location method (expert ``00_config`` and the stage-03
inputs of ``swap.picks_round`` in ``evaluation/human_in_loop/expert_ladder.yaml``), without
station delays.
Scoring the relocated catalog next to the Agent's own locations separates
errors of the front end (picks, association) from those of the velocity model
and locator. Analysis only; the Agent's score is unchanged.

Writes <run>/evaluation/swap/{inputs/, nll/, catalog_relocated.csv, swap.json}.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

from .case import EXPERT_DIR, SEA_LEVEL_MARKER, _strip, headline, load_case
from .metrics import ceilings, score_population
from .tables import Population, in_mask, read_candidate_catalog

ROOT = Path(__file__).resolve().parents[3]
LOCATE = ROOT / "seismotools/nonlinloc/interface/locate.py"
KEYS = ("recall_norm", "shift_km", "scatter_median_km", "epi_gt5km", "dz_median_km", "depth_mode_share",
        "off_structure_fraction", "off_structure_after_shift", "dt_mean_s", "dt_std_s")


def _inputs(case, run_dir: Path, out: Path) -> tuple[Path, Path, Path, dict]:
    spec = yaml.safe_load((case.task_dir / EXPERT_DIR / "expert_ladder.yaml").read_text())["swap"]
    expert = case.task_dir / "expert"
    assoc = expert / "export" / spec["picks_round"] / "03_associate_gamma/full"
    settings = json.loads((assoc / "inputs.json").read_text())
    s, rows = settings["settings"], settings["model_source"]["rows"]
    nl = yaml.safe_load((expert / "00_config/nonlinloc.yaml").read_text())
    st = pd.read_csv(assoc / "stations.csv").drop_duplicates("station_id")
    out.mkdir(parents=True, exist_ok=True)
    pd.DataFrame({"station_id": st.station_id, "latitude": st.latitude, "longitude": st.longitude,
                  "elevation_m": st.elevation_m - st.sensor_depth_m}).to_csv(out / "stations.csv", index=False)
    picks = pd.read_csv(run_dir / "work/picks.csv", dtype=str, keep_default_na=False)
    picks = picks[(picks.event_id.str.strip() != "") & (picks.status.str.lower() != "rejected")
                  & picks.phase.str.upper().str[0].isin(["P", "S"]) & picks.station_id.isin(st.station_id)]
    pd.DataFrame({"event_id": picks.event_id, "pick_id": picks.pick_id, "station_id": picks.station_id,
                  "phase": picks.phase.str.upper().str[0], "time_utc": picks.time_utc}).to_csv(out / "arrivals.csv", index=False)
    (out / "model.txt").write_text("".join(f"{r['top_of_layer_km']} {r['vp_km_s']} {r['vs_km_s']}\n" for r in rows))
    config = {"reference_elevation_km": s["reference_elevation_km"], "projection_center": s["projection_center"],
              "region": {"longitude": s["longitude_bounds"], "latitude": s["latitude_bounds"], "depth_km": s["depth_bounds_km"]},
              "velocity_layering": s.get("velocity_layering", "linear"), "grid_spacing_km": nl["grid_spacing_km"],
              "grid_depth_km": [nl["grid_top_km"], nl["grid_bottom_km"]],
              "min_phases": nl.get("min_phases", 10), "min_s_phases": nl.get("min_s_phases", 3),
              "pick_error_s": nl["pick_error_s"], "model_error_s": nl["model_error_s"],
              "search": {"min_node_km": nl["search_min_node_km"], "max_nodes": nl["search_max_nodes"],
                         "samples": nl["posterior_samples"]},
              "per_event_timeout_s": nl.get("per_event_timeout_s", 180),
              "location_method": nl.get("location_method", "GAU_ANALYTIC")}
    (out / "config.json").write_text(json.dumps(config, indent=1))
    config["picks_round"] = spec["picks_round"]
    return out / "arrivals.csv", out / "stations.csv", out / "model.txt", config


NLL_PYTHON = "/liufeng1afs/software/miniconda3/envs/seismoagent/bin/python"  # environment of the seismotools NLL build


def run_swap(task_dir: Path, run_dir: Path, *, workers: int = 16, python: str = NLL_PYTHON) -> dict:
    case = load_case(task_dir)
    run_dir = run_dir.resolve()
    out = run_dir / "evaluation/swap"
    arrivals, stations, model, config = _inputs(case, run_dir, out / "inputs")
    nll = out / "nll"
    if not (nll / "run_result.json").is_file():
        subprocess.run([python, "-I", str(LOCATE), "--arrivals", str(arrivals), "--stations", str(stations),
                        "--velocity-model", str(model), "--config", str(out / "inputs/config.json"),
                        "--output-dir", str(nll), "--workers", str(workers), "--quiet", "--overwrite"], check=False)
    status = json.loads((nll / "run_result.json").read_text())["status"] if (nll / "run_result.json").is_file() else None
    if status not in ("success", "partial"):  # partial: some events below the expert's minimum phase counts
        raise RuntimeError(f"expert relocation failed: {nll}/run_result.json status {status}")
    del config["picks_round"]
    located = pd.read_csv(nll / "events.csv")
    located = located[located.status == "LOCATED"].set_index("event_id")

    prompt = (run_dir / "control/task_prompt.md").read_text(encoding="utf-8")
    known = SEA_LEVEL_MARKER in prompt
    native, _ = read_candidate_catalog(run_dir / "work/catalog.csv")
    relocated = native.copy()
    ids = relocated.event_id.isin(located.index)
    loc = located.reindex(relocated.event_id[ids])
    relocated.loc[ids, "latitude"] = loc.latitude.to_numpy()
    relocated.loc[ids, "longitude"] = loc.longitude.to_numpy()
    relocated.loc[ids, "depth_km"] = (loc.depth_km - config["reference_elevation_km"]).to_numpy()
    relocated.loc[ids, "time"] = pd.to_datetime(loc.origin_time_utc, format="ISO8601", utc=True).map(
        lambda x: x.timestamp()).to_numpy()
    relocated.loc[~ids, ["latitude", "longitude", "depth_km"]] = np.nan  # not relocatable by the expert locator
    relocated = relocated.sort_values("time").reset_index(drop=True)
    pd.DataFrame(relocated).to_csv(out / "catalog_relocated.csv", index=False)

    ceiling = ceilings(case.refs)
    rows = {}
    for name, events, datum_known in (("agent_locations", native, known), ("expert_locator", relocated, True)):
        pop = Population(key="candidate", events=events, depth_known=datum_known)
        pop.events = events[in_mask(events, case.mask, depth_known=datum_known)].reset_index(drop=True)
        score = _strip(score_population(pop, case.refs, expert=case.expert.get("final"), center=case.center,
                                        off_structure_km=case.config["off_structure_km"], primary=case.primary,
                                        mask=case.mask))
        h = headline(score, case, ceiling)
        rows[name] = {k: h.get(k) for k in KEYS}
        rows[name]["events_in_mask"] = int(len(pop.events))
    report = {"run": str(run_dir.relative_to(case.task_dir)),
              "picks_round": yaml.safe_load((case.task_dir / EXPERT_DIR / "expert_ladder.yaml").read_text())["swap"]["picks_round"],
              "location_method": config["location_method"], "station_delays": False,
              "agent_events": int(len(native)), "relocated": int(ids.sum()),
              "arrivals_used": int(len(pd.read_csv(arrivals))), "rows": rows}
    (out / "swap.json").write_text(json.dumps(report, indent=1) + "\n")
    return report
