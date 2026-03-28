"""Main metadata extraction engine.

Opens images with Pillow, reads all available EXIF data, parses GPS,
identifies camera/software information, calculates file hashes, and
assembles a complete ImageMetadata object.

Optimized for batch processing with concurrent hash computation and
efficient memory usage through chunked file reads.
"""

from __future__ import annotations

import logging
import mimetypes
import os
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

from PIL import Image
from PIL.ExifTags import GPSTAGS, TAGS

from metochina.core.gps import parse_gps_info
from metochina.core.hasher import compute_hashes
from metochina.models.metadata import (
    BatchReport,
    CameraData,
    GPSData,
    ImageMetadata,
    SoftwareData,
)

logger = logging.getLogger(__name__)

SUPPORTED_EXTENSIONS = frozenset({
    ".jpg", ".jpeg", ".png", ".tiff", ".tif",
    ".webp", ".heic", ".heif", ".bmp", ".gif",
})

# Pre-compute a reverse lookup for faster tag resolution
_TAG_LOOKUP: Dict[int, str] = dict(TAGS)
_GPS_TAG_LOOKUP: Dict[int, str] = dict(GPSTAGS)

# EXIF tag name -> CameraData field mappings
_CAMERA_TAG_MAP = {
    "Make": "make",
    "Model": "model",
    "BodySerialNumber": "serial_number",
    "LensMake": "lens_make",
    "LensModel": "lens_model",
    "LensSerialNumber": "lens_serial",
    "ISOSpeedRatings": "iso",
    "MeteringMode": "metering_mode",
    "ExposureMode": "exposure_mode",
    "WhiteBalance": "white_balance",
}

_METERING_MODES = {
    0: "Unknown", 1: "Average", 2: "Center-weighted average",
    3: "Spot", 4: "Multi-spot", 5: "Pattern", 6: "Partial",
}

_EXPOSURE_MODES = {0: "Auto", 1: "Manual", 2: "Auto bracket"}

_WHITE_BALANCE = {0: "Auto", 1: "Manual"}

_ORIENTATION_MAP = {
    1: "Normal", 2: "Mirrored", 3: "Rotated 180°",
    4: "Mirrored + Rotated 180°", 5: "Mirrored + Rotated 270° CW",
    6: "Rotated 90° CW", 7: "Mirrored + Rotated 90° CW", 8: "Rotated 270° CW",
}

_COLOR_SPACE_MAP = {1: "sRGB", 2: "Adobe RGB", 65535: "Uncalibrated"}

_SCENE_TYPE_MAP = {1: "Directly photographed"}

# Bit depth lookup by PIL mode
_MODE_BITS = {
    "1": 1, "L": 8, "P": 8, "RGB": 24, "RGBA": 32,
    "CMYK": 32, "YCbCr": 24, "I": 32, "F": 32, "LA": 16,
    "I;16": 16, "I;16L": 16, "I;16B": 16,
}

# Lookup converters (avoid repeated if/elif in loops)
_ENUM_CONVERTERS: Dict[str, Dict[int, str]] = {
    "metering_mode": _METERING_MODES,
    "exposure_mode": _EXPOSURE_MODES,
    "white_balance": _WHITE_BALANCE,
}


def _safe_str(value: Any) -> Optional[str]:
    """Convert a value to string safely, returning None for empty/None."""
    if value is None:
        return None
    s = str(value).strip()
    return s if s else None


def _safe_float(value: Any) -> Optional[float]:
    """Convert to float, handling IFDRational objects."""
    if value is None:
        return None
    try:
        if hasattr(value, "numerator") and hasattr(value, "denominator"):
            if value.denominator == 0:
                return None
            return float(value.numerator) / float(value.denominator)
        return float(value)
    except (TypeError, ValueError):
        return None


def _safe_int(value: Any) -> Optional[int]:
    """Convert to int safely."""
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _decode_exif(exif_data: Dict) -> Dict[str, Any]:
    """Decode raw EXIF data into a dict with human-readable tag names."""
    decoded: Dict[str, Any] = {}
    for tag_id, value in exif_data.items():
        tag_name = _TAG_LOOKUP.get(tag_id, str(tag_id))
        if tag_name == "GPSInfo" and isinstance(value, dict):
            continue
        decoded[tag_name] = _make_serializable(value)
    return decoded


def _decode_gps_ifd(gps_ifd: Dict) -> Dict[str, Any]:
    """Decode GPS IFD using GPSTAGS for human-readable keys."""
    return {_GPS_TAG_LOOKUP.get(tid, str(tid)): val for tid, val in gps_ifd.items()}


