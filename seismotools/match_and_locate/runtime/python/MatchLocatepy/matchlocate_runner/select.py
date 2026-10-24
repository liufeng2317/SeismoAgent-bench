"""Template-selection helper (a case-level decision; not used by the interfaces).

Match&Locate searches only about +-1-1.5 km around each template on a local
network (see ``traveltime.linearisation_error_s``), so templates must sample
the active volume at about that spacing. ``select_templates`` filters
candidate events by quality and then picks a small set whose spheres of
``radius_km`` cover as many catalog events as possible (greedy set cover,
ties broken by the ranking key).
"""
from __future__ import annotations

import math
from typing import Callable, Dict, List, Optional, Sequence

import numpy as np

from .native import KM_PER_DEG


def _xyz(events: Sequence[Dict], lat0: float, lon0: float) -> np.ndarray:
    c = math.cos(math.radians(lat0))
    return np.array([[(e["longitude"] - lon0) * KM_PER_DEG * c, (e["latitude"] - lat0) * KM_PER_DEG,
                      e["depth_km"]] for e in events], dtype=float).reshape(-1, 3)


def select_templates(catalog: Sequence[Dict], candidates: Sequence[Dict], radius_km: float,
                     max_templates: Optional[int] = None,
                     rank: Callable[[Dict], float] = lambda e: e.get("magnitude") or 0.0) -> Dict:
    """Greedy spatial cover of ``catalog`` events by ``candidates``.

    Both are sequences of dicts with latitude, longitude, depth_km (same depth
    reference) and an ``event_id``; apply quality filters (magnitude, station
    count, location uncertainty, SNR) to ``candidates`` before calling.
    Returns the chosen candidates (in selection order) and the covered fraction.
    """
    if not catalog or not candidates:
        return {"templates": [], "covered_fraction": 0.0, "covered": 0, "catalog": len(catalog)}
    lat0 = float(np.mean([e["latitude"] for e in catalog]))
    lon0 = float(np.mean([e["longitude"] for e in catalog]))
    p, c = _xyz(catalog, lat0, lon0), _xyz(candidates, lat0, lon0)
    reach = np.linalg.norm(p[None, :, :] - c[:, None, :], axis=2) <= radius_km
    order = sorted(range(len(candidates)), key=lambda i: -rank(candidates[i]))
    covered = np.zeros(len(catalog), bool)
    chosen: List[int] = []
    while max_templates is None or len(chosen) < max_templates:
        best, best_gain = None, 0
        for i in order:
            if i in chosen:
                continue
            gain = int((reach[i] & ~covered).sum())
            if gain > best_gain:
                best, best_gain = i, gain
        if best is None:
            break
        chosen.append(best)
        covered |= reach[best]
    return {"templates": [candidates[i] for i in chosen], "covered_fraction": float(covered.mean()),
            "covered": int(covered.sum()), "catalog": len(catalog)}
