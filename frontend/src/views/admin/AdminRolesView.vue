<template>
  <section class="page">
    <div class="page-header">
      <div>
        <h1 class="page-title">Admin · Roles & access</h1>
        <p class="muted">
          Create custom roles, update role metadata, and manage permission assignments.
        </p>
      </div>

      <div class="page-actions">
        <button class="button secondary" type="button" @click="loadData" :disabled="isLoading">
          Refresh
        </button>
        <button class="button" type="button" @click="toggleCreateForm">
          {{ showCreateForm ? "Close" : "Create role" }}
        </button>
      </div>
    </div>

    <div class="grid stats-grid">
      <article class="card stat-card">
        <span class="stat-label">Total roles</span>
        <strong class="stat-value">{{ roles.length }}</strong>
      </article>
      <article class="card stat-card">
        <span class="stat-label">System roles</span>
        <strong class="stat-value">{{ systemRolesCount }}</strong>
      </article>
      <article class="card stat-card">
        <span class="stat-label">Permissions</span>
        <strong class="stat-value">{{ permissions.length }}</strong>
      </article>
    </div>

    <div v-if="showCreateForm" class="card form-card">
      <div class="section-header">
        <div>
          <h2 class="section-title">Create role</h2>
          <p class="muted">Add a custom role for your compliance workflow.</p>
        </div>
      </div>

      <form class="grid form-grid" @submit.prevent="createRole">
        <label class="field">
          <span class="field-label">Role name</span>
          <input v-model.trim="createForm.name" class="input" required maxlength="100" />
        </label>

        <label class="field field-span-2">
          <span class="field-label">Description</span>
          <textarea
            v-model.trim="createForm.description"
            class="textarea"
            rows="3"
            maxlength="255"
          />
        </label>

        <div class="form-actions field-span-2">
          <p v-if="formError" class="form-error">{{ formError }}</p>
          <button class="button" type="submit" :disabled="isSubmitting">
            {{ isSubmitting ? "Saving..." : "Create role" }}
          </button>
        </div>
      </form>
    </div>

    <div class="card table-card">
      <div class="section-header">
        <div>
          <h2 class="section-title">Roles</h2>
          <p class="muted">{{ roles.length }} role(s)</p>
        </div>
      </div>

      <div v-if="errorMessage" class="feedback feedback-error">
        {{ errorMessage }}
      </div>

      <div v-else-if="isLoading" class="feedback">Loading roles…</div>

      <div v-else-if="roles.length === 0" class="empty-state">
        <h3>No roles found</h3>
        <p class="muted">Create your first custom role to begin assigning tailored access.</p>
      </div>

      <div v-else class="roles-grid">
        <article v-for="role in roles" :key="role.id" class="card role-card">
          <div class="role-card-header">
            <div>
              <h3 class="role-title">{{ role.name }}</h3>
              <p class="muted role-description">
                {{ role.description || "No description provided." }}
              </p>
            </div>
            <span class="badge" :class="isSystemRole(role.name) ? 'badge-warning' : 'badge-neutral'">
              {{ isSystemRole(role.name) ? "System" : "Custom" }}
            </span>
          </div>

          <form class="grid role-edit-grid" @submit.prevent="saveRole(role)">
            <label class="field">
              <span class="field-label">Role name</span>
              <input
                v-model.trim="roleDrafts[role.id].name"
                class="input"
                required
                maxlength="100"
              />
            </label>

            <label class="field">
              <span class="field-label">Description</span>
              <input
                v-model.trim="roleDrafts[role.id].description"
                class="input"
                maxlength="255"
              />
            </label>

            <label class="field field-span-2">
              <span class="field-label">Permissions</span>
              <div class="permissions-grid">
                <label
                  v-for="permission in permissions"
                  :key="`${role.id}-${permission.id}`"
                  class="checkbox-option"
                >
                  <input
                    type="checkbox"
                    :checked="roleDrafts[role.id].permission_ids.includes(permission.id)"
                    @change="toggleRolePermission(role.id, permission.id)"
                  />
                  <span>{{ permission.key }}</span>
                </label>
              </div>
            </label>

            <div class="form-actions field-span-2">
              <div class="role-actions">
                <button
                  class="button secondary"
                  type="submit"
                  :disabled="isRoleSaving(role.id)"
                >
                  {{ isRoleSaving(role.id) ? "Saving..." : "Save changes" }}
                </button>

                <button
                  class="button danger"
                  type="button"
                  :disabled="isDeletingRole(role.id) || isSystemRole(role.name)"
                  @click="deleteRole(role)"
                >
                  {{
                    isDeletingRole(role.id)
                      ? "Deleting..."
                      : isSystemRole(role.name)
                        ? "System role"
                        : "Delete role"
                  }}
                </button>
              </div>
            </div>
          </form>
        </article>
      </div>
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from "vue";

