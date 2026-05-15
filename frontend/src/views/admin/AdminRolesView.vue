<template>
  <section class="page">

    <!-- ── Page header ── -->
    <header class="page-header">
      <div>
        <h1 class="page-title">Roles &amp; access</h1>
        <p class="muted page-subtitle">
          Define roles, assign grouped permissions, and audit access across the platform.
          Changes take effect immediately on the user's next request.
        </p>
      </div>
      <div class="page-actions">
        <button class="btn btn-primary" type="button" @click="showCreateModal = true">
          + New role
        </button>
      </div>
    </header>

    <!-- ── Global feedback ── -->
    <div v-if="errorMessage" class="card feedback feedback-error">{{ errorMessage }}</div>
    <div v-if="successMessage" class="card feedback feedback-success">{{ successMessage }}</div>

    <!-- ── Loading / empty ── -->
    <div v-if="isLoading && roles.length === 0" class="card empty-panel">Loading roles…</div>
    <div v-else-if="!isLoading && roles.length === 0" class="card empty-panel">
      <strong>No roles found.</strong>
      <p class="muted">Create your first custom role to begin assigning access.</p>
    </div>

    <!-- ── Main workspace ── -->
    <div v-if="roles.length > 0" class="workspace">

      <!-- ── Left: role list ── -->
      <aside class="card roles-aside">
        <div class="aside-header">
          <span class="aside-title">Roles</span>
          <span class="count-badge">{{ roles.length }}</span>
        </div>

        <div class="role-list">
          <button
            v-for="role in sortedRoles"
            :key="role.id"
            type="button"
            class="role-item"
            :class="{ 'role-item-active': selectedRoleId === role.id }"
            @click="selectRole(role.id)"
          >
            <div class="role-item-icon" :class="roleIconClass(role.name)">
              <svg viewBox="0 0 20 20"><path d="M10 2 4 5v4c0 4.1 2.4 7.8 6 9 3.6-1.2 6-4.9 6-9V5zm0 3.2a2 2 0 0 1 2 2 2 2 0 0 1-.8 1.6l1.1 3.2H7.7l1.1-3.2A2 2 0 0 1 8 7.2a2 2 0 0 1 2-2z" fill="currentColor"/></svg>
            </div>
            <div class="role-item-body">
              <div class="role-item-name">{{ formatRoleName(role.name) }}</div>
              <div class="role-item-meta">
                <span class="perm-count">{{ role.permissions.length }} permissions</span>
                <span class="role-type-badge" :class="isSystemRole(role.name) ? 'badge-system' : 'badge-custom'">
                  {{ isSystemRole(role.name) ? "System" : "Custom" }}
                </span>
              </div>
            </div>
            <span class="role-chevron">›</span>
          </button>
        </div>

        <!-- Stats summary -->
        <div class="aside-stats">
          <div class="stat-item">
            <span class="stat-num">{{ systemRolesCount }}</span>
            <span class="stat-lbl">System roles</span>
          </div>
          <div class="stat-sep" />
          <div class="stat-item">
            <span class="stat-num">{{ roles.length - systemRolesCount }}</span>
            <span class="stat-lbl">Custom roles</span>
          </div>
          <div class="stat-sep" />
          <div class="stat-item">
            <span class="stat-num">{{ permissions.length }}</span>
            <span class="stat-lbl">Permissions</span>
          </div>
        </div>
      </aside>

      <!-- ── Right: role detail ── -->
      <section v-if="selectedRole && roleDrafts[selectedRole.id]" class="card detail-panel">

        <!-- Detail header -->
        <div class="detail-header">
          <div class="detail-header-left">
            <div class="detail-role-icon" :class="roleIconClass(selectedRole.name)">
              <svg viewBox="0 0 20 20"><path d="M10 2 4 5v4c0 4.1 2.4 7.8 6 9 3.6-1.2 6-4.9 6-9V5zm0 3.2a2 2 0 0 1 2 2 2 2 0 0 1-.8 1.6l1.1 3.2H7.7l1.1-3.2A2 2 0 0 1 8 7.2a2 2 0 0 1 2-2z" fill="currentColor"/></svg>
            </div>
            <div>
              <div class="detail-role-name">{{ formatRoleName(selectedRole.name) }}</div>
              <div class="detail-role-desc muted">{{ selectedRole.description || "No description." }}</div>
            </div>
          </div>
          <div class="detail-header-right">
            <span class="role-type-badge" :class="isSystemRole(selectedRole.name) ? 'badge-system' : 'badge-custom'">
              {{ isSystemRole(selectedRole.name) ? "System role" : "Custom role" }}
            </span>
            <span class="perm-count-pill">
              {{ roleDrafts[selectedRole.id].permission_ids.length }} / {{ permissions.length }} permissions
            </span>
          </div>
        </div>

        <form @submit.prevent="saveRole(selectedRole)">

          <!-- Metadata row -->
          <div class="meta-grid">
            <label class="field">
              <span class="field-label">Role name</span>
              <input
                v-model.trim="roleDrafts[selectedRole.id].name"
                required
                maxlength="100"
                :disabled="isSystemRole(selectedRole.name)"
              />
            </label>
            <label class="field">
              <span class="field-label">Description</span>
              <input
                v-model.trim="roleDrafts[selectedRole.id].description"
                maxlength="255"
                placeholder="Describe the purpose of this role…"
              />
            </label>
          </div>

          <!-- Permission groups -->
          <div class="perm-section">
            <div class="perm-section-header">
              <h3 class="perm-section-title">Permissions</h3>
              <div class="perm-section-actions">
                <button type="button" class="btn-link" @click="selectAll(selectedRole.id)">Select all</button>
                <span class="dot-sep">·</span>
                <button type="button" class="btn-link" @click="clearAll(selectedRole.id)">Clear all</button>
              </div>
            </div>

            <div class="perm-groups">
              <div
                v-for="group in permissionGroups"
                :key="group.id"
                class="perm-group"
              >
                <div class="perm-group-header">
                  <div class="perm-group-icon" :class="group.colorClass">
                    <span v-html="group.icon" />
                  </div>
                  <div class="perm-group-meta">
                    <span class="perm-group-name">{{ group.label }}</span>
                    <span class="perm-group-count muted">
                      {{ groupSelectedCount(selectedRole.id, group) }}/{{ group.permissions.length }}
                    </span>
                  </div>
                  <!-- Group toggle: select/deselect all in group -->
                  <button
                    type="button"
                    class="group-toggle"
                    :class="{ 'group-toggle-on': groupSelectedCount(selectedRole.id, group) === group.permissions.length }"
                    @click="toggleGroup(selectedRole.id, group)"
                    :title="groupSelectedCount(selectedRole.id, group) === group.permissions.length ? 'Remove all in group' : 'Add all in group'"
                  >
                    <svg viewBox="0 0 20 20" style="width:12px;height:12px">
                      <path v-if="groupSelectedCount(selectedRole.id, group) === group.permissions.length" d="M4 10h12" stroke="currentColor" stroke-width="2" fill="none"/>
                      <path v-else d="M10 4v12M4 10h12" stroke="currentColor" stroke-width="2" fill="none"/>
                    </svg>
                  </button>
                </div>

                <div class="perm-rows">
                  <label
                    v-for="perm in group.permissions"
                    :key="perm.id"
                    class="perm-row"
                    :class="{ 'perm-row-checked': roleDrafts[selectedRole.id].permission_ids.includes(perm.id) }"
                  >
                    <input
                      type="checkbox"
                      class="perm-checkbox"
                      :checked="roleDrafts[selectedRole.id].permission_ids.includes(perm.id)"
                      @change="toggleRolePermission(selectedRole.id, perm.id)"
                    />
                    <div class="perm-row-body">
                      <span class="perm-key">{{ permLabel(perm.key) }}</span>
                      <span class="perm-desc muted">{{ perm.description || permHint(perm.key) }}</span>
                    </div>
                    <span class="perm-access-type" :class="perm.key.endsWith('_write') || perm.key.endsWith('_generate') ? 'access-write' : 'access-read'">
                      {{ perm.key.endsWith('_write') || perm.key.endsWith('_generate') ? 'Write' : 'Read' }}
                    </span>
                  </label>

                  <!-- Ungrouped permissions fallback handled below -->
                </div>
              </div>

              <!-- Ungrouped / unknown permissions -->
              <div v-if="ungroupedPermissions(selectedRole.id).length > 0" class="perm-group">
                <div class="perm-group-header">
                  <div class="perm-group-icon perm-icon-slate">
                    <svg viewBox="0 0 20 20"><path d="M10 2a8 8 0 1 0 0 16A8 8 0 0 0 10 2zm-1 4h2v5H9zm0 5h2v2H9z" fill="currentColor"/></svg>
                  </div>
                  <div class="perm-group-meta">
                    <span class="perm-group-name">Other</span>
                  </div>
                </div>
                <div class="perm-rows">
                  <label
                    v-for="perm in ungroupedPermissions(selectedRole.id)"
                    :key="perm.id"
                    class="perm-row"
                    :class="{ 'perm-row-checked': roleDrafts[selectedRole.id].permission_ids.includes(perm.id) }"
                  >
                    <input
                      type="checkbox"
                      class="perm-checkbox"
                      :checked="roleDrafts[selectedRole.id].permission_ids.includes(perm.id)"
                      @change="toggleRolePermission(selectedRole.id, perm.id)"
                    />
                    <div class="perm-row-body">
                      <span class="perm-key">{{ permLabel(perm.key) }}</span>
                      <span class="perm-desc muted">{{ perm.description || permHint(perm.key) }}</span>
                    </div>
                  </label>
                </div>
              </div>
            </div>
          </div>

          <!-- Footer actions -->
          <div class="detail-footer">
            <button
              v-if="!isSystemRole(selectedRole.name)"
              type="button"
              class="btn btn-danger-outline"
              :disabled="isDeletingRole(selectedRole.id)"
              @click="deleteRole(selectedRole)"
            >
              {{ isDeletingRole(selectedRole.id) ? "Deleting…" : "Delete role" }}
            </button>
            <span v-else class="muted" style="font-size:var(--text-xs)">System roles cannot be deleted</span>
            <div style="flex:1" />
            <button
              type="submit"
              class="btn btn-primary"
              :disabled="isRoleSaving(selectedRole.id)"
            >
              {{ isRoleSaving(selectedRole.id) ? "Saving…" : "Save changes" }}
            </button>
          </div>
        </form>
      </section>

      <div v-else class="card empty-panel" style="align-self:start">
        Select a role from the list to view and edit its permissions.
      </div>
    </div>

  </section>

  <!-- ── Create role modal ── -->
  <AppModal v-model="showCreateModal" title="Create custom role" size="md" :persistent="true">
    <form id="create-role-form" class="form-grid" @submit.prevent="createRole">
      <label class="field field-span-2">
        <span class="field-label">Role name <span class="required">*</span></span>
        <input v-model.trim="createForm.name" required maxlength="100" placeholder="e.g. compliance_auditor" />
        <p class="field-hint muted">Use lowercase with underscores. Must be unique.</p>
      </label>
      <label class="field field-span-2">
        <span class="field-label">Description</span>
        <textarea v-model.trim="createForm.description" rows="2" maxlength="255" placeholder="What is this role for?" />
      </label>
      <div v-if="formError" class="field-span-2 feedback feedback-error" style="padding:0.6rem 0.9rem;border-radius:0.75rem">{{ formError }}</div>
    </form>
    <template #footer>
      <button class="btn btn-secondary" :disabled="isSubmitting" @click="showCreateModal = false">Cancel</button>
      <button class="btn btn-primary" type="submit" form="create-role-form" :disabled="isSubmitting || !createForm.name">
        {{ isSubmitting ? "Creating…" : "Create role" }}
      </button>
    </template>
  </AppModal>

