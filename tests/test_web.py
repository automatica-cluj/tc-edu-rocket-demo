import json

import pytest

pytest.importorskip("flask")

from conftest import Harness  # noqa: E402

from rocket_demo.web.server import create_app  # noqa: E402


@pytest.fixture
def web():
    h = Harness()
    app = create_app(h.ctrl, h.cfg)
    return h, app.test_client()


def test_index_and_static(web):
    _, client = web
    page = client.get("/")
    assert page.status_code == 200
    assert b"/static/app.js" in page.data
    for asset in ("app.js", "style.css"):
        assert client.get(f"/static/{asset}").status_code == 200


def test_mission_info(web):
    _, client = web
    info = client.get("/api/mission").get_json()
    assert info["name"] == "AURORA"
    assert len(info["checks"]) == 5
    assert info["events"][0] == {"key": "liftoff", "t": 0, "clock": "T+0:00", "title": "Decolare!"}
    assert info["max_vel_kmh"] == 28080


def test_press_updates_state(web):
    h, client = web
    assert client.get("/api/state").get_json()["state"] == "idle"
    assert client.post("/api/press/go").status_code == 200
    h.ctrl.tick()
    snap = client.get("/api/state").get_json()
    assert snap["state"] == "checks"
    assert snap["checks"][0] == "current"
    assert snap["lcd"][0] == "METEO........GO?"


def test_press_rejects_unknown_and_respects_flag(web):
    h, client = web
    assert client.post("/api/press/selfdestruct").status_code == 404
    assert client.get("/api/press/go").status_code == 405
    h.cfg.web_control = False
    assert client.post("/api/press/go").status_code == 403


def test_event_stream_sends_snapshot(web):
    h, client = web
    resp = client.get("/events", buffered=False)
    assert resp.mimetype == "text/event-stream"
    chunks = iter(resp.response)
    assert next(chunks).startswith(b"retry:")
    hello = next(chunks).decode()
    assert hello.startswith("event: hello\ndata: ")
    first = next(chunks).decode()
    assert first.startswith("data: ")
    snap = json.loads(first[len("data: "):])
    assert snap["state"] == "idle"
    h.press("go")
    second = json.loads(next(chunks).decode()[len("data: "):])
    assert second["state"] == "checks"
    assert second["version"] > snap["version"]
    resp.close()


def test_web_server_skips_busy_port():
    import socket

    from rocket_demo.web.server import WebServer

    h = Harness()
    blocker = socket.socket()
    blocker.bind(("127.0.0.1", 0))
    blocker.listen()
    busy = blocker.getsockname()[1]
    h.cfg.web_host = "127.0.0.1"
    h.cfg.web_port = busy
    try:
        server = WebServer(h.ctrl, h.cfg)
        assert server.port != busy
        assert h.cfg.web_port == server.port
        server._server.server_close()
    finally:
        blocker.close()


def test_build_id_changes_with_mission(tmp_path):
    from rocket_demo.web.server import build_id

    info = {"name": "AURORA"}
    assert build_id(info) == build_id(dict(info))
    assert build_id(info) != build_id({"name": "ORION"})
