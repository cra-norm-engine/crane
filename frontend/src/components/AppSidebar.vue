<!--
  CRANE — CRA Norm Engine
  Copyright (C) 2026 Ali Mohammad Hosseini
  SPDX-License-Identifier: AGPL-3.0-or-later
-->
<template>
  <aside
    class="sidebar"
    :class="{ 'sidebar-open': open, 'sidebar-collapsed': effectiveCollapsed }"
    aria-label="Main navigation"
  >
    <div class="brand-row">
      <AppLogo :compact="effectiveCollapsed" :scale="effectiveCollapsed ? 0.72 : 1" />
      <button class="mobile-close" type="button" aria-label="Close navigation" @click="emit('close')">
        <svg viewBox="0 0 20 20" aria-hidden="true"><path d="M4.7 4.7 10 8.6l5.3-3.9 1.4 1.4-5.3 3.9 5.3 3.9-1.4 1.4-5.3-3.9-5.3 3.9-1.4-1.4L8.6 10 3.3 6.1z" fill="currentColor" /></svg>
      </button>
      <button
        class="collapse-button"
        type="button"
        :aria-label="effectiveCollapsed ? 'Expand navigation' : 'Collapse navigation'"
        :title="effectiveCollapsed ? 'Expand navigation' : 'Collapse navigation'"
        @click="toggleCollapsed"
      >
        <svg viewBox="0 0 20 20" aria-hidden="true">
          <path :d="effectiveCollapsed ? ICONS.chevronRight : ICONS.chevronLeft" fill="currentColor" />
        </svg>
      </button>
    </div>

    <div class="nav-search" :class="{ 'nav-search-collapsed': effectiveCollapsed }">
      <svg viewBox="0 0 20 20" aria-hidden="true">
        <path :d="ICONS.search" fill="currentColor" />
      </svg>
      <input
        v-if="!effectiveCollapsed"
        ref="searchInput"
        v-model.trim="searchQuery"
        type="search"
        placeholder="Search navigation…"
        aria-label="Search navigation"
        @keydown.esc="clearSearch"
      />
      <button
        v-else
        type="button"
        aria-label="Search navigation"
        title="Search navigation (Ctrl/⌘ K)"
        @click="openSearch"
      />
    </div>

    <nav class="sidebar-nav" aria-label="Main navigation">
      <template v-if="favoriteItems.length">
        <div v-if="!effectiveCollapsed" class="nav-section-label">Favorites</div>
        <div class="nav-group nav-primary">
          <RouterLink
            v-for="item in favoriteItems"
            :key="`favorite-${item.route}`"
            :to="navTarget(item)"
            class="nav-link"
            :class="{ 'nav-link-active': route.name === item.route }"
            :title="itemTooltip(item)"
            @click="handleNavClick"
          >
            <span class="nav-icon" aria-hidden="true"><svg viewBox="0 0 20 20"><path :d="item.icon" fill="currentColor" /></svg></span>
            <span v-if="!effectiveCollapsed">{{ item.label }}</span>
            <span v-if="!effectiveCollapsed && item.count" class="nav-count">{{ item.count }}</span>
          </RouterLink>
        </div>
      </template>

      <div v-if="!effectiveCollapsed" class="nav-section-label">Overview</div>
      <div class="nav-group nav-primary">
        <div v-for="item in filteredOverviewItems" :key="item.route" class="nav-item-row">
          <RouterLink :to="navTarget(item)" class="nav-link" :class="{ 'nav-link-active': route.name === item.route }" :title="itemTooltip(item)" @click="handleNavClick">
            <span class="nav-icon" aria-hidden="true"><svg viewBox="0 0 20 20"><path :d="item.icon" fill="currentColor" /></svg></span>
            <span v-if="!effectiveCollapsed">{{ item.label }}</span>
            <span v-if="!effectiveCollapsed && item.count" class="nav-count">{{ item.count }}</span>
          </RouterLink>
          <button v-if="!effectiveCollapsed" class="favorite-button" type="button" :aria-label="favoriteLabel(item)" :title="favoriteLabel(item)" @click="toggleFavorite(item.route)">
            <span aria-hidden="true">{{ isFavorite(item.route) ? '★' : '☆' }}</span>
          </button>
        </div>
      </div>

      <div v-if="searchQuery && !hasSearchResults" class="nav-empty">
        No navigation matches “{{ searchQuery }}”.
      </div>

      <template v-for="group in visibleGroups" :key="group.id">
        <div class="nav-divider" role="separator" />
        <div class="nav-group">
          <button
            v-if="!effectiveCollapsed"
            type="button"
            class="nav-group-header"
            :aria-expanded="isExpanded(group.id)"
            :aria-controls="`nav-group-${group.id}`"
            @click="toggleGroup(group.id)"
          >
            <span class="nav-group-label">{{ group.label }}</span>
            <svg class="nav-group-chevron" :class="{ 'is-expanded': isExpanded(group.id) }" viewBox="0 0 16 16" aria-hidden="true">
              <path d="M4 6l4 4 4-4" fill="currentColor" />
            </svg>
          </button>

          <div
            :id="`nav-group-${group.id}`"
            class="nav-group-body"
            :class="{ 'is-expanded': effectiveCollapsed || isExpanded(group.id) }"
          >
            <div class="nav-group-links">
              <div v-for="item in group.items" :key="item.route" class="nav-item-row">
                <RouterLink :to="navTarget(item)" class="nav-link" active-class="nav-link-active" :title="itemTooltip(item, group.label)" @click="handleNavClick">
                  <span class="nav-icon" aria-hidden="true"><svg viewBox="0 0 20 20"><path :d="item.icon" fill="currentColor" /></svg></span>
                  <span v-if="!effectiveCollapsed">{{ item.label }}</span>
                  <span v-if="!effectiveCollapsed && item.count" class="nav-count">{{ item.count }}</span>
                </RouterLink>
                <button v-if="!effectiveCollapsed" class="favorite-button" type="button" :aria-label="favoriteLabel(item)" :title="favoriteLabel(item)" @click="toggleFavorite(item.route)">
                  <span aria-hidden="true">{{ isFavorite(item.route) ? '★' : '☆' }}</span>
                </button>
              </div>
            </div>
          </div>
        </div>
      </template>
    </nav>

    <div class="sidebar-footer">
      <div class="user-row" :title="effectiveCollapsed ? `${displayName} — ${primaryRoleLabel}` : undefined">
        <div class="user-avatar" aria-hidden="true"><img v-if="authStore.user?.avatar_data" :src="authStore.user.avatar_data" alt="" /><span v-else>{{ userEmoji }}</span></div>
        <div v-if="!effectiveCollapsed" class="user-info">
          <div class="user-name">{{ displayName }}</div>
          <span class="user-role-badge">{{ primaryRoleLabel }}</span>
        </div>
      </div>

      <RouterLink
        :to="{ name: 'settings' }"
        class="nav-link"
        active-class="nav-link-active"
        :title="effectiveCollapsed ? 'Settings' : undefined"
        @click="handleNavClick"
      >
        <span class="nav-icon" aria-hidden="true">
          <svg viewBox="0 0 20 20"><path :d="ICONS.settings" fill="currentColor" /></svg>
        </span>
        <span v-if="!effectiveCollapsed">Settings</span>
      </RouterLink>

      <button
        class="nav-link nav-link-button"
        type="button"
        aria-label="Log out of CRANE"
        :title="effectiveCollapsed ? 'Log out' : undefined"
        @click="logout"
      >
        <span class="nav-icon" aria-hidden="true">
          <svg viewBox="0 0 20 20"><path :d="ICONS.logout" fill="currentColor" /></svg>
        </span>
        <span v-if="!effectiveCollapsed">Log out</span>
      </button>
    </div>
  </aside>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref, watch } from "vue";
