"""
HistoryManager — менеджер истории завершённых задач.

Логирует успешно завершённые или упавшие задачи в папку history/
в виде отдельных JSON-файлов. Один файл на одну задачу.
"""

import json
import os
from datetime import datetime, timezone
from pathlib import Path


class HistoryManager:
    """Сохраняет и читает историю задач."""

    def __init__(self, history_dir: str = "history"):
        self._dir = Path(history_dir)
        self._dir.mkdir(parents=True, exist_ok=True)

    def add_to_history(self, task_data: dict) -> str:
        """
        Сохраняет задачу в отдельный JSON-файл.
        Возвращает путь к созданному файлу.
        """
        entry = {
            "saved_at": datetime.now(timezone.utc).isoformat(),
            **task_data,
        }

        task_id = task_data.get("id", "0")
        filename = self._dir / f"task_{task_id}.json"

        with open(filename, "w", encoding="utf-8") as f:
            json.dump(entry, f, ensure_ascii=False, indent=2)

        return str(filename)

    def get_history(self) -> list[dict]:
        """
        Возвращает список всех записей из истории,
        отсортированный по имени файла.
        """
        entries: list[dict] = []
        for filename in sorted(self._dir.glob("*.json")):
            try:
                with open(filename, "r", encoding="utf-8") as f:
                    entries.append(json.load(f))
            except (json.JSONDecodeError, OSError):
                continue
        return entries