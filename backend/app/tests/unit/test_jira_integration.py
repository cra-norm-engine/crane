from __future__ import annotations

from types import SimpleNamespace
from urllib.parse import parse_qs, urlparse
from uuid import uuid4

from jose import jwt

from app.core.config import settings
from app.services.jira_integration_service import (
    JiraIntegrationService,
    adf_to_text,
    text_to_adf,
)


def test_adf_plain_text_round_trip() -> None:
    source = "First paragraph\n\nLast paragraph"
    assert adf_to_text(text_to_adf(source)) == source


def test_oauth_url_has_signed_user_state(monkeypatch) -> None:
    monkeypatch.setattr(settings, "jira_oauth_client_id", "client-id")
    monkeypatch.setattr(settings, "jira_oauth_client_secret", "client-secret")
    actor = SimpleNamespace(id=uuid4())

    url = JiraIntegrationService(None).oauth_url(actor)
    query = parse_qs(urlparse(url).query)
    claims = jwt.decode(query["state"][0], settings.secret_key, algorithms=["HS256"])

    assert query["client_id"] == ["client-id"]
    assert query["audience"] == ["api.atlassian.com"]
    assert "offline_access" in query["scope"][0]
    assert claims["sub"] == str(actor.id)
    assert claims["type"] == "jira_oauth"


def test_adf_reader_ignores_formatting_nodes() -> None:
    document = {
        "type": "doc",
        "version": 1,
        "content": [{"type": "paragraph", "content": [
            {"type": "text", "text": "CRANE", "marks": [{"type": "strong"}]},
            {"type": "text", "text": " task"},
        ]}],
    }
    assert adf_to_text(document) == "CRANE task"
