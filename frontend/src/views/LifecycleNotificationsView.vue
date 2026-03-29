<template>
  <section class="page">
    <header class="page-header card">
      <div>
        <h1 class="page-title">Lifecycle notifications</h1>
        <p class="muted page-subtitle">
          Review approaching end-of-support alerts and manage in-app notification state.
        </p>
      </div>

      <div class="page-actions">
        <select v-model="statusFilter">
          <option value="">All statuses</option>
          <option value="pending">Pending</option>
          <option value="sent">Sent</option>
          <option value="dismissed">Dismissed</option>
        </select>

        <button class="btn btn-secondary" type="button" @click="loadNotifications" :disabled="isLoading">
          {{ isLoading ? "Refreshing..." : "Refresh" }}
        </button>

        <button class="btn btn-primary" type="button" @click="runScheduler" :disabled="isRunningScheduler">
          {{ isRunningScheduler ? "Running..." : "Run EOS check" }}
        </button>
      </div>
    </header>

    <div v-if="errorMessage" class="card feedback feedback-error">
      {{ errorMessage }}
    </div>

    <div v-if="successMessage" class="card feedback feedback-success">
      {{ successMessage }}
    </div>

    <section class="card">
      <div class="section-header">
        <div>
          <h2 class="section-title">Alerts</h2>
          <p class="muted">{{ notifications.length }} notification(s)</p>
        </div>
      </div>

      <div v-if="isLoading" class="empty-panel">
        Loading lifecycle notifications…
      </div>

      <div v-else-if="notifications.length === 0" class="empty-panel">
        No lifecycle notifications found.
      </div>

      <div v-else class="table-wrapper">
        <table class="data-table">
          <thead>
            <tr>
              <th>Type</th>
              <th>Status</th>
              <th>Scheduled</th>
              <th>Message</th>
              <th>Actions</th>
            </tr>
          </thead>

          <tbody>
            <tr v-for="notification in notifications" :key="notification.id">
              <td>{{ formatNotificationType(notification.notification_type) }}</td>
              <td>
                <span class="badge" :class="statusClass(notification.status)">
                  {{ formatStatus(notification.status) }}
                </span>
              </td>
              <td>{{ formatDateTime(notification.scheduled_for) }}</td>
              <td class="message-cell">
                <strong>{{ notification.title }}</strong>
                <p>{{ notification.message }}</p>
              </td>
              <td>
                <div class="table-actions">
                  <button
                    v-if="notification.status === 'pending'"
                    class="btn btn-secondary btn-small"
                    type="button"
                    @click="markSent(notification.id)"
                  >
                    Mark sent
                  </button>
                  <button
                    v-if="notification.status === 'pending'"
                    class="btn btn-secondary btn-small"
                    type="button"
                    @click="dismiss(notification.id)"
                  >
                    Dismiss
                  </button>
                  <span v-if="notification.status !== 'pending'" class="muted">No actions</span>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>
  </section>
</template>

<script setup lang="ts">
import { ref, watch } from "vue";

import { lifecycleNotificationService } from "@/services/lifecycle-notification-service";
import type { LifecycleNotificationRead, LifecycleNotificationStatus } from "@/types/product";

const notifications = ref<LifecycleNotificationRead[]>([]);
const isLoading = ref(false);
const isRunningScheduler = ref(false);
const errorMessage = ref("");
const successMessage = ref("");
const statusFilter = ref<"" | LifecycleNotificationStatus>("");

function formatNotificationType(value: string): string {
  return value.replaceAll("_", " ");
}

function formatStatus(value: string): string {
  return value.replaceAll("_", " ");
}

function statusClass(value: string): string {
  switch (value) {
    case "pending":
      return "badge-warning";
    case "sent":
      return "badge-success";
    case "dismissed":
      return "badge-neutral";
    default:
      return "badge-neutral";
  }
}

function formatDateTime(value: string): string {
  return new Intl.DateTimeFormat(undefined, {
    year: "numeric",
    month: "short",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  }).format(new Date(value));
}

