<template>
  <section class="page">
    <div class="page-header">
      <div>
        <h1 class="page-title">Products</h1>
        <p class="muted">
          Manage CRA products, search by product code or name, and filter by scope, classification,
          support period, and latest update date.
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
      <article class="card stat-card">
        <span class="stat-label">Active support set</span>
        <strong class="stat-value">{{ productsWithSupportCount }}</strong>
      </article>
    </div>

    <div class="card filters-card">
      <div class="section-header">
        <div>
          <h2 class="section-title">Filters</h2>
          <p class="muted">Narrow the inventory by search, scope, classification, support period, and recency.</p>
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
          <span class="field-label">Support status</span>
          <select v-model="filters.supportStatus" class="select">
            <option value="">All</option>
            <option value="set">Support set</option>
            <option value="missing">Not set</option>
            <option value="active">Active</option>
            <option value="approaching_eos">Approaching EOS</option>
            <option value="expired">Expired</option>
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
            <option value="support_end_asc">Support end date</option>
            <option value="support_end_desc">Support end date (latest)</option>
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

        <!-- Parent product picker — opens a search popup to select from existing products -->
        <div class="field field-span-2">
          <span class="field-label">Parent product
            <span class="field-label-hint">(optional — set if this is a variant or sub-product of an existing product)</span>
          </span>
          <div class="parent-picker">
            <button type="button" class="parent-picker-trigger input" @click="showParentPicker = true">
              <span v-if="form.parent_product_id && selectedParentProduct">
                {{ selectedParentProduct.product_code }} — {{ selectedParentProduct.name }}
              </span>
              <span v-else class="muted">None — top-level product</span>
            </button>
            <button
              v-if="form.parent_product_id"
              type="button"
              class="parent-picker-clear"
              @click="form.parent_product_id = null"
              title="Clear parent"
            >✕</button>
          </div>
        </div>

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
              <!-- Gap 4 — CRA Art. 3(20) / Art. 69(2): market placement date and Pre-CRA flag -->
              <th>Placed on market</th>
              <th>Support period</th>
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
              <!--
                Product "preview" cell: shows name, description, and a
                Pre-CRA indicator so compliance status is visible at a glance
                without opening the detail page.
              -->
              <td class="col-product">
                <div class="product-cell">
                  <strong class="text-truncate" :title="product.name">{{ product.name }}</strong>
                  <span class="muted product-description text-truncate" :title="'description' in product ? product.description || '' : ''">
                    {{ "description" in product ? product.description || "No description provided" : "Open detail to view more" }}
                  </span>
                  <!-- Pre-CRA flag — shown inline so it's always visible in the list -->
                  <span v-if="product.is_pre_cra" class="badge badge-warning product-precra-badge">
                    Pre-CRA · Art. 69(2)
                  </span>
                </div>
              </td>
              <td class="col-code"><code class="text-truncate" :title="product.product_code">{{ product.product_code }}</code></td>
              <td class="col-manufacturer"><span class="text-truncate" :title="product.manufacturer_name">{{ product.manufacturer_name }}</span></td>
              <td class="col-type"><span class="text-truncate" :title="product.product_type">{{ product.product_type }}</span></td>
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
              <!--
                Market placement column — shows the first_placed_on_market_date
                from the product record (CRA Art. 3(20)).
                "—" is shown when the product has not yet been placed.
              -->
              <td>
                <span :class="product.first_placed_on_market_date ? '' : 'muted'">
                  {{ formatDate(product.first_placed_on_market_date) }}
                </span>
              </td>
              <td class="col-support">
                <div class="support-cell">
                  <template v-if="supportByProductId[product.id]">
                    <span class="badge" :class="supportStatusClass(getSupportStatus(product.id))">
                      {{ formatSupportStatus(getSupportStatus(product.id)) }}
                    </span>
                    <span class="support-meta text-truncate">
                      {{ formatSupportType(supportByProductId[product.id]!.support_type) }}
                      · ends {{ formatDate(supportByProductId[product.id]!.support_end_date) }}
                    </span>
                  </template>
                  <template v-else>
                    <span class="badge badge-neutral">Not set</span>
                  </template>
                </div>
              </td>
              <td>{{ formatDate(product.updated_at) }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- Parent product picker modal -->
    <Teleport to="body">
      <div v-if="showParentPicker" class="picker-backdrop" @click.self="showParentPicker = false">
        <div class="picker-modal card" role="dialog" aria-modal="true" aria-label="Select parent product">
          <div class="picker-header">
            <h3 class="picker-title">Select parent product</h3>
            <button type="button" class="picker-close" @click="showParentPicker = false">✕</button>
          </div>
          <input
            v-model="parentPickerSearch"
            class="input picker-search"
            type="search"
            placeholder="Search by code, name or manufacturer…"
            autofocus
          />
          <div class="picker-list">
            <p v-if="filteredParentProducts.length === 0" class="muted picker-empty">
              No products match your search.
            </p>
            <button
              v-for="product in filteredParentProducts"
              :key="product.id"
              type="button"
              class="picker-item"
              :class="{ 'picker-item-selected': form.parent_product_id === product.id }"
              @click="selectParent(product.id)"
            >
              <div class="picker-item-row">
                <span class="picker-item-code">{{ product.product_code }}</span>
                <span class="picker-item-name">{{ product.name }}</span>
              </div>
              <div class="picker-item-mfr muted">{{ product.manufacturer_name }}</div>
            </button>
          </div>
        </div>
      </div>
    </Teleport>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from "vue";
import { useRouter } from "vue-router";

import { productService } from "@/services/product-service";
import { supportPeriodService } from "@/services/support-period-service";
import type {
  ProductClassification,
  ProductCreate,
  ProductSummaryRead,
  ScopeStatus,
  SupportPeriodRecordRead,
  SupportType,
} from "@/types/product";

const router = useRouter();

const products = ref<ProductSummaryRead[]>([]);
const supportByProductId = ref<Record<string, SupportPeriodRecordRead | null>>({});
const isLoading = ref(false);
const isSubmitting = ref(false);
const errorMessage = ref("");
const formError = ref("");
const showCreateForm = ref(false);
const showParentPicker = ref(false);
const parentPickerSearch = ref("");

const filters = reactive({
  search: "",
  scopeStatus: "" as ScopeStatus | "",
  classification: "" as ProductClassification | "",
  supportStatus: "" as "" | "set" | "missing" | "active" | "approaching_eos" | "expired",
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

/** The product object currently selected as parent (used to display its name in the trigger button). */
const selectedParentProduct = computed(() =>
  form.parent_product_id
    ? products.value.find((p) => p.id === form.parent_product_id) ?? null
    : null,
);

/** Products shown inside the picker popup, filtered by the picker's own search input. */
const filteredParentProducts = computed(() => {
  const q = parentPickerSearch.value.trim().toLowerCase();
  if (!q) return products.value;
  return products.value.filter(
    (p) =>
      p.product_code.toLowerCase().includes(q) ||
      p.name.toLowerCase().includes(q) ||
      p.manufacturer_name.toLowerCase().includes(q),
  );
});

function selectParent(productId: string): void {
  form.parent_product_id = productId;
  showParentPicker.value = false;
  parentPickerSearch.value = "";
}

const filteredProducts = computed(() => {
  const query = filters.search.trim().toLowerCase();
  const updatedWithinDays = filters.updatedWithin ? Number(filters.updatedWithin) : null;
  const now = Date.now();

  const filtered = products.value.filter((product) => {
    const supportRecord = supportByProductId.value[product.id] ?? null;
    const supportStatus = getSupportStatus(product.id);

    const matchesSearch = !query
      ? true
      : [
          product.product_code,
          product.name,
          product.manufacturer_name,
          product.product_type,
          supportRecord?.support_type ?? "",
          supportRecord?.support_end_date ?? "",
        ]
          .join(" ")
          .toLowerCase()
          .includes(query);

    const matchesScope = !filters.scopeStatus || product.scope_status === filters.scopeStatus;
    const matchesClassification =
      !filters.classification || product.current_classification === filters.classification;

    const matchesSupportStatus =
      !filters.supportStatus ||
      (filters.supportStatus === "set" && Boolean(supportRecord)) ||
      (filters.supportStatus === "missing" && !supportRecord) ||
      (filters.supportStatus === "active" && supportStatus === "active") ||
      (filters.supportStatus === "approaching_eos" && supportStatus === "approaching_eos") ||
      (filters.supportStatus === "expired" && supportStatus === "expired");

    const matchesUpdated = !updatedWithinDays
      ? true
      : now - new Date(product.updated_at).getTime() <= updatedWithinDays * 24 * 60 * 60 * 1000;

    return matchesSearch && matchesScope && matchesClassification && matchesSupportStatus && matchesUpdated;
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
      case "support_end_asc":
        return supportEndTimestamp(a.id) - supportEndTimestamp(b.id);
      case "support_end_desc":
        return supportEndTimestamp(b.id) - supportEndTimestamp(a.id);
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

const productsWithSupportCount = computed(() =>
  products.value.filter((product) => Boolean(supportByProductId.value[product.id])).length,
);

function supportEndTimestamp(productId: string): number {
  const support = supportByProductId.value[productId];
  if (!support?.support_end_date) {
    return Number.MAX_SAFE_INTEGER;
  }
  return new Date(support.support_end_date).getTime();
}

function getSupportStatus(productId: string): "not_set" | "active" | "approaching_eos" | "expired" {
  const support = supportByProductId.value[productId];
  if (!support) {
    return "not_set";
  }

  const endDate = new Date(`${support.support_end_date}T00:00:00`);
  const now = new Date();
  const sixMonthsFromNow = new Date();
  sixMonthsFromNow.setMonth(sixMonthsFromNow.getMonth() + 6);

  if (endDate.getTime() < now.getTime()) {
    return "expired";
  }

  if (endDate.getTime() <= sixMonthsFromNow.getTime()) {
    return "approaching_eos";
  }

  return "active";
}

function formatSupportStatus(value: "not_set" | "active" | "approaching_eos" | "expired"): string {
  switch (value) {
    case "active":
      return "Active";
    case "approaching_eos":
      return "Approaching EOS";
    case "expired":
      return "Expired";
    default:
      return "Not set";
  }
}

function supportStatusClass(value: "not_set" | "active" | "approaching_eos" | "expired"): string {
  switch (value) {
    case "active":
      return "badge-success";
    case "approaching_eos":
      return "badge-warning";
    case "expired":
      return "badge-danger";
    default:
      return "badge-neutral";
  }
}

function formatSupportType(value: SupportType): string {
  switch (value) {
    case "limited":
      return "Limited";
    case "extended":
      return "Extended";
    case "custom":
      return "Custom";
    default:
      return "Standard";
  }
}

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

function formatDate(value: string | null): string {
  if (!value) return "—";
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
  filters.supportStatus = "";
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

async function loadSupportPeriods(productList: ProductSummaryRead[]): Promise<void> {
  const entries = await Promise.all(
    productList.map(async (product) => {
      try {
        const record = await supportPeriodService.getActiveForProduct(product.id);
        return [product.id, record] as const;
      } catch {
        return [product.id, null] as const;
      }
    }),
  );

  supportByProductId.value = Object.fromEntries(entries);
}

async function loadProducts(): Promise<void> {
  isLoading.value = true;
  errorMessage.value = "";

  try {
    const loadedProducts = await productService.list();
    products.value = loadedProducts;
    await loadSupportPeriods(loadedProducts);
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
  grid-template-columns: repeat(4, minmax(0, 1fr));
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
  grid-template-columns: repeat(6, minmax(0, 1fr));
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
  table-layout: fixed;  /* fixed layout lets column widths be enforced */
}

.products-table th,
.products-table td {
  padding: 0.9rem 0.75rem;
  text-align: left;
  border-bottom: 1px solid var(--color-border, rgba(148, 163, 184, 0.18));
  vertical-align: middle;
  overflow: hidden;
}

.products-table th {
  color: var(--color-text-muted, #94a3b8);
  font-size: 0.85rem;
  font-weight: 600;
  white-space: nowrap;
}

/* Column widths — total adds up to 100% */
.col-product      { width: 22%; }
.col-code         { width: 9%; }
.col-manufacturer { width: 13%; }
.col-type         { width: 12%; }
/* Classification, Scope columns get auto width */
.col-support      { width: 14%; }
/* Placed on market, Updated get natural narrow width */

/* Truncation helper — applied to inline elements inside cells */
.text-truncate {
  display: block;
  overflow: hidden;
  white-space: nowrap;
  text-overflow: ellipsis;
  max-width: 100%;
}

.table-row {
  cursor: pointer;
  transition: background-color 0.15s ease;
}

.table-row:hover {
  background: rgba(255, 255, 255, 0.03);
}

.product-cell,
.support-cell {
  display: grid;
  gap: 0.2rem;
  min-width: 0;   /* allows grid children to shrink below their content size */
}

.product-description,
.support-meta {
  font-size: 0.82rem;
}

/* Pre-CRA badge sits below the description inside the product preview cell */
.product-precra-badge {
  justify-self: start; /* left-align inside the grid cell */
  font-size: 0.72rem;
  margin-top: 0.1rem;
}

.badge {
  display: inline-flex;
  align-items: center;
  border-radius: 999px;
  padding: 0.35rem 0.65rem;
  font-size: 0.75rem;
  font-weight: 600;
  width: fit-content;
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

@media (max-width: 1400px) {
  .filters-grid {
    grid-template-columns: repeat(3, minmax(0, 1fr));
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

/* Parent product picker trigger row */
.parent-picker {
  display: flex;
  gap: 0.5rem;
  align-items: center;
}

.parent-picker-trigger {
  flex: 1;
  text-align: left;
  cursor: pointer;
  background: var(--color-surface-soft, rgba(15, 23, 42, 0.45));
  border: 1px solid var(--color-border, rgba(148, 163, 184, 0.2));
  border-radius: 0.85rem;
  padding: 0.75rem 0.9rem;
  color: inherit;
  font: inherit;
}

.parent-picker-clear {
  flex-shrink: 0;
  background: none;
  border: 1px solid var(--color-border, rgba(148, 163, 184, 0.2));
  border-radius: 0.5rem;
  color: var(--color-text-muted, #94a3b8);
  padding: 0.4rem 0.6rem;
  cursor: pointer;
  font-size: 0.85rem;
  line-height: 1;
}

.parent-picker-clear:hover {
  color: #fda4af;
}

/* Picker modal backdrop — rendered via Teleport outside the scoped component,
   so these styles must live in the unscoped block below. */
.field-label-hint {
  font-size: 0.78rem;
  color: var(--color-text-muted, #94a3b8);
  font-weight: 400;
  margin-left: 0.35rem;
}
</style>

<style>
:root[data-theme="light"] .feedback-error,
:root[data-theme="light"] .form-error    { color: #be123c; }
:root[data-theme="light"] .badge-neutral { background: rgba(71,85,105,0.1);   color: #475569; }
:root[data-theme="light"] .badge-success { background: rgba(21,128,61,0.1);   color: #15803d; }
:root[data-theme="light"] .badge-warning { background: rgba(184,155,18,0.1);  color: #78350f; }
:root[data-theme="light"] .badge-danger  { background: rgba(239,68,68,0.1);   color: #be123c; }
:root[data-theme="light"] .table-row:hover { background: rgba(28, 107, 39, 0.04); }

/* --- Parent picker modal (Teleport → body) --- */
.picker-backdrop {
  position: fixed;
  inset: 0;
  z-index: 1000;
  background: rgba(0, 0, 0, 0.55);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 1rem;
}

.picker-modal {
  width: 100%;
  max-width: 520px;
  max-height: 80vh;
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  padding: 1.25rem;
  background: var(--color-surface, #0f172a);
  border: 1px solid var(--color-border, rgba(148, 163, 184, 0.2));
  border-radius: 1rem;
}

.picker-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.picker-title {
  margin: 0;
  font-size: 1rem;
  font-weight: 600;
}

.picker-close {
  background: none;
  border: none;
  color: var(--color-text-muted, #94a3b8);
  font-size: 1rem;
  cursor: pointer;
  padding: 0.25rem;
  line-height: 1;
}

.picker-close:hover {
  color: inherit;
}

.picker-search {
  width: 100%;
  box-sizing: border-box;
  background: var(--color-surface-soft, rgba(15, 23, 42, 0.45));
  border: 1px solid var(--color-border, rgba(148, 163, 184, 0.2));
  border-radius: 0.85rem;
  color: inherit;
  padding: 0.65rem 0.9rem;
  font: inherit;
}

.picker-list {
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.picker-empty {
  padding: 0.75rem;
  font-size: 0.875rem;
}

.picker-item {
  display: flex;
  flex-direction: column;
  gap: 0.2rem;
  text-align: left;
  background: none;
  border: 1px solid transparent;
  border-radius: 0.75rem;
  padding: 0.65rem 0.8rem;
  cursor: pointer;
  color: inherit;
  font: inherit;
  transition: background 0.12s ease;
}

.picker-item:hover {
  background: rgba(255, 255, 255, 0.05);
}

.picker-item-selected {
  border-color: var(--color-accent, rgba(175, 214, 46, 0.6));
  background: rgba(175, 214, 46, 0.06);
}

/* Top row: code badge + name side by side, name truncates */
.picker-item-row {
  display: flex;
  align-items: baseline;
  gap: 0.5rem;
  min-width: 0;
}

.picker-item-code {
  flex-shrink: 0;
  font-size: 0.75rem;
  font-weight: 600;
  background: rgba(148, 163, 184, 0.12);
  color: var(--color-text-muted, #94a3b8);
  border-radius: 0.35rem;
  padding: 0.1rem 0.4rem;
}

.picker-item-name {
  font-size: 0.9rem;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  min-width: 0;
}

/* Second row: manufacturer, full width, truncates naturally */
.picker-item-mfr {
  font-size: 0.78rem;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

/* Light mode overrides for picker */
:root[data-theme="light"] .picker-modal {
  background: #ffffff;
}

:root[data-theme="light"] .picker-search {
  background: #f8fafc;
  color: #0f172a;
}

:root[data-theme="light"] .picker-item:hover {
  background: rgba(0, 0, 0, 0.04);
}

:root[data-theme="light"] .picker-item-selected {
  background: rgba(28, 107, 39, 0.06);
  border-color: rgba(28, 107, 39, 0.5);
}
</style>