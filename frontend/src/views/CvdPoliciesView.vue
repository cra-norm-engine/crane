<template>
  <section class="page">
    <header class="page-header card">
      <div>
        <h1 class="page-title">CVD policies</h1>
        <p class="muted page-subtitle">
          Manage Coordinated Vulnerability Disclosure policies per product.
          An active CVD policy with a published URL is required under CRA Annex I Part II §5.
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

        <button class="btn btn-secondary" @click="loadPolicies" :disabled="isLoading">
          {{ isLoading ? "Refreshing…" : "Load" }}
        </button>

        <button class="btn btn-primary" @click="showCreateModal = true">
          + New policy
        </button>
      </div>
    </header>

    <div v-if="errorMessage" class="card feedback feedback-error">{{ errorMessage }}</div>
    <div v-if="successMessage" class="card feedback feedback-success">{{ successMessage }}</div>

    <!-- Compliance warning -->
    <div v-if="productsWithoutActivePolicy.length > 0" class="card feedback feedback-warning">
      {{ productsWithoutActivePolicy.length }} product(s) have no active CVD policy:
      {{ productsWithoutActivePolicy.slice(0, 3).join(", ") }}
      <span v-if="productsWithoutActivePolicy.length > 3"> and {{ productsWithoutActivePolicy.length - 3 }} more</span>.
    </div>

    <section class="card">
      <div class="section-header">
        <h2 class="section-title">Policies</h2>
        <p class="muted">{{ policies.length }} policy record(s)</p>
      </div>

      <div v-if="isLoading" class="empty-panel">Loading CVD policies…</div>
      <div v-else-if="policies.length === 0" class="empty-panel">No CVD policies found.</div>

      <div v-else class="table-wrapper">
        <table class="data-table">
          <thead>
            <tr>
              <th>Product</th>
              <th>Status</th>
              <th>Disclosure window</th>
              <th>Contact email</th>
              <th>Policy URL</th>
              <th>Updated</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="p in policies"
              :key="p.id"
              class="table-row-clickable"
              @click="openDetail(p)"
              tabindex="0"
              @keydown.enter="openDetail(p)"
            >
              <td>{{ productName(p.product_id) }}</td>
              <td>
                <span class="policy-status-badge" :class="`policy-status-${p.status}`">
                  {{ p.status }}
                </span>
              </td>
              <td>{{ p.disclosure_window_days }} days</td>
              <td>{{ p.contact_email || "—" }}</td>
              <td>
                <a v-if="p.policy_url" :href="p.policy_url" target="_blank" rel="noopener" @click.stop class="policy-url-link">
                  {{ p.policy_url.slice(0, 40) }}{{ p.policy_url.length > 40 ? "…" : "" }}
                </a>
                <span v-else class="muted">—</span>
              </td>
              <td class="nowrap">{{ formatDate(p.updated_at) }}</td>
              <td class="row-arrow">›</td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>
  </section>

  <!-- ── Create Modal ── -->
  <AppModal v-model="showCreateModal" title="New CVD policy" size="lg" :persistent="true">
    <form id="cvd-create-form" class="form-grid" @submit.prevent="createPolicy">
      <div class="field field-span-2">
        <span class="field-label">Product</span>
        <select v-model="createForm.product_id" required>
          <option value="">— Select a product —</option>
          <option v-for="p in products" :key="p.id" :value="p.id">
            {{ p.name }} ({{ p.product_code }})
          </option>
        </select>
      </div>

      <label class="field">
        <span class="field-label">Status</span>
        <select v-model="createForm.status">
          <option value="draft">Draft</option>
          <option value="active">Active</option>
          <option value="archived">Archived</option>
        </select>
      </label>

      <label class="field">
        <span class="field-label">Disclosure window (days)</span>
        <input v-model.number="createForm.disclosure_window_days" type="number" min="1" max="365" />
        <p class="muted" style="font-size:var(--text-xs);margin-top:0.25rem;">CRA guidance recommends ≤ 90 days</p>
      </label>

      <label class="field">
        <span class="field-label">Contact email</span>
        <input v-model.trim="createForm.contact_email" type="email" placeholder="security@example.com" />
      </label>

      <label class="field">
        <span class="field-label">Policy URL</span>
        <input v-model.trim="createForm.policy_url" type="url" placeholder="https://example.com/.well-known/security.txt" />
      </label>

      <label class="field field-span-2">
        <span class="field-label">Policy text (optional)</span>
        <textarea v-model.trim="createForm.policy_text" rows="4" placeholder="Full policy text for offline reference…" />
      </label>
    </form>

    <template #footer>
      <button class="btn btn-secondary" :disabled="isCreating" @click="showCreateModal = false">Cancel</button>
      <button class="btn btn-primary" type="submit" form="cvd-create-form" :disabled="isCreating || !createForm.product_id">
        {{ isCreating ? "Saving…" : "Create policy" }}
      </button>
    </template>
  </AppModal>

  <!-- ── Detail / Edit Modal ── -->
  <AppModal v-if="detailItem" v-model="showDetailModal" title="CVD policy" size="lg">
    <form id="cvd-edit-form" class="form-grid" @submit.prevent="saveEdit">
      <div class="field field-span-2">
        <span class="field-label">Product</span>
        <input :value="productName(detailItem.product_id)" disabled />
      </div>

      <label class="field">
        <span class="field-label">Status</span>
        <select v-model="editForm.status">
          <option value="draft">Draft</option>
          <option value="active">Active</option>
          <option value="archived">Archived</option>
        </select>
      </label>

      <label class="field">
        <span class="field-label">Disclosure window (days)</span>
        <input v-model.number="editForm.disclosure_window_days" type="number" min="1" max="365" />
      </label>

      <label class="field">
        <span class="field-label">Contact email</span>
        <input v-model.trim="editForm.contact_email" type="email" />
      </label>

      <label class="field">
        <span class="field-label">Policy URL</span>
        <input v-model.trim="editForm.policy_url" type="url" />
      </label>

      <label class="field field-span-2">
        <span class="field-label">Policy text</span>
        <textarea v-model.trim="editForm.policy_text" rows="5" />
      </label>
    </form>

    <template #footer>
      <button class="btn btn-danger-outline" :disabled="isDeleting" @click="deletePolicy">
        {{ isDeleting ? "Deleting…" : "Delete" }}
      </button>
      <button class="btn btn-secondary" @click="showDetailModal = false">Cancel</button>
      <button class="btn btn-primary" type="submit" form="cvd-edit-form" :disabled="isSaving">
        {{ isSaving ? "Saving…" : "Save changes" }}
      </button>
    </template>
  </AppModal>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from "vue";

