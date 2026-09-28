export const EXPORT_SCHEMA_VERSION = "2.0" as const;

export type ProductDataIssueLevel = "must_fix" | "will_adjust" | "will_skip" | "ready";

export interface ProductDataIssue {
  level: ProductDataIssueLevel;
  path: string;
  message: string;
}

export interface ProductDataValidation {
  valid: boolean;
  bundle_id: string;
  schema_version: string;
  source_product_name: string;
  source_product_code: string;
  suggested_product_code: string;
  digest: string;
  signature_status: "verified" | "unsigned" | "unverified" | "invalid";
  counts: Record<string, number>;
  included: string[];
  excluded: string[];
  issues: ProductDataIssue[];
}

export interface ProductDataImportResult {
  product_id: string;
  bundle_id: string;
  digest: string;
  counts: Record<string, number>;
  adjusted: number;
  skipped: number;
}

export interface ProductDataHistoryItem {
  occurred_at: string;
  action: "exported" | "imported";
  status: string;
  product_id: string | null;
  product_name: string | null;
  bundle_id: string | null;
  digest: string | null;
  counts: Record<string, number>;
}

export interface ProductDataExportOptions {
  releaseIds?: string[];
  redactPersonalData: boolean;
  includeEmbargoed: boolean;
  sensitivity: "internal" | "confidential" | "restricted";
}
