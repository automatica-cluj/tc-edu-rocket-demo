# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

Educational Raspberry Pi demo (for 12–14 year olds) that walks through a rocket launch: GO/NO-GO checks → countdown → flight stages → orbit. Inputs are 4 physical GPIO buttons (GO, LAUNCH, STAGE, ABORT), outputs are a 16x2 I2C LCD, a speaker, and a live web page for the classroom projector.

**Language:** All user-facing text, comments, docstrings, log messages, README and `docs/ghid-profesor.md` are in **Romanian**. Keep new code consistent with that.

## Commands

```bash
pip install -r requirements-dev.txt          # flask, pygame, gpiozero, RPLCD, smbus2 + pytest
python3 tools/make_placeholder_sounds.py     # generates sounds/placeholder/*.wav (gitignored, stdlib only)
python3 -m rocket_demo --sim                 # run on a laptop: LCD drawn in terminal, keys g/l/s/a/r/q
python3 -m rocket_demo --sim --time-scale 20 --no-hold   # fast flight, no random HOLDs
python3 -m rocket_demo --keyboard            # real LCD/GPIO plus terminal keys (stop the user service first on the Pi)
python3 -m pytest                            # all tests (pytest.ini sets testpaths + pythonpath ". tests")
python3 -m pytest tests/test_controller.py::test_full_mission_with_stage_button
```

On the Pi: `./install.sh` (apt packages, I2C, venv with `--system-site-packages`, then installs `systemd/rocket-demo.service` as a **user** unit in `~/.config/systemd/user/` with `@APP_DIR@` substituted, plus `loginctl enable-linger` so it starts at boot; a user unit is what gives it access to PipeWire audio on Raspberry Pi OS with desktop, and still uses plain ALSA on Lite). Hardware check: `.venv/bin/python -m rocket_demo --selftest`; play a sound: `--play <key|all>`; manage with `systemctl --user stop|start|restart rocket-demo`; logs: `journalctl --user-unit rocket-demo -f`.

Optional HDMI kiosk (Pi 4/5, Lite or desktop): `kiosk/setup-kiosk.sh` installs `cage` + Chromium, enables console autologin and appends a marked block to `~/.profile` that `exec`s `kiosk/start-kiosk.sh` on tty1 (waits for `/api/state`, then runs Chromium full-screen on `/?kiosk=1`, which hides the cursor). `--remove` undoes it (back to desktop autologin if `lightdm` is installed, else console login).

## Architecture

- **`controller.py` — the core.** A single-threaded state machine (`State`: idle → checks ⇄ hold → ready → countdown → flight → orbit, plus scrub/abort end states). Button sources (GPIO callbacks, keyboard thread, web POSTs) only call `press()`, which enqueues; the main loop calls `tick()` ~10×/s, which drains the queue, advances time, renders the LCD and publishes a snapshot dict. Flight time is `real elapsed × cfg.time_scale`; events fire when `_flight_t` passes `FlightEvent.t`. An event with `needs_stage` pauses the flight clock until STAGE is pressed or `stage_window_s` expires (unless pre-armed within `stage_early_s`). Holding ABORT for `reset_hold_s` emits a `reset` button.
- **Snapshot / web sync.** `_publish()` bumps a version and `notify_all()`s a `threading.Condition` only when the snapshot changes. `web/server.py` (Flask in a background thread via werkzeug `make_server`) streams snapshots over SSE at `/events` using `wait_for_update(version)`; also `/api/state`, `/api/mission`, `POST /api/press/<button>` (403 if `web_control` is off). If the port is taken it tries the next 10 and writes the real port back into `cfg.web_port` (shown on the LCD). Frontend is plain static `web/static/{index.html,app.js,style.css}`; the page also maps keys G/L/S/A/R to `POST /api/press/*` when `web_control` is on.
- **`mission.py` is pure data**: checks, flight events, telemetry keypoints `(t, alt_km, vel_ms)`, per-state info texts, and the `SOUNDS` key registry. Content changes go here, not in the controller. LCD text limits: no diacritics; check `lcd` ≤ 13 chars, event `lcd` ≤ 9, `hold_lcd` ≤ 16.
- **`glyphs.py`**: LCD custom chars (`ROCKET = "\x00"`, `FLAME = "\x01"`), `lcd_safe()` (strip diacritics, pad/truncate to 16) and `to_ascii()` for terminal/web. Every rendered line goes through `lcd_safe`.
- **`hardware/`**: each device has a real implementation plus fallbacks (`I2cLcd`/`TerminalDisplay`/`LogDisplay`, `GpioButtons`/`KeyboardButtons`/`NoButtons`, `Audio`/`NoAudio`). Factories in `hardware/__init__.py` pick sim variants for `--sim` and degrade gracefully (log + fallback) when hardware is missing. Hardware libs (`gpiozero`, `RPLCD`, `pygame`) are imported lazily inside constructors so the package imports without them.
- **Sounds**: `find_sound` searches `sounds/` before `sounds/placeholder/`; user files override placeholders by key name; `cfg.sound_files` maps keys to custom filenames.
- **`config.py`**: `Config` dataclass with all tunables; `__main__.build_config` overrides fields from CLI flags.

## Tests

No hardware needed. `tests/conftest.py` provides `Harness`, which builds a `Controller` with a `FakeClock`, seeded RNG, `FakeAudio` (records `play`/`engine`/`stop` calls) and `FakeDisplay` (asserts every frame is exactly 16 printable ASCII chars). Drive it with `h.press(...)`, `h.run(seconds)`, `h.run_until(pred)`, `h.go_to_ready()`, `h.go_to_flight()`. `hold_probability` defaults to 0 in the harness; pass overrides as `Harness(hold_probability=1.0, ...)`. Web tests use Flask's `test_client` on `create_app(h.ctrl, h.cfg)`.
