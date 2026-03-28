"""Tests for data models."""

import json
import unittest

from metochina.models.metadata import (
    BatchReport,
    CameraData,
    GPSData,
    ImageMetadata,
    SoftwareData,
)


class TestGPSData(unittest.TestCase):

    def test_has_coordinates_true(self):
        gps = GPSData(latitude=40.4168, longitude=-3.7038)
        self.assertTrue(gps.has_coordinates)

    def test_has_coordinates_false(self):
        gps = GPSData()
        self.assertFalse(gps.has_coordinates)

    def test_has_coordinates_partial(self):
        gps = GPSData(latitude=40.4168)
        self.assertFalse(gps.has_coordinates)

    def test_google_maps_url(self):
        gps = GPSData(latitude=40.4168, longitude=-3.7038)
        self.assertIn("40.4168", gps.google_maps_url)
        self.assertIn("-3.7038", gps.google_maps_url)
        self.assertIn("google.com/maps", gps.google_maps_url)

    def test_google_maps_url_none_when_no_coords(self):
        gps = GPSData()
        self.assertIsNone(gps.google_maps_url)

    def test_osm_url(self):
        gps = GPSData(latitude=48.8566, longitude=2.3522)
        self.assertIn("openstreetmap.org", gps.osm_url)
        self.assertIn("48.8566", gps.osm_url)

    def test_to_dict_with_coords(self):
        gps = GPSData(latitude=1.0, longitude=2.0, altitude=100.0)
        d = gps.to_dict()
        self.assertEqual(d["latitude"], 1.0)
        self.assertEqual(d["longitude"], 2.0)
        self.assertEqual(d["altitude"], 100.0)
        self.assertIn("google_maps_url", d)
        self.assertIn("osm_url", d)

    def test_to_dict_empty(self):
        gps = GPSData()
        d = gps.to_dict()
        self.assertEqual(d, {})


class TestCameraData(unittest.TestCase):

    def test_to_dict_omits_none(self):
        cam = CameraData(make="Canon", model="EOS R5")
        d = cam.to_dict()
        self.assertEqual(d["make"], "Canon")
        self.assertEqual(d["model"], "EOS R5")
        self.assertNotIn("serial_number", d)

    def test_to_dict_full(self):
        cam = CameraData(
            make="Nikon", model="Z6", serial_number="12345",
            iso=100, aperture=2.8, focal_length=50.0,
        )
        d = cam.to_dict()
        self.assertEqual(d["iso"], 100)
        self.assertEqual(d["aperture"], 2.8)


class TestSoftwareData(unittest.TestCase):

    def test_was_edited_photoshop(self):
        sw = SoftwareData(software="Adobe Photoshop CC 2023")
        self.assertTrue(sw.was_edited)

    def test_was_edited_lightroom(self):
        sw = SoftwareData(software="Adobe Lightroom Classic 12.0")
        self.assertTrue(sw.was_edited)

    def test_was_edited_gimp(self):
        sw = SoftwareData(processing_software="GIMP 2.10")
        self.assertTrue(sw.was_edited)

    def test_was_edited_snapseed(self):
        sw = SoftwareData(creator_tool="Snapseed 2.0")
        self.assertTrue(sw.was_edited)

    def test_was_edited_figma(self):
        sw = SoftwareData(software="Figma Export")
        self.assertTrue(sw.was_edited)

    def test_was_edited_false(self):
        sw = SoftwareData(software="iPhone 15 Pro")
        self.assertFalse(sw.was_edited)

    def test_was_edited_none(self):
        sw = SoftwareData()
        self.assertFalse(sw.was_edited)

    def test_to_dict(self):
        sw = SoftwareData(software="TestApp")
        d = sw.to_dict()
        self.assertEqual(d["software"], "TestApp")
        self.assertIn("was_edited", d)


