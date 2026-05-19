/** TypeScript types for MarketAction (CRA Art. 35 recalls and withdrawals, FR38/FR39). */

export type MarketActionType = "recall" | "withdrawal";

export type MarketActionStatus =
  | "draft"
  | "active"
  | "authority_notified"
  | "closed";

/** Minimal release info embedded in MarketActionRead. */
export interface ProductReleaseSummary {
  id: string;
  product_id: string;
  system_version: number;
  user_version: string | null;
  display_version: string;
}

export interface MarketActionRead {
  id: string;
  product_release_id: string;
  action_type: MarketActionType;
  status: MarketActionStatus;
  reason: string;
  affected_scope: string | null;
  corrective_action: string | null;
  authority_reference_number: string | null;
  authority_notified_at: string | null;
  user_notice_text: string | null;
  internal_notes: string | null;
  product_release: ProductReleaseSummary | null;
  created_at: string;
  updated_at: string;
}

export interface MarketActionCreate {
  product_release_id: string;
  action_type: MarketActionType;
  reason: string;
  affected_scope?: string | null;
  corrective_action?: string | null;
  authority_reference_number?: string | null;
  user_notice_text?: string | null;
  internal_notes?: string | null;
}

export interface MarketActionUpdate {
  action_type?: MarketActionType | null;
  status?: MarketActionStatus | null;
  reason?: string | null;
  affected_scope?: string | null;
  corrective_action?: string | null;
  authority_reference_number?: string | null;
  authority_notified_at?: string | null;
  user_notice_text?: string | null;
  internal_notes?: string | null;
}

export interface AuthorityNotifiedRequest {
  notified_at?: string | null;
}
