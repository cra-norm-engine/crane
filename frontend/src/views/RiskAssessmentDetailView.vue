<template>
  <!-- Edit Assessment Modal -->
  <div v-if="showEditModal" class="modal-overlay" @click="showEditModal = false">
    <div class="modal-content" @click.stop>
      <div class="modal-header">
        <h2>Edit Assessment</h2>
        <button class="modal-close" @click="showEditModal = false">✕</button>
      </div>

      <form class="modal-form" @submit.prevent="updateAssessment">
        <div class="form-row">
          <label class="field">
            <span class="field-label">Title</span>
            <input v-model="editForm.title" class="input" type="text" maxlength="255" required />
          </label>

          <label class="field">
            <span class="field-label">Version Name (Optional)</span>
            <input v-model="editForm.user_version" class="input" type="text" maxlength="100" placeholder="e.g., Q2 Assessment, Annual Review" />
          </label>
        </div>

        <div class="form-row">
          <label class="field">
            <span class="field-label">Status</span>
            <select v-model="editForm.status" class="select">
              <option value="">No change</option>
              <option v-for="option in assessmentStatuses" :key="option" :value="option">
                {{ option }}
              </option>
            </select>
          </label>

          <label class="field">
            <span class="field-label">Owner</span>
            <select v-model="editForm.owner_user_id" class="select">
              <option value="">No owner</option>
              <option v-for="user in users" :key="user.id" :value="user.id">
                {{ getUserDisplay(user.id) }}
              </option>
            </select>
          </label>
        </div>

        <div class="form-row">
          <label class="field">
            <span class="field-label">Methodology</span>
            <input v-model="editForm.methodology" class="input" type="text" />
          </label>

          <label class="field">
            <span class="field-label">Product Release</span>
            <input v-model="editForm.product_release_id" class="input" type="text" placeholder="Optional ID" />
          </label>
        </div>

        <label class="field field-full">
          <span class="field-label">Summary</span>
          <textarea v-model="editForm.summary" class="textarea" rows="3" placeholder="Summary of findings and recommendations" />
        </label>

        <div class="modal-actions">
          <button class="button secondary" type="button" @click="showEditModal = false">Cancel</button>
          <button class="button" type="submit" :disabled="savingAssessment">
            {{ savingAssessment ? "Saving..." : "Save Changes" }}
          </button>
          <button
            class="button"
            type="button"
            @click="approveAssessment"
            :disabled="approvingAssessment"
          >
            {{ approvingAssessment ? "Approving..." : "Approve" }}
          </button>
        </div>
      </form>
    </div>
  </div>

  <!-- Duplicate Modal -->
  <div v-if="showDuplicateModal" class="modal-overlay" @click="showDuplicateModal = false">
    <div class="modal-content" @click.stop>
      <div class="modal-header">
        <h2>Duplicate Assessment Version</h2>
        <button class="modal-close" @click="showDuplicateModal = false">✕</button>
      </div>

      <form class="modal-form" @submit.prevent="duplicateAssessment">
        <div class="form-row">
          <label class="field">
            <span class="field-label">Version Name (Optional)</span>
            <input v-model="duplicateForm.user_version" class="input" type="text" maxlength="100" placeholder="e.g., Q2 Assessment, Annual Review" />
          </label>

          <label class="field">
            <span class="field-label">New Title</span>
            <input v-model="duplicateForm.title" class="input" type="text" maxlength="255" placeholder="Leave blank to keep current" />
          </label>
        </div>

        <div class="form-row">
          <label class="field">
            <span class="field-label">Product Release</span>
            <input v-model="duplicateForm.product_release_id" class="input" type="text" placeholder="Optional" />
          </label>

          <label class="field">
            <span class="field-label">Owner</span>
            <select v-model="duplicateForm.owner_user_id" class="select">
              <option value="">Keep current owner</option>
              <option v-for="user in users" :key="user.id" :value="user.id">
                {{ getUserDisplay(user.id) }}
              </option>
            </select>
          </label>
        </div>

        <label class="field field-full">
          <span class="field-label">Summary Override</span>
          <textarea v-model="duplicateForm.summary" class="textarea" rows="2" placeholder="Leave blank to keep current" />
        </label>

        <div class="checkbox-group">
          <label class="checkbox-field">
            <input v-model="duplicateForm.reset_status_to_draft" type="checkbox" />
            <span>Reset status to draft</span>
          </label>

          <label class="checkbox-field">
            <input v-model="duplicateForm.copy_risk_items" type="checkbox" />
            <span>Copy risk items to new display_version</span>
          </label>

          <label class="checkbox-field">
            <input v-model="duplicateForm.copy_requirement_mappings" type="checkbox" />
            <span>Copy requirement mappings</span>
          </label>

          <label class="checkbox-field">
            <input v-model="duplicateForm.copy_evidence_links" type="checkbox" />
            <span>Copy evidence links</span>
          </label>
        </div>

        <div class="modal-actions">
          <button class="button secondary" type="button" @click="showDuplicateModal = false">Cancel</button>
          <button class="button" type="submit" :disabled="duplicatingAssessment">
            {{ duplicatingAssessment ? "Duplicating..." : "Create New Version" }}
          </button>
        </div>
      </form>
    </div>
  </div>

  <section class="page">
    <header class="page-header">
      <div>
        <p class="eyebrow">Risk Assessment</p>
        <h1 class="page-title">{{ assessment?.title ?? "Risk Assessment Detail" }}</h1>
      </div>
      <div class="header-actions">
        <button class="button secondary" type="button" @click="goBack">← Back</button>
        <button class="button" type="button" @click="loadAssessment" :disabled="loading">
          {{ loading ? "Refreshing…" : "Refresh" }}
        </button>
      </div>
    </header>

    <div v-if="errorMessage" class="feedback feedback-error">{{ errorMessage }}</div>
    <div v-if="successMessage" class="feedback feedback-success">{{ successMessage }}</div>

    <section v-if="loading && !assessment" class="panel">
      <div class="loading-state">Loading assessment...</div>
    </section>

    <template v-else-if="assessment">
      <!-- Assessment Overview Card -->
      <article class="panel">
        <div class="panel-header">
          <div>
            <h2>Assessment Overview</h2>
          </div>
          <div class="overview-actions">
            <span class="count-badge">{{ assessment.display_version }}</span>
            <button class="button secondary" @click="showEditModal = true">Edit Assessment</button>
          </div>
        </div>

        <!-- Modern overview grid -->
        <div class="overview-grid">
          <div class="overview-card">
            <div class="overview-label">Product</div>
            <div class="overview-value">{{ getProductName(assessment.product_id) }}</div>
          </div>

          <div class="overview-card">
            <div class="overview-label">Release Version</div>
            <div class="overview-value">
              {{ productRelease?.display_version ?? assessment.product_release_id ?? "—" }}
            </div>
          </div>

          <div class="overview-card">
            <div class="overview-label">Status</div>
            <div class="overview-value">
              <span class="status-pill">{{ assessment.status.replaceAll("_", " ") }}</span>
            </div>
          </div>

          <div class="overview-card">
            <div class="overview-label">Methodology</div>
            <div class="overview-value">{{ assessment.methodology }}</div>
          </div>

          <div class="overview-card">
            <div class="overview-label">Owner</div>
            <div class="overview-value">{{ getUserDisplay(assessment.owner_user_id) }}</div>
          </div>

          <div class="overview-card">
            <div class="overview-label">Created</div>
            <div class="overview-value">{{ formatDate(assessment.created_at) }}</div>
          </div>

          <div class="overview-card">
            <div class="overview-label">Updated</div>
            <div class="overview-value">{{ formatDate(assessment.updated_at) }}</div>
          </div>

          <div class="overview-card">
            <div class="overview-label">Approved</div>
            <div class="overview-value">{{ assessment.approved_at ? formatDate(assessment.approved_at) : "—" }}</div>
          </div>
        </div>

        <!-- Summary section -->
        <div v-if="assessment.summary" class="summary-section">
          <h3 class="summary-title">Summary</h3>
          <p class="summary-text">{{ assessment.summary }}</p>
        </div>
      </article>

