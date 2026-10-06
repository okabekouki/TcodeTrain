# AGENTS.md — TcodeTrain test6

## Scope

This file applies to everything under `test6/`.

Treat `test6/` as the implementation root for the new TcodeTrain version.

The repository root contains the legacy experiments `test1.py` through `test5.py`, `PCkey.py`, `tcodeData_Maker.py`, and related files. These are reference material. Do not modify legacy files unless the task explicitly requires it.

When `TcodeTrain_test6_spec.md` shows paths such as:

```
main.py
tcode/
gui/
data/
tools/
tests/
user_data/
```

interpret them as:

```
test6/main.py
test6/tcode/
test6/gui/
test6/data/
test6/tools/
test6/tests/
test6/user_data/
```

All new test6 implementation files should normally live under `test6/`.

---

# Source of truth

Read `test6/TcodeTrain_test6_spec.md` before making implementation changes.

Priority when requirements conflict:

1. Explicit instructions from the user in the current task
2. This `AGENTS.md`
3. `test6/TcodeTrain_test6_spec.md`
4. Existing test6 implementation
5. Legacy `test1.py`–`test5.py` behavior

Do not silently preserve legacy behavior when it conflicts with the test6 specification.

---

# Project goal

TcodeTrain test6 is a Python GUI trainer for T-Code.

The important learning model is:

```
displayed character
    ->
two physical key positions
    ->
two-stroke motor action
```

The program must not encourage memorizing QWERTY key names as the primary representation.

The coordinate display is a temporary learning aid. The eventual goal is direct character-to-motion recall.

---

# Required technology

- Python 3
- GUI: `tkinter` / `ttk`
- Prefer the Python standard library
- Avoid adding external dependencies unless there is a strong technical reason
- Windows is the primary target
- Keep non-input core logic portable where practical

Do not replace tkinter with another GUI framework without an explicit request.

---

# Keyboard coordinate model

The T-Code input area is 10 columns by 4 rows.

```text
       x ->
       1  2  3  4  5  6  7  8  9  10

y=1    1  2  3  4  5  6  7  8  9   0
y=2    Q  W  E  R  T  Y  U  I  O   P
y=3    A  S  D  F  G  H  J  K  L   ;
y=4    Z  X  C  V  B  N  M  ,  .   /
```

Internally represent a key position structurally, for example:

```python
(8, 3)
```

or:

```python
KeyPos(x=8, y=3)
```

Never introduce packed coordinate integers such as `83` or `103` in new code.

The legacy packed representation may be read only while converting old data.

---

# T-Code input behavior

Normal training input must be captured from key events directly.

Do not use a text entry field plus Space/Enter as the normal answer mechanism.

Expected flow:

```
WAIT_FIRST
  -> first valid key
WAIT_SECOND
  -> second valid key
automatic judgement
```

The second valid T-Code key completes the answer.

QWERTY letters should not normally be displayed as the learner's answer.

Special keys such as Escape and Backspace may perform control functions as defined by the specification.

---

# Lesson data

Lesson numbering must follow eelll/JS T-Code standard lesson data.

Authoritative references:

- https://miau.github.io/eljs/eellljs.html
- https://github.com/miau/eljs/blob/master/js/lt/eellltxt.js

For the initial test6 target, support the lesson groups defined in the specification:

- Lessons 1–25
- Lessons 101–106

Do not invent new lesson numbering.

Do not treat a character as belonging to exactly one lesson.

The canonical direction is:

```python
lesson_number -> characters
```

For example:

```python
LESSONS = {
    1: "、がの",
    2: "てと",
    3: "でにはを",
}
```

A reverse mapping may be generated when useful, but it must support multiple lesson memberships.

Lesson 11 is intentionally a review lesson with no new `chars` entry in the eelll data. Preserve that meaning rather than filling it with invented characters.

If external lesson data needs to be checked during implementation, verify against the eelll/JS source rather than guessing.

---

# T-Code table data

The existing repository contains useful source material in:

- `tcodeData_Maker.py`
- `tcodeData_generated.py`
- `PCkey.py`

These may be read and converted.

For test6, separate:

1. human-maintained source data
2. generated normalized data
3. user progress data

Do not make generated data the only editable source of truth.

Generated T-Code entries should have an explicit structure similar to:

```json
{
  "の": {
    "first": [8, 3],
    "second": [3, 3]
  }
}
```

Validate generated data for:

- x in 1..10
- y in 1..4
- unique two-stroke assignments
- no accidental `●` entries
- lesson characters resolving to known T-Code entries where required

Prefer deterministic output ordering so diffs are stable.

---

# Architecture

Keep GUI code separate from training logic.

Target modules are described in the specification. The important separation is:

## `tcode/keymap.py`

Responsible for:

- physical key to coordinate conversion
- coordinate validation
- keyboard event normalization

## `tcode/model.py`

Responsible for data models such as:

- `KeyPos`
- `TcodeEntry`
- `CharStats`
- session/result models

Use `dataclasses` where they improve clarity.

## `tcode/lesson.py`

Responsible for:

