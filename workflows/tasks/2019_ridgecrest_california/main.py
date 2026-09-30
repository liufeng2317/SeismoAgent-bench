"""Deterministic Ridgecrest baseline agent for end-to-end smoke evaluation.

This is an infrastructure baseline, not a seismological picker or locator.
It emits two fixed candidate events so the benchmark can exercise the complete
agent -> catalog validation -> reference matching -> scoring path.
"""

from __future__ import annotations

import json
import os
from pathlib import Path


def main() -> None:
    output = Path(os.environ["BENCH_OUTPUT"])
    output.mkdir(parents=True, exist_ok=True)
    catalog = {
        "schema_version": 1,
        "catalog_id": "ridgecrest-deterministic-baseline-v1",
        "description": (
            "Deterministic infrastructure baseline for the Ridgecrest smoke task; "
            "not a scientific event detector or locator."
        ),
        "events": [
            {
                "event_id": "baseline-m6.4",
                "origin_time": "2019-07-04T17:33:49.500Z",
                "latitude": 35.7060,
                "longitude": -117.5032,
                "depth_km": 10.8,
                "magnitude": 6.4,
                "magnitude_type": "Mw",
                "location_method": "deterministic-baseline",
            },
            {
                "event_id": "baseline-m7.1",
                "origin_time": "2019-07-06T03:19:52.540Z",
                "latitude": 35.7688,
                "longitude": -117.6000,
                "depth_km": 8.4,
                "magnitude": 7.1,
                "magnitude_type": "Mw",
                "location_method": "deterministic-baseline",
            },
        ],
    }
    (output / "catalog.json").write_text(
        json.dumps(catalog, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


if __name__ == "__main__":
    main()
