<template>
  <!--
    AppSidebar — primary navigation drawer.

    Desktop: permanently visible on the left; width is controlled by
             the CSS variable --sidebar-width shared with AppLayout.

    Mobile:  fixed overlay that slides in from the left when the
             hamburger in AppHeader is pressed.  Emits 'close' when:
               • a nav link is clicked (so the overlay collapses)
               • the close button (×) is pressed
             The backdrop in AppLayout also fires 'close' on click.
  -->
  <aside
    class="sidebar"
    :class="{ 'sidebar-open': open }"
    aria-label="Main navigation"
  >

    <!-- ══════════════════════════════════════════
         BRAND — logo + product name
         ══════════════════════════════════════════ -->
    <div class="brand">
      <AppLogo />
    </div>

    <!-- ══════════════════════════════════════════
         NAV LINKS
         ══════════════════════════════════════════ -->
    <nav class="sidebar-nav" aria-label="Main navigation">

      <!-- Overview group — single Dashboard link -->
      <div class="nav-group">
        <RouterLink
          :to="{ name: 'dashboard' }"
          class="nav-link"
          active-class="nav-link-active"
          exact-active-class="nav-link-active"
          @click="handleNavClick"
        >
          <span class="nav-icon" aria-hidden="true">
            <!-- Dashboard / grid icon -->
            <svg viewBox="0 0 20 20"><path d="M3 3h6v6H3zm8 0h6v4h-6zM3 11h4v6H3zm6 2h8v4H9z" fill="currentColor"/></svg>
          </span>
          <span>Dashboard</span>
        </RouterLink>
      </div>

      <!-- My Tasks — personal task dashboard -->
      <div class="nav-group">
        <RouterLink
          :to="{ name: 'my-tasks' }"
          class="nav-link"
          active-class="nav-link-active"
          @click="handleNavClick"
        >
          <span class="nav-icon" aria-hidden="true">
            <!-- Checkbox / tasks icon -->
            <svg viewBox="0 0 20 20"><path d="M3 5h14v2H3zm0 4h9v2H3zm0 4h6v2H3zm12-2-4 4-2-2 1.4-1.4L15 12.2l2.6-2.6z" fill="currentColor"/></svg>
          </span>
          <span>My Tasks</span>
        </RouterLink>
      </div>

      <div class="nav-divider" role="separator" />

      <!-- Main workspace links -->
      <div class="nav-group">
        <p class="nav-group-label">Menu</p>

        <!-- Product inventory — always visible -->
        <RouterLink
          :to="{ name: 'products' }"
          class="nav-link"
          active-class="nav-link-active"
          @click="handleNavClick"
        >
          <span class="nav-icon" aria-hidden="true">
            <!-- Box / package icon -->
            <svg viewBox="0 0 20 20"><path d="M4 5.5 10 3l6 2.5v9L10 17l-6-2.5zm6 .2L6.2 7.2 10 8.8l3.8-1.6zM5.5 8.4v5l3.8 1.6v-5zm9 0-3.8 1.6v5l3.8-1.6z" fill="currentColor"/></svg>
          </span>
          <span>Product inventory</span>
        </RouterLink>

        <!-- Risk assessments — permission-gated -->
        <RouterLink
          v-if="canViewRiskAssessments"
          :to="{ name: 'risk-assessments' }"
          class="nav-link"
          active-class="nav-link-active"
          @click="handleNavClick"
        >
          <span class="nav-icon" aria-hidden="true">
            <!-- Warning triangle icon -->
            <svg viewBox="0 0 20 20"><path d="M10 2 2 16h16zm0 4.4 4.5 7.6h-9zM9 8h2v3H9zm0 4h2v2H9z" fill="currentColor"/></svg>
          </span>
          <span>Risk assessments</span>
        </RouterLink>

        <!-- Annex I matrix — permission-gated -->
        <RouterLink
          v-if="canViewAnnexMatrix"
          :to="{ name: 'annex-matrix' }"
          class="nav-link"
          active-class="nav-link-active"
          @click="handleNavClick"
        >
          <span class="nav-icon" aria-hidden="true">
            <!-- Table / matrix icon -->
            <svg viewBox="0 0 20 20"><path d="M3 4h14v12H3zm2 2v2h10V6zm0 4v4h3v-4zm5 0v4h5v-4z" fill="currentColor"/></svg>
          </span>
          <span>CRA requirements</span>
        </RouterLink>

        <!-- Lifecycle alerts — permission-gated -->
        <RouterLink
          v-if="canViewLifecycleNotifications"
          :to="{ name: 'lifecycle-notifications' }"
          class="nav-link"
          active-class="nav-link-active"
          @click="handleNavClick"
        >
          <span class="nav-icon" aria-hidden="true">
            <!-- Bell icon -->
            <svg viewBox="0 0 20 20"><path d="M10 2a5 5 0 0 0-5 5v2.2c0 .5-.2.9-.5 1.3L3 12v1h14v-1l-1.5-1.5c-.3-.4-.5-.8-.5-1.3V7a5 5 0 0 0-5-5zm0 16a2.5 2.5 0 0 0 2.4-2H7.6A2.5 2.5 0 0 0 10 18z" fill="currentColor"/></svg>
          </span>
          <span>Lifecycle alerts</span>
        </RouterLink>

        <!-- Certifications — permission-gated -->
        <RouterLink
          v-if="canViewCertificationRecords"
          :to="{ name: 'certification-records' }"
          class="nav-link"
          active-class="nav-link-active"
          @click="handleNavClick"
        >
          <span class="nav-icon" aria-hidden="true">
            <!-- Certificate / clock icon -->
            <svg viewBox="0 0 20 20"><path d="M10 2a8 8 0 1 0 0 16A8 8 0 0 0 10 2zm0 2a6 6 0 1 1 0 12A6 6 0 0 1 10 4zm-1 3v4.4l3.2 1.9.8-1.4L10.5 10.5V7z" fill="currentColor"/></svg>
          </span>
          <span>Certifications</span>
        </RouterLink>

        <!-- Substantial changes — CRA Art. 3(4), permission-gated -->
        <RouterLink
          v-if="canViewChanges"
          :to="{ name: 'changes' }"
          class="nav-link"
          active-class="nav-link-active"
          @click="handleNavClick"
        >
          <span class="nav-icon" aria-hidden="true">
            <!-- Edit / changes icon -->
            <svg viewBox="0 0 20 20"><path d="M3 5h14v2H3zm0 4h9v2H3zm0 4h6v2H3zm11-1 1.5-1.5L17 8l-4 4v3h3v-4z" fill="currentColor"/></svg>
          </span>
          <span>Substantial changes</span>
        </RouterLink>

        <!-- Support Hub — customer support and lifecycle management tools -->
        <RouterLink
          v-if="canViewSupportHub"
          :to="{ name: 'support-hub' }"
          class="nav-link"
          active-class="nav-link-active"
          @click="handleNavClick"
        >
          <span class="nav-icon" aria-hidden="true">
            <!-- Headset / support icon -->
            <svg viewBox="0 0 20 20"><path d="M10 2a7 7 0 0 0-7 7v1H2v3a2 2 0 0 0 2 2h1v-5H4V9a6 6 0 1 1 12 0v1h-1v5h1a2 2 0 0 0 2-2v-3h-1V9a7 7 0 0 0-7-7z" fill="currentColor"/></svg>
          </span>
          <span>Support Hub</span>
        </RouterLink>
      </div>

      <!-- Vulnerability handling — CRA Annex I Part II (PSIRT workflow) -->
      <template v-if="canViewSecurityUpdates">
        <div class="nav-divider" role="separator" />
        <div class="nav-group">
          <p class="nav-group-label">Vulnerability handling</p>

          <RouterLink
            :to="{ name: 'vulnerability-handling' }"
            class="nav-link"
            active-class="nav-link-active"
            @click="handleNavClick"
          >
            <span class="nav-icon" aria-hidden="true">
              <svg viewBox="0 0 20 20"><path d="M10 2 4 5v4c0 4.1 2.4 7.8 6 9 3.6-1.2 6-4.9 6-9V5zm0 3.2a2.3 2.3 0 0 1 1.3 4.2v2.9H8.7V9.4A2.3 2.3 0 0 1 10 5.2z" fill="currentColor"/></svg>
            </span>
            <span>PSIRT workflow</span>
          </RouterLink>

          <RouterLink
            :to="{ name: 'security-updates' }"
            class="nav-link"
            active-class="nav-link-active"
            @click="handleNavClick"
          >
            <span class="nav-icon" aria-hidden="true">
              <svg viewBox="0 0 20 20"><path d="M10 2a8 8 0 1 0 0 16A8 8 0 0 0 10 2zm-1 4h2v5H9zm0 6h2v2H9z" fill="currentColor"/></svg>
            </span>
            <span>Security updates</span>
          </RouterLink>

          <!-- SBOM Analyzer — Annex I Part II §1 -->
          <RouterLink
            :to="{ name: 'sbom-records' }"
            class="nav-link"
            active-class="nav-link-active"
            @click="handleNavClick"
          >
            <span class="nav-icon" aria-hidden="true">
              <!-- Layers / SBOM icon -->
              <svg viewBox="0 0 20 20"><path d="M10 2 2 6l8 4 8-4zm-8 6 8 4 8-4v4l-8 4-8-4zm0 6 8 4 8-4v2l-8 4-8-4z" fill="currentColor"/></svg>
            </span>
            <span>SBOM analyzer</span>
          </RouterLink>
        </div>
      </template>

      <div class="nav-divider" role="separator" />

      <!-- Governance group -->
      <div class="nav-group">
        <p class="nav-group-label">Governance</p>

        <!-- Audit history — permission-gated -->
        <RouterLink
          v-if="canViewAudit"
          :to="{ name: 'audit-history' }"
          class="nav-link"
          active-class="nav-link-active"
          @click="handleNavClick"
        >
          <span class="nav-icon" aria-hidden="true">
            <!-- Document / audit icon -->
            <svg viewBox="0 0 20 20"><path d="M4 3h12v14H4zm2 2v10h8V5zm1 2h6v1.8H7zm0 3h6v1.8H7z" fill="currentColor"/></svg>
          </span>
          <span>Audit history</span>
        </RouterLink>

        <!-- Data export / import -->
        <RouterLink
          :to="{ name: 'product-data' }"
          class="nav-link"
          active-class="nav-link-active"
          @click="handleNavClick"
        >
          <span class="nav-icon" aria-hidden="true">
            <!-- Transfer / arrows icon -->
            <svg viewBox="0 0 20 20"><path d="M13 3v2H7V3H5v2H3v12h14V5h-2V3zM5 7h10v8H5zm3 2v4l4-2z" fill="currentColor"/></svg>
          </span>
          <span>Data export / import</span>
        </RouterLink>
      </div>

      <!-- Administration group — only for admins -->
      <template v-if="canManageAdmin">
        <div class="nav-divider" role="separator" />

        <div class="nav-group">
          <p class="nav-group-label">Administration</p>

          <RouterLink
            :to="{ name: 'admin-users' }"
            class="nav-link"
            active-class="nav-link-active"
            @click="handleNavClick"
          >
            <span class="nav-icon" aria-hidden="true">
              <!-- Person / user icon -->
              <svg viewBox="0 0 20 20"><path d="M10 10a3.5 3.5 0 1 0-3.5-3.5A3.5 3.5 0 0 0 10 10zm0 2c-3.1 0-5.8 1.6-6.8 4h13.6c-1-2.4-3.7-4-6.8-4z" fill="currentColor"/></svg>
            </span>
            <span>Users</span>
          </RouterLink>

          <RouterLink
            :to="{ name: 'admin-roles' }"
            class="nav-link"
            active-class="nav-link-active"
            @click="handleNavClick"
          >
            <span class="nav-icon" aria-hidden="true">
              <!-- Shield / role icon -->
              <svg viewBox="0 0 20 20"><path d="M10 2 4 5v4c0 4.1 2.4 7.8 6 9 3.6-1.2 6-4.9 6-9V5zm0 3.2a2 2 0 0 1 2 2 2 2 0 0 1-.8 1.6l1.1 3.2H7.7l1.1-3.2A2 2 0 0 1 8 7.2a2 2 0 0 1 2-2z" fill="currentColor"/></svg>
            </span>
            <span>Roles &amp; access</span>
          </RouterLink>

          <RouterLink
            :to="{ name: 'admin-ldap' }"
            class="nav-link"
            active-class="nav-link-active"
            @click="handleNavClick"
          >
            <span class="nav-icon" aria-hidden="true">
              <!-- Network / LDAP icon -->
              <svg viewBox="0 0 20 20"><path d="M3 4h14v2H3zm0 4h14v2H3zm0 4h9v2H3zm11 0 3 3-3 3v-2H9v-2h5z" fill="currentColor"/></svg>
            </span>
            <span>LDAP</span>
          </RouterLink>
        </div>
      </template>

    </nav><!-- /sidebar-nav -->

    <!-- ══════════════════════════════════════════
         USER FOOTER — avatar, name, role, logout
         ══════════════════════════════════════════ -->
    <div class="sidebar-footer">

      <!-- User identity chip -->
      <div class="user-row">
        <!-- Avatar initials badge -->
        <div class="user-avatar" aria-hidden="true">{{ userInitials }}</div>
        <div class="user-info">
          <div class="user-name">{{ displayName }}</div>
          <span class="user-role-badge">{{ primaryRoleLabel }}</span>
        </div>
        <!-- Chevron visual cue -->
        <svg class="user-chevron" viewBox="0 0 16 16" fill="currentColor" width="13" height="13" aria-hidden="true">
          <path d="M4 6l4 4 4-4"/>
        </svg>
      </div>

      <!-- Change password — local users only -->
      <RouterLink
        v-if="isLocalUser"
        :to="{ name: 'change-password' }"
        class="nav-link"
        active-class="nav-link-active"
        @click="handleNavClick"
      >
        <span class="nav-icon" aria-hidden="true">
          <svg viewBox="0 0 20 20"><path d="M10 2a4 4 0 0 0-4 4v2H5a1 1 0 0 0-1 1v7a1 1 0 0 0 1 1h10a1 1 0 0 0 1-1V9a1 1 0 0 0-1-1h-1V6a4 4 0 0 0-4-4zm0 2a2 2 0 0 1 2 2v2H8V6a2 2 0 0 1 2-2zm0 7a1.5 1.5 0 1 1 0 3 1.5 1.5 0 0 1 0-3z" fill="currentColor"/></svg>
        </span>
        <span>Change password</span>
      </RouterLink>

      <!-- Logout button styled as a nav link for visual consistency -->
      <button
        class="nav-link nav-link-button"
        type="button"
        aria-label="Log out of CRANE"
        @click="logout"
      >
        <span class="nav-icon" aria-hidden="true">
          <!-- Arrow-right-from-bracket / logout icon -->
          <svg viewBox="0 0 20 20"><path d="M8 3H4v14h4v-2H6V5h2zm4.6 3.4L11.2 7.8 13.4 10H7v2h6.4l-2.2 2.2 1.4 1.4L17.2 11z" fill="currentColor"/></svg>
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
import AppLogo from "@/components/AppLogo.vue";

