"""Tests for the privacy risk analyzer."""

import unittest

from metochina.analysis.analyzer import (
    PrivacyRisk,
    _haversine_km,
    assess_batch_patterns,
    assess_privacy_risks,
    compute_privacy_score,
    compute_risk_breakdown,
)
from metochina.models.metadata import (
    BatchReport,
    CameraData,
    GPSData,
    ImageMetadata,
    SoftwareData,
)


class TestAssessPrivacyRisks(unittest.TestCase):

    def test_gps_high_risk(self):
        meta = ImageMetadata(gps=GPSData(latitude=40.0, longitude=-3.0))
        risks = assess_privacy_risks(meta)
        high = [r for r in risks if r.level == "HIGH"]
        self.assertTrue(any("GPS" in r.description for r in high))

    def test_serial_high_risk(self):
        meta = ImageMetadata(camera=CameraData(serial_number="ABC123"))
        risks = assess_privacy_risks(meta)
        high = [r for r in risks if r.level == "HIGH"]
        self.assertTrue(any("serial" in r.description.lower() for r in high))

    def test_altitude_medium_risk(self):
        meta = ImageMetadata(gps=GPSData(altitude=100.0))
        risks = assess_privacy_risks(meta)
        medium = [r for r in risks if r.level == "MEDIUM"]
        self.assertTrue(any("altitude" in r.description.lower() for r in medium))

    def test_timestamp_medium_risk(self):
        meta = ImageMetadata(date_taken="2024:06:15 12:00:00")
        risks = assess_privacy_risks(meta)
        medium = [r for r in risks if r.level == "MEDIUM"]
        self.assertTrue(any("timestamp" in r.description.lower() for r in medium))

    def test_host_computer_medium(self):
        meta = ImageMetadata(software=SoftwareData(host_computer="DESKTOP-ABC"))
        risks = assess_privacy_risks(meta)
        medium = [r for r in risks if r.level == "MEDIUM"]
        self.assertTrue(any("host" in r.description.lower() for r in medium))

    def test_camera_make_low(self):
        meta = ImageMetadata(camera=CameraData(make="Canon"))
        risks = assess_privacy_risks(meta)
        low = [r for r in risks if r.level == "LOW"]
        self.assertTrue(any("Canon" in r.description for r in low))

    def test_software_low(self):
        meta = ImageMetadata(software=SoftwareData(software="Camera App"))
        risks = assess_privacy_risks(meta)
        low = [r for r in risks if r.level == "LOW"]
        self.assertTrue(any("Camera App" in r.description for r in low))

    def test_no_risks(self):
        meta = ImageMetadata()
        risks = assess_privacy_risks(meta)
        self.assertEqual(len(risks), 0)

    def test_sorting(self):
        meta = ImageMetadata(
            gps=GPSData(latitude=1.0, longitude=2.0, altitude=50.0),
            camera=CameraData(make="Canon", serial_number="123"),
        )
        risks = assess_privacy_risks(meta)
        levels = [r.level for r in risks]
        # HIGH should come before MEDIUM which comes before LOW
        high_idx = [i for i, l in enumerate(levels) if l == "HIGH"]
        medium_idx = [i for i, l in enumerate(levels) if l == "MEDIUM"]
        low_idx = [i for i, l in enumerate(levels) if l == "LOW"]
        if high_idx and medium_idx:
            self.assertLess(max(high_idx), min(medium_idx))
        if medium_idx and low_idx:
            self.assertLess(max(medium_idx), min(low_idx))


class TestComputePrivacyScore(unittest.TestCase):

    def test_zero(self):
        self.assertEqual(compute_privacy_score([]), 0)

    def test_one_high(self):
        risks = [PrivacyRisk("HIGH", "Location", "", "")]
        self.assertEqual(compute_privacy_score(risks), 25)

    def test_capped_at_100(self):
        risks = [PrivacyRisk("HIGH", "X", "", "") for _ in range(10)]
        self.assertEqual(compute_privacy_score(risks), 100)

    def test_mixed(self):
        risks = [
            PrivacyRisk("HIGH", "A", "", ""),
            PrivacyRisk("MEDIUM", "B", "", ""),
            PrivacyRisk("LOW", "C", "", ""),
        ]
        # 25 + 10 + 3 = 38
        self.assertEqual(compute_privacy_score(risks), 38)


class TestAssessBatchPatterns(unittest.TestCase):

    def test_single_camera(self):
        report = BatchReport(images=[
            ImageMetadata(camera=CameraData(make="Canon", model="R5"), raw_exif={"x": 1}),
            ImageMetadata(camera=CameraData(make="Canon", model="R5"), raw_exif={"x": 1}),
        ])
        report.compute_stats()
        patterns = assess_batch_patterns(report)
        self.assertTrue(any("same device" in p.lower() for p in patterns))

    def test_gps_coverage(self):
        report = BatchReport(images=[
            ImageMetadata(gps=GPSData(latitude=1.0, longitude=2.0)),
            ImageMetadata(),
        ])
        report.compute_stats()
        patterns = assess_batch_patterns(report)
        self.assertTrue(any("GPS" in p for p in patterns))

    def test_date_clustering(self):
        report = BatchReport(images=[
            ImageMetadata(date_taken="2024:06:15 10:00:00"),
            ImageMetadata(date_taken="2024:06:15 14:00:00"),
        ])
        report.compute_stats()
        patterns = assess_batch_patterns(report)
        self.assertTrue(any("clustering" in p.lower() or "date" in p.lower() for p in patterns))

    def test_empty_report(self):
        report = BatchReport()
        report.compute_stats()
        patterns = assess_batch_patterns(report)
        self.assertEqual(patterns, [])

    def test_gps_spread_detection(self):
        report = BatchReport(images=[
            ImageMetadata(gps=GPSData(latitude=40.4168, longitude=-3.7038)),
            ImageMetadata(gps=GPSData(latitude=48.8566, longitude=2.3522)),
        ])
        report.compute_stats()
        patterns = assess_batch_patterns(report)
        self.assertTrue(any("spread" in p.lower() or "km" in p.lower() for p in patterns))


class TestHaversine(unittest.TestCase):

    def test_same_point(self):
        self.assertAlmostEqual(_haversine_km(0, 0, 0, 0), 0.0)

    def test_known_distance(self):
        # Madrid to Paris ≈ 1053 km
        dist = _haversine_km(40.4168, -3.7038, 48.8566, 2.3522)
        self.assertAlmostEqual(dist, 1053, delta=20)

    def test_short_distance(self):
        # Two points ~111 km apart (1 degree latitude at equator)
        dist = _haversine_km(0, 0, 1, 0)
        self.assertAlmostEqual(dist, 111, delta=2)


class TestRiskBreakdown(unittest.TestCase):

    def test_breakdown(self):
        risks = [
            PrivacyRisk("HIGH", "Location", "", ""),
            PrivacyRisk("HIGH", "Device", "", ""),
            PrivacyRisk("MEDIUM", "Temporal", "", ""),
            PrivacyRisk("LOW", "Software", "", ""),
        ]
        bd = compute_risk_breakdown(risks)
        self.assertEqual(bd["by_level"]["HIGH"], 2)
        self.assertEqual(bd["by_level"]["MEDIUM"], 1)
        self.assertEqual(bd["by_level"]["LOW"], 1)
        self.assertEqual(bd["by_category"]["Location"], 1)
        self.assertEqual(bd["by_category"]["Device"], 1)

    def test_empty_breakdown(self):
        bd = compute_risk_breakdown([])
        self.assertEqual(bd["by_level"]["HIGH"], 0)


if __name__ == "__main__":
    unittest.main()
