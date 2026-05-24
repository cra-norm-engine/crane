<template>
  <section class="page" v-if="change">
    <!-- Page header: title, status badge, action buttons -->
    <header class="page-header card">
      <div class="header-left">
        <div class="header-meta">
          <div class="header-badges">
            <span class="type-badge" :class="`type-${change.change_type}`">
              {{ formatLabel(change.change_type) }}
            </span>
            <span class="status-badge" :class="`status-${change.status}`">
              {{ formatLabel(change.status) }}
            </span>
            <span v-if="change.assessment?.is_substantial" class="substantial-pill">
              Substantial
            </span>
          </div>
          <h1 class="page-title">{{ change.title }}</h1>
          <p class="muted page-subtitle">{{ change.description }}</p>
        </div>
      </div>

      <!-- Workflow action buttons — shown only for valid next transitions -->
      <div class="header-actions">
        <!-- draft → submitted -->
        <button
          v-if="change.status === 'draft'"
          class="btn btn-primary"
          :disabled="isActing"
          @click="doSubmit"
        >
          Submit for review
        </button>

        <!-- submitted → under_review (claim) -->
        <button
          v-if="change.status === 'submitted'"
          class="btn btn-primary"
          :disabled="isActing"
          @click="doClaim"
        >
          Claim &amp; start review
        </button>

        <!-- under_review → assessed (show assessment form) -->
        <button
          v-if="change.status === 'under_review' && !change.assessment"
          class="btn btn-primary"
          :disabled="isActing"
          @click="openAssessModal"
        >
          Submit assessment
        </button>

        <!-- assessed | action_required → closed -->
        <button
          v-if="change.status === 'assessed' || change.status === 'action_required'"
          class="btn btn-primary"
          :disabled="isActing"
          @click="doClose"
        >
          Close change
        </button>

        <!-- draft → editable fields -->
        <button
          v-if="change.status === 'draft'"
          class="btn btn-secondary"
          @click="openEditModal"
        >
          Edit draft
        </button>
      </div>
    </header>

    <!-- Feedback banners -->
    <div v-if="errorMessage" class="card feedback feedback-error">{{ errorMessage }}</div>
    <div v-if="successMessage" class="card feedback feedback-success">{{ successMessage }}</div>

    <!-- Workflow timeline strip -->
    <div class="timeline-strip card">
      <div
        v-for="(step, idx) in workflowSteps"
        :key="step.status"
        class="timeline-step"
        :class="{
          'step-done': isStepDone(step.status),
          'step-active': change.status === step.status,
          'step-pending': !isStepDone(step.status) && change.status !== step.status,
        }"
      >
        <div class="step-dot"></div>
        <div class="step-label">{{ step.label }}</div>
        <div v-if="idx < workflowSteps.length - 1" class="step-connector"></div>
      </div>
    </div>

    <div class="detail-grid">
      <!-- Left column: metadata + assessment -->
      <div class="detail-left">

        <!-- Basic info card -->
        <section class="card">
          <h2 class="section-title">Details</h2>
          <dl class="kv-list">
            <div class="kv-row">
              <dt>Product</dt>
              <dd>{{ productName ?? "—" }}</dd>
            </div>
            <div class="kv-row">
              <dt>Release</dt>
              <dd>{{ releaseVersion ?? "—" }}</dd>
            </div>
            <div class="kv-row">
              <dt>Change date</dt>
              <dd>{{ formatDate(change.change_date) }}</dd>
            </div>
            <div class="kv-row">
              <dt>Initiator</dt>
              <dd>{{ initiatorName ?? "—" }}</dd>
            </div>
            <div class="kv-row">
              <dt>Assessor</dt>
              <dd>{{ assessorName ?? "—" }}</dd>
            </div>
            <div class="kv-row">
              <dt>Submitted</dt>
              <dd>{{ formatDate(change.submitted_at) }}</dd>
            </div>
            <div class="kv-row">
              <dt>Assessed</dt>
              <dd>{{ formatDate(change.assessed_at) }}</dd>
            </div>
            <div class="kv-row">
              <dt>Closed</dt>
              <dd>{{ formatDate(change.closed_at) }}</dd>
            </div>
            <div class="kv-row">
              <dt>Created</dt>
              <dd>{{ formatDate(change.created_at) }}</dd>
            </div>
          </dl>

          <!-- Task assignment -->
          <div style="margin-top: 1rem; padding-top: 1rem; border-top: 1px solid var(--color-border, #e2e8f0);">
            <AssigneeSelector
              :assigned-to-user-id="change.assigned_to_user_id ?? null"
              :model-due-date="change.due_date ?? null"
              @update:assigned-to-user-id="(id) => updateChangeAssignment({ assigned_to_user_id: id })"
              @update:model-due-date="(d) => updateChangeAssignment({ due_date: d })"
            />
          </div>
        </section>

        <!-- Assessment results card (shown once assessed) -->
        <section v-if="change.assessment" class="card">
          <div class="section-header-row">
            <h2 class="section-title">Substantiality assessment</h2>
            <span
              class="substantial-verdict"
              :class="change.assessment.is_substantial ? 'verdict-substantial' : 'verdict-not'"
            >
              {{ change.assessment.is_substantial ? "Substantial" : "Not substantial" }}
            </span>
          </div>

          <!-- Five CRA substantiality criteria -->
          <ul class="criteria-list">
            <li class="criteria-item" :class="change.assessment.alters_intended_use ? 'criteria-true' : 'criteria-false'">
              <span class="criteria-icon">{{ change.assessment.alters_intended_use ? "✓" : "✗" }}</span>
              Alters intended use
            </li>
            <li class="criteria-item" :class="change.assessment.introduces_new_threat_vectors ? 'criteria-true' : 'criteria-false'">
              <span class="criteria-icon">{{ change.assessment.introduces_new_threat_vectors ? "✓" : "✗" }}</span>
              Introduces new threat vectors
            </li>
            <li class="criteria-item" :class="change.assessment.enables_new_attack_scenarios ? 'criteria-true' : 'criteria-false'">
              <span class="criteria-icon">{{ change.assessment.enables_new_attack_scenarios ? "✓" : "✗" }}</span>
              Enables new attack scenarios
            </li>
            <li class="criteria-item" :class="change.assessment.changes_attack_likelihood ? 'criteria-true' : 'criteria-false'">
              <span class="criteria-icon">{{ change.assessment.changes_attack_likelihood ? "✓" : "✗" }}</span>
              Changes attack likelihood
            </li>
            <li class="criteria-item" :class="change.assessment.changes_attack_impact ? 'criteria-true' : 'criteria-false'">
              <span class="criteria-icon">{{ change.assessment.changes_attack_impact ? "✓" : "✗" }}</span>
              Changes attack impact
            </li>
          </ul>

          <!-- Assessor reasoning -->
          <div class="reasoning-block">
            <span class="field-label">Reasoning</span>
            <p>{{ change.assessment.reasoning }}</p>
          </div>

          <div class="reasoning-meta muted">
            Decision date: {{ formatDate(change.assessment.decision_date) }}
          </div>
        </section>
      </div>

      <!-- Right column: compliance actions -->
      <div class="detail-right">
        <section class="card">
          <div class="section-header-row">
            <h2 class="section-title">Compliance actions</h2>
            <span v-if="change.assessment?.is_substantial" class="actions-count muted">
              {{ completedActionCount }}/{{ totalActionCount }} complete
            </span>
          </div>

          <!-- No assessment yet -->
          <div v-if="!change.assessment" class="empty-panel">
            No compliance actions yet. Complete the assessment to see required actions.
          </div>

          <!-- Not substantial — no actions needed -->
          <div v-else-if="!change.assessment.is_substantial" class="empty-panel">
            No compliance actions required — this change was not assessed as substantial.
          </div>

          <!-- Compliance action cards -->
          <div v-else class="action-list">
            <div
              v-for="action in change.assessment.compliance_actions"
              :key="action.id"
              class="action-card"
              :class="`action-${action.action_status}`"
            >
              <!-- Top row: type label + status badge + action button -->
              <div class="action-top">
                <div>
                  <span class="action-type">{{ formatActionType(action.action_type) }}</span>
                  <span class="action-status-badge" :class="`ast-${action.action_status}`">
                    {{ formatLabel(action.action_status) }}
                  </span>
                </div>
                <div class="action-btn-group">
                  <!-- Mark complete — shown for pending and in_progress -->
                  <button
                    v-if="action.action_status !== 'completed'"
                    class="btn btn-sm btn-secondary"
                    :disabled="isActing"
                    @click="markAction(action.id, 'completed')"
                  >
                    Mark complete
                  </button>
                  <!-- Restore — shown only when completed, allows reverting -->
                  <button
                    v-else
                    class="btn btn-sm btn-restore"
                    :disabled="isActing"
                    @click="markAction(action.id, 'in_progress')"
                    title="Revert to in progress"
                  >
                    ↩ Restore
                  </button>
                </div>
              </div>

              <!-- Due date display -->
              <div class="action-meta muted">
                <span v-if="action.due_date">Due: {{ formatDate(action.due_date) }}</span>
                <span v-else>No due date set</span>
              </div>

              <!-- Notes display -->
              <div class="action-notes" v-if="action.notes">
                <span class="field-label">Notes</span>
                <p>{{ action.notes }}</p>
              </div>

              <!-- Inline edit form — always available regardless of status -->
              <details class="action-edit-details">
                <summary class="action-edit-trigger muted">Edit due date / notes</summary>
                <form
                  class="action-edit-form"
                  @submit.prevent="saveActionEdit(action.id)"
                >
                  <label class="field">
                    <span class="field-label">Due date</span>
                    <input
                      type="date"
                      :value="actionEdits[action.id]?.due_date ?? action.due_date ?? ''"
                      @change="setActionEdit(action.id, 'due_date', ($event.target as HTMLInputElement).value)"
                    />
                  </label>
                  <label class="field">
                    <span class="field-label">Notes</span>
                    <textarea
                      rows="2"
                      :value="actionEdits[action.id]?.notes ?? action.notes ?? ''"
                      @input="setActionEdit(action.id, 'notes', ($event.target as HTMLTextAreaElement).value)"
                    />
                  </label>
                  <button type="submit" class="btn btn-sm btn-secondary" :disabled="isActing">
                    Save
                  </button>
                </form>
              </details>
            </div>
          </div>
        </section>
      </div>
    </div>

    <!-- Comment thread for this change record -->
    <div class="card" style="margin-top: 1.5rem;">
      <CommentThread entity-type="change" :entity-id="change.id" />
    </div>
  </section>

  <!-- Loading state -->
  <div v-else-if="isLoading" class="page empty-panel">Loading change…</div>

  <!-- Not found -->
  <div v-else class="page empty-panel feedback-error card">Change not found.</div>

  <!-- ── Assessment Modal ── -->
  <Teleport to="body">
    <Transition name="modal">
      <div
        v-if="showAssessModal"
        class="modal-backdrop"
        @click.self="closeAssessModal"
        role="dialog"
        aria-modal="true"
        aria-label="Assessment Wizard"
      >
        <div class="modal-panel modal-panel--large">
          <div class="modal-header">
            <h2 class="section-title">Substantiality Assessment</h2>
            <button class="btn btn-icon btn-close" @click="closeAssessModal" aria-label="Close">✕</button>
          </div>

          <div class="modal-body">
            <AssessmentWizard
              :key="change?.id"
              :change-id="change?.id || ''"
              :change-type="change?.change_type"
              @cancel="closeAssessModal"
              @submitted="onAssessmentSubmitted"
            />
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>

  <!-- ── Edit Modal (draft only) ── -->
  <Teleport to="body">
    <Transition name="modal">
      <div
        v-if="showEditModal"
        class="modal-backdrop"
        @click.self="closeEditModal"
        role="dialog"
        aria-modal="true"
        aria-label="Edit change"
      >
        <div class="modal-panel">
          <div class="modal-header">
            <h2 class="section-title">Edit change</h2>
            <button class="btn btn-icon btn-close" @click="closeEditModal" aria-label="Close">✕</button>
          </div>

          <form class="modal-body" @submit.prevent="doEdit">
            <label class="field">
              <span class="field-label">Type</span>
              <select v-model="editForm.change_type">
                <option value="feature">Feature</option>
                <option value="security">Security</option>
                <option value="repair">Repair</option>
                <option value="maintenance">Maintenance</option>
              </select>
            </label>

            <label class="field">
              <span class="field-label">Change date</span>
              <input v-model="editForm.change_date" type="date" />
            </label>

            <label class="field">
              <span class="field-label">Title</span>
              <input v-model.trim="editForm.title" type="text" minlength="3" maxlength="255" required />
            </label>

            <label class="field">
              <span class="field-label">Description</span>
              <textarea v-model.trim="editForm.description" rows="4" minlength="10" required />
            </label>

            <div class="modal-actions">
              <button type="button" class="btn btn-secondary" @click="closeEditModal">Cancel</button>
              <button type="submit" class="btn btn-primary" :disabled="isActing">
                {{ isActing ? "Saving…" : "Save changes" }}
              </button>
            </div>
          </form>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from "vue";
