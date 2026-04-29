---
id: security-updates
title: Security Updates
sidebar_position: 9
---

# Security Updates

Security update records document the security patches and vulnerability remediation releases issued for a product. This satisfies the manufacturer's obligations under CRA Annex I, Part II, which requires that security updates be made available without delay, clearly identifiable, and distributed via a secure channel.

## CRA Requirement

Annex I, Part II requires manufacturers to:

- Make security updates available without delay when vulnerabilities become known
- Ensure updates are distributed through appropriate and secure channels
- Provide users with sufficient information to apply updates
- Maintain the integrity and authenticity of updates

Security updates are explicitly excluded from constituting substantial modifications under Article 3(4), ensuring that manufacturers are not discouraged from issuing timely security patches.

## Creating a Security Update Record

Navigate to the product release detail page and select **New Security Update**.

### Required Fields

| Field | Description |
|---|---|
| **Title** | Descriptive title of the security update (e.g. "Security patch for CVE-2025-12345") |
| **Distribution Mechanism** | How the update is delivered to users (see below) |
| **CVEs Addressed** | List of CVE identifiers resolved by this update |
| **Affected Versions** | List of product versions affected by the resolved vulnerabilities |
| **Update Channels** | The update channels or endpoints through which the update is distributed |

### Optional Fields

| Field | Description |
|---|---|
| **Description** | Extended description of the vulnerabilities addressed and the remediation approach |
| **Severity** | Overall severity rating: Critical, High, Medium, Low, or Informational |
| **Security-Only Flag** | Indicates whether this update addresses security issues exclusively, with no functional changes |
| **Integrity Information** | Hash values or digital signature details allowing users to verify update integrity |
| **Available Until** | Date after which this update will no longer be available for download |
| **Released At** | Timestamp of public release |

## Distribution Mechanisms

| Mechanism | Description |
|---|---|
| **Automatic Update** | Update is applied automatically without user intervention |
| **In-App Update** | Update is offered and applied from within the product's interface |
| **Package Repository** | Update is published to a package manager repository (e.g. apt, npm, PyPI) |
| **Vendor Download** | Update is available from the manufacturer's download portal |
| **Manual Install** | Update requires manual installation by the user or administrator |
| **Field Service** | Update is applied by a field service engineer |
| **Other** | Any other distribution mechanism; description required |

## Relationship to Substantial Changes

Security updates are never substantial modifications (Article 3(4)). A security update record documents the update without initiating a substantial modification assessment. If a security release coincidentally includes feature changes that may be substantial, those changes should be recorded separately as a [Substantial Change](/user-guide/substantial-changes) and assessed accordingly.

## Integrity and Authenticity

The **Integrity Information** field should contain hash values (SHA-256 or stronger) and, where applicable, digital signature references that allow recipients to verify that the update has not been tampered with in transit. This directly addresses the Annex I, Part II requirement for secure distribution.
