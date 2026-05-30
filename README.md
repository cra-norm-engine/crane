# CRANE — CRA Norm Engine

**Self-hosted compliance management for the EU Cyber Resilience Act.**

CRANE helps manufacturers of products with digital elements meet their CRA obligations — from SBOM analysis and vulnerability tracking to release gates and lifecycle notifications — in one auditable, self-hosted platform.

---

![CRANE Dashboard](.github/assets/dashboard.png)

---

## Who is this for?

| Audience | How CRANE helps |
|---|---|
| **Small & medium manufacturers** | Affordable alternative to expensive GRC platforms — self-host with Docker in minutes |
| **Software manufacturers** | Track products, releases, SBOMs, and vulnerabilities in one place from day one of CRA |
| **Consultants** | Deploy a dedicated instance per client engagement; portable data export at project close |
| **Education & research** | Free, open source, fully documented — ideal for CRA training and academic research |
| **Critical infrastructure operators** | Self-hosted with no external data sharing; LDAP/AD integration for enterprise environments |

---

## Features

| Area | What it does |
|---|---|
| **Product registry** | Track products, versions, releases, and support periods |
| **Release gates** | Structured readiness checklist with evidence before every release |
| **SBOM analysis** | Quality scoring, CRA Phase 2 validation, NTIA compliance, diff view |
| **Vulnerability management** | PSIRT workflow, CVE tracking, EPSS scoring, VEX assessments |
| **Security operations** | Advisories, CVD policies, update history, incoming report triage |
| **Risk assessments** | STRIDE / TARA / custom methodology, approval workflow |
| **CRA Annex I matrix** | Requirement coverage map per product with evidence links |
| **Substantial changes** | Article 3(4) change assessment and re-conformity tracking |
| **Lifecycle alerts** | End-of-support monitoring with configurable thresholds |
| **Audit trail** | Immutable, timestamped log of every action |
| **RBAC + LDAP** | Role-based access control, Active Directory / OpenLDAP integration |

---

## Quick Start

**Prerequisites:** Docker and Docker Compose.

```bash
git clone https://github.com/cra-norm-engine/crane.git
cd crane
cp .env.example .env
# Set BACKEND_SECRET_KEY and POSTGRES_PASSWORD in .env
docker compose up -d
```

| Service | URL |
|---|---|
| App | http://localhost:5173 |
| API | http://localhost:8000/api/v1 |
| API docs | http://localhost:8000/docs |

Default admin credentials are printed in the backend logs on first run.

---

## Stack

**Backend:** FastAPI · SQLAlchemy 2 · PostgreSQL 16 · Alembic · Pydantic v2  
**Frontend:** Vue 3 · TypeScript · Pinia · Vite  
**Scanning:** Trivy (optional) · OSV · NVD · EPSS by FIRST.org

---

## Roadmap

### Near term
- [ ] PDF compliance report export — audit-ready package for Notified Body submissions
- [ ] Email notifications — EOS alerts, vulnerability digest, gate approvals
- [ ] GitHub / GitLab OAuth login
- [ ] Password reset via email

### Medium term
- [ ] Multi-tenant support — manage multiple organisations from one instance
- [ ] Jira / GitHub Issues integration — sync vulnerabilities to your issue tracker
- [ ] REST API webhooks — push compliance events to external systems
- [ ] CRA Article 14 incident reporting workflow

### Long term
- [ ] Railway sector overlay (NIS2, CENELEC EN 50128 / EN 50657)
- [ ] IEC 62443 requirement mapping
- [ ] AI-assisted risk assessment suggestions
- [ ] Marketplace for sector-specific compliance templates

---

## Self-hosted by design

- All data stays in your own PostgreSQL instance
- No telemetry, no callbacks, no external dependencies at runtime
- Full data export at any time
- AGPL-3.0 — audit the code, fork it, extend it

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). Please open an issue before submitting a PR for significant changes.

## Security

To report a vulnerability privately, see [SECURITY.md](SECURITY.md).

## License

[GNU Affero General Public License v3.0](LICENSE)
