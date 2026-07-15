"""
Визуальный виджет очереди задач на базе tkinter v0.3.

Отвечает только за отображение — не управляет задачами и не запускает кодирование.
Поддерживает UUID-идентификаторы задач.
"""

import tkinter as tk
from tkinter import ttk


class QueueWidget(ttk.Frame):
    """Treeview-таблица для отображения очереди задач."""

    COLUMNS = ("id", "source", "output", "profile_name", "status")
    HEADINGS = {
        "id": "ID",
        "source": "Исходный файл",
        "output": "Результат",
        "profile_name": "Профиль",
        "status": "Статус",
    }

    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()

    def _build_ui(self):
        self.tree = ttk.Treeview(
            self, columns=self.COLUMNS, show="headings", height=10
        )
        for col in self.COLUMNS:
            self.tree.heading(col, text=self.HEADINGS.get(col, col))
            self.tree.column(col, width=120, anchor="center")

        scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

    def clear(self):
        """Удалить все строки из таблицы."""
        for item in self.tree.get_children():
            self.tree.delete(item)

    def add_task(self, task: dict):
        """Добавить одну задачу в таблицу."""
        values = tuple(str(task.get(col, "")) for col in self.COLUMNS)
        self.tree.insert("", "end", values=values)

    def load_tasks(self, tasks: list):
        """Заменить всё содержимое таблицы списком задач."""
        self.clear()
        for task in tasks:
            self.add_task(task)

    def update_status(self, task_id: str, new_status: str):
        """Обновить статус задачи в таблице.

        Args:
            task_id: id задачи (UUID-строка или int).
            new_status: новый статус (например, 'done', 'failed').

        Returns:
            True если задача найдена и обновлена, иначе False.
        """
        for item in self.tree.get_children():
            values = self.tree.item(item, "values")
            if values and str(values[0]) == str(task_id):
                new_values = list(values)
                new_values[self.COLUMNS.index("status")] = new_status
                self.tree.item(item, values=new_values)
                return True
        return False

    def get_row_count(self) -> int:
        """Количество строк в таблице."""
        return len(self.tree.get_children())