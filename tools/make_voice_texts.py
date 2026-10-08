#!/usr/bin/env python3
"""Scrie `sounds/voce/<limbă>/TEXTE.md`: textele de dat unui generator de voce (text-to-speech).

Româna vine din `rocket_demo/mission.py`, adaptată ca să fie citită corect: fără
simboluri (~, «»), cu unitățile scrise în cuvinte și cu termenii englezești scriși
cu litere mici (altfel unele voci îi citesc literă cu literă: „G-O”). Engleza vine
din `rocket_demo/mission_en.py`, deja scrisă pentru citit.

Rulează din nou după ce schimbi textele:  python3 tools/make_voice_texts.py
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from rocket_demo.config import VOICE_LANGUAGES  # noqa: E402
from rocket_demo.mission import voice_texts  # noqa: E402
from rocket_demo.mission_en import VOICE_EN  # noqa: E402

VOICE_ROOT = ROOT / "sounds" / "voce"
DRAFT_VOICE = {"en": "Samantha", "ro": "Ioana"}
SOURCE = {"en": "rocket_demo/mission_en.py", "ro": "rocket_demo/mission.py"}

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
# Textele pentru voce ({lang})

Generat de `python3 tools/make_voice_texts.py` din `{source}`. Nu edita de mână:
schimbă textul acolo și rulează din nou scriptul.

Pentru fiecare text de mai jos generează o voce (text-to-speech) și salveaz-o în acest
director cu **numele din titlu**, de ex. `sounds/voce/{lang}/etapa_liftoff.mp3`. Merg
`.mp3`, `.ogg` sau `.wav`. Fișierele tale au prioritate față de ciornele din
`sounds/voce/{lang}/ciorna/` (citite de vocea {draft} din macOS). Dacă lipsește și
ciorna, explicația e sărită, fără erori.
"""
HEADER_RO_NOTE = """
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


def spoken_texts(lang: str) -> dict[str, str]:
    """Cheie (numele fișierului) -> textul de citit, în ordinea din `voice_texts()`."""
    if lang == "en":
        return {key: VOICE_EN[key] for key in voice_texts()}
    return {key: spoken(title, text) for key, (title, text) in voice_texts().items()}


def render(lang: str) -> str:
    header = HEADER.format(lang=lang, source=SOURCE[lang], draft=DRAFT_VOICE[lang])
    parts = [header + (HEADER_RO_NOTE if lang == "ro" else "")]
    for key, text in spoken_texts(lang).items():
        parts.append(f"## `{key}`\n\n{text}\n")
    return "\n".join(parts)


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--root", type=Path, default=VOICE_ROOT, help=f"implicit {VOICE_ROOT}")
    args = p.parse_args(argv)
    for lang in VOICE_LANGUAGES:
        out = args.root / lang / "TEXTE.md"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(render(lang), encoding="utf-8")
        print(f"scris: {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
