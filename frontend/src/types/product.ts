// CRANE — CRA Norm Engine
// Copyright (C) 2026 Ali Mohammad Hosseini
// SPDX-License-Identifier: AGPL-3.0-or-later
// This file is part of CRANE, free software under the GNU AGPL v3.0 or later.
// See <https://www.gnu.org/licenses/>.

export type ProductClassification =
  | "normal"
  | "important_class_1"
  | "important_class_2"
  | "critical"
  | "foss";

export type ConformityRoute =
  | "self_assessment"
  | "third_party_assessment"
  | "not_applicable"
  | "undecided";

export type ScopeStatus = "undecided" | "in_scope" | "out_of_scope";

/** CRA obligation tier: legacy = reporting-only, active = full obligations. */
export type ProductLifecycleStatus = "legacy" | "active";

/** Typed CRA product classification (software-only vs hardware with digital elements). */
export type ProductType =
  | "type1_software"
  | "type2_hardware_with_digital"
  | "undecided";

/** Phase 4 — system-as-product vs component-by-component strategy. */
export interface SystemProfile {
  sold_as_product: boolean | null;
  who_integrates_system: string | null;
  marketed_as_product: boolean | null;
  core_minimum_products_combination: string | null;
}

/** Phase 4 — B2B tailor-made product contract terms. */
export interface TailorMadeTerms {
  customized_support_period: string | null;
  customized_security_config: string | null;
  specific_user: string | null;
  agreement_via_contractual_terms: string | null;
}

export interface ProductSummaryRead {
  id: string;
  product_code: string;
  name: string;
  manufacturer_name: string;
  product_type: string;
  current_classification: ProductClassification;
  scope_status: ScopeStatus | string;
  /** CRA obligation tier: legacy (reporting-only) vs active (full obligations). */
  lifecycle_status: ProductLifecycleStatus;
  /** Phase 3 — typed classification (software vs hardware+digital). */
  product_type_class: ProductType;
  /** Phase 3 — product-level conformity assessment route. */
  conformity_route: ConformityRoute;
  /** Phase 2 — when the (out-of-)scope decision was signed off; null = undecided. */
  scope_decided_at: string | null;
  /** Phase 2 — free-text signature of the scope decision; null = unsigned. */
  scope_decision_signature: string | null;
  /** Phase 4 — flag chip: product carries a SystemProfile. */
  has_system_profile: boolean;
  /** Phase 4 — flag chip: product has tailor-made B2B terms. */
  has_tailor_made_terms: boolean;
  /** Flag chip: product relies on a remote data processing element. */
  has_remote_processing: boolean;
  created_at: string;
  updated_at: string;
  /** Gap 2 — true when this product combines hardware and software/firmware (embedded product). */
  is_embedded_product: boolean;
  /** Gap 4 — CRA Art. 69(2): true when the product was already on the EU market before CRA applied. */
  is_pre_cra: boolean;
  /** Gap 4 — earliest known EU market placement date for this product line. */
  first_placed_on_market_date: string | null;
  /** Gap 4 — Annex I Part II §6: vulnerability reporting contact email. */
  security_contact_email: string | null;
  /** Gap 4 — Annex I Part II §6: URL of the security contact or security.txt. */
  security_contact_url: string | null;
}

export interface ProductHierarchyNode {
  id: string;
  product_code: string;
  name: string;
  current_classification: ProductClassification;
  scope_status: ScopeStatus | string;
}

/** All possible lifecycle states for a product release. */
export type ReleaseStatus =
  | "draft"
  | "in_review"
  | "blocked"
  | "approved"
  // Gap 3 — formal EU market placement event (CRA Art. 3(20))
  | "placed_on_market"
  | "released"
  | "withdrawn"
  | "recalled"
  | "end_of_support";

export interface ProductReleaseSummaryRead {
  id: string;
  product_name: string | null;
  system_version: number;
  user_version: string | null;
  display_version: string;
  /** Gap 2 — hardware version component for embedded products (e.g. "PCB Rev 2.1"). */
  hardware_version: string | null;
  /** Gap 2 — software/firmware version component for embedded products (e.g. "fw 2.5.0"). */
  software_version: string | null;
  release_status: ReleaseStatus;
  classification_snapshot: ProductClassification;
  conformity_route_snapshot: ConformityRoute;
  planned_release_date: string | null;
  actual_release_date: string | null;

  /** Gap 3 — date the EU market placement event occurred (CRA Art. 3(20)). Null until placed. */
  placed_on_market_date: string | null;

  /** Gap 2 — for non-substantial updates: ID of the release whose placement date this version inherits. */
  parent_release_id: string | null;

  /** Art. 13(7) + Art. 3(30): ID of the SubstantialModificationAssessment documenting the substantiality determination for this release. Required for v2+. */
  substantiality_analysis_id: string | null;

  /** Gap 5 — Art. 13(10): this release provides consolidated security coverage for all prior versions. */
  is_consolidated_support_version: boolean;

  /** Gap 1 — CRA Art. 13(2): true if the release contains known exploitable vulnerabilities. */
  has_known_exploitable_vulnerabilities: boolean;
  /** Gap 1 — Free-text description of any known exploitable vulnerabilities. */
  kev_notes: string | null;

  /** CRA Art. 28 — Date the EU Declaration of Conformity was drawn up. Must be ≤ placed_on_market_date. */
  eu_doc_date: string | null;
  /** CRA Art. 28 + Annex V — Manufacturer's unique reference number for this DoC. */
  eu_doc_number: string | null;
  /** CRA Art. 28 + Annex V — Notified body name/ref; only applicable for third-party conformity route. */
  eu_doc_notified_body: string | null;

