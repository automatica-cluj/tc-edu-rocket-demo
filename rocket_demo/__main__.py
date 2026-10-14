"""Pornirea demo-ului:  python -m rocket_demo [opțiuni]"""

from __future__ import annotations

import argparse
import ipaddress
import logging
import queue
import signal
import socket
import subprocess
import sys
import threading
import time

from .config import VOICE_LANGUAGES, Config
from .controller import Controller
from .glyphs import ROCKET, lcd_safe
from .hardware import make_audio, make_buttons, make_display
from .hardware.buttons import KeyboardButtons
from .mission import SOUNDS, voice_texts

log = logging.getLogger("rocket_demo")


def local_ip() -> str | None:
    """Adresa IP a Pi-ului în rețea, ca elevii/profesorul să deschidă pagina web."""
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        try:
            s.connect(("10.254.254.254", 1))  # nu trimite nimic, doar alege interfața
            ip = s.getsockname()[0]
            if not ip.startswith("127."):
                return ip
        except OSError:
            pass
    try:
        out = subprocess.run(["hostname", "-I"], capture_output=True, text=True, timeout=2)
        ip = (out.stdout.split() or [""])[0]
        ipaddress.ip_address(ip)
        return ip
    except (OSError, subprocess.SubprocessError, ValueError):
        return None


def parse_args(argv):
    p = argparse.ArgumentParser(prog="rocket_demo", description="Demo: lansarea unei rachete")
    p.add_argument("--sim", action="store_true", help="fără hardware: LCD în terminal, taste în loc de butoane")
    p.add_argument("--keyboard", action="store_true", help="pe Pi: tastele din terminal merg pe lângă butoanele reale")
    p.add_argument("--selftest", action="store_true", help="testează LCD-ul, sunetul și butoanele")
    p.add_argument(
        "--play",
        metavar="SUNET",
        help="redă un sunet sau o explicație (sau 'all' / 'voce' pentru toate) și iese",
    )
    p.add_argument("--no-sound", action="store_true", help="fără sunet")
    p.add_argument("--no-voice", action="store_true", help="fără vocea care citește explicațiile")
    p.add_argument("--voice-lang", choices=VOICE_LANGUAGES, help="limba vocii (implicit ro)")
    p.add_argument("--no-web", action="store_true", help="fără pagina web")
    p.add_argument("--no-web-control", action="store_true", help="fără butoane virtuale pe pagina web")
    p.add_argument("--port", type=int, help="portul paginii web (implicit 8000)")
    p.add_argument("--lcd-address", type=lambda s: int(s, 0), help="adresa I2C a LCD-ului, de ex. 0x27")
    p.add_argument("--time-scale", type=float, help="accelerarea zborului (implicit 4)")
    p.add_argument("--start-delay", type=float, metavar="SEC", help="pauza la pornire (implicit 5 s; 0 = fără)")
    p.add_argument("--no-hold", action="store_true", help="fără HOLD-uri aleatoare la verificări")
    p.add_argument("--auto-stage", action="store_true", help="separarea treptelor fără butonul STAGE")
    p.add_argument("-v", "--verbose", action="store_true", help="mesaje detaliate")
    return p.parse_args(argv)


def build_config(args) -> Config:
    cfg = Config()
    if args.no_web:
        cfg.web_enabled = False
    if args.no_web_control:
        cfg.web_control = False
    if args.port:
        cfg.web_port = args.port
    if args.lcd_address is not None:
        cfg.lcd_address = args.lcd_address
    if args.time_scale:
        cfg.time_scale = args.time_scale
    if args.start_delay is not None:
        cfg.start_delay_s = args.start_delay
    if args.no_hold:
        cfg.hold_probability = 0.0
    if args.auto_stage:
        cfg.interactive_stage = False
    if args.no_voice:
        cfg.voice_enabled = False
    if args.voice_lang:
        cfg.voice_language = args.voice_lang
    return cfg


