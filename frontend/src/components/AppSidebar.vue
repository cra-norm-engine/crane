<template>
  <aside class="sidebar">

    <!-- Brand -->
    <div class="brand">
      <div class="brand-mark" aria-hidden="true">SA</div>
      <div>
        <div class="brand-title">SICH'AMAN</div>
        <div class="brand-sub">CRA Compliance Platform</div>
      </div>
    </div>

    <nav class="sidebar-nav" aria-label="Main navigation">

      <!-- Overview -->
      <div class="nav-group">
        <RouterLink :to="{ name: 'dashboard' }" class="nav-link" active-class="nav-link-active" exact-active-class="nav-link-active">
          <span class="nav-icon">
            <svg viewBox="0 0 20 20" aria-hidden="true"><path d="M3 3h6v6H3zm8 0h6v4h-6zM3 11h4v6H3zm6 2h8v4H9z" fill="currentColor"/></svg>
          </span>
          <span>Dashboard</span>
        </RouterLink>
      </div>

      <div class="nav-divider" />

      <!-- Main workspace -->
      <div class="nav-group">
        <p class="nav-group-label">Menu</p>

        <RouterLink :to="{ name: 'products' }" class="nav-link" active-class="nav-link-active">
          <span class="nav-icon">
            <svg viewBox="0 0 20 20" aria-hidden="true"><path d="M4 5.5 10 3l6 2.5v9L10 17l-6-2.5zm6 .2L6.2 7.2 10 8.8l3.8-1.6zM5.5 8.4v5l3.8 1.6v-5zm9 0-3.8 1.6v5l3.8-1.6z" fill="currentColor"/></svg>
          </span>
          <span>Product inventory</span>
        </RouterLink>

        <RouterLink
          v-if="canViewRiskAssessments"
          :to="{ name: 'risk-assessments' }"
          class="nav-link"
          active-class="nav-link-active"
        >
          <span class="nav-icon">
            <svg viewBox="0 0 20 20" aria-hidden="true"><path d="M10 2 2 16h16zm0 4.4 4.5 7.6h-9zM9 8h2v3H9zm0 4h2v2H9z" fill="currentColor"/></svg>
          </span>
          <span>Risk assessments</span>
        </RouterLink>

        <RouterLink
          v-if="canViewAnnexMatrix"
          :to="{ name: 'annex-matrix' }"
          class="nav-link"
          active-class="nav-link-active"
        >
          <span class="nav-icon">
            <svg viewBox="0 0 20 20" aria-hidden="true"><path d="M3 4h14v12H3zm2 2v2h10V6zm0 4v4h3v-4zm5 0v4h5v-4z" fill="currentColor"/></svg>
          </span>
          <span>Annex I matrix</span>
        </RouterLink>

        <RouterLink
          v-if="canViewSecurityUpdates"
          :to="{ name: 'security-updates' }"
          class="nav-link"
          active-class="nav-link-active"
        >
          <span class="nav-icon">
            <svg viewBox="0 0 20 20" aria-hidden="true"><path d="M10 2 4 5v4c0 4.1 2.4 7.8 6 9 3.6-1.2 6-4.9 6-9V5zm0 3.2a2.3 2.3 0 0 1 1.3 4.2v2.9H8.7V9.4A2.3 2.3 0 0 1 10 5.2z" fill="currentColor"/></svg>
          </span>
          <span>Security updates</span>
        </RouterLink>

        <RouterLink
          v-if="canViewLifecycleNotifications"
          :to="{ name: 'lifecycle-notifications' }"
          class="nav-link"
          active-class="nav-link-active"
        >
          <span class="nav-icon">
            <svg viewBox="0 0 20 20" aria-hidden="true"><path d="M10 2a5 5 0 0 0-5 5v2.2c0 .5-.2.9-.5 1.3L3 12v1h14v-1l-1.5-1.5c-.3-.4-.5-.8-.5-1.3V7a5 5 0 0 0-5-5zm0 16a2.5 2.5 0 0 0 2.4-2H7.6A2.5 2.5 0 0 0 10 18z" fill="currentColor"/></svg>
          </span>
          <span>Lifecycle alerts</span>
        </RouterLink>
      </div>

      <div class="nav-divider" />

      <!-- Governance -->
      <div class="nav-group">
        <p class="nav-group-label">Governance</p>

        <RouterLink
          v-if="canViewAudit"
          :to="{ name: 'audit-history' }"
          class="nav-link"
          active-class="nav-link-active"
        >
          <span class="nav-icon">
            <svg viewBox="0 0 20 20" aria-hidden="true"><path d="M4 3h12v14H4zm2 2v10h8V5zm1 2h6v1.8H7zm0 3h6v1.8H7z" fill="currentColor"/></svg>
          </span>
          <span>Audit history</span>
        </RouterLink>
      </div>

      <!-- Administration -->
      <template v-if="canManageAdmin">
        <div class="nav-divider" />

        <div class="nav-group">
          <p class="nav-group-label">Administration</p>

          <RouterLink :to="{ name: 'admin-users' }" class="nav-link" active-class="nav-link-active">
            <span class="nav-icon">
              <svg viewBox="0 0 20 20" aria-hidden="true"><path d="M10 10a3.5 3.5 0 1 0-3.5-3.5A3.5 3.5 0 0 0 10 10zm0 2c-3.1 0-5.8 1.6-6.8 4h13.6c-1-2.4-3.7-4-6.8-4z" fill="currentColor"/></svg>
            </span>
            <span>Users</span>
          </RouterLink>

          <RouterLink :to="{ name: 'admin-roles' }" class="nav-link" active-class="nav-link-active">
            <span class="nav-icon">
              <svg viewBox="0 0 20 20" aria-hidden="true"><path d="M10 2 4 5v4c0 4.1 2.4 7.8 6 9 3.6-1.2 6-4.9 6-9V5zm0 3.2a2 2 0 0 1 2 2 2 2 0 0 1-.8 1.6l1.1 3.2H7.7l1.1-3.2A2 2 0 0 1 8 7.2a2 2 0 0 1 2-2z" fill="currentColor"/></svg>
            </span>
            <span>Roles &amp; access</span>
          </RouterLink>
        </div>
      </template>

    </nav>

    <!-- User footer -->
    <div class="sidebar-footer">
      <div class="user-row">
        <div class="user-avatar" aria-hidden="true">{{ userInitials }}</div>
        <div class="user-info">
          <div class="user-name">{{ displayName }}</div>
          <span class="user-role-badge">{{ primaryRoleLabel }}</span>
        </div>
      </div>

      <button class="nav-link nav-link-button" type="button" @click="logout">
        <span class="nav-icon">
          <svg viewBox="0 0 20 20" aria-hidden="true"><path d="M8 3H4v14h4v-2H6V5h2zm4.6 3.4L11.2 7.8 13.4 10H7v2h6.4l-2.2 2.2 1.4 1.4L17.2 11z" fill="currentColor"/></svg>
        </span>
        <span>Log out</span>
      </button>
    </div>

  </aside>
