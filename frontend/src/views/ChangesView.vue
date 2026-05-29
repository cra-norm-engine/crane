<template>
  <section class="page">
    <!-- Page header with filters and create button -->
    <header class="page-header">
      <div>
        <h1 class="page-title">Substantial changes</h1>
        <p class="muted page-subtitle">
          Record, assess, and track modifications to products under CRA substantial modification rules (Art. 3(4)).
        </p>
      </div>

      <div class="page-actions">
        <!-- Status filter -->
        <label class="field">
          <span class="field-label">Status</span>
          <select v-model="filters.status">
            <option value="">All statuses</option>
            <option value="draft">Draft</option>
            <option value="submitted">Submitted</option>
            <option value="under_review">Under review</option>
            <option value="assessed">Assessed</option>
            <option value="action_required">Action required</option>
            <option value="closed">Closed</option>
          </select>
        </label>

        <!-- Change type filter -->
        <label class="field">
          <span class="field-label">Type</span>
          <select v-model="filters.change_type">
            <option value="">All types</option>
            <option value="feature">Feature</option>
            <option value="security">Security</option>
            <option value="repair">Repair</option>
            <option value="maintenance">Maintenance</option>
          </select>
        </label>

        <!-- Substantiality filter -->
        <label class="field">
          <span class="field-label">Substantial</span>
          <select v-model="filters.is_substantial">
            <option value="">Any</option>
            <option value="true">Yes — substantial</option>
            <option value="false">No — not substantial</option>
          </select>
        </label>

        <AppButton variant="primary" type="button" @click="openCreateModal">
          + New change
        </AppButton>
      </div>
    </header>

    <!-- Stat cards: give a quick breakdown by status -->
    <div class="stat-row">
      <div class="stat-card">
        <span class="stat-value">{{ statCounts.open }}</span>
        <span class="stat-label muted">Open (draft / submitted / review)</span>
      </div>
      <div class="stat-card stat-card-warn">
        <span class="stat-value">{{ statCounts.action_required }}</span>
        <span class="stat-label muted">Action required</span>
      </div>
      <div class="stat-card stat-card-success">
        <span class="stat-value">{{ statCounts.closed }}</span>
        <span class="stat-label muted">Closed</span>
      </div>
      <div class="stat-card stat-card-alert">
        <span class="stat-value">{{ statCounts.substantial }}</span>
        <span class="stat-label muted">Substantial (all time)</span>
      </div>
    </div>

    <!-- Error / success banners -->
    <div v-if="errorMessage" class="card feedback feedback-error">{{ errorMessage }}</div>
    <div v-if="successMessage" class="card feedback feedback-success">{{ successMessage }}</div>

    <!-- Change list table -->
    <section class="card">
      <div class="section-header">
        <div>
          <h2 class="section-title">Changes</h2>
          <p class="muted">{{ filteredChanges.length }} change(s) — click a row to view details</p>
        </div>
      </div>

      <div v-if="isLoading" class="empty-panel">Loading changes…</div>
      <div v-else-if="filteredChanges.length === 0" class="empty-panel">
        No changes match the current filters.
      </div>

      <div v-else class="table-wrapper">
        <table class="data-table">
          <thead>
            <tr>
              <th>Title</th>
              <th>Product / Release</th>
              <th>Type</th>
              <th>Status</th>
              <th>Substantial</th>
              <th>Change date</th>
              <th>Created</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="change in filteredChanges"
              :key="change.id"
              class="table-row-clickable"
              tabindex="0"
              @click="goToDetail(change.id)"
              @keydown.enter="goToDetail(change.id)"
              @keydown.space.prevent="goToDetail(change.id)"
            >
              <!-- Title column -->
              <td>
                <strong>{{ change.title }}</strong>
              </td>

              <!-- Product and release display_version — resolved server-side to avoid UUID display -->
              <td>
                <span v-if="change.product_name" class="product-cell">
                  <span class="product-name">{{ change.product_name }}</span>
                  <span v-if="change.release_version" class="release-display_version muted"> v{{ change.release_version }}</span>
                </span>
                <span v-else class="muted">—</span>
              </td>

              <!-- Change type badge -->
              <td>
                <span class="type-badge" :class="`type-${change.change_type}`">
                  {{ formatLabel(change.change_type) }}
                </span>
              </td>

              <!-- Status badge -->
              <td>
                <span class="status-badge" :class="`status-${change.status}`">
                  {{ formatLabel(change.status) }}
                </span>
              </td>

              <!-- Substantiality indicator -->
              <td>
                <span v-if="change.is_substantial === true" class="substantial-yes">Yes</span>
                <span v-else-if="change.is_substantial === false" class="substantial-no">No</span>
                <span v-else class="muted">Pending</span>
              </td>

              <!-- Dates -->
              <td class="nowrap">{{ formatDate(change.change_date) }}</td>
              <td class="nowrap">{{ formatDate(change.created_at) }}</td>
              <td class="row-arrow">›</td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>
  </section>

  <!-- ── Create Change Modal ── -->
  <Teleport to="body">
    <Transition name="modal">
      <div
        v-if="showCreateModal"
        class="modal-backdrop"
        @click.self="closeCreateModal"
        role="dialog"
        aria-modal="true"
        aria-label="Create new change"
      >
        <div class="create-modal">
          <div class="detail-header">
            <h2 class="section-title">New change</h2>
            <button class="btn btn-icon btn-close" @click="closeCreateModal" aria-label="Close">✕</button>
          </div>

          <form class="form-body" @submit.prevent="submitCreate">
            <!-- Step 1: pick a product -->
            <label class="field field-span-2">
              <span class="field-label">Product</span>
              <select
                v-model="selectedProductId"
                required
                :disabled="isLoadingProducts"
                @change="onProductChange"
              >
                <option value="">
                  {{ isLoadingProducts ? "Loading products…" : "Select a product" }}
                </option>
                <option v-for="p in products" :key="p.id" :value="p.id">
                  {{ p.name }} ({{ p.product_code }})
                </option>
              </select>
            </label>

            <!-- Step 2: pick a release for the selected product -->
            <label class="field field-span-2">
              <span class="field-label">Release</span>
              <select
                v-model="createForm.product_version_id"
                required
                :disabled="!selectedProductId || isLoadingReleases || releases.length === 0"
              >
                <option value="">
                  {{
                    !selectedProductId
                      ? "Select a product first"
                      : isLoadingReleases
                        ? "Loading releases…"
                        : releases.length === 0
                          ? "No releases found"
                          : "Select a release"
                  }}
                </option>
                <option v-for="r in releases" :key="r.id" :value="r.id">
                  {{ r.display_version }} — {{ formatLabel(r.release_status) }}
                  {{ r.actual_release_date ? `(${formatDate(r.actual_release_date)})` : "" }}
                </option>
              </select>
            </label>

            <!-- Change type -->
            <label class="field">
              <span class="field-label">Type</span>
              <select v-model="createForm.change_type" required>
                <option value="feature">Feature</option>
                <option value="security">Security</option>
                <option value="repair">Repair</option>
                <option value="maintenance">Maintenance</option>
              </select>
            </label>

            <!-- Change date -->
            <label class="field">
              <span class="field-label">Change date</span>
              <input v-model="createForm.change_date" type="date" required />
            </label>

            <!-- Title -->
            <label class="field field-span-2">
              <span class="field-label">Title</span>
              <input
                v-model.trim="createForm.title"
                type="text"
                placeholder="Brief, descriptive title (min 3 chars)"
                minlength="3"
                maxlength="255"
                required
              />
            </label>

            <!-- Description -->
            <label class="field field-span-2">
              <span class="field-label">Description</span>
              <textarea
                v-model.trim="createForm.description"
                rows="4"
                placeholder="Describe the change in detail (min 10 chars)"
                minlength="10"
                required
              />
            </label>

            <div class="form-actions field-span-2">
              <AppButton variant="secondary" type="button" @click="closeCreateModal">Cancel</AppButton>
              <AppButton variant="primary" type="submit" :disabled="isCreating">
                {{ isCreating ? "Creating…" : "Create draft" }}
              </AppButton>
            </div>
          </form>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref, watch } from "vue";
