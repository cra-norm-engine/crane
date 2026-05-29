<template>
  <section class="page">
    <header class="page-header">
      <div>
        <h1 class="page-title">Risk Assessments</h1>
        <p class="muted page-subtitle">
          Structured cybersecurity risk assessments for products and releases.
        </p>
      </div>
      <AppButton variant="primary" type="button" @click="openCreateForm = !openCreateForm">
        {{ openCreateForm ? "Close" : "New Assessment" }}
      </AppButton>
    </header>

    <section class="panel filters-panel">
      <div class="filters-grid">
        <label class="field">
          <span class="field-label">Product</span>
          <select v-model="filters.productId" class="select">
            <option value="">All products</option>
            <option v-for="product in products" :key="product.id" :value="product.id">
              {{ getProductLabel(product) }}
            </option>
          </select>
        </label>

        <label class="field">
          <span class="field-label">Release</span>
          <select v-model="filters.productReleaseId" class="select" :disabled="!filters.productId">
            <option value="">{{ filters.productId ? "All releases" : "Select a product first" }}</option>
            <option v-for="release in filterReleases" :key="release.id" :value="release.id">
              {{ getReleaseLabel(release) }}
            </option>
          </select>
        </label>

      </div>
    </section>

    <section v-if="openCreateForm" class="panel">
      <div class="panel-header">
        <h2 class="section-title">Create Risk Assessment</h2>
        <span class="count-badge accent-badge">Draft setup</span>
      </div>

      <form class="form-grid" @submit.prevent="createAssessment">
        <label class="field">
          <span class="field-label">Product</span>
          <select v-model="createForm.product_id" class="select" required>
            <option value="" disabled>Select a product</option>
            <option v-for="product in products" :key="product.id" :value="product.id">
              {{ getProductLabel(product) }}
            </option>
          </select>
        </label>

        <label class="field">
          <span class="field-label">Release</span>
          <select v-model="createReleaseId" class="select" :disabled="!createForm.product_id">
            <option value="">{{ createForm.product_id ? "No linked release" : "Select a product first" }}</option>
            <option v-for="release in createReleases" :key="release.id" :value="release.id">
              {{ getReleaseLabel(release) }}
            </option>
          </select>
        </label>

        <label class="field">
          <span class="field-label">Title</span>
          <input v-model="createForm.title" class="input" type="text" required maxlength="255" />
        </label>

        <label class="field">
          <span class="field-label">Version Name (Optional)</span>
          <input v-model="createForm.user_version" class="input" type="text" maxlength="100" placeholder="e.g., Q2 Assessment, Annual Review" />
        </label>

        <label class="field">
          <span class="field-label">Status</span>
          <select v-model="createForm.status" class="select">
            <option v-for="option in assessmentStatuses" :key="option" :value="option">
              {{ option }}
            </option>
          </select>
        </label>

        <label class="field">
          <span class="field-label">Methodology</span>
          <input v-model="createForm.methodology" class="input" type="text" required />
        </label>

        <label class="field field-full">
          <span class="field-label">Summary</span>
          <textarea v-model="createForm.summary" class="textarea" rows="4" required />
        </label>

        <div class="form-actions field-full">
          <AppButton variant="primary" type="submit" :disabled="creating">
            {{ creating ? "Creating..." : "Create Assessment" }}
          </AppButton>
        </div>
      </form>
    </section>

    <section class="panel">
      <div class="panel-header">
        <h2 class="section-title">Assessment List</h2>
        <span class="count-badge">{{ assessments.length }}</span>
      </div>

      <div v-if="errorMessage" class="feedback feedback-error">{{ errorMessage }}</div>
      <div v-if="successMessage" class="feedback feedback-success">{{ successMessage }}</div>

      <div v-if="loading" class="loading-state">Loading risk assessments...</div>

      <div v-else-if="assessments.length === 0" class="empty-state">
        No risk assessments found. Create a new assessment to get started.
      </div>

      <div v-else class="table-wrapper">
        <table class="data-table table">
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
              <td>{{ assessment.display_version }}</td>
              <td>
                <span class="status-pill">{{ formatReleaseStatus(assessment.status) }}</span>
              </td>
              <td>{{ assessment.methodology }}</td>
              <td>{{ getProductName(assessment.product_id) }}</td>
              <td>{{ getReleaseName(assessment.product_release_id) }}</td>
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
import { onMounted, reactive, ref, watch } from "vue";
import { useRouter } from "vue-router";

