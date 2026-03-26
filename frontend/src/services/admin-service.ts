import { apiClient } from "@/services/api";
import type {
  AdminUserCreate,
  AdminUserRead,
  AdminUserRoleUpdate,
  AdminUserStatusUpdate,
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
};