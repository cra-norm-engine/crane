<template>
  <section class="page">
    <header class="page-header card">
      <div>
        <h1 class="page-title">SBOM records</h1>
        <p class="muted page-subtitle">
          Manage machine-readable Software Bills of Materials per product release.
          A machine-readable SBOM listing top-level dependencies is required under
          CRA Annex I Part II §1.
        </p>
      </div>

      <div class="page-actions">
        <label class="field">
          <span class="field-label">Search products</span>
          <input v-model.trim="productQuery" type="text" placeholder="Product name or code" />
        </label>

        <label class="field">
          <span class="field-label">Product</span>
          <select v-model="selectedProductId" :disabled="isLoadingProducts">
            <option value="">{{ isLoadingProducts ? "Loading…" : "All products" }}</option>
            <option v-for="p in filteredProducts" :key="p.id" :value="p.id">
              {{ p.name }} ({{ p.product_code }})
            </option>
          </select>
        </label>

        <label class="field">
          <span class="field-label">Release</span>
          <select v-model="selectedReleaseId" :disabled="!selectedProductId || isLoadingReleases">
            <option value="">{{ !selectedProductId ? "Select a product first" : "All releases" }}</option>
            <option v-for="r in releases" :key="r.id" :value="r.id">{{ r.version }}</option>
          </select>
        </label>

        <button class="btn btn-secondary" @click="loadSbomRecords" :disabled="isLoading">
          {{ isLoading ? "Refreshing…" : "Load" }}
        </button>

        <button class="btn btn-primary" @click="showCreateModal = true">
          + New SBOM
        </button>
      </div>
    </header>

    <div v-if="errorMessage" class="card feedback feedback-error">{{ errorMessage }}</div>
    <div v-if="successMessage" class="card feedback feedback-success">{{ successMessage }}</div>

    <section class="card">
      <div class="section-header">
        <h2 class="section-title">SBOM records</h2>
        <p class="muted">{{ records.length }} record(s)</p>
      </div>

      <div v-if="isLoading" class="empty-panel">Loading SBOM records…</div>
      <div v-else-if="records.length === 0" class="empty-panel">No SBOM records found. Add one to satisfy CRA Annex I Part II §1.</div>

      <div v-else class="table-wrapper">
        <table class="data-table">
          <thead>
            <tr>
              <th>Format</th>
              <th>Spec version</th>
              <th>Components</th>
              <th>Tool</th>
              <th>Generated</th>
              <th>File</th>
              <th>Added</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="r in records"
              :key="r.id"
              class="table-row-clickable"
              @click="openDetail(r)"
              tabindex="0"
              @keydown.enter="openDetail(r)"
            >
              <td><span class="format-badge" :class="`format-${r.format}`">{{ r.format.toUpperCase() }}</span></td>
              <td>{{ r.spec_version || "—" }}</td>
              <td>
                <span v-if="r.component_count !== null" class="component-count">{{ r.component_count }}</span>
                <span v-else class="muted">—</span>
              </td>
              <td>{{ r.tool_name ? `${r.tool_name}${r.tool_version ? " " + r.tool_version : ""}` : "—" }}</td>
              <td class="nowrap">{{ formatDate(r.generated_at) }}</td>
              <td>
                <span v-if="r.file_name" class="file-name">{{ r.file_name }}</span>
                <span v-else class="muted">—</span>
              </td>
              <td class="nowrap">{{ formatDate(r.created_at) }}</td>
              <td class="row-arrow">›</td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>
  </section>

  <!-- ── Create Modal ── -->
  <AppModal v-model="showCreateModal" title="New SBOM record" size="lg" :persistent="true">
    <form id="sbom-create-form" class="form-grid" @submit.prevent="createRecord">
      <div class="field field-span-2">
        <span class="field-label">Release</span>
        <select v-model="createForm.product_release_id" required>
          <option value="">— Select a release —</option>
          <option v-for="r in releases" :key="r.id" :value="r.id">{{ r.version }}</option>
        </select>
      </div>

      <label class="field">
        <span class="field-label">Format</span>
        <select v-model="createForm.format">
          <option value="cyclonedx">CycloneDX</option>
          <option value="spdx">SPDX</option>
          <option value="swid">SWID</option>
          <option value="other">Other</option>
        </select>
      </label>

      <label class="field">
        <span class="field-label">Specification version</span>
        <input v-model.trim="createForm.spec_version" type="text" placeholder="e.g. 1.5" />
      </label>

      <label class="field">
        <span class="field-label">Tool name</span>
        <input v-model.trim="createForm.tool_name" type="text" placeholder="e.g. CycloneDX CLI" />
      </label>

      <label class="field">
        <span class="field-label">Tool version</span>
        <input v-model.trim="createForm.tool_version" type="text" placeholder="e.g. 2.4.1" />
      </label>

      <label class="field">
        <span class="field-label">File name</span>
        <input v-model.trim="createForm.file_name" type="text" placeholder="sbom.cdx.json" />
      </label>

      <label class="field">
        <span class="field-label">Generated at</span>
        <input v-model="createForm.generated_at" type="datetime-local" />
      </label>

      <label class="field field-span-2">
        <span class="field-label">Notes</span>
        <textarea v-model.trim="createForm.notes" rows="2" placeholder="Scope exclusions, known gaps…" />
      </label>

      <div class="field field-span-2">
        <span class="field-label">Component count</span>
        <input v-model.number="createForm.component_count" type="number" min="0" placeholder="Auto-derived if omitted" />
        <p class="muted" style="font-size:var(--text-xs);margin-top:0.25rem;">
          Leave blank to auto-derive from the uploaded SBOM
        </p>
      </div>
    </form>

    <template #footer>
      <button class="btn btn-secondary" :disabled="isCreating" @click="showCreateModal = false">Cancel</button>
      <button class="btn btn-primary" type="submit" form="sbom-create-form"
        :disabled="isCreating || !createForm.product_release_id">
        {{ isCreating ? "Saving…" : "Create SBOM record" }}
      </button>
    </template>
  </AppModal>

  <!-- ── Detail Modal ── -->
  <AppModal v-if="detailItem" v-model="showDetailModal" title="SBOM record" size="lg">
    <div class="detail-grid">
      <div class="detail-section">
        <h3 class="detail-section-title">Format &amp; Tool</h3>
        <div class="detail-kv">
          <span class="detail-key">Format</span>
          <span class="format-badge" :class="`format-${detailItem.format}`">{{ detailItem.format.toUpperCase() }}</span>
        </div>
        <div class="detail-kv">
          <span class="detail-key">Spec version</span>
          <span>{{ detailItem.spec_version || "—" }}</span>
        </div>
        <div class="detail-kv">
          <span class="detail-key">Tool</span>
          <span>{{ detailItem.tool_name || "—" }} {{ detailItem.tool_version || "" }}</span>
        </div>
      </div>

      <div class="detail-section">
        <h3 class="detail-section-title">Contents</h3>
        <div class="detail-kv">
          <span class="detail-key">Components</span>
          <span class="component-count">{{ detailItem.component_count ?? "—" }}</span>
        </div>
        <div class="detail-kv">
          <span class="detail-key">File</span>
          <span class="file-name">{{ detailItem.file_name || "—" }}</span>
        </div>
        <div class="detail-kv">
          <span class="detail-key">Generated</span>
          <span>{{ formatDate(detailItem.generated_at) }}</span>
        </div>
      </div>
    </div>

    <div v-if="detailItem.notes" class="detail-block">
      <h3 class="detail-section-title">Notes</h3>
      <p>{{ detailItem.notes }}</p>
    </div>

    <template #footer>
      <button class="btn btn-danger-outline" :disabled="isDeleting" @click="deleteRecord">
        {{ isDeleting ? "Deleting…" : "Delete" }}
      </button>
      <button class="btn btn-secondary" @click="showDetailModal = false">Close</button>
    </template>
  </AppModal>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref, watch } from "vue";

