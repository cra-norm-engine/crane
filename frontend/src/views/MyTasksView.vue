<template>
  <!-- Task detail drawer -->
  <TaskDrawer
    :task="drawerTask"
    @close="drawerTask = null"
    @navigate="openFullRecord"
    @status-updated="onStatusUpdated"
  />

  <section class="page">
    <!-- Page header -->
    <header class="page-header">
      <div>
        <h1 class="page-title">My Tasks</h1>
        <p class="muted page-subtitle">
          Open items assigned to you across all modules — sorted by urgency.
        </p>
      </div>
      <div class="page-actions">
        <button class="btn btn-secondary" :disabled="isLoading" @click="load">
          <svg class="btn-icon" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true">
            <path fill-rule="evenodd" d="M4 2a1 1 0 011 1v2.101a7.002 7.002 0 0111.601 2.566 1 1 0 11-1.885.666A5.002 5.002 0 005.999 7H9a1 1 0 010 2H4a1 1 0 01-1-1V3a1 1 0 011-1zm.008 9.057a1 1 0 011.276.61A5.002 5.002 0 0014.001 13H11a1 1 0 110-2h5a1 1 0 011 1v5a1 1 0 11-2 0v-2.101a7.002 7.002 0 01-11.601-2.566 1 1 0 01.61-1.276z" clip-rule="evenodd" />
          </svg>
          {{ isLoading ? "Refreshing…" : "Refresh" }}
        </button>
      </div>
    </header>

    <!-- Error banner -->
    <div v-if="loadError" class="feedback feedback-error card">{{ loadError }}</div>

    <!-- Stat row (same pattern as ChangesView) -->
    <div v-if="!isLoading" class="stat-row">
      <div class="stat-card" :class="overdueCount > 0 ? 'stat-card-alert' : ''">
        <span class="stat-value">{{ overdueCount }}</span>
        <span class="stat-label muted">Overdue</span>
      </div>
      <div class="stat-card stat-card-warn">
        <span class="stat-value">{{ dueThisWeekCount }}</span>
        <span class="stat-label muted">Due this week</span>
      </div>
      <div class="stat-card">
        <span class="stat-value">{{ tasks.length }}</span>
        <span class="stat-label muted">Total open</span>
      </div>
    </div>

    <!-- Loading state -->
    <div v-if="isLoading" class="card empty-panel">Loading your tasks…</div>

    <!-- Empty state -->
    <div v-else-if="!tasks.length && !loadError" class="card empty-panel">
      <div class="empty-icon">✓</div>
      <p class="empty-title">All caught up</p>
      <p class="muted">No open tasks are assigned to you right now.</p>
    </div>

    <!-- Task groups -->
    <template v-else>

      <!-- ── Overdue ── -->
      <section v-if="overdueTasks.length" class="card">
        <div class="section-header">
          <div class="section-header-left">
            <span class="group-dot group-dot--overdue"></span>
            <h2 class="section-title">Overdue</h2>
            <span class="count-badge count-badge--overdue">{{ overdueTasks.length }}</span>
          </div>
        </div>
        <div class="table-wrapper">
          <table class="data-table">
            <thead>
              <tr>
                <th>Type</th>
                <th>Title</th>
                <th>Product / Release</th>
                <th>Status</th>
                <th>Due</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="task in overdueTasks"
                :key="task.entity_id"
                class="table-row-clickable"
                tabindex="0"
                @click="openDrawer(task)"
                @keydown.enter="openDrawer(task)"
              >
                <td><span class="type-badge" :class="`type-${task.entity_type}`">{{ formatEntityType(task.entity_type) }}</span></td>
                <td class="task-title-cell">{{ task.title }}</td>
                <td class="muted">
                  <span v-if="task.product_name">{{ task.product_name }}</span>
                  <span v-if="task.release_version" class="muted"> · {{ task.release_version }}</span>
                  <span v-if="!task.product_name">—</span>
                </td>
                <td><span class="status-text">{{ formatStatus(task.status) }}</span></td>
                <td><span class="due-date due-date--overdue">{{ formatDate(task.due_date) }}</span></td>
                <td class="row-arrow">›</td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>

      <!-- ── Due this week ── -->
      <section v-if="dueThisWeekTasks.length" class="card">
        <div class="section-header">
          <div class="section-header-left">
            <span class="group-dot group-dot--week"></span>
            <h2 class="section-title">Due this week</h2>
            <span class="count-badge count-badge--week">{{ dueThisWeekTasks.length }}</span>
          </div>
        </div>
        <div class="table-wrapper">
          <table class="data-table">
            <thead>
              <tr>
                <th>Type</th>
                <th>Title</th>
                <th>Product / Release</th>
                <th>Status</th>
                <th>Due</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="task in dueThisWeekTasks"
                :key="task.entity_id"
                class="table-row-clickable"
                tabindex="0"
                @click="openDrawer(task)"
                @keydown.enter="openDrawer(task)"
              >
                <td><span class="type-badge" :class="`type-${task.entity_type}`">{{ formatEntityType(task.entity_type) }}</span></td>
                <td class="task-title-cell">{{ task.title }}</td>
                <td class="muted">
                  <span v-if="task.product_name">{{ task.product_name }}</span>
                  <span v-if="task.release_version" class="muted"> · {{ task.release_version }}</span>
                  <span v-if="!task.product_name">—</span>
                </td>
                <td><span class="status-text">{{ formatStatus(task.status) }}</span></td>
                <td class="muted">{{ formatDate(task.due_date) }}</td>
                <td class="row-arrow">›</td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>

      <!-- ── Upcoming ── -->
      <section v-if="upcomingTasks.length" class="card">
        <div class="section-header">
          <div class="section-header-left">
            <span class="group-dot group-dot--upcoming"></span>
            <h2 class="section-title">Upcoming</h2>
            <span class="count-badge">{{ upcomingTasks.length }}</span>
          </div>
        </div>
        <div class="table-wrapper">
          <table class="data-table">
            <thead>
              <tr>
                <th>Type</th>
                <th>Title</th>
                <th>Product / Release</th>
                <th>Status</th>
                <th>Due</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="task in upcomingTasks"
                :key="task.entity_id"
                class="table-row-clickable"
                tabindex="0"
                @click="openDrawer(task)"
                @keydown.enter="openDrawer(task)"
              >
                <td><span class="type-badge" :class="`type-${task.entity_type}`">{{ formatEntityType(task.entity_type) }}</span></td>
                <td class="task-title-cell">{{ task.title }}</td>
                <td class="muted">
                  <span v-if="task.product_name">{{ task.product_name }}</span>
                  <span v-if="task.release_version" class="muted"> · {{ task.release_version }}</span>
                  <span v-if="!task.product_name">—</span>
                </td>
                <td><span class="status-text">{{ formatStatus(task.status) }}</span></td>
                <td class="muted">{{ formatDate(task.due_date) }}</td>
                <td class="row-arrow">›</td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>

      <!-- ── No due date ── -->
      <section v-if="noDueDateTasks.length" class="card">
        <div class="section-header">
          <div class="section-header-left">
            <span class="group-dot group-dot--none"></span>
            <h2 class="section-title">No due date</h2>
            <span class="count-badge">{{ noDueDateTasks.length }}</span>
          </div>
        </div>
        <div class="table-wrapper">
          <table class="data-table">
            <thead>
              <tr>
                <th>Type</th>
                <th>Title</th>
                <th>Product / Release</th>
                <th>Status</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="task in noDueDateTasks"
                :key="task.entity_id"
                class="table-row-clickable"
                tabindex="0"
                @click="openDrawer(task)"
                @keydown.enter="openDrawer(task)"
              >
                <td><span class="type-badge" :class="`type-${task.entity_type}`">{{ formatEntityType(task.entity_type) }}</span></td>
                <td class="task-title-cell">{{ task.title }}</td>
                <td class="muted">
                  <span v-if="task.product_name">{{ task.product_name }}</span>
                  <span v-if="task.release_version" class="muted"> · {{ task.release_version }}</span>
                  <span v-if="!task.product_name">—</span>
                </td>
                <td><span class="status-text">{{ formatStatus(task.status) }}</span></td>
                <td class="row-arrow">›</td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>

    </template>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { useRouter } from "vue-router";

