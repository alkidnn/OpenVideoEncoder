"""
Юнит-тесты для core.encoder.VideoEncoder.

Проверяют правильность сборки аргументов командной строки FFmpeg
с использованием unittest.mock. Никаких реальных вызовов ffmpeg.
"""

import unittest
from unittest.mock import patch, MagicMock

from core.encoder import VideoEncoder


# ══════════════════════════════════════════════════════════════
# Хелпер
# ══════════════════════════════════════════════════════════════

def _mock_run_ffmpeg(returncode=0):
    """Создаёт мок для core.ffmpeg.run_ffmpeg."""
    mock = MagicMock()
    mock.return_value.returncode = returncode
    return mock


# ══════════════════════════════════════════════════════════════
# Тесты: сборка аргументов
# ══════════════════════════════════════════════════════════════

class TestEncoderArguments(unittest.TestCase):
    """Проверяет, что VideoEncoder.encode собирает правильные аргументы."""

    def setUp(self):
        self.encoder = VideoEncoder("input.mp4", "output.mp4")

    # ── Базовые аргументы ───────────────────────────

    @patch("core.encoder.run_ffmpeg")
    def test_default_args(self, mock_ffmpeg):
        """Со стандартным профилем собирает аргументы по умолчанию."""
        mock_ffmpeg.return_value.returncode = 0
        self.encoder.encode({})
        args = mock_ffmpeg.call_args[0][0]

        self.assertIn("-y", args)
        self.assertIn("-i", args)
        self.assertIn("input.mp4", args)
        self.assertIn("-c:v", args)
        self.assertIn("libx264", args)
        self.assertIn("-c:a", args)
        self.assertIn("aac", args)
        self.assertEqual(args[-1], "output.mp4")

    @patch("core.encoder.run_ffmpeg")
    def test_custom_codec(self, mock_ffmpeg):
        """Профиль с другим кодеком."""
        mock_ffmpeg.return_value.returncode = 0
        self.encoder.encode({"video": {"codec": "libx265"}})
        args = mock_ffmpeg.call_args[0][0]

        codec_idx = args.index("-c:v") + 1
        self.assertEqual(args[codec_idx], "libx265")

    @patch("core.encoder.run_ffmpeg")
    def test_custom_crf(self, mock_ffmpeg):
        """CRF из профиля попадает как строка."""
        mock_ffmpeg.return_value.returncode = 0
        self.encoder.encode({"video": {"crf": 28}})
        args = mock_ffmpeg.call_args[0][0]

        crf_idx = args.index("-crf") + 1
        self.assertEqual(args[crf_idx], "28")

    @patch("core.encoder.run_ffmpeg")
    def test_custom_preset(self, mock_ffmpeg):
        """Пресет из профиля."""
        mock_ffmpeg.return_value.returncode = 0
        self.encoder.encode({"video": {"preset": "fast"}})
        args = mock_ffmpeg.call_args[0][0]

        preset_idx = args.index("-preset") + 1
        self.assertEqual(args[preset_idx], "fast")

    @patch("core.encoder.run_ffmpeg")
    def test_audio_always_aac(self, mock_ffmpeg):
        """Даже если профиль пустой, аудио — aac."""
        mock_ffmpeg.return_value.returncode = 0
        self.encoder.encode({})
        args = mock_ffmpeg.call_args[0][0]

        aac_idx = args.index("-c:a") + 1
        self.assertEqual(args[aac_idx], "aac")

    # ── Ограничение размера файла (-fs) ─────────────

    @patch("core.encoder.run_ffmpeg")
    def test_max_size_mb_converts_to_bytes(self, mock_ffmpeg):
        """max_size_mb переводится в байты и добавляется как -fs."""
        mock_ffmpeg.return_value.returncode = 0
        self.encoder.encode({"limits": {"max_size_mb": 1900}})
        args = mock_ffmpeg.call_args[0][0]

        self.assertIn("-fs", args)
        fs_idx = args.index("-fs") + 1
        expected_bytes = 1900 * 1024 * 1024
        self.assertEqual(args[fs_idx], str(expected_bytes))

    @patch("core.encoder.run_ffmpeg")
    def test_max_size_zero_bytes(self, mock_ffmpeg):
        """max_size_mb = 0 → -fs 0."""
        mock_ffmpeg.return_value.returncode = 0
        self.encoder.encode({"limits": {"max_size_mb": 0}})
        args = mock_ffmpeg.call_args[0][0]

        self.assertIn("-fs", args)
        fs_idx = args.index("-fs") + 1
        self.assertEqual(args[fs_idx], "0")

    @patch("core.encoder.run_ffmpeg")
    def test_no_max_size_no_fs_flag(self, mock_ffmpeg):
        """Без max_size_mb флаг -fs отсутствует."""
        mock_ffmpeg.return_value.returncode = 0
        self.encoder.encode({})
        args = mock_ffmpeg.call_args[0][0]

        self.assertNotIn("-fs", args)

    @patch("core.encoder.run_ffmpeg")
    def test_max_size_fractional_mb(self, mock_ffmpeg):
        """Дробное значение max_size_mb (0.5 MB → 524288 bytes)."""
        mock_ffmpeg.return_value.returncode = 0
        self.encoder.encode({"limits": {"max_size_mb": 0.5}})
        args = mock_ffmpeg.call_args[0][0]

        self.assertIn("-fs", args)
        fs_idx = args.index("-fs") + 1
        expected_bytes = int(0.5 * 1024 * 1024)
        self.assertEqual(args[fs_idx], str(expected_bytes))

    @patch("core.encoder.run_ffmpeg")
    def test_full_profile_all_keys(self, mock_ffmpeg):
        """Все ключи профиля вместе."""
        mock_ffmpeg.return_value.returncode = 0
        profile = {
            "video": {"codec": "libx265", "crf": 26, "preset": "slow"},
            "limits": {"max_size_mb": 1900},
        }
        self.encoder.encode(profile)
        args = mock_ffmpeg.call_args[0][0]

        # codec
        self.assertEqual(args[args.index("-c:v") + 1], "libx265")
        # crf
        self.assertEqual(args[args.index("-crf") + 1], "26")
        # preset
        self.assertEqual(args[args.index("-preset") + 1], "slow")
        # max_size
        fs_idx = args.index("-fs") + 1
        self.assertEqual(args[fs_idx], str(1900 * 1024 * 1024))
        # output
        self.assertEqual(args[-1], "output.mp4")

    # ── Порядок аргументов ──────────────────────────

    @patch("core.encoder.run_ffmpeg")
    def test_output_is_last_argument(self, mock_ffmpeg):
        """Путь для сохранения всегда последний аргумент."""
        mock_ffmpeg.return_value.returncode = 0
        self.encoder.encode({"max_size_mb": 1900})
        args = mock_ffmpeg.call_args[0][0]

        self.assertEqual(args[-1], "output.mp4")

    @patch("core.encoder.run_ffmpeg")
    def test_input_after_i_flag(self, mock_ffmpeg):
        """Исходный файл идёт после -i."""
        mock_ffmpeg.return_value.returncode = 0
        self.encoder.encode({})
        args = mock_ffmpeg.call_args[0][0]

        input_idx = args.index("-i") + 1
        self.assertEqual(args[input_idx], "input.mp4")

    @patch("core.encoder.run_ffmpeg")
    def test_overwrite_flag_present(self, mock_ffmpeg):
        """Флаг -y (перезапись) всегда присутствует."""
        mock_ffmpeg.return_value.returncode = 0
        self.encoder.encode({})
        args = mock_ffmpeg.call_args[0][0]

        self.assertIn("-y", args)