  created_at: string;
  updated_at: string;
}

// ProductReleaseRead is the canonical full release object; defined in release-gate.ts
// where it is co-located with the rest of the release-gate workflow types.
export type { ProductReleaseRead } from "@/types/release-gate";

export interface ProductReleaseCreate {
  product_id: string;
  user_version?: string | null;
  release_status?: ReleaseStatus;
  classification_snapshot: ProductClassification;
  conformity_route_snapshot: ConformityRoute;
  planned_release_date?: string | null;
  actual_release_date?: string | null;
  /** Gap 3 — formal EU placement date, set when the release reaches the EU market. */
  placed_on_market_date?: string | null;
  release_notes?: string | null;
  /** Gap 2 — ID of the base release this non-substantial update derives placement date from. */
  parent_release_id?: string | null;
  /** Art. 13(7): ID of the SubstantialModificationAssessment for this release. Required for v2+. */
  substantiality_analysis_id?: string | null;
  /** Gap 5 — mark this release as the Art. 13(10) consolidated support version. */
  is_consolidated_support_version?: boolean;
  /** Optional CRA traceability link to a substantial change that triggered this release. */
  caused_by_change_id?: string | null;
  /** CRA Art. 28 — Date the EU DoC was drawn up. Must be on or before placed_on_market_date. */
  eu_doc_date?: string | null;
  /** CRA Art. 28 + Annex V — Unique reference number for this DoC. */
  eu_doc_number?: string | null;
  /** CRA Art. 28 + Annex V — Notified body name/ref for third-party conformity route. */
  eu_doc_notified_body?: string | null;
  /** Gap 2 — hardware revision label for embedded products (e.g. "PCB Rev 2.1"). */
  hardware_version?: string | null;
  /** Gap 2 — software/firmware version for embedded products (e.g. "fw 2.5.0"). */
  software_version?: string | null;
  /** Gap 1 — IDs of remote processing elements in scope for this release. */
  remote_processing_element_ids?: string[];
}

export type RemoteProcessingElementType =
  | "saas"
  | "internal_cloud"
  | "external_api"
  | "backend_service"
  | "data_processing"
  | "firmware_update"
  | "other";

export type RemoteProcessingClassification =
  | "not_assessed"
  | "cra_art_3_2_in_scope"
  | "third_party_component"
  | "out_of_scope"
  | "requires_legal_assessment";

export interface RemoteProcessingElementSummaryRead {
  id: string;
  name: string;
  provider_name: string | null;
  geographic_location: string | null;
  criticality: string | null;
  element_type: RemoteProcessingElementType | null;
  classification: RemoteProcessingClassification;
  created_at: string;
  updated_at: string;
}

export interface RemoteProcessingElementRead extends RemoteProcessingElementSummaryRead {
  product_id: string;
  description: string;
  data_processed: string | null;
  /** Criterion 1: Designed/developed by or on behalf of the manufacturer for this product. */
  is_developed_by_manufacturer: boolean | null;
  /** Criterion 2: Necessary for the product to perform its functions. */
  is_necessary_for_product_function: boolean | null;
  /** Criterion 3: Directly interacts with the product itself. */
  directly_interacts_with_product: boolean | null;
  /** Criterion 4: Bidirectional data exchange — product sends, RDPS processes and returns. */
  has_bidirectional_exchange: boolean | null;
  /** Context: is the third-party provider already covered by NIS2 MSP rules? */
  provider_is_nis2_msp: boolean | null;
  classification_rationale: string | null;
  assessed_at: string | null;
  assessed_by_user_id: string | null;
  /** Display name of the user who ran the evaluation (resolved from assessed_by). */
  assessed_by_name: string | null;
}

export interface RemoteProcessingElementCreate {
  product_id: string;
  name: string;
  description: string;
  provider_name: string | null;
  data_processed: string | null;
  geographic_location: string | null;
  criticality: string | null;
  element_type: RemoteProcessingElementType | null;
}

export interface RemoteProcessingElementUpdate {
  name?: string;
  description?: string;
  provider_name?: string | null;
  data_processed?: string | null;
  geographic_location?: string | null;
  criticality?: string | null;
  element_type?: RemoteProcessingElementType | null;
}

export interface RemoteProcessingAssessRequest {
  /** Criterion 1: Designed/developed by or on behalf of the manufacturer for this product. */
  is_developed_by_manufacturer: boolean | null;
  /** Criterion 2: Necessary for the product to perform its functions. */
  is_necessary_for_product_function: boolean | null;
  /** Criterion 3: Directly interacts with the product itself (not just with users). */
  directly_interacts_with_product: boolean | null;
  /** Criterion 4: Bidirectional data exchange (product → RDPS processes → result returned). */
  has_bidirectional_exchange: boolean | null;
  /** Context: is the provider covered by NIS2 as a Managed Service Provider? */
  provider_is_nis2_msp: boolean | null;
  classification_rationale: string | null;
  classification_override: RemoteProcessingClassification | null;
}