/* ── Props ───────────────────────────────────────────── */
const props = withDefaults(
  defineProps<{
    /** Controls whether the sidebar is visible on mobile.
     *  On desktop this prop has no visual effect (CSS keeps
     *  the sidebar permanently visible). */
    open?: boolean;
  }>(),
  { open: false },
);

/* ── Emits ───────────────────────────────────────────── */
const emit = defineEmits<{
  /** Fired when the user clicks a nav link or the close button
   *  on mobile — tells AppLayout to collapse the sidebar overlay. */
  close: [];
}>();

/* ── Composables ─────────────────────────────────────── */
const router    = useRouter();
const authStore = useAuthStore();

/* ── Permission gates ────────────────────────────────── */
/* Each computed checks a single permission string so the
   template stays readable. */
const canViewSecurityUpdates       = computed(() => authStore.hasPermission("security_update_read"));
const canViewLifecycleNotifications = computed(() => authStore.hasPermission("lifecycle_notification_read"));
const canViewRiskAssessments        = computed(() => authStore.hasPermission("risk_assessment_read"));
const canViewAnnexMatrix            = computed(
  () =>
    authStore.hasPermission("annex_requirement_read") ||
    authStore.hasPermission("requirement_mapping_read"),
);
const canViewCertificationRecords  = computed(() => authStore.hasPermission("certification_record_read"));
const canViewChanges               = computed(() => authStore.hasPermission("change_read"));
const canManageAdmin               = computed(() => authStore.hasPermission("admin_manage_users"));
const canViewAudit                 = computed(() => authStore.hasPermission("audit_read"));
const canViewSupportHub            = computed(() => authStore.hasPermission("lifecycle_notification_read"));
const isLocalUser                  = computed(() => authStore.user?.auth_provider === "local");

