<!--
  CRANE — CRA Norm Engine
  Copyright (C) 2026 Ali Mohammad Hosseini
  SPDX-License-Identifier: AGPL-3.0-or-later
  This file is part of CRANE, free software under the GNU AGPL v3.0 or later.
  See <https://www.gnu.org/licenses/>.
-->
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
        ref="panelRef"
        class="dw-panel"
        :class="{ 'dw-panel-overdue': task.is_overdue }"
        role="dialog"
        aria-modal="true"
        :aria-label="task.title"
      >
        <!-- ── Head ────────────────────────────────────────────────────── -->
        <div class="dw-head" :class="{ 'dw-head-overdue': task.is_overdue }">
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
                <template v-else-if="task.entity_type === 'change_compliance_action'">
                  <rect x="3" y="3" width="14" height="14" rx="2"/><path d="M6.5 8h7M6.5 11h5"/>
                </template>
                <template v-else-if="task.entity_type === 'eos_alert'">
                  <circle cx="10" cy="10" r="7"/><path d="M10 6.5v3.5l2.5 1.5"/>
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

          <!-- Overdue banner — makes the most urgent signal impossible to miss. -->
          <div v-if="task.is_overdue && task.due_date" class="dw-overdue-banner">
            <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.8" width="14" height="14" stroke-linecap="round" stroke-linejoin="round">
              <circle cx="10" cy="10" r="7.5"/><path d="M10 6v4.5l2.5 1.5"/>
            </svg>
            Overdue by {{ relativeDue(task.due_date).replace(' overdue', '') }} — due {{ formatDate(task.due_date) }}
          </div>
        </div>

        <!-- ── Body ────────────────────────────────────────────────────── -->
        <div class="dw-body">

          <!-- Meta cells grid -->
          <div class="dw-meta">
            <!-- Status — editable entities get an inline "Update status" action -->
            <div class="dw-cell" :class="{ 'dw-cell-action': canEditStatus }">
              <div class="dw-k">
                {{ canEditStatus ? 'Update status' : 'Status' }}
                <span v-if="isSaving" class="dw-saving">Saving…</span>
                <span v-else-if="savedFlash" class="dw-saved">
                  <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="2.2" width="11" height="11" stroke-linecap="round" stroke-linejoin="round"><path d="M4 10.5l3.5 3.5 8.5-8.5"/></svg>
                  Saved
                </span>
              </div>
              <div class="dw-v">
                <template v-if="canEditStatus">
                  <select
                    v-model="localStatus"
                    class="dw-select"
                    :class="{ 'dw-select-saved': savedFlash }"
                    :disabled="isSaving"
                    @change="saveStatus"
                  >
                    <option v-for="opt in statusOptions" :key="opt.value" :value="opt.value">
                      {{ opt.label }}
                    </option>
                  </select>
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
              <template v-else-if="task.entity_type === 'eos_alert'">
                This product's support period is approaching end of life. Open the product record to review the support period details and take action.
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
        <!-- Inline dismiss confirmation — a lightweight two-step guard, mirroring
             the status-edit flow, so a task is never closed by a single click. -->
        <div v-if="confirmingDismiss && dismissAction" class="dw-foot dw-foot-confirm">
          <span class="dw-confirm-q">{{ dismissAction.confirmLabel }}</span>
          <div class="dw-confirm-actions">
            <AppButton :disabled="isDismissing" @click="cancelDismiss">Cancel</AppButton>
            <AppButton variant="danger" :disabled="isDismissing" @click="runDismiss">
              {{ isDismissing ? 'Working…' : dismissAction.label }}
            </AppButton>
          </div>
        </div>

        <div v-else class="dw-foot">
          <!-- Secondary dismiss/close action (left), distinct from the primary CTA. -->
          <button
            v-if="dismissAction"
            type="button"
            class="dw-dismiss-btn"
            @click="confirmingDismiss = true"
          >
            <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" width="13" height="13" stroke-linecap="round" stroke-linejoin="round"><path d="M3 8l3.5 3.5L13 4"/></svg>
            {{ dismissAction.label }}
          </button>
          <span class="dw-foot-spacer"></span>
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
import { computed, nextTick, onBeforeUnmount, ref, watch } from "vue";

import AppButton from "@/components/AppButton.vue";
import CommentThread from "@/components/CommentThread.vue";
import { changeService } from "@/services/change-service";
import { lifecycleNotificationService } from "@/services/lifecycle-notification-service";
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
// Brief "Saved ✓" confirmation flash after a successful status change.
const savedFlash  = ref(false);
let savedFlashTimer: ReturnType<typeof setTimeout> | null = null;

