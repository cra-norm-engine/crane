// CRANE — CRA Norm Engine
// Copyright (C) 2026 Ali Mohammad Hosseini
// SPDX-License-Identifier: AGPL-3.0-or-later
// This file is part of CRANE, free software under the GNU AGPL v3.0 or later.
// See <https://www.gnu.org/licenses/>.

export type TaskEntityType =
  | "vulnerability_report"
  | "change"
  | "release_gate_item"
  | "risk_item"
  | "eos_alert";

export interface TaskItem {
  entity_type: TaskEntityType;
  entity_id: string;
  /** Parent entity ID for deep-link navigation:
   *  risk_item → risk_assessment_id, release_gate_item → product_release_id */
  parent_id: string | null;
  title: string;
  status: string;
  due_date: string | null;
  is_overdue: boolean;
  product_name: string | null;
  release_version: string | null;
  severity: string | null;
  /** Display name of whoever created or reported the item. */
  created_by_name: string | null;
}
