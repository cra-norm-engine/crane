---
id: product-registry
title: Product Registry
sidebar_position: 1
---

# Product Registry

The product registry is the foundation of the platform. Every CRA compliance record — scope evaluations, risk assessments, releases, and substantial change assessments — is anchored to a product in the registry.

## Creating a Product

Navigate to **Products → New Product** and complete the registration form.

### Required Fields

| Field | Description |
|---|---|
| **Product Code** | Your organisation's internal unique identifier for this product (e.g. `SW-CTRL-001`). Must be unique across the registry. |
| **Product Name** | Human-readable name of the product. |
| **Manufacturer Name** | Legal name of the manufacturing entity responsible for CRA compliance. |
| **Intended Use** | A clear description of the product's intended use and operating environment. This is a key field for scope evaluation and technical documentation. |
| **Product Type** | Category of product (e.g. industrial control software, consumer IoT device, network appliance). |
| **Classification** | Initial classification: Normal, Important Class I, Important Class II, or Critical. This may be updated following a scope evaluation. |
| **Scope Status** | Set to **Undecided** until a scope evaluation has been completed. |

### Optional Fields

| Field | Description |
|---|---|
| **Description** | Extended description for internal reference. |
| **Parent Product** | Link this product to a parent product if it is a component or variant of a larger product family. |

## Product Classification

The CRA defines four classification tiers that determine the conformity assessment route required:

| Classification | CRA Category | Conformity Route |
|---|---|---|
| Normal | Default category | Self-assessment |
| Important Class I | Annex III, Class I | Self-assessment or third-party |
| Important Class II | Annex III, Class II | Third-party assessment mandatory |
| Critical | Annex IV | European cybersecurity certification mandatory |

Classification should be determined following a [Scope Evaluation](/user-guide/scope-evaluation) and updated accordingly.

## Product Hierarchy

Products may be linked in a parent–child hierarchy to represent product families or platform variants. A parent product record captures shared characteristics, while child products record version-specific or variant-specific information.

To link a child product, select the parent product in the **Parent Product** field during registration or when editing an existing product.

## Editing a Product

To modify an existing product, open the product detail page and select **Edit**. All fields except the product code may be edited. If the product code must be changed (for example, following a re-numbering of your internal product catalogue), create a new product record and archive the existing one.

## Scope Status

The scope status field reflects the outcome of the most recent scope evaluation:

| Status | Meaning |
|---|---|
| Undecided | No scope evaluation has been completed |
| In Scope | The product has been determined to be within the CRA |
| Out of Scope | The product has been determined to be excluded from the CRA |

This field is updated automatically when a scope evaluation is submitted.

## Related Records

From the product detail page, you can access all compliance records associated with the product:

- **Releases** — version history and release status
- **Scope Evaluations** — historical evaluation records
- **Risk Assessments** — linked risk assessment documents
- **Remote Processing Elements** — third-party cloud or processing dependencies
- **Support Period** — support commitment records
- **Certification Records** — third-party certification and assessment records