import { adminService } from "@/services/admin-service";
import type { PermissionRead, RoleRead } from "@/types/admin";

interface RoleDraft {
  name: string;
  description: string;
  permission_ids: string[];
}

const SYSTEM_ROLE_NAMES = [
  "admin",
  "cybersecurity_engineer",
  "development_team",
  "product_owner",
  "lifecycle_manager",
  "legal_team",
  "product_management",
];

const roles = ref<RoleRead[]>([]);
const permissions = ref<PermissionRead[]>([]);

const isLoading = ref(false);
const isSubmitting = ref(false);
const errorMessage = ref("");
const formError = ref("");
const showCreateForm = ref(false);

const roleSavingIds = ref<string[]>([]);
const deletingRoleIds = ref<string[]>([]);

const roleDrafts = reactive<Record<string, RoleDraft>>({});

const createForm = reactive({
  name: "",
  description: "",
});

const systemRolesCount = computed(
  () => roles.value.filter((role) => isSystemRole(role.name)).length,
);

function isSystemRole(roleName: string): boolean {
  return SYSTEM_ROLE_NAMES.includes(roleName);
}

function toggleCreateForm(): void {
  showCreateForm.value = !showCreateForm.value;
  if (!showCreateForm.value) {
    createForm.name = "";
    createForm.description = "";
    formError.value = "";
  }
}

function isRoleSaving(roleId: string): boolean {
  return roleSavingIds.value.includes(roleId);
}

function isDeletingRole(roleId: string): boolean {
  return deletingRoleIds.value.includes(roleId);
}

function syncDrafts(): void {
  const nextDrafts: Record<string, RoleDraft> = {};

  for (const role of roles.value) {
    nextDrafts[role.id] = {
      name: role.name,
      description: role.description ?? "",
      permission_ids: permissions.value
        .filter((permission) => role.permissions.includes(permission.key))
        .map((permission) => permission.id),
    };
  }

  for (const [key, value] of Object.entries(nextDrafts)) {
    roleDrafts[key] = value;
  }

  for (const key of Object.keys(roleDrafts)) {
    if (!nextDrafts[key]) {
      delete roleDrafts[key];
    }
  }
}

function toggleRolePermission(roleId: string, permissionId: string): void {
  const draft = roleDrafts[roleId];
  if (!draft) return;

  if (draft.permission_ids.includes(permissionId)) {
    draft.permission_ids = draft.permission_ids.filter((id) => id !== permissionId);
    return;
  }

  draft.permission_ids = [...draft.permission_ids, permissionId];
}

async function loadData(): Promise<void> {
  isLoading.value = true;
  errorMessage.value = "";

  try {
    const [rolesData, permissionsData] = await Promise.all([
      adminService.listRoles(),
      adminService.listPermissions(),
    ]);

    roles.value = rolesData;
    permissions.value = permissionsData;
    syncDrafts();
  } catch (error) {
    errorMessage.value =
      error instanceof Error ? error.message : "Failed to load roles and permissions.";
  } finally {
    isLoading.value = false;
  }
}

