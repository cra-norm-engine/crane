<template>
  <section class="page">
    <div class="page-header">
      <div>
        <h1 class="page-title">Products</h1>
        <p class="muted">
          Manage CRA products, search by product code or name, and filter by scope, classification,
          and latest update date.
        </p>
      </div>

      <div class="page-actions">
        <button class="button secondary" type="button" @click="loadProducts" :disabled="isLoading">
          {{ isLoading ? "Refreshing..." : "Refresh" }}
        </button>
        <button class="button" type="button" @click="toggleCreateForm">
          {{ showCreateForm ? "Close" : "Add product" }}
        </button>
      </div>
    </div>

    <div class="grid stats-grid">
      <article class="card stat-card">
        <span class="stat-label">Total products</span>
        <strong class="stat-value">{{ products.length }}</strong>
      </article>
      <article class="card stat-card">
        <span class="stat-label">In scope</span>
        <strong class="stat-value">{{ inScopeCount }}</strong>
      </article>
      <article class="card stat-card">
        <span class="stat-label">Critical</span>
        <strong class="stat-value">{{ criticalCount }}</strong>
      </article>
    </div>

    <div class="card filters-card">
      <div class="section-header">
        <div>
          <h2 class="section-title">Filters</h2>
          <p class="muted">Narrow the inventory by search, scope, classification, and recency.</p>
        </div>
        <button class="button secondary" type="button" @click="resetFilters">
          Reset filters
        </button>
      </div>

      <div class="filters-grid">
        <label class="field search-field">
          <span class="field-label">Search</span>
          <input
            v-model.trim="filters.search"
            class="input"
            type="search"
            placeholder="Search by product code, name, manufacturer, or type"
          />
        </label>

        <label class="field">
          <span class="field-label">Scope status</span>
          <select v-model="filters.scopeStatus" class="select">
            <option value="">All</option>
            <option value="in_scope">In scope</option>
            <option value="out_of_scope">Out of scope</option>
            <option value="undecided">Undecided</option>
          </select>
        </label>

        <label class="field">
          <span class="field-label">Classification</span>
          <select v-model="filters.classification" class="select">
            <option value="">All</option>
            <option value="normal">Normal</option>
            <option value="important_class_1">Important Class I</option>
            <option value="important_class_2">Important Class II</option>
            <option value="critical">Critical</option>
          </select>
        </label>

        <label class="field">
          <span class="field-label">Updated</span>
          <select v-model="filters.updatedWithin" class="select">
            <option value="">Any time</option>
            <option value="7">Last 7 days</option>
            <option value="30">Last 30 days</option>
            <option value="90">Last 90 days</option>
          </select>
        </label>

        <label class="field">
          <span class="field-label">Sort by</span>
          <select v-model="filters.sortBy" class="select">
            <option value="updated_desc">Latest updated</option>
            <option value="updated_asc">Oldest updated</option>
            <option value="name_asc">Name A–Z</option>
            <option value="name_desc">Name Z–A</option>
            <option value="code_asc">Code A–Z</option>
            <option value="code_desc">Code Z–A</option>
          </select>
        </label>
      </div>
    </div>

    <div v-if="showCreateForm" class="card form-card">
      <div class="section-header">
        <div>
          <h2 class="section-title">Create product</h2>
          <p class="muted">Add a product to the CRA inventory.</p>
        </div>
      </div>

      <form class="grid form-grid" @submit.prevent="createProduct">
        <label class="field">
          <span class="field-label">Product code</span>
          <input v-model.trim="form.product_code" class="input" required maxlength="100" />
        </label>

        <label class="field">
          <span class="field-label">Name</span>
          <input v-model.trim="form.name" class="input" required maxlength="255" />
        </label>

        <label class="field field-span-2">
          <span class="field-label">Description</span>
          <textarea v-model.trim="form.description" class="textarea" rows="3" />
        </label>

        <label class="field">
          <span class="field-label">Manufacturer name</span>
          <input v-model.trim="form.manufacturer_name" class="input" required maxlength="255" />
        </label>

        <label class="field">
          <span class="field-label">Product type</span>
          <input v-model.trim="form.product_type" class="input" required maxlength="150" />
        </label>

        <label class="field field-span-2">
          <span class="field-label">Intended use</span>
          <textarea v-model.trim="form.intended_use" class="textarea" rows="3" required />
        </label>

        <label class="field">
          <span class="field-label">Classification</span>
          <select v-model="form.current_classification" class="select">
            <option value="normal">Normal</option>
            <option value="important_class_1">Important Class I</option>
            <option value="important_class_2">Important Class II</option>
            <option value="critical">Critical</option>
          </select>
        </label>

        <label class="field">
          <span class="field-label">Scope status</span>
          <select v-model="form.scope_status" class="select">
            <option value="undecided">Undecided</option>
            <option value="in_scope">In scope</option>
            <option value="out_of_scope">Out of scope</option>
          </select>
        </label>

        <div class="form-actions field-span-2">
          <p v-if="formError" class="form-error">{{ formError }}</p>
          <button class="button" type="submit" :disabled="isSubmitting">
            {{ isSubmitting ? "Saving..." : "Create product" }}
          </button>
        </div>
      </form>
    </div>

    <div class="card table-card">
      <div class="section-header">
        <div>
          <h2 class="section-title">Inventory</h2>
          <p class="muted">{{ filteredProducts.length }} result(s)</p>
        </div>
      </div>

      <div v-if="errorMessage" class="feedback feedback-error">
        {{ errorMessage }}
      </div>

      <div v-else-if="isLoading" class="feedback">Loading products…</div>

      <div v-else-if="filteredProducts.length === 0" class="empty-state">
        <h3>No products found</h3>
        <p class="muted">Try different filters or create your first product.</p>
      </div>

      <div v-else class="table-wrapper">
        <table class="products-table">
          <thead>
            <tr>
              <th>Product</th>
              <th>Code</th>
              <th>Manufacturer</th>
              <th>Type</th>
              <th>Classification</th>
              <th>Scope</th>
              <th>Updated</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="product in filteredProducts"
              :key="product.id"
              class="table-row"
              @click="openProduct(product.id)"
            >
              <td>
                <div class="product-cell">
                  <strong>{{ product.name }}</strong>
                  <span class="muted product-description">
                    {{ "description" in product ? product.description || "No description provided" : "Open detail to view more" }}
                  </span>
                </div>
              </td>
              <td><code>{{ product.product_code }}</code></td>
              <td>{{ product.manufacturer_name }}</td>
              <td>{{ product.product_type }}</td>
              <td>
                <span class="badge" :class="classificationClass(product.current_classification)">
                  {{ formatClassification(product.current_classification) }}
                </span>
              </td>
              <td>
                <span class="badge" :class="scopeClass(product.scope_status)">
                  {{ formatScopeStatus(product.scope_status) }}
                </span>
              </td>
              <td>{{ formatDate(product.updated_at) }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from "vue";
import { useRouter } from "vue-router";

import { productService } from "@/services/product-service";
import type {
  ProductClassification,
  ProductCreate,
  ProductSummaryRead,
  ScopeStatus,
} from "@/types/product";

const router = useRouter();

const products = ref<ProductSummaryRead[]>([]);
const isLoading = ref(false);
const isSubmitting = ref(false);
const errorMessage = ref("");
const formError = ref("");
const showCreateForm = ref(false);

const filters = reactive({
  search: "",
  scopeStatus: "" as ScopeStatus | "",
  classification: "" as ProductClassification | "",
  updatedWithin: "",
  sortBy: "updated_desc",
});

const form = reactive<ProductCreate>({
  product_code: "",
  name: "",
  description: null,
  parent_product_id: null,
  manufacturer_name: "",
  intended_use: "",
  product_type: "",
  current_classification: "normal",
  scope_status: "undecided",
});

const filteredProducts = computed(() => {
  const query = filters.search.trim().toLowerCase();
  const updatedWithinDays = filters.updatedWithin ? Number(filters.updatedWithin) : null;
  const now = Date.now();

  const filtered = products.value.filter((product) => {
    const matchesSearch = !query
      ? true
      : [
          product.product_code,
          product.name,
          product.manufacturer_name,
          product.product_type,
          "description" in product ? (product.description ?? "") : "",
        ]
          .join(" ")
          .toLowerCase()
          .includes(query);

    const matchesScope = !filters.scopeStatus || product.scope_status === filters.scopeStatus;
    const matchesClassification =
      !filters.classification || product.current_classification === filters.classification;

    const matchesUpdated = !updatedWithinDays
      ? true
      : now - new Date(product.updated_at).getTime() <= updatedWithinDays * 24 * 60 * 60 * 1000;

    return matchesSearch && matchesScope && matchesClassification && matchesUpdated;
  });

  return [...filtered].sort((a, b) => {
    switch (filters.sortBy) {
      case "updated_asc":
        return new Date(a.updated_at).getTime() - new Date(b.updated_at).getTime();
      case "name_asc":
        return a.name.localeCompare(b.name);
      case "name_desc":
        return b.name.localeCompare(a.name);
      case "code_asc":
        return a.product_code.localeCompare(b.product_code);
      case "code_desc":
        return b.product_code.localeCompare(a.product_code);
      case "updated_desc":
      default:
        return new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime();
    }
  });
});

const inScopeCount = computed(() =>
  products.value.filter((product) => product.scope_status === "in_scope").length,
);

const criticalCount = computed(() =>
  products.value.filter((product) => product.current_classification === "critical").length,
);

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

function formatScopeStatus(value: ScopeStatus | string): string {
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

function scopeClass(value: ScopeStatus | string): string {
  switch (value) {
    case "in_scope":
      return "badge-success";
    case "out_of_scope":
      return "badge-danger";
    default:
      return "badge-neutral";
  }
}

function formatDate(value: string): string {
  return new Intl.DateTimeFormat(undefined, {
    year: "numeric",
    month: "short",
    day: "2-digit",
  }).format(new Date(value));
}

function resetFilters(): void {
  filters.search = "";
  filters.scopeStatus = "";
  filters.classification = "";
  filters.updatedWithin = "";
  filters.sortBy = "updated_desc";
}

function resetForm(): void {
  form.product_code = "";
  form.name = "";
  form.description = null;
  form.parent_product_id = null;
  form.manufacturer_name = "";
  form.intended_use = "";
  form.product_type = "";
  form.current_classification = "normal";
  form.scope_status = "undecided";
  formError.value = "";
}

function toggleCreateForm(): void {
  showCreateForm.value = !showCreateForm.value;
  if (!showCreateForm.value) {
    resetForm();
  }
}

async function loadProducts(): Promise<void> {
  isLoading.value = true;
  errorMessage.value = "";

  try {
    products.value = await productService.list();
  } catch (error) {
    errorMessage.value =
      error instanceof Error ? error.message : "Failed to load products.";
  } finally {
    isLoading.value = false;
  }
}

async function createProduct(): Promise<void> {
  isSubmitting.value = true;
  formError.value = "";

  try {
    const payload: ProductCreate = {
      ...form,
      description: form.description?.trim() || null,
    };

    await productService.create(payload);
    resetForm();
    showCreateForm.value = false;
    await loadProducts();
  } catch (error) {
    formError.value =
      error instanceof Error ? error.message : "Failed to create product.";
  } finally {
    isSubmitting.value = false;
  }
}

function openProduct(productId: string): void {
  router.push({ name: "product-detail", params: { productId } });
}

onMounted(() => {
  void loadProducts();
});
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

.grid {
  display: grid;
  gap: 1rem;
}

.stats-grid {
  grid-template-columns: repeat(3, minmax(0, 1fr));
}

.stat-card {
  display: grid;
  gap: 0.35rem;
}

.stat-label {
  color: var(--color-text-muted, #94a3b8);
  font-size: 0.875rem;
}

.stat-value {
  font-size: 1.75rem;
  font-weight: 700;
}

.filters-card,
.form-card,
.table-card {
  display: grid;
  gap: 1rem;
}

.filters-grid {
  display: grid;
  grid-template-columns: repeat(5, minmax(0, 1fr));
  gap: 1rem;
  align-items: end;
}

.search-field {
  min-width: 0;
}

.field {
  display: grid;
  gap: 0.4rem;
}

.field-label {
  font-size: 0.875rem;
  color: var(--color-text-muted, #94a3b8);
}

.form-grid {
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

.field-span-2 {
  grid-column: span 2;
}

.input,
.select,
.textarea {
  width: 100%;
  box-sizing: border-box;
  border-radius: 0.85rem;
  border: 1px solid var(--color-border, rgba(148, 163, 184, 0.2));
  background: var(--color-surface-soft, rgba(15, 23, 42, 0.45));
  color: inherit;
  padding: 0.75rem 0.9rem;
  font: inherit;
}

.textarea {
  resize: vertical;
}

.feedback,
.empty-state {
  padding: 1.25rem;
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

.products-table {
  width: 100%;
  border-collapse: collapse;
}

.products-table th,
.products-table td {
  padding: 0.9rem 0.75rem;
  text-align: left;
  border-bottom: 1px solid var(--color-border, rgba(148, 163, 184, 0.18));
  vertical-align: top;
}

.products-table th {
  color: var(--color-text-muted, #94a3b8);
  font-size: 0.85rem;
  font-weight: 600;
}

.table-row {
  cursor: pointer;
  transition: background-color 0.15s ease;
}

.table-row:hover {
  background: rgba(255, 255, 255, 0.03);
}

.product-cell {
  display: grid;
  gap: 0.25rem;
}

.product-description {
  font-size: 0.85rem;
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

.muted {
  color: var(--color-text-muted, #94a3b8);
}

@media (max-width: 1200px) {
  .filters-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 900px) {
  .stats-grid,
  .form-grid,
  .filters-grid {
    grid-template-columns: 1fr;
  }

  .field-span-2 {
    grid-column: span 1;
  }
}
</style>