import AppModal from "@/components/AppModal.vue";
import { apiClient } from "@/services/api";
import { sbomRecordService } from "@/services/sbom-record-service";
import type {
  ProductReleaseSummaryRead,
  ProductSummaryRead,
  SbomFormat,
  SbomRecordCreate,
  SbomRecordRead,
} from "@/types/product";

const isLoadingProducts = ref(false);
const isLoadingReleases = ref(false);
const isLoading = ref(false);
const isCreating = ref(false);
const isDeleting = ref(false);
const errorMessage = ref("");
const successMessage = ref("");
const showCreateModal = ref(false);
const showDetailModal = ref(false);
const detailItem = ref<SbomRecordRead | null>(null);

const products = ref<ProductSummaryRead[]>([]);
const releases = ref<ProductReleaseSummaryRead[]>([]);
const records = ref<SbomRecordRead[]>([]);

const productQuery = ref("");
const selectedProductId = ref("");
const selectedReleaseId = ref("");

const createForm = reactive({
  product_release_id: "",
  format: "cyclonedx" as SbomFormat,
  spec_version: "",
  tool_name: "",
  tool_version: "",
  file_name: "",
  generated_at: "",
  notes: "",
  component_count: null as number | null,
});

const filteredProducts = computed(() => {
  const q = productQuery.value.trim().toLowerCase();
  const sorted = [...products.value].sort((a, b) => a.name.localeCompare(b.name));
  if (!q) return sorted;
  return sorted.filter((p) =>
    [p.name, p.product_code].join(" ").toLowerCase().includes(q),
  );
});

