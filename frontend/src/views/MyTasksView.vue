<!--
  CRANE — CRA Norm Engine
  Copyright (C) 2026 Ali Mohammad Hosseini
  SPDX-License-Identifier: AGPL-3.0-or-later
  This file is part of CRANE, free software under the GNU AGPL v3.0 or later.
  See <https://www.gnu.org/licenses/>.
-->
<template>
  <!-- Task detail drawer -->
  <TaskDrawer
    :task="drawerTask"
    @close="drawerTask = null"
    @navigate="openFullRecord"
    @edit="openEditModal"
    @status-updated="onStatusUpdated"
    @task-updated="onTaskUpdated"
  />

  <AppModal v-model="showCreateModal" :title="editingTask ? 'Edit task' : 'New task'" size="sm" :persistent="isCreating">
    <form id="manual-task-form" class="manual-task-form" @submit.prevent="createTask">
      <label class="task-field">
        <span>Title</span>
        <input v-model.trim="createForm.title" required maxlength="255" autofocus placeholder="What needs to be done?" />
      </label>
      <label class="task-field">
        <span>Description <small>Optional</small></span>
        <textarea v-model.trim="createForm.description" rows="3" maxlength="5000" placeholder="Add context or notes" />
      </label>
      <label class="task-field">
        <span>Due date <small>Optional</small></span>
        <input v-model="createForm.due_date" type="date" />
      </label>
      <label class="task-field">
        <span>Priority</span>
        <select v-model="createForm.priority"><option value="low">Low</option><option value="medium">Medium</option><option value="high">High</option></select>
      </label>
      <label class="task-field">
        <span>Assign to</span>
        <select v-model="createForm.assigned_to_user_id">
          <option value="">Myself</option>
          <option v-for="user in users" :key="user.id" :value="user.id">{{ userService.displayName(user) }}</option>
        </select>
      </label>
      <label class="task-field">
        <span>Parent task <small>Optional</small></span>
        <select v-model="createForm.parent_task_id">
          <option value="">Standalone task</option>
          <option v-for="parent in parentTaskChoices" :key="parent.entity_id" :value="parent.entity_id">{{ parent.title }}</option>
        </select>
      </label>
      <label class="task-field">
        <span>Related product <small>Optional</small></span>
        <select v-model="createForm.product_id" @change="onProductChange">
          <option value="">No related product</option>
          <option v-for="product in products" :key="product.id" :value="product.id">{{ product.name }}</option>
        </select>
      </label>
      <label class="task-field">
        <span>Related release <small>Optional</small></span>
        <select v-model="createForm.product_release_id" :disabled="!createForm.product_id || isLoadingReleases">
          <option value="">{{ isLoadingReleases ? 'Loading releases…' : 'No related release' }}</option>
          <option v-for="release in releases" :key="release.id" :value="release.id">{{ release.display_version }}</option>
        </select>
      </label>
      <p v-if="createError" class="create-error">{{ createError }}</p>
    </form>
    <template #footer>
      <button class="hbtn" type="button" :disabled="isCreating" @click="showCreateModal = false">Cancel</button>
      <button class="hbtn hbtn-primary" type="submit" form="manual-task-form" :disabled="isCreating || !createForm.title.trim()">
        {{ isCreating ? "Saving…" : editingTask ? "Save changes" : "Create task" }}
      </button>
    </template>
  </AppModal>

  <section class="tasks-page">

    <!-- ── Page head ─────────────────────────────────────────────────────── -->
    <div class="page-head">
      <div>
        <h1 class="page-title">My Tasks</h1>
        <p class="page-sub">Open items assigned to you or created by you, with completed-task history.</p>
      </div>
      <div class="head-actions">
        <div class="view-toggle" role="group" aria-label="Task layout">
          <button class="hbtn" :class="{ 'view-active': viewMode === 'list' }" @click="viewMode = 'list'">List</button>
          <button class="hbtn" :class="{ 'view-active': viewMode === 'board' }" @click="viewMode = 'board'">Board</button>
        </div>
        <button class="hbtn hbtn-primary" @click="openCreateModal">+ New task</button>
        <template v-if="viewMode === 'board' && jiraConnections.length">
          <select v-model="jiraBoardConnection" class="toolbar-select" aria-label="Jira board destination">
            <option v-for="connection in jiraConnections" :key="connection.id" :value="connection.id">{{ connection.site_name }} · {{ connection.project_key }}</option>
          </select>
          <button class="hbtn" :disabled="jiraBoardBusy || !jiraBoardConnection" @click="syncBoard">{{ jiraBoardBusy ? 'Syncing…' : 'Sync board to Jira' }}</button>
        </template>
        <button class="hbtn" :disabled="isLoading" @click="load">
          <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.7" width="14" height="14" stroke-linecap="round" stroke-linejoin="round">
            <path d="M4 4v4h4"/><path d="M4 8a7 7 0 1 0 1.4-4.1"/>
          </svg>
          {{ isLoading ? "Refreshing…" : "Refresh" }}
        </button>
      </div>
    </div>

    <nav class="task-tabs" aria-label="Task views">
      <button v-for="tab in taskTabs" :key="tab.key" :class="{ active: activeTab === tab.key }" @click="setTab(tab.key)">{{ tab.label }} <span>{{ tab.count }}</span></button>
    </nav>

    <!-- ── Error ──────────────────────────────────────────────────────────── -->
    <div v-if="loadError" class="hub-error">
      <svg viewBox="0 0 20 20" fill="currentColor" width="15" height="15"><path fill-rule="evenodd" d="M8.485 2.495c.673-1.167 2.357-1.167 3.03 0l6.28 10.875c.673 1.167-.17 2.625-1.516 2.625H3.72c-1.347 0-2.189-1.458-1.515-2.625L8.485 2.495zM10 5a.75.75 0 0 1 .75.75v3.5a.75.75 0 0 1-1.5 0v-3.5A.75.75 0 0 1 10 5zm0 9a1 1 0 1 0 0-2 1 1 0 0 0 0 2z" clip-rule="evenodd"/></svg>
      {{ loadError }}
    </div>

    <!-- ── Summary filter cards ───────────────────────────────────────────── -->
    <div v-if="!isLoading && activeTab === 'my_work'" class="summary-grid">

      <!-- Overdue -->
      <button
        type="button"
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
      </button>

      <!-- Due this week -->
      <button
        type="button"
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
      </button>

      <!-- Total open -->
      <button
        type="button"
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
          <div class="sum-num">{{ actionableTasks.length }}</div>
          <div class="sum-label">Total open</div>
        </div>
        <svg class="sum-arrow" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" width="14" height="14" stroke-linecap="round"><path d="M6 4l4 4-4 4"/></svg>
      </button>

    </div>

    <!-- ── Search + active-filter chip ────────────────────────────────────── -->
    <div v-if="!isLoading && tasks.length" class="tasks-toolbar">
      <div class="task-search">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" width="15" height="15" stroke-linecap="round" stroke-linejoin="round">
          <circle cx="11" cy="11" r="7"/><path d="m20 20-3.5-3.5"/>
        </svg>
        <input v-model.trim="search" placeholder="Search tasks by title, product or release…" />
        <button v-if="search" type="button" class="task-search-x" aria-label="Clear search" @click="search = ''">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="13" height="13" stroke-linecap="round" stroke-linejoin="round"><path d="M6 6l12 12M6 18L18 6"/></svg>
        </button>
      </div>
      <select v-model="priorityFilter" class="toolbar-select"><option value="">All priorities</option><option value="high">High</option><option value="medium">Medium</option><option value="low">Low</option></select>
      <select v-model="productFilter" class="toolbar-select" @change="onFilterProductChange()"><option value="">All products</option><option v-for="p in products" :key="p.id" :value="p.id">{{ p.name }}</option></select>
      <select v-model="releaseFilter" class="toolbar-select" :disabled="!productFilter"><option value="">All releases</option><option v-for="r in filterReleases" :key="r.id" :value="r.id">{{ r.display_version }}</option></select>

      <!-- Removable chip mirroring the toggled summary card. -->
      <button v-if="activeFilter" type="button" class="task-chip" @click="activeFilter = null">
        <span class="task-chip-k">Showing:</span>
        <span class="task-chip-v">{{ filterLabel }}</span>
        <svg class="task-chip-x" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="12" height="12" stroke-linecap="round" stroke-linejoin="round"><path d="M6 6l12 12M6 18L18 6"/></svg>
      </button>
    </div>

    <!-- ── Loading skeleton ───────────────────────────────────────────────── -->
    <div v-if="isLoading" class="task-list skel-list" aria-hidden="true">
      <div v-for="n in 5" :key="n" class="skel-row">
        <span class="skel skel-pill"></span>
        <span class="skel skel-line skel-w60"></span>
        <span class="skel skel-mark"></span>
        <span class="skel skel-pill"></span>
        <span class="skel skel-line skel-w40"></span>
        <span></span>
      </div>
    </div>

    <!-- ── Empty: no tasks at all ─────────────────────────────────────────── -->
    <div v-else-if="!tasks.length && !loadError" class="empty-panel">
      <div class="empty-ic">
        <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.8" width="20" height="20" stroke-linecap="round"><path d="M3 10.5l4.5 4.5 9.5-9"/></svg>
      </div>
      <p class="empty-title">All caught up</p>
      <p class="empty-sub">No open tasks assigned to you right now.</p>
    </div>

    <!-- ── Empty: filtered/searched to nothing ────────────────────────────── -->
    <div v-else-if="!visibleGroups.length && !loadError" class="empty-panel">
      <div class="empty-ic empty-ic-muted">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" width="20" height="20" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="7"/><path d="m20 20-3.5-3.5"/></svg>
      </div>
      <p class="empty-title">No matching tasks</p>
      <p class="empty-sub">No tasks match your search or filter. Try clearing them.</p>
      <button class="hbtn" @click="clearFilters">Clear search &amp; filters</button>
    </div>

    <div v-if="viewMode === 'board' && !isLoading" class="task-board">
      <section v-for="column in boardColumns" :key="column.key" class="task-column">
        <div class="task-column-head"><span class="gdot" :class="`gdot-${column.tone}`"></span><strong>{{ column.title }}</strong><span class="gcount">{{ column.tasks.length }}</span></div>
        <div class="task-column-body" @dragover.prevent @drop="dropTask(column.key)">
          <button v-for="task in column.tasks" :key="task.entity_id" class="board-card" :draggable="task.entity_type === 'manual_task' && task.can_update_status" @dragstart="draggedTask = task" @click="openDrawer(task)">
            <span class="board-card-head"><span class="board-card-title">{{ task.title }}</span><span class="board-avatar" :title="task.assigned_to_name || 'Unassigned'"><template v-if="task.assigned_to_name">{{ userInitials(task.assigned_to_name) }}</template><svg v-else viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="8" r="3.2"/><path d="M5.5 20c.7-3.3 3-5 6.5-5s5.8 1.7 6.5 5"/></svg></span></span>
            <span class="board-card-meta">{{ task.product_name || 'No product' }} · {{ task.assigned_to_name || 'Unassigned' }}</span>
            <span class="board-card-foot"><StatusPill :status="task.status" /><span v-if="task.priority" :class="`priority-${task.priority}`">{{ task.priority }}</span></span>
          </button>
          <p v-if="!column.tasks.length" class="board-empty">Drop tasks here</p>
        </div>
      </section>
    </div>

    <!-- ── Task groups — single template, looped over the group model ─────── -->
    <template v-else-if="viewMode === 'list'">
      <div v-for="group in visibleGroups" :key="group.key" class="group">
        <div class="group-head">
          <span class="gdot" :class="`gdot-${group.tone}`"></span>
          <span class="gtitle">{{ group.title }}</span>
          <span class="gcount" :class="group.tone === 'overdue' || group.tone === 'week' ? `gcount-${group.tone}` : ''">{{ group.tasks.length }}</span>
          <span class="gline"></span>
        </div>
        <div class="task-list">
          <div class="col-head">
            <div>Type</div><div>Title</div><div>Product / Release</div><div>Status</div><div>Due</div><div></div>
          </div>
          <div
            v-for="task in group.tasks" :key="task.entity_id"
            class="task-row"
            :class="group.rowClass"
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
              <div class="tt-sub">
                <template v-if="activeTab === 'assigned_by_me'">Assigned to {{ task.assigned_to_name || 'Unassigned' }}</template>
                <template v-else-if="task.product_name">{{ task.product_name }}<template v-if="task.release_version"> · {{ task.release_version }}</template></template>
                <template v-if="task.priority"> · {{ task.priority }} priority</template>
              </div>
            </div>
            <div class="prod-cell">
              <div class="prod-mark">{{ productInitials(task.product_name) }}</div>
              <div class="prod-name">{{ task.product_name || '—' }}</div>
            </div>
            <div><StatusPill :status="task.status" /></div>
            <div class="due-cell">
              <template v-if="task.due_date">
                <span class="due-date" :class="{ 'due-overdue': group.tone === 'overdue' }">{{ formatDate(task.due_date) }}</span>
                <span class="due-rel" :class="group.tone === 'overdue' ? 'due-urgent' : urgencyClass(task.due_date)">{{ relativeDue(task.due_date) }}</span>
              </template>
              <template v-else>
                <span class="due-date" style="opacity:0.4">—</span>
                <span class="due-rel">No deadline</span>
              </template>
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
import { computed, defineComponent, h, onMounted, ref, watch } from "vue";
import { useRoute, useRouter } from "vue-router";