</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from "vue";

import AppModal from "@/components/AppModal.vue";
import { adminService } from "@/services/admin-service";
import type { PermissionRead, RoleRead } from "@/types/admin";

/* ─── Types ─────────────────────────────────────────── */
interface RoleDraft {
  name: string;
  description: string;
  permission_ids: string[];
}

interface PermGroup {
  id: string;
  label: string;
  icon: string;
  colorClass: string;
  /** Permission key prefixes that belong to this group */
  keys: string[];
  permissions: PermissionRead[];
}

/* ─── Constants ─────────────────────────────────────── */
const SYSTEM_ROLE_NAMES = [
  "admin",
  "cybersecurity_engineer",
  "development_team",
  "product_owner",
  "lifecycle_manager",
  "legal_team",
  "product_management",
];

/* Human-readable role name map */
const ROLE_LABELS: Record<string, string> = {
  admin: "Administrator",
  cybersecurity_engineer: "Cybersecurity Engineer",
  development_team: "Development Team",
  product_owner: "Product Owner",
  lifecycle_manager: "Lifecycle Manager",
  legal_team: "Legal Team",
  product_management: "Product Management",
};

/* Permission display labels */
const PERM_LABELS: Record<string, string> = {
  product_read: "View products",
  product_write: "Manage products",
  release_read: "View releases",
  release_write: "Manage releases",
  release_lifecycle_write: "Control release lifecycle",
  remote_processing_element_read: "View remote processing elements",
  remote_processing_element_write: "Manage remote processing elements",
  scope_evaluation_read: "View scope evaluations",
  scope_evaluation_write: "Run scope evaluations",
  risk_assessment_read: "View risk assessments",
  risk_assessment_write: "Manage risk assessments",
  risk_item_read: "View risk items",
  risk_item_write: "Manage risk items",
  annex_requirement_read: "View Annex I requirements",
  annex_requirement_write: "Manage Annex I requirements",
  requirement_mapping_read: "View requirement mappings",
  requirement_mapping_write: "Manage requirement mappings",
  evidence_item_read: "View evidence items",
  evidence_item_write: "Manage evidence items",
  support_period_read: "View support periods",
  support_period_write: "Manage support periods",
  security_update_read: "View security updates & vulnerability data",
  security_update_write: "Publish security updates & vulnerability data",
  lifecycle_notification_read: "View lifecycle notifications",
  lifecycle_notification_write: "Manage lifecycle notifications",
  audit_read: "View audit log",
  authority_package_generate: "Generate authority packages",
  admin_manage_users: "Manage users, roles & LDAP",
  certification_record_read: "View certification records",
  certification_record_write: "Manage certification records",
  change_read: "View substantial changes",
  change_write: "Manage substantial changes",
};

