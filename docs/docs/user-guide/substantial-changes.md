---
id: substantial-changes
title: Substantial Change Tracking
sidebar_position: 6
---

# Substantial Change Tracking

Substantial change tracking implements the manufacturer's obligation under CRA Article 13(8) to assess whether modifications to a product in market constitute a substantial modification. A substantial modification triggers the requirement to treat the modified product as a new product for conformity assessment purposes.

## Regulatory Background

CRA Article 13(8) states that if a manufacturer makes a modification to a product that may have an impact on the compliance of that product with the essential requirements, or changes the intended purpose of the product, a new conformity assessment procedure must be conducted. See [Substantial Modifications](/cra-reference/substantial-modifications) in the CRA Reference for the full regulatory context.

## Recording a Change

Navigate to **Substantial Changes → New Change** and complete the form.

### Required Fields

| Field | Description |
|---|---|
| **Product** | The product to which this change applies |
| **Release** | The specific product release (version) being modified |
| **Change Type** | Category of change: Security Patch, New Feature, Bug Fix, or Maintenance |
| **Title** | Brief, descriptive title of the change |
| **Description** | Full description of what changed and the technical rationale |
| **Change Date** | Date the change was made |

## Change Lifecycle

A change record moves through the following workflow:

```
Draft → Submitted → Under Review → Assessed → Action Required / Closed
```

| Status | Description |
|---|---|
| **Draft** | Change has been recorded but not yet submitted for assessment |
| **Submitted** | Change has been submitted and is awaiting assignment |
| **Under Review** | A cybersecurity engineer has claimed the change and is conducting the assessment |
| **Assessed** | Assessment has been completed; outcome is either substantial or not substantial |
| **Action Required** | Change was assessed as substantial; compliance actions are outstanding |
| **Closed** | All required actions have been completed, or the change was assessed as not substantial |

## Substantiality Assessment

When a cybersecurity engineer claims a change (transition to **Under Review**), they must complete a substantiality assessment against four CRA criteria.

### Assessment Criteria

| Criterion | Description |
|---|---|
| **Alters Intended Use** | Does the change alter the product's intended purpose or scope of use? |
| **Increases Cybersecurity Risk** | Does the change increase the cybersecurity risk compared to the assessed baseline? |
| **Changes Hazard Nature** | Does the change introduce a new category or nature of hazard not present in the original? |
| **Expands Attack Surface** | Does the change introduce features outside the original product scope (new network interfaces, new processing of sensitive data)? |

If **any** criterion is answered **Yes**, the change is classified as **Substantial**. The assessor must also provide a written reasoning that justifies the determination for audit purposes.

:::note
Security patches (Change Type: Security Patch) are explicitly excluded from constituting substantial modifications under CRA Article 3(4). The assessment form can still be completed for documentation purposes, but such changes cannot result in a substantial determination regardless of the criteria answers.
:::

### Why Non-Substantial Changes Do Not Require a Risk Assessment Update

If all four criteria are answered **No**, the assessor has explicitly attested that the change does not increase cybersecurity risk, does not alter the hazard nature, and does not expand the attack surface. The existing risk assessment therefore remains accurate and does not require updating. The substantiality assessment itself serves as the documented justification.

## Compliance Actions

When a change is assessed as substantial, the platform automatically creates the following compliance action records:

| Action | Description |
|---|---|
| **Re-release Product** | Create a new product release representing the post-modification baseline |
| **Update Technical Documentation** | Revise technical documentation to reflect the modified product |
| **Renew Conformity Assessment** | Conduct a new conformity assessment procedure for the modified product |
| **Update Risk Assessment** | Conduct and document a new cybersecurity risk assessment |

Each action can be tracked to completion with due dates, notes, and responsible parties.

## Linking a New Release

When a new release is created as a consequence of a substantial modification, link it to the change record via the **Triggered by Substantial Change** field on the release form. This creates the Article 13(8) traceability chain and automatically marks the **Re-release Product** compliance action as completed.