import TaskDrawer from "@/components/TaskDrawer.vue";
import AppModal from "@/components/AppModal.vue";
import { taskService } from "@/services/task-service";
import { userService, type UserSummary } from "@/services/user-service";
import { productService } from "@/services/product-service";
import { productReleaseService } from "@/services/product-release-service";
import { jiraService, type JiraConnection } from "@/services/jira-service";
import type { ProductSummaryRead } from "@/types/product";
import type { ProductReleaseRead } from "@/types/release-gate";
import type { TaskItem } from "@/types/task";

const tasks = ref<TaskItem[]>([]);
const isLoading = ref(false);
const loadError = ref<string | null>(null);
const router = useRouter();
const route = useRoute();
const activeFilter = ref<"overdue" | "week" | "all" | null>(null);
const viewMode = ref<"list" | "board">("list");
const draggedTask = ref<TaskItem | null>(null);
const jiraConnections = ref<JiraConnection[]>([]);
const jiraBoardConnection = ref("");
const jiraBoardBusy = ref(false);
const search = ref((route.query.search as string) || "");
type TaskTab = "my_work" | "assigned_by_me" | "completed" | "archived";
const validTabs: TaskTab[] = ["my_work", "assigned_by_me", "completed", "archived"];
const activeTab = ref<TaskTab>(validTabs.includes(route.query.tab as TaskTab) ? route.query.tab as TaskTab : "my_work");
const priorityFilter = ref((route.query.priority as string) || "");
const productFilter = ref((route.query.product as string) || "");
const releaseFilter = ref((route.query.release as string) || "");
const filterReleases = ref<ProductReleaseRead[]>([]);
const showCreateModal = ref(false);
const isCreating = ref(false);
const createError = ref<string | null>(null);
const editingTask = ref<TaskItem | null>(null);
const users = ref<UserSummary[]>([]);
const products = ref<ProductSummaryRead[]>([]);
const releases = ref<ProductReleaseRead[]>([]);
const isLoadingReleases = ref(false);
const createForm = ref({ title: "", description: "", due_date: "", priority: "medium" as "low" | "medium" | "high", assigned_to_user_id: "", parent_task_id: "", product_id: "", product_release_id: "" });
const parentTaskChoices = computed(() => tasks.value.filter((task) => task.entity_type === "manual_task" && task.entity_id !== editingTask.value?.entity_id && !task.archived_at));