export interface ProductRead {
  id: string;
  product_code: string;
  name: string;
  description: string | null;
  parent_product_id: string | null;
  manufacturer_name: string;
  /** CRA Annex V(2) — manufacturer's registered trade address (for the DoC). */
  manufacturer_address?: string | null;
  intended_use: string;
  product_type: string;
  current_classification: ProductClassification;
  scope_status: ScopeStatus | string;
  /** CRA obligation tier: legacy (reporting-only) vs active (full obligations). */
  lifecycle_status: ProductLifecycleStatus;
  /** Phase 3 — typed classification (software vs hardware+digital). */
  product_type_class: ProductType;
  /** Phase 3 — product-level conformity assessment route. */
  conformity_route: ConformityRoute;
  /** Phase 2 — out-of-scope decision provenance. */
  out_of_scope_justification: string | null;
  scope_decided_by_user_id: string | null;
  scope_decided_at: string | null;
  scope_decision_signature: string | null;
  /** Resolved display name of the user who signed the scope decision. */
  scope_decided_by_name: string | null;
  /** Phase 4 — system-as-product profile (null when not sold as a system). */
  system_profile_json: SystemProfile | null;
  /** Phase 4 — tailor-made B2B contract terms (null when not tailor-made). */
  tailor_made_terms_json: TailorMadeTerms | null;
  /** Gap 2 — true when this product combines hardware and software/firmware. */
  is_embedded_product: boolean;
  /** Gap 4 — Art. 69(2): true for products on the market before CRA full applicability. */
  is_pre_cra: boolean;
  /** Gap 4 — earliest known EU market placement date for this product line. */
  first_placed_on_market_date: string | null;
  /** Economic operators (CRA Art. 13, 18–23) — free-text supply-chain descriptions. */
  authorised_representative: string | null;
  importers: string | null;
  distributors: string | null;
  single_point_of_contact: string | null;
  created_at: string;
  updated_at: string;
}

export interface ProductDetailRead extends ProductRead {
  child_products: ProductHierarchyNode[];
  releases: ProductReleaseSummaryRead[];
  remote_processing_elements: RemoteProcessingElementSummaryRead[];
}

export interface ProductCreate {
  product_code: string;
  name: string;
  description?: string | null;
  parent_product_id?: string | null;
  manufacturer_name: string;
  /** CRA Annex V(2) — manufacturer's registered trade address (for the DoC). */
  manufacturer_address?: string | null;
  intended_use: string;
  product_type: string;
  current_classification: ProductClassification;
  scope_status: ScopeStatus | string;
  /** CRA obligation tier: legacy (reporting-only) vs active (full obligations). */
  lifecycle_status?: ProductLifecycleStatus;
  /** Phase 3 — typed classification (software vs hardware+digital). */
  product_type_class?: ProductType;
  /** Phase 3 — product-level conformity assessment route. */
  conformity_route?: ConformityRoute;
  /** Gap 2 — true when the product combines hardware and firmware/software. */
  is_embedded_product?: boolean;
  /** Gap 4 — Art. 69(2) flag; defaults to false for new products created after CRA. */
  is_pre_cra?: boolean;
  first_placed_on_market_date?: string | null;
  /** Economic operators (CRA Art. 13, 18–23). */
  authorised_representative?: string | null;
  importers?: string | null;
  distributors?: string | null;
  single_point_of_contact?: string | null;
}

export interface ProductUpdate {
  /** Product code can be corrected post-creation if a naming error was made. */
  product_code?: string;
  name?: string;
  description?: string | null;
  parent_product_id?: string | null;
  manufacturer_name?: string;
  /** CRA Annex V(2) — manufacturer's registered trade address (for the DoC). */
  manufacturer_address?: string | null;
  intended_use?: string;
  product_type?: string;
  current_classification?: ProductClassification;
  scope_status?: ScopeStatus | string;
  /** CRA obligation tier: legacy (reporting-only) vs active (full obligations). */
  lifecycle_status?: ProductLifecycleStatus;
  /** Phase 3 — typed classification (software vs hardware+digital). */
  product_type_class?: ProductType;
  /** Phase 3 — product-level conformity assessment route. */
  conformity_route?: ConformityRoute;
  /** Phase 2 — manual entry/refinement of the out-of-scope decision. */
  out_of_scope_justification?: string | null;
  scope_decision_signature?: string | null;
  /** Phase 4 — system & tailor-made metadata. */
  system_profile_json?: SystemProfile | null;
  tailor_made_terms_json?: TailorMadeTerms | null;
  /** Gap 2 — update the embedded product flag when the product's hardware nature is confirmed. */
  is_embedded_product?: boolean;
  /** Gap 4 — update the pre-CRA flag when a product's status is clarified. */
  is_pre_cra?: boolean;
  first_placed_on_market_date?: string | null;
  /** Economic operators (CRA Art. 13, 18–23). */
  authorised_representative?: string | null;
  importers?: string | null;
  distributors?: string | null;
  single_point_of_contact?: string | null;
}

export interface ProductScopeEvaluationRequest {
  is_digital_product: boolean;
  has_network_connectivity: boolean;
  performs_remote_data_processing: boolean;
  safety_component: boolean;
  used_in_critical_sector: boolean;
  handles_sensitive_functions: boolean;
  excluded_category: boolean;
  notes?: string | null;
}

export interface ProductScopeEvaluationRead extends ProductScopeEvaluationRequest {
  id: string;
  product_id: string;
  in_scope: boolean;
  rationale: string;
  recommended_classification: ProductClassification;
  suggested_conformity_route: ConformityRoute;
  created_at: string;
  updated_at: string;
}
export type SupportType = "standard" | "limited" | "extended" | "custom";