import { RouterLink, useRoute, useRouter } from "vue-router";

import AppLogo from "@/components/AppLogo.vue";
import { apiClient } from "@/services/api";
import { lifecycleNotificationService } from "@/services/lifecycle-notification-service";
import { taskService } from "@/services/task-service";
import { vulnerabilityReportService } from "@/services/vulnerability-report-service";
import { useAuthStore } from "@/stores/auth";

interface NavItem {
  label: string;
  route: string;
  icon: string;
  allowed?: boolean;
  count?: number;
}

interface NavGroup {
  id: string;
  label: string;
  items: NavItem[];
}

const ICONS = {
  dashboard: "M3 3h6v6H3zm8 0h6v4h-6zM3 11h4v6H3zm6 2h8v4H9z",
  tasks: "M3 5h14v2H3zm0 4h9v2H3zm0 4h6v2H3zm12-2-4 4-2-2 1.4-1.4L15 12.2l2.6-2.6z",
  journey: "M6 3a2.5 2.5 0 0 0-.5 4.95V12.5a2.5 2.5 0 1 0 2 0V7.95A2.5 2.5 0 0 0 6 3zm8 1a3 3 0 0 0-3 3c0 2 3 5 3 5s3-3 3-5a3 3 0 0 0-3-3z",
  products: "M4 5.5 10 3l6 2.5v9L10 17l-6-2.5zm6 .2L6.2 7.2 10 8.8l3.8-1.6zM5.5 8.4v5l3.8 1.6v-5zm9 0-3.8 1.6v5l3.8-1.6z",
  sbom: "M10 2 2 6l8 4 8-4zm-8 6 8 4 8-4v4l-8 4-8-4zm0 6 8 4 8-4v2l-8 4-8-4z",
  risk: "M10 2 2 16h16zm0 4.4 4.5 7.6h-9zM9 8h2v3H9zm0 4h2v2H9z",
  requirements: "M3 4h14v12H3zm2 2v2h10V6zm0 4v4h3v-4zm5 0v4h5v-4z",
  shield: "M10 2 4 5v4c0 4.1 2.4 7.8 6 9 3.6-1.2 6-4.9 6-9V5zm0 3.2a2.3 2.3 0 0 1 1.3 4.2v2.9H8.7V9.4A2.3 2.3 0 0 1 10 5.2z",
  update: "M10 2a8 8 0 1 0 0 16A8 8 0 0 0 10 2zm-1 4h2v5H9zm0 6h2v2H9z",
  changes: "M3 5h14v2H3zm0 4h9v2H3zm0 4h6v2H3zm11-1 1.5-1.5L17 8l-4 4v3h3v-4z",
  bell: "M10 2a5 5 0 0 0-5 5v2.2c0 .5-.2.9-.5 1.3L3 12v1h14v-1l-1.5-1.5c-.3-.4-.5-.8-.5-1.3V7a5 5 0 0 0-5-5zm0 16a2.5 2.5 0 0 0 2.4-2H7.6A2.5 2.5 0 0 0 10 18z",
  support: "M10 2a7 7 0 0 0-7 7v1H2v3a2 2 0 0 0 2 2h1v-5H4V9a6 6 0 1 1 12 0v1h-1v5h1a2 2 0 0 0 2-2v-3h-1V9a7 7 0 0 0-7-7z",
  supplier: "M3 4h14v12H3zm2 2v2h10V6zm0 4v4h4v-4zm6 0v4h4v-4z",
  document: "M5 2h7l3 3v11a1 1 0 0 1-1 1H5a1 1 0 0 1-1-1V3a1 1 0 0 1 1-1zm6 1v3h3zM6 9h8v1.5H6zm0 3h8v1.5H6z",
  certification: "M10 2a8 8 0 1 0 0 16A8 8 0 0 0 10 2zm0 2a6 6 0 1 1 0 12A6 6 0 0 1 10 4zm-1 3v4.4l3.2 1.9.8-1.4L10.5 10.5V7z",
  audit: "M4 3h12v14H4zm2 2v10h8V5zm1 2h6v1.8H7zm0 3h6v1.8H7z",
  data: "M13 3v2H7V3H5v2H3v12h14V5h-2V3zM5 7h10v8H5zm3 2v4l4-2z",
  users: "M10 10a3.5 3.5 0 1 0-3.5-3.5A3.5 3.5 0 0 0 10 10zm0 2c-3.1 0-5.8 1.6-6.8 4h13.6c-1-2.4-3.7-4-6.8-4z",
  roles: "M10 2 4 5v4c0 4.1 2.4 7.8 6 9 3.6-1.2 6-4.9 6-9V5zm0 3.2a2 2 0 0 1 1.2 3.6l1.1 3.2H7.7l1.1-3.2A2 2 0 0 1 10 5.2z",
  ldap: "M3 4h14v2H3zm0 4h14v2H3zm0 4h9v2H3zm11 0 3 3-3 3v-2H9v-2h5z",
  search: "M8.5 3a5.5 5.5 0 1 0 3.45 9.78L16.17 17 17.6 15.6l-4.22-4.22A5.5 5.5 0 0 0 8.5 3zm0 2a3.5 3.5 0 1 1 0 7 3.5 3.5 0 0 1 0-7z",
  settings: "M10 6.5A3.5 3.5 0 1 0 10 13.5 3.5 3.5 0 0 0 10 6.5zm0 2A1.5 1.5 0 1 1 10 11.5 1.5 1.5 0 0 1 10 8.5zM8.6 1.5l-.4 1.9-1.5.9-1.8-.7-1.4 2.4L5 7.2v1.7l-1.5 1.2 1.4 2.4 1.8-.7 1.5.9.4 1.9h2.8l.4-1.9 1.5-.9 1.8.7 1.4-2.4L15 8.9V7.2L16.5 6l-1.4-2.4-1.8.7-1.5-.9-.4-1.9z",
  logout: "M8 3H4v14h4v-2H6V5h2zm4.6 3.4L11.2 7.8 13.4 10H7v2h6.4l-2.2 2.2 1.4 1.4L17.2 11z",
  chevronLeft: "M12.7 4.3 7 10l5.7 5.7-1.4 1.4L4.2 10l7.1-7.1z",
  chevronRight: "m7.3 4.3 1.4-1.4 7.1 7.1-7.1 7.1-1.4-1.4L13 10z",
} as const;