/* Per-key contextual hints */
const PERM_HINTS: Record<string, string> = {
  product_read: "Browse product catalogue and view details",
  product_write: "Create, edit, and delete products",
  release_read: "View release versions and gate status",
  release_write: "Create and edit release records",
  release_lifecycle_write: "Approve, reject, and advance release gates",
  security_update_read: "Access security updates, CVD policies, advisories, and SBOMs",
  security_update_write: "Publish and edit security updates and vulnerability records",
  admin_manage_users: "Full user administration including LDAP sync",
  audit_read: "Read-only access to the audit trail",
  authority_package_generate: "Export CRA technical documentation packages",
};

/* ─── Grouped permission taxonomy ───────────────────── */
const GROUP_DEFS: Omit<PermGroup, "permissions">[] = [
  {
    id: "products",
    label: "Product Inventory",
    icon: `<svg viewBox="0 0 20 20"><path d="M4 5.5 10 3l6 2.5v9L10 17l-6-2.5zm6 .2L6.2 7.2 10 8.8l3.8-1.6zM5.5 8.4v5l3.8 1.6v-5zm9 0-3.8 1.6v5l3.8-1.6z" fill="currentColor"/></svg>`,
    colorClass: "perm-icon-blue",
    keys: ["product_read", "product_write"],
  },
  {
    id: "releases",
    label: "Release Management",
    icon: `<svg viewBox="0 0 20 20"><path d="M10 2a8 8 0 1 0 0 16A8 8 0 0 0 10 2zm-1 4h2v5.4l3.2 1.9-.9 1.4-3.7-2.2A1 1 0 0 1 9 11.5z" fill="currentColor"/></svg>`,
    colorClass: "perm-icon-indigo",
    keys: ["release_read", "release_write", "release_lifecycle_write"],
  },
  {
    id: "scope",
    label: "Scope & Remote Elements",
    icon: `<svg viewBox="0 0 20 20"><path d="M10 2a8 8 0 1 0 0 16A8 8 0 0 0 10 2zm0 2a6 6 0 1 1 0 12A6 6 0 0 1 10 4zm0 2a4 4 0 1 0 0 8 4 4 0 0 0 0-8zm0 2a2 2 0 1 1 0 4 2 2 0 0 1 0-4z" fill="currentColor"/></svg>`,
    colorClass: "perm-icon-cyan",
    keys: [
      "scope_evaluation_read", "scope_evaluation_write",
      "remote_processing_element_read", "remote_processing_element_write",
    ],
  },
  {
    id: "risk",
    label: "Risk Assessments",
    icon: `<svg viewBox="0 0 20 20"><path d="M10 2 2 16h16zm0 4.4 4.5 7.6h-9zM9 8h2v3H9zm0 4h2v2H9z" fill="currentColor"/></svg>`,
    colorClass: "perm-icon-orange",
    keys: ["risk_assessment_read", "risk_assessment_write", "risk_item_read", "risk_item_write"],
  },
  {
    id: "annex",
    label: "Annex I Requirements",
    icon: `<svg viewBox="0 0 20 20"><path d="M3 4h14v12H3zm2 2v2h10V6zm0 4v4h3v-4zm5 0v4h5v-4z" fill="currentColor"/></svg>`,
    colorClass: "perm-icon-violet",
    keys: [
      "annex_requirement_read", "annex_requirement_write",
      "requirement_mapping_read", "requirement_mapping_write",
      "evidence_item_read", "evidence_item_write",
    ],
  },
  {
    id: "vuln",
    label: "Vulnerability Handling",
    icon: `<svg viewBox="0 0 20 20"><path d="M10 2 4 5v4c0 4.1 2.4 7.8 6 9 3.6-1.2 6-4.9 6-9V5zm0 3.2a2.3 2.3 0 0 1 1.3 4.2v2.9H8.7V9.4A2.3 2.3 0 0 1 10 5.2z" fill="currentColor"/></svg>`,
    colorClass: "perm-icon-red",
    keys: ["security_update_read", "security_update_write"],
  },
  {
    id: "lifecycle",
    label: "Lifecycle & Support",
    icon: `<svg viewBox="0 0 20 20"><path d="M10 2a5 5 0 0 0-5 5v2.2c0 .5-.2.9-.5 1.3L3 12v1h14v-1l-1.5-1.5c-.3-.4-.5-.8-.5-1.3V7a5 5 0 0 0-5-5zm0 16a2.5 2.5 0 0 0 2.4-2H7.6A2.5 2.5 0 0 0 10 18z" fill="currentColor"/></svg>`,
    colorClass: "perm-icon-teal",
    keys: [
      "lifecycle_notification_read", "lifecycle_notification_write",
      "support_period_read", "support_period_write",
    ],
  },
  {
    id: "changes",
    label: "Substantial Changes",
    icon: `<svg viewBox="0 0 20 20"><path d="M3 5h14v2H3zm0 4h9v2H3zm0 4h6v2H3zm11-1 1.5-1.5L17 8l-4 4v3h3v-4z" fill="currentColor"/></svg>`,
    colorClass: "perm-icon-amber",
    keys: ["change_read", "change_write"],
  },
  {
    id: "certification",
    label: "Certification",
    icon: `<svg viewBox="0 0 20 20"><path d="M10 2a8 8 0 1 0 0 16A8 8 0 0 0 10 2zm3.5 5.5-4 4-2-2-1 1 3 3 5-5z" fill="currentColor"/></svg>`,
    colorClass: "perm-icon-emerald",
    keys: ["certification_record_read", "certification_record_write"],
  },
  {
    id: "governance",
    label: "Governance & Administration",
    icon: `<svg viewBox="0 0 20 20"><path d="M4 3h12v14H4zm2 2v10h8V5zm1 2h6v1.8H7zm0 3h6v1.8H7z" fill="currentColor"/></svg>`,
    colorClass: "perm-icon-slate",
    keys: ["audit_read", "authority_package_generate", "admin_manage_users"],
  },
];

