# CRA Compliance Tool

> **Self-hosted, open-source compliance management platform for manufacturers of products with digital elements under the EU Cyber Resilience Act (CRA).**

---

```
  ██████╗██████╗  █████╗      ████████╗ ██████╗  ██████╗ ██╗
 ██╔════╝██╔══██╗██╔══██╗     ╚══██╔══╝██╔═══██╗██╔═══██╗██║
 ██║     ██████╔╝███████║        ██║   ██║   ██║██║   ██║██║
 ██║     ██╔══██╗██╔══██║        ██║   ██║   ██║██║   ██║██║
 ╚██████╗██║  ██║██║  ██║        ██║   ╚██████╔╝╚██████╔╝███████╗
  ╚═════╝╚═╝  ╚═╝╚═╝  ╚═╝        ╚═╝    ╚═════╝  ╚═════╝ ╚══════╝

  Compliance Management Platform  ·  EU Cyber Resilience Act
```

---

## Why this exists

The EU Cyber Resilience Act mandates that manufacturers of products with digital elements demonstrate continuous cybersecurity compliance — covering vulnerability management, SBOM generation, lifecycle notifications, risk assessments, and more. Existing tools are generic, expensive, or proprietary.

This tool is built by a product security engineer who lives this problem daily. It is open source, self-hosted, and designed to be actually useful rather than checkbox theatre.

---

## Feature Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                     CRA COMPLIANCE TOOL                         │
├─────────────────┬─────────────────┬─────────────────────────────┤
│  Product        │  Security       │  Compliance                 │
│  Management     │  Operations     │  Evidence                   │
├─────────────────┼─────────────────┼─────────────────────────────┤
│  Risk &         │  Vulnerability  │  Platform                   │
│  Assessment     │  Handling       │  Administration             │
└─────────────────┴─────────────────┴─────────────────────────────┘
```

---

## Modules

### 📦 Product Management

```
Products ──► Releases ──► Release Gates ──► Artifacts
   │             │              │
   │             │         Gate Items (SBOM, pentest,
   │             │         risk assessment, etc.)
   │             │
   └─────────────┴──► Support Periods ──► Lifecycle Alerts
```

- **Product inventory** — manage products, versions, manufacturers, categories, and intended purpose
- **Release management** — version lifecycle tracking with release status (draft → released → recalled)
- **Release gate workflow** — structured readiness checklist before a release ships; attach and review evidence artifacts per gate item
- **Artifact management** — upload, version, and link evidence files (SBOMs, test reports, pentest results) to releases
- **Support periods** — define start/end of active support per release

---

### 🛡️ SBOM Analyzer

```
Upload SBOM ──► sbom-tools CLI ──► Analysis Results
     │               │
     │          ┌────┴─────────────────────┐
     │          │  Quality score (0–100)   │
     │          │  CRA Phase 2 validation  │
     │          │  NTIA minimum elements   │
     │          │  Recommendations         │
     │          └──────────────────────────┘
     │
     └──► Auto-import from release gate artifact
          Differential analysis vs previous SBOM
```

- **Automated analysis** via [sbom-tools](https://github.com/sbom-tool/sbom-tools) Rust CLI
- **Quality scoring** (0–100, graded A–F) with prioritised improvement recommendations
- **CRA Phase 2** compliance validation (EU Cyber Resilience Act Annex I Part II §1)
- **NTIA Minimum Elements** validation (7 required data fields)
- **Differential analysis** — automatically compares new SBOM against previous version; shows added, removed, and changed components
- **Auto-import** from release gate artifacts — no double upload needed
- Supports **CycloneDX** (JSON 1.4–1.7) and **SPDX** (JSON 2.2–3.0)

---

### 🔒 Security Operations

```
Security Advisories ──► CVE tracking, affected versions, patches
Security Updates     ──► Update history per product release
CVD Policies         ──► Coordinated vulnerability disclosure policy
Vulnerability Reports──► Incoming report intake and triage
PSIRT Workflow       ──► Internal handling, severity, remediation
```

- **Security advisories** — publish and track CVEs affecting your products
- **Security update history** — record updates issued per release, CVEs addressed, distribution mechanism
- **CVD policies** — define and publish your coordinated vulnerability disclosure policy (CRA Annex I requirement)
- **Vulnerability reports** — manage incoming reports from researchers and customers
- **PSIRT workflow** — internal vulnerability handling from report to fix

---

### 📋 CRA Essential Requirements

```
CRA Annex I Requirements
        │
        ├── Requirement coverage map
        ├── Per-product compliance status
        └── Evidence linking
```

- Visual **requirement coverage matrix** mapping CRA Annex I obligations to your products
- Filter by product to see which requirements are met, partially met, or open
- Links compliance evidence directly to specific requirements

---

### ⚠️ Risk Assessment

```
Assessment ──► Risk Items ──► Severity + Likelihood ──► Mitigation
    │
    └──► Methodology (STRIDE, TARA, custom)
         Version tracking
         Approval workflow
```

- Structured **cybersecurity risk assessments** per product and release
- Multiple methodology support (STRIDE, TARA, custom)
- Risk item tracking with severity, likelihood, and mitigation actions
- Version-controlled assessments with approval status

---

### 🔔 Lifecycle Alerts

```
Support Periods ──► EOS analysis ──► Alerts
                         │
                    Threshold filters:
                    < 30 days / < 3 months /
                    < 6 months / < 1 year /
                    Expired
