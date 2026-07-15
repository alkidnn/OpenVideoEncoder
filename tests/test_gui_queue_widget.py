"""
Тесты для gui/queue_widget.py — визуальный виджет очереди задач.

Запуск: python3 -m unittest tests/test_gui_queue_widget.py -v
"""

import sys
import unittest
from unittest import mock

# ── Фейковый tkinter ───────────────────────────────────────────
class FakeFrame:
    def __init__(self, parent=None):
        self.parent = parent
    def grid_rowconfigure(self, *args, **kwargs):
        pass
    def grid_columnconfigure(self, *args, **kwargs):
        pass

class FakeTreeview:
    def __init__(self, *args, **kwargs):
        pass
    def heading(self, *args, **kwargs):
        pass
    def column(self, *args, **kwargs):
        pass
    def configure(self, **kwargs):
        pass
    def grid(self, **kwargs):
        pass
    def yview(self, *args):
        pass
    def get_children(self):
        return []
    def delete(self, *items):
        pass
    def insert(self, parent, index, **kwargs):
        pass
    def item(self, item, **kwargs):
        return {}

class FakeScrollbar:
    def __init__(self, *args, **kwargs):
        pass
    def grid(self, **kwargs):
        pass
    def set(self, *args):
        pass

_ttk_fake = mock.MagicMock()
_ttk_fake.Frame = FakeFrame
_ttk_fake.Treeview = FakeTreeview
_ttk_fake.Scrollbar = FakeScrollbar

_tk_fake = mock.MagicMock()
_tk_fake.ttk = _ttk_fake          # ← чтобы `from tkinter import ttk` нашёл

sys.modules["tkinter"] = _tk_fake
sys.modules["tkinter.ttk"] = _ttk_fake

from gui.queue_widget import QueueWidget


# ══════════════════════════════════════════════════════════════
# Хелперы
# ══════════════════════════════════════════════════════════════

def _make_task(task_id=1, source="in.mp4", output="out.mp4",
               profile_name="default", status="pending"):
    return {
        "id": task_id,
        "source": source,
        "output": output,
        "profile_name": profile_name,
        "status": status,
    }


def _mock_tree():
    tree = mock.MagicMock()
    tree.get_children.return_value = []
    return tree


# ══════════════════════════════════════════════════════════════
# Тесты инициализации
# ══════════════════════════════════════════════════════════════

class TestInit(unittest.TestCase):

    def test_columns_order(self):
        widget = QueueWidget()
        self.assertEqual(widget.COLUMNS, ("id", "source", "output", "profile_name", "status"))

    def test_headings_dict(self):
        widget = QueueWidget()
        self.assertEqual(widget.HEADINGS["id"], "ID")
        self.assertEqual(widget.HEADINGS["status"], "Статус")

    def test_widget_is_frame_subclass(self):
        self.assertTrue(issubclass(QueueWidget, FakeFrame))


# ══════════════════════════════════════════════════════════════
# Тесты add_task
# ══════════════════════════════════════════════════════════════

class TestAddTask(unittest.TestCase):

    def setUp(self):
        self.widget = QueueWidget()
        self.widget.tree = _mock_tree()

    def test_add_single_task_calls_insert(self):
        self.widget.add_task(_make_task())
        self.widget.tree.insert.assert_called_once()
        args, kwargs = self.widget.tree.insert.call_args
        self.assertEqual(args[1], "end")
        self.assertEqual(len(kwargs["values"]), 5)

    def test_add_task_preserves_all_fields(self):
        task = _make_task(task_id=42, source="/tmp/v.mp4", output="/tmp/o.mp4",
                          profile_name="h264_hq", status="pending")
        self.widget.add_task(task)
        _, kwargs = self.widget.tree.insert.call_args
        vals = kwargs["values"]
        self.assertEqual(vals[0], "42")
        self.assertEqual(vals[1], "/tmp/v.mp4")
        self.assertEqual(vals[2], "/tmp/o.mp4")
        self.assertEqual(vals[3], "h264_hq")
        self.assertEqual(vals[4], "pending")

    def test_add_task_missing_keys_yield_empty_strings(self):
        self.widget.add_task({"id": 1})
        _, kwargs = self.widget.tree.insert.call_args
        self.assertEqual(kwargs["values"], ("1", "", "", "", ""))

    def test_add_multiple_tasks(self):
        for i in range(5):
            self.widget.add_task(_make_task(task_id=i + 1))
        self.assertEqual(self.widget.tree.insert.call_count, 5)


# ══════════════════════════════════════════════════════════════
# Тесты clear
# ══════════════════════════════════════════════════════════════

