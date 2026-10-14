from rocket_demo.mission import CHECKS, EVENTS, SOUNDS, STATE_INFO, TELEMETRY
from rocket_demo.telemetry import Telemetry, format_lcd, interpolate


def test_lcd_texts_fit_and_are_ascii():
    for check in CHECKS:
        assert check.lcd.isascii() and len(check.lcd) <= 13
        assert check.hold_lcd.isascii() and len(check.hold_lcd) <= 16
    for ev in EVENTS:
        assert ev.lcd.isascii() and len(ev.lcd) <= 9, ev.lcd


def test_events_are_ordered_and_sounds_exist():
    times = [ev.t for ev in EVENTS]
    assert times == sorted(times)
    assert EVENTS[0].t == 0
    assert TELEMETRY[-1][0] == EVENTS[-1].t
    for ev in EVENTS:
        assert ev.sound is None or ev.sound in SOUNDS
    assert sum(ev.needs_stage for ev in EVENTS) == 1


def test_state_info_present():
    for state in ("idle", "ready", "countdown", "scrub", "abort", "orbit"):
        assert STATE_INFO[state].title


def test_interpolation():
    pts = ((0, 0.0, 0), (10, 10.0, 100))
    assert interpolate(pts, -5) == Telemetry(0.0, 0)
    assert interpolate(pts, 5) == Telemetry(5.0, 50)
    assert interpolate(pts, 50) == Telemetry(10.0, 100)


def test_telemetry_grows_monotonically():
    prev = interpolate(TELEMETRY, 0)
    for t in range(1, 511):
        cur = interpolate(TELEMETRY, t)
        assert cur.alt_km >= prev.alt_km
        prev = cur


def test_format_lcd_fits():
    for t in range(0, 511):
        assert len(format_lcd(interpolate(TELEMETRY, t))) <= 16
    assert format_lcd(Telemetry(200, 7800)) == "200km 28080km/h"
    assert format_lcd(Telemetry(12.34, 450)) == "12.3km 1620km/h"


def test_voice_texts_files_are_up_to_date():
    import sys
    from pathlib import Path

    root = Path(__file__).resolve().parent.parent
    sys.path.insert(0, str(root / "tools"))
    import make_voice_texts

    for lang in ("en", "ro"):
        current = (root / "sounds" / "voce" / lang / "TEXTE.md").read_text(encoding="utf-8")
        expected = make_voice_texts.render(lang)
        assert current == expected, "rulează: python3 tools/make_voice_texts.py"
        for text in expected.split("\n## ")[1:]:
            assert "~" not in text and "«" not in text, text


def test_english_voice_covers_every_explanation():
    from rocket_demo.mission import voice_texts
    from rocket_demo.mission_en import VOICE_EN

    assert set(VOICE_EN) == set(voice_texts())
    for text in VOICE_EN.values():
        assert text.isascii() and "~" not in text, text
