<template>
  <section class="pi-page">

    <!-- ── Page head ── -->
    <div class="pi-head">
      <div>
        <h1 class="page-title">Product inventory</h1>
        <p class="pi-sub">Catalogue every product, decide CRA scope, track conformity readiness.</p>
      </div>
      <div class="pi-head-actions">
        <AppButton :disabled="isLoading" @click="loadProducts">
          <svg class="pi-ico" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round">
            <path d="M21 12a9 9 0 1 1-3-6.7L21 8"/><path d="M21 3v5h-5"/>
          </svg>
          {{ isLoading ? 'Refreshing…' : 'Refresh' }}
        </AppButton>
        <AppButton variant="primary" @click="toggleCreateForm">
          <svg class="pi-ico" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round">
            <path d="M12 5v14M5 12h14"/>
          </svg>
          {{ showCreateForm ? 'Close' : 'Add product' }}
        </AppButton>
      </div>
    </div>

    <!-- ── KPI strip ── -->
    <div class="pi-kpi-row">
      <!-- Total products -->
      <div class="pi-kpi">
        <div class="pi-kpi-head">
          <span>Total products</span>
          <span class="pi-kpi-ic">
            <svg class="pi-ico-sm" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round">
              <path d="M20 7l-8-4-8 4v6c0 5 3.5 7.5 8 9 4.5-1.5 8-4 8-9V7z"/>
            </svg>
          </span>
        </div>
        <div class="pi-kpi-val">{{ products.length }}</div>
        <div class="pi-kpi-foot">Products in inventory</div>
      </div>

      <!-- In scope -->
      <div class="pi-kpi pi-kpi-ok">
        <div class="pi-kpi-head">
          <span>In scope of CRA</span>
          <span class="pi-kpi-ic">
            <svg class="pi-ico-sm" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round">
              <path d="M20 6L9 17l-5-5"/>
            </svg>
          </span>
        </div>
        <div class="pi-kpi-val">
          {{ inScopeCount }} <span class="pi-kpi-unit">/ {{ products.length }}</span>
        </div>
        <div class="pi-kpi-foot">
          <span class="pi-pill pi-pill-ok">
            <span class="pi-pd"></span>
            {{ products.length > 0 ? Math.round(inScopeCount / products.length * 100) : 0 }}% assessed
          </span>
        </div>
      </div>

      <!-- Critical class -->
      <div class="pi-kpi" :class="criticalCount > 0 ? 'pi-kpi-danger' : ''">
        <div class="pi-kpi-head">
          <span>Critical class</span>
          <span class="pi-kpi-ic">
            <svg class="pi-ico-sm" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round">
              <path d="M12 3l9 16H3L12 3z"/><path d="M12 10v4"/><circle cx="12" cy="17" r="0.5" fill="currentColor"/>
            </svg>
          </span>
        </div>
        <div class="pi-kpi-val">{{ criticalCount }}</div>
        <div class="pi-kpi-foot">
          <span v-if="criticalCount > 0" class="pi-pill pi-pill-err"><span class="pi-pd"></span>Third-party assessment req.</span>
          <span v-else class="pi-pill pi-pill-ok"><span class="pi-pd"></span>None</span>
        </div>
      </div>

      <!-- Active support -->
      <div class="pi-kpi" :class="productsWithSupportCount < products.length ? 'pi-kpi-warn' : 'pi-kpi-ok'">
        <div class="pi-kpi-head">
          <span>Active support set</span>
          <span class="pi-kpi-ic">
            <svg class="pi-ico-sm" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round">
              <circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/>
            </svg>
          </span>
        </div>
        <div class="pi-kpi-val">
          {{ productsWithSupportCount }} <span class="pi-kpi-unit">/ {{ products.length }}</span>
        </div>
        <div class="pi-kpi-foot">
          <span v-if="productsWithSupportCount < products.length" class="pi-pill pi-pill-warn"><span class="pi-pd"></span>Action needed</span>
          <span v-else class="pi-pill pi-pill-ok"><span class="pi-pd"></span>All set</span>
        </div>
      </div>
    </div>

    <!-- ── Filter toolbar ── -->
    <div class="pi-toolbar">
      <!-- Search -->
      <div class="pi-filter-search">
        <svg class="pi-ico-sm" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round">
          <circle cx="11" cy="11" r="7"/><path d="m20 20-3.5-3.5"/>
        </svg>
        <input v-model.trim="filters.search" placeholder="Search by product code, name, manufacturer…" />
      </div>

      <!-- Scope filter pill -->
      <div class="pi-fpill-wrap" :class="{ 'pi-fpill-active': filters.scopeStatus }">
        <span class="pi-fpill-lbl">Scope<span v-if="filters.scopeStatus">: <strong>{{ formatScopeStatus(filters.scopeStatus) }}</strong></span></span>
        <svg class="pi-fpill-chev" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round">
          <path d="M6 9l6 6 6-6"/>
        </svg>
        <select v-model="filters.scopeStatus" class="pi-fpill-select" aria-label="Filter by scope">
          <option value="">All</option>
          <option value="in_scope">In scope</option>
          <option value="out_of_scope">Out of scope</option>
          <option value="undecided">Undecided</option>
        </select>
      </div>

      <!-- Classification filter pill -->
      <div class="pi-fpill-wrap" :class="{ 'pi-fpill-active': filters.classification }">
        <span class="pi-fpill-lbl">Classification<span v-if="filters.classification">: <strong>{{ formatClassification(filters.classification) }}</strong></span></span>
        <svg class="pi-fpill-chev" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round">
          <path d="M6 9l6 6 6-6"/>
        </svg>
        <select v-model="filters.classification" class="pi-fpill-select" aria-label="Filter by classification">
          <option value="">All</option>
          <option value="normal">Default</option>
          <option value="important_class_1">Important Class I</option>
          <option value="important_class_2">Important Class II</option>
          <option value="critical">Critical</option>
        </select>
      </div>

      <!-- Support filter pill -->
      <div class="pi-fpill-wrap" :class="{ 'pi-fpill-active': filters.supportStatus }">
        <span class="pi-fpill-lbl">Support<span v-if="filters.supportStatus">: <strong>{{ formatSupportStatus(filters.supportStatus as 'not_set' | 'active' | 'approaching_eos' | 'expired') }}</strong></span></span>
        <svg class="pi-fpill-chev" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round">
          <path d="M6 9l6 6 6-6"/>
        </svg>
        <select v-model="filters.supportStatus" class="pi-fpill-select" aria-label="Filter by support status">
          <option value="">All</option>
          <option value="set">Support set</option>
          <option value="missing">Not set</option>
          <option value="active">Active</option>
          <option value="approaching_eos">Approaching EOS</option>
          <option value="expired">Expired</option>
        </select>
      </div>

      <!-- Updated filter pill -->
      <div class="pi-fpill-wrap" :class="{ 'pi-fpill-active': filters.updatedWithin }">
        <span class="pi-fpill-lbl">Updated<span v-if="filters.updatedWithin">: <strong>Last {{ filters.updatedWithin }}d</strong></span></span>
        <svg class="pi-fpill-chev" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round">
          <path d="M6 9l6 6 6-6"/>
        </svg>
        <select v-model="filters.updatedWithin" class="pi-fpill-select" aria-label="Filter by updated date">
          <option value="">Any time</option>
          <option value="7">Last 7 days</option>
          <option value="30">Last 30 days</option>
          <option value="90">Last 90 days</option>
        </select>
      </div>

      <div class="pi-toolbar-div"></div>

      <!-- Reset -->
      <button
        v-if="filters.search || filters.scopeStatus || filters.classification || filters.supportStatus || filters.updatedWithin"
        class="pi-reset-btn"
        type="button"
        @click="resetFilters"
      >Reset</button>

      <!-- Sort -->
      <div class="pi-sort-group">
        <span class="pi-sort-lbl">Sort</span>
        <div class="pi-fpill-wrap">
          <span class="pi-fpill-lbl"><strong>{{ sortLabel }}</strong></span>
          <svg class="pi-fpill-chev" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round">
            <path d="M6 9l6 6 6-6"/>
          </svg>
          <select v-model="filters.sortBy" class="pi-fpill-select" aria-label="Sort by">
            <option value="updated_desc">Latest updated</option>
            <option value="updated_asc">Oldest updated</option>
            <option value="name_asc">Name A–Z</option>
            <option value="name_desc">Name Z–A</option>
            <option value="code_asc">Code A–Z</option>
            <option value="code_desc">Code Z–A</option>
            <option value="support_end_asc">Support end ↑</option>
            <option value="support_end_desc">Support end ↓</option>
          </select>
        </div>
      </div>
    </div>

    <!-- ── Create form panel ── -->
    <div v-if="showCreateForm" class="pi-panel pi-form-panel">
      <div class="pi-form-head">
        <div>
          <h3 class="pi-form-title">Create product</h3>
          <p class="pi-muted pi-form-sub">Add a new product to the CRA inventory.</p>
        </div>
      </div>

      <form class="pi-form-grid" @submit.prevent="createProduct">
        <label class="pi-field">
          <span class="pi-field-lbl">Product code</span>
          <input v-model.trim="form.product_code" class="pi-input" required maxlength="100" />
        </label>

        <label class="pi-field">
          <span class="pi-field-lbl">Name</span>
          <input v-model.trim="form.name" class="pi-input" required maxlength="255" />
        </label>

        <label class="pi-field pi-field-span2">
          <span class="pi-field-lbl">Description</span>
          <textarea v-model.trim="form.description" class="pi-textarea" rows="3" />
        </label>

        <label class="pi-field">
          <span class="pi-field-lbl">Manufacturer name</span>
          <input v-model.trim="form.manufacturer_name" class="pi-input" required maxlength="255" />
        </label>

        <label class="pi-field">
          <span class="pi-field-lbl">Product type</span>
          <input v-model.trim="form.product_type" class="pi-input" required maxlength="150" />
        </label>

        <label class="pi-field pi-field-span2">
          <span class="pi-field-lbl">Intended use</span>
          <textarea v-model.trim="form.intended_use" class="pi-textarea" rows="3" required />
        </label>

        <!-- Parent product picker -->
        <div class="pi-field pi-field-span2">
          <span class="pi-field-lbl">
            Parent product
            <span class="pi-field-hint">(optional — set if this is a variant or sub-product)</span>
          </span>
          <div class="pi-parent-picker">
            <button type="button" class="pi-input pi-parent-trigger" @click="showParentPicker = true">
              <span v-if="form.parent_product_id && selectedParentProduct">
                {{ selectedParentProduct.product_code }} — {{ selectedParentProduct.name }}
              </span>
              <span v-else class="pi-muted">None — top-level product</span>
            </button>
            <button v-if="form.parent_product_id" type="button" class="pi-parent-clear" @click="form.parent_product_id = null" title="Clear parent">✕</button>
          </div>
        </div>

        <label class="pi-field">
          <span class="pi-field-lbl">Classification</span>
          <select v-model="form.current_classification" class="pi-select">
            <option value="normal">Default</option>
            <option value="important_class_1">Important Class I</option>
            <option value="important_class_2">Important Class II</option>
            <option value="critical">Critical</option>
          </select>
        </label>

        <label class="pi-field">
          <span class="pi-field-lbl">Scope status</span>
          <select v-model="form.scope_status" class="pi-select">
            <option value="undecided">Undecided</option>
            <option value="in_scope">In scope</option>
            <option value="out_of_scope">Out of scope</option>
          </select>
        </label>

        <!-- Gap 2 — embedded product flag: enables per-release HW+SW version fields -->
        <label class="pi-field pi-field-span2 pi-field-checkbox">
          <input type="checkbox" v-model="form.is_embedded_product" />
          <span>
            <strong>Embedded product (hardware + software/firmware)</strong>
            <span class="pi-field-hint"> — enables separate hardware and software version fields on each release</span>
          </span>
        </label>

        <div class="pi-form-actions pi-field-span2">
          <p v-if="formError" class="pi-form-error">{{ formError }}</p>
          <AppButton variant="primary" type="submit" :disabled="isSubmitting">
            {{ isSubmitting ? 'Saving…' : 'Create product' }}
          </AppButton>
        </div>
      </form>
    </div>

    <!-- ── Inventory panel ── -->
    <div class="pi-panel">
      <div class="pi-panel-head">
        <h3 class="pi-panel-title">
          Inventory
          <span class="pi-count-pill">{{ filteredProducts.length }} results</span>
        </h3>
      </div>

      <!-- States -->
      <div v-if="errorMessage" class="pi-state pi-state-err">{{ errorMessage }}</div>
      <div v-else-if="isLoading" class="pi-state">Loading products…</div>
      <div v-else-if="filteredProducts.length === 0" class="pi-state">
        <strong>No products found</strong><br />
        <span class="pi-muted">Try different filters or add your first product.</span>
      </div>

      <div v-else class="pi-table-wrap">
        <table class="pi-table">
          <thead>
            <tr>
              <th>Product</th>
              <th>Code</th>
              <th>Manufacturer</th>
              <th>Type</th>
              <th>Classification</th>
              <th>Scope</th>
              <th>Placed on market</th>
              <th>Support period</th>
              <th>Updated</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="product in filteredProducts"
              :key="product.id"
              class="pi-row"
              :class="{ 'pi-row-flagged': product.current_classification === 'critical' }"
              @click="openProduct(product.id)"
            >
              <!-- Product cell: initials mark + name + sub -->
              <td>
                <div class="pi-prod-cell">
                  <div
                    class="pi-prod-mark"
                    :class="{ 'pi-prod-mark-danger': product.current_classification === 'critical' }"
                  >{{ productInitials(product.name) }}</div>
                  <div>
                    <div class="pi-prod-name">{{ product.name }}</div>
                    <div class="pi-prod-sub">
                      {{ product.product_type }}
                      <span v-if="product.is_pre_cra"> · Pre-CRA</span>
                    </div>
                  </div>
                </div>
              </td>
              <td><span class="pi-mono">{{ product.product_code }}</span></td>
              <td class="pi-cell-clip">{{ product.manufacturer_name }}</td>
              <td class="pi-cell-clip">{{ product.product_type }}</td>
              <!-- Classification -->
              <td>
                <span class="pi-pill" :class="classificationPillClass(product.current_classification)">
                  <span class="pi-pd"></span>{{ formatClassification(product.current_classification) }}
                </span>
              </td>
              <!-- Scope -->
              <td>
                <span class="pi-pill" :class="scopePillClass(product.scope_status)">
                  <span class="pi-pd"></span>{{ formatScopeStatus(product.scope_status) }}
                </span>
              </td>
              <!-- Placed on market -->
              <td :class="product.first_placed_on_market_date ? '' : 'pi-muted'">
                {{ formatDate(product.first_placed_on_market_date) }}
              </td>
              <!-- Support period -->
              <td>
                <template v-if="supportByProductId[product.id]">
                  <span class="pi-pill" :class="supportPillClass(getSupportStatus(product.id))">
                    <span class="pi-pd"></span>{{ formatSupportStatus(getSupportStatus(product.id)) }}
                  </span>
                  <div class="pi-support-meta">
                    {{ formatSupportType(supportByProductId[product.id]!.support_type) }}
                    · ends {{ formatDate(supportByProductId[product.id]!.support_end_date) }}
                  </div>
                </template>
                <template v-else>
                  <button class="pi-set-link" type="button" @click.stop="openProduct(product.id)">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round" style="width:10px;height:10px">
                      <path d="M12 5v14M5 12h14"/>
                    </svg>
                    Set period
                  </button>
                </template>
              </td>
              <!-- Updated -->
              <td class="pi-muted">{{ formatDate(product.updated_at) }}</td>
              <!-- Action -->
              <td class="pi-action-cell">
                <button class="pi-row-action" type="button" @click.stop="openProduct(product.id)" aria-label="Open product">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round" style="width:14px;height:14px">
                    <circle cx="5" cy="12" r="1"/><circle cx="12" cy="12" r="1"/><circle cx="19" cy="12" r="1"/>
                  </svg>
                </button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <div class="pi-panel-foot">
        <span>
          Showing <strong>{{ filteredProducts.length }}</strong> of <strong>{{ products.length }}</strong> products
        </span>
      </div>
    </div>

    <!-- ── Parent product picker modal ── -->
    <Teleport to="body">
      <div v-if="showParentPicker" class="pi-picker-backdrop" @click.self="showParentPicker = false">
        <div class="pi-picker-modal" role="dialog" aria-modal="true" aria-label="Select parent product">
          <div class="pi-picker-head">
            <h3 class="pi-picker-title">Select parent product</h3>
            <button type="button" class="pi-picker-close" @click="showParentPicker = false">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round" style="width:16px;height:16px">
                <path d="M6 6l12 12M6 18L18 6"/>
              </svg>
            </button>
          </div>
          <input
            v-model="parentPickerSearch"
            class="pi-input"
            type="search"
            placeholder="Search by code, name or manufacturer…"
            autofocus
          />
          <div class="pi-picker-list">
            <p v-if="filteredParentProducts.length === 0" class="pi-muted pi-picker-empty">
              No products match your search.
            </p>
            <button
              v-for="product in filteredParentProducts"
              :key="product.id"
              type="button"
              class="pi-picker-item"
              :class="{ 'pi-picker-item-sel': form.parent_product_id === product.id }"
              @click="selectParent(product.id)"
            >
              <div class="pi-picker-item-row">
                <span class="pi-picker-code">{{ product.product_code }}</span>
                <span class="pi-picker-name">{{ product.name }}</span>
              </div>
              <div class="pi-muted pi-picker-mfr">{{ product.manufacturer_name }}</div>
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

