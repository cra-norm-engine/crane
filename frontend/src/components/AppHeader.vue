<template>
  <header class="topbar">
    <div class="topbar-left">
      <div class="topbar-greeting">{{ greeting }}, <strong>{{ firstName }}</strong></div>
      <div class="topbar-meta muted">{{ appName }} &mdash; CRA Norm Engine</div>
    </div>

    <div class="topbar-right">
      <label class="theme-switch" :aria-label="`Switch to ${isLightMode ? 'dark' : 'light'} mode`">
        <input
          :checked="isLightMode"
          type="checkbox"
          class="theme-switch-input"
          @change="appStore.toggleTheme()"
        />
        <span class="theme-switch-track">
          <span class="theme-switch-label theme-switch-label-dark">Dark</span>
          <span class="theme-switch-thumb" />
          <span class="theme-switch-label theme-switch-label-light">Light</span>
        </span>
      </label>

      <button class="button secondary topbar-signout" type="button" @click="logout">
        Sign out
      </button>
    </div>
  </header>
</template>

<script setup lang="ts">
import { computed } from "vue";
import { useRouter } from "vue-router";

import { useAppStore } from "@/stores/app";
import { useAuthStore } from "@/stores/auth";

const router = useRouter();
const appStore = useAppStore();
const authStore = useAuthStore();

const appName = computed(() => appStore.appName);
const isLightMode = computed(() => appStore.themeMode === "light");

const firstName = computed(() => {
  const full = authStore.userFullName || authStore.userEmail || "there";
  return full.split(/[\s@]/)[0] ?? "there";
});

const greeting = computed(() => {
  const h = new Date().getHours();
  if (h < 12) return "Good morning";
  if (h < 17) return "Good afternoon";
  return "Good evening";
});

function logout() {
  authStore.logout();
  router.push({ name: "login" });
}
</script>

<style scoped>
.topbar {
  padding: 0.9rem 1.5rem;
  border-bottom: 1px solid var(--color-border);
  display: flex;
  gap: 1rem;
  align-items: center;
  justify-content: space-between;
  background: var(--color-header-bg);
  position: sticky;
  top: 0;
  z-index: 10;
  backdrop-filter: blur(16px);
}

.topbar-left {
  display: grid;
  gap: 0.15rem;
  min-width: 0;
}

.topbar-greeting {
  font-size: 0.95rem;
  font-weight: 500;
  color: var(--color-text-muted);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.topbar-greeting strong {
  color: var(--color-text);
  font-weight: 700;
}

.topbar-meta {
  font-size: 0.78rem;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.topbar-right {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  flex-shrink: 0;
}

/* ── Theme switch ────────────────────────────── */
.theme-switch {
  display: inline-flex;
  align-items: center;
  cursor: pointer;
}

.theme-switch-input {
  position: absolute;
  opacity: 0;
  pointer-events: none;
}

.theme-switch-track {
  position: relative;
  display: inline-grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  align-items: center;
  min-width: 124px;
  padding: 0.26rem;
  border-radius: 999px;
  border: 1px solid var(--color-border);
  background: var(--color-surface-soft);
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.04);
}

.theme-switch-label {
  position: relative;
  z-index: 1;
  text-align: center;
  font-size: 0.72rem;
  font-weight: 700;
  letter-spacing: 0.05em;
  color: var(--color-text-muted);
  padding: 0.28rem 0.5rem;
  transition: color 0.18s ease;
  user-select: none;
}

.theme-switch-thumb {
  position: absolute;
  top: 0.22rem;
  bottom: 0.22rem;
  left: 0.22rem;
  width: calc(50% - 0.22rem);
  border-radius: 999px;
  background: linear-gradient(135deg, rgba(175, 214, 46, 0.95), rgba(28, 107, 39, 0.95));
  box-shadow: 0 8px 20px rgba(28, 107, 39, 0.24);
  transition: transform 0.2s cubic-bezier(0.4, 0, 0.2, 1);
}

.theme-switch-input:checked + .theme-switch-track .theme-switch-thumb {
  transform: translateX(100%);
}

.theme-switch-input:not(:checked) + .theme-switch-track .theme-switch-label-dark,
.theme-switch-input:checked + .theme-switch-track .theme-switch-label-light {
  color: #fff;
}

/* ── Sign out ────────────────────────────────── */
.topbar-signout {
  font-size: 0.88rem;
  padding: 0.62rem 1rem;
}

@media (max-width: 720px) {
  .topbar {
    align-items: flex-start;
    flex-direction: column;
    gap: 0.75rem;
  }

  .topbar-right {
    width: 100%;
    justify-content: space-between;
  }
}
</style>
