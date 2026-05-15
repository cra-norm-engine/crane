<template>
  <section class="page">

    <!-- ── Page header ── -->
    <header class="page-header">
      <div>
        <h1 class="page-title">Users</h1>
        <p class="muted page-subtitle">
          Invite users, assign roles, and control account status. Changes take effect immediately.
        </p>
      </div>
      <div class="page-actions">
        <button class="btn btn-primary" type="button" @click="showCreateModal = true">
          + Invite user
        </button>
      </div>
    </header>

    <!-- ── Global feedback ── -->
    <div v-if="errorMessage" class="card feedback feedback-error">{{ errorMessage }}</div>
    <div v-if="successMessage" class="card feedback feedback-success">{{ successMessage }}</div>

    <!-- ── Loading / empty ── -->
    <div v-if="isLoading && users.length === 0" class="card empty-panel">
      <div class="spinner" />
      <p>Loading users…</p>
    </div>

    <div v-else-if="!isLoading && users.length === 0" class="card empty-panel">
      <div class="empty-icon">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.4">
          <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/>
          <circle cx="9" cy="7" r="4"/>
          <path d="M23 21v-2a4 4 0 0 0-3-3.87M16 3.13a4 4 0 0 1 0 7.75"/>
        </svg>
      </div>
      <strong>No users yet</strong>
      <p class="muted">Invite your first user to get started.</p>
      <button class="btn btn-primary" type="button" @click="showCreateModal = true">Invite user</button>
    </div>

    <!-- ── Main workspace ── -->
    <div v-if="users.length > 0" class="workspace">

      <!-- ── Left: user list ── -->
      <aside class="card users-aside">

        <!-- Search + filter -->
        <div class="aside-search">
          <div class="search-wrap">
            <svg class="search-icon" viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.6">
              <circle cx="9" cy="9" r="6"/><path d="m15 15 3 3"/>
            </svg>
            <input
              v-model.trim="searchTerm"
              class="search-input"
              type="search"
              placeholder="Search users…"
              aria-label="Search users"
            />
          </div>
          <select v-model="statusFilter" class="filter-select" aria-label="Status filter">
            <option value="all">All</option>
            <option value="active">Active</option>
            <option value="inactive">Inactive</option>
          </select>
        </div>

        <!-- User list -->
        <div class="user-list" role="listbox" aria-label="Users">
          <div v-if="filteredUsers.length === 0" class="list-empty">
            No users match your filters.
          </div>

          <button
            v-for="user in filteredUsers"
            :key="user.id"
            type="button"
            class="user-item"
            :class="{ 'user-item-active': selectedUserId === user.id }"
            role="option"
            :aria-selected="selectedUserId === user.id"
            @click="selectUser(user.id)"
          >
            <!-- Avatar initials -->
            <div class="user-avatar" :class="avatarClass(user)">
              {{ initials(user.full_name) }}
            </div>

            <div class="user-item-body">
              <div class="user-item-name">{{ user.full_name }}</div>
              <div class="user-item-email muted">{{ user.email }}</div>
            </div>

            <div class="user-item-badges">
              <span class="status-dot" :class="user.is_active ? 'dot-active' : 'dot-inactive'" :title="user.is_active ? 'Active' : 'Inactive'" />
              <span v-if="user.auth_provider === 'ldap'" class="pill pill-ldap">LDAP</span>
            </div>
          </button>
        </div>

        <!-- Stats footer -->
        <div class="aside-stats">
          <div class="stat-item">
            <span class="stat-num">{{ users.length }}</span>
            <span class="stat-lbl">Total</span>
          </div>
          <div class="stat-sep" />
          <div class="stat-item">
            <span class="stat-num">{{ activeUsersCount }}</span>
            <span class="stat-lbl">Active</span>
          </div>
          <div class="stat-sep" />
          <div class="stat-item">
            <span class="stat-num">{{ adminUsersCount }}</span>
            <span class="stat-lbl">Admins</span>
          </div>
        </div>
      </aside>

      <!-- ── Right: user detail panel ── -->
      <section v-if="selectedUser" class="card detail-panel">

        <!-- Detail header -->
        <div class="detail-header">
          <div class="detail-avatar" :class="avatarClass(selectedUser)">
            {{ initials(selectedUser.full_name) }}
          </div>
          <div class="detail-meta">
            <div class="detail-name">{{ selectedUser.full_name }}</div>
            <div class="detail-email muted">{{ selectedUser.email }}</div>
            <div class="detail-chips">
              <span class="chip" :class="selectedUser.is_active ? 'chip-success' : 'chip-danger'">
                {{ selectedUser.is_active ? "Active" : "Inactive" }}
              </span>
              <span class="chip" :class="selectedUser.auth_provider === 'ldap' ? 'chip-info' : 'chip-neutral'">
                {{ selectedUser.auth_provider === "ldap" ? "LDAP" : "Local auth" }}
              </span>
              <span v-if="selectedUser.must_change_password && selectedUser.auth_provider === 'local'" class="chip chip-warning">
                Must change password
              </span>
            </div>
          </div>
          <!-- Account status toggle -->
          <div class="detail-status-action">
            <button
              class="btn"
              :class="selectedUser.is_active ? 'btn-danger-soft' : 'btn-success-soft'"
              type="button"
              :disabled="isStatusSaving(selectedUser.id)"
              @click="toggleUserStatus(selectedUser)"
            >
              <span v-if="isStatusSaving(selectedUser.id)">Saving…</span>
              <span v-else-if="selectedUser.is_active">Disable account</span>
              <span v-else>Enable account</span>
            </button>
          </div>
        </div>

        <div class="detail-body">

          <!-- ── Roles section ── -->
          <div class="detail-section">
            <div class="section-heading">
              <div>
                <span class="section-title">Roles</span>
                <span class="section-hint">Assign one or more roles to control access.</span>
              </div>
              <div class="section-count">
                {{ draftRoleIds.length }} selected
              </div>
            </div>

            <div class="roles-grid">
              <label
                v-for="role in roles"
                :key="role.id"
                class="role-option"
                :class="{ 'role-option-checked': draftRoleIds.includes(role.id) }"
              >
                <input
                  type="checkbox"
                  class="role-checkbox"
                  :checked="draftRoleIds.includes(role.id)"
                  @change="toggleDraftRole(role.id)"
                />
                <div class="role-option-icon" :class="roleIconClass(role.name)">
                  <svg viewBox="0 0 20 20">
                    <path d="M10 2 4 5v4c0 4.1 2.4 7.8 6 9 3.6-1.2 6-4.9 6-9V5zm0 3.2a2 2 0 0 1 2 2 2 2 0 0 1-.8 1.6l1.1 3.2H7.7l1.1-3.2A2 2 0 0 1 8 7.2a2 2 0 0 1 2-2z" fill="currentColor"/>
                  </svg>
                </div>
                <div class="role-option-body">
                  <div class="role-option-name">{{ formatRoleName(role.name) }}</div>
                  <div class="role-option-perms muted">{{ role.permissions.length }} permissions</div>
                </div>
                <div class="role-option-check">
                  <svg v-if="draftRoleIds.includes(role.id)" viewBox="0 0 16 16" fill="currentColor">
                    <path d="M13.5 3.5 6 11 2.5 7.5l-1 1L6 13l8.5-8.5z"/>
                  </svg>
                </div>
              </label>
            </div>

            <div class="section-actions">
              <button
                class="btn btn-primary"
                type="button"
                :disabled="isRoleSaving(selectedUser.id) || !rolesChanged"
                @click="saveRoles"
              >
                {{ isRoleSaving(selectedUser.id) ? "Saving…" : "Save roles" }}
              </button>
              <button
                v-if="rolesChanged"
                class="btn btn-secondary"
                type="button"
                @click="discardRoleChanges"
              >
                Discard
              </button>
            </div>
          </div>

          <!-- ── Password section (local users only) ── -->
          <div v-if="selectedUser.auth_provider === 'local'" class="detail-section">
            <div class="section-heading">
              <div>
                <span class="section-title">Password</span>
                <span class="section-hint">Set a temporary password — the user must change it on next login.</span>
              </div>
            </div>

            <div class="pwd-row">
              <label class="field flex-grow">
                <span class="field-label">New temporary password</span>
                <input
                  v-model="newPassword"
                  class="input"
                  type="password"
                  minlength="8"
                  maxlength="255"
                  autocomplete="new-password"
                  placeholder="Min. 8 characters"
                />
              </label>
              <button
                class="btn btn-secondary pwd-btn"
                type="button"
                :disabled="isResetting || newPassword.length < 8"
                @click="submitResetPassword"
              >
                {{ isResetting ? "Saving…" : "Set password" }}
              </button>
            </div>
            <p v-if="resetError" class="form-error">{{ resetError }}</p>
          </div>

          <div v-else class="detail-section">
            <div class="section-heading">
              <div>
                <span class="section-title">Password</span>
                <span class="section-hint">This account is managed by LDAP — passwords cannot be changed here.</span>
              </div>
            </div>
            <div class="ldap-notice">
              <svg viewBox="0 0 20 20" fill="currentColor" style="width:1.1rem;flex-shrink:0">
                <path fill-rule="evenodd" d="M18 10a8 8 0 1 1-16 0 8 8 0 0 1 16 0zm-7-4a1 1 0 1 1-2 0 1 1 0 0 1 2 0zM9 9a1 1 0 0 0 0 2v3a1 1 0 0 0 1 1h1a1 1 0 1 0 0-2v-3a1 1 0 0 0-1-1H9z" clip-rule="evenodd"/>
              </svg>
              Managed via LDAP. Password changes must be performed in your directory service.
            </div>
          </div>

        </div>
      </section>

      <!-- No selection placeholder -->
      <div v-else class="card detail-panel detail-placeholder">
        <div class="placeholder-icon">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.2">
            <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/>
            <circle cx="12" cy="7" r="4"/>
          </svg>
        </div>
        <p class="muted">Select a user to view and edit their profile.</p>
      </div>

    </div>
  </section>

  <!-- ── Create user modal ── -->
  <Teleport to="body">
    <Transition name="modal">
      <div
        v-if="showCreateModal"
        class="modal-backdrop"
        role="dialog"
        aria-modal="true"
        aria-label="Invite user"
        @click.self="closeCreateModal"
      >
        <div class="modal">
          <div class="modal-header">
            <div>
              <h2 class="modal-title">Invite user</h2>
              <p class="muted" style="margin: 0.2rem 0 0; font-size: 0.87rem;">
                Create a local account and optionally assign roles immediately.
              </p>
            </div>
            <button class="btn-icon" type="button" @click="closeCreateModal" aria-label="Close">
              <svg viewBox="0 0 16 16" fill="currentColor"><path d="M3.5 3.5 8 8l4.5-4.5 1 1L9 9l4.5 4.5-1 1L8 10l-4.5 4.5-1-1L7 9 2.5 4.5z"/></svg>
            </button>
          </div>

          <form class="modal-body" @submit.prevent="createUser">
            <div class="form-row">
              <label class="field">
                <span class="field-label">Full name <span class="required">*</span></span>
                <input v-model.trim="form.full_name" class="input" required maxlength="255" placeholder="Jane Smith" />
              </label>
              <label class="field">
                <span class="field-label">Email <span class="required">*</span></span>
                <input v-model.trim="form.email" class="input" type="email" required maxlength="320" placeholder="jane@company.com" />
              </label>
            </div>

            <label class="field">
              <span class="field-label">Password <span class="required">*</span></span>
              <input
                v-model="form.password"
                class="input"
                type="password"
                required
                minlength="8"
                maxlength="255"
                placeholder="Min. 8 characters"
                autocomplete="new-password"
              />
            </label>

            <div class="field">
              <span class="field-label">Roles</span>
              <div class="modal-roles-grid">
                <label
                  v-for="role in roles"
                  :key="role.id"
                  class="modal-role-option"
                  :class="{ 'modal-role-option-checked': form.role_ids.includes(role.id) }"
                >
                  <input
                    type="checkbox"
                    :checked="form.role_ids.includes(role.id)"
                    @change="toggleCreateRole(role.id)"
                  />
                  <span class="modal-role-name">{{ formatRoleName(role.name) }}</span>
                  <span class="modal-role-perms muted">{{ role.permissions.length }} perms</span>
                </label>
              </div>
            </div>

            <p v-if="formError" class="form-error">{{ formError }}</p>
          </form>

          <div class="modal-footer">
            <button class="btn btn-secondary" type="button" @click="closeCreateModal">Cancel</button>
            <button class="btn btn-primary" type="submit" :disabled="isSubmitting" @click.prevent="createUser">
              {{ isSubmitting ? "Creating…" : "Create user" }}
            </button>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref, watch } from "vue";

