"""
Trivy CLI wrapper for SBOM-based vulnerability scanning.

Trivy (https://trivy.dev) is a free, open-source vulnerability scanner by
Aqua Security. It aggregates NVD, GHSA, OSV, Ubuntu Security Notices,
Debian Security Tracker, Alpine, RHEL, and more into a single DB — giving
broader OS-level package coverage than the OSV API alone.

Usage: pass the raw SBOM content (CycloneDX/SPDX JSON) to scan_sbom_content().
The binary must be in PATH; the function returns None gracefully if it isn't.

Install Trivy: https://trivy.dev/latest/getting-started/installation/
"""
from __future__ import annotations

import json
import logging
import os
import shutil
import subprocess
import tempfile
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger(__name__)

_TRIVY_TIMEOUT = 180  # seconds — large SBOMs can take 60–90 s to scan


@dataclass
class TrivyFinding:
    """Normalized single CVE finding from a Trivy JSON scan output."""
    vuln_id: str
    pkg_name: str
    installed_version: str
    fixed_version: str | None
    severity: str | None          # uppercase: CRITICAL, HIGH, MEDIUM, LOW, UNKNOWN
    cvss_score: float | None
    cvss_vector: str | None
    description: str | None
    published_date: str | None
    last_modified_date: str | None
    aliases: list[str] = field(default_factory=list)


def is_trivy_available() -> bool:
    """Return True if the trivy binary is accessible in PATH."""
    return shutil.which("trivy") is not None


def _extract_cvss(vuln: dict[str, Any]) -> tuple[float | None, str | None]:
    """
    Pull CVSS v3 score and vector from a Trivy vulnerability dict.
    Prefers NVD data; falls back to first available provider.
    """
    cvss_map: dict[str, Any] = vuln.get("CVSS") or {}
    if not cvss_map:
        return None, None

    # Preferred source order
    for provider in ("nvd", "redhat", "ghsa"):
        entry = cvss_map.get(provider, {})
        score = entry.get("V3Score") or entry.get("v3Score")
        vector = entry.get("V3Vector") or entry.get("v3Vector")
        if score is not None:
            return float(score), vector

    # Fall back to whatever the first provider gives
    for entry in cvss_map.values():
        if isinstance(entry, dict):
            score = entry.get("V3Score") or entry.get("v3Score")
            vector = entry.get("V3Vector") or entry.get("v3Vector")
            if score is not None:
                return float(score), vector

    return None, None


def _detect_distro(sbom_content: str) -> str | None:
    """
    Parse purl strings from an SPDX/CycloneDX SBOM to detect the OS distro.

    Returns a Trivy --distro value like "ubuntu/20.04", "debian/11", or None.
    Trivy's SBOM mode cannot auto-detect OS from SPDX purl strings, so we
    inject it via --distro (experimental flag) to enable OS-level CVE lookups.
    """
    try:
        data = json.loads(sbom_content)
    except json.JSONDecodeError:
        return None

    # Collect purl strings from SPDX (externalRefs) or CycloneDX (purl field)
    purls: list[str] = []
    for pkg in data.get("packages", []):  # SPDX
        for ref in pkg.get("externalRefs", []):
            if ref.get("referenceType") == "purl":
                loc = ref.get("referenceLocator", "")
                if loc:
                    purls.append(loc)
    for comp in data.get("components", []):  # CycloneDX
        purl = comp.get("purl", "")
        if purl:
            purls.append(purl)

    if not purls:
        return None

    # Extract distro= query parameter from purls.
    # e.g. "pkg:deb/ubuntu/adduser@3.118ubuntu2?arch=all&distro=ubuntu-20.04"
    #       → "ubuntu/20.04"
    from urllib.parse import urlparse, parse_qs
    distro_counts: dict[str, int] = {}
    for purl in purls:
        qs_part = purl.split("?", 1)[1] if "?" in purl else ""
        if not qs_part:
            continue
        params = dict(kv.split("=", 1) for kv in qs_part.split("&") if "=" in kv)
        distro_raw = params.get("distro", "")  # e.g. "ubuntu-20.04"
        if not distro_raw:
            continue
        # Convert "ubuntu-20.04" → "ubuntu/20.04"
        parts = distro_raw.rsplit("-", 1)
        if len(parts) == 2:
            family, version = parts
            key = f"{family}/{version}"
            distro_counts[key] = distro_counts.get(key, 0) + 1

    if not distro_counts:
        return None

    # Return the most common distro
    return max(distro_counts, key=lambda k: distro_counts[k])


