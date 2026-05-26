# CRA Demo Data — Products 02–10

> Products 02–10 each focus on a distinct CRA edge case or scenario type.
> Field names and enum values match the tool schema exactly.
> Product 01 (MillGuard MC-400) is in `demo-data-product-01.md`.

---

## Scenario Map

| # | Product | Class | Primary Scenario |
|---|---|---|---|
| 01 | MillGuard MC-400 | Important I | Vuln patch (not substantial) → cloud module (substantial) |
| **02** | SafeLogic SL-Pro | **Critical** | Notified-body mandatory, 20-year support, credential theft → remote diagnostics substantial |
| **03** | NetMonitor Pro | Important II | Pure software fully in CRA scope — transitive dependency CVE fleet-wide |
| **04** | NetMonitor Agent | Default | SaaS out of scope / downloadable agent in scope — scope split |
| **05** | PackFlow P-200 | Normal | Supplier insolvency forces emergency PLC swap — SBOM + conformity refresh |
| **06** | MoldMaster IM-1200 | Normal → Important I | Mid-lifecycle reclassification triggers re-conformity |
| **07** | FleetManager Mobile | Default | Mobile app in scope — OAuth vuln, app-store enforcement post-2027 |
| **08** | EdgeVision EV-Cluster | Important I (×2) | Composite distributed product — per-component CRA scoping |
| **09** | MC-Platform + Apps | Important I / Default | Parent/child product family — marketplace governance |
| **10** | EcoMeter EM-3 | Important I | Pre-CRA exemption → substantial modification ends exemption (Art. 69(2)) |

---

---

## Product 02 — SafeLogic SL-Pro

> **Scenario:** Critical-class safety PLC. Notified-body conformity mandatory. Credential theft → security patch (not substantial). Remote IP diagnostics added in v2.0 → substantial modification, new notified-body cycle.

### Product

| Field | Value |
|---|---|
| `name` | SafeLogic SL-Pro |
| `product_code` | SL-PRO-SIL3 |
| `manufacturer_name` | Axiom Safety Systems BV |
| `product_type` | SIL-3 programmable safety controller |
| `current_classification` | `critical` |
| `intended_use` | SIL-3 safety logic execution for emergency stop, safety interlock, and process shutdown systems in chemical, oil & gas, and heavy manufacturing. Engineering interface via dedicated workstation over isolated Ethernet. |
| `is_pre_cra` | `false` |
| `first_placed_on_market_date` | 2027-01-20 |
| `eu_doc_notified_body` | TÜV Rheinland (NB 0035) |

---

### Releases

#### v1.0 — Initial placement (notified body)

| Field | Value |
|---|---|
| `system_version` | 1.0.0 |
| `release_status` | `placed_on_market` |
| `placed_on_market_date` | 2027-01-20 |
| `conformity_route_snapshot` | `third_party_assessment` |
| `eu_doc_date` | 2027-01-10 |
| `eu_doc_number` | DOC-SLPRO-2027-001 |
| `eu_doc_notified_body` | TÜV Rheinland (NB 0035) — Certificate TÜV-NB-2027-SL-4421 |
| `release_notes` | First CRA-conformant release. Hardware root-of-trust, signed safety logic, IEC 62443-4-1 SDLC. Notified-body technical file audit completed Jan 2027. |

**Gate items (v1.0):**

| Gate item | Status | Notes |
|---|---|---|
| `technical_documentation` | pass | Full IEC 62443-4-2 + CRA Annex VII technical file |
| `risk_assessment` | pass | TARA methodology; SIL-3 cybersecurity case |
| `sbom` | pass | SPDX 2.3; hardware and firmware components |
| `test_report` | pass | Notified-body functional safety + cybersecurity test report |
| `declaration_of_conformity` | pass | Signed by TÜV Rheinland 2027-01-10 |
| `annex_mapping` | pass | All Annex I requirements mapped with notified-body annotations |

---

#### v1.1 — Credential theft patch

| Field | Value |
|---|---|
| `system_version` | 1.1.0 |
| `release_status` | `placed_on_market` |
| `placed_on_market_date` | 2029-11-08 |
| `conformity_route_snapshot` | `third_party_assessment` |
| `eu_doc_date` | 2029-11-05 |
| `eu_doc_number` | DOC-SLPRO-2029-002 |
| `release_notes` | Mandatory MFA enforcement on engineering workstation interface after confirmed credential theft incident (2029-10-14). Private key rotation. No new functionality. |
| `parent_release_id` | → v1.0 |

**Substantial modification assessment (v1.1):**

| Criterion | Value | Reasoning |
|---|---|---|
| `alters_intended_use` | `false` | Safety logic execution unchanged |
| `introduces_new_threat_vectors` | `false` | MFA closes an existing attack path; no new surface |
| `enables_new_attack_scenarios` | `false` | — |
| `changes_attack_likelihood` | `false` | Likelihood decreases (credential reuse eliminated) |
| `changes_attack_impact` | `false` | — |
| `is_substantial` | **`false`** | Security hardening only. Not a substantial modification. |
| `reasoning` | Response to confirmed credential theft in a customer deployment. Mandates TOTP MFA on engineering workstation login. No change to safety-logic interface, communication protocols, or attack surface topology. |

---

#### v2.0 — Remote IP diagnostics (substantial modification)

| Field | Value |
|---|---|
| `system_version` | 2.0.0 |
| `release_status` | `placed_on_market` |
| `placed_on_market_date` | 2032-03-10 |
| `conformity_route_snapshot` | `third_party_assessment` |
| `eu_doc_date` | 2032-02-28 |
| `eu_doc_number` | DOC-SLPRO-2032-003 |
| `eu_doc_notified_body` | TÜV Rheinland (NB 0035) — Certificate TÜV-NB-2032-SL-7703 |
| `release_notes` | Optional remote diagnostics channel over TLS 1.3 TCP/IP for authorised service engineers. Previously air-gapped design; this introduces a network interface for the first time. Full notified-body re-assessment completed. |
| `parent_release_id` | → v1.1 |

**Substantial modification assessment (v2.0):**

| Criterion | Value | Reasoning |
|---|---|---|
| `alters_intended_use` | `false` | Safety logic execution unchanged |
| `introduces_new_threat_vectors` | **`true`** | New IP-accessible service interface — entirely absent in v1.x air-gapped design |
| `enables_new_attack_scenarios` | **`true`** | Network reachable service engineer channel creates remote code execution attack path if compromised |
| `changes_attack_likelihood` | **`true`** | Air-gapped → network-connected is a categorical likelihood increase |
| `changes_attack_impact` | **`true`** | Remote attacker can now target safety logic directly over the network |
| `is_substantial` | **`true`** | All four §103 criteria met — substantial modification. New notified-body cycle required. |
| `reasoning` | Introduction of the first IP-accessible interface on a previously air-gapped Critical-class safety controller constitutes a substantial modification. The entire cybersecurity case must be rewritten. New TÜV Rheinland assessment commissioned and completed before release. New EU DoC issued. |

