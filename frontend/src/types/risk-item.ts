export type RiskLevel = "low" | "medium" | "high" | "critical";

export type RiskItemStatus =
  | "open"
  | "in_progress"
  | "mitigated"
  | "accepted"
  | "closed";

export interface RiskItemRead {
  id: string;
  risk_assessment_id: string;
  title: string;
  description: string;
  threat_scenario: string;
  asset_affected: string;
  likelihood: RiskLevel;
  impact: RiskLevel;
  risk_level: RiskLevel;
  mitigation_plan: string;
  residual_risk_level: RiskLevel | null;
  status: RiskItemStatus;
  owner_user_id: string | null;
  due_date: string | null;
  created_at: string;
  updated_at: string;
}

export interface RiskItemSummaryRead {
  id: string;
  risk_assessment_id: string;
  title: string;
  risk_level: RiskLevel;
  residual_risk_level: RiskLevel | null;
  status: RiskItemStatus;
}

export interface RiskItemCreate {
  risk_assessment_id: string;
  title: string;
  description: string;
  threat_scenario: string;
  asset_affected: string;
  likelihood: RiskLevel;
  impact: RiskLevel;
  risk_level: RiskLevel;
  mitigation_plan: string;
  residual_risk_level?: RiskLevel | null;
  status?: RiskItemStatus;
  owner_user_id?: string | null;
}

export interface RiskItemUpdate {
  title?: string;
  description?: string;
  threat_scenario?: string;
  asset_affected?: string;
  likelihood?: RiskLevel;
  impact?: RiskLevel;
  risk_level?: RiskLevel;
  mitigation_plan?: string;
  residual_risk_level?: RiskLevel | null;
  status?: RiskItemStatus;
  owner_user_id?: string | null;
  due_date?: string | null;
}

export type RiskItem = RiskItemRead;