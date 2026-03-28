"""Data models for image metadata, GPS, camera, software info, and batch reports."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class GPSData:
    """Parsed GPS information from EXIF data."""

    latitude: Optional[float] = None
    longitude: Optional[float] = None
    altitude: Optional[float] = None
    altitude_ref: Optional[str] = None
    speed: Optional[float] = None
    speed_ref: Optional[str] = None
    direction: Optional[float] = None
    direction_ref: Optional[str] = None
    timestamp: Optional[str] = None
    datum: Optional[str] = None

    @property
    def has_coordinates(self) -> bool:
        """Return True if valid latitude and longitude are present."""
        return self.latitude is not None and self.longitude is not None

    @property
    def google_maps_url(self) -> Optional[str]:
        """Generate a Google Maps URL for the coordinates."""
        if not self.has_coordinates:
            return None
        return f"https://www.google.com/maps?q={self.latitude},{self.longitude}"

    @property
    def osm_url(self) -> Optional[str]:
        """Generate an OpenStreetMap URL for the coordinates."""
        if not self.has_coordinates:
            return None
        return (
            f"https://www.openstreetmap.org/"
            f"?mlat={self.latitude}&mlon={self.longitude}#map=16/{self.latitude}/{self.longitude}"
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        result: Dict[str, Any] = {}
        for fld in (
            "latitude", "longitude", "altitude", "altitude_ref",
            "speed", "speed_ref", "direction", "direction_ref",
            "timestamp", "datum",
        ):
            val = getattr(self, fld)
            if val is not None:
                result[fld] = val
        if self.has_coordinates:
            result["google_maps_url"] = self.google_maps_url
            result["osm_url"] = self.osm_url
        return result


@dataclass
class CameraData:
    """Camera and lens information from EXIF data."""

    make: Optional[str] = None
    model: Optional[str] = None
    serial_number: Optional[str] = None
    lens_make: Optional[str] = None
    lens_model: Optional[str] = None
    lens_serial: Optional[str] = None
    focal_length: Optional[float] = None
    focal_length_35mm: Optional[float] = None
    aperture: Optional[float] = None
    shutter_speed: Optional[str] = None
    iso: Optional[int] = None
    flash: Optional[str] = None
    metering_mode: Optional[str] = None
    exposure_mode: Optional[str] = None
    white_balance: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary, omitting None values."""
        result: Dict[str, Any] = {}
        for fld in (
            "make", "model", "serial_number",
            "lens_make", "lens_model", "lens_serial",
            "focal_length", "focal_length_35mm", "aperture",
            "shutter_speed", "iso", "flash",
            "metering_mode", "exposure_mode", "white_balance",
        ):
            val = getattr(self, fld)
            if val is not None:
                result[fld] = val
        return result


_EDITOR_KEYWORDS = frozenset({
    "photoshop", "lightroom", "gimp", "snapseed", "capture one",
    "darktable", "affinity", "luminar", "pixelmator", "paint.net",
    "acdsee", "dxo", "topaz", "on1", "corel", "photopea",
    "canva", "picasa", "instagram", "vsco", "afterlight",
    "polarr", "fotor", "befunky", "ribbet", "photoscape",
    "rawtherapee", "photoline", "zoner", "paintshop",
    "adobe", "figma", "sketch",
})


