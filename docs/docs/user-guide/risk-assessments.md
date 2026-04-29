---
id: risk-assessments
title: Risk Assessments
sidebar_position: 3
---

# Risk Assessments

The CRA requires manufacturers to conduct and document a cybersecurity risk assessment as part of the product design and development process (Annex I, Part I, §1). Risk assessments in this platform are stored as structured records linked to a specific product and, optionally, a specific product release.

## CRA Requirement

Annex I, Part I requires that the product be designed and developed having regard to the results of an integrated cybersecurity risk assessment. The risk assessment must:

- Identify and analyse cybersecurity risks relevant to the product
- Consider risks associated with the product's intended use and reasonably foreseeable misuse
- Address the product's entire lifecycle, including development, deployment, and end of support

The risk assessment must be included in the technical documentation (Annex VII).

## Creating a Risk Assessment

Navigate to the product detail page and select **New Risk Assessment**, or navigate to a specific release and create the assessment from the release context.

### Required Information

| Field | Description |
|---|---|
| **Title** | Descriptive title for this assessment (e.g. "v2.1 Initial Risk Assessment") |
| **Assessment Date** | Date the assessment was conducted |
| **Assessor** | The person or team responsible for this assessment |
| **Summary** | Executive summary of findings and overall risk determination |
| **Identified Risks** | Structured list of identified risks, each with likelihood, impact, and mitigation |
| **Residual Risk Conclusion** | Statement on whether residual risk is acceptable |

## Linking to a Release

A risk assessment may be linked to a specific product release. When linked, the assessment appears in the release gate as evidence for the **risk_assessment** gate item. This linkage creates the traceability between the conformity evidence and the specific product version being assessed.

## Risk Assessment and Substantial Modifications

When a [substantial modification](/user-guide/substantial-changes) is confirmed, the resulting compliance actions include updating the risk assessment for the new product version. A new risk assessment record should be created for the new release and linked accordingly.

For non-substantial changes, no new risk assessment is required — the existing assessment remains valid by virtue of the substantiality determination having confirmed that the change does not increase cybersecurity risk, alter the hazard nature, or expand the attack surface.

## Assessment History

All risk assessments are retained as immutable records. The product detail page and each release page display associated assessments. Historical assessments are not deleted when a new assessment is created; they remain accessible for audit and regulatory inspection purposes.