/* ── User display helpers ────────────────────────────── */

/** Human-readable role label shown under the user's name */
const primaryRoleLabel = computed(() => {
  const role = authStore.roles?.[0];
  const labels: Record<string, string> = {
    admin:                  "Admin",
    product_owner:          "Product Owner",
    cybersecurity_engineer: "Cybersecurity Engineer",
    legal_team:             "Legal Team",
    development_team:       "Development Team",
    product_management:     "Product Management",
    lifecycle_manager:      "Lifecycle Manager",
  };
  return labels[role ?? ""] ?? "User";
});

/** Full name preferred; fall back to email address */
const displayName = computed(
  () => authStore.userFullName || authStore.userEmail || "User",
);

/** Two-letter initials extracted from name or email for the avatar */
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

/* ── Actions ─────────────────────────────────────────── */

/** Close the mobile sidebar whenever any nav link is clicked */
function handleNavClick(): void {
  emit("close");
}

/** Clear auth state and redirect to the login page */
function logout(): void {
  authStore.logout();
  router.push({ name: "login" });
}
</script>

<style scoped>
/* ═══════════════════════════════════════════════
   SIDEBAR SHELL
   ═══════════════════════════════════════════════ */
.sidebar {
  /* Match --sidebar-width so AppLayout grid and sidebar element agree */
  width: var(--sidebar-width);
  padding: 1rem 0.75rem;

  /* Visual layering */
  border-right: 1px solid var(--color-border);
  background: var(--color-sidebar-bg);
  backdrop-filter: blur(14px);
  -webkit-backdrop-filter: blur(14px);

  /* Vertical layout: brand → nav (flex-grow) → footer */
  display: flex;
  flex-direction: column;
  gap: 0;

  /* Stick to the top and fill the full viewport height */
  position: sticky;
  top: 0;
  height: 100vh;

  /* Hide overflow on the shell itself — scrolling is on .sidebar-nav */
  overflow: hidden;
  box-sizing: border-box;

  transition: background var(--t-base), border-color var(--t-base);
}