import AppModal from "@/components/AppModal.vue";
import { apiClient } from "@/services/api";
import { cvdPolicyService } from "@/services/cvd-policy-service";
import type {
  CvdPolicyCreate,
  CvdPolicyRead,
  CvdPolicyStatus,
  CvdPolicyUpdate,
  ProductSummaryRead,
} from "@/types/product";

const isLoadingProducts = ref(false);
const isLoading = ref(false);
const isCreating = ref(false);
const isSaving = ref(false);
const isDeleting = ref(false);
const errorMessage = ref("");
const successMessage = ref("");
const showCreateModal = ref(false);
const showDetailModal = ref(false);
const detailItem = ref<CvdPolicyRead | null>(null);

const products = ref<ProductSummaryRead[]>([]);
const policies = ref<CvdPolicyRead[]>([]);
const productQuery = ref("");
const selectedProductId = ref("");

const createForm = reactive({
  product_id: "",
  status: "draft" as CvdPolicyStatus,
  policy_url: "",
  disclosure_window_days: 90,
  contact_email: "",
  policy_text: "",
});

const editForm = reactive({
  status: "draft" as CvdPolicyStatus,
  policy_url: "",
  disclosure_window_days: 90,
  contact_email: "",
  policy_text: "",
});

const filteredProducts = computed(() => {
  const q = productQuery.value.trim().toLowerCase();
  const sorted = [...products.value].sort((a, b) => a.name.localeCompare(b.name));
  if (!q) return sorted;
  return sorted.filter((p) =>
    [p.name, p.product_code].join(" ").toLowerCase().includes(q),
  );
});

const productsWithActivePolicy = computed(() => new Set(
  policies.value.filter((p) => p.status === "active").map((p) => p.product_id),
));

const productsWithoutActivePolicy = computed(() =>
  products.value
    .filter((p) => !productsWithActivePolicy.value.has(p.id))
    .map((p) => p.name),
);