```

- **End-of-Support (EOS) analysis** across all products
- Configurable threshold alerts (30 days, 3 months, 6 months, 1 year)
- Filters by EOS state, classification, and search
- Manual EOS check trigger

---

### 📜 Certification Records

Track third-party certifications and conformity assessments:
- Certificate type, issuing body, validity period
- Linked to specific product releases
- Expiry tracking

---

### 🔄 Substantial Changes

CRA Article 3(4) requires manufacturers to assess whether product modifications constitute a "substantial change" requiring re-conformity assessment:

- Record and categorise changes (feature, security, repair, maintenance)
- Assess substantiality with documented rationale
- Status workflow (draft → submitted → assessed → closed)
- Linked to specific product releases

---

### 📊 Dashboard

```
┌──────────────┬──────────────┬──────────────┬──────────────┐
│   Products   │   Releases   │ Open Vulns   │  SBOM Score  │
├──────────────┴──────────────┴──────────────┴──────────────┤
│          Compliance status overview                        │
│          Recent activity feed                              │
│          Tasks requiring attention                         │
└────────────────────────────────────────────────────────────┘
```

---

### 🏢 Support Hub

CRA-oriented tools for customer support teams:
- Product support lookup by product code or customer
- EOS watchlist for at-risk customers
- CVE lookup by product

---

### 🗃️ Data Export / Import

- Full data export for backup and migration
- Import from external sources
- Works with the self-hosted model — your data is always portable

---

### 👥 Platform Administration

```
Users ──► Roles ──► Permissions
  │
  ├── Local authentication (email + password)
  ├── LDAP / Active Directory integration
  ├── Force password change on next login
  └── Account activation / deactivation
```

- **Role-based access control** — define custom roles with granular permissions
- **User management** — invite users, assign roles, manage account status
- **LDAP integration** — plug into your existing Active Directory or OpenLDAP
- **Audit history** — immutable, timestamped log of every action in the platform

---

## Tech Stack

```
┌──────────────────────────────────────────────────────┐
│  Frontend                                            │
│  Vue 3 · TypeScript · Pinia · Vue Router · Axios    │
├──────────────────────────────────────────────────────┤
│  Backend                                             │
│  FastAPI · SQLAlchemy 2.x · Pydantic v2 · Alembic   │
├──────────────────────────────────────────────────────┤
│  Database                                            │
│  PostgreSQL 16                                       │
├──────────────────────────────────────────────────────┤
│  Analysis                                            │
│  sbom-tools (Rust CLI) — quality + CRA validation   │
├──────────────────────────────────────────────────────┤
│  Infrastructure                                      │
│  Docker · Docker Compose                             │
└──────────────────────────────────────────────────────┘
```

---

## Quick Start

### Prerequisites
- Docker and Docker Compose
- Git

### 1. Clone the repository

```bash
git clone https://github.com/yourrepo/cra-compliance-tool.git
cd cra-compliance-tool
```

### 2. Configure environment

```bash
cp .env.example .env
```

Edit `.env` and set at minimum:

```env
BACKEND_SECRET_KEY=your-secret-key-min-32-chars
POSTGRES_PASSWORD=your-db-password
```

### 3. Start the stack

```bash
docker compose up -d
```

### 4. Access the tool

| Service  | URL                         |
|----------|-----------------------------|
| Frontend | http://localhost:5173       |
| API      | http://localhost:8000/api/v1|
| API Docs | http://localhost:8000/docs  |

---

## Project Structure

```
cra-compliance-tool/
├── backend/
│   ├── app/
│   │   ├── api/routes/       # FastAPI route handlers
│   │   ├── models/           # SQLAlchemy ORM models
│   │   ├── repositories/     # Database access layer
│   │   ├── schemas/          # Pydantic request/response schemas
│   │   ├── services/         # Business logic
│   │   └── core/             # Config, security, database, audit
│   ├── alembic/              # Database migrations
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── views/            # Page components
│   │   ├── components/       # Shared UI components
│   │   ├── services/         # API client services
│   │   ├── stores/           # Pinia state stores
│   │   └── types/            # TypeScript type definitions
│   └── package.json
├── docker-compose.yml
├── .env.example
└── README.md
```

---

## CRA Coverage

| CRA Obligation | Covered by |
|---|---|
| Annex I Part I — Security requirements | Risk assessments, PSIRT workflow, CVD policy |
| Annex I Part II §1 — SBOM | SBOM analyzer with CRA Phase 2 validation |
| Annex I Part II §2 — Vulnerability handling | Security advisories, vulnerability reports |
| Annex I Part II §3 — CVD policy | CVD policies module |
| Annex I Part II §4 — Security updates | Security update history |
| Article 3(4) — Substantial changes | Substantial changes module |
| Article 13 — Lifecycle notifications | Lifecycle alerts, support periods |
| Annex II — Technical documentation | Certification records, release gate evidence |

---

## Authentication

- **Local accounts** — email and password, bcrypt hashed
- **LDAP / Active Directory** — JIT provisioning on first login
- **JWT** — short-lived access tokens + refresh token rotation
- **Forced password change** — flag users to change password on next login
- **Immutable audit log** — every login, change, and deletion is recorded

---

## Self-Hosted by Design

Your compliance data never leaves your infrastructure:

- All data stored in your own PostgreSQL instance
- SBOM files stored on your own filesystem
- No telemetry, no callbacks, no external dependencies at runtime
- Full data export at any time
- Open source — audit the code, fork it, extend it

---

## Roadmap

- [ ] PDF compliance report export (Notified Body audit package)
- [ ] Self-service registration with demo workspaces
- [ ] GitHub / Google OAuth
- [ ] Email-based password reset
- [ ] Jira / GitHub Issues integration for vulnerability tracking
- [ ] Multi-tenant support
- [ ] Railway sector overlay (NIS2, CENELEC EN 50128/50657)

---

## Contributing

Contributions are welcome. Please open an issue before submitting a pull request for significant changes.

---

## License

[MIT](LICENSE)

---

> Built by a product security engineer working in critical infrastructure.  
> CRA compliance is hard. This tool tries to make it less hard.