/* ═══════════════════════════════════════════════
   BRAND BLOCK
   ═══════════════════════════════════════════════ */
.brand {
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 1rem 1rem 0.75rem;
  flex-shrink: 0;
}


/* ═══════════════════════════════════════════════
   NAVIGATION AREA
   ═══════════════════════════════════════════════ */
.sidebar-nav {
  flex: 1;             /* fills all space between brand and footer */
  display: flex;
  flex-direction: column;
  gap: 0;
  min-height: 0;       /* required for overflow-y to work inside a flex child */
  overflow-y: auto;    /* only the nav link area scrolls; brand and footer stay pinned */
  scrollbar-width: none;
}

.sidebar-nav::-webkit-scrollbar {
  display: none;
}

/* ── Nav groups ────────────────────────────── */
/* A group is a labelled cluster of related links */
.nav-group {
  display: flex;
  flex-direction: column;
  gap: 0.15rem;
  padding: 0.35rem 0;
}

/* Small all-caps label above a group of links */
.nav-group-label {
  margin: 0 0 0.25rem;
  padding: 0 0.5rem;
  font-size: 10.5px;
  font-weight: 700;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  color: rgba(220, 233, 214, 0.35);
}

/* Thin horizontal rule between groups */
.nav-divider {
  height: 1px;
  background: var(--color-border);
  opacity: 0.5;
  margin: 0.1rem 0.25rem;
}

