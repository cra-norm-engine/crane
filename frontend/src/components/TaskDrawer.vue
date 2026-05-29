<template>
  <Teleport to="body">
    <!-- Scrim -->
    <Transition name="scrim">
      <div v-if="task" class="dw-scrim" @click="$emit('close')" />
    </Transition>

    <!-- Drawer panel -->
    <Transition name="drawer">
      <aside
        v-if="task"
        class="dw-panel"
        role="dialog"
        aria-modal="true"
        :aria-label="task.title"
      >
        <!-- ── Head ────────────────────────────────────────────────────── -->
        <div class="dw-head">
          <div class="dw-topline">
            <!-- Type pill with icon -->
            <span class="dw-type-pill" :class="`dtp-${task.entity_type}`">
              <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.9" width="13" height="13" stroke-linecap="round" stroke-linejoin="round">
                <template v-if="task.entity_type === 'vulnerability_report'">
                  <path d="M10 2.5l7.5 13H2.5L10 2.5z"/><path d="M10 8v3"/><circle cx="10" cy="13.5" r=".6" fill="currentColor" stroke="none"/>
                </template>
                <template v-else-if="task.entity_type === 'risk_item'">
                  <rect x="3" y="3" width="14" height="14" rx="2"/><path d="M7 7h6M7 10h6M7 13h4"/>
                </template>
                <template v-else-if="task.entity_type === 'change'">
                  <path d="M3 5h14M3 9h14M3 13h9"/>
                </template>
                <template v-else>
                  <path d="M4 10.5l3.5 3.5 8.5-8.5"/><rect x="2.5" y="2.5" width="15" height="15" rx="2"/>
                </template>
              </svg>
              {{ formatEntityType(task.entity_type) }}
            </span>

            <!-- Severity / priority pill -->
            <span v-if="task.severity" class="dw-sev-pill" :class="`dsev-${task.severity}`">
              <span class="dsev-dot"></span>{{ task.severity }}
            </span>
            <span v-if="task.is_overdue" class="dw-sev-pill dsev-overdue">
              <span class="dsev-dot"></span>Overdue
            </span>

            <span class="dw-spacer"></span>

            <!-- Close button -->
            <button class="dw-close" @click="$emit('close')" aria-label="Close">
              <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" width="13" height="13" stroke-linecap="round">
                <path d="M3 3l10 10M13 3 3 13"/>
              </svg>
            </button>
          </div>

          <h2 class="dw-title">{{ task.title }}</h2>
        </div>

        <!-- ── Body ────────────────────────────────────────────────────── -->
        <div class="dw-body">

          <!-- Meta cells grid -->
          <div class="dw-meta">
            <!-- Status -->
            <div class="dw-cell">
              <div class="dw-k">Status</div>
              <div class="dw-v">
                <template v-if="canEditStatus">
                  <select
                    v-model="localStatus"
                    class="dw-select"
                    :disabled="isSaving"
                    @change="saveStatus"
                  >
                    <option v-for="opt in statusOptions" :key="opt.value" :value="opt.value">
                      {{ opt.label }}
                    </option>
                  </select>
                  <span v-if="isSaving" class="dw-saving">Saving…</span>
                </template>
                <span v-else class="dw-readonly">{{ formatLabel(task.status) }}</span>
              </div>
            </div>

            <!-- Assignee / created by -->
            <div class="dw-cell">
              <div class="dw-k">{{ createdByLabel }}</div>
              <div class="dw-v dw-person">
                <span class="dw-avatar">{{ creatorInitials }}</span>
                {{ task.created_by_name || '—' }}
              </div>
            </div>

            <!-- Due date -->
            <div class="dw-cell">
              <div class="dw-k">Due date</div>
              <div class="dw-v">
                <template v-if="task.due_date">
                  {{ formatDate(task.due_date) }}
                  <span class="dw-rel" :class="task.is_overdue ? 'dw-rel-urgent' : dueSoonClass">
                    · {{ relativeDue(task.due_date) }}
                  </span>
                </template>
                <span v-else class="dw-faint">No deadline</span>
              </div>
            </div>

            <!-- Product / release -->
            <div class="dw-cell">
              <div class="dw-k">Product / Release</div>
              <div class="dw-v dw-person">
                <span class="dw-prod-mark">{{ productInitials(task.product_name) }}</span>
                <span>
                  {{ task.product_name || '—' }}
                  <span v-if="task.release_version" class="dw-faint"> · {{ task.release_version }}</span>
                </span>
              </div>
            </div>
          </div>

          <!-- Save error -->
          <p v-if="saveError" class="dw-error">{{ saveError }}</p>

          <!-- Workflow note for read-only status entities -->
          <template v-if="!canEditStatus">
            <h4 class="dw-section-h">Details</h4>
            <p class="dw-note">
              <template v-if="task.entity_type === 'change'">
                Status is managed through the change workflow (submit → review → assess → close). Open the full record to take action.
              </template>
              <template v-else-if="task.entity_type === 'release_gate_item'">
                Gate item status is updated through evidence review. Open the full record to review evidence and decisions.
              </template>
            </p>
          </template>

          <div class="dw-divider"></div>

          <!-- Comments -->
          <h4 class="dw-section-h">Activity &amp; comments</h4>
          <div class="dw-comments-wrap">
            <CommentThread
              :entity-type="task.entity_type"
              :entity-id="task.entity_id"
            />
          </div>

        </div>

        <!-- ── Footer ──────────────────────────────────────────────────── -->
        <div class="dw-foot">
          <AppButton @click="$emit('close')">Close</AppButton>
          <AppButton variant="primary" @click="$emit('navigate', task)">
            Open full record
            <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" width="13" height="13" stroke-linecap="round"><path d="M3 8h10M9 4l4 4-4 4"/></svg>
          </AppButton>
        </div>

      </aside>
    </Transition>
  </Teleport>
