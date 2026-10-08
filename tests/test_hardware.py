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


def test_keyboard_buttons_map_keys():
    import time

    from rocket_demo.hardware.buttons import KeyboardButtons

    pressed = []
    buttons = KeyboardButtons(pressed.append, stream=io.StringIO("gLsxaRq"))
    for _ in range(50):
        if len(pressed) == 6:
            break
        time.sleep(0.01)
    buttons.close()
    assert pressed == ["go", "launch", "stage", "abort", "reset", "quit"]


def test_audio_reopens_when_default_output_changes(tmp_path, monkeypatch):
    pytest.importorskip("pygame")
    monkeypatch.setenv("SDL_AUDIODRIVER", "dummy")
    import sys
    from pathlib import Path

    sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))
    import make_placeholder_sounds as gen

    from rocket_demo.hardware import audio as audio_mod

    gen.main(["--out", str(tmp_path)])
    sink = {"name": "alsa_output.hdmi"}
    monkeypatch.setattr(audio_mod, "default_sink", lambda: sink["name"])

    audio = audio_mod.Audio([tmp_path], ["go_beep", "engine_loop"], watch_s=None)
    try:
        audio._sink = "alsa_output.hdmi"
        audio.engine(True)
        audio.check_output()  # nicio schimbare
        assert audio.reopen_count == 0

        sink["name"] = "bluez_output.12_34_56_78_9A_BC.1"  # s-a conectat boxa Bluetooth
        audio.check_output()
        assert audio.reopen_count == 1
        assert audio._sink == sink["name"]
        assert audio._engine_channel.get_busy()  # motorul continuă după redeschidere
        audio.play("go_beep")

        sink["name"] = None  # PipeWire nu răspunde: nu schimbăm nimic
        audio.check_output()
        assert audio.reopen_count == 1
    finally:
        audio.close()


def test_audio_retries_when_unavailable_at_boot(tmp_path, monkeypatch):
    pytest.importorskip("pygame")
    from rocket_demo.hardware import audio as audio_mod

    monkeypatch.setattr(audio_mod.shutil, "which", lambda name: "/usr/bin/wpctl")
    monkeypatch.setattr(audio_mod, "default_sink", lambda: None)
    monkeypatch.setenv("SDL_AUDIODRIVER", "nu_exista")  # la boot sunetul nu e gata

    audio = audio_mod.Audio([tmp_path], ["go_beep"], watch_s=3600)
    try:
        assert not audio._ready
        audio.play("go_beep")  # nu trebuie să dea eroare
        monkeypatch.setenv("SDL_AUDIODRIVER", "dummy")  # acum sunetul e disponibil
        audio.check_output()
        assert audio._ready
        assert audio.reopen_count == 1
    finally:
        audio.close()
