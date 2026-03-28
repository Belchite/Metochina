"""GPS coordinate parsing from EXIF data.

Converts EXIF GPS IFD entries (DMS with IFDRational values) to decimal degrees
and extracts auxiliary GPS fields (altitude, speed, direction, timestamp, datum).
"""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional, Tuple

from metochina.models.metadata import GPSData

logger = logging.getLogger(__name__)

# EXIF GPS IFD tag keys (numeric and string forms used by Pillow)
_TAG_LAT_REF = "GPSLatitudeRef"
_TAG_LAT = "GPSLatitude"
_TAG_LON_REF = "GPSLongitudeRef"
_TAG_LON = "GPSLongitude"
_TAG_ALT_REF = "GPSAltitudeRef"
_TAG_ALT = "GPSAltitude"
_TAG_SPEED_REF = "GPSSpeedRef"
_TAG_SPEED = "GPSSpeed"
_TAG_DIR_REF = "GPSImgDirectionRef"
_TAG_DIR = "GPSImgDirection"
_TAG_TIMESTAMP = "GPSTimeStamp"
_TAG_DATESTAMP = "GPSDateStamp"
_TAG_DATUM = "GPSMapDatum"


def _rational_to_float(value: Any) -> Optional[float]:
    """Convert an IFDRational or numeric value to float.

    Handles Pillow IFDRational objects, plain tuples (num, den), and scalars.
    Returns None if conversion fails or denominator is zero.
    """
    if value is None:
        return None
    try:
        # Pillow IFDRational has numerator/denominator attributes
        if hasattr(value, "numerator") and hasattr(value, "denominator"):
            if value.denominator == 0:
                return None
            return float(value.numerator) / float(value.denominator)
        # Tuple form (numerator, denominator)
        if isinstance(value, (tuple, list)) and len(value) == 2:
            num, den = value
            if den == 0:
                return None
            return float(num) / float(den)
        return float(value)
    except (TypeError, ValueError, ZeroDivisionError):
        return None


def _dms_to_decimal(dms: Any, ref: Optional[str] = None) -> Optional[float]:
    """Convert DMS (degrees, minutes, seconds) EXIF tuple to decimal degrees.

    Args:
        dms: A tuple/list of three IFDRational or numeric values representing
             (degrees, minutes, seconds).
        ref: Reference direction — "N", "S", "E", or "W".

    Returns:
        Decimal degrees as float, or None on failure.
    """
    if dms is None:
        return None
    try:
        if not (isinstance(dms, (tuple, list)) and len(dms) >= 3):
            return None

        degrees = _rational_to_float(dms[0])
        minutes = _rational_to_float(dms[1])
        seconds = _rational_to_float(dms[2])

        if degrees is None or minutes is None or seconds is None:
            return None

        decimal = degrees + minutes / 60.0 + seconds / 3600.0

        if ref and ref.upper() in ("S", "W"):
            decimal = -decimal

        return round(decimal, 8)
    except (TypeError, ValueError, IndexError) as exc:
        logger.debug("DMS conversion failed: %s", exc)
        return None


def _parse_gps_timestamp(time_val: Any, date_val: Optional[str] = None) -> Optional[str]:
    """Parse GPSTimeStamp and optional GPSDateStamp into an ISO-like string."""
    if time_val is None:
        return None
    try:
        if isinstance(time_val, (tuple, list)) and len(time_val) >= 3:
            h = _rational_to_float(time_val[0])
            m = _rational_to_float(time_val[1])
            s = _rational_to_float(time_val[2])
            if h is None or m is None or s is None:
                return None
            time_str = f"{int(h):02d}:{int(m):02d}:{int(s):02d}"
        else:
            time_str = str(time_val)

        if date_val:
            # GPSDateStamp is typically "YYYY:MM:DD"
            date_clean = str(date_val).replace(":", "-")
            return f"{date_clean}T{time_str}Z"
        return time_str
    except (TypeError, ValueError):
        return None


def _parse_altitude(alt: Any, alt_ref: Any) -> Tuple[Optional[float], Optional[str]]:
    """Parse altitude value and reference."""
    altitude = _rational_to_float(alt)
    ref_str: Optional[str] = None
    if alt_ref is not None:
        try:
            ref_val = int(alt_ref) if not isinstance(alt_ref, str) else alt_ref
            if ref_val == 0 or str(ref_val) == "0":
                ref_str = "Above sea level"
            elif ref_val == 1 or str(ref_val) == "1":
                ref_str = "Below sea level"
                if altitude is not None:
                    altitude = -abs(altitude)
            else:
                ref_str = str(ref_val)
        except (TypeError, ValueError):
            ref_str = str(alt_ref)
    return altitude, ref_str


def parse_gps_info(gps_dict: Dict[str, Any]) -> GPSData:
    """Parse a GPS IFD dictionary into a GPSData object.

    Args:
        gps_dict: Dictionary of GPS EXIF tags. Keys can be tag names (str)
                  or numeric tag IDs.

    Returns:
        Populated GPSData instance.
    """
    if not gps_dict:
        return GPSData()

    latitude = _dms_to_decimal(
        gps_dict.get(_TAG_LAT),
        gps_dict.get(_TAG_LAT_REF),
    )
    longitude = _dms_to_decimal(
        gps_dict.get(_TAG_LON),
        gps_dict.get(_TAG_LON_REF),
    )

    altitude, altitude_ref = _parse_altitude(
        gps_dict.get(_TAG_ALT),
        gps_dict.get(_TAG_ALT_REF),
    )

    speed = _rational_to_float(gps_dict.get(_TAG_SPEED))
    speed_ref = gps_dict.get(_TAG_SPEED_REF)
    if speed_ref is not None:
        speed_ref = str(speed_ref)

    direction = _rational_to_float(gps_dict.get(_TAG_DIR))
    direction_ref = gps_dict.get(_TAG_DIR_REF)
    if direction_ref is not None:
        direction_ref = str(direction_ref)

    timestamp = _parse_gps_timestamp(
        gps_dict.get(_TAG_TIMESTAMP),
        gps_dict.get(_TAG_DATESTAMP),
    )

    datum = gps_dict.get(_TAG_DATUM)
    if datum is not None:
        datum = str(datum)

    return GPSData(
        latitude=latitude,
        longitude=longitude,
        altitude=altitude,
        altitude_ref=altitude_ref,
        speed=speed,
        speed_ref=speed_ref,
        direction=direction,
        direction_ref=direction_ref,
        timestamp=timestamp,
        datum=datum,
    )
