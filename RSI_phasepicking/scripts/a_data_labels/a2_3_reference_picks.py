"""a2: reference-pick table of the first batch.

For every event of results/a_data_labels/a1_first_batch/events.csv, reads the
SCEDC QuakeML and writes one row per pick at the chosen stations: time, phase,
evaluationMode, onset, polarity, uncertainty and weight code, channel and
location, epicentral distance, the catalog's residual and time weight, plus
the preferred origin. Manual picks are the reference; automatic picks are kept
and marked so that both versions of every metric can be reported.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # scripts/, for paths.py
import argparse

import pandas as pd
from obspy import read_events

from a2_2_label_stats import weight_code
from paths import CATALOGS_RAW, RES_A

QUAKEML = CATALOGS_RAW / "scedc_quakeml"


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", default=str(RES_A / "a2_labels" / "reference_picks_first_batch.csv"))
    args = ap.parse_args()
    batch = RES_A / "a1_first_batch"
    stations = set(pd.read_csv(batch / "stations.csv").station)
    events = pd.read_csv(batch / "events.csv")

    rows = []
    for eid in events.event_id:
        ev = read_events(str(QUAKEML / f"{eid}.xml"))[0]
        org = ev.preferred_origin() or ev.origins[0]
        mag = ev.preferred_magnitude() or (ev.magnitudes[0] if ev.magnitudes else None)
        picks = {p.resource_id.id: p for p in ev.picks}
        for arr in org.arrivals:
            p = picks.get(arr.pick_id.id)
            if p is None:
                continue
            w = p.waveform_id
            sta = f"{w.network_code}.{w.station_code}"
            if sta not in stations:
                continue
            unc = p.time_errors.uncertainty if p.time_errors else None
            rows.append(dict(
                event_id=eid, origin_time=str(org.time), origin_lat=org.latitude, origin_lon=org.longitude,
                origin_depth_km=org.depth / 1000 if org.depth is not None else None,
                magnitude=mag.mag if mag else None, magnitude_type=mag.magnitude_type if mag else None,
                station=sta, location=w.location_code or "", channel=w.channel_code or "",
                phase=(arr.phase or p.phase_hint or "")[:1].upper(), time=str(p.time),
                mode=p.evaluation_mode or "", onset=p.onset or "", polarity=p.polarity or "",
                uncertainty_s=unc, weight_code=weight_code(unc if unc is not None else float("nan")),
                distance_km=arr.distance * 111.19 if arr.distance is not None else None,
                residual_s=arr.time_residual, time_weight=arr.time_weight,
            ))
    df = pd.DataFrame(rows).sort_values(["event_id", "phase", "distance_km"])
    df.to_csv(args.out, index=False)
    man = df[df["mode"] == "manual"]
    print(f"events {df.event_id.nunique()}, picks {len(df)}, manual {len(man)} "
          f"(P {int((man.phase == 'P').sum())}, S {int((man.phase == 'S').sum())})")


if __name__ == "__main__":
    main()
