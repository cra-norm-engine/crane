export type TaskEntityType =
  | "vulnerability_report"
  | "change"
  | "release_gate_item"
  | "risk_item";

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
