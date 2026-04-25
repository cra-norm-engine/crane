<template>
  <section class="page">
    <header class="page-header card">
      <div>
        <h1 class="page-title">Admin · Roles & access</h1>
        <p class="muted page-subtitle">
          Manage role definitions and permission assignments from a single workspace.
        </p>
      </div>

      <div class="page-actions">
        <button class="button secondary" type="button" @click="loadData" :disabled="isLoading">
          {{ isLoading ? "Refreshing..." : "Refresh" }}
        </button>
        <button class="button" type="button" @click="toggleCreateForm">
          {{ showCreateForm ? "Close" : "Create role" }}
        </button>
      </div>
    </header>

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
          <p class="muted">Add a custom role for your workflow.</p>
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

    <div v-if="errorMessage" class="feedback feedback-error">
      {{ errorMessage }}
    </div>

    <div v-else-if="isLoading" class="feedback">
      Loading roles…
    </div>

    <div v-else-if="roles.length === 0" class="empty-state card">
      <h3>No roles found</h3>
      <p class="muted">Create your first custom role to begin assigning tailored access.</p>
    </div>

    <div v-else class="workspace">
      <aside class="card roles-sidebar">
        <div class="section-header sidebar-header">
          <div>
            <h2 class="section-title">Roles</h2>
            <p class="muted">{{ roles.length }} role(s)</p>
          </div>
        </div>

        <div class="role-list">
          <button
            v-for="role in roles"
            :key="role.id"
            type="button"
            class="role-list-item"
            :class="{ 'role-list-item-active': selectedRoleId === role.id }"
            @click="selectRole(role.id)"
          >
            <div class="role-list-item-main">
              <div class="role-list-item-top">
                <strong class="role-list-item-title">{{ role.name }}</strong>
                <span
                  class="badge"
                  :class="isSystemRole(role.name) ? 'badge-warning' : 'badge-neutral'"
                >
                  {{ isSystemRole(role.name) ? "System" : "Custom" }}
                </span>
              </div>

              <p class="muted role-list-item-description">
                {{ role.description || "No description provided." }}
              </p>

              <span class="role-list-item-meta">
                {{ role.permissions.length }} permission(s)
              </span>
            </div>
          </button>
        </div>
      </aside>

      <section v-if="selectedRole" class="card details-panel">
        <div class="details-header">
          <div>
            <div class="details-title-row">
              <h2 class="section-title">{{ selectedRole.name }}</h2>
              <span
                class="badge"
                :class="isSystemRole(selectedRole.name) ? 'badge-warning' : 'badge-neutral'"
              >
                {{ isSystemRole(selectedRole.name) ? "System role" : "Custom role" }}
              </span>
            </div>
            <p class="muted">
              Edit metadata and permission assignments for the selected role.
            </p>
          </div>
        </div>

        <form class="details-form" @submit.prevent="saveRole(selectedRole)">
          <div class="grid details-grid">
            <label class="field">
              <span class="field-label">Role name</span>
              <input
                v-model.trim="roleDrafts[selectedRole.id].name"
                class="input"
                required
                maxlength="100"
              />
            </label>

            <label class="field">
              <span class="field-label">Description</span>
              <input
                v-model.trim="roleDrafts[selectedRole.id].description"
                class="input"
                maxlength="255"
              />
            </label>
          </div>

          <div class="permissions-section">
            <div class="permissions-header">
              <div>
                <h3 class="subsection-title">Permissions</h3>
                <p class="muted">
                  {{ roleDrafts[selectedRole.id].permission_ids.length }} selected
                </p>
              </div>
            </div>

            <div class="permissions-grid">
              <label
                v-for="permission in permissions"
                :key="`${selectedRole.id}-${permission.id}`"
                class="checkbox-option"
              >
                <input
                  type="checkbox"
                  :checked="roleDrafts[selectedRole.id].permission_ids.includes(permission.id)"
                  @change="toggleRolePermission(selectedRole.id, permission.id)"
                />
                <span>{{ permission.key }}</span>
              </label>
            </div>
          </div>

          <div class="form-actions">
            <div class="role-actions">
              <button
                class="button secondary"
                type="submit"
                :disabled="isRoleSaving(selectedRole.id)"
              >
                {{ isRoleSaving(selectedRole.id) ? "Saving..." : "Save changes" }}
              </button>

              <button
                class="button danger"
                type="button"
                :disabled="
                  isDeletingRole(selectedRole.id) || isSystemRole(selectedRole.name)
                "
                @click="deleteRole(selectedRole)"
              >
                {{
                  isDeletingRole(selectedRole.id)
                    ? "Deleting..."
                    : isSystemRole(selectedRole.name)
                      ? "System role"
                      : "Delete role"
                }}
              </button>
            </div>
          </div>
        </form>
      </section>
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