import AppButton from "@/components/AppButton.vue";
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
  is_embedded_product: false,
});

/** Returns 2-letter initials for the product name. */
function productInitials(name: string): string {
  const words = name.trim().split(/\s+/);
  if (words.length === 1) return words[0].slice(0, 2).toUpperCase();
  return (words[0][0] + words[1][0]).toUpperCase();
}

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

/** Human-readable label for the current sort value (shown in the sort pill). */
const sortLabel = computed(() => {
  const map: Record<string, string> = {
    updated_desc: "Latest updated",
    updated_asc:  "Oldest updated",
    name_asc:     "Name A–Z",
    name_desc:    "Name Z–A",
    code_asc:     "Code A–Z",
    code_desc:    "Code Z–A",
    support_end_asc:  "Support end ↑",
    support_end_desc: "Support end ↓",
  };
  return map[filters.sortBy] ?? "Latest updated";
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
  if (!support?.support_end_date) return Number.MAX_SAFE_INTEGER;
  return new Date(support.support_end_date).getTime();
}

function getSupportStatus(productId: string): "not_set" | "active" | "approaching_eos" | "expired" {
  const support = supportByProductId.value[productId];
  if (!support) return "not_set";

  const endDate = new Date(`${support.support_end_date}T00:00:00`);
  const now = new Date();
  const sixMonthsFromNow = new Date();
  sixMonthsFromNow.setMonth(sixMonthsFromNow.getMonth() + 6);

  if (endDate.getTime() < now.getTime()) return "expired";
  if (endDate.getTime() <= sixMonthsFromNow.getTime()) return "approaching_eos";
  return "active";
}

function formatSupportStatus(value: "not_set" | "active" | "approaching_eos" | "expired"): string {
  switch (value) {
    case "active":         return "Active";
    case "approaching_eos": return "Approaching EOS";
    case "expired":        return "Expired";
    default:               return "Not set";
  }
}

function supportPillClass(value: "not_set" | "active" | "approaching_eos" | "expired"): string {
  switch (value) {
    case "active":          return "pi-pill-ok";
    case "approaching_eos": return "pi-pill-warn";
    case "expired":         return "pi-pill-err";
    default:                return "pi-pill-flat";
  }
}

function formatSupportType(value: SupportType): string {
  switch (value) {
    case "limited":  return "Limited";
    case "extended": return "Extended";
    case "custom":   return "Custom";
    default:         return "Standard";
  }
}

function formatClassification(value: ProductClassification | string): string {
  switch (value) {
    case "important_class_1": return "Important Class I";
    case "important_class_2": return "Important Class II";
    case "critical":          return "Critical";
    default:                  return "Default";
  }
}

function formatScopeStatus(value: ScopeStatus | string): string {
  switch (value) {
    case "in_scope":    return "In scope";
    case "out_of_scope": return "Out of scope";
    default:            return "Undecided";
  }
}

function classificationPillClass(value: ProductClassification): string {
  switch (value) {
    case "critical":          return "pi-pill-err";
    case "important_class_1":
    case "important_class_2": return "pi-pill-warn";
    default:                  return "pi-pill-flat";
  }
}

function scopePillClass(value: ScopeStatus | string): string {
  switch (value) {
    case "in_scope":     return "pi-pill-ok";
    case "out_of_scope": return "pi-pill-err";
    default:             return "pi-pill-flat";
  }
}

function formatDate(value: string | null): string {
  if (!value) return "—";
  return new Intl.DateTimeFormat("en-GB", {
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
  form.is_embedded_product = false;
  formError.value = "";
}

function toggleCreateForm(): void {
  showCreateForm.value = !showCreateForm.value;
  if (!showCreateForm.value) resetForm();
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
/* ─── Page shell ─────────────────────────────────── */
.pi-page {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

/* ─── Page head ──────────────────────────────────── */
.pi-head {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 24px;
  flex-wrap: wrap;
}
.pi-sub {
  margin: 0;
  font-size: 13px;
  color: var(--color-text-muted);
}
.pi-head-actions {
  display: flex;
  gap: 8px;
  align-items: center;
  flex-shrink: 0;
}

/* Buttons rendered by AppButton component */

/* ─── Icons ──────────────────────────────────────── */
.pi-ico    { width: 14px; height: 14px; flex-shrink: 0; }
.pi-ico-sm { width: 13px; height: 13px; flex-shrink: 0; }

/* ─── KPI row ────────────────────────────────────── */
.pi-kpi-row {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 12px;
}
.pi-kpi {
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: 10px;
  padding: 14px 16px;
  display: flex;
  flex-direction: column;
  gap: 10px;
  box-shadow: 0 1px 2px rgba(0,0,0,0.04);
}
.pi-kpi-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  color: var(--color-text-muted);
  font-size: 12px;
  font-weight: 500;
}
.pi-kpi-ic {
  width: 24px;
  height: 24px;
  border-radius: 6px;
  background: var(--color-surface-elevated);
  display: grid;
  place-items: center;
  color: var(--color-text-muted);
}
/* Coloured icon backgrounds by KPI variant */
.pi-kpi-ok .pi-kpi-ic    { background: var(--color-success-bg);  color: var(--color-success); }
.pi-kpi-danger .pi-kpi-ic { background: var(--color-danger-bg);  color: var(--color-danger); }
.pi-kpi-warn .pi-kpi-ic  { background: var(--color-warning-bg); color: var(--color-warning); }

.pi-kpi-val {
  font-size: 26px;
  font-weight: 600;
  letter-spacing: -0.02em;
  line-height: 1;
  color: var(--color-text);
}
.pi-kpi-unit { font-size: 13px; color: var(--color-text-muted); font-weight: 500; margin-left: 4px; }
.pi-kpi-foot { display: flex; align-items: center; gap: 6px; font-size: 12px; color: var(--color-text-muted); }

/* ─── Status pills ───────────────────────────────── */
.pi-pill {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  padding: 2px 9px;
  border-radius: 999px;
  font-size: 11px;
  font-weight: 600;
  line-height: 1.6;
  white-space: nowrap;
}
.pi-pd { width: 6px; height: 6px; border-radius: 50%; }

.pi-pill-ok   { background: var(--color-success-bg); color: var(--color-success-text); }
.pi-pill-ok .pi-pd { background: var(--color-success); }
.pi-pill-warn { background: var(--color-warning-bg); color: var(--color-warning-text); }
.pi-pill-warn .pi-pd { background: var(--color-warning); }
.pi-pill-err  { background: var(--color-danger-bg); color: var(--color-danger-text); }
.pi-pill-err .pi-pd { background: var(--color-danger); }
.pi-pill-flat { background: var(--color-slate-bg); color: var(--color-slate-text); border: 1px dashed var(--color-slate-border); }
.pi-pill-flat .pi-pd { background: var(--color-slate-text); }

/* ─── Filter toolbar ─────────────────────────────── */
.pi-toolbar {
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: 14px;
  box-shadow: 0 1px 2px rgba(0,0,0,0.04);
  padding: 10px 12px;
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}
.pi-filter-search {
  flex: 1;
  min-width: 220px;
  display: flex;
  align-items: center;
  gap: 8px;
  background: var(--color-surface-elevated);
  border: 1px solid var(--color-border);
  border-radius: 6px;
  padding: 7px 11px;
  color: var(--color-text-muted);
}
.pi-filter-search input {
  border: none;
  outline: none;
  background: transparent;
  font: inherit;
  color: var(--color-text);
  flex: 1;
  min-width: 0;
  font-size: 13px;
}
.pi-filter-search input::placeholder { color: var(--color-text-muted); }

/* Filter pill wrapper */
.pi-fpill-wrap {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  height: 32px;
  padding: 0 11px;
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: 6px;
  cursor: pointer;
  position: relative;
  white-space: nowrap;
  transition: background 0.1s, border-color 0.1s;
}
.pi-fpill-wrap:hover { background: var(--color-surface-elevated); }
.pi-fpill-active {
  background: var(--color-success-bg) !important;
  border-color: var(--color-success-border) !important;
  color: var(--color-success-text);
}
.pi-fpill-lbl {
  font-size: 12.5px;
  font-weight: 500;
  pointer-events: none;
  color: var(--color-text-muted);
}
.pi-fpill-active .pi-fpill-lbl { color: var(--color-success-text); }
.pi-fpill-chev {
  width: 12px;
  height: 12px;
  color: var(--color-text-muted);
  pointer-events: none;
  flex-shrink: 0;
}
.pi-fpill-active .pi-fpill-chev { color: var(--color-success-text); }
/* Transparent select overlay — captures clicks for the pill */
.pi-fpill-select {
  position: absolute;
  inset: 0;
  opacity: 0;
  width: 100%;
  cursor: pointer;
  font: inherit;
}

.pi-toolbar-div { width: 1px; height: 22px; background: var(--color-border); margin: 0 2px; }
.pi-reset-btn {
  background: transparent;
  border: none;
  color: var(--color-text-muted);
  font: 500 12.5px/1 inherit;
  cursor: pointer;
  padding: 4px 6px;
}
.pi-reset-btn:hover { color: var(--color-text); text-decoration: underline; }

.pi-sort-group { margin-left: auto; display: flex; gap: 6px; align-items: center; }
.pi-sort-lbl { font-size: 12px; color: var(--color-text-muted); }

/* ─── Shared panel style ──────────────────────────── */
.pi-panel {
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: 14px;
  box-shadow: 0 1px 2px rgba(0,0,0,0.04);
  overflow: hidden;
}
.pi-panel-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 14px 18px;
  border-bottom: 1px solid var(--color-border);
}
.pi-panel-title {
  margin: 0;
  font-size: 14px;
  font-weight: 600;
  color: var(--color-text);
  display: flex;
  align-items: center;
  gap: 10px;
}
.pi-count-pill {
  background: var(--color-surface-elevated);
  color: var(--color-text-muted);
  font-size: 11.5px;
  font-weight: 600;
  padding: 2px 9px;
  border-radius: 999px;
  letter-spacing: 0.02em;
}
.pi-panel-foot {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 18px;
  border-top: 1px solid var(--color-border);
  color: var(--color-text-muted);
  font-size: 12.5px;
  background: var(--color-surface-elevated);
}
.pi-panel-foot strong { color: var(--color-text); }

/* ─── State messages ─────────────────────────────── */
.pi-state {
  padding: 28px 20px;
  text-align: center;
  color: var(--color-text-muted);
  font-size: 13.5px;
}
.pi-state-err { color: var(--color-danger-text); }

/* ─── Table ──────────────────────────────────────── */
.pi-table-wrap { overflow-x: auto; }
.pi-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;
}
.pi-table thead th {
  text-align: left;
  font-size: 11px;
  font-weight: 600;
  color: var(--color-text-muted);
  text-transform: uppercase;
  letter-spacing: 0.06em;
  padding: 12px 14px;
  background: var(--color-surface-elevated);
  border-bottom: 1px solid var(--color-border);
  white-space: nowrap;
  position: sticky;
  top: 0;
  z-index: 1;
}
.pi-table tbody td {
  padding: 14px;
  border-bottom: 1px solid var(--color-border);
  color: var(--color-text-muted);
  vertical-align: middle;
}
.pi-table tbody tr:last-child td { border-bottom: none; }
.pi-row { cursor: pointer; transition: background 0.12s; }
.pi-row:hover td { background: var(--color-surface-elevated); }
.pi-row-flagged td { background: var(--color-danger-bg); }
.pi-row-flagged:hover td { background: rgba(255,125,125,0.14); }

/* Product cell */
.pi-prod-cell {
  display: flex;
  align-items: center;
  gap: 12px;
}
.pi-prod-mark {
  width: 36px;
  height: 36px;
  border-radius: 9px;
  background: var(--color-surface-elevated);
  border: 1px solid var(--color-border);
  display: grid;
  place-items: center;
  font-size: 11px;
  font-weight: 700;
  color: var(--color-text-muted);
  flex-shrink: 0;
  letter-spacing: 0.03em;
}
.pi-prod-mark-danger {
  background: var(--color-danger-bg);
  color: var(--color-danger-text);
  border-color: var(--color-danger-border);
}
.pi-prod-name { font-weight: 600; color: var(--color-text); white-space: nowrap; }
.pi-prod-sub  { font-size: 11.5px; color: var(--color-text-muted); margin-top: 2px; white-space: nowrap; max-width: 180px; overflow: hidden; text-overflow: ellipsis; }

/* Misc cells */
.pi-mono { font-family: 'JetBrains Mono', 'Fira Code', monospace; font-size: 12px; color: var(--color-text); }
.pi-muted { color: var(--color-text-muted); }
.pi-cell-clip { max-width: 130px; overflow: hidden; white-space: nowrap; text-overflow: ellipsis; }
.pi-support-meta { font-size: 11px; color: var(--color-text-muted); margin-top: 4px; white-space: nowrap; }

/* "Set period" dashed button */
.pi-set-link {
  font-size: 12px;
  color: var(--color-text-muted);
  border: 1px dashed var(--color-border-strong);
  background: transparent;
  padding: 3px 9px;
  border-radius: 999px;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font: 500 12px/1 inherit;
  transition: background 0.12s, color 0.12s, border-color 0.12s;
}
.pi-set-link:hover {
  color: var(--color-success-text);
  border-color: var(--color-success);
  border-style: solid;
  background: var(--color-success-bg);
}

/* Row action button */
.pi-action-cell { text-align: right; white-space: nowrap; }
.pi-row-action {
  width: 28px;
  height: 28px;
  border-radius: 6px;
  background: transparent;
  border: none;
  color: var(--color-text-muted);
  display: inline-grid;
  place-items: center;
  cursor: pointer;
  opacity: 0;
  transition: background 0.1s, opacity 0.1s;
}
.pi-row:hover .pi-row-action { opacity: 1; }
.pi-row-action:hover { background: var(--color-surface-elevated-strong); color: var(--color-text); }

/* ─── Create form panel ──────────────────────────── */
.pi-form-panel { padding: 18px; }
.pi-form-head { margin-bottom: 16px; }
.pi-form-title { margin: 0 0 4px; font-size: 15px; font-weight: 600; color: var(--color-text); }
.pi-form-sub { margin: 0; }
.pi-form-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 14px;
}
.pi-field { display: grid; gap: 5px; }
.pi-field-span2 { grid-column: span 2; }
.pi-field-lbl { font-size: 12.5px; font-weight: 500; color: var(--color-text-muted); }
.pi-field-hint { font-size: 11.5px; font-weight: 400; margin-left: 4px; }
.pi-field-checkbox { display: flex; flex-direction: row; align-items: flex-start; gap: 8px; padding: 6px 0; cursor: pointer; }
.pi-field-checkbox input[type="checkbox"] { margin-top: 2px; flex-shrink: 0; }
.pi-input, .pi-select, .pi-textarea {
  width: 100%;
  box-sizing: border-box;
  border-radius: 6px;
  border: 1px solid var(--color-border);
  background: var(--color-surface-elevated);
  color: var(--color-text);
  padding: 8px 11px;
  font: inherit;
  font-size: 13px;
  outline: none;
  transition: border-color 0.12s;
}
.pi-input:focus, .pi-select:focus, .pi-textarea:focus { border-color: var(--color-primary); }
.pi-textarea { resize: vertical; }
.pi-parent-picker { display: flex; gap: 8px; align-items: center; }
.pi-parent-trigger { flex: 1; text-align: left; cursor: pointer; }
.pi-parent-clear {
  flex-shrink: 0;
  background: none;
  border: 1px solid var(--color-border);
  border-radius: 6px;
  color: var(--color-text-muted);
  padding: 4px 8px;
  cursor: pointer;
  font-size: 12px;
  line-height: 1;
}
.pi-parent-clear:hover { color: var(--color-danger); }
.pi-form-actions { display: flex; align-items: center; gap: 12px; justify-content: flex-end; }
.pi-form-error { font-size: 12.5px; color: var(--color-danger-text); margin: 0; }

/* ─── Parent picker modal ────────────────────────── */
.pi-picker-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
}
.pi-picker-title { margin: 0; font-size: 15px; font-weight: 600; }
.pi-picker-close {
  background: none;
  border: 1px solid var(--color-border);
  border-radius: 6px;
  color: var(--color-text-muted);
  padding: 4px;
  cursor: pointer;
  display: grid;
  place-items: center;
}
.pi-picker-close:hover { color: var(--color-text); background: var(--color-surface-elevated); }
.pi-picker-list { overflow-y: auto; display: flex; flex-direction: column; gap: 3px; margin-top: 10px; max-height: 300px; }
.pi-picker-empty { padding: 12px; font-size: 13px; margin: 0; }
.pi-picker-item {
  display: flex;
  flex-direction: column;
  gap: 2px;
  text-align: left;
  background: none;
  border: 1px solid transparent;
  border-radius: 8px;
  padding: 8px 10px;
  cursor: pointer;
  color: inherit;
  font: inherit;
  transition: background 0.1s;
}
.pi-picker-item:hover { background: var(--color-surface-elevated); }
.pi-picker-item-sel { border-color: var(--color-primary); background: var(--color-success-bg); }
.pi-picker-item-row { display: flex; align-items: baseline; gap: 8px; min-width: 0; }
.pi-picker-code {
  flex-shrink: 0;
  font-size: 11px;
  font-weight: 600;
  background: var(--color-surface-elevated);
  color: var(--color-text-muted);
  border-radius: 4px;
  padding: 1px 5px;
}
.pi-picker-name { font-size: 13px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; min-width: 0; color: var(--color-text); }
.pi-picker-mfr { font-size: 11.5px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }

