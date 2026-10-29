"""Event correspondence (docs/framework/03_EVALUATION_METRICS.md §2)."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .tables import KM_PER_DEG, Population

PRIMARY_GATES = (2.0, 5.0)  # v2; v1 used 4 s / 15 km, larger than a compact swarm (Maple Creek)
SENSITIVITY_GATES = ((4.0, 15.0), (1.0, 3.0))
TIME_ONLY_GATE_S = 1.0
CHANCE_SHIFT_S = 60.0


@dataclass(frozen=True)
class Pairs:
    """One-to-one pairs: row indices into the candidate (a) and reference (b)."""

    a: np.ndarray
    b: np.ndarray
    distance_km: np.ndarray
    dt_s: np.ndarray

    def __len__(self) -> int:
        return len(self.a)


def epicentral_km(lat_a, lon_a, lat_b, lon_b):
    return np.hypot((lat_a - lat_b) * KM_PER_DEG, (lon_a - lon_b) * KM_PER_DEG * np.cos(np.radians(lat_a)))


def match(a: Population, b: Population, dt_max: float, d_max: float | None, *,
          shift_b_s: float = 0.0) -> Pairs:
    """Greedy one-to-one pairing, ranked by (distance, |dt|); time only when ``d_max`` is None.

    Rows of ``b`` must be sorted by time. Ties are broken by row order, so the
    result is deterministic.
    """
    ta = a.events.time.to_numpy()
    tb = b.events.time.to_numpy() + shift_b_s
    usable_a = np.isfinite(ta) & (a.located if d_max is not None else True)
    ia = np.flatnonzero(usable_a)
    lo = np.searchsorted(tb, ta[ia] - dt_max, side="left")
    hi = np.searchsorted(tb, ta[ia] + dt_max, side="right")
    counts = hi - lo
    total = int(counts.sum())
    empty = np.array([], dtype=int)
    if total == 0:
        return Pairs(empty, empty, np.array([]), np.array([]))
    cand_a = np.repeat(ia, counts)
    starts = np.repeat(np.cumsum(counts) - counts, counts)
    cand_b = np.arange(total) - starts + np.repeat(lo, counts)
    dt = np.abs(tb[cand_b] - ta[cand_a])
    keep = dt <= dt_max
    if d_max is not None:
        ea, eb = a.events, b.events
        keep &= b.located[cand_b]
        d = np.full(total, np.inf)
        d[keep] = epicentral_km(ea.latitude.to_numpy()[cand_a[keep]], ea.longitude.to_numpy()[cand_a[keep]],
                                eb.latitude.to_numpy()[cand_b[keep]], eb.longitude.to_numpy()[cand_b[keep]])
        keep &= d <= d_max
        cand_a, cand_b, dt, d = cand_a[keep], cand_b[keep], dt[keep], d[keep]
        order = np.lexsort((cand_b, cand_a, dt, d))
    else:
        cand_a, cand_b, dt = cand_a[keep], cand_b[keep], dt[keep]
        d = np.full(len(cand_a), np.nan)
        order = np.lexsort((cand_b, cand_a, dt))
    used_a = np.zeros(len(ta), dtype=bool)
    used_b = np.zeros(len(tb), dtype=bool)
    chosen = []
    for k in order:
        i, j = cand_a[k], cand_b[k]
        if not used_a[i] and not used_b[j]:
            used_a[i] = used_b[j] = True
            chosen.append(k)
    chosen = np.asarray(chosen, dtype=int)
    return Pairs(cand_a[chosen], cand_b[chosen], d[chosen], dt[chosen])


def gates_for(a: Population, b: Population) -> tuple[float, float | None]:
    """Primary gates of a pairing: time only if either side is, else the reference override,
    else the case's primary gates carried by the reference, else ``PRIMARY_GATES``."""
    if a.time_only or b.time_only:
        return TIME_ONLY_GATE_S, None
    if b.gates:
        return tuple(b.gates)
    return tuple(b.primary_gates) if b.primary_gates else PRIMARY_GATES


def correspond(a: Population, b: Population, gates: tuple[float, float | None] | None = None) -> dict:
    """Pairs under the given (default primary) gates, with the chance count.

    The same matcher run against ``b`` shifted by 60 s counts coincidences at
    the sequence's own event density (v2: for located and time-only pairing).
    """
    dt_max, d_max = gates if gates is not None else gates_for(a, b)
    pairs = match(a, b, dt_max, d_max)
    chance = len(match(a, b, dt_max, d_max, shift_b_s=CHANCE_SHIFT_S))
    return {"pairs": pairs, "chance": chance, "gates": [dt_max, d_max]}