import { adminService } from "@/services/admin-service";
import type { AdminUserCreate, AdminUserRead, RoleRead } from "@/types/admin";

/* ─── State ─────────────────────────────────────────── */
type StatusFilter = "all" | "active" | "inactive";

const users             = ref<AdminUserRead[]>([]);
const roles             = ref<RoleRead[]>([]);
const selectedUserId    = ref("");
const searchTerm        = ref("");
const statusFilter      = ref<StatusFilter>("all");

const isLoading         = ref(false);
const isSubmitting      = ref(false);
const isResetting       = ref(false);
const errorMessage      = ref("");
const successMessage    = ref("");
const formError         = ref("");
const resetError        = ref("");
const showCreateModal   = ref(false);

const newPassword       = ref("");
const draftRoleIds      = ref<string[]>([]);
const savedRoleIds      = ref<string[]>([]);

const roleSavingIds     = ref<string[]>([]);
const statusSavingIds   = ref<string[]>([]);

const form = reactive<AdminUserCreate>({
  email: "",
  full_name: "",
  password: "",
  role_ids: [],
});

/* ─── Computed ──────────────────────────────────────── */
const filteredUsers = computed(() => {
  const q = searchTerm.value.toLowerCase();
  return users.value.filter((u: AdminUserRead) => {
    const matchQuery = !q || u.email.toLowerCase().includes(q) || u.full_name.toLowerCase().includes(q);
    const matchStatus =
      statusFilter.value === "all" ||
      (statusFilter.value === "active" && u.is_active) ||
      (statusFilter.value === "inactive" && !u.is_active);
    return matchQuery && matchStatus;
  });
});

