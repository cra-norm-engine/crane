<template>
  <section class="page">
    <div class="page-header">
      <div>
        <h1 class="page-title">{{ product?.name || "Product Detail" }}</h1>
        <p class="muted">
          Review CRA scope, classification, releases, and remote processing elements.
        </p>
      </div>

      <div class="page-actions">
        <button class="btn btn-secondary" type="button" @click="loadProduct" :disabled="isLoading">
          Refresh
        </button>
      </div>
    </div>

    <div v-if="errorMessage" class="card feedback feedback-error">
      {{ errorMessage }}
    </div>

    <div v-else-if="isLoading" class="card feedback">
      Loading product…
    </div>

    <template v-else-if="product">
      <div class="grid stats-grid">
        <article class="card stat-card">
          <span class="stat-label">Product code</span>
          <strong class="stat-value stat-value-code">{{ product.product_code }}</strong>
        </article>
        <article class="card stat-card">
          <span class="stat-label">Classification</span>
          <strong class="stat-value">
            <span class="badge" :class="classificationClass(product.current_classification)">
              {{ formatClassification(product.current_classification) }}
            </span>
          </strong>
        </article>
        <article class="card stat-card">
          <span class="stat-label">Scope</span>
          <strong class="stat-value">
            <span class="badge" :class="scopeClass(product.scope_status)">
              {{ formatScopeStatus(product.scope_status) }}
            </span>
          </strong>
        </article>
      </div>

      <div class="detail-grid">
        <div class="card">
          <h2 class="section-title">Product information</h2>
          <div class="detail-list">
            <div>
              <span class="detail-label">Manufacturer</span>
              <p>{{ product.manufacturer_name }}</p>
            </div>
            <div>
              <span class="detail-label">Type</span>
              <p>{{ product.product_type }}</p>
            </div>
            <div>
              <span class="detail-label">Description</span>
              <p>{{ product.description || "No description provided" }}</p>
            </div>
            <div>
              <span class="detail-label">Intended use</span>
              <p>{{ product.intended_use }}</p>
            </div>
            <div>
              <span class="detail-label">Parent product</span>
              <p>{{ product.parent_product_id || "None" }}</p>
            </div>
            <div>
              <span class="detail-label">Updated</span>
              <p>{{ formatDateTime(product.updated_at) }}</p>
            </div>
          </div>
        </div>

        <div class="card">
          <div class="section-header">
            <div>
              <h2 class="section-title">CRA scope wizard</h2>
              <p class="muted">Run the backend rule engine and store the evaluation result.</p>
            </div>
          </div>

          <form class="wizard-grid" @submit.prevent="runScopeEvaluation">
            <label class="check-field">
              <input v-model="scopeForm.is_digital_product" type="checkbox" />
              <span>Digital product</span>
            </label>
            <label class="check-field">
              <input v-model="scopeForm.has_network_connectivity" type="checkbox" />
              <span>Has network connectivity</span>
            </label>
            <label class="check-field">
              <input v-model="scopeForm.performs_remote_data_processing" type="checkbox" />
              <span>Performs remote data processing</span>
            </label>
            <label class="check-field">
              <input v-model="scopeForm.safety_component" type="checkbox" />
              <span>Safety component</span>
            </label>
            <label class="check-field">
              <input v-model="scopeForm.used_in_critical_sector" type="checkbox" />
              <span>Used in critical sector</span>
            </label>
            <label class="check-field">
              <input v-model="scopeForm.handles_sensitive_functions" type="checkbox" />
              <span>Handles sensitive functions</span>
            </label>
            <label class="check-field">
              <input v-model="scopeForm.excluded_category" type="checkbox" />
              <span>Excluded category</span>
            </label>

            <label class="field field-span-2">
              <span class="field-label">Notes</span>
              <textarea v-model.trim="scopeForm.notes" rows="3" />
            </label>

            <div class="field-span-2 form-actions">
              <p v-if="scopeError" class="form-error">{{ scopeError }}</p>
              <button class="btn btn-primary" type="submit" :disabled="isEvaluatingScope">
                {{ isEvaluatingScope ? "Evaluating..." : "Run scope evaluation" }}
              </button>
            </div>
          </form>

          <div v-if="scopeResult" class="result-panel">
            <div class="result-row">
              <span class="detail-label">In scope</span>
              <span class="badge" :class="scopeResult.in_scope ? 'badge-success' : 'badge-danger'">
                {{ scopeResult.in_scope ? "Yes" : "No" }}
              </span>
            </div>
            <div class="result-row">
              <span class="detail-label">Recommended classification</span>
              <span class="badge" :class="classificationClass(scopeResult.recommended_classification)">
                {{ formatClassification(scopeResult.recommended_classification) }}
              </span>
            </div>
            <div class="result-row">
              <span class="detail-label">Suggested conformity route</span>
              <span class="badge badge-neutral">
                {{ formatConformityRoute(scopeResult.suggested_conformity_route) }}
              </span>
            </div>
            <div>
              <span class="detail-label">Rationale</span>
              <p class="result-rationale">{{ scopeResult.rationale }}</p>
            </div>
          </div>
        </div>
      </div>

      <div class="detail-grid">
        <div class="card">
          <div class="section-header">
            <div>
              <h2 class="section-title">Releases</h2>
              <p class="muted">{{ product.releases.length }} release(s)</p>
            </div>
          </div>

          <div v-if="product.releases.length === 0" class="empty-panel">
            No releases yet.
          </div>
          <div v-else class="table-wrapper">
            <table class="data-table">
              <thead>
                <tr>
                  <th>Version</th>
                  <th>Status</th>
                  <th>Classification</th>
                  <th>Conformity route</th>
                  <th>Planned</th>
                  <th>Actual</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="release in product.releases" :key="release.id">
                  <td><strong>{{ release.version }}</strong></td>
                  <td>
                    <span class="badge badge-neutral">{{ formatReleaseStatus(release.release_status) }}</span>
                  </td>
                  <td>
                    <span class="badge" :class="classificationClass(release.classification_snapshot)">
                      {{ formatClassification(release.classification_snapshot) }}
                    </span>
                  </td>
                  <td>{{ formatConformityRoute(release.conformity_route_snapshot) }}</td>
                  <td>{{ formatDate(release.planned_release_date) }}</td>
                  <td>{{ formatDate(release.actual_release_date) }}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        <div class="card">
          <div class="section-header">
            <div>
              <h2 class="section-title">Remote processing elements</h2>
              <p class="muted">{{ product.remote_processing_elements.length }} element(s)</p>
            </div>
          </div>

          <div v-if="product.remote_processing_elements.length === 0" class="empty-panel">
            No remote processing elements yet.
          </div>
          <div v-else class="table-wrapper">
            <table class="data-table">
              <thead>
                <tr>
                  <th>Name</th>
                  <th>Provider</th>
                  <th>Location</th>
                  <th>Criticality</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="element in product.remote_processing_elements" :key="element.id">
                  <td><strong>{{ element.name }}</strong></td>
                  <td>{{ element.provider_name || "—" }}</td>
                  <td>{{ element.geographic_location || "—" }}</td>
                  <td>{{ element.criticality || "—" }}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>

      <div class="card">
        <div class="section-header">
          <div>
            <h2 class="section-title">Child products</h2>
            <p class="muted">{{ product.child_products.length }} child product(s)</p>
          </div>
        </div>

        <div v-if="product.child_products.length === 0" class="empty-panel">
          No child products linked.
        </div>
        <div v-else class="table-wrapper">
          <table class="data-table">
            <thead>
              <tr>
                <th>Name</th>
                <th>Code</th>
                <th>Classification</th>
                <th>Scope</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="child in product.child_products" :key="child.id">
                <td>{{ child.name }}</td>
                <td><code>{{ child.product_code }}</code></td>
                <td>
                  <span class="badge" :class="classificationClass(child.current_classification)">
                    {{ formatClassification(child.current_classification) }}
                  </span>
                </td>
                <td>
                  <span class="badge" :class="scopeClass(child.scope_status)">
                    {{ formatScopeStatus(child.scope_status) }}
                  </span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </template>
  </section>
