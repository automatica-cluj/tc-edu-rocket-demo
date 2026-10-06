# tc-edu-rocket-demo

Demo educațional pentru elevi de 12–14 ani, care rulează pe un **Raspberry Pi**. Arată
etapele lansării unei rachete, de la verificările GO/NO-GO până pe orbită.

- **Butoane fizice:** GO, LAUNCH, STAGE și ABORT.
- **LCD 16x2:** arată etapa, numărătoarea inversă, altitudinea și viteza.
- **Difuzor:** fiecare etapă are sunetul ei.
- **Pagină web:** racheta animată, telemetria și explicații „Știai că…?”. O poți
  deschide pe calculatorul clasei sau pe proiector.

```
GO x5 stații ─► LAUNCH ─► T-10 … T-3 aprindere … T-0 DECOLARE
   ─► Max-Q ─► MECO ─► [STAGE] separare ─► treapta 2 ─► turn de salvare
   ─► treapta 1 aterizează ─► SECO: ORBITĂ!          (ABORT oricând)
```

Ghidul pentru oră (roluri, întrebări, explicații): [docs/ghid-profesor.md](docs/ghid-profesor.md).

---

## 1. De ce ai nevoie

| Componentă | Observații |
|---|---|
| Raspberry Pi 3 Model B+, 4 sau 5 + card microSD ≥ 8 GB | Raspberry Pi OS **Lite** (64-bit), versiunea curentă |
| Alimentator | Pi 3B+: 5V/2,5A · Pi 4: 5V/3A · Pi 5: 5V/5A (27 W, oficial) |
| LCD 1602 cu adaptor I2C (PCF8574) | 4 fire: GND, VCC, SDA, SCL |
| 4 butoane | ideal mari, de tip „arcade”; ABORT roșu |
| Difuzor activ (cu alimentare proprie) | Pi 3/4: în mufa jack 3,5 mm. **Pi 5 nu are jack**: folosește o placă de sunet USB (adaptor USB → jack 3,5 mm) sau un difuzor USB. |
| Breadboard, T-cobbler, fire | |

**Raspberry Pi 5:** codul e același. Pinii GPIO, I2C-ul și butoanele sunt identice. Diferențele sunt
doar de hardware: sunetul merge printr-o placă de sunet USB, iar alimentatorul trebuie să fie de 5A.

## 2. Cablare

Numerotarea pinilor: **fizic** (1–40) și **BCM** (GPIOxx).

| Componentă | Pin Pi (fizic) | GPIO |
|---|---|---|
| LCD GND | 6 (sau orice GND) | – |
| LCD VCC | 2 (5V) | – |
| LCD SDA | 3 | GPIO2 |
| LCD SCL | 5 | GPIO3 |
| Buton **GO** | 29 | GPIO5 |
| Buton **LAUNCH** | 31 | GPIO6 |
| Buton **STAGE** | 33 | GPIO13 |
| Buton **ABORT** | 35 | GPIO19 |
| Celălalt picior al fiecărui buton | 39 (GND) | – |

```
             Raspberry Pi (header 40 pini, vedere de sus)
        3V3  (1) (2)  5V ──────────── LCD VCC
LCD SDA ─ GPIO2  (3) (4)  5V
LCD SCL ─ GPIO3  (5) (6)  GND ─────────── LCD GND
                  ...
     GO ─ GPIO5 (29) (30) GND
 LAUNCH ─ GPIO6 (31) (32)
  STAGE ─ GPIO13(33) (34) GND
  ABORT ─ GPIO19(35) (36)
                (37) (38)
butoane ─── GND (39) (40)
```

- Butoanele nu au nevoie de rezistențe: folosim rezistența pull-up internă a Pi-ului.
  Fiecare buton se leagă între pinul lui și GND.
- Pinii se pot schimba din `rocket_demo/config.py` (`button_pins`).
- *Notă:* adaptorul I2C alimentat la 5V își trage liniile SDA/SCL puțin peste 3,3 V. În
  practică merge, dar varianta corectă electric este un mic level-shifter I2C.

## 3. Instalare pe Raspberry Pi