import { useRouter } from "vue-router";
import AppButton from "@/components/AppButton.vue";

import { changeService } from "@/services/change-service";
import { productService } from "@/services/product-service";
import { productReleaseService } from "@/services/product-release-service";
import type { ChangeCreate, ChangeListParams, ChangeSummary, ChangeType, ChangeStatus } from "@/types/change";
import type { ProductSummaryRead } from "@/types/product";
import type { ProductReleaseRead } from "@/types/release-gate";

const router = useRouter();

// ---------------------------------------------------------------------------
// State
// ---------------------------------------------------------------------------

/** Full unfiltered list fetched from the API. */
const allChanges = ref<ChangeSummary[]>([]);

/** Whether the initial list load is in progress. */
const isLoading = ref(false);

/** Whether a create-change POST is in flight. */
const isCreating = ref(false);

/** Controls visibility of the create-change modal. */
const showCreateModal = ref(false);

const errorMessage = ref("");
const successMessage = ref("");

/** Active filter values — watched to re-fetch from server. */
const filters = reactive<{
  status: ChangeStatus | "";
  change_type: ChangeType | "";
  is_substantial: "true" | "false" | "";
}>({
  status: "",
  change_type: "",
  is_substantial: "",
});

/** Blank create-change form, reset after each successful submit. */
const createForm = reactive<ChangeCreate>({
  product_version_id: "",
  change_type: "feature",
  title: "",
  description: "",
  change_date: new Date().toISOString().slice(0, 10),
});

