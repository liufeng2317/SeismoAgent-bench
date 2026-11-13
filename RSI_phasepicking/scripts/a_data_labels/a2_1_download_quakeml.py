"""a2: download QuakeML (with arrivals) for the M>=2.5 events of the candidate regions.

Reads results/a_data_labels/a1_candidate_regions/candidate_regions.csv and the SCEDC event lists; for
every local earthquake of M>=--min-mag within --radius km of a candidate centre
(outside the excluded Ridgecrest/Coso box), saves the SCEDC QuakeML as returned
under data/catalogs/raw/scedc_quakeml/<event_id>.xml. Complete existing files are kept.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # scripts/, for paths.py
import argparse
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor

import numpy as np
import pandas as pd

from a1_2_candidate_regions import EXCLUDE, dist_km, in_box, load_events
from paths import CATALOGS_RAW, RES_A

SCEDC_EVENT = "https://service.scedc.caltech.edu/fdsnws/event/1/query"
QUAKEML = CATALOGS_RAW / "scedc_quakeml"


def complete(path):
    return path.exists() and path.read_bytes().rstrip().endswith(b"quakeml>")


def fetch(eid):
    path = QUAKEML / f"{eid}.xml"
    for attempt in range(3):
        try:
            body = urllib.request.urlopen(f"{SCEDC_EVENT}?eventid={eid}&includearrivals=true", timeout=180).read()
            path.write_bytes(body)
            return True
        except Exception:  # noqa: BLE001 - retry, then count as failed
            time.sleep(3 * (attempt + 1))
    return False


def region_events(min_mag, radius):
    ev = load_events()
    outside = np.ones(len(ev), bool)
    for b in EXCLUDE.values():
        outside &= ~in_box(ev.lat.values, ev.lon.values, b)
    ev = ev[(ev.mag >= min_mag) & outside]
    cand = pd.read_csv(RES_A / "a1_candidate_regions" / "candidate_regions.csv")
    parts = []
    for _, r in cand.iterrows():
        sub = ev[dist_km(r.lat, r.lon, ev.lat.values, ev.lon.values) <= radius].copy()
        sub["region"] = r.candidate
        parts.append(sub)
    return pd.concat(parts, ignore_index=True)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--min-mag", type=float, default=2.5)
    ap.add_argument("--radius", type=float, default=50.0, help="km")
    ap.add_argument("--workers", type=int, default=4, help="parallel requests")
    args = ap.parse_args()
    QUAKEML.mkdir(parents=True, exist_ok=True)
    ev = region_events(args.min_mag, args.radius)
    out = RES_A / "a2_labels"
    out.mkdir(parents=True, exist_ok=True)
    ev.to_csv(out / "region_events.csv", index=False)
    todo = [e for e in ev.event_id.unique() if not complete(QUAKEML / f"{e}.xml")]
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        results = list(pool.map(fetch, todo))
    done, failed = results.count(True), results.count(False)
    print(f"events {ev.event_id.nunique()} (per region: {ev.region.value_counts().to_dict()}); fetched {done}; failed {failed}")


if __name__ == "__main__":
    main()