<!-- Quick Actions Bar -->
      <div class="actions-bar">
        <div class="action-group">
          <div class="action-content">
            <h3 class="action-title">Release Workflow</h3>
            <p class="action-description">Add and review evidence through the structured release process</p>
          </div>
          <RouterLink
            v-if="assessment.product_release_id"
            class="button"
            :to="{ name: 'release-gate', params: { releaseId: assessment.product_release_id } }"
          >
            Open Workflow →
          </RouterLink>
          <button v-else class="button" disabled title="Link this assessment to a product release first">
            No Release Linked
          </button>
        </div>

        <div class="action-group">
          <div class="action-content">
            <h3 class="action-title">Create New Version</h3>
            <p class="action-description">Duplicate this assessment with optional modifications</p>
          </div>
          <button class="button secondary" @click="showDuplicateModal = true">
            Duplicate Version →
          </button>
        </div>
      </div>

      <section class="panel">
        <div class="panel-header">
          <h2>Risk Items</h2>
          <div class="risk-items-actions">
            <span class="count-badge">{{ riskItems.length }}</span>
            <button class="button" type="button" @click="showRiskItemForm = !showRiskItemForm">
              {{ showRiskItemForm ? "Close Editor" : "Add Risk Item" }}
            </button>
          </div>
        </div>

        <div v-if="showRiskItemForm" class="editor-block">
          <form class="form-grid" @submit.prevent="createRiskItem">
            <label class="field">
              <span class="field-label">Title</span>
              <input v-model="riskItemForm.title" class="input" type="text" required maxlength="255" />
            </label>

            <label class="field">
              <span class="field-label">Asset Affected</span>
              <input v-model="riskItemForm.asset_affected" class="input" type="text" required maxlength="255" />
            </label>

            <label class="field">
              <span class="field-label">Likelihood</span>
              <select v-model="riskItemForm.likelihood" class="select">
                <option v-for="level in riskLevels" :key="level" :value="level">{{ level }}</option>
              </select>
            </label>

            <label class="field">
              <span class="field-label">Impact</span>
              <select v-model="riskItemForm.impact" class="select">
                <option v-for="level in riskLevels" :key="level" :value="level">{{ level }}</option>
              </select>
            </label>

            <label class="field">
              <span class="field-label">Risk Level</span>
              <select v-model="riskItemForm.risk_level" class="select">
                <option v-for="level in riskLevels" :key="level" :value="level">{{ level }}</option>
              </select>
            </label>

            <label class="field">
              <span class="field-label">Status</span>
              <select v-model="riskItemForm.status" class="select">
                <option v-for="statusOption in riskItemStatuses" :key="statusOption" :value="statusOption">
                  {{ statusOption }}
                </option>
              </select>
            </label>

            <label class="field">
              <span class="field-label">Residual Risk Level</span>
              <select v-model="riskItemForm.residual_risk_level" class="select">
                <option value="">None</option>
                <option v-for="level in riskLevels" :key="level" :value="level">{{ level }}</option>
              </select>
            </label>

            <label class="field">
              <span class="field-label">Owner</span>
              <select v-model="riskItemForm.owner_user_id" class="select">
                <option value="">No owner</option>
                <option v-for="user in users" :key="user.id" :value="user.id">
                  {{ getUserDisplay(user.id) }}
                </option>
              </select>
            </label>

            <label class="field field-full">
              <span class="field-label">Description</span>
              <textarea v-model="riskItemForm.description" class="textarea" rows="3" required />
            </label>

            <label class="field field-full">
              <span class="field-label">Threat Scenario</span>
              <textarea v-model="riskItemForm.threat_scenario" class="textarea" rows="3" required />
            </label>

            <label class="field field-full">
              <span class="field-label">Mitigation Plan</span>
              <textarea v-model="riskItemForm.mitigation_plan" class="textarea" rows="3" required />
            </label>

            <div class="form-actions field-full">
              <button class="button" type="submit" :disabled="creatingRiskItem">
                {{ creatingRiskItem ? "Saving..." : "Create Risk Item" }}
              </button>
            </div>
          </form>
        </div>

        <div v-if="riskItemsLoading" class="loading-state">Loading risk items...</div>

        <div v-else-if="riskItems.length === 0" class="empty-state">
          No risk items recorded for this assessment yet.
        </div>

        <div v-else class="risk-items-grid">
          <article v-for="item in riskItems" :key="item.id" class="risk-card">
            <div class="risk-card-header">
              <div>
                <h3>{{ item.title }}</h3>
                <p class="risk-meta">
                  Asset: {{ item.asset_affected }} · Status: {{ item.status }}
                </p>
              </div>
              <span class="risk-level-pill">{{ item.risk_level }}</span>
            </div>

            <div class="risk-copy">
              <p><strong>Description:</strong> {{ item.description }}</p>
              <p><strong>Threat Scenario:</strong> {{ item.threat_scenario }}</p>
              <p><strong>Mitigation:</strong> {{ item.mitigation_plan }}</p>
            </div>

            <div class="risk-card-grid">
              <div><strong>Likelihood:</strong> {{ item.likelihood }}</div>
              <div><strong>Impact:</strong> {{ item.impact }}</div>
              <div><strong>Residual:</strong> {{ item.residual_risk_level ?? "—" }}</div>
              <div><strong>Owner:</strong> {{ getUserDisplay(item.owner_user_id) }}</div>
            </div>

            <!-- Task assignment for this risk item -->
            <div style="margin-top: 0.75rem; padding-top: 0.75rem; border-top: 1px solid var(--color-border, #e2e8f0);">
              <AssigneeSelector
                :assigned-to-user-id="item.owner_user_id ?? null"
                :model-due-date="item.due_date ?? null"
                @update:assigned-to-user-id="(id: string | null) => updateRiskItemAssignment(item.id, { owner_user_id: id })"
                @update:model-due-date="(d: string | null) => updateRiskItemAssignment(item.id, { due_date: d })"
              />
            </div>
          </article>
        </div>
      </section>
    </template>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from "vue";