/** Product/release picker state for the create modal. */
const products = ref<ProductSummaryRead[]>([]);
const releases = ref<ProductReleaseRead[]>([]);
const selectedProductId = ref("");
const isLoadingProducts = ref(false);
const isLoadingReleases = ref(false);

// ---------------------------------------------------------------------------
// Computed helpers
// ---------------------------------------------------------------------------

/**
 * Client-side filtered view of allChanges.
 * Server already filters by status/type/is_substantial, but we keep this
 * computed so the table stays reactive while the user changes dropdowns
 * before the debounced fetch returns.
 */
const filteredChanges = computed(() => allChanges.value);

/** Summary counts for the stat cards at the top. */
const statCounts = computed(() => {
  const list = allChanges.value;
  return {
    open: list.filter((c) =>
      ["draft", "submitted", "under_review"].includes(c.status)
    ).length,
    action_required: list.filter((c) => c.status === "action_required").length,
    closed: list.filter((c) => c.status === "closed").length,
    substantial: list.filter((c) => c.is_substantial === true).length,
  };
});

// ---------------------------------------------------------------------------
// Data fetching
// ---------------------------------------------------------------------------

/** Load changes from the API using the current filter values. */
async function loadChanges(): Promise<void> {
  isLoading.value = true;
  errorMessage.value = "";

  try {
    const params: ChangeListParams = {};
    if (filters.status) params.status = filters.status;
    if (filters.change_type) params.change_type = filters.change_type;
    if (filters.is_substantial === "true") params.is_substantial = true;
    else if (filters.is_substantial === "false") params.is_substantial = false;

    allChanges.value = await changeService.list(params);
  } catch (err) {
    errorMessage.value = err instanceof Error ? err.message : "Failed to load changes.";
  } finally {
    isLoading.value = false;
  }
}

// Re-fetch whenever a filter changes
watch([() => filters.status, () => filters.change_type, () => filters.is_substantial], () => {
  void loadChanges();
});

onMounted(() => {
  void loadChanges();
  void loadProducts();
});

// ---------------------------------------------------------------------------
// Product / release picker for the create modal
// ---------------------------------------------------------------------------

