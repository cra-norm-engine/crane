/**
 * TypeScript types for the Substantial Change Tracking feature.
 *
 * Mirrors the backend Pydantic schemas in backend/app/schemas/change.py.
 * Three groups:
 *   1. Change — the change record and its workflow lifecycle
 *   2. Assessment — the four CRA criteria and substantiality decision
 *   3. ComplianceAction — individual compliance tasks for substantial changes
 */

// ---------------------------------------------------------------------------
// Enum-style string unions
// ---------------------------------------------------------------------------

/**
 * Type of change being recorded.
 * security = security fix (never substantial per CRA Art. 3(4))
 * feature / repair / maintenance = may be substantial
 */
export type ChangeType = "security" | "feature" | "repair" | "maintenance";

/**
 * Workflow states a change moves through.
 * draft → submitted → under_review → assessed | action_required → closed
 */
export type ChangeStatus =
  | "draft"
  | "submitted"
  | "under_review"
  | "assessed"
  | "action_required"
  | "closed";

/**
 * Auto-created compliance obligations when a change is deemed substantial.
 * These correspond to CRA Art. 13 obligations triggered by a substantial modification.
 */
export type ComplianceActionType =
  | "renew_conformity_assessment"
  | "update_technical_docs"
  | "update_declaration_of_conformity"
  | "re_release_product";

/** Lifecycle status of a single compliance action item. */
export type ComplianceActionStatus = "pending" | "in_progress" | "completed";

// ---------------------------------------------------------------------------
// ComplianceAction schemas
// ---------------------------------------------------------------------------

/**
 * Read schema for a single compliance action item.
 * Nested inside AssessmentRead when a change is substantial.
 */
export interface ComplianceActionRead {
  id: string;
  created_at: string;
  updated_at: string;
  assessment_id: string;
  action_type: ComplianceActionType;
  action_status: ComplianceActionStatus;
  due_date: string | null;       // ISO date string
  notes: string | null;
  completed_by_user_id: string | null;
}

/**
 * Update payload for a compliance action.
 * Only status, due_date, and notes can be changed after creation.
 */
export interface ComplianceActionUpdate {
  action_status?: ComplianceActionStatus;
  due_date?: string | null;      // ISO date string
  notes?: string | null;
}

// ---------------------------------------------------------------------------
// Assessment schemas
// ---------------------------------------------------------------------------

/**
 * Payload for submitting a substantial modification assessment.
 * The four boolean fields correspond to CRA evaluation questions.
 * If ANY is true → is_substantial = true automatically.
 */
export interface AssessmentCreate {
  alters_intended_use: boolean;
  increases_cybersecurity_risk: boolean;
  changes_hazard_nature: boolean;
  expands_attack_surface: boolean;
  reasoning: string;             // min 10 chars, required justification
  decision_date: string;         // ISO date string
}

/**
 * Read schema for an assessment, including the derived is_substantial flag
 * and any compliance actions created as a result.
 */
export interface AssessmentRead {
  id: string;
  created_at: string;
  updated_at: string;
  change_id: string;
  assessor_user_id: string | null;
  alters_intended_use: boolean;
  increases_cybersecurity_risk: boolean;
  changes_hazard_nature: boolean;
  expands_attack_surface: boolean;
  is_substantial: boolean;
  reasoning: string;
  decision_date: string;         // ISO date string
  compliance_actions: ComplianceActionRead[];
}

// ---------------------------------------------------------------------------
// Change schemas
// ---------------------------------------------------------------------------

/**
 * Payload for recording a new change (creates a draft).
 */
export interface ChangeCreate {
  product_version_id: string;
  change_type: ChangeType;
  title: string;                 // min 3, max 255 chars
  description: string;           // min 10 chars
  change_date: string;           // ISO date string
}

/**
 * Partial update payload for editing a change while it is in 'draft' status.
 * All fields are optional; omitted fields are left unchanged.
 */
export interface ChangeUpdate {
  change_type?: ChangeType;
  title?: string;
  description?: string;
  change_date?: string;          // ISO date string
}

/**
 * Full read schema for a change including nested assessment (if present).
 */
export interface ChangeRead {
  id: string;
  created_at: string;
  updated_at: string;
  product_version_id: string;
  initiator_user_id: string | null;
  assessor_user_id: string | null;
  change_type: ChangeType;
  title: string;
  description: string;
  change_date: string;           // ISO date string
  status: ChangeStatus;
  submitted_at: string | null;   // ISO date string
  assessed_at: string | null;    // ISO date string
  closed_at: string | null;      // ISO date string
  assessment: AssessmentRead | null;
}

/**
 * Lightweight summary used in list views.
 * Excludes nested assessment to keep payloads small.
 * is_substantial is a shortcut flag from the assessment (null if not yet assessed).
 */
export interface ChangeSummary {
  id: string;
  created_at: string;
  updated_at: string;
  product_version_id: string;
  initiator_user_id: string | null;
  assessor_user_id: string | null;
  change_type: ChangeType;
  title: string;
  change_date: string;           // ISO date string
  status: ChangeStatus;
  is_substantial: boolean | null;
}

// ---------------------------------------------------------------------------
// Filter params (used by the list API)
// ---------------------------------------------------------------------------

/** Query parameters accepted by GET /changes. */
export interface ChangeListParams {
  product_version_id?: string;
  status?: ChangeStatus;
  change_type?: ChangeType;
  is_substantial?: boolean;
}
