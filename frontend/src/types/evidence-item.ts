export type EvidenceType =
  | "document"
  | "test_report"
  | "sbom"
  | "screenshot"
  | "link"
  | "declaration"
  | "annex_output"
  | "authority_package";

export interface EvidenceItemRead {
  id: string;
  product_release_id: string | null;
  risk_assessment_id: string | null;
  requirement_mapping_id: string | null;
  title: string;
  description: string | null;
  evidence_type: EvidenceType;
  file_path: string | null;
  external_url: string | null;
  uploaded_by_user_id: string;
  created_at: string;
  updated_at: string;
}

export interface EvidenceItemSummaryRead {
  id: string;
  title: string;
  evidence_type: EvidenceType;
  product_release_id: string | null;
  risk_assessment_id: string | null;
  requirement_mapping_id: string | null;
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

export type EvidenceItem = EvidenceItemRead;