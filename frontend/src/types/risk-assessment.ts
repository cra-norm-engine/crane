export type RiskAssessmentStatus =
  | "draft"
  | "in_review"
  | "approved"
  | "archived";

export type RiskItemStatus =
  | "open"
  | "in_progress"
  | "mitigated"
  | "accepted"
  | "closed";

export type RiskLevel = "low" | "medium" | "high" | "critical";

export type EvidenceType =
  | "document"
  | "test_report"
  | "sbom"
  | "screenshot"
  | "link"
  | "declaration"
  | "annex_output"
  | "authority_package";

export interface RiskItemSummaryRead {
  id: string;
  title: string;
  risk_level: RiskLevel;
  status: RiskItemStatus;
  owner_user_id: string | null;
  created_at: string;
  updated_at: string;
}

export interface EvidenceItemSummaryRead {
  id: string;
  title: string;
  evidence_type: EvidenceType;
  file_path: string | null;
  external_url: string | null;
  uploaded_by_user_id: string;
  created_at: string;
  updated_at: string;
}

export interface RiskAssessmentRead {
  id: string;
  product_id: string;
  product_release_id: string | null;
  title: string;
  system_version: number;
  user_version: string | null;
  status: RiskAssessmentStatus;
  methodology: string;
  summary: string;
  owner_user_id: string;
  approved_at: string | null;
  created_at: string;
  updated_at: string;
  system_version_label: string;
  display_version: string;
}

export interface RiskAssessmentDetailRead extends RiskAssessmentRead {
  risk_items_count: number;
  evidence_items_count: number;
  risk_items: RiskItemSummaryRead[];
  evidence_items: EvidenceItemSummaryRead[];
}

export interface RiskAssessmentCreate {
  product_id: string;
  product_release_id?: string | null;
  title: string;
  user_version?: string | null;
  status?: RiskAssessmentStatus;
  methodology: string;
  summary: string;
  owner_user_id: string;
}

export interface RiskAssessmentUpdate {
  product_release_id?: string | null;
  title?: string;
  user_version?: string | null;
  status?: RiskAssessmentStatus;
  methodology?: string;
  summary?: string;
  owner_user_id?: string | null;
  approved_at?: string | null;
  reviewer_user_id?: string | null;
  rejection_reason?: string | null;
}

export interface RiskAssessmentApproveRequest {
  approved_at?: string | null;
}

export interface RiskAssessmentDuplicateRequest {
  user_version?: string | null;
  title?: string | null;
  product_release_id?: string | null;
  summary?: string | null;
  owner_user_id?: string | null;
  reset_status_to_draft?: boolean;
  copy_risk_items?: boolean;
  copy_requirement_mappings?: boolean;
  copy_evidence_links?: boolean;
}

export type RiskAssessment = RiskAssessmentRead | RiskAssessmentDetailRead;