async function createRole(): Promise<void> {
  isSubmitting.value = true;
  formError.value = "";

  try {
    await adminService.createRole({
      name: createForm.name,
      description: createForm.description || null,
    });

    createForm.name = "";
    createForm.description = "";
    showCreateForm.value = false;
    await loadData();
  } catch (error) {
    formError.value =
      error instanceof Error ? error.message : "Failed to create role.";
  } finally {
    isSubmitting.value = false;
  }
}

async function saveRole(role: RoleRead): Promise<void> {
  const draft = roleDrafts[role.id];
  if (!draft) return;

  roleSavingIds.value = [...roleSavingIds.value, role.id];

  try {
    await adminService.updateRole(role.id, {
      name: draft.name,
      description: draft.description || null,
    });

    await adminService.setRolePermissions(role.id, {
      permission_ids: draft.permission_ids,
    });

    await loadData();
  } catch (error) {
    errorMessage.value =
      error instanceof Error ? error.message : "Failed to update role.";
  } finally {
    roleSavingIds.value = roleSavingIds.value.filter((id) => id !== role.id);
  }
}

async function deleteRole(role: RoleRead): Promise<void> {
  if (isSystemRole(role.name)) {
    return;
  }

  const confirmed = window.confirm(`Delete role "${role.name}"?`);
  if (!confirmed) {
    return;
  }

  deletingRoleIds.value = [...deletingRoleIds.value, role.id];

  try {
    await adminService.deleteRole(role.id);
    await loadData();
  } catch (error) {
    errorMessage.value =
      error instanceof Error ? error.message : "Failed to delete role.";
  } finally {
    deletingRoleIds.value = deletingRoleIds.value.filter((id) => id !== role.id);
  }
}

onMounted(() => {
  void loadData();
});
</script>

<style scoped>
.page {
  display: grid;
  gap: 1rem;
}

.page-header,
.section-header,
.form-actions {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  flex-wrap: wrap;
}

.page-actions,
.role-actions {
  display: flex;
  gap: 0.75rem;
  flex-wrap: wrap;
}

.page-title,
.section-title,
.role-title {
  margin: 0;
}

.grid {
  display: grid;
  gap: 1rem;
}

.stats-grid {
  grid-template-columns: repeat(3, minmax(0, 1fr));
}

.stat-card {
  display: grid;
  gap: 0.35rem;
}

.stat-label {
  color: var(--color-text-muted, #94a3b8);
  font-size: 0.875rem;
}

.stat-value {
  font-size: 1.75rem;
  font-weight: 700;
}

.form-card,
.table-card {
  display: grid;
  gap: 1rem;
}

.field {
  display: grid;
  gap: 0.4rem;
}

.field-label {
  font-size: 0.875rem;
  color: var(--color-text-muted, #94a3b8);
}

.form-grid,
.role-edit-grid {
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

.field-span-2 {
  grid-column: span 2;
}

.feedback,
.empty-state {
  padding: 1.25rem;
  border-radius: 1rem;
  background: var(--color-surface-soft, rgba(15, 23, 42, 0.45));
}

.feedback-error,
.form-error {
  color: #fda4af;
}

.roles-grid {
  display: grid;
  gap: 1rem;
}

.role-card {
  display: grid;
  gap: 1rem;
}

.role-card-header {
  display: flex;
  justify-content: space-between;
  gap: 1rem;
  align-items: flex-start;
  flex-wrap: wrap;
}

.role-description {
  margin-top: 0.35rem;
}

.permissions-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 0.75rem;
}

.checkbox-option {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.badge-neutral {
  background: rgba(148, 163, 184, 0.15);
  color: #cbd5e1;
}

.badge-warning {
  background: rgba(251, 191, 36, 0.15);
  color: #fde68a;
}

@media (max-width: 900px) {
  .stats-grid,
  .form-grid,
  .role-edit-grid,
  .permissions-grid {
    grid-template-columns: 1fr;
  }

  .field-span-2 {
    grid-column: span 1;
  }
}
</style>