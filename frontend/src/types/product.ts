export type ProductClassification =
  | "normal"
  | "important_class_1"
  | "important_class_2"
  | "critical";

export type ConformityRoute =
  | "self_assessment"
  | "third_party_assessment"
  | "not_applicable"
  | "undecided";

export type ScopeStatus = "undecided" | "in_scope" | "out_of_scope";

export interface ProductSummaryRead {
  id: string;
  product_code: string;
  name: string;
  manufacturer_name: string;
  product_type: string;
  current_classification: ProductClassification;
  scope_status: ScopeStatus | string;
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
  /** I1: Designed/developed by or on behalf of the manufacturer for this product. */
  is_developed_by_manufacturer: boolean | null;
  /** I3: Necessary for the product to perform its functions. */
  is_necessary_for_product_function: boolean | null;
  /** I5: Directly interacts with the product itself. */
  directly_interacts_with_product: boolean | null;
  /** I6: Bidirectional data exchange — product sends, RDPS processes and returns. */
  has_bidirectional_exchange: boolean | null;
  /** Context: is the third-party provider already covered by NIS2 MSP rules? */
  provider_is_nis2_msp: boolean | null;
  classification_rationale: string | null;
  assessed_at: string | null;
  assessed_by_user_id: string | null;
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
  /** I1: Designed/developed by or on behalf of the manufacturer for this product. */
  is_developed_by_manufacturer: boolean | null;
  /** I3: Necessary for the product to perform its functions. */
  is_necessary_for_product_function: boolean | null;
  /** I5: Directly interacts with the product itself (not just with users). */
  directly_interacts_with_product: boolean | null;
  /** I6: Bidirectional data exchange (product → RDPS processes → result returned). */
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
  intended_use: string;
  product_type: string;
  current_classification: ProductClassification;
  scope_status: ScopeStatus | string;
  /** Gap 2 — true when this product combines hardware and software/firmware. */
  is_embedded_product: boolean;
  /** Gap 4 — Art. 69(2): true for products on the market before CRA full applicability. */
  is_pre_cra: boolean;
  /** Gap 4 — earliest known EU market placement date for this product line. */
  first_placed_on_market_date: string | null;
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
  intended_use: string;
  product_type: string;
  current_classification: ProductClassification;
  scope_status: ScopeStatus | string;
  /** Gap 2 — true when the product combines hardware and firmware/software. */
  is_embedded_product?: boolean;
  /** Gap 4 — Art. 69(2) flag; defaults to false for new products created after CRA. */
  is_pre_cra?: boolean;
  first_placed_on_market_date?: string | null;
}

export interface ProductUpdate {
  /** Product code can be corrected post-creation if a naming error was made. */
  product_code?: string;
  name?: string;
  description?: string | null;
  parent_product_id?: string | null;
  manufacturer_name?: string;
  intended_use?: string;
  product_type?: string;
  current_classification?: ProductClassification;
  scope_status?: ScopeStatus | string;
  /** Gap 2 — update the embedded product flag when the product's hardware nature is confirmed. */
  is_embedded_product?: boolean;
  /** Gap 4 — update the pre-CRA flag when a product's status is clarified. */
  is_pre_cra?: boolean;
  first_placed_on_market_date?: string | null;
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

export interface SecurityAdvisoryRead {
  id: string;
  product_release_id: string;
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
  linked_security_update_id: string | null;
  created_at: string;
  updated_at: string;
}

export interface SecurityAdvisoryCreate {
  product_release_id: string;
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
  linked_security_update_id?: string | null;
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
  linked_security_update_id?: string | null;
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

export interface VulnerabilityReportRead {
  id: string;
  product_release_id: string;
  title: string;
  description: string | null;
  reporter_name: string | null;
  reporter_email: string | null;
  status: VulnerabilityLifecycleStatus;
  severity: SecurityUpdateSeverity | null;
  cve_ids_json: string[];
  discovered_at: string | null;
  remediation_deadline: string | null;
  fixed_at: string | null;
  disclosed_at: string | null;
  linked_security_update_id: string | null;
  linked_advisory_id: string | null;
  assigned_to_user_id: string | null;
  due_date: string | null;
  created_at: string;
  updated_at: string;
  // Exploitability assessment fields (CRA Art. 13(2))
  source: VulnerabilitySource;
  sbom_finding_id: string | null;
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
  cve_ids_json?: string[];
  discovered_at?: string | null;
  remediation_deadline?: string | null;
  fixed_at?: string | null;
  disclosed_at?: string | null;
  linked_security_update_id?: string | null;
  linked_advisory_id?: string | null;
  assigned_to_user_id?: string | null;
  due_date?: string | null;
  enisa_reporting_required?: boolean;
  enisa_reference_number?: string | null;
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
  /** Per-scanner finding counts: {osv, trivy, both}. */
  per_scanner: Record<string, number>;
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
