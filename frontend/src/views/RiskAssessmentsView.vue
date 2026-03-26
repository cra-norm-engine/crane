<template>
  <section class="page">
    <header class="page-header">
      <div>
        <h1>Risk Assessments</h1>
        <p class="page-subtitle">
          Structured cybersecurity risk assessments for products and releases.
        </p>
      </div>
      <button class="primary-button" type="button" @click="openCreateForm = !openCreateForm">
        {{ openCreateForm ? "Close" : "New Assessment" }}
      </button>
    </header>

    <section class="panel filters-panel">
      <div class="filters-grid">
        <label class="field">
          <span>Product ID</span>
          <input v-model="filters.productId" type="text" placeholder="Filter by product UUID" />
        </label>

        <label class="field">
          <span>Product Release ID</span>
          <input
            v-model="filters.productReleaseId"
            type="text"
            placeholder="Filter by product release UUID"
          />
        </label>

        <div class="filter-actions">
          <button class="secondary-button" type="button" @click="loadAssessments">
            Apply Filters
          </button>
          <button class="ghost-button" type="button" @click="resetFilters">
            Reset
          </button>
        </div>
      </div>
    </section>

    <section v-if="openCreateForm" class="panel">
      <div class="panel-header">
        <h2>Create Risk Assessment</h2>
      </div>

      <form class="form-grid" @submit.prevent="createAssessment">
        <label class="field">
          <span>Product ID</span>
          <input v-model="createForm.product_id" type="text" required />
        </label>

        <label class="field">
          <span>Product Release ID</span>
          <input v-model="createForm.product_release_id" type="text" />
        </label>

        <label class="field">
          <span>Title</span>
          <input v-model="createForm.title" type="text" required maxlength="255" />
        </label>

        <label class="field">
          <span>Version Label</span>
          <input v-model="createForm.version_label" type="text" required maxlength="100" />
        </label>

        <label class="field">
          <span>Status</span>
          <select v-model="createForm.status">
            <option v-for="option in assessmentStatuses" :key="option" :value="option">
              {{ option }}
            </option>
          </select>
        </label>

        <label class="field">
          <span>Methodology</span>
          <input v-model="createForm.methodology" type="text" required />
        </label>

        <label class="field field-full">
          <span>Summary</span>
          <textarea v-model="createForm.summary" rows="4" required />
        </label>

        <div class="form-actions field-full">
          <button class="primary-button" type="submit" :disabled="creating">
            {{ creating ? "Creating..." : "Create Assessment" }}
          </button>
        </div>
      </form>
    </section>

    <section class="panel">
      <div class="panel-header">
        <h2>Assessment List</h2>
        <span class="count-badge">{{ assessments.length }}</span>
      </div>

      <p v-if="errorMessage" class="error-text">{{ errorMessage }}</p>
      <p v-if="successMessage" class="success-text">{{ successMessage }}</p>

      <div v-if="loading" class="loading-state">Loading risk assessments...</div>

      <div v-else-if="assessments.length === 0" class="empty-state">
        No risk assessments found. Apply a product or release filter, or create a new assessment.
      </div>

      <div v-else class="table-wrapper">
        <table class="data-table">
          <thead>
            <tr>
              <th>Title</th>
              <th>Version</th>
              <th>Status</th>
              <th>Methodology</th>
              <th>Product</th>
              <th>Release</th>
              <th>Approved</th>
              <th>Updated</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="assessment in assessments"
              :key="assessment.id"
              class="table-row-link"
              @click="goToDetail(assessment.id)"
            >
              <td>{{ assessment.title }}</td>
              <td>{{ assessment.version_label }}</td>
              <td>
                <span class="status-pill">{{ assessment.status }}</span>
              </td>
              <td>{{ assessment.methodology }}</td>
              <td class="uuid-cell">{{ assessment.product_id }}</td>
              <td class="uuid-cell">{{ assessment.product_release_id ?? "—" }}</td>
              <td>{{ formatDate(assessment.approved_at) }}</td>
              <td>{{ formatDate(assessment.updated_at) }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>
  </section>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref } from "vue";
import { useRouter } from "vue-router";

import { riskAssessmentService } from "@/services/risk-assessment-service";
import { useAuthStore } from "@/stores/auth";
import type {
  RiskAssessmentCreate,
  RiskAssessmentRead,
  RiskAssessmentStatus,
} from "@/types/risk-assessment";

const router = useRouter();
const authStore = useAuthStore();

const loading = ref(false);
const creating = ref(false);
const openCreateForm = ref(false);
const errorMessage = ref("");
const successMessage = ref("");
const assessments = ref<RiskAssessmentRead[]>([]);

const assessmentStatuses: RiskAssessmentStatus[] = [
  "draft",
  "in_review",
  "approved",
  "archived",
];

const filters = reactive({
  productId: "",
  productReleaseId: "",
});

const createForm = reactive<RiskAssessmentCreate>({
  product_id: "",
  product_release_id: null,
  title: "",
  version_label: "",
  status: "draft",
  methodology: "STRIDE",
  summary: "",
  owner_user_id: authStore.user?.id ?? "",
});

