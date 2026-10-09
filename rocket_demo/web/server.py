"""Serverul web: pagina cu animația și actualizări live (Server-Sent Events)."""

from __future__ import annotations

import hashlib
import json
import logging
import socket
import threading
from pathlib import Path

from flask import Flask, Response, abort, jsonify, send_from_directory
from werkzeug.serving import make_server

from ..config import Config
from ..controller import BUTTONS, Controller, clock_text
from ..mission import Mission
from ..parts_data import PARTS

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
        "button_layout": dict(cfg.button_layout),
        "parts": [{"key": p.key, "label": p.label} for p in PARTS],
    }


def build_id(info: dict) -> str:
    """Amprenta paginii (fișiere statice + misiune); se schimbă la fiecare actualizare."""
    digest = hashlib.sha1(json.dumps(info, sort_keys=True).encode())
    for path in sorted(STATIC_DIR.iterdir()):
        if path.is_file():
            digest.update(path.read_bytes())
    return digest.hexdigest()[:12]


def create_app(controller: Controller, cfg: Config) -> Flask:
    app = Flask(__name__, static_folder=str(STATIC_DIR), static_url_path="/static")
    info = mission_info(controller.mission, cfg)
    build = build_id(info)

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
            # pagina se reîncarcă singură dacă serverul a pornit cu altă versiune
            yield f"event: hello\ndata: {build}\n\n"
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


PORT_ATTEMPTS = 10


def port_in_use(port: int) -> bool:
    """True dacă alt program răspunde deja pe acest port (IPv4 sau IPv6)."""
    for host in ("127.0.0.1", "::1"):
        try:
            with socket.create_connection((host, port), timeout=0.3):
                return True
        except OSError:
            continue
    return False


class WebServer:
    """Rulează serverul Flask într-un thread separat de bucla principală.

    Dacă portul ales e ocupat de alt program, încearcă următoarele porturi și
    actualizează `cfg.web_port` (LCD-ul afișează portul real).
    """

    def __init__(self, controller: Controller, cfg: Config):
        logging.getLogger("werkzeug").setLevel(logging.WARNING)
        app = create_app(controller, cfg)
        wanted = cfg.web_port
        for port in range(wanted, wanted + PORT_ATTEMPTS):
            if port_in_use(port):
                continue
            try:
                self._server = make_server(cfg.web_host, port, app, threaded=True)
            except OSError:
                continue
            break
        else:
            raise OSError(f"porturile {wanted}-{wanted + PORT_ATTEMPTS - 1} sunt ocupate")
        if port != wanted:
            log.warning("portul %d e ocupat de alt program; folosesc portul %d", wanted, port)
        cfg.web_port = port
        self.port = port
        self._thread = threading.Thread(
            target=self._server.serve_forever, name="web", daemon=True
        )

    def start(self) -> None:
        self._thread.start()
        log.info("pagina web: http://%s:%d", *self._server.server_address[:2])

    def stop(self) -> None:
        self._server.shutdown()
