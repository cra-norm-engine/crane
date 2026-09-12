# CRANE — CRA Norm Engine
# Copyright (C) 2026 Ali Mohammad Hosseini
# SPDX-License-Identifier: AGPL-3.0-or-later

from __future__ import annotations

from starlette.responses import JSONResponse
from starlette.types import ASGIApp, Receive, Scope, Send

from app.core.config import settings

_active_requests = 0
_HEALTH_PATHS = {"/healthz", f"{settings.api_prefix}/health"}


def maintenance_mode() -> bool:
    return (settings.update_state_dir / "maintenance.json").is_file()


def active_requests() -> int:
    return _active_requests


class MaintenanceMiddleware:
    """Drain and reject application traffic during a controlled update."""

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        global _active_requests
        if scope["type"] != "http" or scope["path"] in _HEALTH_PATHS:
            await self.app(scope, receive, send)
            return

        _active_requests += 1
        try:
            if maintenance_mode():
                response = JSONResponse(
                    status_code=503,
                    headers={"Retry-After": "60"},
                    content={
                        "detail": "CRANE is temporarily unavailable while a verified update is applied.",
                        "code": "maintenance_mode",
                    },
                )
                await response(scope, receive, send)
                return
            await self.app(scope, receive, send)
        finally:
            _active_requests -= 1
