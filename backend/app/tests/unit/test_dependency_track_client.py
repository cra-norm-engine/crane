from uuid import uuid4

import httpx
import pytest

from app.core.exceptions import ValidationException
from app.services.dependency_track_service import get_json, list_projects


def test_pagination_includes_later_projects(monkeypatch):
    page = [{"uuid": str(uuid4()), "name": f"Project {i}"} for i in range(100)]
    tail = {"uuid": str(uuid4()), "name": "Last project"}
    calls = []
    def fetch(url, key, path, params):
        calls.append(params["pageNumber"])
        return page if params["pageNumber"] == 1 else [tail]
    monkeypatch.setattr("app.services.dependency_track_service.get_json", fetch)
    projects = list_projects("https://example.com", "secret")
    assert len(projects) == 101 and projects[-1].name == "Last project"
    assert calls == [1, 2]


@pytest.mark.parametrize("status", [401, 403, 302, 500])
def test_remote_errors_do_not_expose_secret_and_redirects_are_not_followed(monkeypatch, status):
    original_client = httpx.Client
    calls = []
    def response(request):
        calls.append(request)
        assert request.headers["X-Api-Key"] == "sensitive-key"
        return httpx.Response(status, text="sensitive-key", headers={"Location": "https://elsewhere.example"})
    monkeypatch.setattr("app.services.dependency_track_service.socket.getaddrinfo", lambda *args, **kwargs: [(2, 1, 6, "", ("127.0.0.1", 80))])
    monkeypatch.setattr("app.services.dependency_track_service.httpx.Client", lambda **kwargs: original_client(transport=httpx.MockTransport(response), **kwargs))
    with pytest.raises(ValidationException) as exc:
        get_json("https://example.com", "sensitive-key", "/api/v1/project")
    assert "sensitive-key" not in str(exc.value)
    assert len(calls) == 1


def test_blocks_cloud_metadata_addresses(monkeypatch):
    monkeypatch.setattr("app.services.dependency_track_service.socket.getaddrinfo", lambda *args, **kwargs: [(2, 1, 6, "", ("169.254.169.254", 80))])
    with pytest.raises(ValidationException, match="not allowed"):
        get_json("http://169.254.169.254", "secret", "/api/v1/project")
