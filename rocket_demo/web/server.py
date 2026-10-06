"""Serverul web: pagina cu animația și actualizări live (Server-Sent Events)."""

from __future__ import annotations

import json
import logging
import threading
from pathlib import Path

from flask import Flask, Response, abort, jsonify, send_from_directory
from werkzeug.serving import make_server

from ..config import Config
from ..controller import BUTTONS, Controller, clock_text
from ..mission import Mission

log = logging.getLogger(__name__)

STATIC_DIR = Path(__file__).resolve().parent / "static"
KEEPALIVE_S = 15.0


def mission_info(mission: Mission, cfg: Config) -> dict:
    last = mission.telemetry[-1]
    return {
        "name": cfg.mission_name,
        "checks": [c.name for c in mission.checks],
        "events": [
            {"key": ev.key, "t": ev.t, "clock": clock_text(ev.t), "title": ev.title}
            for ev in mission.events
        ],
        "max_alt_km": last[1],
        "max_vel_kmh": round(last[2] * 3.6),
    }


def create_app(controller: Controller, cfg: Config) -> Flask:
    app = Flask(__name__, static_folder=str(STATIC_DIR), static_url_path="/static")
    info = mission_info(controller.mission, cfg)

    @app.get("/")
    def index():
        return send_from_directory(STATIC_DIR, "index.html")

    @app.get("/api/mission")
    def api_mission():
        return jsonify(info)

    @app.get("/api/state")
    def api_state():
        return jsonify(controller.snapshot())

    @app.post("/api/press/<button>")
    def api_press(button: str):
        if not cfg.web_control:
            abort(403)
        if button not in BUTTONS:
            abort(404)
        controller.press(button)
        return jsonify({"ok": True})

    @app.get("/events")
    def events():
        def stream():
            yield "retry: 2000\n\n"
            version = None
            while True:
                snap = controller.wait_for_update(version, timeout=KEEPALIVE_S)
                if snap.get("version") == version:
                    yield ": ping\n\n"
                    continue
                version = snap.get("version")
                yield f"data: {json.dumps(snap, ensure_ascii=False)}\n\n"

        return Response(
            stream(),
            mimetype="text/event-stream",
            headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
        )

    return app


class WebServer:
    """Rulează serverul Flask într-un thread separat de bucla principală."""

    def __init__(self, controller: Controller, cfg: Config):
        logging.getLogger("werkzeug").setLevel(logging.WARNING)
        self._server = make_server(
            cfg.web_host, cfg.web_port, create_app(controller, cfg), threaded=True
        )
        self._thread = threading.Thread(
            target=self._server.serve_forever, name="web", daemon=True
        )

    def start(self) -> None:
        self._thread.start()
        log.info("pagina web: http://%s:%d", *self._server.server_address[:2])

    def stop(self) -> None:
        self._server.shutdown()
