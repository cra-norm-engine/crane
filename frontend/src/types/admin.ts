export interface AdminUserRead {
  id: string;
  email: string;
  full_name: string;
  roles: string[];
  is_active: boolean;
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