function formatDate(val: string | null | undefined): string {
  if (!val) return "—";
  return new Date(val).toLocaleDateString(undefined, { dateStyle: "medium" });
}

function toIsoOrNull(val: string): string | null {
  if (!val) return null;
  return val.includes("T") ? new Date(val).toISOString() : `${val}T00:00:00Z`;
}

async function loadProducts(): Promise<void> {
  isLoadingProducts.value = true;
  try {
    const { data } = await apiClient.get<ProductSummaryRead[]>("/products/");
    products.value = data;
  } finally {
    isLoadingProducts.value = false;
  }
}

async function loadReleases(productId: string): Promise<void> {
  isLoadingReleases.value = true;
  releases.value = [];
  try {
    const { data } = await apiClient.get<{ releases: ProductReleaseSummaryRead[] }>(
      `/products/${productId}`,
    );
    releases.value = data.releases ?? [];
  } finally {
    isLoadingReleases.value = false;
  }
}

async function loadSbomRecords(): Promise<void> {
  isLoading.value = true;
  errorMessage.value = "";
  try {
    records.value = await sbomRecordService.list(selectedReleaseId.value || undefined);
  } catch {
    errorMessage.value = "Failed to load SBOM records.";
  } finally {
    isLoading.value = false;
  }
}

watch(selectedProductId, (id) => {
  releases.value = [];
  selectedReleaseId.value = "";
  if (id) loadReleases(id);
});

watch(selectedReleaseId, (id) => {
  createForm.product_release_id = id;
});

async function createRecord(): Promise<void> {
  isCreating.value = true;
  errorMessage.value = "";
  try {
    const payload: SbomRecordCreate = {
      product_release_id: createForm.product_release_id,
      format: createForm.format,
      spec_version: createForm.spec_version || null,
      tool_name: createForm.tool_name || null,
      tool_version: createForm.tool_version || null,
      file_name: createForm.file_name || null,
      generated_at: toIsoOrNull(createForm.generated_at),
      notes: createForm.notes || null,
      component_count: createForm.component_count,
    };
    await sbomRecordService.create(payload);
    showCreateModal.value = false;
    successMessage.value = "SBOM record created.";
    Object.assign(createForm, {
      product_release_id: selectedReleaseId.value,
      format: "cyclonedx",
      spec_version: "",
      tool_name: "",
      tool_version: "",
      file_name: "",
      generated_at: "",
      notes: "",
      component_count: null,
    });
    await loadSbomRecords();
  } catch (err) {
    errorMessage.value = err instanceof Error ? err.message : "Failed to create SBOM record.";
  } finally {
    isCreating.value = false;
  }
}

function openDetail(item: SbomRecordRead): void {
  detailItem.value = item;
  showDetailModal.value = true;
}

async function deleteRecord(): Promise<void> {
  if (!detailItem.value) return;
  isDeleting.value = true;
  try {
    await sbomRecordService.remove(detailItem.value.id);
    showDetailModal.value = false;
    detailItem.value = null;
    successMessage.value = "SBOM record deleted.";
    await loadSbomRecords();
  } catch {
    errorMessage.value = "Failed to delete SBOM record.";
  } finally {
    isDeleting.value = false;
  }
}

onMounted(loadProducts);
</script>

<style scoped>
/* ── Page layout ── */
.page-actions {
  display: flex;
  align-items: flex-end;
  gap: 0.75rem;
  flex-wrap: wrap;
}

/* ── Buttons ── */
.btn {
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
  border: 1px solid transparent;
  border-radius: 0.85rem;
  padding: 0.6rem 1.1rem;
  font: inherit;
  font-size: var(--text-sm);
  font-weight: 600;
  cursor: pointer;
  transition: opacity 0.12s, transform 0.12s, box-shadow 0.12s;
  white-space: nowrap;
}

.btn:disabled { opacity: 0.55; cursor: not-allowed; }

.btn-primary {
  background: linear-gradient(135deg, rgba(175, 214, 46, 0.95), rgba(28, 107, 39, 0.95));
  color: #fff;
  box-shadow: 0 6px 16px rgba(28, 107, 39, 0.22);
}

.btn-primary:not(:disabled):hover {
  transform: translateY(-1px);
  box-shadow: 0 10px 20px rgba(28, 107, 39, 0.3);
}

