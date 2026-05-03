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
} from "@/types/admin";

export const adminService = {
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