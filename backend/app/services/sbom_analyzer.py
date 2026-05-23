"""Thin wrapper around the sbom-tools CLI for SBOM quality and compliance analysis.

Runs two commands per analysis:
  - sbom-tools quality  <file> --profile security --recommendations --output json
  - sbom-tools validate <file> --standard cra,ntia --output json

When a previous SBOM content is provided (for diff), also runs:
  - sbom-tools diff <old> <new> --output json

Results are merged into a single dict stored in analysis_findings.
All failures are non-fatal — callers receive partial results on error.
"""

from __future__ import annotations

import json
import logging
import re
import subprocess
import tempfile
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# sbom-tools exits with non-zero to signal findings, not failure.
_EXPECTED_EXIT_CODES = {0, 1, 2, 4}
_TIMEOUT_SECONDS = 60

# sbom-tools emits ANSI-colored INFO lines to stdout before the JSON payload.
# Strip them so the JSON search doesn't mistake ESC [ (e.g. \x1b[2m) for an array.
_ANSI_RE = re.compile(r"\x1b\[[0-9;]*[mGKHFABCDJK]")


def _extract_json(stdout: str) -> str:
    """Strip ANSI codes and INFO log lines that precede the JSON payload on stdout."""
    clean = _ANSI_RE.sub("", stdout)
    for i, ch in enumerate(clean):
        if ch in ("{", "["):
            return clean[i:]
    return ""


def _run(args: list[str], label: str) -> dict[str, Any] | list[Any]:
    """Run a sbom-tools command and return parsed JSON output."""
    try:
        result = subprocess.run(
            args,
            capture_output=True,
            text=True,
            timeout=_TIMEOUT_SECONDS,
        )
        if result.returncode not in _EXPECTED_EXIT_CODES:
            logger.warning(
                "sbom-tools %s exited %d: %s", label, result.returncode, result.stderr[:500]
            )
            return {"error": result.stderr[:500], "exit_code": result.returncode}
        raw = _extract_json(result.stdout)
        if not raw:
            return {}
        return json.loads(raw)
    except FileNotFoundError:
        logger.error("sbom-tools binary not found — skipping analysis")
        return {"error": "sbom-tools not installed"}
    except subprocess.TimeoutExpired:
        logger.warning("sbom-tools %s timed out after %ds", label, _TIMEOUT_SECONDS)
        return {"error": "analysis timed out"}
    except json.JSONDecodeError as exc:
        logger.warning("sbom-tools %s produced unparseable JSON: %s", label, exc)
        return {"error": "invalid JSON output"}


def _parse_quality_score(quality_result: Any) -> int | None:
    """Extract the overall quality score (0-100) from sbom-tools quality JSON output."""
    if not isinstance(quality_result, dict):
        return None
    # Primary location: result["report"]["overall_score"]
    report = quality_result.get("report")
    if isinstance(report, dict):
        val = report.get("overall_score")
        if isinstance(val, (int, float)):
            return int(val)
    # Fallback: top-level keys
    for key in ("overall_score", "score", "total_score", "quality_score"):
        val = quality_result.get(key)
        if isinstance(val, (int, float)):
            return int(val)
    return None


class SbomMetadata:
    """Parsed metadata extracted directly from an SBOM document."""

    __slots__ = (
        "format",
        "spec_version",
        "tool_name",
        "tool_version",
        "generated_at",
        "component_count",
        "components_json",
    )

    def __init__(self) -> None:
        self.format: str = "cyclonedx"
        self.spec_version: str | None = None
        self.tool_name: str | None = None
        self.tool_version: str | None = None
        self.generated_at: str | None = None  # ISO-8601 string or None
        self.component_count: int | None = None
        self.components_json: list[dict[str, Any]] = []


def _parse_cdx_tool(tools_node: Any) -> tuple[str | None, str | None]:
    """
    Extract (name, version) from a CycloneDX tools node.
    Handles both CycloneDX ≤1.5 (list of objects) and
    1.6 (object with components/services sub-keys).
    """
    if isinstance(tools_node, list):
        # ≤1.5: [ {vendor, name, version}, ... ]
        for t in tools_node:
            if isinstance(t, dict):
                name = t.get("name") or t.get("vendor")
                version = t.get("version")
                if name:
                    return str(name), str(version) if version else None
    elif isinstance(tools_node, dict):
        # 1.6: { components: [...], services: [...] }
        for sub_key in ("components", "services"):
            entries = tools_node.get(sub_key)
            if isinstance(entries, list):
                for t in entries:
                    if isinstance(t, dict):
                        name = t.get("name") or t.get("vendor")
                        version = t.get("version")
                        if name:
                            return str(name), str(version) if version else None
    return None, None


def _cdx_component_to_dict(comp: dict[str, Any]) -> dict[str, Any]:
    """Normalise a CycloneDX component object to a compact storage dict."""
    out: dict[str, Any] = {}
    for key in ("name", "version", "type", "purl", "cpe", "group", "supplier"):
        if comp.get(key):
            out[key] = comp[key]
    return out


