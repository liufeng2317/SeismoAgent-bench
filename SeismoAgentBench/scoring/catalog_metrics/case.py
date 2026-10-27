"""Case configuration and scoring entry points (docs/framework/03_EVALUATION_METRICS.md).

Each task package provides ``evaluation/metrics_v1.yaml`` (mask, roles,
datums, expert catalogs, leakage patterns). The reference cohorts come from
``references_loader``: ``stage05`` reads them through the case's expert
stage-05 module and its hard count gates; ``adapter`` calls
``load_references(task_dir, config)`` in ``evaluation/metrics_v1_adapter.py``.
Either returns masked DataFrames with ``time``, ``latitude``, ``longitude``,
``depth_km`` (in the reference's own datum), ``magnitude`` and optionally
``event_id``, ``magnitude_type``. Everything else is shared.
"""

from __future__ import annotations

import importlib.util
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import yaml

from . import METRICS_VERSION
from .audit import LABEL_FILE, SAMPLE_FILE, audited_false_rate, sample_unsupported
from .metrics import ceilings, effective_recall, score_population
from .process import consistency, contract_status, process_metrics
from .tables import ROLES, Population, epoch_seconds, in_mask, read_candidate_catalog, standardize

CONFIG_FILE = "metrics_v1.yaml"
ADAPTER_FILE = "metrics_v1_adapter.py"
RUN_SCORE_FILE = "metrics_v1.json"
BASELINE_FILE = "metrics_v1_baseline.json"
FIGURE_FILE = "location_diagnostics.png"
SEA_LEVEL_MARKER = "below sea level"


@dataclass
class Case:
    task_dir: Path
    config: dict
    mask: dict
    center: tuple
    refs: dict
    expert: dict

    @property
    def primary(self) -> dict:
        return self.config["primary"]


def _depth_offset(datum: str, config: dict) -> float | None:
    if datum == "sea_level":
        return 0.0
    if datum == "surface":
        return -float(config["surface_elevation_km"])
    if datum == "unknown":
        return None
    raise ValueError(f"unknown depth datum {datum!r}")


def _population(key: str, frame: pd.DataFrame, spec: dict, config: dict) -> Population:
    offset = _depth_offset(spec.get("depth_datum", "unknown"), config)
    roles = frozenset(spec.get("roles", ""))
    if not roles <= ROLES:
        raise ValueError(f"{key}: unknown roles {sorted(roles - ROLES)}")
    return Population(key=key, events=standardize(frame, depth_offset_km=offset or 0.0), roles=roles,
                      depth_known=offset is not None, time_only=bool(spec.get("time_only")),
                      gates=tuple(spec["gates"]) if spec.get("gates") else None)


def _mask(config: dict) -> dict:
    m = config["mask"]
    start, end = epoch_seconds([m["start_utc"], m["end_utc"]])
    return {"start": start, "end": end, "latitude": m["latitude"], "longitude": m["longitude"],
            "depth_bsl_km": m["depth_bsl_km"]}


def _module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def stage05_references(task_dir: Path, config: dict) -> dict:
    """Reference cohorts through the expert stage-05 readers, mask and hard count gates."""
    validation = yaml.safe_load((task_dir / "expert/00_config/validation.yaml").read_text(encoding="utf-8"))
    stage05 = _module(task_dir / "expert/04_comparison/05_match_references.py", f"stage05_{task_dir.name}")
    case_root = task_dir.parents[2] / "data" / task_dir.name
    frames, _ = stage05.read_references(case_root, validation["references"])
    out = {}
    for name in validation["references"]:
        f = frames[name][stage05.reference_mask(frames[name], validation)]
        expected = validation["expected_reference_counts"][name]
        if len(f) != expected:
            raise ValueError(f"{name}: {len(f)} masked rows != hard gate {expected}")
        out[name] = pd.DataFrame({"event_id": f.reference_id.astype(str), "time": f.time,
                                  "latitude": f.latitude, "longitude": f.longitude, "depth_km": f.depth_km,
                                  "magnitude": f["magnitude"] if "magnitude" in f else np.nan})
    return out


def _references(task_dir: Path, config: dict) -> dict:
    loader = config["references_loader"]
    if loader == "stage05":
        return stage05_references(task_dir, config)
    if loader == "adapter":
        adapter = _module(task_dir / "evaluation" / ADAPTER_FILE, f"metrics_adapter_{task_dir.name}")
        return adapter.load_references(task_dir, config)
    raise ValueError(f"unknown references_loader {loader!r}")


