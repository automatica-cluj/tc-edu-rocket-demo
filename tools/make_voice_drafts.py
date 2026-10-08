#!/usr/bin/env python3
"""Generează ciornele de voce din `sounds/voce/ciorna/` cu vocea Ioana din macOS.

Ciornele sunt doar ca demo-ul să aibă voce de la început: fișierele tale din
`sounds/voce/` (de ex. generate pe elevenlabs.io) au prioritate față de ele.

Merge doar pe macOS și are nevoie de un encoder MP3:
    pip install lameenc
    python3 tools/make_voice_drafts.py              # toate
    python3 tools/make_voice_drafts.py etapa_les    # doar unele
"""

from __future__ import annotations

import argparse
import subprocess
import sys
import tempfile
import wave
from pathlib import Path

from make_voice_texts import ROOT, spoken_texts

OUT_DIR = ROOT / "sounds" / "voce" / "ciorna"
VOICE = "Ioana"
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
    p.add_argument("--voice", default=VOICE, help=f"vocea din macOS (implicit {VOICE})")
    p.add_argument("--out", type=Path, default=OUT_DIR)
    args = p.parse_args(argv)

    texts = spoken_texts()
    unknown = [k for k in args.keys if k not in texts]
    if unknown:
        print(f"necunoscute: {', '.join(unknown)}. Variante: {', '.join(texts)}")
        return 2
    args.out.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        for key in args.keys or texts:
            wav = Path(tmp) / f"{key}.wav"
            subprocess.run(
                ["say", "-v", args.voice, "-o", str(wav), f"--data-format=LEI16@{RATE}", texts[key]],
                check=True,
            )
            to_mp3(wav, args.out / f"{key}.mp3")
            print(f"scris: {args.out / key}.mp3")
    return 0


if __name__ == "__main__":
    sys.exit(main())
