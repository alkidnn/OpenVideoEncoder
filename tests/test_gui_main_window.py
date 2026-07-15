"""
Юнит-тесты для gui/main_window.py.

Мокаем tkinter на уровне sys.modules, чтобы обойти отсутствие дисплея.
Проверяем логику: выбор файлов, запуск кодирования, фоновый поток, callback.
"""

import sys
import unittest
from unittest import mock

# ═══════════════════════════════════════════════════
# Моки tkinter и ttk (до импорта gui.*)
# ═══════════════════════════════════════════════════

class FakeStringVar:
    """Подмена tk.StringVar."""

    def __init__(self, value=""):
        self._value = value

    def get(self):
        return self._value

    def set(self, value):
        self._value = value


class FakeTk:
    """Подмена tk.Tk."""

    def __init__(self, *args, **kwargs):
        pass

    def title(self, *args):
        pass

    def geometry(self, *args):
        pass

    def minsize(self, *args, **kwargs):
        pass

    def configure(self, **kwargs):
        pass

    def after(self, *args, **kwargs):
        pass

    def mainloop(self, *args, **kwargs):
        pass


class FakeWidget:
    """Базовый виджет: принимает любые аргументы, глушит grid/pack/config."""

    def __init__(self, parent=None, **kwargs):
        self.parent = parent
        for k, v in kwargs.items():
            setattr(self, k, v)

    def grid(self, **kwargs):
        pass

    def pack(self, **kwargs):
        pass

    def config(self, **kwargs):
        pass

    def configure(self, **kwargs):
        pass

    def grid_rowconfigure(self, *args, **kwargs):
        pass

    def grid_columnconfigure(self, *args, **kwargs):
        pass

    def columnconfigure(self, *args, **kwargs):
        pass

    def rowconfigure(self, *args, **kwargs):
        pass


class FakeButton(FakeWidget):
    pass


class FakeLabel(FakeWidget):
    pass


class FakeEntry(FakeWidget):
    pass


class FakeCheckbutton(FakeWidget):
    pass


class FakeFrame(FakeWidget):
    pass


class FakeLabelFrame(FakeWidget):
    pass


class FakeTreeview(FakeWidget):
    def heading(self, *args, **kwargs):
        pass

    def column(self, *args, **kwargs):
        pass

    def insert(self, *args, **kwargs):
        pass

    def delete(self, *args):
        pass

    def get_children(self):
        return []

    def item(self, *args, **kwargs):
        return ()

    def yview(self, *args, **kwargs):
        pass


class FakeScrollbar(FakeWidget):
    def set(self, *args, **kwargs):
        pass


class FakeMessagebox:
    """Подмена tkinter.messagebox."""

    @staticmethod
    def showwarning(*args, **kwargs):
        pass

    @staticmethod
    def showerror(*args, **kwargs):
        pass

    @staticmethod
    def showinfo(*args, **kwargs):
        pass


# Собираем tkinter-моки
_tk_mock = mock.MagicMock()
_tk_mock.Tk = FakeTk
_tk_mock.StringVar = FakeStringVar
_tk_mock.messagebox = FakeMessagebox

_ttk_mock = mock.MagicMock()
_ttk_mock.Frame = FakeFrame
_ttk_mock.Label = FakeLabel
_ttk_mock.Button = FakeButton
_ttk_mock.Entry = FakeEntry
_ttk_mock.Checkbutton = FakeCheckbutton
_ttk_mock.LabelFrame = FakeLabelFrame
_ttk_mock.Treeview = FakeTreeview
_ttk_mock.Scrollbar = FakeScrollbar

_tk_mock.ttk = _ttk_mock  # чтобы from tkinter import ttk получил наши фейки

sys.modules["tkinter"] = _tk_mock
sys.modules["tkinter.ttk"] = _ttk_mock
sys.modules["tkinter.messagebox"] = FakeMessagebox

# ═══════════════════════════════════════════════════
# Теперь импортируем тестируемый модуль
# ═══════════════════════════════════════════════════

from gui.main_window import MainWindow


# ═══════════════════════════════════════════════════
# Вспомогательные функции
# ═══════════════════════════════════════════════════

def _patch_many(targets):
    """Декоратор: применяет несколько mock.patch за раз."""
    def decorator(fn):
        for target in reversed(targets):
            fn = mock.patch(target)(fn)
        return fn
    return decorator


# ═══════════════════════════════════════════════════
# Тесты
# ═══════════════════════════════════════════════════

class TestInit(unittest.TestCase):
    """Проверка инициализации MainWindow."""

    def test_title_set_correctly(self):
        win = MainWindow()
        self.assertIsInstance(win, MainWindow)
        self.assertTrue(hasattr(win, "queue_widget"))

    def test_default_source_is_none(self):
        win = MainWindow()
        self.assertIsNone(win._source)

    def test_default_output_is_none(self):
        win = MainWindow()
        self.assertIsNone(win._output)

    def test_default_profile_is_none(self):
        win = MainWindow()
        self.assertIsNone(win._profile_name)

    def test_task_counter_starts_at_zero(self):
        win = MainWindow()
        self.assertEqual(win._task_counter, 0)

    def test_status_bar_created(self):
        win = MainWindow()
        self.assertTrue(hasattr(win, "_status_bar"))