watch(() => props.task, (t) => {
  localStatus.value = t?.status ?? "";
  saveError.value   = null;
  savedFlash.value  = false;
}, { immediate: true });

// ── Accessibility: panel ref, focus management, scroll lock, Esc-to-close ───────
// The drawer is a modal dialog, so per WCAG it must: trap focus while open, move
// focus into itself on open, restore focus to the invoking element on close, lock
// the background scroll, and close on Escape.
const panelRef = ref<HTMLElement | null>(null);
let lastFocused: HTMLElement | null = null;

function onKeydown(event: KeyboardEvent): void {
  if (event.key === "Escape") {
    event.preventDefault();
    emit("close");
    return;
  }
  if (event.key === "Tab") trapFocus(event);
}

/** Keep Tab focus cycling within the drawer's focusable elements. */
function trapFocus(event: KeyboardEvent): void {
  const panel = panelRef.value;
  if (!panel) return;
  const focusable = panel.querySelectorAll<HTMLElement>(
    'a[href], button:not([disabled]), select:not([disabled]), textarea:not([disabled]), input:not([disabled]), [tabindex]:not([tabindex="-1"])',
  );
  if (focusable.length === 0) return;
  const first = focusable[0];
  const last  = focusable[focusable.length - 1];
  const active = document.activeElement as HTMLElement | null;

  if (event.shiftKey && active === first) {
    event.preventDefault();
    last.focus();
  } else if (!event.shiftKey && active === last) {
    event.preventDefault();
    first.focus();
  }
}

// Open/close side-effects driven by the presence of a task.
watch(() => props.task, (t) => {
  if (t) {
    lastFocused = document.activeElement as HTMLElement | null;
    document.addEventListener("keydown", onKeydown);
    document.body.style.overflow = "hidden";
    void nextTick(() => {
      // Focus the close button so keyboard users land inside the dialog.
      panelRef.value?.querySelector<HTMLElement>(".dw-close")?.focus();
    });
  } else {
    teardown();
    // Return focus to the row/control that opened the drawer.
    lastFocused?.focus?.();
    lastFocused = null;
  }
});

/** Remove the global listener and release the scroll lock. */
function teardown(): void {
  document.removeEventListener("keydown", onKeydown);
  document.body.style.overflow = "";
}

onBeforeUnmount(() => {
  teardown();
  if (savedFlashTimer) clearTimeout(savedFlashTimer);
});

const canEditStatus = computed(() =>
  props.task?.entity_type === "risk_item" ||
  props.task?.entity_type === "vulnerability_report" ||
  props.task?.entity_type === "change_compliance_action"
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
  if (props.task.entity_type === "change_compliance_action") {
    return [
      { value: "pending", label: "Pending" },
      { value: "in_progress", label: "In progress" },
      { value: "completed", label: "Completed" },
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
    } else if (props.task.entity_type === "change_compliance_action") {
      await changeService.updateComplianceAction(props.task.entity_id, { action_status: localStatus.value as any });
    }
    emit("statusUpdated", props.task, localStatus.value);
    // Flash a brief success confirmation (cleared after 2s).
    savedFlash.value = true;
    if (savedFlashTimer) clearTimeout(savedFlashTimer);
    savedFlashTimer = setTimeout(() => (savedFlash.value = false), 2000);
  } catch {
    saveError.value   = "Failed to save status.";
    localStatus.value = props.task.status;
  } finally {
    isSaving.value = false;
  }
}

// ── Dismiss / close a task ──────────────────────────────────────────────────────
// Some task types can be closed straight from the drawer by reusing the existing,
// already-audited entity endpoints. Each action moves the underlying entity to its
// terminal status, which removes it from My Tasks. Types without a clean one-click
// transition (risk item / vuln report use the inline status select above; gate items
// are closed via evidence review on their full record) return null.
interface DismissAction {
  label: string;
  confirmLabel: string;
  terminalStatus: string;
  run: (id: string) => Promise<unknown>;
}
const dismissAction = computed<DismissAction | null>(() => {
  switch (props.task?.entity_type) {
    case "eos_alert":
      return {
        label: "Dismiss alert",
        confirmLabel: "Dismiss this end-of-support alert?",
        terminalStatus: "dismissed",
        run: (id) => lifecycleNotificationService.dismiss(id),
      };
    case "change":
      return {
        label: "Close change",
        confirmLabel: "Close this change request?",
        terminalStatus: "closed",
        run: (id) => changeService.close(id),
      };
    default:
      return null;
  }
});

const confirmingDismiss = ref(false);
const isDismissing = ref(false);

function cancelDismiss(): void {
  confirmingDismiss.value = false;
}

