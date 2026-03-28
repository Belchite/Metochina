"""Tests for the display and effects modules."""

import io
import sys
import unittest
from unittest.mock import patch

from metochina.ui.display import (
    box_bottom,
    box_divider,
    box_empty,
    box_line,
    box_top,
    score_bar,
)
from metochina.ui.effects import progress_bar


class TestBoxDrawing(unittest.TestCase):

    def test_box_top(self):
        top = box_top(30)
        self.assertIn("┌", top)
        self.assertIn("┐", top)

    def test_box_bottom(self):
        bottom = box_bottom(30)
        self.assertIn("└", bottom)
        self.assertIn("┘", bottom)

    def test_box_divider(self):
        div = box_divider(30)
        self.assertIn("├", div)
        self.assertIn("┤", div)

    def test_box_line(self):
        line = box_line("test content", 30)
        self.assertIn("│", line)
        self.assertIn("test content", line)

    def test_box_empty(self):
        empty = box_empty(30)
        self.assertIn("│", empty)


class TestScoreBar(unittest.TestCase):

    def test_score_zero(self):
        bar = score_bar(0)
        self.assertIn("0/100", bar)

    def test_score_100(self):
        bar = score_bar(100)
        self.assertIn("100/100", bar)

    def test_score_50(self):
        bar = score_bar(50)
        self.assertIn("50/100", bar)


class TestProgressBar(unittest.TestCase):

    def test_progress_0(self):
        bar = progress_bar(0, 100)
        self.assertIn("0%", bar)

    def test_progress_50(self):
        bar = progress_bar(50, 100)
        self.assertIn("50%", bar)

    def test_progress_100(self):
        bar = progress_bar(100, 100)
        self.assertIn("100%", bar)

    def test_progress_with_prefix(self):
        bar = progress_bar(5, 10, prefix="Test")
        self.assertIn("Test", bar)


class TestDisplayFunctions(unittest.TestCase):

    def test_info_no_crash(self):
        from metochina.ui.display import info
        with patch("sys.stdout", new_callable=io.StringIO) as mock_out:
            info("test message")
            self.assertIn("test message", mock_out.getvalue())

    def test_success_no_crash(self):
        from metochina.ui.display import success
        with patch("sys.stdout", new_callable=io.StringIO) as mock_out:
            success("ok")
            self.assertIn("ok", mock_out.getvalue())

    def test_error_no_crash(self):
        from metochina.ui.display import error
        with patch("sys.stdout", new_callable=io.StringIO) as mock_out:
            error("fail")
            self.assertIn("fail", mock_out.getvalue())

    def test_warning_no_crash(self):
        from metochina.ui.display import warning
        with patch("sys.stdout", new_callable=io.StringIO) as mock_out:
            warning("watch out")
            self.assertIn("watch out", mock_out.getvalue())

    def test_section_box_no_crash(self):
        from metochina.ui.display import section_box
        with patch("sys.stdout", new_callable=io.StringIO) as mock_out:
            section_box("TITLE", [(">", "Key", "Value"), ("+", "Key2", "Val2")])
            output = mock_out.getvalue()
            self.assertIn("TITLE", output)
            self.assertIn("Key", output)

    def test_menu_box_no_crash(self):
        from metochina.ui.display import menu_box
        with patch("sys.stdout", new_callable=io.StringIO) as mock_out:
            menu_box("MENU", [("1", "Option", "Desc"), ("0", "Exit", "")])
            output = mock_out.getvalue()
            self.assertIn("MENU", output)
            self.assertIn("Option", output)


class TestEffects(unittest.TestCase):

    def test_spinner_no_crash(self):
        from metochina.ui.effects import spinner
        with patch("sys.stdout", new_callable=io.StringIO):
            with patch("time.sleep"):
                spinner("test", duration=0.01)

    def test_pause_no_crash(self):
        from metochina.ui.effects import pause
        with patch("builtins.input", return_value=""):
            pause()

    def test_clear_line(self):
        from metochina.ui.effects import clear_line
        with patch("sys.stdout", new_callable=io.StringIO):
            clear_line()


if __name__ == "__main__":
    unittest.main()