class TestFileSelection(unittest.TestCase):
    """Проверка выбора файлов и профиля."""

    @mock.patch("gui.main_window.open_file_dialog")
    def test_select_source_calls_dialog(self, mock_dialog):
        mock_dialog.return_value = "/tmp/in.mp4"
        win = MainWindow()
        win._select_source()
        mock_dialog.assert_called_once()
        self.assertEqual(win._source, "/tmp/in.mp4")

    @mock.patch("gui.main_window.open_file_dialog")
    def test_select_source_none_ignored(self, mock_dialog):
        mock_dialog.return_value = None
        win = MainWindow()
        win._source = "/old/path.mp4"
        win._select_source()
        self.assertEqual(win._source, "/old/path.mp4")

    @mock.patch("gui.main_window.save_file_dialog")
    def test_select_output_calls_dialog(self, mock_dialog):
        mock_dialog.return_value = "/tmp/out.mp4"
        win = MainWindow()
        win._select_output()
        mock_dialog.assert_called_once()
        self.assertEqual(win._output, "/tmp/out.mp4")

    @mock.patch("gui.main_window.save_file_dialog")
    def test_select_output_none_ignored(self, mock_dialog):
        mock_dialog.return_value = None
        win = MainWindow()
        win._output = "/old/out.mp4"
        win._select_output()
        self.assertEqual(win._output, "/old/out.mp4")

    @mock.patch("gui.main_window.select_profile_dialog")
    def test_select_profile_calls_dialog(self, mock_dialog):
        mock_dialog.return_value = "h264_fast"
        win = MainWindow()
        win._select_profile()
        mock_dialog.assert_called_once()
        self.assertEqual(win._profile_name, "h264_fast")

    @mock.patch("gui.main_window.select_profile_dialog")
    def test_select_profile_none_ignored(self, mock_dialog):
        mock_dialog.return_value = None
        win = MainWindow()
        win._profile_name = "old_profile"
        win._select_profile()
        self.assertEqual(win._profile_name, "old_profile")


class TestStartEncoding(unittest.TestCase):
    """Проверка запуска кодирования."""

    def _make_ready_window(self):
        """Создаёт окно с заполненными полями."""
        win = MainWindow()
        win._source = "in.mp4"
        win._output = "out.mp4"
        win._profile_name = "test"
        return win

    @mock.patch("gui.main_window.messagebox.showwarning")
    def test_missing_source_shows_warning(self, mock_warn):
        win = self._make_ready_window()
        win._source = None
        win._start_encoding()
        mock_warn.assert_called_once()

    @mock.patch("gui.main_window.messagebox.showwarning")
    def test_missing_output_shows_warning(self, mock_warn):
        win = self._make_ready_window()
        win._output = None
        win._start_encoding()
        mock_warn.assert_called_once()

    @mock.patch("gui.main_window.messagebox.showwarning")
    def test_missing_profile_shows_warning(self, mock_warn):
        win = self._make_ready_window()
        win._profile_name = None
        win._start_encoding()
        mock_warn.assert_called_once()

    @mock.patch("gui.main_window.messagebox.showwarning")
    def test_all_filled_no_warning(self, mock_warn):
        win = self._make_ready_window()
        win._start_encoding()
        mock_warn.assert_not_called()

    def test_task_counter_increments(self):
        win = self._make_ready_window()
        self.assertEqual(win._task_counter, 0)
        win._start_encoding()
        self.assertEqual(win._task_counter, 1)
        win._start_encoding()
        self.assertEqual(win._task_counter, 2)

    def test_task_added_to_queue_widget(self):
        win = self._make_ready_window()
        win.queue_widget.add_task = mock.MagicMock()
        win._start_encoding()
        win.queue_widget.add_task.assert_called_once()
        task = win.queue_widget.add_task.call_args[0][0]
        self.assertEqual(task["source"], "in.mp4")
        self.assertEqual(task["output"], "out.mp4")
        self.assertEqual(task["profile_name"], "test")
        self.assertEqual(task["status"], "pending")

    def test_task_ids_are_unique(self):
        win = self._make_ready_window()
        win.queue_widget.add_task = mock.MagicMock()
        win._start_encoding()
        win._start_encoding()
        task1 = win.queue_widget.add_task.call_args_list[0][0][0]
        task2 = win.queue_widget.add_task.call_args_list[1][0][0]
        self.assertEqual(task1["id"], 1)
        self.assertEqual(task2["id"], 2)

    @mock.patch("gui.main_window.threading.Thread")
    def test_thread_started(self, mock_thread):
        win = self._make_ready_window()
        win._start_encoding()
        mock_thread.assert_called_once()
        call_kwargs = mock_thread.call_args.kwargs
        self.assertEqual(call_kwargs["target"], win._encode_worker)
        self.assertTrue(call_kwargs["daemon"])
        mock_thread.return_value.start.assert_called_once()

    @mock.patch("gui.main_window.threading.Thread")
    def test_thread_receives_correct_task(self, mock_thread):
        win = self._make_ready_window()
        win._start_encoding()
        args = mock_thread.call_args.kwargs["args"]
        task = args[0]
        self.assertEqual(task["id"], 1)
        self.assertEqual(task["source"], "in.mp4")
        self.assertEqual(task["profile_name"], "test")


