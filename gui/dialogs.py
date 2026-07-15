"""
Диалоги выбора файлов для GUI OpenVideoEncoder v0.3.
Обёртки над tkinter.filedialog с единым стилем.
"""

import os
import tkinter as tk
from tkinter import filedialog


def _ensure_root():
    """Создаёт скрытое корневое окно для диалогов, если его ещё нет."""
    root = tk._default_root
    if root is None:
        root = tk.Tk()
        root.withdraw()
    return root


def open_file_dialog(title="Выберите видеофайл",
                     filetypes=None,
                     initial_dir=None):
    """
    Диалог открытия файла.
    Возвращает путь к файлу или None, если пользователь отменил выбор.
    """
    root = _ensure_root()
    if filetypes is None:
        filetypes = [
            ("Видеофайлы", "*.mp4 *.mkv *.avi *.mov *.webm"),
            ("Все файлы", "*.*"),
        ]
    path = filedialog.askopenfilename(
        title=title,
        filetypes=filetypes,
        initialdir=initial_dir or os.path.expanduser("~"),
        parent=root,
    )
    return path if path else None


def save_file_dialog(title="Сохранить как",
                     filetypes=None,
                     default_extension=".mp4",
                     initial_file="output.mp4",
                     initial_dir=None):
    """
    Диалог сохранения файла.
    Возвращает путь или None, если пользователь отменил.
    """
    root = _ensure_root()
    if filetypes is None:
        filetypes = [
            ("MP4 видео", "*.mp4"),
            ("MKV видео", "*.mkv"),
            ("Все файлы", "*.*"),
        ]
    path = filedialog.asksaveasfilename(
        title=title,
        filetypes=filetypes,
        defaultextension=default_extension,
        initialfile=initial_file,
        initialdir=initial_dir or os.path.expanduser("~"),
        parent=root,
    )
    return path if path else None


def select_profile_dialog(profiles_dir="profiles",
                          title="Выберите профиль кодирования"):
    """
    Диалог выбора профиля из папки profiles/.
    Возвращает имя профиля (без пути и расширения) или None.
    """
    root = _ensure_root()
    path = filedialog.askopenfilename(
        title=title,
        filetypes=[("JSON профили", "*.json"), ("Все файлы", "*.*")],
        initialdir=profiles_dir if os.path.isdir(profiles_dir) else os.path.expanduser("~"),
        parent=root,
    )
    if not path:
        return None
    return os.path.splitext(os.path.basename(path))[0]