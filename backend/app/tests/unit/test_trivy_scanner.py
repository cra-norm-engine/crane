from __future__ import annotations

import json

from app.services.trivy_scanner import _trivy_compatible_content


def test_normalizes_unsupported_cyclonedx_types_for_trivy() -> None:
    original = {
        "bomFormat": "CycloneDX",
        "metadata": {"component": {"type": "firmware", "name": "device"}},
        "components": [
            {"type": "library", "name": "valid"},
            {"type": "device-driver", "name": "driver"},
        ],
    }

    normalized = json.loads(_trivy_compatible_content(json.dumps(original)))

    assert normalized["metadata"]["component"]["type"] == "application"
    assert normalized["components"][0]["type"] == "library"
    assert normalized["components"][1]["type"] == "library"
    assert original["metadata"]["component"]["type"] == "firmware"


def test_leaves_spdx_content_unchanged() -> None:
    content = '{"spdxVersion":"SPDX-2.3"}'
    assert _trivy_compatible_content(content) == content