const selectedUser = computed<AdminUserRead | null>(
  () => users.value.find((u: AdminUserRead) => u.id === selectedUserId.value) ?? null,
);

const activeUsersCount = computed(() => users.value.filter((u: AdminUserRead) => u.is_active).length);
const adminUsersCount  = computed(() => users.value.filter((u: AdminUserRead) => u.roles.includes("admin")).length);

const rolesChanged = computed(
  () => JSON.stringify([...draftRoleIds.value].sort()) !== JSON.stringify([...savedRoleIds.value].sort()),
);

/* ─── Watchers ──────────────────────────────────────── */
/* Sync draft roles whenever the selected user changes */
watch(selectedUser, (user: AdminUserRead | null) => {
  if (!user) { draftRoleIds.value = []; savedRoleIds.value = []; return; }
  const ids = roles.value.filter((r: RoleRead) => user.roles.includes(r.name)).map((r: RoleRead) => r.id);
  draftRoleIds.value = [...ids];
  savedRoleIds.value = [...ids];
  newPassword.value = "";
  resetError.value  = "";
});

/* ─── Helpers ───────────────────────────────────────── */
function initials(name: string): string {
  return name.trim().split(/\s+/).map((p) => p[0]?.toUpperCase() ?? "").slice(0, 2).join("");
}

