"""Automatul de stări al demo-ului.

Butoanele (fizice, de la tastatură sau de pe pagina web) apelează `press()`, care
doar pune evenimentul într-o coadă. Bucla principală apelează `tick()` de ~10 ori pe
secundă: consumă evenimentele, avansează timpul, actualizează LCD-ul și publică o
„fotografie” a stării (snapshot) pentru pagina web.
"""

from __future__ import annotations

import logging
import math
import queue
import random
import threading
import time
from enum import Enum
from typing import Callable

from .config import Config
from .glyphs import ROCKET, lcd_safe, to_ascii
from .mission import DEFAULT_MISSION, FlightEvent, Mission
from .telemetry import Telemetry, format_lcd, interpolate

log = logging.getLogger(__name__)

BUTTONS = ("go", "launch", "stage", "abort", "reset")


class State(str, Enum):
    IDLE = "idle"
    CHECKS = "checks"
    HOLD = "hold"
    READY = "ready"
    COUNTDOWN = "countdown"
    FLIGHT = "flight"
    ORBIT = "orbit"
    SCRUB = "scrub"
    ABORT = "abort"


END_STATES = (State.ORBIT, State.SCRUB, State.ABORT)
SCREEN_CYCLE_S = 3.0
IP_REFRESH_S = 10.0
FLASH_S = 2.5


def clock_text(t: float) -> str:
    sign = "-" if t < 0 else "+"
    secs = math.ceil(-t) if t < 0 else int(t)
    return f"T{sign}{secs // 60}:{secs % 60:02d}"