@media (max-width: 1200px) {
  .pi-kpi-row { grid-template-columns: repeat(2, 1fr); }
}
@media (max-width: 800px) {
  .pi-kpi-row { grid-template-columns: 1fr; }
  .pi-form-grid { grid-template-columns: 1fr; }
  .pi-field-span2 { grid-column: span 1; }
}
</style>

<style>
/* ── Picker modal (Teleport → body, must be unscoped) ── */
.pi-picker-backdrop {
  position: fixed;
  inset: 0;
  z-index: 1000;
  background: rgba(0, 0, 0, 0.55);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 1rem;
}
.pi-picker-modal {
  width: 100%;
  max-width: 520px;
  max-height: 80vh;
  display: flex;
  flex-direction: column;
  padding: 20px;
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: 14px;
  box-shadow: 0 8px 40px rgba(0,0,0,0.35);
  overflow: hidden;
}

/* Light mode overrides */
:root[data-theme="light"] .pi-row-flagged td { background: rgba(200,95,95,0.07); }
:root[data-theme="light"] .pi-row-flagged:hover td { background: rgba(200,95,95,0.11); }
:root[data-theme="light"] .pi-row:hover td { background: rgba(28,107,39,0.04); }
:root[data-theme="light"] .pi-picker-modal { background: #fff; }
:root[data-theme="light"] .pi-picker-item:hover { background: rgba(0,0,0,0.04); }
:root[data-theme="light"] .pi-picker-item-sel { background: rgba(28,107,39,0.06); border-color: rgba(28,107,39,0.5); }
</style>
