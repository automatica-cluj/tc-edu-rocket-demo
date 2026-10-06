"""Sunet prin pygame.mixer (ALSA → mufa jack 3,5 mm → difuzor activ)."""

from __future__ import annotations

import logging
import os
from pathlib import Path

log = logging.getLogger(__name__)

EXTENSIONS = (".wav", ".ogg", ".mp3")
ENGINE_KEY = "engine_loop"


def find_sound(dirs: list[Path], name: str) -> Path | None:
    """Caută `name` (cu sau fără extensie) în directoare, în ordine."""
    candidates = [name] if Path(name).suffix else [name + ext for ext in EXTENSIONS]
    for directory in dirs:
        for candidate in candidates:
            path = Path(directory) / candidate
            if path.is_file():
                return path
    return None


class Audio:
    def __init__(self, dirs: list[Path], keys, files: dict[str, str] | None = None, volume=1.0):
        os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")
        import pygame

        self._pygame = pygame
        pygame.mixer.pre_init(frequency=44100, size=-16, channels=2, buffer=1024)
        pygame.mixer.init()
        pygame.mixer.set_num_channels(16)
        pygame.mixer.set_reserved(1)  # canalul 0 e doar pentru motor
        self._engine_channel = pygame.mixer.Channel(0)

        files = files or {}
        self.sounds = {}
        self.paths: dict[str, Path] = {}
        missing = []
        for key in keys:
            path = find_sound(dirs, files.get(key, key))
            if path is None:
                missing.append(key)
                continue
            try:
                sound = pygame.mixer.Sound(str(path))
            except pygame.error as exc:
                log.warning("nu pot citi %s: %s", path, exc)
                continue
            sound.set_volume(volume)
            self.sounds[key] = sound
            self.paths[key] = path
        log.info("sunete încărcate: %d/%d", len(self.sounds), len(list(keys)))
        if missing:
            log.warning("lipsesc sunetele: %s (demo-ul merge și fără ele)", ", ".join(missing))

    def play(self, key: str) -> None:
        sound = self.sounds.get(key)
        if sound is not None:
            sound.play()

    def engine(self, on: bool) -> None:
        sound = self.sounds.get(ENGINE_KEY)
        if sound is None:
            return
        if on:
            if not self._engine_channel.get_busy():
                self._engine_channel.play(sound, loops=-1, fade_ms=500)
        else:
            self._engine_channel.fadeout(800)

    def stop_all(self) -> None:
        self._pygame.mixer.stop()

    def length(self, key: str) -> float:
        sound = self.sounds.get(key)
        return sound.get_length() if sound else 0.0

    def close(self) -> None:
        self._pygame.mixer.quit()


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
