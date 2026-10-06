import random

import pytest

from rocket_demo.config import Config
from rocket_demo.controller import Controller
from rocket_demo.glyphs import ASCII_FALLBACK, LCD_COLS


class FakeClock:
    def __init__(self):
        self.t = 1000.0

    def __call__(self):
        return self.t


class FakeDisplay:
    def __init__(self):
        self.frames = []

    def show(self, line1, line2):
        for line in (line1, line2):
            assert len(line) == LCD_COLS, repr(line)
            assert all(c.isascii() for c in line), repr(line)
            assert all(c.isprintable() or c in ASCII_FALLBACK for c in line), repr(line)
        self.frames.append((line1, line2))

    @property
    def last(self):
        return self.frames[-1]


class FakeAudio:
    def __init__(self):
        self.calls = []

    def play(self, key):
        self.calls.append(("play", key))

    def engine(self, on):
        self.calls.append(("engine", on))

    def stop_all(self):
        self.calls.append(("stop",))

    @property
    def played(self):
        return [c[1] for c in self.calls if c[0] == "play"]


class Harness:
    def __init__(self, **overrides):
        self.cfg = Config(**{"hold_probability": 0.0, **overrides})
        self.clock = FakeClock()
        self.display = FakeDisplay()
        self.audio = FakeAudio()
        self.ctrl = Controller(
            self.cfg,
            self.display,
            self.audio,
            clock=self.clock,
            rng=random.Random(1),
            ip_provider=lambda: "192.168.1.42",
        )

    @property
    def state(self):
        return self.ctrl.state.value

    def press(self, *buttons):
        for b in buttons:
            self.ctrl.press(b)
            self.ctrl.tick()

    def run(self, seconds, step=0.1):
        for _ in range(round(seconds / step)):
            self.clock.t += step
            self.ctrl.tick()

    def run_until(self, predicate, limit=600, step=0.1):
        for _ in range(round(limit / step)):
            if predicate():
                return
            self.clock.t += step
            self.ctrl.tick()
        raise AssertionError("condiția nu a fost îndeplinită la timp")

    def go_to_ready(self):
        self.press("go")
        self.press(*["go"] * len(self.ctrl.mission.checks))
        assert self.state == "ready"

    def go_to_flight(self):
        self.go_to_ready()
        self.press("launch")
        self.run(self.cfg.countdown_s + 0.1)
        assert self.state == "flight"


@pytest.fixture
def h():
    return Harness()
