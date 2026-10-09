# Sunete

Pune sample-urile tale în acest director, cu numele de mai jos. Cele care sunt deja
aici sunt înregistrări reale NASA (apeluri radio și vuietul lansării); sursele sunt în
[SURSE.md](SURSE.md). Extensia poate fi
`.wav`, `.ogg` sau `.mp3`; recomandăm **WAV sau OGG**.

Sunetele tale au prioritate. Pentru cele care lipsesc, demo-ul folosește sunete
provizorii din `sounds/placeholder/`, generate de `install.sh` sau de
`python3 tools/make_placeholder_sounds.py`. Dacă lipsește și cel provizoriu, demo-ul
merge mai departe fără sunetul respectiv.

| Fișier | Când se redă | Durată sugerată |
|---|---|---|
| `go_beep` | fiecare stație confirmă GO | < 0,5 s |
| `hold` | o stație cere HOLD | 1–3 s |
| `all_go` | toate stațiile au spus GO (de ex. „All stations go for launch”) | 1–4 s |
| `countdown` | pornește exact la **T-10**; ideal o voce care numără 10…1 | ~10 s |
| `ignition` | la **T-3**, aprinderea motoarelor | 2–4 s |
| `liftoff` | la **T-0**, decolarea („Liftoff!” + vuiet) | 3–8 s |
| `engine_loop` | zgomot de motor, **repetat în buclă** cât timp motoarele merg | 2–10 s, fără pauze la capete |
| `pitch` | racheta a trecut de turn și se înclină („roll program”) | 1–5 s |
| `maxq` | momentul Max-Q (o voce sau un semnal scurt) | 1–3 s |
| `meco` | oprirea motoarelor treptei 1 | 1–3 s |
| `stage_prompt` | alarmă „apăsați STAGE!” | 1–2 s |
| `separation` | separarea treptelor (o bufnitură) | < 1 s |
| `stage2_ignition` | pornirea treptei a 2-a | 1–3 s |
| `les_jettison` | desprinderea turnului de salvare | < 1 s |
| `landing` | treapta 1 a aterizat | 1–3 s |
| `orbit` | am ajuns pe orbită (aplauze, fanfară) | 3–10 s |
| `abort_alarm` | ABORT în zbor (sirenă) | 2–5 s |
| `scrub` | lansare anulată înainte de decolare | 1–3 s |
| `quiz_start` | începe o rundă de quiz | 1–2 s |
| `quiz_correct` | răspuns corect la quiz | < 1 s |
| `quiz_wrong` | răspuns greșit sau timp expirat | < 1 s |
| `quiz_tick` | tic-tac în ultimele 5 secunde ale unei întrebări | < 0,2 s |
| `quiz_end` | finalul quiz-ului, cu scorul | 2–4 s |

Vocea care citește explicațiile are directorul ei, `sounds/voce/<limbă>/`; textele și
numele fișierelor sunt în [voce/en/TEXTE.md](voce/en/TEXTE.md) și
[voce/ro/TEXTE.md](voce/ro/TEXTE.md).

## Sfaturi

- **Ascultă un sunet pe Pi:** `.venv/bin/python -m rocket_demo --play liftoff`.
  Toate pe rând: `--play all`. Oprește întâi serviciul:
  `systemctl --user stop rocket-demo`.
- **Alte nume de fișiere:** dacă nu vrei să redenumești fișierele, completează
  `sound_files` în `rocket_demo/config.py`, de exemplu
  `{"liftoff": "apollo11_liftoff.mp3"}`.
- **Volumul:** adu toate sample-urile la un nivel apropiat (de ex. în Audacity:
  Effect → Normalize). Volumul general se reglează cu `alsamixer` sau din
  `sound_volume` în `config.py`.
- **Countdown:** taie sample-ul astfel încât „10” să se audă din prima secundă.
  Altfel vocea nu se va potrivi cu numărătoarea de pe LCD.
- **Surse gratuite:** înregistrările NASA (de exemplu, misiunile Apollo și Space
  Shuttle) sunt în general libere pentru uz educațional. Pe freesound.org caută
  fișiere cu licență CC0 sau CC-BY.