class TestClear(unittest.TestCase):

    def setUp(self):
        self.widget = QueueWidget()
        self.widget.tree = _mock_tree()

    def test_clear_deletes_all_items(self):
        self.widget.tree.get_children.return_value = ["i1", "i2", "i3"]
        self.widget.clear()
        self.assertEqual(self.widget.tree.delete.call_count, 3)

    def test_clear_empty_does_nothing(self):
        self.widget.tree.get_children.return_value = []
        self.widget.clear()
        self.widget.tree.delete.assert_not_called()


# ══════════════════════════════════════════════════════════════
# Тесты load_tasks
# ══════════════════════════════════════════════════════════════

class TestLoadTasks(unittest.TestCase):

    def setUp(self):
        self.widget = QueueWidget()
        self.widget.tree = _mock_tree()

    def test_load_tasks_replaces_content(self):
        tasks = [_make_task(i) for i in range(1, 4)]
        self.widget.load_tasks(tasks)
        self.assertEqual(self.widget.tree.insert.call_count, 3)

    def test_load_tasks_calls_clear_first(self):
        self.widget.tree.get_children.return_value = ["old1"]
        self.widget.load_tasks([_make_task()])
        self.widget.tree.delete.assert_called()

    def test_load_empty_list_clears_table(self):
        self.widget.tree.get_children.return_value = ["x"]
        self.widget.load_tasks([])
        self.widget.tree.delete.assert_called_once_with("x")
        self.widget.tree.insert.assert_not_called()


# ══════════════════════════════════════════════════════════════
# Тесты update_status
# ══════════════════════════════════════════════════════════════

class TestUpdateStatus(unittest.TestCase):

    def setUp(self):
        self.widget = QueueWidget()
        self.widget.tree = _mock_tree()

    def test_update_existing_task(self):
        self.widget.tree.get_children.return_value = ["item_1"]
        self.widget.tree.item.return_value = ("1", "in.mp4", "out.mp4", "default", "pending")
        result = self.widget.update_status(1, "done")
        self.assertIs(result, True)
        self.widget.tree.item.assert_any_call(
            "item_1",
            values=["1", "in.mp4", "out.mp4", "default", "done"]
        )

    def test_update_nonexistent_task(self):
        self.widget.tree.get_children.return_value = ["item_1"]
        self.widget.tree.item.return_value = ("2", "in.mp4", "out.mp4", "default", "pending")
        result = self.widget.update_status(99, "done")
        self.assertFalse(result)

    def test_update_status_to_failed(self):
        self.widget.tree.get_children.return_value = ["item_1"]
        self.widget.tree.item.return_value = ("1", "in.mp4", "out.mp4", "default", "pending")
        result = self.widget.update_status(1, "failed")
        self.assertTrue(result)
        self.widget.tree.item.assert_any_call(
            "item_1",
            values=["1", "in.mp4", "out.mp4", "default", "failed"]
        )

    def test_update_second_of_three_tasks(self):
        self.widget.tree.get_children.return_value = ["i1", "i2", "i3"]

        def item_side_effect(item_id, option=None, **kwargs):
            values = {
                "i1": ("1", "a.mp4", "a-out.mp4", "p1", "pending"),
                "i2": ("2", "b.mp4", "b-out.mp4", "p2", "pending"),
                "i3": ("3", "c.mp4", "c-out.mp4", "p3", "pending"),
            }
            if option == "values":
                return values[item_id]
            if not kwargs:
                return {"values": values[item_id]}
            return mock.DEFAULT

        self.widget.tree.item.side_effect = item_side_effect
        result = self.widget.update_status(2, "done")
        self.assertTrue(result)


# ══════════════════════════════════════════════════════════════
# Тесты get_row_count
# ══════════════════════════════════════════════════════════════

class TestGetRowCount(unittest.TestCase):

    def setUp(self):
        self.widget = QueueWidget()
        self.widget.tree = _mock_tree()

    def test_empty_table_returns_zero(self):
        self.widget.tree.get_children.return_value = []
        self.assertEqual(self.widget.get_row_count(), 0)

    def test_three_rows_returns_three(self):
        self.widget.tree.get_children.return_value = ["a", "b", "c"]
        self.assertEqual(self.widget.get_row_count(), 3)

    def test_after_clear_returns_zero(self):
        self.widget.tree.get_children.return_value = ["a", "b"]
        self.assertEqual(self.widget.get_row_count(), 2)
        self.widget.tree.get_children.return_value = []
        self.assertEqual(self.widget.get_row_count(), 0)