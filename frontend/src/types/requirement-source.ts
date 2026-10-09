import type { AnnexRequirementRead } from "@/types/annex-requirement";

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

export type LibraryRequirement = AnnexRequirementRead;
