"""Intrări: butoanele reale (GPIO) și tastatura în modul --sim."""

from __future__ import annotations

import logging
import sys
import threading
from typing import Callable

log = logging.getLogger(__name__)

OnPress = Callable[[str], None]


class _ShortOrLong:
    """GO trimite `short` la eliberare sau `long` dacă a fost ținut apăsat."""

    def __init__(self, on_press: OnPress, short: str, long: str):
        self._on_press = on_press
        self._short = short
        self._long = long
        self._held = False

    def pressed(self) -> None:
        self._held = False

    def held(self) -> None:
        self._held = True
        self._on_press(self._long)

    def released(self) -> None:
        if not self._held:
            self._on_press(self._short)


class GpioButtons:
    """Butoane legate între un pin GPIO și GND (folosim rezistența pull-up internă).

    Ținerea apăsată a butonului ABORT trimite evenimentul `reset`. GO acționează la
    eliberare: apăsat scurt trimite `go`, ținut `go_hold_s` secunde trimite `quiz`.
    """

    def __init__(
        self,
        pins: dict[str, int],
        on_press: OnPress,
        reset_hold_s: float = 3.0,
        go_hold_s: float = 2.0,
    ):
        from gpiozero import Button

        self._buttons = []
        for name, pin in pins.items():
            hold_s = go_hold_s if name == "go" else reset_hold_s
            button = Button(pin, pull_up=True, bounce_time=0.05, hold_time=hold_s)
            if name == "go":
                go = _ShortOrLong(on_press, "go", "quiz")
                button.when_pressed = go.pressed
                button.when_held = go.held
                button.when_released = go.released
            else:
                button.when_pressed = self._callback(on_press, name)
            if name == "abort":
                button.when_held = self._callback(on_press, "reset")
            self._buttons.append(button)
        log.info("butoane pe GPIO: %s", pins)

    @staticmethod
    def _callback(on_press: OnPress, name: str):
        return lambda: on_press(name)

    def close(self) -> None:
        for button in self._buttons:
            button.close()


class KeyboardButtons:
    """Tastele din terminal în locul butoanelor (modul --sim)."""

    KEYS = {
        "g": "go",
        "l": "launch",
        "s": "stage",
        "a": "abort",
        "r": "reset",
        "z": "quiz",
        "q": "quit",
    }
    HELP = "Taste: g=GO  l=LAUNCH  s=STAGE  a=ABORT  r=RESET  z=QUIZ  q=iesire"

    def __init__(self, on_press: OnPress, stream=None):
        self._on_press = on_press
        self._stream = stream or sys.stdin
        self._saved_tty = None
        self._windows_console = sys.platform == "win32" and self._stream.isatty()
        if self._stream.isatty() and not self._windows_console:
            import termios
            import tty

            fd = self._stream.fileno()
            self._saved_tty = termios.tcgetattr(fd)
            tty.setcbreak(fd)  # o tastă = un eveniment, fără Enter
        threading.Thread(target=self._read, name="keyboard", daemon=True).start()

    def _read(self) -> None:
        if self._windows_console:
            import msvcrt

            read_key = msvcrt.getwch
        else:
            read_key = lambda: self._stream.read(1)  # noqa: E731
        while True:
            ch = read_key()
            if not ch:
                return
            name = self.KEYS.get(ch.lower())
            if name:
                self._on_press(name)

    def close(self) -> None:
        if self._saved_tty is not None:
            import termios

            termios.tcsetattr(self._stream.fileno(), termios.TCSADRAIN, self._saved_tty)
            self._saved_tty = None


class NoButtons:
    def close(self) -> None:
        pass
