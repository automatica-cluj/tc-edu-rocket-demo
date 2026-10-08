"""Crearea dispozitivelor; dacă hardware-ul lipsește, demo-ul continuă fără el."""

from __future__ import annotations

import logging

from ..config import Config
from ..mission import SOUNDS, voice_texts
from .audio import Audio, NoAudio
from .buttons import GpioButtons, KeyboardButtons, NoButtons
from .lcd import I2cLcd, LogDisplay, TerminalDisplay

log = logging.getLogger(__name__)


def make_display(cfg: Config, sim: bool):
    if sim:
        return TerminalDisplay()
    try:
        return I2cLcd(cfg.lcd_address, cfg.lcd_port)
    except Exception as exc:  # noqa: BLE001
        log.error("LCD indisponibil (%s); continui fără el", exc)
        return LogDisplay()


def make_buttons(cfg: Config, sim: bool, on_press):
    if sim:
        return KeyboardButtons(on_press)
    try:
        return GpioButtons(cfg.button_pins, on_press, cfg.reset_hold_s)
    except Exception as exc:  # noqa: BLE001
        log.error("butoane GPIO indisponibile (%s); merg doar butoanele de pe web", exc)
        return NoButtons()


def make_audio(cfg: Config, enabled: bool = True):
    if not enabled:
        return NoAudio()
    try:
        return Audio(
            [cfg.sounds_dir, cfg.placeholder_dir],
            SOUNDS,
            cfg.sound_files,
            cfg.sound_volume,
            voice_dirs=cfg.voice_dirs(),
            voice_keys=voice_texts() if cfg.voice_enabled else (),
            duck=cfg.voice_duck,
        )
    except Exception as exc:  # noqa: BLE001
        log.error("sunet indisponibil (%s); continui fără sunet", exc)
        return NoAudio()