import { useRoute, useRouter } from "vue-router";

import AssigneeSelector from "@/components/AssigneeSelector.vue";
import { userService, type UserSummary } from "@/services/user-service";
import { productService } from "@/services/product-service";
import { productReleaseService } from "@/services/product-release-service";
import { riskAssessmentService } from "@/services/risk-assessment-service";
import { riskItemService } from "@/services/risk-item-service";
import type { ProductSummaryRead } from "@/types/product";
import type {
  RiskAssessmentDetailRead,
  RiskAssessmentDuplicateRequest,
  RiskAssessmentStatus,
  RiskAssessmentUpdate,
} from "@/types/risk-assessment";
import type { RiskItemCreate, RiskItemRead, RiskItemStatus, RiskLevel } from "@/types/risk-item";

const route = useRoute();
const router = useRouter();

const assessment = ref<RiskAssessmentDetailRead | null>(null);
const riskItems = ref<RiskItemRead[]>([]);
const users = ref<UserSummary[]>([]);
const products = ref<ProductSummaryRead[]>([]);
const productRelease = ref<any>(null);
const loading = ref(false);
const riskItemsLoading = ref(false);
const savingAssessment = ref(false);
const approvingAssessment = ref(false);
const duplicatingAssessment = ref(false);
const creatingRiskItem = ref(false);
const showRiskItemForm = ref(false);
const showDuplicateModal = ref(false);
const showEditModal = ref(false);