async function runDismiss(): Promise<void> {
  const action = dismissAction.value;
  const task = props.task;
  if (!action || !task) return;
  isDismissing.value = true;
  saveError.value = null;
  try {
    await action.run(task.entity_id);
    // Reuse the existing status-update path: MyTasksView prunes the row and closes
    // the drawer when the new status is terminal.
    emit("statusUpdated", task, action.terminalStatus);
  } catch {
    saveError.value = "Failed to update this task. Please try again.";
  } finally {
    isDismissing.value = false;
    confirmingDismiss.value = false;
  }
}

// Reset the inline confirm whenever a different task is loaded into the drawer.
watch(() => props.task, () => {
  confirmingDismiss.value = false;
});

// ── Helpers ───────────────────────────────────────────────────────────────────
const createdByLabel = computed(() => {
  if (!props.task) return "Created by";
  if (props.task.entity_type === "vulnerability_report") return "Reported by";
  if (props.task.entity_type === "eos_alert") return "Assigned as";
  return "Initiated by";
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
    change_compliance_action: "Change action",
    release_gate_item:   "Gate item",
    risk_item:           "Risk item",
    eos_alert:           "EOL Alert",
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

/* Overdue accent — a thin danger bar down the left edge of the panel. */
.dw-panel-overdue { border-left: 3px solid var(--color-danger); }

/* ── Head ─────────────────────────────────────────────────────────────────── */
.dw-head {
  padding: 1.25rem 1.5rem 1.1rem;
  border-bottom: 1px solid var(--color-border);
  flex-shrink: 0;
}
/* Subtle tinted head when the task is overdue. */
.dw-head-overdue {
  background: linear-gradient(180deg, var(--color-danger-bg) 0%, transparent 100%);
}

/* Overdue banner under the title */
.dw-overdue-banner {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  margin-top: 0.75rem;
  padding: 0.5rem 0.7rem;
  border-radius: 7px;
  background: var(--color-danger-bg);
  border: 1px solid var(--color-danger-border);
  color: var(--color-danger-text);
  font-size: 0.78rem;
  font-weight: 600;
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
.dtp-change_compliance_action { background: var(--color-purple-bg); color: var(--color-purple-text); }
.dtp-release_gate_item    { background: var(--color-success-bg); color: var(--color-success-text); }
.dtp-risk_item            { background: var(--color-warning-bg); color: var(--color-warning-text); }
.dtp-eos_alert            { background: var(--color-warning-bg); color: var(--color-warning-text); }

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
.dw-close:focus-visible { outline: 2px solid var(--color-primary); outline-offset: 2px; }

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
.dw-saving { font-size: 0.66rem; font-weight: 600; color: var(--color-text-muted); text-transform: none; letter-spacing: 0; }

/* Editable-status cell reads as the primary inline action of the drawer. */
.dw-cell-action { background: var(--color-surface-elevated); }
.dw-cell-action .dw-k { display: flex; align-items: center; gap: 0.4rem; }
.dw-saved {
  display: inline-flex;
  align-items: center;
  gap: 3px;
  font-size: 0.66rem;
  font-weight: 700;
  text-transform: none;
  letter-spacing: 0;
  color: var(--color-success-text);
}
/* Green confirmation ring flashed on the select after a successful save. */
.dw-select-saved {
  border-color: var(--color-success);
  box-shadow: 0 0 0 3px var(--color-success-bg);
  transition: border-color 0.2s, box-shadow 0.2s;
}

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

.dw-foot-spacer { flex: 1; }

/* Secondary dismiss/close action */
.dw-dismiss-btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  height: 34px;
  padding: 0 12px;
  border-radius: 7px;
  border: 1px solid var(--color-border);
  background: var(--color-surface);
  color: var(--color-text-muted);
  font: 600 12.5px/1 'Inter', sans-serif;
  cursor: pointer;
  transition: background 0.12s, color 0.12s, border-color 0.12s;
}
.dw-dismiss-btn:hover { background: var(--color-success-bg); color: var(--color-success-text); border-color: var(--color-success-border); }
.dw-dismiss-btn:focus-visible { outline: 2px solid var(--color-primary); outline-offset: 2px; }

/* Inline confirm strip */
.dw-foot-confirm { justify-content: space-between; gap: 0.75rem; }
.dw-confirm-q { font-size: 0.82rem; font-weight: 600; color: var(--color-text); }
.dw-confirm-actions { display: flex; gap: 0.5rem; flex-shrink: 0; }

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

/* Respect reduced-motion: fade instead of slide, no scrim blur transition churn. */
@media (prefers-reduced-motion: reduce) {
  .drawer-enter-active,
  .drawer-leave-active { transition: opacity 0.15s ease; }
  .drawer-enter-from,
  .drawer-leave-to { transform: none; opacity: 0; }
}
</style>