class TestEncodeWorker(unittest.TestCase):
    """Проверка фонового потока кодирования."""

    def setUp(self):
        self.win = MainWindow()
        self.win._source = "in.mp4"
        self.win._output = "out.mp4"
        self.win._profile_name = "test"
        self.task = {
            "id": 1,
            "source": "in.mp4",
            "output": "out.mp4",
            "profile_name": "test",
            "status": "pending",
        }

    @mock.patch("gui.main_window.ProfileManager")
    @mock.patch("gui.main_window.VideoEncoder")
    def test_encode_worker_loads_profile(self, mock_encoder_cls, mock_pm_cls):
        mock_pm = mock_pm_cls.return_value
        mock_pm.load.return_value = {"codec": "libx264"}

        self.win._encode_worker(self.task)

        mock_pm_cls.assert_called_once_with(self.win._profiles_dir)
        mock_pm.load.assert_called_once_with("test")

    @mock.patch("gui.main_window.ProfileManager")
    @mock.patch("gui.main_window.VideoEncoder")
    def test_encode_worker_creates_encoder(self, mock_encoder_cls, mock_pm_cls):
        mock_pm = mock_pm_cls.return_value
        mock_pm.load.return_value = {"codec": "libx264"}

        self.win._encode_worker(self.task)

        mock_encoder_cls.assert_called_once_with("in.mp4", "out.mp4")

    @mock.patch("gui.main_window.ProfileManager")
    @mock.patch("gui.main_window.VideoEncoder")
    def test_encode_worker_calls_encode(self, mock_encoder_cls, mock_pm_cls):
        mock_pm = mock_pm_cls.return_value
        mock_pm.load.return_value = {"codec": "libx264"}
        mock_encoder = mock_encoder_cls.return_value

        self.win._encode_worker(self.task)

        mock_encoder.encode.assert_called_once_with({"codec": "libx264"})

    @mock.patch("gui.main_window.ProfileManager")
    @mock.patch("gui.main_window.VideoEncoder")
    def test_encode_success_schedules_done(self, mock_encoder_cls, mock_pm_cls):
        mock_pm = mock_pm_cls.return_value
        mock_pm.load.return_value = {"codec": "libx264"}
        mock_encoder_cls.return_value.encode.return_value = True

        self.win.after = mock.MagicMock()
        self.win._encode_worker(self.task)

        self.win.after.assert_called_once_with(
            0, self.win._on_encode_complete, 1, "done"
        )

    @mock.patch("gui.main_window.ProfileManager")
    @mock.patch("gui.main_window.VideoEncoder")
    def test_encode_failure_schedules_failed(self, mock_encoder_cls, mock_pm_cls):
        mock_pm = mock_pm_cls.return_value
        mock_pm.load.return_value = {"codec": "libx264"}
        mock_encoder_cls.return_value.encode.return_value = False

        self.win.after = mock.MagicMock()
        self.win._encode_worker(self.task)

        self.win.after.assert_called_once_with(
            0, self.win._on_encode_complete, 1, "failed"
        )


class TestOnEncodeComplete(unittest.TestCase):
    """Проверка callback-а после завершения кодирования."""

    def setUp(self):
        self.win = MainWindow()
        self.win.queue_widget.update_status = mock.MagicMock()

    def test_update_status_called(self):
        self.win._on_encode_complete(1, "done")
        self.win.queue_widget.update_status.assert_called_once_with(1, "done")

    def test_done_updates_status_bar(self):
        self.win._status_bar.config = mock.MagicMock()
        self.win._on_encode_complete(1, "done")
        self.win._status_bar.config.assert_called_once()
        text_arg = self.win._status_bar.config.call_args.kwargs.get("text", "")
        self.assertIn("Готово", text_arg)

    def test_failed_updates_status_bar(self):
        self.win._status_bar.config = mock.MagicMock()
        self.win._on_encode_complete(1, "failed")
        self.win._status_bar.config.assert_called_once()
        text_arg = self.win._status_bar.config.call_args.kwargs.get("text", "")
        self.assertIn("Ошибка", text_arg)


if __name__ == "__main__":
    unittest.main()