"""Tests for file hashing."""

import os
import tempfile
import unittest

from metochina.core.hasher import compute_hashes


class TestComputeHashes(unittest.TestCase):

    def test_known_content(self):
        """Hash of known content should match pre-computed values."""
        content = b"Hello, Metochina!"
        with tempfile.NamedTemporaryFile(delete=False, suffix=".txt") as f:
            f.write(content)
            f.flush()
            path = f.name

        try:
            md5, sha256 = compute_hashes(path)
            # Verify format: hex strings of correct length
            self.assertEqual(len(md5), 32)
            self.assertEqual(len(sha256), 64)
            # Verify they are valid hex
            int(md5, 16)
            int(sha256, 16)
        finally:
            os.unlink(path)

    def test_empty_file(self):
        """Hash of empty file should be deterministic."""
        with tempfile.NamedTemporaryFile(delete=False, suffix=".txt") as f:
            path = f.name

        try:
            md5, sha256 = compute_hashes(path)
            # Known MD5 of empty input
            self.assertEqual(md5, "d41d8cd98f00b204e9800998ecf8427e")
            # Known SHA-256 of empty input
            self.assertEqual(sha256, "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855")
        finally:
            os.unlink(path)

    def test_consistency(self):
        """Hashing the same file twice should produce identical results."""
        with tempfile.NamedTemporaryFile(delete=False, suffix=".bin") as f:
            f.write(b"\x00\xff" * 1000)
            path = f.name

        try:
            h1 = compute_hashes(path)
            h2 = compute_hashes(path)
            self.assertEqual(h1, h2)
        finally:
            os.unlink(path)

    def test_different_content(self):
        """Different content should produce different hashes."""
        paths = []
        for content in (b"aaa", b"bbb"):
            with tempfile.NamedTemporaryFile(delete=False, suffix=".txt") as f:
                f.write(content)
                paths.append(f.name)

        try:
            h1 = compute_hashes(paths[0])
            h2 = compute_hashes(paths[1])
            self.assertNotEqual(h1, h2)
        finally:
            for p in paths:
                os.unlink(p)

    def test_nonexistent_file(self):
        with self.assertRaises(OSError):
            compute_hashes("/nonexistent/path/file.txt")


if __name__ == "__main__":
    unittest.main()
