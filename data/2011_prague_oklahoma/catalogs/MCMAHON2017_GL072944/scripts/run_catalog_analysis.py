#!/usr/bin/env python3
"""Compact, catalog-local Prague catalog profiling.

Raw files are never modified.  The default profile writes benchmark-first
300-dpi PNG figures, schemas, normalized event tables, and JSON statistics
under this catalog bundle's analysis/ directory.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
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

CASE_ID = "2011_prague_oklahoma"
SOURCE_REF = "MCMAHON2017_GL072944"
CATALOG_ROOT = Path(__file__).resolve().parents[1]
ANALYSIS_ROOT = CATALOG_ROOT / "analysis"
STATS_ROOT = ANALYSIS_ROOT / "stats"
FIGURES_ROOT = ANALYSIS_ROOT / "figures"
DERIVED_ROOT = ANALYSIS_ROOT / "derived"
PARSER_VERSION = "prague-local-v1-compact"
UTC = timezone.utc
WINDOW_START = datetime(2011, 11, 11, tzinfo=UTC)
WINDOW_END = datetime(2011, 11, 19, tzinfo=UTC)
# Common comparison mask used by the official benchmark query.  Research
# products retain a separate time_only selection, which is the canonical
# Cochran window (2,078 rows before this rounded sensitivity mask).
LAT_MIN, LAT_MAX = 35.4523, 35.5576
LON_MIN, LON_MAX = -96.8723, -96.7334
DEPTH_MIN, DEPTH_MAX = 1.02, 9.62
PRODUCTS = [{'id': 'events_subspace', 'kind': 'mcmahon_event', 'path': 'raw/MCMAHON2017_GL072944__catalog_subspace_5446events.txt', 'unit': 'event', 'role': 'secondary', 'note': 'McMahon subspace/Bayesloc E-record event catalog.'}, {'id': 'phase_arrivals', 'kind': 'mcmahon_phase', 'path': 'raw/MCMAHON2017_GL072944__catalog_subspace_5446events.txt', 'unit': 'phase_pick', 'role': 'auxiliary', 'note': 'McMahon P-record phase observations; row count is not an event count and release timestamps omit hour.'}]
OVERVIEW = "Independent subspace-detection/Bayesloc event and phase products; E and P records are analyzed separately."

MCMAHON_EVENT_TIME_CACHE = None


def finite_float(value):
    try:
        result = float(value)
    except (TypeError, ValueError):
        return None
    return result if math.isfinite(result) else None


def parse_iso(value):
    if not value:
        return None
    try:
        dt = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        return dt.replace(tzinfo=UTC) if dt.tzinfo is None else dt.astimezone(UTC)
    except ValueError:
        return None


def parse_parts_datetime(parts):
    try:
        year, month, day, hour, minute = [int(parts[i]) for i in range(5)]
        second = float(parts[5])
        return datetime(year, month, day, hour, minute, tzinfo=UTC) + timedelta(seconds=second)
    except (TypeError, ValueError, IndexError, OverflowError):
        return None


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def json_safe(value):
    if isinstance(value, dict):
        return {str(key): json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [json_safe(item) for item in value]
    if isinstance(value, float) and (math.isnan(value) or math.isinf(value)):
        return None
    return value


def parse_mcmahon_event(cols):
    if len(cols) < 12 or cols[0] != "E":
        return None
    return {
        "datetime": parse_parts_datetime(cols[2:8]),
        "native_event_id": cols[1],
        "latitude_deg": finite_float(cols[8]),
        "longitude_deg": finite_float(cols[9]),
        "depth_km": finite_float(cols[10]),
        "magnitude": finite_float(cols[11]),
        "magnitude_type": "unresolved",
        "network": "mixed",
    }


def mcmahon_event_times():
    global MCMAHON_EVENT_TIME_CACHE
    if MCMAHON_EVENT_TIME_CACHE is not None:
        return MCMAHON_EVENT_TIME_CACHE
    product = next((item for item in PRODUCTS if item["kind"] == "mcmahon_event"), None)
    if product is None:
        MCMAHON_EVENT_TIME_CACHE = {}
        return MCMAHON_EVENT_TIME_CACHE
    result = {}
    with (CATALOG_ROOT / product["path"]).open("r", encoding="utf-8", errors="replace") as handle:
        for line in handle:
            record = parse_mcmahon_event(line.split())
            if record:
                result[str(record["native_event_id"])] = record.get("datetime")
    MCMAHON_EVENT_TIME_CACHE = result
    return result


def iter_records(product):
    path = CATALOG_ROOT / product["path"]
    kind = product["kind"]
    if kind == "cochran_event":
        with path.open("r", encoding="utf-8", errors="replace") as handle:
            for line_no, line in enumerate(handle, start=1):
                cols = line.split()
                if len(cols) < 11:
                    continue
                dt = parse_parts_datetime(cols[0:6])
                yield {
                    "datetime": dt, "native_event_id": cols[6],
                    "latitude_deg": finite_float(cols[7]), "longitude_deg": finite_float(cols[8]),
                    "depth_km": finite_float(cols[9]), "magnitude": finite_float(cols[10]),
                    "magnitude_type": "unresolved", "network": "mixed",
                    "source_row": line_no, "raw": cols,
                }
        return
    if kind == "mcmahon_event":
        with path.open("r", encoding="utf-8", errors="replace") as handle:
            for line_no, line in enumerate(handle, start=1):
                record = parse_mcmahon_event(line.split())
                if record:
                    record["source_row"] = line_no
                    record["raw"] = line.split()
                    yield record
        return
    if kind == "mcmahon_phase":
        event_times = mcmahon_event_times()
        with path.open("r", encoding="utf-8", errors="replace") as handle:
            for line_no, line in enumerate(handle, start=1):
                cols = line.split()
                if len(cols) < 10 or cols[0] != "P":
                    continue
                event_id = str(cols[1])
                yield {
                    # The release P row has no hour token.  Selection uses
                    # the parent E-record origin time; raw phase tokens stay
                    # intact for later schema repair.
                    "datetime": event_times.get(event_id),
                    "native_event_id": event_id,
                    "network": cols[2], "station": cols[3], "phase": cols[4],
                    "phase_time_raw": " ".join(cols[5:10]),
                    "source_row": line_no, "raw": cols,
                }
        return
    if kind == "isken_event":
        with path.open("r", encoding="utf-8", errors="replace", newline="") as handle:
            for row_no, row in enumerate(csv.DictReader(handle), start=2):
                yield {
                    "datetime": parse_iso(row.get("time_utc")),
                    "native_event_id": row.get("no"),
                    "latitude_deg": finite_float(row.get("latitude_deg")),
                    "longitude_deg": finite_float(row.get("longitude_deg")),
                    "depth_km": finite_float(row.get("depth_km")),
                    "magnitude": finite_float(row.get("Mw")),
                    "magnitude_type": "Mw", "network": "mixed",
                    "horizontal_error_km": finite_float(row.get("erh_km")),
                    "vertical_error_km": finite_float(row.get("erz_km")),
                    "rms_s": finite_float(row.get("rms_s")),
                    "source_row": row_no, "raw": row,
                }
        return
    if kind == "usgs_csv":
        with path.open("r", encoding="utf-8", errors="replace", newline="") as handle:
            for row_no, row in enumerate(csv.DictReader(handle), start=2):
                yield {
                    "datetime": parse_iso(row.get("time")),
                    "native_event_id": row.get("id"),
                    "latitude_deg": finite_float(row.get("latitude")),
                    "longitude_deg": finite_float(row.get("longitude")),
                    "depth_km": finite_float(row.get("depth")),
                    "magnitude": finite_float(row.get("mag")),
                    "magnitude_type": row.get("magType"), "network": row.get("net"),
                    "quality_flag": row.get("status"), "source_row": row_no, "raw": row,
                }
        return
    raise ValueError(f"Unsupported product kind: {kind}")


def in_time(dt):
    return dt is not None and WINDOW_START <= dt < WINDOW_END


def in_common_mask(record):
    lat, lon, depth = record.get("latitude_deg"), record.get("longitude_deg"), record.get("depth_km")
    return all(value is not None for value in (lat, lon, depth)) and LAT_MIN <= lat <= LAT_MAX and LON_MIN <= lon <= LON_MAX and DEPTH_MIN <= depth <= DEPTH_MAX


def selection_names(record, product):
    if product["kind"] == "mcmahon_phase":
        return ["full"] + (["benchmark_time"] if in_time(record.get("datetime")) else [])
    names = ["full"]
    if in_time(record.get("datetime")):
        names.append("time_only")
        if in_common_mask(record):
            names.append("benchmark")
    return names


def matches_selection(record, selection):
    if selection == "full":
        return True
    if not in_time(record.get("datetime")):
        return False
    if selection == "benchmark_time" or selection == "time_only":
        return True
    return selection == "benchmark" and in_common_mask(record)


class Accumulator:
    def __init__(self, kind):
        self.kind = kind
        self.rows = 0
        self.native_ids = set()
        self.duplicate_ids = 0
        self.missing = Counter()
        self.ranges = {key: [None, None] for key in ("latitude_deg", "longitude_deg", "depth_km", "magnitude")}
        self.daily = Counter()
        self.hourly = Counter()
        self.magnitude_types = Counter()
        self.networks = Counter()
        self.stations = Counter()
        self.phases = Counter()

    def _range(self, key, value):
        value = finite_float(value)
        if value is None:
            return
        low, high = self.ranges[key]
        self.ranges[key] = [value if low is None else min(low, value), value if high is None else max(high, value)]

    def add_event(self, record):
        self.rows += 1
        native_id = record.get("native_event_id")
        if native_id in (None, ""):
            self.missing["native_event_id"] += 1
        elif str(native_id) in self.native_ids:
            self.duplicate_ids += 1
        else:
            self.native_ids.add(str(native_id))
        dt = record.get("datetime")
        if dt is None:
            self.missing["origin_time_utc"] += 1
        else:
            self.daily[dt.date().isoformat()] += 1
            self.hourly[dt.strftime("%Y-%m-%dT%H")] += 1
        for key in self.ranges:
            if finite_float(record.get(key)) is None:
                self.missing[key] += 1
            else:
                self._range(key, record.get(key))
        self.magnitude_types[str(record.get("magnitude_type") or "unknown")] += 1
        if record.get("network"):
            self.networks[str(record["network"])] += 1

    def add_phase(self, record):
        self.rows += 1
        event_id = record.get("native_event_id")
        if event_id in (None, ""):
            self.missing["parent_event_id"] += 1
        else:
            if str(event_id) in self.native_ids:
                self.duplicate_ids += 1
            self.native_ids.add(str(event_id))
        if record.get("datetime") is None:
            self.missing["parent_origin_time_utc"] += 1
        else:
            self.daily[record["datetime"].date().isoformat()] += 1
            self.hourly[record["datetime"].strftime("%Y-%m-%dT%H")] += 1
        for key in ("network", "station", "phase"):
            if not record.get(key):
                self.missing[key] += 1
        if record.get("network"):
            self.networks[str(record["network"])] += 1
        if record.get("station"):
            self.stations[str(record["station"])] += 1
        if record.get("phase"):
            self.phases[str(record["phase"])] += 1

    def as_dict(self):
        return json_safe({
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
            "daily_counts": dict(sorted(self.daily.items())),
            "hourly_counts": dict(sorted(self.hourly.items())),
        })


def schema_reference(kind):
    if kind == "lengline":
        return "docs/schemas/catalog_relative_event.schema.yaml"
    if kind == "mcmahon_phase":
        return "docs/schemas/catalog_parent_phase.schema.yaml"
    if kind == "phase_csv":
        return "docs/schemas/catalog_correlation_phase.schema.yaml"
    return "docs/schemas/catalog_event.schema.yaml"


def write_normalized(product):
    if product["kind"] == "mcmahon_phase":
        return None
    out = DERIVED_ROOT / product["id"]
    out.mkdir(parents=True, exist_ok=True)
    path = out / f"{SOURCE_REF}__{product['id']}__normalized_v1.csv"
    fields = ["event_id", "native_event_id", "origin_time_utc", "latitude_deg", "longitude_deg", "depth_km", "magnitude", "magnitude_type", "network", "source_row", "extras_json"]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row_no, record in enumerate(iter_records(product), start=1):
            excluded = {"datetime", "native_event_id", "latitude_deg", "longitude_deg", "depth_km", "magnitude", "magnitude_type", "network", "source_row", "raw"}
            extras = {key: value for key, value in record.items() if key not in excluded}
            row = {key: "" for key in fields}
            row["event_id"] = f"E{row_no:06d}"
            row["native_event_id"] = record.get("native_event_id") or ""
            if record.get("datetime"):
                row["origin_time_utc"] = record["datetime"].isoformat().replace("+00:00", "Z")
            for key in ("latitude_deg", "longitude_deg", "depth_km", "magnitude", "magnitude_type", "network", "source_row"):
                if record.get(key) is not None:
                    row[key] = record[key]
            row["extras_json"] = json.dumps(json_safe(extras), sort_keys=True)
            writer.writerow(row)
    return str(path.relative_to(CATALOG_ROOT))


def profile_product(product):
    path = CATALOG_ROOT / product["path"]
    is_phase = product["kind"] == "mcmahon_phase"
    accumulators = {}
    phase_sample = []
    for record in iter_records(product):
        for selection in selection_names(record, product):
            accumulators.setdefault(selection, Accumulator(product["kind"]))
            if is_phase:
                accumulators[selection].add_phase(record)
                if selection == "full" and len(phase_sample) < 10000:
                    phase_sample.append(record)
            else:
                accumulators[selection].add_event(record)
    normalized_path = write_normalized(product)
    out = STATS_ROOT / product["id"]
    out.mkdir(parents=True, exist_ok=True)
    stats = {}
    for selection, accumulator in accumulators.items():
        stats[selection] = accumulator.as_dict()
        payload = {
            "case_id": CASE_ID, "source_ref": SOURCE_REF, "product_id": product["id"],
            "kind": product["kind"], "unit": product["unit"], "selection": selection,
            "selection_rule": "[2011-11-11T00:00:00Z, 2011-11-19T00:00:00Z); rounded common Prague mask where applicable",
            "time_basis": "parent E-record origin time" if is_phase else "native origin time",
            "parser_version": PARSER_VERSION, "source_path": product["path"],
            "source_sha256": sha256(path),
            "generated_utc": datetime.now(UTC).replace(microsecond=0).isoformat(),
            "stats": stats[selection],
        }
        (out / f"{selection}_v1.json").write_text(json.dumps(json_safe(payload), indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    if is_phase and phase_sample:
        sample = DERIVED_ROOT / product["id"] / f"{SOURCE_REF}__{product['id']}__sample_v1.csv"
        sample.parent.mkdir(parents=True, exist_ok=True)
        fields = ["native_event_id", "network", "station", "phase", "parent_origin_time_utc", "phase_time_raw", "source_row"]
        with sample.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=fields)
            writer.writeheader()
            for record in phase_sample:
                writer.writerow({
                    "native_event_id": record.get("native_event_id", ""),
                    "network": record.get("network", ""), "station": record.get("station", ""),
                    "phase": record.get("phase", ""),
                    "parent_origin_time_utc": record["datetime"].isoformat().replace("+00:00", "Z") if record.get("datetime") else "",
                    "phase_time_raw": record.get("phase_time_raw", ""), "source_row": record.get("source_row", ""),
                })
    return stats, normalized_path


RUN_FIGURE_STEMS = {"catalog_overview_v1", "phase_overview_v1", "map_v1", "depth_section_v1", "event_rate_v1", "magnitude_distribution_v1"}


def clean_figure_dir(out):
    out.mkdir(parents=True, exist_ok=True)
    for candidate in out.iterdir():
        if candidate.is_file() and (candidate.suffix.lower() == ".svg" or candidate.stem in RUN_FIGURE_STEMS):
            candidate.unlink()


def style_axes(ax, grid=True):
    ax.spines["top"].set_visible(False); ax.spines["right"].set_visible(False)
    ax.spines["left"].set_linewidth(0.6); ax.spines["bottom"].set_linewidth(0.6)
    ax.tick_params(width=0.6, length=3, pad=2)
    if grid:
        ax.set_axisbelow(True); ax.grid(axis="y", color="#D9DEE3", linewidth=0.45, alpha=0.75)


def panel_label(ax, label):
    ax.text(-0.12, 1.04, label, transform=ax.transAxes, fontsize=9, fontweight="bold", va="bottom", ha="left")


def savefig(fig, path):
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.tight_layout(pad=0.45)
    fig.savefig(path.with_suffix(".png"), dpi=300, facecolor="white", bbox_inches="tight")
    stale_svg = path.with_suffix(".svg")
    if stale_svg.exists():
        stale_svg.unlink()
    plt.close(fig)


def plot_selection(stats):
    for candidate in ("benchmark", "benchmark_time", "time_only", "full"):
        if candidate in stats and stats[candidate].get("row_count", 0):
            return candidate
    return "full"


def plot_policy(product):
    if product["kind"] == "mcmahon_phase":
        return {"phase": True}
    if product["id"] in {"operational_full"} and not FULL_PLOTS:
        return {}
    return {"event": True, "depth": product["id"] != "operational_benchmark" or FULL_PLOTS}


def plot_event_product(product, stats):
    out = FIGURES_ROOT / product["id"]
    clean_figure_dir(out)
    if not plot_policy(product).get("event"):
        return
    selection = plot_selection(stats)
    summary = stats.get(selection, stats.get("full", {}))
    records = [record for record in iter_records(product) if matches_selection(record, selection)]
    points = [record for record in records if record.get("longitude_deg") is not None and record.get("latitude_deg") is not None]
    dates = sorted(summary.get("daily_counts", {}))
    daily = [summary["daily_counts"][date] for date in dates]
    depths = [record for record in points if record.get("depth_km") is not None]
    panels = int(bool(points)) + int(bool(dates)) + int(bool(depths) and plot_policy(product).get("depth"))
    if panels == 0:
        return
    fig, axes = plt.subplots(1, panels, figsize=(3.15 * panels, 3.15), squeeze=False)
    axes = list(axes[0]); index = 0
    if points:
        ax = axes[index]; index += 1
        values = [record.get("depth_km") for record in points]
        if all(value is not None for value in values):
            sc = ax.scatter([record["longitude_deg"] for record in points], [record["latitude_deg"] for record in points], c=values, s=8, alpha=0.70, linewidths=0, cmap="cividis")
            cbar = fig.colorbar(sc, ax=ax, fraction=0.046, pad=0.04); cbar.set_label("Depth (km)"); cbar.ax.tick_params(labelsize=7, width=0.5)
        else:
            ax.scatter([record["longitude_deg"] for record in points], [record["latitude_deg"] for record in points], s=8, alpha=0.70, linewidths=0, color=NATURE_BLUE)
        ax.set_xlabel("Longitude (°)"); ax.set_ylabel("Latitude (°)"); style_axes(ax, grid=False); panel_label(ax, "a")
    if dates:
        ax = axes[index]; index += 1
        x = list(range(len(dates))); ax.plot(x, daily, color=NATURE_ORANGE, linewidth=1.25, marker="o", markersize=2.2, markeredgewidth=0)
        step = max(1, len(dates) // 6); ax.set_xticks(x[::step]); ax.set_xticklabels(dates[::step], rotation=35, ha="right")
        ax.set_xlabel("UTC date"); ax.set_ylabel("Rows / events"); style_axes(ax); panel_label(ax, chr(ord("a") + index - 1))
    if depths and plot_policy(product).get("depth"):
        ax = axes[index]
        ax.scatter([record["longitude_deg"] for record in depths], [record["depth_km"] for record in depths], s=8, alpha=0.65, linewidths=0, color=NATURE_TEAL)
        ax.invert_yaxis(); ax.set_xlabel("Longitude (°)"); ax.set_ylabel("Depth (km)"); style_axes(ax, grid=False); panel_label(ax, chr(ord("a") + index))
    fig.suptitle(f"{SOURCE_REF} · {product['id']} · {selection}", x=0.01, ha="left", fontsize=9)
    savefig(fig, out / "catalog_overview_v1")


def plot_phase_product(product, stats):
    out = FIGURES_ROOT / product["id"]
    clean_figure_dir(out)
    if not plot_policy(product).get("phase"):
        return
    selection = plot_selection(stats); summary = stats.get(selection, stats.get("full", {}))
    phases = summary.get("phases", {}); stations = summary.get("stations", {}); dates = sorted(summary.get("daily_counts", {})); daily = [summary["daily_counts"][date] for date in dates]
    if not phases and not stations and not dates:
        return
    fig, axes = plt.subplots(1, 3, figsize=(8.8, 3.05), squeeze=False); axes = list(axes[0])
    ax = axes[0]; keys = sorted(phases); ax.bar(keys, [phases[key] for key in keys], color=[NATURE_BLUE if key.upper().startswith("P") else NATURE_ORANGE for key in keys], width=0.65); ax.set_xlabel("Phase"); ax.set_ylabel("Phase rows"); style_axes(ax); panel_label(ax, "a")
    ax = axes[1]; top = sorted(stations.items(), key=lambda item: item[1], reverse=True)[:10]
    if top:
        labels = [item[0] for item in reversed(top)]; values = [item[1] for item in reversed(top)]; ax.barh(labels, values, color=NATURE_TEAL, height=0.65)
    ax.set_xlabel("Phase rows"); ax.set_ylabel("Station (top 10)"); style_axes(ax); panel_label(ax, "b")
    ax = axes[2]
    if dates:
        x = list(range(len(dates))); ax.plot(x, daily, color=NATURE_ORANGE, linewidth=1.2, marker="o", markersize=2.0, markeredgewidth=0); step = max(1, len(dates) // 6); ax.set_xticks(x[::step]); ax.set_xticklabels(dates[::step], rotation=35, ha="right")
    ax.set_xlabel("Parent-event UTC date"); ax.set_ylabel("Phase rows"); style_axes(ax); panel_label(ax, "c")
    fig.suptitle(f"{SOURCE_REF} · {product['id']} · {selection}", x=0.01, ha="left", fontsize=9); savefig(fig, out / "phase_overview_v1")


def write_report(all_stats, paths):
    lines = [f"# {SOURCE_REF} catalog-local analysis", "", OVERVIEW, "", f"- Parser version: `{PARSER_VERSION}`", f"- Benchmark window: `[2011-11-11T00:00:00Z, 2011-11-19T00:00:00Z)`", "- Plot profile: minimal, benchmark-first, PNG-only; use `--full-plots` for optional diagnostics.", "- Raw files are unchanged; event, phase and baseline products remain separate.", "", "## Product summary", "", "| Product | Kind | Full rows | Unique event IDs | Frozen selection |", "|---|---|---:|---:|---:|"]
    for product in PRODUCTS:
        stats = all_stats[product["id"]]; full = stats.get("full", {}); selected = stats.get("benchmark", stats.get("benchmark_time", stats.get("time_only", {})))
        lines.append(f"| `{product['id']}` | `{product['kind']}` | {full.get('row_count', 0)} | {full.get('unique_native_event_ids') if full.get('unique_native_event_ids') is not None else 'n/a'} | {selected.get('row_count', 0) if selected else 'n/a'} |")
    lines += ["", "## Product semantics", ""]
    for product in PRODUCTS:
        figure_note = f"`analysis/figures/{product['id']}/`" if plot_policy(product) else "stats only in minimal profile"
        lines += [f"### `{product['id']}`", "", product["note"], "", f"- Native input: `{product['path']}`", f"- Derived output: `{paths.get(product['id']) or 'phase sample only; raw phase table is retained'}`", f"- Schema: `{schema_reference(product['kind'])}`", f"- Statistics: `analysis/stats/{product['id']}/`", f"- Figures: {figure_note}", ""]
    lines += ["## Interpretation", "", "Cochran, McMahon, Isken and ComCat are separate reference populations. McMahon P rows are pick-level observations and use parent E-record origin time for the frozen selection because the distributed P schema omits an hour token; the raw phase tokens are retained unchanged. Isken is a sparse manual relocation anchor, not a completeness catalog. Magnitude types remain source-native or unresolved.", ""]
    (ANALYSIS_ROOT / "catalog_analysis.md").write_text("\n".join(lines), encoding="utf-8")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--only", action="append", help="run selected product_id values")
    parser.add_argument("--full-plots", action="store_true", help="include optional diagnostics; default is compact")
    args = parser.parse_args()
    global FULL_PLOTS
    FULL_PLOTS = args.full_plots
    for directory in (ANALYSIS_ROOT, STATS_ROOT, FIGURES_ROOT, DERIVED_ROOT):
        directory.mkdir(parents=True, exist_ok=True)
    selected = [product for product in PRODUCTS if not args.only or product["id"] in args.only]
    all_stats, paths = {}, {}
    for product in selected:
        stats, normalized_path = profile_product(product)
        all_stats[product["id"]] = stats; paths[product["id"]] = normalized_path
        if product["kind"] == "mcmahon_phase":
            plot_phase_product(product, stats)
        else:
            plot_event_product(product, stats)
    if len(selected) == len(PRODUCTS):
        write_report(all_stats, paths)
    print(json.dumps({key: {selection: value.get("row_count", 0) for selection, value in stats.items()} for key, stats in all_stats.items()}, indent=2))


if __name__ == "__main__":
    main()
