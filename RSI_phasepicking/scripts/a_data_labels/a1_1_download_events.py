"""a1 round 1: download event lists (all magnitudes) and station lists.

SCEDC: southern California, 2020-01 to today, plus the T1 window 2019-07-04..07.
NCEDC: same period (the service also returns southern California events; the
northern subset is selected later). Station lists: SCEDC networks CI and AZ, stations operating since 2020.
Raw responses are stored under data/ as returned; existing files are kept.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # scripts/, for paths.py
import argparse
import datetime as dt
import time
import urllib.request

from paths import NCEDC_EVENTS, SCEDC_EVENTS, STATIONS_RAW

SCEDC_EVENT = "https://service.scedc.caltech.edu/fdsnws/event/1/query"
NCEDC_EVENT = "https://service.ncedc.org/fdsnws/event/1/query"
SCEDC_STATION = "https://service.scedc.caltech.edu/fdsnws/station/1/query"


def fetch(url, path, retries=3):
    if path.exists() and path.stat().st_size > 0:
        return "kept"
    for attempt in range(retries):
        try:
            body = urllib.request.urlopen(url, timeout=300).read()
            path.write_bytes(body)
            return "fetched"
        except Exception as exc:  # noqa: BLE001 - report and retry
            if getattr(exc, "code", None) == 204:  # no events in the window
                path.write_bytes(b"")
                return "empty"
            time.sleep(5 * (attempt + 1))
    raise RuntimeError(f"failed: {url}")


def months(start, end):
    d = start
    while d < end:
        nxt = dt.date(d.year + (d.month == 12), d.month % 12 + 1, 1)
        yield d, min(nxt, end)
        d = nxt


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--start", default="2020-01-01")
    ap.add_argument("--end", default=dt.date.today().isoformat())
    args = ap.parse_args()
    start, end = dt.date.fromisoformat(args.start), dt.date.fromisoformat(args.end)

    for d in (SCEDC_EVENTS, NCEDC_EVENTS, STATIONS_RAW):
        d.mkdir(parents=True, exist_ok=True)

    status = []
    windows = list(months(start, end)) + [(dt.date(2019, 7, 4), dt.date(2019, 7, 7))]
    for a, b in windows:
        tag = f"{a:%Y-%m}" if a.day == 1 else f"{a}_{b}"
        url = f"{SCEDC_EVENT}?starttime={a}&endtime={b}&format=text"
        status.append(fetch(url, SCEDC_EVENTS / f"{tag}.txt"))
    for a, b in months(start, end):
        url = f"{NCEDC_EVENT}?starttime={a}T00:00:00&endtime={b}T00:00:00&format=text"
        status.append(fetch(url, NCEDC_EVENTS / f"{a:%Y-%m}.txt"))
    for net in ("CI", "AZ"):
        url = f"{SCEDC_STATION}?network={net}&level=station&format=text&starttime=2020-01-01T00:00:00.000000"
        status.append(fetch(url, STATIONS_RAW / f"scedc_{net}_stations.txt"))
    print({s: status.count(s) for s in set(status)})


if __name__ == "__main__":
    main()
