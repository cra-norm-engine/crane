---
id: substantial-modifications
title: Substantial Modifications
sidebar_position: 4
---

# Substantial Modifications

CRA Article 13(8) addresses the regulatory treatment of modifications made to products that are already on the market. If a modification is deemed **substantial**, the manufacturer must treat the modified product as a new product and conduct a new conformity assessment procedure.

## Regulatory Text

Article 13(8) provides:

> Where a modification is made to a product with digital elements that is already placed on the market or put into service and that modification may affect the compliance of the product with this Regulation or results in a change of the intended purpose for which the product has been assessed, the manufacturer shall carry out a new conformity assessment procedure [...].

Article 2(37) defines **substantial modification** as:

> A modification of a product with digital elements, made after the product has been placed on the market or put into service, that affects the compliance of the product with digital elements with the essential cybersecurity requirements set out in Annex I or results in a change of the intended purpose for which the product with digital elements has been assessed [...].

## The Four Assessment Criteria

In practice, a modification is substantial if it meets any of the following criteria:

| Criterion | Description |
|---|---|
| **Alters intended use** | The modification changes the product's intended purpose or the scope of its deployment |
| **Increases cybersecurity risk** | The modification increases cybersecurity risk beyond the baseline assessed in the original conformity procedure |
| **Changes hazard nature** | The modification introduces a new category or nature of hazard not foreseen in the original assessment |
| **Expands attack surface** | The modification introduces features or capabilities outside the original product scope — such as new network interfaces or processing of new categories of sensitive data |

If **any** criterion is met, the modification is substantial and a new conformity assessment procedure is required.

## Security Patches — Article 3(4) Exception

Article 3(4) explicitly states that security updates — modifications made solely to address security vulnerabilities — do not constitute substantial modifications. This exception exists to ensure that manufacturers are not discouraged from issuing timely security patches by the prospect of triggering a full re-assessment.

Security patches must still be documented as security update records (see [Security Updates](/user-guide/security-updates)), but they do not require a substantiality assessment and cannot result in a substantial determination.

## Consequences of a Substantial Modification

When a modification is assessed as substantial, the manufacturer must:

1. Treat the modified product as a **new product** for conformity purposes
2. Conduct a new cybersecurity **risk assessment**
3. Carry out the applicable **conformity assessment procedure**
4. Update the **technical documentation** and EU Declaration of Conformity
5. Create a new **product release** record representing the modified baseline
6. **Re-mark** the product with CE marking as appropriate

## Non-Substantial Modifications

If all four criteria are answered **No**, the modification is not substantial. The existing conformity assessment, risk assessment, and technical documentation remain valid. No new conformity procedure is required.

:::note
The substantiality assessment itself constitutes a documented justification that the existing risk assessment remains accurate. Because the assessor has attested that the modification does not increase cybersecurity risk, alter the hazard nature, or expand the attack surface, no separate risk assessment update is required for a non-substantial change.
:::

## Platform Implementation

The [Substantial Change Tracking](/user-guide/substantial-changes) feature implements this workflow:

- Change records capture the modification details and type
- The assessment form operationalises the four criteria
- Compliance actions track the mandatory re-assessment steps for substantial changes
- The `caused_by_change_id` link on product releases creates the Article 13(8) traceability chain
