"""Dependency-free SAC binary header reader.

MatchLocate2 reads SAC files through Lupei Zhu's ``sacio.c`` in the host byte
order and takes every timing value from the header. This reader exposes the
fields the native program uses so that datasets can be validated without
importing ObsPy.
"""
from __future__ import annotations

import dataclasses
import datetime as _dt
import struct
from pathlib import Path
from typing import Optional

HEADER_BYTES = 632
UNDEFINED = -12345.0

# Float-word indices in the 70-float header block.
_F = {"delta": 0, "b": 5, "e": 6, "o": 7, "a": 8, "stla": 31, "stlo": 32, "stel": 33,
      "evla": 35, "evlo": 36, "evdp": 38, "mag": 39, "user0": 40}
# Integer-word indices in the 40-int header block.
_I = {"nzyear": 0, "nzjday": 1, "nzhour": 2, "nzmin": 3, "nzsec": 4, "nzmsec": 5,
      "nvhdr": 6, "npts": 9, "iztype": 17}


def _undef(value: float) -> Optional[float]:
    return None if abs(value - UNDEFINED) < 1e-3 else value


@dataclasses.dataclass(frozen=True)
class SacHeader:
    path: str
    byte_order: str          # "<" or ">"
    delta: float
    npts: int
    b: float
    e: float
    o: Optional[float]
    t: tuple                 # t0..t9, None when undefined
    stla: Optional[float]
    stlo: Optional[float]
    stel: Optional[float]
    evla: Optional[float]
    evlo: Optional[float]
    evdp: Optional[float]
    mag: Optional[float]
    user0: Optional[float]
    reference: Optional[_dt.datetime]   # nz* reference time (UTC), None if undefined
    kstnm: str
    kcmpnm: str
    knetwk: str

    def mark(self, index: int) -> Optional[float]:
        """Time mark used by MatchLocate2's integer phase marker (1 -> t1)."""
        return self.t[index]


def read_sac_header(path) -> SacHeader:
    raw = Path(path).read_bytes()[:HEADER_BYTES]
    if len(raw) < HEADER_BYTES:
        raise ValueError(f"{path}: shorter than a SAC header")
    for order in ("<", ">"):
        ints = struct.unpack(order + "40i", raw[280:440])
        if ints[_I["nvhdr"]] in (6, 7):
            break
    else:
        raise ValueError(f"{path}: not a SAC file (nvhdr not 6/7 in either byte order)")
    floats = struct.unpack(order + "70f", raw[:280])
    chars = raw[440:632]

    def text(start: int, length: int) -> str:
        value = chars[start - 440:start - 440 + length].decode("ascii", "replace").strip()
        return "" if value == "-12345" else value

    reference = None
    nz = [ints[_I[k]] for k in ("nzyear", "nzjday", "nzhour", "nzmin", "nzsec", "nzmsec")]
    if all(v != -12345 for v in nz):
        reference = (_dt.datetime(nz[0], 1, 1, tzinfo=_dt.timezone.utc)
                     + _dt.timedelta(days=nz[1] - 1, hours=nz[2], minutes=nz[3],
                                     seconds=nz[4], milliseconds=nz[5]))
    return SacHeader(
        path=str(path), byte_order=order,
        delta=floats[_F["delta"]], npts=ints[_I["npts"]],
        b=floats[_F["b"]], e=floats[_F["e"]], o=_undef(floats[_F["o"]]),
        t=tuple(_undef(floats[10 + k]) for k in range(10)),
        stla=_undef(floats[_F["stla"]]), stlo=_undef(floats[_F["stlo"]]),
        stel=_undef(floats[_F["stel"]]), evla=_undef(floats[_F["evla"]]),
        evlo=_undef(floats[_F["evlo"]]), evdp=_undef(floats[_F["evdp"]]),
        mag=_undef(floats[_F["mag"]]), user0=_undef(floats[_F["user0"]]),
        reference=reference, kstnm=text(440, 8), kcmpnm=text(600, 8), knetwk=text(608, 8),
    )
