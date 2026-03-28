"""Privacy risk assessment engine.

Evaluates extracted image metadata against a comprehensive set of privacy
risk rules and produces a scored risk report. Includes batch pattern
analysis with GPS distance calculations and temporal clustering.
"""

from __future__ import annotations

import math
from collections import Counter
from dataclasses import dataclass, field
from typing import List, Optional, Tuple

from metochina.models.metadata import BatchReport, ImageMetadata


@dataclass
class PrivacyRisk:
    """A single privacy risk finding."""

    level: str  # "HIGH", "MEDIUM", "LOW"
    category: str  # "Location", "Device", "Temporal", "Software"
    description: str
    recommendation: str

    def to_dict(self) -> dict:
        return {
            "level": self.level,
            "category": self.category,
            "description": self.description,
            "recommendation": self.recommendation,
        }


# ── Privacy scoring weights ─────────────────────────────────────────────────

_WEIGHTS = {"HIGH": 25, "MEDIUM": 10, "LOW": 3}
_LEVEL_ORDER = {"HIGH": 0, "MEDIUM": 1, "LOW": 2}


# ── Haversine for GPS distance ──────────────────────────────────────────────

def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate great-circle distance between two GPS points in kilometers."""
    R = 6371.0  # Earth radius in km
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2) ** 2
         + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2))
         * math.sin(dlon / 2) ** 2)
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


# ── Risk assessment ─────────────────────────────────────────────────────────

def assess_privacy_risks(metadata: ImageMetadata) -> List[PrivacyRisk]:
    """Evaluate privacy risks for a single image.

    Applies a comprehensive ruleset covering location, device identity,
    temporal patterns, and software information.

    Args:
        metadata: Extracted image metadata.

    Returns:
        List of PrivacyRisk findings, sorted HIGH -> MEDIUM -> LOW.
    """
    risks: List[PrivacyRisk] = []

    # ── HIGH ────────────────────────────────────────────────────────────
    if metadata.gps.has_coordinates:
        risks.append(PrivacyRisk(
            level="HIGH",
            category="Location",
            description=(
                f"GPS coordinates embedded: {metadata.gps.latitude}, {metadata.gps.longitude}. "
                "Exact location can be determined."
            ),
            recommendation=(
                "Strip EXIF GPS data before sharing. "
                "Use exiftool -gps:all= or similar."
            ),
        ))

    if metadata.camera.serial_number:
        risks.append(PrivacyRisk(
            level="HIGH",
            category="Device",
            description=f"Camera body serial number exposed: {metadata.camera.serial_number}",
            recommendation=(
                "Remove serial number from EXIF before publishing. "
                "This can uniquely identify your device across images."
            ),
        ))

    # ── MEDIUM ──────────────────────────────────────────────────────────
    if metadata.gps.altitude is not None:
        risks.append(PrivacyRisk(
            level="MEDIUM",
            category="Location",
            description=f"GPS altitude data present: {metadata.gps.altitude}m",
            recommendation="Strip altitude data along with other GPS fields.",
        ))

    if metadata.date_taken:
        risks.append(PrivacyRisk(
            level="MEDIUM",
            category="Temporal",
            description=f"Original capture timestamp: {metadata.date_taken}",
            recommendation="Consider removing timestamps if they could reveal your schedule or patterns.",
        ))

    if metadata.software.host_computer:
        risks.append(PrivacyRisk(
            level="MEDIUM",
            category="Device",
            description=f"Host computer name exposed: {metadata.software.host_computer}",
            recommendation="Remove host computer information from EXIF metadata.",
        ))

    if metadata.camera.lens_serial:
        risks.append(PrivacyRisk(
            level="MEDIUM",
            category="Device",
            description=f"Lens serial number exposed: {metadata.camera.lens_serial}",
            recommendation="Remove lens serial number to prevent equipment fingerprinting.",
        ))

    if metadata.gps.timestamp:
        risks.append(PrivacyRisk(
            level="MEDIUM",
            category="Temporal",
            description=f"GPS timestamp present: {metadata.gps.timestamp}",
            recommendation="GPS timestamps can be used to correlate location and time. Strip if unnecessary.",
        ))

    if metadata.software.os_version:
        risks.append(PrivacyRisk(
            level="MEDIUM",
            category="Device",
            description=f"Operating system version exposed: {metadata.software.os_version}",
            recommendation="OS version info can help profile your device. Strip from metadata.",
        ))

    # ── LOW ──────────────────────────────────────────────────────────────
    if metadata.gps.speed is not None:
        risks.append(PrivacyRisk(
            level="LOW",
            category="Location",
            description=f"GPS speed recorded: {metadata.gps.speed} {metadata.gps.speed_ref or ''}".strip(),
            recommendation="Speed data can reveal movement patterns. Consider stripping.",
        ))

    if metadata.gps.direction is not None:
        risks.append(PrivacyRisk(
            level="LOW",
            category="Location",
            description=f"GPS heading/direction recorded: {metadata.gps.direction}\u00b0",
            recommendation="Direction data reveals which way the camera was pointing.",
        ))

    if metadata.camera.make or metadata.camera.model:
        cam = " ".join(filter(None, [metadata.camera.make, metadata.camera.model]))
        risks.append(PrivacyRisk(
            level="LOW",
            category="Device",
            description=f"Camera make/model identified: {cam}",
            recommendation="Camera info alone is low risk but aids device fingerprinting in aggregate.",
        ))

    if metadata.software.software:
        risks.append(PrivacyRisk(
            level="LOW",
            category="Software",
            description=f"Software identified: {metadata.software.software}",
            recommendation="Software info reveals your tools. Low risk unless combined with other data.",
        ))

    if metadata.software.was_edited:
        risks.append(PrivacyRisk(
            level="LOW",
            category="Software",
            description="Image was processed with editing software",
            recommendation="Editing metadata may reveal workflow details. Strip if sensitive.",
        ))

    if metadata.camera.iso and metadata.camera.aperture and metadata.camera.shutter_speed:
        risks.append(PrivacyRisk(
            level="LOW",
            category="Device",
            description=(
                f"Full exposure triangle: ISO {metadata.camera.iso}, "
                f"f/{metadata.camera.aperture}, {metadata.camera.shutter_speed}"
            ),
            recommendation="Detailed exposure data can fingerprint shooting style. Low risk individually.",
        ))

    # Sort by severity
    risks.sort(key=lambda r: _LEVEL_ORDER.get(r.level, 3))

    return risks


def compute_privacy_score(risks: List[PrivacyRisk]) -> int:
    """Compute a privacy exposure score from 0 to 100.

    Higher scores mean more privacy exposure.

    Scoring:
        - Each HIGH risk: +25 points
        - Each MEDIUM risk: +10 points
        - Each LOW risk: +3 points
        - Capped at 100
    """
    score = sum(_WEIGHTS.get(r.level, 0) for r in risks)
    return min(score, 100)


def compute_risk_breakdown(risks: List[PrivacyRisk]) -> dict:
    """Return a breakdown of risk counts by level and category."""
    by_level: dict = {"HIGH": 0, "MEDIUM": 0, "LOW": 0}
    by_category: dict = {}
    for r in risks:
        by_level[r.level] = by_level.get(r.level, 0) + 1
        by_category[r.category] = by_category.get(r.category, 0) + 1
    return {"by_level": by_level, "by_category": by_category}


# ── Batch pattern analysis ──────────────────────────────────────────────────

def assess_batch_patterns(report: BatchReport) -> List[str]:
    """Identify patterns across a batch of images.

    Analyzes device consistency, GPS clustering, temporal patterns,
    serial number exposure, and geographic spread.

    Args:
        report: A BatchReport with computed stats.

    Returns:
        List of human-readable pattern observations.
    """
    observations: List[str] = []

    if report.total_files == 0:
        return observations

    # ── Device consistency ───────────────────────────────────────────────
    if len(report.unique_cameras) == 1:
        observations.append(
            f"Single device: all images taken with {report.unique_cameras[0]}"
        )
    elif len(report.unique_cameras) > 1:
        observations.append(
            f"Multiple devices detected ({len(report.unique_cameras)}): "
            + ", ".join(report.unique_cameras)
        )

    # ── GPS coverage & geographic spread ─────────────────────────────────
    gps_pct = (report.files_with_gps / report.total_files) * 100
    if report.files_with_gps > 0:
        observations.append(
            f"{report.files_with_gps}/{report.total_files} images ({gps_pct:.0f}%) "
            "contain GPS coordinates"
        )

        # Calculate geographic spread
        gps_images = report.gps_images
        if len(gps_images) >= 2:
            lats = [img.gps.latitude for img in gps_images]
            lons = [img.gps.longitude for img in gps_images]
            max_dist = 0.0
            for i in range(len(gps_images)):
                for j in range(i + 1, len(gps_images)):
                    d = _haversine_km(lats[i], lons[i], lats[j], lons[j])
                    max_dist = max(max_dist, d)

            if max_dist < 0.5:
                observations.append(
                    f"GPS cluster: all geotagged images within {max_dist * 1000:.0f}m "
                    "\u2014 likely same location"
                )
            elif max_dist < 10:
                observations.append(
                    f"GPS spread: {max_dist:.1f} km \u2014 images are in the same area"
                )
            else:
                observations.append(
                    f"GPS spread: {max_dist:.0f} km \u2014 images span a wide geographic area"
                )

    # ── Editing detection ────────────────────────────────────────────────
    if report.files_edited > 0:
        edit_pct = (report.files_edited / report.total_files) * 100
        observations.append(
            f"{report.files_edited}/{report.total_files} images ({edit_pct:.0f}%) "
            "show signs of editing"
        )

    # ── Date clustering ──────────────────────────────────────────────────
    dates: List[str] = []
    for img in report.images:
        if img.date_taken:
            day = img.date_taken[:10].replace(":", "-")
            dates.append(day)

    if dates:
        date_counts = Counter(dates)
        most_common_date, count = date_counts.most_common(1)[0]
        if count > 1:
            observations.append(
                f"Date clustering: {count} images taken on {most_common_date}"
            )
        date_range = sorted(set(dates))
        if len(date_range) > 1:
            observations.append(
                f"Date range: {date_range[0]} to {date_range[-1]} "
                f"({len(date_range)} unique days)"
            )

    # ── Serial number exposure ───────────────────────────────────────────
    serials: List[str] = []
    for img in report.images:
        if img.camera.serial_number:
            serials.append(img.camera.serial_number)
    if serials:
        unique_serials = set(serials)
        observations.append(
            f"{len(serials)} images expose camera serial numbers "
            f"({len(unique_serials)} unique serial(s))"
        )

    # ── Software diversity ───────────────────────────────────────────────
    if len(report.unique_software) > 1:
        observations.append(
            f"Multiple software detected: {', '.join(report.unique_software)}"
        )

    return observations
