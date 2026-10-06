"""Conținutul misiunii: stațiile GO/NO-GO, etapele zborului, telemetria și explicațiile.

Fișierul conține DOAR date. Poți schimba textele, momentele și sunetele fără să
modifici logica programului.

Reguli pentru textele de pe LCD (câmpurile `lcd...`):
  * fără diacritice (LCD-ul nu le poate afișa);
  * stații: max. 13 caractere; etape: max. 9 caractere; HOLD: max. 16 caractere.

Valorile de zbor sunt aproximative, inspirate de o rachetă reală cu două trepte
(de tip Falcon 9) care duce o capsulă cu echipaj pe o orbită joasă (~200 km).
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Check:
    """O stație din verificarea GO/NO-GO."""

    lcd: str
    name: str
    info: str
    hold_lcd: str
    hold_info: str


@dataclass(frozen=True)
class FlightEvent:
    """O etapă a zborului."""

    key: str
    t: float  # secunde după decolare (timpul real al misiunii)
    lcd: str
    title: str
    info: str
    sound: str | None = None
    engine: bool | None = None  # True = pornește sunetul de motor, False = îl oprește
    needs_stage: bool = False  # aici elevii trebuie să apese STAGE


@dataclass(frozen=True)
class Info:
    title: str
    text: str


@dataclass(frozen=True)
class Mission:
    checks: tuple[Check, ...]
    events: tuple[FlightEvent, ...]
    # (secunde după decolare, altitudine km, viteză m/s)
    telemetry: tuple[tuple[float, float, float], ...]
    state_info: dict[str, Info]


CHECKS = (
    Check(
        lcd="METEO",
        name="Meteo",
        info="Meteorologii verifică vântul, norii și fulgerele. Un vânt puternic la "
        "înălțime poate împinge racheta de pe traseu.",
        hold_lcd="Vant prea tare",
        hold_info="Vânt prea puternic la înălțime! Așteptăm să se calmeze. În realitate, "
        "multe lansări sunt amânate din cauza vremii.",
    ),
    Check(
        lcd="PROPULSIE",
        name="Propulsie",
        info="Echipa de propulsie verifică motoarele și rezervoarele. Racheta are nevoie "
        "de combustibil, dar și de oxigen lichid ca să-l poată arde.",
        hold_lcd="Presiune mica",
        hold_info="Presiunea dintr-un rezervor este prea mică. Inginerii o corectează "
        "înainte să continuăm.",
    ),
    Check(
        lcd="GHIDARE",
        name="Ghidare",
        info="Se verifică calculatoarele de bord și senzorii care țin racheta pe traseul "
        "corect, fără ajutorul unui pilot.",
        hold_lcd="Eroare senzor",
        hold_info="Un senzor a trimis o valoare ciudată. Calculatorul este repornit și "
        "verificat din nou.",
    ),
    Check(
        lcd="COMUNICATII",
        name="Comunicații",
        info="Antenele de pe sol trebuie să primească semnalul rachetei pe tot drumul, ca "
        "echipa să știe în fiecare secundă ce se întâmplă.",
        hold_lcd="Semnal slab",
        hold_info="Semnalul radio este prea slab. Se reglează antenele de la sol.",
    ),
    Check(
        lcd="SIGURANTA",
        name="Siguranța zonei",
        info="Zona din jurul rampei și traseul peste ocean trebuie să fie libere: nicio "
        "navă și niciun avion acolo unde ar putea cădea bucăți din rachetă.",
        hold_lcd="Barca in zona",
        hold_info="O barcă a intrat în zona interzisă! Lansarea așteaptă până pleacă. "
        "Chiar s-a întâmplat de multe ori!",
    ),
)

EVENTS = (
    FlightEvent(
        key="liftoff",
        t=0,
        lcd="DECOLARE",
        title="Decolare!",
        info="Motoarele împing mai tare decât cântărește racheta, așa că ea începe să "
        "urce. La start, o rachetă ca Falcon 9 cântărește aproape 550 de tone, cam cât "
        "90 de elefanți!",
        sound="liftoff",
        engine=True,
    ),
    FlightEvent(
        key="pitch",
        t=12,
        lcd="INCLINARE",
        title="Turnul a rămas în urmă",
        info="Racheta a trecut de turnul de lansare și începe să se încline spre est. "
        "Pentru a ajunge pe orbită contează mai mult viteza «în lateral» decât "
        "înălțimea, iar spre est ne ajută și rotația Pământului.",
    ),
    FlightEvent(
        key="maxq",
        t=72,
        lcd="MAX-Q",
        title="Max-Q: presiunea maximă",
        info="Zburăm deja mai repede decât sunetul, dar aerul este încă dens, așa că "
        "apasă cel mai tare pe rachetă. Motoarele își reduc puțin puterea ca racheta "
        "să nu fie solicitată prea mult.",
        sound="maxq",
    ),
    FlightEvent(
        key="meco",
        t=150,
        lcd="MECO",
        title="MECO: treapta 1 se oprește",
        info="MECO = Main Engine Cut-Off. Combustibilul primei trepte s-a terminat, iar "
        "motoarele se opresc. În doar două minute și jumătate au ars peste 400 de tone "
        "de combustibil și oxigen!",
        sound="meco",
        engine=False,
    ),
    FlightEvent(
        key="separation",
        t=153,
        lcd="SEPARARE",
        title="Separarea treptelor",
        info="Treapta 1, acum goală, se desprinde. Fără greutatea ei, restul rachetei "
        "accelerează mult mai ușor. De aceea rachetele au mai multe trepte!",
        sound="separation",
        needs_stage=True,
    ),
    FlightEvent(
        key="stage2",
        t=161,
        lcd="TREAPTA 2",
        title="Pornește treapta a 2-a",
        info="Motorul treptei a doua se aprinde. Are o duză mult mai mare, construită "
        "special pentru vid, unde aproape nu mai există aer.",
        sound="stage2_ignition",
        engine=True,
    ),
    FlightEvent(
        key="les",
        t=190,
        lcd="TURN SALV",
        title="Turnul de salvare se desprinde",
        info="Pe vârful capsulei e un mic turn cu motoare-rachetă. Dacă ceva nu merge "
        "bine, el trage capsula cu astronauții departe de rachetă. Acum suntem destul "
        "de sus și nu mai e nevoie de el.",
        sound="les_jettison",
    ),
    FlightEvent(
        key="speed",
        t=300,
        lcd="ACCELERAM",
        title="Câștigăm viteză",
        info="Racheta aproape nu mai urcă, ci accelerează pe orizontală. Pe orbită, nava "
        "cade încontinuu spre Pământ, dar merge atât de repede încât îl «ratează» mereu. "
        "Pentru asta e nevoie de aproape 28.000 km/h!",
    ),
    FlightEvent(
        key="landing",
        t=470,
        lcd="ATERIZARE",
        title="Treapta 1 a aterizat!",
        info="Între timp, prima treaptă s-a întors și a aterizat vertical pe o platformă "
        "din ocean. Unele rachete moderne își refolosesc treptele, ca un avion, iar "
        "lansările devin mai ieftine.",
        sound="landing",
    ),
    FlightEvent(
        key="seco",
        t=510,
        lcd="SECO",
        title="SECO: suntem pe orbită!",
        info="Motorul treptei 2 se oprește: am ajuns pe orbită la ~200 km înălțime și "
        "~28.000 km/h. Cu viteza asta ai ajunge de la București la Cluj în mai puțin "
        "de un minut și ai înconjura Pământul în aproximativ 90 de minute!",
        sound="orbit",
        engine=False,
    ),
)

TELEMETRY = (
    (0, 0.0, 0),
    (12, 0.3, 50),
    (30, 2.0, 150),
    (60, 8.0, 330),
    (72, 12.0, 450),
    (100, 25.0, 850),
    (130, 45.0, 1500),
    (150, 65.0, 2200),
    (161, 72.0, 2180),
    (190, 105.0, 2450),
    (300, 165.0, 4000),
    (400, 190.0, 5800),
    (510, 200.0, 7800),
)

STATE_INFO = {
    "idle": Info(
        "Pregătiți pentru lansare",
        "Apăsați GO ca să începeți verificările. Înainte de orice lansare, fiecare echipă "
        "din centrul de control trebuie să spună «GO».",
    ),
    "ready": Info(
        "Toate echipele: GO!",
        "Directorul de zbor dă undă verde. Apăsați LAUNCH ca să porniți numărătoarea "
        "inversă.",
    ),
    "countdown": Info(
        "Numărătoarea inversă",
        "În ultimele secunde, calculatoarele preiau controlul. La T-3 pornesc motoarele, "
        "dar racheta e ținută de cleme până se confirmă că împing destul de tare.",
    ),
    "scrub": Info(
        "Lansare anulată (scrub)",
        "Lansarea a fost oprită înainte de decolare. Nu e un eșec: e mai bine să încerci "
        "altă dată decât să riști. Apăsați GO pentru o nouă încercare.",
    ),
    "abort": Info(
        "ABORT! Salvăm echipajul",
        "Sistemul de salvare a desprins capsula de rachetă. Capsula coboară cu parașute, "
        "iar astronauții sunt în siguranță. Siguranța echipajului e cea mai importantă! "
        "Apăsați GO pentru o nouă misiune.",
    ),
    "orbit": Info(
        "Misiune îndeplinită!",
        "Felicitări, echipă! Capsula este pe orbită la ~200 km deasupra Pământului și "
        "face un ocol complet în ~90 de minute. Apăsați GO pentru o nouă misiune.",
    ),
}

# Sunetele folosite de demo: cheie -> când se redă.
SOUNDS = {
    "go_beep": "confirmare GO pentru fiecare stație și la apăsarea butoanelor în selftest",
    "hold": "o stație cere HOLD (oprire temporară)",
    "all_go": "toate stațiile au spus GO",
    "countdown": "pornește la T-10 (ideal o voce care numără 10...1)",
    "ignition": "la T-3, aprinderea motoarelor",
    "liftoff": "la T-0, decolarea",
    "engine_loop": "zgomot de motor, se repetă cât timp motoarele merg",
    "maxq": "momentul Max-Q",
    "meco": "oprirea motoarelor treptei 1",
    "stage_prompt": "alarmă: «apăsați STAGE!»",
    "separation": "separarea treptelor (o bufnitură)",
    "stage2_ignition": "pornirea treptei a 2-a",
    "les_jettison": "desprinderea turnului de salvare",
    "landing": "treapta 1 a aterizat",
    "orbit": "am ajuns pe orbită (aplauze/fanfară)",
    "abort_alarm": "ABORT în zbor (sirenă)",
    "scrub": "lansare anulată înainte de decolare",
}

DEFAULT_MISSION = Mission(
    checks=CHECKS, events=EVENTS, telemetry=TELEMETRY, state_info=STATE_INFO
)
