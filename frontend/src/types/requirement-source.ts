export type RequirementSourceStatus = "draft" | "published" | "retired";

export interface RequirementSourceRead {
  id: string;
  identifier: string;
  title: string;
  source_type: string;
  edition: string | null;
  publisher: string | null;
  reference_url: string | null;
  license_note: string | null;
  status: RequirementSourceStatus;
  organization_wide: boolean;
  is_system_managed: boolean;
  product_ids: string[];
  requirement_count: number;
  created_at: string;
  updated_at: string;
}

export interface RequirementSourceCreate {
  identifier: string;
  title: string;
  source_type: string;
  edition?: string | null;
  publisher?: string | null;
  reference_url?: string | null;
  license_note?: string | null;
  organization_wide: boolean;
  product_ids: string[];
}

export interface LibraryRequirement {
  id: string;
  code: string;
  title: string;
  description: string;
  annex_part: "part_i" | "part_ii";
  is_active: boolean;
  source_id: string | null;
  source_identifier: string;
  source_title: string;
  clause_reference: string | null;
  applicability_guidance: string | null;
  verification_guidance: string | null;
  expected_evidence: string | null;
  revision: number;
  status: string;
  is_mandatory: boolean;
}
