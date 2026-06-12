# CRANE — CRA Norm Engine
# Copyright (C) 2026 Ali Mohammad Hosseini
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# This file is part of CRANE, free software under the GNU Affero General Public
# License v3.0 or later. See <https://www.gnu.org/licenses/>.

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_root_returns_running_message() -> None:
    response = client.get("/")
    assert response.status_code == 200
    assert "running" in response.json()["message"].lower()