function avatarClass(user: AdminUserRead): string {
  const colors = ["av-blue", "av-violet", "av-teal", "av-orange", "av-rose", "av-emerald"];
  let hash = 0;
  for (const c of user.email) hash = (hash * 31 + c.charCodeAt(0)) & 0xffff;
  return colors[hash % colors.length] ?? "av-blue";
}

function roleIconClass(name: string): string {
  const map: Record<string, string> = {
    admin: "icon-red",
    cybersecurity_engineer: "icon-orange",
    development_team: "icon-blue",
    product_owner: "icon-indigo",
    lifecycle_manager: "icon-teal",
    legal_team: "icon-violet",
    product_management: "icon-emerald",
  };
  return map[name] ?? "icon-slate";
}

const ROLE_LABELS: Record<string, string> = {
  admin: "Administrator",
  cybersecurity_engineer: "Cybersecurity Engineer",
  development_team: "Development Team",
  product_owner: "Product Owner",
  lifecycle_manager: "Lifecycle Manager",
  legal_team: "Legal Team",
  product_management: "Product Management",
};

function formatRoleName(name: string): string {
  return ROLE_LABELS[name] ?? name.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
}

function isRoleSaving(userId: string): boolean   { return roleSavingIds.value.includes(userId); }
function isStatusSaving(userId: string): boolean { return statusSavingIds.value.includes(userId); }

function setSuccess(msg: string): void {
  successMessage.value = msg;
  setTimeout(() => { successMessage.value = ""; }, 3500);
}

/* ─── Actions ───────────────────────────────────────── */
function selectUser(id: string): void { selectedUserId.value = id; }

function toggleDraftRole(roleId: string): void {
  if (draftRoleIds.value.includes(roleId)) {
    draftRoleIds.value = draftRoleIds.value.filter((id: string) => id !== roleId);
  } else {
    draftRoleIds.value = [...draftRoleIds.value, roleId];
  }
}

function discardRoleChanges(): void {
  draftRoleIds.value = [...savedRoleIds.value];
}

function toggleCreateRole(roleId: string): void {
  if (form.role_ids.includes(roleId)) {
    form.role_ids = form.role_ids.filter((id: string) => id !== roleId);
  } else {
    form.role_ids = [...form.role_ids, roleId];
  }
}

function closeCreateModal(): void {
  showCreateModal.value = false;
  form.email = "";
  form.full_name = "";
  form.password = "";
  form.role_ids = [];
  formError.value = "";
}

/* ─── Data loading ──────────────────────────────────── */
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
    /* Preserve selection if user still exists after reload */
    if (selectedUserId.value && !usersData.some((u: AdminUserRead) => u.id === selectedUserId.value)) {
      selectedUserId.value = usersData[0]?.id ?? "";
    }
    if (!selectedUserId.value && usersData.length > 0) {
      selectedUserId.value = usersData[0]!.id;
    }
  } catch (err) {
    errorMessage.value = err instanceof Error ? err.message : "Failed to load users.";
  } finally {
    isLoading.value = false;
  }
}

/* ─── Mutations ─────────────────────────────────────── */
async function createUser(): Promise<void> {
  isSubmitting.value = true;
  formError.value = "";
  try {
    const created = await adminService.createUser({ ...form });
    closeCreateModal();
    await loadData();
    selectedUserId.value = created.id;
    setSuccess(`User "${form.full_name || created.email}" created.`);
  } catch (err) {
    formError.value = err instanceof Error ? err.message : "Failed to create user.";
  } finally {
    isSubmitting.value = false;
  }
}

async function saveRoles(): Promise<void> {
  if (!selectedUser.value) return;
  const userId = selectedUser.value.id;
  roleSavingIds.value = [...roleSavingIds.value, userId];
  try {
    await adminService.updateUserRoles(userId, { role_ids: draftRoleIds.value });
    await loadData();
    setSuccess("Roles updated.");
  } catch (err) {
    errorMessage.value = err instanceof Error ? err.message : "Failed to update roles.";
  } finally {
    roleSavingIds.value = roleSavingIds.value.filter((id: string) => id !== userId);
  }
}

