// CRANE — CRA Norm Engine
// Copyright (C) 2026 Ali Mohammad Hosseini
// SPDX-License-Identifier: AGPL-3.0-or-later
// This file is part of CRANE, free software under the GNU AGPL v3.0 or later.
// See <https://www.gnu.org/licenses/>.

export type AuthProvider = "local" | "ldap";

export interface AdminUserRead {
  id: string;
  email: string;
  full_name: string;
  roles: string[];
  is_active: boolean;
  auth_provider: AuthProvider;
  must_change_password: boolean;
}

export interface AdminPasswordReset {
  new_password: string;
}

export interface LDAPStatusResult {
  enabled: boolean;
  connected: boolean;
  server?: string;
  base_dn?: string;
  message: string;
}

export interface LDAPTestPayload {
  email: string;
  password: string;
}

export interface LDAPTestResult {
  success: boolean;
  message?: string;
  email?: string;
  full_name?: string;
}

export interface LDAPSyncPayload {
  search?: string;
  role_ids?: string[];
}

export interface LDAPSyncResult {
  created: number;
  skipped: number;
  total: number;
}

export interface AdminUserCreate {
  email: string;
  full_name: string;
  password: string;
  role_ids: string[];
}

export interface AdminUserRoleUpdate {
  role_ids: string[];
}

export interface AdminUserStatusUpdate {
  is_active: boolean;
}

export interface RoleRead {
  id: string;
  name: string;
  description: string | null;
  permissions: string[];
}

export interface RoleCreate {
  name: string;
  description: string | null;
}

export interface RoleUpdate {
  name?: string;
  description?: string | null;
}

export interface RolePermissionsUpdate {
  permission_ids: string[];
}

export interface PermissionRead {
  id: string;
  key: string;
  description: string | null;
}

export interface VulnerabilityScanningSetting {
  enabled: boolean;
}

export type SystemUpdatePolicyMode = "manual" | "security" | "all";

export interface SystemUpdateManifest {
  schema_version: number;
  version: string;
  channel: "stable" | "preview";
  update_type: "security" | "maintenance" | "feature";
  severity: "none" | "low" | "medium" | "high" | "critical";
  published_at: string;
  expires_at: string;
  minimum_upgrade_version: string;
  database_revision: string;
  postgres_major_versions: number[];
  automatic_update_allowed: boolean;
  rollback_mode: "image-only" | "database-restore";
  advisory_url: string | null;
  release_notes_url: string;
}

export interface SystemUpdatePolicy {
  policy: SystemUpdatePolicyMode;
  channel: "stable" | "preview";
  maintenance_day: number;
  maintenance_hour_utc: number;
  postponed_until: string | null;
}

export interface SystemUpdateStatus {
  installed_version: string;
  configured: boolean;
  update_checks_enabled: boolean;
  policy: SystemUpdatePolicy;
  update_available: boolean;
  automatic_update_eligible: boolean;
  manifest: SystemUpdateManifest | null;
  last_checked_at: string | null;
  last_error: string | null;
  last_operation: Record<string, unknown> | null;
  manual_command: string;
}

export interface IngestionKey {
  id: string;
  name: string;
  sbom_record_id: string;
  source: string;
  expires_at: string;
  revoked_at: string | null;
}
