import tempfile
import unittest
from pathlib import Path
import sys
import types

# PlatformIO's small Python distribution has no Tk bindings.  The core tests do
# not construct GUI objects, so provide only the class needed while importing.
try:
    import tkinter  # noqa: F401
except ModuleNotFoundError:
    tkinter_stub = types.ModuleType("tkinter")
    tkinter_stub.Tk = object
    tkinter_stub.Event = object
    tkinter_stub.messagebox = types.ModuleType("messagebox")
    tkinter_stub.ttk = types.ModuleType("ttk")
    sys.modules["tkinter"] = tkinter_stub
    sys.modules["tkinter.messagebox"] = tkinter_stub.messagebox
    sys.modules["tkinter.ttk"] = tkinter_stub.ttk

from test6 import (
    CORRECT_FACTOR,
    KEY_TO_POS,
    LESSONS,
    CharStats,
    KeyPos,
    ProgressStore,
    Scheduler,
    Session,
    State,
    TcodeEntry,
    lesson_chars,
    load_tcode_table,
    normalize_key,
)


class KeymapTests(unittest.TestCase):
    def test_all_40_keys_are_unique_and_valid(self):
        self.assertEqual(40, len(KEY_TO_POS))
        self.assertEqual(40, len(set(KEY_TO_POS.values())))
        for key, (x, y) in KEY_TO_POS.items():
            self.assertEqual(KeyPos(x, y), normalize_key(key))


class LessonTests(unittest.TestCase):
    def test_reference_values(self):
        self.assertEqual("、がの", LESSONS[1])
        self.assertEqual("せやよわ", LESSONS[10])
        self.assertEqual("", LESSONS[11])
        self.assertEqual("「」すそまり", LESSONS[12])
        self.assertEqual("ごひへべむ", LESSONS[101])
        self.assertEqual("ぱぴぷぺぽゃ", LESSONS[106])

    def test_union_has_no_duplicates(self):
        chars = lesson_chars(1, 10)
        self.assertEqual(len(chars), len(set(chars)))


class DataTests(unittest.TestCase):
    def test_lesson_characters_have_unique_valid_strokes(self):
        table = load_tcode_table()
        lesson_set = set("".join(LESSONS.values()))
        self.assertFalse(lesson_set - table.keys())
        strokes = {(entry.first, entry.second) for entry in table.values()}
        # The normalized dash alias intentionally shares the source stroke.
        self.assertGreaterEqual(len(strokes), len(table) - 1)


class StubRandom:
    def randint(self, start, end):
        return start

    def choices(self, population, weights, k):
        return [population[0]]


class SchedulerTests(unittest.TestCase):
    def test_recent_suppression_and_retry(self):
        stats = {char: CharStats() for char in "abc"}
        scheduler = Scheduler("abc", stats, StubRandom())
        self.assertEqual("a", scheduler.choose())
        self.assertEqual("b", scheduler.choose())
        scheduler.schedule_retry("a")
        scheduler.choose()
        scheduler.choose()
        scheduler.choose()
        self.assertEqual("a", scheduler.choose())


class SessionTests(unittest.TestCase):
    def make_session(self, clock_values):
        values = iter(clock_values)
        table = {"の": TcodeEntry(KeyPos(8, 3), KeyPos(3, 3))}
        return Session(table, ["の"], {}, 1, rng=StubRandom(), clock=lambda: next(values))

    def test_second_stroke_judges_correct(self):
        session = self.make_session([1.0, 1.2, 1.3])
        session.start()
        self.assertEqual("first", session.normal_input(KeyPos(8, 3)))
        self.assertEqual(State.WAIT_SECOND, session.state)
        self.assertEqual("correct", session.normal_input(KeyPos(3, 3)))
        self.assertEqual(1, session.correct)
        self.assertEqual(CORRECT_FACTOR, session.stats["の"].weight)

    def test_wrong_requires_complete_correction(self):
        session = self.make_session([1.0, 1.2, 1.3])
        session.start()
        session.normal_input(KeyPos(1, 1))
        self.assertEqual("wrong", session.normal_input(KeyPos(2, 1)))
        self.assertEqual(State.CORRECTION_FIRST, session.state)
        self.assertEqual("correction_restart", session.correction_input(KeyPos(1, 1)))
        self.assertEqual("correction_first", session.correction_input(KeyPos(8, 3)))
        self.assertEqual("correction_done", session.correction_input(KeyPos(3, 3)))
        self.assertEqual(0, session.correct)
        self.assertEqual(1, session.corrections)


class StorageTests(unittest.TestCase):
    def test_round_trip(self):
        with tempfile.TemporaryDirectory() as directory:
            store = ProgressStore(Path(directory) / "progress.json")
            store.save({"の": CharStats(attempts=2, correct_first_try=1)})
            loaded = store.load()
            self.assertEqual(2, loaded["の"].attempts)


if __name__ == "__main__":
    unittest.main()