</template>

<script setup lang="ts">
import { computed } from "vue";
import { RouterLink, useRouter } from "vue-router";

import { useAuthStore } from "@/stores/auth";

const router = useRouter();
const authStore = useAuthStore();

const canViewSecurityUpdates = computed(() => authStore.hasPermission("security_update_read"));
const canViewLifecycleNotifications = computed(() => authStore.hasPermission("lifecycle_notification_read"));
const canViewRiskAssessments = computed(() => authStore.hasPermission("risk_assessment_read"));
const canViewAnnexMatrix = computed(
  () => authStore.hasPermission("annex_requirement_read") || authStore.hasPermission("requirement_mapping_read"),
);
const canManageAdmin = computed(() => authStore.hasPermission("admin_manage_users"));
const canViewAudit = computed(() => authStore.hasPermission("audit_read"));

const primaryRoleLabel = computed(() => {
  const role = authStore.roles?.[0];
  switch (role) {
    case "admin": return "Admin";
    case "product_owner": return "Product Owner";
    case "cybersecurity_engineer": return "Cybersecurity Engineer";
    case "legal_team": return "Legal Team";
    case "development_team": return "Development Team";
    case "product_management": return "Product Management";
    case "lifecycle_manager": return "Lifecycle Manager";
    default: return "User";
  }
});

const displayName = computed(() => authStore.userFullName || authStore.userEmail || "User");

const userInitials = computed(() => {
  const name = authStore.userFullName || authStore.userEmail || "";
  return name
    .split(/[\s@]/)
    .filter(Boolean)
    .map((part: string) => part[0])
    .join("")
    .toUpperCase()
    .slice(0, 2);
});

function logout(): void {
  authStore.logout();
  router.push({ name: "login" });
}
</script>

<style scoped>
/* ── Shell ───────────────────────────────────────── */
.sidebar {
  width: 220px;
  padding: 1rem 0.75rem 1rem;
  border-right: 1px solid var(--color-border);
  background: var(--color-sidebar-bg);
  backdrop-filter: blur(14px);
  display: flex;
  flex-direction: column;
  gap: 0;
  position: sticky;
  top: 0;
  height: 100vh;
  overflow-y: auto;
  scrollbar-width: none;
  box-sizing: border-box;
}

.sidebar::-webkit-scrollbar {
  display: none;
}

/* ── Brand ───────────────────────────────────────── */
.brand {
  display: flex;
  gap: 0.7rem;
  align-items: center;
  padding: 0.25rem 0.35rem 1rem;
  flex-shrink: 0;
}

