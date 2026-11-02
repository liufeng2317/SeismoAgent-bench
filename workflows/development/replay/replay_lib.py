"""Offline replay of recorded Agent runs: build a candidate product from a run's own picks, check and compare it
as the Agent would (no reference), then score both against the references to see whether the decision was right.

A scenario names a run, an intervention and the kind of change; optionally a pilot rule. Everything the
Agent could see (checker reports, compare verdicts, pilot predictions) is kept apart from what only the
benchmark sees (scores, trusted-catalog verdicts). Results are cached per run and intervention.
"""

from __future__ import annotations

import hashlib
import json
import math
import subprocess
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
CHECKER = ROOT / "seismotools/checker/interface/run.py"
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "seismotools/checker/source"))

from SeismoAgentBench.scoring.catalog_metrics.case import SEA_LEVEL_MARKER, final_headline, headline, load_case  # noqa: E402
from SeismoAgentBench.scoring.catalog_metrics.metrics import ceilings, score_population  # noqa: E402
from SeismoAgentBench.scoring.catalog_metrics.tables import Population, in_mask, read_candidate_catalog  # noqa: E402
from SeismoAgentBench.scoring.catalog_metrics.trust import trust_verdict  # noqa: E402
from catalog_checker.checks import DEFAULTS, Data  # noqa: E402
from catalog_checker.compare import compare_reports  # noqa: E402
from catalog_checker.ensemble import ENSEMBLE_DEFAULTS, LOCATE, _locate, _model_rows  # noqa: E402
from catalog_checker.io import read_catalog, read_picks, read_stations  # noqa: E402
from catalog_checker.velocity import regional_models  # noqa: E402

KEYS = ["recall_final", "time_bias_final_s", "time_mad_final_s", "dz_final_km", "shift_final_km", "scatter_final_km",
        "off_structure_fraction", "depth_mode_share", "dmag_median", "out_of_mask_fraction"]
# trusted-catalog dimensions a kind of change can affect
# (location changes move events in and out of the study region, so reality's inside_region counts for them)
RELEVANT = {"velocity_model": ("reality", "time", "space"), "location_method": ("reality", "time", "space"),
            "relocation": ("reality", "time", "space"),
            "magnitude": ("strength",), "event_selection": ("reality", "time", "space"), "picks": ("reality", "time", "space"),
            "association": ("reality", "time", "space"), "other": ("reality", "time", "space", "strength")}
_cases: dict = {}


# ------------------------------------------------------------------ runs and products

class Run:
    def __init__(self, case: str, run: str):
        self.case, self.run = case, run
        self.dir = ROOT / "workflows/tasks" / case / "runs" / run
        self.work = self.dir / "work"
        self.stations = (self.work / "input/waveforms/stations").resolve()
        self.waveforms = (self.work / "input/waveforms/data").resolve()
        self.catalog = self.work / "catalog.csv"
        self.picks = self.work / "picks.csv"
        if not self.catalog.is_file():
            raise FileNotFoundError(self.catalog)

    @property
    def key(self) -> str:
        return f"{self.case}/{self.run.replace('/', '__')}"

    def raw_catalog(self) -> pd.DataFrame:
        return pd.read_csv(self.catalog, dtype=str, keep_default_na=False)

    def data(self) -> Data:
        return Data(read_catalog(self.catalog), read_picks(self.picks), read_stations(self.stations))


def spec_hash(spec) -> str:
    return hashlib.sha1(json.dumps(spec, sort_keys=True, default=str).encode()).hexdigest()[:10]


def write_subset(run: Run, event_ids, out: Path) -> tuple[Path, Path]:
    """The run's catalog and picks restricted to the given events (picks of other events dropped)."""
    out.mkdir(parents=True, exist_ok=True)
    ids = set(event_ids)
    cat = run.raw_catalog()
    cat[cat.event_id.isin(ids)].to_csv(out / "catalog.csv", index=False)
    pk = pd.read_csv(run.picks, dtype=str, keep_default_na=False)
    pk[pk.event_id.isin(ids)].to_csv(out / "picks.csv", index=False)
    return out / "catalog.csv", out / "picks.csv"


# ------------------------------------------------------------------ interventions

