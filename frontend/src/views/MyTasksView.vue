<template>
  <!-- Task detail drawer -->
  <TaskDrawer
    :task="drawerTask"
    @close="drawerTask = null"
    @navigate="openFullRecord"
    @status-updated="onStatusUpdated"
  />

  <section class="tasks-page">

    <!-- ── Page head ─────────────────────────────────────────────────────── -->
    <div class="page-head">
      <div>
        <h1 class="page-title">My Tasks</h1>
        <p class="page-sub">Open items assigned to you across all modules — sorted by urgency.</p>
      </div>
      <div class="head-actions">
        <button class="hbtn" :disabled="isLoading" @click="load">
          <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.7" width="14" height="14" stroke-linecap="round" stroke-linejoin="round">
            <path d="M4 4v4h4"/><path d="M4 8a7 7 0 1 0 1.4-4.1"/>
          </svg>
          {{ isLoading ? "Refreshing…" : "Refresh" }}
        </button>
      </div>
    </div>

    <!-- ── Error ──────────────────────────────────────────────────────────── -->
    <div v-if="loadError" class="hub-error">
      <svg viewBox="0 0 20 20" fill="currentColor" width="15" height="15"><path fill-rule="evenodd" d="M8.485 2.495c.673-1.167 2.357-1.167 3.03 0l6.28 10.875c.673 1.167-.17 2.625-1.516 2.625H3.72c-1.347 0-2.189-1.458-1.515-2.625L8.485 2.495zM10 5a.75.75 0 0 1 .75.75v3.5a.75.75 0 0 1-1.5 0v-3.5A.75.75 0 0 1 10 5zm0 9a1 1 0 1 0 0-2 1 1 0 0 0 0 2z" clip-rule="evenodd"/></svg>
      {{ loadError }}
    </div>

    <!-- ── Summary filter cards ───────────────────────────────────────────── -->
    <div v-if="!isLoading" class="summary-grid">

      <!-- Overdue -->
      <div
        class="sum-card"
        :class="[overdueCount === 0 ? 'sum-overdue-ok' : 'sum-overdue', activeFilter === 'overdue' ? 'sum-active' : '']"
        @click="toggleFilter('overdue')"
      >
        <div class="sum-ic">
          <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.8" width="20" height="20" stroke-linecap="round" stroke-linejoin="round">
            <path v-if="overdueCount === 0" d="M3 10.5l4.5 4.5 9.5-9"/>
            <template v-else>
              <path d="M10 5.75v3.5"/><circle cx="10" cy="12.5" r=".75" fill="currentColor" stroke="none"/>
              <circle cx="10" cy="10" r="7.5"/>
            </template>
          </svg>
        </div>
        <div class="sum-body">
          <div class="sum-num">{{ overdueCount }}</div>
          <div class="sum-label">{{ overdueCount === 0 ? "Overdue — you're caught up" : "Overdue" }}</div>
        </div>
        <svg v-if="overdueCount > 0" class="sum-arrow" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" width="14" height="14" stroke-linecap="round"><path d="M6 4l4 4-4 4"/></svg>
      </div>

      <!-- Due this week -->
      <div
        class="sum-card sum-week"
        :class="activeFilter === 'week' ? 'sum-active' : ''"
        @click="toggleFilter('week')"
      >
        <div class="sum-ic">
          <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.8" width="20" height="20" stroke-linecap="round" stroke-linejoin="round">
            <circle cx="10" cy="10" r="7.5"/><path d="M10 6v4.5l2.5 1.5"/>
          </svg>
        </div>
        <div class="sum-body">
          <div class="sum-num">{{ dueThisWeekCount }}</div>
          <div class="sum-label">Due this week</div>
        </div>
        <svg class="sum-arrow" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" width="14" height="14" stroke-linecap="round"><path d="M6 4l4 4-4 4"/></svg>
      </div>

      <!-- Total open -->
      <div
        class="sum-card sum-open"
        :class="activeFilter === 'all' ? 'sum-active' : ''"
        @click="toggleFilter('all')"
      >
        <div class="sum-ic">
          <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.8" width="20" height="20" stroke-linecap="round" stroke-linejoin="round">
            <path d="M4 10.5l3.5 3.5 8.5-8.5"/><rect x="2.5" y="2.5" width="15" height="15" rx="2"/>
          </svg>
        </div>
        <div class="sum-body">
          <div class="sum-num">{{ tasks.length }}</div>
          <div class="sum-label">Total open</div>
        </div>
        <svg class="sum-arrow" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" width="14" height="14" stroke-linecap="round"><path d="M6 4l4 4-4 4"/></svg>
      </div>

    </div>

    <!-- ── Loading ────────────────────────────────────────────────────────── -->
    <div v-if="isLoading" class="empty-panel">Loading your tasks…</div>

    <!-- ── Empty ──────────────────────────────────────────────────────────── -->
    <div v-else-if="!tasks.length && !loadError" class="empty-panel">
      <div class="empty-ic">
        <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.8" width="20" height="20" stroke-linecap="round"><path d="M3 10.5l4.5 4.5 9.5-9"/></svg>
      </div>
      <p class="empty-title">All caught up</p>
      <p class="empty-sub">No open tasks assigned to you right now.</p>
    </div>

    <!-- ── Task groups ────────────────────────────────────────────────────── -->
    <template v-else>

      <!-- Overdue -->
      <div v-if="visibleOverdue.length" class="group">
        <div class="group-head">
          <span class="gdot gdot-overdue"></span>
          <span class="gtitle">Overdue</span>
          <span class="gcount gcount-overdue">{{ visibleOverdue.length }}</span>
          <span class="gline"></span>
        </div>
        <div class="task-list">
          <div class="col-head">
            <div>Type</div><div>Title</div><div>Product / Release</div><div>Status</div><div>Due</div><div></div>
          </div>
          <div
            v-for="task in visibleOverdue" :key="task.entity_id"
            class="task-row prio-high"
            tabindex="0"
            @click="openDrawer(task)"
            @keydown.enter="openDrawer(task)"
          >
            <div><span class="type-pill" :class="`tp-${task.entity_type}`">
              <TypeIcon :type="task.entity_type" />
              {{ formatEntityType(task.entity_type) }}
            </span></div>
            <div class="tt-wrap">
              <div class="tt-main">{{ task.title }}</div>
              <div v-if="task.product_name" class="tt-sub">{{ task.product_name }}<template v-if="task.release_version"> · {{ task.release_version }}</template></div>
            </div>
            <div class="prod-cell">
              <div class="prod-mark">{{ productInitials(task.product_name) }}</div>
              <div class="prod-name">{{ task.product_name || '—' }}</div>
            </div>
            <div><StatusPill :status="task.status" /></div>
            <div class="due-cell">
              <span class="due-date due-overdue">{{ formatDate(task.due_date) }}</span>
              <span class="due-rel due-urgent">{{ relativeDue(task.due_date) }}</span>
            </div>
            <button class="row-go" aria-label="Open">
              <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" width="13" height="13" stroke-linecap="round"><path d="M6 4l4 4-4 4"/></svg>
            </button>
          </div>
        </div>
      </div>

      <!-- Due this week -->
      <div v-if="visibleWeek.length" class="group">
        <div class="group-head">
          <span class="gdot gdot-week"></span>
          <span class="gtitle">Due this week</span>
          <span class="gcount gcount-week">{{ visibleWeek.length }}</span>
          <span class="gline"></span>
        </div>
        <div class="task-list">
          <div class="col-head">
            <div>Type</div><div>Title</div><div>Product / Release</div><div>Status</div><div>Due</div><div></div>
          </div>
          <div
            v-for="task in visibleWeek" :key="task.entity_id"
            class="task-row prio-med"
            tabindex="0"
            @click="openDrawer(task)"
            @keydown.enter="openDrawer(task)"
          >
            <div><span class="type-pill" :class="`tp-${task.entity_type}`">
              <TypeIcon :type="task.entity_type" />
              {{ formatEntityType(task.entity_type) }}
            </span></div>
            <div class="tt-wrap">
              <div class="tt-main">{{ task.title }}</div>
              <div v-if="task.product_name" class="tt-sub">{{ task.product_name }}<template v-if="task.release_version"> · {{ task.release_version }}</template></div>
            </div>
            <div class="prod-cell">
              <div class="prod-mark">{{ productInitials(task.product_name) }}</div>
              <div class="prod-name">{{ task.product_name || '—' }}</div>
            </div>
            <div><StatusPill :status="task.status" /></div>
            <div class="due-cell">
              <span class="due-date">{{ formatDate(task.due_date) }}</span>
              <span class="due-rel" :class="urgencyClass(task.due_date)">{{ relativeDue(task.due_date) }}</span>
            </div>
            <button class="row-go" aria-label="Open">
              <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" width="13" height="13" stroke-linecap="round"><path d="M6 4l4 4-4 4"/></svg>
            </button>
          </div>
        </div>
      </div>

      <!-- Upcoming -->
      <div v-if="visibleUpcoming.length" class="group">
        <div class="group-head">
          <span class="gdot gdot-upcoming"></span>
          <span class="gtitle">Upcoming</span>
          <span class="gcount">{{ visibleUpcoming.length }}</span>
          <span class="gline"></span>
        </div>
        <div class="task-list">
          <div class="col-head">
            <div>Type</div><div>Title</div><div>Product / Release</div><div>Status</div><div>Due</div><div></div>
          </div>
          <div
            v-for="task in visibleUpcoming" :key="task.entity_id"
            class="task-row"
            tabindex="0"
            @click="openDrawer(task)"
            @keydown.enter="openDrawer(task)"
          >
            <div><span class="type-pill" :class="`tp-${task.entity_type}`">
              <TypeIcon :type="task.entity_type" />
              {{ formatEntityType(task.entity_type) }}
            </span></div>
            <div class="tt-wrap">
              <div class="tt-main">{{ task.title }}</div>
              <div v-if="task.product_name" class="tt-sub">{{ task.product_name }}<template v-if="task.release_version"> · {{ task.release_version }}</template></div>
            </div>
            <div class="prod-cell">
              <div class="prod-mark">{{ productInitials(task.product_name) }}</div>
              <div class="prod-name">{{ task.product_name || '—' }}</div>
            </div>
            <div><StatusPill :status="task.status" /></div>
            <div class="due-cell">
              <span class="due-date">{{ formatDate(task.due_date) }}</span>
              <span class="due-rel">{{ relativeDue(task.due_date) }}</span>
            </div>
            <button class="row-go" aria-label="Open">
              <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" width="13" height="13" stroke-linecap="round"><path d="M6 4l4 4-4 4"/></svg>
            </button>
          </div>
        </div>
      </div>

      <!-- No due date -->
      <div v-if="visibleNoDue.length" class="group">
        <div class="group-head">
          <span class="gdot gdot-none"></span>
          <span class="gtitle">No due date</span>
          <span class="gcount">{{ visibleNoDue.length }}</span>
          <span class="gline"></span>
        </div>
        <div class="task-list">
          <div class="col-head">
            <div>Type</div><div>Title</div><div>Product / Release</div><div>Status</div><div>Due</div><div></div>
          </div>
          <div
            v-for="task in visibleNoDue" :key="task.entity_id"
            class="task-row"
            tabindex="0"
            @click="openDrawer(task)"
            @keydown.enter="openDrawer(task)"
          >
            <div><span class="type-pill" :class="`tp-${task.entity_type}`">
              <TypeIcon :type="task.entity_type" />
              {{ formatEntityType(task.entity_type) }}
            </span></div>
            <div class="tt-wrap">
              <div class="tt-main">{{ task.title }}</div>
              <div v-if="task.product_name" class="tt-sub">{{ task.product_name }}<template v-if="task.release_version"> · {{ task.release_version }}</template></div>
            </div>
            <div class="prod-cell">
              <div class="prod-mark">{{ productInitials(task.product_name) }}</div>
              <div class="prod-name">{{ task.product_name || '—' }}</div>
            </div>
            <div><StatusPill :status="task.status" /></div>
            <div class="due-cell">
              <span class="due-date" style="opacity:0.4">—</span>
              <span class="due-rel">No deadline</span>
            </div>
            <button class="row-go" aria-label="Open">
              <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" width="13" height="13" stroke-linecap="round"><path d="M6 4l4 4-4 4"/></svg>
            </button>
          </div>
        </div>
      </div>

    </template>
  </section>