import AppButton from "@/components/AppButton.vue";
import { productReleaseService } from "@/services/product-release-service";
import { productService } from "@/services/product-service";
import { riskAssessmentService } from "@/services/risk-assessment-service";
import { useAuthStore } from "@/stores/auth";
import type {
  RiskAssessmentCreate,
  RiskAssessmentRead,
  RiskAssessmentStatus,
} from "@/types/risk-assessment";
import type { ProductSummaryRead } from "@/types/product";
import type { ProductReleaseRead } from "@/types/release-gate";

const router = useRouter();
const authStore = useAuthStore();

const loading = ref(false);
const creating = ref(false);
const openCreateForm = ref(false);
const errorMessage = ref("");
const successMessage = ref("");
const assessments = ref<RiskAssessmentRead[]>([]);
const products = ref<ProductSummaryRead[]>([]);
const filterReleases = ref<ProductReleaseRead[]>([]);
const createReleases = ref<ProductReleaseRead[]>([]);
const createReleaseId = ref("");
// Maps release UUID → display_version string for all releases referenced by loaded assessments.
const releaseMap = ref<Record<string, string>>({});

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
  user_version: null,
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

function getProductLabel(product: ProductSummaryRead): string {
  if (!("name" in product) || !product.name) return product.product_code;
  return product.product_code
    ? `${product.name} (${product.product_code})`
    : product.name;
}

function getProductName(productId: string): string {
  const product = products.value.find((item) => item.id === productId);

  if (!product) {
    return productId;
  }

  return "name" in product && product.name ? product.name : product.id;
}

function formatReleaseStatus(value: string): string {
  return value.replaceAll("_", " ");
}

function getReleaseLabel(release: ProductReleaseRead): string {
  return `${release.display_version} (${formatReleaseStatus(release.release_status)})`;
}

function getReleaseName(releaseId: string | null): string {
  if (!releaseId) {
    return "—";
  }

  // Check the global map built from all loaded assessments first.
  if (releaseMap.value[releaseId]) {
    return releaseMap.value[releaseId];
  }

  const release = [...filterReleases.value, ...createReleases.value].find((item) => item.id === releaseId);
  return release ? release.display_version : releaseId;
}

async function loadProducts(): Promise<void> {
  try {
    products.value = await productService.list();
  } catch (error) {
    console.error("Failed to load products.", error);
  }
}

async function loadReleases(productId: string): Promise<ProductReleaseRead[]> {
  if (!productId.trim()) {
    return [];
  }

  try {
    return await productReleaseService.list(productId.trim());
  } catch (error) {
    console.error("Failed to load product releases.", error);
    return [];
  }
}

async function buildReleaseMap(loaded: RiskAssessmentRead[]): Promise<void> {
  // Collect product IDs that have at least one assessment with a release.
  const productIds = [
    ...new Set(
      loaded
        .filter((a) => a.product_release_id !== null)
        .map((a) => a.product_id),
    ),
  ];

  const map: Record<string, string> = {};
  await Promise.all(
    productIds.map(async (pid) => {
      try {
        const releases = await productReleaseService.list(pid);
        for (const r of releases) {
          map[r.id] = r.display_version;
        }
      } catch {
        // Non-critical: table will fall back to UUID for this product's releases.
      }
    }),
  );
  releaseMap.value = map;
}

async function loadAssessments(): Promise<void> {
  loading.value = true;
  errorMessage.value = "";
  successMessage.value = "";

  try {
    const productId = filters.productId.trim();
    const productReleaseId = filters.productReleaseId.trim();

    const loaded = await riskAssessmentService.list({
      product_id: productId || undefined,
      product_release_id: productReleaseId || undefined,
    });
    assessments.value = loaded;
    void buildReleaseMap(loaded);
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
      product_release_id: normalizeOptional(createReleaseId.value),
      title: createForm.title.trim(),
      user_version: normalizeOptional(createForm.user_version),
      status: createForm.status,
      methodology: createForm.methodology.trim(),
      summary: createForm.summary.trim(),
      owner_user_id: createForm.owner_user_id.trim(),
    };

    await riskAssessmentService.create(payload);

    successMessage.value = "Risk assessment created successfully.";
    openCreateForm.value = false;

    createForm.product_id = "";
    createForm.product_release_id = null;
    createReleaseId.value = "";
    createReleases.value = [];
    createForm.title = "";
    createForm.user_version = null;
    createForm.status = "draft";
    createForm.methodology = "STRIDE";
    createForm.summary = "";
    createForm.owner_user_id = authStore.user?.id ?? "";

    await loadAssessments();
  } catch (error: any) {
    errorMessage.value = error?.message ?? "Failed to create risk assessment.";
  } finally {
    creating.value = false;
  }
}


