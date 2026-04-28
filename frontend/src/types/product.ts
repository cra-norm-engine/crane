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
}

export interface ProductHierarchyNode {
  id: string;
  product_code: string;
  name: string;
  current_classification: ProductClassification;
  scope_status: ScopeStatus | string;
}

export interface ProductReleaseSummaryRead {
  id: string;
  version: string;
  release_status:
    | "draft"
    | "in_review"
    | "blocked"
    | "approved"
    | "released"
    | "withdrawn"
    | "recalled"
    | "end_of_support";
  classification_snapshot: ProductClassification;
  conformity_route_snapshot: ConformityRoute;
  planned_release_date: string | null;
  actual_release_date: string | null;
  created_at: string;
  updated_at: string;
}

export interface ProductReleaseCreate {
  product_id: string;
  version: string;
  release_status?:
    | "draft"
    | "in_review"
    | "blocked"
    | "approved"
    | "released"
    | "withdrawn"
    | "recalled"
    | "end_of_support";
  classification_snapshot: ProductClassification;
  conformity_route_snapshot: ConformityRoute;
  planned_release_date?: string | null;
  actual_release_date?: string | null;
  release_notes?: string | null;
  // Optional CRA traceability link to a substantial change that triggered this release
  caused_by_change_id?: string | null;
}

export interface RemoteProcessingElementSummaryRead {
  id: string;
  name: string;
  provider_name: string | null;
  geographic_location: string | null;
  criticality: string | null;
  created_at: string;
  updated_at: string;
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
}

export interface ProductUpdate {
  name?: string;
  description?: string | null;
  parent_product_id?: string | null;
  manufacturer_name?: string;
  intended_use?: string;
  product_type?: string;
  current_classification?: ProductClassification;
  scope_status?: ScopeStatus | string;
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

export type LifecycleNotificationType = "end_of_support_upcoming";

export type LifecycleNotificationStatus = "pending" | "sent" | "dismissed";

export interface SupportPeriodRecordRead {
  id: string;
  product_id: string;
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
}

export interface LifecycleNotificationRead {
  id: string;
  support_period_record_id: string;
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
