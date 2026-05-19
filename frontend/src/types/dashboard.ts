export interface VulnSeverityBreakdown {
  critical: number;
  high: number;
  medium: number;
  low: number;
  total_open: number;
  overdue: number;
}

export interface RiskAssessmentSummary {
  total: number;
  draft: number;
  in_review: number;
  approved: number;
  archived: number;
}

export interface ProductSummary {
  total: number;
  in_scope: number;
  released: number;
}

export interface TaskSummary {
  total_open: number;
  overdue: number;
  due_this_week: number;
}

export interface ChangeSummary {
  total_open: number;
  action_required: number;
  substantial_open: number;
}

export interface UpcomingRelease {
  id: string;
  product_name: string | null;
  system_version: number;
  user_version: string | null;
  display_version: string;
  planned_date: string | null;
  days_until: number | null;
  release_status: string;
}

export interface ActivityItem {
  id: string;
  action_type: string;
  entity_type: string | null;
  actor_email: string | null;
  created_at: string;
  summary: string;
}

export interface LifecycleAlertSummary {
  total_active: number;
  expired: number;
  expiring_90d: number;
  expiring_180d: number;
  pending_alerts: number;
}

export interface DashboardRead {
  vulnerability_summary: VulnSeverityBreakdown;
  risk_summary: RiskAssessmentSummary;
  product_summary: ProductSummary;
  task_summary: TaskSummary;
  change_summary: ChangeSummary;
  lifecycle_summary: LifecycleAlertSummary;
  upcoming_releases: UpcomingRelease[];
  recent_activity: ActivityItem[];
  compliance_score: number;
}