const errorMessage = ref("");
const successMessage = ref("");

const assessmentStatuses: RiskAssessmentStatus[] = ["draft", "in_review", "approved", "archived"];
const riskLevels: RiskLevel[] = ["low", "medium", "high", "critical"];
const riskItemStatuses: RiskItemStatus[] = ["open", "in_progress", "mitigated", "accepted", "closed"];

const assessmentId = computed(() => String(route.params.assessmentId));

const editForm = reactive({
  title: "",
  user_version: "",
  status: "" as RiskAssessmentStatus | "",
  methodology: "",
  summary: "",
  owner_user_id: "",
  product_release_id: "",
});

const duplicateForm = reactive({
  user_version: "",
  title: "",
  product_release_id: "",
  summary: "",
  owner_user_id: "",
  reset_status_to_draft: true,
  copy_risk_items: true,
  copy_requirement_mappings: true,
  copy_evidence_links: false,
});

const riskItemForm = reactive({
  title: "",
  description: "",
  threat_scenario: "",
  asset_affected: "",
  likelihood: "medium" as RiskLevel,
  impact: "medium" as RiskLevel,
  risk_level: "medium" as RiskLevel,
  mitigation_plan: "",
  residual_risk_level: "" as RiskLevel | "",
  status: "open" as RiskItemStatus,
  owner_user_id: "",
});

function normalizeOptional(value: string | null | undefined): string | null {
  const trimmed = (value ?? "").trim();
  return trimmed.length > 0 ? trimmed : null;
}

function formatDate(value: string | null): string {
  if (!value) return "—";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleString();
}

function getUserDisplay(userId: string | null | undefined): string {
  if (!userId) return "—";

  const user = users.value.find((item: UserSummary) => item.id === userId);
  if (!user) return userId;

  const fullName = user.full_name?.trim();
  return fullName ? `${fullName} (${user.email})` : user.email;
}

function getProductName(productId: string | null | undefined): string {
  if (!productId) return "—";

  const product = products.value.find((item: ProductSummaryRead) => item.id === productId);
  if (!product) return productId;

  return "name" in product && product.name ? product.name : product.id;
}

