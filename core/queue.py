"""
JobQueue — менеджер очереди задач кодирования (UUID-based).

Хранит задачи в списке. Каждая задача — словарь с ключами:
    id, source, output, profile_name, status.

Не запускает кодирование и не создаёт потоки — только управляет
списком и статусами.
"""

import uuid
from typing import Optional


class JobQueue:
    """FIFO-очередь задач с отслеживанием статусов (UUID v4)."""

    def __init__(self):
        self._tasks: list[dict] = []

    @staticmethod
    def _next_id() -> str:
        return uuid.uuid4().hex

    def add_task(self, source: str, output: str, profile_name: str) -> dict:
        """Добавляет задачу в очередь. Возвращает созданную задачу."""
        task = {
            "id": self._next_id(),
            "source": source,
            "output": output,
            "profile_name": profile_name,
            "status": "pending",
        }
        self._tasks.append(task)
        return task

    def get_next_task(self) -> Optional[dict]:
        """
        Возвращает первую задачу со статусом 'pending' и переводит её
        в статус 'processing'. Если ожидающих задач нет — возвращает None.
        """
        for task in self._tasks:
            if task["status"] == "pending":
                task["status"] = "processing"
                return task
        return None

    def update_task_status(self, task_id: str, status: str) -> bool:
        """
        Обновляет статус задачи по id.
        Возвращает True, если задача найдена и статус обновлён, иначе False.
        """
        task = self.get_task(task_id)
        if task is None:
            return False
        task["status"] = status
        return True

    def get_task(self, task_id: str) -> Optional[dict]:
        """Возвращает задачу по id или None."""
        for task in self._tasks:
            if task["id"] == task_id:
                return task
        return None

    def get_all_tasks(self) -> list[dict]:
        """Возвращает копию списка всех задач."""
        return list(self._tasks)