---
id: release-gate
title: Release Gate
sidebar_position: 5
---

# Release Gate

The release gate is a structured, evidence-based readiness review that a product release must pass before it can be approved for market placement. It operationalises the manufacturer's obligation to assemble the conformity documentation required under CRA Annex VII and the applicable conformity assessment procedure.

## Gate Items

Each release gate contains a set of mandatory and optional items. The following items are defined by default:

| Code | Title | Required | CRA Basis |
|---|---|---|---|
| `technical_documentation` | Technical Documentation | Yes | Annex VII |
| `risk_assessment` | Cybersecurity Risk Assessment | Yes | Annex I, Part I; Annex VII |
| `sbom` | Software Bill of Materials | Yes | Annex I, Part II; Annex VII |
| `test_report` | Security Test Report | Yes | Annex I, Part I |
| `declaration_of_conformity` | EU Declaration of Conformity | Yes | Article 28; Annex V |
| `annex_mapping` | Annex I Requirements Mapping | Yes | Annex I |

Additional custom gate items may be added to reflect organisation-specific processes or certification body requirements.

## Evidence Linking

For each gate item, one or more artifact revisions must be linked as evidence. An artifact revision is a specific version of a document or file stored in the platform's artifact management system.

To link evidence:

1. Open the release detail page and navigate to the **Release Gate** section.
2. Select the gate item to which evidence will be linked.
3. Select the artifact revision that serves as evidence for that item.
4. Set an initial decision of **Pending Review**.

## Item Decisions

Each piece of linked evidence carries a decision set by the reviewer:

| Decision | Meaning |
|---|---|
| **Pending Review** | Evidence has been linked but not yet reviewed |
| **Accepted** | Evidence is complete and satisfies the gate item |
| **Needs Update** | Evidence has been reviewed but requires revision before acceptance |
| **Rejected** | Evidence does not satisfy the gate item |
| **Waived** | Gate item is not applicable to this release (must be justified) |

A required gate item must reach **Accepted** or **Waived** status before the release can be approved.

## Gate Status

The overall gate status is derived from the status of its items:

| Gate Status | Condition |
|---|---|
| **Draft** | Gate has not been submitted for review |
| **In Review** | Gate has been submitted; review is in progress |
| **Blocked** | One or more required items are rejected or flagged |
| **Approved** | All required items are accepted or waived |

## Approving a Release

Once all required gate items have been accepted or waived and the gate status is **Approved**, the release status transitions to **Approved**. The authorised reviewer selects **Approve Release** to formally record the approval.

The approval is recorded with:
- The identity of the approving user
- The timestamp of approval
- A SHA-256 bundle hash of all linked evidence at the time of approval, providing a tamper-evident record of the evidence set reviewed

## Audit Trail

All gate actions — linking evidence, changing decisions, submitting for review, approving — are recorded in the platform's immutable audit log. This log is available to administrators and is intended to support regulatory inspection.
