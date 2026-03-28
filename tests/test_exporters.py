"""Tests for JSON, CSV, and HTML exporters."""

import csv
import json
import os
import tempfile
import unittest

from metochina.models.metadata import (
    BatchReport,
    CameraData,
    GPSData,
    ImageMetadata,
    SoftwareData,
)
from metochina.output.exporters import export_csv, export_html, export_json


class TestExportJSON(unittest.TestCase):

    def test_single_image(self):
        meta = ImageMetadata(
            filename="test.jpg",
            gps=GPSData(latitude=1.0, longitude=2.0),
            camera=CameraData(make="Canon"),
        )
        with tempfile.NamedTemporaryFile(delete=False, suffix=".json", mode="w") as f:
            path = f.name

        try:
            export_json(meta, path)
            with open(path, "r", encoding="utf-8") as fh:
                data = json.load(fh)
            self.assertEqual(data["file"]["filename"], "test.jpg")
            self.assertIn("privacy_risks", data)
            self.assertIn("privacy_score", data)
        finally:
            os.unlink(path)

    def test_batch_report(self):
        report = BatchReport(images=[
            ImageMetadata(filename="a.jpg"),
            ImageMetadata(filename="b.jpg"),
        ], elapsed_seconds=0.5)
        report.compute_stats()

        with tempfile.NamedTemporaryFile(delete=False, suffix=".json") as f:
            path = f.name

        try:
            export_json(report, path)
            with open(path, "r", encoding="utf-8") as fh:
                data = json.load(fh)
            self.assertIn("summary", data)
            self.assertIn("images", data)
            self.assertEqual(len(data["images"]), 2)
        finally:
            os.unlink(path)


class TestExportCSV(unittest.TestCase):

    def test_batch_csv(self):
        report = BatchReport(images=[
            ImageMetadata(filename="a.jpg", file_size_bytes=1024),
            ImageMetadata(filename="b.png", file_size_bytes=2048),
        ])
        report.compute_stats()

        with tempfile.NamedTemporaryFile(delete=False, suffix=".csv") as f:
            path = f.name

        try:
            export_csv(report, path)
            with open(path, "r", encoding="utf-8") as fh:
                reader = csv.DictReader(fh)
                rows = list(reader)
            self.assertEqual(len(rows), 2)
            self.assertEqual(rows[0]["filename"], "a.jpg")
            self.assertEqual(rows[1]["filename"], "b.png")
        finally:
            os.unlink(path)


class TestExportHTML(unittest.TestCase):

    def test_single_html(self):
        meta = ImageMetadata(
            filename="test.jpg",
            gps=GPSData(latitude=48.8566, longitude=2.3522),
            camera=CameraData(make="Sony", model="A7III"),
        )
        with tempfile.NamedTemporaryFile(delete=False, suffix=".html") as f:
            path = f.name

        try:
            export_html(meta, path)
            with open(path, "r", encoding="utf-8") as fh:
                content = fh.read()
            self.assertIn("Metochina", content)
            self.assertIn("test.jpg", content)
            self.assertIn("openstreetmap.org", content)
            self.assertIn("google.com/maps", content)
            self.assertIn("<style>", content)  # Self-contained
        finally:
            os.unlink(path)

    def test_batch_html(self):
        report = BatchReport(images=[
            ImageMetadata(
                filename="a.jpg",
                gps=GPSData(latitude=40.0, longitude=-3.0),
            ),
            ImageMetadata(filename="b.jpg"),
        ], elapsed_seconds=0.3)
        report.compute_stats()

        with tempfile.NamedTemporaryFile(delete=False, suffix=".html") as f:
            path = f.name

        try:
            export_html(report, path)
            with open(path, "r", encoding="utf-8") as fh:
                content = fh.read()
            self.assertIn("Batch Report", content)
            self.assertIn("a.jpg", content)
            self.assertIn("b.jpg", content)
        finally:
            os.unlink(path)

    def test_html_no_gps(self):
        meta = ImageMetadata(filename="no_gps.jpg")
        with tempfile.NamedTemporaryFile(delete=False, suffix=".html") as f:
            path = f.name

        try:
            export_html(meta, path)
            with open(path, "r", encoding="utf-8") as fh:
                content = fh.read()
            self.assertIn("Metochina", content)
            self.assertNotIn("iframe", content)
        finally:
            os.unlink(path)


if __name__ == "__main__":
    unittest.main()
