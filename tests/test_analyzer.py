"""
Юнит-тесты для модуля core.analyzer (VideoAnalyzer).

Использует встроенный unittest. Не требует установки ffmpeg/ffprobe —
вызовы run_ffprobe замоканы.
"""

import json
import sys
import os
import unittest
from unittest.mock import patch

# Путь к проекту для импорта core/
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from core.analyzer import VideoAnalyzer
from core.ffmpeg import FFprobeError


# ═══════════════════════════════════════════════════════════
# Хелперы
# ═══════════════════════════════════════════════════════════

def _ffprobe_output(*, codec="h264", fps_frac="30000/1001",
                     duration="125.5", color_transfer="bt709",
                     has_subtitles=False, audio_tracks=1) -> str:
    """Генерирует валидный JSON-вывод ffprobe для моков."""
    streams = [
        {
            "codec_type": "video",
            "codec_name": codec,
            "r_frame_rate": fps_frac,
            "color_transfer": color_transfer,
        }
    ]

    for _ in range(audio_tracks):
        streams.append({"codec_type": "audio"})

    if has_subtitles:
        streams.append({"codec_type": "subtitle"})

    probe = {
        "streams": streams,
        "format": {"duration": duration},
    }
    return json.dumps(probe)


def _mock_result(stdout: str, returncode: int = 0, stderr: str = ""):
    """Создаёт поддельный CompletedProcess."""
    result = unittest.mock.MagicMock()
    result.stdout = stdout
    result.stderr = stderr
    result.returncode = returncode
    return result


# ═══════════════════════════════════════════════════════════
# Тесты VideoAnalyzer
# ═══════════════════════════════════════════════════════════

class TestGetCodec(unittest.TestCase):

    @patch("core.analyzer.run_ffprobe")
    def test_h264_codec(self, mock_ffprobe):
        mock_ffprobe.return_value = _mock_result(
            _ffprobe_output(codec="h264")
        )
        analyzer = VideoAnalyzer("video.mp4")
        self.assertEqual(analyzer.get_codec(), "h264")

    @patch("core.analyzer.run_ffprobe")
    def test_hevc_codec(self, mock_ffprobe):
        mock_ffprobe.return_value = _mock_result(
            _ffprobe_output(codec="hevc")
        )
        analyzer = VideoAnalyzer("video.mkv")
        self.assertEqual(analyzer.get_codec(), "hevc")

    @patch("core.analyzer.run_ffprobe")
    def test_no_video_stream_returns_unknown(self, mock_ffprobe):
        """Файл без видеопотока (например, чистый аудио)."""
        data = {
            "streams": [{"codec_type": "audio"}],
            "format": {"duration": "10.0"},
        }
        mock_ffprobe.return_value = _mock_result(json.dumps(data))
        analyzer = VideoAnalyzer("audio.aac")
        self.assertEqual(analyzer.get_codec(), "unknown")


class TestGetFps(unittest.TestCase):

    @patch("core.analyzer.run_ffprobe")
    def test_standard_fps(self, mock_ffprobe):
        mock_ffprobe.return_value = _mock_result(
            _ffprobe_output(fps_frac="30000/1001")
        )
        analyzer = VideoAnalyzer("video.mp4")
        self.assertAlmostEqual(analyzer.get_fps(), 29.97, places=2)

    @patch("core.analyzer.run_ffprobe")
    def test_exact_fps(self, mock_ffprobe):
        mock_ffprobe.return_value = _mock_result(
            _ffprobe_output(fps_frac="60/1")
        )
        analyzer = VideoAnalyzer("video.mp4")
        self.assertEqual(analyzer.get_fps(), 60.0)

    @patch("core.analyzer.run_ffprobe")
    def test_no_video_stream_fps_none(self, mock_ffprobe):
        data = {
            "streams": [{"codec_type": "audio"}],
            "format": {"duration": "10.0"},
        }
        mock_ffprobe.return_value = _mock_result(json.dumps(data))
        analyzer = VideoAnalyzer("audio.aac")
        self.assertIsNone(analyzer.get_fps())

    @patch("core.analyzer.run_ffprobe")
    def test_empty_fps_string(self, mock_ffprobe):
        mock_ffprobe.return_value = _mock_result(
            _ffprobe_output(fps_frac="")
        )
        analyzer = VideoAnalyzer("video.mp4")
        self.assertIsNone(analyzer.get_fps())


class TestGetDuration(unittest.TestCase):

    @patch("core.analyzer.run_ffprobe")
    def test_standard_duration(self, mock_ffprobe):
        mock_ffprobe.return_value = _mock_result(
            _ffprobe_output(duration="125.5")
        )
        analyzer = VideoAnalyzer("video.mp4")
        self.assertEqual(analyzer.get_duration(), 125.5)

    @patch("core.analyzer.run_ffprobe")
    def test_zero_duration(self, mock_ffprobe):
        mock_ffprobe.return_value = _mock_result(
            _ffprobe_output(duration="0.0")
        )
        analyzer = VideoAnalyzer("empty.mp4")
        self.assertEqual(analyzer.get_duration(), 0.0)

    @patch("core.analyzer.run_ffprobe")
    def test_missing_duration(self, mock_ffprobe):
        data = {
            "streams": [{"codec_type": "video", "codec_name": "h264"}],
            "format": {},
        }
        mock_ffprobe.return_value = _mock_result(json.dumps(data))
        analyzer = VideoAnalyzer("live.mp4")
        self.assertIsNone(analyzer.get_duration())


