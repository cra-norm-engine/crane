---
id: scope-evaluation
title: Scope Evaluation
sidebar_position: 2
---

# Scope Evaluation

The scope evaluation determines whether a product falls within the CRA and, if so, recommends an appropriate classification and conformity route. A completed scope evaluation is the starting point for all subsequent compliance activities.

## When to Run a Scope Evaluation

A scope evaluation should be run:

- When a new product is registered in the platform
- When a product undergoes a change that may affect its regulatory classification
- When the manufacturer becomes aware of updated regulatory guidance that may affect previously evaluated products

## Running a Scope Evaluation

Navigate to the product detail page and select **Run Scope Evaluation**. The evaluation form presents a series of questions corresponding to the CRA's scope criteria.

### Evaluation Questions

| Question | CRA Relevance |
|---|---|
| Is this a product with digital elements? | Primary scope criterion — Article 2 |
| Does the product have network connectivity (direct or indirect)? | Connectivity is a defining characteristic of a PDE under CRA |
| Does the product perform remote data processing? | Relevant to Article 2 scope and Annex III classification |
| Is the product intended as a safety component? | Relevant to Important Class I classification — Annex III |
| Is the product used in a critical sector as defined by NIS 2? | Relevant to Important Class II classification — Annex III |
| Does the product handle sensitive functions (authentication, access control)? | Relevant to classification and risk profile |
| Does the product fall within an excluded category? | CRA Article 2(2) and (3) list specific exclusions |

An optional **Notes** field allows the evaluator to document the reasoning behind each answer for audit purposes.

## Evaluation Outcome

After submission, the platform generates a documented determination containing:

- **In Scope** — whether the product is subject to the CRA
- **Rationale** — a structured explanation of the determination
- **Recommended Classification** — Normal, Important Class I, Important Class II, or Critical
- **Suggested Conformity Route** — Self-assessment, Third-Party Assessment, or Not Applicable

The scope status on the product record is updated automatically to reflect the outcome.

:::note
The evaluation outcome is a recommendation based on the answers provided. The manufacturer retains legal responsibility for the final classification decision. Where the classification is ambiguous, legal and regulatory affairs counsel should be consulted.
:::

## Evaluation History

All scope evaluations are retained as immutable records. The product detail page displays the full history of evaluations in reverse chronological order. A new evaluation does not overwrite previous records; it supersedes them as the current determination while preserving the audit trail.

## AI-Assisted Evaluation

When an AI provider is configured (see [Installation](/getting-started/installation)), the platform will supplement the structured questionnaire with an AI-generated rationale that cross-references the answers against the CRA text. This is intended to assist the evaluator, not to replace their judgment.
