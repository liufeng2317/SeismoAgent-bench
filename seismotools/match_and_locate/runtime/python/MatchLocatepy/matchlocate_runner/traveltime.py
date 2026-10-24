"""First-arrival travel times and slownesses in a flat layered 1-D model.

MatchLocate2 shifts each correlogram by a linearised moveout
``dt = dT/dDelta * dDelta + dT/dz * dz`` about the template. This module
supplies the template travel time (SAC t-mark) and both derivatives for the
first-arriving ray: the direct ray between source and receiver, or a head wave
along the top of any faster layer below both of them.

Depths are km below the model datum (the model's ``top_of_layer_km`` origin).
A receiver above the datum has a negative depth; the top layer's velocity is
extended upward for it. Derivatives are analytic for the selected ray:
``dT/dDelta = p`` and ``dT/dz_source = +eta`` when the source leg is the
deeper end of an upgoing direct ray, ``-eta`` for a downgoing leg, where
``eta = sqrt(1/v^2 - p^2)`` in the source layer.
"""
from __future__ import annotations

import dataclasses
import math
from typing import List, Optional, Sequence, Tuple

from .native import KM_PER_DEG


@dataclasses.dataclass(frozen=True)
class LayeredModel:
    tops_km: Tuple[float, ...]
    vp_km_s: Tuple[float, ...]
    vs_km_s: Tuple[float, ...]

    def __post_init__(self) -> None:
        n = len(self.tops_km)
        if n == 0 or len(self.vp_km_s) != n or len(self.vs_km_s) != n:
            raise ValueError("tops/vp/vs must be non-empty and of equal length")
        if any(b <= a for a, b in zip(self.tops_km, self.tops_km[1:])):
            raise ValueError("layer tops must increase strictly")
        if min(self.vp_km_s) <= 0 or min(self.vs_km_s) <= 0:
            raise ValueError("velocities must be positive")

    @classmethod
    def from_rows(cls, rows: Sequence[dict]) -> "LayeredModel":
        """Rows shaped like ``data/<case>/data/models/velocity_models.json``:
        ``{"top_of_layer_km", "vp_km_s", "vs_km_s"}``."""
        rows = sorted(rows, key=lambda r: float(r["top_of_layer_km"]))
        return cls(tuple(float(r["top_of_layer_km"]) for r in rows),
                   tuple(float(r["vp_km_s"]) for r in rows),
                   tuple(float(r["vs_km_s"]) for r in rows))

    def velocities(self, phase: str) -> Tuple[float, ...]:
        key = phase.upper()[:1]
        if key == "P":
            return self.vp_km_s
        if key == "S":
            return self.vs_km_s
        raise ValueError(f"phase must start with P or S: {phase!r}")

    def layer_index(self, depth_km: float) -> int:
        idx = 0
        for k, top in enumerate(self.tops_km):
            if depth_km >= top:
                idx = k
        return idx


@dataclasses.dataclass(frozen=True)
class Ray:
    travel_time_s: float
    p_s_per_km: float
    dtdz_s_per_km: float
    kind: str                      # "direct" or "head:<layer index>"

    @property
    def slowness_h_s_per_deg(self) -> float:
        return self.p_s_per_km * KM_PER_DEG


def _segments(model: LayeredModel, v: Sequence[float], z_top: float, z_bottom: float) -> List[Tuple[float, float]]:
    """(thickness, velocity) pieces of the column between two depths."""
    pieces = []
    bounds = list(model.tops_km[1:]) + [math.inf]
    for k, top in enumerate(model.tops_km):
        lo = -math.inf if k == 0 else top
        hi = bounds[k]
        a, b = max(lo, z_top), min(hi, z_bottom)
        if b > a:
            pieces.append((b - a, v[k]))
    return pieces


def _eta(p: float, v: float) -> float:
    return math.sqrt(max(1.0 / (v * v) - p * p, 0.0))