const props = withDefaults(defineProps<{ open?: boolean }>(), { open: false });
const emit = defineEmits<{ close: []; "collapse-change": [collapsed: boolean] }>();
const route = useRoute();
const router = useRouter();
const authStore = useAuthStore();
const searchInput = ref<HTMLInputElement>();
const searchQuery = ref("");
const collapsed = ref(localStorage.getItem("sidebar-collapsed") === "true");
const mobileMedia = window.matchMedia("(max-width: 960px)");
const isMobile = ref(mobileMedia.matches);
const effectiveCollapsed = computed(() => collapsed.value && !isMobile.value);
const taskCount = ref(0);
const vulnerabilityCount = ref(0);
const alertCount = ref(0);
const favoriteRoutes = ref<string[]>(readStringList("sidebar-favorites"));

const can = (permission: string) => authStore.hasPermission(permission);
const canViewAnnexMatrix = computed(() => can("annex_requirement_read") || can("requirement_mapping_read"));

const overviewItems = computed<NavItem[]>(() => [
  { label: "Dashboard", route: "dashboard", icon: ICONS.dashboard },
  { label: "My tasks", route: "my-tasks", icon: ICONS.tasks, count: taskCount.value },
  { label: "Compliance journey", route: "compliance-journey", icon: ICONS.journey },
]);

