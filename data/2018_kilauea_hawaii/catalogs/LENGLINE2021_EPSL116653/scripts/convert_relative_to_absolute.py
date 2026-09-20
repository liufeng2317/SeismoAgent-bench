#!/usr/bin/env python3
"""Derive an explicitly labelled approximate absolute position product.

The native Lengline release contains only local x/y coordinates.  This script
never overwrites them.  It assumes x=east and y=north in a local WGS84
azimuthal-equidistant frame centred at the published reference point.  Depth
is retained as a fixed 3 km modelling assumption, not an observed field.
"""
from __future__ import annotations

import csv
import hashlib
import json
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from pyproj import CRS, Transformer

# Keep the derivative figure visually consistent with the catalog profiles.
plt.rcParams.update({
    "font.family": "DejaVu Serif",
    "font.size": 8,
    "axes.labelsize": 8,
    "axes.titlesize": 9,
    "xtick.labelsize": 7,
    "ytick.labelsize": 7,
    "axes.linewidth": 0.6,
    "figure.dpi": 150,
    "savefig.dpi": 300,
    "savefig.bbox": "tight",
    "savefig.facecolor": "white",
    "axes.facecolor": "white",
    "figure.facecolor": "white",
})

CASE_ID = "2018_kilauea_hawaii"
SOURCE_REF = "LENGLINE2021_EPSL116653"
ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "raw" / "loc_events.txt"
OUT = ROOT / "analysis" / "derived" / "relative_events"
FIG = ROOT / "analysis" / "figures" / "relative_events"
STATS = ROOT / "analysis" / "stats" / "relative_events"
UTC = timezone.utc
T0 = datetime(2018, 4, 29, tzinfo=UTC)
WINDOW_START = datetime(2018, 5, 1, tzinfo=UTC)
WINDOW_END = datetime(2018, 5, 9, tzinfo=UTC)
REFERENCE_LAT = 19.3864
REFERENCE_LON = -155.1050
ASSUMED_DEPTH_KM = 3.0
TRANSFORM_ID = "local_EN_assumption_v1"
DERIVATIVE_VERSION = "absolute-approx-v1"

