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

export interface RequirementMappingRead {
  id: string;
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
  risk_item_id: string | null;
  annex_requirement_id: string;
  engineering_requirement_ref: string | null;
  sdl_activity: SdlActivity;
  implementation_status: RequirementImplementationStatus;
}

export interface RequirementMappingCreate {
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

export type RequirementMapping = RequirementMappingRead;