.brand-mark {
  width: 38px;
  height: 38px;
  border-radius: 12px;
  display: grid;
  place-items: center;
  background: linear-gradient(145deg, var(--color-card-start), var(--color-card-end));
  border: 1px solid var(--color-border-strong);
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.2), 0 0 0 1px rgba(175, 214, 46, 0.08);
  font-weight: 900;
  font-size: 0.82rem;
  letter-spacing: 0.04em;
  color: var(--color-primary-2);
  flex-shrink: 0;
}

.brand-title {
  font-size: 0.97rem;
  font-weight: 800;
  letter-spacing: 0.05em;
  line-height: 1.2;
}

.brand-sub {
  font-size: 0.72rem;
  color: var(--color-text-muted);
  margin-top: 0.1rem;
  line-height: 1.3;
}

/* ── Nav container ───────────────────────────────── */
.sidebar-nav {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 0;
  min-height: 0;
}

/* ── Nav groups ──────────────────────────────────── */
.nav-group {
  display: flex;
  flex-direction: column;
  gap: 0.15rem;
  padding: 0.35rem 0;
}

.nav-group-label {
  margin: 0 0 0.2rem;
  padding: 0 0.5rem;
  font-size: 0.68rem;
  font-weight: 700;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: rgba(220, 233, 214, 0.35);
}

.nav-divider {
  height: 1px;
  background: var(--color-border);
  opacity: 0.5;
  margin: 0.1rem 0.25rem;
}

/* ── Nav links ───────────────────────────────────── */
.nav-link {
  display: flex;
  align-items: center;
  gap: 0.65rem;
  padding: 0.6rem 0.75rem;
  border-radius: 10px;
  border: 1px solid transparent;
  font-size: 0.875rem;
  font-weight: 500;
  color: var(--color-text-muted);
  text-decoration: none;
  transition: background-color 0.13s, border-color 0.13s, color 0.13s;
  white-space: nowrap;
  overflow: hidden;
}

.nav-link-button {
  width: 100%;
  background: transparent;
  text-align: left;
  cursor: pointer;
  font-family: inherit;
}

.nav-icon {
  width: 18px;
  height: 18px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  opacity: 0.7;
  transition: opacity 0.13s;
}

.nav-icon svg {
  width: 18px;
  height: 18px;
  display: block;
}

.nav-link:hover {
  background: rgba(255, 255, 255, 0.04);
  color: var(--color-text);
  border-color: rgba(233, 238, 252, 0.06);
}

.nav-link:hover .nav-icon {
  opacity: 1;
}

.nav-link-active {
  background: linear-gradient(135deg, rgba(112, 185, 23, 0.13), rgba(28, 107, 39, 0.16));
  border-color: rgba(173, 214, 84, 0.22);
  color: var(--color-text);
  font-weight: 600;
  box-shadow: inset 3px 0 0 var(--color-primary-2);
}

.nav-link-active .nav-icon {
  opacity: 1;
  color: var(--color-primary-2);
}

/* ── Footer ──────────────────────────────────────── */
.sidebar-footer {
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  gap: 0.4rem;
  padding-top: 0.75rem;
  border-top: 1px solid rgba(233, 238, 252, 0.08);
  margin-top: auto;
}

.user-row {
  display: flex;
  align-items: center;
  gap: 0.65rem;
  padding: 0.4rem 0.35rem;
}

.user-avatar {
  width: 32px;
  height: 32px;
  border-radius: 9px;
  background: linear-gradient(135deg, rgba(112, 185, 23, 0.22), rgba(28, 107, 39, 0.28));
  border: 1px solid rgba(173, 214, 84, 0.2);
  display: grid;
  place-items: center;
  font-size: 0.7rem;
  font-weight: 800;
  color: var(--color-primary-2);
  letter-spacing: 0.04em;
  flex-shrink: 0;
}

.user-info {
  display: flex;
  flex-direction: column;
  gap: 0.1rem;
  min-width: 0;
}

.user-name {
  font-size: 0.82rem;
  font-weight: 700;
  color: var(--color-text);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.user-role-badge {
  font-size: 0.68rem;
  font-weight: 500;
  color: var(--color-text-muted);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

@media (max-width: 960px) {
  .sidebar {
    display: none;
  }
}
</style>

<style>
:root[data-theme="light"] .nav-group-label {
  color: rgba(20, 33, 15, 0.42);
}
:root[data-theme="light"] .nav-divider {
  background: rgba(20, 33, 15, 0.1);
}
:root[data-theme="light"] .nav-link:hover {
  background: rgba(28, 107, 39, 0.06);
  border-color: rgba(28, 107, 39, 0.1);
}
:root[data-theme="light"] .sidebar-footer {
  border-top-color: rgba(28, 107, 39, 0.12);
}
</style>