---

### Security Update

**SU-001 — Credential theft response patch**

| Field | Value |
|---|---|
| `title` | Enforce MFA on engineering workstation interface |
| `severity` | `high` |
| `cvss_score` | 7.4 |
| `cves_addressed_json` | `[]` |
| `description` | Incident confirmed Oct 2029: attacker obtained engineering credentials via phishing and logged into safety controller workstation. Patch mandates TOTP MFA; invalidates all existing long-lived session tokens. |
| `vulnerability_discovered_at` | 2029-10-14 |
| `remediation_deadline` | 2029-11-14 |
| `released_at` | 2029-11-08 |
| `distribution_mechanism` | `field_service` |
| `is_security_only` | `true` |

---

### Support Period

| Field | Value |
|---|---|
| `support_type` | `extended` |
| `support_start_date` | 2027-01-20 |
| `support_end_date` | 2047-01-20 |
| `notify_before_days` | 730 |
| `justification_text` | 20-year support commitment matching IEC 62443 guidance for Critical-class safety instrumented systems. Chemical and oil & gas plant lifecycles routinely exceed 20 years. SIL-3 controller replacement requires full safety re-validation. |
| `user_facing_summary` | Axiom Safety Systems commits to security patches for SafeLogic SL-Pro through 20 January 2047. Critical vulnerabilities will be patched within 14 days. End-of-support notice issued no less than 24 months in advance. |

---

### Key Milestones

| Date | Event | CRA / IEC 62443 trigger |
|---|---|---|
| 2026-06 | Notified-body pre-assessment engagement | Critical class — NB mandatory |
| 2027-01-10 | TÜV Rheinland DoC signed | Art. 28 + third-party assessment |
| 2027-01-20 | v1.0 placed on market | Art. 3(20) |
| 2027-09-11 | CRA enforcement; Critical-class scrutiny | Full technical file reviewed by NB |
| 2029-10-14 | Engineering credential theft confirmed | Art. 14 — ENISA notification; Art. 13(7) incident documentation |
| 2029-11-08 | v1.1 MFA patch released | Annex I Part II §8 — timely remedy |
| 2032-03-10 | v2.0 with remote diagnostics — new NB DoC | Art. 3(30) substantial + new notified-body cycle |
| 2045-01-20 | EOS notification (730 days ahead) | Art. 13(7) lifecycle communication |
| 2047-01-20 | End of support | 20-year commitment honoured |

---
---

## Product 03 — NetMonitor Pro

> **Scenario:** On-premises network monitoring + IDS software. **No hardware.** Important Class II
> (network management / intrusion detection = listed category). Demonstrates that pure software is
> fully in CRA scope. A Log4j-style transitive dependency CVE hits the entire installed base simultaneously.

### Product

| Field | Value |
|---|---|
| `name` | NetMonitor Pro |
| `product_code` | NMP-SOFT |
| `manufacturer_name` | Vigilant Software Ltd |
| `product_type` | On-premises network security monitoring and intrusion detection software |
| `current_classification` | `important_class_2` |
| `intended_use` | Network traffic analysis, anomaly detection, and intrusion detection for enterprise and industrial networks. Installed on customer-managed servers; no cloud component shipped. Connects to all monitored network segments. |
| `is_pre_cra` | `false` |
| `first_placed_on_market_date` | 2026-12-01 |

> **Note for demo:** This product has no hardware. When entering in the tool, leave all hardware-specific fields blank. CRA applies to software placed on the EU market as fully as to any hardware product.

---

### Releases

#### v4.0 — First CRA-conformant version

| Field | Value |
|---|---|
| `system_version` | 4.0.0 |
| `release_status` | `placed_on_market` |
| `placed_on_market_date` | 2026-12-01 |
| `conformity_route_snapshot` | `third_party_assessment` |
| `eu_doc_date` | 2026-11-18 |
| `eu_doc_number` | DOC-NMP-2026-001 |
| `release_notes` | First release under CRA. Notified-body conformity assessment for Important Class II software. SBOM covers all OSS dependencies including transitive. CVD program published at security.vigilantsoftware.eu. |

---

#### v4.1 — Transitive dependency CVE (Log4j-style)

| Field | Value |
|---|---|
| `system_version` | 4.1.0 |
| `release_status` | `placed_on_market` |
| `placed_on_market_date` | 2027-05-19 |
| `conformity_route_snapshot` | `third_party_assessment` |
| `eu_doc_date` | 2027-05-17 |
| `eu_doc_number` | DOC-NMP-2027-002 |
| `release_notes` | Emergency patch for CVE-2027-11204 (RCE in jackson-databind 2.14.x — a transitive dependency of the analytics engine). All v4.0 installations affected. 24-hour ENISA early warning filed. Patch released within 48 hours of CVE publication. |
| `parent_release_id` | → v4.0 |

**Substantial modification assessment (v4.1):**

| Criterion | Value | Reasoning |
|---|---|---|
| `alters_intended_use` | `false` | Same detection and monitoring functions |
| `introduces_new_threat_vectors` | `false` | Removes vuln; adds no new interfaces |
| `enables_new_attack_scenarios` | `false` | — |
| `changes_attack_likelihood` | `false` | Likelihood reduced |
| `changes_attack_impact` | `false` | — |
| `is_substantial` | **`false`** | Pure security patch of a transitive OSS dependency. Not substantial. |
| `reasoning` | jackson-databind upgraded from 2.14.2 → 2.15.4 to remediate CVE-2027-11204. No functional change, no new interfaces, no new data flows. Transitive dependency patch does not alter the product's threat surface topology. |

---

#### v5.0 — Major version with new detection engine

| Field | Value |
|---|---|
| `system_version` | 5.0.0 |
| `release_status` | `placed_on_market` |
| `placed_on_market_date` | 2030-11-10 |
| `conformity_route_snapshot` | `third_party_assessment` |
| `eu_doc_date` | 2030-11-01 |
| `eu_doc_number` | DOC-NMP-2030-003 |
| `release_notes` | New ML-based detection engine with active response module. Active response introduces outbound network actions (blocking, quarantine) — new capability not present in v4.x. Full re-conformity cycle. v4.x enters extended security-only support. |
| `parent_release_id` | → v4.1 |

**Substantial modification assessment (v5.0):**

| Criterion | Value | Reasoning |
|---|---|---|
| `alters_intended_use` | **`true`** | v4.x was passive monitoring only; v5.0 can actively block traffic and quarantine endpoints — fundamentally different intended use |
| `introduces_new_threat_vectors` | **`true`** | Active response module creates new outbound network actions that could be abused or misdirected |
| `enables_new_attack_scenarios` | **`true`** | Attacker controlling detection logic could use active response to disrupt legitimate network traffic |
| `changes_attack_likelihood` | **`true`** | Elevated privilege + active network access increases attractiveness as attack target |
| `changes_attack_impact` | **`true`** | Compromised active response = network disruption, not just data exfiltration |
| `is_substantial` | **`true`** | All five criteria met. Full re-conformity. New notified-body assessment. |
| `reasoning` | Addition of active response capability (traffic blocking, endpoint quarantine) fundamentally changes both the intended use and the cybersecurity risk profile. This is a new product generation, not an incremental update. |