function openCreateModal(): void {
  editingTask.value = null;
  createForm.value = { title: "", description: "", due_date: "", priority: "medium", assigned_to_user_id: "", parent_task_id: "", product_id: "", product_release_id: "" };
  releases.value = [];
  createError.value = null;
  showCreateModal.value = true;
}

async function openEditModal(task: TaskItem): Promise<void> {
  drawerTask.value = null;
  editingTask.value = task;
  createError.value = null;
  createForm.value = {
    title: task.title,
    description: task.description ?? "",
    due_date: task.due_date ?? "",
    priority: task.priority ?? "medium",
    assigned_to_user_id: task.assigned_to_user_id ?? "",
    parent_task_id: task.parent_task_id ?? "",
    product_id: task.related_product_id ?? "",
    product_release_id: task.related_release_id ?? "",
  };
  releases.value = [];
  if (createForm.value.product_id) {
    isLoadingReleases.value = true;
    try {
      releases.value = await productReleaseService.list(createForm.value.product_id);
    } catch {
      releases.value = [];
    } finally {
      isLoadingReleases.value = false;
    }
  }
  showCreateModal.value = true;
}

async function createTask(): Promise<void> {
  isCreating.value = true;
  createError.value = null;
  try {
    const payload = {
      title: createForm.value.title,
      description: createForm.value.description || null,
      due_date: createForm.value.due_date || null,
      priority: createForm.value.priority,
      assigned_to_user_id: createForm.value.assigned_to_user_id || null,
      parent_task_id: createForm.value.parent_task_id || null,
      product_id: createForm.value.product_id || null,
      product_release_id: createForm.value.product_release_id || null,
    };
    if (editingTask.value) await taskService.update(editingTask.value.entity_id, payload);
    else await taskService.create(payload);
    showCreateModal.value = false;
    editingTask.value = null;
    await load();
  } catch {
    createError.value = `Failed to ${editingTask.value ? "update" : "create"} task. Please try again.`;
  } finally {
    isCreating.value = false;
  }
}

