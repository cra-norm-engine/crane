import asyncio

from starlette.responses import PlainTextResponse

from app.core.config import settings
from app.core.maintenance import MaintenanceMiddleware


def test_maintenance_blocks_application_but_not_health(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(settings, "update_state_dir", tmp_path)
    (tmp_path / "maintenance.json").write_text("{}", encoding="utf-8")

    async def downstream(scope, receive, send) -> None:
        await PlainTextResponse("ok")(scope, receive, send)

    async def request(path: str) -> list[dict]:
        messages = []
        scope = {
            "type": "http", "asgi": {"version": "3.0"}, "http_version": "1.1",
            "method": "GET", "scheme": "http", "path": path,
            "raw_path": path.encode(), "query_string": b"", "headers": [],
        }

        async def receive() -> dict:
            return {"type": "http.request", "body": b"", "more_body": False}

        async def send(message: dict) -> None:
            messages.append(message)

        await MaintenanceMiddleware(downstream)(scope, receive, send)
        return messages

    blocked, health = asyncio.run(request("/work")), asyncio.run(request("/healthz"))
    assert blocked[0]["status"] == 503
    assert (b"retry-after", b"60") in blocked[0]["headers"]
    assert health[0]["status"] == 200
