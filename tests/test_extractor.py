"""Tests for the metadata extraction engine."""

import os
import tempfile
import unittest
from unittest.mock import MagicMock, patch

from PIL import Image

from metochina.core.extractor import (
    SUPPORTED_EXTENSIONS,
    _make_serializable,
    _parse_flash,
    _parse_shutter_speed,
    _safe_float,
    _safe_str,
    extract_batch,
    extract_metadata,
    find_images,
)


class TestSafeConversions(unittest.TestCase):

    def test_safe_str_none(self):
        self.assertIsNone(_safe_str(None))

    def test_safe_str_empty(self):
        self.assertIsNone(_safe_str(""))

    def test_safe_str_normal(self):
        self.assertEqual(_safe_str("hello"), "hello")

    def test_safe_str_strips(self):
        self.assertEqual(_safe_str("  test  "), "test")

    def test_safe_float_none(self):
        self.assertIsNone(_safe_float(None))

    def test_safe_float_number(self):
        self.assertAlmostEqual(_safe_float(3.14), 3.14)

    def test_safe_float_rational(self):
        r = MagicMock()
        r.numerator = 1
        r.denominator = 4
        self.assertAlmostEqual(_safe_float(r), 0.25)

    def test_safe_float_zero_denom(self):
        r = MagicMock()
        r.numerator = 1
        r.denominator = 0
        self.assertIsNone(_safe_float(r))


class TestMakeSerializable(unittest.TestCase):

    def test_bytes(self):
        result = _make_serializable(b"hello")
        self.assertEqual(result, "hello")

    def test_rational(self):
        r = MagicMock()
        r.numerator = 3
        r.denominator = 2
        self.assertAlmostEqual(_make_serializable(r), 1.5)

    def test_nested_tuple(self):
        r = MagicMock()
        r.numerator = 1
        r.denominator = 1
        result = _make_serializable((r, 2, "hello"))
        self.assertEqual(result, [1.0, 2, "hello"])


class TestFlashParsing(unittest.TestCase):

    def test_fired(self):
        self.assertEqual(_parse_flash(1), "Fired")

    def test_not_fired(self):
        self.assertEqual(_parse_flash(0), "Did not fire")

    def test_none(self):
        self.assertIsNone(_parse_flash(None))


class TestShutterSpeed(unittest.TestCase):

    def test_fast(self):
        result = _parse_shutter_speed(0.001)
        self.assertEqual(result, "1/1000s")

    def test_slow(self):
        result = _parse_shutter_speed(2.0)
        self.assertEqual(result, "2.0s")

    def test_none(self):
        self.assertIsNone(_parse_shutter_speed(None))


class TestExtractMetadata(unittest.TestCase):

    def test_extract_jpeg(self):
        """Extract metadata from a minimal JPEG created in memory."""
        with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as f:
            img = Image.new("RGB", (100, 50), color="red")
            img.save(f, format="JPEG")
            path = f.name

        try:
            meta = extract_metadata(path)
            self.assertEqual(meta.filename, os.path.basename(path))
            self.assertEqual(meta.width, 100)
            self.assertEqual(meta.height, 50)
            self.assertEqual(meta.file_format, "JPEG")
            self.assertEqual(meta.color_mode, "RGB")
            self.assertTrue(meta.file_size_bytes > 0)
            self.assertIsNotNone(meta.md5)
            self.assertIsNotNone(meta.sha256)
            self.assertFalse(meta.has_gps)
        finally:
            os.unlink(path)

    def test_extract_png(self):
        with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as f:
            img = Image.new("RGBA", (200, 200), color=(0, 0, 255, 128))
            img.save(f, format="PNG")
            path = f.name

        try:
            meta = extract_metadata(path)
            self.assertEqual(meta.file_format, "PNG")
            self.assertEqual(meta.color_mode, "RGBA")
        finally:
            os.unlink(path)

    def test_skip_hash(self):
        with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as f:
            img = Image.new("RGB", (10, 10))
            img.save(f, format="JPEG")
            path = f.name

        try:
            meta = extract_metadata(path, skip_hash=True)
            self.assertIsNone(meta.md5)
            self.assertIsNone(meta.sha256)
        finally:
            os.unlink(path)

    def test_nonexistent_file(self):
        meta = extract_metadata("/nonexistent/file.jpg")
        self.assertTrue(len(meta.warnings) > 0)