import { useRoute, useRouter } from "vue-router";

import AssigneeSelector from "@/components/AssigneeSelector.vue";
import AssessmentWizard from "@/components/AssessmentWizard.vue";
import CommentThread from "@/components/CommentThread.vue";
import { changeService } from "@/services/change-service";
import { productReleaseService } from "@/services/product-release-service";
import { productService } from "@/services/product-service";
import { userService } from "@/services/user-service";
import type { AssessmentCreate, ChangeRead, ChangeUpdate, ComplianceActionUpdate } from "@/types/change";

const route = useRoute();
const router = useRouter();

// ---------------------------------------------------------------------------
// State
// ---------------------------------------------------------------------------

const change = ref<ChangeRead | null>(null);
const isLoading = ref(false);
const isActing  = ref(false);
const errorMessage   = ref("");
const successMessage = ref("");

/** Resolved display strings for UUIDs shown in the details card. */
const productName    = ref<string | null>(null);
const releaseVersion = ref<string | null>(null);
const initiatorName  = ref<string | null>(null);
const assessorName   = ref<string | null>(null);

const showAssessModal = ref(false);
const showEditModal   = ref(false);

/** Assessment form, pre-filled with defaults. */
const assessForm = reactive<AssessmentCreate>({
  alters_intended_use: false,
  introduces_new_threat_vectors: false,
  enables_new_attack_scenarios: false,
  changes_attack_likelihood: false,
  changes_attack_impact: false,
  reasoning: "",
  decision_date: new Date().toISOString().slice(0, 10),
});

