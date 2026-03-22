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

export interface ProductRead {
  id: string;
  name: string;
  product_code: string;
  description: string | null;
  classification: ProductClassification;
  conformity_route: ConformityRoute;
  market_placement_blocked: boolean;
  support_period_months: number | null;
  created_at: string;
  updated_at: string;
}

export interface ProductCreate {
  name: string;
  product_code: string;
  description?: string | null;
  classification: ProductClassification;
  conformity_route: ConformityRoute;
  market_placement_blocked: boolean;
  support_period_months?: number | null;
}

export type ProductUpdate = Partial<Omit<ProductCreate, "product_code">>;