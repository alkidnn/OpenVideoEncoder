"""
Главное окно приложения OpenVideoEncoder v0.3.

Объединяет выбор файлов, профилей и очередь задач.
Кодирование выполняется в фоновом потоке — интерфейс не зависает.
Автовыбор стратегии: при наличии limits.max_size_mb запускается двухпроходное кодирование.
"""

import threading
import tkinter as tk
from tkinter import ttk, messagebox
from uuid import uuid4

from core.encoder import VideoEncoder
from core.analyzer import VideoAnalyzer
from core.profiles import ProfileManager
from gui.dialogs import open_file_dialog, save_file_dialog, select_profile_dialog
from gui.queue_widget import QueueWidget
from gui.settings import (
    PAD_NORMAL, PAD_SMALL,
    WINDOW_HEIGHT, WINDOW_TITLE, WINDOW_WIDTH,
)


class MainWindow(tk.Tk):
    """Главное окно: выбор файлов, профиля, очередь, статус-бар."""

    def __init__(self, profiles_dir: str = "profiles"):
        super().__init__()
        self.title(WINDOW_TITLE)
        self.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}")

        self._source: str | None = None
        self._output: str | None = None
        self._profile_name: str | None = None
        self._profiles_dir: str = profiles_dir

        self._build_ui()

    # ── UI ─────────────────────────────────────────

    def _build_ui(self) -> None:
        """Собирает все элементы интерфейса."""
        self._build_control_panel()
        self._build_queue()
        self._build_status_bar()

    def _build_control_panel(self) -> None:
        """Панель выбора файлов и профиля + кнопка кодирования."""
        frame = ttk.Frame(self, padding=PAD_NORMAL)
        frame.pack(fill="x")

        row = 0
        # Исходный файл
        ttk.Label(frame, text="Исходный файл:").grid(
            row=row, column=0, sticky="w", pady=PAD_SMALL
        )
        self._source_btn = ttk.Button(
            frame, text="Выбрать…", command=self._select_source
        )
        self._source_btn.grid(row=row, column=1, sticky="ew", padx=PAD_SMALL)
        self._source_label = ttk.Label(frame, text="Не выбран", foreground="gray")
        self._source_label.grid(row=row, column=2, sticky="w")

        row = 1
        # Сохранить как
        ttk.Label(frame, text="Сохранить как:").grid(
            row=row, column=0, sticky="w", pady=PAD_SMALL
        )
        self._output_btn = ttk.Button(
            frame, text="Выбрать…", command=self._select_output
        )
        self._output_btn.grid(row=row, column=1, sticky="ew", padx=PAD_SMALL)
        self._output_label = ttk.Label(frame, text="Не выбран", foreground="gray")
        self._output_label.grid(row=row, column=2, sticky="w")

        row = 2
        # Профиль
        ttk.Label(frame, text="Профиль:").grid(
            row=row, column=0, sticky="w", pady=PAD_SMALL
        )
        self._profile_btn = ttk.Button(
            frame, text="Выбрать…", command=self._select_profile
        )
        self._profile_btn.grid(row=row, column=1, sticky="ew", padx=PAD_SMALL)
        self._profile_label = ttk.Label(frame, text="Не выбран", foreground="gray")
        self._profile_label.grid(row=row, column=2, sticky="w")

        row = 3
        # Кнопка запуска
        self._encode_btn = ttk.Button(
            frame, text="▶ Кодировать", command=self._start_encoding
        )
        self._encode_btn.grid(row=row, column=1, pady=PAD_NORMAL)

        frame.columnconfigure(1, weight=1)

    def _build_queue(self) -> None:
        """Виджет очереди задач."""
        self.queue_widget = QueueWidget(self)
        self.queue_widget.pack(
            fill="both", expand=True, padx=PAD_NORMAL, pady=PAD_NORMAL
        )

    def _build_status_bar(self) -> None:
        """Статус-бар внизу окна."""
        self._status_bar = ttk.Label(
            self, text="Готов", relief="sunken", anchor="w"
        )
        self._status_bar.pack(fill="x", side="bottom")

    # ── Обработчики ────────────────────────────────

    def _select_source(self) -> None:
        path = open_file_dialog()
        if path:
            self._source = path
            self._source_label.config(text=path, foreground="black")

    def _select_output(self) -> None:
        path = save_file_dialog()
        if path:
            self._output = path
            self._output_label.config(text=path, foreground="black")

    def _select_profile(self) -> None:
        name = select_profile_dialog(self._profiles_dir)
        if name:
            self._profile_name = name
            self._profile_label.config(text=name, foreground="black")

    def _start_encoding(self) -> None:
        """Проверяет поля и запускает фоновое кодирование."""
        if not self._source or not self._output or not self._profile_name:
            messagebox.showwarning(
                "Не заполнено", "Выберите файл, путь сохранения и профиль."
            )
            return

        task_id = str(uuid4())
        task = {
            "id": task_id,
            "source": self._source,
            "output": self._output,
            "profile_name": self._profile_name,
            "status": "pending",
        }
        self.queue_widget.add_task(task)
        self._status_bar.config(text=f"Кодирование: {self._source}")

        thread = threading.Thread(
            target=self._encode_worker, args=(task,), daemon=True
        )
        thread.start()

    def _encode_worker(self, task: dict) -> None:
        """Фоновый поток: автостратегия + кодирование + обновление UI."""
        pm = ProfileManager(self._profiles_dir)
        profile = pm.load(task["profile_name"])

        encoder = VideoEncoder(task["source"], task["output"])
        limits: dict = profile.get("limits", {})

        if limits.get("max_size_mb") is not None:
            # ── Двухпроходное кодирование ──
            self._update_status_from_thread(task["id"], "Encoding (Pass 1/2)...")

            analyzer = VideoAnalyzer(task["source"])
            duration = analyzer.get_duration()
            if duration is None:
                self.after(0, self._on_encode_complete, task["id"], "failed")
                return

            def status_callback(status_text: str) -> None:
                self._update_status_from_thread(task["id"], status_text)

            success = encoder.encode_two_pass(
                profile, duration, status_callback=status_callback
            )
        else:
            # ── Однопроходное кодирование (CRF) ──
            self._update_status_from_thread(task["id"], "Encoding...")
            success = encoder.encode(profile)

        status = "done" if success else "failed"
        self.after(0, self._on_encode_complete, task["id"], status)

    def _update_status_from_thread(self, task_id: str, status_text: str) -> None:
        """Потокобезопасное обновление статуса задачи в UI."""
        self.after(0, self.queue_widget.update_status, task_id, status_text)

    def _on_encode_complete(self, task_id: str, status: str) -> None:
        """Обновляет UI после завершения кодирования."""
        self.queue_widget.update_status(task_id, status)
        if status == "done":
            self._status_bar.config(text=f"Готово: задача #{task_id[:8]}...")
        else:
            self._status_bar.config(text=f"Ошибка: задача #{task_id[:8]}...")


if __name__ == "__main__":
    app = MainWindow()
    app.mainloop()