def _make_serializable(value: Any) -> Any:
    """Make a value JSON-serializable."""
    if isinstance(value, bytes):
        try:
            return value.decode("utf-8", errors="replace")
        except Exception:
            return repr(value)
    if hasattr(value, "numerator") and hasattr(value, "denominator"):
        if value.denominator == 0:
            return None
        return float(value.numerator) / float(value.denominator)
    if isinstance(value, (tuple, list)):
        return [_make_serializable(v) for v in value]
    if isinstance(value, dict):
        return {str(k): _make_serializable(v) for k, v in value.items()}
    return value


def _parse_flash(value: Any) -> Optional[str]:
    """Interpret flash EXIF value with detailed mode."""
    if value is None:
        return None
    try:
        v = int(value)
        fired = "Fired" if v & 1 else "Did not fire"
        parts = [fired]
        if v & 0x06 == 0x04:
            parts.append("return not detected")
        elif v & 0x06 == 0x06:
            parts.append("return detected")
        if v & 0x18 == 0x08:
            parts.append("compulsory on")
        elif v & 0x18 == 0x10:
            parts.append("compulsory off")
        elif v & 0x18 == 0x18:
            parts.append("auto")
        if v & 0x40:
            parts.append("red-eye reduction")
        return ", ".join(parts)
    except (TypeError, ValueError):
        return _safe_str(value)


def _parse_shutter_speed(value: Any) -> Optional[str]:
    """Format exposure time as a fraction string."""
    f = _safe_float(value)
    if f is None:
        return None
    if f >= 1:
        return f"{f:.1f}s"
    if f > 0:
        inv = 1.0 / f
        return f"1/{int(round(inv))}s"
    return None


def _extract_camera(decoded: Dict[str, Any]) -> CameraData:
    """Extract camera information from decoded EXIF."""
    cam = CameraData()
    for exif_key, attr in _CAMERA_TAG_MAP.items():
        val = decoded.get(exif_key)
        if val is None:
            continue
        converter = _ENUM_CONVERTERS.get(attr)
        if attr == "iso":
            setattr(cam, attr, _safe_int(val))
        elif converter is not None:
            setattr(cam, attr, converter.get(val, _safe_str(val)))
        else:
            setattr(cam, attr, _safe_str(val))

    cam.focal_length = _safe_float(decoded.get("FocalLength"))
    cam.focal_length_35mm = _safe_float(decoded.get("FocalLengthIn35mmFilm"))
    cam.aperture = _safe_float(decoded.get("FNumber"))
    cam.shutter_speed = _parse_shutter_speed(decoded.get("ExposureTime"))
    cam.flash = _parse_flash(decoded.get("Flash"))

    return cam


def _extract_software(decoded: Dict[str, Any]) -> SoftwareData:
    """Extract software information from decoded EXIF."""
    return SoftwareData(
        software=_safe_str(decoded.get("Software")),
        processing_software=_safe_str(decoded.get("ProcessingSoftware")),
        creator_tool=_safe_str(decoded.get("CreatorTool") or decoded.get("XMP:CreatorTool")),
        host_computer=_safe_str(decoded.get("HostComputer")),
        os_version=_safe_str(decoded.get("OSVersion")),
    )


def _extract_dates(decoded: Dict[str, Any]) -> Dict[str, Optional[str]]:
    """Extract date fields."""
    return {
        "date_taken": _safe_str(decoded.get("DateTimeOriginal")),
        "date_modified": _safe_str(decoded.get("DateTime")),
        "date_digitized": _safe_str(decoded.get("DateTimeDigitized")),
    }


def _generate_warnings(meta: ImageMetadata) -> List[str]:
    """Generate privacy/integrity warnings based on extracted metadata."""
    warnings: List[str] = []

    if meta.gps.has_coordinates:
        warnings.append("GPS coordinates found — exact location is embedded in this image")

    if meta.camera.serial_number:
        warnings.append(f"Camera serial number exposed: {meta.camera.serial_number}")

    if meta.camera.lens_serial:
        warnings.append(f"Lens serial number exposed: {meta.camera.lens_serial}")

    if meta.software.was_edited:
        warnings.append("Image appears to have been edited with image processing software")

    if meta.software.host_computer:
        warnings.append(f"Host computer name exposed: {meta.software.host_computer}")

    if meta.gps.altitude is not None:
        warnings.append("GPS altitude data present")

    if meta.gps.speed is not None:
        warnings.append("GPS speed data present — movement tracking possible")

    if meta.date_taken and meta.date_modified and meta.date_taken != meta.date_modified:
        warnings.append("Date taken differs from date modified — possible tampering or editing")

    return warnings


def _get_mime_type(filepath: str) -> Optional[str]:
    """Guess MIME type from file extension."""
    mime, _ = mimetypes.guess_type(filepath)
    return mime


