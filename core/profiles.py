"""
Менеджер профилей кодирования.

Загружает JSON-конфигурации из папки profiles/.
Отвечает строго за чтение и валидацию профилей — ничего больше.
"""

import json
import os


class ProfileManager:
    """
    Загружает профили кодирования из указанной директории.

    Использование:
        pm = ProfileManager("profiles")
        profile = pm.load("telegram_4gb")  # → dict или {} при ошибке

    Правила:
        - Ищет файл <name>.json в profiles_dir.
        - При любых ошибках (файл не найден, битый JSON) возвращает {},
          НЕ выбрасывает исключений.
    """

    def __init__(self, profiles_dir: str = "profiles"):
        """
        Args:
            profiles_dir: путь к папке с профилями (относительный или абсолютный).
        """
        self._profiles_dir = profiles_dir

    def load(self, name: str) -> dict:
        """
        Загружает профиль по имени.

        Args:
            name: имя профиля без расширения (например, 'telegram_4gb').

        Returns:
            Словарь с параметрами профиля. Пустой словарь при любой ошибке.
        """
        filename = f"{name}.json"
        filepath = os.path.join(self._profiles_dir, filename)

        try:
            with open(filepath, "r", encoding="utf-8") as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError, OSError):
            return {}