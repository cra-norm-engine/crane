<template>
  <section class="page">
    <div class="page-header">
      <div>
        <h1 class="page-title">Admin · Users</h1>
        <p class="muted">
          Create users, assign roles, and manage account status for the CRA compliance tool.
        </p>
      </div>

      <div class="page-actions">
        <button class="button secondary" type="button" @click="loadData" :disabled="isLoading">
          Refresh
        </button>
        <button class="button" type="button" @click="toggleCreateForm">
          {{ showCreateForm ? "Close" : "Create user" }}
        </button>
      </div>
    </div>

    <div class="grid stats-grid">
      <article class="card stat-card">
        <span class="stat-label">Total users</span>
        <strong class="stat-value">{{ users.length }}</strong>
      </article>
      <article class="card stat-card">
        <span class="stat-label">Active users</span>
        <strong class="stat-value">{{ activeUsersCount }}</strong>
      </article>
      <article class="card stat-card">
        <span class="stat-label">Admins</span>
        <strong class="stat-value">{{ adminUsersCount }}</strong>
      </article>
    </div>

    <div class="card filters-card">
      <div class="filters-row">
        <label class="field search-field">
          <span class="field-label">Search</span>
          <input
            v-model.trim="searchTerm"
            class="input"
            type="search"
            placeholder="Search by email or full name"
          />
        </label>

        <label class="field status-field">
          <span class="field-label">Status</span>
          <select v-model="statusFilter" class="select">
            <option value="all">All</option>
            <option value="active">Active only</option>
            <option value="inactive">Inactive only</option>
          </select>
        </label>
      </div>
    </div>

    <div v-if="showCreateForm" class="card form-card">
      <div class="section-header">
        <div>
          <h2 class="section-title">Create user</h2>
          <p class="muted">Add a new user and assign initial roles.</p>
        </div>
      </div>

      <form class="grid form-grid" @submit.prevent="createUser">
        <label class="field">
          <span class="field-label">Email</span>
          <input v-model.trim="form.email" class="input" type="email" required maxlength="320" />
        </label>

        <label class="field">
          <span class="field-label">Full name</span>
          <input v-model.trim="form.full_name" class="input" required maxlength="255" />
        </label>

        <label class="field">
          <span class="field-label">Password</span>
          <input
            v-model="form.password"
            class="input"
            type="password"
            required
            minlength="8"
            maxlength="255"
          />
        </label>

        <label class="field field-span-2">
          <span class="field-label">Roles</span>
          <div class="checkbox-grid">
            <label
              v-for="role in roles"
              :key="role.id"
              class="checkbox-option"
            >
              <input
                :checked="form.role_ids.includes(role.id)"
                type="checkbox"
                @change="toggleCreateRole(role.id)"
              />
              <span>{{ role.name }}</span>
            </label>
          </div>
        </label>

        <div class="form-actions field-span-2">
          <p v-if="formError" class="form-error">{{ formError }}</p>
          <button class="button" type="submit" :disabled="isSubmitting">
            {{ isSubmitting ? "Saving..." : "Create user" }}
          </button>
        </div>
      </form>
    </div>

    <div class="card table-card">
      <div class="section-header">
        <div>
          <h2 class="section-title">Users</h2>
          <p class="muted">{{ filteredUsers.length }} result(s)</p>
        </div>
      </div>

      <div v-if="errorMessage" class="feedback feedback-error">
        {{ errorMessage }}
      </div>

      <div v-else-if="isLoading" class="feedback">Loading users…</div>

      <div v-else-if="filteredUsers.length === 0" class="empty-state">
        <h3>No users found</h3>
        <p class="muted">Try a different search or create a new user.</p>
      </div>

      <div v-else class="table-wrapper">
        <table class="users-table">
          <thead>
            <tr>
              <th>User</th>
              <th>Roles</th>
              <th>Status</th>
              <th>Update roles</th>
              <th>Account</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="user in filteredUsers" :key="user.id">
              <td>
                <div class="user-cell">
                  <strong>{{ user.full_name }}</strong>
                  <span class="muted">{{ user.email }}</span>
                </div>
              </td>
              <td>
                <div class="badge-list">
                  <span
                    v-for="roleName in user.roles"
                    :key="`${user.id}-${roleName}`"
                    class="badge badge-neutral"
                  >
                    {{ roleName }}
                  </span>
                </div>
              </td>
              <td>
                <span class="badge" :class="user.is_active ? 'badge-success' : 'badge-danger'">
                  {{ user.is_active ? "Active" : "Inactive" }}
                </span>
              </td>
              <td>
                <div class="inline-editor">
                  <select
                    class="select"
                    multiple
                    :value="selectedRoleIdsByUser[user.id] ?? roleIdsForUser(user)"
                    @change="onRoleSelectionChange(user.id, $event)"
                  >
                    <option v-for="role in roles" :key="role.id" :value="role.id">
                      {{ role.name }}
                    </option>
                  </select>
                  <button
                    class="button secondary"
                    type="button"
                    :disabled="isRoleSaving(user.id)"
                    @click="saveUserRoles(user.id)"
                  >
                    {{ isRoleSaving(user.id) ? "Saving..." : "Save roles" }}
                  </button>
                </div>
              </td>
              <td>
                <button
                  class="button secondary"
                  type="button"
                  :disabled="isStatusSaving(user.id)"
                  @click="toggleUserStatus(user)"
                >
                  {{
                    isStatusSaving(user.id)
                      ? "Saving..."
                      : user.is_active
                        ? "Disable"
                        : "Enable"
                  }}
                </button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from "vue";