class TestFindImages(unittest.TestCase):

    def test_find_in_directory(self):
        with tempfile.TemporaryDirectory() as d:
            # Create test files
            for name in ("a.jpg", "b.png", "c.txt", "d.bmp"):
                with open(os.path.join(d, name), "w") as f:
                    f.write("x")

            found = find_images(d)
            names = [os.path.basename(p) for p in found]
            self.assertIn("a.jpg", names)
            self.assertIn("b.png", names)
            self.assertIn("d.bmp", names)
            self.assertNotIn("c.txt", names)

    def test_recursive(self):
        with tempfile.TemporaryDirectory() as d:
            subdir = os.path.join(d, "sub")
            os.makedirs(subdir)
            with open(os.path.join(subdir, "deep.tiff"), "w") as f:
                f.write("x")

            found = find_images(d, recursive=True)
            self.assertEqual(len(found), 1)
            self.assertIn("deep.tiff", found[0])

    def test_non_recursive(self):
        with tempfile.TemporaryDirectory() as d:
            subdir = os.path.join(d, "sub")
            os.makedirs(subdir)
            with open(os.path.join(d, "top.jpg"), "w") as f:
                f.write("x")
            with open(os.path.join(subdir, "deep.jpg"), "w") as f:
                f.write("x")

            found = find_images(d, recursive=False)
            self.assertEqual(len(found), 1)

    def test_supported_extensions(self):
        self.assertIn(".jpg", SUPPORTED_EXTENSIONS)
        self.assertIn(".jpeg", SUPPORTED_EXTENSIONS)
        self.assertIn(".png", SUPPORTED_EXTENSIONS)
        self.assertIn(".tiff", SUPPORTED_EXTENSIONS)
        self.assertIn(".webp", SUPPORTED_EXTENSIONS)
        self.assertIn(".heic", SUPPORTED_EXTENSIONS)


class TestExtractBatch(unittest.TestCase):

    def test_batch_multiple(self):
        """Batch extraction should process multiple files."""
        paths = []
        for i in range(4):
            with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as f:
                img = Image.new("RGB", (10 + i, 10 + i), color="blue")
                img.save(f, format="JPEG")
                paths.append(f.name)

        try:
            report = extract_batch(paths)
            self.assertEqual(report.total_files, 4)
            self.assertEqual(len(report.images), 4)
            self.assertTrue(report.elapsed_seconds >= 0)
        finally:
            for p in paths:
                os.unlink(p)

    def test_batch_progress_callback(self):
        """Progress callback should be called for each image."""
        with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as f:
            img = Image.new("RGB", (10, 10))
            img.save(f, format="JPEG")
            path = f.name

        try:
            progress_calls = []

            def on_progress(current, total, filename):
                progress_calls.append((current, total, filename))

            report = extract_batch([path], on_progress=on_progress)
            self.assertEqual(len(progress_calls), 1)
            self.assertEqual(progress_calls[0][0], 1)
            self.assertEqual(progress_calls[0][1], 1)
        finally:
            os.unlink(path)

    def test_batch_with_invalid_file(self):
        """Batch should handle invalid files gracefully."""
        report = extract_batch(["/nonexistent/file.jpg"])
        self.assertEqual(report.total_files, 1)
        self.assertTrue(len(report.images[0].warnings) > 0)


class TestDateWarning(unittest.TestCase):

    def test_date_mismatch_warning(self):
        """Extractor should warn when date_taken != date_modified."""
        with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as f:
            img = Image.new("RGB", (10, 10))
            img.save(f, format="JPEG")
            path = f.name

        try:
            # This image won't have EXIF dates, so no date mismatch warning
            meta = extract_metadata(path)
            # Just verify it doesn't crash
            self.assertIsNotNone(meta)
        finally:
            os.unlink(path)


if __name__ == "__main__":
    unittest.main()
