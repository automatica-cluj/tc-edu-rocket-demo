"""Ecranul „Piesele rachetei”: racheta desfăcută pe bucăți, cu numele fiecărei piese.

Se deschide cu LAUNCH ținut apăsat în ecranul de start sau pe cele finale. GO trece la
piesa următoare, STAGE înapoi, ABORT iese. Dacă nimeni nu apasă, trece singur la piesa
următoare la fiecare `Config.parts_step_s` secunde și se închide după
`Config.parts_idle_timeout_s` secunde fără nicio apăsare. Controllerul trimite butoanele
aici cât timp e în starea PARTS și citește `view()` (pagina web) și `lcd()` (LCD).
"""

from __future__ import annotations

from .config import Config
from .parts_data import PARTS, Part


class PartsTour:
    def __init__(self, cfg: Config, now: float, parts: tuple[Part, ...] = PARTS):
        self.cfg = cfg
        self.parts = parts
        self.index = 0
        self.exited = False
        self._last_press = now
        self._last_step = now

    @property
    def part(self) -> Part:
        return self.parts[self.index]

    def _go(self, delta: int, now: float) -> None:
        self.index = (self.index + delta) % len(self.parts)
        self._last_step = now

    def press(self, button: str, now: float) -> None:
        self._last_press = now
        if button == "abort":
            self.exited = True
        elif button == "go":
            self._go(1, now)
        elif button == "stage":
            self._go(-1, now)

    def update(self, now: float) -> None:
        if now - self._last_press >= self.cfg.parts_idle_timeout_s:
            self.exited = True
        elif now - self._last_step >= self.cfg.parts_step_s:
            self._go(1, now)

    def lcd(self, now: float) -> tuple[str, str]:
        return f"PIESA {self.index + 1:>2}/{len(self.parts)}", self.part.lcd

    def view(self, now: float) -> dict:
        part = self.part
        return {
            "index": self.index + 1,
            "total": len(self.parts),
            "key": part.key,
            "name": part.name,
            "text": part.text,
        }
