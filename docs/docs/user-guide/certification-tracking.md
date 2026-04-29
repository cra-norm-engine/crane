---
id: certification-tracking
title: Certification Tracking
sidebar_position: 8
---

# Certification Tracking

Certification tracking provides a centralised record of third-party conformity assessments and European cybersecurity certifications obtained for products subject to mandatory third-party assessment under the CRA.

## When Certification Records Apply

Certification records are relevant for:

- **Important Class II** products — third-party conformity assessment is mandatory
- **Critical** products — European cybersecurity certification under a relevant scheme is mandatory
- **Important Class I** products — where the manufacturer elects to use a third-party assessment instead of self-assessment

For **Normal** and **Important Class I** (self-assessment route) products, the release gate evidence record serves as the primary conformity documentation. A certification record is not required.

## Creating a Certification Record

Navigate to the product detail page and select **New Certification Record**.

### Required Fields

| Field | Description |
|---|---|
| **Certificate Number** | The reference number issued by the certification body or notified body |
| **Certification Body** | Name of the notified body, accredited conformity assessment body, or certification authority |
| **Certification Scheme** | The scheme under which the certificate was issued (e.g. a European cybersecurity certification scheme under ENISA) |
| **Issue Date** | Date the certificate was issued |
| **Expiry Date** | Date on which the certificate expires |
| **Scope** | Description of the products, versions, and configurations covered by the certificate |
| **Classification Covered** | The CRA classification tier addressed by this certificate |

### Optional Fields

| Field | Description |
|---|---|
| **Certificate Document** | Link to the artifact record containing the certificate document |
| **Assessment Report** | Link to the artifact record containing the assessment body's report |
| **Notes** | Internal notes regarding the certification engagement |

## Certificate Validity Monitoring

The platform displays the expiry status of all active certification records. Records approaching expiry are flagged to allow manufacturers to initiate renewal in advance. A lapsed certificate against a product currently on the market represents a compliance risk and should be remediated promptly.

## Relationship to Release Gate

For products requiring third-party certification, the `declaration_of_conformity` gate item in the release gate should reference the certificate issued following the third-party assessment. The certification record and the release gate evidence link together provide full traceability from the market release to the conformity documentation.

## Historical Records

Expired certification records are retained in the platform. This allows manufacturers to demonstrate the validity of their compliance position at any point in time, which may be required during market surveillance authority inspections.
