"""
OpenVideoEncoder — ядро библиотеки кодирования видео v0.3.0.
"""

from core.ffmpeg import run_ffmpeg, run_ffprobe
from core.analyzer import VideoAnalyzer
from core.profiles import ProfileManager
from core.encoder import VideoEncoder
from core.queue import JobQueue
from core.history import HistoryManager
from core.bitrate_calculator import calculate_video_bitrate

__version__ = "0.3.0"