/** Load all products to populate the product dropdown. */
async function loadProducts(): Promise<void> {
  isLoadingProducts.value = true;
  try {
    products.value = await productService.list();
  } catch {
    // Silently fail — modal will show an empty list
  } finally {
    isLoadingProducts.value = false;
  }
}

/** Load releases whenever the user picks a product. */
async function onProductChange(): Promise<void> {
  releases.value = [];
  createForm.product_version_id = "";

  if (!selectedProductId.value) return;

  isLoadingReleases.value = true;
  try {
    const all = await productReleaseService.list(selectedProductId.value);
    // Show all releases so users can associate a change with any display_version,
    // but sort released/approved first for convenience.
    const priority = ["released", "approved"];
    releases.value = [...all].sort((a, b) => {
      const ai = priority.indexOf(a.release_status);
      const bi = priority.indexOf(b.release_status);
      if (ai !== bi) return (ai === -1 ? 99 : ai) - (bi === -1 ? 99 : bi);
      return (b.display_version ?? "").localeCompare(a.display_version ?? "");
    });
  } catch {
    releases.value = [];
  } finally {
    isLoadingReleases.value = false;
  }
}

// ---------------------------------------------------------------------------
// Create change
// ---------------------------------------------------------------------------

function openCreateModal(): void {
  showCreateModal.value = true;
}

function closeCreateModal(): void {
  showCreateModal.value = false;
}

async function submitCreate(): Promise<void> {
  isCreating.value = true;
  errorMessage.value = "";
  successMessage.value = "";

  try {
    const created = await changeService.create({ ...createForm });
    successMessage.value = `Change "${created.title}" created as draft.`;
    showCreateModal.value = false;

    // Reset form and picker
    createForm.product_version_id = "";
    createForm.change_type = "feature";
    createForm.title = "";
    createForm.description = "";
    createForm.change_date = new Date().toISOString().slice(0, 10);
    selectedProductId.value = "";
    releases.value = [];

    await loadChanges();
  } catch (err) {
    errorMessage.value = err instanceof Error ? err.message : "Failed to create change.";
  } finally {
    isCreating.value = false;
  }
}

// ---------------------------------------------------------------------------
// Navigation
// ---------------------------------------------------------------------------

function goToDetail(changeId: string): void {
  void router.push({ name: "change-detail", params: { id: changeId } });
}

// ---------------------------------------------------------------------------
// Formatting helpers
// ---------------------------------------------------------------------------

function formatDate(value: string | null): string {
  if (!value) return "—";
  return new Intl.DateTimeFormat(undefined, {
    year: "numeric",
    month: "short",
    day: "2-digit",
  }).format(new Date(value));
}

function formatLabel(value: string): string {
  return value.replaceAll("_", " ");
}
</script>

<style scoped>
.page {
  display: grid;
  gap: 1rem;
}