class Controller:
    def __init__(
        self,
        config: Config,
        display,
        audio,
        mission: Mission = DEFAULT_MISSION,
        clock: Callable[[], float] = time.monotonic,
        rng: random.Random | None = None,
        ip_provider: Callable[[], str | None] = lambda: None,
    ):
        self.cfg = config
        self.display = display
        self.audio = audio
        self.mission = mission
        self._clock = clock
        self._rng = rng or random.Random()
        self._ip_provider = ip_provider
        self._ip: str | None = None
        self._ip_checked_at = -math.inf

        self._buttons: queue.Queue[str] = queue.Queue()
        self._cond = threading.Condition()
        self._snapshot: dict = {}
        self._version = 0

        self._flash_text = ""
        self._flash_until = 0.0
        self._voice_playing: str | None = None
        self._enter_idle(self._clock())
        self.tick()

    # ------------------------------------------------------------------ API
    def press(self, button: str) -> None:
        """Înregistrează apăsarea unui buton (sigur de apelat din orice thread)."""
        if button not in BUTTONS:
            raise ValueError(f"buton necunoscut: {button}")
        self._buttons.put(button)

    def snapshot(self) -> dict:
        with self._cond:
            return dict(self._snapshot)

    def wait_for_update(self, version: int, timeout: float) -> dict:
        """Așteaptă până când starea are altă versiune decât `version` (sau expiră)."""
        with self._cond:
            self._cond.wait_for(lambda: self._version != version, timeout)
            return dict(self._snapshot)

    def run(self, stop: threading.Event, period: float = 0.1) -> None:
        while not stop.is_set():
            started = time.monotonic()
            self.tick()
            stop.wait(max(0.0, period - (time.monotonic() - started)))

    def tick(self) -> None:
        now = self._clock()
        while True:
            try:
                button = self._buttons.get_nowait()
            except queue.Empty:
                break
            log.info("buton: %s (stare: %s)", button, self.state.value)
            self._handle(button, now)
        self._update(now)
        self._update_voice()
        self.audio.update()
        line1, line2 = self._render(now)
        self.display.show(line1, line2)
        self._publish(now, line1, line2)

    # ------------------------------------------------------- tranziții
    def _set_state(self, state: State, now: float) -> None:
        log.info("stare: %s", state.value)
        self.state = state
        self._state_since = now

    def _enter_idle(self, now: float) -> None:
        self._set_state(State.IDLE, now)
        self._checks_done = 0
        self._hold_station: int | None = None
        self._fired: list[FlightEvent] = []
        self._flight_t = 0.0
        self._awaiting_since: float | None = None
        self._stage_armed = False
        self._engine_on = False
        self._ignition_done = False

    def _start_checks(self, now: float) -> None:
        self._enter_idle(now)
        if self._rng.random() < self.cfg.hold_probability:
            self._hold_station = self._rng.randrange(len(self.mission.checks))
        self._set_state(State.CHECKS, now)

    def _handle(self, button: str, now: float) -> None:
        if button == "reset":
            self.audio.stop_all()
            self._enter_idle(now)
            self._flash("Reset", now)
            return

        s = self.state
        if s == State.IDLE or s in END_STATES:
            if button == "go":
                self.audio.stop_all()
                self._start_checks(now)
        elif s == State.CHECKS:
            if button == "go":
                self._confirm_station(now)
            elif button == "launch":
                self._flash("Mai intai GO!", now)
            elif button == "abort":
                self._scrub(now)
        elif s == State.HOLD:
            if button == "abort":
                self._scrub(now)
        elif s == State.READY:
            if button == "launch":
                self._set_state(State.COUNTDOWN, now)
                self.audio.play("countdown")
            elif button == "abort":
                self._scrub(now)
        elif s == State.COUNTDOWN:
            if button == "abort":
                self._scrub(now)
        elif s == State.FLIGHT:
            if button == "abort":
                self._abort(now)
            elif button == "stage":
                self._stage_pressed(now)

    def _confirm_station(self, now: float) -> None:
        if self._checks_done == self._hold_station:
            self._hold_station = None
            self._set_state(State.HOLD, now)
            self.audio.play("hold")
            return
        self._checks_done += 1
        if self._checks_done >= len(self.mission.checks):
            self._set_state(State.READY, now)
            self.audio.play("all_go")
        else:
            self.audio.play("go_beep")

    def _scrub(self, now: float) -> None:
        self.audio.stop_all()
        self.audio.play("scrub")
        self._engine_on = False
        self._set_state(State.SCRUB, now)

    def _abort(self, now: float) -> None:
        self.audio.stop_all()
        self.audio.play("abort_alarm")
        self._engine_on = False
        self._awaiting_since = None
        self._set_state(State.ABORT, now)

    def _next_event(self) -> FlightEvent | None:
        events = self.mission.events
        return events[len(self._fired)] if len(self._fired) < len(events) else None

    def _stage_pressed(self, now: float) -> None:
        if self._awaiting_since is not None:
            self._awaiting_since = None
            self._flash("Bravo! Separare", now)
            self._fire(self._next_event(), now)
            return
        ev = self._next_stage_event()
        if ev is None:
            return
        if ev.t - self._flight_t <= self.cfg.stage_early_s:
            self._stage_armed = True
        else:
            self._flash("Prea devreme!", now)

    def _next_stage_event(self) -> FlightEvent | None:
        for ev in self.mission.events[len(self._fired):]:
            if ev.needs_stage:
                return ev
        return None

    def _fire(self, ev: FlightEvent, now: float) -> None:
        log.info("etapa: %s (T+%.0f)", ev.key, ev.t)
        self._fired.append(ev)
        self._flight_t = max(self._flight_t, ev.t)
        if ev.sound:
            self.audio.play(ev.sound)
        if ev.engine is not None:
            self._engine_on = ev.engine
            self.audio.engine(ev.engine)
        if ev.needs_stage:
            self._stage_armed = False
        if self._next_event() is None:
            self._flight_t = ev.t  # ceasul se oprește la SECO
            self._set_state(State.ORBIT, now)

    def _flash(self, text: str, now: float) -> None:
        self._flash_text = text
        self._flash_until = now + FLASH_S

    # ------------------------------------------------------- timp
    def _update(self, now: float) -> None:
        elapsed = now - self._state_since
        if self.state == State.HOLD and elapsed >= self.cfg.hold_s and not self._voice_busy():
            self._set_state(State.CHECKS, now)
            self._flash("Rezolvat! GO?", now)
        elif self.state == State.COUNTDOWN:
            remaining = self.cfg.countdown_s - elapsed
            if not self._ignition_done and remaining <= self.cfg.ignition_at_s:
                self._ignition_done = True
                self._engine_on = True
                self.audio.play("ignition")
                self.audio.engine(True)
            if remaining <= 0:
                self._set_state(State.FLIGHT, now)
                self._flight_t = 0.0
                self._last_flight_tick = now
                self._advance_flight(now)
        elif self.state == State.FLIGHT:
            self._advance_flight(now)
        elif self.state in END_STATES and elapsed >= self.cfg.end_screen_timeout_s:
            self.audio.stop_all()
            self._enter_idle(now)

    def _advance_flight(self, now: float) -> None:
        dt = now - self._last_flight_tick
        self._last_flight_tick = now
        if self._awaiting_since is not None:
            if now - self._awaiting_since >= self.cfg.stage_window_s:
                self._awaiting_since = None
                self._flash("Separare auto", now)
                self._fire(self._next_event(), now)
            return

        self._flight_t += dt * self.cfg.time_scale
        while self.state == State.FLIGHT:
            ev = self._next_event()
            if ev is None or ev.t > self._flight_t:
                break
            if self._fired and self._voice_busy():
                self._flight_t = ev.t  # așteptăm să se termine explicația etapei curente
                break
            if ev.needs_stage and self.cfg.interactive_stage:
                if not self._stage_armed:
                    self._flight_t = ev.t
                    self._awaiting_since = now
                    self.audio.play("stage_prompt")
                    break
                self._flash("Bravo! Separare", now)
            self._fire(ev, now)

    # ------------------------------------------------------- voce
    def _voice_busy(self) -> bool:
        return self.cfg.voice_wait and self.audio.voice_busy()

    def _voice_key(self) -> str:
        """Fișierul de voce pentru textul afișat acum pe pagina web (vezi `voice_texts`)."""
        s = self.state
        if s in (State.CHECKS, State.HOLD):
            check = self.mission.checks[self._checks_done]
            return f"{'hold' if s == State.HOLD else 'statie'}_{check.key}"
        if s == State.FLIGHT and self._fired:
            return f"etapa_{self._fired[-1].key}"
        return f"stare_{s.value}"

    def _update_voice(self) -> None:
        key = self._voice_key()
        if key != self._voice_playing:
            self._voice_playing = key
            self.audio.voice(key)

    # ------------------------------------------------------- afișare
    def _telemetry(self) -> Telemetry:
        if self.state in (State.FLIGHT, State.ORBIT, State.ABORT):
            return interpolate(self.mission.telemetry, self._flight_t)
        return Telemetry(0.0, 0.0)

    def _mission_t(self, now: float) -> float | None:
        if self.state == State.COUNTDOWN:
            return -(self.cfg.countdown_s - (now - self._state_since))
        if self.state in (State.FLIGHT, State.ORBIT) or (
            self.state == State.ABORT and self._fired
        ):
            return self._flight_t
        return None

    def _web_ip(self, now: float) -> str | None:
        if now - self._ip_checked_at >= IP_REFRESH_S:
            self._ip_checked_at = now
            try:
                self._ip = self._ip_provider()
            except Exception:  # noqa: BLE001 - adresa IP e doar informativă
                self._ip = None
        return self._ip

    def _render(self, now: float) -> tuple[str, str]:
        line1, line2 = self._render_state(now)
        if now < self._flash_until:
            line2 = self._flash_text
        return lcd_safe(line1), lcd_safe(line2)

    def _render_state(self, now: float) -> tuple[str, str]:
        s = self.state
        screen = int((now - self._state_since) / SCREEN_CYCLE_S) % 2
        blink = int(now * 2) % 2 == 0

        if s == State.IDLE:
            ip = self._web_ip(now) if self.cfg.web_enabled else None
            if screen == 1 and ip:
                return f"Web: port {self.cfg.web_port}", ip
            return f"{ROCKET} MISIUNE {self.cfg.mission_name}", "Apasa GO >>"
        if s == State.CHECKS:
            check = self.mission.checks[self._checks_done]
            n = len(self.mission.checks)
            return (
                f"{check.lcd:.<13}GO?",
                f"Apasa GO {self._checks_done + 1:>5}/{n}",
            )
        if s == State.HOLD:
            check = self.mission.checks[self._checks_done]
            return ("HOLD! Asteptam" if blink else "HOLD!", check.hold_lcd)
        if s == State.READY:
            return "TOTUL ESTE GO!", "Apasa LAUNCH >>"
        if s == State.COUNTDOWN:
            t = self._mission_t(now)
            ignition = -t <= self.cfg.ignition_at_s
            return (
                f"{ROCKET}     {clock_text(t)}",
                "Aprindere motor" if ignition else "Secv. automata",
            )
        if s == State.FLIGHT:
            label = self._fired[-1].lcd if self._fired else ""
            line1 = f"{clock_text(self._flight_t)} {label}"
            if self._awaiting_since is not None:
                return line1, ">> APASA STAGE!" if blink else ""
            return line1, format_lcd(self._telemetry())
        if s == State.ORBIT:
            if screen == 0:
                return "ORBITA ATINSA!", format_lcd(self._telemetry())
            return "Misiune reusita", "GO=misiune noua"
        if s == State.SCRUB:
            return "LANSARE ANULATA", "GO = reincercam"
        if s == State.ABORT:
            if screen == 0:
                return "!!! ABORT !!!", "Capsula salvata"
            return "Echipaj in sigur", "GO=misiune noua"
        return "", ""

    # ------------------------------------------------------- pagina web
    def _info(self) -> dict:
        s = self.state
        if s in (State.CHECKS, State.HOLD):
            check = self.mission.checks[self._checks_done]
            if s == State.HOLD:
                return {"title": f"HOLD: {check.name}", "text": check.hold_info}
            return {"title": f"Verificare: {check.name}", "text": check.info}
        if s == State.FLIGHT and self._fired:
            ev = self._fired[-1]
            return {"title": ev.title, "text": ev.info}
        info = self.mission.state_info.get(s.value)
        return {"title": info.title, "text": info.text} if info else {"title": "", "text": ""}

    def _check_statuses(self) -> list[str]:
        statuses = []
        for i in range(len(self.mission.checks)):
            if i < self._checks_done:
                statuses.append("go")
            elif i == self._checks_done and self.state == State.CHECKS:
                statuses.append("current")
            elif i == self._checks_done and self.state == State.HOLD:
                statuses.append("hold")
            else:
                statuses.append("pending")
        return statuses

    def _publish(self, now: float, line1: str, line2: str) -> None:
        tel = self._telemetry()
        t = self._mission_t(now)
        snap = {
            "state": self.state.value,
            "mission_name": self.cfg.mission_name,
            "lcd": [to_ascii(line1), to_ascii(line2)],
            "t": None if t is None else round(t, 2),
            "clock": "" if t is None else clock_text(t),
            "alt_km": round(tel.alt_km, 2),
            "vel_ms": round(tel.vel_ms),
            "vel_kmh": tel.vel_kmh,
            "engine_on": self._engine_on,
            "fired": [ev.key for ev in self._fired],
            "awaiting_stage": self._awaiting_since is not None,
            "checks": self._check_statuses(),
            "info": self._info(),
            "web_control": self.cfg.web_control,
        }
        with self._cond:
            previous = {k: v for k, v in self._snapshot.items() if k != "version"}
            if snap != previous:
                self._version += 1
                snap["version"] = self._version
                self._snapshot = snap
                self._cond.notify_all()
