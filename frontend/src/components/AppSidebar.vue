<template>
  <aside class="sidebar">
    <div class="brand">
      <div class="brand-mark" aria-hidden="true">ALI</div>
      <div>
        <div class="brand-title">Audit-Linked Integrity</div>
        <div class="brand-sub">A CRA Compliance Tool</div>
      </div>
    </div>

    <div class="separator"></div>

    <nav class="nav">
      <RouterLink :to="{ name: 'dashboard' }" class="nav-link" active-class="nav-link-active">
        Dashboard
      </RouterLink>

      <RouterLink :to="{ name: 'products' }" class="nav-link" active-class="nav-link-active">
        Product inventory
      </RouterLink>

      <RouterLink
        v-if="canViewRiskAssessments"
        :to="{ name: 'risk-assessments' }"
        class="nav-link"
        active-class="nav-link-active"
      >
        Risk assessments
      </RouterLink>

      <RouterLink
        v-if="canViewAnnexMatrix"
        :to="{ name: 'annex-matrix' }"
        class="nav-link"
        active-class="nav-link-active"
      >
        Annex I matrix
      </RouterLink>

      <RouterLink
        v-if="canManageAdmin"
        :to="{ name: 'admin-users' }"
        class="nav-link"
        active-class="nav-link-active"
      >
        Users
      </RouterLink>

      <RouterLink
        v-if="canManageAdmin"
        :to="{ name: 'admin-roles' }"
        class="nav-link"
        active-class="nav-link-active"
      >
        Roles & access
      </RouterLink>
    </nav>

    <div class="separator"></div>

    <div class="sidebar-footer">
      <span class="badge">
        Role:
        <strong class="badge-strong">{{ primaryRoleLabel }}</strong>
      </span>
    </div>
  </aside>
</template>

<script setup lang="ts">
import { computed } from "vue";
import { RouterLink } from "vue-router";

import { useAuthStore } from "@/stores/auth";

const authStore = useAuthStore();

const canViewRiskAssessments = computed(() =>
  authStore.hasPermission("risk_assessment_read"),
);

const canViewAnnexMatrix = computed(
  () =>
    authStore.hasPermission("annex_requirement_read") ||
    authStore.hasPermission("requirement_mapping_read"),
);

const canManageAdmin = computed(() =>
  authStore.hasPermission("admin_manage_users"),
);

const primaryRoleLabel = computed(() => {
  const role = authStore.roles?.[0];

  switch (role) {
    case "admin":
      return "Admin";
    case "product_owner":
      return "Product Owner";
    case "cybersecurity_engineer":
      return "Cybersecurity Engineer";
    case "legal_team":
      return "Legal Team";
    case "development_team":
      return "Development Team";
    case "product_management":
      return "Product Management";
    case "lifecycle_manager":
      return "Lifecycle Manager";
    default:
      return "User";
  }
});
</script>

<style scoped>
.sidebar {
  padding: 1.1rem;
  border-right: 1px solid rgba(233, 238, 252, 0.1);
  background: rgba(15, 26, 46, 0.55);
  backdrop-filter: blur(12px);
  display: flex;
  flex-direction: column;
  gap: 0.9rem;
}

.brand {
  display: flex;
  gap: 0.75rem;
  align-items: center;
}

.brand-mark {
  width: 44px;
  height: 44px;
  border-radius: 12px;
  display: grid;
  place-items: center;
  background: linear-gradient(135deg, var(--color-primary-2), var(--color-primary));
  box-shadow: 0 10px 30px rgba(110, 168, 254, 0.18);
  font-weight: 900;
  color: white;
}

.brand-title {
  font-weight: 800;
}

.brand-sub {
  font-size: 0.8rem;
  color: var(--color-text-muted);
}

.separator {
  height: 1px;
  background: var(--color-border);
}

.nav {
  display: grid;
  gap: 0.4rem;
}

.nav-link {
  display: block;
  padding: 0.78rem 0.85rem;
  border-radius: 12px;
  border: 1px solid transparent;
  color: var(--color-text-muted);
  transition: background-color 0.15s ease, border-color 0.15s ease, color 0.15s ease;
}

.nav-link:hover {
  background: rgba(255, 255, 255, 0.04);
  color: var(--color-text);
}

.nav-link-active {
  background: rgba(255, 255, 255, 0.06);
  border-color: rgba(110, 168, 254, 0.25);
  color: var(--color-text);
}

.sidebar-footer {
  margin-top: auto;
  display: flex;
  align-items: center;
}

.badge-strong {
  margin-left: 0.35rem;
  color: var(--color-text);
}

@media (max-width: 960px) {
  .sidebar {
    display: none;
  }
}
</style>