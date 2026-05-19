export type RiskAssessmentStatus = "draft" | "in_review" | "approved" | "archived";

export type RiskLevel = "low" | "medium" | "high" | "critical";

export type RiskItemStatus = "open" | "in_progress" | "mitigated" | "accepted" | "closed";

export type AnnexPart = "part_i" | "part_ii";

export type RequirementImplementationStatus =
  | "planned"
  | "in_progress"
  | "implemented"
  | "verified"
  | "not_applicable";

export type EvidenceType =
  | "document"
  | "test_report"
  | "sbom"
  | "screenshot"
  | "link"
  | "declaration"
  | "annex_output"
  | "authority_package";

// =====================
// Risk Assessment
// =====================

export interface RiskAssessmentRead {
  id: string;
  product_id: string;
  product_release_id: string | null;
  title: string;
  system_version: number;
  user_version: string | null;
  display_version: string;
  status: RiskAssessmentStatus;
  methodology: string;
  summary: string | null;
  owner_user_id: string;
  approved_at: string | null;
  created_at: string;
  updated_at: string;
  risk_items_count?: number;
  evidence_items_count?: number;
}

export interface RiskAssessmentCreate {
  product_id: string;
  product_release_id?: string | null;
  title: string;
  user_version?: string | null;
  status?: RiskAssessmentStatus;
  methodology: string;
  summary?: string | null;
  owner_user_id: string;
}

export interface RiskAssessmentUpdate {
  title?: string;
  user_version?: string | null;
  status?: RiskAssessmentStatus;
  methodology?: string;
  summary?: string | null;
  owner_user_id?: string;
  product_release_id?: string | null;
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

// =====================
// Risk Item
// =====================

export interface RiskItemRead {
  id: string;
  risk_assessment_id: string;
  title: string;
  description: string;
  threat_scenario: string;
  asset_affected: string;
  likelihood: RiskLevel;
  impact: RiskLevel;
  risk_level: RiskLevel;
  mitigation_plan: string;
  residual_risk_level: RiskLevel | null;
  status: RiskItemStatus;
  owner_user_id: string | null;
  created_at: string;
  updated_at: string;
}

export interface RiskItemCreate {
  risk_assessment_id: string;
  title: string;
  description: string;
  threat_scenario: string;
  asset_affected: string;
  likelihood: RiskLevel;
  impact: RiskLevel;
  risk_level: RiskLevel;
  mitigation_plan: string;
  residual_risk_level?: RiskLevel | null;
  status: RiskItemStatus;
  owner_user_id?: string | null;
}

export interface RiskItemUpdate {
  title?: string;
  description?: string;
  threat_scenario?: string;
  asset_affected?: string;
  likelihood?: RiskLevel;
  impact?: RiskLevel;
  risk_level?: RiskLevel;
  mitigation_plan?: string;
  residual_risk_level?: RiskLevel | null;
  status?: RiskItemStatus;
  owner_user_id?: string | null;
}

// =====================
// Annex Requirement
// =====================

export interface AnnexRequirementRead {
  id: string;
  code: string;
  title: string;
  description: string;
  annex_part: AnnexPart;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface AnnexRequirementCreate {
  code: string;
  title: string;
  description: string;
  annex_part: AnnexPart;
  is_active?: boolean;
}

export interface AnnexRequirementUpdate {
  title?: string;
  description?: string;
  annex_part?: AnnexPart;
  is_active?: boolean;
}

// =====================
// Requirement Mapping
// =====================

export interface RequirementMappingRead {
  id: string;
  risk_item_id: string | null;
  annex_requirement_id: string;
  engineering_requirement_ref: string | null;
  sdl_activity: string;
  implementation_status: RequirementImplementationStatus;
  evidence_summary: string | null;
  created_at: string;
  updated_at: string;

  annex_requirement?: AnnexRequirementRead;
  risk_item?: RiskItemRead | null;
  evidence_items?: EvidenceItemRead[];
}

export interface RequirementMappingCreate {
  risk_item_id?: string | null;
  annex_requirement_id: string;
  engineering_requirement_ref?: string | null;
  sdl_activity: string;
  implementation_status: RequirementImplementationStatus;
  evidence_summary?: string | null;
}

export interface RequirementMappingUpdate {
  risk_item_id?: string | null;
  annex_requirement_id?: string;
  engineering_requirement_ref?: string | null;
  sdl_activity?: string;
  implementation_status?: RequirementImplementationStatus;
  evidence_summary?: string | null;
}

// =====================
// Evidence
// =====================

export interface EvidenceItemRead {
  id: string;
  title: string;
  description: string | null;
  evidence_type: EvidenceType;
  file_path: string | null;
  external_url: string | null;
  product_release_id: string | null;
  risk_assessment_id: string | null;
  requirement_mapping_id: string | null;
  uploaded_by_user_id: string;
  created_at: string;
  updated_at: string;
}

export interface EvidenceItemCreate {
  product_release_id?: string | null;
  risk_assessment_id?: string | null;
  requirement_mapping_id?: string | null;
  title: string;
  description?: string | null;
  evidence_type: EvidenceType;
  file_path?: string | null;
  external_url?: string | null;
  uploaded_by_user_id: string;
}

export interface EvidenceItemUpdate {
  product_release_id?: string | null;
  risk_assessment_id?: string | null;
  requirement_mapping_id?: string | null;
  title?: string;
  description?: string | null;
  evidence_type?: EvidenceType;
  file_path?: string | null;
  external_url?: string | null;
  uploaded_by_user_id?: string | null;
}