/**
 * Product Export Bundle — canonical JSON schema for full product data transfer.
 * Schema version must be checked on import before processing.
 */

import type { ProductRead } from "@/types/product";
import type { ProductReleaseRead } from "@/types/release-gate";
import type { RiskAssessmentRead } from "@/types/risk-assessment";
import type { RiskItemRead } from "@/types/risk-item";
import type {
  CvdPolicyRead,
  VulnerabilityReportRead,
  SecurityAdvisoryRead,
  SecurityUpdateRead,
  SbomRecordRead,
  SupportPeriodRecordRead,
} from "@/types/product";
import type { CertificationRecord } from "@/types/certification-record";
import type { ChangeSummary } from "@/types/change";

export const EXPORT_SCHEMA_VERSION = "1.0" as const;
export type ExportSchemaVersion = typeof EXPORT_SCHEMA_VERSION;

/* ── Meta block ─────────────────────────────────────── */
export interface ExportMeta {
  /* Bumped when the bundle structure changes in a breaking way. */
  schema_version: ExportSchemaVersion;
  exported_at: string;      // ISO-8601 UTC
  exported_by: string;      // user email
  tool: "CRANE CRA Compliance Tool";
}

/* ── Per-release sub-bundle ─────────────────────────── */
export interface ExportedRelease extends ProductReleaseRead {
  /* All per-release entities keyed by old release ID (preserved for re-linking on import). */
  vulnerability_reports: VulnerabilityReportRead[];
  security_advisories: SecurityAdvisoryRead[];
  security_updates: SecurityUpdateRead[];
  sbom_records: SbomRecordRead[];
}

/* ── Per-assessment sub-bundle ──────────────────────── */
export interface ExportedRiskAssessment extends RiskAssessmentRead {
  risk_items: RiskItemRead[];
}

/* ── Root bundle ────────────────────────────────────── */
export interface ProductExportBundle {
  _meta: ExportMeta;

  /* Core product record (no child_products / releases expansion). */
  product: ProductRead;

  /* Releases with all per-release entities nested inside. */
  releases: ExportedRelease[];

  /* Product-level entities. */
  risk_assessments: ExportedRiskAssessment[];
  cvd_policies: CvdPolicyRead[];
  support_periods: SupportPeriodRecordRead[];
  certification_records: CertificationRecord[];
  changes: ChangeSummary[];
}

/* ── Import result ──────────────────────────────────── */
export interface ImportSummary {
  product_name: string;
  schema_version: string;
  exported_at: string;
  counts: {
    releases: number;
    risk_assessments: number;
    risk_items: number;
    vulnerability_reports: number;
    security_advisories: number;
    security_updates: number;
    sbom_records: number;
    cvd_policies: number;
    support_periods: number;
    certification_records: number;
    changes: number;
  };
}

/* ── Import progress ─────────────────────────────────── */
export interface ImportProgress {
  step: string;
  done: number;
  total: number;
}
