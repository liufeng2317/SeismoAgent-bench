#!/usr/bin/env python3
"""Stage 70: compare association and location methods on the same r2 PhaseNet picks.

Every arm runs a seismotools interface on identical inputs (r2 picks, stations,
Keranen 2013 model as step layers, 0.28-km datum, no station delays):

  association  GaMMA (the r2 stage-03 association), PyOcto, REAL
  location     NonLinLoc GAU_ANALYTIC / EDT / EDT_OT_WT, HypoInverse — for every association
  model        GaMMA + NLL-GAU with Vp and Vs scaled by model_scaling
  relative     ccdt + GrowClust on the GaMMA + NLL-GAU catalog

Each catalog is scored like the evaluation layer (evaluation/scripts/
plot_evaluation_comparison.py: masked references, greedy 4 s / 15 km pairs).
The cross-method spread of each event's location (locators within one
association; the scaled models) is tested as an internal quality indicator
against the error relative to Cochran et al. (2020).

Resumable: an arm whose run_result.json reports success is not rerun.
Outputs: export/<source_round>/70_method_comparison/{inputs,associate,locate,relative}/,
scores.csv, spread_events.csv, report.json, summary.md.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import shutil
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import yaml
from scipy.stats import spearmanr

EXPERT = Path(__file__).resolve().parents[1]
TASK = EXPERT.parent
ROOT = EXPERT.parents[3]
TOOLS = ROOT / "seismotools"
PY = sys.executable
CFG = yaml.safe_load((EXPERT / "00_config/method_comparison.yaml").read_text())
SRC = EXPERT / "export" / CFG["source_round"]
OUT = SRC / "70_method_comparison"
WAVES = (EXPERT / yaml.safe_load((EXPERT / "00_config/config.yaml").read_text())["data_root"] / "data").resolve()
spec = importlib.util.spec_from_file_location("evaluation", TASK / "evaluation/scripts/plot_evaluation_comparison.py")
E = importlib.util.module_from_spec(spec)
spec.loader.exec_module(E)


def done(path: Path) -> bool:
    f = path / "run_result.json"
    return f.exists() and json.loads(f.read_text()).get("status") == "success"


def tool(cmd: list, out: Path, log: Path) -> None:
    if done(out):
        return
    with log.open("w") as h:
        subprocess.run([PY, "-I", *map(str, cmd), "--output-dir", str(out), "--overwrite"], stdout=h,
                       stderr=subprocess.STDOUT, check=False)
    if not done(out):
        raise RuntimeError(f"{out.name} failed; see {log}")


# ---------------------------------------------------------------- inputs
def prepare() -> dict:
    d = OUT / "inputs"
    d.mkdir(parents=True, exist_ok=True)
    inputs = json.loads((SRC / "03_associate_gamma/full/inputs.json").read_text())
    s = inputs["settings"]
    p = pd.read_csv(SRC / "02_pick_phasenet/full/picks.csv")
    p[["pick_id", "station_id", "phase", "time_utc", "probability"]].to_csv(d / "picks.csv", index=False)
    st = pd.read_csv(SRC / "03_associate_gamma/full/stations.csv")
    st.assign(elevation_m=st.elevation_m - st.sensor_depth_m)[["station_id", "latitude", "longitude", "elevation_m"]] \
        .to_csv(d / "stations.csv", index=False)
    rows = inputs["model_source"]["rows"]
    for f in [1.0] + CFG["model_scaling"]:
        name = "model.txt" if f == 1.0 else f"model_x{f:.2f}.txt"
        (d / name).write_text("".join(f"{r['top_of_layer_km']} {r['vp_km_s'] * f:.4f} {r['vs_km_s'] * f:.4f}\n"
                                      for r in rows))
    region = {"latitude": s["latitude_bounds"], "longitude": s["longitude_bounds"], "depth_km": s["depth_bounds_km"]}
    return {"region": region, "datum": s["reference_elevation_km"], "center": s["projection_center"],
            "layering": s["velocity_layering"], "picks": len(p)}


# ----------------------------------------------------------- association
def associate(ctx: dict) -> dict:
    d, inp = OUT / "associate", OUT / "inputs"
    d.mkdir(exist_ok=True)
    picks = pd.read_csv(inp / "picks.csv")
    out = {}
    g = pd.read_csv(SRC / "03_associate_gamma/full/picks.csv", keep_default_na=False)
    g = g[g.association_status == "associated"][["event_id", "pick_id", "station_id", "phase", "time_utc"]]
    (d / "gamma").mkdir(exist_ok=True)
    g.to_csv(d / "gamma/arrivals.csv", index=False)
    out["gamma"] = g.event_id.nunique()
    for name, extra in (("pyocto", CFG["association"]["pyocto"]), ("real", CFG["association"]["real"])):
        cfg = {"region": ctx["region"], "reference_elevation_km": ctx["datum"], "velocity_layering": ctx["layering"],
               **extra}
        (d / f"{name}.json").write_text(json.dumps(cfg))
        run = d / f"{name}_run"
        tool([TOOLS / name / "interface/run.py", "--picks", inp / "picks.csv", "--stations", inp / "stations.csv",
              "--velocity-model", inp / "model.txt", "--config", d / f"{name}.json", "--workers", CFG["workers"],
              "--quiet"], run, d / f"{name}.log")
        a = pd.read_csv(run / "assignments.csv", keep_default_na=False)
        a = a[a.assignment_status == "assigned"].merge(picks, on="pick_id")
        a["event_id"] = name + "_" + a.event_index.astype(str)
        (d / name).mkdir(exist_ok=True)
        a[["event_id", "pick_id", "station_id", "phase", "time_utc"]].to_csv(d / name / "arrivals.csv", index=False)
        out[name] = a.event_id.nunique()
    return out


# -------------------------------------------------------------- location
def locate(ctx: dict) -> dict:
    d, inp = OUT / "locate", OUT / "inputs"
    d.mkdir(exist_ok=True)
    loc = CFG["location"]
    nll_base = {"reference_elevation_km": ctx["datum"], "projection_center": ctx["center"], "region": ctx["region"],
                "velocity_layering": ctx["layering"], **loc["nll"]}
    arms = []
    for assoc in ("gamma", "pyocto", "real"):
        for arm, method in loc["nll_methods"].items():
            arms.append((assoc, arm, "nll", {**nll_base, "location_method": method}, "model.txt"))
        arms.append((assoc, "hypoinverse", "hypoinverse", loc["hypoinverse"], "model.txt"))
    for f in CFG["model_scaling"]:
        arms.append(("gamma", f"nll_gau_x{f:.2f}", "nll", {**nll_base, "location_method": "GAU_ANALYTIC"},
                     f"model_x{f:.2f}.txt"))
    out = {}
    for assoc, arm, kind, cfg, model in arms:
        name = f"{assoc}__{arm}"
        (d / f"{name}.json").write_text(json.dumps(cfg))
        args = ["--arrivals", OUT / "associate" / assoc / "arrivals.csv", "--stations", inp / "stations.csv",
                "--velocity-model", inp / model, "--config", d / f"{name}.json", "--quiet"]
        script = TOOLS / ("nonlinloc/interface/locate.py" if kind == "nll" else "hypoinverse/interface/run.py")
        tool([script, *args, *(["--workers", CFG["workers"]] if kind == "nll" else [])], d / name, d / f"{name}.log")
        shutil.rmtree(d / name / "grids", ignore_errors=True)       # ~70 MB per arm, regenerable
        out[name] = json.loads((d / name / "run_result.json").read_text()).get("located")
    return out


# -------------------------------------------------------------- relative
def relative() -> dict:
    d, inp = OUT / "relative", OUT / "inputs"
    d.mkdir(exist_ok=True)
    e = pd.read_csv(OUT / "locate/gamma__nll_gau/events.csv")
    e = e[e.status == "LOCATED"][["event_id", "origin_time_utc", "latitude", "longitude", "depth_km"]]
    e.to_csv(d / "events.csv", index=False)
    a = pd.read_csv(OUT / "associate/gamma/arrivals.csv")
    a[a.event_id.isin(e.event_id)].to_csv(d / "arrivals.csv", index=False)
    (d / "ccdt.json").write_text(json.dumps(CFG["relative"]["ccdt"]))
    tool([TOOLS / "cross_correlation/interface/run.py", "--events", d / "events.csv", "--arrivals",
          d / "arrivals.csv", "--waveforms", WAVES, "--config", d / "ccdt.json", "--workers", CFG["workers"],
          "--quiet"], d / "ccdt", d / "ccdt.log")
    (d / "growclust.json").write_text(json.dumps(CFG["relative"]["growclust"]))
    tool([TOOLS / "growclust/interface/run.py", "--events", d / "events.csv", "--stations", inp / "stations.csv",
          "--dtcc", d / "ccdt", "--velocity-model", inp / "model.txt", "--config", d / "growclust.json", "--quiet"],
         d / "growclust", d / "growclust.log")
    r = json.loads((d / "growclust/run_result.json").read_text())
    c = json.loads((d / "ccdt/run_result.json").read_text())
    return {"events": len(e), "ccdt_pairs": c.get("pairs_with_dt"), "ccdt_dt_lines": c.get("dt_lines"),
            "growclust_relocated": r.get("relocated")}


# --------------------------------------------------------------- scoring
def catalogs() -> dict:
    """name -> CSV path of a located catalog (origin_time_utc, latitude, longitude, depth_km below the datum)."""
    cats = {}
    for p in sorted((OUT / "locate").glob("*/events.csv")):
        e = pd.read_csv(p)
        e = e[e.status == "LOCATED"]
        f = p.parent / "located.csv"
        e.to_csv(f, index=False)
        cats[p.parent.name] = f
    g = pd.read_csv(OUT / "relative/growclust/relocated.csv")
    g[g.relocated].to_csv(OUT / "relative/growclust/located.csv", index=False)
    cats["gamma__nll_gau__growclust_relocated_only"] = OUT / "relative/growclust/located.csv"
    return cats


def score(refs: dict, cats: dict, core: dict) -> pd.DataFrame:
    rows = []
    r2 = E.read_catalog(SRC / "04_locate_nonlinloc/full/events.csv", "origin_time", "depth_km",
                        keep=lambda r: r["status"] == "LOCATED")
    pops = {"r2_expert_nll_with_delays": r2}
    pops.update({k: E.read_catalog(v, "origin_time_utc", "depth_km") for k, v in cats.items()})
    union = {"rows": sorted(refs["cochran"]["rows"] + refs["mcmahon"]["rows"], key=lambda r: r["time"]), "gates": None}
    for name, cat in pops.items():
        rec = E.as_record(name, name, "k", cat)
        inside = [r for r in cat if r["latitude"] is not None and
                  core["latitude_bounds"][0] <= r["latitude"] <= core["latitude_bounds"][1] and
                  core["longitude_bounds"][0] <= r["longitude"] <= core["longitude_bounds"][1]]
        row = {"catalog": name, "events": len(cat), "events_core": len(inside),
               "precision_proxy": round(len(E.match(E.as_record("x", "x", "k", inside), union)) / max(len(inside), 1), 4)}
        for ref in ("cochran", "mcmahon", "comcat"):
            pairs = E.match(rec, refs[ref])
            row[f"recall_{ref}"] = round(len(pairs) / len(refs[ref]["rows"]), 4)
            if ref == "cochran":
                d = np.array([p[2] for p in pairs])
                dz = np.array([cat[i]["depth_km"] - refs[ref]["rows"][j]["depth_km"] for i, j, _, _ in pairs
                               if cat[i]["depth_km"] is not None and refs[ref]["rows"][j]["depth_km"] is not None])
                row.update(epi_median_km=round(float(np.median(d)), 3), epi_p90_km=round(float(np.quantile(d, 0.9)), 3),
                           dz_median_km=round(float(np.median(dz)), 3),
                           dz_mad_km=round(float(np.median(np.abs(dz - np.median(dz)))), 3),
                           dt_abs_median_s=round(float(np.median([p[3] for p in pairs])), 3))
        rows.append(row)
    return pd.DataFrame(rows)


def epi(a_lat, a_lon, b_lat, b_lon):
    return np.hypot((np.asarray(a_lat) - b_lat) * 111.195, (np.asarray(a_lon) - b_lon) * 111.195 * np.cos(np.radians(b_lat)))


def spread(refs: dict) -> tuple[pd.DataFrame, dict]:
    """Per-event spread across locators (GaMMA association) and across scaled models; vs Cochran error."""
    loc = OUT / "locate"
    sets = {"locators": ["gamma__nll_gau", "gamma__nll_edt", "gamma__nll_edt_ot_wt", "gamma__hypoinverse"],
            "models": ["gamma__nll_gau"] + [f"gamma__nll_gau_x{f:.2f}" for f in CFG["model_scaling"]]}
    base = pd.read_csv(loc / "gamma__nll_gau/events.csv").set_index("event_id")
    base = base[base.status == "LOCATED"]
    ev = pd.DataFrame(index=base.index)
    for label, names in sets.items():
        sol = {n: pd.read_csv(loc / n / "events.csv").set_index("event_id") for n in names}
        lat = pd.concat({n: s.latitude.where(s.status == "LOCATED") for n, s in sol.items()}, axis=1).reindex(ev.index)
        lon = pd.concat({n: s.longitude.where(s.status == "LOCATED") for n, s in sol.items()}, axis=1).reindex(ev.index)
        dep = pd.concat({n: s.depth_km.where(s.status == "LOCATED") for n, s in sol.items()}, axis=1).reindex(ev.index)
        mlat, mlon = lat.median(axis=1), lon.median(axis=1)
        ev[f"spread_h_{label}_km"] = np.nanmax(np.vstack([epi(lat[c], lon[c], mlat, mlon) for c in names]), axis=0)
        ev[f"spread_z_{label}_km"] = dep.max(axis=1) - dep.min(axis=1)
        ev[f"n_{label}"] = lat.notna().sum(axis=1)
    for c in ("erh_km", "sigma_x_km", "gap_deg", "rms_s", "n_stations"):
        ev[c] = base[c]
    # error: NLL-GAU epicentre vs its Cochran match
    rec = E.as_record("b", "b", "k", [{"time": E.parse_time(t), "latitude": a, "longitude": o, "depth_km": z,
                                       "magnitude": None, "id": i}
                                      for i, t, a, o, z in zip(base.index, base.origin_time_utc, base.latitude,
                                                               base.longitude, base.depth_km)])
    rec["rows"].sort(key=lambda r: r["time"])
    ev["epi_error_cochran_km"] = np.nan
    for i, j, d, _ in E.match(rec, refs["cochran"]):
        ev.loc[rec["rows"][i]["id"], "epi_error_cochran_km"] = d
    m = ev.dropna(subset=["epi_error_cochran_km"])
    big = m.epi_error_cochran_km > CFG["spread"]["error_km"]
    summary = {"matched_events": len(m), "large_error_fraction": round(float(big.mean()), 4), "indicators": {}}
    for c in ("spread_h_locators_km", "spread_z_locators_km", "spread_h_models_km", "spread_z_models_km",
              "erh_km", "gap_deg", "rms_s", "n_stations"):
        x = m[c].astype(float)
        ok = x.notna()
        rho = spearmanr(x[ok], m.epi_error_cochran_km[ok]).correlation
        top = x[ok] >= x[ok].quantile(1 - CFG["spread"]["top_fraction"]) if c != "n_stations" else \
            x[ok] <= x[ok].quantile(CFG["spread"]["top_fraction"])
        lift = float(big[ok][top].mean() / big[ok].mean()) if big[ok].mean() > 0 else float("nan")
        summary["indicators"][c] = {"spearman_rho": round(float(rho), 3), "lift_top": round(lift, 2)}
    # does the locator spread add anything beyond the NLL posterior error?
    rk = m[["spread_h_locators_km", "erh_km", "epi_error_cochran_km"]].rank()
    res_s = rk.spread_h_locators_km - np.polyval(np.polyfit(rk.erh_km, rk.spread_h_locators_km, 1), rk.erh_km)
    res_e = rk.epi_error_cochran_km - np.polyval(np.polyfit(rk.erh_km, rk.epi_error_cochran_km, 1), rk.erh_km)
    summary["partial_rho_spread_given_erh"] = round(float(np.corrcoef(res_s, res_e)[0, 1]), 3)
    return ev, summary


def summary_md(rep: dict, scores: pd.DataFrame) -> str:
    cols = ["catalog", "events_core", "recall_cochran", "recall_mcmahon", "recall_comcat", "precision_proxy",
            "epi_median_km", "epi_p90_km", "dz_median_km", "dz_mad_km", "dt_abs_median_s"]
    lines = ["# Stage 70 method comparison (Prague, r2 picks)", "",
             "| " + " | ".join(cols) + " |", "|" + "---|" * len(cols)]
    for r in scores[cols].itertuples(index=False):
        lines.append("| " + " | ".join(str(v) for v in r) + " |")
    lines += ["", "## Spread as a quality indicator (GaMMA association, vs Cochran epicentral error)", "",
              "```json", json.dumps(rep["spread"], indent=2), "```"]
    return "\n".join(lines) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--step", choices=["all", "associate", "locate", "relative", "score"], default="all")
    a = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    rp = OUT / "report.json"
    rep = json.loads(rp.read_text()) if rp.exists() else {}
    ctx = prepare()
    rep["inputs"] = ctx
    steps = ["associate", "locate", "relative", "score"] if a.step == "all" else [a.step]
    for s in steps:
        if s == "associate":
            rep["associations"] = associate(ctx)
        elif s == "locate":
            rep["located"] = locate(ctx)
        elif s == "relative":
            rep["relative"] = relative()
        elif s == "score":
            pops, _ = E.load_references()
            refs = {p["key"]: p for p in pops}
            core = yaml.safe_load((EXPERT / "00_config/config.yaml").read_text())["core_region"]
            scores = score(refs, catalogs(), core)
            scores.to_csv(OUT / "scores.csv", index=False)
            ev, rep["spread"] = spread(refs)
            ev.to_csv(OUT / "spread_events.csv")
            (OUT / "summary.md").write_text(summary_md(rep, scores))
            print(scores.to_string(index=False))
        rp.write_text(json.dumps(rep, indent=2, default=str) + "\n")
        print(f"{s}: {json.dumps(rep.get({'associate': 'associations', 'locate': 'located'}.get(s, s)), default=str)[:800]}",
              flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
