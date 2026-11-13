"""a1 round 3: download event-window waveforms and station responses for the first batch.

Reads results/a_data_labels/a1_first_batch/{stations,events}.csv. For each
event, requests all chosen stations (channels --channels, every location code)
from origin - --before s to origin + --after s through the SCEDC FDSN
dataselect service (one GET request per event) and saves one MiniSEED per event under
data/waveforms/raw/<--name>/<event_id>.mseed. Also saves a StationXML with
responses under data/stations/raw/<--name>_response.xml. Existing files are kept.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # scripts/, for paths.py
import argparse
import json
from concurrent.futures import ThreadPoolExecutor

import pandas as pd
from obspy import UTCDateTime
from obspy.clients.fdsn import Client

from paths import DATA, RES_A, STATIONS_RAW


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--name", default="socal_r2")
    ap.add_argument("--channels", default="HH?,EH?,HN?")
    ap.add_argument("--before", type=float, default=120.0)
    ap.add_argument("--after", type=float, default=240.0)
    ap.add_argument("--workers", type=int, default=4)
    args = ap.parse_args()
    batch = RES_A / "a1_first_batch"
    st = pd.read_csv(batch / "stations.csv")
    ev = pd.read_csv(batch / "events.csv", parse_dates=["time"])
    wdir = DATA / "waveforms" / "raw" / args.name
    wdir.mkdir(parents=True, exist_ok=True)
    STATIONS_RAW.mkdir(parents=True, exist_ok=True)

    resp = STATIONS_RAW / f"{args.name}_response.xml"
    if not resp.exists():
        inv = Client("SCEDC").get_stations(network=",".join(sorted(st.network.unique())),
                                           station=",".join(st.code), channel=args.channels,
                                           level="response", starttime=UTCDateTime(2020, 1, 1))
        inv.write(str(resp), format="STATIONXML")

    def fetch(row):
        path = wdir / f"{row.event_id}.mseed"
        if path.exists() and path.stat().st_size > 0:
            return row.event_id, "kept", None
        t0 = UTCDateTime(row.time.to_pydatetime()) - args.before
        t1 = UTCDateTime(row.time.to_pydatetime()) + args.after
        # One GET request with comma lists; the SCEDC bulk (POST) request returned no data.
        query = dict(network=",".join(sorted(st.network.unique())), station=",".join(st.code),
                     location="*", channel=args.channels, starttime=t0, endtime=t1)
        for attempt in range(3):
            try:
                stream = Client("SCEDC").get_waveforms(**query)
                stream.write(str(path), format="MSEED")
                have = {f"{tr.stats.network}.{tr.stats.station}" for tr in stream}
                return row.event_id, len(stream), sorted(set(st.station) - have)
            except Exception as exc:  # noqa: BLE001 - retry, then report
                err = repr(exc)
        return row.event_id, "failed", err

    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        results = list(pool.map(fetch, ev.itertuples()))
    report = [dict(event_id=e, traces=n, missing_stations=m) for e, n, m in results]
    (batch / "download_report.json").write_text(json.dumps(report, indent=1, default=str))
    failed = [r for r in report if r["traces"] == "failed"]
    size = sum(f.stat().st_size for f in wdir.glob("*.mseed"))
    print(f"events {len(report)}, failed {len(failed)}, files {len(list(wdir.glob('*.mseed')))}, "
          f"{size / 1e6:.0f} MB; response file {resp.stat().st_size / 1e6:.1f} MB")


if __name__ == "__main__":
    main()
