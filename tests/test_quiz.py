import random

import pytest
from conftest import Harness

from rocket_demo.config import Config
from rocket_demo.glyphs import lcd_safe
from rocket_demo.quiz import ANSWER_BUTTONS, Phase, QuizSession, grade
from rocket_demo.quiz_data import QUESTIONS, Question


class Recorder:
    def __init__(self):
        self.sounds = []

    def __call__(self, key):
        self.sounds.append(key)


def make_session(**overrides):
    cfg = Config(**overrides)
    sounds = Recorder()
    session = QuizSession(cfg, sounds, now=0.0, rng=random.Random(3))
    return session, sounds


def wrong_button(session):
    return next(b for b in ANSWER_BUTTONS if b != session.current.correct)


# ------------------------------------------------------------------ banca de întrebări
def test_question_bank_is_valid():
    assert len(QUESTIONS) >= 20
    texts = [q.text for q in QUESTIONS]
    assert len(set(texts)) == len(texts)
    for q in QUESTIONS:
        assert len(q.options) == 3, q.text
        assert len(set(q.options)) == 3, q.text
        assert all(0 < len(o) <= 60 for o in q.options), q.text
        assert q.text.strip() and q.explanation.strip()


def test_grades():
    assert [grade(s, 8) for s in range(9)] == (
        ["Cadet"] * 3 + ["Pilot"] * 2 + ["Inginer de zbor"] * 2 + ["Director de zbor"] * 2
    )


# ------------------------------------------------------------------ desfășurare
def test_round_flow_correct_wrong_and_timeout():
    s, sounds = make_session()
    assert s.phase == Phase.INTRO and sounds.sounds == ["quiz_start"]
    assert len(s.rounds) == 8
    assert len({a.question.text for a in s.rounds}) == 8

    s.press("launch", 1)  # pe ecranul de start doar GO pornește jocul
    assert s.phase == Phase.INTRO
    s.press("go", 1)
    assert s.phase == Phase.QUESTION and s.index == 0

    # răspuns corect
    s.press(s.current.correct, 2)
    assert s.phase == Phase.FEEDBACK and s.score == 1
    assert sounds.sounds[-1] == "quiz_correct"
    view = s.view(2)
    assert view["outcome"] == "correct" and view["correct"] == s.current.correct

    # după explicație trece singur la întrebarea următoare
    s.update(2 + s.cfg.quiz_feedback_s)
    assert s.phase == Phase.QUESTION and s.index == 1

    # răspuns greșit
    t = 2 + s.cfg.quiz_feedback_s
    s.press(wrong_button(s), t + 1)
    assert s.score == 1 and sounds.sounds[-1] == "quiz_wrong"
    assert s.view(t + 1)["outcome"] == "wrong"

    # GO trece mai departe, dar nu imediat după răspuns
    s.press("go", t + 1.5)
    assert s.phase == Phase.FEEDBACK
    s.press("go", t + 4)
    assert s.phase == Phase.QUESTION and s.index == 2

    # timpul expiră: tic-tac în ultimele 5 secunde, apoi răspuns greșit
    start = t + 4
    before = len(sounds.sounds)
    for i in range(1, 201):
        s.update(start + i * 0.1)
    assert sounds.sounds[before:].count("quiz_tick") == 5
    assert sounds.sounds[-1] == "quiz_wrong"
    assert s.view(start + 20)["outcome"] == "timeout"
    assert s.view(start + 20)["results"][:3] == [True, False, False]


def test_round_ends_with_result_and_new_round():
    s, sounds = make_session()
    now = 1.0
    s.press("go", now)
    for _ in range(8):
        now += 1
        s.press(s.current.correct, now)
        now += s.cfg.quiz_feedback_s
        s.update(now)
    assert s.phase == Phase.RESULT
    assert sounds.sounds[-1] == "quiz_end"
    view = s.view(now)
    assert view["score"] == 8 and view["grade"] == "Director de zbor"
    assert s.lcd(now) == ("SCOR 8/8", "Director de zbor")

    first = [a.question.text for a in s.rounds]
    s.press("go", now + 1)  # rundă nouă, direct prima întrebare
    assert s.phase == Phase.QUESTION and s.score == 0 and s.index == 0
    assert [a.question.text for a in s.rounds] != first


def test_options_are_shuffled_but_correct_answer_tracked():
    s, _ = make_session()
    positions = set()
    for asked in s.rounds:
        assert asked.options[asked.correct] == asked.question.options[0]
        assert sorted(asked.options.values()) == sorted(asked.question.options)
        positions.add(asked.correct)
    assert len(positions) > 1  # răspunsul corect nu e mereu pe același buton


def test_correct_answer_hidden_until_answered():
    s, _ = make_session()
    s.press("go", 1)
    view = s.view(1)
    assert "correct" not in view and "explanation" not in view
    assert set(view["options"]) == set(ANSWER_BUTTONS)
    assert view["time_left"] == 20