class TestImageMetadata(unittest.TestCase):

    def test_file_size_human_bytes(self):
        meta = ImageMetadata(file_size_bytes=500)
        self.assertEqual(meta.file_size_human, "500 B")

    def test_file_size_human_kb(self):
        meta = ImageMetadata(file_size_bytes=2048)
        self.assertEqual(meta.file_size_human, "2.0 KB")

    def test_file_size_human_mb(self):
        meta = ImageMetadata(file_size_bytes=5 * 1024 * 1024)
        self.assertEqual(meta.file_size_human, "5.0 MB")

    def test_resolution(self):
        meta = ImageMetadata(width=1920, height=1080)
        self.assertEqual(meta.resolution, "1920x1080")

    def test_resolution_none(self):
        meta = ImageMetadata()
        self.assertIsNone(meta.resolution)

    def test_megapixels(self):
        meta = ImageMetadata(width=4000, height=3000)
        self.assertEqual(meta.megapixels, 12.0)

    def test_has_exif(self):
        meta = ImageMetadata(raw_exif={"Make": "Canon"})
        self.assertTrue(meta.has_exif)

    def test_has_exif_false(self):
        meta = ImageMetadata()
        self.assertFalse(meta.has_exif)

    def test_has_gps(self):
        meta = ImageMetadata(gps=GPSData(latitude=1.0, longitude=2.0))
        self.assertTrue(meta.has_gps)

    def test_to_dict(self):
        meta = ImageMetadata(
            filename="test.jpg", filepath="/tmp/test.jpg",
            file_size_bytes=1024, width=100, height=100,
        )
        d = meta.to_dict()
        self.assertEqual(d["file"]["filename"], "test.jpg")
        self.assertIn("hashes", d)
        self.assertIn("gps", d)

    def test_to_json(self):
        meta = ImageMetadata(filename="test.jpg")
        j = meta.to_json()
        parsed = json.loads(j)
        self.assertEqual(parsed["file"]["filename"], "test.jpg")

    def test_to_row(self):
        meta = ImageMetadata(
            filename="test.jpg", filepath="/tmp/test.jpg",
            gps=GPSData(latitude=1.0, longitude=2.0),
        )
        row = meta.to_row()
        self.assertEqual(row["filename"], "test.jpg")
        self.assertEqual(row["gps_latitude"], 1.0)
        self.assertTrue(row["has_gps"])


class TestBatchReport(unittest.TestCase):

    def _make_images(self):
        img1 = ImageMetadata(
            filename="a.jpg",
            camera=CameraData(make="Canon", model="EOS R5"),
            software=SoftwareData(software="Adobe Photoshop"),
            gps=GPSData(latitude=1.0, longitude=2.0),
            raw_exif={"Make": "Canon"},
        )
        img2 = ImageMetadata(
            filename="b.jpg",
            camera=CameraData(make="Canon", model="EOS R5"),
            software=SoftwareData(software="Camera App"),
            raw_exif={"Make": "Canon"},
        )
        return [img1, img2]

    def test_compute_stats(self):
        report = BatchReport(images=self._make_images())
        report.compute_stats()
        self.assertEqual(report.total_files, 2)
        self.assertEqual(report.files_with_exif, 2)
        self.assertEqual(report.files_with_gps, 1)
        self.assertEqual(report.files_edited, 1)
        self.assertEqual(len(report.unique_cameras), 1)

    def test_gps_images(self):
        report = BatchReport(images=self._make_images())
        gps_imgs = report.gps_images
        self.assertEqual(len(gps_imgs), 1)
        self.assertEqual(gps_imgs[0].filename, "a.jpg")

    def test_summary(self):
        report = BatchReport(images=self._make_images(), elapsed_seconds=1.5)
        report.compute_stats()
        s = report.summary()
        self.assertEqual(s["total_files"], 2)
        self.assertEqual(s["elapsed_seconds"], 1.5)


if __name__ == "__main__":
    unittest.main()
