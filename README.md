# CRANE — CRA Norm Engine

![License](https://img.shields.io/badge/license-AGPL--3.0-green)
![Python](https://img.shields.io/badge/python-3.12-blue)
![Vue](https://img.shields.io/badge/vue-3-brightgreen)
![Docker](https://img.shields.io/badge/docker-compose-blue)
![Status](https://img.shields.io/badge/status-beta-orange)
![CI](https://img.shields.io/github/actions/workflow/status/cra-norm-engine/crane/ci.yml?branch=main)

## What is CRANE?

**CRANE** is a self-hosted open-source compliance management platform for meeting the **EU Cyber Resilience Act (CRA)**. CRANE can be deployed on-prem or via third-party clouds. Play with an online instance [here](https://cra-compliance-tool-1.onrender.com/). To get a username and password, please contact with this email address [cra.norm.engine@gmail.com]

![CRANE Dashboard](.github/assets/Main_dashboard.png)

What make CRANE diffferent:

- Free of charge and open source
- Security and privacy by keeping data inside organizations
- Strong access control and audit for collaborative environment
- Covering complex scenarios in product development and operation
- Focuse on compliance and staying compliant

Comprehensive overview of products with required CRA properties and justifications.

![Product Inventory](.github/assets/productInventory.png)

In one integrated tool, you can:
- **Track products & releases** with version history and lifecycle management
- **Upload & analyze SBOMs** (CycloneDX, SPDX) for component completeness and CVE exposure
- **Manage vulnerabilities** with EPSS risk scoring and patch tracking
- **Enforce release gates** with structured readiness checklists requiring evidence (pentests, assessments, SBOMs)
- **Maintain audit trails** of every compliance action for regulators and notified bodies
- **Organize evidence** in one place for conformity assessments and CE marking
- **On-prem** all data stays in your own PostgreSQL instance
- **Full control** no telemetry, no callbacks, no external dependencies at runtime

All data stays on your infrastructure. No external API calls, no vendor lock-in, fully auditable.



---

## Real-world scenarios
See [Scenarios](https://cra-norm-engine.github.io/crane/scenarios.html) where CRANE can be used. 
- 🏭 Industrial Manufacturer
- 💡 Small IoT Startup
- 🧑‍💼 CRA Compliance Consultant
- 🎓 Training & Research
  

---
## Who is this for?

| Audience | How CRANE helps |
|---|---|
| **Small & medium manufacturers** | Free alternative to expensive GRC platforms — self-host with Docker in minutes |
| **Software manufacturers** | Track products, releases, SBOMs, and vulnerabilities in one place from day one of CRA |
| **Consultants** | Deploy a dedicated instance per client engagement; portable data export at project close |
| **Education & research** | Free, open source, fully documented — ideal for CRA training and academic research |
| **Critical infrastructure operators** | Self-hosted with no external data sharing; LDAP/AD integration for enterprise environments |

---
## Key Features

| Feature | What it does |
|---|---|
| **Product Registry** | Track products, versions, releases, and support periods |
| **SBOM Analysis** | Quality scoring, CRA validation, NTIA compliance, component diffing |
| **Vulnerability Management** | CVE tracking, EPSS scoring, VEX assessments, patch workflows |
| **Release Gates** | Mandatory readiness checklist with attached evidence before shipping |
| **CRA Compliance Matrix** | Map requirements (Annex I) to products with evidence links |
| **Audit Trail** | Immutable, timestamped log of every action (regulatory proof) |
| **Risk Assessments** | STRIDE/TARA methodology support with approval workflows |
| **Team Collaboration** | Multi-user, role-based access, task assignment, commenting |
| **LDAP/AD Integration** | Enterprise identity management via Active Directory or OpenLDAP |
| **Data Export** | Full compliance package for notified bodies, with zero vendor lock-in |

---

## Installation
Prerequisites#

- [Docker Desktop](https://docs.docker.com/get-started/get-docker/) installed and running.
- On Windows: Docker set to Linux containers (right-click the Docker tray icon to switch).
- Roughly 2 GB of free disk for the image and vulnerability database.

**One-liner (fastest):**

```bash
# Linux / macOS
curl -fsSL https://raw.githubusercontent.com/cra-norm-engine/crane/main/install.sh | bash

# Windows (PowerShell)
irm https://raw.githubusercontent.com/cra-norm-engine/crane/main/install.ps1 | iex
```

**Or follow the detailed guide:** [Installation Guide](https://cra-norm-engine.github.io/crane/installation.html)

### Access the app

| Service | URL |
|---|---|
| App | http://localhost:5173 |
| API | http://localhost:8000/api/v1 |
| API docs | http://localhost:8000/docs |

### Default login

| Field | Value |
|---|---|
| Email | `admin@example.com` |
| Password | `admin1234` |

You will be prompted to set a new password on first login.

### Production Deployment

For production environments, use the production compose [Configuration](https://cra-norm-engine.github.io/crane/configuration.html) with strict security settings.

---

## Stack

**Backend:** FastAPI · SQLAlchemy 2 · PostgreSQL 16 · Alembic · Pydantic v2  
**Frontend:** Vue 3 · TypeScript · Pinia · Vite  
**Scanning:** Trivy (optional) · OSV · NVD · EPSS by FIRST.org

---

## Roadmap

<table>
<tr>
<td width="33%" valign="top">

### 🚀 Near Term (Q3 2026)
&nbsp;
- [ ] Full compliance with CRA reporting obligations before 11 September 2026
- [ ] Gates for fulfilling "without known exploitable vulnerability" requirements
- [ ] GitHub / GitLab integration

</td>
<td width="33%" valign="top">

### 📈 Medium Term (Q1 2027)
&nbsp;
- [ ] Integration of CENELEC vertical and horizontal standards
- [ ] Jira / GitHub Issues integration
- [ ] Integration with Security Development Lifecycle (SDL) processes (agile, V-Model, Waterfall)

</td>
<td width="33%" valign="top">

### 🎯 Long Term (Q3 2027 upward)
&nbsp;
- [ ] Formalised conformity reasoning
- [ ] AI integration
- [ ] Optimisation and performance

</td>
</tr>
</table>

---
## ⚠️ Maturity & Production Readiness

CRANE is **beta software** currently used in real compliance engagements. **Core modules are stable and production-ready:**
- Product registry, SBOM analysis, vulnerability tracking, audit logs, release gates

**Some advanced features are still evolving:**
- Substantial change assessment, automated integrations, advanced reporting

**Before deploying to production:**
- Review the [Installation Guide](INSTALLATION.md) thoroughly
- Use [`docker-compose.prod.yml`](docker-compose.prod.yml) — **never use `docker-compose.yml` in production**
- Set strong database and secret key values (see [.env.example](.env.example))
- Run behind a reverse proxy with TLS (nginx, Caddy, etc.)
- Regularly apply security updates to OS and dependencies
- Have a backup and recovery procedure in place

**Not recommended for:** Fully unattended production use without a designated operator. Plan for at least one person to monitor logs and handle database migrations during upgrades.

---

## Contact

- **Issues & feature requests:** [GitHub Issues](https://github.com/cra-norm-engine/crane/issues)
- **Security vulnerabilities:** See [SECURITY.md](SECURITY.md)
- **General enquiries:** cra.norm.engine@gmail.com

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). Please open an issue before submitting a PR for significant changes.

## License

[GNU Affero General Public License v3.0](LICENSE)