/** Edit form, populated from the current change when modal opens. */
const editForm = reactive<ChangeUpdate>({
  change_type: undefined,
  title: undefined,
  description: undefined,
  change_date: undefined,
});

/**
 * Per-action edit state keyed by action ID.
 * Stores partial ComplianceActionUpdate values before the user saves.
 */
const actionEdits = ref<Record<string, ComplianceActionUpdate>>({});

// ---------------------------------------------------------------------------
// Computed helpers
// ---------------------------------------------------------------------------

/** Ordered workflow steps used to render the progress strip. */
const workflowSteps = [
  { status: "draft",          label: "Draft" },
  { status: "submitted",      label: "Submitted" },
  { status: "under_review",   label: "Under review" },
  { status: "assessed",       label: "Assessed" },
  { status: "action_required", label: "Actions" },
  { status: "closed",         label: "Closed" },
];

/** Status ordering used to decide which steps are "done". */
const STATUS_ORDER: Record<string, number> = {
  draft: 0,
  submitted: 1,
  under_review: 2,
  assessed: 3,
  action_required: 3,  // same rank as assessed — parallel states
  closed: 5,
};

function isStepDone(status: string): boolean {
  if (!change.value) return false;
  const currentRank = STATUS_ORDER[change.value.status] ?? 0;
  const stepRank    = STATUS_ORDER[status] ?? 0;
  return currentRank > stepRank;
}

