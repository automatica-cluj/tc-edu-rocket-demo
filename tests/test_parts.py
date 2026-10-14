from pathlib import Path

import pytest
from conftest import Harness

from rocket_demo.config import Config
from rocket_demo.parts import PartsTour
from rocket_demo.parts_data import PARTS

INDEX_HTML = Path(__file__).resolve().parent.parent / "rocket_demo" / "web" / "static" / "index.html"


def test_parts_data_is_valid_and_drawn():
    keys = [p.key for p in PARTS]
    assert len(keys) == len(set(keys))
    html = INDEX_HTML.read_text(encoding="utf-8")
    for p in PARTS:
        assert p.lcd.isascii() and len(p.lcd) <= 16, p.lcd
        assert p.label and p.name and p.text
        assert f'data-part="{p.key}"' in html, p.key  # fiecare piesă are un desen


def test_tour_navigation_wraps_and_abort_exits():
    t = PartsTour(Config(), 0.0)
    assert t.part.key == "les"  # începe de la vârful rachetei
    t.press("stage", 1.0)
    assert t.index == len(PARTS) - 1  # înapoi de la prima piesă = ultima
    t.press("go", 2.0)
    t.press("go", 3.0)
    assert t.index == 1
    t.press("launch", 4.0)  # LAUNCH nu schimbă piesa
    assert t.index == 1 and not t.exited
    t.press("abort", 5.0)
    assert t.exited


def test_tour_advances_by_itself_and_closes_when_idle():
    cfg = Config(parts_step_s=8.0, parts_idle_timeout_s=120.0)
    t = PartsTour(cfg, 0.0)
    t.update(7.9)
    assert t.index == 0
    t.update(8.0)
    assert t.index == 1
    t.press("go", 10.0)  # o apăsare repornește numărătoarea pentru trecerea automată
    t.update(17.9)
    assert t.index == 2
    t.update(129.9)
    assert not t.exited
    t.update(130.0)
    assert t.exited


def test_lcd_shows_number_and_name():
    t = PartsTour(Config(), 0.0)
    assert t.lcd(0.0) == (f"PIESA  1/{len(PARTS)}", "TURN SALVARE")


def test_long_launch_opens_parts_from_idle_and_abort_returns(h):
    h.press("parts")
    assert h.state == "parts"
    snap = h.ctrl.snapshot()
    assert snap["parts"]["key"] == "les"
    assert h.display.last == (f"PIESA  1/{len(PARTS)}".ljust(16), "TURN SALVARE".ljust(16))
    h.press("go")
    assert h.ctrl.snapshot()["parts"]["index"] == 2
    h.press("abort")
    assert h.state == "idle"
    assert h.ctrl.snapshot()["parts"] is None
    assert h.ctrl.snapshot()["voice_on"] is True  # ABORT a ieșit, nu a oprit vocea


def test_parts_from_end_screen_and_no_voice():
    h = Harness(interactive_stage=False)
    h.go_to_flight()
    h.run_until(lambda: h.state == "orbit")
    h.press("parts")
    assert h.state == "parts"
    assert h.audio.voiced[-1] is None  # vocea tace pe ecranul cu piese


def test_long_launch_when_ready_still_launches(h):
    h.go_to_ready()
    h.press("parts")
    assert h.state == "countdown"


def test_parts_closes_itself_when_nobody_presses():
    h = Harness(parts_idle_timeout_s=30.0)
    h.press("parts")
    h.run(31)
    assert h.state == "idle"


def test_gpio_launch_short_press_and_hold():
    gpiozero = pytest.importorskip("gpiozero")
    import time

    from gpiozero.pins.mock import MockFactory

    from rocket_demo.hardware.buttons import GpioButtons

    gpiozero.Device.pin_factory = MockFactory()
    pressed = []
    buttons = GpioButtons({"launch": 6}, pressed.append, launch_hold_s=0.2)
    try:
        pin = gpiozero.Device.pin_factory.pin(6)
        pin.drive_low()
        time.sleep(0.05)
        pin.drive_high()
        time.sleep(0.05)
        assert pressed == ["launch"]

        pin.drive_low()
        time.sleep(0.5)
        pin.drive_high()
        time.sleep(0.05)
        assert pressed == ["launch", "parts"]  # ținut: doar ecranul cu piese, fără LAUNCH
    finally:
        buttons.close()
        gpiozero.Device.pin_factory.reset()