function productName(id: string): string {
  return products.value.find((p) => p.id === id)?.name ?? id;
}

function formatDate(val: string): string {
  return new Date(val).toLocaleDateString(undefined, { dateStyle: "medium" });
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

async function loadPolicies(): Promise<void> {
  isLoading.value = true;
  errorMessage.value = "";
  try {
    policies.value = await cvdPolicyService.list(selectedProductId.value || undefined);
  } catch {
    errorMessage.value = "Failed to load CVD policies.";
  } finally {
    isLoading.value = false;
  }
}

async function createPolicy(): Promise<void> {
  isCreating.value = true;
  errorMessage.value = "";
  try {
    const payload: CvdPolicyCreate = {
      product_id: createForm.product_id,
      status: createForm.status,
      policy_url: createForm.policy_url || null,
      disclosure_window_days: createForm.disclosure_window_days,
      contact_email: createForm.contact_email || null,
      policy_text: createForm.policy_text || null,
    };
    await cvdPolicyService.create(payload);
    showCreateModal.value = false;
    successMessage.value = "CVD policy created.";
    Object.assign(createForm, { product_id: "", status: "draft", policy_url: "", disclosure_window_days: 90, contact_email: "", policy_text: "" });
    await loadPolicies();
  } catch (err) {
    errorMessage.value = err instanceof Error ? err.message : "Failed to create policy.";
  } finally {
    isCreating.value = false;
  }
}

function openDetail(item: CvdPolicyRead): void {
  detailItem.value = item;
  Object.assign(editForm, {
    status: item.status,
    policy_url: item.policy_url ?? "",
    disclosure_window_days: item.disclosure_window_days,
    contact_email: item.contact_email ?? "",
    policy_text: item.policy_text ?? "",
  });
  showDetailModal.value = true;
}

async function saveEdit(): Promise<void> {
  if (!detailItem.value) return;
  isSaving.value = true;
  errorMessage.value = "";
  try {
    const payload: CvdPolicyUpdate = {
      status: editForm.status,
      policy_url: editForm.policy_url || null,
      disclosure_window_days: editForm.disclosure_window_days,
      contact_email: editForm.contact_email || null,
      policy_text: editForm.policy_text || null,
    };
    await cvdPolicyService.update(detailItem.value.id, payload);
    showDetailModal.value = false;
    successMessage.value = "CVD policy updated.";
    await loadPolicies();
  } catch (err) {
    errorMessage.value = err instanceof Error ? err.message : "Failed to update policy.";
  } finally {
    isSaving.value = false;
  }
}

async function deletePolicy(): Promise<void> {
  if (!detailItem.value) return;
  isDeleting.value = true;
  try {
    await cvdPolicyService.remove(detailItem.value.id);
    showDetailModal.value = false;
    detailItem.value = null;
    successMessage.value = "Policy deleted.";
    await loadPolicies();
  } catch {
    errorMessage.value = "Failed to delete policy.";
  } finally {
    isDeleting.value = false;
  }
}

onMounted(async () => {
  await loadProducts();
  await loadPolicies();
});
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

/* ── Policy status badges — design-system tokens only ── */
.policy-status-badge {
  display: inline-block;
  padding: 0.15rem 0.55rem;
  border-radius: 999px;
  font-size: var(--text-xs);
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.04em;
}

.policy-status-draft    { background: var(--color-slate-bg);   color: var(--color-slate-text);   border: 1px solid var(--color-slate-border); }
.policy-status-active   { background: var(--color-emerald-bg); color: var(--color-emerald-text); border: 1px solid var(--color-emerald-border); }
.policy-status-archived { background: var(--color-slate-bg);   color: var(--color-slate-text);   border: 1px solid var(--color-slate-border); }

.policy-url-link { font-size: var(--text-sm); color: var(--color-primary-2); text-decoration: none; }
.policy-url-link:hover { text-decoration: underline; }
.nowrap { white-space: nowrap; }
.row-arrow { color: var(--color-text-muted); font-size: 1.1rem; text-align: right; opacity: 0; transition: opacity 0.12s; }
.table-row-clickable:hover .row-arrow,
.table-row-clickable:focus-visible .row-arrow { opacity: 1; }
</style>
