"""Setările demo-ului.

Modifică valorile de aici ca să se potrivească hardware-ului tău și clasei.
Cele mai multe se pot schimba și din linia de comandă (vezi `python -m rocket_demo --help`).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent.parent
VOICE_LANGUAGES = ("en", "ro")


@dataclass
class Config:
    # Numele misiunii, afișat pe LCD (max. 14 caractere, fără diacritice) și pe pagina web.
    mission_name: str = "AURORA"

    # --- LCD 16x2 cu adaptor I2C (PCF8574) ---
    # None = detectare automată (încearcă 0x27, apoi 0x3F).
    lcd_address: int | None = None
    lcd_port: int = 1

    # --- Butoane (numerotare BCM: GPIO5, GPIO6...), legate între pin și GND ---
    button_pins: dict[str, int] = field(
        default_factory=lambda: {"go": 5, "launch": 6, "stage": 13, "abort": 19}
    )
    # Câte secunde ții apăsat ABORT ca să resetezi demo-ul.
    reset_hold_s: float = 3.0

    # --- Timpi ---
    # Pauză la pornire (nu în --sim), ca sistemul să apuce să pornească și boxa Bluetooth
    # să se conecteze înainte de primul sunet. 0 = fără pauză.
    start_delay_s: float = 5.0
    # De câte ori e accelerat zborul (4 = zborul de 8,5 minute durează ~2 minute).
    time_scale: float = 4.0
    countdown_s: int = 10
    ignition_at_s: int = 3  # motoarele pornesc la T-3
    # Probabilitatea ca una dintre stații să ceară HOLD (0 = niciodată).
    hold_probability: float = 0.3
    hold_s: float = 6.0
    # True = elevii trebuie să apese STAGE pentru separarea treptelor.
    interactive_stage: bool = True
    # Câte secunde (reale) așteptăm apăsarea STAGE înainte de separarea automată.
    stage_window_s: float = 8.0
    # Cu câte secunde de misiune înainte de separare e acceptată apăsarea STAGE.
    stage_early_s: float = 5.0
    # După câte secunde ecranele finale (orbită / abort / scrub) revin la început.
    end_screen_timeout_s: float = 180.0

    # --- Sunete ---
    # Fișierele tale din `sounds/` au prioritate față de cele provizorii din `sounds/placeholder/`.
    sounds_dir: Path = PROJECT_DIR / "sounds"
    placeholder_dir: Path = PROJECT_DIR / "sounds" / "placeholder"
    # Nume de fișier diferite de cele standard, de ex. {"liftoff": "decolare_nasa.mp3"}.
    sound_files: dict[str, str] = field(default_factory=dict)
    sound_volume: float = 1.0

    # --- Vocea care citește explicațiile (vezi `sounds/voce/<limbă>/TEXTE.md`) ---
    voice_enabled: bool = True
    # "en" sau "ro". Doar vocea își schimbă limba; textele de pe ecran rămân în română.
    voice_language: str = "ro"
    voice_root: Path = PROJECT_DIR / "sounds" / "voce"
    # True = zborul și HOLD-ul așteaptă să se termine explicația înainte de etapa următoare.
    voice_wait: bool = True
    # Volumul motorului și al celorlalte efecte cât vorbește vocea (1 = nu le reduce).
    voice_duck: float = 0.3

    # --- Pagina web ---
    web_enabled: bool = True
    web_host: str = "0.0.0.0"
    web_port: int = 8000
    # Permite butoanele virtuale de pe pagină (http://.../?control=1).
    web_control: bool = True

    def voice_dirs(self) -> list[Path]:
        """Fișierele tale din `sounds/voce/<limbă>/` au prioritate față de ciornele din `ciorna/`."""
        base = self.voice_root / self.voice_language
        return [base, base / "ciorna"]
