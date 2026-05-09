<template>
  <Teleport to="body">
    <Transition name="drawer">
      <div v-if="task" class="drawer-backdrop" @click.self="$emit('close')">
        <aside class="drawer" role="dialog" aria-modal="true" :aria-label="task.title">

          <!-- ── Header ── -->
          <div class="drawer-header">
            <div class="drawer-header-left">
              <span class="type-badge" :class="`type-${task.entity_type}`">
                {{ formatEntityType(task.entity_type) }}
              </span>
              <span v-if="task.severity" class="severity-badge" :class="`severity-${task.severity}`">
                {{ task.severity }}
              </span>
              <span v-if="task.is_overdue" class="overdue-pill">Overdue</span>
            </div>
            <button class="close-btn" @click="$emit('close')" aria-label="Close">✕</button>
          </div>

          <div class="drawer-body">
            <h2 class="drawer-title">{{ task.title }}</h2>

            <!-- ── Meta grid ── -->
            <dl class="meta-grid">
              <div class="meta-row">
                <dt>Status</dt>
                <dd>
                  <!-- Editable for risk items and vulnerability reports -->
                  <template v-if="canEditStatus">
                    <select
                      v-model="localStatus"
                      class="status-select"
                      :disabled="isSaving"
                      @change="saveStatus"
                    >
                      <option v-for="opt in statusOptions" :key="opt.value" :value="opt.value">
                        {{ opt.label }}
                      </option>
                    </select>
                    <span v-if="isSaving" class="saving-hint muted">Saving…</span>
                  </template>
                  <!-- Read-only for changes and gate items -->
                  <span v-else class="status-readonly">{{ formatLabel(task.status) }}</span>
                </dd>
              </div>

              <div class="meta-row">
                <dt>Due date</dt>
                <dd :class="task.is_overdue ? 'text-danger' : ''">
                  {{ task.due_date ? formatDate(task.due_date) : "—" }}
                </dd>
              </div>

              <div class="meta-row" v-if="task.product_name">
                <dt>Product</dt>
                <dd>{{ task.product_name }}<span v-if="task.release_version" class="muted"> · {{ task.release_version }}</span></dd>
              </div>

              <div class="meta-row" v-if="task.created_by_name">
                <dt>{{ createdByLabel }}</dt>
                <dd>{{ task.created_by_name }}</dd>
              </div>

              <div class="meta-row" v-if="saveError">
                <dt></dt>
                <dd class="text-danger">{{ saveError }}</dd>
              </div>
            </dl>

            <!-- ── Status change note for workflow-locked entities ── -->
            <p v-if="!canEditStatus" class="workflow-note muted">
              <template v-if="task.entity_type === 'change'">
                Status is managed through the change workflow (submit → review → assess → close).
              </template>
              <template v-else-if="task.entity_type === 'release_gate_item'">
                Gate item status is updated through evidence review.
              </template>
            </p>

            <!-- ── Comments ── -->
            <div class="drawer-section">
              <CommentThread
                :entity-type="task.entity_type"
                :entity-id="task.entity_id"
              />
            </div>
          </div>

          <!-- ── Footer: navigate to full record ── -->
          <div class="drawer-footer">
            <button class="btn btn-secondary" @click="$emit('close')">Close</button>
            <button class="btn btn-primary" @click="$emit('navigate', task)">
              Open full record →
            </button>
          </div>

        </aside>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup lang="ts">
import { computed, ref, watch } from "vue";

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

// ── Status editing ────────────────────────────────────────────────────────────
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
  return new Date(iso).toLocaleDateString(undefined, { dateStyle: "medium" });
}
</script>

<style scoped>
/* ── Backdrop ────────────────────────────────────────────────────────────────── */
.drawer-backdrop {
  position: fixed;
  inset: 0;
  z-index: 200;
  background: rgba(0, 0, 0, 0.45);
  backdrop-filter: blur(3px);
  display: flex;
  justify-content: flex-end;
}

/* ── Drawer panel ───────────────────────────────────────────────────────────── */
.drawer {
  width: min(480px, 100vw);
  height: 100%;
  display: flex;
  flex-direction: column;
  background: var(--color-surface, #0f172a);
  border-left: 1px solid var(--color-border, rgba(148,163,184,0.2));
  box-shadow: -8px 0 40px rgba(0,0,0,0.4);
  overflow: hidden;
}

/* ── Header ─────────────────────────────────────────────────────────────────── */
.drawer-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 1rem 1.25rem;
  border-bottom: 1px solid var(--color-border, rgba(148,163,184,0.15));
  gap: 0.75rem;
  flex-shrink: 0;
}

.drawer-header-left {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  flex-wrap: wrap;
}