import TaskDrawer from "@/components/TaskDrawer.vue";
import { taskService } from "@/services/task-service";
import type { TaskItem } from "@/types/task";

const tasks = ref<TaskItem[]>([]);
const isLoading = ref(false);
const loadError = ref<string | null>(null);
const router = useRouter();

// ── Drawer ────────────────────────────────────────────────────────────────────
const drawerTask = ref<TaskItem | null>(null);

function openDrawer(task: TaskItem): void {
  drawerTask.value = task;
}

function onStatusUpdated(task: TaskItem, newStatus: string): void {
  const idx = tasks.value.findIndex((t) => t.entity_id === task.entity_id);
  if (idx !== -1) tasks.value[idx] = { ...tasks.value[idx], status: newStatus };
  // Remove from list if it moved to a terminal status
  const terminal = new Set(["mitigated", "accepted", "closed", "disclosed", "retired"]);
  if (terminal.has(newStatus)) {
    tasks.value.splice(idx, 1);
    drawerTask.value = null;
  }
}

function openFullRecord(task: TaskItem): void {
  drawerTask.value = null;
  navigateToTask(task);
}

async function load(): Promise<void> {
  isLoading.value = true;
  loadError.value = null;
  try {
    tasks.value = await taskService.listMyTasks();
  } catch {
    loadError.value = "Failed to load tasks. Please try again.";
  } finally {
    isLoading.value = false;
  }
}