export type DistributionMechanism =
  | "automatic_update"
  | "in_app_update"
  | "package_repository"
  | "vendor_download"
  | "manual_install"
  | "field_service"
  | "other";

export type SecurityUpdateSeverity =
  | "critical"
  | "high"
  | "medium"
  | "low"
  | "informational";

export type LifecycleNotificationType = "end_of_support_upcoming" | "security_update_available";

export type LifecycleNotificationStatus = "pending" | "sent" | "dismissed";

export interface SupportPeriodRecordRead {
  id: string;
  product_id: string;
  /** Gap 1 — if set, this record applies to a specific release not the whole product. */
  product_release_id: string | null;
  support_start_date: string;
  support_end_date: string;
  notify_before_days: number;
  support_type: SupportType;
  recipient_user_ids: string[];
  justification_text: string;
  expected_use_time_text: string | null;
  comparable_products_text: string | null;
  third_party_support_constraints_text: string | null;
  user_facing_summary: string | null;
  packaging_summary: string | null;
  eos_notification_sent_at: string | null;
  is_active: boolean;
  superseded_by_id: string | null;
  recipients: SupportPeriodNotificationRecipientRead[];
  /** Audit trail — user who created or versioned this record. */
  created_by_user_id: string | null;
  created_by_user_name: string | null;
  /** Required when updating an existing record — explains why the change was made. */
  change_reason: string | null;
  created_at: string;
  updated_at: string;
}

export interface SupportPeriodRecordCreate {
  product_id: string;
  /** Gap 1 — link to a specific release for per-version support periods (CRA §117). */
  product_release_id?: string | null;
  support_start_date: string;
  support_end_date: string;
  notify_before_days: number;
  support_type: SupportType;
  recipient_user_ids: string[];
  justification_text: string;
  expected_use_time_text?: string | null;
  comparable_products_text?: string | null;
  third_party_support_constraints_text?: string | null;
  user_facing_summary?: string | null;
  packaging_summary?: string | null;
}

export interface SupportPeriodRecordUpdate {
  /** Required — must explain why the support period is being changed. */
  change_reason: string;
  support_start_date?: string;
  support_end_date?: string;
  notify_before_days?: number;
  support_type?: SupportType;
  recipient_user_ids?: string[];
  justification_text?: string;
  expected_use_time_text?: string | null;
  comparable_products_text?: string | null;
  third_party_support_constraints_text?: string | null;
  user_facing_summary?: string | null;
  packaging_summary?: string | null;
}

export interface SupportPeriodRecordHistoryRead {
  product_id: string;
  records: SupportPeriodRecordRead[];
}

export interface SupportPeriodNotificationRecipientRead {
  id: string;
  user_id: string;
  full_name: string;
  email: string;
}

export interface SupportPeriodNotificationRecipientOptionRead {
  id: string;
  email: string;
  full_name: string;
  roles: string[];
}

export interface SupportPeriodSnippetGenerateRequest {
  product_id: string;
  support_start_date: string;
  support_end_date: string;
  support_type: SupportType;
  justification_text: string;
  expected_use_time_text?: string | null;
  comparable_products_text?: string | null;
  third_party_support_constraints_text?: string | null;
}

export interface SupportPeriodSnippetRead {
  user_facing_summary: string;
  packaging_summary: string;
}

export interface SecurityUpdateRead {
  id: string;
  product_release_id: string;
  title: string;
  description: string | null;
  severity: SecurityUpdateSeverity | null;
  is_security_only: boolean;
  integrity_info: string | null;
  cves_addressed_json: string[] | Record<string, unknown>;
  affected_versions_json: string[] | Record<string, unknown>;
  update_channels_json: string[];
  distribution_mechanism: DistributionMechanism;
  available_until: string | null;
  released_at: string | null;
  /** Gap 5 — numeric CVSS score (0.0–10.0). */
  cvss_score: number | null;
  /** Gap 5 — CVSS vector string, e.g. "CVSS:3.1/AV:N/AC:L/...". */
  cvss_vector: string | null;
  /** Gap 5 — external CVE database links (NVD, MITRE, vendor advisories). */
  cve_links_json: string[];
  /** Gap 8 — date the vulnerability was discovered, anchoring the remediation SLA. */
  vulnerability_discovered_at: string | null;
  /** Gap 8 — deadline for fix delivery ("without delay", CRA Annex I Part II §2). */
  remediation_deadline: string | null;
  /** Gap 9 — Annex I Part II §8: security updates must be free of charge. */
  is_free_of_charge: boolean;
  created_at: string;
  updated_at: string;
}

export interface SecurityUpdateCreate {
  product_release_id: string;
  title: string;
  description?: string | null;
  severity?: SecurityUpdateSeverity | null;
  is_security_only?: boolean;
  integrity_info?: string | null;
  cves_addressed_json: string[] | Record<string, unknown>;
  affected_versions_json: string[] | Record<string, unknown>;
  update_channels_json?: string[];
  distribution_mechanism: DistributionMechanism;
  available_until?: string | null;
  released_at?: string | null;
  cvss_score?: number | null;
  cvss_vector?: string | null;
  cve_links_json?: string[];
  vulnerability_discovered_at?: string | null;
  remediation_deadline?: string | null;
  is_free_of_charge?: boolean;
}