# ══════════════════════════════════════════════════════════════
# Тесты: возвращаемое значение
# ══════════════════════════════════════════════════════════════

class TestEncoderReturnValue(unittest.TestCase):
    """Проверяет, что encode возвращает корректный bool."""

    def setUp(self):
        self.encoder = VideoEncoder("input.mp4", "output.mp4")

    @patch("core.encoder.run_ffmpeg")
    def test_success_returns_true(self, mock_ffmpeg):
        """returncode 0 → True."""
        mock_ffmpeg.return_value.returncode = 0
        result = self.encoder.encode({})
        self.assertTrue(result)

    @patch("core.encoder.run_ffmpeg")
    def test_failure_returns_false(self, mock_ffmpeg):
        """returncode != 0 → False."""
        mock_ffmpeg.return_value.returncode = 1
        result = self.encoder.encode({})
        self.assertFalse(result)


# ══════════════════════════════════════════════════════════════
# Тесты: конструктор
# ══════════════════════════════════════════════════════════════

class TestEncoderInit(unittest.TestCase):
    """Проверяет, что VideoEncoder корректно сохраняет пути."""

    def test_source_and_output_stored(self):
        encoder = VideoEncoder("a.mp4", "b.mp4")
        self.assertEqual(encoder._source, "a.mp4")
        self.assertEqual(encoder._output, "b.mp4")

    @patch("core.encoder.run_ffmpeg")
    def test_source_used_in_args(self, mock_ffmpeg):
        """Разные source попадают в аргументы."""
        mock_ffmpeg.return_value.returncode = 0
        encoder = VideoEncoder("my_video.mkv", "out.mp4")
        encoder.encode({})
        args = mock_ffmpeg.call_args[0][0]
        self.assertIn("my_video.mkv", args)

    @patch("core.encoder.run_ffmpeg")
    def test_output_used_in_args(self, mock_ffmpeg):
        """Разные output попадают в аргументы."""
        mock_ffmpeg.return_value.returncode = 0
        encoder = VideoEncoder("in.mp4", "encoded.mkv")
        encoder.encode({})
        args = mock_ffmpeg.call_args[0][0]
        self.assertEqual(args[-1], "encoded.mkv")