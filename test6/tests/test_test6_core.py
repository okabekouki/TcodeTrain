import tempfile
import unittest
from pathlib import Path
import random
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
    RandomSequenceCursor,
    Scheduler,
    SentenceCursor,
    Session,
    State,
    TcodeEntry,
    lesson_chars,
    load_lesson_texts,
    load_tcode_table,
    make_random_sequence,
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
        # Two Unicode dash aliases intentionally share the source stroke.
        self.assertGreaterEqual(len(strokes), len(table) - 2)

    def test_lesson_5_text_and_all_sentence_characters(self):
        texts = load_lesson_texts()
        self.assertEqual(
            "なにをしないでいたいの。ない。はい。いないが",
            texts[5][0],
        )
        table = load_tcode_table()
        for lines in texts.values():
            SentenceCursor(lines, table)


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


class RandomSequenceTests(unittest.TestCase):
    def test_exact_length_pool_membership_duplicates_and_seed(self):
        first = make_random_sequence("abc", 100, random.Random(1234))
        second = make_random_sequence("abc", 100, random.Random(1234))
        self.assertEqual(100, len(first))
        self.assertEqual(first, second)
        self.assertLessEqual(set(first), set("abc"))
        self.assertEqual(["あ"] * 100, make_random_sequence("あ", 100, random.Random(1)))
        self.assertEqual(1, len(make_random_sequence("abc", 1, random.Random(1))))

    def test_invalid_length_and_empty_pool(self):
        for length in (0, -1, 1001, True):
            with self.subTest(length=length), self.assertRaises(ValueError):
                make_random_sequence("abc", length, random.Random(1))
        with self.assertRaises(ValueError):
            make_random_sequence("", 1, random.Random(1))

    def test_unknown_character_is_rejected(self):
        table = {"あ": TcodeEntry(KeyPos(1, 1), KeyPos(2, 1))}
        with self.assertRaises(ValueError):
            RandomSequenceCursor("あ?", table)


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


class SentenceSessionTests(unittest.TestCase):
    def setUp(self):
        self.a = TcodeEntry(KeyPos(1, 1), KeyPos(2, 1))
        self.b = TcodeEntry(KeyPos(3, 1), KeyPos(4, 1))
        self.table = {"あ": self.a, "い": self.b}

    def make_session(self, lines, clock_values):
        values = iter(clock_values)
        return Session(self.table, (), {}, 0, rng=StubRandom(),
                       clock=lambda: next(values), sentence_lines=lines)

    @staticmethod
    def answer(session, entry):
        session.normal_input(entry.first)
        return session.normal_input(entry.second)

    def test_source_order_spaces_and_line_boundaries(self):
        session = self.make_session(["あ い", "あ"], [1, 2, 3, 4, 5, 6, 7, 8, 9, 10])
        session.start()
        self.assertEqual("あ", session.current)
        self.assertEqual("correct", self.answer(session, self.a))
        session.next_question()
        self.assertEqual("い", session.current)
        self.assertEqual("correct", self.answer(session, self.b))
        session.next_question()
        self.assertEqual("あ", session.current)
        self.assertEqual(1, session.sentence.line_index)
        self.assertEqual("correct", self.answer(session, self.a))
        session.next_question()
        self.assertEqual(State.RESULT, session.state)
        self.assertEqual(2, session.sentence.completed_lines)
        self.assertIsNone(session.scheduler)

    def test_wrong_stays_until_correction_then_advances(self):
        session = self.make_session(["あい"], [1, 2, 3, 4, 5, 6])
        session.start()
        session.normal_input(self.b.first)
        self.assertEqual("wrong", session.normal_input(self.b.second))
        self.assertEqual("あ", session.current)
        self.assertEqual(0, session.sentence.char_index)
        self.assertEqual("correction_first", session.correction_input(self.a.first))
        self.assertEqual("correction_done", session.correction_input(self.a.second))
        self.assertEqual("あ", session.current)
        session.next_question()
        self.assertEqual("い", session.current)
        self.assertEqual(1, session.stats["あ"].attempts)
        self.assertEqual(0, session.stats["あ"].correct_first_try)

    def test_unknown_non_separator_is_rejected(self):
        with self.assertRaises(ValueError):
            SentenceCursor(["あ?"], self.table)


class RandomSequenceSessionTests(unittest.TestCase):
    def setUp(self):
        self.a = TcodeEntry(KeyPos(1, 1), KeyPos(2, 1))
        self.b = TcodeEntry(KeyPos(3, 1), KeyPos(4, 1))
        self.table = {"あ": self.a, "い": self.b}

    def make_session(self, clock_values):
        values = iter(clock_values)
        return Session(self.table, (), {}, 0, clock=lambda: next(values),
                       random_sequence=["あ", "い"])

    def test_fixed_order_one_stroke_and_result(self):
        session = self.make_session([1, 2, 3, 4, 5, 6, 7])
        original = list(session.random_sequence.sequence)
        session.start()
        self.assertEqual("あ", session.current)
        session.normal_input(self.a.first)
        self.assertEqual(0, session.random_sequence.sequence_index)
        self.assertEqual("correct", session.normal_input(self.a.second))
        session.next_question()
        self.assertEqual(1, session.random_sequence.sequence_index)
        self.assertEqual("い", session.current)
        session.normal_input(self.b.first)
        self.assertEqual("correct", session.normal_input(self.b.second))
        session.next_question()
        self.assertEqual(State.RESULT, session.state)
        self.assertEqual(original, session.random_sequence.sequence)
        self.assertIsNone(session.scheduler)
        self.assertEqual(1, session.stats["あ"].correct_first_try)

    def test_wrong_waits_for_correction_and_has_no_retry_queue(self):
        session = self.make_session([1, 2, 3, 4])
        session.start()
        session.normal_input(self.b.first)
        self.assertEqual("wrong", session.normal_input(self.b.second))
        self.assertEqual(0, session.random_sequence.sequence_index)
        self.assertEqual("correction_first", session.correction_input(self.a.first))
        self.assertEqual("correction_done", session.correction_input(self.a.second))
        self.assertEqual(0, session.random_sequence.sequence_index)
        session.next_question()
        self.assertEqual(1, session.random_sequence.sequence_index)
        self.assertEqual("い", session.current)
        self.assertIsNone(session.scheduler)
        self.assertEqual(1, session.stats["あ"].wrong)


class StorageTests(unittest.TestCase):
    def test_round_trip(self):
        with tempfile.TemporaryDirectory() as directory:
            store = ProgressStore(Path(directory) / "progress.json")
            store.save({"の": CharStats(attempts=2, correct_first_try=1)})
            loaded = store.load()
            self.assertEqual(2, loaded["の"].attempts)


if __name__ == "__main__":
    unittest.main()