</template>

<script setup lang="ts">
import { computed, defineComponent, h, onMounted, ref } from "vue";
import { useRouter } from "vue-router";

import TaskDrawer from "@/components/TaskDrawer.vue";
import { taskService } from "@/services/task-service";
import type { TaskItem } from "@/types/task";

const tasks = ref<TaskItem[]>([]);
const isLoading = ref(false);
const loadError = ref<string | null>(null);
const router = useRouter();
const activeFilter = ref<"overdue" | "week" | "all" | null>(null);

// ── Inline sub-components ─────────────────────────────────────────────────────

/** Small SVG icon matched to entity type */
const TypeIcon = defineComponent({
  props: { type: String },
  setup(props) {
    return () => {
      const paths: Record<string, string> = {
        vulnerability_report: "M10 3l7.5 13H2.5L10 3zM10 8v3.5M10 13.5v.5",
        change:               "M4 5h12M4 9h12M4 13h8",
        release_gate_item:    "M9 11l3 3 8-8M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11",
        risk_item:            "M4 4h12v12H4zM8 8h4M8 11h4M8 14h2",
      };
      const d = paths[props.type ?? ""] ?? paths.risk_item;
      return h("svg", { viewBox: "0 0 20 20", fill: "none", stroke: "currentColor", "stroke-width": "1.9", width: 13, height: 13, "stroke-linecap": "round", "stroke-linejoin": "round" },
        d.split("M").filter(Boolean).map(seg =>
          h("path", { d: "M" + seg })
        )
      );
    };
  },
});