- lesson definitions
- selecting characters from one lesson
- selecting the union of a lesson range
- optional reverse lesson lookup

## `tcode/scheduler.py`

Responsible for:

- weighted question selection
- recent-question suppression
- retry scheduling
- weight updates

This module must not depend on tkinter.

## `tcode/session.py`

Responsible for:

- training state
- current question
- key sequence handling
- answer judgement
- correction flow
- timing
- session statistics

Keep this independently testable without opening a GUI.

## `tcode/storage.py`

Responsible for:

- reading/writing user progress
- schema version handling
- safe handling of missing/corrupt progress files

## `gui/`

Responsible for rendering and forwarding user actions.

Do not put scheduling or answer-correctness rules into widget classes unless unavoidable.

---

# Training state machine

Use explicit states rather than scattered booleans.

The specification currently defines:

```
SETUP
READY
WAIT_FIRST
WAIT_SECOND
CORRECT_FEEDBACK
WRONG_FEEDBACK
CORRECTION_FIRST
CORRECTION_SECOND
PAUSED
RESULT
```

Equivalent enums are preferred.

State transitions should be deterministic and covered by tests.

Important invariants:

- One valid key in `WAIT_FIRST` must not judge the answer.
- The second valid key performs judgement.
- A wrong answer enters correction flow.
- Correction input does not count as a first-try correct answer.
- The next normal question is not shown until required correction is completed.

---

# Error correction behavior

Do not simply show the correct answer and immediately move on after a mistake.

On a wrong answer:

1. record the wrong first attempt
2. show the correct two coordinates
3. enter correction mode
4. require the learner to type the correct two-stroke sequence
5. only then continue

If the correction sequence is wrong, restart the correction sequence from its first stroke.

Do not erase the original error from statistics after successful correction.

---

# Question scheduling

Preserve the useful concept from `test5.py`: weaker characters should appear more often.

However, do not rely only on multiplicative random weights.

Implement both:

- long-term weight adjustment
- short-term retry scheduling after an error

Default specification behavior:

```
correct:
    weight = max(0.25, weight * 0.80)

wrong:
    weight = min(8.0, weight * 1.60)
```

Wrong characters should normally reappear roughly 3–7 questions later.

Avoid immediate repetition where the lesson contains enough different characters.

Keep numeric tuning constants centralized so they can be changed later.

When random behavior is tested, allow injecting or seeding the random source.

---

# Timing

Use a monotonic clock for response timing, preferably `time.perf_counter()`.

Track at minimum:

```
t0 = question shown
t1 = first stroke
t2 = second stroke
```

Derive:

- first-stroke reaction time: `t1 - t0`
- inter-stroke time: `t2 - t1`
- total response time: `t2 - t0`

Do not use wall-clock timestamps for elapsed-time measurement.

Wall-clock timestamps may still be used for `last_seen` metadata.

---

# GUI behavior

The normal training screen should emphasize the target character.

The coordinate keyboard should show coordinate labels rather than QWERTY labels.

Normal training should not require mouse interaction after a session starts.

Keep keyboard focus robust when switching views.

Use `after()` for short feedback delays. Do not block the tkinter event loop with `sleep()`.

Do not create multiple independent `Tk()` roots. Use one root and switch frames/views.

Color may supplement feedback, but important state must not be conveyed by color alone.

---

# User data

User progress is runtime data and must not be committed.

Expected location under the test6 implementation root:

```
test6/user_data/progress.json
```

Add appropriate ignore rules when implementation begins.

Do not overwrite valid user progress simply because a new field was added. Prefer versioned migration/default filling.

If progress data is corrupt, fail safely and preserve the bad file when practical before resetting it.

---

# Tests

Add automated tests for non-GUI logic as features are implemented.

At minimum cover:

## Key map

- all 40 physical keys map to unique positions
- x is 1..10
- y is 1..4
- inverse mapping is unambiguous if implemented

## Lessons

Verify important source values, including:

- Lesson 1: `、がの`
- Lesson 10: `せやよわ`
- Lesson 11: no new characters
- Lesson 12: `「」すそまり`
- Lesson 101: `ごひへべむ`
- Lesson 106: `ぱぴぷぺぽゃ`

Verify range unions remove duplicate characters.

## T-Code data

- all coordinates valid
- no duplicate two-stroke assignment
- no placeholder symbol becomes an entry

## Scheduler

- correct lowers weight
- wrong raises weight
- limits are respected
- recent-repeat suppression works
- scheduled retry becomes eligible

## Session

- first stroke alone does not judge
- second stroke judges
- wrong answer enters correction
- correction must be completed
- correction does not increment first-try correct

Run the full relevant test suite before considering an implementation task complete.

If no test framework has been introduced yet, prefer `unittest` to avoid adding a dependency. Using `pytest` is acceptable only if the project explicitly adopts it.

---

# Development workflow

Before editing:

1. read this file
2. read `TcodeTrain_test6_spec.md`
3. inspect relevant legacy files only as reference
4. inspect existing test6 code before adding parallel implementations

While editing:

