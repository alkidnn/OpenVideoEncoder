"""
Тесты для gui/settings.py.
Проверяет наличие и типы всех стилевых констант.
"""

import sys
import os
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from gui import settings


class TestWindowConstants(unittest.TestCase):
    """Константы окна."""

    def test_title_is_non_empty_string(self):
        self.assertIsInstance(settings.WINDOW_TITLE, str)
        self.assertGreater(len(settings.WINDOW_TITLE), 0)

    def test_width_positive_int(self):
        self.assertIsInstance(settings.WINDOW_WIDTH, int)
        self.assertGreater(settings.WINDOW_WIDTH, 0)

    def test_height_positive_int(self):
        self.assertIsInstance(settings.WINDOW_HEIGHT, int)
        self.assertGreater(settings.WINDOW_HEIGHT, 0)

    def test_min_width_positive_int(self):
        self.assertIsInstance(settings.WINDOW_MIN_WIDTH, int)
        self.assertGreater(settings.WINDOW_MIN_WIDTH, 0)

    def test_min_height_positive_int(self):
        self.assertIsInstance(settings.WINDOW_MIN_HEIGHT, int)
        self.assertGreater(settings.WINDOW_MIN_HEIGHT, 0)

    def test_min_dimensions_not_larger_than_window(self):
        self.assertLessEqual(settings.WINDOW_MIN_WIDTH, settings.WINDOW_WIDTH)
        self.assertLessEqual(settings.WINDOW_MIN_HEIGHT, settings.WINDOW_HEIGHT)


class TestColors(unittest.TestCase):
    """Цветовые константы."""

    def test_all_colors_are_hex_strings(self):
        for attr in ("BG_COLOR", "FG_COLOR", "ACCENT_COLOR",
                     "ERROR_COLOR", "SUCCESS_COLOR"):
            with self.subTest(attr=attr):
                val = getattr(settings, attr)
                self.assertIsInstance(val, str)
                self.assertTrue(
                    val.startswith("#") and len(val) == 7,
                    f"{attr}={val!r} должен быть hex-цветом вида #rrggbb"
                )

    def test_no_duplicate_colors(self):
        """Все пять цветов должны быть разными — иначе дизайн теряет смысл."""
        colors = {
            settings.BG_COLOR,
            settings.FG_COLOR,
            settings.ACCENT_COLOR,
            settings.ERROR_COLOR,
            settings.SUCCESS_COLOR,
        }
        self.assertEqual(len(colors), 5)


class TestFonts(unittest.TestCase):
    """Шрифтовые константы."""

    def test_family_is_non_empty_string(self):
        self.assertIsInstance(settings.FONT_FAMILY, str)
        self.assertGreater(len(settings.FONT_FAMILY), 0)

    def test_sizes_are_positive_ints(self):
        for attr in ("FONT_SIZE_LARGE", "FONT_SIZE_NORMAL", "FONT_SIZE_SMALL"):
            with self.subTest(attr=attr):
                val = getattr(settings, attr)
                self.assertIsInstance(val, int)
                self.assertGreater(val, 0)

    def test_sizes_are_in_descending_order(self):
        self.assertGreater(settings.FONT_SIZE_LARGE, settings.FONT_SIZE_NORMAL)
        self.assertGreater(settings.FONT_SIZE_NORMAL, settings.FONT_SIZE_SMALL)


class TestPads(unittest.TestCase):
    """Константы отступов."""

    def test_pads_are_positive_ints(self):
        for attr in ("PAD_LARGE", "PAD_NORMAL", "PAD_SMALL"):
            with self.subTest(attr=attr):
                val = getattr(settings, attr)
                self.assertIsInstance(val, int)
                self.assertGreater(val, 0)

    def test_pads_are_in_descending_order(self):
        self.assertGreater(settings.PAD_LARGE, settings.PAD_NORMAL)
        self.assertGreater(settings.PAD_NORMAL, settings.PAD_SMALL)


class TestModuleDocstring(unittest.TestCase):
    """Документирование модуля."""

    def test_has_docstring(self):
        self.assertIsNotNone(settings.__doc__)
        self.assertGreater(len(settings.__doc__.strip()), 0)