async function toggleUserStatus(user: AdminUserRead): Promise<void> {
  statusSavingIds.value = [...statusSavingIds.value, user.id];
  try {
    await adminService.updateUserStatus(user.id, { is_active: !user.is_active });
    await loadData();
    setSuccess(user.is_active ? "Account disabled." : "Account enabled.");
  } catch (err) {
    errorMessage.value = err instanceof Error ? err.message : "Failed to update status.";
  } finally {
    statusSavingIds.value = statusSavingIds.value.filter((id: string) => id !== user.id);
  }
}

async function submitResetPassword(): Promise<void> {
  if (!selectedUser.value || newPassword.value.length < 8) return;
  resetError.value = "";
  isResetting.value = true;
  try {
    await adminService.resetUserPassword(selectedUser.value.id, { new_password: newPassword.value });
    newPassword.value = "";
    setSuccess("Password reset. User will be prompted to change it on next login.");
  } catch (err) {
    resetError.value = err instanceof Error ? err.message : "Failed to reset password.";
  } finally {
    isResetting.value = false;
  }
}

onMounted(() => { void loadData(); });
</script>

<style scoped>
/* ── Layout ─────────────────────────────────────────── */
.page { display: grid; gap: 1rem; }

.page-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 1rem;
  flex-wrap: wrap;
}
.page-title    { margin: 0; }
.page-subtitle { margin-top: 0.35rem; }

.page-actions {
  display: flex;
  gap: 0.75rem;
  flex-shrink: 0;
}

.workspace {
  display: grid;
  grid-template-columns: 300px 1fr;
  gap: 1rem;
  align-items: start;
}

