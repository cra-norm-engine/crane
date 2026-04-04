export type ArtifactType =
  | "document"
  | "test_report"
  | "sbom"
  | "screenshot"
  | "link"
  | "declaration"
  | "annex_output"
  | "authority_package";

export type ArtifactSourceType = "upload" | "external_link";

export interface UserSummaryRead {
  id: string;
  email: string;
  full_name: string;
}

export interface ArtifactRevisionRead {
  id: string;
  artifact_id: string;
  revision_number: number;
  source_type: ArtifactSourceType;
  original_filename: string | null;
  content_type: string | null;
  file_size_bytes: number | null;
  sha256: string | null;
  storage_path: string | null;
  external_url: string | null;
  change_summary: string | null;
  uploaded_by_user_id: string;
  uploaded_by_user: UserSummaryRead | null;
  created_at: string;
  updated_at: string;
}

export interface ArtifactListRead {
  id: string;
  title: string;
  description: string | null;
  artifact_type: ArtifactType;
  created_by_user_id: string;
  created_by_user: UserSummaryRead | null;
  created_at: string;
  updated_at: string;
  latest_revision: ArtifactRevisionRead | null;
  linked_product_ids: string[];
}

export interface ArtifactRead extends ArtifactListRead {
  revisions: ArtifactRevisionRead[];
}
