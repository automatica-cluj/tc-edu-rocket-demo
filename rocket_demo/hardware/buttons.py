"""Intrări: butoanele reale (GPIO) și tastatura în modul --sim."""

from __future__ import annotations

import logging
import sys
import threading
from typing import Callable

log = logging.getLogger(__name__)

OnPress = Callable[[str], None]


class GpioButtons:
    """Butoane legate între un pin GPIO și GND (folosim rezistența pull-up internă).

    Ținerea apăsată a butonului ABORT trimite evenimentul `reset`.
    """

    def __init__(self, pins: dict[str, int], on_press: OnPress, reset_hold_s: float = 3.0):
        from gpiozero import Button

        self._buttons = []
        for name, pin in pins.items():
            button = Button(pin, pull_up=True, bounce_time=0.05, hold_time=reset_hold_s)
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

    KEYS = {"g": "go", "l": "launch", "s": "stage", "a": "abort", "r": "reset", "q": "quit"}
    HELP = "Taste: g=GO  l=LAUNCH  s=STAGE  a=ABORT  r=RESET  q=iesire"

    def __init__(self, on_press: OnPress, stream=None):
        self._on_press = on_press
        self._stream = stream or sys.stdin
        self._saved_tty = None
        if self._stream.isatty():
            import termios
            import tty

            fd = self._stream.fileno()
            self._saved_tty = termios.tcgetattr(fd)
            tty.setcbreak(fd)  # o tastă = un eveniment, fără Enter
        threading.Thread(target=self._read, name="keyboard", daemon=True).start()

    def _read(self) -> None:
        while True:
            ch = self._stream.read(1)
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