/* ── Individual nav links ──────────────────── */
.nav-link {
  display: flex;
  align-items: center;
  gap: 0.65rem;
  padding: 0.6rem 0.75rem;
  border-radius: 10px;
  border: 1px solid transparent;
  font-size: var(--text-sm);
  font-weight: 500;
  color: var(--color-text-muted);
  text-decoration: none;
  white-space: nowrap;
  overflow: hidden;
  transition:
    background-color var(--t-fast),
    border-color     var(--t-fast),
    color            var(--t-fast);
}

/* <button> used for logout needs to look identical to an <a> nav link */
.nav-link-button {
  width: 100%;
  background: transparent;
  text-align: left;
  cursor: pointer;
  font-family: inherit;
}

/* Icon wrapper — fixed size so text lines up regardless of icon shape */
.nav-icon {
  width: 18px;
  height: 18px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  opacity: 0.7;
  transition: opacity var(--t-fast);
}

.nav-icon svg {
  width: 18px;
  height: 18px;
  display: block;
}

/* ── Hover state ──────────────────────────── */
.nav-link:hover {
  background: var(--color-nav-hover-bg);
  color: var(--color-text);
  border-color: var(--color-nav-hover-border);
}

.nav-link:hover .nav-icon {
  opacity: 1;
}

/* ── Active (current route) state ─────────── */
.nav-link-active {
  /* Subtle green gradient to indicate active destination */
  background: linear-gradient(
    135deg,
    rgba(112, 185, 23, 0.13),
    rgba(28, 107, 39, 0.16)
  );
  border-color: rgba(173, 214, 84, 0.22);
  color: var(--color-text);
  font-weight: 600;
  /* Left accent bar — a quick visual cue of the active state */
  box-shadow: inset 3px 0 0 var(--color-primary-2);
}