.btn-secondary {
  background: transparent;
  border-color: var(--color-border);
  color: inherit;
}

.btn-secondary:not(:disabled):hover { background: var(--color-surface-elevated); }

.btn-danger-outline {
  background: transparent;
  border-color: var(--color-danger-border);
  color: var(--color-danger-text);
}

.btn-danger-outline:not(:disabled):hover { background: var(--color-danger-bg); }

/* ── Feedback banners ── */
.feedback {
  padding: 0.85rem 1.1rem;
  border-radius: 1rem;
  font-size: var(--text-sm);
  border: 1px solid transparent;
}

.feedback-error   { background: var(--color-danger-bg);  border-color: var(--color-danger-border);  color: var(--color-danger-text); }
.feedback-success { background: var(--color-success-bg); border-color: var(--color-success-border); color: var(--color-success-text); }
.feedback-warning { background: var(--color-warning-bg); border-color: var(--color-warning-border); color: var(--color-warning-text); }

/* ── Empty / loading panel ── */
.empty-panel {
  padding: 2rem 1rem;
  text-align: center;
  color: var(--color-text-muted);
  font-size: var(--text-sm);
}

/* ── Form ── */
.form-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 1rem;
}

.field { display: grid; gap: 0.4rem; }
.field-label { font-size: var(--text-sm); font-weight: 600; color: var(--color-text-muted); }
.field-span-2 { grid-column: span 2; }

input, select, textarea {
  width: 100%;
  padding: 0.65rem 0.9rem;
  border-radius: 0.75rem;
  border: 1px solid var(--color-border);
  background: var(--color-surface-soft);
  color: inherit;
  font: inherit;
}

input:focus, select:focus, textarea:focus {
  outline: none;
  border-color: rgba(175, 214, 46, 0.45);
  box-shadow: 0 0 0 3px rgba(112, 185, 23, 0.12);
}

/* ── Table ── */
.table-wrapper { overflow-x: auto; }

.data-table {
  width: 100%;
  border-collapse: collapse;
}

.data-table th, .data-table td {
  padding: 0.8rem 0.75rem;
  text-align: left;
  border-bottom: 1px solid var(--color-divider);
  vertical-align: middle;
}

.data-table th {
  color: var(--color-text-muted);
  font-size: var(--text-xs);
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  white-space: nowrap;
}

.data-table tbody tr:last-child td { border-bottom: none; }
.table-row-clickable { cursor: pointer; transition: background 0.12s; }
.table-row-clickable:hover { background: var(--color-surface-elevated); }
.table-row-clickable:focus-visible { outline: 2px solid var(--color-primary); outline-offset: -2px; }

/* ── Format badges — design-system tokens only ── */
.format-badge {
  display: inline-block;
  padding: 0.15rem 0.55rem;
  border-radius: 999px;
  font-size: var(--text-xs);
  font-weight: 700;
  letter-spacing: 0.04em;
}

.format-cyclonedx { background: var(--color-info-bg);     color: var(--color-info-text);     border: 1px solid var(--color-info-border); }
.format-spdx      { background: var(--color-purple-bg);   color: var(--color-purple-text);   border: 1px solid rgba(139, 92, 246, 0.3); }
.format-swid      { background: var(--color-warning-bg);  color: var(--color-warning-text);  border: 1px solid var(--color-warning-border); }
.format-other     { background: var(--color-slate-bg);    color: var(--color-slate-text);    border: 1px solid var(--color-slate-border); }

.component-count { font-weight: 700; font-size: var(--text-sm); }
.file-name { font-family: monospace; font-size: var(--text-xs); }

/* ── Detail panels ── */
.detail-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 1.25rem; margin-bottom: 1rem; }
.detail-section { display: flex; flex-direction: column; gap: 0.5rem; }
.detail-section-title { font-size: var(--text-sm); font-weight: 700; color: var(--color-text-muted); margin-bottom: 0.25rem; }
.detail-kv { display: flex; gap: 0.5rem; align-items: flex-start; }
.detail-key { font-size: var(--text-sm); color: var(--color-text-muted); min-width: 90px; flex-shrink: 0; }
.detail-block { margin-top: 1rem; padding-top: 1rem; border-top: 1px solid var(--color-border); }

.nowrap { white-space: nowrap; }
.row-arrow { color: var(--color-text-muted); font-size: 1.1rem; text-align: right; opacity: 0; transition: opacity 0.12s; }
.table-row-clickable:hover .row-arrow,
.table-row-clickable:focus-visible .row-arrow { opacity: 1; }
</style>