const groups = computed<NavGroup[]>(() => [
  {
    id: "product",
    label: "Product workspace",
    items: [
      { label: "Products", route: "products", icon: ICONS.products },
      { label: "SBOMs & components", route: "sbom-records", icon: ICONS.sbom, allowed: can("security_update_read") },
      { label: "Risk assessments", route: "risk-assessments", icon: ICONS.risk, allowed: can("risk_assessment_read") },
      { label: "CRA requirements", route: "annex-matrix", icon: ICONS.requirements, allowed: canViewAnnexMatrix.value },
    ],
  },
  {
    id: "security",
    label: "Security & lifecycle",
    items: [
      { label: "Vulnerabilities", route: "vulnerability-handling", icon: ICONS.shield, count: vulnerabilityCount.value, allowed: can("security_update_read") },
      { label: "Security updates", route: "security-updates", icon: ICONS.update, allowed: can("security_update_read") },
      { label: "Substantial changes", route: "changes", icon: ICONS.changes, allowed: can("change_read") },
      { label: "Lifecycle alerts", route: "lifecycle-notifications", icon: ICONS.bell, count: alertCount.value, allowed: can("lifecycle_notification_read") },
      { label: "Support hub", route: "support-hub", icon: ICONS.support, allowed: can("lifecycle_notification_read") },
    ],
  },
  {
    id: "supply-chain",
    label: "Supply chain",
    items: [
      { label: "Supplier assurance", route: "supplier-assurance", icon: ICONS.supplier, allowed: can("supplier_assessment_read") },
    ],
  },
  {
    id: "records",
    label: "Conformity & records",
    items: [
      { label: "Declarations", route: "declarations", icon: ICONS.document, allowed: can("release_read") },
      { label: "Certifications", route: "certification-records", icon: ICONS.certification, allowed: can("certification_record_read") },
      { label: "Audit history", route: "audit-history", icon: ICONS.audit, allowed: can("audit_read") },
      { label: "Data export / import", route: "product-data", icon: ICONS.data },
    ],
  },
  {
    id: "administration",
    label: "Administration",
    items: [
      { label: "Users", route: "admin-users", icon: ICONS.users },
      { label: "Roles & access", route: "admin-roles", icon: ICONS.roles },
      { label: "LDAP", route: "admin-ldap", icon: ICONS.ldap },
    ].map((item) => ({ ...item, allowed: can("admin_manage_users") })),
  },
].map((group) => ({ ...group, items: group.items.filter((item) => item.allowed !== false) }))
  .filter((group) => group.items.length > 0));