---

### Security Update

**SU-001 — CVE-2027-11204 (jackson-databind RCE)**

| Field | Value |
|---|---|
| `title` | Remote code execution in jackson-databind transitive dependency |
| `severity` | `critical` |
| `cvss_score` | 9.8 |
| `cves_addressed_json` | `["CVE-2027-11204"]` |
| `description` | Critical RCE in jackson-databind 2.14.x via polymorphic type handling. Attacker sending crafted JSON to the analytics API endpoint achieves arbitrary code execution as the monitoring service user. All v4.0 installations affected. |
| `vulnerability_discovered_at` | 2027-05-17 |
| `remediation_deadline` | 2027-06-17 |
| `released_at` | 2027-05-19 |
| `distribution_mechanism` | `package_repository` |
| `is_security_only` | `true` |
| `affected_versions_json` | `["4.0.0"]` |

> **Demo note:** When this security update is created, a lifecycle notification is automatically generated for all support period recipients.

---

### Support Period

| Field | Value |
|---|---|
| `support_type` | `standard` |
| `support_start_date` | 2026-12-01 |
| `support_end_date` | 2033-12-01 |
| `notify_before_days` | 180 |
| `justification_text` | 7-year support per major version. v4.x enters CVE-only extended support from v5.0 release date (2030-11-10). Active development focused on v5.x. |

---

### Key Milestones

| Date | Event | CRA trigger |
|---|---|---|
| 2026-11 | Notified-body assessment (Important Class II — mandatory) | Class II requirement |
| 2026-12-01 | v4.0 placed on market | Art. 3(20) — software product |
| 2027-05-17 | CVE-2027-11204 published (transitive OSS dependency) | Art. 14 — 24h ENISA early warning filed |
| 2027-05-19 | v4.1 patch released within 48h | Annex I Part II §8 |
| 2027-09-11 | CRA enforcement — software-only product fully in scope | No hardware exemption |
| 2030-11-10 | v5.0 — active response → substantial modification | Art. 3(30) + new notified-body cycle |
| 2033-12-01 | v4.x end-of-support | Migration tooling provided |

---
---

## Product 04 — NetMonitor Agent *(+ out-of-scope SaaS context)*

