import io
import wave

import pytest

from rocket_demo.hardware.audio import find_sound
from rocket_demo.hardware.lcd import TerminalDisplay


def test_find_sound_prefers_user_dir(tmp_path):
    user, placeholder = tmp_path / "user", tmp_path / "ph"
    user.mkdir()
    placeholder.mkdir()
    (placeholder / "liftoff.wav").write_bytes(b"x")
    assert find_sound([user, placeholder], "liftoff") == placeholder / "liftoff.wav"
    (user / "liftoff.ogg").write_bytes(b"x")
    assert find_sound([user, placeholder], "liftoff") == user / "liftoff.ogg"
    (user / "my file.mp3").write_bytes(b"x")
    assert find_sound([user, placeholder], "my file.mp3") == user / "my file.mp3"
    assert find_sound([user, placeholder], "missing") is None


def test_terminal_display_draws_box():
    out = io.StringIO()
    display = TerminalDisplay(out)
    display.show("\x00 MISIUNE", "Apasa GO")
    display.show("\x00 MISIUNE", "Apasa GO")  # identic: nu redesenează
    text = out.getvalue()
    assert text.count("+----------------+") == 2
    assert "|^ MISIUNE       |" in text


def test_gpio_buttons_with_mock_pins():
    gpiozero = pytest.importorskip("gpiozero")
    from gpiozero.pins.mock import MockFactory

    from rocket_demo.hardware.buttons import GpioButtons

    gpiozero.Device.pin_factory = MockFactory()
    pressed = []
    buttons = GpioButtons({"go": 5, "abort": 19}, pressed.append, reset_hold_s=0.05)
    try:
        pin = gpiozero.Device.pin_factory.pin(5)
        pin.drive_low()
        pin.drive_high()
        abort_pin = gpiozero.Device.pin_factory.pin(19)
        abort_pin.drive_low()
        import time

        time.sleep(0.3)
        abort_pin.drive_high()
        time.sleep(0.05)
    finally:
        buttons.close()
        gpiozero.Device.pin_factory.reset()
    assert pressed[:3] == ["go", "abort", "reset"]


def test_placeholder_generator(tmp_path):
    import sys
    from pathlib import Path

    sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))
    import make_placeholder_sounds as gen

    from rocket_demo.mission import SOUNDS

    assert set(gen.SOUNDS) == set(SOUNDS)
    gen.main(["--out", str(tmp_path)])
    with wave.open(str(tmp_path / "countdown.wav")) as w:
        assert w.getframerate() == gen.RATE
        assert 9.9 < w.getnframes() / w.getframerate() < 10.1