async function loadUsers(): Promise<void> {
  try {
    users.value = await userService.listSummary();
  } catch (error: any) {
    console.error("Failed to load users.", error);
  }
}

async function loadProducts(): Promise<void> {
  try {
    products.value = await productService.list();
  } catch (error: any) {
    console.error("Failed to load products.", error);
  }
}

async function loadProductRelease(releaseId: string): Promise<void> {
  try {
    productRelease.value = await productReleaseService.get(releaseId);
  } catch (error: any) {
    console.error("Failed to load product release.", error);
  }
}

function syncEditForm(): void {
  if (!assessment.value) return;
  editForm.title = assessment.value.title;
  editForm.user_version = assessment.value.user_version ?? "";
  editForm.status = assessment.value.status;
  editForm.methodology = assessment.value.methodology;
  editForm.summary = assessment.value.summary ?? "";
  editForm.owner_user_id = assessment.value.owner_user_id ?? "";
  editForm.product_release_id = assessment.value.product_release_id ?? "";
}

async function loadAssessment(): Promise<void> {
  loading.value = true;
  errorMessage.value = "";

  try {
    assessment.value = await riskAssessmentService.get(assessmentId.value);
    syncEditForm();
    // Load product release if linked
    if (assessment.value?.product_release_id) {
      await loadProductRelease(assessment.value.product_release_id);
    }
  } catch (error: any) {
    errorMessage.value = error?.message ?? "Failed to load assessment.";
  } finally {
    loading.value = false;
  }
}

async function loadRiskItems(): Promise<void> {
  riskItemsLoading.value = true;

  try {
    riskItems.value = await riskItemService.listByAssessment(assessmentId.value);
  } catch (error: any) {
    errorMessage.value = error?.message ?? "Failed to load risk items.";
  } finally {
    riskItemsLoading.value = false;
  }
}

async function updateAssessment(): Promise<void> {
  savingAssessment.value = true;
  errorMessage.value = "";
  successMessage.value = "";

  try {
    const payload: RiskAssessmentUpdate = {
      title: editForm.title.trim() || undefined,
      user_version: normalizeOptional(editForm.user_version),
      status: editForm.status || undefined,
      methodology: editForm.methodology.trim() || undefined,
      summary: editForm.summary.trim() || undefined,
      owner_user_id: normalizeOptional(editForm.owner_user_id) ?? undefined,
      product_release_id: normalizeOptional(editForm.product_release_id),
    };

    await riskAssessmentService.update(assessmentId.value, payload);
    successMessage.value = "Assessment updated.";
    await loadAssessment();
  } catch (error: any) {
    errorMessage.value = error?.message ?? "Failed to update assessment.";
  } finally {
    savingAssessment.value = false;
  }
}

async function approveAssessment(): Promise<void> {
  approvingAssessment.value = true;
  errorMessage.value = "";
  successMessage.value = "";

  try {
    await riskAssessmentService.approve(assessmentId.value, {});
    successMessage.value = "Assessment approved.";
    await loadAssessment();
  } catch (error: any) {
    errorMessage.value = error?.message ?? "Failed to approve assessment.";
  } finally {
    approvingAssessment.value = false;
  }
}

async function duplicateAssessment(): Promise<void> {
  duplicatingAssessment.value = true;
  errorMessage.value = "";
  successMessage.value = "";

  try {
    const payload: RiskAssessmentDuplicateRequest = {
      user_version: normalizeOptional(duplicateForm.user_version),
      title: normalizeOptional(duplicateForm.title),
      product_release_id: normalizeOptional(duplicateForm.product_release_id),
      summary: normalizeOptional(duplicateForm.summary),
      owner_user_id: normalizeOptional(duplicateForm.owner_user_id),
      reset_status_to_draft: duplicateForm.reset_status_to_draft,
      copy_risk_items: duplicateForm.copy_risk_items,
      copy_requirement_mappings: duplicateForm.copy_requirement_mappings,
      copy_evidence_links: duplicateForm.copy_evidence_links,
    };

    const duplicated = await riskAssessmentService.duplicateVersion(assessmentId.value, payload);

    successMessage.value = "Assessment display_version duplicated.";
    router.push({
      name: "risk-assessment-detail",
      params: { assessmentId: duplicated.id },
    });
  } catch (error: any) {
    errorMessage.value = error?.message ?? "Failed to duplicate assessment.";
  } finally {
    duplicatingAssessment.value = false;
  }
}