> **Scenario:** Same vendor as Product 03 launches a SaaS variant. The SaaS backend is **out of CRA
> scope** (no product placed on market — it's a service). However, the customer-installed
> **on-premises agent** that ships with the SaaS subscription **is a CRA product** on its own.
> This creates a scope split inside one product family.

### Product A — NetMonitor Cloud *(out of scope — for context only)*

| Field | Value |
|---|---|
| `name` | NetMonitor Cloud |
| `product_code` | NMC-SAAS |
| `CRA status` | **OUT OF SCOPE** — pure multi-tenant SaaS accessed via browser; no software is placed on market |
| `Applicable regime` | NIS2 (as digital service provider), GDPR |
| `Note` | A SaaS incident (2029-11) triggers **NIS2 incident reporting**, NOT CRA Article 14 notification |

> Do not create this as a CRA product in the tool. It exists in this document only to illustrate the scope boundary.

---

### Product B — NetMonitor Agent *(in scope — enter this one)*

| Field | Value |
|---|---|
| `name` | NetMonitor Agent |
| `product_code` | NMA-AGENT |
| `manufacturer_name` | Vigilant Software Ltd |
| `product_type` | On-premises data collection and forwarding agent for NetMonitor Cloud |
| `current_classification` | `normal` |
| `intended_use` | Lightweight agent installed on customer-managed servers and endpoints. Collects network telemetry and forwards it to the NetMonitor Cloud SaaS backend over TLS 1.3. Default class — no intrusion detection or active response function. |
| `is_pre_cra` | `false` |
| `first_placed_on_market_date` | 2028-03-01 |

> **Key teaching point:** The SaaS backend is out of scope. This agent — downloaded and installed by customers — **is a CRA product with its own DoC, SBOM, and vulnerability handling obligations**, even though it only communicates with a SaaS backend.

---

### Releases

#### v1.0 — Initial agent release

| Field | Value |
|---|---|
| `system_version` | 1.0.0 |
| `release_status` | `placed_on_market` |
| `placed_on_market_date` | 2028-03-01 |
| `conformity_route_snapshot` | `self_assessment` |
| `eu_doc_date` | 2028-02-22 |
| `eu_doc_number` | DOC-NMA-2028-001 |
| `release_notes` | Initial agent release. TLS 1.3 with certificate pinning to NMC backend. Minimal attack surface: one outbound HTTPS connection, no listening ports. |

---

#### v1.2 — Third-party analytics SDK CVE

| Field | Value |
|---|---|
| `system_version` | 1.2.0 |
| `release_status` | `placed_on_market` |
| `placed_on_market_date` | 2029-09-14 |
| `conformity_route_snapshot` | `self_assessment` |
| `eu_doc_date` | 2029-09-12 |
| `eu_doc_number` | DOC-NMA-2029-002 |
| `release_notes` | Patch for CVE-2029-07331 in bundled analytics SDK. Memory corruption in JSON parsing. Not substantial — security-only fix. |
| `parent_release_id` | → v1.0 |

**Substantial modification assessment (v1.2):** `is_substantial = false` — security patch only, no new functionality or interfaces.

---

### Support Period

| Field | Value |
|---|---|
| `support_type` | `standard` |
| `support_start_date` | 2028-03-01 |
| `support_end_date` | 2033-03-01 |
| `notify_before_days` | 180 |
| `justification_text` | 5-year support for agent software. Tied to SaaS contract lifecycle. Users receive in-app update prompts. |

---

### Key Milestones

| Date | Event | CRA / NIS2 trigger |
|---|---|---|
| 2028-03-01 | Agent v1.0 placed on market | CRA Art. 3(20) — software product in scope |
| 2028-09 | Architecture documented: agent = CRA product, backend = NIS2 service | Scope decision recorded in technical file |
| 2029-09-14 | Agent v1.2 patches CVE-2029-07331 | Art. 14 — ENISA notification for agent vuln |
| 2029-11 | SaaS backend breach | **NIS2** incident report — NOT CRA Art. 14 |

---
---

## Product 05 — PackFlow P-200

> **Scenario:** Default-class packaging machine. PLC vendor declares end-of-product-line mid-support
> period. Emergency supplier swap required — SBOM refresh and conformity re-validation needed.
> Assessment shows supplier swap is NOT a substantial modification (same function, equivalent security posture).

### Product

| Field | Value |
|---|---|
| `name` | PackFlow P-200 |
| `product_code` | PF-P200 |
| `manufacturer_name` | FlowPack Machinery SpA |
| `product_type` | Form-fill-seal packaging line controller |
| `current_classification` | `normal` |
| `intended_use` | Control system for industrial form-fill-seal packaging lines. PROFINET connection to MES; remote diagnostics via per-session VPN. No safety function in the cyber path. |
| `is_pre_cra` | `false` |
| `first_placed_on_market_date` | 2026-11-14 |

---

### Releases

#### v1.0 — Initial placement

| Field | Value |
|---|---|
| `system_version` | 1.0.0 |
| `release_status` | `placed_on_market` |
| `placed_on_market_date` | 2026-11-14 |
| `conformity_route_snapshot` | `self_assessment` |
| `eu_doc_date` | 2026-11-05 |
| `eu_doc_number` | DOC-PFP200-2026-001 |
| `release_notes` | Initial CRA-conformant release. Remote diagnostics tunnel uses per-session certificates with time-boxed access (max 4 hours per session). Siemens S7-1500 PLC. |

---

#### v1.1 — Emergency PLC supplier swap

| Field | Value |
|---|---|
| `system_version` | 1.1.0 |
| `release_status` | `placed_on_market` |
| `placed_on_market_date` | 2028-09-22 |
| `conformity_route_snapshot` | `self_assessment` |
| `eu_doc_date` | 2028-09-18 |
| `eu_doc_number` | DOC-PFP200-2028-002 |
| `release_notes` | Emergency hardware revision. Siemens S7-1500 discontinued due to supply chain disruption (supplier insolvency, 2028-07). Replaced with Beckhoff CX5140 running equivalent ladder-logic program. SBOM fully updated. Functional equivalence validated. |
| `parent_release_id` | → v1.0 |

**Substantial modification assessment (v1.1):**

| Criterion | Value | Reasoning |
|---|---|---|
| `alters_intended_use` | `false` | Form-fill-seal control logic unchanged; same I/O map, same PROFINET topology |
| `introduces_new_threat_vectors` | `false` | Beckhoff CX5140 has equivalent or better security posture to S7-1500; same network interface count and protocol set |
| `enables_new_attack_scenarios` | `false` | No new protocols, no new network paths |
| `changes_attack_likelihood` | `false` | Security posture equivalent; no regression found in evaluation |
| `changes_attack_impact` | `false` | — |
| `is_substantial` | **`false`** | Hardware component replacement with functional and security equivalent. Not substantial. |
| `reasoning` | Supplier swap driven by external supply chain event. The replacement PLC (Beckhoff CX5140) was evaluated against the same threat model as the S7-1500. No new network interfaces, no new attack paths, same security baseline. SBOM updated to reflect new component tree. DoC revised to reference updated technical file. |

**Supply chain changes in SBOM (v1.1):**

| Removed component | Replaced by | Notes |
|---|---|---|
| Siemens S7-1500 firmware 2.9.7 | Beckhoff CX5140 TwinCAT 3.1.4026 | Equivalent PLC function |
| Siemens TIA Portal runtime libs | Beckhoff TwinCAT runtime libs | Build toolchain change only |

---

### Support Period

| Field | Value |
|---|---|
| `support_type` | `standard` |
| `support_start_date` | 2026-11-14 |
| `support_end_date` | 2041-11-14 |
| `notify_before_days` | 365 |
| `justification_text` | 15-year support reflecting industrial packaging line lifetime. Customer installations are typically integrated into production lines with 12–20 year replacement cycles. |

---

### Key Milestones

| Date | Event | CRA trigger |
|---|---|---|
| 2026-11-14 | v1.0 placed on market | Art. 3(20) |
| 2028-07 | Siemens declares S7-1500 product-line discontinuation | SBOM risk event — procurement alert |
| 2028-08 | Emergency supplier evaluation + security assessment of Beckhoff CX5140 | Art. 13(7) — document supply chain response |
| 2028-09-22 | v1.1 placed on market — SBOM + DoC updated | Art. 28 — revised DoC |
| 2041-11-14 | End of support | 15-year commitment |

---
---

## Product 06 — MoldMaster IM-1200

> **Scenario:** Injection moulding machine placed on market as **Default class**. Two years later,
> updated EU sector guidance reclassifies remote-serviceable industrial machinery as **Important Class I**.
> Mid-lifecycle reclassification triggers a re-conformity cycle without a new product version.

### Product

| Field | Value |
|---|---|
| `name` | MoldMaster IM-1200 |
| `product_code` | MM-IM1200 |
| `manufacturer_name` | PressTech Engineering GmbH |
| `product_type` | Large-tonnage injection moulding machine controller |
| `current_classification` | `important_class_1` *(reclassified from `normal` in 2028)* |
| `intended_use` | Control, monitoring, and remote service access for large-tonnage injection moulding machines. OPC-UA to factory MES; remote service portal for authorised engineers via per-engineer certificate. |
| `is_pre_cra` | `false` |
| `first_placed_on_market_date` | 2027-02-10 |

---

### Releases

#### v1.0 — Placed as Default class

| Field | Value |
|---|---|
| `system_version` | 1.0.0 |
| `release_status` | `placed_on_market` |
| `placed_on_market_date` | 2027-02-10 |
| `conformity_route_snapshot` | `self_assessment` |
| `eu_doc_date` | 2027-02-01 |
| `eu_doc_number` | DOC-MMIM1200-2027-001 |
| `classification_snapshot` | `normal` |
| `release_notes` | Initial CRA-conformant release as Default class. Remote service portal uses per-engineer TLS certificates and full audit logging. Self-assessment conformity route applied. |

---

#### v1.1 — Re-conformity after reclassification

| Field | Value |
|---|---|
| `system_version` | 1.1.0 |
| `release_status` | `placed_on_market` |
| `placed_on_market_date` | 2028-07-30 |
| `conformity_route_snapshot` | `self_assessment` |
| `eu_doc_date` | 2028-07-22 |
| `eu_doc_number` | DOC-MMIM1200-2028-002 |
| `classification_snapshot` | `important_class_1` |
| `release_notes` | Re-conformity release following reclassification to Important Class I (EU sector guidance update, Jan 2028: remote-serviceable industrial machinery with internet-accessible service portal = Important Class I). No new features. Updated threat model, expanded Annex I mapping, revised DoC. |
| `parent_release_id` | → v1.0 |

**Substantial modification assessment (v1.1):**

| Criterion | Value | Reasoning |
|---|---|---|
| `alters_intended_use` | `false` | No functional change; same product, reclassified |
| `introduces_new_threat_vectors` | `false` | Remote service portal existed in v1.0; unchanged |
| `enables_new_attack_scenarios` | `false` | — |
| `changes_attack_likelihood` | `false` | — |
| `changes_attack_impact` | `false` | — |
| `is_substantial` | **`false`** | Re-conformity release only. Reclassification is a regulatory event, not a product change. |
| `reasoning` | This release exists solely to update the DoC, technical documentation, and Annex I mapping to reflect Important Class I obligations. No product functionality changed. The reclassification was triggered by updated EU sector guidance, not by any modification to the product itself. |

> **Note for demo:** Update the product's `current_classification` from `normal` to `important_class_1` before creating v1.1. The re-conformity cycle demonstrates that classification can change post-market without a technical change to the product.

---

### Support Period

| Field | Value |
|---|---|
| `support_type` | `standard` |
| `support_start_date` | 2027-02-10 |
| `support_end_date` | 2042-02-10 |
| `notify_before_days` | 365 |
| `justification_text` | 15-year support. Injection moulding machines are capital equipment with 15–20 year plant lifecycles. Remote service capability requires continuous security support commitment. |

---

### Key Milestones

| Date | Event | CRA trigger |
|---|---|---|
| 2027-02-10 | v1.0 placed on market as Default class | Self-assessment |
| 2028-01 | EU Commission sector guidance: remote-serviceable industrial machinery → Important Class I | Regulatory reclassification event |
| 2028-07-30 | v1.1 re-conformity release; updated DoC and classification | Art. 28 — new DoC; Annex I mapping expanded |
| 2029-11 | Remote service portal CVE — patch v1.2 | Art. 14 + Annex I Part II §8 |
| 2042-02-10 | End of support | — |

---
---

## Product 07 — FleetManager Mobile App

> **Scenario:** Mobile companion app for fleet management hardware. Distributed via EU app stores.
> **In CRA scope** as software placed on the EU market. OAuth token leak via deeplink.
> Post-Sep-2027 enforcement: app stores begin requiring CRA DoC for EU-market listings.
> Biometric pairing feature (v2.0) triggers a substantial modification assessment.

### Product

| Field | Value |
|---|---|
| `name` | FleetManager Mobile App |
| `product_code` | FM-MOBILE |
| `manufacturer_name` | Velocity Fleet Systems SAS |
| `product_type` | Mobile application — fleet management and vehicle telemetry |
| `current_classification` | `normal` |
| `intended_use` | iOS and Android mobile app for fleet operators. Connects to FleetManager hardware gateways and cloud API over HTTPS. Real-time vehicle telemetry, geofencing, maintenance scheduling, driver authentication. |
| `is_pre_cra` | `false` |
| `first_placed_on_market_date` | 2026-11-20 |

> **Key teaching point:** The mobile app is a CRA product. The cloud API it communicates with is out of CRA scope (SaaS). The hardware gateways it connects to are separate CRA products. Each is scoped independently.

---

### Releases

#### v1.0 — Initial EU release

| Field | Value |
|---|---|
| `system_version` | 1.0.0 |
| `release_status` | `placed_on_market` |
| `placed_on_market_date` | 2026-11-20 |
| `conformity_route_snapshot` | `self_assessment` |
| `eu_doc_date` | 2026-11-14 |
| `eu_doc_number` | DOC-FMMOBILE-2026-001 |
| `release_notes` | Initial release. Certificate pinning, OS secure storage (Keychain/Keystore), jailbreak/root detection, OAuth 2.0 PKCE flow. |

---

#### v1.1 — OAuth deeplink token leak patch

| Field | Value |
|---|---|
| `system_version` | 1.1.0 |
| `release_status` | `placed_on_market` |
| `placed_on_market_date` | 2027-06-14 |
| `conformity_route_snapshot` | `self_assessment` |
| `eu_doc_date` | 2027-06-12 |
| `eu_doc_number` | DOC-FMMOBILE-2027-002 |
| `release_notes` | Patch for CVE-2027-09901. OAuth redirect URI was insufficiently validated — a malicious app registered the same deeplink scheme and intercepted access tokens. Force-update pushed via app stores. |
| `parent_release_id` | → v1.0 |

**Substantial modification assessment (v1.1):** `is_substantial = false` — security fix only, no new functionality.

---

#### v2.0 — Biometric vehicle pairing (substantial modification)

| Field | Value |
|---|---|
| `system_version` | 2.0.0 |
| `release_status` | `placed_on_market` |
| `placed_on_market_date` | 2028-08-19 |
| `conformity_route_snapshot` | `self_assessment` |
| `eu_doc_date` | 2028-08-14 |
| `eu_doc_number` | DOC-FMMOBILE-2028-003 |
| `release_notes` | New biometric authentication for vehicle pairing. App can now command ignition enable/disable via gateway API. Introduces a control channel (previously read-only telemetry). Full re-conformity cycle. |
| `parent_release_id` | → v1.1 |

**Substantial modification assessment (v2.0):**

| Criterion | Value | Reasoning |
|---|---|---|
| `alters_intended_use` | **`true`** | v1.x was read-only telemetry; v2.0 can command ignition enable/disable — fundamentally different role |
| `introduces_new_threat_vectors` | **`true`** | Biometric credential store + ignition control API = new attack surface |
| `enables_new_attack_scenarios` | **`true`** | Attacker with compromised app can now remotely disable vehicle ignition |
| `changes_attack_likelihood` | **`true`** | Control capability makes app a higher-value target |
| `changes_attack_impact` | **`true`** | From telemetry leak to vehicle immobilisation — categorically higher impact |
| `is_substantial` | **`true`** | All five criteria met. Full re-conformity required. |
| `reasoning` | Addition of ignition control via biometric pairing transforms the app from a passive monitoring tool to an active control surface. The attack impact model changes entirely — this is a new product generation. |

---

### Security Update

**SU-001 — CVE-2027-09901 (OAuth deeplink token interception)**

| Field | Value |
|---|---|
| `title` | OAuth access token interception via malicious deeplink |
| `severity` | `high` |
| `cvss_score` | 7.5 |
| `cves_addressed_json` | `["CVE-2027-09901"]` |
| `description` | Insufficient validation of OAuth redirect URI allowed a malicious Android app registering the same custom scheme to intercept the authorization code. Attacker gains access to all fleet management functions of the victim. |
| `vulnerability_discovered_at` | 2027-06-10 |
| `remediation_deadline` | 2027-07-10 |
| `released_at` | 2027-06-14 |
| `distribution_mechanism` | `in_app_update` |
| `is_security_only` | `true` |
| `affected_versions_json` | `["1.0.0"]` |

---

### Support Period

| Field | Value |
|---|---|
| `support_type` | `standard` |
| `support_start_date` | 2026-11-20 |
| `support_end_date` | 2031-11-20 |
| `notify_before_days` | 180 |
| `justification_text` | 5-year support (CRA minimum). App store availability ends 12 months before EOS. Users notified in-app 6 months before cloud disconnection. |
| `user_facing_summary` | FleetManager Mobile App will receive security updates through 20 November 2031. After this date, the app will be removed from EU app stores. Cloud connectivity disabled on 20 November 2031. |

---

### Key Milestones

| Date | Event | CRA trigger |
|---|---|---|
| 2026-11-20 | v1.0 published to EU app stores | Art. 3(20) — software placed on EU market |
| 2027-06-10 | CVE-2027-09901 reported | Art. 14 — ENISA early warning filed |
| 2027-06-14 | v1.1 force-update pushed | Annex I Part II §8 — timely remedy |
| 2027-09-11 | CRA enforcement — app stores require DoC for EU listings | App store gate: CRA DoC mandatory |
| 2028-08-19 | v2.0 — ignition control, biometric pairing → substantial modification | Art. 3(30) + new DoC |
| 2030-11-20 | EOS notification (180 days ahead) | Art. 13(7) lifecycle communication |
| 2031-11-20 | End of support; app removed from EU stores | CRA Art. 13 commitment honoured |

---
---

## Product 08 — EdgeVision EV-Cluster *(Composite Distributed System)*

> **Scenario:** Industrial vision system shipped as a composite product: camera units + remote
> processing unit appliance + SaaS dashboard. Each hardware component is its own CRA product.
> The SaaS dashboard is out of scope. A GPU swap in the RPU is substantial for the RPU only;
> cameras are unaffected. Demonstrates per-component scoping.

---

### Product 08-A — EdgeVision Camera Unit EC-200

| Field | Value |
|---|---|
| `name` | EdgeVision Camera Unit EC-200 |
| `product_code` | EV-CAM-EC200 |
| `manufacturer_name` | OptixVision AG |
| `product_type` | Industrial machine vision camera with edge inference |
| `current_classification` | `important_class_1` |
| `intended_use` | Machine vision cameras for inline quality inspection. mTLS connection to EdgeVision RPU over private factory network. Runs signed inference models. No internet connectivity. |
| `is_pre_cra` | `false` |
| `first_placed_on_market_date` | 2027-04-01 |

**v1.0 release:**

| Field | Value |
|---|---|
| `system_version` | 1.0.0 | 
| `release_status` | `placed_on_market` |
| `placed_on_market_date` | 2027-04-01 |
| `conformity_route_snapshot` | `self_assessment` |
| `eu_doc_date` | 2027-03-22 |
| `eu_doc_number` | DOC-EVCAM-2027-001 |
| `release_notes` | Camera unit with secure boot, signed inference models, mTLS to RPU. CVD channel shared with RPU product line. |

**v1.1 release — Camera sensor supplier swap:**

| Field | Value |
|---|---|
| `system_version` | 1.1.0 |
| `release_status` | `placed_on_market` |
| `placed_on_market_date` | 2030-06-12 |
| `conformity_route_snapshot` | `self_assessment` |
| `eu_doc_date` | 2030-06-08 |
| `eu_doc_number` | DOC-EVCAM-2030-002 |
| `release_notes` | Image sensor updated from Sony IMX477 to ON Semiconductor AR0821 (supplier change). Firmware updated for new sensor interface. Security posture equivalent. RPU unaffected — SBOM updated for camera unit only. |
| `parent_release_id` | → v1.0 |

**Substantial modification assessment (camera v1.1):** `is_substantial = false` — sensor swap, equivalent security posture, no new interfaces.

---

### Product 08-B — EdgeVision RPU ER-500

| Field | Value |
|---|---|
| `name` | EdgeVision RPU ER-500 |
| `product_code` | EV-RPU-ER500 |
| `manufacturer_name` | OptixVision AG |
| `product_type` | GPU-accelerated inference server appliance for machine vision |
| `current_classification` | `important_class_1` |
| `intended_use` | Rack-mounted GPU appliance receiving camera streams via private network, running vision inference workloads in isolated containers. Optional cloud management channel (TLS 1.3 mutual auth). |
| `is_pre_cra` | `false` |
| `first_placed_on_market_date` | 2027-04-01 |

**v1.0 release:**

| Field | Value |
|---|---|
| `system_version` | 1.0.0 |
| `release_status` | `placed_on_market` |
| `placed_on_market_date` | 2027-04-01 |
| `conformity_route_snapshot` | `self_assessment` |
| `eu_doc_date` | 2027-03-22 |
| `eu_doc_number` | DOC-EVRPU-2027-001 |
| `release_notes` | Signed container runtime (Kata containers), measured boot, TPM 2.0. mTLS from cameras; optional cloud management channel (default off). |

**v2.0 release — GPU model swap (substantial modification for RPU):**

| Field | Value |
|---|---|
| `system_version` | 2.0.0 |
| `release_status` | `placed_on_market` |
| `placed_on_market_date` | 2028-09-15 |
| `conformity_route_snapshot` | `self_assessment` |
| `eu_doc_date` | 2028-09-10 |
| `eu_doc_number` | DOC-EVRPU-2028-002 |
| `release_notes` | GPU upgraded from NVIDIA A2 to NVIDIA H100. New GPU firmware, new driver stack, new container isolation boundary. Camera units not affected — they communicate via the same mTLS API. RPU only re-conformity. |
| `parent_release_id` | → v1.0 |

**Substantial modification assessment (RPU v2.0):**

| Criterion | Value | Reasoning |
|---|---|---|
| `alters_intended_use` | `false` | Vision inference workloads unchanged |
| `introduces_new_threat_vectors` | **`true`** | New GPU driver stack (H100) has different firmware attack surface; new DMA paths |
| `enables_new_attack_scenarios` | **`true`** | H100 confidential computing extensions introduce new firmware privilege boundaries not present in A2 |
| `changes_attack_likelihood` | `false` | H100 is a higher-security platform overall |
| `changes_attack_impact` | `false` | Container isolation model unchanged |
| `is_substantial` | **`true`** | Two of five criteria met; new GPU firmware attack surface requires updated threat model and SBOM. RPU re-conformity only — cameras untouched. |
| `reasoning` | The GPU is the primary processing component of the appliance. Swapping GPU model introduces a fundamentally different firmware and driver attack surface. Re-conformity scoped to RPU only. EC-200 camera units use the same API and are unaffected. |

---

### Out-of-scope SaaS context

| Component | CRA status | Reason |
|---|---|---|
| EdgeVision Cloud Dashboard | **Out of scope** | Pure SaaS — browser-only, no software placed on market |
| Cloud Dashboard Agent (if installed) | **In scope** | If customer installs a local agent, it becomes a CRA product |

> **Two Declarations of Conformity** in this system: one for EC-200, one for ER-500. No DoC for the SaaS dashboard.

---

### Key Milestones

| Date | Event | CRA trigger |
|---|---|---|
| 2027-04-01 | EC-200 + ER-500 placed on market | Two DoCs; two technical files; two SBOMs |
| 2027-09-11 | Enforcement; each component audited independently | Per-component scoping confirmed |
| 2028-09-15 | RPU v2.0 GPU swap → substantial (RPU only) | New DoC for RPU; cameras unchanged |
| 2030-06-12 | Camera v1.1 sensor swap → not substantial (camera only) | Camera SBOM + DoC updated; RPU unchanged |
| 2032-11 | SaaS dashboard breach | **NIS2 incident report** — not CRA Art. 14 |

---
---

## Product 09 — MC-Platform + MC-Apps *(Parent / Child Product Family)*

> **Scenario:** Industrial control platform (parent) with a first-party app ecosystem and a
> third-party marketplace. Demonstrates: parent runtime obligations, child app independence,
> marketplace enforcement, and what happens when a third-party developer abandons their app.

---

### Product 09-A — MC-Platform (Parent)

| Field | Value |
|---|---|
| `name` | MC-Platform |
| `product_code` | MCP-RUNTIME |
| `manufacturer_name` | AxisWorks Controls Ltd |
| `product_type` | Industrial control platform runtime and hardware |
| `current_classification` | `important_class_1` |
| `intended_use` | Secure runtime environment for industrial control apps. Hardware + signed-app loader + sandboxed execution. Apps connect to plant-floor I/O via standardised API. |
| `is_pre_cra` | `false` |
| `first_placed_on_market_date` | 2027-03-15 |

**v1.0 release:**

| Field | Value |
|---|---|
| `system_version` | 1.0.0 |
| `release_status` | `placed_on_market` |
| `placed_on_market_date` | 2027-03-15 |
| `conformity_route_snapshot` | `self_assessment` |
| `eu_doc_date` | 2027-03-05 |
| `eu_doc_number` | DOC-MCPRT-2027-001 |
| `release_notes` | Platform with signed-app loader (rejects unsigned apps), app sandboxing (SELinux profiles per app), hardware root-of-trust. Marketplace policy requires CRA DoC for all listed apps. |

**v1.1 release — Runtime vulnerability affecting ALL apps:**

| Field | Value |
|---|---|
| `system_version` | 1.1.0 |
| `release_status` | `placed_on_market` |
| `placed_on_market_date` | 2028-02-20 |
| `conformity_route_snapshot` | `self_assessment` |
| `eu_doc_date` | 2028-02-18 |
| `eu_doc_number` | DOC-MCPRT-2028-002 |
| `release_notes` | Critical patch for CVE-2028-03341 — sandbox escape in SELinux policy for runtime IPC broker. Affects all installed apps. Platform patch; apps do not need to change. Customer advisory dispatched to all marketplace app developers. |
| `parent_release_id` | → v1.0 |

**Substantial modification assessment (v1.1):** `is_substantial = false` — runtime security patch; no new APIs or features.

> **Note:** A vulnerability in the parent platform affects ALL children. The parent's CVD process must coordinate with all app developers. Each app developer must assess whether the sandbox fix changes their own threat model (it generally doesn't, but they should document the review).