.nav-link-active .nav-icon {
  opacity: 1;
  color: var(--color-primary-2);
}

/* ═══════════════════════════════════════════════
   USER FOOTER
   ═══════════════════════════════════════════════ */
.sidebar-footer {
  flex-shrink: 0;       /* always visible — never pushed off-screen */
  display: flex;
  flex-direction: column;
  gap: 0.4rem;
  padding-top: 0.75rem;
  border-top: 1px solid rgba(233, 238, 252, 0.08);
  margin-top: auto;     /* push to the bottom of the sidebar */
}

/* Avatar + name + role row */
.user-row {
  display: flex;
  align-items: center;
  gap: 0.65rem;
  padding: 0.4rem 0.35rem;
}

/* Circular initials avatar */
.user-avatar {
  width: 32px;
  height: 32px;
  border-radius: 9px;
  background: linear-gradient(
    135deg,
    rgba(112, 185, 23, 0.22),
    rgba(28, 107, 39, 0.28)
  );
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
  min-width: 0;       /* allow text truncation */
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

.user-chevron {
  flex-shrink: 0;
  margin-left: auto;
  color: var(--color-text-muted);
  opacity: 0.5;
}

/* ═══════════════════════════════════════════════
   MOBILE BEHAVIOUR (≤ 960 px)
   ─────────────────────────────────────────────
   The sidebar becomes a fixed overlay that slides
   in from the left.  The .sidebar-open class
   (bound to the :open prop) triggers the slide.
   ═══════════════════════════════════════════════ */
@media (max-width: 960px) {
  .sidebar {
    /* Take the sidebar out of the grid flow and pin it to the viewport */
    position: fixed;
    top: 0;
    left: 0;
    height: 100vh;
    z-index: 50;           /* above the backdrop (z-index 40) */

    /* Start off-screen to the left */
    transform: translateX(-100%);
    /* Smooth slide animation matching --t-slow */
    transition: transform 0.28s cubic-bezier(0.4, 0, 0.2, 1),
                box-shadow var(--t-base);

    /* Add depth shadow when the overlay is visible */
    box-shadow: none;
  }

  /* When AppLayout binds :open="true", the sidebar slides into view */
  .sidebar.sidebar-open {
    transform: translateX(0);
    box-shadow: var(--shadow-lg);
  }
}
</style>

<!--
  Non-scoped overrides for light theme.
  These must be global because Vue scoped styles
  cannot target :root[data-theme] selectors on
  elements outside the component's own DOM.
-->
<style>
:root[data-theme="light"] .nav-group-label {
  /* CRANE Dashboard reference: muted forest green for section labels */
  color: oklch(0.48 0.07 150 / 0.5);
}

:root[data-theme="light"] .nav-divider {
  background: oklch(0.48 0.07 150 / 0.12);
}

:root[data-theme="light"] .nav-link:hover {
  background: oklch(0.48 0.092 150 / 0.07);
  border-color: oklch(0.48 0.092 150 / 0.14);
  color: oklch(0.26 0.07 150);
}

:root[data-theme="light"] .nav-link-active {
  background: oklch(0.955 0.024 150);
  border-color: oklch(0.85 0.05 150);
  color: oklch(0.26 0.07 150);
  box-shadow: inset 3px 0 0 oklch(0.48 0.092 150);
}

:root[data-theme="light"] .nav-link-active .nav-icon {
  color: oklch(0.38 0.092 150);
}

:root[data-theme="light"] .sidebar-footer {
  border-top-color: oklch(0.48 0.092 150 / 0.14);
}

:root[data-theme="light"] .user-avatar {
  background: oklch(0.955 0.024 150);
  border-color: oklch(0.85 0.05 150);
  color: oklch(0.38 0.092 150);
}
</style>
