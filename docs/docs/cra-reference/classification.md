---
id: classification
title: Product Classification
sidebar_position: 3
---

# Product Classification

The CRA establishes four classification tiers for products with digital elements. The tier determines the conformity assessment route the manufacturer must follow before placing the product on the EU market.

## Classification Tiers

### Normal (Default Category)

All PDEs that do not fall within Annex III or Annex IV are classified as Normal. The manufacturer may demonstrate conformity through **self-assessment** against the essential requirements in Annex I.

Self-assessment requires the manufacturer to:
- Conduct and document a cybersecurity risk assessment
- Produce the technical documentation required by Annex VII
- Draw up the EU Declaration of Conformity

### Important Class I (Annex III, Class I)

Important Class I products include, among others:

- Identity management and privileged access management software
- Browsers
- Password managers
- Software that searches for, removes, or quarantines malicious software
- Products using virtual private networks (VPNs)
- Network management systems
- SIEM systems
- Routers and modems intended for consumer use
- General-purpose microprocessors and operating systems

For Important Class I products, the manufacturer may self-assess **unless** a harmonised standard is not available or the manufacturer does not apply the relevant harmonised standards. In those cases, third-party assessment is required.

### Important Class II (Annex III, Class II)

Important Class II products include, among others:

- Hypervisors and container runtime systems
- Firewalls, intrusion detection and prevention systems
- Tamper-resistant microprocessors and microcontrollers
- Industrial automation and control systems (IACS) used in critical infrastructure

Important Class II products require **mandatory third-party assessment** by an accredited conformity assessment body (notified body).

### Critical (Annex IV)

Critical products are those specifically listed in Annex IV. These require a **European cybersecurity certification** under a relevant scheme established by ENISA under Regulation (EU) 2019/881 (the Cybersecurity Act). Until a relevant scheme is available, the rules applicable to Important Class II apply.

## Classification and Conformity Routes

| Classification | Conformity Route | Third-Party Required |
|---|---|---|
| Normal | Self-assessment | No |
| Important Class I | Self-assessment (default) | Only if harmonised standards not applied |
| Important Class II | Third-party assessment | Yes |
| Critical | European cybersecurity certification | Yes |

## Classification in the Platform

When registering a product, set the **Classification** field to reflect the manufacturer's determination. Following a [Scope Evaluation](/user-guide/scope-evaluation), the recommended classification is provided and should be applied to the product record.

When a product release is created, the current classification is captured as an immutable **classification snapshot** on the release record. This ensures that the historical compliance position is preserved regardless of subsequent reclassification.

:::important
Classification decisions should be reviewed whenever a [substantial modification](/user-guide/substantial-changes) is made to the product, and whenever the manufacturer becomes aware of regulatory updates to Annex III or Annex IV, or new implementing or delegated acts that may affect the classification.
:::
