"""TcodeTrain test6 - coordinate based two-stroke T-Code trainer."""

from __future__ import annotations

import json
import random
import re
import time
import tkinter as tk
from collections import Counter, deque
from dataclasses import asdict, dataclass
from datetime import datetime
from enum import Enum, auto
from pathlib import Path
from tkinter import messagebox, ttk
from typing import Callable, Iterable


APP_DIR = Path(__file__).resolve().parent
LEGACY_SOURCE = APP_DIR.parent / "tcodeData_Maker.py"
PROGRESS_PATH = APP_DIR / "user_data" / "progress.json"
LESSON_TEXT_PATH = APP_DIR / "data" / "lesson_texts.json"

KEY_ROWS = ("1234567890", "qwertyuiop", "asdfghjkl;", "zxcvbnm,./")
KEY_TO_POS = {
    key: (x, y)
    for y, row in enumerate(KEY_ROWS, 1)
    for x, key in enumerate(row, 1)
}

LESSONS: dict[int, str] = {
    1: "、がの", 2: "てと", 3: "でにはを", 4: "。たな", 5: "いしる",
    6: "（）おこども", 7: "られ", 8: "あうえ", 9: "かきくさっろ",
    10: "せやよわ", 11: "", 12: "「」すそまり", 13: "だちつ",
    14: "けみめん", 15: "げじずばほ", 16: "０１２３４５月時人",
    17: "―６７８９円月人日年分", 18: "―日", 19: "・時分",
    20: "ーアシストラリルレ", 21: "キコタナマ", 22: "イカクドフン",
    23: "ジッニバムロ", 24: "サチテパプュ", 25: "ウオグビメ",
    101: "ごひへべむ", 102: "ぞひびょ", 103: "ぎぐねふぶ",
    104: "ざづぬぼゅ", 105: "ぜぢ", 106: "ぱぴぷぺぽゃ",
}

CORRECT_FACTOR = 0.80
WRONG_FACTOR = 1.60
MIN_WEIGHT = 0.25
MAX_WEIGHT = 8.0
RECENT_LIMIT = 2
RETRY_MIN = 3
RETRY_MAX = 7
MAX_RANDOM_SEQUENCE_LENGTH = 1000


@dataclass(frozen=True, order=True)
class KeyPos:
    x: int
    y: int

    def __post_init__(self) -> None:
        if not (1 <= self.x <= 10 and 1 <= self.y <= 4):
            raise ValueError(f"invalid key position: ({self.x}, {self.y})")

    def label(self) -> str:
        return f"({self.x},{self.y})"


@dataclass(frozen=True)
class TcodeEntry:
    first: KeyPos
    second: KeyPos


@dataclass
class CharStats:
    weight: float = 1.0
    attempts: int = 0
    correct_first_try: int = 0
    wrong: int = 0
    avg_first_ms: float | None = None
    avg_second_ms: float | None = None
    last_seen: str | None = None

    @classmethod
    def from_dict(cls, value: object) -> "CharStats":
        if not isinstance(value, dict):
            return cls()
        defaults = asdict(cls())
        clean = {key: value.get(key, default) for key, default in defaults.items()}
        try:
            return cls(**clean)
        except (TypeError, ValueError):
            return cls()


class State(Enum):
    SETUP = auto()
    WAIT_FIRST = auto()
    WAIT_SECOND = auto()
    CORRECT_FEEDBACK = auto()
    CORRECTION_FIRST = auto()
    CORRECTION_SECOND = auto()
    PAUSED = auto()
    RESULT = auto()


def normalize_key(char: str) -> KeyPos | None:
    """Convert a Tk key event character to a physical T-Code coordinate."""
    if not char:
        return None
    return KeyPos(*KEY_TO_POS[char.lower()]) if char.lower() in KEY_TO_POS else None


def lesson_chars(start: int, end: int | None = None) -> list[str]:
    """Return a stable, duplicate-free union of lesson characters."""
    end = start if end is None else end
    numbers = [number for number in sorted(LESSONS) if start <= number <= end]
    return list(dict.fromkeys("".join(LESSONS[number] for number in numbers)))


