"""Piesele rachetei, pentru ecranul „Piesele rachetei” (LAUNCH ținut apăsat).

Fișierul conține DOAR date, de la vârful rachetei spre bază. Ca la `mission.py`, valorile
sunt aproximative, inspirate de o rachetă cu două trepte de tip Falcon 9 cu o capsulă
cu turn de salvare.

Câmpuri:
  * `label`: numele scurt de pe desen (pagina web);
  * `name`: numele complet, deasupra explicației;
  * `lcd`: numele pe LCD, fără diacritice, max. 16 caractere;
  * `text`: explicația, 1–2 propoziții.

Fiecare `key` are pe pagina web un desen `<g data-part="key">` în `web/static/index.html`.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Part:
    key: str
    label: str
    name: str
    lcd: str
    text: str


PARTS = (
    Part(
        key="les",
        label="Turn de salvare",
        name="Turnul de salvare",
        lcd="TURN SALVARE",
        text="Motoare-rachetă mici care, dacă ceva merge prost, trag capsula cu astronauții "
        "departe de rachetă. Se aruncă după aproximativ 3 minute, când nu mai e nevoie de el.",
    ),
    Part(
        key="capsule",
        label="Capsulă",
        name="Capsula cu echipajul",
        lcd="CAPSULA",
        text="Aici stau astronauții. E singura parte care se întoarce acasă: frânează în "
        "atmosferă, apoi coboară cu parașute.",
    ),
    Part(
        key="heat_shield",
        label="Scut termic",
        name="Scutul termic",
        lcd="SCUT TERMIC",
        text="Stratul de la baza capsulei. La întoarcere, aerul din fața capsulei se încinge la "
        "peste 1.500 °C, iar scutul îi protejează pe astronauți.",
    ),
    Part(
        key="stage2_tanks",
        label="Rezervoare T2",
        name="Treapta a 2-a: rezervoarele",
        lcd="REZERVOARE T2",
        text="Un rezervor cu combustibil și unul cu oxigen lichid. Motorul treptei a 2-a le "
        "arde împreună ca să ducă capsula până pe orbită.",
    ),
    Part(
        key="stage2_engine",
        label="Motor de vid",
        name="Motorul de vid",
        lcd="MOTOR DE VID",
        text="Un singur motor, cu o duză foarte mare, făcută pentru vid. Pornește abia după "
        "separarea treptelor, unde aproape nu mai există aer.",
    ),
    Part(
        key="interstage",
        label="Interetapă",
        name="Interetapa",
        lcd="INTERETAPA",
        text="Inelul care leagă cele două trepte și acoperă motorul de vid. Aici se face "
        "separarea: când apăsați STAGE, treptele se despart.",
    ),
    Part(
        key="grid_fins",
        label="Aripioare-grilă",
        name="Aripioarele-grilă",
        lcd="ARIPIOARE GRILA",
        text="Stau strânse în timpul urcării și se deschid doar la întoarcerea treptei 1. O "
        "ghidează prin aer, ca să ajungă exact deasupra platformei de aterizare.",
    ),
    Part(
        key="lox_tank",
        label="Rezervor oxigen",
        name="Rezervorul de oxigen lichid",
        lcd="REZERVOR OXIGEN",
        text="Oxigen răcit sub -183 °C, ca să devină lichid și să încapă mult într-un rezervor. "
        "Fără oxigen, combustibilul nu ar putea arde.",
    ),
    Part(
        key="fuel_tank",
        label="Rezervor kerosen",
        name="Rezervorul de combustibil",
        lcd="REZERVOR KEROSEN",
        text="Kerosen special pentru rachete (RP-1). Împreună cu oxigenul, treapta 1 duce cam "
        "400 de tone de combustibil la decolare.",
    ),
    Part(
        key="engines",
        label="Motoare",
        name="Motoarele principale",
        lcd="MOTOARE",
        text="La Falcon 9 sunt nouă motoare. Împreună împing de aproape 1,4 ori mai mult decât "
        "cântărește racheta la decolare, așa că ea poate urca.",
    ),
    Part(
        key="legs",
        label="Picioare",
        name="Picioarele de aterizare",
        lcd="PICIOARE",
        text="Stau strânse lângă treaptă în timpul zborului și se desfac chiar înainte de "
        "aterizare, ca treapta 1 să stea dreaptă pe platformă.",
    ),
)
