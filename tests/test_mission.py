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