export interface SecurityUpdateUpdate {
  title?: string;
  description?: string | null;
  severity?: SecurityUpdateSeverity | null;
  is_security_only?: boolean | null;
  integrity_info?: string | null;
  cves_addressed_json?: string[] | Record<string, unknown>;
  affected_versions_json?: string[] | Record<string, unknown>;
  update_channels_json?: string[] | null;
  distribution_mechanism?: DistributionMechanism;
  available_until?: string | null;
  released_at?: string | null;
  cvss_score?: number | null;
  cvss_vector?: string | null;
  cve_links_json?: string[];
  vulnerability_discovered_at?: string | null;
  remediation_deadline?: string | null;
  is_free_of_charge?: boolean | null;
}

// ── Gap 2: CVD Policy ──────────────────────────────────────────────────────
export type CvdPolicyStatus = "draft" | "active" | "archived";

export interface CvdPolicyRead {
  id: string;
  product_id: string;
  status: CvdPolicyStatus;
  // Contact & reporting channels
  contact_email: string | null;
  pgp_key_url: string | null;
  security_txt_url: string | null;
  bug_bounty_url: string | null;
  // Timelines
  response_sla_hours: number;
  disclosure_window_days: number;
  // Legal & researcher relations
  safe_harbor: boolean;
  acknowledgement_offered: boolean;
  // Scope
  scope_description: string | null;
  out_of_scope_description: string | null;
  supported_versions: string | null;
  // Policy document
  policy_url: string | null;
  policy_text: string | null;
  created_at: string;
  updated_at: string;
}

export interface CvdPolicyCreate {
  product_id: string;
  status?: CvdPolicyStatus;
  contact_email?: string | null;
  pgp_key_url?: string | null;
  security_txt_url?: string | null;
  bug_bounty_url?: string | null;
  response_sla_hours?: number;
  disclosure_window_days?: number;
  safe_harbor?: boolean;
  acknowledgement_offered?: boolean;
  scope_description?: string | null;
  out_of_scope_description?: string | null;
  supported_versions?: string | null;
  policy_url?: string | null;
  policy_text?: string | null;
}

export interface CvdPolicyUpdate {
  status?: CvdPolicyStatus;
  contact_email?: string | null;
  pgp_key_url?: string | null;
  security_txt_url?: string | null;
  bug_bounty_url?: string | null;
  response_sla_hours?: number;
  disclosure_window_days?: number;
  safe_harbor?: boolean;
  acknowledgement_offered?: boolean;
  scope_description?: string | null;
  out_of_scope_description?: string | null;
  supported_versions?: string | null;
  policy_url?: string | null;
  policy_text?: string | null;
}

// ── Gaps 3 & 7: Security Advisory ─────────────────────────────────────────
export type AdvisoryStatus = "draft" | "embargo" | "published" | "archived";

/** A release an advisory affects (for display). */
export interface AdvisoryReleaseRef {
  id: string;
  display_version: string;
  release_status: string;
}

