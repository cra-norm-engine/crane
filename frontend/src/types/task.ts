// CRANE — CRA Norm Engine
// Copyright (C) 2026 Ali Mohammad Hosseini
// SPDX-License-Identifier: AGPL-3.0-or-later
// This file is part of CRANE, free software under the GNU AGPL v3.0 or later.
// See <https://www.gnu.org/licenses/>.

export type TaskEntityType =
  | "vulnerability_report"
  | "change"
  | "change_compliance_action"
  | "release_gate_item"
  | "risk_item"
  | "supplier_reassessment"
  | "maintainer_notification"
  | "manual_task"
  | "eos_alert";

export interface ManualTaskCreate {
  title: string;
  description?: string | null;
  due_date?: string | null;
  assigned_to_user_id?: string | null;
  product_id?: string | null;
  product_release_id?: string | null;
  priority?: "low" | "medium" | "high";
}

export interface TaskArtifact {
  id: string;
  revision_id: string;
  artifact_id: string;
  title: string;
  filename: string | null;
  uploader_name: string | null;
  revision_number: number;
  linked_at: string;
}

export interface TaskActivity {
  id: string;
  occurred_at: string;
  actor_name: string | null;
  action_type: string;
  details: Record<string, unknown>;
}

export interface TaskNotification {
  id: string;
  manual_task_id: string;
  event_type: string;
  title: string;
  message: string;
  read_at: string | null;
  created_at: string;
}

export interface TaskItem {
  entity_type: TaskEntityType;
  entity_id: string;
  /** Parent entity ID for deep-link navigation:
   *  risk_item → risk_assessment_id, release_gate_item → product_release_id */
  parent_id: string | null;
  title: string;
  description?: string | null;
  status: string;
  created_at?: string | null;
  due_date: string | null;
  is_overdue: boolean;
  product_name: string | null;
  release_version: string | null;
  severity: string | null;
  /** Display name of whoever created or reported the item. */
  created_by_name: string | null;
  assigned_to_user_id?: string | null;
  assigned_to_name?: string | null;
  assigned_to_avatar_data?: string | null;
  related_product_id?: string | null;
  related_release_id?: string | null;
  parent_task_id?: string | null;
  viewer_is_assignee?: boolean;
  viewer_is_creator?: boolean;
  is_completed?: boolean;
  priority?: "low" | "medium" | "high" | null;
  completed_at?: string | null;
  completed_by_name?: string | null;
  completion_note?: string | null;
  archived_at?: string | null;
  archive_reason?: string | null;
  can_edit_definition?: boolean;
  can_update_status?: boolean;
  can_archive?: boolean;
  evidence?: TaskArtifact[];
}