def test_abort_needs_confirmation_during_game():
    s, _ = make_session()
    s.press("go", 1)
    s.press("abort", 2)
    assert not s.exited and s.view(2)["confirm_exit"]
    assert s.lcd(2)[1] == "ABORT = iesire?"
    s.press("abort", 6)  # prea târziu: cere din nou confirmare
    assert not s.exited
    s.press("abort", 7)
    assert s.exited


def test_other_button_cancels_exit_prompt():
    s, _ = make_session()
    s.press("go", 1)
    s.press("abort", 2)
    s.press("stage", 2.5)  # răspunde, deci rămâne în joc
    s.press("abort", 3)
    assert not s.exited


def test_abort_exits_directly_on_intro_and_result():
    s, _ = make_session()
    s.press("abort", 1)
    assert s.exited


def test_idle_timeout_exits():
    s, _ = make_session(quiz_idle_timeout_s=60)
    s.press("go", 1)
    s.update(60)
    assert not s.exited
    s.update(61)
    assert s.exited


def test_lcd_lines_fit():
    s, _ = make_session()
    now = 0.0
    lines = [s.lcd(now)]
    s.press("go", now)
    for i in range(8):
        now += 1
        lines.append(s.lcd(now))
        if i % 2:
            s.press(s.current.correct, now)
        else:
            now += 21
            s.update(now)
        lines.append(s.lcd(now))
        now += 9
        s.update(now)
    lines.append(s.lcd(now))
    for line1, line2 in lines:
        assert lcd_safe(line1).rstrip() == line1.rstrip()
        assert lcd_safe(line2).rstrip() == line2.rstrip()


# ------------------------------------------------------------------ în controller
def test_long_go_opens_quiz_from_idle_and_abort_returns():
    h = Harness()
    h.press("quiz")
    assert h.state == "quiz"
    assert h.audio.played[-1] == "quiz_start"
    snap = h.ctrl.snapshot()
    assert snap["quiz"]["phase"] == "intro"
    assert h.display.last[0].strip() == "QUIZ LANSARE"
    h.press("go")
    assert h.ctrl.snapshot()["quiz"]["phase"] == "question"
    h.press("abort", "abort")
    assert h.state == "idle"
    assert h.ctrl.snapshot()["quiz"] is None


def test_quiz_from_end_screen_and_reset():
    h = Harness()
    h.go_to_ready()
    h.press("abort")
    assert h.state == "scrub"
    h.press("quiz")
    assert h.state == "quiz"
    h.press("reset")
    assert h.state == "idle"


def test_long_go_during_mission_counts_as_go():
    h = Harness()
    h.press("go")
    assert h.state == "checks"
    h.press("quiz")
    assert h.state == "checks"
    assert h.ctrl.snapshot()["checks"][0] == "go"


def test_quiz_runs_in_controller_with_timer_and_no_voice():
    h = Harness()
    h.press("quiz", "go")
    assert h.audio.voiced[-1] is None  # vocea tace în quiz
    h.run(20.1)
    assert h.ctrl.snapshot()["quiz"]["outcome"] == "timeout"
    assert "quiz_wrong" in h.audio.played
    h.run(h.cfg.quiz_feedback_s)
    assert h.ctrl.snapshot()["quiz"]["index"] == 2


def test_quiz_closes_itself_when_nobody_presses():
    h = Harness(quiz_idle_timeout_s=60)
    h.press("quiz")
    h.run(60.2)
    assert h.state == "idle"


# ------------------------------------------------------------------ butonul GO
def test_gpio_go_short_press_and_hold():
    gpiozero = pytest.importorskip("gpiozero")
    import time

    from gpiozero.pins.mock import MockFactory

    from rocket_demo.hardware.buttons import GpioButtons

    gpiozero.Device.pin_factory = MockFactory()
    pressed = []
    buttons = GpioButtons({"go": 5}, pressed.append, reset_hold_s=3, go_hold_s=0.2)
    try:
        pin = gpiozero.Device.pin_factory.pin(5)
        pin.drive_low()
        time.sleep(0.05)
        assert pressed == []  # GO acționează abia la eliberare
        pin.drive_high()
        time.sleep(0.05)
        assert pressed == ["go"]

        pin.drive_low()
        time.sleep(0.5)
        pin.drive_high()
        time.sleep(0.05)
        assert pressed == ["go", "quiz"]  # ținut: doar quiz, fără GO
    finally:
        buttons.close()
        gpiozero.Device.pin_factory.reset()


def test_custom_bank_smaller_than_round():
    bank = (Question("a?", ("x", "y", "z"), "e"), Question("b?", ("x", "y", "z"), "e"))
    s = QuizSession(Config(), Recorder(), 0.0, rng=random.Random(1), bank=bank)
    assert len(s.rounds) == 2
