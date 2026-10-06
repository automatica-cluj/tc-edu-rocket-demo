from conftest import Harness

from rocket_demo.mission import EVENTS


def test_idle_screen_alternates_with_web_address(h):
    assert h.state == "idle"
    assert h.display.last[1].strip() == "Apasa GO >>"
    h.run(3.1)
    assert h.display.last == ("Web: port 8000".ljust(16), "192.168.1.42".ljust(16))


def test_checks_need_go_from_every_station(h):
    h.press("go")
    assert h.state == "checks"
    assert h.display.last[0] == "METEO........GO?"
    for i in range(len(h.ctrl.mission.checks) - 1):
        h.press("go")
        assert h.state == "checks"
        assert h.ctrl.snapshot()["checks"][: i + 1] == ["go"] * (i + 1)
    h.press("go")
    assert h.state == "ready"
    assert h.audio.played[-1] == "all_go"


def test_launch_before_checks_is_refused(h):
    h.press("go", "launch")
    assert h.state == "checks"
    assert h.display.last[1].strip() == "Mai intai GO!"


def test_hold_pauses_checks_then_resumes():
    h = Harness(hold_probability=1.0, hold_s=5)
    h.press("go")
    station = h.ctrl._hold_station
    h.press(*["go"] * station)
    h.press("go")
    assert h.state == "hold"
    assert h.audio.played[-1] == "hold"
    assert h.ctrl.snapshot()["checks"][station] == "hold"
    h.press("go")  # ignorat în HOLD
    assert h.state == "hold"
    h.run(5.1)
    assert h.state == "checks"
    h.press(*["go"] * (len(h.ctrl.mission.checks) - station))
    assert h.state == "ready"


def test_full_mission_with_stage_button(h):
    h.go_to_ready()
    h.press("launch")
    assert h.state == "countdown"
    assert h.audio.played[-1] == "countdown"
    assert h.display.last[0].strip().endswith("T-0:10")
    h.run(7.1)
    assert "ignition" in h.audio.played
    assert ("engine", True) in h.audio.calls
    assert h.display.last[1].strip() == "Aprindere motor"
    h.run(3.0)
    assert h.state == "flight"
    assert h.ctrl.snapshot()["fired"] == ["liftoff"]

    h.run_until(lambda: h.ctrl.snapshot()["awaiting_stage"])
    snap = h.ctrl.snapshot()
    assert snap["fired"][-1] == "meco"
    assert snap["clock"] == "T+2:33"
    assert h.audio.played[-1] == "stage_prompt"
    # ceasul misiunii stă pe loc cât așteptăm butonul STAGE
    h.run(2)
    assert h.ctrl.snapshot()["clock"] == "T+2:33"

    h.press("stage")
    assert h.ctrl.snapshot()["fired"][-1] == "separation"
    assert h.display.last[1].strip() == "Bravo! Separare"

    h.run_until(lambda: h.state == "orbit")
    snap = h.ctrl.snapshot()
    assert snap["fired"] == [ev.key for ev in EVENTS]
    assert snap["alt_km"] == 200
    assert snap["vel_kmh"] == 28080
    assert h.audio.played[-1] == "orbit"
    assert h.audio.calls[-1] == ("engine", False)
    assert h.display.last[0].strip() == "ORBITA ATINSA!"


def test_flight_duration_is_scaled(h):
    h.go_to_flight()
    start = h.clock.t
    h.run_until(lambda: h.ctrl.snapshot()["awaiting_stage"])
    h.press("stage")
    h.run_until(lambda: h.state == "orbit")
    assert 125 <= h.clock.t - start <= 130  # 510 s de misiune / 4


def test_stage_separates_automatically_after_window(h):
    h.go_to_flight()
    h.run_until(lambda: h.ctrl.snapshot()["awaiting_stage"])
    h.run(h.cfg.stage_window_s + 0.1)
    assert h.ctrl.snapshot()["fired"][-1] == "separation"
    assert h.display.last[1].strip() == "Separare auto"


def test_stage_too_early(h):
    h.go_to_flight()
    h.run(5)
    h.press("stage")
    assert h.display.last[1].strip() == "Prea devreme!"
    assert "separation" not in h.ctrl.snapshot()["fired"]


def test_stage_pressed_just_before_separation_does_not_wait(h):
    h.go_to_flight()
    h.run_until(lambda: "meco" in h.ctrl.snapshot()["fired"])
    h.press("stage")
    h.run(1)
    snap = h.ctrl.snapshot()
    assert not snap["awaiting_stage"]
    assert "separation" in snap["fired"]


def test_non_interactive_stage():
    h = Harness(interactive_stage=False)
    h.go_to_flight()
    h.run_until(lambda: h.state == "orbit")
    assert "stage_prompt" not in h.audio.played


def test_abort_during_countdown_scrubs(h):
    h.go_to_ready()
    h.press("launch")
    h.run(2)
    h.press("abort")
    assert h.state == "scrub"
    assert h.audio.calls[-2:] == [("stop",), ("play", "scrub")]
    h.press("go")
    assert h.state == "checks"


def test_abort_in_flight_freezes_telemetry(h):
    h.go_to_flight()
    h.run(20)
    h.press("abort")
    assert h.state == "abort"
    assert h.audio.played[-1] == "abort_alarm"
    assert h.display.last[0].strip() == "!!! ABORT !!!"
    snap = h.ctrl.snapshot()
    h.run(5)
    assert h.ctrl.snapshot()["alt_km"] == snap["alt_km"] > 0
    assert not h.ctrl.snapshot()["engine_on"]
    assert h.display.last[0].strip() == "Echipaj in sigur"


def test_reset_from_anywhere(h):
    h.go_to_flight()
    h.run(10)
    h.press("reset")
    assert h.state == "idle"
    assert ("stop",) in h.audio.calls
    snap = h.ctrl.snapshot()
    assert snap["fired"] == [] and snap["alt_km"] == 0


def test_end_screen_times_out_to_idle():
    h = Harness(end_screen_timeout_s=10)
    h.go_to_ready()
    h.press("abort")
    assert h.state == "scrub"
    h.run(10.1)
    assert h.state == "idle"


def test_snapshot_version_changes_and_wait_returns(h):
    v = h.ctrl.snapshot()["version"]
    assert h.ctrl.wait_for_update(v, timeout=0.01)["version"] == v
    h.press("go")
    assert h.ctrl.wait_for_update(v, timeout=0.01)["version"] > v


def test_unknown_button_rejected(h):
    try:
        h.ctrl.press("selfdestruct")
    except ValueError:
        pass
    else:
        raise AssertionError("trebuia să dea eroare")
