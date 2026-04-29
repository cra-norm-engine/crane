---
id: release-management
title: Release Management
sidebar_position: 4
---

# Release Management

A product release represents a specific version of a product that is, or is intended to be, placed on the EU market. Each release carries a classification snapshot, a conformity route, and a lifecycle status that tracks its progress from draft through to market placement and eventual end of support.

## Creating a Release

Navigate to the product detail page and select **New Release**.

### Required Fields

| Field | Description |
|---|---|
| **Version** | Version string for this release (e.g. `2.1.0`). Must be unique within the product. |
| **Classification Snapshot** | The product classification at the time of this release. Captured as a snapshot so that subsequent reclassification does not retroactively alter the release record. |
| **Conformity Route** | The conformity assessment route applicable to this release: Self-assessment, Third-Party Assessment, or Not Applicable. |

### Optional Fields

| Field | Description |
|---|---|
| **Planned Release Date** | Target date for market placement. |
| **Actual Release Date** | Date the product was actually placed on the market. Set when transitioning to Released status. |
| **Release Notes** | Summary of changes included in this release. |
| **Triggered by Substantial Change** | If this release is required as a consequence of a [substantial modification](/user-guide/substantial-changes) (CRA Article 13(8)), link it to the relevant change record. This creates the regulatory traceability chain and automatically completes the re-release compliance action. |

## Release Lifecycle

A release moves through the following status transitions:

```
Draft → In Review → Approved → Released
              ↓
           Blocked
```

| Status | Meaning |
|---|---|
| **Draft** | Release is being prepared; gate review has not commenced |
| **In Review** | Release gate review is in progress |
| **Blocked** | Gate review identified deficiencies; release is on hold |
| **Approved** | All gate items accepted; release is approved for market placement |
| **Released** | Product has been placed on the market |
| **Withdrawn** | Release was withdrawn before or after market placement |
| **Recalled** | Release was recalled from the market |
| **End of Support** | Support period for this release has ended |

## Classification and Conformity Snapshots

When a release is created, the product's current classification and selected conformity route are captured as snapshots on the release record. These snapshots are immutable after creation, ensuring that the historical compliance position for each version remains accurate regardless of subsequent changes to the product's classification.

## Release Gate

Before a release is approved, it must pass a release gate review. The gate enforces that all required conformity evidence has been assembled and reviewed. See [Release Gate](/user-guide/release-gate) for the full procedure.

## Traceability to Substantial Changes

When a new release is created as a direct consequence of a substantial modification (for example, a re-certification following a material change to the product), linking the release to the substantial change record via the **Triggered by Substantial Change** field fulfils the traceability requirement under CRA Article 13(8). The platform automatically marks the re-release compliance action as completed when this link is established.