.close-btn {
  background: none;
  border: none;
  font-size: 1.1rem;
  cursor: pointer;
  color: var(--color-text-muted, #94a3b8);
  padding: 0.2rem 0.4rem;
  border-radius: 4px;
  line-height: 1;
  flex-shrink: 0;
  transition: color 0.12s;
}
.close-btn:hover { color: var(--color-text, #e2e8f0); }

/* ── Body ───────────────────────────────────────────────────────────────────── */
.drawer-body {
  flex: 1;
  overflow-y: auto;
  padding: 1.25rem;
  display: flex;
  flex-direction: column;
  gap: 1.25rem;
}

.drawer-title {
  margin: 0;
  font-size: 1.1rem;
  font-weight: 700;
  color: var(--color-text, #e2e8f0);
  line-height: 1.4;
}

/* ── Meta grid ──────────────────────────────────────────────────────────────── */
.meta-grid {
  display: grid;
  gap: 0.6rem;
  margin: 0;
  border: 1px solid var(--color-border, rgba(148,163,184,0.15));
  border-radius: 8px;
  padding: 0.9rem 1rem;
  background: var(--color-surface-soft, rgba(15,23,42,0.4));
}

.meta-row {
  display: grid;
  grid-template-columns: 7rem 1fr;
  gap: 0.5rem;
  align-items: start;
}

.meta-row dt {
  font-size: 0.8rem;
  font-weight: 600;
  color: var(--color-text-muted, #94a3b8);
  padding-top: 0.15rem;
}

.meta-row dd {
  margin: 0;
  font-size: 0.88rem;
  color: var(--color-text, #e2e8f0);
  display: flex;
  align-items: center;
  gap: 0.5rem;
  flex-wrap: wrap;
}

/* ── Status select ──────────────────────────────────────────────────────────── */
.status-select {
  border: 1px solid var(--color-border, rgba(148,163,184,0.2));
  border-radius: 6px;
  padding: 0.25rem 0.6rem;
  font-size: 0.82rem;
  background: var(--color-surface-elevated, rgba(255,255,255,0.06));
  color: var(--color-text, #e2e8f0);
  cursor: pointer;
  min-width: 10rem;
}

.status-select:disabled { opacity: 0.6; cursor: not-allowed; }

.status-readonly {
  text-transform: capitalize;
  color: var(--color-text-muted, #94a3b8);
}

.saving-hint { font-size: 0.78rem; }

/* ── Workflow note ──────────────────────────────────────────────────────────── */
.workflow-note {
  font-size: 0.8rem;
  margin: 0;
  padding: 0.6rem 0.8rem;
  border-radius: 6px;
  border: 1px solid var(--color-border, rgba(148,163,184,0.15));
  background: var(--color-surface-soft, rgba(15,23,42,0.3));
}

/* ── Comments section ───────────────────────────────────────────────────────── */
.drawer-section {
  border-top: 1px solid var(--color-border, rgba(148,163,184,0.15));
  padding-top: 1rem;
}

/* ── Footer ─────────────────────────────────────────────────────────────────── */
.drawer-footer {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 0.75rem;
  padding: 1rem 1.25rem;
  border-top: 1px solid var(--color-border, rgba(148,163,184,0.15));
  flex-shrink: 0;
}

/* ── Buttons ─────────────────────────────────────────────────────────────────── */
.btn {
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
  padding: 0.55rem 1.1rem;
  border-radius: 8px;
  font-size: 0.88rem;
  font-weight: 600;
  cursor: pointer;
  border: 1px solid transparent;
  transition: opacity 0.12s, background 0.12s;
  white-space: nowrap;
}

.btn-secondary {
  background: var(--color-surface-elevated, rgba(255,255,255,0.06));
  border-color: var(--color-border, rgba(148,163,184,0.2));
  color: var(--color-text, #e2e8f0);
}

.btn-primary {
  background: linear-gradient(135deg, rgba(99,102,241,0.9), rgba(79,70,229,0.9));
  color: #fff;
  border-color: rgba(99,102,241,0.4);
}

.btn-primary:hover { opacity: 0.9; }

/* ── Badges ──────────────────────────────────────────────────────────────────── */
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

.severity-badge {
  font-size: 0.7rem;
  font-weight: 700;
  padding: 0.15rem 0.45rem;
  border-radius: 4px;
  text-transform: capitalize;
}
.severity-critical { background: rgba(220,38,38,0.2);  color: #fca5a5; }
.severity-high     { background: rgba(217,119,6,0.2);  color: #fcd34d; }
.severity-medium   { background: rgba(202,138,4,0.15); color: #fde68a; }
.severity-low      { background: rgba(22,163,74,0.15); color: #86efac; }

.overdue-pill {
  font-size: 0.7rem;
  font-weight: 700;
  padding: 0.15rem 0.45rem;
  border-radius: 4px;
  background: rgba(248,113,113,0.2);
  color: #f87171;
}

/* ── Colours ─────────────────────────────────────────────────────────────────── */
.text-danger { color: #f87171; font-weight: 600; }

/* ── Slide-in transition ─────────────────────────────────────────────────────── */
.drawer-enter-active,
.drawer-leave-active {
  transition: opacity 0.2s ease;
}
.drawer-enter-active .drawer,
.drawer-leave-active .drawer {
  transition: transform 0.25s cubic-bezier(0.4, 0, 0.2, 1);
}
.drawer-enter-from,
.drawer-leave-to {
  opacity: 0;
}
.drawer-enter-from .drawer,
.drawer-leave-to .drawer {
  transform: translateX(100%);
}
</style>