def _expert(key: str, spec: dict, case_cfg: dict, task_dir: Path, mask: dict) -> Population:
    frame = pd.read_csv(task_dir / spec["path"], dtype=str, keep_default_na=False).replace({"": np.nan})
    for column, value in (spec.get("keep") or {}).items():
        frame = frame[frame[column] == value]
    rename = {spec["time_column"]: "time", spec["depth_column"]: "depth_km"}
    frame = frame.drop(columns=[c for c in rename.values() if c in frame and c not in rename]).rename(columns=rename)
    pop = _population(key, frame, {"roles": "", "depth_datum": spec["depth_datum"]}, case_cfg)
    pop.events = pop.events[in_mask(pop.events, mask)].reset_index(drop=True)
    pop.notes = {"path": spec["path"], "events": int(len(pop.events))}
    return pop


def load_case(task_dir: Path) -> Case:
    task_dir = task_dir.resolve()
    config = yaml.safe_load((task_dir / "evaluation" / CONFIG_FILE).read_text(encoding="utf-8"))
    if config.get("metrics_version") != METRICS_VERSION:
        raise ValueError(f"{CONFIG_FILE}: metrics_version {config.get('metrics_version')} != {METRICS_VERSION}")
    mask = _mask(config)
    frames = _references(task_dir, config)
    if set(frames) != set(config["references"]):
        raise ValueError(f"adapter references {sorted(frames)} != config {sorted(config['references'])}")
    refs = {k: _population(k, frames[k], config["references"][k], config) for k in config["references"]}
    expert = {k: _expert(f"expert_{k}", spec, config, task_dir, mask) for k, spec in config["expert"].items()}
    center = (float(np.mean(config["mask"]["longitude"])), float(np.mean(config["mask"]["latitude"])))
    return Case(task_dir, config, mask, center, refs, expert)


def _strip(score: dict) -> dict:
    score["union_support"].pop("unsupported_index", None)
    return score


def headline(score: dict, case: Case, ceiling: dict) -> dict:
    p = case.primary
    det = score["versus"][p["detection"]]["detection"]
    recall = effective_recall(det)
    ceil = ceiling[p["detection"]]["value"]
    loc = score["versus"][p["location"]].get("location", {})
    depth = score.get("depth_profile") or {}
    return {"recall": recall, "ceiling": ceil,
            "recall_norm": round(recall / ceil, 4) if recall is not None and ceil else None,
            "union_support": score["union_support"]["fraction"],
            "epi_median_km": loc.get("epi_median_km"), "shift_km": loc.get("shift_km"),
            "scatter_median_km": loc.get("scatter_median_km"), "epi_gt5km": loc.get("epi_gt5km"),
            "dz_median_km": loc.get("dz_median_km"), "depth_datum_known": loc.get("depth_datum_known"),
            "depth_mode_share": depth.get("mode_share"), "depth_band_share": depth.get("band_share"),
            "off_structure_fraction": score["off_structure"]["fraction"],
            "off_structure_after_shift": (score.get("off_structure_after_shift") or {}).get("fraction")}


def _scorer_record() -> dict:
    from SeismoAgentBench.execution.version import tools_snapshot
    snap = tools_snapshot(Path(__file__).resolve().parent)
    return {"metrics_version": METRICS_VERSION, "scorer_commit": snap["commit"], "scorer_dirty": snap["dirty"],
            "generated_utc": datetime.now(timezone.utc).isoformat(timespec="seconds")}


def _references_record(case: Case) -> dict:
    return {k: {"events": int(len(r.events)), "roles": "".join(sorted(r.roles)), "depth_known": r.depth_known,
                "time_only": r.time_only, "gates": list(r.gates) if r.gates else None}
            for k, r in case.refs.items()}


def score_baseline(task_dir: Path, *, write: bool = True) -> dict:
    """Ceilings plus reference, expert-final and expert-blind rows (§4, §7)."""
    case = load_case(task_dir)
    ceiling = ceilings(case.refs)
    rows = {}
    for key, ref in case.refs.items():  # U excludes the expert for reference rows (§5 L1)
        rows[key] = _strip(score_population(ref, case.refs, expert=None, center=case.center,
                                            off_structure_km=case.config["off_structure_km"],
                                        location_ref=case.primary["location"]))
    for key, pop in case.expert.items():
        score = _strip(score_population(pop, case.refs, expert=None, center=case.center,
                                        off_structure_km=case.config["off_structure_km"],
                                        location_ref=case.primary["location"]))
        score["headline"] = headline(score, case, ceiling)
        rows[pop.key] = score
    report = {**_scorer_record(), "task": case.task_dir.name, "references": _references_record(case),
              "expert": {k: v.notes for k, v in case.expert.items()}, "ceilings": ceiling, "rows": rows}
    if write:
        out = case.task_dir / "evaluation" / BASELINE_FILE
        out.write_text(json.dumps(report, indent=1) + "\n", encoding="utf-8")
    return report


