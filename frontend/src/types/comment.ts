// Supported entity types that can have comment threads.
export type CommentEntityType =
  | "vulnerability_report"
  | "change"
  | "market_action"
  | "risk_assessment"
  | "risk_item"
  | "release_gate"
  | "certification_record"
  | "sbom_record"
  | "security_advisory"
  | "cvd_policy"
  | "product"
  | "product_release";

export interface CommentAuthor {
  id: string;
  full_name: string | null;
  email: string;
}

export interface CommentRead {
  id: string;
  entity_type: string;
  entity_id: string;
  author_user_id: string;
  author: CommentAuthor | null;
  body: string;
  created_at: string;
  updated_at: string;
}

export interface CommentCreate {
  entity_type: string;
  entity_id: string;
  body: string;
}

export interface CommentUpdate {
  body: string;
}
