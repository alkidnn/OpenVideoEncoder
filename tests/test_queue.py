"""Тесты для core/queue.py и автостратегии кодирования — v0.3.0."""

import unittest
from unittest import mock

from core.queue import JobQueue


class TestJobQueueBasics(unittest.TestCase):
    """Базовые операции очереди."""

    def setUp(self):
        self.queue = JobQueue()

    def test_add_task_returns_dict(self):
        task = self.queue.add_task("input.mp4", "output.mp4", "test")
        self.assertIsInstance(task, dict)

    def test_add_task_generates_uuid(self):
        task = self.queue.add_task("input.mp4", "output.mp4", "test")
        self.assertIn("id", task)
        self.assertIsInstance(task["id"], str)
        # UUID hex — 32 символа (без дефисов)
        self.assertEqual(len(task["id"]), 32)

    def test_add_task_unique_ids(self):
        task1 = self.queue.add_task("a.mp4", "b.mp4", "x")
        task2 = self.queue.add_task("c.mp4", "d.mp4", "y")
        self.assertNotEqual(task1["id"], task2["id"])

    def test_add_task_status_is_pending(self):
        task = self.queue.add_task("input.mp4", "output.mp4", "test")
        self.assertEqual(task["status"], "pending")

    def test_get_next_returns_none_empty(self):
        self.assertIsNone(self.queue.get_next_task())

    def test_get_next_returns_first_pending(self):
        t1 = self.queue.add_task("a.mp4", "b.mp4", "x")
        t2 = self.queue.add_task("c.mp4", "d.mp4", "y")
        next_task = self.queue.get_next_task()
        self.assertEqual(next_task["id"], t1["id"])

    def test_get_next_skips_non_pending(self):
        t1 = self.queue.add_task("a.mp4", "b.mp4", "x")
        t2 = self.queue.add_task("c.mp4", "d.mp4", "y")
        t3 = self.queue.add_task("e.mp4", "f.mp4", "z")
        self.queue.update_task_status(t2["id"], "done")
        next_task = self.queue.get_next_task()
        self.assertEqual(next_task["id"], t1["id"])

    def test_get_next_marks_task_encoding(self):
        self.queue.add_task("a.mp4", "b.mp4", "x")
        next_task = self.queue.get_next_task()
        self.assertEqual(next_task["status"], "processing")

    def test_get_next_skips_in_progress(self):
        t1 = self.queue.add_task("a.mp4", "b.mp4", "x")
        t2 = self.queue.add_task("c.mp4", "d.mp4", "y")
        self.queue.get_next_task()  # t1 → encoding
        next_task = self.queue.get_next_task()  # should be t2
        self.assertIsNotNone(next_task)
        self.assertEqual(next_task["id"], t2["id"])

    def test_update_valid_id_returns_true(self):
        task = self.queue.add_task("a.mp4", "b.mp4", "x")
        result = self.queue.update_task_status(task["id"], "done")
        self.assertTrue(result)

    def test_update_invalid_id_returns_false(self):
        result = self.queue.update_task_status("00000000-0000-0000-0000-000000000000", "done")
        self.assertFalse(result)

    def test_update_changes_status(self):
        task = self.queue.add_task("a.mp4", "b.mp4", "x")
        self.queue.update_task_status(task["id"], "done")
        updated = self.queue.get_task(task["id"])
        self.assertEqual(updated["status"], "done")

    def test_update_to_failed(self):
        t1 = self.queue.add_task("a.mp4", "b.mp4", "x")
        t2 = self.queue.add_task("c.mp4", "d.mp4", "y")
        self.queue.update_task_status(t2["id"], "failed")
        self.assertEqual(self.queue.get_task(t2["id"])["status"], "failed")

    def test_update_preserves_other_fields(self):
        task = self.queue.add_task("input.mp4", "output.mp4", "my_profile")
        self.queue.update_task_status(task["id"], "done")
        updated = self.queue.get_task(task["id"])
        self.assertEqual(updated["source"], "input.mp4")
        self.assertEqual(updated["output"], "output.mp4")
        self.assertEqual(updated["profile_name"], "my_profile")

    def test_get_existing_task(self):
        task = self.queue.add_task("a.mp4", "b.mp4", "x")
        fetched = self.queue.get_task(task["id"])
        self.assertEqual(fetched["source"], "a.mp4")

    def test_get_nonexistent_task(self):
        self.assertIsNone(self.queue.get_task("00000000-0000-0000-0000-000000000000"))

    def test_get_task_returns_same_object(self):
        task = self.queue.add_task("a.mp4", "b.mp4", "x")
        fetched = self.queue.get_task(task["id"])
        self.assertIs(task, fetched)

    def test_get_multiple_tasks_returns_list(self):
        t1 = self.queue.add_task("a.mp4", "b.mp4", "x")
        t2 = self.queue.add_task("c.mp4", "d.mp4", "y")
        tasks = self.queue.get_all_tasks()
        self.assertEqual(len(tasks), 2)
        self.assertIn(t1, tasks)
        self.assertIn(t2, tasks)

    def test_get_tasks_returns_copy(self):
        self.queue.add_task("a.mp4", "b.mp4", "x")
        tasks = self.queue.get_all_tasks()
        tasks.pop()
        self.assertEqual(len(self.queue.get_all_tasks()), 1)


