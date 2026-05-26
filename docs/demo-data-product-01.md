# CRA Demo Data — Product 01: MillGuard MC-400

> **Scenario theme:** Important Class I industrial controller. Ships pre-enforcement, survives a
> critical OPC-UA vulnerability, then receives a cloud telemetry module (substantial modification)
> that triggers a full re-conformity cycle.

---

## Product

| Field | Value |
|---|---|
| `name` | MillGuard MC-400 |
| `product_code` | MG-MC400 |
| `manufacturer_name` | NexaControl GmbH |
| `product_type` | 5-axis CNC machining centre controller |
| `current_classification` | `important_class_1` |
| `intended_use` | Real-time motion control and process supervision for 5-axis CNC milling machines in metalworking factories. Connects to shop-floor OPC-UA network and optional vendor cloud for predictive maintenance telemetry. |
| `is_pre_cra` | `false` |
| `first_placed_on_market_date` | 2026-11-03 |
| `parent_product_id` | *(none — standalone product)* |

---

## Releases

### Release v1.0 — Initial market placement

| Field | Value |
|---|---|
| `system_version` | 1.0.0 |
| `release_status` | `placed_on_market` |
| `planned_release_date` | 2026-10-01 |
| `placed_on_market_date` | 2026-11-03 |
| `conformity_route_snapshot` | `self_assessment` |
| `eu_doc_date` | 2026-10-28 |
| `eu_doc_number` | DOC-MG-MC400-2026-001 |
| `release_notes` | First CRA-conformant release. OPC-UA stack hardened, signed firmware, CVD channel live. |

**Release gate items (v1.0 — all `pass`):**

| Gate item | Status | Notes |
|---|---|---|
| `technical_documentation` | pass | Technical file complete per Annex VII |
| `risk_assessment` | pass | STRIDE analysis completed 2026-09-10 |
| `sbom` | pass | CycloneDX 1.6 SBOM generated and supplier-validated |
| `test_report` | pass | SAST + pen-test report signed off 2026-10-15 |
| `declaration_of_conformity` | pass | DoC signed 2026-10-28 |
| `annex_mapping` | pass | All 22 Annex I requirements mapped |

---

### Release v1.1 — Security patch (OPC-UA CVE)

| Field | Value |
|---|---|
| `system_version` | 1.1.0 |
| `release_status` | `placed_on_market` |
| `planned_release_date` | 2027-03-15 |
| `placed_on_market_date` | 2027-03-22 |
| `conformity_route_snapshot` | `self_assessment` |
| `eu_doc_date` | 2027-03-20 |
| `eu_doc_number` | DOC-MG-MC400-2027-002 |
| `release_notes` | Emergency patch for CVE-2027-04821 (heap overflow in open62541 OPC-UA stack). Distribution via vendor download portal and automated OTA for cloud-enrolled units. |
| `parent_release_id` | → v1.0 |

**Substantial modification assessment (v1.1):**

| Criterion | Value | Reasoning |
|---|---|---|
| `alters_intended_use` | `false` | Patch only; no new functionality |
| `introduces_new_threat_vectors` | `false` | Removes an attack surface, adds none |
| `enables_new_attack_scenarios` | `false` | No new interfaces or protocols |
| `changes_attack_likelihood` | `false` | Likelihood reduced, not increased |
| `changes_attack_impact` | `false` | Impact reduced, not increased |
| `is_substantial` | **`false`** | Security-only patch — not a substantial modification (CRA Art. 3(30)) |
| `reasoning` | Pure security fix for a known CVE in a third-party OPC-UA library. No change to intended use, attack surface topology, or product function scope. |

**Release gate items (v1.1):**

| Gate item | Status | Notes |
|---|---|---|
| `technical_documentation` | pass | Updated to reflect patched component |
| `sbom` | pass | open62541 updated from 1.3.5 → 1.3.9 |
| `test_report` | pass | Regression + targeted CVE verification |
| `declaration_of_conformity` | pass | Revised DoC issued 2027-03-20 |
| `substantial_modification_analysis` | pass | Assessment concludes not substantial |

---

### Release v2.0 — Cloud telemetry module (substantial modification)

| Field | Value |
|---|---|
| `system_version` | 2.0.0 |
| `release_status` | `placed_on_market` |
| `planned_release_date` | 2028-04-01 |
| `placed_on_market_date` | 2028-05-14 |
| `conformity_route_snapshot` | `self_assessment` |
| `eu_doc_date` | 2028-05-09 |
| `eu_doc_number` | DOC-MG-MC400-2028-003 |
| `release_notes` | Adds cloud-based predictive maintenance telemetry module (MQTT over TLS 1.3 to NexaCloud endpoint). Introduces new internet-facing interface. Full re-conformity assessment completed. |
| `parent_release_id` | → v1.1 |

**Substantial modification assessment (v2.0):**

