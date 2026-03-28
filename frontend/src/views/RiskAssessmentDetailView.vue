<template>
  <section class="page">
    <header class="page-header">
      <div>
        <p class="eyebrow">Risk Assessment</p>
        <h1>{{ assessment?.title ?? "Risk Assessment Detail" }}</h1>
        <p class="page-subtitle">
          View assessment metadata, edit the assessment, manage risk items, and duplicate a new version.
        </p>
      </div>
      <div class="header-actions">
        <button class="secondary-button" type="button" @click="goBack">Back</button>
        <button class="primary-button" type="button" @click="loadAssessment" :disabled="loading">
          {{ loading ? "Refreshing..." : "Refresh" }}
        </button>
      </div>
    </header>

    <p v-if="errorMessage" class="error-text">{{ errorMessage }}</p>
    <p v-if="successMessage" class="success-text">{{ successMessage }}</p>

    <section v-if="loading && !assessment" class="panel">
      <div class="loading-state">Loading assessment...</div>
    </section>

    <template v-else-if="assessment">
      <section class="details-grid">
        <article class="panel">
          <div class="panel-header">
            <h2>Assessment Overview</h2>
          </div>

          <dl class="detail-list">
            <div>
              <dt>ID</dt>
              <dd class="mono">{{ assessment.id }}</dd>
            </div>
            <div>
              <dt>Product</dt>
              <dd>{{ getProductName(assessment.product_id) }}</dd>
            </div>
            <div>
              <dt>Product ID</dt>
              <dd class="mono">{{ assessment.product_id }}</dd>
            </div>
            <div>
              <dt>Product Release ID</dt>
              <dd class="mono">{{ assessment.product_release_id ?? "—" }}</dd>
            </div>
            <div>
              <dt>Version</dt>
              <dd>{{ assessment.version_label }}</dd>
            </div>
            <div>
              <dt>Status</dt>
              <dd><span class="status-pill">{{ assessment.status }}</span></dd>
            </div>
            <div>
              <dt>Methodology</dt>
              <dd>{{ assessment.methodology }}</dd>
            </div>
            <div>
              <dt>Owner</dt>
              <dd>{{ getUserDisplay(assessment.owner_user_id) }}</dd>
            </div>
            <div>
              <dt>Approved At</dt>
              <dd>{{ formatDate(assessment.approved_at) }}</dd>
            </div>
            <div>
              <dt>Created At</dt>
              <dd>{{ formatDate(assessment.created_at) }}</dd>
            </div>
            <div>
              <dt>Updated At</dt>
              <dd>{{ formatDate(assessment.updated_at) }}</dd>
            </div>
            <div class="detail-full">
              <dt>Summary</dt>
              <dd>{{ assessment.summary || "—" }}</dd>
            </div>
          </dl>
        </article>

        <article class="panel">
          <div class="panel-header">
            <h2>Edit Assessment</h2>
          </div>

          <form class="form-grid" @submit.prevent="updateAssessment">
            <label class="field">
              <span>Title</span>
              <input v-model="editForm.title" type="text" maxlength="255" />
            </label>

            <label class="field">
              <span>Version Label</span>
              <input v-model="editForm.version_label" type="text" maxlength="100" />
            </label>

            <label class="field">
              <span>Status</span>
              <select v-model="editForm.status">
                <option value="">No change</option>
                <option v-for="option in assessmentStatuses" :key="option" :value="option">
                  {{ option }}
                </option>
              </select>
            </label>

            <label class="field">
              <span>Methodology</span>
              <input v-model="editForm.methodology" type="text" />
            </label>

            <label class="field">
              <span>Product Release ID</span>
              <input v-model="editForm.product_release_id" type="text" />
            </label>

            <label class="field">
              <span>Owner</span>
              <select v-model="editForm.owner_user_id">
                <option value="">No owner</option>
                <option v-for="user in users" :key="user.id" :value="user.id">
                  {{ getUserDisplay(user.id) }}
                </option>
              </select>
            </label>

            <label class="field field-full">
              <span>Summary</span>
              <textarea v-model="editForm.summary" rows="4" />
            </label>

            <div class="form-actions field-full">
              <button class="primary-button" type="submit" :disabled="savingAssessment">
                {{ savingAssessment ? "Saving..." : "Save Changes" }}
              </button>
              <button
                class="ghost-button"
                type="button"
                @click="approveAssessment"
                :disabled="approvingAssessment"
              >
                {{ approvingAssessment ? "Approving..." : "Approve Assessment" }}
              </button>
            </div>
          </form>
        </article>
      </section>

      <section class="details-grid">
        <article class="panel">
          <div class="panel-header">
            <h2>Duplicate New Version</h2>
          </div>

          <form class="form-grid" @submit.prevent="duplicateAssessment">
            <label class="field">
              <span>New Version Label</span>
              <input v-model="duplicateForm.version_label" type="text" required maxlength="100" />
            </label>

            <label class="field">
              <span>New Title</span>
              <input v-model="duplicateForm.title" type="text" maxlength="255" />
            </label>

            <label class="field">
              <span>Product Release ID</span>
              <input v-model="duplicateForm.product_release_id" type="text" />
            </label>

            <label class="field">
              <span>Owner</span>
              <select v-model="duplicateForm.owner_user_id">
                <option value="">Keep / no override</option>
                <option v-for="user in users" :key="user.id" :value="user.id">
                  {{ getUserDisplay(user.id) }}
                </option>
              </select>
            </label>

            <label class="field field-full">
              <span>Summary Override</span>
              <textarea v-model="duplicateForm.summary" rows="3" />
            </label>

            <label class="checkbox-field">
              <input v-model="duplicateForm.reset_status_to_draft" type="checkbox" />
              <span>Reset status to draft</span>
            </label>

            <label class="checkbox-field">
              <input v-model="duplicateForm.copy_risk_items" type="checkbox" />
              <span>Copy risk items</span>
            </label>

            <label class="checkbox-field">
              <input v-model="duplicateForm.copy_requirement_mappings" type="checkbox" />
              <span>Copy requirement mappings</span>
            </label>

            <label class="checkbox-field">
              <input v-model="duplicateForm.copy_evidence_links" type="checkbox" />
              <span>Copy evidence links</span>
            </label>

            <div class="form-actions field-full">
              <button class="primary-button" type="submit" :disabled="duplicatingAssessment">
                {{ duplicatingAssessment ? "Duplicating..." : "Duplicate Version" }}
              </button>
            </div>
          </form>
        </article>

        <article class="panel">
          <div class="panel-header">
            <h2>Evidence Attachments</h2>
          </div>

          <div class="placeholder-box">
            <p class="placeholder-title">File upload placeholder</p>
            <p class="placeholder-text">
              This section is compatible with later file uploads. For now, add evidence records using
              file paths or external URLs in the backend/API.
            </p>
            <ul class="placeholder-list">
              <li>Assessment-linked evidence count: {{ assessment.evidence_items_count ?? 0 }}</li>
              <li>Future enhancement: direct uploads + storage integration</li>
              <li>Current scope: metadata placeholder only</li>
            </ul>
          </div>
        </article>
      </section>

      <section class="panel">
        <div class="panel-header">
          <h2>Risk Items</h2>
          <button class="primary-button" type="button" @click="showRiskItemForm = !showRiskItemForm">
            {{ showRiskItemForm ? "Close Editor" : "Add Risk Item" }}
          </button>
        </div>

        <div v-if="showRiskItemForm" class="editor-block">
          <form class="form-grid" @submit.prevent="createRiskItem">
            <label class="field">
              <span>Title</span>
              <input v-model="riskItemForm.title" type="text" required maxlength="255" />
            </label>

            <label class="field">
              <span>Asset Affected</span>
              <input v-model="riskItemForm.asset_affected" type="text" required maxlength="255" />
            </label>

            <label class="field">
              <span>Likelihood</span>
              <select v-model="riskItemForm.likelihood">
                <option v-for="level in riskLevels" :key="level" :value="level">{{ level }}</option>
              </select>
            </label>

            <label class="field">
              <span>Impact</span>
              <select v-model="riskItemForm.impact">
                <option v-for="level in riskLevels" :key="level" :value="level">{{ level }}</option>
              </select>
            </label>

            <label class="field">
              <span>Risk Level</span>
              <select v-model="riskItemForm.risk_level">
                <option v-for="level in riskLevels" :key="level" :value="level">{{ level }}</option>
              </select>
            </label>

            <label class="field">
              <span>Status</span>
              <select v-model="riskItemForm.status">
                <option v-for="statusOption in riskItemStatuses" :key="statusOption" :value="statusOption">
                  {{ statusOption }}
                </option>
              </select>
            </label>

            <label class="field">
              <span>Residual Risk Level</span>
              <select v-model="riskItemForm.residual_risk_level">
                <option value="">None</option>
                <option v-for="level in riskLevels" :key="level" :value="level">{{ level }}</option>
              </select>
            </label>

            <label class="field">
              <span>Owner</span>
              <select v-model="riskItemForm.owner_user_id">
                <option value="">No owner</option>
                <option v-for="user in users" :key="user.id" :value="user.id">
                  {{ getUserDisplay(user.id) }}
                </option>
              </select>
            </label>

            <label class="field field-full">
              <span>Description</span>
              <textarea v-model="riskItemForm.description" rows="3" required />
            </label>

            <label class="field field-full">
              <span>Threat Scenario</span>
              <textarea v-model="riskItemForm.threat_scenario" rows="3" required />
            </label>

            <label class="field field-full">
              <span>Mitigation Plan</span>
              <textarea v-model="riskItemForm.mitigation_plan" rows="3" required />
            </label>

            <div class="form-actions field-full">
              <button class="primary-button" type="submit" :disabled="creatingRiskItem">
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

            <p><strong>Description:</strong> {{ item.description }}</p>
            <p><strong>Threat Scenario:</strong> {{ item.threat_scenario }}</p>
            <p><strong>Mitigation:</strong> {{ item.mitigation_plan }}</p>

            <div class="risk-card-grid">
              <div><strong>Likelihood:</strong> {{ item.likelihood }}</div>
              <div><strong>Impact:</strong> {{ item.impact }}</div>
              <div><strong>Residual:</strong> {{ item.residual_risk_level ?? "—" }}</div>
              <div><strong>Owner:</strong> {{ getUserDisplay(item.owner_user_id) }}</div>
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