def _velocity_rows(run: Run, d: Data, spec: dict) -> list:
    model = spec["model"]
    if model == "file":  # "depth vp vs" rows, depths below file_reference_km (km above sea level)
        ref = float(spec.get("file_reference_km", 0.0))
        tops = [tuple(map(float, line.split()[:3])) for line in Path(spec["path"]).read_text().splitlines()
                if line.strip() and not line.lstrip().startswith("#")]
        if spec.get("layering", "step") == "linear":
            z = np.arange(tops[0][0], tops[-1][0] + 0.001, 0.25)
            tops = [(float(zz), float(np.interp(zz, [t[0] for t in tops], [t[1] for t in tops])),
                     float(np.interp(zz, [t[0] for t in tops], [t[2] for t in tops]))) for zz in z]
        return [(t - ref, vp, vs) for t, vp, vs in tops]
    if model in ("litho1", "crust1"):
        ev = d.events.dropna(subset=["latitude"])
        return regional_models(np.r_[d.stations.latitude, ev.latitude.median()],
                               np.r_[d.stations.longitude, ev.longitude.median()])[model]["rows"]
    datum_arg = spec.get("datum_km", "stations")
    datum = float(d.stations.elevation_m.mean()) / 1000.0 if datum_arg == "stations" else float(datum_arg)
    m = json.load(open(ROOT / f"data/{run.case}/data/models/velocity_models.json"))["models"][model]["rows"]
    tops = [(r.get("top_of_layer_km", r.get("depth_km")), r["vp_km_s"], r["vs_km_s"]) for r in m]
    if spec.get("layering", "step") == "linear":  # nodes interpolated linearly, densified into 0.25 km steps
        z = np.arange(0, tops[-1][0] + 0.001, 0.25)
        tops = [(float(zz), float(np.interp(zz, [t[0] for t in tops], [t[1] for t in tops])),
                 float(np.interp(zz, [t[0] for t in tops], [t[2] for t in tops]))) for zz in z]
    return [(t - datum, vp, vs) for t, vp, vs in tops]  # layer tops below sea level


def relocate(run: Run, spec: dict, out: Path, event_ids=None, workers: int = 16) -> pd.DataFrame:
    """Relocate the run's events (or a subset) with its own picks and another velocity model.

    usage "expert": reference elevation = model datum, depth search 0–20 km below it, EDT_OT_WT (how a
    regional model is used in practice); usage "checker": the checker's generic setup (reference at the
    highest station, grid to 1.5× the 95th-percentile catalog depth)."""
    out.mkdir(parents=True, exist_ok=True)
    done = out / "relocated_events.csv"
    if done.is_file():
        return pd.read_csv(done)
    d = run.data()
    rows = _velocity_rows(run, d, spec)
    picks = d.picks.drop_duplicates(["event_id", "station_id", "phase"])
    if event_ids is not None:
        picks = picks[picks.event_id.isin(set(event_ids))]
    pd.DataFrame({"event_id": picks.event_id, "pick_id": np.arange(len(picks)).astype(str), "station_id": picks.station_id,
                  "phase": picks.phase, "time_utc": pd.to_datetime(picks.time, unit="s", utc=True).dt.strftime("%Y-%m-%dT%H:%M:%S.%fZ")}
                 ).to_csv(out / "arrivals.csv", index=False)
    d.stations[["station_id", "latitude", "longitude", "elevation_m"]].to_csv(out / "stations.csv", index=False)
    c = {**DEFAULTS, **ENSEMBLE_DEFAULTS, "ensemble_workers": workers, "ensemble_timeout_s": 30 * 3600}
    if spec.get("usage", "expert") == "expert":
        datum_arg = spec.get("datum_km", "stations")
        ref_elev = float(d.stations.elevation_m.mean()) / 1000.0 if datum_arg == "stations" else float(datum_arg)
        ev = d.events.dropna(subset=["latitude"])
        lat = np.nanpercentile(ev.latitude, [0.1, 99.9])
        lon = np.nanpercentile(ev.longitude, [0.1, 99.9])
        cfg = {"reference_elevation_km": ref_elev, "velocity_layering": "step", "grid_depth_km": [-3.0, 35.0],
               "region": {"latitude": [float(lat[0] - 0.18), float(lat[1] + 0.18)],
                          "longitude": [float(lon[0] - 0.18), float(lon[1] + 0.18)], "depth_km": [0, 20]},
               "location_method": "EDT_OT_WT", "pick_error_s": {"P": 0.1, "S": 0.2},
               **({"grid_spacing_km": spec["grid_spacing_km"]} if spec.get("grid_spacing_km") else {})}
        (out / "relocated_model.txt").write_text("".join(f"{z:.3f} {vp:.3f} {vs:.3f}\n" for z, vp, vs in _model_rows(rows, ref_elev)))
        (out / "relocated_config.json").write_text(json.dumps(cfg))
        subprocess.run([sys.executable, "-I", str(LOCATE), "--arrivals", str(out / "arrivals.csv"), "--stations", str(out / "stations.csv"),
                        "--velocity-model", str(out / "relocated_model.txt"), "--config", str(out / "relocated_config.json"),
                        "--output-dir", str(out / "relocated"), "--workers", str(workers), "--quiet", "--overwrite"],
                       check=False, capture_output=True)
        loc = pd.read_csv(out / "relocated/events.csv")
        loc = loc[loc.status == "LOCATED"].copy()
        loc["depth_bsl"] = loc.depth_km - ref_elev
        loc["t"] = (pd.to_datetime(loc.origin_time_utc, utc=True, format="ISO8601") - pd.Timestamp(0, tz="UTC")).dt.total_seconds()
        loc = loc[["event_id", "depth_bsl", "t", "latitude", "longitude", "rms_s"]]
    else:
        ref_elev = math.ceil(float(d.stations.elevation_m.max()) / 100.0) / 10.0
        depth_bottom = max(30.0, float(np.nanpercentile(d.events.depth_km.dropna(), 95)) * 1.5)
        loc = _locate(out, "relocated", rows, ref_elev, depth_bottom, c)
        loc = loc if loc is not None else pd.DataFrame(columns=["event_id", "depth_bsl", "t", "latitude", "longitude", "rms_s"])
    loc.to_csv(done, index=False)
    return loc