def _direct(model: LayeredModel, v: Sequence[float], distance: float, zs: float, zr: float) -> Ray:
    z_top, z_bottom = min(zs, zr), max(zs, zr)
    segs = _segments(model, v, z_top, z_bottom)
    v_src = v[model.layer_index(zs)]
    sign = 1.0 if zs >= zr else -1.0
    if not segs:                                   # source and receiver at one depth
        p = 1.0 / v_src
        return Ray(distance * p, p, 0.0, "direct")
    if distance == 0.0:
        return Ray(sum(h / vv for h, vv in segs), 0.0, sign / v_src, "direct")
    u_max = 1.0 / max(vv for _, vv in segs)

    def offset(p: float) -> float:
        return sum(h * p * vv / math.sqrt(1.0 - (p * vv) ** 2) for h, vv in segs)

    lo, hi = 0.0, u_max * (1.0 - 1e-15)
    for _ in range(200):                           # X(p) is monotonic in p
        mid = 0.5 * (lo + hi)
        if offset(mid) < distance:
            lo = mid
        else:
            hi = mid
    p = 0.5 * (lo + hi)
    t = sum(h / (vv * math.sqrt(1.0 - (p * vv) ** 2)) for h, vv in segs)
    return Ray(t, p, sign * _eta(p, v_src), "direct")


def _heads(model: LayeredModel, v: Sequence[float], distance: float, zs: float, zr: float) -> List[Ray]:
    rays = []
    v_src = v[model.layer_index(zs)]
    for k in range(1, len(model.tops_km)):
        z_ref = model.tops_km[k]
        if z_ref <= max(zs, zr):
            continue
        legs = _segments(model, v, zs, z_ref) + _segments(model, v, zr, z_ref)
        if max(vv for _, vv in legs) >= v[k]:
            continue
        p = 1.0 / v[k]
        crit = sum(h * p * vv / math.sqrt(1.0 - (p * vv) ** 2) for h, vv in legs)
        if distance < crit:
            continue
        t = distance * p + sum(h * _eta(p, vv) for h, vv in legs)
        rays.append(Ray(t, p, -_eta(p, v_src), f"head:{k}"))
    return rays


def first_arrival(model: LayeredModel, phase: str, distance_km: float,
                  source_depth_km: float, receiver_depth_km: float = 0.0) -> Ray:
    """Fastest of the direct ray and all valid head waves."""
    if distance_km < 0:
        raise ValueError("distance must be non-negative")
    v = model.velocities(phase)
    rays = [_direct(model, v, distance_km, source_depth_km, receiver_depth_km)]
    rays += _heads(model, v, distance_km, source_depth_km, receiver_depth_km)
    return min(rays, key=lambda r: r.travel_time_s)


def epicentral_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Great-circle distance in km on the sphere MatchLocate2 uses."""
    a1, b1, a2, b2 = map(math.radians, (lat1, lon1, lat2, lon2))
    c = (math.sin(a1) * math.sin(a2) + math.cos(a1) * math.cos(a2) * math.cos(b2 - b1))
    return math.degrees(math.acos(max(-1.0, min(1.0, c)))) * KM_PER_DEG


def linearisation_error_s(model: LayeredModel, phase: str, station: Tuple[float, float, float],
                          template: Tuple[float, float, float], offset: Tuple[float, float, float]) -> float:
    """|exact - linearised| relative travel time for a source offset (dlat_km, dlon_km, dz_km).

    ``station`` is (lat, lon, receiver depth km); ``template`` is (lat, lon,
    depth km). Quantifies the native linear moveout's error for a grid node.
    """
    slat, slon, sz = station
    tlat, tlon, tz = template
    dn, de, dz = offset
    nlat = tlat + dn / KM_PER_DEG
    nlon = tlon + de / (KM_PER_DEG * math.cos(math.radians(tlat)))
    ref = first_arrival(model, phase, epicentral_km(slat, slon, tlat, tlon), tz, sz)
    exact = first_arrival(model, phase, epicentral_km(slat, slon, nlat, nlon), tz + dz, sz)
    d_delta = epicentral_km(slat, slon, nlat, nlon) - epicentral_km(slat, slon, tlat, tlon)
    linear = ref.p_s_per_km * d_delta + ref.dtdz_s_per_km * dz
    return abs((exact.travel_time_s - ref.travel_time_s) - linear)
