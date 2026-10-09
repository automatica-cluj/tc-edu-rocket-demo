#!/usr/bin/env python3
"""Generează sunete provizorii (bip-uri, zgomot de motor, sirenă) în `sounds/placeholder/`.

Demo-ul merge astfel de la început. Când ai sample-urile tale, pune-le în `sounds/`
cu aceleași nume (de ex. `sounds/liftoff.wav`); ele au prioritate față de acestea.

Folosește doar biblioteca standard Python:  python3 tools/make_placeholder_sounds.py
"""

from __future__ import annotations

import argparse
import math
import random
import wave
from array import array
from pathlib import Path

RATE = 22050
OUT_DIR = Path(__file__).resolve().parent.parent / "sounds" / "placeholder"
rng = random.Random(42)


def silence(dur):
    return [0.0] * int(RATE * dur)


def tone(freq, dur, vol=0.5, freq_end=None, attack=0.01, release=0.05):
    n = int(RATE * dur)
    freq_end = freq if freq_end is None else freq_end
    out, phase = [], 0.0
    for i in range(n):
        f = freq + (freq_end - freq) * i / n
        phase += 2 * math.pi * f / RATE
        env = min(1.0, i / (attack * RATE + 1), (n - i) / (release * RATE + 1))
        out.append(vol * env * math.sin(phase))
    return out


def noise(dur, vol=0.6, smooth=0.08, envelope=lambda x: 1.0):
    """Zgomot filtrat trece-jos (`smooth` mic = mai grav, ca un motor de rachetă)."""
    n = int(RATE * dur)
    out, y = [], 0.0
    for i in range(n):
        y += smooth * (rng.uniform(-1, 1) - y)
        out.append(y * envelope(i / n))
    peak = max(abs(s) for s in out) or 1.0
    return [s / peak * vol for s in out]


def concat(*parts):
    out = []
    for part in parts:
        out.extend(part)
    return out


def mix(*parts):
    out = [0.0] * max(len(p) for p in parts)
    for part in parts:
        for i, s in enumerate(part):
            out[i] += s
    return out


def beeps(freq, count, on=0.1, off=0.08, vol=0.5):
    return concat(*[concat(tone(freq, on, vol), silence(off)) for _ in range(count)])


def countdown():
    # Un bip pe secundă, de la T-10 la T-1; ultimele trei mai înalte.
    parts = []
    for i in range(10):
        freq = 1400 if i >= 7 else 1000
        parts += [tone(freq, 0.12, 0.5), silence(0.88)]
    return concat(*parts)


def siren(dur, low=600, high=1200, period=1.0, vol=0.5):
    n = int(RATE * dur)
    out, phase = [], 0.0
    for i in range(n):
        x = (i / RATE) % period / period
        f = low + (high - low) * (1 - abs(2 * x - 1))
        phase += 2 * math.pi * f / RATE
        out.append(vol * math.sin(phase))
    return out


SOUNDS = {
    "go_beep": lambda: tone(880, 0.15),
    "hold": lambda: concat(tone(440, 0.25), silence(0.1), tone(330, 0.45)),
    "all_go": lambda: concat(*[tone(f, 0.15) for f in (523, 659, 784)], tone(1047, 0.4)),
    "countdown": countdown,
    "ignition": lambda: noise(3.0, 0.8, 0.06, envelope=lambda x: x**1.5),
    "liftoff": lambda: noise(4.0, 0.9, 0.08, envelope=lambda x: min(1, x * 10) * (1 - x) ** 0.5),
    "engine_loop": lambda: noise(3.0, 0.5, 0.05),
    "pitch": lambda: concat(tone(523, 0.12), tone(659, 0.25)),
    "maxq": lambda: concat(tone(660, 0.2), tone(880, 0.35)),
    "meco": lambda: tone(600, 0.8, freq_end=200),
    "stage_prompt": lambda: concat(beeps(1200, 3), silence(0.25), beeps(1200, 3)),
    "separation": lambda: mix(
        noise(0.6, 0.8, 0.3, envelope=lambda x: math.exp(-8 * x)),
        tone(60, 0.5, 0.6, release=0.4),
    ),
    "stage2_ignition": lambda: noise(1.5, 0.6, 0.1, envelope=lambda x: min(1, x * 3)),
    "les_jettison": lambda: concat(
        noise(0.25, 0.7, 0.4, envelope=lambda x: math.exp(-10 * x)),
        tone(300, 0.4, 0.4, freq_end=900),
    ),
    "landing": lambda: concat(tone(784, 0.2), tone(1047, 0.5)),
    "orbit": lambda: concat(
        *[tone(f, 0.18) for f in (523, 659, 784)],
        mix(tone(523, 1.2, 0.25), tone(659, 1.2, 0.25), tone(1047, 1.2, 0.25)),
    ),
    "abort_alarm": lambda: siren(4.0),
    "scrub": lambda: concat(tone(400, 0.3), silence(0.05), tone(300, 0.6)),
}


def write_wav(path: Path, samples) -> None:
    data = array("h", (int(max(-1.0, min(1.0, s)) * 32767) for s in samples))
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(RATE)
        w.writeframes(data.tobytes())


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--out", type=Path, default=OUT_DIR)
    parser.add_argument("--force", action="store_true", help="rescrie fișierele existente")
    args = parser.parse_args(argv)

    args.out.mkdir(parents=True, exist_ok=True)
    for name, make in SOUNDS.items():
        path = args.out / f"{name}.wav"
        if path.exists() and not args.force:
            continue
        write_wav(path, make())
        print(f"generat {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
