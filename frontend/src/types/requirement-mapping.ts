import type { AnnexRequirementRead } from "@/types/annex-requirement";
import type { ArtifactListRead } from "@/types/artifact";
import type { RiskItemSummaryRead } from "@/types/risk-item";

export type RequirementImplementationStatus =
  | "planned"
  | "in_progress"
  | "implemented"
  | "verified"
  | "not_applicable";

export type SdlActivity =
  | "requirements"
  | "design"
  | "implementation"
  | "verification"
  | "validation"
  | "vulnerability_management"
  | "documentation"
  | "post_market";

export type RequirementApplicabilityDecision =
  | "undecided"
  | "applicable"
  | "not_applicable";

export interface RequirementMappingRead {
  id: string;
  product_release_id: string;
  risk_item_id: string | null;
  annex_requirement_id: string;
  engineering_requirement_ref: string | null;
  sdl_activity: SdlActivity;
  implementation_status: RequirementImplementationStatus;
  evidence_summary: string | null;
  created_at: string;
  updated_at: string;
}

export interface RequirementMappingSummaryRead {
  id: string;
  product_release_id: string;
  risk_item_id: string | null;
  annex_requirement_id: string;
  engineering_requirement_ref: string | null;
  sdl_activity: SdlActivity;
  implementation_status: RequirementImplementationStatus;
}

export interface RequirementMappingMatrixRead extends RequirementMappingRead {
  risk_item: RiskItemSummaryRead | null;
  artifacts: ArtifactListRead[];
}

export interface ProductRequirementMatrixRowRead {
  annex_requirement: AnnexRequirementRead;
  artifact_traceability_available: boolean;
  applicability_decision: RequirementApplicabilityDecision;
  applicability_rationale: string | null;
  mapping_ids: string[];
  trace_records: RequirementMappingMatrixRead[];
  risk_items: RiskItemSummaryRead[];
  artifacts: ArtifactListRead[];
  engineering_requirement_refs: string[];
  sdl_activities: SdlActivity[];
  notes: string[];
  overall_status: RequirementImplementationStatus | null;
  applicability: "needs_decision" | "applicable" | "not_applicable";
  traceability_strength: "missing" | "weak" | "partial" | "complete";
}

export interface ProductRequirementDecisionUpdate {
  applicability_decision: RequirementApplicabilityDecision;
  rationale?: string | null;
}

export interface RequirementMappingCreate {
  product_release_id: string;
  risk_item_id?: string | null;
  annex_requirement_id: string;
  engineering_requirement_ref?: string | null;
  sdl_activity: SdlActivity;
  implementation_status?: RequirementImplementationStatus;
  evidence_summary?: string | null;
}

export interface RequirementMappingUpdate {
  risk_item_id?: string | null;
  annex_requirement_id?: string | null;
  engineering_requirement_ref?: string | null;
  sdl_activity?: SdlActivity;
  implementation_status?: RequirementImplementationStatus;
  evidence_summary?: string | null;
}

export interface RequirementMappingArtifactLinkRequest {
  artifact_id: string;
}

export type RequirementMapping = RequirementMappingRead;