/* ── Feedback ────────────────────────────────────────── */
.feedback {
  padding: 0.85rem 1.1rem;
  border-radius: 0.75rem;
  font-size: 0.9rem;
}
.feedback-error   { background: rgba(251,113,133,0.12); color: #fda4af; border: 1px solid rgba(251,113,133,0.25); }
.feedback-success { background: rgba(52,211,153,0.12);  color: #86efac; border: 1px solid rgba(52,211,153,0.25); }

/* ── Empty / loading ─────────────────────────────────── */
.empty-panel {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.75rem;
  padding: 3rem 1rem;
  text-align: center;
}
.empty-icon {
  width: 3.5rem;
  height: 3.5rem;
  color: var(--color-text-muted, #94a3b8);
  opacity: 0.5;
}
.empty-icon svg { width: 100%; height: 100%; }

.spinner {
  width: 2rem; height: 2rem;
  border: 3px solid var(--color-border, rgba(148,163,184,0.2));
  border-top-color: var(--color-primary, #6366f1);
  border-radius: 50%;
  animation: spin 0.7s linear infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }

/* ── Users aside ─────────────────────────────────────── */
.users-aside {
  display: flex;
  flex-direction: column;
  gap: 0;
  padding: 0;
  overflow: hidden;
  position: sticky;
  top: 1rem;
}

.aside-search {
  display: flex;
  gap: 0.5rem;
  padding: 0.9rem 1rem;
  border-bottom: 1px solid var(--color-border, rgba(148,163,184,0.18));
}

.search-wrap {
  position: relative;
  flex: 1;
}
.search-icon {
  position: absolute;
  left: 0.65rem;
  top: 50%;
  transform: translateY(-50%);
  width: 0.9rem;
  height: 0.9rem;
  color: var(--color-text-muted, #94a3b8);
  pointer-events: none;
}
.search-input {
  width: 100%;
  padding: 0.45rem 0.65rem 0.45rem 2rem;
  background: var(--color-surface-soft, rgba(15,23,42,0.4));
  border: 1px solid var(--color-border, rgba(148,163,184,0.18));
  border-radius: 0.55rem;
  color: inherit;
  font-size: 0.85rem;
  outline: none;
  box-sizing: border-box;
}
.search-input:focus { border-color: var(--color-primary, #6366f1); }
.search-input::placeholder { color: var(--color-text-muted, #94a3b8); }

.filter-select {
  padding: 0.45rem 0.6rem;
  background: var(--color-surface-soft, rgba(15,23,42,0.4));
  border: 1px solid var(--color-border, rgba(148,163,184,0.18));
  border-radius: 0.55rem;
  color: inherit;
  font-size: 0.82rem;
  cursor: pointer;
  outline: none;
}
.filter-select:focus { border-color: var(--color-primary, #6366f1); }

.user-list {
  overflow-y: auto;
  max-height: 60vh;
  padding: 0.5rem 0;
}

.list-empty {
  padding: 1.25rem 1rem;
  text-align: center;
  color: var(--color-text-muted, #94a3b8);
  font-size: 0.875rem;
}

.user-item {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  width: 100%;
  padding: 0.7rem 1rem;
  border: none;
  background: transparent;
  cursor: pointer;
  text-align: left;
  color: inherit;
  transition: background 0.12s;
}
.user-item:hover  { background: var(--color-surface-soft, rgba(148,163,184,0.07)); }
.user-item-active { background: var(--color-primary-subtle, rgba(99,102,241,0.12)) !important; }

.user-avatar {
  width: 2.2rem;
  height: 2.2rem;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.78rem;
  font-weight: 700;
  flex-shrink: 0;
  letter-spacing: 0.02em;
}
.av-blue    { background: rgba(99,102,241,0.18); color: #818cf8; }
.av-violet  { background: rgba(139,92,246,0.18); color: #a78bfa; }
.av-teal    { background: rgba(20,184,166,0.18);  color: #5eead4; }
.av-orange  { background: rgba(249,115,22,0.18);  color: #fb923c; }
.av-rose    { background: rgba(244,63,94,0.18);   color: #fb7185; }
.av-emerald { background: rgba(16,185,129,0.18);  color: #6ee7b7; }

.user-item-body  { flex: 1; min-width: 0; }
.user-item-name  { font-size: 0.875rem; font-weight: 600; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.user-item-email { font-size: 0.78rem; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }

.user-item-badges { display: flex; align-items: center; gap: 0.4rem; flex-shrink: 0; }

.status-dot {
  width: 0.55rem;
  height: 0.55rem;
  border-radius: 50%;
  display: inline-block;
}
.dot-active   { background: #34d399; }
.dot-inactive { background: #94a3b8; }

.pill {
  font-size: 0.68rem;
  font-weight: 600;
  padding: 0.15rem 0.45rem;
  border-radius: 999px;
  text-transform: uppercase;
  letter-spacing: 0.04em;
}
.pill-ldap { background: rgba(56,189,248,0.15); color: #7dd3fc; }

/* ── Aside stats ─────────────────────────────────────── */
.aside-stats {
  display: flex;
  align-items: center;
  justify-content: space-around;
  padding: 0.85rem 1rem;
  border-top: 1px solid var(--color-border, rgba(148,163,184,0.18));
  margin-top: auto;
}
.stat-item { display: flex; flex-direction: column; align-items: center; gap: 0.15rem; }
.stat-num  { font-size: 1.25rem; font-weight: 700; }
.stat-lbl  { font-size: 0.72rem; color: var(--color-text-muted, #94a3b8); }
.stat-sep  { width: 1px; height: 2rem; background: var(--color-border, rgba(148,163,184,0.18)); }

/* ── Detail panel ────────────────────────────────────── */
.detail-panel { padding: 0; overflow: hidden; }

.detail-header {
  display: flex;
  align-items: flex-start;
  gap: 1rem;
  padding: 1.5rem;
  border-bottom: 1px solid var(--color-border, rgba(148,163,184,0.18));
  flex-wrap: wrap;
}

.detail-avatar {
  width: 3.5rem;
  height: 3.5rem;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.1rem;
  font-weight: 700;
  flex-shrink: 0;
}

.detail-meta    { flex: 1; min-width: 0; }
.detail-name    { font-size: 1.15rem; font-weight: 700; }
.detail-email   { font-size: 0.875rem; margin-top: 0.15rem; }
.detail-chips   { display: flex; gap: 0.4rem; flex-wrap: wrap; margin-top: 0.6rem; }

.chip {
  display: inline-flex;
  align-items: center;
  font-size: 0.75rem;
  font-weight: 600;
  padding: 0.25rem 0.65rem;
  border-radius: 999px;
}
.chip-success { background: rgba(52,211,153,0.15); color: #86efac; }
.chip-danger  { background: rgba(251,113,133,0.15); color: #fda4af; }
.chip-info    { background: rgba(56,189,248,0.12); color: #7dd3fc; }
.chip-neutral { background: rgba(148,163,184,0.12); color: #94a3b8; }
.chip-warning { background: rgba(251,191,36,0.15); color: #fbbf24; border: 1px solid rgba(251,191,36,0.3); }

.detail-status-action { margin-left: auto; flex-shrink: 0; }

/* ── Detail body ─────────────────────────────────────── */
.detail-body { display: grid; }

.detail-section {
  padding: 1.5rem;
  display: grid;
  gap: 1rem;
  border-bottom: 1px solid var(--color-border, rgba(148,163,184,0.12));
}
.detail-section:last-child { border-bottom: none; }

.section-heading {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 1rem;
}
.section-title {
  display: block;
  font-size: 0.9rem;
  font-weight: 700;
  letter-spacing: 0.01em;
}
.section-hint {
  display: block;
  font-size: 0.82rem;
  color: var(--color-text-muted, #94a3b8);
  margin-top: 0.2rem;
}
.section-count {
  font-size: 0.82rem;
  color: var(--color-text-muted, #94a3b8);
  white-space: nowrap;
  padding-top: 0.15rem;
}

/* ── Roles grid ──────────────────────────────────────── */
.roles-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
  gap: 0.5rem;
}

.role-option {
  display: flex;
  align-items: center;
  gap: 0.65rem;
  padding: 0.65rem 0.85rem;
  border-radius: 0.65rem;
  border: 1px solid var(--color-border, rgba(148,163,184,0.18));
  cursor: pointer;
  transition: border-color 0.12s, background 0.12s;
  user-select: none;
}
.role-option:hover         { border-color: var(--color-primary, #6366f1); background: rgba(99,102,241,0.05); }
.role-option-checked       { border-color: var(--color-primary, #6366f1); background: rgba(99,102,241,0.1); }

.role-checkbox { display: none; }

.role-option-icon {
  width: 1.9rem;
  height: 1.9rem;
  border-radius: 0.45rem;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}
.role-option-icon svg { width: 1rem; height: 1rem; }

.icon-red     { background: rgba(239,68,68,0.15);   color: #f87171; }
.icon-orange  { background: rgba(249,115,22,0.15);  color: #fb923c; }
.icon-blue    { background: rgba(59,130,246,0.15);  color: #60a5fa; }
.icon-indigo  { background: rgba(99,102,241,0.15);  color: #818cf8; }
.icon-teal    { background: rgba(20,184,166,0.15);  color: #5eead4; }
.icon-violet  { background: rgba(139,92,246,0.15);  color: #a78bfa; }
.icon-emerald { background: rgba(16,185,129,0.15);  color: #6ee7b7; }
.icon-slate   { background: rgba(148,163,184,0.15); color: #94a3b8; }

.role-option-body    { flex: 1; min-width: 0; }
.role-option-name    { font-size: 0.875rem; font-weight: 600; }
.role-option-perms   { font-size: 0.75rem; margin-top: 0.1rem; }

.role-option-check {
  width: 1.1rem;
  height: 1.1rem;
  color: var(--color-primary, #6366f1);
  flex-shrink: 0;
}
.role-option-check svg { width: 100%; height: 100%; }

.section-actions { display: flex; gap: 0.65rem; }

/* ── Password row ────────────────────────────────────── */
.pwd-row {
  display: flex;
  align-items: flex-end;
  gap: 0.75rem;
}
.flex-grow { flex: 1; }
.pwd-btn   { align-self: flex-end; flex-shrink: 0; }

.field { display: grid; gap: 0.4rem; }
.field-label { font-size: 0.82rem; color: var(--color-text-muted, #94a3b8); }
.input {
  padding: 0.55rem 0.8rem;
  background: var(--color-surface-soft, rgba(15,23,42,0.4));
  border: 1px solid var(--color-border, rgba(148,163,184,0.18));
  border-radius: 0.55rem;
  color: inherit;
  font-size: 0.875rem;
  width: 100%;
  box-sizing: border-box;
  outline: none;
}
.input:focus { border-color: var(--color-primary, #6366f1); }

.ldap-notice {
  display: flex;
  align-items: flex-start;
  gap: 0.6rem;
  padding: 0.85rem 1rem;
  background: rgba(56,189,248,0.07);
  border: 1px solid rgba(56,189,248,0.2);
  border-radius: 0.65rem;
  font-size: 0.875rem;
  color: #7dd3fc;
}

.form-error { color: #fda4af; font-size: 0.875rem; margin: 0; }

/* ── Detail placeholder ──────────────────────────────── */
.detail-placeholder {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 0.75rem;
  min-height: 20rem;
  text-align: center;
}
.placeholder-icon {
  width: 3.5rem;
  height: 3.5rem;
  color: var(--color-text-muted, #94a3b8);
  opacity: 0.35;
}
.placeholder-icon svg { width: 100%; height: 100%; }

/* ── Buttons ─────────────────────────────────────────── */
.btn {
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
  padding: 0.55rem 1.1rem;
  border-radius: 0.6rem;
  font-size: 0.875rem;
  font-weight: 600;
  border: none;
  cursor: pointer;
  white-space: nowrap;
  transition: opacity 0.12s, background 0.12s;
}
.btn:disabled { opacity: 0.5; cursor: not-allowed; }

.btn-primary   { background: var(--color-primary, #6366f1); color: #fff; }
.btn-secondary { background: var(--color-surface-soft, rgba(148,163,184,0.12)); color: inherit; border: 1px solid var(--color-border, rgba(148,163,184,0.2)); }
.btn-success-soft { background: rgba(52,211,153,0.15); color: #86efac; border: 1px solid rgba(52,211,153,0.25); }
.btn-danger-soft  { background: rgba(251,113,133,0.12); color: #fda4af; border: 1px solid rgba(251,113,133,0.25); }

.btn-icon {
  width: 2rem; height: 2rem;
  display: flex; align-items: center; justify-content: center;
  border: none; background: transparent; cursor: pointer; color: inherit;
  border-radius: 0.4rem;
  opacity: 0.65;
  transition: opacity 0.12s;
  flex-shrink: 0;
}
.btn-icon:hover { opacity: 1; }
.btn-icon svg { width: 0.9rem; height: 0.9rem; }

/* ── Create user modal ───────────────────────────────── */
.modal-backdrop {
  position: fixed;
  inset: 0;
  background: rgba(0,0,0,0.55);
  z-index: 200;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 1rem;
  backdrop-filter: blur(6px);
}

.modal {
  background: var(--color-modal-bg, #0f172a);
  border: 1px solid var(--color-modal-border, rgba(148,163,184,0.2));
  border-radius: 1.1rem;
  width: 100%;
  max-width: 38rem;
  display: flex;
  flex-direction: column;
  box-shadow: 0 24px 80px rgba(0,0,0,0.55);
  overflow: hidden;
  max-height: 90vh;
}

.modal-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 1rem;
  padding: 1.35rem 1.5rem 1.1rem;
  border-bottom: 1px solid var(--color-border, rgba(148,163,184,0.18));
  flex-shrink: 0;
}
.modal-title { margin: 0; font-size: 1.05rem; font-weight: 700; }

.modal-body {
  padding: 1.35rem 1.5rem;
  display: flex;
  flex-direction: column;
  gap: 1rem;
  overflow-y: auto;
}

.form-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1rem;
}

.modal-roles-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
  gap: 0.4rem;
  margin-top: 0.35rem;
}

.modal-role-option {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 0.7rem;
  border-radius: 0.55rem;
  border: 1px solid var(--color-border, rgba(148,163,184,0.18));
  cursor: pointer;
  transition: border-color 0.12s, background 0.12s;
  font-size: 0.85rem;
}
.modal-role-option:hover          { border-color: var(--color-primary, #6366f1); }
.modal-role-option-checked        { border-color: var(--color-primary, #6366f1); background: rgba(99,102,241,0.1); }
.modal-role-option input          { accent-color: var(--color-primary, #6366f1); }
.modal-role-name  { flex: 1; font-weight: 500; }
.modal-role-perms { font-size: 0.75rem; white-space: nowrap; }

.required { color: #f87171; }

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 0.75rem;
  padding: 1rem 1.5rem;
  border-top: 1px solid var(--color-border, rgba(148,163,184,0.18));
  flex-shrink: 0;
}

/* ── Modal transition ────────────────────────────────── */
.modal-enter-active, .modal-leave-active { transition: opacity 0.18s ease; }
.modal-enter-active .modal, .modal-leave-active .modal { transition: transform 0.18s ease, opacity 0.18s ease; }
.modal-enter-from, .modal-leave-to { opacity: 0; }
.modal-enter-from .modal, .modal-leave-to .modal { transform: translateY(12px) scale(0.98); opacity: 0; }

/* ── Responsive ──────────────────────────────────────── */
@media (max-width: 860px) {
  .workspace         { grid-template-columns: 1fr; }
  .users-aside       { position: static; }
  .user-list         { max-height: 40vh; }
  .roles-grid        { grid-template-columns: 1fr; }
  .form-row          { grid-template-columns: 1fr; }
  .pwd-row           { flex-direction: column; align-items: stretch; }
  .detail-status-action { margin-left: 0; }
}
</style>

<style>
/* ── Light theme overrides ───────────────────────────── */
:root[data-theme="light"] .chip-success  { background: rgba(21,128,61,0.1);   color: #15803d; }
:root[data-theme="light"] .chip-danger   { background: rgba(239,68,68,0.1);   color: #be123c; }
:root[data-theme="light"] .chip-info     { background: rgba(2,132,199,0.1);   color: #0369a1; }
:root[data-theme="light"] .chip-neutral  { background: rgba(71,85,105,0.1);   color: #475569; }
:root[data-theme="light"] .chip-warning  { background: rgba(180,130,0,0.1);   color: #92400e; }
:root[data-theme="light"] .pill-ldap     { background: rgba(2,132,199,0.1);   color: #0369a1; }
:root[data-theme="light"] .ldap-notice   { background: rgba(2,132,199,0.07);  color: #0369a1; border-color: rgba(2,132,199,0.2); }
:root[data-theme="light"] .btn-success-soft { background: rgba(21,128,61,0.1);   color: #15803d; border-color: rgba(21,128,61,0.25); }
:root[data-theme="light"] .btn-danger-soft  { background: rgba(239,68,68,0.1);   color: #be123c; border-color: rgba(239,68,68,0.25); }
:root[data-theme="light"] .icon-red     { background: rgba(239,68,68,0.1);   color: #dc2626; }
:root[data-theme="light"] .icon-orange  { background: rgba(234,88,12,0.1);   color: #ea580c; }
:root[data-theme="light"] .icon-blue    { background: rgba(37,99,235,0.1);   color: #2563eb; }
:root[data-theme="light"] .icon-indigo  { background: rgba(79,70,229,0.1);   color: #4f46e5; }
:root[data-theme="light"] .icon-teal    { background: rgba(13,148,136,0.1);  color: #0d9488; }
:root[data-theme="light"] .icon-violet  { background: rgba(124,58,237,0.1);  color: #7c3aed; }
:root[data-theme="light"] .icon-emerald { background: rgba(5,150,105,0.1);   color: #059669; }
:root[data-theme="light"] .icon-slate   { background: rgba(71,85,105,0.1);   color: #475569; }
:root[data-theme="light"] .modal        { background: #fff; }
</style>