def play_sounds(cfg: Config, which: str) -> int:
    audio = make_audio(cfg)
    voices = voice_texts()
    keys = list(SOUNDS) if which == "all" else list(voices) if which == "voce" else [which]
    for key in keys:
        if key not in SOUNDS and key not in voices:
            print(f"sunet necunoscut: {key}. Sunete: {', '.join(SOUNDS)}")
            print(f"Explicații: {', '.join(voices)}")
            return 2
        if key in SOUNDS:
            path = audio.paths.get(key)
            print(f"{key:20} {path or 'LIPSĂ'}", flush=True)
            if path:
                audio.play(key)
                time.sleep(min(audio.length(key), 6.0) + 0.3)
        else:
            path = audio.voice_paths.get(key)
            print(f"{key:20} {path or 'LIPSĂ'}", flush=True)
            if path:
                audio.voice(key)
                time.sleep(audio.length(key) + 0.3)
        audio.stop_all()
    audio.close()
    return 0


def selftest(cfg: Config, sim: bool) -> int:
    print("== Test hardware ==")
    display = make_display(cfg, sim)
    display.show("TEST LCD  " + ROCKET, "Apasa butoanele")
    print(f"LCD: {type(display).__name__}")

    audio = make_audio(cfg)
    print(f"Sunete găsite: {len(audio.sounds)}/{len(SOUNDS)}")
    for key in SOUNDS:
        print(f"  {key:16} {audio.paths.get(key, 'LIPSĂ')}")
    print(f"Explicații citite ({cfg.voice_language}): {len(audio.voices)}/{len(voice_texts())}")
    audio.play("all_go")

    presses: queue.Queue[str] = queue.Queue()
    buttons = make_buttons(cfg, sim, presses.put)
    if sim:
        print(KeyboardButtons.HELP)
    print("Apasă fiecare buton (ține ABORT 3 s pentru RESET). Ctrl+C pentru ieșire.")
    try:
        while True:
            try:
                name = presses.get(timeout=0.5)
            except queue.Empty:
                continue
            if name == "quit":
                break
            print(f"buton: {name.upper()}")
            display.show("Buton apasat:", name.upper())
            audio.play("go_beep")
    except KeyboardInterrupt:
        pass
    finally:
        buttons.close()
        audio.close()
        display.close()
    return 0


def main(argv=None) -> int:
    args = parse_args(argv)
    level = logging.DEBUG if args.verbose else logging.WARNING if args.sim else logging.INFO
    logging.basicConfig(level=level, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    cfg = build_config(args)

    if args.play:
        return play_sounds(cfg, args.play)
    if args.selftest:
        return selftest(cfg, args.sim)

    stop = threading.Event()
    signal.signal(signal.SIGTERM, lambda *_: stop.set())
    display = make_display(cfg, args.sim)
    if cfg.start_delay_s > 0 and not args.sim:
        # Sunetul se deschide după pauză, pe ieșirea implicită de atunci (de ex. boxa BT).
        log.info("aștept %.0f s la pornire (boxa Bluetooth se conectează)", cfg.start_delay_s)
        display.show(lcd_safe(f"{ROCKET} Pornire..."), lcd_safe("Asteptam boxa"))
        if stop.wait(cfg.start_delay_s):
            display.close()
            return 0
    audio = make_audio(cfg, enabled=not args.no_sound)
    controller = Controller(cfg, display, audio, ip_provider=local_ip)

    def on_press(name: str) -> None:
        if name == "quit":
            stop.set()
        else:
            controller.press(name)

    buttons = make_buttons(cfg, args.sim, on_press)
    keyboard = KeyboardButtons(on_press) if args.keyboard and not args.sim else None
    web = None
    if cfg.web_enabled:
        try:
            from .web.server import WebServer

            web = WebServer(controller, cfg)
            web.start()
            if args.sim:
                print(f"Pagina web: http://127.0.0.1:{web.port}/?control=1")
        except Exception as exc:  # noqa: BLE001
            log.error("pagina web nu a pornit (%s)", exc)
            web = None
    if args.sim or keyboard:
        print(KeyboardButtons.HELP)

    try:
        controller.run(stop)
    except KeyboardInterrupt:
        pass
    finally:
        buttons.close()
        if keyboard:
            keyboard.close()
        if web:
            web.stop()
        audio.close()
        display.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
