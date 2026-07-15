"""Главный модуль приложения OpenVideoEncoder v0.3."""

import os
import sys

# Добавляем корневую директорию в PYTHONPATH при прямом запуске
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from gui.main_window import MainWindow


def main():
    """Точка входа в приложение."""
    profiles_dir = os.path.join(os.path.dirname(__file__), "profiles")
    app = MainWindow(profiles_dir=profiles_dir)
    app.mainloop()


if __name__ == "__main__":
    main()