</template>

<script setup lang="ts">
import { computed, ref, watch } from "vue";

import AppButton from "@/components/AppButton.vue";
import CommentThread from "@/components/CommentThread.vue";
import { riskItemService } from "@/services/risk-item-service";
import { vulnerabilityReportService } from "@/services/vulnerability-report-service";
import type { TaskItem } from "@/types/task";

const props = defineProps<{ task: TaskItem | null }>();
const emit  = defineEmits<{
  (e: "close"): void;
  (e: "navigate", task: TaskItem): void;
  (e: "statusUpdated", task: TaskItem, newStatus: string): void;
}>();

// ── Status editing ─────────────────────────────────────────────────────────────
const localStatus = ref("");
const isSaving    = ref(false);
const saveError   = ref<string | null>(null);

watch(() => props.task, (t) => {
  localStatus.value = t?.status ?? "";
  saveError.value   = null;
}, { immediate: true });

const canEditStatus = computed(() =>
  props.task?.entity_type === "risk_item" ||
  props.task?.entity_type === "vulnerability_report"
);

const statusOptions = computed(() => {
  if (!props.task) return [];
  if (props.task.entity_type === "risk_item") {
    return [
      { value: "open",        label: "Open" },
      { value: "in_progress", label: "In progress" },
      { value: "mitigated",   label: "Mitigated" },
      { value: "accepted",    label: "Accepted" },
      { value: "closed",      label: "Closed" },
    ];
  }
  if (props.task.entity_type === "vulnerability_report") {
    return [
      { value: "reported",        label: "Reported" },
      { value: "triaged",         label: "Triaged" },
      { value: "fix_in_progress", label: "Fix in progress" },
      { value: "fixed",           label: "Fixed" },
      { value: "embargo",         label: "Embargo" },
      { value: "disclosed",       label: "Disclosed" },
      { value: "retired",         label: "Retired" },
    ];
  }
  return [];
});

async function saveStatus(): Promise<void> {
  if (!props.task || !canEditStatus.value) return;
  isSaving.value  = true;
  saveError.value = null;
  try {
    if (props.task.entity_type === "risk_item") {
      await riskItemService.update(props.task.entity_id, { status: localStatus.value as any });
    } else if (props.task.entity_type === "vulnerability_report") {
      await vulnerabilityReportService.update(props.task.entity_id, { status: localStatus.value as any });
    }
    emit("statusUpdated", props.task, localStatus.value);
  } catch {
    saveError.value   = "Failed to save status.";
    localStatus.value = props.task.status;
  } finally {
    isSaving.value = false;
  }
}

// ── Helpers ───────────────────────────────────────────────────────────────────
const createdByLabel = computed(() => {
  if (!props.task) return "Created by";
  return props.task.entity_type === "vulnerability_report" ? "Reported by" : "Initiated by";
});

const creatorInitials = computed(() => {
  const name = props.task?.created_by_name;
  if (!name) return "?";
  const parts = name.trim().split(/\s+/);
  return parts.length === 1
    ? parts[0].slice(0, 2).toUpperCase()
    : (parts[0][0] + parts[parts.length - 1][0]).toUpperCase();
});

const dueSoonClass = computed(() => {
  if (!props.task?.due_date) return "";
  const days = Math.ceil((new Date(props.task.due_date).getTime() - Date.now()) / 86_400_000);
  if (days <= 1) return "dw-rel-urgent";
  if (days <= 3) return "dw-rel-soon";
  return "";
});

