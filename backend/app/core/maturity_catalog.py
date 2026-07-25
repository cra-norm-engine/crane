from __future__ import annotations

from datetime import date

from app.core.maturity_catalog_data import OFFICIAL_QUESTIONS

DOMAINS = {
    "1": "Governance and documentation",
    "2": "Risk management and security by design and by default",
    "3": "Vulnerability and patch management",
    "4": "Product life cycle management",
    "5": "Awareness, competence and skills",
}

CATALOG = [
    {**question, "domain_code": question["code"][0], "domain": DOMAINS[question["code"][0]]}
    for question in OFFICIAL_QUESTIONS
]

MODEL = {
    "code": "ENISA-SME-2026-07",
    "title": "SME Cyber Resilience Maturity Assessment Model",
    "source": "European Union Agency for Cybersecurity (ENISA)",
    "published_on": date(2026, 7, 1),
    "attribution": "© European Union Agency for Cybersecurity (ENISA), 2026. Reused under CC BY 4.0.",
}

RECOMMENDATIONS = {
    "1": "Define and approve policies, responsibilities, product documentation, review routines, and authority contacts.",
    "2": "Maintain product risk assessments and integrate secure design, secure defaults, and testing into development.",
    "3": "Track vulnerabilities, maintain SBOMs, prioritise by risk, deliver updates, and verify fixes.",
    "4": "Define support periods, operational monitoring, issue response, customer communication, and feedback loops.",
    "5": "Identify required skills, deliver role-relevant training, follow external intelligence, and assess competence.",
}

