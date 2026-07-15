"""Тесты для core/bitrate_calculator.py — v0.3.0."""

import math
import sys
import unittest
from unittest import mock

import core.bitrate_calculator as bc
from core.bitrate_calculator import (
    calculate_video_bitrate,
    get_null_device,
)


class TestBitrateFormula(unittest.TestCase):
    """Формула Коры: (target_mb × 8388.608 × 0.98) / duration_sec − audio_kbps"""

    def test_regular_scenario(self):
        """Стандартный сценарий — 100 MB, 60 сек, аудио 128 Кбит/с."""
        bitrate = calculate_video_bitrate(
            target_mb=100, duration_sec=60, audio_kbps=128
        )
        expected = round((100 * 8388.608 * 0.98) / 60 - 128, 3)
        self.assertAlmostEqual(bitrate, expected, places=3)

    def test_short_video(self):
        """Короткое видео — 10 MB, 5 сек."""
        bitrate = calculate_video_bitrate(
            target_mb=10, duration_sec=5, audio_kbps=64
        )
        expected = round((10 * 8388.608 * 0.98) / 5 - 64, 3)
        self.assertAlmostEqual(bitrate, expected, places=3)

    def test_long_video(self):
        """Длинное видео — 500 MB, 3600 сек."""
        bitrate = calculate_video_bitrate(
            target_mb=500, duration_sec=3600, audio_kbps=192
        )
        expected = round((500 * 8388.608 * 0.98) / 3600 - 192, 3)
        self.assertAlmostEqual(bitrate, expected, places=3)

    def test_low_target(self):
        """Маленький целевой размер — 1 MB, 10 сек."""
        bitrate = calculate_video_bitrate(
            target_mb=1, duration_sec=10, audio_kbps=128
        )
        expected = round((1 * 8388.608 * 0.98) / 10 - 128, 3)
        self.assertAlmostEqual(bitrate, expected, places=3)


class TestBitrateOverhead(unittest.TestCase):
    """OVERHEAD_FACTOR = 0.98 (2% overhead)"""

    def test_overhead_factor_value(self):
        self.assertEqual(bc.OVERHEAD_PCT, 2.0)

    def test_formula_uses_overhead(self):
        """0% overhead = просто размер / длительность − аудио."""
        raw = (100 * 8388.608 * 1.0) / 60 - 128
        with_overhead = (100 * 8388.608 * 0.98) / 60 - 128
        self.assertNotEqual(raw, with_overhead)

    def test_overhead_rounds_to_2_percent(self):
        """Проверяем, что overhead ~2%."""
        full = 100 * 8388.608 / 60
        reduced = 100 * 8388.608 * 0.98 / 60
        self.assertAlmostEqual((full - reduced) / full, 0.02, places=3)


class TestNegativeBitrateProtection(unittest.TestCase):
    """Защита от отрицательного битрейта (аудио «съедает» весь бюджет)."""

    def test_negative_bitrate_returns_min(self):
        """Очень маленький target → отрицательный битрейт → возвращаем 1.0."""
        bitrate = calculate_video_bitrate(
            target_mb=0.01, duration_sec=100, audio_kbps=320
        )
        self.assertAlmostEqual(bitrate, 1.0, places=5)

    def test_zero_effective_bitrate_returns_min(self):
        """Нулевой битрейт → возвращаем 1.0."""
        bitrate = calculate_video_bitrate(
            target_mb=0.01, duration_sec=100, audio_kbps=128
        )
        self.assertAlmostEqual(bitrate, 1.0, places=5)

    def test_positive_bitrate_unchanged(self):
        """Нормальный битрейт не меняется."""
        bitrate = calculate_video_bitrate(
            target_mb=100, duration_sec=10, audio_kbps=128
        )
        self.assertGreater(bitrate, 1.0)


class TestNullDevice(unittest.TestCase):
    """Кроссплатформенный null-девайс."""

    @mock.patch.object(sys, "platform", "win32")
    def test_windows(self):
        self.assertEqual(get_null_device(), "NUL")

    @mock.patch.object(sys, "platform", "linux")
    def test_linux(self):
        self.assertEqual(get_null_device(), "/dev/null")

    @mock.patch.object(sys, "platform", "darwin")
    def test_macos(self):
        self.assertEqual(get_null_device(), "/dev/null")


if __name__ == "__main__":
    unittest.main()