def scan_sbom_content(sbom_content: str) -> list[TrivyFinding] | None:
    """
    Run Trivy against a SBOM file (CycloneDX or SPDX JSON) and return findings.

    Auto-detects OS distro from purl strings and passes --distro to Trivy so
    OS-level packages (deb/rpm) are matched against the correct CVE database.

    Returns:
        list[TrivyFinding]  — findings found (may be empty for a clean SBOM)
        None                — Trivy is not installed; caller should log and skip
    """
    if not is_trivy_available():
        logger.warning("trivy not found in PATH — Trivy scanner skipped")
        return None

    distro = _detect_distro(sbom_content)
    if distro:
        logger.debug("Detected OS distro from SBOM purls: %s", distro)
    else:
        logger.debug("No OS distro detected from SBOM purls — Trivy will scan lang-pkgs only")

    findings: list[TrivyFinding] = []

    with tempfile.TemporaryDirectory() as tmpdir:
        sbom_path = os.path.join(tmpdir, "sbom.json")
        with open(sbom_path, "w", encoding="utf-8") as f:
            f.write(sbom_content)

        cmd = [
            "trivy", "sbom",
            "--format", "json",
            "--quiet",
            "--no-progress",
        ]
        if distro:
            # Experimental flag: override the detected OS so Trivy can query
            # the correct distro-specific advisory DB (Ubuntu USN, Debian DSA, etc.)
            cmd += ["--distro", distro]
        cmd.append(sbom_path)
        try:
            proc = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=_TRIVY_TIMEOUT,
            )
        except FileNotFoundError:
            logger.error("trivy binary not found despite shutil.which() check")
            return None
        except subprocess.TimeoutExpired:
            logger.warning("Trivy scan timed out after %ds — returning empty findings", _TRIVY_TIMEOUT)
            return []

        if proc.returncode not in (0, 1):
            # 0 = no vulns, 1 = vulns found; anything else is an error
            logger.warning(
                "Trivy exited with code %d — stderr: %s",
                proc.returncode,
                proc.stderr[:500] if proc.stderr else "(none)",
            )
            return []

        if not proc.stdout.strip():
            logger.debug("Trivy returned empty output")
            return []

        try:
            output = json.loads(proc.stdout)
        except json.JSONDecodeError as exc:
            logger.warning("Trivy JSON parse error: %s", exc)
            return []

    # Parse Results[*].Vulnerabilities[*]
    for result in output.get("Results", []):
        for vuln in result.get("Vulnerabilities") or []:
            try:
                vuln_id = vuln.get("VulnerabilityID", "")
                if not vuln_id:
                    continue

                cvss_score, cvss_vector = _extract_cvss(vuln)

                # Normalize severity — Trivy uses uppercase strings
                raw_sev = (vuln.get("Severity") or "").upper()
                severity = raw_sev if raw_sev in ("CRITICAL", "HIGH", "MEDIUM", "LOW") else None

                # Trivy may include related IDs under "RelatedVulnerabilities"
                aliases = [
                    r for r in (vuln.get("RelatedVulnerabilities") or [])
                    if r != vuln_id
                ]

                findings.append(TrivyFinding(
                    vuln_id=vuln_id,
                    pkg_name=vuln.get("PkgName", ""),
                    installed_version=vuln.get("InstalledVersion", ""),
                    fixed_version=vuln.get("FixedVersion") or None,
                    severity=severity,
                    cvss_score=cvss_score,
                    cvss_vector=cvss_vector,
                    description=vuln.get("Description") or vuln.get("Title"),
                    published_date=vuln.get("PublishedDate"),
                    last_modified_date=vuln.get("LastModifiedDate"),
                    aliases=aliases,
                ))
            except Exception as exc:
                logger.debug("Skipping malformed Trivy vuln entry: %s", exc)

    logger.info("Trivy scan found %d findings", len(findings))
    return findings


def trivy_findings_to_matched_vulns(
    findings: list[TrivyFinding],
    sbom_components: list[dict[str, Any]],
) -> list[tuple[dict[str, Any], dict[str, Any]]]:
    """
    Convert TrivyFinding objects into (component_dict, vuln_dict) pairs that
    the orchestrator can handle identically to OSV results.

    The vuln_dict keys mirror OSV format so the merge and persist logic
    doesn't need to know which scanner produced a given record.
    """
    # Build a name→component lookup for fast matching
    comp_by_name: dict[str, dict[str, Any]] = {}
    for comp in sbom_components:
        name = (comp.get("name") or comp.get("Name") or "").lower()
        if name:
            comp_by_name[name] = comp

    matched: list[tuple[dict[str, Any], dict[str, Any]]] = []

    for f in findings:
        # Look up the SBOM component by package name
        component = comp_by_name.get(f.pkg_name.lower()) or {
            "name": f.pkg_name,
            "version": f.installed_version,
        }

        # Build a vuln_dict shaped like an OSV record so the orchestrator
        # can treat both sources uniformly.
        cvss_severity_entry: list[dict] = []
        if f.cvss_vector:
            cvss_severity_entry = [{"type": "CVSS_V3", "score": f.cvss_vector}]

        vuln_dict: dict[str, Any] = {
            "id": f.vuln_id,
            "aliases": f.aliases,
            "severity": cvss_severity_entry,
            "summary": f.description,
            "details": f.description,
            "published": f.published_date,
            "modified": f.last_modified_date,
            "database_specific": {
                "severity": f.severity,
                "cvss_score": f.cvss_score,
            },
            "affected": [{"versions": [f.installed_version]}],
            "_fixed_in": [f.fixed_version] if f.fixed_version else [],
            "_source": "trivy",  # internal marker — stripped before DB storage
        }
        matched.append((component, vuln_dict))

    return matched