function goToDetail(assessmentId: string): void {
  router.push({
    name: "risk-assessment-detail",
    params: { assessmentId },
  });
}

onMounted(async () => {
  createForm.owner_user_id = authStore.user?.id ?? "";
  await loadProducts();
  void loadAssessments();
});

watch(
  () => filters.productId,
  async (productId) => {
    filters.productReleaseId = "";
    filterReleases.value = await loadReleases(productId);
    void loadAssessments();
  },
);

watch(
  () => filters.productReleaseId,
  () => { void loadAssessments(); },
);

watch(
  () => createForm.product_id,
  async (productId) => {
    createReleaseId.value = "";
    createForm.product_release_id = null;
    createReleases.value = await loadReleases(productId);
  },
);

watch(createReleaseId, (releaseId) => {
  createForm.product_release_id = normalizeOptional(releaseId);
});
</script>

<style scoped>
.page {
  display: flex;
  flex-direction: column;
  gap: 1.2rem;
}

.panel {
  background: linear-gradient(180deg, var(--color-card-start), var(--color-card-end));
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  padding: 1rem;
  box-shadow: var(--shadow-lg);
  backdrop-filter: blur(14px);
  color: var(--color-text);
}

.page-header,
.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 1rem;
}

/* section-title is the global class; margin: 0 prevents panel layout shift */
.panel-header .section-title {
  margin: 0;
}

.page-subtitle {
  margin: 0.35rem 0 0;
  font-size: var(--text-sm);
  color: var(--color-text-muted);
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

.field-label {
  font-size: var(--text-xs);   /* 12px — eyebrow / label tier */
  font-weight: 600;
  color: var(--color-text-muted);
  text-transform: uppercase;
  letter-spacing: 0.07em;
}

.field-full {
  grid-column: 1 / -1;
}

.form-actions {
  display: flex;
  align-items: end;
  gap: 0.75rem;
}

.count-badge {
  min-width: 2rem;
  text-align: center;
  padding: 0.25rem 0.65rem;
  border-radius: 999px;
  background: var(--color-surface-elevated);
  border: 1px solid var(--color-border);
  color: var(--color-text-muted);
  font-size: var(--text-sm);   /* 14px — badge tier */
  font-weight: 600;
}

.accent-badge {
  background: var(--color-success-bg);
  color: var(--color-success-text);
}


.table-wrapper {
  overflow-x: auto;
}

.data-table th,
.data-table td {
  padding: 0.8rem 0.75rem;
  border-top: 1px solid var(--color-divider);
  text-align: left;
  vertical-align: top;
}

.data-table th {
  color: var(--color-text-muted);
  font-size: var(--text-xs);   /* 12px — column header tier */
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  white-space: nowrap;
}

.data-table td {
  font-size: var(--text-sm);   /* 14px — body copy tier */
}

.table-row-link {
  cursor: pointer;
  transition: background 0.18s ease;
}

.table-row-link:hover {
  background: var(--color-surface-soft);
}

.status-pill {
  display: inline-flex;
  align-items: center;
  border-radius: 999px;
  background: var(--color-status-bg);
  color: var(--color-status-text);
  border: 1px solid var(--color-status-border);
  padding: 0.25rem 0.62rem;
  font-size: var(--text-xs);   /* 12px — badge / pill tier */
  font-weight: 600;
  text-transform: capitalize;
}

.uuid-cell {
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
  font-size: var(--text-xs);   /* 12px — monospace identifiers */
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

@media (max-width: 900px) {
  .filters-grid,
  .form-grid {
    grid-template-columns: 1fr;
  }

  .page-header,
  .panel-header,
  .form-actions {
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
</style>