const totalActionCount = computed(
  () => change.value?.assessment?.compliance_actions.length ?? 0
);

const completedActionCount = computed(
  () =>
    change.value?.assessment?.compliance_actions.filter(
      (a) => a.action_status === "completed"
    ).length ?? 0
);

// Close is only allowed once every compliance action is marked complete.
// For assessed (non-substantial) changes there are no actions, so it is always allowed.
const allActionsComplete = computed(
  () => totalActionCount.value === 0 || completedActionCount.value === totalActionCount.value
);

// ---------------------------------------------------------------------------
// Data fetching
// ---------------------------------------------------------------------------

async function loadChange(): Promise<void> {
  isLoading.value = true;
  errorMessage.value = "";

  try {
    const id = route.params.id as string;
    change.value = await changeService.get(id);

    // Resolve UUIDs to human-readable names in parallel after the change loads
    void resolveDisplayNames(change.value);
  } catch (err) {
    errorMessage.value = err instanceof Error ? err.message : "Failed to load change.";
  } finally {
    isLoading.value = false;
  }
}

/**
 * Fetches the product release, product, and user records needed to show
 * names instead of raw UUIDs in the details panel.
 * Runs in parallel and silently ignores individual lookup failures.
 */
async function resolveDisplayNames(c: ChangeRead): Promise<void> {
  // Resolve product release → display_version string and product name
  const releasePromise = productReleaseService.get(c.product_version_id).then(async (release) => {
    releaseVersion.value = release.display_version;
    const product = await productService.get(release.product_id);
    productName.value = product.name;
  }).catch(() => { /* leave null if lookup fails */ });

  // Fetch all users once, then look up initiator and assessor by ID
  const usersPromise = userService.listSummary().then((users) => {
    const findName = (id: string | null) => {
      if (!id) return null;
      const u = users.find((user) => user.id === id);
      return u ? (u.full_name || u.email) : id;
    };
    initiatorName.value = findName(c.initiator_user_id ? String(c.initiator_user_id) : null);
    assessorName.value  = findName(c.assessor_user_id ? String(c.assessor_user_id) : null);
  }).catch(() => {
    initiatorName.value = c.initiator_user_id ? String(c.initiator_user_id) : null;
    assessorName.value  = c.assessor_user_id ? String(c.assessor_user_id) : null;
  });

  await Promise.all([releasePromise, usersPromise]);
}

onMounted(() => void loadChange());

// ---------------------------------------------------------------------------
// Workflow actions
// ---------------------------------------------------------------------------

async function doSubmit(): Promise<void> {
  await runAction(() => changeService.submit(change.value!.id), "Change submitted for review.");
}

async function doClaim(): Promise<void> {
  await runAction(() => changeService.claim(change.value!.id), "You have been assigned as assessor.");
}

async function doClose(): Promise<void> {
  if (!allActionsComplete.value) {
    errorMessage.value = `Please complete all compliance actions before closing this change (${completedActionCount.value} of ${totalActionCount.value} complete).`;
    return;
  }
  await runAction(() => changeService.close(change.value!.id), "Change closed.");
}