function normalizeOptional(value: string | null | undefined): string | null {
  const trimmed = (value ?? "").trim();
  return trimmed.length > 0 ? trimmed : null;
}

function formatDate(value: string | null): string {
  if (!value) {
    return "—";
  }

  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return value;
  }

  return date.toLocaleString();
}

async function loadAssessments(): Promise<void> {
  loading.value = true;
  errorMessage.value = "";
  successMessage.value = "";

  try {
    const productId = filters.productId.trim();
    const productReleaseId = filters.productReleaseId.trim();

    if (!productId && !productReleaseId) {
      assessments.value = [];
      errorMessage.value = "Provide a product ID or product release ID to load assessments.";
      return;
    }

    assessments.value = await riskAssessmentService.list({
      product_id: productId || undefined,
      product_release_id: productReleaseId || undefined,
    });
  } catch (error: any) {
    errorMessage.value = error?.message ?? "Failed to load risk assessments.";
    assessments.value = [];
  } finally {
    loading.value = false;
  }
}

async function createAssessment(): Promise<void> {
  creating.value = true;
  errorMessage.value = "";
  successMessage.value = "";

  try {
    const payload: RiskAssessmentCreate = {
      product_id: createForm.product_id.trim(),
      product_release_id: normalizeOptional(createForm.product_release_id),
      title: createForm.title.trim(),
      version_label: createForm.version_label.trim(),
      status: createForm.status,
      methodology: createForm.methodology.trim(),
      summary: createForm.summary.trim(),
      owner_user_id: createForm.owner_user_id.trim(),
    };

    const created = await riskAssessmentService.create(payload);

    successMessage.value = "Risk assessment created successfully.";
    openCreateForm.value = false;

    createForm.product_id = "";
    createForm.product_release_id = null;
    createForm.title = "";
    createForm.version_label = "";
    createForm.status = "draft";
    createForm.methodology = "STRIDE";
    createForm.summary = "";
    createForm.owner_user_id = authStore.user?.id ?? "";

    if (filters.productId.trim() || filters.productReleaseId.trim()) {
      await loadAssessments();
    } else {
      assessments.value = [created, ...assessments.value];
    }
  } catch (error: any) {
    errorMessage.value = error?.message ?? "Failed to create risk assessment.";
  } finally {
    creating.value = false;
  }
}

function resetFilters(): void {
  filters.productId = "";
  filters.productReleaseId = "";
  assessments.value = [];
  errorMessage.value = "";
  successMessage.value = "";
}

function goToDetail(assessmentId: string): void {
  router.push({
    name: "risk-assessment-detail",
    params: { assessmentId },
  });
}

onMounted(() => {
  createForm.owner_user_id = authStore.user?.id ?? "";
  assessments.value = [];
});
</script>

<style scoped>
.page {
  display: flex;
  flex-direction: column;
  gap: 1.25rem;
}

.page-header,
.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 1rem;
}

.page-header h1,
.panel-header h2 {
  margin: 0;
}

.page-subtitle {
  margin: 0.35rem 0 0;
  color: #64748b;
}

.panel {
  background: #ffffff;
  border: 1px solid #e2e8f0;
  border-radius: 14px;
  padding: 1rem;
}

.filters-grid,
.form-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 1rem;
}

.field {
  display: flex;
  flex-direction: column;
  gap: 0.35rem;
}

.field span {
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
  box-sizing: border-box;
}

.field textarea {
  resize: vertical;
}

.field-full {
  grid-column: 1 / -1;
}

.filter-actions,
.form-actions {
  display: flex;
  align-items: end;
  gap: 0.75rem;
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

.count-badge {
  min-width: 2rem;
  text-align: center;
  padding: 0.35rem 0.65rem;
  border-radius: 999px;
  background: #e2e8f0;
  color: #0f172a;
  font-weight: 700;
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
  padding: 0.9rem 0.75rem;
  border-top: 1px solid #e2e8f0;
  text-align: left;
  vertical-align: top;
}

.data-table th {
  color: #475569;
  font-size: 0.9rem;
  font-weight: 700;
}

.table-row-link {
  cursor: pointer;
}

.table-row-link:hover {
  background: #f8fafc;
}

.status-pill {
  display: inline-flex;
  align-items: center;
  border-radius: 999px;
  background: #eff6ff;
  color: #1d4ed8;
  padding: 0.25rem 0.55rem;
  font-size: 0.85rem;
  font-weight: 600;
}

.uuid-cell {
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
  font-size: 0.84rem;
  word-break: break-all;
}

.loading-state,
.empty-state,
.error-text,
.success-text {
  padding: 0.75rem 0;
}

.error-text {
  color: #b91c1c;
}

.success-text {
  color: #15803d;
}

@media (max-width: 900px) {
  .filters-grid,
  .form-grid {
    grid-template-columns: 1fr;
  }

  .page-header,
  .panel-header,
  .filter-actions,
  .form-actions {
    flex-direction: column;
    align-items: stretch;
  }
}
</style>