---

### Product 09-B — MC-Motion App (First-party child)

| Field | Value |
|---|---|
| `name` | MC-Motion App |
| `product_code` | MCA-MOTION |
| `manufacturer_name` | AxisWorks Controls Ltd |
| `product_type` | Motion control application for MC-Platform |
| `current_classification` | `normal` |
| `intended_use` | Motion control and servo coordination application running on MC-Platform. Accesses motor drives via platform I/O API. No direct network interface — all network access via platform runtime. |
| `is_pre_cra` | `false` |
| `first_placed_on_market_date` | 2027-03-15 |
| `parent_product_id` | → MC-Platform (09-A) |

> **Note for demo:** This is a child product. Set `parent_product_id` to MC-Platform's product ID. The child has its own DoC, SBOM, and support period — but its attack surface is bounded by the platform sandbox.

**v1.0 release:**

| Field | Value |
|---|---|
| `system_version` | 1.0.0 |
| `release_status` | `placed_on_market` |
| `placed_on_market_date` | 2027-03-15 |
| `conformity_route_snapshot` | `self_assessment` |
| `eu_doc_date` | 2027-03-04 |
| `eu_doc_number` | DOC-MCAMOTION-2027-001 |
| `release_notes` | Motion app v1.0. Attack surface bounded by MC-Platform sandbox. No direct network exposure. SBOM contains only motion control logic — no OSS networking stack. |