def make_random_sequence(
    chars: Iterable[str],
    length: int,
    rng: random.Random | None = None,
) -> list[str]:
    """Generate a fixed-length sequence with replacement from the given pool."""
    pool = list(dict.fromkeys(chars))
    if not pool:
        raise ValueError("ランダム列の候補文字がありません")
    if not isinstance(length, int) or isinstance(length, bool) or not (1 <= length <= MAX_RANDOM_SEQUENCE_LENGTH):
        raise ValueError(f"文字数は1～{MAX_RANDOM_SEQUENCE_LENGTH}の整数にしてください")
    generator = rng or random.Random()
    return [generator.choice(pool) for _ in range(length)]


def load_lesson_texts(path: Path = LESSON_TEXT_PATH) -> dict[int, list[str]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("文章Lessonデータの形式が不正です")
    result: dict[int, list[str]] = {}
    for number, lines in data.items():
        if not isinstance(lines, list) or not lines or not all(isinstance(line, str) for line in lines):
            raise ValueError(f"Lesson {number} の文章データが不正です")
        result[int(number)] = lines
    return result


def _extract_legacy_tables(source: str) -> dict[str, str]:
    pattern = re.compile(r'^(TCODE_RAW[1-4])\s*=\s*"""(.*?)"""', re.MULTILINE | re.DOTALL)
    tables = dict(pattern.findall(source))
    if len(tables) != 4:
        raise ValueError("T-Code元表を4面とも読み取れませんでした")
    return tables


def load_tcode_table(path: Path = LEGACY_SOURCE) -> dict[str, TcodeEntry]:
    """Normalize the human-readable legacy table without importing its script."""
    tables = _extract_legacy_tables(path.read_text(encoding="utf-8"))
    hand_modes = {
        "TCODE_RAW1": (0, 0), "TCODE_RAW2": (1, 0),
        "TCODE_RAW3": (0, 1), "TCODE_RAW4": (1, 1),
    }
    result: dict[str, TcodeEntry] = {}
    strokes: dict[tuple[KeyPos, KeyPos], str] = {}
    for table_name, table in tables.items():
        first_right, second_right = hand_modes[table_name]
        lines = [line for line in table.splitlines() if line.strip()]
        if len(lines) != 16:
            raise ValueError(f"{table_name}: 16行ではありません")
        for global_y, line in enumerate(lines):
            blocks = re.findall(r'"(.{5})"', line)
            if len(blocks) != 5:
                raise ValueError(f"{table_name}: 表の列数が不正です")
            for global_x, block in enumerate(blocks):
                for local_x, char in enumerate(block):
                    if char in {"●", "◆"}:
                        continue
                    first = KeyPos(local_x + 1 + first_right * 5, global_y % 4 + 1)
                    second = KeyPos(global_x + 1 + second_right * 5, global_y // 4 + 1)
                    stroke = (first, second)
                    if stroke in strokes and strokes[stroke] != char:
                        raise ValueError(f"打鍵重複: {strokes[stroke]} / {char}")
                    if char in result and result[char] != TcodeEntry(first, second):
                        raise ValueError(f"文字重複: {char}")
                    strokes[stroke] = char
                    result[char] = TcodeEntry(first, second)

    # The source table uses the typographic full-width minus for this dash.
    if "―" not in result and "－" in result:
        result["―"] = result["－"]
    if "—" not in result and "－" in result:
        result["—"] = result["－"]
    missing = sorted(set("".join(LESSONS.values())) - result.keys())
    if missing:
        raise ValueError("Lesson文字がT-Code表にありません: " + " ".join(missing))
    return result


class ProgressStore:
    def __init__(self, path: Path = PROGRESS_PATH):
        self.path = path

    def load(self) -> dict[str, CharStats]:
        if not self.path.exists():
            return {}
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
            if not isinstance(data, dict) or not isinstance(data.get("chars", {}), dict):
                raise ValueError("invalid progress schema")
            return {char: CharStats.from_dict(value) for char, value in data["chars"].items()}
        except (OSError, UnicodeError, json.JSONDecodeError, ValueError):
            stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
            backup = self.path.with_name(f"progress.corrupt-{stamp}.json")
            try:
                self.path.replace(backup)
            except OSError:
                pass
            return {}

    def save(self, stats: dict[str, CharStats]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = {"version": 1, "chars": {char: asdict(value) for char, value in sorted(stats.items())}}
        temporary = self.path.with_suffix(".tmp")
        serialized = json.dumps(payload, ensure_ascii=False, indent=2)
        temporary.write_text(serialized, encoding="utf-8")
        try:
            temporary.replace(self.path)
        except OSError:
            # Some restricted Windows folders reject atomic replace even when
            # ordinary writes are allowed. Preserve functionality there.
            self.path.write_text(serialized, encoding="utf-8")
            try:
                temporary.unlink()
            except OSError:
                pass


class Scheduler:
    def __init__(self, chars: Iterable[str], stats: dict[str, CharStats], rng: random.Random | None = None):
        self.chars = list(dict.fromkeys(chars))
        if not self.chars:
            raise ValueError("出題できる文字がありません")
        self.stats = stats
        self.rng = rng or random.Random()
        self.recent: deque[str] = deque(maxlen=RECENT_LIMIT)
        self.retries: list[tuple[int, str]] = []
        self.question_index = 0

    def schedule_retry(self, char: str) -> None:
        due = self.question_index + self.rng.randint(RETRY_MIN, RETRY_MAX)
        self.retries.append((due, char))

    def choose(self) -> str:
        due = [(index, char) for index, char in self.retries if index <= self.question_index]
        if due:
            _, chosen = min(due)
            self.retries.remove(min(due))
        else:
            candidates = [char for char in self.chars if char not in self.recent]
            if not candidates:
                candidates = [char for char in self.chars if not self.recent or char != self.recent[-1]]
            if not candidates:
                candidates = self.chars
            weights = [self.stats.setdefault(char, CharStats()).weight for char in candidates]
            chosen = self.rng.choices(candidates, weights=weights, k=1)[0]
        self.recent.append(chosen)
        self.question_index += 1
        return chosen


class SentenceCursor:
    """Supply T-Code characters in lesson-text order, skipping ASCII spaces."""

    SEPARATORS = {" "}

    def __init__(self, lines: Iterable[str], table: dict[str, TcodeEntry]):
        self.lines = list(lines)
        if not self.lines:
            raise ValueError("文章Lessonに練習行がありません")
        unknown = sorted({char for line in self.lines for char in line
                          if char not in table and char not in self.SEPARATORS})
        if unknown:
            raise ValueError("文章にT-Code未対応文字があります: " + " ".join(unknown))
        self.line_index = 0
        self.char_index = 0
        self.done = False
        self._skip_separators_and_empty_lines()

    @property
    def current(self) -> str:
        if self.done:
            raise IndexError("sentence is complete")
        return self.lines[self.line_index][self.char_index]

    @property
    def total_chars(self) -> int:
        return sum(char not in self.SEPARATORS for line in self.lines for char in line)

    @property
    def completed_lines(self) -> int:
        return len(self.lines) if self.done else self.line_index

    def advance(self) -> None:
        if self.done:
            return
        self.char_index += 1
        self._skip_separators_and_empty_lines()

    def _skip_separators_and_empty_lines(self) -> None:
        while self.line_index < len(self.lines):
            line = self.lines[self.line_index]
            while self.char_index < len(line) and line[self.char_index] in self.SEPARATORS:
                self.char_index += 1
            if self.char_index < len(line):
                return
            self.line_index += 1
            self.char_index = 0
        self.done = True


class RandomSequenceCursor:
    """Keep a generated random sequence in its original fixed order."""

    def __init__(self, sequence: Iterable[str], table: dict[str, TcodeEntry]):
        self.sequence = list(sequence)
        if not self.sequence:
            raise ValueError("ランダム列が空です")
        unknown = sorted(set(self.sequence) - table.keys())
        if unknown:
            raise ValueError("ランダム列にT-Code未対応文字があります: " + " ".join(unknown))
        self.sequence_index = 0
        self.done = False

    @property
    def current(self) -> str:
        if self.done:
            raise IndexError("random sequence is complete")
        return self.sequence[self.sequence_index]

    def advance(self) -> None:
        if self.done:
            return
        self.sequence_index += 1
        self.done = self.sequence_index >= len(self.sequence)


class Session:
    def __init__(
        self,
        table: dict[str, TcodeEntry],
        chars: Iterable[str],
        stats: dict[str, CharStats],
        question_limit: int,
        rng: random.Random | None = None,
        clock: Callable[[], float] = time.perf_counter,
        sentence_lines: Iterable[str] | None = None,
        random_sequence: Iterable[str] | None = None,
    ):
        if sentence_lines is not None and random_sequence is not None:
            raise ValueError("文章とランダム列は同時に指定できません")
        self.table = table
        self.stats = stats
        self.sentence = SentenceCursor(sentence_lines, table) if sentence_lines is not None else None
        self.random_sequence = RandomSequenceCursor(random_sequence, table) if random_sequence is not None else None
        if self.sentence:
            self.limit = self.sentence.total_chars
        elif self.random_sequence:
            self.limit = len(self.random_sequence.sequence)
        else:
            self.limit = question_limit
        self.scheduler = None if self.sentence or self.random_sequence else Scheduler(chars, stats, rng)
        self.clock = clock
        self.state = State.SETUP
        self.current = ""
        self.first_input: KeyPos | None = None
        self.t0 = self.t1 = 0.0
        self.completed = self.correct = self.corrections = 0
        self.timings: list[tuple[str, float, float, float]] = []
        self.wrong_chars: Counter[str] = Counter()
        self.started_at = self.finished_at = 0.0
        self._advance_fixed = False

    @property
    def is_sentence(self) -> bool:
        return self.sentence is not None

    @property
    def is_random_sequence(self) -> bool:
        return self.random_sequence is not None

    @property
    def entry(self) -> TcodeEntry:
        return self.table[self.current]

    def start(self) -> None:
        self.next_question()

    def next_question(self) -> None:
        if self._advance_fixed:
            if self.sentence:
                self.sentence.advance()
            elif self.random_sequence:
                self.random_sequence.advance()
            self._advance_fixed = False
        if self.sentence and self.sentence.done:
            self.finished_at = self.clock()
            self.state = State.RESULT
            return
        if self.random_sequence and self.random_sequence.done:
            self.finished_at = self.clock()
            self.state = State.RESULT
            return
        if self.completed >= self.limit:
            self.finished_at = self.clock()
            self.state = State.RESULT
            return
        if self.sentence:
            self.current = self.sentence.current
        elif self.random_sequence:
            self.current = self.random_sequence.current
        else:
            assert self.scheduler is not None
            self.current = self.scheduler.choose()
        self.first_input = None
        self.t0 = self.clock()
        if not self.started_at:
            self.started_at = self.t0
        self.state = State.WAIT_FIRST

    def normal_input(self, pos: KeyPos) -> str:
        if self.state == State.WAIT_FIRST:
            self.first_input = pos
            self.t1 = self.clock()
            self.state = State.WAIT_SECOND
            return "first"
        if self.state != State.WAIT_SECOND or self.first_input is None:
            return "ignored"
        t2 = self.clock()
        correct = (self.first_input, pos) == (self.entry.first, self.entry.second)
        first_ms = (self.t1 - self.t0) * 1000
        second_ms = (t2 - self.t1) * 1000
        self.timings.append((self.current, first_ms, second_ms, first_ms + second_ms))
        stat = self.stats.setdefault(self.current, CharStats())
        old_attempts = stat.attempts
        stat.attempts += 1
        stat.last_seen = datetime.now().astimezone().isoformat(timespec="seconds")
        stat.avg_first_ms = _running_average(stat.avg_first_ms, old_attempts, first_ms)
        stat.avg_second_ms = _running_average(stat.avg_second_ms, old_attempts, second_ms)
        self.completed += 1
        if correct:
            stat.correct_first_try += 1
            stat.weight = max(MIN_WEIGHT, stat.weight * CORRECT_FACTOR)
            self.correct += 1
            self._advance_fixed = self.sentence is not None or self.random_sequence is not None
            self.state = State.CORRECT_FEEDBACK
            return "correct"
        stat.wrong += 1
        stat.weight = min(MAX_WEIGHT, stat.weight * WRONG_FACTOR)
        self.wrong_chars[self.current] += 1
        if self.scheduler is not None:
            self.scheduler.schedule_retry(self.current)
        self.state = State.CORRECTION_FIRST
        return "wrong"

    def correction_input(self, pos: KeyPos) -> str:
        if self.state == State.CORRECTION_FIRST:
            if pos == self.entry.first:
                self.state = State.CORRECTION_SECOND
                return "correction_first"
            return "correction_restart"
        if self.state == State.CORRECTION_SECOND:
            if pos == self.entry.second:
                self.corrections += 1
                self._advance_fixed = self.sentence is not None or self.random_sequence is not None
                return "correction_done"
            self.state = State.CORRECTION_FIRST
            return "correction_restart"
        return "ignored"

    def cancel_first(self) -> bool:
        if self.state == State.WAIT_SECOND:
            self.first_input = None
            self.state = State.WAIT_FIRST
            return True
        if self.state == State.CORRECTION_SECOND:
            self.state = State.CORRECTION_FIRST
            return True
        return False


def _running_average(old: float | None, old_count: int, new: float) -> float:
    return new if old is None or old_count <= 0 else (old * old_count + new) / (old_count + 1)


class TcodeTrainApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("TcodeTrain test6")
        self.geometry("900x680")
        self.minsize(760, 600)
        self.store = ProgressStore()
        self.stats = self.store.load()
        self.lesson_texts: dict[int, list[str]] = {}
        self.session: Session | None = None
        self.table: dict[str, TcodeEntry] = {}
        self.feedback_job: str | None = None
        self.protocol("WM_DELETE_WINDOW", self.close)
        try:
            self.table = load_tcode_table()
            self.lesson_texts = load_lesson_texts()
        except (OSError, UnicodeError, ValueError) as exc:
            messagebox.showerror("データエラー", str(exc), parent=self)
            self.after_idle(self.destroy)
            return
        self.show_setup()

    def clear(self) -> ttk.Frame:
        if self.feedback_job:
            self.after_cancel(self.feedback_job)
            self.feedback_job = None
        self.unbind("<KeyPress>")
        for child in self.winfo_children():
            child.destroy()
        frame = ttk.Frame(self, padding=24)
        frame.pack(fill="both", expand=True)
        return frame

    def show_setup(self) -> None:
        frame = self.clear()
        ttk.Label(frame, text="TcodeTrain test6", font=("Yu Gothic UI", 28, "bold")).pack(pady=(10, 24))
        form = ttk.Frame(frame)
        form.pack()
        lesson_values = [str(number) for number in sorted(LESSONS)]
        self.mode_var = tk.StringVar(value="Lesson範囲")
        self.form_var = tk.StringVar(value="単字")
        self.start_var = tk.StringVar(value="1")
        self.end_var = tk.StringVar(value="5")
        self.count_var = tk.IntVar(value=30)
        self.hint_var = tk.IntVar(value=1)
        self.direct_var = tk.StringVar()
        rows = [
            ("練習形式", ttk.Combobox(form, textvariable=self.form_var, state="readonly", width=22,
             values=("単字", "文章", "ランダム n 文字"))),
            ("練習モード", ttk.Combobox(form, textvariable=self.mode_var, state="readonly", width=22,
             values=("単一Lesson", "Lesson範囲", "苦手文字", "文字直接指定", "全対象文字"))),
            ("開始Lesson", ttk.Combobox(form, textvariable=self.start_var, state="readonly", width=22, values=lesson_values)),
            ("終了Lesson", ttk.Combobox(form, textvariable=self.end_var, state="readonly", width=22, values=lesson_values)),
            ("直接指定", ttk.Entry(form, textvariable=self.direct_var, width=25)),
            ("出題数 / 文字数 n", ttk.Spinbox(form, from_=1, to=MAX_RANDOM_SEQUENCE_LENGTH,
                                      textvariable=self.count_var, width=23)),
            ("ヒント", ttk.Combobox(form, textvariable=self.hint_var, state="readonly", width=22,
             values=(0, 1, 2, 3))),
        ]
        for row, (label, widget) in enumerate(rows):
            ttk.Label(form, text=label).grid(row=row, column=0, sticky="e", padx=8, pady=7)
            widget.grid(row=row, column=1, sticky="w", padx=8, pady=7)
        ttk.Label(frame, text="ヒント: 0=なし / 1=誤答時 / 2=第1打鍵 / 3=両打鍵").pack(pady=10)
        buttons = ttk.Frame(frame)
        buttons.pack(pady=20)
        ttk.Button(buttons, text="練習開始", command=self.begin).pack(side="left", padx=8)
        ttk.Button(buttons, text="成績を見る", command=self.show_progress).pack(side="left", padx=8)

    def selected_chars(self) -> tuple[list[str], str]:
        mode = self.mode_var.get()
        if mode == "単一Lesson":
            number = int(self.start_var.get())
            return lesson_chars(number), f"Lesson {number}"
        if mode == "Lesson範囲":
            start, end = int(self.start_var.get()), int(self.end_var.get())
            if start > end:
                raise ValueError("開始Lessonは終了Lesson以下にしてください")
            return lesson_chars(start, end), f"Lesson {start}-{end}"
        if mode == "苦手文字":
            chars = [char for char, stat in self.stats.items()
                     if char in self.table and (stat.weight >= 1.5 or
                     (stat.attempts and stat.correct_first_try / stat.attempts < 0.85))]
            return chars, "苦手文字"
        if mode == "文字直接指定":
            requested = list(dict.fromkeys(self.direct_var.get().strip()))
            unknown = [char for char in requested if char not in self.table]
            if unknown:
                raise ValueError("T-Code表にない文字: " + " ".join(unknown))
            return requested, "文字直接指定"
        return lesson_chars(min(LESSONS), max(LESSONS)), "全対象文字"

    def begin(self) -> None:
        try:
            if self.form_var.get() == "文章":
                lesson = int(self.start_var.get())
                if lesson < 5 or lesson not in self.lesson_texts:
                    raise ValueError("文章モードは本文のあるLesson 5以降を選んでください")
                lines = self.lesson_texts[lesson]
                self.session_label = f"文章 Lesson {lesson}"
                self.session = Session(self.table, (), self.stats, 0, sentence_lines=lines)
            elif self.form_var.get() == "ランダム n 文字":
                if self.mode_var.get() not in {"単一Lesson", "Lesson範囲", "文字直接指定"}:
                    raise ValueError("ランダム n 文字では単一Lesson・Lesson範囲・文字直接指定を選んでください")
                chars, source_label = self.selected_chars()
                length = int(self.count_var.get())
                sequence = make_random_sequence(chars, length)
                self.session_label = f"ランダム {length}文字（{source_label}）"
                self.session = Session(self.table, (), self.stats, 0, random_sequence=sequence)
            else:
                chars, self.session_label = self.selected_chars()
                if not chars:
                    raise ValueError("この条件には練習対象がありません")
                limit = int(self.count_var.get())
                if limit < 1:
                    raise ValueError("出題数は1以上にしてください")
                self.session = Session(self.table, chars, self.stats, limit)
        except (TypeError, ValueError) as exc:
            messagebox.showwarning("設定を確認してください", str(exc), parent=self)
            return
        self.build_training()
        self.session.start()
        self.render_question()

    def build_training(self) -> None:
        frame = self.clear()
        self.bind("<KeyPress>", self.on_key)
        top = ttk.Frame(frame)
        top.pack(fill="x")
        self.session_text = ttk.Label(top, text=self.session_label)
        self.session_text.pack(side="left")
        self.progress_text = ttk.Label(top)
        self.progress_text.pack(side="right")
        self.char_text = ttk.Label(frame, font=("Yu Gothic UI", 72, "bold"), anchor="center")
        self.char_text.pack(pady=(48, 12))
        self.sentence_text = tk.Text(frame, height=3, wrap="word", font=("Yu Gothic UI", 19),
                                     relief="flat", borderwidth=0, cursor="arrow")
        self.sentence_text.tag_configure("current", background="#ffd966", underline=True,
                                         font=("Yu Gothic UI", 21, "bold"))
        if self.session and (self.session.is_sentence or self.session.is_random_sequence):
            self.char_text.pack_forget()
            self.sentence_text.pack(fill="x", padx=30, pady=(38, 12))
        self.status_text = ttk.Label(frame, font=("Yu Gothic UI", 16), anchor="center")
        self.status_text.pack(pady=6)
        self.detail_text = ttk.Label(frame, font=("Yu Gothic UI", 12), anchor="center", justify="center")
        self.detail_text.pack(pady=5)
        grid = ttk.Frame(frame)
        grid.pack(pady=24)
        self.key_labels: dict[KeyPos, ttk.Label] = {}
        for y in range(1, 5):
            for x in range(1, 11):
                pos = KeyPos(x, y)
                label = ttk.Label(grid, text=f"{x},{y}", anchor="center", relief="solid", width=7, padding=7)
                label.grid(row=y - 1, column=x - 1, padx=2, pady=2)
                self.key_labels[pos] = label
        ttk.Label(frame, text="Esc: 一時停止　Backspace: 1打目を取り消す").pack(side="bottom")
        self.focus_force()

    def reset_keys(self) -> None:
        for label in self.key_labels.values():
            label.configure(text=label.cget("text").replace(" ①", "").replace(" ②", ""))

    def mark_answer(self, entry: TcodeEntry) -> None:
        self.reset_keys()
        self.key_labels[entry.first].configure(text=f"{entry.first.x},{entry.first.y} ①")
        self.key_labels[entry.second].configure(text=f"{entry.second.x},{entry.second.y} ②")

    def render_question(self) -> None:
        assert self.session is not None
        if self.session.state == State.RESULT:
            self.store.save(self.stats)
            self.show_result()
            return
        self.reset_keys()
        if self.session.is_sentence:
            assert self.session.sentence is not None
            cursor = self.session.sentence
            line = cursor.lines[cursor.line_index]
            self.sentence_text.configure(state="normal")
            self.sentence_text.delete("1.0", "end")
            self.sentence_text.insert("1.0", line)
            start = f"1.{cursor.char_index}"
            self.sentence_text.tag_add("current", start, f"{start}+1c")
            self.sentence_text.see(start)
            self.sentence_text.configure(state="disabled")
        elif self.session.is_random_sequence:
            assert self.session.random_sequence is not None
            cursor = self.session.random_sequence
            sequence = "".join(cursor.sequence)
            self.sentence_text.configure(state="normal")
            self.sentence_text.delete("1.0", "end")
            self.sentence_text.insert("1.0", sequence)
            start = f"1.{cursor.sequence_index}"
            self.sentence_text.tag_add("current", start, f"{start}+1c")
            self.sentence_text.see(start)
            self.sentence_text.configure(state="disabled")
        else:
            self.char_text.configure(text=self.session.current)
        self.status_text.configure(text="第1打鍵待ち")
        entry = self.session.entry
        hint = self.hint_var.get()
        if hint == 2:
            self.detail_text.configure(text=f"第1打鍵: {entry.first.label()}")
            self.key_labels[entry.first].configure(text=f"{entry.first.x},{entry.first.y} ①")
        elif hint == 3:
            self.detail_text.configure(text=f"{entry.first.label()} → {entry.second.label()}")
            self.mark_answer(entry)
        else:
            self.detail_text.configure(text="")
        done, total = self.session.completed, self.session.limit
        rate = self.session.correct / done * 100 if done else 0
        if self.session.is_sentence and self.session.sentence:
            line = self.session.sentence.line_index + 1
            line_total = len(self.session.sentence.lines)
            self.progress_text.configure(
                text=f"行 {line}/{line_total}　{done}/{total}文字　初回正答率 {rate:.0f}%"
            )
        elif self.session.is_random_sequence:
            self.progress_text.configure(text=f"{done}/{total}文字　初回正答率 {rate:.0f}%")
        else:
            self.progress_text.configure(text=f"{done} / {total}　初回正答率 {rate:.0f}%")

    def on_key(self, event: tk.Event) -> str | None:
        assert self.session is not None
        if event.keysym == "Escape":
            if self.session.state == State.PAUSED:
                self.session.state = self.paused_from
                self.status_text.configure(text="再開しました")
            elif self.session.state in {State.WAIT_FIRST, State.WAIT_SECOND, State.CORRECTION_FIRST, State.CORRECTION_SECOND}:
                self.paused_from = self.session.state
                self.session.state = State.PAUSED
                self.status_text.configure(text="一時停止中（Escで再開）")
            return "break"
        if self.session.state == State.PAUSED:
            return "break"
        if event.keysym == "BackSpace":
            if self.session.cancel_first():
                self.status_text.configure(text="第1打鍵待ち")
            return "break"
        pos = normalize_key(event.char)
        if pos is None:
            return None
        if self.session.state in {State.WAIT_FIRST, State.WAIT_SECOND}:
            entered_first = self.session.first_input
            outcome = self.session.normal_input(pos)
            if outcome == "first":
                self.status_text.configure(text="第2打鍵待ち")
            elif outcome == "correct":
                self.status_text.configure(text="正解")
                self.detail_text.configure(text="")
                self.feedback_job = self.after(300, self.advance)
            elif outcome == "wrong":
                assert entered_first is not None
                answer = self.session.entry
                self.mark_answer(answer)
                self.status_text.configure(text="誤答：正しい2打鍵を入力してください")
                self.detail_text.configure(
                    text=f"入力: {entered_first.label()} → {pos.label()}\n"
                         f"正解: {answer.first.label()} → {answer.second.label()}"
                )
        elif self.session.state in {State.CORRECTION_FIRST, State.CORRECTION_SECOND}:
            outcome = self.session.correction_input(pos)
            if outcome == "correction_first":
                self.status_text.configure(text="訂正：第2打鍵待ち")
            elif outcome == "correction_restart":
                self.status_text.configure(text="違います。訂正を第1打鍵からやり直してください")
            elif outcome == "correction_done":
                self.status_text.configure(text="訂正完了")
                self.feedback_job = self.after(300, self.advance)
        return "break"

    def advance(self) -> None:
        self.feedback_job = None
        assert self.session is not None
        self.session.next_question()
        self.render_question()

    def show_result(self) -> None:
        assert self.session is not None
        frame = self.clear()
        ttk.Label(frame, text="練習結果", font=("Yu Gothic UI", 28, "bold")).pack(pady=20)
        count = self.session.completed
        averages = [sum(values) / len(values) if values else 0.0 for values in (
            [x[1] for x in self.session.timings], [x[2] for x in self.session.timings],
            [x[3] for x in self.session.timings],
        )]
        lines = (
            f"出題数: {count}", f"初回正解: {self.session.correct}",
            f"初回正答率: {self.session.correct / count * 100 if count else 0:.1f}%",
            f"訂正完了数: {self.session.corrections}", f"平均総反応時間: {averages[2]:.0f} ms",
            f"平均第1打鍵: {averages[0]:.0f} ms", f"平均第2打鍵間隔: {averages[1]:.0f} ms",
        )
        if (self.session.is_sentence and self.session.sentence) or self.session.is_random_sequence:
            elapsed = max(0.0, self.session.finished_at - self.session.started_at)
            per_minute = count / elapsed * 60 if elapsed else 0.0
            if self.session.is_sentence and self.session.sentence:
                lines += (f"完了行数: {self.session.sentence.completed_lines}",)
            else:
                lines += (f"指定文字数: {self.session.limit}",)
            lines += (f"総所要時間: {elapsed:.1f} 秒", f"入力速度: {per_minute:.1f} 文字/分")
        ttk.Label(frame, text="\n".join(lines), font=("Yu Gothic UI", 14), justify="left").pack(pady=12)
        wrong = "、".join(f"{char}({number})" for char, number in self.session.wrong_chars.most_common(8)) or "なし"
        slow = sorted(self.session.timings, key=lambda item: item[3], reverse=True)[:5]
        slow_text = "、".join(f"{char}({total:.0f}ms)" for char, _, _, total in slow) or "なし"
        ttk.Label(frame, text=f"誤答上位: {wrong}\n反応が遅かった問題: {slow_text}", justify="left").pack(pady=12)
        ttk.Button(frame, text="設定へ戻る", command=self.show_setup).pack(pady=20)

    def show_progress(self) -> None:
        window = tk.Toplevel(self)
        window.title("文字別成績")
        window.geometry("680x440")
        columns = ("char", "attempts", "rate", "weight", "first", "second")
        tree = ttk.Treeview(window, columns=columns, show="headings")
        headings = ("文字", "回数", "正答率", "重み", "第1打鍵ms", "第2打鍵ms")
        for column, heading in zip(columns, headings):
            tree.heading(column, text=heading)
            tree.column(column, width=95, anchor="center")
        for char, stat in sorted(self.stats.items(), key=lambda item: (-item[1].weight, item[0])):
            rate = stat.correct_first_try / stat.attempts * 100 if stat.attempts else 0
            tree.insert("", "end", values=(char, stat.attempts, f"{rate:.0f}%", f"{stat.weight:.2f}",
                        _number(stat.avg_first_ms), _number(stat.avg_second_ms)))
        tree.pack(fill="both", expand=True, padx=12, pady=12)

    def close(self) -> None:
        try:
            self.store.save(self.stats)
        except OSError as exc:
            messagebox.showwarning("保存エラー", str(exc), parent=self)
        self.destroy()


def _number(value: float | None) -> str:
    return "-" if value is None else f"{value:.0f}"


def main() -> None:
    app = TcodeTrainApp()
    app.mainloop()


if __name__ == "__main__":
    main()