1. Scrie pe card **Raspberry Pi OS Lite (64-bit)** cu Raspberry Pi Imager. În setări:
   - hostname `racheta`;
   - activează SSH;
   - completează rețeaua Wi-Fi.
2. Conectează-te la Pi (`ssh pi@racheta.local`) și rulează:

   ```bash
   sudo apt-get install -y git
   git clone https://github.com/automatica-cluj/tc-edu-rocket-demo.git
   cd tc-edu-rocket-demo
   ./install.sh
   ```

   Scriptul face următoarele:
   - instalează pachetele;
   - activează I2C;
   - creează mediul Python;
   - generează sunete provizorii;
   - pornește demo-ul automat la fiecare boot.
3. Alege ieșirea audio: `sudo raspi-config` → *System Options* → *Audio* →
   **Headphones** (jack-ul de pe Pi 3/4) sau placa de sunet **USB** (Pi 5).
4. Repornește Pi-ul: `sudo reboot`.
5. Verifică hardware-ul:

   ```bash
   sudo systemctl stop rocket-demo
   .venv/bin/python -m rocket_demo --selftest   # LCD + sunet + fiecare buton
   sudo systemctl start rocket-demo
   ```

## 4. Utilizare

1. La pornire, LCD-ul arată „MISIUNE AURORA / Apasa GO”, alternând cu adresa paginii
   web.
2. **GO** pornește verificările. Fiecare dintre cele 5 stații cere câte un **GO**. Uneori
   o stație cere **HOLD**; după câteva secunde problema se rezolvă și se cere din nou GO.
3. **LAUNCH** pornește numărătoarea de la T-10. Motoarele se aprind la T-3, iar la T-0
   racheta decolează.
4. Zborul este accelerat de 4 ori: 8 minute și jumătate de misiune durează ~2 minute.
   - După MECO, LCD-ul cere **STAGE**. Dacă nimeni nu apasă în 8 secunde, separarea se
     face automat.
   - **ABORT** în timpul numărătorii anulează lansarea (scrub). În zbor, ABORT salvează
     capsula.
5. Pe orbită, după abort sau după un scrub, **GO** pornește o misiune nouă.
6. **Ținând ABORT apăsat 3 secunde**, demo-ul se resetează (util pentru profesor).

### Pagina web

Deschide în browser, pe un calculator din aceeași rețea:
**`http://racheta.local:8000`** sau `http://<IP>:8000` (IP-ul apare pe LCD).

- Pagina se actualizează singură. Poate fi deschisă pe mai multe calculatoare deodată.
- Cu `http://racheta.local:8000/?control=1` apar și butoane virtuale (GO, LAUNCH,
  STAGE, ABORT, RESET). Sunt utile la teste sau dacă un buton fizic nu merge. Le poți
  dezactiva cu `web_control = False` în `config.py`.
- **Dacă rețeaua școlii nu permite** conexiunea între dispozitive, ai două variante.
  - **Pi-ul creează propria rețea Wi-Fi:**

    ```bash
    sudo nmcli device wifi hotspot ifname wlan0 ssid Racheta password lansare123
    ```

    Conectează laptopul la rețeaua „Racheta” și deschide `http://10.42.0.1:8000`.
  - **Cablu Ethernet direct** între Pi și laptop, apoi `http://racheta.local:8000`.

## 5. Sunete

Pune sample-urile în `sounds/` cu numele din [sounds/README.md](sounds/README.md), de
exemplu `sounds/liftoff.wav`. Ele înlocuiesc automat sunetele provizorii. Ca să asculți
unul: `.venv/bin/python -m rocket_demo --play liftoff`.

## 6. Personalizare

- **`rocket_demo/config.py`:**
  - numele misiunii;
  - pinii butoanelor și adresa LCD-ului;
  - accelerarea zborului (`time_scale`);
  - HOLD-uri aleatoare (`hold_probability`);
  - separarea cu STAGE (`interactive_stage`);
  - portul paginii web.
- **`rocket_demo/mission.py`:** stațiile, etapele, momentele, textele de pe LCD și de
  pe pagina web, sunetul fiecărei etape. Fișierul conține doar date.
- **Opțiuni din linia de comandă** (`python -m rocket_demo --help`): `--no-hold`,
  `--auto-stage`, `--time-scale 2`, `--no-web`, `--no-sound`, `--port 8080`,
  `--lcd-address 0x3F`.

