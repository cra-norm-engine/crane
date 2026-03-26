export type AnnexPart = "part_i" | "part_ii";

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

export interface AnnexRequirementSummaryRead {
  id: string;
  code: string;
  title: string;
  annex_part: AnnexPart;
  is_active: boolean;
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

export type AnnexRequirement = AnnexRequirementRead;