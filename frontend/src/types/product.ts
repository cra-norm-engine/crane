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