async function onProductChange(): Promise<void> {
  createForm.value.product_release_id = "";
  releases.value = [];
  if (!createForm.value.product_id) return;
  isLoadingReleases.value = true;
  try {
    releases.value = await productReleaseService.list(createForm.value.product_id);
  } catch {
    releases.value = [];
  } finally {
    isLoadingReleases.value = false;
  }
}

// ── Inline sub-components ─────────────────────────────────────────────────────

/** Small SVG icon matched to entity type */
const TypeIcon = defineComponent({
  props: { type: String },
  setup(props) {
    return () => {
      const paths: Record<string, string> = {
        vulnerability_report: "M10 3l7.5 13H2.5L10 3zM10 8v3.5M10 13.5v.5",
        change:               "M4 5h12M4 9h12M4 13h8",
        change_compliance_action: "M4 4h12v12H4zM7 8h6M7 11h4",
        release_gate_item:    "M9 11l3 3 8-8M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11",
        risk_item:            "M4 4h12v12H4zM8 8h4M8 11h4M8 14h2",
        eos_alert:            "M10 3a7 7 0 1 0 0 14A7 7 0 0 0 10 3M10 6.5v3.5l2.5 1.5",
        manual_task:          "M4 4h12v12H4zM7 8h6M7 11h4",
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
        open: "spill-warn", review: "spill-warn", pending: "spill-warn",
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
  if (idx !== -1) tasks.value[idx] = {
    ...tasks.value[idx], status: newStatus, is_completed: newStatus === "completed",
  };
  if (newStatus === "completed") {
    drawerTask.value = null;
  }
}

function onTaskUpdated(task: TaskItem): void {
  const idx = tasks.value.findIndex((item) => item.entity_id === task.entity_id && item.entity_type === task.entity_type);
  if (idx !== -1) tasks.value[idx] = task;
  drawerTask.value = task;
}

function openFullRecord(task: TaskItem): void {
  drawerTask.value = null;
  navigateToTask(task);
}

async function load(): Promise<void> {
  isLoading.value = true;
  loadError.value = null;
  try {
    tasks.value = await taskService.listMyTasks(true, { scope: "all", state: "all" });
    const requestedTask = route.query.task as string | undefined;
    if (requestedTask) drawerTask.value = tasks.value.find((task) => task.entity_id === requestedTask) ?? null;
  } catch {
    loadError.value = "Failed to load tasks. Please try again.";
  } finally {
    isLoading.value = false;
  }
}

async function syncBoard(): Promise<void> {
  if (!jiraBoardConnection.value) return;
  jiraBoardBusy.value = true;
  try {
    const result = await jiraService.syncBoard(jiraBoardConnection.value);
    window.alert(`Jira board sync complete: ${result.exported} exported, ${result.synchronized} synchronized, ${result.skipped} skipped, ${result.failed} failed.`);
    await load();
  } finally { jiraBoardBusy.value = false; }
}

onMounted(async () => {
  void load();
  jiraConnections.value = (await jiraService.connections().catch(() => [])).filter((connection) => connection.is_active && !!connection.project_key);
  jiraBoardConnection.value = jiraConnections.value[0]?.id || "";
  userService.listSummary().then((result) => { users.value = result; }).catch(() => { users.value = []; });
  products.value = await productService.list().catch(() => []);
  if (productFilter.value) void onFilterProductChange(false);
  if (route.query.new === "1") {
    openCreateModal();
    createForm.value.product_id = (route.query.product as string) || "";
    if (createForm.value.product_id) {
      await onProductChange();
      createForm.value.product_release_id = (route.query.release as string) || "";
    }
  }
});

function setTab(tab: TaskTab): void {
  activeTab.value = tab;
  activeFilter.value = null;
}

async function onFilterProductChange(clear = true): Promise<void> {
  if (clear) releaseFilter.value = "";
  filterReleases.value = [];
  if (!productFilter.value) return;
  filterReleases.value = await productReleaseService.list(productFilter.value).catch(() => []);
}

watch([activeTab, priorityFilter, productFilter, releaseFilter, search], () => {
  void router.replace({ query: {
    ...(activeTab.value !== "my_work" ? { tab: activeTab.value } : {}),
    ...(priorityFilter.value ? { priority: priorityFilter.value } : {}),
    ...(productFilter.value ? { product: productFilter.value } : {}),
    ...(releaseFilter.value ? { release: releaseFilter.value } : {}),
    ...(search.value ? { search: search.value } : {}),
  } });
});

watch(() => route.query.task, (taskId) => {
  drawerTask.value = taskId ? tasks.value.find((task) => task.entity_id === taskId) ?? null : null;
});

// ── Filter toggle ─────────────────────────────────────────────────────────────
function toggleFilter(f: "overdue" | "week" | "all"): void {
  activeFilter.value = activeFilter.value === f ? null : f;
}

/** Human label for the active summary-card filter (shown in the removable chip). */
const filterLabel = computed(() => {
  switch (activeFilter.value) {
    case "overdue": return "Overdue";
    case "week":    return "Due this week";
    case "all":     return "All open";
    default:        return "";
  }
});

function clearFilters(): void {
  activeFilter.value = null;
  search.value = "";
  priorityFilter.value = "";
  productFilter.value = "";
  releaseFilter.value = "";
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
const delegatedTasks = computed(() => tasks.value.filter((t) =>
  !t.is_completed && !t.archived_at && t.entity_type === "manual_task" && t.viewer_is_creator && t.viewer_is_assignee === false
));
const completedTasks = computed(() => tasks.value.filter((t) => t.is_completed && !t.archived_at));
const archivedTasks = computed(() => tasks.value.filter((t) => !!t.archived_at && t.viewer_is_creator));
const actionableTasks = computed(() => tasks.value.filter((t) => !t.is_completed && !t.archived_at && t.viewer_is_assignee !== false));
const overdueTasks     = computed(() => actionableTasks.value.filter((t) => t.is_overdue));
const dueThisWeekTasks = computed(() => {
  const eow = endOfWeek();
  const today = new Date(); today.setHours(0, 0, 0, 0);
  return actionableTasks.value.filter((t) => {
    if (t.is_overdue || !t.due_date) return false;
    const d = new Date(t.due_date);
    return d >= today && d <= eow;
  });
});
const upcomingTasks    = computed(() => {
  const eow = endOfWeek();
  return actionableTasks.value.filter((t) => !t.is_overdue && !!t.due_date && new Date(t.due_date) > eow);
});
const noDueDateTasks   = computed(() => actionableTasks.value.filter((t) => !t.due_date && !t.is_overdue));

const overdueCount     = computed(() => overdueTasks.value.length);
const dueThisWeekCount = computed(() => dueThisWeekTasks.value.length);

/** Case-insensitive match of a task against the search box (title/product/release). */
function matchesSearch(task: TaskItem): boolean {
  if (priorityFilter.value && task.priority !== priorityFilter.value) return false;
  if (productFilter.value && task.related_product_id !== productFilter.value) return false;
  if (releaseFilter.value && task.related_release_id !== releaseFilter.value) return false;
  const q = search.value.trim().toLowerCase();
  if (!q) return true;
  return [task.title, task.product_name, task.release_version]
    .filter(Boolean)
    .join(" ")
    .toLowerCase()
    .includes(q);
}

const taskTabs = computed(() => [
  { key: "my_work" as TaskTab, label: "My work", count: actionableTasks.value.length },
  { key: "assigned_by_me" as TaskTab, label: "Assigned by me", count: delegatedTasks.value.length },
  { key: "completed" as TaskTab, label: "Completed", count: completedTasks.value.length },
  { key: "archived" as TaskTab, label: "Archived", count: archivedTasks.value.length },
]);

/**
 * The single group model that drives the whole list. Each group carries its
 * display tone + priority-strip row class, so the template renders one row
 * markup for every group instead of four near-identical copies. The active
 * summary-card filter hides non-matching groups; the search box filters the
 * tasks within every group; empty groups drop out.
 */
interface TaskGroup {
  key: string;
  title: string;
  tone: "overdue" | "week" | "upcoming" | "none";
  rowClass: string;
  tasks: TaskItem[];
}
const visibleGroups = computed<TaskGroup[]>(() => {
  const f = activeFilter.value;
  const wantOverdue  = !f || f === "overdue" || f === "all";
  const wantWeek     = !f || f === "week" || f === "all";
  const wantRest     = !f || f === "all";

  let defs: TaskGroup[];
  if (activeTab.value === "assigned_by_me") defs = [{ key: "delegated", title: "Tasks I assigned", tone: "upcoming", rowClass: "", tasks: delegatedTasks.value }];
  else if (activeTab.value === "completed") defs = [{ key: "completed", title: "Completed tasks", tone: "none", rowClass: "", tasks: completedTasks.value }];
  else if (activeTab.value === "archived") defs = [{ key: "archived", title: "Archived tasks", tone: "none", rowClass: "", tasks: archivedTasks.value }];
  else defs = [
    { key: "overdue", title: "Overdue", tone: "overdue", rowClass: "prio-high", tasks: wantOverdue ? overdueTasks.value : [] },
    { key: "week", title: "Due this week", tone: "week", rowClass: "prio-med", tasks: wantWeek ? dueThisWeekTasks.value : [] },
    { key: "upcoming", title: "Upcoming", tone: "upcoming", rowClass: "", tasks: wantRest ? upcomingTasks.value : [] },
    { key: "nodue", title: "No due date", tone: "none", rowClass: "", tasks: wantRest ? noDueDateTasks.value : [] },
  ];

  const priorityRank: Record<string, number> = { high: 0, medium: 1, low: 2 };
  return defs
    .map((g) => ({ ...g, tasks: g.tasks.filter(matchesSearch).sort((a, b) => {
      if (g.key === "completed") return Date.parse(b.completed_at ?? "") - Date.parse(a.completed_at ?? "");
      if (g.key === "archived") return Date.parse(b.archived_at ?? "") - Date.parse(a.archived_at ?? "");
      const priorityDifference = (priorityRank[a.priority ?? ""] ?? 3) - (priorityRank[b.priority ?? ""] ?? 3);
      if (priorityDifference) return priorityDifference;
      const dueDifference = Date.parse(a.due_date ?? "9999-12-31") - Date.parse(b.due_date ?? "9999-12-31");
      return dueDifference || Date.parse(a.created_at ?? "") - Date.parse(b.created_at ?? "");
    }) }))
    .filter((g) => g.tasks.length > 0);
});

const boardColumns = computed(() => {
  const source = (activeTab.value === "assigned_by_me" ? delegatedTasks.value : activeTab.value === "completed" ? completedTasks.value : activeTab.value === "archived" ? archivedTasks.value : tasks.value)
    .filter(matchesSearch);
  const columns = [
    { key: "open", title: "Backlog", tone: "none", tasks: [] as TaskItem[] },
    { key: "in_progress", title: "In progress", tone: "week", tasks: [] as TaskItem[] },
    { key: "completed", title: "Done / release", tone: "upcoming", tasks: [] as TaskItem[] },
  ];
  source.forEach((task) => columns.find((column) => column.key === (task.is_completed ? "completed" : task.status === "in_progress" ? "in_progress" : "open"))?.tasks.push(task));
  return columns;
});

async function dropTask(status: string): Promise<void> {
  const task = draggedTask.value;
  draggedTask.value = null;
  if (!task || task.entity_type !== "manual_task" || !task.can_update_status || status === "completed" && task.status === "completed") return;
  try {
    const updated = status === "completed" ? await taskService.complete(task.entity_id, null) : await taskService.updateStatus(task.entity_id, status);
    onTaskUpdated(updated);
    await load();
  } catch { /* the drawer remains the source of detailed validation errors */ }
}

// ── Navigation ────────────────────────────────────────────────────────────────
function navigateToTask(task: TaskItem): void {
  switch (task.entity_type) {
    case "vulnerability_report":
      router.push({ name: "vulnerability-handling", query: { tab: "remediation", report: task.entity_id } });
      break;
    case "change":
      router.push({ name: "change-detail", params: { id: task.entity_id } });
      break;
    case "change_compliance_action":
      router.push(task.parent_id
        ? { name: "change-detail", params: { id: task.parent_id }, hash: "#compliance-actions" }
        : { name: "changes" });
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
    case "eos_alert":
      router.push(task.parent_id
        ? { name: "product-detail", params: { productId: task.parent_id } }
        : { name: "products" });
      break;
    case "supplier_reassessment":
      router.push({ name: "supplier-assessment-detail", params: { assessmentId: task.entity_id } });
      break;
    case "maintainer_notification":
      router.push({ name: "vulnerability-handling", query: { tab: "remediation", report: task.parent_id } });
      break;
    case "manual_task":
      if (task.related_release_id) router.push({ name: "release-gate", params: { releaseId: task.related_release_id } });
      else if (task.related_product_id) router.push({ name: "product-detail", params: { productId: task.related_product_id } });
      break;
  }
}

// ── Formatters ────────────────────────────────────────────────────────────────
function formatEntityType(type: string): string {
  const map: Record<string, string> = {
    vulnerability_report: "Vulnerability",
    change:              "Change",
    change_compliance_action: "Change action",
    release_gate_item:   "Gate item",
    risk_item:           "Risk item",
    eos_alert:           "EOL Alert",
    supplier_reassessment: "Supplier reassessment",
    maintainer_notification: "Maintainer notice",
    manual_task:         "Task",
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

function userInitials(name: string | null | undefined): string {
  return (name || "?").split(/\s+/).filter(Boolean).slice(0, 2).map((part) => part[0]).join("").toUpperCase();
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

.task-tabs { display: flex; gap: 0.35rem; border-bottom: 1px solid var(--color-border); }
.task-tabs button { border: 0; border-bottom: 2px solid transparent; background: none; color: var(--color-text-muted); padding: 0.65rem 0.85rem; cursor: pointer; font-weight: 600; }
.task-tabs button.active { color: var(--color-text); border-bottom-color: var(--color-primary); }
.task-tabs span { margin-left: 0.3rem; padding: 0.1rem 0.4rem; border-radius: 999px; background: var(--color-surface-elevated); font-size: 0.7rem; }

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
.hbtn-primary { background: var(--color-primary); border-color: var(--color-primary); color: white; }
.hbtn-primary:hover { filter: brightness(1.08); background: var(--color-primary); }

.manual-task-form { display: grid; gap: 1rem; }
.task-field { display: grid; gap: 0.4rem; color: var(--color-text); font-size: 0.82rem; font-weight: 600; }
.task-field small { color: var(--color-text-muted); font-weight: 400; }
.task-field input, .task-field textarea, .task-field select {
  width: 100%; box-sizing: border-box; padding: 0.65rem 0.75rem; border-radius: 7px;
  border: 1px solid var(--color-border); background: var(--color-surface); color: var(--color-text); font: inherit;
}
.task-field input:focus, .task-field textarea:focus, .task-field select:focus { outline: 2px solid var(--color-primary); outline-offset: 1px; }
.task-field textarea { resize: vertical; }
.create-error { margin: 0; color: var(--color-danger-text); font-size: 0.82rem; }

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
  transition: border-color 0.12s, box-shadow 0.12s, transform 0.08s;
  user-select: none;
  text-align: left;
  width: 100%;
  font: inherit;
  color: inherit;
}
.sum-card:hover { border-color: var(--color-border-strong, var(--color-border)); }
.sum-card:active { transform: translateY(1px); }
.sum-card:focus-visible { outline: 2px solid var(--color-primary); outline-offset: 2px; }
.sum-active {
  box-shadow: 0 0 0 2px var(--color-text);
  border-color: var(--color-text);
}

/* ── Search + active-filter chip toolbar ──────────────────────────────────── */
.tasks-toolbar { display: flex; align-items: center; gap: 0.6rem; flex-wrap: wrap; }
.toolbar-select { height: 38px; max-width: 180px; padding: 0 0.65rem; border: 1px solid var(--color-border); border-radius: 9px; background: var(--color-surface); color: var(--color-text); }
.task-search {
  flex: 1;
  min-width: 240px;
  display: flex;
  align-items: center;
  gap: 8px;
  height: 38px;
  padding: 0 12px;
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: 9px;
  color: var(--color-text-muted);
}
.task-search:focus-within { border-color: var(--color-primary); }
.task-search input {
  flex: 1;
  min-width: 0;
  border: none;
  outline: none;
  background: transparent;
  font: 500 13px/1 'Inter', sans-serif;
  color: var(--color-text);
}
.task-search input::placeholder { color: var(--color-text-muted); }
.task-search-x {
  display: grid;
  place-items: center;
  width: 20px;
  height: 20px;
  border: none;
  border-radius: 5px;
  background: transparent;
  color: var(--color-text-muted);
  cursor: pointer;
}
.task-search-x:hover { background: var(--color-surface-elevated); color: var(--color-text); }

.task-chip {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  height: 30px;
  padding: 0 10px;
  border: 1px solid var(--color-text);
  border-radius: 999px;
  background: var(--color-surface);
  color: var(--color-text);
  font: 500 12.5px/1 'Inter', sans-serif;
  cursor: pointer;
  flex-shrink: 0;
  transition: background 0.1s;
}
.task-chip:hover { background: var(--color-surface-elevated); }
.task-chip-k { color: var(--color-text-muted); }
.task-chip-v { font-weight: 700; }
.task-chip-x { color: var(--color-text-muted); }

/* ── Skeleton loader ──────────────────────────────────────────────────────── */
.skel-list { padding: 4px 0; }
.skel-row {
  display: grid;
  grid-template-columns: 130px 1fr 190px 130px 130px 28px;
  align-items: center;
  gap: 1rem;
  padding: 0.85rem 1.1rem;
  border-bottom: 1px solid var(--color-border);
}
.skel-row:last-child { border-bottom: none; }
.skel {
  background: linear-gradient(90deg, var(--color-surface-elevated) 25%, var(--color-border) 37%, var(--color-surface-elevated) 63%);
  background-size: 400% 100%;
  border-radius: 6px;
  animation: task-shimmer 1.4s ease-in-out infinite;
}
.skel-pill { height: 20px; border-radius: 999px; }
.skel-line { height: 12px; }
.skel-mark { width: 26px; height: 26px; border-radius: 6px; }
.skel-w60 { width: 60%; }
.skel-w40 { width: 55%; }
@keyframes task-shimmer { 0% { background-position: 100% 0; } 100% { background-position: 0 0; } }
@media (prefers-reduced-motion: reduce) { .skel { animation: none; } }

.empty-ic-muted { background: var(--color-surface-elevated); color: var(--color-text-muted); }

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
.empty-panel .hbtn { margin-top: 0.9rem; }

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
.tp-change_compliance_action { background: var(--color-purple-bg); color: var(--color-purple-text); }
.tp-release_gate_item    { background: var(--color-success-bg); color: var(--color-success-text); }
.tp-risk_item            { background: var(--color-warning-bg); color: var(--color-warning-text); }
.tp-eos_alert            { background: var(--color-warning-bg); color: var(--color-warning-text); }

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

.view-toggle { display: flex; gap: .2rem; }
.view-active { background: var(--color-surface-elevated); border-color: var(--color-primary); color: var(--color-primary); }
.task-board { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 1rem; align-items: start; }
.task-column { min-width: 0; background: var(--color-surface-elevated); border: 1px solid var(--color-border); border-radius: 8px; overflow: hidden; }
.task-column-head { display: flex; align-items: center; gap: .5rem; padding: .8rem; border-bottom: 1px solid var(--color-border); }
.task-column-head strong { font-size: .82rem; text-transform: uppercase; letter-spacing: .04em; }
.task-column-body { min-height: 18rem; padding: .6rem; display: flex; flex-direction: column; gap: .55rem; }
.board-card { display: flex; flex-direction: column; align-items: flex-start; gap: .35rem; width: 100%; padding: .75rem; border: 1px solid var(--color-border); border-radius: 7px; background: var(--color-surface); color: var(--color-text); text-align: left; cursor: pointer; box-shadow: 0 1px 2px rgba(0,0,0,.08); }
.board-card:hover { border-color: var(--color-primary); transform: translateY(-1px); }
.board-card-title { font-size: .84rem; font-weight: 650; }
.board-card-head { display: flex; align-items: flex-start; justify-content: space-between; gap: .5rem; width: 100%; }
.board-avatar { display: grid; place-items: center; width: 24px; height: 24px; flex: 0 0 24px; border-radius: 50%; background: var(--color-primary); color: white; font-size: .62rem; font-weight: 750; }
.board-avatar svg { width: 15px; height: 15px; fill: none; stroke: currentColor; stroke-width: 1.8; stroke-linecap: round; }
.board-card-meta { font-size: .72rem; color: var(--color-text-muted); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; max-width: 100%; }
.board-card-foot { display: flex; align-items: center; justify-content: space-between; width: 100%; margin-top: .2rem; font-size: .7rem; text-transform: capitalize; }
.priority-high { color: var(--color-danger); } .priority-medium { color: var(--color-warning); } .priority-low { color: var(--color-text-muted); }
.board-empty { margin: auto; color: var(--color-text-muted); font-size: .78rem; }
@media (max-width: 900px) { .task-board { grid-template-columns: 1fr; } }
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
