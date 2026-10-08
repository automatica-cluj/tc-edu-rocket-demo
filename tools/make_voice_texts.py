#!/usr/bin/env python3
"""Scrie `sounds/voce/TEXTE.md`: textele de dat unui generator de voce (text-to-speech).

Textele vin din `rocket_demo/mission.py`, adaptate ca să fie citite corect: fără
simboluri (~, «»), cu unitățile scrise în cuvinte și cu termenii englezești scriși
cu litere mici (altfel unele voci îi citesc literă cu literă: „G-O”).

Rulează din nou după ce schimbi textele din `mission.py`:  python3 tools/make_voice_texts.py
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from rocket_demo.mission import voice_texts  # noqa: E402

OUT = ROOT / "sounds" / "voce" / "TEXTE.md"

# Înlocuiri, în ordine: cele mai specifice întâi.
SPOKEN = (
    ("~28.000 km/h", "aproximativ douăzeci și opt de mii de kilometri pe oră"),
    ("28.000 km/h", "douăzeci și opt de mii de kilometri pe oră"),
    ("~200 km", "aproximativ 200 de kilometri"),
    ("~", "aproximativ "),
    ("T-3", "T minus 3"),
    ("Max-Q", "Max Q"),
    (
        "MECO = Main Engine Cut-Off. Motoarele primei trepte se opresc.",
        "MECO vine de la Main Engine Cut-Off, adică oprirea motoarelor principale.",
    ),
    ("a 2-a", "a doua"),
    ("Treapta 1", "Treapta întâi"),
    ("treapta 1", "treapta întâi"),
    ("«", ""),
    ("»", ""),
)
CAPS = re.compile(r"\b[A-ZĂÂÎȘȚ]{2,}(?:-[A-ZĂÂÎȘȚ]{2,})?\b")

HEADER = """\
# Textele pentru voce

Generat de `python3 tools/make_voice_texts.py` din `rocket_demo/mission.py`. Nu edita
de mână: schimbă textul în `mission.py` și rulează din nou scriptul.

Pentru fiecare text de mai jos generează o voce (text-to-speech) și salveaz-o în acest
director cu **numele din titlu**, de ex. `sounds/voce/etapa_liftoff.mp3`. Merg
`.mp3`, `.ogg` sau `.wav`. Fișierele tale au prioritate față de ciornele din
`sounds/voce/ciorna/` (citite de vocea Ioana din macOS). Dacă lipsește și ciorna,
explicația e sărită, fără erori.

Verifică pronunția termenilor englezești (Go, No-Go, Launch, Stage, Hold, Abort,
scrub, Max Q, MECO, Falcon, Crew Dragon). Dacă generatorul îi citește greșit, scrie-i
cum se pronunță doar în textul dat generatorului.
"""


def spoken(title: str, text: str) -> str:
    sentence = title if title[-1] in ".!?" else title + "."
    out = f"{sentence} {text}"
    for old, new in SPOKEN:
        out = out.replace(old, new)
    return CAPS.sub(lambda m: m.group(0).capitalize(), out)


def spoken_texts() -> dict[str, str]:
    """Cheie (numele fișierului) -> textul de citit."""
    return {key: spoken(title, text) for key, (title, text) in voice_texts().items()}


def render() -> str:
    parts = [HEADER]
    for key, text in spoken_texts().items():
        parts.append(f"## `{key}`\n\n{text}\n")
    return "\n".join(parts)


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--out", type=Path, default=OUT, help=f"fișierul scris (implicit {OUT})")
    args = p.parse_args(argv)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(render(), encoding="utf-8")
    print(f"scris: {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