# Product capability guidance is intentionally separate from the frozen ENISA
# question text: model wording remains historical while CRANE support can evolve.
CRANE_SUPPORT = {
    "1.1": {"level": "partial", "summary": "Store approved policies as versioned artifacts and retain an audit trail.", "links": [{"label": "Technical artifacts", "route": "product-data"}], "gap": "CRANE does not yet provide a dedicated organisation-wide policy approval register."},
    "1.2": {"level": "strong", "summary": "Roles, permissions, product ownership, reviewers, assignees, and due dates establish accountable responsibilities.", "links": [{"label": "Roles & access", "route": "admin-roles"}, {"label": "My tasks", "route": "my-tasks"}]},
    "1.3": {"level": "strong", "summary": "Products, releases, risk assessments, requirement mappings, artifacts, SBOMs, and update records form traceable technical documentation.", "links": [{"label": "Product inventory", "route": "products"}, {"label": "CRA requirements", "route": "annex-matrix"}]},
    "1.4": {"level": "strong", "summary": "Review and approval workflows plus the append-only audit history demonstrate recurring review activity.", "links": [{"label": "Audit history", "route": "audit-history"}, {"label": "Risk assessments", "route": "risk-assessments"}]},
    "1.5": {"level": "partial", "summary": "Product classification and conformity routes are recorded and carried into releases and declarations.", "links": [{"label": "Product inventory", "route": "products"}, {"label": "Declarations", "route": "declarations"}], "gap": "A market-surveillance authority contact directory is not yet available."},
    "2.1": {"level": "strong", "summary": "Versioned risk assessments link risks to releases, controls, owners, evidence, and approval decisions.", "links": [{"label": "Risk assessments", "route": "risk-assessments"}]},
    "2.2": {"level": "strong", "summary": "CRA requirement mappings capture implementation decisions, secure-development activities, linked risks, artifacts, and evidence.", "links": [{"label": "CRA requirements", "route": "annex-matrix"}, {"label": "Compliance journey", "route": "compliance-journey"}]},
    "2.3": {"level": "partial", "summary": "Security requirements and release evidence can document secure-default decisions.", "links": [{"label": "CRA requirements", "route": "annex-matrix"}], "gap": "Secure-default declarations are not a dedicated first-class record."},
    "2.4": {"level": "strong", "summary": "Release gates, requirement evidence, artifacts, and SBOM analysis capture pre-release security checks.", "links": [{"label": "Products and releases", "route": "products"}, {"label": "SBOM analyzer", "route": "sbom-records"}]},
    "2.5": {"level": "strong", "summary": "Versioned risk reviews, vulnerability monitoring, SBOM scans, advisories, and change assessments support reassessment when threats change.", "links": [{"label": "Risk assessments", "route": "risk-assessments"}, {"label": "Substantial changes", "route": "changes"}]},
    "3.1": {"level": "strong", "summary": "CVD policies and the PSIRT workflow receive, assign, acknowledge, track, and report vulnerabilities.", "links": [{"label": "PSIRT workflow", "route": "vulnerability-handling"}]},
    "3.2": {"level": "strong", "summary": "Security updates record remediation, testing, distribution, customer communication, deadlines, and linked advisories.", "links": [{"label": "Security updates", "route": "security-updates"}]},
    "3.3": {"level": "strong", "summary": "Machine-readable SBOMs, quality analysis, component inventories, scan runs, and findings support dependency management.", "links": [{"label": "SBOM analyzer", "route": "sbom-records"}]},
    "3.4": {"level": "strong", "summary": "CVSS, EPSS, CISA KEV, VEX, exploitability, severity, impact, and remediation deadlines support risk-based prioritisation.", "links": [{"label": "PSIRT workflow", "route": "vulnerability-handling"}]},
    "3.5": {"level": "partial", "summary": "Updates link back to vulnerability records and can retain verification artifacts and release evidence.", "links": [{"label": "Security updates", "route": "security-updates"}], "gap": "Fix-verification is not yet a distinct approval workflow."},
    "4.1": {"level": "strong", "summary": "PSIRT, support periods, security updates, advisories, incidents, and lifecycle notifications cover operational security.", "links": [{"label": "Support Hub", "route": "support-hub"}, {"label": "PSIRT workflow", "route": "vulnerability-handling"}]},
    "4.2": {"level": "strong", "summary": "Versioned support periods capture ownership, end-of-support dates, customer summaries, and notification recipients.", "links": [{"label": "Support Hub", "route": "support-hub"}, {"label": "Lifecycle alerts", "route": "lifecycle-notifications"}]},
    "4.3": {"level": "partial", "summary": "Incident reports, comments, changes, and audit history retain operational experience and follow-up activity.", "links": [{"label": "PSIRT workflow", "route": "vulnerability-handling"}, {"label": "Substantial changes", "route": "changes"}], "gap": "Post-incident lessons and customer-feedback records are not dedicated modules."},
    "4.4": {"level": "strong", "summary": "Assigned vulnerabilities, incident reporting, remediation deadlines, update workflows, and release gates provide a repeatable response path.", "links": [{"label": "PSIRT workflow", "route": "vulnerability-handling"}, {"label": "My tasks", "route": "my-tasks"}]},
    "4.5": {"level": "strong", "summary": "SBOM scanning, vulnerability sources, advisories, lifecycle alerts, and incident records provide operational monitoring evidence.", "links": [{"label": "SBOM analyzer", "route": "sbom-records"}, {"label": "Lifecycle alerts", "route": "lifecycle-notifications"}]},
    "5.1": {"level": "partial", "summary": "Roles, permissions, named owners, reviewers, and assignees show which expertise is allocated to security work.", "links": [{"label": "Roles & access", "route": "admin-roles"}, {"label": "Users", "route": "admin-users"}], "gap": "CRANE does not maintain a skills inventory or external-expertise register."},
    "5.2": {"level": "gap", "summary": "No current CRANE module records training programmes, attendance, or training effectiveness.", "links": [], "gap": "A training and awareness module is required to substantiate this answer."},
    "5.3": {"level": "partial", "summary": "Assigned work, comments, reporting channels, safe-harbour CVD policies, and audit history support open reporting and accountability.", "links": [{"label": "PSIRT workflow", "route": "vulnerability-handling"}, {"label": "Audit history", "route": "audit-history"}], "gap": "Security-culture measurement is outside the current platform."},
    "5.4": {"level": "strong", "summary": "Security advisories, NVD/OSV-based SBOM scanning, CISA KEV, EPSS, and lifecycle alerts bring external intelligence into product records.", "links": [{"label": "SBOM analyzer", "route": "sbom-records"}, {"label": "PSIRT workflow", "route": "vulnerability-handling"}]},
    "5.5": {"level": "gap", "summary": "Roles and assignments show responsibility but do not validate individual competence.", "links": [{"label": "Roles & access", "route": "admin-roles"}], "gap": "Competence assessments and skills-gap tracking are not currently available."},
}
