/**
 * API service for the Substantial Change Tracking feature.
 *
 * Wraps all /changes endpoints:
 *   - CRUD on changes (list, get, create, update)
 *   - Workflow transitions (submit, claim, assess, close)
 *   - Compliance action updates
 */

import { apiClient } from "@/services/api";
import type {
  AssessmentCreate,
  ChangeCreate,
  ChangeListParams,
  ChangeRead,
  ChangeSummary,
  ChangeUpdate,
  ComplianceActionRead,
  ComplianceActionUpdate,
} from "@/types/change";

export const changeService = {
  /**
   * Fetch a filtered list of change summaries.
   * All filter params are optional; omit to retrieve all changes.
   */
  async list(params?: ChangeListParams): Promise<ChangeSummary[]> {
    const { data } = await apiClient.get<ChangeSummary[]>("/changes", { params });
    return data;
  },

  /**
   * Fetch full detail for a single change, including nested assessment and
   * compliance actions.
   */
  async get(changeId: string): Promise<ChangeRead> {
    const { data } = await apiClient.get<ChangeRead>(`/changes/${changeId}`);
    return data;
  },

  /**
   * Create a new change in 'draft' status.
   */
  async create(payload: ChangeCreate): Promise<ChangeRead> {
    const { data } = await apiClient.post<ChangeRead>("/changes", payload);
    return data;
  },

  /**
   * Partially update a change. Only allowed while status is 'draft'.
   */
  async update(changeId: string, payload: ChangeUpdate): Promise<ChangeRead> {
    const { data } = await apiClient.patch<ChangeRead>(`/changes/${changeId}`, payload);
    return data;
  },

  /**
   * Set assignee / due date on a change. Works regardless of workflow status.
   */
  async assign(
    changeId: string,
    payload: { assigned_to_user_id?: string | null; due_date?: string | null },
  ): Promise<ChangeRead> {
    const { data } = await apiClient.patch<ChangeRead>(`/changes/${changeId}/assign`, payload);
    return data;
  },

  // ---------------------------------------------------------------------------
  // Workflow transition endpoints
  // ---------------------------------------------------------------------------

  /**
   * Transition: draft → submitted.
   * Signals the change is ready for assessment.
   */
  async submit(changeId: string): Promise<ChangeRead> {
    const { data } = await apiClient.post<ChangeRead>(`/changes/${changeId}/submit`);
    return data;
  },

  /**
   * Transition: submitted → under_review.
   * Assigns the calling user as assessor.
   */
  async claim(changeId: string): Promise<ChangeRead> {
    const { data } = await apiClient.post<ChangeRead>(`/changes/${changeId}/claim`);
    return data;
  },

  /**
   * Transition: under_review → assessed | action_required.
   * Records the four CRA criteria and derives is_substantial.
   * If substantial, four compliance actions are auto-created.
   */
  async assess(changeId: string, payload: AssessmentCreate): Promise<ChangeRead> {
    const { data } = await apiClient.post<ChangeRead>(
      `/changes/${changeId}/assess`,
      payload,
    );
    return data;
  },

  /**
   * Transition: assessed | action_required → closed.
   * Blocked if any compliance action is still pending (for substantial changes).
   */
  async close(changeId: string): Promise<ChangeRead> {
    const { data } = await apiClient.post<ChangeRead>(`/changes/${changeId}/close`);
    return data;
  },

  // ---------------------------------------------------------------------------
  // Compliance action management
  // ---------------------------------------------------------------------------

  /**
   * Update the status, due date, or notes of a compliance action.
   */
  async updateComplianceAction(
    actionId: string,
    payload: ComplianceActionUpdate,
  ): Promise<ComplianceActionRead> {
    const { data } = await apiClient.patch<ComplianceActionRead>(
      `/changes/compliance-actions/${actionId}`,
      payload,
    );
    return data;
  },
};