function matchesSearch(item: NavItem): boolean {
  return !searchQuery.value || item.label.toLowerCase().includes(searchQuery.value.toLowerCase());
}

const filteredOverviewItems = computed(() => overviewItems.value.filter(matchesSearch));
const visibleGroups = computed(() => groups.value
  .map((group) => ({ ...group, items: group.items.filter(matchesSearch) }))
  .filter((group) => group.items.length > 0));
const hasSearchResults = computed(() => filteredOverviewItems.value.length > 0 || visibleGroups.value.length > 0);
const allItems = computed(() => [...overviewItems.value, ...groups.value.flatMap((group) => group.items)]);
const favoriteItems = computed(() => favoriteRoutes.value
  .map((routeName) => allItems.value.find((item) => item.route === routeName))
  .filter((item): item is NavItem => Boolean(item)));
function navTarget(item: NavItem): { name: string } {
  return { name: item.route };
}

function itemTooltip(item: NavItem, section = "Overview"): string {
  return `${section} — ${item.label}`;
}

function readStringList(key: string): string[] {
  try {
    const value = JSON.parse(localStorage.getItem(key) ?? "[]");
    return Array.isArray(value) ? value.filter((item): item is string => typeof item === "string") : [];
  } catch {
    return [];
  }
}

function isFavorite(routeName: string): boolean {
  return favoriteRoutes.value.includes(routeName);
}

function favoriteLabel(item: NavItem): string {
  return `${isFavorite(item.route) ? "Remove" : "Add"} ${item.label} ${isFavorite(item.route) ? "from" : "to"} favorites`;
}

function toggleFavorite(routeName: string): void {
  favoriteRoutes.value = isFavorite(routeName)
    ? favoriteRoutes.value.filter((item) => item !== routeName)
    : [...favoriteRoutes.value, routeName].slice(-3);
  localStorage.setItem("sidebar-favorites", JSON.stringify(favoriteRoutes.value));
}

async function loadSidebarData(): Promise<void> {
  const requests: Promise<void>[] = [
    taskService.listMyTasks().then((items) => {
      taskCount.value = items.filter((item) => item.viewer_is_assignee !== false).length;
    }),
  ];
  if (can("security_update_read")) {
    requests.push(vulnerabilityReportService.list().then((items) => {
      vulnerabilityCount.value = items.filter((item) => item.status !== "retired").length;
    }));
  }
  if (can("lifecycle_notification_read")) {
    requests.push(lifecycleNotificationService.list({ status: "pending" }).then((items) => { alertCount.value = items.length; }));
  }
  await Promise.allSettled(requests);
}

