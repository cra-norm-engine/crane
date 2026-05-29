import type { ArtifactRevisionRead, UserSummaryRead } from "@/types/artifact";
import type { ConformityRoute, ProductClassification } from "@/types/product";

export type ReleaseGateStatus = "draft" | "in_review" | "approved" | "blocked";
export type GateDecision = "pending_review" | "accepted" | "rejected" | "needs_update" | "waived";
export type ReleaseGateItemCode =
  | "technical_documentation"
  | "risk_assessment"
  | "sbom"
  | "test_report"
  | "declaration_of_conformity"
  | "annex_mapping";

export interface ProductReleaseRead {
  id: string;
  product_id: string;
  product_name: string | null;
  system_version: number;
  system_version_label: string;
  user_version: string | null;
  display_version: string;
  release_status:
    | "draft"
    | "in_review"
    | "blocked"
    | "approved"
    | "placed_on_market"
    | "released"
    | "withdrawn"
    | "recalled"
    | "end_of_support";
  planned_release_date: string | null;
  actual_release_date: string | null;
  placed_on_market_date: string | null;
  classification_snapshot: ProductClassification;
  conformity_route_snapshot: ConformityRoute;
  release_notes: string | null;
  parent_release_id: string | null;
  substantiality_analysis_id: string | null;
  is_consolidated_support_version: boolean;
  // CRA Art. 13(8) traceability: ID of the substantial change that required this re-release.
  caused_by_change_id: string | null;
  /** CRA Art. 13(2): true when this release has known exploitable vulnerabilities blocking gate approval. */
  has_known_exploitable_vulnerabilities: boolean;
  kev_notes: string | null;
  eu_doc_date: string | null;
  eu_doc_number: string | null;
  eu_doc_notified_body: string | null;
  /** Gap 2 — hardware version for embedded products. */
  hardware_version: string | null;
  /** Gap 2 — software/firmware version for embedded products. */
  software_version: string | null;
  /** Gap 1 — remote processing elements linked to this release. */
  release_remote_processing_elements: import("@/types/product").RemoteProcessingElementSummaryRead[];
  created_at: string;
  updated_at: string;
}

export interface ReleaseGateEvidenceLinkRead {
  id: string;
  decision: GateDecision;
  rationale: string | null;
  linked_by_user_id: string;
  linked_by_user: UserSummaryRead | null;
  reviewed_by_user_id: string | null;
  reviewed_by_user: UserSummaryRead | null;
  reviewed_at: string | null;
  created_at: string;
  updated_at: string;
  artifact_revision: ArtifactRevisionRead;
}

export interface ReleaseGateItemRead {
  id: string;
  code: ReleaseGateItemCode | null;
  title: string;
  description: string | null;
  is_required: boolean;
  sort_order: number;
  status: GateDecision;
  evidence_links: ReleaseGateEvidenceLinkRead[];
  prerequisites?: ReleaseGateItemSummary[];
  unmet_prerequisites?: ReleaseGateItemSummary[];
}

export interface ReleaseGateItemSummary {
  id: string;
  code: ReleaseGateItemCode | null;
  title: string;
  status: GateDecision;
}

export interface ReleaseGateRead {
  id: string;
  product_release_id: string;
  status: ReleaseGateStatus;
  submitted_at: string | null;
  submitted_by_user_id: string | null;
  submitted_by_user: UserSummaryRead | null;
  approved_at: string | null;
  approved_by_user_id: string | null;
  approved_by_user: UserSummaryRead | null;
  bundle_sha256: string | null;
  bundle_generated_at: string | null;
  snapshot_json: Record<string, unknown> | null;
  created_at: string;
  updated_at: string;
  items: ReleaseGateItemRead[];
  required_items_count: number;
  accepted_items_count: number;
  pending_items_count: number;
}

export interface ReleaseGateDetailRead {
  release: ProductReleaseRead;
  gate: ReleaseGateRead;
}