/* ─── State ─────────────────────────────────────────── */
const roles       = ref<RoleRead[]>([]);
const permissions = ref<PermissionRead[]>([]);
const roleDrafts  = reactive<Record<string, RoleDraft>>({});

const isLoading     = ref(false);
const isSubmitting  = ref(false);
const errorMessage  = ref("");
const successMessage = ref("");
const formError     = ref("");
const showCreateModal = ref(false);
const selectedRoleId  = ref<string>("");

const roleSavingIds  = ref<string[]>([]);
const deletingRoleIds = ref<string[]>([]);

const createForm = reactive({ name: "", description: "" });

/* ─── Computed ──────────────────────────────────────── */
const sortedRoles = computed(() => {
  return [...roles.value].sort((a, b) => {
    const aSystem = isSystemRole(a.name) ? 0 : 1;
    const bSystem = isSystemRole(b.name) ? 0 : 1;
    if (aSystem !== bSystem) return aSystem - bSystem;
    return a.name.localeCompare(b.name);
  });
});

const systemRolesCount = computed(() => roles.value.filter((r) => isSystemRole(r.name)).length);

const selectedRole = computed(() =>
  roles.value.find((r) => r.id === selectedRoleId.value) ?? null,
);

/* Populate group.permissions from the live permissions list */
const permissionGroups = computed<PermGroup[]>(() => {
  return GROUP_DEFS.map((def) => ({
    ...def,
    permissions: def.keys
      .map((key) => permissions.value.find((p) => p.key === key))
      .filter((p): p is PermissionRead => p !== undefined),
  })).filter((g) => g.permissions.length > 0);
});

