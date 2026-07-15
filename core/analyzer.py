"""
Модуль анализа видео на основе ffprobe.

Использует core.ffmpeg для вызова ffprobe и парсит JSON-вывод,
чтобы ответить на вопросы о видеофайле.
"""

import json
from typing import Optional

from core.ffmpeg import run_ffprobe, FFprobeError


class VideoAnalyzer:
    """
    Анализатор видеофайла. Лениво вызывает ffprobe при первом запросе.

    Использование:
        analyzer = VideoAnalyzer("/path/to/video.mp4")
        codec = analyzer.get_codec()       # "h264"
        fps = analyzer.get_fps()           # 29.97
        duration = analyzer.get_duration() # 125.5
        is_hdr = analyzer.has_hdr()        # False
    """

    def __init__(self, video_path: str):
        """
        Args:
            video_path: Путь к видеофайлу.
        """
        self._video_path = video_path
        self._probe_data: Optional[dict] = None

    # ── Приватные методы ──────────────────────────────

    def _ensure_probed(self) -> None:
        """Вызывает ffprobe один раз и кеширует результат."""
        if self._probe_data is not None:
            return

        result = run_ffprobe([
            "-v", "quiet",
            "-print_format", "json",
            "-show_format",
            "-show_streams",
            self._video_path,
        ])

        try:
            self._probe_data = json.loads(result.stdout)
        except json.JSONDecodeError:
            raise FFprobeError("ffprobe вернул невалидный JSON")

    def _get_video_stream(self) -> Optional[dict]:
        """Возвращает первый видеопоток или None."""
        self._ensure_probed()
        for stream in self._probe_data.get("streams", []):
            if stream.get("codec_type") == "video":
                return stream
        return None

    @staticmethod
    def _parse_fraction(frac_str: str) -> Optional[float]:
        """Парсит дробную строку '30000/1001' → 29.97. При ошибке возвращает None."""
        if not frac_str or "/" not in frac_str:
            return None
        try:
            num, den = frac_str.split("/", 1)
            return float(num) / float(den)
        except (ValueError, ZeroDivisionError):
            return None

    # ── Публичные методы ──────────────────────────────

    def get_codec(self) -> str:
        """
        Возвращает название видеокодека.
        Пример: 'h264', 'hevc', 'vp9'.
        Если видеопоток не найден — 'unknown'.
        """
        stream = self._get_video_stream()
        if stream is None:
            return "unknown"
        return stream.get("codec_name", "unknown")

    def get_fps(self) -> Optional[float]:
        """
        Возвращает FPS видео как float.
        Пример: 29.97, 60.0.
        Если не удалось определить — None.
        """
        stream = self._get_video_stream()
        if stream is None:
            return None
        r_frame_rate = stream.get("r_frame_rate", "")
        return self._parse_fraction(r_frame_rate)

    def get_duration(self) -> Optional[float]:
        """
        Возвращает длительность видео в секундах.
        Если не удалось определить — None.
        """
        self._ensure_probed()
        fmt = self._probe_data.get("format", {})
        duration_str = fmt.get("duration")
        if duration_str is None:
            return None
        try:
            return float(duration_str)
        except (ValueError, TypeError):
            return None

    def has_hdr(self) -> bool:
        """
        Проверяет, является ли видео HDR.
        Определяет по color_transfer видеопотока:
        'smpte2084' → HDR10 (PQ), 'arib-std-b67' → HLG.
        """
        stream = self._get_video_stream()
        if stream is None:
            return False
        color_transfer = stream.get("color_transfer", "")
        return color_transfer in ("smpte2084", "arib-std-b67")

    def has_subtitles(self) -> bool:
        """Проверяет наличие субтитров в файле."""
        self._ensure_probed()
        for stream in self._probe_data.get("streams", []):
            if stream.get("codec_type") == "subtitle":
                return True
        return False

    def get_audio_tracks_count(self) -> int:
        """Возвращает количество аудиодорожек."""
        self._ensure_probed()
        count = 0
        for stream in self._probe_data.get("streams", []):
            if stream.get("codec_type") == "audio":
                count += 1
        return count