onMounted(load);

// ── Date helpers ──────────────────────────────────────────────────────────────
function endOfWeek(): Date {
  const d = new Date();
  d.setHours(23, 59, 59, 999);
  d.setDate(d.getDate() + (6 - d.getDay()));
  return d;
}

// ── Computed groups ───────────────────────────────────────────────────────────
const overdueTasks      = computed(() => tasks.value.filter((t) => t.is_overdue));
const dueThisWeekTasks  = computed(() => {
  const eow   = endOfWeek();
  const today = new Date(); today.setHours(0, 0, 0, 0);
  return tasks.value.filter((t) => {
    if (t.is_overdue || !t.due_date) return false;
    const d = new Date(t.due_date);
    return d >= today && d <= eow;
  });
});
const upcomingTasks    = computed(() => {
  const eow = endOfWeek();
  return tasks.value.filter((t) => !t.is_overdue && !!t.due_date && new Date(t.due_date) > eow);
});
const noDueDateTasks   = computed(() => tasks.value.filter((t) => !t.due_date && !t.is_overdue));

const overdueCount     = computed(() => overdueTasks.value.length);
const dueThisWeekCount = computed(() => dueThisWeekTasks.value.length);

// ── Navigation ────────────────────────────────────────────────────────────────
function navigateToTask(task: TaskItem): void {
  switch (task.entity_type) {
    case "vulnerability_report":
      router.push({ name: "vulnerability-handling" });
      break;
    case "change":
      router.push({ name: "change-detail", params: { id: task.entity_id } });
      break;
    case "release_gate_item":
      if (task.parent_id) {
        router.push({ name: "release-gate", params: { releaseId: task.parent_id } });
      } else {
        router.push({ name: "products" });
      }
      break;
    case "risk_item":
      if (task.parent_id) {
        router.push({ name: "risk-assessment-detail", params: { assessmentId: task.parent_id } });
      } else {
        router.push({ name: "risk-assessments" });
      }
      break;
  }
}

// ── Formatters ────────────────────────────────────────────────────────────────
function formatEntityType(type: string): string {
  const map: Record<string, string> = {
    vulnerability_report: "Vulnerability",
    change:              "Change",
    release_gate_item:   "Gate item",
    risk_item:           "Risk item",
  };
  return map[type] ?? type;
}

function formatStatus(status: string): string {
  return status.replace(/_/g, " ");
}

function formatDate(iso: string | null): string {
  if (!iso) return "—";
  return new Date(iso).toLocaleDateString(undefined, { dateStyle: "medium" });
}
</script>

<style scoped>
/* ── Layout ─────────────────────────────────────────────────────────────────── */
.page {
  display: grid;
  gap: 1rem;
}

.page-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 1rem;
  flex-wrap: wrap;
}

.page-title  { margin: 0; }
.page-subtitle { margin-top: 0.35rem; }

