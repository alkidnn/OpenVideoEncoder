"""
Обёртка для безопасных системных вызовов ffmpeg и ffprobe.

Использует subprocess. Никаких внешних зависимостей.
"""

import subprocess
import shutil
from typing import List


class FFmpegError(Exception):
    """Ошибка вызова ffmpeg/ffprobe."""


class FFmpegNotFoundError(FFmpegError):
    """Утилита ffmpeg или ffprobe не найдена в системе."""


class FFprobeError(FFmpegError):
    """ffprobe завершился с ошибкой (невалидный файл и т.д.)."""


class FFmpegTimeoutError(FFmpegError):
    """Вызов превысил допустимое время ожидания."""


def _find_executable(name: str) -> str:
    """Находит полный путь к утилите. Выбрасывает FFmpegNotFoundError, если её нет."""
    path = shutil.which(name)
    if path is None:
        raise FFmpegNotFoundError(
            f"{name} не найден. Установите ffmpeg: https://ffmpeg.org/download.html"
        )
    return path


def run_ffmpeg(args: List[str], timeout: int = None) -> subprocess.CompletedProcess:
    """
    Безопасно вызывает ffmpeg с переданными аргументами.

    Args:
        args: Список аргументов (без 'ffmpeg' — он добавляется автоматически).
        timeout: Таймаут в секундах.

    Returns:
        subprocess.CompletedProcess с атрибутами stdout, stderr, returncode.

    Raises:
        FFmpegNotFoundError: ffmpeg не установлен.
        FFmpegTimeoutError: превышен таймаут.
        FFmpegError: прочие ошибки вызова.
    """
    exe = _find_executable("ffmpeg")
    cmd = [exe] + args

    try:
        return subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        raise FFmpegTimeoutError(
            f"ffmpeg превысил таймаут {timeout}с при вызове: {' '.join(args)}"
        )
    except FileNotFoundError:
        raise FFmpegNotFoundError(
            "ffmpeg не найден. Установите ffmpeg: https://ffmpeg.org/download.html"
        )
    except Exception as e:
        raise FFmpegError(f"Ошибка вызова ffmpeg: {e}")


def run_ffprobe(args: List[str], timeout: int = 60) -> subprocess.CompletedProcess:
    """
    Безопасно вызывает ffprobe с переданными аргументами.

    Args:
        args: Список аргументов (без 'ffprobe' — он добавляется автоматически).
        timeout: Таймаут в секундах.

    Returns:
        subprocess.CompletedProcess с атрибутами stdout, stderr, returncode.

    Raises:
        FFmpegNotFoundError: ffprobe не установлен.
        FFmpegTimeoutError: превышен таймаут.
        FFprobeError: ffprobe завершился с ошибкой.
        FFmpegError: прочие ошибки вызова.
    """
    exe = _find_executable("ffprobe")
    cmd = [exe] + args

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        raise FFmpegTimeoutError(
            f"ffprobe превысил таймаут {timeout}с при вызове: {' '.join(args)}"
        )
    except FileNotFoundError:
        raise FFmpegNotFoundError(
            "ffprobe не найден. Установите ffmpeg: https://ffmpeg.org/download.html"
        )
    except Exception as e:
        raise FFmpegError(f"Ошибка вызова ffprobe: {e}")

    if result.returncode != 0:
        raise FFprobeError(
            f"ffprobe завершился с кодом {result.returncode}: {result.stderr.strip()}"
        )

    return result