"""
NVD (NIST National Vulnerability Database) REST API client.

Used exclusively for CVSS score enrichment — not as a primary scanner.
OSV and Trivy already discover CVEs; this fills in missing severity data by
querying authoritative CVSS v3 scores from NVD for CVEs that neither OSV nor
Trivy returned scores for.

Rate limits (without API key):  50 requests / 30 s  (~1.67/s)
Rate limits (with NVD_API_KEY):  2000 requests / 30 s  (~66/s)

Set NVD_API_KEY env var to a key obtained free at https://nvd.nist.gov/developers/request-an-api-key.
"""
from __future__ import annotations

import json
import logging
import os
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed

logger = logging.getLogger(__name__)

NVD_API_URL = "https://services.nvd.nist.gov/rest/json/cves/2.0"
_NVD_API_KEY = os.environ.get("NVD_API_KEY")

# Conservative sleep to stay under rate limit.
# Each thread sleeps this long before its network call.
_RATE_LIMIT_DELAY = 0.65 if not _NVD_API_KEY else 0.02


def fetch_cvss(cve_id: str) -> tuple[str | None, float | None, str | None]:
    """
    Fetch CVSS v3 data for a single CVE from NVD.

    Returns (severity_label, cvss_score, cvss_vector) or (None, None, None)
    on any error. Never raises — NVD enrichment is best-effort.
    """
    time.sleep(_RATE_LIMIT_DELAY)
    url = f"{NVD_API_URL}?cveId={cve_id}"
    headers: dict[str, str] = {"Accept": "application/json"}
    if _NVD_API_KEY:
        headers["apiKey"] = _NVD_API_KEY

    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read())
    except urllib.error.HTTPError as exc:
        if exc.code == 429:
            logger.warning("NVD rate limit hit for %s (429) — skipping enrichment", cve_id)
        elif exc.code == 404:
            logger.debug("NVD: %s not found (404)", cve_id)
        else:
            logger.warning("NVD HTTP %s for %s", exc.code, cve_id)
        return None, None, None
    except urllib.error.URLError as exc:
        logger.warning("NVD unreachable for %s: %s", cve_id, exc)
        return None, None, None
    except json.JSONDecodeError as exc:
        logger.warning("NVD returned invalid JSON for %s: %s", cve_id, exc)
        return None, None, None

    try:
        vulns = data.get("vulnerabilities", [])
        if not vulns:
            return None, None, None
        metrics = vulns[0]["cve"].get("metrics", {})
        # Prefer V31, fall back to V30
        for metric_key in ("cvssMetricV31", "cvssMetricV30"):
            entries = metrics.get(metric_key, [])
            if entries:
                cvss_data = entries[0]["cvssData"]
                return (
                    cvss_data.get("baseSeverity"),
                    cvss_data.get("baseScore"),
                    cvss_data.get("vectorString"),
                )
    except (KeyError, IndexError, TypeError) as exc:
        logger.debug("NVD parse error for %s: %s", cve_id, exc)

    return None, None, None


def enrich_findings_with_nvd(
    findings_missing_cvss: list[dict],
    max_enrichments: int = 100,
) -> dict[str, tuple[str | None, float | None, str | None]]:
    """
    Enrich a list of findings (each a dict with 'vuln_id' and 'aliases_json')
    by fetching CVSS data from NVD for any CVE IDs among them.

    Returns a {cve_id: (severity, score, vector)} cache dict.
    Only processes CVE-YYYY-NNNN IDs; GHSA and ecosystem-specific IDs are skipped.
    """
    # Collect unique CVE IDs from vuln_id and aliases
    cve_ids: list[str] = []
    seen: set[str] = set()
    for finding in findings_missing_cvss:
        candidates = [finding.get("vuln_id", "")] + (finding.get("aliases_json") or [])
        for cid in candidates:
            if cid.upper().startswith("CVE-") and cid not in seen:
                cve_ids.append(cid)
                seen.add(cid)
            if len(cve_ids) >= max_enrichments:
                break
        if len(cve_ids) >= max_enrichments:
            break

    if not cve_ids:
        return {}

    logger.info("NVD enrichment: fetching CVSS data for %d CVEs (key=%s)", len(cve_ids), bool(_NVD_API_KEY))

    cache: dict[str, tuple[str | None, float | None, str | None]] = {}
    # Low worker count: NVD rate limits are strict without a key.
    with ThreadPoolExecutor(max_workers=4) as pool:
        future_to_id = {pool.submit(fetch_cvss, cve_id): cve_id for cve_id in cve_ids}
        for future in as_completed(future_to_id):
            cve_id = future_to_id[future]
            try:
                result = future.result()
                if result[0] or result[1]:
                    cache[cve_id] = result
                    logger.debug("NVD enriched %s → %s (%.1f)", cve_id, result[0], result[1] or 0)
            except Exception as exc:
                logger.debug("NVD enrichment failed for %s: %s", cve_id, exc)

    return cache
