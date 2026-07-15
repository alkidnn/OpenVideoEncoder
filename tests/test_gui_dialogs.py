"""
Тесты для gui/dialogs.py.
Мокируют tkinter — реальные диалоги не открываются, tkinter не требуется.
"""

import sys
import os
import unittest
from unittest import mock

# ── Мокаем tkinter ДО импорта dialogs ─────────────
sys.modules["tkinter"] = mock.MagicMock()
sys.modules["tkinter.filedialog"] = mock.MagicMock()
# tkinter._default_root = None для _ensure_root()
import tkinter as tk_mock
tk_mock._default_root = None

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from gui import dialogs


class TestOpenFileDialog(unittest.TestCase):
    """open_file_dialog."""

    @mock.patch("gui.dialogs.filedialog.askopenfilename")
    def test_returns_path_when_selected(self, mock_ask):
        mock_ask.return_value = "/home/user/video.mp4"
        result = dialogs.open_file_dialog()
        self.assertEqual(result, "/home/user/video.mp4")

    @mock.patch("gui.dialogs.filedialog.askopenfilename")
    def test_returns_none_when_cancelled(self, mock_ask):
        mock_ask.return_value = ""
        result = dialogs.open_file_dialog()
        self.assertIsNone(result)

    @mock.patch("gui.dialogs.filedialog.askopenfilename")
    def test_passes_custom_title(self, mock_ask):
        mock_ask.return_value = "/tmp/x.mp4"
        dialogs.open_file_dialog(title="Мой заголовок")
        call_kwargs = mock_ask.call_args.kwargs
        self.assertEqual(call_kwargs["title"], "Мой заголовок")

    @mock.patch("gui.dialogs.filedialog.askopenfilename")
    def test_passes_custom_filetypes(self, mock_ask):
        mock_ask.return_value = "/tmp/x.mp4"
        ft = [("Все", "*.*")]
        dialogs.open_file_dialog(filetypes=ft)
        call_kwargs = mock_ask.call_args.kwargs
        self.assertEqual(call_kwargs["filetypes"], ft)

    @mock.patch("gui.dialogs.filedialog.askopenfilename")
    def test_passes_custom_initial_dir(self, mock_ask):
        mock_ask.return_value = "/tmp/x.mp4"
        dialogs.open_file_dialog(initial_dir="/my/dir")
        call_kwargs = mock_ask.call_args.kwargs
        self.assertEqual(call_kwargs["initialdir"], "/my/dir")

    @mock.patch("gui.dialogs.filedialog.askopenfilename")
    def test_default_filetypes_include_mp4(self, mock_ask):
        mock_ask.return_value = "/tmp/x.mp4"
        dialogs.open_file_dialog()
        call_kwargs = mock_ask.call_args.kwargs
        ft_str = str(call_kwargs["filetypes"])
        self.assertIn("mp4", ft_str)


class TestSaveFileDialog(unittest.TestCase):
    """save_file_dialog."""

    @mock.patch("gui.dialogs.filedialog.asksaveasfilename")
    def test_returns_path_when_selected(self, mock_ask):
        mock_ask.return_value = "/home/user/output.mp4"
        result = dialogs.save_file_dialog()
        self.assertEqual(result, "/home/user/output.mp4")

    @mock.patch("gui.dialogs.filedialog.asksaveasfilename")
    def test_returns_none_when_cancelled(self, mock_ask):
        mock_ask.return_value = ""
        result = dialogs.save_file_dialog()
        self.assertIsNone(result)

    @mock.patch("gui.dialogs.filedialog.asksaveasfilename")
    def test_default_extension_is_mp4(self, mock_ask):
        mock_ask.return_value = "/tmp/out"
        dialogs.save_file_dialog()
        call_kwargs = mock_ask.call_args.kwargs
        self.assertEqual(call_kwargs["defaultextension"], ".mp4")

    @mock.patch("gui.dialogs.filedialog.asksaveasfilename")
    def test_custom_extension(self, mock_ask):
        mock_ask.return_value = "/tmp/out"
        dialogs.save_file_dialog(default_extension=".mkv")
        call_kwargs = mock_ask.call_args.kwargs
        self.assertEqual(call_kwargs["defaultextension"], ".mkv")

    @mock.patch("gui.dialogs.filedialog.asksaveasfilename")
    def test_custom_initial_file(self, mock_ask):
        mock_ask.return_value = "/tmp/out"
        dialogs.save_file_dialog(initial_file="my_video.mp4")
        call_kwargs = mock_ask.call_args.kwargs
        self.assertEqual(call_kwargs["initialfile"], "my_video.mp4")


class TestSelectProfileDialog(unittest.TestCase):
    """select_profile_dialog."""

    @mock.patch("gui.dialogs.filedialog.askopenfilename")
    def test_returns_profile_name_without_extension(self, mock_ask):
        mock_ask.return_value = "/home/user/profiles/telegram_4gb.json"
        result = dialogs.select_profile_dialog()
        self.assertEqual(result, "telegram_4gb")

    @mock.patch("gui.dialogs.filedialog.askopenfilename")
    def test_returns_none_when_cancelled(self, mock_ask):
        mock_ask.return_value = ""
        result = dialogs.select_profile_dialog()
        self.assertIsNone(result)

    @mock.patch("gui.dialogs.filedialog.askopenfilename")
    def test_strips_only_json_extension(self, mock_ask):
        mock_ask.return_value = "/tmp/my.profile.json"
        result = dialogs.select_profile_dialog()
        self.assertEqual(result, "my.profile")

    @mock.patch("gui.dialogs.filedialog.askopenfilename")
    def test_passes_json_filetype(self, mock_ask):
        mock_ask.return_value = "/tmp/p.json"
        dialogs.select_profile_dialog()
        call_kwargs = mock_ask.call_args.kwargs
        ft_str = str(call_kwargs["filetypes"])
        self.assertIn("json", ft_str.lower())