</template>

<script setup lang="ts">
import { reactive, ref, watch } from "vue";

import { productService } from "@/services/product-service";
import type {
  ConformityRoute,
  ProductClassification,
  ProductDetailRead,
  ProductScopeEvaluationRead,
  ProductScopeEvaluationRequest,
} from "@/types/product";

const props = defineProps<{
  productId: string;
}>();

const product = ref<ProductDetailRead | null>(null);
const isLoading = ref(false);
const isEvaluatingScope = ref(false);
const errorMessage = ref("");
const scopeError = ref("");
const scopeResult = ref<ProductScopeEvaluationRead | null>(null);

const scopeForm = reactive<ProductScopeEvaluationRequest>({
  is_digital_product: false,
  has_network_connectivity: false,
  performs_remote_data_processing: false,
  safety_component: false,
  used_in_critical_sector: false,
  handles_sensitive_functions: false,
  excluded_category: false,
  notes: "",
});

function formatClassification(value: ProductClassification): string {
  switch (value) {
    case "important_class_1":
      return "Important Class I";
    case "important_class_2":
      return "Important Class II";
    case "critical":
      return "Critical";
    default:
      return "Normal";
  }
}

function formatConformityRoute(value: ConformityRoute): string {
  switch (value) {
    case "self_assessment":
      return "Self assessment";
    case "third_party_assessment":
      return "Third-party assessment";
    case "not_applicable":
      return "Not applicable";
    default:
      return "Undecided";
  }
}

