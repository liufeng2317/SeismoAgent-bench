"""Shared data models and coordinate helpers for NonLinLoc workflows."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np

try:
    import utm  # type: ignore
except ImportError:  # pragma: no cover - fallback for environments without utm
    from pyproj import CRS, Transformer

    class _UTMFallback:
        """Fallback UTM converter implemented with pyproj."""

        @staticmethod
        def _zone_number(lon: float) -> int:
            """Return the UTM zone number for a longitude.

            Args:
                lon (float): Longitude in degrees.

            Returns:
                int: UTM zone number.
            """
            return int((lon + 180.0) / 6.0) + 1

        @staticmethod
        def _zone_letter(lat: float) -> str:
            """Return the UTM latitude-band letter for a latitude.

            Args:
                lat (float): Latitude in degrees.

            Returns:
                str: UTM latitude-band letter.
            """
            if not -80.0 <= lat <= 84.0:
                raise ValueError(f"Latitude out of UTM range: {lat}")
            letters = "CDEFGHJKLMNPQRSTUVWXX"
            return letters[int((lat + 80.0) // 8.0)]

        @classmethod
        def _transformer(cls, zone_number: int, zone_letter: str, inverse: bool = False) -> Transformer:
            """Create a pyproj transformer for one UTM zone.

            Args:
                zone_number (int): UTM zone number.
                zone_letter (str): UTM latitude-band letter.
                inverse (bool): Whether to transform from UTM to geographic coordinates.

            Returns:
                Transformer: Configured pyproj transformer.
            """
            epsg = 32600 + zone_number if zone_letter >= "N" else 32700 + zone_number
            crs_utm = CRS.from_epsg(epsg)
            crs_geo = CRS.from_epsg(4326)
            if inverse:
                return Transformer.from_crs(crs_utm, crs_geo, always_xy=True)
            return Transformer.from_crs(crs_geo, crs_utm, always_xy=True)

        @classmethod
        def from_latlon(cls, lat: Any, lon: Any):
            """Convert latitude/longitude coordinates to UTM coordinates.

            Args:
                lat (Any): Latitude scalar or array-like values.
                lon (Any): Longitude scalar or array-like values.

            Returns:
                tuple: Easting, northing, UTM zone number, and zone letter.
            """
            lat_arr = np.asarray(lat, dtype=float)
            lon_arr = np.asarray(lon, dtype=float)
            zone_number = cls._zone_number(float(np.ravel(lon_arr)[0]))
            zone_letter = cls._zone_letter(float(np.ravel(lat_arr)[0]))
            transformer = cls._transformer(zone_number, zone_letter, inverse=False)
            east, north = transformer.transform(lon_arr, lat_arr)
            return east, north, zone_number, zone_letter

        @classmethod
        def to_latlon(cls, east: float, north: float, zone_number: int, zone_letter: str):
            """Convert UTM coordinates to latitude/longitude.

            Args:
                east (float): UTM easting in meters.
                north (float): UTM northing in meters.
                zone_number (int): UTM zone number.
                zone_letter (str): UTM latitude-band letter.

            Returns:
                tuple: Latitude and longitude in degrees.
            """
            transformer = cls._transformer(zone_number, zone_letter, inverse=True)
            lon, lat = transformer.transform(float(east), float(north))
            return lat, lon

    utm = _UTMFallback()


@dataclass
class Station:
    """Seismic station; ``station_id`` is the GTSRCE label and NLLOC_OBS station.
    
    Attributes:
        station_id (str): station id.
        lon (float): lon.
        lat (float): lat.
        elev_m (float): elev m.
    """

    station_id: str
    lon: float
    lat: float
    elev_m: float


@dataclass
class PhasePick:
    """One NLLOC_OBS arrival, with seconds after the event reference ``hhmm``.
    
    Attributes:
        station_id (str): station id.
        phase (str): phase.
        time_sec (float): time sec.
        first_motion (str): first motion.
    """

    station_id: str
    phase: str
    time_sec: float
    first_motion: str = "?"