---

### Product 09-C — Third-party app context *(not entered as product — teaching note)*

> **Context for demo:** A third-party developer published "MC-Vision QA App" to the marketplace.
> In 2030, the developer goes silent and stops responding to CVD reports. AxisWorks removes the app
> from the marketplace and issues an advisory to all users to uninstall it.

> **Key teaching points:**
> - The third-party developer is the CRA manufacturer for their app. AxisWorks is not responsible for the app's vulnerabilities.
> - AxisWorks IS responsible for: (a) enforcing CRA DoC as a marketplace listing gate; (b) removing non-conformant apps; (c) notifying users.
> - When a third-party app is removed, users have no migration path from the platform owner — this is the app developer's obligation.

---

### Support Period (MC-Platform)

| Field | Value |
|---|---|
| `support_type` | `standard` |
| `support_start_date` | 2027-03-15 |
| `support_end_date` | 2039-03-15 |
| `notify_before_days` | 365 |
| `justification_text` | 12-year platform support. App support periods are declared independently by each app's manufacturer. |

---

### Key Milestones

| Date | Event | CRA trigger |
|---|---|---|
| 2027-03-15 | MC-Platform + MC-Motion App placed on market | Two DoCs (one per product) |
| 2027-09-11 | Enforcement; marketplace enforces CRA DoC as listing gate | Platform governance |
| 2028-02-20 | CVE-2028-03341 — runtime patch; all apps potentially affected | Platform CVD coordinates with all app developers |
| 2029-05 | New first-party AI quality app → separate conformity assessment | Child app = independent CRA product |
| 2030-10 | Third-party app developer abandons product | Platform removes app; user advisory issued |
| 2032-08 | Platform major OS version — all child apps must re-validate against new runtime API | Art. 13(7) supply chain documentation |

