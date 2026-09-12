// CRANE — CRA Norm Engine
// Copyright (C) 2026 Ali Mohammad Hosseini
// SPDX-License-Identifier: AGPL-3.0-or-later
// This file is part of CRANE, free software under the GNU AGPL v3.0 or later.
// See <https://www.gnu.org/licenses/>.

import { apiClient } from "@/services/api";
import type {
  AdminPasswordReset,
  AdminUserCreate,
  AdminUserRead,
  AdminUserRoleUpdate,
  AdminUserStatusUpdate,
  LDAPStatusResult,
  LDAPSyncPayload,
  LDAPSyncResult,
  LDAPTestPayload,
  LDAPTestResult,
  PermissionRead,
  RoleCreate,
  RolePermissionsUpdate,
  RoleRead,
  RoleUpdate,
  VulnerabilityScanningSetting,
  IngestionKey,
  SystemUpdatePolicy,
  SystemUpdateStatus,
} from "@/types/admin";

export const adminService = {
  async getSystemUpdates(): Promise<SystemUpdateStatus> {
    return (await apiClient.get<SystemUpdateStatus>("/admin/system-updates")).data;
  },
  async checkSystemUpdates(): Promise<SystemUpdateStatus> {
    return (await apiClient.post<SystemUpdateStatus>("/admin/system-updates/check")).data;
  },
  async setSystemUpdatePolicy(payload: SystemUpdatePolicy): Promise<SystemUpdateStatus> {
    return (await apiClient.put<SystemUpdateStatus>("/admin/system-updates/policy", payload)).data;
  },
  async listIngestionKeys(): Promise<IngestionKey[]> {
    return (await apiClient.get<IngestionKey[]>("/admin/ingestion-keys")).data;
  },
  async createIngestionKey(payload: { name: string; source: string; sbom_record_id: string; expires_in_days: number }): Promise<IngestionKey & { token: string }> {
    return (await apiClient.post<IngestionKey & { token: string }>("/admin/ingestion-keys", payload)).data;
  },
  async revokeIngestionKey(id: string): Promise<void> {
    await apiClient.delete(`/admin/ingestion-keys/${id}`);
  },
  async getVulnerabilityScanning(): Promise<VulnerabilityScanningSetting> {
    const { data } = await apiClient.get<VulnerabilityScanningSetting>(
      "/admin/vulnerability-scanning",
    );
    return data;
  },

  async setVulnerabilityScanning(enabled: boolean): Promise<VulnerabilityScanningSetting> {
    const { data } = await apiClient.put<VulnerabilityScanningSetting>(
      "/admin/vulnerability-scanning",
      { enabled },
    );
    return data;
  },

  // USERS
  async listUsers(): Promise<AdminUserRead[]> {
    const { data } = await apiClient.get<AdminUserRead[]>("/admin/users");
    return data;
  },

  async createUser(payload: AdminUserCreate): Promise<AdminUserRead> {
    const { data } = await apiClient.post<AdminUserRead>("/admin/users", payload);
    return data;
  },

  async updateUserRoles(
    userId: string,
    payload: AdminUserRoleUpdate,
  ): Promise<AdminUserRead> {
    const { data } = await apiClient.patch<AdminUserRead>(
      `/admin/users/${userId}/roles`,
      payload,
    );
    return data;
  },

  async updateUserStatus(
    userId: string,
    payload: AdminUserStatusUpdate,
  ): Promise<AdminUserRead> {
    const { data } = await apiClient.patch<AdminUserRead>(
      `/admin/users/${userId}/status`,
      payload,
    );
    return data;
  },

  async resetUserPassword(
    userId: string,
    payload: AdminPasswordReset,
  ): Promise<AdminUserRead> {
    const { data } = await apiClient.post<AdminUserRead>(
      `/admin/users/${userId}/reset-password`,
      payload,
    );
    return data;
  },

  // ROLES
  async listRoles(): Promise<RoleRead[]> {
    const { data } = await apiClient.get<RoleRead[]>("/admin/roles");
    return data;
  },

  async createRole(payload: RoleCreate): Promise<RoleRead> {
    const { data } = await apiClient.post<RoleRead>("/admin/roles", payload);
    return data;
  },

  async updateRole(roleId: string, payload: RoleUpdate): Promise<RoleRead> {
    const { data } = await apiClient.patch<RoleRead>(`/admin/roles/${roleId}`, payload);
    return data;
  },

  async deleteRole(roleId: string): Promise<void> {
    await apiClient.delete(`/admin/roles/${roleId}`);
  },

  async setRolePermissions(
    roleId: string,
    payload: RolePermissionsUpdate,
  ): Promise<RoleRead> {
    const { data } = await apiClient.put<RoleRead>(
      `/admin/roles/${roleId}/permissions`,
      payload,
    );
    return data;
  },

  // PERMISSIONS
  async listPermissions(): Promise<PermissionRead[]> {
    const { data } = await apiClient.get<PermissionRead[]>("/admin/permissions");
    return data;
  },

  // LDAP
  async getLdapStatus(): Promise<LDAPStatusResult> {
    const { data } = await apiClient.get<LDAPStatusResult>("/admin/ldap/status");
    return data;
  },

  async testLdapCredentials(payload: LDAPTestPayload): Promise<LDAPTestResult> {
    const { data } = await apiClient.post<LDAPTestResult>("/admin/ldap/test", payload);
    return data;
  },

  async syncLdapUsers(payload: LDAPSyncPayload): Promise<LDAPSyncResult> {
    const { data } = await apiClient.post<LDAPSyncResult>("/admin/ldap/sync", payload);
    return data;
  },
};
