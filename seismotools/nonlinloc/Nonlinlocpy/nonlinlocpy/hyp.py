"""Parsers for NonLinLoc ``.hyp`` output files."""

from __future__ import annotations

import os
import pickle
import re
from typing import Any, Dict, List, Optional

from .models import utm

try:
    from pyproj import CRS, Transformer
except ImportError:  # pragma: no cover - pyproj is an optional fallback here
    CRS = None  # type: ignore[assignment]
    Transformer = None  # type: ignore[assignment]

_GEOG_RE = re.compile(
    r"GEOGRAPHIC\s+OT\s+(\d{4})\s+(\d+)\s+(\d+)\s+\s*(\d+)\s+(\d+)\s+([\d.]+)\s+"
    r"Lat\s+([\d.-]+)\s+Long\s+([\d.-]+)\s+Depth\s+([\d.]+)",
    re.MULTILINE,
)
_QUALITY_RE = re.compile(
    r"QUALITY\s+.*?RMS\s+([-\d.eE+]+)\s+Nphs\s+([-\d.eE+]+)\s+Gap\s+([-\d.eE+]+)\s+Dist\s+([-\d.eE+]+)",
    re.MULTILINE,
)
_QML_ORIGIN_QUALITY_RE = re.compile(
    r"QML_OriginQuality\s+assocPhCt\s+([-\d.eE+]+)\s+usedPhCt\s+([-\d.eE+]+)\s+assocStaCt\s+([-\d.eE+]+)\s+"
    r"usedStaCt\s+([-\d.eE+]+)\s+depthPhCt\s+([-\d.eE+]+)\s+stdErr\s+([-\d.eE+]+)\s+azGap\s+([-\d.eE+]+)\s+"
    r"secAzGap\s+([-\d.eE+]+)\s+gtLevel\s+(\S+)\s+minDist\s+([-\d.eE+]+)\s+maxDist\s+([-\d.eE+]+)\s+medDist\s+([-\d.eE+]+)",
    re.MULTILINE,
)
_QML_ORIGIN_UNCERTAINTY_RE = re.compile(
    r"QML_OriginUncertainty\s+horUnc\s+([-\d.eE+]+)\s+minHorUnc\s+([-\d.eE+]+)\s+maxHorUnc\s+([-\d.eE+]+)\s+azMaxHorUnc\s+([-\d.eE+]+)",
    re.MULTILINE,
)
_QML_CONFIDENCE_ELLIPSOID_RE = re.compile(
    r"QML_ConfidenceEllipsoid\s+semiMajorAxisLength\s+([-\d.eE+]+)\s+semiMinorAxisLength\s+([-\d.eE+]+)\s+"
    r"semiIntermediateAxisLength\s+([-\d.eE+]+)\s+majorAxisPlunge\s+([-\d.eE+]+)\s+majorAxisAzimuth\s+([-\d.eE+]+)\s+majorAxisRotation\s+([-\d.eE+]+)",
    re.MULTILINE,
)
_STATISTICS_RE = re.compile(
    r"STATISTICS\s+ExpectX\s+([-\d.eE+]+)\s+Y\s+([-\d.eE+]+)\s+Z\s+([-\d.eE+]+)\s+"
    r"CovXX\s+([-\d.eE+]+)\s+XY\s+([-\d.eE+]+)\s+XZ\s+([-\d.eE+]+)\s+YY\s+([-\d.eE+]+)\s+YZ\s+([-\d.eE+]+)\s+ZZ\s+([-\d.eE+]+)",
    re.MULTILINE,
)


def parse_hyp_geographic(text: str) -> Optional[Dict[str, Any]]:
    """Extract origin time and geographic coordinates from the ``GEOGRAPHIC`` line.
    
    Args:
        text (str): text.
    
    Returns:
        Optional[Dict[str, Any]]: Result returned by the function.
    """

    m = _GEOG_RE.search(text)
    if not m:
        return None
    y, mo, d, hh, mm, sec, lat, lon, dep = m.groups()
    return {
        "origin_yyyymmdd": f"{y}{int(mo):02d}{int(d):02d}",
        "origin_hhmmss": f"{int(hh):02d}{int(mm):02d}{float(sec):06.3f}",
        "lat": float(lat),
        "lon": float(lon),
        "depth_km": float(dep),
    }


def _float_or_none(text: str) -> Optional[float]:
    """Convert a text token to float and return ``None`` for invalid values.
    
    Args:
        text (str): text.
    
    Returns:
        Optional[float]: Result returned by the function.
    """

    try:
        return float(text)
    except (TypeError, ValueError):
        return None