- make cohesive changes
- avoid unrelated cleanup
- keep public interfaces small
- keep constants centralized
- add type hints where useful
- use descriptive names rather than abbreviations such as `fi`, `se`, `Chdict`

After editing:

1. run relevant tests
2. run the full non-GUI test suite
3. perform a basic import/startup check
4. report what changed
5. report tests actually run and their results
6. mention any known limitation or specification item intentionally deferred

Do not claim a test passed unless it was actually run.

---

# Legacy compatibility

The legacy files are prototypes, not a compatibility contract.

Reuse ideas and source data where useful, but test6 may intentionally break internal compatibility with:

- packed integer coordinates
- `Chdict`
- `fi` / `se`
- Entry + Space answer submission
- single-valued lesson membership
- `a/n` retry navigation

Do not add compatibility wrappers merely to preserve these designs unless an external caller requires them.

---

# Changes that require caution

Do not change these without a clear requirement:

- the 10×4 physical key coordinate convention
- eelll/JS lesson numbering
- two-stroke T-Code answer semantics
- wrong-answer correction requirement
- separation of user data from source/generated data
- direct key-event answer input
- tkinter as the GUI framework

If a requested change conflicts with one of these, point out the conflict before implementing a broad redesign.

---

# Definition of done for the MVP

The MVP criteria in `TcodeTrain_test6_spec.md` are the acceptance criteria.

In particular, the implementation is not complete merely because a GUI opens.

It must also provide:

- lesson selection using eelll/JS definitions
- direct two-stroke input
- automatic judgement on stroke 2
- coordinate-only learning display
- correction typing after errors
- response timing
- adaptive scheduling
- persistent per-character progress
- results view

Implement in phases when appropriate, but keep incomplete phases clearly identified.


---

# Sentence training mode

Sentence training is part of the test6 MVP, not merely a future enhancement.

The single-character trainer remains the primary learning mode, but the application must also support sequential lesson-text practice based on the eelll/JS `EELLLTXT` `text` arrays.

Use sentence mode primarily from Lesson 5 onward.

## Data model

Lesson records should be able to hold both:

```python
chars
text
```

These have different meanings:

- `chars`: characters introduced/used for single-character lesson selection
- `text`: ordered lesson practice lines for sentence mode

Do not derive sentence text from `chars`.
Do not invent new practice sentences when the eelll/JS source already provides the lesson text.

When copying eelll/JS text data into this repository, preserve clear source attribution and applicable license information.

## Shared input engine

Do not implement a second answer engine for sentence mode.

Sentence mode must reuse the same:

- physical key normalization
- two-stroke collection
- coordinate comparison
- error correction
- timing
- per-character statistics

as single-character mode.

Only the source of the next target character changes.

Single-character mode gets the next character from the scheduler.

Sentence mode gets the next character from the current lesson text position.

## Sentence progression

Track sentence position separately, for example:

```python
lesson_number
line_index
char_index
```

For each input target:

1. highlight the current character in the displayed lesson line
2. wait for stroke 1
3. wait for stroke 2
4. judge the two-stroke answer
5. advance only on a correct first attempt or after required correction is completed

A wrong answer must not advance the text cursor.

Correction behavior is identical to single-character mode.

## Separators

ASCII spaces and line boundaries are display separators and should not normally require T-Code input.

Skip explicit separators automatically.

Do not silently skip an arbitrary character merely because it is missing from the T-Code table.

If a non-separator character in lesson text is not representable by the current T-Code data, treat that as a data validation failure.

Punctuation, full-width digits, kana, katakana, brackets, and other characters should be typed normally whenever they have a valid T-Code mapping.

## Ordering

Sentence mode follows the source text order.

Do not use weighted random selection to reorder sentence characters.

Do not inject the normal 3–7-question retry queue into the middle of lesson text.

Still update the character's long-term `weight` and statistics after each first attempt.

The learner already performs immediate correction after a wrong answer; later adaptive review belongs in single-character practice.

## GUI

SetupView should expose a clear training-form choice:

```
Single character
Sentence
```

Sentence mode should show enough surrounding text to read naturally while clearly marking the current target character.

Do not show the learner's QWERTY answer string.

Keep the normal coordinate keyboard available.

For sentence mode, useful progress indicators include:

- current Lesson
- current line
- completed characters / total characters
- current first-try accuracy

## Sentence statistics

Sentence answers update the same persistent per-character statistics as single-character answers.

Session results should additionally be able to show:

- completed lines
- completed characters
- elapsed time
- characters per minute
- first-try accuracy
- errors
- slowest characters

Count one completed T-Code character as one character for characters-per-minute metrics, regardless of its two physical strokes.

## Sentence-mode tests

Add tests for:

- loading Lesson 5 text
- feeding characters in source order
- advancing only after complete two-stroke answers
- remaining on the same character after a wrong answer
- advancing after successful correction
- automatic ASCII-space skipping
- rejecting unknown non-separator characters
- moving across line boundaries
- reaching result state at lesson end
- updating shared character statistics
- ensuring the weighted scheduler does not reorder lesson text

