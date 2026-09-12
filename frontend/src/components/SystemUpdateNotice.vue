<!-- CRANE — CRA Norm Engine — SPDX-License-Identifier: AGPL-3.0-or-later -->
<template>
  <aside v-if="visible" class="update-notice" :class="`severity-${status!.manifest!.severity}`" role="status">
    <div>
      <strong>{{ status!.manifest!.update_type === "security" ? "Security update" : "CRANE update" }} {{ status!.manifest!.version }} is available</strong>
      <span>Installed: {{ status!.installed_version }} · {{ updateMessage }}</span>
    </div>
    <RouterLink to="/settings#system-updates">Review update</RouterLink>
  </aside>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { RouterLink } from "vue-router";
import { adminService } from "@/services/admin-service";
import { useAuthStore } from "@/stores/auth";
import type { SystemUpdateStatus } from "@/types/admin";

const auth = useAuthStore();
const status = ref<SystemUpdateStatus | null>(null);
const visible = computed(() => {
  if (!auth.hasPermission("admin_manage_users") || !status.value?.update_available) return false;
  const postponed = status.value.policy.postponed_until;
  return status.value.manifest?.severity === "critical" || !postponed || new Date(postponed) <= new Date();
});
const updateMessage = computed(() => {
  const manifest = status.value?.manifest;
  if (!manifest) return "";
  return manifest.update_type === "security"
    ? `${manifest.severity.toUpperCase()} severity; review without delay.`
    : "Review compatibility and release notes.";
});

onMounted(async () => {
  if (!auth.hasPermission("admin_manage_users")) return;
  try { status.value = await adminService.getSystemUpdates(); } catch { /* Settings shows diagnostics. */ }
});
</script>

<style scoped>
.update-notice { margin: .75rem 2rem 0; padding: .8rem 1rem; border: 1px solid var(--color-border); border-radius: var(--radius-md); background: var(--color-surface-elevated); display: flex; align-items: center; justify-content: space-between; gap: 1rem; }
.update-notice div { display: grid; gap: .2rem; }
.update-notice span { color: var(--color-text-muted); font-size: var(--text-sm); }
.update-notice a { white-space: nowrap; font-weight: 650; }
.severity-high, .severity-critical { border-color: var(--color-danger); }
@media (max-width: 700px) { .update-notice { margin: .75rem 1.25rem 0; align-items: flex-start; flex-direction: column; } }
</style>