import { adminService } from "@/services/admin-service";
import { productService } from "@/services/product-service";
import { riskAssessmentService } from "@/services/risk-assessment-service";
import { riskItemService } from "@/services/risk-item-service";
import type { AdminUserRead } from "@/types/admin";
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
const users = ref<AdminUserRead[]>([]);
const products = ref<ProductSummaryRead[]>([]);
const loading = ref(false);
const riskItemsLoading = ref(false);
const savingAssessment = ref(false);
const approvingAssessment = ref(false);
const duplicatingAssessment = ref(false);
const creatingRiskItem = ref(false);
const showRiskItemForm = ref(false);

const errorMessage = ref("");
const successMessage = ref("");

const assessmentStatuses: RiskAssessmentStatus[] = ["draft", "in_review", "approved", "archived"];
const riskLevels: RiskLevel[] = ["low", "medium", "high", "critical"];
const riskItemStatuses: RiskItemStatus[] = ["open", "in_progress", "mitigated", "accepted", "closed"];

const assessmentId = computed(() => String(route.params.assessmentId));

const editForm = reactive({
  title: "",
  version_label: "",
  status: "" as RiskAssessmentStatus | "",
  methodology: "",
  summary: "",
  owner_user_id: "",
  product_release_id: "",
});

const duplicateForm = reactive({
  version_label: "",
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

  const user = users.value.find((item) => item.id === userId);
  if (!user) return userId;

  const fullName = user.full_name?.trim();
  return fullName ? `${fullName} (${user.email})` : user.email;
}

function getProductName(productId: string | null | undefined): string {
  if (!productId) return "—";

  const product = products.value.find((item) => item.id === productId);
  if (!product) return productId;

  return "name" in product && product.name ? product.name : product.id;
}

async function loadUsers(): Promise<void> {
  try {
    users.value = await adminService.listUsers();
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

function syncEditForm(): void {
  if (!assessment.value) return;
  editForm.title = assessment.value.title;
  editForm.version_label = assessment.value.version_label;
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
      version_label: editForm.version_label.trim() || undefined,
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
      version_label: duplicateForm.version_label.trim(),
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

    successMessage.value = "Assessment version duplicated.";
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
.page {
  display: flex;
  flex-direction: column;
  gap: 1.25rem;
}

.eyebrow {
  margin: 0 0 0.25rem;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  font-size: 0.78rem;
  color: #64748b;
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
  color: #64748b;
}

.header-actions,
.form-actions {
  display: flex;
  gap: 0.75rem;
}

.details-grid {
  display: grid;
  grid-template-columns: 1.2fr 1fr;
  gap: 1.25rem;
}

.panel {
  background: #fff;
  border: 1px solid #e2e8f0;
  border-radius: 14px;
  padding: 1rem;
  color: #0f172a;
}

.detail-list {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 1rem;
  margin: 0;
}

.detail-list dt {
  font-size: 0.85rem;
  color: #64748b;
  margin-bottom: 0.25rem;
}

.detail-list dd {
  margin: 0;
  color: #0f172a;
}

.detail-full {
  grid-column: 1 / -1;
}

.form-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 1rem;
}

.field,
.checkbox-field {
  display: flex;
  flex-direction: column;
  gap: 0.35rem;
}

.checkbox-field {
  flex-direction: row;
  align-items: center;
}

.field span,
.checkbox-field span {
  font-size: 0.92rem;
  font-weight: 600;
  color: #334155;
}

.field input,
.field select,
.field textarea {
  width: 100%;
  border: 1px solid #cbd5e1;
  border-radius: 10px;
  padding: 0.75rem 0.85rem;
  font: inherit;
  background: #fff;
  color: #0f172a;
  box-sizing: border-box;
}

.field textarea {
  resize: vertical;
}

.field-full {
  grid-column: 1 / -1;
}

.primary-button,
.secondary-button,
.ghost-button {
  border-radius: 10px;
  padding: 0.75rem 1rem;
  font: inherit;
  cursor: pointer;
  border: 1px solid transparent;
}

.primary-button {
  background: #0f172a;
  color: #fff;
}

.secondary-button {
  background: #e2e8f0;
  color: #0f172a;
}

.ghost-button {
  background: transparent;
  color: #334155;
  border-color: #cbd5e1;
}

.status-pill,
.risk-level-pill {
  display: inline-flex;
  align-items: center;
  border-radius: 999px;
  background: #eff6ff;
  color: #1d4ed8;
  padding: 0.25rem 0.55rem;
  font-size: 0.85rem;
  font-weight: 600;
}

.placeholder-box {
  border: 1px dashed #cbd5e1;
  border-radius: 12px;
  padding: 1rem;
  background: #f8fafc;
}

.placeholder-title {
  margin: 0 0 0.4rem;
  font-weight: 700;
}

.placeholder-text {
  margin: 0 0 0.8rem;
  color: #475569;
}

.placeholder-list {
  margin: 0;
  padding-left: 1.25rem;
  color: #334155;
}

.editor-block {
  margin-bottom: 1rem;
  padding: 1rem 0;
}

.risk-items-grid {
  display: grid;
  grid-template-columns: 1fr;
  gap: 1rem;
}

.risk-card {
  border: 1px solid #e2e8f0;
  border-radius: 12px;
  padding: 1rem;
  background: #fcfcfd;
  color: #0f172a;
}

.risk-meta {
  margin: 0.35rem 0 0;
  color: #64748b;
}

.risk-card-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 0.75rem;
  margin-top: 0.9rem;
}

.mono {
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
  word-break: break-all;
}

.loading-state,
.empty-state,
.error-text,
.success-text {
  padding: 0.75rem 0;
}

.empty-state,
.loading-state {
  color: #0f172a;
}

.error-text {
  color: #b91c1c;
}

.success-text {
  color: #15803d;
}

@media (max-width: 960px) {
  .details-grid,
  .form-grid,
  .detail-list,
  .risk-card-grid {
    grid-template-columns: 1fr;
  }

  .page-header,
  .panel-header,
  .header-actions,
  .form-actions,
  .risk-card-header {
    flex-direction: column;
    align-items: stretch;
  }
}
</style>