| Criterion | Value | Reasoning |
|---|---|---|
| `alters_intended_use` | `false` | Core machining function unchanged |
| `introduces_new_threat_vectors` | **`true`** | New internet-facing MQTT channel to cloud endpoint — entirely new attack surface not present in v1.x |
| `enables_new_attack_scenarios` | **`true`** | Cloud endpoint compromise could exfiltrate process data or deliver malicious firmware commands |
| `changes_attack_likelihood` | **`true`** | Internet connectivity raises exploitation likelihood vs. LAN-only v1.x |
| `changes_attack_impact` | `false` | Telemetry is read-only; no cloud-to-machine control path in v2.0 |
| `is_substantial` | **`true`** | Three of five §103 criteria met — substantial modification under Art. 3(30) |
| `reasoning` | Addition of the cloud telemetry MQTT interface constitutes a substantial modification. New internet-facing channel introduces threat vectors and attack scenarios absent from v1.x. Full re-conformity cycle initiated: updated threat model, new SBOM entries, revised technical documentation, new DoC. |

**Compliance actions triggered by substantial modification:**
- New threat model covering cloud channel (STRIDE)
- SBOM updated with MQTT client library + cloud SDK
- Penetration test focused on cloud communication path
- Revised technical documentation (Annex VII)
- New EU Declaration of Conformity issued

**Release gate items (v2.0):**

| Gate item | Status | Notes |
|---|---|---|
| `technical_documentation` | pass | Full revision for cloud module |
| `risk_assessment` | pass | Updated STRIDE: cloud endpoint + MQTT channel |
| `sbom` | pass | Eclipse Paho MQTT 1.3.13 + NexaCloud SDK 2.1.0 added |
| `test_report` | pass | Pen-test by external firm; cloud channel findings resolved |
| `declaration_of_conformity` | pass | New DoC 2028-05-09 |
| `annex_mapping` | pass | Annex I §1(a) re-evaluated for cloud path |
| `substantial_modification_analysis` | pass | Substantial — new conformity cycle complete |

---

## Risk Assessment

**Assessment:** MC-400 Threat Model v1 (covers v1.0–v1.1)
**Methodology:** `stride`
**Product version scope:** v1.0 and v1.1 (cloud-free architecture)

| # | Threat | STRIDE | Likelihood | Impact | Risk | Mitigation |
|---|---|---|---|---|---|---|
| 1 | Unauthenticated OPC-UA command injection via plant network | Tampering | high | high | **critical** | OPC-UA certificate-based auth + allowlist enforced in v1.0 |
| 2 | Firmware rollback via unsigned update package | Tampering | medium | high | **high** | Signed firmware; version check blocks downgrade |
| 3 | Credential theft from engineering workstation → machine auth | Information Disclosure | medium | medium | **medium** | Per-machine certificates; no shared credentials |
| 4 | Man-in-the-middle on OPC-UA channel during diagnostics | Spoofing | low | high | **medium** | Mutual TLS on all OPC-UA sessions |
| 5 | Denial of service via malformed OPC-UA packets | Denial of Service | low | medium | **low** | Rate limiting + input validation on OPC-UA parser |

**Assessment v2 (covers v2.0 — updated for cloud module):**

| # | Threat | STRIDE | Likelihood | Impact | Risk | Mitigation |
|---|---|---|---|---|---|---|
| 6 | Cloud endpoint compromise → exfiltration of process telemetry | Information Disclosure | medium | medium | **medium** | TLS 1.3 mutual auth; telemetry is non-sensitive process data |
| 7 | MQTT broker takeover → spoofed telemetry → misleading maintenance alerts | Spoofing | low | low | **low** | Certificate pinning to NexaCloud endpoint; no control path from cloud |
| 8 | DNS hijack redirecting MQTT to attacker endpoint | Spoofing | low | medium | **medium** | Certificate pinning prevents connection to untrusted endpoint |

---

## Security Updates

### SU-001 — CVE-2027-04821 (OPC-UA heap overflow)

| Field | Value |
|---|---|
| `title` | Critical heap overflow in open62541 OPC-UA stack |
| `severity` | `critical` |
| `cvss_score` | 9.1 |
| `cves_addressed_json` | `["CVE-2027-04821"]` |
| `description` | Heap overflow in open62541 v1.3.5 triggered by malformed OPC-UA NodeId in Browse request. Unauthenticated remote attacker can achieve arbitrary code execution on the controller. |
| `vulnerability_discovered_at` | 2027-02-28 |
| `remediation_deadline` | 2027-03-30 |
| `released_at` | 2027-03-22 |
| `distribution_mechanism` | `vendor_download` + `automatic_update` (cloud-enrolled units) |
| `is_free_of_charge` | `true` |
| `affected_versions_json` | `["1.0.0"]` |
| `is_security_only` | `true` |
| `integrity_info` | SHA-256: a3f9c1d88e2b74f05c3a9e1d7b0f4a2c1e8d5b7f |

**Associated vulnerability report:**