/** Generic action runner: sets loading, calls fn, refreshes, shows feedback. */
async function updateChangeAssignment(
  patch: { assigned_to_user_id?: string | null; due_date?: string | null },
): Promise<void> {
  if (!change.value) return;
  try {
    change.value = await changeService.assign(change.value.id, patch);
  } catch {
    errorMessage.value = "Failed to save assignment.";
  }
}

async function runAction(fn: () => Promise<ChangeRead>, successMsg: string): Promise<void> {
  isActing.value = true;
  errorMessage.value = "";
  successMessage.value = "";

  try {
    change.value = await fn();
    successMessage.value = successMsg;
    // Re-resolve names in case assessor_user_id changed (e.g. after claim)
    void resolveDisplayNames(change.value);
  } catch (err) {
    errorMessage.value = err instanceof Error ? err.message : "Action failed.";
  } finally {
    isActing.value = false;
  }
}

// ---------------------------------------------------------------------------
// Assessment modal
// ---------------------------------------------------------------------------

function openAssessModal(): void {
  showAssessModal.value = true;
}

function closeAssessModal(): void {
  showAssessModal.value = false;
}

async function onAssessmentSubmitted(): Promise<void> {
  try {
    // Reload change to get updated assessment
    if (change.value) {
      change.value = await changeService.get(change.value.id);
      successMessage.value = `Assessment recorded. Change is ${change.value.assessment?.is_substantial ? "substantial" : "not substantial"}.`;
    }
    showAssessModal.value = false;
  } catch (err) {
    errorMessage.value = err instanceof Error ? err.message : "Failed to load updated change.";
  }
}

// ---------------------------------------------------------------------------
// Edit modal
// ---------------------------------------------------------------------------

function openEditModal(): void {
  if (!change.value) return;
  editForm.change_type = change.value.change_type;
  editForm.title       = change.value.title;
  editForm.description = change.value.description;
  editForm.change_date = change.value.change_date;
  showEditModal.value  = true;
}

function closeEditModal(): void {
  showEditModal.value = false;
}

async function doEdit(): Promise<void> {
  isActing.value = true;
  errorMessage.value = "";
  successMessage.value = "";

  try {
    change.value = await changeService.update(change.value!.id, { ...editForm });
    successMessage.value = "Change updated.";
    showEditModal.value = false;
  } catch (err) {
    errorMessage.value = err instanceof Error ? err.message : "Update failed.";
  } finally {
    isActing.value = false;
  }
}

// ---------------------------------------------------------------------------
// Compliance action helpers
// ---------------------------------------------------------------------------

/**
 * Set a compliance action to the given status.
 * Used both to mark complete and to restore a completed action back to in_progress.
 */
async function markAction(actionId: string, status: "completed" | "in_progress" | "pending"): Promise<void> {
  isActing.value = true;
  errorMessage.value = "";
  successMessage.value = "";

  try {
    await changeService.updateComplianceAction(actionId, { action_status: status });
    successMessage.value =
      status === "completed" ? "Action marked as completed." : "Action restored to in progress.";
    // Reload to get fresh compliance action state
    await loadChange();
  } catch (err) {
    errorMessage.value = err instanceof Error ? err.message : "Failed to update action.";
  } finally {
    isActing.value = false;
  }
}

/** Track partial edits for a compliance action before saving. */
function setActionEdit(actionId: string, field: keyof ComplianceActionUpdate, value: string): void {
  if (!actionEdits.value[actionId]) {
    actionEdits.value[actionId] = {};
  }
  // @ts-expect-error — dynamic field assignment
  actionEdits.value[actionId][field] = value || null;
}

/** Save due date / notes for a compliance action. */
async function saveActionEdit(actionId: string): Promise<void> {
  const edit = actionEdits.value[actionId];
  if (!edit) return;

  isActing.value = true;
  errorMessage.value = "";
  successMessage.value = "";

  try {
    await changeService.updateComplianceAction(actionId, edit);
    successMessage.value = "Action updated.";
    delete actionEdits.value[actionId];
    await loadChange();
  } catch (err) {
    errorMessage.value = err instanceof Error ? err.message : "Failed to save action.";
  } finally {
    isActing.value = false;
  }
}

// ---------------------------------------------------------------------------
// Formatting helpers
// ---------------------------------------------------------------------------

function formatDate(value: string | null | undefined): string {
  if (!value) return "—";
  return new Intl.DateTimeFormat(undefined, {
    year: "numeric",
    month: "short",
    day: "2-digit",
  }).format(new Date(value));
}

function formatLabel(value: string): string {
  return value.replaceAll("_", " ");
}

/** Convert snake_case action type keys to readable labels. */
const ACTION_LABELS: Record<string, string> = {
  renew_conformity_assessment: "Renew conformity assessment",
  update_technical_docs: "Update technical documentation",
  update_declaration_of_conformity: "Update declaration of conformity",
  re_release_product: "Re-release product",
};

function formatActionType(value: string): string {
  return ACTION_LABELS[value] ?? formatLabel(value);
}
</script>