/** Coloured status pill */
const StatusPill = defineComponent({
  props: { status: String },
  setup(props) {
    return () => {
      const s = props.status ?? "";
      const map: Record<string, string> = {
        new: "spill-info", in_progress: "spill-info", triaged: "spill-info",
        fix_in_progress: "spill-info",
        fixed: "spill-ok", mitigated: "spill-ok", accepted: "spill-ok",
        closed: "spill-ok", disclosed: "spill-ok",
        action_required: "spill-err", rejected: "spill-err",
        open: "spill-warn", review: "spill-warn",
      };
      const cls = map[s] ?? "spill-flat";
      const label = s.replace(/_/g, " ");
      return h("span", { class: ["spill", cls] }, [
        h("span", { class: "spill-dot" }),
        label,
      ]);
    };
  },
});

// ── Drawer ────────────────────────────────────────────────────────────────────
const drawerTask = ref<TaskItem | null>(null);

function openDrawer(task: TaskItem): void {
  drawerTask.value = task;
}

function onStatusUpdated(task: TaskItem, newStatus: string): void {
  const idx = tasks.value.findIndex((t) => t.entity_id === task.entity_id);
  if (idx !== -1) tasks.value[idx] = { ...tasks.value[idx], status: newStatus };
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

// ── Filter toggle ─────────────────────────────────────────────────────────────
function toggleFilter(f: "overdue" | "week" | "all"): void {
  activeFilter.value = activeFilter.value === f ? null : f;
}

// ── Date helpers ──────────────────────────────────────────────────────────────
function endOfWeek(): Date {
  const d = new Date();
  d.setHours(23, 59, 59, 999);
  d.setDate(d.getDate() + (6 - d.getDay()));
  return d;
}

function relativeDue(iso: string | null): string {
  if (!iso) return "";
  const now = new Date();
  const d = new Date(iso);
  const diffMs = d.getTime() - now.getTime();
  const diffDays = Math.ceil(diffMs / 86_400_000);
  if (diffDays < 0) return `${Math.abs(diffDays)}d overdue`;
  if (diffDays === 0) return "Today";
  if (diffDays === 1) return "Tomorrow";
  if (diffDays <= 7) return `In ${diffDays} days`;
  if (diffDays <= 30) return `In ${Math.ceil(diffDays / 7)}w`;
  return `In ${Math.ceil(diffDays / 30)}mo`;
}

function urgencyClass(iso: string | null): string {
  if (!iso) return "";
  const diffDays = Math.ceil((new Date(iso).getTime() - Date.now()) / 86_400_000);
  if (diffDays <= 1) return "due-urgent";
  if (diffDays <= 3) return "due-soon";
  return "";
}

// ── Computed groups ───────────────────────────────────────────────────────────
const overdueTasks     = computed(() => tasks.value.filter((t) => t.is_overdue));
const dueThisWeekTasks = computed(() => {
  const eow = endOfWeek();
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

// Apply active filter — when a filter is active, only show its group
const visibleOverdue  = computed(() =>
  (!activeFilter.value || activeFilter.value === "overdue" || activeFilter.value === "all") ? overdueTasks.value : []);
const visibleWeek     = computed(() =>
  (!activeFilter.value || activeFilter.value === "week" || activeFilter.value === "all") ? dueThisWeekTasks.value : []);
const visibleUpcoming = computed(() =>
  (!activeFilter.value || activeFilter.value === "all") ? upcomingTasks.value : []);
const visibleNoDue    = computed(() =>
  (!activeFilter.value || activeFilter.value === "all") ? noDueDateTasks.value : []);

// ── Navigation ────────────────────────────────────────────────────────────────
function navigateToTask(task: TaskItem): void {
  switch (task.entity_type) {
    case "vulnerability_report":
      router.push({ name: "vulnerability-handling", query: { tab: "enisa", report: task.entity_id } });
      break;
    case "change":
      router.push({ name: "change-detail", params: { id: task.entity_id } });
      break;
    case "release_gate_item":
      router.push(task.parent_id
        ? { name: "release-gate", params: { releaseId: task.parent_id } }
        : { name: "products" });
      break;
    case "risk_item":
      router.push(task.parent_id
        ? { name: "risk-assessment-detail", params: { assessmentId: task.parent_id } }
        : { name: "risk-assessments" });
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

function formatDate(iso: string | null): string {
  if (!iso) return "—";
  return new Date(iso).toLocaleDateString("en-GB", { day: "numeric", month: "short", year: "numeric" });
}

function productInitials(name: string | null | undefined): string {
  if (!name) return "?";
  const words = name.trim().split(/\s+/);
  if (words.length === 1) return words[0].slice(0, 2).toUpperCase();
  return (words[0][0] + words[1][0]).toUpperCase();
}
</script>

<style scoped>
/* ── Page shell ───────────────────────────────────────────────────────────── */
.tasks-page {
  display: flex;
  flex-direction: column;
  gap: 1.1rem;
  font-family: 'Inter', system-ui, sans-serif;
}

/* ── Page head ────────────────────────────────────────────────────────────── */
.page-head {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 1.5rem;
}

.page-title {
  font-size: 1.35rem;
  font-weight: 700;
  letter-spacing: -0.01em;
  margin: 0 0 0.2rem;
  color: var(--color-text);
}

.page-sub {
  font-size: 0.82rem;
  color: var(--color-text-muted);
  margin: 0;
}

.head-actions { display: flex; gap: 0.5rem; align-items: center; flex-shrink: 0; }

.hbtn {
  height: 32px;
  padding: 0 11px;
  border-radius: 7px;
  border: 1px solid var(--color-border);
  background: var(--color-surface);
  color: var(--color-text);
  font: 500 12.5px/1 'Inter', sans-serif;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  gap: 6px;
  transition: background 0.12s;
}
.hbtn:hover { background: var(--color-surface-elevated); }
.hbtn:disabled { opacity: 0.55; cursor: not-allowed; }

/* ── Error ────────────────────────────────────────────────────────────────── */
.hub-error {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.7rem 1rem;
  border-radius: 8px;
  background: var(--color-danger-bg);
  border: 1px solid var(--color-danger-border);
  color: var(--color-danger-text);
  font-size: 0.85rem;
}

/* ── Summary filter cards ─────────────────────────────────────────────────── */
.summary-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 0.75rem;
}

.sum-card {
  display: flex;
  align-items: center;
  gap: 0.85rem;
  padding: 1rem 1.1rem;
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: 12px;
  cursor: pointer;
  transition: border-color 0.12s, box-shadow 0.12s;
  user-select: none;
}
.sum-card:hover { border-color: var(--color-border-strong, var(--color-border)); }
.sum-active {
  box-shadow: 0 0 0 2px var(--color-text);
  border-color: var(--color-text);
}

.sum-ic {
  width: 42px;
  height: 42px;
  border-radius: 10px;
  display: grid;
  place-items: center;
  flex-shrink: 0;
}

/* Overdue (bad) */
.sum-overdue .sum-ic { background: var(--color-danger-bg); color: var(--color-danger-text); }
.sum-overdue .sum-num { color: var(--color-danger); }
/* Overdue (ok / zero) */
.sum-overdue-ok .sum-ic { background: var(--color-success-bg); color: var(--color-success-text); }
.sum-overdue-ok .sum-num { color: var(--color-success); }
/* Due this week */
.sum-week .sum-ic { background: var(--color-warning-bg); color: var(--color-warning-text); }
.sum-week .sum-num { color: var(--color-warning); }
/* Total open */
.sum-open .sum-ic { background: var(--color-info-bg); color: var(--color-info-text); }

.sum-body { flex: 1; min-width: 0; }

.sum-num {
  font-size: 1.75rem;
  font-weight: 700;
  letter-spacing: -0.02em;
  line-height: 1;
  color: var(--color-text);
}

.sum-label {
  font-size: 0.78rem;
  font-weight: 500;
  color: var(--color-text-muted);
  margin-top: 0.2rem;
}

.sum-arrow { color: var(--color-text-muted); flex-shrink: 0; }

/* ── Empty state ──────────────────────────────────────────────────────────── */
.empty-panel {
  padding: 3rem 2rem;
  text-align: center;
  color: var(--color-text-muted);
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: 12px;
  font-size: 0.9rem;
}

.empty-ic {
  width: 36px;
  height: 36px;
  border-radius: 9px;
  background: var(--color-success-bg);
  color: var(--color-success-text);
  display: grid;
  place-items: center;
  margin: 0 auto 0.75rem;
}

.empty-title {
  font-size: 1rem;
  font-weight: 700;
  color: var(--color-text);
  margin: 0 0 0.3rem;
}

.empty-sub { font-size: 0.82rem; margin: 0; }

/* ── Group header ─────────────────────────────────────────────────────────── */
.group { display: flex; flex-direction: column; gap: 0; }

.group-head {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0 0.25rem 0.6rem;
}

.gdot {
  width: 9px;
  height: 9px;
  border-radius: 50%;
  flex-shrink: 0;
}
.gdot-overdue  { background: var(--color-danger); }
.gdot-week     { background: var(--color-warning); }
.gdot-upcoming { background: var(--color-info); }
.gdot-none     { background: var(--color-text-muted); }

.gtitle {
  font-size: 0.72rem;
  font-weight: 700;
  letter-spacing: 0.07em;
  text-transform: uppercase;
  color: var(--color-text);
  white-space: nowrap;
}

.gcount {
  font-size: 0.68rem;
  font-weight: 700;
  color: var(--color-text-muted);
  background: var(--color-surface-elevated);
  border: 1px solid var(--color-border);
  padding: 1px 7px;
  border-radius: 999px;
  flex-shrink: 0;
}
.gcount-overdue { background: var(--color-danger-bg); color: var(--color-danger-text); border-color: var(--color-danger-border); }
.gcount-week    { background: var(--color-warning-bg); color: var(--color-warning-text); border-color: var(--color-warning-border); }

.gline {
  flex: 1;
  height: 1px;
  background: var(--color-border);
}

/* ── Task list card ───────────────────────────────────────────────────────── */
.task-list {
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: 12px;
  overflow: hidden;
}

/* Column header */
.col-head {
  display: grid;
  grid-template-columns: 130px 1fr 190px 130px 130px 28px;
  gap: 1rem;
  padding: 0.65rem 1.1rem;
  background: var(--color-surface-elevated);
  border-bottom: 1px solid var(--color-border);
  font-size: 0.68rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.07em;
  color: var(--color-text-muted);
}

/* Task row */
.task-row {
  display: grid;
  grid-template-columns: 130px 1fr 190px 130px 130px 28px;
  align-items: center;
  gap: 1rem;
  padding: 0.85rem 1.1rem;
  border-bottom: 1px solid var(--color-border);
  cursor: pointer;
  position: relative;
  transition: background 0.1s;
}
.task-row:last-child { border-bottom: none; }
.task-row:hover { background: var(--color-surface-elevated); }
.task-row:focus-visible { outline: 2px solid var(--color-primary); outline-offset: -2px; }

/* Left priority strip */
.task-row::before {
  content: '';
  position: absolute;
  left: 0; top: 0; bottom: 0;
  width: 3px;
  background: transparent;
  border-radius: 3px 0 0 3px;
}
.task-row.prio-high::before { background: var(--color-danger); }
.task-row.prio-med::before  { background: var(--color-warning); }

/* ── Type pill ────────────────────────────────────────────────────────────── */
.type-pill {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  padding: 4px 9px 4px 7px;
  border-radius: 6px;
  font-size: 0.72rem;
  font-weight: 600;
  white-space: nowrap;
}
.tp-vulnerability_report { background: var(--color-danger-bg);  color: var(--color-danger-text); }
.tp-change               { background: var(--color-info-bg);    color: var(--color-info-text); }
.tp-release_gate_item    { background: var(--color-success-bg); color: var(--color-success-text); }
.tp-risk_item            { background: var(--color-warning-bg); color: var(--color-warning-text); }

/* ── Title cell ───────────────────────────────────────────────────────────── */
.tt-wrap { min-width: 0; }
.tt-main {
  font-weight: 600;
  font-size: 0.84rem;
  color: var(--color-text);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.tt-sub {
  font-size: 0.71rem;
  color: var(--color-text-muted);
  margin-top: 2px;
  font-family: 'JetBrains Mono', monospace;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

/* ── Product cell ─────────────────────────────────────────────────────────── */
.prod-cell {
  display: flex;
  align-items: center;
  gap: 8px;
  min-width: 0;
}
.prod-mark {
  width: 26px;
  height: 26px;
  border-radius: 6px;
  background: var(--color-surface-elevated);
  border: 1px solid var(--color-border);
  display: grid;
  place-items: center;
  font-size: 0.62rem;
  font-weight: 700;
  color: var(--color-text);
  flex-shrink: 0;
}
.prod-name {
  font-size: 0.82rem;
  color: var(--color-text-muted);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

/* ── Status pill ──────────────────────────────────────────────────────────── */
.spill {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  padding: 3px 9px;
  border-radius: 999px;
  font-size: 0.72rem;
  font-weight: 600;
  white-space: nowrap;
  text-transform: capitalize;
}
.spill-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  flex-shrink: 0;
}
.spill-ok   { background: var(--color-success-bg);  color: var(--color-success-text); }
.spill-ok .spill-dot { background: var(--color-success); }
.spill-warn { background: var(--color-warning-bg); color: var(--color-warning-text); }
.spill-warn .spill-dot { background: var(--color-warning); }
.spill-err  { background: var(--color-danger-bg);  color: var(--color-danger-text); }
.spill-err .spill-dot { background: var(--color-danger); }
.spill-info { background: var(--color-info-bg);    color: var(--color-info-text); }
.spill-info .spill-dot { background: var(--color-info); }
.spill-flat { background: var(--color-surface-elevated); color: var(--color-text-muted); border: 1px solid var(--color-border); }
.spill-flat .spill-dot { background: var(--color-text-muted); }

/* ── Due date cell ────────────────────────────────────────────────────────── */
.due-cell { display: flex; flex-direction: column; gap: 1px; }
.due-date { font-size: 0.82rem; color: var(--color-text); font-weight: 500; }
.due-overdue { color: var(--color-danger); }
.due-rel  { font-size: 0.7rem; color: var(--color-text-muted); }
.due-urgent { color: var(--color-danger); font-weight: 600; }
.due-soon   { color: var(--color-warning); font-weight: 600; }

/* ── Row go button ────────────────────────────────────────────────────────── */
.row-go {
  width: 26px;
  height: 26px;
  border-radius: 5px;
  background: transparent;
  border: none;
  color: var(--color-text-muted);
  display: grid;
  place-items: center;
  cursor: pointer;
  opacity: 0;
  transition: opacity 0.1s, background 0.1s;
}
.task-row:hover .row-go { opacity: 1; background: var(--color-surface-elevated-strong, var(--color-surface-elevated)); color: var(--color-text); }
</style>

<!-- Light-mode overrides — non-scoped to reach [data-theme] root -->
<style>
[data-theme="light"] .tasks-page .sum-card {
  box-shadow: 0 1px 3px rgba(0,0,0,0.06), 0 0 0 1px rgba(0,0,0,0.10);
  border-color: transparent;
}
[data-theme="light"] .tasks-page .sum-active {
  box-shadow: 0 0 0 2px oklch(0.22 0.012 150);
  border-color: transparent;
}
[data-theme="light"] .tasks-page .task-list {
  box-shadow: 0 1px 3px rgba(0,0,0,0.06), 0 0 0 1px rgba(0,0,0,0.10);
  border-color: transparent;
}
[data-theme="light"] .tasks-page .task-row:hover {
  background: oklch(0.985 0.005 150);
}
[data-theme="light"] .tasks-page .col-head {
  background: oklch(0.972 0.004 140);
  border-bottom-color: oklch(0.91 0.012 150);
}
</style>
