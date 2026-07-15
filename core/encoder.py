"""
Кодировщик видео на базе FFmpeg — v0.3.0.

Поддерживает однопроходное (CRF) и двухпроходное (target bitrate) кодирование.
Все параметры читаются из структурированного профиля (video / audio / limits).
"""

import glob
import os
from typing import Callable, Optional

from core.ffmpeg import run_ffmpeg


class VideoEncoder:
    """
    Принимает исходный файл и путь для сохранения, кодирует по профилю.

    Использование (однопроходное):
        encoder = VideoEncoder("input.mp4", "output.mp4")
        success = encoder.encode({
            "video": {"codec": "libx265", "crf": 28, "preset": "medium"},
            "audio": {"codec": "aac", "sample_rate": 48000},
        })

    Использование (двухпроходное):
        success = encoder.encode_two_pass(profile, duration_seconds=125.5)
    """

    def __init__(self, source: str, output: str):
        self._source = source
        self._output = output

    # ── Приватные хелперы сборки аргументов ──────────

    @staticmethod
    def _build_video_args(video: dict, for_two_pass: bool = False) -> list[str]:
        """Собирает видео-аргументы FFmpeg из секции video профиля."""
        args: list[str] = []
        codec = video.get("codec", "libx264")
        args.extend(["-c:v", codec])

        if not for_two_pass:
            crf = video.get("crf")
            if crf is not None:
                args.extend(["-crf", str(crf)])

        preset = video.get("preset")
        if preset:
            args.extend(["-preset", preset])

        profile = video.get("profile")
        if profile:
            args.extend(["-profile:v", str(profile)])

        gop = video.get("gop")
        if gop is not None:
            args.extend(["-g", str(gop)])

        bf = video.get("bf")
        if bf is not None:
            args.extend(["-bf", str(bf)])

        color_primaries = video.get("color_primaries")
        if color_primaries:
            args.extend(["-color_primaries", color_primaries])

        color_trc = video.get("color_trc")
        if color_trc:
            args.extend(["-color_trc", color_trc])

        color_space = video.get("color_space")
        if color_space:
            args.extend(["-colorspace", color_space])

        return args

    @staticmethod
    def _build_audio_args(audio: dict) -> list[str]:
        """Собирает аудио-аргументы FFmpeg из секции audio профиля."""
        args: list[str] = []
        codec = audio.get("codec", "aac")
        args.extend(["-c:a", codec])

        sample_rate = audio.get("sample_rate")
        if sample_rate is not None:
            args.extend(["-ar", str(sample_rate)])

        return args

    @staticmethod
    def _build_limits_args(limits: dict) -> list[str]:
        """Собирает аргументы ограничений (макс. размер и т.д.)."""
        args: list[str] = []
        max_size_mb = limits.get("max_size_mb")
        if max_size_mb is not None:
            max_size_bytes = int(max_size_mb * 1024 * 1024)
            args.extend(["-fs", str(max_size_bytes)])
        return args

    @staticmethod
    def _cleanup_passlogs(passlogfile: str) -> None:
        """Удаляет временные файлы логов двухпроходного кодирования."""
        for f in glob.glob(f"{passlogfile}*"):
            try:
                os.remove(f)
            except OSError:
                pass

    # ── Публичные методы ─────────────────────────────

    def encode(self, profile: dict) -> bool:
        """
        Однопроходное CRF-кодирование.

        Returns:
            True, если returncode == 0, иначе False.
        """
        video = profile.get("video", {})
        audio = profile.get("audio", {})
        limits = profile.get("limits", {})

        args = ["-y", "-i", self._source]
        args.extend(self._build_video_args(video))
        args.extend(self._build_audio_args(audio))
        args.extend(self._build_limits_args(limits))
        args.append(self._output)

        result = run_ffmpeg(args)
        return result.returncode == 0

    def encode_two_pass(
        self,
        profile: dict,
        duration_seconds: float,
        passlogfile: str = "ffmpeg2pass",
        status_callback: Optional[Callable[[str], None]] = None,
    ) -> bool:
        """
        Двухпроходное кодирование с целевым битрейтом.

        Pass 1 — анализ в null-девайс, Pass 2 — финальное кодирование.
        Битрейт вычисляется через bitrate_calculator.
        Временные лог-файлы автоматически удаляются в finally.

        Args:
            profile: полный профиль (video / audio / limits).
            duration_seconds: длительность видео (из VideoAnalyzer).
            passlogfile: префикс для временных лог-файлов.
            status_callback: опциональный колбэк для UI-статусов.

        Returns:
            True при успехе, False при ошибке.
        """
        from core.bitrate_calculator import calculate_video_bitrate

        target_mb = profile.get("limits", {}).get("max_size_mb")
        if target_mb is None:
            return self.encode(profile)

        audio_kbps = 128.0  # default AAC bitrate
        video_kbps = calculate_video_bitrate(
            target_mb=target_mb,
            duration_sec=duration_seconds,
            audio_kbps=audio_kbps,
            overhead_pct=2.0,
        )

        video = profile.get("video", {})
        audio = profile.get("audio", {})
        limits = profile.get("limits", {})

        # --- Pass 1 ---
        if status_callback:
            status_callback("Encoding (Pass 1/2)...")

        null_device = self._get_null_device()
        pass1_args = [
            "-y", "-i", self._source,
            *self._build_video_args(video, for_two_pass=True),
            "-b:v", f"{video_kbps}k",
            "-pass", "1",
            "-passlogfile", passlogfile,
            "-f", "null",
            null_device,
        ]

        try:
            result1 = run_ffmpeg(pass1_args)
        except Exception:
            self._cleanup_passlogs(passlogfile)
            return False

        if result1.returncode != 0:
            self._cleanup_passlogs(passlogfile)
            return False

        # --- Pass 2 ---
        if status_callback:
            status_callback("Encoding (Pass 2/2)...")

        pass2_args = [
            "-y", "-i", self._source,
            *self._build_video_args(video, for_two_pass=True),
            "-b:v", f"{video_kbps}k",
            "-pass", "2",
            "-passlogfile", passlogfile,
            *self._build_audio_args(audio),
            *self._build_limits_args(limits),
            self._output,
        ]

        try:
            result2 = run_ffmpeg(pass2_args)
            return result2.returncode == 0
        finally:
            self._cleanup_passlogs(passlogfile)

    @staticmethod
    def _get_null_device() -> str:
        """Кроссплатформенный null-девайс: NUL (Windows), /dev/null (*nix)."""
        return "NUL" if os.name == "nt" else "/dev/null"