def run_layout(task_dir: Path, run_dir: Path) -> dict:
    parts = run_dir.resolve().relative_to(task_dir.resolve()).parts
    if len(parts) != 5 or parts[0] != "runs":
        raise ValueError(f"run directory must be <task>/runs/<variant>/<harness>/<model>/<run_id>: {run_dir}")
    return {"variant": parts[1], "harness": parts[2], "model": parts[3], "run_id": parts[4],
            "path": "/".join(parts)}


def score_run(task_dir: Path, run_dir: Path, *, write: bool = True) -> dict:
    """Score one run; a run without a contract-valid catalog is scored as failed (§6)."""
    case = load_case(task_dir)
    run_dir = run_dir.resolve()
    layout = run_layout(case.task_dir, run_dir)
    work = run_dir / "work"
    contract_path = run_dir / "control" / "output_contract.json"
    if not contract_path.is_file():  # runs older than the control snapshot (retired base variant)
        contract_path = case.task_dir / "output_contract_min.json"
    contract = json.loads(contract_path.read_text(encoding="utf-8"))
    status = contract_status(work, contract)
    status["contract"] = str(contract_path.relative_to(case.task_dir))
    report = {**_scorer_record(), "task": case.task_dir.name, "run": layout, "completion": status,
              "process": process_metrics(run_dir, case.config.get("leakage_patterns", []))}
    out_dir = run_dir / "evaluation"
    if status["completed"]:
        prompt = (run_dir / "control" / "task_prompt.md").read_text(encoding="utf-8")
        depth_known = SEA_LEVEL_MARKER in prompt
        events, notes = read_candidate_catalog(work / "catalog.csv")
        cand = Population(key="candidate", events=events, depth_known=depth_known)
        inside = in_mask(events, case.mask, depth_known=depth_known)
        cand.events = events[inside].reset_index(drop=True)
        notes.update({"scored": int(len(events)), "in_mask": int(inside.sum()),
                      "out_of_mask_fraction": round(float(1 - inside.mean()), 4) if len(events) else None,
                      "depth_datum": "sea_level" if depth_known else "unknown (run predates the convention)"})
        raw_catalog = pd.read_csv(work / "catalog.csv", dtype=str, keep_default_na=False)
        raw_picks = pd.read_csv(work / "picks.csv", dtype=str, keep_default_na=False)
        status["consistency"] = consistency(raw_catalog, raw_picks)
        score = score_population(cand, case.refs, expert=case.expert.get("final"), center=case.center,
                                 off_structure_km=case.config["off_structure_km"],
                                 location_ref=case.primary["location"])
        ceiling = ceilings(case.refs)
        unsupported = score["union_support"]["unsupported_index"]
        sample = sample_unsupported(cand, unsupported)
        report.update({"catalog": notes, "scores": _strip(score), "headline": headline(score, case, ceiling)})
        audit = audited_false_rate(out_dir / LABEL_FILE, 1 - score["union_support"]["fraction"]
                                   if score["union_support"]["fraction"] is not None else None)
        report["headline"]["audited_false_rate"] = audit["rate"] if audit else None
        if write:
            from .figures import location_figure
            ref = case.refs[case.primary["location"]]
            location_figure(out_dir / FIGURE_FILE, cand, ref, [r for r in case.refs.values() if "S" in r.roles],
                            case.expert, case.center, off_structure_km=case.config["off_structure_km"],
                            title=f"{case.task_dir.name} - {layout['path']}")
        report["audit"] = {"sample_file": SAMPLE_FILE, "sampled": int(len(sample)),
                           "unsupported": int(len(unsupported)), "labels": audit}
    else:
        report["headline"] = {"recall": 0.0, "recall_norm": 0.0}
        sample = None
    if write:
        out_dir.mkdir(exist_ok=True)
        if sample is not None and not (out_dir / SAMPLE_FILE).exists():
            sample.to_csv(out_dir / SAMPLE_FILE, index=False)  # never redrawn once reviewed
        (out_dir / RUN_SCORE_FILE).write_text(json.dumps(report, indent=1, default=_jsonable) + "\n",
                                              encoding="utf-8")
    return report


def _jsonable(value: Any):
    if isinstance(value, np.generic):
        return value.item()
    raise TypeError(f"not JSON serialisable: {type(value)}")