async function loadNotifications(): Promise<void> {
  isLoading.value = true;
  errorMessage.value = "";

  try {
    notifications.value = await lifecycleNotificationService.list(
      statusFilter.value ? { status: statusFilter.value } : undefined,
    );
  } catch (error) {
    errorMessage.value =
      error instanceof Error ? error.message : "Failed to load lifecycle notifications.";
  } finally {
    isLoading.value = false;
  }
}

async function runScheduler(): Promise<void> {
  isRunningScheduler.value = true;
  errorMessage.value = "";
  successMessage.value = "";

  try {
    const created = await lifecycleNotificationService.scheduleEosCheck();
    successMessage.value = `EOS check completed. ${created.length} notification(s) created.`;
    await loadNotifications();
  } catch (error) {
    errorMessage.value =
      error instanceof Error ? error.message : "Failed to run EOS scheduling check.";
  } finally {
    isRunningScheduler.value = false;
  }
}

async function markSent(notificationId: string): Promise<void> {
  errorMessage.value = "";
  successMessage.value = "";

  try {
    await lifecycleNotificationService.markSent(notificationId);
    successMessage.value = "Notification marked as sent.";
    await loadNotifications();
  } catch (error) {
    errorMessage.value =
      error instanceof Error ? error.message : "Failed to mark notification as sent.";
  }
}

async function dismiss(notificationId: string): Promise<void> {
  errorMessage.value = "";
  successMessage.value = "";

  try {
    await lifecycleNotificationService.dismiss(notificationId);
    successMessage.value = "Notification dismissed.";
    await loadNotifications();
  } catch (error) {
    errorMessage.value =
      error instanceof Error ? error.message : "Failed to dismiss notification.";
  }
}

watch(statusFilter, () => {
  void loadNotifications();
}, { immediate: true });
</script>

<style scoped>
.page {
  display: grid;
  gap: 1rem;
}

.page-header,
.section-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 1rem;
  flex-wrap: wrap;
}

.page-actions {
  display: flex;
  gap: 0.75rem;
  flex-wrap: wrap;
  align-items: center;
}

.page-title,
.section-title {
  margin: 0;
}

.page-subtitle {
  margin-top: 0.35rem;
}

.feedback,
.empty-panel {
  padding: 1rem 1.1rem;
  border-radius: 1rem;
  background: var(--color-surface-soft, rgba(15, 23, 42, 0.45));
}

.feedback-error {
  color: #fda4af;
}

.feedback-success {
  color: #86efac;
}

.table-wrapper {
  overflow-x: auto;
}

.data-table {
  width: 100%;
  border-collapse: collapse;
}

.data-table th,
.data-table td {
  padding: 0.85rem 0.75rem;
  text-align: left;
  border-bottom: 1px solid var(--color-border, rgba(148, 163, 184, 0.18));
  vertical-align: top;
}

.data-table th {
  color: var(--color-text-muted, #94a3b8);
  font-size: 0.85rem;
  font-weight: 600;
  white-space: nowrap;
}

.message-cell p {
  margin: 0.35rem 0 0;
  line-height: 1.5;
}

.table-actions {
  display: flex;
  gap: 0.5rem;
  flex-wrap: wrap;
}

.badge {
  display: inline-flex;
  align-items: center;
  border-radius: 999px;
  padding: 0.35rem 0.65rem;
  font-size: 0.75rem;
  font-weight: 600;
}

.badge-neutral {
  background: rgba(148, 163, 184, 0.15);
  color: #cbd5e1;
}

.badge-success {
  background: rgba(52, 211, 153, 0.15);
  color: #86efac;
}

.badge-warning {
  background: rgba(251, 191, 36, 0.15);
  color: #fde68a;
}

.btn {
  border: 1px solid transparent;
  border-radius: 0.85rem;
  padding: 0.75rem 1rem;
  font: inherit;
  cursor: pointer;
}

.btn-small {
  padding: 0.5rem 0.7rem;
}

.btn-primary {
  background: linear-gradient(135deg, #8b5cf6, #6ea8fe);
  color: white;
}

.btn-secondary {
  background: transparent;
  border-color: var(--color-border, rgba(148, 163, 184, 0.25));
  color: inherit;
}

.muted {
  color: var(--color-text-muted, #94a3b8);
}
</style>