import { adminService } from "@/services/admin-service";
import type { AdminUserCreate, AdminUserRead, RoleRead } from "@/types/admin";

type StatusFilter = "all" | "active" | "inactive";

const users = ref<AdminUserRead[]>([]);
const roles = ref<RoleRead[]>([]);
const searchTerm = ref("");
const statusFilter = ref<StatusFilter>("all");

const isLoading = ref(false);
const isSubmitting = ref(false);
const errorMessage = ref("");
const formError = ref("");
const showCreateForm = ref(false);

const roleSavingUserIds = ref<string[]>([]);
const statusSavingUserIds = ref<string[]>([]);
const selectedRoleIdsByUser = ref<Record<string, string[]>>({});

const form = reactive<AdminUserCreate>({
  email: "",
  full_name: "",
  password: "",
  role_ids: [],
});

const filteredUsers = computed(() => {
  const query = searchTerm.value.toLowerCase();

  return users.value.filter((user) => {
    const matchesQuery =
      !query ||
      user.email.toLowerCase().includes(query) ||
      user.full_name.toLowerCase().includes(query);

    const matchesStatus =
      statusFilter.value === "all" ||
      (statusFilter.value === "active" && user.is_active) ||
      (statusFilter.value === "inactive" && !user.is_active);

    return matchesQuery && matchesStatus;
  });
});

const activeUsersCount = computed(() => users.value.filter((user) => user.is_active).length);

const adminUsersCount = computed(() =>
  users.value.filter((user) => user.roles.includes("admin")).length,
);

function resetForm(): void {
  form.email = "";
  form.full_name = "";
  form.password = "";
  form.role_ids = [];
  formError.value = "";
}

function toggleCreateForm(): void {
  showCreateForm.value = !showCreateForm.value;
  if (!showCreateForm.value) {
    resetForm();
  }
}

function toggleCreateRole(roleId: string): void {
  if (form.role_ids.includes(roleId)) {
    form.role_ids = form.role_ids.filter((id) => id !== roleId);
    return;
  }
  form.role_ids = [...form.role_ids, roleId];
}

function roleIdsForUser(user: AdminUserRead): string[] {
  return roles.value
    .filter((role) => user.roles.includes(role.name))
    .map((role) => role.id);
}

function onRoleSelectionChange(userId: string, event: Event): void {
  const target = event.target as HTMLSelectElement;
  selectedRoleIdsByUser.value[userId] = Array.from(target.selectedOptions).map(
    (option) => option.value,
  );
}

function isRoleSaving(userId: string): boolean {
  return roleSavingUserIds.value.includes(userId);
}

function isStatusSaving(userId: string): boolean {
  return statusSavingUserIds.value.includes(userId);
}