def apply_relocation(raw: pd.DataFrame, loc: pd.DataFrame, unlocated: str = "keep") -> pd.DataFrame:
    """The catalog with the hypocentre and origin time of every relocated event replaced."""
    new = raw.copy()
    loc = loc.set_index("event_id")
    hit = new.event_id.isin(loc.index)
    ids = new.event_id[hit]
    new.loc[hit, "latitude"] = loc.loc[ids, "latitude"].map(lambda v: f"{v:.6f}").to_numpy()
    new.loc[hit, "longitude"] = loc.loc[ids, "longitude"].map(lambda v: f"{v:.6f}").to_numpy()
    new.loc[hit, "depth_km"] = loc.loc[ids, "depth_bsl"].map(lambda v: f"{v:.4f}").to_numpy()
    new.loc[hit, "origin_time_utc"] = pd.to_datetime(loc.loc[ids, "t"], unit="s", utc=True).dt.strftime("%Y-%m-%dT%H:%M:%S.%fZ").to_numpy()
    return new if unlocated == "keep" else new[hit]


def _num(raw: pd.DataFrame, col: str) -> pd.Series:
    return pd.to_numeric(raw[col], errors="coerce")


def candidate(run: Run, spec: dict, out: Path, event_ids=None, workers: int = 16) -> Path:
    """Write the candidate catalog for an intervention (restricted to ``event_ids`` if given)."""
    out.mkdir(parents=True, exist_ok=True)
    path = out / "catalog.csv"
    if path.is_file():
        return path
    raw = run.raw_catalog()
    if event_ids is not None:
        raw = raw[raw.event_id.isin(set(event_ids))]
    kind = spec["type"]
    if kind == "relocate":
        new = apply_relocation(raw, relocate(run, spec, out / "relocation", event_ids, workers), spec.get("unlocated", "keep"))
    elif kind == "catalog":  # a candidate built elsewhere
        new = pd.read_csv(spec["path"], dtype=str, keep_default_na=False)
        new = new[new.event_id.isin(set(raw.event_id))]
    elif kind == "depth_shift":
        new = raw.copy()
        new["depth_km"] = (_num(raw, "depth_km") + spec["dz_km"]).map(lambda v: f"{v:.4f}")
    elif kind == "magnitude_shift":
        new = raw.copy()
        new["magnitude"] = (_num(raw, "magnitude") + spec["dm"]).map(lambda v: f"{v:.3f}")
    elif kind == "drop_few_picks":
        pk = pd.read_csv(run.picks, dtype=str, keep_default_na=False)
        pk = pk[(pk.get("status", "") != "rejected") & (pk.event_id != "")]
        n = pk[pk.phase.str.upper().str[0] == "P"].groupby("event_id").size()
        new = raw[raw.event_id.map(n).fillna(0) >= spec.get("min_p", 4)]
    elif kind == "drop_pileup":
        z = _num(raw, "depth_km").round(2)
        new = raw[z != z.value_counts().idxmax()]
    else:
        raise ValueError(f"unknown intervention {kind}")
    new.to_csv(path, index=False)
    return path