LOCAL_CRS = CRS.from_proj4(
    f"+proj=aeqd +lat_0={REFERENCE_LAT} +lon_0={REFERENCE_LON} "
    "+datum=WGS84 +units=m +no_defs"
)
TO_WGS84 = Transformer.from_crs(LOCAL_CRS, CRS.from_epsg(4326), always_xy=True)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def rows():
    with RAW.open("r", encoding="utf-8", errors="replace") as f:
        for line_no, line in enumerate(f, start=1):
            cols = line.split()
            if len(cols) < 3:
                continue
            try:
                relative_day, x_m, y_m = map(float, cols[:3])
            except ValueError:
                continue
            yield line_no, relative_day, x_m, y_m


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    FIG.mkdir(parents=True, exist_ok=True)
    for old_svg in FIG.glob("*.svg"):
        old_svg.unlink()
    STATS.mkdir(parents=True, exist_ok=True)

    fields = [
        "event_id", "origin_time_utc", "relative_day", "x_m", "y_m",
        "longitude_deg", "latitude_deg", "depth_km", "depth_status",
        "coordinate_status", "coordinate_transform", "source_row",
    ]
    records = []
    for source_row, relative_day, x_m, y_m in rows():
        lon, lat = TO_WGS84.transform(x_m, y_m)
        dt = T0 + timedelta(days=relative_day)
        records.append({
            "event_id": f"E{len(records)+1:06d}",
            "origin_time_utc": dt.isoformat().replace("+00:00", "Z"),
            "relative_day": relative_day,
            "x_m": x_m,
            "y_m": y_m,
            "longitude_deg": lon,
            "latitude_deg": lat,
            "depth_km": ASSUMED_DEPTH_KM,
            "depth_status": "fixed_model_assumption",
            "coordinate_status": "approximate_assumption",
            "coordinate_transform": TRANSFORM_ID,
            "source_row": source_row,
        })

    csv_path = OUT / f"{SOURCE_REF}__relative_events__absolute_approx_v1.csv"
    with csv_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(records)

    transform_doc = f"""# Lengliné relative-to-absolute derivative

- `transform_id`: `{TRANSFORM_ID}`
- `case_id`: `{CASE_ID}`
- `source_ref`: `{SOURCE_REF}`
- reference point: `{REFERENCE_LAT}°N, {REFERENCE_LON}°E`
- projection: WGS84 azimuthal equidistant centred on the reference point
- axis assumption: `x=east_positive`, `y=north_positive`
- depth: `{ASSUMED_DEPTH_KM} km`, fixed model assumption
- confidence: approximate

This derivative must not be used for event-by-event absolute-location error,
depth evaluation, or magnitude evaluation against Shelly, Wei, Matoza, or HVO.
The released table has no event-specific depth; the paper uses a fixed 3 km
depth in its two-dimensional localization model.

## Evidence

- `data/2018_kilauea_hawaii/references/LENGLINE2021_EPSL116653/parsed/supplement/LENGLINE2021_EPSL116653__supplement__mmc2__mineru.md` — catalog description paragraph
- `data/2018_kilauea_hawaii/references/LENGLINE2021_EPSL116653/parsed/paper/LENGLINE2021_EPSL116653__paper__mineru.md` — Sections 3.1–3.2
"""
    (OUT / "coordinate_transform.md").write_text(transform_doc, encoding="utf-8")

    readme_path = OUT / "README.md"
    readme = readme_path.read_text(encoding="utf-8") if readme_path.exists() else ""
    marker = "## Approximate absolute derivative"
    if marker not in readme:
        readme += (
            "\n\n" + marker + "\n\n"
            "Schema: `docs/schemas/catalog_absolute_approx.schema.yaml`\n\n"
            "Assumptions and evidence: `coordinate_transform.md`\n"
        )
        readme_path.write_text(readme, encoding="utf-8")

    subsets = {
        "full": records,
        "time_only": [
            r for r in records
            if WINDOW_START <= datetime.fromisoformat(r["origin_time_utc"].replace("Z", "+00:00")) < WINDOW_END
        ],
    }
    common = {
        "case_id": CASE_ID,
        "source_ref": SOURCE_REF,
        "product_id": "absolute_approx_v1",
        "derivative_version": DERIVATIVE_VERSION,
        "source_product": "relative_events",
        "source_path": str(RAW.relative_to(ROOT)),
        "source_sha256": sha256(RAW),
        "coordinate_status": "approximate_assumption",
        "coordinate_transform": TRANSFORM_ID,
        "depth_km": ASSUMED_DEPTH_KM,
        "axis_assumption": "x=east, y=north",
    }
    for name, subset in subsets.items():
        payload = dict(common)
        payload["selection"] = name
        payload["row_count"] = len(subset)
        payload["ranges"] = {
            "latitude_deg": [min(r["latitude_deg"] for r in subset), max(r["latitude_deg"] for r in subset)] if subset else [None, None],
            "longitude_deg": [min(r["longitude_deg"] for r in subset), max(r["longitude_deg"] for r in subset)] if subset else [None, None],
            "x_m": [min(r["x_m"] for r in subset), max(r["x_m"] for r in subset)] if subset else [None, None],
            "y_m": [min(r["y_m"] for r in subset), max(r["y_m"] for r in subset)] if subset else [None, None],
        }
        (STATS / f"absolute_approx_{name}_v1.json").write_text(
            json.dumps(payload, indent=2) + "\n", encoding="utf-8"
        )

    if records:
        fig, ax = plt.subplots(figsize=(7, 5))
        sc = ax.scatter(
            [r["longitude_deg"] for r in records],
            [r["latitude_deg"] for r in records],
            c=[r["relative_day"] for r in records],
            s=4, alpha=0.5, cmap="viridis",
        )
        ax.scatter([REFERENCE_LON], [REFERENCE_LAT], marker="*", s=85, c="#D55E00", label="reference point")
        ax.set_xlabel("Longitude (° WGS84)")
        ax.set_ylabel("Latitude (° WGS84)")
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.grid(axis="both", color="#D9DEE3", linewidth=0.45, alpha=0.7)
        ax.set_axisbelow(True)
        ax.legend(loc="best", frameon=False, fontsize=7)
        cbar = fig.colorbar(sc, ax=ax, label="Days since 2018-04-29")
        cbar.ax.tick_params(labelsize=7, width=0.5)
        fig.tight_layout(pad=0.45)
        png = FIG / "absolute_approx_map_v1.png"
        fig.savefig(png, dpi=300, facecolor="white", bbox_inches="tight")
        stale_svg = FIG / "absolute_approx_map_v1.svg"
        if stale_svg.exists():
            stale_svg.unlink()
        plt.close(fig)

    print(json.dumps({
        "rows": len(records),
        "time_only": len(subsets["time_only"]),
        "output": str(csv_path.relative_to(ROOT)),
        "transform": TRANSFORM_ID,
    }, indent=2))


if __name__ == "__main__":
    main()
