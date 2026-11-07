"""Deterministic screening; never a certification or legal verdict."""
from datetime import date

from app.schemas.support_advisor import AssessmentCreate

RULES_VERSION = "support-advisor-1.0"
SOURCE = {"title": "Regulation (EU) 2024/2847", "version": "2024-11-20", "sections": ["Article 13(8)", "Annex I Part II", "Annex VII"], "url": "https://eur-lex.europa.eu/eli/reg/2024/2847/2024-11-20/eng"}


def assess(payload: AssessmentCreate, components: list[dict], sboms: list[dict] | None = None) -> dict:
    start, end, expected = payload.support_start, payload.support_end, payload.expected_use_end
    anniversary_day = 28 if (start.month, start.day) == (2, 29) else start.day
    fifth = start.replace(year=start.year + 5, day=anniversary_day)
    findings = []

    def flag(rule, message):
        findings.append({"rule": rule, "message": message})

    if end < fifth and not (expected < fifth and end == expected and payload.expected_use_basis == "documented" and payload.evidence_ids):
        flag("SP-001", "Support below five years needs documented shorter expected use and corresponding support.")
    if end < expected:
        flag("SP-002", "Support is shorter than expected use; proportionality reasoning requires human review.")
    if not payload.evidence_ids or payload.expected_use_basis != "documented":
        flag("SP-006", "Expected-use justification needs documented evidence.")
    registered = {(c["name"].casefold(), c["version"]) for c in components}
    for sbom in sboms or []:
        for dependency in sbom.get("components_json", []):
            if not isinstance(dependency, dict) or (str(dependency.get("name", "")).casefold(), dependency.get("version")) not in registered:
                name = dependency.get("name", "Unnamed dependency") if isinstance(dependency, dict) else "Unnamed dependency"
                flag("SP-005", f"SBOM dependency {name}: no version-specific support commitment linked.")
    remedies = {str(r.component_link_id): r for r in payload.remediations}
    gaps = []
    if not components:
        flag("SP-005", "No release component inventory is linked; dependency coverage is unknown.")
    for c in components:
        component_end = date.fromisoformat(c["support_end_date"]) if c["support_end_date"] else None
        component_start = date.fromisoformat(c["support_start_date"]) if c["support_start_date"] else None
        trailing = max(0, (end - max(start, component_end)).days) if component_end else None
        leading = max(0, (min(end, component_start) - start).days) if component_start else 0
        verified = bool(component_start and component_end and component_end >= component_start and c["support_verified_at"] and c["support_reference_url"] and c["support_scope"])
        remedy = remedies.get(c["link_id"])
        days = trailing + leading if trailing is not None and (not component_start or component_end >= component_start) else None
        status = "UNKNOWN" if not verified else "REMEDIATION_REVIEW" if days and remedy else "ACTION_REQUIRED" if days else "COVERED"
        if not verified:
            flag("SP-005", f'{c["name"]}: commitment evidence or end date is missing; coverage unknown.')
        if days:
            flag("SP-003", f'{c["name"]}: {days} days require alternative remediation assessment.')
            if not remedy:
                flag("SP-004", f'{c["name"]}: documented remediation is missing.')
        gaps.append({**c, "gap_days": days, "leading_gap_days": leading, "status": status})
    unresolved = not gaps or any(g["status"] in ("UNKNOWN", "ACTION_REQUIRED") for g in gaps)
    unresolved = unresolved or any(f["rule"] == "SP-005" for f in findings)
    return {"rules_version": RULES_VERSION, "source": SOURCE, "findings": findings, "components": gaps,
            "legal_admissibility": "review_required", "technical_readiness": "unresolved" if unresolved else "review_required",
            "economic_attractiveness": "not_assessed", "general_minimum_met": end >= fifth,
            "approval_blockers": sorted({f["rule"] for f in findings} & {"SP-001", "SP-004", "SP-005", "SP-006"})}
