<template>
  <header class="card" style="display: flex; align-items: center; justify-content: space-between; gap: 1rem;">
    <div>
      <div style="font-size: 1.2rem; font-weight: 700;">{{ appName }}</div>
      <div class="muted">Self-hosted CRA compliance management</div>
    </div>

    <div style="display: flex; align-items: center; gap: 0.75rem;">
      <div class="muted">{{ authStore.userEmail || "anonymous" }}</div>
      <button class="button secondary" type="button" @click="logout">
        Sign out
      </button>
    </div>
  </header>
</template>

<script setup lang="ts">
import { useRouter } from "vue-router";

import { useAppStore } from "@/stores/app";
import { useAuthStore } from "@/stores/auth";

const router = useRouter();
const appStore = useAppStore();
const authStore = useAuthStore();

const appName = appStore.appName;

function logout() {
  authStore.logout();
  router.push({ name: "login" });
}
</script>