class TestHasHdr(unittest.TestCase):

    @patch("core.analyzer.run_ffprobe")
    def test_sdr_video(self, mock_ffprobe):
        mock_ffprobe.return_value = _mock_result(
            _ffprobe_output(color_transfer="bt709")
        )
        analyzer = VideoAnalyzer("sdr.mp4")
        self.assertFalse(analyzer.has_hdr())

    @patch("core.analyzer.run_ffprobe")
    def test_hdr10_video(self, mock_ffprobe):
        mock_ffprobe.return_value = _mock_result(
            _ffprobe_output(color_transfer="smpte2084")
        )
        analyzer = VideoAnalyzer("hdr10.mp4")
        self.assertTrue(analyzer.has_hdr())

    @patch("core.analyzer.run_ffprobe")
    def test_hlg_video(self, mock_ffprobe):
        mock_ffprobe.return_value = _mock_result(
            _ffprobe_output(color_transfer="arib-std-b67")
        )
        analyzer = VideoAnalyzer("hlg.mp4")
        self.assertTrue(analyzer.has_hdr())

    @patch("core.analyzer.run_ffprobe")
    def test_no_video_stream_hdr_false(self, mock_ffprobe):
        data = {
            "streams": [{"codec_type": "audio"}],
            "format": {"duration": "10.0"},
        }
        mock_ffprobe.return_value = _mock_result(json.dumps(data))
        analyzer = VideoAnalyzer("audio.aac")
        self.assertFalse(analyzer.has_hdr())


class TestHasSubtitles(unittest.TestCase):

    @patch("core.analyzer.run_ffprobe")
    def test_no_subtitles(self, mock_ffprobe):
        mock_ffprobe.return_value = _mock_result(_ffprobe_output(has_subtitles=False))
        analyzer = VideoAnalyzer("video.mp4")
        self.assertFalse(analyzer.has_subtitles())

    @patch("core.analyzer.run_ffprobe")
    def test_with_subtitles(self, mock_ffprobe):
        mock_ffprobe.return_value = _mock_result(_ffprobe_output(has_subtitles=True))
        analyzer = VideoAnalyzer("video.mkv")
        self.assertTrue(analyzer.has_subtitles())


class TestGetAudioTracksCount(unittest.TestCase):

    @patch("core.analyzer.run_ffprobe")
    def test_one_audio_track(self, mock_ffprobe):
        mock_ffprobe.return_value = _mock_result(_ffprobe_output(audio_tracks=1))
        analyzer = VideoAnalyzer("video.mp4")
        self.assertEqual(analyzer.get_audio_tracks_count(), 1)

    @patch("core.analyzer.run_ffprobe")
    def test_multiple_audio_tracks(self, mock_ffprobe):
        mock_ffprobe.return_value = _mock_result(_ffprobe_output(audio_tracks=3))
        analyzer = VideoAnalyzer("video.mkv")
        self.assertEqual(analyzer.get_audio_tracks_count(), 3)

    @patch("core.analyzer.run_ffprobe")
    def test_no_audio_tracks(self, mock_ffprobe):
        mock_ffprobe.return_value = _mock_result(_ffprobe_output(audio_tracks=0))
        analyzer = VideoAnalyzer("silent.mp4")
        self.assertEqual(analyzer.get_audio_tracks_count(), 0)


class TestLazyProbing(unittest.TestCase):

    @patch("core.analyzer.run_ffprobe")
    def test_ffprobe_called_only_once(self, mock_ffprobe):
        mock_ffprobe.return_value = _mock_result(_ffprobe_output())
        analyzer = VideoAnalyzer("video.mp4")

        analyzer.get_codec()
        analyzer.get_fps()
        analyzer.get_duration()

        self.assertEqual(mock_ffprobe.call_count, 1)

    @patch("core.analyzer.run_ffprobe")
    def test_no_ffprobe_until_used(self, mock_ffprobe):
        analyzer = VideoAnalyzer("video.mp4")
        # Создание объекта не должно вызывать ffprobe
        mock_ffprobe.assert_not_called()


class TestErrorHandling(unittest.TestCase):

    @patch("core.analyzer.run_ffprobe")
    def test_invalid_json_raises_ffprobe_error(self, mock_ffprobe):
        mock_ffprobe.return_value = _mock_result("not valid json {{{")
        analyzer = VideoAnalyzer("broken.mp4")
        with self.assertRaises(FFprobeError):
            analyzer.get_codec()

    @patch("core.analyzer.run_ffprobe")
    def test_ffprobe_error_propagates(self, mock_ffprobe):
        mock_ffprobe.side_effect = FFprobeError("файл повреждён")
        analyzer = VideoAnalyzer("corrupt.mp4")
        with self.assertRaises(FFprobeError):
            analyzer.get_codec()