def parse_hyp_quality(text: str) -> Dict[str, Any]:
    """Extract common quality, uncertainty, and covariance fields from one ``.hyp`` body.
    
    Args:
        text (str): text.
    
    Returns:
        Dict[str, Any]: Result returned by the function.
    """

    row: Dict[str, Any] = {}

    m = _QUALITY_RE.search(text)
    if m:
        row["rms_sec"] = _float_or_none(m.group(1))
        row["nphs"] = int(float(m.group(2)))
        row["gap_deg"] = _float_or_none(m.group(3))
        row["min_dist_km"] = _float_or_none(m.group(4))

    m = _QML_ORIGIN_QUALITY_RE.search(text)
    if m:
        row["assoc_phase_count"] = int(float(m.group(1)))
        row["used_phase_count"] = int(float(m.group(2)))
        row["assoc_station_count"] = int(float(m.group(3)))
        row["used_station_count"] = int(float(m.group(4)))
        row["depth_phase_count"] = int(float(m.group(5)))
        row["std_err_sec"] = _float_or_none(m.group(6))
        row["az_gap_deg"] = _float_or_none(m.group(7))
        row["secondary_az_gap_deg"] = _float_or_none(m.group(8))
        row["ground_truth_level"] = m.group(9)
        row["max_dist_km"] = _float_or_none(m.group(11))
        row["median_dist_km"] = _float_or_none(m.group(12))

    m = _QML_ORIGIN_UNCERTAINTY_RE.search(text)
    if m:
        row["horizontal_uncertainty_km"] = _float_or_none(m.group(1))
        row["min_horizontal_uncertainty_km"] = _float_or_none(m.group(2))
        row["max_horizontal_uncertainty_km"] = _float_or_none(m.group(3))
        row["azimuth_max_horizontal_uncertainty_deg"] = _float_or_none(m.group(4))

    m = _QML_CONFIDENCE_ELLIPSOID_RE.search(text)
    if m:
        row["semi_major_axis_km"] = _float_or_none(m.group(1))
        row["semi_minor_axis_km"] = _float_or_none(m.group(2))
        row["semi_intermediate_axis_km"] = _float_or_none(m.group(3))
        row["major_axis_plunge_deg"] = _float_or_none(m.group(4))
        row["major_axis_azimuth_deg"] = _float_or_none(m.group(5))
        row["major_axis_rotation_deg"] = _float_or_none(m.group(6))

    m = _STATISTICS_RE.search(text)
    if m:
        row["expect_x_km"] = _float_or_none(m.group(1))
        row["expect_y_km"] = _float_or_none(m.group(2))
        row["expect_z_km"] = _float_or_none(m.group(3))
        row["cov_xx_km2"] = _float_or_none(m.group(4))
        row["cov_xy_km2"] = _float_or_none(m.group(5))
        row["cov_xz_km2"] = _float_or_none(m.group(6))
        row["cov_yy_km2"] = _float_or_none(m.group(7))
        row["cov_yz_km2"] = _float_or_none(m.group(8))
        row["cov_zz_km2"] = _float_or_none(m.group(9))

    return row


def _parse_hyp_xy_utm(
    hyp_text_line: str,
    x0: float,
    y0: float,
    zone_number: int,
    zone_letter: str,
) -> Optional[Dict[str, Any]]:
    """Fallback: HYPOCENTER ``x .. y .. z`` line plus UTM pickle.
    
    Args:
        hyp_text_line (str): hyp text line.
        x0 (float): x0.
        y0 (float): y0.
        zone_number (int): zone number.
        zone_letter (str): zone letter.
    
    Returns:
        Optional[Dict[str, Any]]: Result returned by the function.
    """

    mx = re.search(r"\bx\s+([-\d.]+)\s+y\s+([-\d.]+)\s+z\s+([\d.]+)", hyp_text_line)
    if not mx:
        return None
    x_km, y_km, z_km = map(float, mx.groups())
    xm = x_km * 1000.0 + x0
    ym = y_km * 1000.0 + y0
    try:
        lat, lon = utm.to_latlon(xm, ym, int(zone_number), zone_letter)
    except Exception:
        if CRS is None or Transformer is None:
            raise
        epsg = 32600 + int(zone_number) if zone_letter.upper() >= "N" else 32700 + int(zone_number)
        transformer = Transformer.from_crs(CRS.from_epsg(epsg), CRS.from_epsg(4326), always_xy=True)
        lon, lat = transformer.transform(xm, ym)
    return {"lat": lat, "lon": lon, "depth_km": z_km}


def parse_hyp_solutions(
    control_file_path: str,
    loc_subdir: str = "loc",
) -> List[Dict[str, Any]]:
    """Read ``loc/*.hyp`` event files and return compact solution dictionaries.
    
    Args:
        control_file_path (str): control file path.
        loc_subdir (str): loc subdir.
    
    Returns:
        List[Dict[str, Any]]: Result returned by the function.
    """

    loc = os.path.join(control_file_path, loc_subdir)
    if not os.path.isdir(loc):
        return []

    zone_path = os.path.join(control_file_path, "Zone_info.pickle")
    zone = None
    if os.path.isfile(zone_path):
        with open(zone_path, "rb") as fp:
            zone = (
                pickle.load(fp),
                pickle.load(fp),
                pickle.load(fp),
                pickle.load(fp),
            )

    out: List[Dict[str, Any]] = []
    for name in sorted(os.listdir(loc)):
        if "sum" in name or name in ("last.hyp", "last.hypo_inv"):
            continue
        if ".hyp" not in name:
            continue
        path = os.path.join(loc, name)
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            body = f.read()

        row: Dict[str, Any] = {"hyp_file": name}
        geo = parse_hyp_geographic(body)
        transform_none = "TRANSFORM  NONE" in body
        xy = None
        if zone is not None:
            hyp_line = ""
            for ln in body.splitlines():
                if ln.startswith("HYPOCENTER"):
                    hyp_line = ln
                    break
            if hyp_line:
                zn, zl, x0, y0 = zone
                xy = _parse_hyp_xy_utm(hyp_line, float(x0), float(y0), int(zn), zl)

        if geo:
            row.update(geo)
            row["raw_geographic_lat"] = geo["lat"]
            row["raw_geographic_lon"] = geo["lon"]
            row["raw_geographic_depth_km"] = geo["depth_km"]

        row.update(parse_hyp_quality(body))

        if xy is not None and transform_none:
            row.update(xy)
            row["coord_source"] = "hypocenter_xy_utm"
        elif xy is not None and geo is None:
            row.update(xy)
            row["coord_source"] = "hypocenter_xy_utm"
        elif geo is not None:
            row["coord_source"] = "geographic"
        out.append(row)
    return out
