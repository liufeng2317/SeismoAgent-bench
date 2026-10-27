"""Waveform review plots for audited events (docs/framework/03_EVALUATION_METRICS.md §5 L1 audit).

One PNG per event: three-component records of the nearest stations, 2-15 Hz,
each trace normalised, aligned on the event's origin time, with the event's
predicted P and S (homogeneous Vp 6.0, Vs 3.46 km/s) and those of every
context-catalog event in the window (a larger earlier event, a neighbour in
the same catalog). The reviewer labels the event earthquake /
not_earthquake / undecidable in audit_labels.csv; the plot shows no
information about where the event came from.

CLI:
  python -m SeismoAgentBench.scoring.catalog_metrics.audit_plots --task-dir T \\
      --events events.csv --out-dir D [--context context.csv] [--limit N]
events/context CSV: event_id, origin_time_utc, latitude, longitude, depth_km[, magnitude]
(events may add source_id: the event's id in the context catalog, so it is not drawn as context)
"""

from __future__ import annotations

import argparse
import json
from functools import lru_cache
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from obspy import UTCDateTime, read, read_inventory  # noqa: E402

VP, VS = 6.0, 3.46
FAMILY_ORDER = ("HH", "BH", "EH", "SH", "DH", "EN", "HN", "CN")
EVENT_COLOR, CONTEXT_COLOR = "#D55E00", "#0072B2"


def input_root(task_dir: Path) -> Path:
    entries = json.loads((task_dir / "input.json").read_text())["entries"]
    return Path(entries[0]["path"])


@lru_cache(maxsize=4)
def stations(root: str) -> pd.DataFrame:
    """One row per station with data: coordinates and the preferred channel family."""
    rows = {}
    for xml in sorted(Path(root, "stations").glob("*.stationxml")):
        for net in read_inventory(str(xml)):
            for sta in net:
                key = f"{net.code}.{sta.code}"
                if key not in rows and Path(root, "data", key).is_dir():
                    rows[key] = (sta.latitude, sta.longitude)
    out = []
    for key, (lat, lon) in rows.items():
        files = [p.name for p in Path(root, "data", key).glob("*.mseed")]
        families = {f.split("__")[0].split(".")[-1][:2] for f in files}
        family = next((f for f in FAMILY_ORDER if f in families), None)
        if family:
            out.append({"station": key, "latitude": lat, "longitude": lon, "family": family})
    return pd.DataFrame(out)


def _km(lat0, lon0, lat, lon):
    return np.hypot((lat - lat0) * 111.195, (lon - lon0) * 111.195 * np.cos(np.radians(lat0)))


def _traces(root: Path, station: str, family: str, t0: UTCDateTime, t1: UTCDateTime):
    day = t0.strftime("%Y%m%d")
    st = None
    for path in sorted(Path(root, "data", station).glob(f"{station}.*.{family}?__{day}T000000Z__*.mseed")):
        try:
            part = read(str(path), starttime=t0 - 5, endtime=t1 + 5)
        except Exception:
            continue
        st = part if st is None else st + part
    if st is None or not len(st):
        return None
    st.merge(fill_value=0)
    st.detrend("demean")
    st.taper(0.05)
    st.filter("bandpass", freqmin=2.0, freqmax=15.0, corners=4, zerophase=True)
    st.trim(t0, t1)
    return st


def plot_event(root: Path, event: dict, context: pd.DataFrame | None, out_png: Path,
               n_stations: int = 6, pre: float = 10.0, post: float = 30.0) -> bool:
    origin = UTCDateTime(str(event["origin_time_utc"]))
    sta = stations(str(root)).copy()
    sta["dist"] = _km(event["latitude"], event["longitude"], sta.latitude.to_numpy(), sta.longitude.to_numpy())
    sta = sta.sort_values("dist")
    t0, t1 = origin - pre, origin + post
    panels = []
    for row in sta.itertuples():
        st = _traces(root, row.station, row.family, t0, t1)
        if st is not None:
            panels.append((row, st))
        if len(panels) == n_stations:
            break
    if not panels:
        return False
    others = pd.DataFrame()
    if context is not None and len(context):
        ct = context.copy()
        ct["t"] = [UTCDateTime(str(x)) - origin for x in ct.origin_time_utc]
        own = str(event.get("source_id") or event["event_id"])  # the reviewed event itself is not context
        others = ct[(ct.t > -120) & (ct.t < post) & (ct.event_id.astype(str) != own)]
    fig, axes = plt.subplots(len(panels), 1, figsize=(7.2, 1.25 * len(panels) + 0.8), sharex=True)
    axes = np.atleast_1d(axes)
    depth = float(event.get("depth_km") or 5.0)
    for ax, (row, st) in zip(axes, panels):
        for k, tr in enumerate(sorted(st, key=lambda tr: tr.stats.channel[-1] != "Z")[:3]):
            t = tr.times() + (tr.stats.starttime - origin)
            peak = np.max(np.abs(tr.data)) or 1.0
            ax.plot(t, tr.data / peak * 0.45 - k, lw=0.5, color="0.15")
            ax.text(-pre + 0.2, -k + 0.2, tr.stats.channel, fontsize=5.5, color="0.4")
        r = np.hypot(row.dist, depth)
        for v, style in ((VP, "-"), (VS, "--")):
            ax.axvline(r / v, color=EVENT_COLOR, lw=1.0, ls=style)
        for o in others.itertuples():
            ro = np.hypot(_km(o.latitude, o.longitude, row.latitude, row.longitude), float(o.depth_km or 5.0))
            for v, style in ((VP, "-"), (VS, "--")):
                ta = o.t + ro / v
                if -pre <= ta <= post:
                    ax.axvline(ta, color=CONTEXT_COLOR, lw=0.8, ls=style, alpha=0.8)
                    if v == VP:
                        label = f"M{o.magnitude:.1f}" if "magnitude" in others and pd.notna(o.magnitude) else "event"
                        ax.text(ta, 0.55, label, fontsize=5.5, color=CONTEXT_COLOR, ha="center")
        ax.set_yticks([])
        ax.set_ylabel(f"{row.station}\n{row.dist:.0f} km", fontsize=6.5, rotation=0, ha="right", va="center")
        ax.spines[["left", "top", "right"]].set_visible(False)
    axes[-1].set_xlabel("seconds after the reviewed origin time")
    axes[-1].set_xlim(-pre, post)
    mag = event.get("magnitude")
    fig.suptitle(f"{event['event_id']}  {str(event['origin_time_utc'])[:22]}  "
                 f"{'' if mag is None or pd.isna(mag) else f'M{float(mag):.1f}'}  —  "
                 "orange: this event's predicted P (solid) / S (dashed); blue: other catalog events",
                 fontsize=7, x=0.01, ha="left")
    fig.tight_layout()
    out_png.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_png, dpi=150)
    plt.close(fig)
    return True


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--task-dir", type=Path, required=True)
    ap.add_argument("--events", type=Path, required=True)
    ap.add_argument("--context", type=Path)
    ap.add_argument("--out-dir", type=Path, required=True)
    ap.add_argument("--limit", type=int, default=0)
    a = ap.parse_args(argv)
    root = input_root(a.task_dir.resolve())
    events = pd.read_csv(a.events)
    if a.limit:
        events = events.head(a.limit)
    context = pd.read_csv(a.context) if a.context else None
    done = 0
    for ev in events.to_dict("records"):
        if plot_event(root, ev, context, a.out_dir / f"{ev['event_id']}.png"):
            done += 1
    print(f"{done}/{len(events)} plots in {a.out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
