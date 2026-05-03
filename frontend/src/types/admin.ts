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