.page-header {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.page-title,
.section-title {
  margin: 0;
}

.page-subtitle {
  margin-top: 0.35rem;
}

.page-actions {
  display: flex;
  align-items: flex-end;
  gap: 0.75rem;
  flex-wrap: wrap;
}

.page-actions .field {
  flex: 1 1 12rem;
  min-width: 10rem;
}

.field {
  display: grid;
  gap: 0.4rem;
}

.field-label {
  color: var(--color-text-muted, #94a3b8);
  font-size: var(--text-xs);
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.06em;
}

/* Stat cards */
.stat-row {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 0.75rem;
}

.stat-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 0.25rem;
  padding: 1rem;
  border-radius: 1rem;
  border: 1px solid var(--color-border, rgba(148, 163, 184, 0.2));
  background: var(--color-surface-soft, rgba(15, 23, 42, 0.4));
  text-align: center;
}

.stat-value {
  font-size: var(--text-3xl);
  font-weight: 700;
  line-height: 1;
}

.stat-label {
  font-size: var(--text-xs);
}

.stat-card-warn .stat-value   { color: #fbbf24; }
.stat-card-success .stat-value { color: #4ade80; }
.stat-card-alert .stat-value  { color: #f87171; }

/* Feedback banners */
.feedback {
  padding: 1rem 1.1rem;
  border-radius: 1rem;
}

.feedback-error   { color: #fda4af; }
.feedback-success { color: #86efac; }

/* Section header */
.section-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 1rem;
  margin-bottom: 1rem;
}

/* Empty state */
.empty-panel {
  padding: 2rem;
  text-align: center;
  color: var(--color-text-muted, #94a3b8);
}

/* Table */
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
  border-bottom: 1px solid var(--color-border, rgba(148, 163, 184, 0.15));
  vertical-align: middle;
}

.data-table th {
  color: var(--color-text-muted, #94a3b8);
  font-size: var(--text-xs);
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  white-space: nowrap;
}

.table-row-clickable {
  cursor: pointer;
  transition: background 0.13s;
}

.table-row-clickable:hover {
  background: var(--color-surface-elevated, rgba(255, 255, 255, 0.04));
}

.table-row-clickable:focus-visible {
  outline: 2px solid var(--color-primary, #6ea8fe);
  outline-offset: -2px;
}

.row-arrow {
  color: var(--color-text-muted, #94a3b8);
  text-align: right;
  font-size: var(--text-lg);
  opacity: 0;
  transition: opacity 0.13s;
}

.table-row-clickable:hover .row-arrow,
.table-row-clickable:focus-visible .row-arrow {
  opacity: 1;
}

.nowrap { white-space: nowrap; }

/* Product/release column in the changes list */
.product-cell { display: flex; flex-direction: column; gap: 0.1rem; }
.product-name  { font-size: var(--text-sm); font-weight: 500; }
.release-display_version { font-size: var(--text-xs); }

/* Change-type badges */
.type-badge {
  display: inline-block;
  padding: 0.15rem 0.55rem;
  border-radius: 999px;
  font-size: var(--text-xs);
  font-weight: 500;
  text-transform: capitalize;
}

.type-feature     { background: rgba(110, 168, 254, 0.15); color: #6ea8fe; }
.type-security    { background: rgba(34, 197, 94, 0.15);  color: #4ade80; }
.type-repair      { background: rgba(251, 191, 36, 0.15); color: #fbbf24; }
.type-maintenance { background: rgba(148, 163, 184, 0.15); color: #94a3b8; }

/* Status badges */
.status-badge {
  display: inline-block;
  padding: 0.15rem 0.55rem;
  border-radius: 999px;
  font-size: var(--text-xs);
  font-weight: 500;
  text-transform: capitalize;
}

.status-draft          { background: rgba(148, 163, 184, 0.12); color: #94a3b8; }
.status-submitted      { background: rgba(110, 168, 254, 0.15); color: #6ea8fe; }
.status-under_review   { background: rgba(139, 92, 246, 0.15);  color: #a78bfa; }
.status-assessed       { background: rgba(34, 197, 94, 0.15);   color: #4ade80; }
.status-action_required{ background: rgba(251, 191, 36, 0.18);  color: #fbbf24; }
.status-closed         { background: rgba(100, 116, 139, 0.12); color: #64748b; }

/* Substantiality indicators */
.substantial-yes { color: #f87171; font-weight: 600; font-size: var(--text-sm); }
.substantial-no  { color: #4ade80; font-size: var(--text-sm); }

/* Buttons */
.btn {
  border: 1px solid transparent;
  border-radius: 0.85rem;
  padding: 0.75rem 1rem;
  font: inherit;
  cursor: pointer;
  white-space: nowrap;
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

.btn-icon {
  padding: 0.4rem 0.6rem;
  font-size: var(--text-xs);
  line-height: 1;
}

.btn-close {
  background: transparent;
  border-color: var(--color-border, rgba(148, 163, 184, 0.2));
  color: var(--color-text-muted, #94a3b8);
  border-radius: 0.6rem;
  transition: color 0.12s, border-color 0.12s;
}

.btn-close:hover {
  color: #f87171;
  border-color: rgba(248, 113, 113, 0.4);
}

/* Modal */
.modal-backdrop {
  position: fixed;
  inset: 0;
  background: rgba(5, 10, 20, 0.78);
  z-index: 200;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 1rem;
}

.create-modal {
  background: var(--color-modal-bg, #0c1524);
  border: 1px solid var(--color-border, rgba(148, 163, 184, 0.2));
  border-radius: 1.2rem;
  width: 100%;
  max-width: 42rem;
  max-height: 90vh;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  box-shadow: 0 24px 80px rgba(0, 0, 0, 0.6);
}

.detail-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 1.5rem;
  border-bottom: 1px solid var(--color-border, rgba(148, 163, 184, 0.15));
  flex-shrink: 0;
}

.form-body {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 1rem;
  padding: 1.5rem;
  overflow-y: auto;
}

.field-span-2 {
  grid-column: span 2;
}

input,
textarea,
select {
  width: 100%;
  padding: 0.75rem 0.9rem;
  border-radius: 0.85rem;
  border: 1px solid var(--color-border, rgba(148, 163, 184, 0.25));
  background: var(--color-surface-soft, rgba(15, 23, 42, 0.5));
  color: inherit;
  font: inherit;
  box-sizing: border-box;
}

.form-actions {
  display: flex;
  justify-content: flex-end;
  gap: 0.75rem;
  padding-top: 0.5rem;
}

/* Modal transitions */
.modal-enter-active,
.modal-leave-active {
  transition: opacity 0.18s ease;
}

.modal-enter-active .create-modal,
.modal-leave-active .create-modal {
  transition: transform 0.18s ease, opacity 0.18s ease;
}

.modal-enter-from,
.modal-leave-to { opacity: 0; }

.modal-enter-from .create-modal,
.modal-leave-to .create-modal {
  transform: translateY(12px) scale(0.98);
  opacity: 0;
}

.muted { color: var(--color-text-muted, #94a3b8); }

@media (max-width: 900px) {
  .stat-row { grid-template-columns: repeat(2, 1fr); }
}

@media (max-width: 600px) {
  .stat-row { grid-template-columns: 1fr; }
  .form-body { grid-template-columns: 1fr; }
  .field-span-2 { grid-column: span 1; }
}
</style>

<style>
:root[data-theme="light"] .feedback-error   { color: #be123c; }
:root[data-theme="light"] .feedback-success { color: #15803d; }
:root[data-theme="light"] .btn-primary { background: linear-gradient(135deg, rgba(175, 214, 46, 0.95), rgba(28, 107, 39, 0.95)); }
:root[data-theme="light"] .table-row-clickable:hover { background: rgba(37, 99, 235, 0.04); }
:root[data-theme="light"] .type-feature { background: rgba(37, 99, 235, 0.1); color: #2563eb; }
:root[data-theme="light"] .type-security { background: rgba(22, 163, 74, 0.1); color: #16a34a; }
:root[data-theme="light"] .type-repair { background: rgba(202, 138, 4, 0.1); color: #ca8a04; }
:root[data-theme="light"] .type-maintenance { background: rgba(100, 116, 139, 0.1); color: #475569; }
:root[data-theme="light"] .status-submitted { background: rgba(37, 99, 235, 0.1); color: #2563eb; }
:root[data-theme="light"] .status-under_review { background: rgba(109, 40, 217, 0.1); color: #6d28d9; }
:root[data-theme="light"] .status-assessed { background: rgba(22, 163, 74, 0.1); color: #16a34a; }
:root[data-theme="light"] .status-action_required { background: rgba(202, 138, 4, 0.1); color: #b45309; }
:root[data-theme="light"] .substantial-yes { color: #dc2626; }
:root[data-theme="light"] .substantial-no  { color: #16a34a; }
:root[data-theme="light"] .create-modal { background: #ffffff; }
</style>