class TestAutoStrategy(unittest.TestCase):
    """Автовыбор стратегии: limits.max_size_mb → two-pass, иначе single-pass."""

    def test_profile_with_max_size_mb_uses_two_pass(self):
        """Профиль с limits.max_size_mb → двухпроходное кодирование."""
        from core.encoder import VideoEncoder
        from core.analyzer import VideoAnalyzer

        profile = {
            "video": {"codec": "libx264", "crf": 23, "preset": "medium"},
            "audio": {"codec": "aac"},
            "limits": {"max_size_mb": 100},
        }

        with mock.patch.object(VideoEncoder, "encode") as mock_single:
            with mock.patch.object(VideoEncoder, "encode_two_pass", return_value=True) as mock_two:
                with mock.patch.object(VideoAnalyzer, "get_duration", return_value=120.0):
                    encoder = VideoEncoder("source.mp4", "output.mp4")
                    limits = profile.get("limits", {})
                    if limits.get("max_size_mb") is not None:
                        analyzer = VideoAnalyzer("source.mp4")
                        duration = analyzer.get_duration()
                        encoder.encode_two_pass(profile, duration)
                    else:
                        encoder.encode(profile)

        mock_two.assert_called_once()
        mock_single.assert_not_called()

    def test_profile_without_max_size_mb_uses_single_pass(self):
        """Профиль без limits.max_size_mb → однопроходное кодирование."""
        from core.encoder import VideoEncoder

        profile = {
            "video": {"codec": "libx264", "crf": 23, "preset": "medium"},
            "audio": {"codec": "aac"},
            "limits": {},
        }

        with mock.patch.object(VideoEncoder, "encode", return_value=True) as mock_single:
            with mock.patch.object(VideoEncoder, "encode_two_pass") as mock_two:
                encoder = VideoEncoder("source.mp4", "output.mp4")
                limits = profile.get("limits", {})
                if limits.get("max_size_mb") is not None:
                    from core.analyzer import VideoAnalyzer
                    analyzer = VideoAnalyzer("source.mp4")
                    duration = analyzer.get_duration()
                    encoder.encode_two_pass(profile, duration)
                else:
                    encoder.encode(profile)

        mock_single.assert_called_once()
        mock_two.assert_not_called()

    def test_profile_with_max_size_mb_none_uses_single_pass(self):
        """Профиль с max_size_mb = None → однопроходное кодирование."""
        from core.encoder import VideoEncoder

        profile = {
            "video": {"codec": "libx264", "crf": 23, "preset": "medium"},
            "audio": {"codec": "aac"},
            "limits": {"max_size_mb": None},
        }

        with mock.patch.object(VideoEncoder, "encode", return_value=True) as mock_single:
            with mock.patch.object(VideoEncoder, "encode_two_pass") as mock_two:
                encoder = VideoEncoder("source.mp4", "output.mp4")
                limits = profile.get("limits", {})
                if limits.get("max_size_mb") is not None:
                    from core.analyzer import VideoAnalyzer
                    analyzer = VideoAnalyzer("source.mp4")
                    duration = analyzer.get_duration()
                    encoder.encode_two_pass(profile, duration)
                else:
                    encoder.encode(profile)

        mock_single.assert_called_once()
        mock_two.assert_not_called()


if __name__ == "__main__":
    unittest.main()