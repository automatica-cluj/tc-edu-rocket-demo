"""Quiz-ul despre lansare: clasa răspunde cu GO, LAUNCH și STAGE; ABORT iese din joc.

O rundă are `Config.quiz_questions` întrebări, fiecare cu `Config.quiz_time_s` secunde.
După fiecare răspuns (sau când expiră timpul) se afișează răspunsul corect și o scurtă
explicație. La final apar scorul și gradul. Controllerul trimite butoanele aici cât timp
e în starea QUIZ și citește `view()` (pentru pagina web) și `lcd()` (pentru LCD).
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass
from enum import Enum
from typing import Callable

from .config import Config
from .quiz_data import QUESTIONS, Question

ANSWER_BUTTONS = ("go", "launch", "stage")
BUTTON_LCD = {"go": "GO", "launch": "LAUNCH", "stage": "STAGE"}
TICK_FROM_S = 5  # tic-tac în ultimele secunde ale fiecărei întrebări
# După răspuns, GO trece mai departe abia după atâtea secunde, ca explicația să nu fie
# sărită din greșeală de cineva care apasă de mai multe ori.
SKIP_AFTER_S = 2.0
# Gradul minim pentru fiecare procent de răspunsuri corecte (8 întrebări: 0–2, 3–4, 5–6, 7–8).
GRADES = ((0.875, "Director de zbor"), (0.625, "Inginer de zbor"), (0.375, "Pilot"), (0.0, "Cadet"))


def grade(score: int, total: int) -> str:
    ratio = score / total if total else 0.0
    for threshold, name in GRADES:
        if ratio >= threshold:
            return name
    return GRADES[-1][1]


class Phase(str, Enum):
    INTRO = "intro"
    QUESTION = "question"
    FEEDBACK = "feedback"
    RESULT = "result"


@dataclass
class Asked:
    """O întrebare din runda curentă, cu variantele așezate pe butoane."""

    question: Question
    options: dict[str, str]  # buton -> textul variantei
    correct: str  # butonul cu răspunsul corect
    chosen: str | None = None
    answered: bool = False

    @property
    def is_correct(self) -> bool:
        return self.chosen == self.correct


class QuizSession:
    def __init__(
        self,
        cfg: Config,
        play: Callable[[str], None],
        now: float,
        rng: random.Random | None = None,
        bank: tuple[Question, ...] = QUESTIONS,
    ):
        self.cfg = cfg
        self._play = play
        self._rng = rng or random.Random()
        self._bank = bank
        self.exited = False
        self._last_input = now
        self._confirm_until = -math.inf
        self._new_round(now)

    # ------------------------------------------------------------ desfășurare
    def _new_round(self, now: float, start: bool = False) -> None:
        """Alege întrebările rundei; cu `start`, sare peste ecranul de început."""
        count = min(self.cfg.quiz_questions, len(self._bank))
        self.rounds = [self._prepare(q) for q in self._rng.sample(self._bank, count)]
        self.index = 0
        self.score = 0
        self._play("quiz_start")
        if start:
            self._ask(now)
        else:
            self._set_phase(Phase.INTRO, now)

    def _prepare(self, question: Question) -> Asked:
        order = [0, 1, 2]
        self._rng.shuffle(order)
        options = {button: question.options[i] for button, i in zip(ANSWER_BUTTONS, order)}
        return Asked(question, options, correct=ANSWER_BUTTONS[order.index(0)])

    def _set_phase(self, phase: Phase, now: float) -> None:
        self.phase = phase
        self._phase_since = now

    @property
    def current(self) -> Asked:
        return self.rounds[self.index]

    def _ask(self, now: float) -> None:
        self._set_phase(Phase.QUESTION, now)
        self._last_tick = TICK_FROM_S + 1

    def _answer(self, button: str | None, now: float) -> None:
        asked = self.current
        asked.chosen = button
        asked.answered = True
        if asked.is_correct:
            self.score += 1
            self._play("quiz_correct")
        else:
            self._play("quiz_wrong")
        self._set_phase(Phase.FEEDBACK, now)

    def _next(self, now: float) -> None:
        if self.index + 1 >= len(self.rounds):
            self._set_phase(Phase.RESULT, now)
            self._play("quiz_end")
        else:
            self.index += 1
            self._ask(now)

    def time_left(self, now: float) -> float:
        return max(0.0, self.cfg.quiz_time_s - (now - self._phase_since))

    # ------------------------------------------------------------ intrări
    def press(self, button: str, now: float) -> None:
        self._last_input = now
        if button == "abort":
            # La început și la final ieșim direct; în timpul jocului cerem confirmare.
            if self.phase in (Phase.INTRO, Phase.RESULT) or now < self._confirm_until:
                self.exited = True
            else:
                self._confirm_until = now + self.cfg.quiz_exit_confirm_s
            return
        self._confirm_until = -math.inf  # alt buton anulează întrebarea „Ieși?”

        if self.phase == Phase.INTRO:
            if button == "go":
                self._ask(now)
        elif self.phase == Phase.QUESTION:
            if button in ANSWER_BUTTONS:
                self._answer(button, now)
        elif self.phase == Phase.FEEDBACK:
            if button == "go" and now - self._phase_since >= SKIP_AFTER_S:
                self._next(now)
        elif self.phase == Phase.RESULT:
            if button == "go":
                self._new_round(now, start=True)

    def update(self, now: float) -> None:
        if now - self._last_input >= self.cfg.quiz_idle_timeout_s:
            self.exited = True
            return
        if self.phase == Phase.QUESTION:
            left = self.time_left(now)
            second = math.ceil(left)
            if 0 < second <= TICK_FROM_S and second < self._last_tick:
                self._last_tick = second
                self._play("quiz_tick")
            if left <= 0:
                self._answer(None, now)
        elif self.phase == Phase.FEEDBACK and now - self._phase_since >= self.cfg.quiz_feedback_s:
            self._next(now)

    # ------------------------------------------------------------ afișare
    def confirming_exit(self, now: float) -> bool:
        return now < self._confirm_until

    def view(self, now: float) -> dict:
        """Starea quiz-ului pentru pagina web (răspunsul corect apare doar după răspuns)."""
        view = {
            "phase": self.phase.value,
            "index": self.index + 1,
            "total": len(self.rounds),
            "score": self.score,
            "results": [a.is_correct if a.answered else None for a in self.rounds],
            "confirm_exit": self.confirming_exit(now),
            "time_total": self.cfg.quiz_time_s,
        }
        if self.phase in (Phase.QUESTION, Phase.FEEDBACK):
            view["question"] = self.current.question.text
            view["options"] = dict(self.current.options)
        if self.phase == Phase.QUESTION:
            view["time_left"] = round(self.time_left(now), 1)
        elif self.phase == Phase.FEEDBACK:
            asked = self.current
            view["correct"] = asked.correct
            view["chosen"] = asked.chosen
            view["outcome"] = (
                "correct" if asked.is_correct else "timeout" if asked.chosen is None else "wrong"
            )
            view["explanation"] = asked.question.explanation
        elif self.phase == Phase.RESULT:
            view["grade"] = grade(self.score, len(self.rounds))
        return view

    def lcd(self, now: float) -> tuple[str, str]:
        line1, line2 = self._lcd_lines(now)
        if self.confirming_exit(now):
            line2 = "ABORT = iesire?"
        return line1, line2

    def _lcd_lines(self, now: float) -> tuple[str, str]:
        n = len(self.rounds)
        if self.phase == Phase.INTRO:
            return "QUIZ LANSARE", "GO = incepem"
        if self.phase == Phase.QUESTION:
            return (
                f"QUIZ {self.index + 1}/{n} Scor {self.score}",
                f"Raspuns? {math.ceil(self.time_left(now)):>3}s",
            )
        if self.phase == Phase.FEEDBACK:
            asked = self.current
            if asked.is_correct:
                return "CORECT! +1", f"Scor {self.score}/{self.index + 1}"
            title = "TIMP EXPIRAT!" if asked.chosen is None else "GRESIT!"
            return title, f"Corect: {BUTTON_LCD[asked.correct]}"
        return f"SCOR {self.score}/{n}", grade(self.score, n)
