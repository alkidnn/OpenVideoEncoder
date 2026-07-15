"""
Bitrate calculator — формула Коры для двухпроходного кодирования.

Формула:
    video_kbps = (target_mb × 8388.608 × (1 − overhead/100)) / duration_sec − audio_kbps

где 8388.608 = (1024² × 8) / 1000 — перевод МБ в килобиты.
"""

import sys

OVERHEAD_PCT: float = 2.0


def calculate_video_bitrate(
    target_mb: float,
    duration_sec: float,
    audio_kbps: float = 128.0,
    overhead_pct: float = 2.0,
) -> float:
    """
    Вычисляет целевой видеобитрейт для двухпроходного кодирования.

    Args:
        target_mb: целевой размер файла в мегабайтах.
        duration_sec: длительность видео в секундах.
        audio_kbps: битрейт аудиодорожки в кбит/с (по умолч. 128).
        overhead_pct: процент оверхеда контейнера (по умолч. 2.0).

    Returns:
        Видеобитрейт в кбит/с, гарантированно ≥ 1.0.

    Raises:
        ValueError: если target_mb или duration_sec ≤ 0.
    """
    if target_mb <= 0:
        raise ValueError(f"target_mb must be positive, got {target_mb}")
    if duration_sec <= 0:
        raise ValueError(f"duration_sec must be positive, got {duration_sec}")

    bits_per_mb = (1024 ** 2) * 8
    kbits_per_mb = bits_per_mb / 1000  # 8388.608

    available_kbps = (target_mb * kbits_per_mb * (1 - overhead_pct / 100)) / duration_sec
    video_kbps = available_kbps - audio_kbps

    return max(video_kbps, 1.0)


def get_null_device() -> str:
    """Возвращает платформозависимый путь к null-устройству."""
    return "NUL" if sys.platform == "win32" else "/dev/null"