async function loadData(): Promise<void> {
  isLoading.value = true;
  errorMessage.value = "";

  try {
    const [usersData, rolesData] = await Promise.all([
      adminService.listUsers(),
      adminService.listRoles(),
    ]);

    users.value = usersData;
    roles.value = rolesData;

    const nextSelections: Record<string, string[]> = {};
    for (const user of usersData) {
      nextSelections[user.id] = rolesData
        .filter((role) => user.roles.includes(role.name))
        .map((role) => role.id);
    }
    selectedRoleIdsByUser.value = nextSelections;
  } catch (error) {
    errorMessage.value =
      error instanceof Error ? error.message : "Failed to load admin data.";
  } finally {
    isLoading.value = false;
  }
}

async function createUser(): Promise<void> {
  isSubmitting.value = true;
  formError.value = "";

  try {
    await adminService.createUser({
      email: form.email,
      full_name: form.full_name,
      password: form.password,
      role_ids: form.role_ids,
    });

    resetForm();
    showCreateForm.value = false;
    await loadData();
  } catch (error) {
    formError.value =
      error instanceof Error ? error.message : "Failed to create user.";
  } finally {
    isSubmitting.value = false;
  }
}

async function saveUserRoles(userId: string): Promise<void> {
  roleSavingUserIds.value = [...roleSavingUserIds.value, userId];

  try {
    await adminService.updateUserRoles(userId, {
      role_ids: selectedRoleIdsByUser.value[userId] ?? [],
    });
    await loadData();
  } catch (error) {
    errorMessage.value =
      error instanceof Error ? error.message : "Failed to update user roles.";
  } finally {
    roleSavingUserIds.value = roleSavingUserIds.value.filter((id) => id !== userId);
  }
}

async function toggleUserStatus(user: AdminUserRead): Promise<void> {
  statusSavingUserIds.value = [...statusSavingUserIds.value, user.id];

  try {
    await adminService.updateUserStatus(user.id, {
      is_active: !user.is_active,
    });
    await loadData();
  } catch (error) {
    errorMessage.value =
      error instanceof Error ? error.message : "Failed to update user status.";
  } finally {
    statusSavingUserIds.value = statusSavingUserIds.value.filter((id) => id !== user.id);
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
.filters-row,
.form-actions {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  flex-wrap: wrap;
}

.page-actions {
  display: flex;
  gap: 0.75rem;
}

.page-title,
.section-title {
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

.filters-card,
.form-card,
.table-card {
  display: grid;
  gap: 1rem;
}

.search-field {
  min-width: min(100%, 24rem);
}

.status-field {
  min-width: 12rem;
}

.field {
  display: grid;
  gap: 0.4rem;
}

.field-label {
  font-size: 0.875rem;
  color: var(--color-text-muted, #94a3b8);
}

.form-grid {
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

.checkbox-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 0.75rem;
}

.checkbox-option {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.table-wrapper {
  overflow-x: auto;
}

.users-table {
  width: 100%;
  border-collapse: collapse;
}

.users-table th,
.users-table td {
  padding: 0.9rem 0.75rem;
  text-align: left;
  border-bottom: 1px solid var(--color-border, rgba(148, 163, 184, 0.18));
  vertical-align: top;
}

.users-table th {
  color: var(--color-text-muted, #94a3b8);
  font-size: 0.85rem;
  font-weight: 600;
}

.user-cell {
  display: grid;
  gap: 0.25rem;
}

.badge-list {
  display: flex;
  gap: 0.35rem;
  flex-wrap: wrap;
}

.inline-editor {
  display: grid;
  gap: 0.5rem;
  min-width: 14rem;
}

.badge-neutral {
  background: rgba(148, 163, 184, 0.15);
  color: #cbd5e1;
}

.badge-success {
  background: rgba(52, 211, 153, 0.15);
  color: #86efac;
}

.badge-danger {
  background: rgba(251, 113, 133, 0.15);
  color: #fda4af;
}

@media (max-width: 900px) {
  .stats-grid,
  .form-grid,
  .checkbox-grid {
    grid-template-columns: 1fr;
  }

  .field-span-2 {
    grid-column: span 1;
  }
}
</style>