@dataclass
class SoftwareData:
    """Software and processing information from EXIF data."""

    software: Optional[str] = None
    processing_software: Optional[str] = None
    creator_tool: Optional[str] = None
    host_computer: Optional[str] = None
    os_version: Optional[str] = None

    @property
    def was_edited(self) -> bool:
        """Heuristic: return True if known editing software is detected."""
        for field_val in (self.software, self.processing_software, self.creator_tool):
            if field_val:
                lower = field_val.lower()
                if any(kw in lower for kw in _EDITOR_KEYWORDS):
                    return True
        return False

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary, omitting None values."""
        result: Dict[str, Any] = {}
        for fld in (
            "software", "processing_software", "creator_tool",
            "host_computer", "os_version",
        ):
            val = getattr(self, fld)
            if val is not None:
                result[fld] = val
        result["was_edited"] = self.was_edited
        return result


@dataclass
class ImageMetadata:
    """Complete metadata for a single image."""

    # File info
    filename: str = ""
    filepath: str = ""
    file_size_bytes: int = 0
    file_format: Optional[str] = None
    mime_type: Optional[str] = None
    width: Optional[int] = None
    height: Optional[int] = None
    color_mode: Optional[str] = None
    bit_depth: Optional[int] = None

    # Hashes
    md5: Optional[str] = None
    sha256: Optional[str] = None

    # Dates
    date_taken: Optional[str] = None
    date_modified: Optional[str] = None
    date_digitized: Optional[str] = None

    # Components
    gps: GPSData = field(default_factory=GPSData)
    camera: CameraData = field(default_factory=CameraData)
    software: SoftwareData = field(default_factory=SoftwareData)

    # Raw EXIF
    raw_exif: Dict[str, Any] = field(default_factory=dict)

    # Warnings
    warnings: List[str] = field(default_factory=list)

    @property
    def raw_exif_count(self) -> int:
        """Number of raw EXIF fields extracted."""
        return len(self.raw_exif)

    @property
    def has_exif(self) -> bool:
        """Return True if any EXIF data was extracted."""
        return self.raw_exif_count > 0

    @property
    def has_gps(self) -> bool:
        """Return True if GPS coordinates are present."""
        return self.gps.has_coordinates

    @property
    def file_size_human(self) -> str:
        """Return human-readable file size."""
        size = self.file_size_bytes
        for unit in ("B", "KB", "MB", "GB"):
            if size < 1024:
                return f"{size:.1f} {unit}" if unit != "B" else f"{size} B"
            size /= 1024
        return f"{size:.1f} TB"

    @property
    def resolution(self) -> Optional[str]:
        """Return resolution as WxH string."""
        if self.width and self.height:
            return f"{self.width}x{self.height}"
        return None

    @property
    def megapixels(self) -> Optional[float]:
        """Return megapixel count."""
        if self.width and self.height:
            return round((self.width * self.height) / 1_000_000, 1)
        return None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to full dictionary representation."""
        return {
            "file": {
                "filename": self.filename,
                "filepath": self.filepath,
                "file_size_bytes": self.file_size_bytes,
                "file_size_human": self.file_size_human,
                "file_format": self.file_format,
                "mime_type": self.mime_type,
                "width": self.width,
                "height": self.height,
                "resolution": self.resolution,
                "megapixels": self.megapixels,
                "color_mode": self.color_mode,
                "bit_depth": self.bit_depth,
            },
            "hashes": {
                "md5": self.md5,
                "sha256": self.sha256,
            },
            "dates": {
                "date_taken": self.date_taken,
                "date_modified": self.date_modified,
                "date_digitized": self.date_digitized,
            },
            "gps": self.gps.to_dict(),
            "camera": self.camera.to_dict(),
            "software": self.software.to_dict(),
            "raw_exif_count": self.raw_exif_count,
            "has_exif": self.has_exif,
            "has_gps": self.has_gps,
            "warnings": self.warnings,
        }

    def to_json(self, indent: int = 2) -> str:
        """Serialize to JSON string."""
        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=False)

    def to_row(self) -> Dict[str, Any]:
        """Flat dictionary suitable for a CSV row."""
        return {
            "filename": self.filename,
            "filepath": self.filepath,
            "file_size_bytes": self.file_size_bytes,
            "file_format": self.file_format,
            "width": self.width,
            "height": self.height,
            "megapixels": self.megapixels,
            "md5": self.md5,
            "sha256": self.sha256,
            "date_taken": self.date_taken,
            "date_modified": self.date_modified,
            "date_digitized": self.date_digitized,
            "gps_latitude": self.gps.latitude,
            "gps_longitude": self.gps.longitude,
            "gps_altitude": self.gps.altitude,
            "google_maps_url": self.gps.google_maps_url,
            "camera_make": self.camera.make,
            "camera_model": self.camera.model,
            "camera_serial": self.camera.serial_number,
            "lens_model": self.camera.lens_model,
            "focal_length": self.camera.focal_length,
            "aperture": self.camera.aperture,
            "iso": self.camera.iso,
            "software": self.software.software,
            "was_edited": self.software.was_edited,
            "has_exif": self.has_exif,
            "has_gps": self.has_gps,
            "warnings_count": len(self.warnings),
        }


@dataclass
class BatchReport:
    """Aggregated report for multiple images."""

    images: List[ImageMetadata] = field(default_factory=list)
    elapsed_seconds: float = 0.0

    # Computed stats (populated by compute_stats)
    total_files: int = 0
    files_with_exif: int = 0
    files_with_gps: int = 0
    files_edited: int = 0
    unique_cameras: List[str] = field(default_factory=list)
    unique_software: List[str] = field(default_factory=list)

    def compute_stats(self) -> None:
        """Calculate aggregate statistics from the image list."""
        self.total_files = len(self.images)
        self.files_with_exif = sum(1 for img in self.images if img.has_exif)
        self.files_with_gps = sum(1 for img in self.images if img.has_gps)
        self.files_edited = sum(1 for img in self.images if img.software.was_edited)

        cameras: set = set()
        software_set: set = set()
        for img in self.images:
            if img.camera.make or img.camera.model:
                cam = " ".join(filter(None, [img.camera.make, img.camera.model]))
                cameras.add(cam)
            if img.software.software:
                software_set.add(img.software.software)

        self.unique_cameras = sorted(cameras)
        self.unique_software = sorted(software_set)

    @property
    def gps_images(self) -> List[ImageMetadata]:
        """Return only images that have GPS data."""
        return [img for img in self.images if img.has_gps]

    def summary(self) -> Dict[str, Any]:
        """Return summary dictionary."""
        return {
            "total_files": self.total_files,
            "files_with_exif": self.files_with_exif,
            "files_with_gps": self.files_with_gps,
            "files_edited": self.files_edited,
            "unique_cameras": self.unique_cameras,
            "unique_software": self.unique_software,
            "elapsed_seconds": round(self.elapsed_seconds, 2),
        }