const ROUTE_GROUP_MAP: Record<string, string> = {
  products: "product", "product-detail": "product", "release-gate": "product",
  "sbom-records": "product", "risk-assessments": "product", "risk-assessment-detail": "product", "annex-matrix": "product",
  "vulnerability-handling": "security", "security-updates": "security", changes: "security",
  "lifecycle-notifications": "security", "support-hub": "security",
  "supplier-assurance": "supply-chain", "supplier-assessment-detail": "supply-chain", "third-party-component-detail": "supply-chain",
  declarations: "records", "certification-records": "records", "audit-history": "records", "product-data": "records",
  "admin-users": "administration", "admin-roles": "administration", "admin-ldap": "administration",
};

const activeGroup = computed(() => ROUTE_GROUP_MAP[String(route.name ?? "")] ?? "product");
const expandedGroup = ref(activeGroup.value);
watch(activeGroup, (group) => { expandedGroup.value = group; });

function isExpanded(groupId: string): boolean {
  return Boolean(searchQuery.value) || expandedGroup.value === groupId;
}

function toggleGroup(groupId: string): void {
  expandedGroup.value = expandedGroup.value === groupId ? "" : groupId;
}

function toggleCollapsed(): void {
  collapsed.value = !collapsed.value;
  localStorage.setItem("sidebar-collapsed", String(collapsed.value));
  emit("collapse-change", collapsed.value);
  if (collapsed.value) clearSearch();
}

function openSearch(): void {
  if (collapsed.value) toggleCollapsed();
  requestAnimationFrame(() => searchInput.value?.focus());
}

function clearSearch(): void {
  searchQuery.value = "";
  searchInput.value?.blur();
}

function handleShortcut(event: KeyboardEvent): void {
  if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === "k") {
    event.preventDefault();
    openSearch();
  }
}

onMounted(() => {
  emit("collapse-change", collapsed.value);
  window.addEventListener("keydown", handleShortcut);
  mobileMedia.addEventListener("change", handleViewportChange);
  void loadSidebarData();
});
onBeforeUnmount(() => {
  window.removeEventListener("keydown", handleShortcut);
  mobileMedia.removeEventListener("change", handleViewportChange);
});

function handleViewportChange(event: MediaQueryListEvent): void {
  isMobile.value = event.matches;
}

const primaryRoleLabel = computed(() => ({
  admin: "Admin", product_owner: "Product Owner", cybersecurity_engineer: "Cybersecurity Engineer",
  legal_team: "Legal Team", development_team: "Development Team", product_management: "Product Management",
  lifecycle_manager: "Lifecycle Manager",
}[authStore.roles?.[0] ?? ""] ?? "User"));
const displayName = computed(() => authStore.userFullName || authStore.userEmail || "User");
const userEmoji = computed(() => ({
  admin: "🛡️",
  product_owner: "🧭",
  cybersecurity_engineer: "🔐",
  legal_team: "⚖️",
  development_team: "🧑‍💻",
  product_management: "📊",
  lifecycle_manager: "♻️",
}[authStore.roles?.[0] ?? ""] ?? "👤"));

function handleNavClick(): void {
  clearSearch();
  emit("close");
}

async function logout(): Promise<void> {
  try {
    await apiClient.post("/auth/logout", { refresh_token: authStore.refreshToken });
  } catch {
    // Local logout must still succeed if the API is unavailable.
  }
  authStore.logout();
  router.push({ name: "login" });
}

</script>

<style scoped>
.sidebar {
  width: var(--sidebar-width);
  height: 100vh;
  padding: 0.8rem 0.7rem;
  position: sticky;
  top: 0;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  box-sizing: border-box;
  border-right: 1px solid var(--color-border);
  background: var(--color-sidebar-bg);
  backdrop-filter: blur(14px);
  transition: width var(--t-base), background var(--t-base), border-color var(--t-base);
}

.sidebar.sidebar-collapsed { width: 72px; }