function formatReleaseStatus(value: string): string {
  return value.replaceAll("_", " ");
}

function formatScopeStatus(value: string): string {
  switch (value) {
    case "in_scope":
      return "In scope";
    case "out_of_scope":
      return "Out of scope";
    default:
      return "Undecided";
  }
}

function classificationClass(value: ProductClassification): string {
  switch (value) {
    case "critical":
      return "badge-danger";
    case "important_class_1":
    case "important_class_2":
      return "badge-warning";
    default:
      return "badge-neutral";
  }
}

function scopeClass(value: string): string {
  switch (value) {
    case "in_scope":
      return "badge-success";
    case "out_of_scope":
      return "badge-danger";
    default:
      return "badge-neutral";
  }
}

function formatDate(value: string | null): string {
  if (!value) return "—";
  return new Intl.DateTimeFormat(undefined, {
    year: "numeric",
    month: "short",
    day: "2-digit",
  }).format(new Date(value));
}

function formatDateTime(value: string): string {
  return new Intl.DateTimeFormat(undefined, {
    year: "numeric",
    month: "short",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  }).format(new Date(value));
}

async function loadProduct(): Promise<void> {
  isLoading.value = true;
  errorMessage.value = "";

  try {
    product.value = await productService.get(props.productId);
  } catch (error) {
    errorMessage.value =
      error instanceof Error ? error.message : "Failed to load product.";
  } finally {
    isLoading.value = false;
  }
}

async function runScopeEvaluation(): Promise<void> {
  scopeError.value = "";
  isEvaluatingScope.value = true;

  try {
    scopeResult.value = await productService.evaluateScope(props.productId, {
      ...scopeForm,
      notes: scopeForm.notes?.trim() || null,
    });
    await loadProduct();
  } catch (error) {
    scopeError.value =
      error instanceof Error ? error.message : "Failed to run scope evaluation.";
  } finally {
    isEvaluatingScope.value = false;
  }
}

watch(
  () => props.productId,
  () => {
    scopeResult.value = null;
    void loadProduct();
  },
  { immediate: true },
);
</script>

