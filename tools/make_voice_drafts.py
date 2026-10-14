#!/usr/bin/env python3
"""Generează ciornele de voce din `sounds/voce/<limbă>/ciorna/` cu vocile din macOS.

Ciornele sunt doar ca demo-ul să aibă voce de la început: fișierele tale din
`sounds/voce/<limbă>/` (de ex. generate pe elevenlabs.io) au prioritate față de ele.
Vocile: Samantha pentru engleză, Ioana pentru română.

Merge doar pe macOS și are nevoie de un encoder MP3:
    pip install lameenc
    python3 tools/make_voice_drafts.py                      # toate, în ambele limbi
    python3 tools/make_voice_drafts.py --lang en etapa_les  # doar unele
"""

from __future__ import annotations

import argparse
import subprocess
import sys
import tempfile
import wave
from pathlib import Path

from make_voice_texts import DRAFT_VOICE, VOICE_LANGUAGES, VOICE_ROOT, spoken_texts

RATE = 22050
KBPS = 48


def to_mp3(wav_path: Path, mp3_path: Path) -> None:
    import lameenc

    with wave.open(str(wav_path)) as w:
        pcm = w.readframes(w.getnframes())
        rate, channels = w.getframerate(), w.getnchannels()
    enc = lameenc.Encoder()
    enc.set_bit_rate(KBPS)
    enc.set_in_sample_rate(rate)
    enc.set_channels(channels)
    enc.set_quality(2)
    mp3_path.write_bytes(enc.encode(pcm) + enc.flush())


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("keys", nargs="*", help="doar aceste explicații (implicit toate)")
    p.add_argument("--lang", choices=VOICE_LANGUAGES, help="doar această limbă (implicit toate)")
    p.add_argument("--voice", help="altă voce din macOS (`say -v '?'` le arată)")
    args = p.parse_args(argv)

    for lang in [args.lang] if args.lang else VOICE_LANGUAGES:
        texts = spoken_texts(lang)
        unknown = [k for k in args.keys if k not in texts]
        if unknown:
            print(f"necunoscute: {', '.join(unknown)}. Variante: {', '.join(texts)}")
            return 2
        out_dir = VOICE_ROOT / lang / "ciorna"
        out_dir.mkdir(parents=True, exist_ok=True)
        voice = args.voice or DRAFT_VOICE[lang]
        with tempfile.TemporaryDirectory() as tmp:
            for key in args.keys or texts:
                wav = Path(tmp) / f"{key}.wav"
                subprocess.run(
                    ["say", "-v", voice, "-o", str(wav), f"--data-format=LEI16@{RATE}", texts[key]],
                    check=True,
                )
                to_mp3(wav, out_dir / f"{key}.mp3")
                print(f"scris: {out_dir / key}.mp3")
    return 0


if __name__ == "__main__":
    sys.exit(main())