const groupedKeys = computed(() => new Set(GROUP_DEFS.flatMap((g) => g.keys)));

/* ─── Helpers ───────────────────────────────────────── */
function isSystemRole(name: string): boolean {
  return SYSTEM_ROLE_NAMES.includes(name);
}

function formatRoleName(name: string): string {
  return ROLE_LABELS[name] ?? name.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
}

function permLabel(key: string): string {
  return PERM_LABELS[key] ?? key.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
}

function permHint(key: string): string {
  return PERM_HINTS[key] ?? "";
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

function groupSelectedCount(roleId: string, group: PermGroup): number {
  const draft = roleDrafts[roleId];
  if (!draft) return 0;
  return group.permissions.filter((p) => draft.permission_ids.includes(p.id)).length;
}

function ungroupedPermissions(roleId: string): PermissionRead[] {
  void roleId; // roleId not needed for filtering but keeps the API consistent
  return permissions.value.filter((p) => !groupedKeys.value.has(p.key));
}

function isRoleSaving(id: string): boolean   { return roleSavingIds.value.includes(id); }
function isDeletingRole(id: string): boolean { return deletingRoleIds.value.includes(id); }

function setSuccess(msg: string): void {
  successMessage.value = msg;
  setTimeout(() => { successMessage.value = ""; }, 3500);
}

/* ─── Actions ───────────────────────────────────────── */
function selectRole(id: string): void { selectedRoleId.value = id; }

function toggleRolePermission(roleId: string, permId: string): void {
  const draft = roleDrafts[roleId];
  if (!draft) return;
  if (draft.permission_ids.includes(permId)) {
    draft.permission_ids = draft.permission_ids.filter((id) => id !== permId);
  } else {
    draft.permission_ids = [...draft.permission_ids, permId];
  }
}

function selectAll(roleId: string): void {
  const draft = roleDrafts[roleId];
  if (!draft) return;
  draft.permission_ids = permissions.value.map((p) => p.id);
}

function clearAll(roleId: string): void {
  const draft = roleDrafts[roleId];
  if (!draft) return;
  draft.permission_ids = [];
}

function toggleGroup(roleId: string, group: PermGroup): void {
  const draft = roleDrafts[roleId];
  if (!draft) return;
  const allSelected = group.permissions.every((p) => draft.permission_ids.includes(p.id));
  if (allSelected) {
    draft.permission_ids = draft.permission_ids.filter((id) => !group.permissions.some((p) => p.id === id));
  } else {
    const toAdd = group.permissions.map((p) => p.id).filter((id) => !draft.permission_ids.includes(id));
    draft.permission_ids = [...draft.permission_ids, ...toAdd];
  }
}

function syncDrafts(): void {
  const next: Record<string, RoleDraft> = {};
  for (const role of roles.value) {
    next[role.id] = {
      name: role.name,
      description: role.description ?? "",
      permission_ids: permissions.value
        .filter((p) => role.permissions.includes(p.key))
        .map((p) => p.id),
    };
  }
  for (const [k, v] of Object.entries(next)) roleDrafts[k] = v;
  for (const k of Object.keys(roleDrafts)) if (!next[k]) delete roleDrafts[k];
  if (!roles.value.some((r) => r.id === selectedRoleId.value)) {
    selectedRoleId.value = roles.value[0]?.id ?? "";
  }
}

async function loadData(): Promise<void> {
  isLoading.value = true;
  errorMessage.value = "";
  try {
    const [rolesData, permsData] = await Promise.all([
      adminService.listRoles(),
      adminService.listPermissions(),
    ]);
    roles.value = rolesData;
    permissions.value = permsData;
    syncDrafts();
  } catch (err) {
    errorMessage.value = err instanceof Error ? err.message : "Failed to load roles.";
  } finally {
    isLoading.value = false;
  }
}

async function createRole(): Promise<void> {
  isSubmitting.value = true;
  formError.value = "";
  try {
    const created = await adminService.createRole({
      name: createForm.name,
      description: createForm.description || null,
    });
    createForm.name = "";
    createForm.description = "";
    showCreateModal.value = false;
    await loadData();
    selectedRoleId.value = created.id;
    setSuccess(`Role "${formatRoleName(created.name)}" created.`);
  } catch (err) {
    formError.value = err instanceof Error ? err.message : "Failed to create role.";
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
    await adminService.setRolePermissions(role.id, { permission_ids: draft.permission_ids });
    await loadData();
    setSuccess(`Role "${formatRoleName(draft.name)}" saved.`);
  } catch (err) {
    errorMessage.value = err instanceof Error ? err.message : "Failed to save role.";
  } finally {
    roleSavingIds.value = roleSavingIds.value.filter((id) => id !== role.id);
  }
}

async function deleteRole(role: RoleRead): Promise<void> {
  if (isSystemRole(role.name)) return;
  if (!window.confirm(`Delete role "${formatRoleName(role.name)}"? This action cannot be undone.`)) return;
  deletingRoleIds.value = [...deletingRoleIds.value, role.id];
  try {
    await adminService.deleteRole(role.id);
    await loadData();
    setSuccess("Role deleted.");
  } catch (err) {
    errorMessage.value = err instanceof Error ? err.message : "Failed to delete role.";
  } finally {
    deletingRoleIds.value = deletingRoleIds.value.filter((id) => id !== role.id);
  }
}

onMounted(() => { void loadData(); });
</script>

<style scoped>
/* ── Layout ────────────────────────────────────────── */
.page { display: grid; gap: 1rem; }

.page-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 1rem;
  flex-wrap: wrap;
}
.page-title { margin: 0; }
.page-subtitle { margin-top: 0.35rem; }
.page-actions { display: flex; gap: 0.75rem; }