.brand-row { min-height: 52px; display: flex; align-items: center; justify-content: space-between; padding: 0.35rem 0.4rem 0.65rem; }
.sidebar-collapsed .brand-row { flex-direction: column; gap: 0.45rem; padding-inline: 0; }
.collapse-button { width: 28px; height: 28px; display: grid; place-items: center; flex-shrink: 0; border: 1px solid var(--color-border); border-radius: 8px; color: var(--color-text-muted); background: transparent; cursor: pointer; }
.collapse-button:hover { color: var(--color-text); background: var(--color-nav-hover-bg); }
.collapse-button svg { width: 15px; height: 15px; }
.mobile-close { display: none; width: 34px; height: 34px; place-items: center; border: 1px solid var(--color-border); border-radius: 9px; background: transparent; color: var(--color-text-muted); }
.mobile-close svg { width: 17px; height: 17px; }

.nav-search { min-height: 38px; margin: 0.25rem 0 0.6rem; padding: 0 0.65rem; display: flex; align-items: center; gap: 0.5rem; border: 1px solid var(--color-border); border-radius: 10px; background: color-mix(in srgb, var(--color-sidebar-bg) 70%, var(--color-surface)); }
.nav-search:focus-within { border-color: var(--color-primary-2); box-shadow: 0 0 0 2px color-mix(in srgb, var(--color-primary-2) 18%, transparent); }
.nav-search svg { width: 17px; height: 17px; flex-shrink: 0; color: var(--color-text-muted); }
.nav-search input { width: 100%; min-width: 0; padding: 0; border: 0; outline: 0; background: transparent; color: var(--color-text); font: inherit; font-size: var(--text-sm); }
.nav-search input::placeholder { color: var(--color-text-muted); }
.nav-search-collapsed { width: 42px; padding: 0; margin-inline: auto; justify-content: center; position: relative; }
.nav-search-collapsed button { position: absolute; inset: 0; border: 0; background: transparent; cursor: pointer; }

.sidebar-nav { flex: 1; min-height: 0; display: flex; flex-direction: column; overflow-y: auto; scrollbar-width: none; }
.sidebar-nav::-webkit-scrollbar { display: none; }
.nav-section-label, .nav-group-label { color: rgba(220, 233, 214, 0.42); font-size: 10px; font-weight: 750; letter-spacing: 0.1em; text-transform: uppercase; }
.nav-section-label { padding: 0.2rem 0.55rem 0.1rem; }
.nav-group { display: flex; flex-direction: column; gap: 0.12rem; padding: 0.25rem 0; }
.nav-group-header { width: 100%; padding: 0.25rem 0.55rem; display: flex; justify-content: space-between; align-items: center; border: 0; border-radius: 7px; background: transparent; cursor: pointer; }
.nav-group-header:hover { background: var(--color-nav-hover-bg); }
.nav-group-chevron { width: 13px; color: var(--color-text-muted); opacity: 0.6; transform: rotate(-90deg); transition: transform var(--t-base); }
.nav-group-chevron.is-expanded { transform: rotate(0); }
.nav-group-body { display: grid; grid-template-rows: 0fr; opacity: 0; overflow: hidden; transition: grid-template-rows var(--t-slow), opacity var(--t-base); }
.nav-group-body.is-expanded { grid-template-rows: 1fr; opacity: 1; }
.nav-group-links { min-height: 0; display: flex; flex-direction: column; gap: 0.12rem; }
.nav-divider { height: 1px; margin: 0.15rem 0.3rem; background: var(--color-border); opacity: 0.5; }
.nav-empty { padding: 1rem 0.65rem; color: var(--color-text-muted); font-size: var(--text-sm); line-height: 1.45; }