<style scoped>
.page {
  display: grid;
  gap: 1rem;
}

/* Page header */
.page-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 1rem;
  flex-wrap: wrap;
}

.header-left {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  min-width: 0;
}

.header-meta {
  display: flex;
  flex-direction: column;
  gap: 0.4rem;
}

.header-badges {
  display: flex;
  gap: 0.5rem;
  flex-wrap: wrap;
}

.header-actions {
  display: flex;
  gap: 0.75rem;
  flex-wrap: wrap;
  align-items: flex-start;
  flex-shrink: 0;
}

.page-title {
  margin: 0;
  font-size: 1.4rem;
}

.page-subtitle {
  margin: 0;
  font-size: 0.92rem;
  line-height: 1.5;
}

.back-btn {
  padding: 0.3rem 0;
  font-size: 0.9rem;
  border: none;
  background: none;
  cursor: pointer;
  color: var(--color-text-muted, #94a3b8);
}

.back-btn:hover { color: inherit; }

/* Feedback */
.feedback {
  padding: 1rem 1.1rem;
  border-radius: 1rem;
}

.feedback-error   { color: #fda4af; }
.feedback-success { color: #86efac; }

/* Workflow timeline strip */
.timeline-strip {
  display: flex;
  align-items: center;
  padding: 1rem 1.5rem;
  overflow-x: auto;
  gap: 0;
}

.timeline-step {
  display: flex;
  flex-direction: column;
  align-items: center;
  position: relative;
  flex-shrink: 0;
}

.step-dot {
  width: 12px;
  height: 12px;
  border-radius: 50%;
  background: var(--color-border, rgba(148, 163, 184, 0.3));
  transition: background 0.2s;
}

.step-done .step-dot   { background: #4ade80; }
.step-active .step-dot { background: #6ea8fe; box-shadow: 0 0 0 3px rgba(110, 168, 254, 0.25); }

.step-label {
  font-size: 0.72rem;
  margin-top: 0.4rem;
  white-space: nowrap;
  color: var(--color-text-muted, #94a3b8);
}

.step-done .step-label   { color: #4ade80; }
.step-active .step-label { color: #6ea8fe; font-weight: 600; }

.step-connector {
  position: absolute;
  top: 5px;  /* vertically center on the dot */
  left: 100%;
  width: 4rem;
  height: 2px;
  background: var(--color-border, rgba(148, 163, 184, 0.25));
}

.step-done .step-connector { background: #4ade80; }

/* Two-column layout */
.detail-grid {
  display: grid;
  grid-template-columns: 1fr 1.4fr;
  gap: 1rem;
  align-items: start;
}

.detail-left,
.detail-right {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

/* Section titles */
.section-title { margin: 0 0 1rem; font-size: 1rem; }

.section-header-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.75rem;
  margin-bottom: 1rem;
}

/* Key-value list in details card */
.kv-list {
  display: flex;
  flex-direction: column;
  gap: 0.6rem;
  margin: 0;
}

.kv-row {
  display: grid;
  grid-template-columns: 10rem 1fr;
  gap: 0.5rem;
  font-size: 0.9rem;
}

dt { color: var(--color-text-muted, #94a3b8); }
dd { margin: 0; word-break: break-all; }
.mono { font-family: monospace; font-size: 0.82rem; }

/* Assessment criteria */
.criteria-list {
  list-style: none;
  padding: 0;
  margin: 0 0 1rem;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.criteria-item {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.9rem;
  padding: 0.45rem 0.7rem;
  border-radius: 0.6rem;
}

.criteria-true  { background: rgba(34, 197, 94, 0.1);  color: #4ade80; }
.criteria-false { background: rgba(148, 163, 184, 0.07); color: var(--color-text-muted, #94a3b8); }

.criteria-icon { font-size: 0.85rem; font-weight: 700; }

.criteria-ref {
  margin-left: auto;
  font-size: 0.72rem;
  font-weight: 500;
  opacity: 0.55;
}

.reasoning-block {
  display: flex;
  flex-direction: column;
  gap: 0.35rem;
  padding: 0.75rem;
  border-radius: 0.75rem;
  border: 1px solid var(--color-border, rgba(148, 163, 184, 0.15));
  background: var(--color-surface-soft, rgba(255, 255, 255, 0.02));
  font-size: 0.9rem;
  line-height: 1.5;
  margin-bottom: 0.5rem;
}

.reasoning-meta { font-size: 0.8rem; }

/* Substantiality verdict badge */
.substantial-verdict {
  font-size: 0.78rem;
  font-weight: 700;
  padding: 0.2rem 0.6rem;
  border-radius: 999px;
}

.verdict-substantial { background: rgba(248, 113, 113, 0.15); color: #f87171; }
.verdict-not         { background: rgba(34, 197, 94, 0.12);  color: #4ade80; }

/* Compliance action cards */
.action-list {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.action-card {
  padding: 0.9rem 1rem;
  border-radius: 0.9rem;
  border: 1px solid var(--color-border, rgba(148, 163, 184, 0.18));
  background: var(--color-surface-soft, rgba(255, 255, 255, 0.02));
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  transition: border-color 0.15s;
}

.action-completed { border-color: rgba(34, 197, 94, 0.25); }

.action-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.75rem;
  flex-wrap: wrap;
}

.action-type {
  display: block;
  font-size: 0.9rem;
  font-weight: 600;
  margin-bottom: 0.25rem;
}

.action-status-badge {
  display: inline-block;
  padding: 0.1rem 0.5rem;
  border-radius: 999px;
  font-size: 0.75rem;
  font-weight: 500;
  text-transform: capitalize;
}

.ast-pending     { background: rgba(148, 163, 184, 0.12); color: #94a3b8; }
.ast-in_progress { background: rgba(110, 168, 254, 0.12); color: #6ea8fe; }
.ast-completed   { background: rgba(34, 197, 94, 0.12);   color: #4ade80; }

.action-btn-group {
  display: flex;
  gap: 0.4rem;
  align-items: center;
  flex-shrink: 0;
}

.btn-restore {
  background: transparent;
  border: 1px solid rgba(251, 191, 36, 0.35);
  color: #fbbf24;
  border-radius: 0.85rem;
  padding: 0.35rem 0.8rem;
  font: inherit;
  font-size: 0.83rem;
  cursor: pointer;
  white-space: nowrap;
  transition: background 0.12s, border-color 0.12s;
}

.btn-restore:hover {
  background: rgba(251, 191, 36, 0.1);
  border-color: rgba(251, 191, 36, 0.6);
}

.action-meta { font-size: 0.8rem; }

.action-notes {
  display: flex;
  flex-direction: column;
  gap: 0.2rem;
  font-size: 0.85rem;
}

/* Inline edit collapse */
.action-edit-details { font-size: 0.85rem; }

.action-edit-trigger {
  cursor: pointer;
  font-size: 0.8rem;
  user-select: none;
}

.action-edit-form {
  display: flex;
  flex-direction: column;
  gap: 0.6rem;
  margin-top: 0.65rem;
}

/* Empty panel */
.empty-panel {
  padding: 2rem;
  text-align: center;
  color: var(--color-text-muted, #94a3b8);
}

/* Badges (shared with list view) */
.type-badge,
.status-badge,
.substantial-pill {
  display: inline-block;
  padding: 0.15rem 0.55rem;
  border-radius: 999px;
  font-size: 0.78rem;
  font-weight: 500;
}

.type-feature     { background: rgba(110, 168, 254, 0.15); color: #6ea8fe; }
.type-security    { background: rgba(34, 197, 94, 0.15);  color: #4ade80; }
.type-repair      { background: rgba(251, 191, 36, 0.15); color: #fbbf24; }
.type-maintenance { background: rgba(148, 163, 184, 0.15); color: #94a3b8; }

.status-draft          { background: rgba(148, 163, 184, 0.12); color: #94a3b8; }
.status-submitted      { background: rgba(110, 168, 254, 0.15); color: #6ea8fe; }
.status-under_review   { background: rgba(139, 92, 246, 0.15);  color: #a78bfa; }
.status-assessed       { background: rgba(34, 197, 94, 0.15);   color: #4ade80; }
.status-action_required{ background: rgba(251, 191, 36, 0.18);  color: #fbbf24; }
.status-closed         { background: rgba(100, 116, 139, 0.12); color: #64748b; }

.substantial-pill { background: rgba(248, 113, 113, 0.15); color: #f87171; font-weight: 600; }

/* Actions count */
.actions-count { font-size: 0.82rem; }

/* Buttons */
.btn {
  border: 1px solid transparent;
  border-radius: 0.85rem;
  padding: 0.75rem 1rem;
  font: inherit;
  cursor: pointer;
  white-space: nowrap;
}

.btn-primary {
  background: linear-gradient(135deg, rgba(175, 214, 46, 0.95), rgba(28, 107, 39, 0.95));
  color: white;
}

.btn-secondary {
  background: transparent;
  border-color: var(--color-border, rgba(148, 163, 184, 0.25));
  color: inherit;
}

.btn-ghost { border: none; background: none; cursor: pointer; }
.btn-sm { padding: 0.35rem 0.8rem; font-size: 0.83rem; }

.btn-icon {
  padding: 0.4rem 0.6rem;
  font-size: 0.8rem;
  line-height: 1;
}

.close-blocked-hint {
  font-size: 0.8rem;
  align-self: center;
}

.btn-close {
  background: transparent;
  border-color: var(--color-border, rgba(148, 163, 184, 0.2));
  color: var(--color-text-muted, #94a3b8);
  border-radius: 0.6rem;
  transition: color 0.12s, border-color 0.12s;
}

.btn-close:hover { color: #f87171; border-color: rgba(248, 113, 113, 0.4); }

/* Modal */
.modal-backdrop {
  position: fixed;
  inset: 0;
  background: rgba(5, 10, 20, 0.78);
  z-index: 200;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 1rem;
}

.modal-panel {
  background: var(--color-modal-bg, #0c1524);
  border: 1px solid var(--color-border, rgba(148, 163, 184, 0.2));
  border-radius: 1.2rem;
  width: 100%;
  max-width: 40rem;
  max-height: 90vh;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  box-shadow: 0 24px 80px rgba(0, 0, 0, 0.6);
}

.modal-panel--large {
  max-width: 60rem;
}

.modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 1.5rem;
  border-bottom: 1px solid var(--color-border, rgba(148, 163, 184, 0.15));
  flex-shrink: 0;
}

.modal-body {
  display: flex;
  flex-direction: column;
  gap: 1rem;
  padding: 1.5rem;
  overflow-y: auto;
}

.modal-actions {
  display: flex;
  justify-content: flex-end;
  gap: 0.75rem;
}

.assess-note {
  margin: 0;
  font-size: 0.9rem;
  line-height: 1.5;
}

.checkbox-label {
  display: flex;
  align-items: flex-start;
  gap: 0.6rem;
  font-size: 0.92rem;
  cursor: pointer;
}

.checkbox-label input[type="checkbox"] {
  width: auto;
  flex-shrink: 0;
  margin-top: 0.15rem;
  accent-color: var(--color-primary, #6ea8fe);
}

.field {
  display: flex;
  flex-direction: column;
  gap: 0.4rem;
}

.field-label {
  font-size: 0.82rem;
  color: var(--color-text-muted, #94a3b8);
}

input, textarea, select {
  width: 100%;
  padding: 0.75rem 0.9rem;
  border-radius: 0.85rem;
  border: 1px solid var(--color-border, rgba(148, 163, 184, 0.25));
  background: var(--color-surface-soft, rgba(15, 23, 42, 0.5));
  color: inherit;
  font: inherit;
  box-sizing: border-box;
}

.muted { color: var(--color-text-muted, #94a3b8); }

/* Modal transitions */
.modal-enter-active, .modal-leave-active { transition: opacity 0.18s ease; }
.modal-enter-active .modal-panel,
.modal-leave-active .modal-panel { transition: transform 0.18s ease, opacity 0.18s ease; }
.modal-enter-from, .modal-leave-to { opacity: 0; }
.modal-enter-from .modal-panel,
.modal-leave-to .modal-panel { transform: translateY(12px) scale(0.98); opacity: 0; }

@media (max-width: 800px) {
  .detail-grid { grid-template-columns: 1fr; }
  .timeline-strip { gap: 0; }
  .step-connector { width: 2rem; }
}
</style>

<style>
:root[data-theme="light"] .feedback-error   { color: #be123c; }
:root[data-theme="light"] .feedback-success { color: #15803d; }
:root[data-theme="light"] .btn-primary { background: linear-gradient(135deg, rgba(175, 214, 46, 0.95), rgba(28, 107, 39, 0.95)); }
:root[data-theme="light"] .verdict-substantial { background: rgba(220, 38, 38, 0.1); color: #dc2626; }
:root[data-theme="light"] .verdict-not { background: rgba(22, 163, 74, 0.1); color: #16a34a; }
:root[data-theme="light"] .action-completed { border-color: rgba(22, 163, 74, 0.25); }
:root[data-theme="light"] .criteria-true { background: rgba(22, 163, 74, 0.08); color: #16a34a; }
:root[data-theme="light"] .modal-panel { background: #ffffff; }
:root[data-theme="light"] .substantial-pill { background: rgba(220, 38, 38, 0.1); color: #dc2626; }
:root[data-theme="light"] .btn-restore { border-color: rgba(202, 138, 4, 0.4); color: #b45309; }
:root[data-theme="light"] .btn-restore:hover { background: rgba(202, 138, 4, 0.08); border-color: rgba(202, 138, 4, 0.7); }
:root[data-theme="light"] .type-feature { background: rgba(37, 99, 235, 0.1); color: #2563eb; }
:root[data-theme="light"] .type-security { background: rgba(22, 163, 74, 0.1); color: #16a34a; }
:root[data-theme="light"] .type-repair { background: rgba(202, 138, 4, 0.1); color: #ca8a04; }
:root[data-theme="light"] .status-submitted { background: rgba(37, 99, 235, 0.1); color: #2563eb; }
:root[data-theme="light"] .status-under_review { background: rgba(109, 40, 217, 0.1); color: #6d28d9; }
:root[data-theme="light"] .status-assessed { background: rgba(22, 163, 74, 0.1); color: #16a34a; }
:root[data-theme="light"] .status-action_required { background: rgba(202, 138, 4, 0.1); color: #b45309; }
</style>
