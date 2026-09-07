from __future__ import annotations

import json

import pytest

from app.services.sbom_analyzer import parse_metadata, validate_sbom_content


def test_parses_nested_cyclonedx_components() -> None:
    content = json.dumps({
        "bomFormat": "CycloneDX",
        "specVersion": "1.6",
        "components": [{
            "type": "application",
            "name": "parent",
            "components": [{
                "type": "library",
                "name": "lodash",
                "version": "4.17.20",
                "purl": "pkg:npm/lodash@4.17.20",
            }],
        }],
    })

    metadata = parse_metadata(content)

    assert metadata.component_count == 2
    assert metadata.components_json[1]["purl"] == "pkg:npm/lodash@4.17.20"


def test_spdx_purl_does_not_require_reference_category() -> None:
    content = json.dumps({
        "spdxVersion": "SPDX-2.3",
        "packages": [{
            "name": "requests",
            "versionInfo": "2.19.0",
            "externalRefs": [{
                "referenceType": "PURL",
                "referenceLocator": "pkg:pypi/requests@2.19.0",
            }],
        }],
    })

    assert parse_metadata(content).components_json[0]["purl"] == "pkg:pypi/requests@2.19.0"


@pytest.mark.parametrize("content", ["not json", "[]", "{}", '{"bomFormat":"Other"}'])
def test_rejects_invalid_or_unsupported_sboms(content: str) -> None:
    with pytest.raises(ValueError):
        validate_sbom_content(content)