def extract_metadata(filepath: str, skip_hash: bool = False) -> ImageMetadata:
    """Extract all metadata from a single image file.

    Args:
        filepath: Path to the image file.
        skip_hash: If True, skip MD5/SHA-256 computation.

    Returns:
        Populated ImageMetadata instance.
    """
    filepath = os.path.abspath(filepath)
    meta = ImageMetadata(
        filename=os.path.basename(filepath),
        filepath=filepath,
    )

    # File-level info
    try:
        stat = os.stat(filepath)
        meta.file_size_bytes = stat.st_size
    except OSError as exc:
        meta.warnings.append(f"Could not stat file: {exc}")

    meta.mime_type = _get_mime_type(filepath)

    # Hashes
    if not skip_hash:
        try:
            meta.md5, meta.sha256 = compute_hashes(filepath)
        except OSError as exc:
            meta.warnings.append(f"Hash computation failed: {exc}")

    # Open image with Pillow
    try:
        with Image.open(filepath) as img:
            meta.file_format = img.format
            meta.width, meta.height = img.size
            meta.color_mode = img.mode
            meta.bit_depth = _MODE_BITS.get(img.mode)

            # EXIF extraction
            exif_data = img.getexif()
            if exif_data:
                decoded = _decode_exif(exif_data)
                meta.raw_exif = decoded

                # GPS
                gps_ifd_raw = exif_data.get_ifd(0x8825)
                if gps_ifd_raw:
                    gps_decoded = _decode_gps_ifd(gps_ifd_raw)
                    meta.gps = parse_gps_info(gps_decoded)

                # Camera
                meta.camera = _extract_camera(decoded)

                # Software
                meta.software = _extract_software(decoded)

                # Dates
                dates = _extract_dates(decoded)
                meta.date_taken = dates["date_taken"]
                meta.date_modified = dates["date_modified"]
                meta.date_digitized = dates["date_digitized"]
            else:
                meta.warnings.append("No EXIF data found")

    except Exception as exc:
        meta.warnings.append(f"Could not open image: {exc}")
        logger.error("Failed to open %s: %s", filepath, exc)

    # Auto-generate warnings
    meta.warnings.extend(_generate_warnings(meta))

    return meta


def find_images(directory: str, recursive: bool = True) -> List[str]:
    """Find all supported image files in a directory.

    Args:
        directory: Root directory to search.
        recursive: If True, search subdirectories.

    Returns:
        Sorted list of absolute file paths.
    """
    directory = os.path.abspath(directory)
    found: List[str] = []

    if recursive:
        for root, _dirs, files in os.walk(directory):
            for fname in files:
                if Path(fname).suffix.lower() in SUPPORTED_EXTENSIONS:
                    found.append(os.path.join(root, fname))
    else:
        try:
            for entry in os.scandir(directory):
                if entry.is_file() and Path(entry.name).suffix.lower() in SUPPORTED_EXTENSIONS:
                    found.append(entry.path)
        except OSError as exc:
            logger.error("Could not scan directory %s: %s", directory, exc)

    return sorted(found)


def extract_batch(
    filepaths: List[str],
    skip_hash: bool = False,
    on_progress: Optional[Callable[[int, int, str], None]] = None,
    max_workers: int = 4,
) -> BatchReport:
    """Extract metadata from multiple images with parallel processing.

    Uses a thread pool for concurrent I/O-bound operations (hash computation,
    file reads). Each image is processed in its own thread.

    Args:
        filepaths: List of image file paths.
        skip_hash: If True, skip hash computation.
        on_progress: Optional callback(current, total, filename) for progress tracking.
        max_workers: Maximum number of concurrent worker threads.

    Returns:
        Populated BatchReport with computed stats.
    """
    start = time.time()
    report = BatchReport()
    total = len(filepaths)

    def _process_one(fp: str) -> ImageMetadata:
        try:
            return extract_metadata(fp, skip_hash=skip_hash)
        except Exception as exc:
            logger.error("Failed to process %s: %s", fp, exc)
            err_meta = ImageMetadata(
                filename=os.path.basename(fp),
                filepath=os.path.abspath(fp),
            )
            err_meta.warnings.append(f"Processing failed: {exc}")
            return err_meta

    if total <= 2:
        # For small batches, skip thread overhead
        for i, fp in enumerate(filepaths):
            meta = _process_one(fp)
            report.images.append(meta)
            if on_progress:
                on_progress(i + 1, total, meta.filename)
    else:
        # Parallel extraction for larger batches
        futures_map = {}
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            for fp in filepaths:
                future = executor.submit(_process_one, fp)
                futures_map[future] = fp

            completed = 0
            # Collect results preserving original order
            results: Dict[str, ImageMetadata] = {}
            for future in as_completed(futures_map):
                fp = futures_map[future]
                results[fp] = future.result()
                completed += 1
                if on_progress:
                    on_progress(completed, total, os.path.basename(fp))

        # Preserve input order
        for fp in filepaths:
            report.images.append(results[fp])

    report.elapsed_seconds = time.time() - start
    report.compute_stats()
    return report