<style scoped>
.page {
  display: grid;
  gap: 1rem;
}

.page-header,
.section-header,
.form-actions {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  flex-wrap: wrap;
}

.page-actions {
  display: flex;
  gap: 0.75rem;
}

.page-title,
.section-title {
  margin: 0;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 1rem;
}

.detail-grid {
  display: grid;
  grid-template-columns: 1.1fr 1fr;
  gap: 1rem;
}

.stat-card,
.card {
  display: grid;
  gap: 0.75rem;
}

.stat-label,
.detail-label,
.field-label {
  color: var(--color-text-muted, #94a3b8);
  font-size: 0.85rem;
}

.stat-value {
  font-size: 1.35rem;
  font-weight: 700;
}

.stat-value-code {
  word-break: break-word;
}

.detail-list {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 1rem;
}

.detail-list p,
.result-rationale {
  margin: 0.35rem 0 0;
  line-height: 1.5;
}

.wizard-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 0.9rem;
}

.check-field {
  display: flex;
  gap: 0.65rem;
  align-items: center;
  padding: 0.8rem 0.9rem;
  border-radius: 0.85rem;
  border: 1px solid var(--color-border, rgba(148, 163, 184, 0.2));
  background: var(--color-surface-soft, rgba(15, 23, 42, 0.45));
}

.field-span-2 {
  grid-column: span 2;
}

input,
textarea {
  width: 100%;
}

textarea {
  padding: 0.75rem 0.9rem;
  border-radius: 0.85rem;
  border: 1px solid var(--color-border, rgba(148, 163, 184, 0.25));
  background: var(--color-surface-soft, rgba(15, 23, 42, 0.5));
  color: inherit;
  resize: vertical;
}

.btn {
  border: 1px solid transparent;
  border-radius: 0.85rem;
  padding: 0.75rem 1rem;
  font: inherit;
  cursor: pointer;
}

.btn-primary {
  background: linear-gradient(135deg, #8b5cf6, #6ea8fe);
  color: white;
}

.btn-secondary {
  background: transparent;
  border-color: var(--color-border, rgba(148, 163, 184, 0.25));
  color: inherit;
}

.btn:disabled {
  opacity: 0.65;
  cursor: not-allowed;
}

.feedback,
.empty-panel {
  padding: 1rem 1.1rem;
  border-radius: 1rem;
  background: var(--color-surface-soft, rgba(15, 23, 42, 0.45));
}

.feedback-error,
.form-error {
  color: #fda4af;
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
  padding: 0.85rem 0.75rem;
  text-align: left;
  border-bottom: 1px solid var(--color-border, rgba(148, 163, 184, 0.18));
  vertical-align: top;
}

.data-table th {
  color: var(--color-text-muted, #94a3b8);
  font-size: 0.85rem;
  font-weight: 600;
}

.badge {
  display: inline-flex;
  align-items: center;
  border-radius: 999px;
  padding: 0.35rem 0.65rem;
  font-size: 0.75rem;
  font-weight: 600;
}

.badge-neutral {
  background: rgba(148, 163, 184, 0.15);
  color: #cbd5e1;
}

.badge-success {
  background: rgba(52, 211, 153, 0.15);
  color: #86efac;
}

.badge-warning {
  background: rgba(251, 191, 36, 0.15);
  color: #fde68a;
}

.badge-danger {
  background: rgba(251, 113, 133, 0.15);
  color: #fda4af;
}

.result-panel {
  display: grid;
  gap: 0.85rem;
  padding: 1rem;
  border-radius: 1rem;
  background: rgba(255, 255, 255, 0.03);
}

.result-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
}

.muted {
  color: var(--color-text-muted, #94a3b8);
}

@media (max-width: 960px) {
  .stats-grid,
  .detail-grid,
  .detail-list,
  .wizard-grid {
    grid-template-columns: 1fr;
  }

  .field-span-2 {
    grid-column: span 1;
  }
}
</style>