# ------------------------------------------------------------------ pilot subsets

def pilot_events(run: Run, rule: str, n: int, seed: int = 0) -> list[str]:
    """A pilot batch of events chosen by a fixed rule, from the run's catalog and picks only."""
    d = run.data()
    counts = d.picks.groupby("event_id").size()
    ev = d.events[d.events.event_id.isin(counts.index) & d.events[["latitude", "longitude", "depth_km"]].notna().all(axis=1)].copy()
    ev["n"] = ev.event_id.map(counts)
    rng = np.random.default_rng(seed)
    if len(ev) <= n:
        return list(ev.event_id)
    if rule == "best_recorded":  # the events picked at the most stations (what a careful analyst checks first)
        return list(ev.sort_values(["n", "time"], ascending=[False, True]).event_id[:n])
    if rule == "random":
        return list(ev.event_id.sample(n, random_state=seed))
    if rule == "composite":  # seismotools/checker pilot.py: representative + busiest hour + largest events
        from catalog_checker.pilot import select_events
        parts = select_events(d.events, d.picks, {"events": n, "seed": seed})
        return parts["representative"] + parts["busiest"] + parts["largest"]
    if rule in ("time_uniform", "pick_count_strata", "magnitude_strata"):
        if rule == "time_uniform":  # equal numbers from equal-duration windows: quiet periods count as much as busy ones
            key = pd.cut(ev.time, 30, labels=False)
        elif rule == "pick_count_strata":  # equal numbers from each decile of picks per event: weak events included
            key = pd.qcut(ev.n.rank(method="first"), 10, labels=False)
        else:
            m = ev.magnitude if ev.magnitude.notna().mean() > 0.5 else ev.n
            key = pd.qcut(m.rank(method="first"), 10, labels=False)
        groups = [g for _, g in ev.groupby(key)]
        per = max(1, n // len(groups))
        take = [g.event_id.sample(min(per, len(g)), random_state=int(rng.integers(1 << 30))) for g in groups]
        return list(pd.concat(take))
    raise ValueError(f"unknown pilot rule {rule}")


# ------------------------------------------------------------------ what the Agent could see

def checker_report(catalog: Path, picks: Path, run: Run, out: Path, stage: str = "location", waveforms: bool = False,
                   pilot: bool = False) -> dict:
    report = out / "checker_report.json"
    if not report.is_file():
        cmd = [sys.executable, "-W", "ignore", str(CHECKER), "--stage", stage, "--catalog", str(catalog), "--picks", str(picks),
               "--stations", str(run.stations), "--output-dir", str(out), "--no-figures"] + (["--pilot"] if pilot else [])
        if waveforms:
            cmd += ["--waveforms", str(run.waveforms)]
        subprocess.run(cmd, check=True, capture_output=True, text=True)
    return json.loads(report.read_text())


def catalog_shift(before: Path, after: Path, event_ids=None) -> dict:
    """Median change of the candidate against the current catalog over the events both locate (no reference)."""
    a = read_catalog(before).set_index("event_id")
    b = read_catalog(after).set_index("event_id")
    if event_ids is not None:
        a = a[a.index.isin(set(event_ids))]
    j = a.join(b, lsuffix="_a", rsuffix="_b", how="inner").dropna(subset=["depth_km_a", "depth_km_b"])
    moved = j[(j.depth_km_a != j.depth_km_b) | (j.time_a != j.time_b)]
    if moved.empty:
        return {"events": 0}
    lat0 = np.deg2rad(float(moved.latitude_a.median()))
    dx = (moved.longitude_b - moved.longitude_a) * 111.19 * np.cos(lat0)
    dy = (moved.latitude_b - moved.latitude_a) * 111.19
    return {"events": int(len(moved)), "dz_km": round(float((moved.depth_km_b - moved.depth_km_a).median()), 3),
            "dt_s": round(float((moved.time_b - moved.time_a).median()), 3),
            "dx_km": round(float(dx.median()), 3), "dy_km": round(float(dy.median()), 3)}


# ------------------------------------------------------------------ what only the benchmark sees

def score(run: Run, catalog: Path) -> dict:
    case = _cases.setdefault(run.case, load_case(ROOT / "workflows/tasks" / run.case))
    depth_known = SEA_LEVEL_MARKER in (run.dir / "control/task_prompt.md").read_text()
    events, _ = read_candidate_catalog(catalog)
    cand = Population(key="candidate", events=events, depth_known=depth_known)
    inside = in_mask(events, case.mask, depth_known=depth_known)
    cand.events = events[inside].reset_index(drop=True)
    s = score_population(cand, case.refs, expert=case.expert.get("final"), center=case.center,
                         off_structure_km=case.config["off_structure_km"], primary=case.primary, mask=case.mask,
                         yardstick=case.expert.get("final"))
    h = headline(s, case, ceilings(case.refs))
    h["out_of_mask_fraction"] = round(float(1 - inside.mean()), 4) if len(events) else None
    v = trust_verdict(h, final_headline(case), True)
    values = {k: (round(h[k], 3) if isinstance(h.get(k), (int, float)) else h.get(k)) for k in KEYS}
    criteria = {name: {"dimension": dim, **chk} for dim, dd in v["dimensions"].items() for name, chk in dd["checks"].items()}
    return {"values": values, "failed": v["failed"], "trusted": v["trusted"], "criteria": criteria}


def _excess(criteria: dict, dims) -> float:
    """How far the relevant criteria are beyond their thresholds, summed in units of each threshold."""
    total = 0.0
    for chk in criteria.values():
        if chk["dimension"] not in dims or chk.get("value") is None or not isinstance(chk.get("threshold"), (int, float)):
            continue
        thr = abs(chk["threshold"]) or 1.0
        val = abs(chk["value"])
        total += max(0.0, val / thr - 1.0) if chk["op"] in ("<=", "abs<=", "<") else max(0.0, 1.0 - val / thr)
    return round(total, 3)


def truth(before: dict, after: dict, change: str) -> dict:
    """Was the candidate better against the references, in the dimensions the change can affect?"""
    dims = RELEVANT.get(change, RELEVANT["other"])
    fb = [k for k in before["failed"] if before["criteria"].get(k, {}).get("dimension") in dims]
    fa = [k for k in after["failed"] if after["criteria"].get(k, {}).get("dimension") in dims]
    eb, ea = _excess(before["criteria"], dims), _excess(after["criteria"], dims)
    if len(fa) < len(fb) or (len(fa) == len(fb) and ea < 0.9 * eb):
        label = "better"
    elif len(fa) > len(fb) or (len(fa) == len(fb) and ea > 1.1 * eb + 0.05):
        label = "worse"
    else:
        label = "same"
    return {"label": label, "dimensions": list(dims), "failed_before": fb, "failed_after": fa, "excess_before": eb, "excess_after": ea}


def benchmark_view(s_base: dict, s_cand: dict, change: str, verdict: str) -> dict:
    tr = truth(s_base, s_cand, change)
    return {"before": {"values": s_base["values"], "failed": s_base["failed"]},
            "after": {"values": s_cand["values"], "failed": s_cand["failed"], "trusted": s_cand["trusted"]},
            "truth": tr, "agreement": agreement(verdict, tr["label"])}


def rescore(rec: dict) -> dict:
    """Recompute the benchmark view of a record from its cached catalogs (after a change to the scoring or truth rule)."""
    run = Run(rec["case"], rec["run"])
    after = rec.get("catalogs", {}).get("after") or str(ROOT / "workflows/development/replay/outputs/cache" / run.key /
                                                         f"{rec['intervention']['type']}_{spec_hash(rec['intervention'])}" / "full/catalog.csv")
    rec["catalogs"] = {"before": str(run.catalog), "after": after}
    rec["benchmark_view"] = benchmark_view(score(run, run.catalog), score(run, Path(after)), rec["change"], rec["agent_view"]["verdict"])
    return rec


def agreement(verdict: str, truth_label: str) -> str:
    if verdict in ("mixed", "uncertain"):
        return "undecided"
    expected = {"better": "better", "worse": "worse", "no_difference": "same"}[verdict]
    return "right" if expected == truth_label else "wrong"


# ------------------------------------------------------------------ one scenario

def run_scenario(sc: dict, out_root: Path, workers: int = 16, log=print) -> dict:
    run = Run(sc["case"], sc["run"])
    spec, change, stage = sc["intervention"], sc.get("change", "other"), sc.get("stage", "location")
    waveforms = stage in ("magnitude", "all")
    base_dir = out_root / "cache" / run.key
    cand_dir = base_dir / f"{spec['type']}_{spec_hash(spec)}"
    rec = {"name": sc["name"], "case": run.case, "run": run.run, "intervention": spec, "change": change, "stage": stage}
    t0 = time.time()
    log(f"[{sc['name']}] candidate ...")
    full_cat = candidate(run, spec, cand_dir / "full", workers=workers)
    rec["cost_s"] = {"candidate": round(time.time() - t0, 1)}
    t1 = time.time()
    base_rep = checker_report(run.catalog, run.picks, run, base_dir / f"base_{stage}", stage, waveforms)
    cand_rep = checker_report(full_cat, run.picks, run, cand_dir / "full" / f"checker_{stage}", stage, waveforms)
    cmp = compare_reports(base_rep, cand_rep, change)
    rec["cost_s"]["checker"] = round(time.time() - t1, 1)
    rec["agent_view"] = {"verdict": cmp["verdict"], "improved": cmp["improved"], "worsened": cmp["worsened"],
                         "not_counted": cmp["not_counted"], "flags_before": cmp["flags_before"], "flags_after": cmp["flags_after"],
                         "catalog_shift": catalog_shift(run.catalog, full_cat), "notes": cmp["notes"]}
    log(f"[{sc['name']}] compare: {cmp['verdict']} (+{cmp['improved']} -{cmp['worsened']}); scoring ...")
    s_base, s_cand = score(run, run.catalog), score(run, full_cat)
    tr = truth(s_base, s_cand, change)
    rec["catalogs"] = {"before": str(run.catalog), "after": str(full_cat)}
    rec["benchmark_view"] = benchmark_view(s_base, s_cand, change, cmp["verdict"])
    pilots = []
    for rule in sc.get("pilots", []):
        n = sc.get("pilot_events", 300)
        ids = pilot_events(run, rule, n)
        pdir = cand_dir / f"pilot_{rule}_{n}" if rule != "composite" else cand_dir / f"pilot_{rule}_{n}_v2"
        flag_pilot = rule == "composite"  # the checker's pilot mode: population checks reported, not judged
        log(f"[{sc['name']}] pilot {rule} ({len(ids)} events) ...")
        tp = time.time()
        b_cat, b_pk = write_subset(run, ids, pdir / "base")
        p_cat = candidate(run, spec, pdir / "candidate", event_ids=ids, workers=workers)
        b_rep = checker_report(b_cat, b_pk, run, pdir / "base" / f"checker_{stage}", stage, waveforms, flag_pilot)
        c_rep = checker_report(p_cat, b_pk, run, pdir / "candidate" / f"checker_{stage}", stage, waveforms, flag_pilot)
        pc = compare_reports(b_rep, c_rep, change)
        rep_ids = None
        if rule == "composite":
            from catalog_checker.pilot import select_events
            d = run.data()
            rep_ids = select_events(d.events, d.picks, {"events": n})["representative"]
        shift = catalog_shift(b_cat, p_cat, rep_ids)
        pred = {k: (round(s_base["values"][kk] + shift[k], 3) if shift.get(k) is not None and s_base["values"].get(kk) is not None else None)
                for k, kk in (("dz_km", "dz_final_km"), ("dt_s", "time_bias_final_s"))}
        pilots.append({"rule": rule, "events": len(ids), "cost_s": round(time.time() - tp, 1), "verdict": pc["verdict"],
                       "improved": pc["improved"], "worsened": pc["worsened"], "same_verdict_as_full": pc["verdict"] == cmp["verdict"],
                       "catalog_shift": shift,
                       "predicted": {"dz_final_km": pred["dz_km"], "time_bias_final_s": pred["dt_s"]},
                       "actual": {"dz_final_km": s_cand["values"]["dz_final_km"], "time_bias_final_s": s_cand["values"]["time_bias_final_s"]},
                       "checks": {r["id"]: [r["before"], r["after"]] for r in pc["checks"] if r["change"] != "same"}})
    rec["pilots"] = pilots
    rec["cost_s"]["total"] = round(time.time() - t0, 1)
    return rec