---
---

## Product 10 — EcoMeter EM-3

> **Scenario:** Residential smart energy meter with `is_pre_cra = true`. Placed on market **before**
> 11 September 2027 — exempt from CRA Art. 13 obligations under Art. 69(2) unless substantially
> modified. In 2028, a cloud demand-response integration is added → substantial modification →
> CRA obligations triggered in full.

### Product

| Field | Value |
|---|---|
| `name` | EcoMeter EM-3 |
| `product_code` | EM3-EU |
| `manufacturer_name` | VoltSense Technologies NV |
| `product_type` | Residential smart energy meter |
| `current_classification` | `important_class_1` |
| `intended_use` | Residential smart electricity meter with LTE-M backhaul to DSO head-end system. DLMS/COSEM protocol for meter reading and tariff management. Listed product category (smart metering). |
| `is_pre_cra` | **`true`** |
| `first_placed_on_market_date` | 2026-07-01 |

> **Key teaching point (Art. 69(2)):** `is_pre_cra = true` + `placed_on_market_date` before 11 Sep 2027 → **exempt from CRA Art. 13** for v1.x *unless* subsequently substantially modified. The exemption does NOT mean no security — it means the CRA's specific conformity obligation is delayed until either the enforcement date or a substantial modification, whichever comes first.

---

### Releases