## 7. Rulare pe laptop (fără Raspberry Pi)

Merge pe Windows, macOS și Linux, cu Python 3.10 sau mai nou (de pe python.org; pe
Windows bifează „Add python.exe to PATH”).

1. Descarcă proiectul: `git clone` sau, de pe GitHub, *Code → Download ZIP*.
2. Deschide un terminal în directorul proiectului. Pe Windows e PowerShell, iar
   comanda e `python` în loc de `python3`.
3. Rulează:

   ```bash
   python3 -m venv .venv
   # Windows:      .venv\Scripts\activate
   # macOS/Linux:  source .venv/bin/activate
   pip install -r requirements.txt
   python3 tools/make_placeholder_sounds.py
   python3 -m rocket_demo --sim
   ```

   Mediul virtual (`.venv`) e opțional. Dacă PowerShell refuză comanda `activate`,
   sari peste primele două linii.

Ce primești în modul `--sim`:

- **LCD-ul** este desenat în terminal.
- **Butoanele** sunt taste: `g`=GO, `l`=LAUNCH, `s`=STAGE, `a`=ABORT, `r`=RESET, `q`=ieșire.
- **Sunetul** iese prin difuzoarele laptopului.
- **Pagina web** se deschide la adresa afișată în terminal, de obicei
  http://127.0.0.1:8000/?control=1. Are și butoane pe ecran. Dacă portul 8000 e ocupat de
  alt program, demo-ul alege singur următorul port liber (8001, 8002…).
- **De pe telefon sau alt calculator** din aceeași rețea: `http://<IP-ul laptopului>:8000`.
  Pe Windows, permite accesul când întreabă firewall-ul.

Opțiuni utile la testare:

- `--time-scale 20` face zborul să dureze sub 30 de secunde.
- `--no-hold` scoate HOLD-urile aleatoare.

Modul `--sim` nu testează firele: LCD-ul I2C, butoanele GPIO și ieșirea audio a Pi-ului.
Pe acestea le verifici pe Pi, cu `--selftest`.

## 8. Depanare

| Problemă | Ce verifici |
|---|---|
| LCD-ul e aprins, dar nu apare text (sau apar pătrățele) | Rotește potențiometrul albastru de pe spatele LCD-ului (contrastul). |
| „nu am găsit LCD-ul” | Verifică firele SDA/SCL. `i2cdetect -y 1` trebuie să arate `27` sau `3f`. Dacă e altă adresă: `--lcd-address 0x..`. |
| Nu se aude nimic | Verifică alimentarea și volumul difuzorului. Rulează `speaker-test -c2 -t wav`; `aplay -l` arată plăcile audio. Alege ieșirea corectă din `raspi-config`: *Headphones* (Pi 3/4) sau placa USB (Pi 5). |
| Sunetul iese pe HDMI | Creează `~/.asoundrc` cu `defaults.pcm.card Headphones` și `defaults.ctl.card Headphones`, apoi repornește serviciul. Pe Pi 5, în loc de `Headphones` pune numele plăcii USB afișat de `aplay -l`. |
| Un buton nu reacționează | `--selftest` afișează fiecare apăsare. Verifică pinul și legătura la GND. |
| Pagina web nu se deschide | Pi-ul și calculatorul trebuie să fie în aceeași rețea. Încearcă IP-ul afișat pe LCD sau varianta hotspot. |
| Ce face aplicația? | `journalctl -u rocket-demo -f` |

## 9. Pentru dezvoltatori

```
rocket_demo/
  config.py       setări
  mission.py      conținutul misiunii (date)
  telemetry.py    interpolarea altitudinii și vitezei
  controller.py   automatul de stări + bucla principală
  hardware/       LCD (RPLCD), butoane (gpiozero), sunet (pygame) + variante simulate
  web/            server Flask + Server-Sent Events, pagina statică
tools/make_placeholder_sounds.py
systemd/rocket-demo.service, install.sh
tests/            pytest (ceas simulat, fără hardware)
```

Rularea testelor:

```bash
pip install -r requirements-dev.txt
python3 -m pytest
```