.page-actions {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

/* ── Buttons ─────────────────────────────────────────────────────────────────── */
.btn {
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
  padding: 0.55rem 1rem;
  border-radius: 8px;
  font-size: 0.88rem;
  font-weight: 600;
  cursor: pointer;
  border: 1px solid transparent;
  transition: opacity 0.12s, background 0.12s, border-color 0.12s;
  white-space: nowrap;
}

.btn:disabled { opacity: 0.55; cursor: not-allowed; }

.btn-secondary {
  background: var(--color-surface-elevated, rgba(255,255,255,0.06));
  border-color: var(--color-border, rgba(148,163,184,0.2));
  color: var(--color-text, #e2e8f0);
}

.btn-secondary:not(:disabled):hover {
  background: var(--color-surface-alt, rgba(255,255,255,0.1));
}

.btn-icon {
  width: 1rem;
  height: 1rem;
  flex-shrink: 0;
}

/* ── Stat row (mirrors ChangesView exactly) ────────────────────────────────── */
.stat-row {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 0.75rem;
}

.stat-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 0.25rem;
  padding: 1rem;
  border-radius: 1rem;
  border: 1px solid var(--color-border, rgba(148, 163, 184, 0.2));
  background: var(--color-surface-soft, rgba(15, 23, 42, 0.4));
  text-align: center;
}

.stat-value {
  font-size: 2rem;
  font-weight: 700;
  line-height: 1;
}

.stat-label { font-size: 0.8rem; }

.stat-card-warn  .stat-value { color: #fbbf24; }
.stat-card-alert .stat-value { color: #f87171; }

/* ── Empty state ────────────────────────────────────────────────────────────── */
.empty-panel {
  padding: 3rem 2rem;
  text-align: center;
  color: var(--color-text-muted, #94a3b8);
}

.empty-icon {
  font-size: 2.5rem;
  margin-bottom: 0.5rem;
  color: #4ade80;
}

.empty-title {
  font-size: 1.1rem;
  font-weight: 700;
  color: var(--color-text, #e2e8f0);
  margin: 0 0 0.4rem;
}

/* ── Feedback ────────────────────────────────────────────────────────────────── */
.feedback { padding: 1rem 1.1rem; border-radius: 1rem; }
.feedback-error { color: #fda4af; }

/* ── Section header ─────────────────────────────────────────────────────────── */
.section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 1rem;
}

.section-header-left {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.section-title {
  margin: 0;
  font-size: 0.85rem;
  font-weight: 700;
  letter-spacing: 0.05em;
  text-transform: uppercase;
  color: var(--color-text, #e2e8f0);
}

/* Coloured dot before section title */
.group-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  flex-shrink: 0;
  background: var(--color-text-muted, #94a3b8);
}

.group-dot--overdue  { background: #f87171; }
.group-dot--week     { background: #fbbf24; }
.group-dot--upcoming { background: #60a5fa; }
.group-dot--none     { background: var(--color-text-muted, #94a3b8); }

/* Count pill next to section title */
.count-badge {
  font-size: 0.72rem;
  font-weight: 700;
  padding: 0.1rem 0.5rem;
  border-radius: 999px;
  background: var(--color-surface-elevated, rgba(255,255,255,0.08));
  color: var(--color-text-muted, #94a3b8);
  border: 1px solid var(--color-border, rgba(148,163,184,0.15));
}

.count-badge--overdue { background: rgba(248,113,113,0.15); color: #f87171; border-color: rgba(248,113,113,0.25); }
.count-badge--week    { background: rgba(251,191,36,0.12);  color: #fbbf24; border-color: rgba(251,191,36,0.25); }

/* ── Table (identical to ChangesView) ──────────────────────────────────────── */
.table-wrapper { overflow-x: auto; }

.data-table {
  width: 100%;
  border-collapse: collapse;
}

.data-table th,
.data-table td {
  padding: 0.85rem 0.75rem;
  text-align: left;
  border-bottom: 1px solid var(--color-border, rgba(148, 163, 184, 0.15));
  vertical-align: middle;
}

.data-table th {
  color: var(--color-text-muted, #94a3b8);
  font-size: 0.82rem;
  font-weight: 600;
  white-space: nowrap;
}

.data-table tbody tr:last-child td { border-bottom: none; }

.table-row-clickable {
  cursor: pointer;
  transition: background 0.13s;
}

.table-row-clickable:hover {
  background: var(--color-surface-elevated, rgba(255, 255, 255, 0.04));
}

.table-row-clickable:focus-visible {
  outline: 2px solid var(--color-primary, #6ea8fe);
  outline-offset: -2px;
}

.row-arrow {
  color: var(--color-text-muted, #94a3b8);
  text-align: right;
  font-size: 1.1rem;
}

/* ── Task title ─────────────────────────────────────────────────────────────── */
.task-title-cell {
  font-weight: 600;
  max-width: 20rem;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

/* ── Status text ────────────────────────────────────────────────────────────── */
.status-text {
  font-size: 0.82rem;
  text-transform: capitalize;
  color: var(--color-text-muted, #94a3b8);
}

/* ── Due date ───────────────────────────────────────────────────────────────── */
.due-date { font-size: 0.82rem; }
.due-date--overdue { color: #f87171; font-weight: 600; }

/* ── Entity type badges ─────────────────────────────────────────────────────── */
.type-badge {
  font-size: 0.7rem;
  font-weight: 700;
  padding: 0.18rem 0.5rem;
  border-radius: 4px;
  white-space: nowrap;
}

.type-vulnerability_report { background: rgba(220,38,38,0.15);  color: #fca5a5; }
.type-change               { background: rgba(37,99,235,0.15);  color: #93c5fd; }
.type-release_gate_item    { background: rgba(22,163,74,0.15);  color: #86efac; }
.type-risk_item            { background: rgba(217,119,6,0.15);  color: #fcd34d; }

</style>
