"""Tests for the banner module."""

import io
import sys
import unittest
from unittest.mock import patch

from metochina.ui.banner import ALL_BANNERS as BANNERS, get_random_banner, print_banner


class TestBanners(unittest.TestCase):

    def test_banners_exist(self):
        """At least 4 banner variants should be defined."""
        self.assertGreaterEqual(len(BANNERS), 4)

    def test_banners_are_strings(self):
        for i, b in enumerate(BANNERS):
            self.assertIsInstance(b, str, f"Banner {i} is not a string")

    def test_banners_are_multiline(self):
        for i, b in enumerate(BANNERS):
            lines = b.strip().split("\n")
            self.assertGreaterEqual(len(lines), 4, f"Banner {i} has too few lines")

    def test_get_random_banner(self):
        banner = get_random_banner()
        self.assertIn(banner, BANNERS)

    def test_get_random_banner_returns_string(self):
        self.assertIsInstance(get_random_banner(), str)

    def test_print_banner_no_crash(self):
        """print_banner should not raise."""
        with patch("sys.stdout", new_callable=io.StringIO):
            print_banner(version="1.2.0", author="Test")


class TestStartupSequence(unittest.TestCase):

    def test_startup_no_crash(self):
        """print_startup_sequence should not raise."""
        from metochina.ui.banner import print_startup_sequence
        with patch("sys.stdout", new_callable=io.StringIO):
            with patch("time.sleep"):  # skip delays
                print_startup_sequence()


if __name__ == "__main__":
    unittest.main()