async function createRiskItem(): Promise<void> {
  creatingRiskItem.value = true;
  errorMessage.value = "";
  successMessage.value = "";

  try {
    const payload: RiskItemCreate = {
      risk_assessment_id: assessmentId.value,
      title: riskItemForm.title.trim(),
      description: riskItemForm.description.trim(),
      threat_scenario: riskItemForm.threat_scenario.trim(),
      asset_affected: riskItemForm.asset_affected.trim(),
      likelihood: riskItemForm.likelihood,
      impact: riskItemForm.impact,
      risk_level: riskItemForm.risk_level,
      mitigation_plan: riskItemForm.mitigation_plan.trim(),
      residual_risk_level: riskItemForm.residual_risk_level || null,
      status: riskItemForm.status,
      owner_user_id: normalizeOptional(riskItemForm.owner_user_id),
    };

    await riskItemService.create(payload);

    successMessage.value = "Risk item created.";
    showRiskItemForm.value = false;

    riskItemForm.title = "";
    riskItemForm.description = "";
    riskItemForm.threat_scenario = "";
    riskItemForm.asset_affected = "";
    riskItemForm.likelihood = "medium";
    riskItemForm.impact = "medium";
    riskItemForm.risk_level = "medium";
    riskItemForm.mitigation_plan = "";
    riskItemForm.residual_risk_level = "";
    riskItemForm.status = "open";
    riskItemForm.owner_user_id = "";

    await loadAssessment();
    await loadRiskItems();
  } catch (error: any) {
    errorMessage.value = error?.message ?? "Failed to create risk item.";
  } finally {
    creatingRiskItem.value = false;
  }
}

async function updateRiskItemAssignment(
  itemId: string,
  patch: { owner_user_id?: string | null; due_date?: string | null },
): Promise<void> {
  try {
    const updated = await riskItemService.update(itemId, patch);
    const idx = riskItems.value.findIndex((r: RiskItemRead) => r.id === itemId);
    if (idx !== -1) riskItems.value[idx] = updated;
  } catch {
    // Silent — the UI stays unchanged if the patch fails.
  }
}

function goBack(): void {
  router.push({ name: "risk-assessments" });
}

onMounted(async () => {
  await loadUsers();
  await loadProducts();
  await loadAssessment();
  await loadRiskItems();
});
</script>

<style scoped>
/* ── Modal ───────────────────────────────────────────────────────────────────── */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  backdrop-filter: blur(4px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  padding: 1rem;
  animation: fadeIn 0.15s ease;
}

@keyframes fadeIn {
  from {
    opacity: 0;
  }
  to {
    opacity: 1;
  }
}

.modal-content {
  background: linear-gradient(180deg, var(--color-card-start), var(--color-card-end));
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  max-width: 600px;
  width: 100%;
  max-height: 90vh;
  overflow-y: auto;
  box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.3);
  animation: slideUp 0.2s ease;
}

@keyframes slideUp {
  from {
    transform: translateY(20px);
    opacity: 0;
  }
  to {
    transform: translateY(0);
    opacity: 1;
  }
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1.5rem;
  border-bottom: 1px solid var(--color-border);
}

.modal-header h2 {
  margin: 0;
  font-size: 1.3rem;
}

.modal-close {
  background: none;
  border: none;
  font-size: 1.5rem;
  cursor: pointer;
  color: var(--color-text-muted);
  transition: color 0.2s;
  padding: 0;
  width: 2rem;
  height: 2rem;
  display: flex;
  align-items: center;
  justify-content: center;
}

.modal-close:hover {
  color: var(--color-text);
}

.modal-form {
  padding: 1.5rem;
  display: flex;
  flex-direction: column;
  gap: 1.2rem;
}

.form-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1rem;
}

