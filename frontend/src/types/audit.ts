export interface AuditActorRead {
  id: string | null;
  full_name: string | null;
  email: string | null;
}

export interface AuditEventRead {
  id: string;
  occurred_at: string;
  actor: AuditActorRead;
  action_type: string;
  entity_type: string;
  entity_id: string | null;
  status: string;
  summary: string;
  entity_label: string | null;
  product_id: string | null;
  product_release_id: string | null;
  details_json: Record<string, unknown>;
}

export interface AuditEventListRead {
  items: AuditEventRead[];
  total: number;
}

export interface AuditIntegrityIssueRead {
  sequence_number: number | null;
  event_id: string | null;
  reason: string;
}

export interface AuditIntegrityRead {
  verified: boolean;
  total_events: number;
  verified_events: number;
  latest_sequence_number: number | null;
  issues: AuditIntegrityIssueRead[];
}

export interface AuditEventListParams {
  entity_id?: string;
  product_id?: string;
  product_release_id?: string;
  actor_user_id?: string;
  action_type?: string;
  action_prefix?: string;
  entity_type?: string;
  limit?: number;
}
