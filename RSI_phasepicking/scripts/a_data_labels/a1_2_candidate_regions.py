"""a1 round 1: propose candidate regions outside Ridgecrest/Coso.

For each grid centre (0.25 deg) in southern California, count SCEDC local
earthquakes within a radius (M>=2.5, M>=3, split into the practice period and
later) and CI/AZ stations operating since 2020. Centres whose circle overlaps
the excluded Ridgecrest/Coso box are dropped, and events inside the box are not
counted. Centres whose events lie mostly in deep basins (where the
Hadley-Kanamori model is a poor approximation; the basin boxes are rough
outlines) are dropped. The best remaining centres, at least --min-sep km apart
and with enough stations, become candidates.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # scripts/, for paths.py
import argparse
import json

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from paths import RES_A, SCEDC_EVENTS, STATIONS_RAW

EXCLUDE = {"Ridgecrest/Coso": (35.3, 36.3, -118.2, -117.2)}  # lat0, lat1, lon0, lon1
# Approximate outlines, used only as flags (Hutton et al. 2010 name these basins).
BASINS = {
    "Imperial Valley / Salton Trough": (32.5, 33.6, -116.2, -115.2),
    "Los Angeles basin": (33.7, 34.2, -118.5, -117.7),
    "Ventura basin": (34.1, 34.5, -119.4, -118.6),
}
PRACTICE_END = pd.Timestamp("2023-11-01")


def box_dist_km(lat, lon, box):
    """Distance from a point to a lat/lon box (0 inside), flat-earth approximation."""
    dlat = max(box[0] - lat, 0.0, lat - box[1]) * 111.0
    dlon = max(box[2] - lon, 0.0, lon - box[3]) * 111.0 * np.cos(np.radians(lat))
    return float(np.hypot(dlat, dlon))


def in_box(lat, lon, box):
    return (lat >= box[0]) & (lat <= box[1]) & (lon >= box[2]) & (lon <= box[3])


def dist_km(lat0, lon0, lat, lon):
    r = 6371.0
    p0, p = np.radians(lat0), np.radians(lat)
    dphi, dlmb = p - p0, np.radians(lon - lon0)
    a = np.sin(dphi / 2) ** 2 + np.cos(p0) * np.cos(p) * np.sin(dlmb / 2) ** 2
    return 2 * r * np.arcsin(np.sqrt(a))


def load_events():
    rows = []
    for f in sorted(SCEDC_EVENTS.glob("20[2-9]*.txt")):  # the 2019 T1 file is not used here
        for line in f.read_text().splitlines():
            if not line.strip() or line.startswith("#"):
                continue
            c = [x.strip() for x in line.split("|")]
            rows.append(dict(event_id=c[0], time=c[1], lat=float(c[2]), lon=float(c[3]),
                             depth_km=float(c[4]), etype=c[7], gtype=c[8], mag=float(c[10])))
    ev = pd.DataFrame(rows)
    ev["time"] = pd.to_datetime(ev["time"], format="%Y/%m/%d %H:%M:%S.%f")
    return ev[(ev.etype == "eq") & (ev.gtype == "l")].reset_index(drop=True)


def load_stations():
    rows = []
    for f in STATIONS_RAW.glob("scedc_*_stations.txt"):
        for line in f.read_text().splitlines():
            if not line.strip() or line.startswith("#"):
                continue
            c = [x.strip() for x in line.split("|")]
            rows.append(dict(net=c[0], sta=c[1], lat=float(c[2]), lon=float(c[3]), start=c[6], end=c[7]))
    st = pd.DataFrame(rows)
    active = (st.end == "") | (st.end >= "2020-01-01")
    return st[active].drop_duplicates(["net", "sta"]).reset_index(drop=True)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--radius", type=float, default=50.0, help="km")
    ap.add_argument("--min-stations", type=int, default=25)
    ap.add_argument("--min-sep", type=float, default=100.0, help="km between candidates")
    ap.add_argument("--n", type=int, default=6, help="number of candidates")
    ap.add_argument("--max-basin-share", type=float, default=0.2,
                    help="largest share of a circle's M>=2.5 events inside basin boxes")
    ap.add_argument("--out", default=str(RES_A / "a1_events"))
    args = ap.parse_args()
    out = pd.io.common.Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    ev, st = load_events(), load_stations()
    outside = np.ones(len(ev), bool)
    for b in EXCLUDE.values():
        outside &= ~in_box(ev.lat.values, ev.lon.values, b)
    big = ev[(ev.mag >= 2.5) & outside]
    grid = [(la, lo) for la in np.arange(32.0, 37.01, 0.25) for lo in np.arange(-121.0, -113.99, 0.25)]
    cells = []
    for la, lo in grid:
        if any(box_dist_km(la, lo, b) < args.radius for b in EXCLUDE.values()):
            continue  # the circle would overlap the excluded area
        d = dist_km(la, lo, big.lat.values, big.lon.values) <= args.radius
        sub = big[d]
        n_sta = int((dist_km(la, lo, st.lat.values, st.lon.values) <= args.radius).sum())
        in_basin = np.zeros(len(sub), bool)
        for b in BASINS.values():
            in_basin |= in_box(sub.lat.values, sub.lon.values, b)
        basin_share = float(in_basin.mean()) if len(sub) else 0.0
        cells.append(dict(lat=la, lon=lo, n_m25=len(sub), n_m3=int((sub.mag >= 3).sum()),
                          n_m25_practice=int((sub.time < PRACTICE_END).sum()),
                          n_m25_after=int((sub.time >= PRACTICE_END).sum()),
                          n_stations=n_sta, basin_share=round(basin_share, 2)))
    cells = pd.DataFrame(cells)
    ok = cells[(cells.n_stations >= args.min_stations) & (cells.basin_share <= args.max_basin_share)]
    ok = ok.sort_values("n_m25", ascending=False)
    chosen = []
    for _, r in ok.iterrows():
        if all(dist_km(r.lat, r.lon, c.lat, c.lon) >= args.min_sep for c in chosen):
            chosen.append(r)
        if len(chosen) == args.n:
            break
    cand = pd.DataFrame(chosen).reset_index(drop=True)
    cand.insert(0, "candidate", [f"R{i + 1}" for i in range(len(cand))])
    cand.to_csv(out / "candidate_regions.csv", index=False)
    cells.to_csv(out / "grid_counts.csv", index=False)

    # Map: M>=2.5 events, stations, excluded and basin boxes, candidate circles.
    fig, ax = plt.subplots(figsize=(9, 7.5))
    ax.scatter(big.lon, big.lat, s=2, c="0.55", lw=0, label="M≥2.5 events outside the excluded box, 2020-01 to now")
    ax.scatter(st.lon, st.lat, s=12, marker="^", c="tab:blue", lw=0, label="CI/AZ stations active since 2020")
    for name, b in EXCLUDE.items():
        ax.add_patch(plt.Rectangle((b[2], b[0]), b[3] - b[2], b[1] - b[0], fill=False, ec="tab:red", lw=1.5))
        ax.text(b[2], b[1] + 0.05, f"excluded: {name}", color="tab:red", fontsize=8)
    for name, b in BASINS.items():
        ax.add_patch(plt.Rectangle((b[2], b[0]), b[3] - b[2], b[1] - b[0], fill=False, ec="tab:orange", ls="--", lw=1))
        ax.text(b[2], b[0] - 0.12, f"basin: {name}", color="tab:orange", fontsize=7)
    for _, r in cand.iterrows():
        deg = args.radius / 111.0
        ax.add_patch(plt.Circle((r.lon, r.lat), deg / np.cos(np.radians(r.lat)), fill=False, ec="tab:green", lw=1.5))
        ax.text(r.lon, r.lat, r.candidate, color="tab:green", fontsize=11, weight="bold", ha="center", va="center")
    ax.set_xlim(-121, -114)
    ax.set_ylim(32, 37)
    ax.set_aspect(1 / np.cos(np.radians(34.5)))
    ax.set_xlabel("Longitude (°)")
    ax.set_ylabel("Latitude (°)")
    ax.set_title(f"Candidate regions (radius {args.radius:.0f} km, ≥{args.min_stations} stations, no overlap with excluded box, basin share ≤{args.max_basin_share:.0%})")
    ax.legend(loc="lower left", fontsize=8)
    fig.tight_layout()
    fig.savefig(out / "candidate_regions_map.png", dpi=150)

    # Events per year in each candidate.
    fig, ax = plt.subplots(figsize=(9, 4))
    years = sorted(big.time.dt.year.unique())
    w = 0.8 / max(len(cand), 1)
    for i, r in cand.iterrows():
        sub = big[dist_km(r.lat, r.lon, big.lat.values, big.lon.values) <= args.radius]
        cnt = sub.time.dt.year.value_counts().reindex(years, fill_value=0)
        ax.bar(np.array(years) + (i - len(cand) / 2) * w + w / 2, cnt.values, width=w, label=r.candidate)
    ax.set_xlabel("Year")
    ax.set_ylabel("M≥2.5 events within radius")
    ax.legend(ncol=len(cand), fontsize=8)
    fig.tight_layout()
    fig.savefig(out / "candidate_regions_per_year.png", dpi=150)

    summary = dict(events_local_eq=len(ev), events_m25=len(big), stations_active=len(st),
                   period=[str(ev.time.min()), str(ev.time.max())], args=vars(args))
    (out / "summary.json").write_text(json.dumps(summary, indent=1))
    print(json.dumps(summary, indent=1))
    print(cand.to_string(index=False))


if __name__ == "__main__":
    main()