| Field | Value |
|---|---|
| `title` | CVE-2027-04821 — open62541 heap overflow |
| `status` | `remediated` |
| `lifecycle_status` | `disclosed` |
| `cvss_score` | 9.1 |
| `cve_id` | CVE-2027-04821 |
| `affected_component` | open62541 OPC-UA library v1.3.5 |
| `reporter` | External researcher (coordinated disclosure, 30-day embargo) |
| `reported_date` | 2027-02-28 |
| `remediation_date` | 2027-03-22 |

---

## Changes

### CHG-001 — Emergency OPC-UA library update (→ v1.1)

| Field | Value |
|---|---|
| `title` | Upgrade open62541 to v1.3.9 — CVE-2027-04821 |
| `change_type` | `security` |
| `description` | Replace open62541 1.3.5 with 1.3.9 which patches the heap overflow. No API or behaviour change. Firmware re-signed and regression-tested. |
| `is_breaking` | `false` |
| `affected_versions` | v1.0.0 |

### CHG-002 — Add cloud telemetry MQTT module (→ v2.0)

| Field | Value |
|---|---|
| `title` | Integrate NexaCloud predictive maintenance telemetry |
| `change_type` | `feature` |
| `description` | New MQTT-over-TLS 1.3 channel streams spindle load, temperature, and vibration telemetry to NexaCloud endpoint. Opt-in by default; configurable via operator panel. Adds Eclipse Paho MQTT client and NexaCloud SDK to firmware image. |
| `is_breaking` | `false` |
| `affected_versions` | v1.1.0 |
| *→ links to substantial modification assessment* | **is_substantial = true** |

---

## SBOM Snapshot (v2.0 key components)

| Component | Version | Supplier | License | Notes |
|---|---|---|---|---|
| open62541 | 1.3.9 | open62541 project | MPL-2.0 | OPC-UA stack (patched) |
| Eclipse Paho MQTT C | 1.3.13 | Eclipse Foundation | EPL-2.0 | Cloud telemetry transport |
| NexaCloud SDK | 2.1.0 | NexaControl GmbH | Proprietary | Cloud auth + envelope |
| FreeRTOS | 10.5.1 | Amazon / MIT | MIT | RTOS kernel |
| mbedTLS | 3.5.0 | Arm | Apache-2.0 | TLS stack |
| lwIP | 2.2.0 | Adam Dunkels | BSD | TCP/IP stack |
| u-boot | 2023.10 | Denx | GPL-2.0 | Bootloader |

**Format:** `cyclonedx` (CycloneDX 1.6)
**Total component count:** 47 (7 shown above are top-level; 40 transitive dependencies)

---

## Support Period

| Field | Value |
|---|---|
| `support_type` | `standard` |
| `support_start_date` | 2026-11-03 |
| `support_end_date` | 2038-11-03 |
| `notify_before_days` | 365 |
| `justification_text` | 12-year support commitment matching typical metalworking CNC machine operational lifetime. Manufacturer commits to security patches for all critical and high severity vulnerabilities for the full period. |
| `expected_use_time_text` | CNC machining centres in metalworking SMEs operate for 10–15 years before replacement. 12-year support aligns with the 75th-percentile operational lifetime for this segment. |
| `user_facing_summary` | NexaControl guarantees security updates for MillGuard MC-400 through 3 November 2038. Critical vulnerabilities will be patched within 30 days of disclosure. End-of-support notification will be issued no later than 12 months before the support end date. |

---

## Key Scenario Milestones (Timeline)

| Date | Event | CRA trigger |
|---|---|---|
| 2026-09 | Threat model + SBOM completed | Pre-release gate |
| 2026-10-28 | EU DoC signed | Art. 28 — DoC precedes placement |
| 2026-11-03 | v1.0 placed on market | Art. 3(20) market placement |
| 2027-02-28 | CVE-2027-04821 reported to NexaControl | Art. 14 — ENISA early warning within 24h |
| 2027-03-22 | v1.1 patch released within 30 days | Art. 14 / Annex I Part II §8 — timely remedy |
| 2027-09-11 | CRA full enforcement | Ongoing conformity — v1.1 already compliant |
| 2028-05-14 | v2.0 placed on market after full re-conformity | Art. 3(30) + Art. 28 — new DoC for substantial modification |
| 2037-11-03 | EOS notification dispatched (365 days before end) | Art. 13(7) — documented lifecycle communication |
| 2038-11-03 | End of support | Art. 13(10) — support period commitment honoured |

---

## Notes for Demo Input

- Enter the product first, then v1.0 release → run gate → mark placed on market.
- Create the risk assessment and link to v1.0.
- Create CHG-001, run the v1.1 substantial modification assessment (all false → not substantial), create v1.1 release, link SBOM update.
- Create the security update SU-001, observe that a **lifecycle notification** is automatically generated for the support period recipients.
- Create CHG-002, run the v2.0 substantial modification assessment (introduces_new_threat_vectors = true → is_substantial = true), observe compliance actions generated.
- Create v2.0 release with new DoC number and date, complete the full gate.