.nav-item-row { display: flex; align-items: center; min-width: 0; }
.nav-item-row .nav-link { flex: 1; min-width: 0; }
.nav-link { display: flex; align-items: center; gap: 0.65rem; padding: 0.58rem 0.7rem; border: 1px solid transparent; border-radius: 10px; color: var(--color-text-muted); text-decoration: none; white-space: nowrap; overflow: hidden; font-size: var(--text-sm); font-weight: 500; transition: background-color var(--t-fast), border-color var(--t-fast), color var(--t-fast); }
.nav-link:hover { background: var(--color-nav-hover-bg); border-color: var(--color-nav-hover-border); color: var(--color-text); }
.nav-icon { width: 18px; height: 18px; display: inline-flex; flex-shrink: 0; opacity: 0.75; }
.nav-icon svg { width: 18px; height: 18px; }
.nav-link-active { background: linear-gradient(135deg, rgba(112, 185, 23, 0.13), rgba(28, 107, 39, 0.16)); border-color: rgba(173, 214, 84, 0.22); color: var(--color-text); font-weight: 650; box-shadow: inset 3px 0 0 var(--color-primary-2); }
.nav-link-active .nav-icon { color: var(--color-primary-2); opacity: 1; }
.nav-link-button { width: 100%; background: transparent; text-align: left; cursor: pointer; font-family: inherit; }
.nav-count { min-width: 1.35rem; margin-left: auto; padding: 0.08rem 0.35rem; border-radius: 999px; background: color-mix(in srgb, var(--color-primary-2) 18%, transparent); color: var(--color-primary-2); font-size: 0.67rem; font-weight: 750; text-align: center; }
.favorite-button { width: 25px; height: 28px; display: grid; place-items: center; flex-shrink: 0; padding: 0; border: 0; background: transparent; color: var(--color-text-muted); cursor: pointer; opacity: 0; }
.nav-item-row:hover .favorite-button, .favorite-button:focus-visible { opacity: 1; }
.favorite-button:hover { color: #e2ae28; }

.sidebar-footer { flex-shrink: 0; display: flex; flex-direction: column; gap: 0.25rem; padding-top: 0.55rem; border-top: 1px solid rgba(233, 238, 252, 0.08); }
.user-row { display: flex; align-items: center; gap: 0.65rem; padding: 0.4rem 0.35rem; }
.user-avatar { width: 32px; height: 32px; display: grid; place-items: center; flex-shrink: 0; border: 1px solid rgba(173, 214, 84, 0.2); border-radius: 9px; background: linear-gradient(135deg, rgba(112, 185, 23, 0.22), rgba(28, 107, 39, 0.28)); font-size: 1rem; }
.user-avatar img { width: 100%; height: 100%; border-radius: inherit; object-fit: cover; }
.user-info { min-width: 0; display: flex; flex-direction: column; gap: 0.1rem; }
.user-name, .user-role-badge { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.user-name { color: var(--color-text); font-size: 0.82rem; font-weight: 700; }
.user-role-badge { color: var(--color-text-muted); font-size: 0.68rem; }
.sidebar-collapsed .nav-link { justify-content: center; padding-inline: 0; }
.sidebar-collapsed .nav-divider { margin-inline: 0.55rem; }
.sidebar-collapsed .user-row { justify-content: center; }

@media (max-width: 960px) {
  .sidebar, .sidebar.sidebar-collapsed { position: fixed; left: 0; top: 0; z-index: 50; width: 248px; transform: translateX(-100%); transition: transform 0.28s cubic-bezier(0.4, 0, 0.2, 1), box-shadow var(--t-base); }
  .sidebar.sidebar-open { transform: translateX(0); box-shadow: var(--shadow-lg); }
  .collapse-button { display: none; }
  .mobile-close { display: grid; margin-left: auto; cursor: pointer; }
  .sidebar-collapsed .brand-row { flex-direction: row; padding: 0.35rem 0.4rem 0.65rem; }
  .sidebar-collapsed .nav-search { width: auto; padding: 0 0.65rem; margin-inline: 0; justify-content: flex-start; }
  .sidebar-collapsed .nav-link { justify-content: flex-start; padding-inline: 0.7rem; }
}
</style>

<style>
:root[data-theme="light"] .nav-group-label,
:root[data-theme="light"] .nav-section-label { color: oklch(0.48 0.07 150 / 0.58); }
:root[data-theme="light"] .nav-link-active { background: oklch(0.955 0.024 150); border-color: oklch(0.85 0.05 150); color: oklch(0.26 0.07 150); box-shadow: inset 3px 0 0 oklch(0.48 0.092 150); }
:root[data-theme="light"] .nav-link-active .nav-icon { color: oklch(0.38 0.092 150); }
</style>
