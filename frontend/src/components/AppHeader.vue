<template>
  <header class="topbar">
    <div class="topbar-left">
      <div class="app-title">{{ appName }}</div>
      <div class="muted">
        CRA inventory, scope evaluation, releases, lifecycle support, security updates, and audit readiness
      </div>
    </div>

    <div class="topbar-right">
      <RouterLink
        v-if="canViewLifecycleNotifications"
        :to="{ name: 'lifecycle-notifications' }"
        class="button secondary nav-shortcut"
      >
        Lifecycle alerts
      </RouterLink>

      <RouterLink
        v-if="canViewSecurityUpdates"
        :to="{ name: 'security-updates' }"
        class="button secondary nav-shortcut"
      >
        Security updates
      </RouterLink>

      <span class="badge">
        Signed in as
        <strong class="badge-strong">{{ authStore.userEmail || "anonymous" }}</strong>
      </span>

      <button class="button secondary" type="button" @click="logout">
        Sign out
      </button>
    </div>
  </header>
</template>

<script setup lang="ts">
import { computed } from "vue";
import { RouterLink, useRouter } from "vue-router";

import { useAppStore } from "@/stores/app";
import { useAuthStore } from "@/stores/auth";

const router = useRouter();
const appStore = useAppStore();
const authStore = useAuthStore();

const appName = computed(() => appStore.appName);

const canViewLifecycleNotifications = computed(() =>
  authStore.hasPermission("lifecycle_notification_read"),
);

const canViewSecurityUpdates = computed(() =>
  authStore.hasPermission("security_update_read"),
);

function logout() {
  authStore.logout();
  router.push({ name: "login" });
}
</script>

<style scoped>
.topbar {
  padding: 1rem 1.25rem;
  border-bottom: 1px solid rgba(233, 238, 252, 0.1);
  display: flex;
  gap: 1rem;
  align-items: center;
  justify-content: space-between;
  background: rgba(11, 18, 32, 0.35);
  position: sticky;
  top: 0;
  z-index: 10;
  backdrop-filter: blur(12px);
}

.topbar-left {
  display: grid;
  gap: 0.2rem;
}

.app-title {
  font-size: 1.1rem;
  font-weight: 800;
}

.topbar-right {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  flex-wrap: wrap;
  justify-content: flex-end;
}

.nav-shortcut {
  text-decoration: none;
}

.badge-strong {
  margin-left: 0.35rem;
  color: var(--color-text);
}

@media (max-width: 720px) {
  .topbar {
    align-items: flex-start;
    flex-direction: column;
  }

  .topbar-right {
    width: 100%;
    justify-content: space-between;
  }
}
</style>