.checkbox-group {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.modal-actions {
  display: flex;
  gap: 1rem;
  justify-content: flex-end;
  padding-top: 1rem;
  border-top: 1px solid var(--color-border);
  margin-top: 1rem;
}

/* ── Page Layout ─────────────────────────────────────────────────────────────── */
.page {
  display: flex;
  flex-direction: column;
  gap: 1.2rem;
}

.eyebrow {
  margin: 0 0 0.25rem;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  font-size: 0.78rem;
  color: var(--color-text-muted);
}

.page-header,
.panel-header,
.risk-card-header {
  display: flex;
  justify-content: space-between;
  gap: 1rem;
  align-items: flex-start;
}

.page-header h1,
.panel-header h2,
.risk-card-header h3 {
  margin: 0;
}

.page-subtitle {
  margin: 0.4rem 0 0;
}

.header-actions,
.form-actions {
  display: flex;
  gap: 0.75rem;
}

.risk-items-actions {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

/* ── Actions Bar ─────────────────────────────────────────────────────────────── */
.actions-bar {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 1.25rem;
}

.action-group {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 1.2rem;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  background: var(--color-surface-soft);
  transition: all 0.2s ease;
}

.action-group:hover {
  border-color: var(--color-primary);
  background: var(--color-surface-elevated);
}

.action-content {
  flex: 1;
}

.action-title {
  margin: 0 0 0.3rem;
  font-size: 0.95rem;
  font-weight: 700;
  color: var(--color-text);
}

.action-description {
  margin: 0;
  font-size: 0.82rem;
  color: var(--color-text-muted);
  line-height: 1.4;
}

/* ── Edit Form ───────────────────────────────────────────────────────────────── */
.edit-form {
  display: flex;
  flex-direction: column;
  gap: 1.2rem;
}

.form-grid-2 {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 1rem;
}

.panel-description {
  margin: 0.4rem 0 0;
  font-size: 0.85rem;
  color: var(--color-text-muted);
}

/* ── Responsive ──────────────────────────────────────────────────────────────── */
@media (max-width: 1200px) {
  .form-grid-2 {
    grid-template-columns: repeat(2, 1fr);
  }

  .actions-bar {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 768px) {
  .form-grid-2,
  .form-row {
    grid-template-columns: 1fr;
  }

  .modal-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 1rem;
  }

  .modal-close {
    align-self: flex-end;
    margin-top: -0.5rem;
  }

  .action-group {
    flex-direction: column;
    text-align: center;
  }

  .action-content {
    width: 100%;
  }

  .overview-actions {
    width: 100%;
    flex-direction: column;
  }

  .overview-actions .button {
    width: 100%;
  }
}

.details-grid {
  display: grid;
  grid-template-columns: 1.2fr 1fr;
  gap: 1.25rem;
}

.panel {
  background: linear-gradient(180deg, var(--color-card-start), var(--color-card-end));
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  padding: 1rem;
  color: var(--color-text);
  box-shadow: var(--shadow-lg);
  backdrop-filter: blur(14px);
}

/* ── Modern Overview Grid ──────────────────────────────────────────────────── */
.overview-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 1rem;
  margin-bottom: 1.5rem;
}

.overview-card {
  display: flex;
  flex-direction: column;
  gap: 0.4rem;
  padding: 0.9rem 1rem;
  border-radius: var(--radius-md);
  background: var(--color-surface-soft);
  border: 1px solid var(--color-border);
  transition: all 0.2s ease;
}

.overview-card:hover {
  border-color: var(--color-primary);
  background: var(--color-surface-elevated);
}

.overview-label {
  font-size: 0.75rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: var(--color-text-muted);
}

.overview-value {
  font-size: 0.95rem;
  font-weight: 600;
  color: var(--color-text);
  word-break: break-word;
}

.summary-section {
  padding: 1rem;
  border-radius: var(--radius-md);
  background: var(--color-surface-soft);
  border: 1px solid var(--color-border);
}

.summary-title {
  margin: 0 0 0.5rem;
  font-size: 0.9rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--color-text-muted);
}

.summary-text {
  margin: 0;
  font-size: 0.95rem;
  line-height: 1.5;
  color: var(--color-text);
}

