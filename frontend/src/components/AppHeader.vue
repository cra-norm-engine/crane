<template>
  <header class="topbar">
    <div class="topbar-left">
      <div class="app-title">{{ appName }}</div>
      <div class="muted">
        Single Source of Truth for CRA compliance, releases, lifecycle evidence, and audit integrity
      </div>
    </div>

    <div class="topbar-right">
      <label class="theme-switch" aria-label="Toggle light mode">
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

      <button class="button secondary" type="button" @click="logout">
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

function logout() {
  authStore.logout();
  router.push({ name: "login" });
}
</script>

<style scoped>
.topbar {
  padding: 1rem 1.25rem;
  border-bottom: 1px solid var(--color-border-strong);
  display: flex;
  gap: 1rem;
  align-items: center;
  justify-content: space-between;
  background: var(--color-header-bg);
  position: sticky;
  top: 0;
  z-index: 10;
  backdrop-filter: blur(14px);
}

.topbar-left {
  display: grid;
  gap: 0.2rem;
}

.app-title {
  font-size: 1.1rem;
  font-weight: 800;
  letter-spacing: 0.04em;
}

.topbar-right {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  flex-wrap: wrap;
  justify-content: flex-end;
}

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
  min-width: 128px;
  padding: 0.28rem;
  border-radius: 999px;
  border: 1px solid var(--color-border);
  background: var(--color-surface-soft);
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.04);
}

.theme-switch-label {
  position: relative;
  z-index: 1;
  text-align: center;
  font-size: 0.75rem;
  font-weight: 700;
  letter-spacing: 0.04em;
  color: var(--color-text-muted);
  padding: 0.3rem 0.55rem;
  transition: color 0.18s ease;
}

.theme-switch-thumb {
  position: absolute;
  top: 0.24rem;
  bottom: 0.24rem;
  left: 0.24rem;
  width: calc(50% - 0.24rem);
  border-radius: 999px;
  background: linear-gradient(135deg, rgba(175, 214, 46, 0.95), rgba(28, 107, 39, 0.95));
  box-shadow: 0 10px 22px rgba(28, 107, 39, 0.22);
  transition: transform 0.2s ease;
}

.theme-switch-input:checked + .theme-switch-track .theme-switch-thumb {
  transform: translateX(100%);
}

.theme-switch-input:not(:checked) + .theme-switch-track .theme-switch-label-dark,
.theme-switch-input:checked + .theme-switch-track .theme-switch-label-light {
  color: #fff;
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
