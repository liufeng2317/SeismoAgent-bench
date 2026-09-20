#!/usr/bin/env python3
"""Catalog-local Kīlauea profiling, normalization, statistics and figures.

This script is intentionally kept inside its source catalog bundle. It never
modifies raw files; all generated artifacts go below analysis/.
"""
from __future__ import annotations
import argparse
import csv
import hashlib
import json
import math
import random
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

PLOT_PROFILE = "minimal"
FULL_PLOTS = False
NATURE_BLUE = "#2C5F8A"
NATURE_ORANGE = "#D55E00"
NATURE_TEAL = "#009E73"
NATURE_PURPLE = "#7B5EA7"
NATURE_GREY = "#5B6573"

# Compact, publication-oriented defaults.  The default profile intentionally
# produces only benchmark-first PNG figures; use --full-plots for diagnostics.
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
SOURCE_REF = 'SHELLY2019_GL085636'
CATALOG_ROOT = Path(__file__).resolve().parents[1]
ANALYSIS_ROOT = CATALOG_ROOT / "analysis"
STATS_ROOT = ANALYSIS_ROOT / "stats"
FIGURES_ROOT = ANALYSIS_ROOT / "figures"
DERIVED_ROOT = ANALYSIS_ROOT / "derived"
PARSER_VERSION = "kilauea-local-v2-compact"
UTC = timezone.utc
WINDOW_START = datetime(2018, 5, 1, tzinfo=UTC)
WINDOW_END = datetime(2018, 5, 9, tzinfo=UTC)
LAT_MIN, LAT_MAX = 19.30, 19.50
LON_MIN, LON_MAX = -155.40, -155.15
DEPTH_MIN, DEPTH_MAX = 0.0, 20.0
PRODUCTS = [{'id': 'events_s1', 'kind': 'shelly_s1', 'path': 'SHELLY2019_GL085636__catalog_S1.txt', 'unit': 'event', 'role': 'primary', 'note': 'Shelly high-resolution hypocentroid product S1.'}, {'id': 'events_s2', 'kind': 'shelly_s2', 'path': 'SHELLY2019_GL085636__catalog_S2.txt', 'unit': 'event', 'role': 'secondary', 'note': 'Shelly polarity-cluster product S2; separate event table.'}, {'id': 'phase_arrivals', 'kind': 'phase_csv', 'path': 'raw/Kilauea_2018_correlation_phase_arrivals.csv', 'unit': 'phase_pick', 'role': 'auxiliary', 'note': 'USGS correlation-derived phase arrivals; template_id and match_id are not event IDs.'}]
FORCE = False
OVERVIEW = 'Primary summit event products plus a large phase-arrival auxiliary. S1, S2 and phase rows are never merged.'


def finite_float(value):
    try:
        x = float(value)
    except (TypeError, ValueError):
        return None
    return x if math.isfinite(x) else None


def parse_iso(value):
    if not value:
        return None
    try:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
        # Native timezone-naive timestamps are documented as UTC.
        return dt.replace(tzinfo=UTC) if dt.tzinfo is None else dt.astimezone(UTC)
    except ValueError:
        return None


def parse_parts_datetime(parts):
    try:
        year, month, day, hour, minute = [int(parts[i]) for i in range(5)]
        sec = float(parts[5])
        base = datetime(year, month, day, hour, minute, tzinfo=UTC)
        return base + timedelta(seconds=sec)
    except (TypeError, ValueError, IndexError, OverflowError):
        return None


