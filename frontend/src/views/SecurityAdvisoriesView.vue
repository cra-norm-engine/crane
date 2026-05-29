<template>
  <section class="page">
    <header class="page-header card">
      <div>
        <h1 class="page-title">Security advisories</h1>
        <p class="muted page-subtitle">
          Publish structured advisories for fixed vulnerabilities — with embargo management
          and remediation guidance (CRA Annex I Part II §4, §7, §8).
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
            <option v-for="r in releases" :key="r.id" :value="r.id">{{ r.display_version }}</option>
          </select>
        </label>

        <button class="btn btn-secondary" type="button" @click="loadAdvisories" :disabled="isLoading">
          {{ isLoading ? "Refreshing…" : "Load" }}
        </button>

        <button class="btn btn-primary" type="button" @click="showCreateModal = true">
          + New advisory
        </button>
      </div>
    </header>

    <div v-if="errorMessage" class="card feedback feedback-error">{{ errorMessage }}</div>
    <div v-if="successMessage" class="card feedback feedback-success">{{ successMessage }}</div>

    <!-- Embargo warning -->
    <div v-if="embargoCount > 0" class="card feedback feedback-warning">
      {{ embargoCount }} advisory(ies) currently under embargo — review disclosure dates.
    </div>

    <section class="card">
      <div class="section-header">
        <h2 class="section-title">Advisories</h2>
        <p class="muted">{{ advisories.length }} advisory(ies)</p>
      </div>

      <div v-if="isLoading" class="empty-panel">Loading security advisories…</div>
      <div v-else-if="advisories.length === 0" class="empty-panel">No advisories found.</div>

      <div v-else class="table-wrapper">
        <table class="data-table">
          <thead>
            <tr>
              <th>Advisory ID</th>
              <th>Title</th>
              <th>Status</th>
              <th>Severity</th>
              <th>CVEs</th>
              <th>Embargo until</th>
              <th>Published</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="a in advisories"
              :key="a.id"
              class="table-row-clickable"
              @click="openDetail(a)"
              tabindex="0"
              @keydown.enter="openDetail(a)"
            >
              <td><code class="advisory-id">{{ a.advisory_id }}</code></td>
              <td><strong>{{ a.title }}</strong></td>
              <td>
                <span class="advisory-status-badge" :class="`advisory-status-${a.status}`">
                  {{ a.status }}
                </span>
              </td>
              <td>
                <span v-if="a.severity" class="severity-badge" :class="`severity-${a.severity}`">{{ a.severity }}</span>
                <span v-else class="muted">—</span>
              </td>
              <td>
                <template v-if="a.cve_ids_json.length">
                  <span class="cve-pill" v-for="c in a.cve_ids_json.slice(0, 2)" :key="c">{{ c }}</span>
                  <span v-if="a.cve_ids_json.length > 2" class="muted">+{{ a.cve_ids_json.length - 2 }}</span>
                </template>
                <span v-else class="muted">—</span>
              </td>
              <td class="nowrap">{{ formatDate(a.embargo_until) }}</td>
              <td class="nowrap">{{ formatDate(a.published_at) }}</td>
              <td class="row-arrow">›</td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>
  </section>

  <!-- ── Create Modal ── -->
  <AppModal v-model="showCreateModal" title="New security advisory" size="lg" :persistent="true">
    <form id="advisory-create-form" class="form-grid" @submit.prevent="createAdvisory">
      <label class="field">
        <span class="field-label">Advisory ID</span>
        <input v-model.trim="createForm.advisory_id" type="text" required placeholder="e.g. CRANE-2026-001" />
      </label>

      <label class="field">
        <span class="field-label">Status</span>
        <select v-model="createForm.status">
          <option value="draft">Draft</option>
          <option value="embargo">Embargo</option>
          <option value="published">Published</option>
          <option value="archived">Archived</option>
        </select>
      </label>

      <label class="field field-span-2">
        <span class="field-label">Title</span>
        <input v-model.trim="createForm.title" type="text" required />
      </label>

      <label class="field field-span-2">
        <span class="field-label">Summary</span>
        <textarea v-model.trim="createForm.summary" rows="2" />
      </label>

      <label class="field">
        <span class="field-label">Severity</span>
        <select v-model="createForm.severity">
          <option value="">— Not specified —</option>
          <option value="critical">Critical</option>
          <option value="high">High</option>
          <option value="medium">Medium</option>
          <option value="low">Low</option>
          <option value="informational">Informational</option>
        </select>
      </label>

      <label class="field">
        <span class="field-label">CVE IDs (comma-separated)</span>
        <input v-model.trim="cveInput" type="text" placeholder="CVE-2026-0001" />
      </label>

      <label class="field">
        <span class="field-label">Embargo until</span>
        <input v-model="createForm.embargo_until" type="date" />
        <p class="muted" style="font-size:var(--text-xs);margin-top:0.25rem;">Leave blank for no embargo</p>
      </label>

      <label class="field">
        <span class="field-label">Published at</span>
        <input v-model="createForm.published_at" type="datetime-local" />
      </label>

      <label class="field field-span-2">
        <span class="field-label">Workaround</span>
        <textarea v-model.trim="createForm.workaround" rows="2" placeholder="Interim mitigation steps" />
      </label>

      <label class="field field-span-2">
        <span class="field-label">Remediation steps</span>
        <textarea v-model.trim="createForm.remediation_steps" rows="3" placeholder="Step-by-step fix instructions" />
      </label>

      <div class="field field-span-2">
        <span class="field-label">Release</span>
        <select v-model="createForm.product_release_id" required>
          <option value="">— Select a release —</option>
          <option v-for="r in releases" :key="r.id" :value="r.id">{{ r.display_version }}</option>
        </select>
      </div>
    </form>

    <template #footer>
      <button class="btn btn-secondary" :disabled="isCreating" @click="showCreateModal = false">Cancel</button>
      <button class="btn btn-primary" type="submit" form="advisory-create-form"
        :disabled="isCreating || !createForm.product_release_id">
        {{ isCreating ? "Saving…" : "Create advisory" }}
      </button>
    </template>
  </AppModal>

  <!-- ── Detail Modal ── -->
  <AppModal v-if="detailItem" v-model="showDetailModal" :title="detailItem.advisory_id" size="lg">
    <div class="detail-grid">
      <div class="detail-section">
        <h3 class="detail-section-title">Overview</h3>
        <div class="detail-kv">
          <span class="detail-key">Status</span>
          <span class="advisory-status-badge" :class="`advisory-status-${detailItem.status}`">{{ detailItem.status }}</span>
        </div>
        <div class="detail-kv">
          <span class="detail-key">Severity</span>
          <span v-if="detailItem.severity" class="severity-badge" :class="`severity-${detailItem.severity}`">{{ detailItem.severity }}</span>
          <span v-else class="muted">—</span>
        </div>
        <div class="detail-kv">
          <span class="detail-key">CVEs</span>
          <span v-if="detailItem.cve_ids_json.length">
            <span class="cve-pill" v-for="c in detailItem.cve_ids_json" :key="c">{{ c }}</span>
          </span>
          <span v-else class="muted">None</span>
        </div>
      </div>

      <div class="detail-section">
        <h3 class="detail-section-title">Embargo &amp; Publication</h3>
        <div class="detail-kv">
          <span class="detail-key">Embargo until</span>
          <span :class="{ 'text-warning': isUnderEmbargo(detailItem) }">{{ formatDate(detailItem.embargo_until) }}</span>
        </div>
        <div class="detail-kv">
          <span class="detail-key">Published</span>
          <span>{{ formatDate(detailItem.published_at) }}</span>
        </div>
      </div>
    </div>

    <div v-if="detailItem.summary" class="detail-block">
      <h3 class="detail-section-title">Summary</h3>
      <p>{{ detailItem.summary }}</p>
    </div>

    <div v-if="detailItem.workaround" class="detail-block">
      <h3 class="detail-section-title">Workaround</h3>
      <p class="preformatted">{{ detailItem.workaround }}</p>
    </div>

    <div v-if="detailItem.remediation_steps" class="detail-block">
      <h3 class="detail-section-title">Remediation steps</h3>
      <p class="preformatted">{{ detailItem.remediation_steps }}</p>
    </div>

    <template #footer>
      <button class="btn btn-danger-outline" :disabled="isDeleting" @click="deleteAdvisory">
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
import { securityAdvisoryService } from "@/services/security-advisory-service";
import type {
  AdvisoryStatus,
  ProductReleaseSummaryRead,
  ProductSummaryRead,
  SecurityAdvisoryCreate,
  SecurityAdvisoryRead,
  SecurityUpdateSeverity,
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
const detailItem = ref<SecurityAdvisoryRead | null>(null);

const products = ref<ProductSummaryRead[]>([]);
const releases = ref<ProductReleaseSummaryRead[]>([]);
const advisories = ref<SecurityAdvisoryRead[]>([]);

const productQuery = ref("");
const selectedProductId = ref("");
const selectedReleaseId = ref("");
const cveInput = ref("");

const createForm = reactive({
  product_release_id: "",
  advisory_id: "",
  title: "",
  summary: "",
  severity: "" as SecurityUpdateSeverity | "",
  status: "draft" as AdvisoryStatus,
  workaround: "",
  remediation_steps: "",
  embargo_until: "",
  published_at: "",
});

const filteredProducts = computed(() => {
  const q = productQuery.value.trim().toLowerCase();
  const sorted = [...products.value].sort((a, b) => a.name.localeCompare(b.name));
  if (!q) return sorted;
  return sorted.filter((p) =>
    [p.name, p.product_code].join(" ").toLowerCase().includes(q),
  );
});

const embargoCount = computed(
  () => advisories.value.filter((a) => a.status === "embargo").length,
);

function isUnderEmbargo(a: SecurityAdvisoryRead): boolean {
  if (!a.embargo_until) return false;
  return new Date(a.embargo_until) > new Date();
}

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

async function loadAdvisories(): Promise<void> {
  isLoading.value = true;
  errorMessage.value = "";
  try {
    advisories.value = await securityAdvisoryService.list(selectedReleaseId.value || undefined);
  } catch {
    errorMessage.value = "Failed to load advisories.";
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

async function createAdvisory(): Promise<void> {
  isCreating.value = true;
  errorMessage.value = "";
  try {
    const payload: SecurityAdvisoryCreate = {
      product_release_id: createForm.product_release_id,
      advisory_id: createForm.advisory_id,
      title: createForm.title,
      summary: createForm.summary || null,
      severity: (createForm.severity as SecurityUpdateSeverity) || null,
      status: createForm.status,
      cve_ids_json: cveInput.value.split(",").map((s) => s.trim()).filter(Boolean),
      workaround: createForm.workaround || null,
      remediation_steps: createForm.remediation_steps || null,
      embargo_until: toIsoOrNull(createForm.embargo_until),
      published_at: toIsoOrNull(createForm.published_at),
    };
    await securityAdvisoryService.create(payload);
    showCreateModal.value = false;
    successMessage.value = `Advisory ${payload.advisory_id} created.`;
    Object.assign(createForm, {
      advisory_id: "", title: "", summary: "", severity: "", status: "draft",
      workaround: "", remediation_steps: "", embargo_until: "", published_at: "",
    });
    cveInput.value = "";
    await loadAdvisories();
  } catch (err) {
    errorMessage.value = err instanceof Error ? err.message : "Failed to create advisory.";
  } finally {
    isCreating.value = false;
  }
}

function openDetail(item: SecurityAdvisoryRead): void {
  detailItem.value = item;
  showDetailModal.value = true;
}

async function deleteAdvisory(): Promise<void> {
  if (!detailItem.value) return;
  isDeleting.value = true;
  try {
    await securityAdvisoryService.remove(detailItem.value.id);
    showDetailModal.value = false;
    detailItem.value = null;
    successMessage.value = "Advisory deleted.";
    await loadAdvisories();
  } catch {
    errorMessage.value = "Failed to delete advisory.";
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

/* ── Advisory ID ── */
.advisory-id { font-family: monospace; font-size: var(--text-sm); }

/* ── Advisory status badges — design-system tokens only ── */
.advisory-status-badge {
  display: inline-block;
  padding: 0.15rem 0.55rem;
  border-radius: 999px;
  font-size: var(--text-xs);
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.04em;
}

.advisory-status-draft     { background: var(--color-slate-bg);   color: var(--color-slate-text);   border: 1px solid var(--color-slate-border); }
.advisory-status-embargo   { background: var(--color-pink-bg);    color: var(--color-pink-text);    border: 1px solid var(--color-pink-border); }
.advisory-status-published { background: var(--color-emerald-bg); color: var(--color-emerald-text); border: 1px solid var(--color-emerald-border); }
.advisory-status-archived  { background: var(--color-slate-bg);   color: var(--color-slate-text);   border: 1px solid var(--color-slate-border); }

/* ── Severity badges ── */
.severity-badge {
  display: inline-block;
  padding: 0.15rem 0.55rem;
  border-radius: 999px;
  font-size: var(--text-xs);
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.04em;
}

.severity-critical      { background: var(--color-danger-bg);   color: var(--color-danger-text);   border: 1px solid var(--color-danger-border); }
.severity-high          { background: var(--color-pink-bg);     color: var(--color-pink-text);     border: 1px solid var(--color-pink-border); }
.severity-medium        { background: var(--color-warning-bg);  color: var(--color-warning-text);  border: 1px solid var(--color-warning-border); }
.severity-low           { background: var(--color-emerald-bg);  color: var(--color-emerald-text);  border: 1px solid var(--color-emerald-border); }
.severity-informational { background: var(--color-info-bg);     color: var(--color-info-text);     border: 1px solid var(--color-info-border); }

/* ── CVE pills ── */
.cve-pill {
  display: inline-block;
  padding: 0.1rem 0.45rem;
  border-radius: 0.4rem;
  font-size: var(--text-xs);
  font-weight: 600;
  background: var(--color-surface-elevated);
  border: 1px solid var(--color-border);
  margin-right: 0.2rem;
}

/* ── Detail panels ── */
.detail-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 1.25rem; margin-bottom: 1rem; }
.detail-section { display: flex; flex-direction: column; gap: 0.5rem; }
.detail-section-title { font-size: var(--text-sm); font-weight: 700; color: var(--color-text-muted); margin-bottom: 0.25rem; }
.detail-kv { display: flex; gap: 0.5rem; align-items: flex-start; }
.detail-key { font-size: var(--text-sm); color: var(--color-text-muted); min-width: 90px; flex-shrink: 0; }
.detail-block { margin-top: 1rem; padding-top: 1rem; border-top: 1px solid var(--color-border); }
.preformatted { white-space: pre-wrap; font-family: monospace; font-size: var(--text-sm); }

.text-warning { color: var(--color-warning-text); }
.nowrap { white-space: nowrap; }
.row-arrow { color: var(--color-text-muted); font-size: var(--text-lg); text-align: right; opacity: 0; transition: opacity 0.12s; }
.table-row-clickable:hover .row-arrow,
.table-row-clickable:focus-visible .row-arrow { opacity: 1; }
</style>
