---
id: support-period
title: Support Period Management
sidebar_position: 7
---

# Support Period Management

CRA Article 13(7) requires manufacturers to specify the support period during which the product will receive security updates, and to communicate this period clearly to users. The support period must reflect the expected lifetime of the product. Support period management in this platform provides structured records, end-of-support notification management, and standardised text generation for user-facing disclosures.

## CRA Requirement

Article 13(7) states that the manufacturer shall ensure that security updates are available for the expected product lifetime or five years, whichever is shorter, unless the expected product lifetime is longer, in which case the manufacturer shall ensure availability for the full expected lifetime. The support period must be communicated to the user at the point of sale and through product packaging or accompanying documentation.

## Creating a Support Period Record

Navigate to the product detail page and select **New Support Period Record**.

### Required Fields

| Field | Description |
|---|---|
| **Support Start Date** | Date from which security support commences (typically the product's market release date) |
| **Support End Date** | Date on which security support ends |
| **Support Type** | Standard, Limited, Extended, or Custom |
| **Justification** | Documented rationale for the selected support duration, referencing the product's expected lifetime |
| **Notification Threshold** | Number of days before end-of-support at which notifications should be sent to designated recipients |
| **Recipients** | Users who will receive end-of-support notifications |

### Optional Fields

| Field | Description |
|---|---|
| **Expected Use Time** | Narrative description of the product's expected operational lifetime |
| **Comparable Products** | Reference to comparable products and their support commitments, used to justify the selected duration |
| **Third-Party Support Constraints** | Any constraints imposed by third-party component support timelines |
| **User-Facing Summary** | Public-facing text describing the support commitment, suitable for product documentation |
| **Packaging Summary** | Condensed support period statement for inclusion on product packaging |

## Support Types

| Type | Description |
|---|---|
| **Standard** | Security updates provided for the standard product lifetime |
| **Limited** | Reduced support scope (e.g. critical vulnerabilities only); must be justified |
| **Extended** | Support beyond the standard period, typically for enterprise or industrial deployments |
| **Custom** | Custom support arrangement; full justification required |

## AI-Assisted Text Generation

When an AI provider is configured, the platform can generate compliant user-facing and packaging summary text based on the support period details. The generated text follows the disclosure requirements of Article 13(7) and may be edited before saving.

## End-of-Support Notifications

The platform monitors active support period records and issues notifications to designated recipients when the end-of-support date is within the configured threshold. Notification records track:

- Scheduled notification date
- Sending status (Pending, Sent, Dismissed)
- Recipient identity and contact details

## Active Record Management

Only one support period record may be active at a time for a given product. Creating a new support period record supersedes the previous active record, which is retained as a historical record. This supports scenarios where a support period is extended (for example, following a regulatory or commercial decision to extend product lifecycle).
