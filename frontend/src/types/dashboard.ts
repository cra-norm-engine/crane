// CRANE — CRA Norm Engine
// Copyright (C) 2026 Ali Mohammad Hosseini
// SPDX-License-Identifier: AGPL-3.0-or-later
// This file is part of CRANE, free software under the GNU AGPL v3.0 or later.
// See <https://www.gnu.org/licenses/>.

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

// ── Compliance Journey (guided roadmap) ──────────────────────────────────────
// Mirrors backend schemas in app/schemas/release_journey.py. A journey is a
// computed, read-only checklist that sequences existing per-entity states into
// a step-by-step roadmap toward a CRA-ready release.

export type JourneyStepStatus =
  | "complete"
  | "in_progress"
  | "todo"
  | "blocked"
  | "not_applicable";

export interface JourneyStep {
  id: string;
  title: string;
  description: string;
  status: JourneyStepStatus;
  next_action: string;
  // Vue route target for the deep link (name + params + optional query + hash).
  route_name: string;
  route_params: Record<string, string>;
  route_query: Record<string, string>;
  route_hash: string | null;
}

export interface ReleaseJourney {
  release_id: string | null;
  product_id: string;
  product_name: string;
  version: string;
  release_status: string | null;
  completed_steps: number;
  total_steps: number;
  next_step_id: string | null;
  steps: JourneyStep[];
}

/** Annex I Part I coverage for a product's latest release. */
export interface ReadinessCoverage {
  total: number;
  assessed: number;
  met: number;
  assessed_pct: number;
  met_pct: number;
}

/** Readiness of one release (the honest per-release unit). */
export interface ReleaseReadinessRead {
  release_id: string;
  version_label: string;
  system_version: number;
  release_status: string;
  is_released: boolean;
  coverage: ReadinessCoverage;
  /** not_started | in_progress | substantially_ready | ready */
  state: string;
  /** This release's requirement assessment is formally approved. */
  is_approved: boolean;
}

/** A product grouping its releases' readiness (anchored on Annex I Part I). */
export interface ProductReadinessRead {
  product_id: string;
  product_code: string;
  name: string;
  scope_status: string;
  /** Every release, newest first, each with its own readiness. */
  releases: ReleaseReadinessRead[];
  /** The latest-released release used for roll-ups (null when none). */
  representative_release_id: string | null;
  /** Latest released release's assessment is approved (drives conformance). */
  is_conformant: boolean;
  // Secondary operational signals — product-scoped, informational only.
  has_open_critical_vuln: boolean;
  open_critical_vuln_count: number;
  risk_unapproved: boolean;
  support_expired: boolean;
  change_action_required: boolean;
}

/** High-level portfolio conformance summary (dashboard pie). */
export interface ConformanceSummary {
  total: number;
  in_scope: number;
  out_of_scope: number;
  conformant: number;
  not_conformant: number;
  /** % of in-scope products that are conformant (0 when in_scope === 0). */
  conformant_pct: number;
}
