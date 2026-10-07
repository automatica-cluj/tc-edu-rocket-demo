"""Sunet prin pygame.mixer (ALSA/PipeWire → jack, placă USB, HDMI sau boxă Bluetooth)."""

from __future__ import annotations

import logging
import os
import re
import shutil
import subprocess
import threading
import time
from pathlib import Path

log = logging.getLogger(__name__)

EXTENSIONS = (".wav", ".ogg", ".mp3")
ENGINE_KEY = "engine_loop"
APP_NAME = "Demo racheta"
WATCH_S = 5.0


def find_sound(dirs: list[Path], name: str) -> Path | None:
    """Caută `name` (cu sau fără extensie) în directoare, în ordine."""
    candidates = [name] if Path(name).suffix else [name + ext for ext in EXTENSIONS]
    for directory in dirs:
        for candidate in candidates:
            path = Path(directory) / candidate
            if path.is_file():
                return path
    return None


def default_sink() -> str | None:
    """Numele ieșirii audio implicite din PipeWire (de ex. boxa Bluetooth), dacă există."""
    try:
        out = subprocess.run(
            ["wpctl", "inspect", "@DEFAULT_AUDIO_SINK@"],
            capture_output=True,
            text=True,
            timeout=2,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    match = re.search(r'node\.name = "([^"]+)"', out.stdout)
    return match.group(1) if match else None


class Audio:
    """Redă sunetele demo-ului.

    Pe sistemele cu PipeWire (Raspberry Pi OS cu desktop), un fir de fundal verifică la
    câteva secunde ieșirea audio implicită. Dacă ea se schimbă (de ex. s-a conectat sau
    reconectat boxa Bluetooth) sau sunetul nu a putut fi pornit la boot, redeschide
    sunetul pe noua ieșire, fără repornirea aplicației.
    """

    def __init__(
        self,
        dirs: list[Path],
        keys,
        files: dict[str, str] | None = None,
        volume=1.0,
        watch_s: float | None = WATCH_S,
    ):
        os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")
        # Nume propriu în PipeWire (`wpctl status`), ca volumul demo-ului să nu fie
        # amestecat cu al altor programe Python.
        os.environ.setdefault("SDL_APP_NAME", APP_NAME)
        os.environ.setdefault("SDL_AUDIO_DEVICE_APP_NAME", APP_NAME)
        import pygame

        self._pygame = pygame
        self._dirs = dirs
        self._keys = list(keys)
        self._files = files or {}
        self._volume = volume
        self._lock = threading.RLock()
        self._ready = False
        self._engine_on = False
        self.sounds = {}
        self.paths: dict[str, Path] = {}
        self.reopen_count = 0

        watching = watch_s is not None and shutil.which("wpctl") is not None
        self._sink = default_sink() if watching else None
        try:
            self._open()
        except Exception as exc:  # noqa: BLE001
            if not watching:
                raise
            log.warning("sunetul nu e încă disponibil (%s); reîncerc automat", exc)
        if watching:
            threading.Thread(target=self._watch, args=(watch_s,), name="audio", daemon=True).start()

    # ------------------------------------------------------------ deschidere
    def _open(self) -> None:
        pygame = self._pygame
        pygame.mixer.pre_init(frequency=44100, size=-16, channels=2, buffer=1024)
        pygame.mixer.init()
        pygame.mixer.set_num_channels(16)
        pygame.mixer.set_reserved(1)  # canalul 0 e doar pentru motor
        self._engine_channel = pygame.mixer.Channel(0)

        sounds, paths, missing = {}, {}, []
        for key in self._keys:
            path = find_sound(self._dirs, self._files.get(key, key))
            if path is None:
                missing.append(key)
                continue
            try:
                sound = pygame.mixer.Sound(str(path))
            except pygame.error as exc:
                log.warning("nu pot citi %s: %s", path, exc)
                continue
            sound.set_volume(self._volume)
            sounds[key] = sound
            paths[key] = path
        self.sounds, self.paths = sounds, paths
        self._ready = True
        log.info(
            "sunete încărcate: %d/%d (ieșire: %s)",
            len(sounds),
            len(self._keys),
            self._sink or "implicită",
        )
        if missing:
            log.warning("lipsesc sunetele: %s (demo-ul merge și fără ele)", ", ".join(missing))

    def _reopen(self) -> None:
        with self._lock:
            self._ready = False
            try:
                self._pygame.mixer.quit()
            except self._pygame.error:
                pass
            try:
                self._open()
            except Exception as exc:  # noqa: BLE001
                log.warning("nu pot redeschide sunetul (%s); reîncerc", exc)
                return
            self.reopen_count += 1
            if self._engine_on and ENGINE_KEY in self.sounds:
                self._engine_channel.play(self.sounds[ENGINE_KEY], loops=-1, fade_ms=500)

    def check_output(self) -> None:
        """Redeschide sunetul dacă ieșirea implicită s-a schimbat sau sunetul nu merge."""
        sink = default_sink()
        if sink is not None and sink != self._sink:
            log.info("ieșirea audio s-a schimbat: %s → %s; redeschid sunetul", self._sink, sink)
            self._sink = sink
            self._reopen()
        elif not self._ready:
            self._reopen()

    def _watch(self, period: float) -> None:
        while True:
            time.sleep(period)
            try:
                self.check_output()
            except Exception:  # noqa: BLE001 - firul de fundal nu trebuie să moară
                log.exception("eroare la verificarea ieșirii audio")

    # ------------------------------------------------------------ redare
    def play(self, key: str) -> None:
        with self._lock:
            sound = self.sounds.get(key)
            if self._ready and sound is not None:
                try:
                    sound.play()
                except self._pygame.error as exc:
                    log.debug("nu pot reda %s: %s", key, exc)

    def engine(self, on: bool) -> None:
        with self._lock:
            self._engine_on = on
            sound = self.sounds.get(ENGINE_KEY)
            if not self._ready or sound is None:
                return
            try:
                if on:
                    if not self._engine_channel.get_busy():
                        self._engine_channel.play(sound, loops=-1, fade_ms=500)
                else:
                    self._engine_channel.fadeout(800)
            except self._pygame.error as exc:
                log.debug("nu pot comanda motorul: %s", exc)

    def stop_all(self) -> None:
        with self._lock:
            self._engine_on = False
            if self._ready:
                try:
                    self._pygame.mixer.stop()
                except self._pygame.error:
                    pass

    def length(self, key: str) -> float:
        sound = self.sounds.get(key)
        return sound.get_length() if sound else 0.0

    def close(self) -> None:
        with self._lock:
            self._ready = False
            try:
                self._pygame.mixer.quit()
            except self._pygame.error:
                pass


class NoAudio:
    sounds: dict = {}
    paths: dict = {}

    def play(self, key: str) -> None:
        log.debug("sunet (dezactivat): %s", key)

    def engine(self, on: bool) -> None:
        pass

    def stop_all(self) -> None:
        pass

    def length(self, key: str) -> float:
        return 0.0

    def close(self) -> None:
        pass