function relativeDue(iso: string): string {
  const days = Math.ceil((new Date(iso).getTime() - Date.now()) / 86_400_000);
  if (days < 0)  return `${Math.abs(days)}d overdue`;
  if (days === 0) return "Today";
  if (days === 1) return "Tomorrow";
  if (days <= 7)  return `In ${days} days`;
  return `In ${Math.ceil(days / 7)}w`;
}

function productInitials(name: string | null | undefined): string {
  if (!name) return "?";
  const words = name.trim().split(/\s+/);
  return words.length === 1
    ? words[0].slice(0, 2).toUpperCase()
    : (words[0][0] + words[1][0]).toUpperCase();
}

function formatEntityType(type: string): string {
  const map: Record<string, string> = {
    vulnerability_report: "Vulnerability",
    change:              "Change",
    release_gate_item:   "Gate item",
    risk_item:           "Risk item",
  };
  return map[type] ?? type;
}

function formatLabel(s: string): string {
  return s.replace(/_/g, " ");
}

function formatDate(iso: string): string {
  return new Date(iso).toLocaleDateString("en-GB", { day: "numeric", month: "short", year: "numeric" });
}
</script>

<style scoped>
/* ── Scrim ────────────────────────────────────────────────────────────────── */
.dw-scrim {
  position: fixed;
  inset: 0;
  z-index: 200;
  background: oklch(0.12 0.012 150 / 0.32);
  backdrop-filter: blur(1.5px);
}

/* ── Panel ────────────────────────────────────────────────────────────────── */
.dw-panel {
  position: fixed;
  top: 0;
  right: 0;
  bottom: 0;
  width: 480px;
  max-width: 92vw;
  z-index: 201;
  display: flex;
  flex-direction: column;
  background: var(--color-surface);
  border-left: 1px solid var(--color-border);
  box-shadow: -12px 0 40px -16px rgba(0, 0, 0, 0.28);
}

/* ── Head ─────────────────────────────────────────────────────────────────── */
.dw-head {
  padding: 1.25rem 1.5rem 1.1rem;
  border-bottom: 1px solid var(--color-border);
  flex-shrink: 0;
}

.dw-topline {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-bottom: 0.85rem;
}

.dw-spacer { flex: 1; }

/* Type pill with icon */
.dw-type-pill {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  padding: 4px 9px 4px 7px;
  border-radius: 6px;
  font-size: 0.72rem;
  font-weight: 600;
  white-space: nowrap;
}
.dtp-vulnerability_report { background: var(--color-danger-bg);  color: var(--color-danger-text); }
.dtp-change               { background: var(--color-info-bg);    color: var(--color-info-text); }
.dtp-release_gate_item    { background: var(--color-success-bg); color: var(--color-success-text); }
.dtp-risk_item            { background: var(--color-warning-bg); color: var(--color-warning-text); }

/* Severity pill */
.dw-sev-pill {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  padding: 3px 9px;
  border-radius: 999px;
  font-size: 0.72rem;
  font-weight: 600;
  text-transform: capitalize;
  background: var(--color-surface-elevated);
  color: var(--color-text-muted);
  border: 1px solid var(--color-border);
}
.dsev-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--color-text-muted);
  flex-shrink: 0;
}
.dsev-critical .dsev-dot, .dsev-high .dsev-dot, .dsev-overdue .dsev-dot { background: var(--color-danger); }
.dsev-critical, .dsev-high, .dsev-overdue { background: var(--color-danger-bg); color: var(--color-danger-text); border-color: var(--color-danger-border); }
.dsev-medium .dsev-dot { background: var(--color-warning); }
.dsev-medium  { background: var(--color-warning-bg); color: var(--color-warning-text); border-color: var(--color-warning-border); }
.dsev-low .dsev-dot { background: var(--color-success); }
.dsev-low     { background: var(--color-success-bg); color: var(--color-success-text); border-color: var(--color-success-border); }

/* Close button */
.dw-close {
  width: 30px;
  height: 30px;
  border-radius: 6px;
  border: 1px solid var(--color-border);
  background: var(--color-surface);
  color: var(--color-text-muted);
  display: grid;
  place-items: center;
  cursor: pointer;
  flex-shrink: 0;
  transition: background 0.12s, color 0.12s;
}
.dw-close:hover { background: var(--color-surface-elevated); color: var(--color-text); }

.dw-title {
  margin: 0;
  font-size: 1.1rem;
  font-weight: 700;
  letter-spacing: -0.01em;
  line-height: 1.35;
  color: var(--color-text);
}