/* ── Overview Actions ────────────────────────────────────────────────────────── */
.overview-actions {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.detail-full {
  grid-column: 1 / -1;
}

/* ── Form Styling ────────────────────────────────────────────────────────────── */
.form-grid,
.form-grid-2 {
  display: grid;
  gap: 1rem;
}

.form-grid {
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

.field,
.checkbox-field {
  display: flex;
  flex-direction: column;
  gap: 0.35rem;
}

.form-actions {
  display: flex;
  gap: 0.75rem;
  padding-top: 1rem;
  border-top: 1px solid var(--color-border);
}

.checkbox-field {
  flex-direction: row;
  align-items: center;
  gap: 0.65rem;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  padding: 0.85rem 0.95rem;
  background: var(--color-surface-soft);
}

.field-label,
.checkbox-field span {
  font-size: 0.82rem;
  font-weight: 700;
  color: var(--color-text-muted);
  text-transform: uppercase;
  letter-spacing: 0.06em;
}

.checkbox-field input {
  accent-color: var(--color-primary);
}

.field-full {
  grid-column: 1 / -1;
}

.status-pill,
.risk-level-pill {
  display: inline-flex;
  align-items: center;
  border-radius: 999px;
  background: var(--color-status-bg);
  color: var(--color-status-text);
  border: 1px solid var(--color-status-border);
  padding: 0.28rem 0.62rem;
  font-size: 0.85rem;
  font-weight: 600;
  text-transform: capitalize;
}

.count-badge {
  min-width: 2rem;
  text-align: center;
  padding: 0.35rem 0.65rem;
  border-radius: 999px;
  background: var(--color-surface-elevated);
  border: 1px solid var(--color-border);
  color: var(--color-text);
  font-weight: 700;
}

.accent-badge {
  background: var(--color-success-bg);
  color: var(--color-success-text);
}

.placeholder-box {
  border: 1px dashed var(--color-border);
  border-radius: var(--radius-md);
  padding: 1rem;
  background: var(--color-surface-soft);
}

.placeholder-title {
  margin: 0 0 0.4rem;
  font-weight: 700;
}

.placeholder-text {
  margin: 0 0 0.8rem;
  color: var(--color-text-muted);
}

.placeholder-actions {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  flex-wrap: wrap;
  margin-bottom: 0.9rem;
}

.workflow-link {
  text-decoration: none;
}

.placeholder-note {
  margin: 0;
  color: var(--color-text-muted);
}

.placeholder-list {
  margin: 0;
  padding-left: 1.25rem;
  color: var(--color-text);
}

.editor-block {
  margin-bottom: 1rem;
  padding: 1rem;
  border-radius: var(--radius-md);
  border: 1px solid var(--color-border);
  background: var(--color-surface-soft);
}

.risk-items-grid {
  display: grid;
  grid-template-columns: 1fr;
  gap: 1rem;
}

.risk-card {
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  padding: 1rem;
  background: linear-gradient(180deg, var(--color-card-start), var(--color-card-end));
  color: var(--color-text);
  box-shadow: inset 0 1px 0 var(--color-surface-elevated);
}

.risk-meta {
  margin: 0.35rem 0 0;
  color: var(--color-text-muted);
  text-transform: capitalize;
}

.risk-copy {
  display: grid;
  gap: 0.7rem;
  margin-top: 0.9rem;
}

.risk-copy p {
  margin: 0;
}

.risk-card-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 0.75rem;
  margin-top: 0.9rem;
}

.risk-card-grid > div {
  border: 1px solid var(--color-border);
  border-radius: 10px;
  padding: 0.8rem 0.9rem;
  background: var(--color-surface-soft);
}

.mono {
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
  word-break: break-all;
}

.feedback,
.loading-state,
.empty-state {
  border-radius: var(--radius-md);
  padding: 0.9rem 1rem;
}

.feedback {
  margin-bottom: 0.9rem;
}

.loading-state,
.empty-state {
  background: var(--color-surface-soft);
  border: 1px dashed var(--color-border);
  color: var(--color-text-muted);
}

.feedback-error {
  background: var(--color-danger-bg);
  border: 1px solid var(--color-danger-border);
  color: var(--color-danger-text);
}

.feedback-success {
  background: var(--color-success-bg);
  border: 1px solid var(--color-success-border);
  color: var(--color-success-text);
}

@media (max-width: 1200px) {
  .overview-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 768px) {
  .overview-grid,
  .details-grid,
  .form-grid,
  .risk-card-grid {
    grid-template-columns: 1fr;
  }

  .page-header,
  .panel-header,
  .header-actions,
  .form-actions,
  .risk-card-header,
  .risk-items-actions {
    flex-direction: column;
    align-items: stretch;
  }
}
</style>

<style>
/* ── Card border visibility in light mode ── */
[data-theme="light"] .page .panel {
  box-shadow: 0 2px 6px rgba(0,0,0,0.09), 0 0 0 1px rgba(0,0,0,0.16);
  border-color: transparent;
}
[data-theme="light"] .page .overview-card {
  box-shadow: 0 1px 4px rgba(0,0,0,0.08), 0 0 0 1px rgba(0,0,0,0.14);
  border-color: transparent;
}
[data-theme="light"] .page .risk-card {
  box-shadow: 0 1px 4px rgba(0,0,0,0.08), 0 0 0 1px rgba(0,0,0,0.14);
  border-color: transparent;
}
</style>