.workspace {
  display: grid;
  grid-template-columns: 280px minmax(0, 1fr);
  gap: 1rem;
  align-items: start;
}

/* ── Feedback ──────────────────────────────────────── */
.feedback { padding: 0.85rem 1.1rem; border-radius: 1rem; font-size: var(--text-sm); border: 1px solid transparent; }
.feedback-error   { background: var(--color-danger-bg);  border-color: var(--color-danger-border);  color: var(--color-danger-text); }
.feedback-success { background: var(--color-success-bg); border-color: var(--color-success-border); color: var(--color-success-text); }

.empty-panel { padding: 2.5rem; text-align: center; color: var(--color-text-muted); display: grid; gap: 0.5rem; }

/* ── Buttons ───────────────────────────────────────── */
.btn {
  display: inline-flex; align-items: center; gap: 0.4rem;
  border: 1px solid transparent; border-radius: 0.85rem;
  padding: 0.6rem 1.1rem; font: inherit; font-size: var(--text-sm);
  font-weight: 600; cursor: pointer; transition: opacity 0.12s, transform 0.12s; white-space: nowrap;
}
.btn:disabled { opacity: 0.5; cursor: not-allowed; }
.btn-primary {
  background: linear-gradient(135deg, rgba(175,214,46,.95), rgba(28,107,39,.95));
  color: #fff; box-shadow: 0 6px 16px rgba(28,107,39,.22);
}
.btn-primary:not(:disabled):hover { transform: translateY(-1px); }
.btn-secondary { background: transparent; border-color: var(--color-border); color: inherit; }
.btn-secondary:not(:disabled):hover { background: var(--color-surface-elevated); }
.btn-danger-outline { background: transparent; border-color: var(--color-danger-border); color: var(--color-danger-text); }
.btn-danger-outline:not(:disabled):hover { background: var(--color-danger-bg); }
.btn-link { background: none; border: none; cursor: pointer; font: inherit; font-size: var(--text-xs); color: var(--color-primary-2); padding: 0; }
.btn-link:hover { text-decoration: underline; }
.dot-sep { color: var(--color-text-muted); font-size: var(--text-xs); }

/* ── Roles aside ───────────────────────────────────── */
.roles-aside {
  display: flex; flex-direction: column; gap: 1rem;
  position: sticky; top: 1rem; max-height: calc(100vh - 6rem); overflow: hidden;
}
.aside-header { display: flex; align-items: center; gap: 0.5rem; padding-bottom: 0.5rem; border-bottom: 1px solid var(--color-divider); }
.aside-title { font-weight: 700; font-size: var(--text-sm); }
.count-badge { background: var(--color-surface-elevated); border: 1px solid var(--color-border); border-radius: 999px; padding: 0.1rem 0.55rem; font-size: var(--text-xs); font-weight: 700; color: var(--color-text-muted); }

.role-list { display: flex; flex-direction: column; gap: 0.35rem; overflow-y: auto; flex: 1; min-height: 0; }