export interface SecurityAdvisoryRead {
  id: string;
  product_id: string;
  product_name: string | null;
  releases: AdvisoryReleaseRef[];
  advisory_id: string;
  title: string;
  summary: string | null;
  severity: SecurityUpdateSeverity | null;
  status: AdvisoryStatus;
  cve_ids_json: string[];
  affected_versions_json: string[] | Record<string, unknown>;
  fixed_in_versions_json: string[];
  workaround: string | null;
  remediation_steps: string | null;
  embargo_until: string | null;
  published_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface SecurityAdvisoryCreate {
  product_id: string;
  /** Affected release ids. Ignored when all_releases is true. */
  release_ids?: string[];
  /** Snapshot every current release of the product at creation time. */
  all_releases?: boolean;
  advisory_id: string;
  title: string;
  summary?: string | null;
  severity?: SecurityUpdateSeverity | null;
  status?: AdvisoryStatus;
  cve_ids_json?: string[];
  affected_versions_json?: string[] | Record<string, unknown>;
  fixed_in_versions_json?: string[];
  workaround?: string | null;
  remediation_steps?: string | null;
  embargo_until?: string | null;
  published_at?: string | null;
}

export interface SecurityAdvisoryUpdate {
  title?: string;
  summary?: string | null;
  severity?: SecurityUpdateSeverity | null;
  status?: AdvisoryStatus;
  cve_ids_json?: string[];
  affected_versions_json?: string[] | Record<string, unknown>;
  fixed_in_versions_json?: string[];
  workaround?: string | null;
  remediation_steps?: string | null;
  embargo_until?: string | null;
  published_at?: string | null;
  /** When provided, replaces the advisory's affected-release set. */
  release_ids?: string[];
}

// ── Gap 6: Vulnerability Report lifecycle ─────────────────────────────────
export type VulnerabilityLifecycleStatus =
  | "reported"
  | "triaged"
  | "fix_in_progress"
  | "fixed"
  | "embargo"
  | "disclosed"
  | "retired";

/** CRA Art. 13(2): VEX (Vulnerability Exploitability eXchange) status for a vulnerability finding. */
export type VexStatus = "not_affected" | "affected" | "fixed" | "under_investigation";

/** Whether a vulnerability report was filed manually or discovered via SBOM CVE scan. */
export type VulnerabilitySource = "manual" | "sbom_scan";
export type VulnerabilityPriority = "critical" | "high" | "medium" | "low" | "informational" | "needs_review";
export type VulnerabilityExposure = "external" | "internal" | "unknown";
export type AssetCriticality = "critical" | "high" | "medium" | "low" | "unknown";

export interface VulnerabilityReportRead {
  id: string;
  product_release_id: string;
  title: string;
  description: string | null;
  reporter_name: string | null;
  reporter_email: string | null;
  status: VulnerabilityLifecycleStatus;
  severity: SecurityUpdateSeverity | null;
  cvss_score: number | null;
  exposure: VulnerabilityExposure;
  asset_criticality: AssetCriticality;
  impact_level: SecurityUpdateSeverity | null;
  priority: VulnerabilityPriority;
  priority_rule_id: string | null;
  priority_rule_name: string | null;
  priority_policy_id: string | null;
  priority_policy_version: number | null;
  priority_reason: string | null;
  priority_evaluated_at: string | null;
  cve_ids_json: string[];
  discovered_at: string | null;
  remediation_deadline: string | null;
  fixed_at: string | null;
  disclosed_at: string | null;
  linked_security_update_id: string | null;
  linked_advisory_id: string | null;
  assigned_to_user_id: string | null;
  assigned_to_user_name: string | null;
  due_date: string | null;
  responsible_team: string | null;
  remediation_plan: string | null;
  resolution_summary: string | null;
  external_ticket_system: string | null;
  external_ticket_id: string | null;
  external_ticket_url: string | null;
  external_ticket_status: string | null;
  remediation_started_at: string | null;
  escalation_level: number;
  last_escalated_at: string | null;
  created_at: string;
  updated_at: string;
  // Exploitability assessment fields (CRA Art. 13(2))
  source: VulnerabilitySource;
  sbom_finding_id: string | null;
  supplier_component_id: string | null;
  supplier_component_name: string | null;
  supplier_id: string | null;
  supplier_name: string | null;
  affected_supplier_releases: Array<{ product_id:string; product_name:string; release_id:string; release_version:string }>;
  vex_status: VexStatus | null;
  is_exploitable: boolean | null;
  exploitability_rationale: string | null;
  operational_conditions: string | null;
  exploitability_assessed_by_id: string | null;
  exploitability_assessed_at: string | null;
  /** EPSS probability score from api.first.org — denormalized from linked SBOM finding. Null for manual reports. */
  epss_score: number | null;
  /** EPSS percentile rank [0.0–1.0] among all scored CVEs. */
  epss_percentile: number | null;
  /** True if CISA's Known Exploited Vulnerabilities catalog lists this CVE. */
  is_known_exploited: boolean;
  kev_date_added: string | null;
  kev_due_date: string | null;
  kev_required_action: string | null;
  kev_known_ransomware_campaign_use: string | null;
  // ENISA SRP vulnerability-specific fields (v14–v26)
  /** v14 — ENISA European Vulnerability Database ID (separate from CVE). */
  euvd_id: string | null;
  /** v18 — actions the manufacturer has taken to fix or mitigate the vulnerability. */
  corrective_measures_taken: string | null;
  /** v19 — guidance for product users (patches to apply, config changes, workarounds). */
  user_corrective_measures: string | null;
  /** v20 — whether this report contains sensitive information that should not be publicly disseminated. */
  information_sensitivity: string | null;
  /** v24 — impact of the vulnerability, e.g. remote code execution, data exfiltration, denial of service. */
  vulnerability_impact: string | null;
  /** v25 — known or suspected threat actor actively exploiting this vulnerability. */
  malicious_actor_info: string | null;
  // CRA Art. 14 — ENISA Single Reporting Platform fields
  /** True when the manufacturer confirms reliable evidence of active exploitation (Art. 3(42)) requiring ENISA notification. */
  enisa_reporting_required: boolean;
  enisa_reference_number: string | null;
  enisa_early_warning_sent_at: string | null;
  enisa_initial_report_sent_at: string | null;
  enisa_final_report_sent_at: string | null;
  /** Computed: discovered_at + 24h. Null when enisa_reporting_required is false or discovered_at unset. */
  enisa_early_warning_deadline: string | null;
  /** Computed: discovered_at + 72h. */
  enisa_initial_report_deadline: string | null;
  /** Computed: fixed_at + 14 days. Null when no fix date yet ("Pending fix"). */
  enisa_final_report_deadline: string | null;
}

export interface VulnerabilityReportCreate {
  product_release_id: string;
  title: string;
  description?: string | null;
  reporter_name?: string | null;
  reporter_email?: string | null;
  status?: VulnerabilityLifecycleStatus;
  severity?: SecurityUpdateSeverity | null;
  cvss_score?: number | null;
  exposure?: VulnerabilityExposure;
  asset_criticality?: AssetCriticality;
  impact_level?: SecurityUpdateSeverity | null;
  cve_ids_json?: string[];
  discovered_at?: string | null;
  remediation_deadline?: string | null;
  fixed_at?: string | null;
  disclosed_at?: string | null;
  linked_security_update_id?: string | null;
  linked_advisory_id?: string | null;
}

export interface VulnerabilityReportUpdate {
  title?: string;
  description?: string | null;
  reporter_name?: string | null;
  reporter_email?: string | null;
  status?: VulnerabilityLifecycleStatus;
  severity?: SecurityUpdateSeverity | null;
  cvss_score?: number | null;
  exposure?: VulnerabilityExposure;
  asset_criticality?: AssetCriticality;
  impact_level?: SecurityUpdateSeverity | null;
  cve_ids_json?: string[];
  discovered_at?: string | null;
  remediation_deadline?: string | null;
  fixed_at?: string | null;
  disclosed_at?: string | null;
  linked_security_update_id?: string | null;
  linked_advisory_id?: string | null;
  assigned_to_user_id?: string | null;
  due_date?: string | null;
  euvd_id?: string | null;
  corrective_measures_taken?: string | null;
  user_corrective_measures?: string | null;
  information_sensitivity?: string | null;
  vulnerability_impact?: string | null;
  malicious_actor_info?: string | null;
  enisa_reporting_required?: boolean;
  enisa_reference_number?: string | null;
}

export interface VulnerabilityRemediationUpdate {
  assigned_to_user_id?: string | null;
  responsible_team?: string | null;
  due_date?: string | null;
  remediation_plan?: string | null;
  resolution_summary?: string | null;
  external_ticket_system?: string | null;
  external_ticket_id?: string | null;
  external_ticket_url?: string | null;
  external_ticket_status?: string | null;
  status?: VulnerabilityLifecycleStatus;
}

export interface VulnerabilityRemediationBulkUpdate {
  report_ids: string[];
  assigned_to_user_id?: string | null;
  responsible_team?: string | null;
  due_date?: string | null;
}

/** Payload to record an exploitability assessment for a vulnerability (CRA Art. 13(2)). */
export interface ExploitabilityAssessmentUpdate {
  vex_status: VexStatus;
  exploitability_rationale?: string | null;
  operational_conditions?: string | null;
}

/** Payload for ENISA Art. 14 mark-sent endpoints. */
export interface EnisaMarkSentRequest {
  /** ISO datetime — defaults to server-side now() when omitted. */
  sent_at?: string | null;
  /** SRP reference number issued by the national CSIRT/ENISA platform. */
  reference_number?: string | null;
}

export type PriorityField = "severity" | "cvss_score" | "epss_score" | "is_known_exploited" | "exposure" | "asset_criticality" | "impact_level" | "is_exploitable" | "source" | "status";
export type PriorityOperator = "eq" | "neq" | "gte" | "gt" | "lte" | "lt";

export interface PriorityCondition {
  field: PriorityField;
  operator: PriorityOperator;
  value: string | number | boolean;
}

export interface PriorityRule {
  id: string;
  name: string;
  enabled: boolean;
  priority: VulnerabilityPriority;
  conditions: PriorityCondition[];
}

export interface PriorityPolicyRead {
  id: string;
  name: string;
  description: string | null;
  change_reason: string | null;
  version: number;
  is_active: boolean;
  rules: PriorityRule[];
  created_by_user_id: string | null;
  created_by_name: string | null;
  created_at: string;
}

export interface PriorityPolicyPublish {
  name: string;
  description?: string | null;
  change_reason?: string | null;
  rules: PriorityRule[];
}

export interface PriorityEvaluationRead {
  id: string;
  vulnerability_report_id: string;
  policy_id: string | null;
  policy_version: number;
  priority: VulnerabilityPriority;
  rule_id: string | null;
  rule_name: string | null;
  reason: string;
  inputs_json: Record<string, unknown>;
  trigger: string;
  actor_user_id: string | null;
  actor_user_name: string | null;
  evaluated_at: string;
}

export interface PriorityPreviewRead {
  counts: Record<VulnerabilityPriority, number>;
  total: number;
}

// ── Gap 10: SBOM Vulnerability Findings ──────────────────────────────────
/** A CVE/vulnerability finding linked to a specific SBOM component via OSV scan. */
export interface SbomVulnerabilityFindingRead {
  id: string;
  sbom_record_id: string;
  component_name: string;
  component_version: string | null;
  component_purl: string | null;
  vuln_id: string;
  aliases_json: string[];
  severity: SecurityUpdateSeverity | null;
  cvss_score: number | null;
  cvss_vector: string | null;
  summary: string | null;
  published_at: string | null;
  fixed_in_versions_json: string[];
  linked_report_id: string | null;
  /** Scanner(s) that detected this finding: ["osv"], ["trivy"], or ["osv","trivy"]. */
  sources_json: string[];
  created_at: string;
  updated_at: string;
  /** EPSS probability score [0.0–1.0] that this CVE will be exploited in the wild. Null if not yet fetched. */
  epss_score: number | null;
  /** EPSS percentile rank [0.0–1.0] among all scored CVEs. */
  epss_percentile: number | null;
  /** ISO timestamp of when the EPSS score was last fetched. */
  epss_fetched_at: string | null;
  /** CISA KEV match: public evidence that this CVE is exploited in the wild. */
  is_known_exploited: boolean;
  kev_date_added: string | null;
  kev_due_date: string | null;
  kev_required_action: string | null;
  kev_known_ransomware_campaign_use: string | null;
  kev_fetched_at: string | null;
}

/** Result returned by the SBOM vulnerability scan endpoint. */
export interface SbomScanResult {
  findings_created: number;
  reports_created: number;
  /** Number of SBOM components that had a recognised ecosystem PURL and were queried. */
  components_scanned: number;
  /** False when the OSV API was unreachable — findings may be incomplete. */
  osv_reachable: boolean;
  /** Whether the Trivy CLI was installed and ran during this scan. */
  trivy_available: boolean;
  /** Number of findings that received CVSS data from NVD (were missing it from OSV/Trivy). */
  nvd_enrichments: number;
  /** Number of findings that received EPSS scores from api.first.org. */
  epss_enrichments: number;
  /** Number of scanned CVEs present in CISA's KEV catalog. */
  kev_matches: number;
  /** Per-scanner finding counts: {osv, trivy, both}. */
  per_scanner: Record<string, number>;
}

/** One recorded scan execution (manual / scheduled / on_upload). */
export interface SbomScanRunRead {
  id: string;
  created_at: string;
  sbom_record_id: string;
  /** "manual" | "scheduled" | "on_upload". */
  trigger: string;
  /** "completed" | "degraded" | "failed". */
  status: string;
  findings_created: number;
  reports_created: number;
  components_scanned: number;
  nvd_enrichments: number;
  epss_enrichments: number;
  osv_reachable: boolean;
  trivy_available: boolean;
  error: string | null;
  duration_ms: number | null;
}

// ── Gap 10: SBOM Record ────────────────────────────────────────────────────
export type SbomFormat = "cyclonedx" | "spdx" | "swid" | "other";

export interface SbomRecordRead {
  id: string;
  product_release_id: string;
  format: SbomFormat;
  spec_version: string | null;
  components_json: Record<string, unknown>[];
  component_count: number | null;
  file_name: string | null;
  tool_name: string | null;
  tool_version: string | null;
  generated_at: string | null;
  notes: string | null;
  created_at: string;
  updated_at: string;
  /** Raw SBOM file content stored for re-analysis (may be null for manually created records). */
  sbom_content: string | null;
  /** Quality score 0–100 from sbom-tools quality --profile security. Null if not yet analyzed. */
  quality_score: number | null;
  /** Full JSON output from sbom-tools validate + quality + diff runs. */
  analysis_findings: Record<string, unknown> | null;
}

export interface SbomRecordCreate {
  product_release_id: string;
  format?: SbomFormat;
  spec_version?: string | null;
  components_json?: Record<string, unknown>[];
  component_count?: number | null;
  file_name?: string | null;
  tool_name?: string | null;
  tool_version?: string | null;
  generated_at?: string | null;
  notes?: string | null;
}

export interface SbomRecordUpdate {
  format?: SbomFormat;
  spec_version?: string | null;
  components_json?: Record<string, unknown>[];
  component_count?: number | null;
  file_name?: string | null;
  tool_name?: string | null;
  tool_version?: string | null;
  generated_at?: string | null;
  notes?: string | null;
}

export interface LifecycleNotificationRead {
  id: string;
  support_period_record_id: string | null;
  security_update_id: string | null;
  recipient_user_id: string | null;
  notification_type: LifecycleNotificationType;
  status: LifecycleNotificationStatus;
  scheduled_for: string;
  sent_at: string | null;
  dismissed_at: string | null;
  title: string;
  message: string;
  recipient_user: {
    id: string;
    full_name: string;
    email: string;
  } | null;
  created_at: string;
  updated_at: string;
}

export interface LifecycleNotificationMarkSentRequest {
  sent_at?: string | null;
}

export interface LifecycleNotificationDismissRequest {
  dismissed_at?: string | null;
}

// ── CRA Art. 14 — Incident Reports ───────────────────────────────────────────

export type IncidentReportStatus = "reported" | "triaged" | "contained" | "resolved" | "closed";

export interface IncidentReportRead {
  id: string;
  product_release_id: string;
  title: string;
  status: IncidentReportStatus;
  suspected_malicious_act: boolean;
  incident_nature: string | null;
  detected_at: string | null;
  occurred_at: string | null;
  initial_assessment: string | null;
  corrective_measures_taken: string | null;
  user_corrective_measures: string | null;
  information_sensitivity: string | null;
  incident_impact_category: string | null;
  severity: SecurityUpdateSeverity | null;
  incident_impact: string | null;
  threat_type_root_cause: string | null;
  applied_mitigations: string | null;
  assigned_to_user_id: string | null;
  created_at: string;
  updated_at: string;
  enisa_reporting_required: boolean;
  enisa_reference_number: string | null;
  enisa_early_warning_sent_at: string | null;
  enisa_initial_report_sent_at: string | null;
  enisa_final_report_sent_at: string | null;
  enisa_early_warning_deadline: string | null;
  enisa_initial_report_deadline: string | null;
  enisa_final_report_deadline: string | null;
}

export interface IncidentReportCreate {
  product_release_id: string;
  title: string;
  suspected_malicious_act?: boolean;
  incident_nature?: string | null;
  detected_at?: string | null;
  occurred_at?: string | null;
  initial_assessment?: string | null;
  corrective_measures_taken?: string | null;
  user_corrective_measures?: string | null;
  information_sensitivity?: string | null;
  incident_impact_category?: string | null;
  severity?: SecurityUpdateSeverity | null;
  incident_impact?: string | null;
  threat_type_root_cause?: string | null;
  applied_mitigations?: string | null;
  enisa_reporting_required?: boolean;
}

export interface IncidentReportUpdate {
  title?: string;
  status?: IncidentReportStatus;
  suspected_malicious_act?: boolean;
  incident_nature?: string | null;
  detected_at?: string | null;
  occurred_at?: string | null;
  initial_assessment?: string | null;
  corrective_measures_taken?: string | null;
  user_corrective_measures?: string | null;
  information_sensitivity?: string | null;
  incident_impact_category?: string | null;
  severity?: SecurityUpdateSeverity | null;
  incident_impact?: string | null;
  threat_type_root_cause?: string | null;
  applied_mitigations?: string | null;
  assigned_to_user_id?: string | null;
  enisa_reporting_required?: boolean;
  enisa_reference_number?: string | null;
}

export interface IncidentEnisaMarkSentRequest {
  sent_at?: string | null;
  reference_number?: string | null;
}