def _spdx_package_to_dict(pkg: dict[str, Any]) -> dict[str, Any]:
    """Normalise an SPDX package object to a compact storage dict."""
    out: dict[str, Any] = {}
    for key in ("name", "versionInfo", "downloadLocation"):
        if pkg.get(key):
            out[key] = pkg[key]
    if out.get("versionInfo"):
        out["version"] = out.pop("versionInfo")
    # Extract purl from externalRefs (SPDX 2.2+: referenceCategory PACKAGE-MANAGER, referenceType purl)
    for ref in pkg.get("externalRefs", []):
        if (
            ref.get("referenceCategory") in ("PACKAGE-MANAGER", "PACKAGE_MANAGER")
            and ref.get("referenceType") == "purl"
            and ref.get("referenceLocator")
        ):
            out["purl"] = ref["referenceLocator"]
            break
    return out


def parse_metadata(sbom_content: str) -> SbomMetadata:
    """
    Parse an SBOM document (JSON only — XML is left as future work) and
    return a SbomMetadata instance with all extractable fields populated.
    Non-fatal: if the content cannot be parsed, returns a default instance.
    """
    meta = SbomMetadata()
    try:
        doc = json.loads(sbom_content)
    except (json.JSONDecodeError, ValueError):
        return meta  # unknown / XML format — leave defaults

    if not isinstance(doc, dict):
        return meta

    # ── CycloneDX JSON ──────────────────────────────────────────────────────
    bom_format = doc.get("bomFormat", "")
    if isinstance(bom_format, str) and bom_format.lower() == "cyclonedx":
        meta.format = "cyclonedx"
        meta.spec_version = doc.get("specVersion")

        metadata = doc.get("metadata") or {}
        meta.generated_at = metadata.get("timestamp")
        meta.tool_name, meta.tool_version = _parse_cdx_tool(metadata.get("tools"))

        # Fallback: tools at top-level (non-standard but seen in the wild)
        if not meta.tool_name:
            meta.tool_name, meta.tool_version = _parse_cdx_tool(doc.get("tools"))

        components = doc.get("components") or []
        if isinstance(components, list):
            meta.components_json = [
                _cdx_component_to_dict(c) for c in components if isinstance(c, dict)
            ]
            meta.component_count = len(meta.components_json)
        return meta

    # ── SPDX JSON ────────────────────────────────────────────────────────────
    spdx_version = doc.get("spdxVersion", "")
    if isinstance(spdx_version, str) and spdx_version.lower().startswith("spdx"):
        meta.format = "spdx"
        # e.g. "SPDX-2.3" → "2.3"
        meta.spec_version = spdx_version.replace("SPDX-", "").strip() or None

        creation_info = doc.get("creationInfo") or {}
        meta.generated_at = creation_info.get("created")

        # Creators: ["Tool: syft-0.99.0", "Organization: ..."]
        for creator in creation_info.get("creators") or []:
            if isinstance(creator, str) and creator.lower().startswith("tool:"):
                raw = creator.split(":", 1)[1].strip()
                # "syft-0.99.0" → name="syft", version="0.99.0"
                if "-" in raw:
                    # Split on last hyphen-followed-by-digit to separate version
                    import re as _re
                    m = _re.match(r"^(.+?)-(\d[\w.]*)$", raw)
                    if m:
                        meta.tool_name, meta.tool_version = m.group(1), m.group(2)
                    else:
                        meta.tool_name = raw
                else:
                    meta.tool_name = raw
                break

        packages = doc.get("packages") or []
        if isinstance(packages, list):
            meta.components_json = [
                _spdx_package_to_dict(p) for p in packages if isinstance(p, dict)
            ]
            meta.component_count = len(meta.components_json)
        return meta

    return meta


def analyze(sbom_content: str, previous_content: str | None = None) -> dict[str, Any]:
    """
    Write sbom_content to a temp file, run quality + validate (and optionally diff),
    and return a merged findings dict along with a parsed quality_score.

    Returns:
        dict with keys: quality, validate, diff (optional), quality_score (int | None)
    """
    findings: dict[str, Any] = {}
    quality_score: int | None = None

    with tempfile.TemporaryDirectory() as tmp_dir:
        sbom_path = Path(tmp_dir) / "sbom.json"
        sbom_path.write_text(sbom_content, encoding="utf-8")

        # Quality scoring with recommendations
        quality_result = _run(
            [
                "sbom-tools", "quality", str(sbom_path),
                "--profile", "security",
                "--recommendations",
                "--output", "json",
            ],
            label="quality",
        )
        findings["quality"] = quality_result
        quality_score = _parse_quality_score(quality_result)

        # CRA + NTIA compliance validation
        validate_result = _run(
            [
                "sbom-tools", "validate", str(sbom_path),
                "--standard", "cra,ntia",
                "--output", "json",
            ],
            label="validate",
        )
        # validate returns a list of standard results
        findings["validate"] = validate_result

        # Diff against previous SBOM if one exists
        if previous_content:
            prev_path = Path(tmp_dir) / "sbom_prev.json"
            prev_path.write_text(previous_content, encoding="utf-8")
            diff_result = _run(
                ["sbom-tools", "diff", str(prev_path), str(sbom_path), "--output", "json"],
                label="diff",
            )
            findings["diff"] = diff_result

    findings["quality_score"] = quality_score
    return findings