/* ── Body ─────────────────────────────────────────────────────────────────── */
.dw-body {
  flex: 1;
  overflow-y: auto;
  padding: 1.25rem 1.5rem 1.5rem;
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

/* Meta cells — 2-column grid with 1px gap acting as borders */
.dw-meta {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1px;
  background: var(--color-border);
  border: 1px solid var(--color-border);
  border-radius: 10px;
  overflow: hidden;
}

.dw-cell {
  background: var(--color-surface);
  padding: 0.75rem 0.9rem;
}

.dw-k {
  font-size: 0.67rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.07em;
  color: var(--color-text-muted);
  margin-bottom: 0.3rem;
}

.dw-v {
  font-size: 0.84rem;
  font-weight: 500;
  color: var(--color-text);
}

.dw-person {
  display: flex;
  align-items: center;
  gap: 0.45rem;
}

/* Avatar circle */
.dw-avatar {
  width: 22px;
  height: 22px;
  border-radius: 50%;
  background: var(--color-success-bg);
  color: var(--color-success-text);
  display: grid;
  place-items: center;
  font-size: 0.6rem;
  font-weight: 700;
  flex-shrink: 0;
}

/* Product mark badge */
.dw-prod-mark {
  width: 22px;
  height: 22px;
  border-radius: 5px;
  background: var(--color-surface-elevated);
  border: 1px solid var(--color-border);
  display: grid;
  place-items: center;
  font-size: 0.6rem;
  font-weight: 700;
  color: var(--color-text);
  flex-shrink: 0;
}

/* Status select */
.dw-select {
  appearance: none;
  -webkit-appearance: none;
  border: 1px solid var(--color-border);
  background: var(--color-surface);
  border-radius: 6px;
  padding: 5px 26px 5px 9px;
  font: 600 12.5px/1 'Inter', sans-serif;
  color: var(--color-text);
  cursor: pointer;
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' viewBox='0 0 24 24' fill='none' stroke='%23888' stroke-width='2' stroke-linecap='round'%3E%3Cpath d='M6 9l6 6 6-6'/%3E%3C/svg%3E");
  background-repeat: no-repeat;
  background-position: right 8px center;
  min-width: 9rem;
  transition: border-color 0.12s;
}
.dw-select:hover  { border-color: var(--color-primary); }
.dw-select:disabled { opacity: 0.55; cursor: not-allowed; }

.dw-readonly {
  text-transform: capitalize;
  color: var(--color-text-muted);
}
.dw-saving { font-size: 0.72rem; color: var(--color-text-muted); margin-left: 0.4rem; }

/* Due date relative label */
.dw-rel       { font-size: 0.78rem; font-weight: 500; color: var(--color-text-muted); }
.dw-rel-soon  { color: var(--color-warning); font-weight: 600; }
.dw-rel-urgent { color: var(--color-danger); font-weight: 600; }
.dw-faint     { color: var(--color-text-muted); opacity: 0.6; }

/* Error */
.dw-error {
  font-size: 0.8rem;
  color: var(--color-danger-text);
  background: var(--color-danger-bg);
  border: 1px solid var(--color-danger-border);
  border-radius: 6px;
  padding: 0.5rem 0.75rem;
  margin: 0;
}

/* Section heading */
.dw-section-h {
  font-size: 0.68rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: var(--color-text-muted);
  margin: 0;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

/* Workflow note */
.dw-note {
  font-size: 0.82rem;
  color: var(--color-text-muted);
  line-height: 1.55;
  margin: 0;
  padding: 0.7rem 0.9rem;
  background: var(--color-surface-elevated);
  border: 1px solid var(--color-border);
  border-radius: 8px;
}

/* Divider */
.dw-divider {
  height: 1px;
  background: var(--color-border);
  margin: 0.25rem 0;
}

/* Comments wrapper — overrides CommentThread defaults to match drawer style */
.dw-comments-wrap {
  flex: 1;
}

/* ── Footer ───────────────────────────────────────────────────────────────── */
.dw-foot {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 0.6rem;
  padding: 0.85rem 1.5rem;
  border-top: 1px solid var(--color-border);
  flex-shrink: 0;
  background: var(--color-surface);
}

/* Footer buttons rendered by AppButton component */

/* ── Transitions ──────────────────────────────────────────────────────────── */
.scrim-enter-active,
.scrim-leave-active {
  transition: opacity 0.2s ease;
}
.scrim-enter-from,
.scrim-leave-to {
  opacity: 0;
}

.drawer-enter-active,
.drawer-leave-active {
  transition: transform 0.26s cubic-bezier(0.4, 0, 0.2, 1);
}
.drawer-enter-from,
.drawer-leave-to {
  transform: translateX(100%);
}
</style>