#### v1.0 — Pre-CRA placement (exempt under Art. 69(2))

| Field | Value |
|---|---|
| `system_version` | 1.0.0 |
| `release_status` | `placed_on_market` |
| `placed_on_market_date` | 2026-07-01 |
| `conformity_route_snapshot` | `self_assessment` |
| `eu_doc_date` | 2026-06-20 |
| `eu_doc_number` | DOC-EM3-2026-001 |
| `release_notes` | First market deployment in pilot DSO rollout. Placed before CRA enforcement date. Art. 69(2) exemption applies: exempt from Art. 13 obligations unless substantially modified. MID conformity assessment completed separately. |

> **Art. 69(2) status for v1.0:** Exempt. Product was placed on market before 11 Sep 2027 and has not been substantially modified. The manufacturer documents this status in the technical file.

---

#### v1.1 — LoRaWAN CVE patch (pre-enforcement)

| Field | Value |
|---|---|
| `system_version` | 1.1.0 |
| `release_status` | `placed_on_market` |
| `placed_on_market_date` | 2027-04-18 |
| `conformity_route_snapshot` | `self_assessment` |
| `eu_doc_date` | 2027-04-15 |
| `eu_doc_number` | DOC-EM3-2027-002 |
| `release_notes` | Security patch for CVE-2027-05511 (LoRaWAN join procedure vulnerability). Patch released pre-enforcement. Art. 69(2) exemption continues — patch is not a substantial modification. |
| `parent_release_id` | → v1.0 |

**Substantial modification assessment (v1.1):** `is_substantial = false` — security patch only.

---

#### v2.0 — Demand-response cloud integration (substantial modification → CRA obligations triggered)

| Field | Value |
|---|---|
| `system_version` | 2.0.0 |
| `release_status` | `placed_on_market` |
| `placed_on_market_date` | 2028-08-05 |
| `conformity_route_snapshot` | `self_assessment` |
| `eu_doc_date` | 2028-07-28 |
| `eu_doc_number` | DOC-EM3-2028-003 |
| `release_notes` | New demand-response module: DSO can now send tariff control commands to the meter over the cloud channel (bi-directional). Previously read-only backhaul becomes read-write. Substantial modification — CRA Art. 13 obligations now apply in full. First CRA-conformant DoC issued. |
| `parent_release_id` | → v1.1 |

**Substantial modification assessment (v2.0):**

| Criterion | Value | Reasoning |
|---|---|---|
| `alters_intended_use` | **`true`** | v1.x: read-only metering. v2.0: DSO can remotely control tariff and load via cloud command channel. Fundamentally different product role. |
| `introduces_new_threat_vectors` | **`true`** | Bi-directional cloud command channel; attacker compromising cloud endpoint can send tariff control commands to meters |
| `enables_new_attack_scenarios` | **`true`** | Mass manipulation of grid-edge load via compromised cloud = grid stability event |
| `changes_attack_likelihood` | **`true`** | Cloud command channel raises attack attractiveness (grid-scale impact potential) |
| `changes_attack_impact` | **`true`** | From billing manipulation to grid disruption — categorically higher impact |
| `is_substantial` | **`true`** | All five criteria met. **Art. 69(2) exemption ends. Full CRA Art. 13 obligations apply from v2.0 onward.** |
| `reasoning` | The addition of a remotely controllable demand-response command channel transforms the meter from a passive measurement device into an actuator reachable from the internet via the cloud endpoint. This constitutes a substantial modification under Art. 3(30). The Art. 69(2) pre-CRA exemption terminates. A full CRA conformity assessment under Art. 13 was completed before v2.0 placement. |

> **Art. 69(2) status for v2.0:** Exemption **terminated**. Full CRA Art. 13 obligations apply. New DoC references CRA Annex V requirements in addition to MID.

---

### Security Update

**SU-001 — CVE-2027-05511 (LoRaWAN join vulnerability)**

| Field | Value |
|---|---|
| `title` | LoRaWAN join procedure authentication bypass |
| `severity` | `medium` |
| `cvss_score` | 5.9 |
| `cves_addressed_json` | `["CVE-2027-05511"]` |
| `description` | Vulnerability in LoRaWAN 1.0.3 join procedure allows replay of join-accept frames in certain network server configurations. Attacker can cause meter to rejoin a rogue network server. |
| `vulnerability_discovered_at` | 2027-04-10 |
| `remediation_deadline` | 2027-05-10 |
| `released_at` | 2027-04-18 |
| `distribution_mechanism` | `automatic_update` |
| `is_security_only` | `true` |

---

### Support Period

| Field | Value |
|---|---|
| `support_type` | `standard` |
| `support_start_date` | 2026-07-01 |
| `support_end_date` | 2041-07-01 |
| `notify_before_days` | 365 |
| `justification_text` | 15-year support matching metering hardware deployment lifecycle. DSO contracts require 15-year meter operational lifetime. Security patches delivered OTA. |
| `expected_use_time_text` | EU metering regulations and DSO procurement standards require 15-year operational lifetime for residential smart meters. Replacement programs are coordinated at grid operator level. |

---

### Key Milestones

| Date | Event | CRA / Art. 69(2) trigger |
|---|---|---|
| 2026-07-01 | v1.0 placed on market | **Art. 69(2) exemption begins** — placed before enforcement date |
| 2027-04-18 | v1.1 LoRaWAN patch | Not substantial; exemption continues |
| 2027-09-11 | CRA enforcement | Exemption still valid for v1.x (placed before enforcement, not yet substantially modified) |
| 2028-08-05 | v2.0 demand-response command channel | **Art. 69(2) exemption terminates** — substantial modification; full CRA obligations triggered |
| 2028-08-05 | First CRA-conformant DoC issued | Art. 28 — DoC predates placement |
| 2040-07-01 | EOS notification (365 days ahead) | Art. 13(7) lifecycle communication |
| 2041-07-01 | End of support | 15-year commitment honoured |

---

## Summary: CRA Scenarios Covered

| Scenario | Product(s) |
|---|---|
| Important Class I — vuln + substantial modification | 01 MillGuard MC-400 |
| Critical class — notified body + credential theft + IP interface added | 02 SafeLogic SL-Pro |
| Pure software in CRA scope — transitive dep CVE | 03 NetMonitor Pro |
| SaaS out of scope / downloadable agent creates scope split | 04 NetMonitor Agent |
| Normal class — emergency supplier swap, SBOM refresh, not substantial | 05 PackFlow P-200 |
| Mid-lifecycle reclassification Normal → Important I | 06 MoldMaster IM-1200 |
| Mobile app in scope — OAuth vuln, app-store enforcement | 07 FleetManager Mobile |
| Composite distributed product — per-component scoping, same vendor two DoCs | 08 EdgeVision |
| Parent/child platform — marketplace governance, 3rd-party liability | 09 MC-Platform |
| Pre-CRA Art. 69(2) exemption → substantial modification ends exemption | 10 EcoMeter EM-3 |