def sha256(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def json_safe(value):
    if isinstance(value, dict):
        return {str(k): json_safe(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [json_safe(v) for v in value]
    if isinstance(value, float) and (math.isnan(value) or math.isinf(value)):
        return None
    return value


class Accumulator:
    def __init__(self, kind):
        self.kind = kind
        self.rows = 0
        self.native_ids = set()
        self.duplicate_ids = 0
        self.missing = Counter()
        self.ranges = {k: [None, None] for k in ("latitude_deg", "longitude_deg", "depth_km", "magnitude", "x_m", "y_m")}
        self.daily = Counter()
        self.hourly = Counter()
        self.magnitude_types = Counter()
        self.networks = Counter()
        self.stations = Counter()
        self.phases = Counter()
        self.templates = set()
        self.matches = set()
        self.relocated = Counter()
        self.sample = []
        self.rng = random.Random(17)

    def _range(self, key, value):
        value = finite_float(value)
        if value is None:
            return
        lo, hi = self.ranges[key]
        self.ranges[key] = [value if lo is None else min(lo, value), value if hi is None else max(hi, value)]

    def add_event(self, record):
        self.rows += 1
        native_id = record.get("native_event_id")
        if native_id in (None, ""):
            self.missing["native_event_id"] += 1
        elif native_id in self.native_ids:
            self.duplicate_ids += 1
        else:
            self.native_ids.add(str(native_id))
        dt = record.get("datetime")
        if dt is None:
            self.missing["origin_time_utc"] += 1
        else:
            self.daily[dt.date().isoformat()] += 1
            self.hourly[dt.strftime("%Y-%m-%dT%H")] += 1
        for key in ("latitude_deg", "longitude_deg", "depth_km", "magnitude", "x_m", "y_m"):
            value = record.get(key)
            if finite_float(value) is None:
                self.missing[key] += 1
            else:
                self._range(key, value)
        mag_type = record.get("magnitude_type") or "unknown"
        self.magnitude_types[str(mag_type)] += 1
        network = record.get("network")
        if network:
            self.networks[str(network)] += 1
        if record.get("relocation_flag") is not None:
            self.relocated[str(record["relocation_flag"])] += 1
        point = (finite_float(record.get("longitude_deg")), finite_float(record.get("latitude_deg")), finite_float(record.get("depth_km")), finite_float(record.get("magnitude")))
        if len(self.sample) < 50000:
            self.sample.append(point)
        else:
            index = self.rng.randrange(self.rows)
            if index < len(self.sample):
                self.sample[index] = point

    def add_phase(self, row):
        self.rows += 1
        dt = row.get("datetime")
        if dt is None:
            self.missing["arrival_utc"] += 1
        else:
            self.daily[dt.date().isoformat()] += 1
            self.hourly[dt.strftime("%Y-%m-%dT%H")] += 1
        for key in ("network", "station", "phase", "template_id", "match_id"):
            if not row.get(key):
                self.missing[key] += 1
        if row.get("network"):
            self.networks[str(row["network"])] += 1
        if row.get("station"):
            self.stations[str(row["station"])] += 1
        if row.get("phase"):
            self.phases[str(row["phase"])] += 1
        if row.get("template_id"):
            self.templates.add(str(row["template_id"]))
        if row.get("match_id"):
            self.matches.add(str(row["match_id"]))

    def as_dict(self):
        result = {
            "kind": self.kind,
            "row_count": self.rows,
            "unique_native_event_ids": len(self.native_ids) if self.native_ids else None,
            "duplicate_native_event_ids": self.duplicate_ids,
            "missing": dict(self.missing),
            "ranges": self.ranges,
            "magnitude_types": dict(self.magnitude_types),
            "networks": dict(self.networks),
            "stations": dict(self.stations),
            "phases": dict(self.phases),
            "unique_template_ids": len(self.templates) if self.templates else None,
            "unique_match_ids": len(self.matches) if self.matches else None,
            "relocation_flags": dict(self.relocated),
            "daily_counts": dict(sorted(self.daily.items())),
            "hourly_counts": dict(sorted(self.hourly.items())),
        }
        return json_safe(result)


def iter_records(product):
    path = CATALOG_ROOT / product["path"]
    kind = product["kind"]
    if kind == "phase_csv":
        with path.open("r", encoding="utf-8", errors="replace", newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                arrival = finite_float(row.get("arrival"))
                dt = datetime.fromtimestamp(arrival, UTC) if arrival is not None else None
                yield {"datetime": dt, "template_id": row.get("template_id"), "match_id": row.get("match_id"), "network": row.get("network"), "station": row.get("station"), "phase": row.get("phase"), "raw": row}
        return
    if kind == "usgs_csv":
        with path.open("r", encoding="utf-8", errors="replace", newline="") as f:
            for row in csv.DictReader(f):
                dt = parse_iso(row.get("time"))
                yield {"datetime": dt, "native_event_id": row.get("id"), "latitude_deg": finite_float(row.get("latitude")), "longitude_deg": finite_float(row.get("longitude")), "depth_km": finite_float(row.get("depth")), "magnitude": finite_float(row.get("mag")), "magnitude_type": row.get("magType"), "network": row.get("net"), "quality_flag": row.get("status"), "raw": row}
        return
    with path.open("r", encoding="utf-8", errors="replace") as f:
        for line_no, line in enumerate(f, start=1):
            text = line.strip()
            if not text or text.startswith("%") or text.startswith("SourceTime") or text.startswith("Catalog of detected"):
                continue
            cols = text.split()
            try:
                if kind == "shelly_s1" and len(cols) >= 14:
                    yield {"datetime": parse_parts_datetime(cols[0:6]), "native_event_id": cols[13], "latitude_deg": finite_float(cols[6]), "longitude_deg": finite_float(cols[7]), "depth_km": finite_float(cols[8]), "magnitude": finite_float(cols[12]), "magnitude_type": "Shelly_native", "network": "HV", "source_row": line_no, "raw": cols}
                elif kind == "shelly_s2" and len(cols) >= 12:
                    yield {"datetime": parse_parts_datetime(cols[1:7]), "native_event_id": cols[11], "latitude_deg": finite_float(cols[7]), "longitude_deg": finite_float(cols[8]), "depth_km": finite_float(cols[9]), "magnitude": finite_float(cols[10]), "magnitude_type": "Shelly_native", "network": "HV", "cluster": cols[0], "source_row": line_no, "raw": cols}
                elif kind == "wei" and len(cols) >= 14:
                    yield {"datetime": parse_iso(cols[0]), "native_event_id": None, "latitude_deg": finite_float(cols[1]), "longitude_deg": finite_float(cols[2]), "depth_km": finite_float(cols[3]), "magnitude": finite_float(cols[11]), "magnitude_type": cols[12], "network": "mixed", "source_row": line_no, "azimuthal_gap": finite_float(cols[4]), "nobs": finite_float(cols[6]), "rms_s": finite_float(cols[7]), "std_mag": finite_float(cols[13]), "raw": cols}
                elif kind == "matoza14" and len(cols) >= 17:
                    yield {"datetime": parse_parts_datetime(cols[0:6]), "native_event_id": cols[6], "latitude_deg": finite_float(cols[7]), "longitude_deg": finite_float(cols[8]), "depth_km": finite_float(cols[9]), "magnitude": finite_float(cols[10]), "magnitude_type": "CUSP_native", "network": "HV", "quality_flag": cols[11], "cluster_id": cols[12], "cluster_size": finite_float(cols[13]), "horizontal_error_km": finite_float(cols[14]), "vertical_error_km": finite_float(cols[15]), "relocation_flag": cols[16], "source_row": line_no, "raw": cols}
                elif kind == "matoza21" and len(cols) >= 26:
                    yield {"datetime": parse_parts_datetime(cols[0:6]), "native_event_id": cols[6], "latitude_deg": finite_float(cols[7]), "longitude_deg": finite_float(cols[8]), "depth_km": finite_float(cols[9]), "magnitude": finite_float(cols[10]), "magnitude_type": "Matoza_native", "network": "HV", "nbranch": finite_float(cols[13]), "relocation_flag": "relocated" if finite_float(cols[13]) and finite_float(cols[13]) > 1 else "starting", "cluster_id": cols[12], "polygon": cols[25], "latitude_start": finite_float(cols[22]), "longitude_start": finite_float(cols[23]), "depth_start_km": finite_float(cols[24]), "horizontal_error_km": finite_float(cols[19]), "vertical_error_km": finite_float(cols[20]), "source_row": line_no, "raw": cols}
                elif kind == "lengline" and len(cols) >= 3:
                    relative_day = finite_float(cols[0])
                    dt = datetime(2018, 4, 29, tzinfo=UTC) + timedelta(days=relative_day) if relative_day is not None else None
                    yield {"datetime": dt, "native_event_id": None, "relative_day": relative_day, "x_m": finite_float(cols[1]), "y_m": finite_float(cols[2]), "network": "HV_template_subset", "source_row": line_no, "raw": cols}
            except (ValueError, IndexError):
                continue


def in_time(dt):
    return dt is not None and WINDOW_START <= dt < WINDOW_END


def in_common_mask(record, basis="relocated"):
    if basis == "starting":
        lat, lon, depth = record.get("latitude_start"), record.get("longitude_start"), record.get("depth_start_km")
    else:
        lat, lon, depth = record.get("latitude_deg"), record.get("longitude_deg"), record.get("depth_km")
    return all(v is not None for v in (lat, lon, depth)) and LAT_MIN <= lat <= LAT_MAX and LON_MIN <= lon <= LON_MAX and DEPTH_MIN <= depth <= DEPTH_MAX


def selection_names(record, product):
    kind = product["kind"]
    if kind == "phase_csv":
        return ["full"] + (["benchmark_time"] if in_time(record.get("datetime")) else [])
    if kind == "lengline":
        return ["full"] + (["time_only"] if in_time(record.get("datetime")) else [])
    names = ["full"]
    if in_time(record.get("datetime")):
        names.append("time_only")
        if in_common_mask(record):
            names.append("benchmark")
        if kind == "matoza21" and in_common_mask(record, "starting"):
            names.append("benchmark_starting")
    return names


def normalized_fields(kind):
    base = ["event_id", "native_event_id", "origin_time_utc", "latitude_deg", "longitude_deg", "depth_km", "magnitude", "magnitude_type", "network", "source_row", "extras_json"]
    if kind == "lengline":
        return ["event_id", "native_event_id", "origin_time_utc", "relative_day", "x_m", "y_m", "source_row", "extras_json"]
    return base


def schema_reference(kind):
    if kind == "lengline":
        return "docs/schemas/catalog_relative_event.schema.yaml"
    if kind == "mcmahon_phase":
        return "docs/schemas/catalog_parent_phase.schema.yaml"
    if kind == "phase_csv":
        return "docs/schemas/catalog_correlation_phase.schema.yaml"
    return "docs/schemas/catalog_event.schema.yaml"


def write_normalized(product):
    if product["kind"] == "phase_csv":
        return None
    out = DERIVED_ROOT / product["id"]
    out.mkdir(parents=True, exist_ok=True)
    path = out / f"{SOURCE_REF}__{product['id']}__normalized_v1.csv"
    fields = normalized_fields(product["kind"])
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for i, record in enumerate(iter_records(product), start=1):
            extras = {k: v for k, v in record.items() if k not in {"datetime", "native_event_id", "latitude_deg", "longitude_deg", "depth_km", "magnitude", "magnitude_type", "network", "source_row", "relative_day", "x_m", "y_m", "raw"}}
            row = {key: "" for key in fields}
            row["event_id"] = f"E{i:06d}"
            row["native_event_id"] = record.get("native_event_id") or ""
            row["origin_time_utc"] = record["datetime"].isoformat().replace("+00:00", "Z") if record.get("datetime") else ""
            for key in ("latitude_deg", "longitude_deg", "depth_km", "magnitude", "relative_day", "x_m", "y_m"):
                if key in row and record.get(key) is not None:
                    row[key] = record[key]
            for key in ("magnitude_type", "network", "source_row"):
                if key in row and record.get(key) is not None:
                    row[key] = record[key]
            row["extras_json"] = json.dumps(json_safe(extras), sort_keys=True)
            writer.writerow(row)
    return str(path.relative_to(CATALOG_ROOT))


def profile_product(product):
    path = CATALOG_ROOT / product["path"]
    is_phase = product["kind"] == "phase_csv"
    accumulators = {}
    sample_rows = []
    for record in iter_records(product):
        for selection in selection_names(record, product):
            accumulators.setdefault(selection, Accumulator(product["kind"]))
            if is_phase:
                accumulators[selection].add_phase(record)
                if len(sample_rows) < 10000 and selection == "full":
                    sample_rows.append(record.get("raw", {}))
            else:
                accumulators[selection].add_event(record)
    normalized_path = write_normalized(product)
    output_dir = STATS_ROOT / product["id"]
    output_dir.mkdir(parents=True, exist_ok=True)
    stats = {}
    for selection, accumulator in accumulators.items():
        stats[selection] = accumulator.as_dict()
        payload = {
            "case_id": CASE_ID,
            "source_ref": SOURCE_REF,
            "product_id": product["id"],
            "kind": product["kind"],
            "unit": product["unit"],
            "selection": selection,
            "selection_rule": "[2018-05-01T00:00:00Z, 2018-05-09T00:00:00Z); common summit mask where applicable",
            "parser_version": PARSER_VERSION,
            "source_path": product["path"],
            "source_sha256": sha256(path),
            "generated_utc": datetime.now(UTC).replace(microsecond=0).isoformat(),
            "stats": stats[selection],
        }
        (output_dir / f"{selection}_v1.json").write_text(json.dumps(json_safe(payload), indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    if is_phase:
        sample_path = DERIVED_ROOT / product["id"] / f"{SOURCE_REF}__{product['id']}__sample_v1.csv"
        sample_path.parent.mkdir(parents=True, exist_ok=True)
        if sample_rows:
            fields = list(sample_rows[0])
            with sample_path.open("w", encoding="utf-8", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=fields)
                writer.writeheader(); writer.writerows(sample_rows)
    return stats, normalized_path



def load_cached_product(product):
    """Load a large-product profile when raw bytes are unchanged."""
    if FORCE or product["kind"] != "phase_csv":
        return None
    source = CATALOG_ROOT / product["path"]
    output_dir = STATS_ROOT / product["id"]
    full_file = output_dir / "full_v1.json"
    if not full_file.exists():
        return None
    try:
        payload = json.loads(full_file.read_text(encoding="utf-8"))
        if payload.get("source_sha256") != sha256(source):
            return None
        if payload.get("parser_version") != PARSER_VERSION:
            return None
        stats = {}
        for f in sorted(output_dir.glob("*_v1.json")):
            item = json.loads(f.read_text(encoding="utf-8"))
            stats[item["selection"]] = item["stats"]
        return stats if "full" in stats else None
    except (OSError, KeyError, json.JSONDecodeError):
        return None

RUN_FIGURE_STEMS = {
    "catalog_overview_v1", "relative_overview_v1", "phase_overview_v1",
    "map_v1", "depth_section_v1", "event_rate_v1", "magnitude_distribution_v1",
    "relative_xy_v1", "phase_composition_v1", "station_coverage_v1", "phase_rate_v1",
}


def _clean_figure_dir(out):
    """Remove this parser's stale images without touching other derived products."""
    out.mkdir(parents=True, exist_ok=True)
    for candidate in out.iterdir():
        if not candidate.is_file():
            continue
        if candidate.suffix.lower() == ".svg" or candidate.stem in RUN_FIGURE_STEMS:
            candidate.unlink()


def _style_axes(ax, grid=True):
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_linewidth(0.6)
    ax.spines["bottom"].set_linewidth(0.6)
    ax.tick_params(width=0.6, length=3, pad=2)
    if grid:
        ax.set_axisbelow(True)
        ax.grid(axis="y", color="#D9DEE3", linewidth=0.45, alpha=0.75)


def _panel_label(ax, label):
    ax.text(-0.12, 1.04, label, transform=ax.transAxes,
            fontsize=9, fontweight="bold", va="bottom", ha="left")


def savefig(fig, path):
    """Write one high-resolution PNG and never create vector output."""
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.tight_layout(pad=0.45)
    png_path = path.with_suffix(".png")
    fig.savefig(png_path, dpi=300, facecolor="white", bbox_inches="tight")
    stale_svg = path.with_suffix(".svg")
    if stale_svg.exists():
        stale_svg.unlink()
    plt.close(fig)


def _plot_selection(product, stats):
    for candidate in ("benchmark", "benchmark_time", "time_only", "full"):
        if candidate in stats and stats[candidate].get("row_count", 0):
            return candidate
    return "full"


def _matches_selection(record, product, selection):
    if selection == "full":
        return True
    dt = record.get("datetime")
    if not in_time(dt):
        return False
    if selection in {"time_only", "benchmark_time"}:
        return True
    if selection == "benchmark":
        return in_common_mask(record)
    if selection == "benchmark_starting":
        return in_common_mask(record, "starting")
    return True


def _plot_policy(product):
    """Return the compact figure policy for one native product."""
    if product["kind"] == "phase_csv":
        return {"phase_overview": True}
    if product["kind"] == "lengline":
        return {"relative_overview": True}
    if FULL_PLOTS:
        return {"overview": True, "depth": True, "magnitude": True}
    # These products are useful as statistics/provenance, but duplicate the
    # core benchmark view or have no overlap with the frozen 2018 window.
    if product["id"] in {"lp_events", "operational_full"}:
        return {}
    return {"overview": True, "depth": product["id"] == "relocated_events"}


def _event_records_for_plot(product, stats, limit=100000):
    selection = _plot_selection(product, stats)
    records = []
    for record in iter_records(product):
        if not _matches_selection(record, product, selection):
            continue
        if any(record.get(k) is not None for k in ("latitude_deg", "longitude_deg", "depth_km", "magnitude")) or record.get("datetime") is not None:
            records.append(record)
        if len(records) >= limit:
            break
    return selection, records


def _daily_values(summary):
    daily = summary.get("daily_counts", {}) if summary else {}
    dates = sorted(daily)
    return dates, [daily[d] for d in dates]


def plot_event_product(product, stats):
    out = FIGURES_ROOT / product["id"]
    _clean_figure_dir(out)
    policy = _plot_policy(product)
    if not policy.get("overview"):
        return
    selection, records = _event_records_for_plot(product, stats)
    summary = stats.get(selection, stats.get("full", {}))
    points = [r for r in records if r.get("longitude_deg") is not None and r.get("latitude_deg") is not None]
    depths = [r.get("depth_km") for r in points if r.get("depth_km") is not None]
    mags = [r.get("magnitude") for r in records if r.get("magnitude") is not None]
    dates, daily = _daily_values(summary)
    has_map = bool(points)
    has_rate = bool(dates)
    has_depth = bool(policy.get("depth") and points and depths)
    has_magnitude = bool(FULL_PLOTS and mags)
    n_panels = int(has_map) + int(has_rate) + int(has_depth) + int(has_magnitude)
    if n_panels == 0:
        return

    fig, axes = plt.subplots(1, n_panels, figsize=(3.15 * n_panels, 3.15), squeeze=False)
    axes = list(axes[0])
    panel = 0
    if has_map:
        ax = axes[panel]; panel += 1
        coords = [(r["longitude_deg"], r["latitude_deg"]) for r in points]
        z = [r.get("depth_km") for r in points]
        if all(value is not None for value in z):
            sc = ax.scatter([p[0] for p in coords], [p[1] for p in coords], c=z,
                            s=7, alpha=0.68, linewidths=0, cmap="cividis")
            cbar = fig.colorbar(sc, ax=ax, fraction=0.046, pad=0.04)
            cbar.set_label("Depth (km)")
            cbar.ax.tick_params(labelsize=7, width=0.5)
        else:
            ax.scatter([p[0] for p in coords], [p[1] for p in coords],
                       s=7, alpha=0.68, linewidths=0, color=NATURE_BLUE)
        ax.set_xlabel("Longitude (°)"); ax.set_ylabel("Latitude (°)")
        _style_axes(ax, grid=False); _panel_label(ax, "a")

    if has_rate:
        ax = axes[panel]; panel += 1
        x = list(range(len(dates)))
        ax.plot(x, daily, color=NATURE_ORANGE, linewidth=1.25, marker="o",
                markersize=2.2, markeredgewidth=0)
        step = max(1, len(dates) // 6)
        ax.set_xticks(x[::step]); ax.set_xticklabels(dates[::step], rotation=35, ha="right")
        ax.set_xlabel("UTC date"); ax.set_ylabel("Rows / events")
        _style_axes(ax); _panel_label(ax, chr(ord("a") + panel - 1))

    if has_depth:
        ax = axes[panel]; panel += 1
        ax.scatter([r["longitude_deg"] for r in points if r.get("depth_km") is not None],
                   [r["depth_km"] for r in points if r.get("depth_km") is not None],
                   s=7, alpha=0.60, linewidths=0, color=NATURE_TEAL)
        ax.invert_yaxis(); ax.set_xlabel("Longitude (°)"); ax.set_ylabel("Depth (km)")
        _style_axes(ax, grid=False); _panel_label(ax, chr(ord("a") + panel - 1))

    if has_magnitude:
        ax = axes[panel]; panel += 1
        ax.hist(mags, bins=30, color=NATURE_PURPLE, alpha=0.88, edgecolor="white", linewidth=0.3)
        ax.set_xlabel("Native magnitude"); ax.set_ylabel("Rows")
        _style_axes(ax); _panel_label(ax, chr(ord("a") + panel - 1))

    fig.suptitle(f"{SOURCE_REF} · {product['id']} · {selection}", x=0.01, ha="left", fontsize=9)
    savefig(fig, out / "catalog_overview_v1")


def plot_relative_product(product, stats):
    out = FIGURES_ROOT / product["id"]
    _clean_figure_dir(out)
    if not _plot_policy(product).get("relative_overview"):
        return
    selection = _plot_selection(product, stats)
    summary = stats.get(selection, stats.get("full", {}))
    points, dates = [], []
    for record in iter_records(product):
        if not _matches_selection(record, product, selection):
            continue
        if record.get("x_m") is not None and record.get("y_m") is not None:
            points.append((record["x_m"], record["y_m"]))
        if record.get("datetime") is not None:
            dates.append(record["datetime"])
    daily_dates, daily = _daily_values(summary)
    if not points and not daily_dates:
        return
    fig, axes = plt.subplots(1, 2, figsize=(6.4, 3.15), squeeze=False)
    axes = list(axes[0])
    ax = axes[0]
    if points:
        ax.scatter([p[0] / 1000 for p in points], [p[1] / 1000 for p in points],
                   s=7, alpha=0.62, linewidths=0, color=NATURE_PURPLE)
    ax.set_xlabel("Native x (km)"); ax.set_ylabel("Native y (km)")
    _style_axes(ax, grid=False); _panel_label(ax, "a")
    ax = axes[1]
    if daily_dates:
        x = list(range(len(daily_dates)))
        ax.plot(x, daily, color=NATURE_ORANGE, linewidth=1.25, marker="o",
                markersize=2.2, markeredgewidth=0)
        step = max(1, len(daily_dates) // 6)
        ax.set_xticks(x[::step]); ax.set_xticklabels(daily_dates[::step], rotation=35, ha="right")
    ax.set_xlabel("UTC date"); ax.set_ylabel("Rows")
    _style_axes(ax); _panel_label(ax, "b")
    fig.suptitle(f"{SOURCE_REF} · native relative coordinates · {selection}", x=0.01, ha="left", fontsize=9)
    savefig(fig, out / "relative_overview_v1")


def plot_phase_product(product, stats):
    out = FIGURES_ROOT / product["id"]
    _clean_figure_dir(out)
    if not _plot_policy(product).get("phase_overview"):
        return
    selection = _plot_selection(product, stats)
    summary = stats.get(selection, stats.get("full", {}))
    phases = summary.get("phases", {})
    stations = summary.get("stations", {})
    dates, daily = _daily_values(summary)
    if not phases and not stations and not dates:
        return
    fig, axes = plt.subplots(1, 3, figsize=(8.8, 3.05), squeeze=False)
    axes = list(axes[0])

    ax = axes[0]
    keys = sorted(phases)
    ax.bar(keys, [phases[k] for k in keys], color=[NATURE_BLUE if k.upper() == "P" else NATURE_ORANGE for k in keys], width=0.65)
    ax.set_xlabel("Phase"); ax.set_ylabel("Phase rows")
    _style_axes(ax); _panel_label(ax, "a")

    ax = axes[1]
    top = sorted(stations.items(), key=lambda item: item[1], reverse=True)[:10]
    if top:
        labels = [item[0] for item in reversed(top)]
        values = [item[1] for item in reversed(top)]
        ax.barh(labels, values, color=NATURE_TEAL, height=0.65)
    ax.set_xlabel("Phase rows"); ax.set_ylabel("Station (top 10)")
    _style_axes(ax); _panel_label(ax, "b")

    ax = axes[2]
    if dates:
        x = list(range(len(dates)))
        ax.plot(x, daily, color=NATURE_ORANGE, linewidth=1.2, marker="o",
                markersize=1.9, markeredgewidth=0)
        step = max(1, len(dates) // 6)
        ax.set_xticks(x[::step]); ax.set_xticklabels(dates[::step], rotation=35, ha="right")
    ax.set_xlabel("UTC date"); ax.set_ylabel("Phase rows")
    _style_axes(ax); _panel_label(ax, "c")

    fig.suptitle(f"{SOURCE_REF} · {product['id']} · {selection}", x=0.01, ha="left", fontsize=9)
    savefig(fig, out / "phase_overview_v1")


def write_catalog_report(all_stats, paths):
    lines = [f"# {SOURCE_REF} catalog-local analysis", "", OVERVIEW, "", f"- Parser version: `{PARSER_VERSION}`", f"- Benchmark window: `[2018-05-01T00:00:00Z, 2018-05-09T00:00:00Z)`", "- Plot profile: minimal, benchmark-first, PNG-only; use `--full-plots` for optional diagnostics.", "- Raw files are unchanged; outputs below are reproducible derived artifacts.", "", "## Product summary", "", "| Product | Kind | Full rows | Unique native IDs | Benchmark/time rows |", "|---|---|---:|---:|---:|"]
    for product in PRODUCTS:
        stats = all_stats[product["id"]]
        full = stats.get("full", {})
        selected = stats.get("benchmark", stats.get("benchmark_time", stats.get("time_only", {})))
        lines.append(f"| `{product['id']}` | `{product['kind']}` | {full.get('row_count', 0)} | {full.get('unique_native_event_ids') if full.get('unique_native_event_ids') is not None else 'n/a'} | {selected.get('row_count', 0) if selected else 'n/a'} |")
    lines += ["", "## Product semantics", ""]
    for product in PRODUCTS:
        figure_note = f"`analysis/figures/{product['id']}/`" if _plot_policy(product) else "stats only in minimal profile"
        lines += [f"### `{product['id']}`", "", product["note"], "", f"- Native input: `{product['path']}`", f"- Derived output: `{paths.get(product['id']) or 'phase sample only; raw phase table is retained'}`", f"- Schema: `{schema_reference(product['kind'])}`", f"- Statistics: `analysis/stats/{product['id']}/`", f"- Figures: {figure_note}", ""]
    lines += ["## Interpretation", "", "Event products are summarized as event rows and unique native IDs. Phase/pick products are summarized by phase-row count, template/match IDs, station and phase composition; their row count is not an event count. The common summit mask is applied only where latitude, longitude and depth are available. Relative-coordinate products retain native coordinates and use time-only selection.", ""]
    (ANALYSIS_ROOT / "catalog_analysis.md").write_text("\n".join(lines), encoding="utf-8")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--only", action="append", help="run selected product_id values")
    parser.add_argument("--force", action="store_true", help="ignore cached large-product profiles")
    parser.add_argument("--full-plots", action="store_true", help="include optional diagnostic panels; default is compact")
    args = parser.parse_args()
    global FORCE, FULL_PLOTS
    FORCE = args.force
    FULL_PLOTS = args.full_plots
    for d in (ANALYSIS_ROOT, STATS_ROOT, FIGURES_ROOT, DERIVED_ROOT):
        d.mkdir(parents=True, exist_ok=True)
    selected = [p for p in PRODUCTS if not args.only or p["id"] in args.only]
    all_stats, paths = {}, {}
    for product in selected:
        cached = load_cached_product(product)
        if cached is not None:
                    stats, normalized_path = cached, None
        else:
            stats, normalized_path = profile_product(product)
        all_stats[product["id"]] = stats; paths[product["id"]] = normalized_path
        if product["kind"] == "phase_csv": plot_phase_product(product, stats)
        elif product["kind"] == "lengline": plot_relative_product(product, stats)
        else: plot_event_product(product, stats)
    if len(selected) == len(PRODUCTS):
        write_catalog_report(all_stats, paths)
    print(json.dumps({k: {s: v.get("row_count", 0) for s, v in stats.items()} for k, stats in all_stats.items()}, indent=2))


if __name__ == "__main__":
    main()