const selectedRoleId = ref<string>("");

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

const selectedRole = computed(() => {
  return roles.value.find((role) => role.id === selectedRoleId.value) ?? roles.value[0] ?? null;
});

function isSystemRole(roleName: string): boolean {
  return SYSTEM_ROLE_NAMES.includes(roleName);
}

function selectRole(roleId: string): void {
  selectedRoleId.value = roleId;
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

  if (!roles.value.some((role) => role.id === selectedRoleId.value)) {
    selectedRoleId.value = roles.value[0]?.id ?? "";
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

.grid {
  display: grid;
  gap: 1rem;
}

.page-header,
.section-header,
.form-actions,
.details-header,
.permissions-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 1rem;
  flex-wrap: wrap;
}

.page-title,
.section-title,
.subsection-title {
  margin: 0;
}

.page-subtitle {
  margin-top: 0.35rem;
}

.page-actions,
.role-actions {
  display: flex;
  gap: 0.75rem;
  flex-wrap: wrap;
}

.stats-grid {
  grid-template-columns: repeat(3, minmax(0, 1fr));
}

.stat-card {
  display: grid;
  gap: 0.35rem;
}

.stat-label,
.field-label,
.role-list-item-meta {
  color: var(--color-text-muted, #94a3b8);
  font-size: 0.875rem;
}

.stat-value {
  font-size: 1.75rem;
  font-weight: 700;
}

.form-card,
.details-panel {
  display: grid;
  gap: 1rem;
}

.form-grid,
.details-grid {
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

.field {
  display: grid;
  gap: 0.4rem;
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

.workspace {
  display: grid;
  grid-template-columns: minmax(280px, 340px) minmax(0, 1fr);
  gap: 1rem;
  align-items: start;
}

.roles-sidebar {
  display: grid;
  gap: 1rem;
  position: sticky;
  top: 1rem;
  max-height: calc(100vh - 2rem);
  overflow: hidden;
}

.sidebar-header {
  padding-bottom: 0.25rem;
}

.role-list {
  display: grid;
  gap: 0.75rem;
  overflow: auto;
}

.role-list-item {
  width: 100%;
  border: 1px solid var(--color-border-soft, rgba(148, 163, 184, 0.18));
  border-radius: 1rem;
  background: transparent;
  padding: 1rem;
  text-align: left;
  cursor: pointer;
  transition: border-color 0.2s ease, background 0.2s ease, transform 0.2s ease;
}

.role-list-item:hover {
  border-color: var(--color-border-strong, rgba(148, 163, 184, 0.4));
  background: var(--color-surface-soft, rgba(15, 23, 42, 0.25));
}

.role-list-item-active {
  border-color: var(--color-primary, #60a5fa);
  background: rgba(96, 165, 250, 0.08);
}

.role-list-item-main {
  display: grid;
  gap: 0.4rem;
}

.role-list-item-top,
.details-title-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.75rem;
  flex-wrap: wrap;
}

.role-list-item-title {
  font-size: 0.95rem;
}

.role-list-item-description {
  margin: 0;
  line-height: 1.4;
}

.details-panel {
  min-width: 0;
}

.details-form {
  display: grid;
  gap: 1.25rem;
}

.permissions-section {
  display: grid;
  gap: 1rem;
  padding-top: 0.25rem;
}

.permissions-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 0.75rem;
}

.checkbox-option {
  display: flex;
  align-items: center;
  gap: 0.65rem;
  min-height: 44px;
  padding: 0.75rem 0.9rem;
  border: 1px solid var(--color-border-soft, rgba(148, 163, 184, 0.18));
  border-radius: 0.875rem;
  background: var(--color-surface-soft, rgba(15, 23, 42, 0.18));
}

.badge-neutral {
  background: rgba(148, 163, 184, 0.15);
  color: #cbd5e1;
}

.badge-warning {
  background: rgba(251, 191, 36, 0.15);
  color: #fde68a;
}

@media (max-width: 1000px) {
  .workspace {
    grid-template-columns: 1fr;
  }

  .roles-sidebar {
    position: static;
    max-height: none;
  }
}

@media (max-width: 900px) {
  .stats-grid,
  .form-grid,
  .details-grid {
    grid-template-columns: 1fr;
  }

  .field-span-2 {
    grid-column: span 1;
  }
}
</style>

<style>
:root[data-theme="light"] .feedback-error,
:root[data-theme="light"] .form-error  { color: #be123c; }
:root[data-theme="light"] .badge-neutral { background: rgba(71,85,105,0.1);  color: #475569; }
:root[data-theme="light"] .badge-warning { background: rgba(184,155,18,0.1); color: #78350f; }
</style>