.role-item {
  display: flex; align-items: center; gap: 0.6rem;
  padding: 0.6rem 0.75rem; border-radius: 0.75rem;
  border: 1px solid transparent; background: transparent;
  cursor: pointer; text-align: left; transition: background 0.12s, border-color 0.12s;
  font: inherit; width: 100%;
}
.role-item:hover { background: var(--color-surface-elevated); border-color: var(--color-border); }
.role-item-active { background: rgba(112,185,23,.1); border-color: rgba(173,214,84,.35); }

.role-item-icon {
  width: 32px; height: 32px; border-radius: 8px;
  display: grid; place-items: center; flex-shrink: 0;
}
.role-item-icon svg { width: 16px; height: 16px; }

.role-item-body { flex: 1; min-width: 0; display: grid; gap: 0.2rem; }
.role-item-name { font-size: var(--text-sm); font-weight: 600; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.role-item-meta { display: flex; align-items: center; gap: 0.4rem; }
.perm-count { font-size: var(--text-xs); color: var(--color-text-muted); }
.role-chevron { color: var(--color-text-muted); opacity: 0.4; font-size: 1rem; flex-shrink: 0; }
.role-item-active .role-chevron { opacity: 1; color: var(--color-primary-2); }

/* Role type badges */
.role-type-badge { border-radius: 999px; padding: 0.15rem 0.55rem; font-size: 0.68rem; font-weight: 700; letter-spacing: 0.03em; white-space: nowrap; }
.badge-system { background: rgba(251,191,36,.15); color: #d97706; border: 1px solid rgba(251,191,36,.3); }
.badge-custom { background: rgba(112,185,23,.12); color: var(--color-primary-2); border: 1px solid rgba(112,185,23,.25); }

/* Aside stats */
.aside-stats { display: flex; align-items: center; justify-content: space-around; padding: 0.75rem 0.5rem 0; border-top: 1px solid var(--color-divider); flex-shrink: 0; }
.stat-item { display: flex; flex-direction: column; align-items: center; gap: 0.1rem; }
.stat-num { font-size: 1.1rem; font-weight: 800; }
.stat-lbl { font-size: 0.65rem; color: var(--color-text-muted); text-transform: uppercase; letter-spacing: 0.06em; }
.stat-sep { width: 1px; height: 28px; background: var(--color-divider); }

/* ── Detail panel ──────────────────────────────────── */
.detail-panel { display: flex; flex-direction: column; gap: 1.25rem; }

.detail-header { display: flex; align-items: center; justify-content: space-between; gap: 1rem; flex-wrap: wrap; padding-bottom: 1rem; border-bottom: 1px solid var(--color-divider); }
.detail-header-left { display: flex; align-items: center; gap: 0.85rem; }
.detail-role-icon { width: 44px; height: 44px; border-radius: 12px; display: grid; place-items: center; flex-shrink: 0; }
.detail-role-icon svg { width: 22px; height: 22px; }
.detail-role-name { font-size: var(--text-lg); font-weight: 700; }
.detail-role-desc { font-size: var(--text-sm); margin-top: 0.15rem; }
.detail-header-right { display: flex; align-items: center; gap: 0.6rem; flex-wrap: wrap; }
.perm-count-pill { background: var(--color-surface-elevated); border: 1px solid var(--color-border); border-radius: 999px; padding: 0.2rem 0.75rem; font-size: var(--text-xs); font-weight: 600; color: var(--color-text-muted); }

.meta-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 0.75rem; }
.field { display: grid; gap: 0.4rem; }
.field-label { font-size: var(--text-sm); font-weight: 600; color: var(--color-text-muted); }
.field-hint { font-size: var(--text-xs); margin-top: 0.2rem; }
.required { color: var(--color-danger-text); }
.field-span-2 { grid-column: span 2; }
input, select, textarea {
  width: 100%; padding: 0.6rem 0.85rem; border-radius: 0.75rem;
  border: 1px solid var(--color-border); background: var(--color-surface-soft);
  color: inherit; font: inherit; font-size: var(--text-sm);
}
input:focus, select:focus, textarea:focus {
  outline: none; border-color: rgba(175,214,46,.45);
  box-shadow: 0 0 0 3px rgba(112,185,23,.12);
}
input:disabled { opacity: 0.6; cursor: not-allowed; }

/* ── Permission section ─────────────────────────────── */
.perm-section { display: flex; flex-direction: column; gap: 1rem; }
.perm-section-header { display: flex; align-items: center; justify-content: space-between; gap: 0.5rem; }
.perm-section-title { font-size: var(--text-sm); font-weight: 700; margin: 0; text-transform: uppercase; letter-spacing: 0.06em; color: var(--color-text-muted); }
.perm-section-actions { display: flex; align-items: center; gap: 0.4rem; }

.perm-groups { display: flex; flex-direction: column; gap: 0.75rem; }

.perm-group { border: 1px solid var(--color-border); border-radius: 1rem; overflow: hidden; }
.perm-group-header {
  display: flex; align-items: center; gap: 0.75rem;
  padding: 0.7rem 1rem; background: var(--color-surface-elevated);
  border-bottom: 1px solid var(--color-divider);
}
.perm-group-icon { width: 28px; height: 28px; border-radius: 7px; display: grid; place-items: center; flex-shrink: 0; }
.perm-group-icon svg { width: 14px; height: 14px; }
.perm-group-meta { flex: 1; display: flex; align-items: center; gap: 0.5rem; }
.perm-group-name { font-size: var(--text-sm); font-weight: 700; }
.perm-group-count { font-size: var(--text-xs); }

.group-toggle {
  width: 22px; height: 22px; border-radius: 6px; border: 1px solid var(--color-border);
  background: var(--color-surface-soft); display: grid; place-items: center;
  cursor: pointer; color: var(--color-text-muted); flex-shrink: 0;
  transition: background 0.12s, border-color 0.12s, color 0.12s;
}
.group-toggle:hover { border-color: rgba(112,185,23,.4); color: var(--color-primary-2); }
.group-toggle-on { background: rgba(112,185,23,.15); border-color: rgba(112,185,23,.4); color: var(--color-primary-2); }

.perm-rows { display: flex; flex-direction: column; }

.perm-row {
  display: flex; align-items: center; gap: 0.85rem;
  padding: 0.65rem 1rem; cursor: pointer;
  border-bottom: 1px solid var(--color-divider);
  transition: background 0.1s;
}
.perm-row:last-child { border-bottom: none; }
.perm-row:hover { background: var(--color-surface-elevated); }
.perm-row-checked { background: rgba(112,185,23,.05); }

.perm-checkbox { width: 16px; height: 16px; flex-shrink: 0; accent-color: var(--color-primary-2); cursor: pointer; }
.perm-row-body { flex: 1; display: grid; gap: 0.1rem; min-width: 0; }
.perm-key { font-size: var(--text-sm); font-weight: 600; }
.perm-desc { font-size: var(--text-xs); }

.perm-access-type { font-size: 0.65rem; font-weight: 700; letter-spacing: 0.05em; border-radius: 999px; padding: 0.1rem 0.5rem; flex-shrink: 0; }
.access-read  { background: rgba(96,165,250,.12); color: #60a5fa; border: 1px solid rgba(96,165,250,.2); }
.access-write { background: rgba(251,146,60,.12); color: #fb923c; border: 1px solid rgba(251,146,60,.2); }

/* ── Detail footer ─────────────────────────────────── */
.detail-footer { display: flex; align-items: center; gap: 0.75rem; padding-top: 1rem; border-top: 1px solid var(--color-divider); flex-wrap: wrap; }

/* ── Role icon color themes ─────────────────────────── */
.icon-red    { background: rgba(239,68,68,.15);  color: #ef4444; }
.icon-orange { background: rgba(249,115,22,.15); color: #f97316; }
.icon-blue   { background: rgba(59,130,246,.15); color: #3b82f6; }
.icon-indigo { background: rgba(99,102,241,.15); color: #6366f1; }
.icon-teal   { background: rgba(20,184,166,.15); color: #14b8a6; }
.icon-violet { background: rgba(139,92,246,.15); color: #8b5cf6; }
.icon-emerald{ background: rgba(16,185,129,.15); color: #10b981; }
.icon-slate  { background: rgba(100,116,139,.15);color: #64748b; }
.icon-amber  { background: rgba(245,158,11,.15); color: #f59e0b; }

/* Permission group icon themes */
.perm-icon-blue   { background: rgba(59,130,246,.15);  color: #3b82f6; }
.perm-icon-indigo { background: rgba(99,102,241,.15);  color: #6366f1; }
.perm-icon-cyan   { background: rgba(6,182,212,.15);   color: #06b6d4; }
.perm-icon-orange { background: rgba(249,115,22,.15);  color: #f97316; }
.perm-icon-violet { background: rgba(139,92,246,.15);  color: #8b5cf6; }
.perm-icon-red    { background: rgba(239,68,68,.15);   color: #ef4444; }
.perm-icon-teal   { background: rgba(20,184,166,.15);  color: #14b8a6; }
.perm-icon-amber  { background: rgba(245,158,11,.15);  color: #f59e0b; }
.perm-icon-emerald{ background: rgba(16,185,129,.15);  color: #10b981; }
.perm-icon-slate  { background: rgba(100,116,139,.15); color: #64748b; }

/* ── Form modal ────────────────────────────────────── */
.form-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 0.85rem; }

/* ── Responsive ────────────────────────────────────── */
@media (max-width: 1024px) {
  .workspace { grid-template-columns: 1fr; }
  .roles-aside { position: static; max-height: none; overflow: visible; }
  .role-list { max-height: 260px; overflow-y: auto; }
}
@media (max-width: 640px) {
  .meta-grid { grid-template-columns: 1fr; }
  .form-grid { grid-template-columns: 1fr; }
  .field-span-2 { grid-column: span 1; }
}
</style>

<style>
/* Light-mode overrides for elements that need global scope */
:root[data-theme="light"] .badge-system { color: #92400e; background: rgba(245,158,11,.1); border-color: rgba(245,158,11,.25); }
:root[data-theme="light"] .access-read  { color: #2563eb; background: rgba(37,99,235,.08); border-color: rgba(37,99,235,.2); }
:root[data-theme="light"] .access-write { color: #c2410c; background: rgba(194,65,12,.08); border-color: rgba(194,65,12,.2); }
</style>
