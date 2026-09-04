# CRANE

<div align="center">

# The Open-Source Cyber Resilience Act (CRA) Compliance Platform

**Stop managing CRA compliance with spreadsheets.**

Track Products • Analyze SBOMs • Manage Vulnerabilities • Manage Tasks • Collect Evidence • Pass Audits

Built for **manufacturers**, **software vendors**, **consultants**, **startups**, and **researchers**.

![License](https://img.shields.io/badge/license-AGPL--3.0-green)
![Python](https://img.shields.io/badge/python-3.12-blue)
![Vue](https://img.shields.io/badge/vue-3-brightgreen)
![Docker](https://img.shields.io/badge/docker-compose-blue)
![Status](https://img.shields.io/badge/status-beta-orange)
![CI](https://img.shields.io/github/actions/workflow/status/cra-norm-engine/crane/ci.yml?branch=main)

### 🚀 Open Source • 🔒 Self Hosted • 🇪🇺 CRA Ready • 📦 SBOM Native • 🛡️ Privacy First

</div>

---

# Why CRANE?

The **EU Cyber Resilience Act (CRA)** introduces a new era of cybersecurity requirements for digital products.

CRANE transforms CRA compliance from scattered spreadsheets, documents, and disconnected tools into **one integrated platform**.

Instead of juggling:

- 📄 Word documents
- 📊 Excel sheets
- 🔍 Vulnerability scanners
- 📁 Evidence folders
- ✅ Release checklists

CRANE centralizes everything in a single, auditable workspace.

---

# 📸 Dashboard

![CRANE Dashboard](.github/assets/Main_dashboard.png)

---

# ✨ Why Choose CRANE?

| Traditional Compliance Tools | CRANE |
|------------------------------|-------|
| 💰 Expensive enterprise licenses | ✅ Completely Open Source |
| ☁ Vendor cloud | ✅ Self-hosted |
| 🔒 Vendor lock-in | ✅ Your data stays yours |
| 📄 Documents everywhere | ✅ One integrated workspace |
| ❌ Generic GRC software | ✅ Built specifically for CRA |
| 📦 Multiple disconnected tools | ✅ Everything in one platform |

---

# 🚀 Everything You Need for CRA Compliance

CRANE provides a complete workflow for the Cyber Resilience Act.

- 📦 Product Registry
- 🏷️ Version & Release Management
- 📋 SBOM Analysis (CycloneDX & SPDX)
- 🛡️ Vulnerability Management
- 📈 EPSS Risk Prioritization
- ✅ CRA Compliance Matrix
- 📝 Audit Trail
- 🚦 Release Gates
- ⚠️ Risk Assessments
- 📂 Evidence Repository
- 👥 Team Collaboration
- 🔐 LDAP / Active Directory Integration
- ✅ Task board with assignment, parent/subtask links, comments, history, and archive tracking
- 🔗 Jira Cloud integration with OAuth, issue export, status synchronization, and board-level sync
- 🖼️ Personal profile photos shown on task assignments

---

# 📦 Product Inventory

Comprehensive overview of products, releases, lifecycle, and CRA-related information.

![Product Inventory](.github/assets/productInventory.png)

---

# 🎯 Built For

| Audience | Benefits |
|-----------|----------|
| 🏭 Manufacturers | Manage CRA compliance across product portfolios |
| 💻 Software Vendors | Track releases, SBOMs, vulnerabilities, and evidence |
| 🚀 IoT Startups | Affordable alternative to enterprise GRC platforms |
| 👨‍💼 CRA Consultants | Deploy isolated environments for each customer |
| 🎓 Universities & Research | Ideal for teaching and CRA research |
| 🏛 Critical Infrastructure | Fully self-hosted with enterprise authentication |

---

# ⚡ Key Features

| Feature | Description |
|---------|-------------|
| 📦 Product Registry | Products, versions, releases, lifecycle management |
| 📋 SBOM Analysis | CycloneDX, SPDX, NTIA validation, quality scoring |
| 🛡️ Vulnerability Management | CVEs, EPSS, VEX assessments, patch workflow |
| 🚦 Release Gates | Evidence-based release approval |
| 🇪🇺 CRA Compliance Matrix | Annex I requirement mapping |
| 📝 Audit Trail | Immutable compliance history |
| ⚠️ Risk Assessment | STRIDE & TARA methodology support |
| 👥 Collaboration | Role-based access, tasks, comments |
| 🔐 LDAP / Active Directory | Enterprise authentication |
| ✅ Task management | Jira-style board, drag-and-drop status, assignees, parent/subtasks, comments, and history |
| 🔗 Jira Cloud | OAuth connection, configurable projects/statuses/priorities, issue export and synchronization |
| 📦 Data Export | Portable compliance packages with zero vendor lock-in |

---

# 🔒 Privacy First

Unlike cloud-first compliance platforms, CRANE keeps **everything under your control**.

✅ Self-hosted

✅ No telemetry

✅ No vendor lock-in

✅ No external callbacks

✅ PostgreSQL database under your control

✅ Fully auditable

Your compliance data **never leaves your infrastructure**.

---

# 🌍 Online Demo

Try CRANE instantly without installing anything.

### 🌐 https://cra-compliance-tool-1.onrender.com

| Demo Account | |
|--------------|----------------|
| Email | `crane@cra-norm-engine.com` |
| Password | `8hARz]9$]>r3Tn` |

> ⚠️ **Please do not upload confidential or sensitive information into the public demo.**

---

# 💬 Free CRA Consultation

Every **Friday**, I offer **free consultations** focused on the Cyber Resilience Act.

We can discuss:

- CRA Questions & Answers
- Compliance Strategy
- Gap Assessment
- Product Readiness
- How CRANE fits your workflow

📅 Schedule your session:

👉 https://cal.com/crane-2027/30min

Or connect on LinkedIn:

👉 https://www.linkedin.com/in/ali-m-hosseini-216b24121/

---

# ⚡ Installation

## Prerequisites

- Docker Desktop installed
- Docker running with Linux containers
- Approximately 2 GB free disk space

## One-Command Installation

### Linux / macOS

```bash
curl -fsSL https://raw.githubusercontent.com/cra-norm-engine/crane/main/install.sh | bash
```

### Windows (PowerShell)

```powershell
irm https://raw.githubusercontent.com/cra-norm-engine/crane/main/install.ps1 | iex
```

For a detailed guide, see the documentation:

👉 https://cra-norm-engine.github.io/crane/installation.html

---

# 🚀 Access CRANE

| Service | URL |
|----------|-----|
| Web Application | http://localhost:5173 |
| REST API | http://localhost:8000/api/v1 |
| API Documentation | http://localhost:8000/docs |

---

# 🔑 Default Login

| Field | Value |
|--------|-------|
| Email | `admin@example.com` |
| Password | `admin1234` |

You'll be prompted to create a new password on first login.

---

# 🏢 Production Deployment

For production deployments:

- Use `docker-compose.prod.yml`
- Configure strong secrets
- Run behind HTTPS (NGINX, Caddy, Traefik, etc.)
- Regularly update dependencies
- Maintain database backups

Complete guide:

https://cra-norm-engine.github.io/crane/configuration.html

---

# 🛠️ Technology Stack

### Backend

- FastAPI
- SQLAlchemy 2
- PostgreSQL 16
- Alembic
- Pydantic v2

### Frontend

- Vue 3
- TypeScript
- Pinia
- Vite

### Security Intelligence

- Trivy
- NVD
- OSV
- EPSS (FIRST.org)

---

# 🗺️ Roadmap

## ✅ Delivered (September 2026)

- [x] Jira Cloud integration (OAuth, issue export, status synchronization, Forge issue panel)
- [x] Task board with Backlog, In progress, and Done / release columns
- [x] Drag-and-drop task status updates
- [x] Task assignment, parent/subtask links, comments, completion history, and archive tracking
- [x] Role-selectable `task_assign` permission
- [x] Personal profile photos for task assignees

## 🚀 Near Term (Q4 2026)

- [ ] CRA reporting obligations
- [ ] Release gates for exploitable vulnerabilities
- [ ] GitHub integration
- [ ] GitLab integration

---

## 📈 Medium Term (Q1 2027)

- [ ] CENELEC standards integration
- [ ] Security Development Lifecycle (SDL)

---

## 🎯 Long Term

- [ ] AI-assisted compliance
- [ ] Automated conformity reasoning
- [ ] Performance optimization
- [ ] Advanced reporting
- [ ] Automated integrations

---

# 🌍 Real-World Scenarios

See practical deployment examples:

https://cra-norm-engine.github.io/crane/scenarios.html

- 🏭 Industrial Manufacturer
- 💡 IoT Startup
- 👨‍💼 CRA Consultant
- 🎓 Education & Research

---

# 🤝 Contributing

Contributions are welcome!

Whether you're fixing bugs, improving documentation, or implementing new features, we'd love your help.

Before opening a large Pull Request, please create an issue to discuss your proposal.

See:

**CONTRIBUTING.md**

---

# 📬 Contact

- 🐞 Issues & Feature Requests: https://github.com/cra-norm-engine/crane/issues
- 🔒 Security Reports: SECURITY.md
- 📧 Email: amh1036@yahoo.com

---

# 📜 License

Copyright © 2026 **Ali Mohammad Hosseini**

Licensed under the **GNU Affero General Public License v3.0 (AGPL-3.0).**

CRANE is network server software covered by the AGPL. If you modify and deploy CRANE over a network, you must make the corresponding source code available under the terms of the license.

---

<div align="center">

## ⭐ If CRANE helps your organization, consider giving the project a Star!

**Helping the open-source community build a safer digital future under the EU Cyber Resilience Act.**

Made with ❤️ for the cybersecurity and open-source community.

</div>
