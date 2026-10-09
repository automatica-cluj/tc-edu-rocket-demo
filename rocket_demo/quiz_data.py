"""Întrebările quiz-ului (doar date, ca `mission.py`).

Reguli pentru fiecare întrebare:
  * exact 3 variante; **prima variantă este cea corectă** (ordinea se amestecă la joc);
  * variante scurte (cel mult ~60 de caractere), ca să încapă pe cardurile de pe ecran;
  * o explicație de 1–2 propoziții, afișată după răspuns.

La fiecare rundă se aleg aleatoriu `Config.quiz_questions` întrebări (implicit 8).
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Question:
    text: str
    options: tuple[str, str, str]  # prima = răspunsul corect
    explanation: str


QUESTIONS = (
    Question(
        "Ce înseamnă MECO?",
        ("Oprirea motoarelor primei trepte", "Momentul decolării", "Intrarea pe orbită"),
        "MECO vine din engleză: Main Engine Cut-Off. Motoarele primei trepte se opresc, "
        "după ce au ars aproape tot combustibilul.",
    ),
    Question(
        "Ce înseamnă SECO?",
        ("Oprirea motorului treptei a doua", "Separarea treptelor", "Pornirea motoarelor"),
        "SECO vine din engleză: Second Engine Cut-Off. Când motorul treptei a doua se "
        "oprește, nava a ajuns pe orbită.",
    ),
    Question(
        "De ce au rachetele mai multe trepte?",
        (
            "Ca să arunce rezervoarele goale și să fie mai ușoare",
            "Ca să arate mai frumos",
            "Ca să zboare mai încet",
        ),
        "O treaptă goală e doar greutate în plus. Când e aruncată, restul rachetei "
        "accelerează mult mai ușor.",
    ),
    Question(
        "Ce este Max-Q?",
        (
            "Momentul în care aerul apasă cel mai tare pe rachetă",
            "Viteza maximă a rachetei",
            "Înălțimea maximă a zborului",
        ),
        "Racheta zboară deja foarte repede, dar aerul e încă dens, așa că apasă cel mai "
        "tare pe ea. Motoarele își reduc puțin puterea în acel moment.",
    ),
    Question(
        "Cu ce viteză trebuie să zboare o navă ca să rămână pe o orbită joasă?",
        ("Aproape 28.000 km/h", "Aproape 1.000 km/h", "Aproape 300 km/h"),
        "La ~200 km înălțime, nava are nevoie de ~7,8 km pe secundă. Așa cade încontinuu "
        "spre Pământ, dar merge atât de repede încât îl „ratează” mereu.",
    ),
    Question(
        "Spre ce direcție se lansează de obicei rachetele?",
        ("Spre est", "Spre vest", "Drept în sus, fără să se încline"),
        "Pământul se rotește spre est, așa că racheta pornește deja cu viteza de rotație "
        "a locului de lansare (până la ~1.600 km/h la Ecuator).",
    ),
    Question(
        "Cine a fost primul român care a zburat în spațiu?",
        ("Dumitru Prunariu", "Hermann Oberth", "Aurel Vlaicu"),
        "Dumitru Prunariu a zburat în mai 1981 cu nava Soiuz 40 și a stat aproape 8 zile "
        "în spațiu, la stația Saliut 6.",
    ),
    Question(
        "Ce a descris Conrad Haas la Sibiu, în secolul al XVI-lea?",
        ("Rachete cu mai multe trepte", "Primul avion", "Telescopul"),
        "În manuscrisul lui de la Sibiu, Conrad Haas a descris rachete cu mai multe "
        "trepte, cu sute de ani înaintea rachetelor moderne.",
    ),
    Question(
        "Cine a fost Hermann Oberth?",
        (
            "Un pionier al rachetelor, născut la Sibiu",
            "Primul om care a pășit pe Lună",
            "Inventatorul telefonului",
        ),
        "Hermann Oberth, născut la Sibiu în 1894, este unul dintre părinții zborului "
        "spațial. Cărțile lui i-au inspirat pe cei care au construit primele rachete mari.",
    ),
    Question(
        "Cine a fost primul om care a zburat în spațiu?",
        ("Iuri Gagarin", "Neil Armstrong", "Dumitru Prunariu"),
        "Iuri Gagarin a înconjurat Pământul pe 12 aprilie 1961, cu nava Vostok 1. "
        "Neil Armstrong a fost primul om care a pășit pe Lună, în 1969.",
    ),
    Question(
        "Care a fost primul satelit artificial al Pământului?",
        ("Sputnik 1", "Stația Spațială Internațională", "Telescopul Hubble"),
        "Sputnik 1 a fost lansat pe 4 octombrie 1957. Era o sferă metalică cam cât o "
        "minge de plajă, care trimitea semnale radio.",
    ),
    Question(
        "Ce misiune a dus primii oameni pe Lună?",
        ("Apollo 11", "Soiuz 40", "Vostok 1"),
        "În iulie 1969, Neil Armstrong și Buzz Aldrin au pășit pe Lună, iar Michael "
        "Collins i-a așteptat pe orbita Lunii.",
    ),
    Question(
        "Ce face turnul de salvare de pe vârful capsulei?",
        (
            "Trage capsula departe de rachetă dacă ceva merge prost",
            "Răcește motoarele",
            "Ține racheta dreaptă pe rampă",
        ),
        "Turnul are motoarele lui. La o problemă, smulge capsula cu astronauții departe "
        "de rachetă, iar capsula coboară apoi cu parașute.",
    ),
    Question(
        "Ce se întâmplă cu capsula după un ABORT?",
        (
            "Se desprinde de rachetă și coboară cu parașute",
            "Continuă singură spre orbită",
            "Rămâne prinsă de rachetă",
        ),
        "Siguranța echipajului e cea mai importantă. Sistemul de salvare desparte capsula "
        "de rachetă, iar parașutele o aduc în siguranță jos.",
    ),
    Question(
        "De ce plutesc astronauții în stația spațială?",
        (
            "Pentru că ei și stația cad împreună în jurul Pământului",
            "Pentru că în spațiu nu există deloc gravitație",
            "Pentru că stația are magneți",
        ),
        "La 400 km înălțime, gravitația e tot cam 90% din cea de la sol. Astronauții "
        "plutesc pentru că ei și stația cad împreună, încontinuu, în jurul Pământului.",
    ),
    Question(
        "Ce înseamnă „T-10” în numărătoarea inversă?",
        (
            "Mai sunt 10 secunde până la decolare",
            "Au trecut 10 secunde de la decolare",
            "Racheta are 10 motoare",
        ),
        "T este momentul decolării. „T minus” arată cât timp a mai rămas, iar „T plus” "
        "cât a trecut de la decolare.",
    ),
    Question(
        "De ce pornesc motoarele la T-3, înainte de decolare?",
        (
            "Ca să se verifice că împing destul de tare",
            "Ca să încălzească rampa de lansare",
            "Ca să consume combustibilul în plus",
        ),
        "Motoarele au nevoie de câteva secunde ca să ajungă la putere maximă. Racheta e "
        "ținută de cleme până calculatoarele confirmă că totul e în regulă.",
    ),
    Question(
        "Ce înseamnă „scrub” la o lansare?",
        (
            "Lansarea e anulată și se reîncearcă altă dată",
            "Racheta e spălată înainte de zbor",
            "Racheta a ajuns pe orbită",
        ),
        "Un „scrub” nu e un eșec: e mai bine să amâni lansarea decât să riști. Multe "
        "lansări sunt amânate din cauza vremii sau a unei probleme tehnice.",
    ),
    Question(
        "Ce se întâmplă dacă o singură echipă spune „NO-GO”?",
        ("Lansarea se oprește", "Lansarea continuă oricum", "Numărătoarea se grăbește"),
        "Înainte de lansare, fiecare echipă trebuie să spună „GO”. Un singur „NO-GO” "
        "ajunge ca lansarea să fie oprită până se rezolvă problema.",
    ),
    Question(
        "Ce verifică echipa Meteo înainte de lansare?",
        ("Vântul, norii și fulgerele", "Combustibilul din rezervoare", "Semnalul radio"),
        "Un vânt puternic la înălțime poate împinge racheta de pe traseu, iar fulgerele "
        "sunt periculoase. De aceea vremea poate amâna o lansare.",
    ),
    Question(
        "De ce are nevoie o rachetă, pe lângă combustibil, ca să-l poată arde?",
        ("De oxigen, pe care îl duce cu ea", "De aerul din jur, ca un avion", "De apă"),
        "În spațiu nu există aer, așa că racheta își duce singură oxigenul, de obicei "
        "oxigen lichid, foarte rece.",
    ),
    Question(
        "Cum poate o rachetă să accelereze în spațiu, unde nu e aer?",
        (
            "Aruncă gaze în spate, iar gazele o împing în față",
            "O trage Luna după ea",
            "Nu poate: în spațiu motoarele nu merg",
        ),
        "E legea a 3-a a lui Newton: racheta împinge gazele înapoi, iar gazele împing "
        "racheta înainte. Nu are nevoie de aer ca să se împingă în el.",
    ),
    Question(
        "De ce are motorul treptei a doua o duză mai mare?",
        (
            "E făcut special pentru vid, unde nu mai e aer",
            "Ca să încapă mai mult combustibil",
            "Ca să facă mai mult zgomot",
        ),
        "În vid, gazele se pot destinde mult mai tare, iar o duză mare le folosește mai "
        "bine ca să împingă racheta.",
    ),
    Question(
        "Ce a făcut prima treaptă a rachetei după separare?",
        (
            "S-a întors și a aterizat pe o platformă în ocean",
            "A ajuns și ea pe orbită",
            "A rămas atașată de treapta a doua",
        ),
        "Unele rachete moderne, ca Falcon 9, își aduc înapoi prima treaptă și o "
        "refolosesc, așa că lansările devin mai ieftine.",
    ),
    Question(
        "Cât durează aproximativ un ocol al Pământului pe o orbită joasă?",
        ("Aproximativ 90 de minute", "O zi", "O lună"),
        "La ~28.000 km/h, o navă pe orbită joasă înconjoară Pământul în ~90 de minute, "
        "așa că astronauții văd aproape 16 răsărituri pe zi.",
    ),
    Question(
        "La ce înălțime se consideră, de obicei, că începe spațiul?",
        ("Aproximativ 100 km", "Aproximativ 10 km", "Aproximativ 1.000 km"),
        "Granița folosită de obicei se numește linia Kármán și e la 100 km. Avioanele de "
        "pasageri zboară la doar ~10–12 km.",
    ),
    Question(
        "Cât cântărește la decolare o rachetă ca Falcon 9?",
        ("Aproape 550 de tone", "Aproape 5 tone", "Aproape 50.000 de tone"),
        "Cam cât 90 de elefanți mari! Cea mai mare parte e combustibil și oxigen, iar "
        "motoarele trebuie să împingă mai tare decât toată această greutate.",
    ),
)
