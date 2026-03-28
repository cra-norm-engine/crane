<template>
  <section class="page">
    <header class="hero">
      <div class="hero-copy">
        <p class="eyebrow">Annex I Mapping Matrix</p>
        <h1>Requirement Mapping Matrix</h1>
        <p class="page-subtitle">
          Trace Annex I obligations to risks, SDL activities, engineering requirements, and audit evidence.
        </p>
      </div>

      <div class="hero-actions">
        <button class="ghost-button" type="button" @click="resetFilters" :disabled="loading">
          Reset filters
        </button>
        <button class="primary-button" type="button" @click="loadData" :disabled="loading">
          {{ loading ? "Refreshing..." : "Refresh data" }}
        </button>
      </div>
    </header>

    <section class="stats-grid" aria-label="Matrix overview">
      <article class="stat-card">
        <span class="stat-label">Visible mappings</span>
        <strong class="stat-value">{{ filteredMappings.length }}</strong>
      </article>
      <article class="stat-card">
        <span class="stat-label">Implemented</span>
        <strong class="stat-value">{{ statusCounts.implemented }}</strong>
      </article>
      <article class="stat-card">
        <span class="stat-label">Verified</span>
        <strong class="stat-value">{{ statusCounts.verified }}</strong>
      </article>
      <article class="stat-card">
        <span class="stat-label">Need attention</span>
        <strong class="stat-value">{{ statusCounts.planned + statusCounts.in_progress }}</strong>
      </article>
    </section>

    <transition name="fade">
      <div v-if="errorMessage" class="alert alert-error" role="alert">
        <span>{{ errorMessage }}</span>
      </div>
    </transition>

    <transition name="fade">
      <div v-if="successMessage" class="alert alert-success" role="status">
        <span>{{ successMessage }}</span>
      </div>
    </transition>

    <section class="panel filters-panel">
      <div class="panel-header panel-header-tight">
        <div>
          <h2>Filters</h2>
          <p class="panel-subtitle">Refine the matrix by annex part, status, or keyword.</p>
        </div>
        <div class="quick-statuses" aria-label="Quick status filters">
          <button
            type="button"
            class="quick-chip"
            :class="{ active: filters.implementationStatus === '' }"
            @click="filters.implementationStatus = ''"
          >
            All
          </button>
          <button
            v-for="option in implementationStatuses"
            :key="option"
            type="button"
            class="quick-chip"
            :class="{ active: filters.implementationStatus === option }"
            @click="filters.implementationStatus = option"
          >
            {{ formatStatus(option) }}
          </button>
        </div>
      </div>

      <div class="filters-grid">
        <label class="field">
          <span>Annex Part</span>
          <select v-model="filters.annexPart">
            <option value="">All parts</option>
            <option value="part_i">Part I</option>
            <option value="part_ii">Part II</option>
          </select>
        </label>

        <label class="field">
          <span>Implementation Status</span>
          <select v-model="filters.implementationStatus">
            <option value="">All statuses</option>
            <option v-for="option in implementationStatuses" :key="option" :value="option">
              {{ formatStatus(option) }}
            </option>
          </select>
        </label>

        <label class="field field-search">
          <span>Search</span>
          <div class="search-input-wrap">
            <input
              v-model="filters.search"
              type="text"
              placeholder="Search code, title, SDL activity, engineering ref, evidence..."
            />
            <button
              v-if="filters.search"
              type="button"
              class="clear-search"
              aria-label="Clear search"
              @click="filters.search = ''"
            >
              ×
            </button>
          </div>
        </label>
      </div>
    </section>

    <section class="matrix-layout">
      <article class="panel list-panel">
        <div class="panel-header list-header">
          <div>
            <h2>Mappings</h2>
            <p class="panel-subtitle">
              {{ filteredMappings.length }} result{{ filteredMappings.length === 1 ? "" : "s" }}
            </p>
          </div>
          <span class="count-badge">{{ filteredMappings.length }}</span>
        </div>

        <div v-if="loading" class="state-block">
          <div class="skeleton-row" v-for="i in 6" :key="i"></div>
        </div>

        <div v-else-if="filteredMappings.length === 0" class="state-block empty-state">
          <h3>No mappings found</h3>
          <p>Try changing filters or clearing the search term.</p>
          <button class="ghost-button" type="button" @click="resetFilters">Clear filters</button>
        </div>

        <div v-else class="table-wrapper">
          <table class="data-table">
            <thead>
              <tr>
                <th>Requirement</th>
                <th>Risk</th>
                <th>SDL</th>
                <th>Engineering Ref</th>
                <th>Status</th>
                <th>Evidence</th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="mapping in filteredMappings"
                :key="mapping.id"
                class="table-row-link"
                :class="{ selected: selectedMapping?.id === mapping.id }"
                tabindex="0"
                @click="selectMapping(mapping)"
                @keydown.enter.prevent="selectMapping(mapping)"
                @keydown.space.prevent="selectMapping(mapping)"
              >
                <td>
                  <div class="primary-cell">
                    <strong class="annex-code">
                      {{ mapping.annex_requirement?.code ?? mapping.annex_requirement_id }}
                    </strong>
                    <span class="cell-title">
                      {{ mapping.annex_requirement?.title ?? "Untitled requirement" }}
                    </span>
                    <span class="cell-meta">
                      {{ formatAnnexPart(mapping.annex_requirement?.annex_part) }}
                    </span>
                  </div>
                </td>
                <td>
                  <span class="truncate-2">
                    {{ mapping.risk_item?.title ?? "Unlinked" }}
                  </span>
                </td>
                <td>
                  <span class="inline-tag">{{ formatLabel(mapping.sdl_activity) }}</span>
                </td>
                <td>
                  <span class="mono truncate-2">
                    {{ mapping.engineering_requirement_ref ?? "—" }}
                  </span>
                </td>
                <td>
                  <span
                    class="status-pill"
                    :class="statusClass(mapping.implementation_status)"
                  >
                    {{ formatStatus(mapping.implementation_status) }}
                  </span>
                </td>
                <td>
                  <span class="evidence-count">
                    {{ mapping.evidence_items?.length ?? 0 }}
                  </span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </article>

      <aside class="panel side-panel">
        <div class="panel-header">
          <div>
            <h2>Selected Mapping</h2>
            <p class="panel-subtitle">
              Inspect details and update implementation data.
            </p>
          </div>
        </div>

        <div v-if="!selectedMapping" class="state-block empty-state side-empty">
          <h3>No mapping selected</h3>
          <p>Select a row from the matrix to inspect and edit its details.</p>
        </div>

        <template v-else>
          <section class="selected-summary">
            <div class="selected-topline">
              <strong class="selected-code">
                {{ selectedMapping.annex_requirement?.code ?? "—" }}
              </strong>
              <span
                class="status-pill"
                :class="statusClass(selectedMapping.implementation_status)"
              >
                {{ formatStatus(selectedMapping.implementation_status) }}
              </span>
            </div>

            <h3 class="selected-title">
              {{ selectedMapping.annex_requirement?.title ?? "Untitled requirement" }}
            </h3>

            <p class="selected-description">
              {{ selectedMapping.annex_requirement?.description ?? "No annex description available." }}
            </p>
          </section>

          <dl class="detail-list">
            <div class="detail-card">
              <dt>Mapping ID</dt>
              <dd class="mono">{{ selectedMapping.id }}</dd>
            </div>
            <div class="detail-card">
              <dt>Annex Part</dt>
              <dd>{{ formatAnnexPart(selectedMapping.annex_requirement?.annex_part) }}</dd>
            </div>
            <div class="detail-card">
              <dt>Risk Item</dt>
              <dd>{{ selectedMapping.risk_item?.title ?? "Unlinked" }}</dd>
            </div>
            <div class="detail-card">
              <dt>Risk Item ID</dt>
              <dd class="mono">{{ selectedMapping.risk_item_id ?? "—" }}</dd>
            </div>
          </dl>

          <form class="form-grid" @submit.prevent="updateSelectedMapping">
            <label class="field">
              <span>Engineering Requirement Ref</span>
              <input
                v-model="editForm.engineering_requirement_ref"
                type="text"
                maxlength="255"
                placeholder="e.g. ENG-SEC-014"
              />
            </label>

            <label class="field">
              <span>Implementation Status</span>
              <select v-model="editForm.implementation_status">
                <option value="">No change</option>
                <option v-for="option in implementationStatuses" :key="option" :value="option">
                  {{ formatStatus(option) }}
                </option>
              </select>
            </label>

            <label class="field field-full">
              <span>SDL Activity</span>
              <select v-model="editForm.sdl_activity">
                <option value="">No change</option>
                <option v-for="option in sdlActivities" :key="option" :value="option">
                  {{ formatLabel(option) }}
                </option>
              </select>
            </label>

            <label class="field field-full">
              <span>Evidence Summary</span>
              <textarea
                v-model="editForm.evidence_summary"
                rows="5"
                placeholder="Summarize evidence, control linkage, verification notes, or audit references..."
              />
            </label>

            <div class="form-actions field-full">
              <button class="primary-button" type="submit" :disabled="saving">
                {{ saving ? "Saving changes..." : "Save mapping" }}
              </button>
            </div>
          </form>

          <section class="evidence-section">
            <div class="section-header">
              <h3>Evidence Links</h3>
              <span class="count-badge subtle">
                {{ selectedMapping.evidence_items?.length ?? 0 }}
              </span>
            </div>

            <div
              v-if="!selectedMapping.evidence_items || selectedMapping.evidence_items.length === 0"
              class="state-block empty-state small"
            >
              <p>No evidence items linked yet.</p>
            </div>

            <ul v-else class="evidence-list">
              <li v-for="item in selectedMapping.evidence_items" :key="item.id" class="evidence-item">
                <div class="evidence-title-row">
                  <strong>{{ item.title }}</strong>
                  <span class="inline-tag">{{ formatLabel(item.evidence_type) }}</span>
                </div>
                <span class="evidence-meta mono">
                  {{ item.external_url || item.file_path || "No path available" }}
                </span>
              </li>
            </ul>
          </section>
        </template>
      </aside>
    </section>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from "vue";

import { requirementMappingService } from "@/services/requirement-mapping-service";
import type { AnnexRequirementRead, AnnexPart } from "@/types/annex-requirement";
import type { EvidenceItemSummaryRead } from "@/types/evidence-item";
import type {
  RequirementImplementationStatus,
  RequirementMappingRead,
  RequirementMappingUpdate,
  SdlActivity,
} from "@/types/requirement-mapping";
import type { RiskItemSummaryRead } from "@/types/risk-item";

type RequirementMappingMatrixRead = RequirementMappingRead & {
  annex_requirement?: AnnexRequirementRead | null;
  risk_item?: RiskItemSummaryRead | null;
  evidence_items?: EvidenceItemSummaryRead[];
};

const loading = ref(false);
const saving = ref(false);
const errorMessage = ref("");
const successMessage = ref("");

const mappings = ref<RequirementMappingMatrixRead[]>([]);
const selectedMapping = ref<RequirementMappingMatrixRead | null>(null);

const implementationStatuses: RequirementImplementationStatus[] = [
  "planned",
  "in_progress",
  "implemented",
  "verified",
  "not_applicable",
];

const sdlActivities: SdlActivity[] = [
  "requirements",
  "design",
  "implementation",
  "verification",
  "validation",
  "vulnerability_management",
  "documentation",
  "post_market",
];

const filters = reactive({
  annexPart: "" as AnnexPart | "",
  implementationStatus: "" as RequirementImplementationStatus | "",
  search: "",
});

const editForm = reactive({
  engineering_requirement_ref: "",
  implementation_status: "" as RequirementImplementationStatus | "",
  sdl_activity: "" as SdlActivity | "",
  evidence_summary: "",
});

const filteredMappings = computed(() => {
  const term = filters.search.trim().toLowerCase();

  return mappings.value.filter((mapping) => {
    if (filters.annexPart && mapping.annex_requirement?.annex_part !== filters.annexPart) {
      return false;
    }

    if (
      filters.implementationStatus &&
      mapping.implementation_status !== filters.implementationStatus
    ) {
      return false;
    }

    if (!term) return true;

    const haystack = [
      mapping.annex_requirement?.code,
      mapping.annex_requirement?.title,
      mapping.annex_requirement?.description,
      mapping.risk_item?.title,
      mapping.sdl_activity,
      mapping.engineering_requirement_ref,
      mapping.evidence_summary,
      ...(mapping.evidence_items?.map(
        (item) => `${item.title} ${item.file_path ?? ""} ${item.external_url ?? ""}`,
      ) ?? []),
    ]
      .filter(Boolean)
      .join(" ")
      .toLowerCase();

    return haystack.includes(term);
  });
});

const statusCounts = computed(() => {
  const counts: Record<RequirementImplementationStatus, number> = {
    planned: 0,
    in_progress: 0,
    implemented: 0,
    verified: 0,
    not_applicable: 0,
  };

  for (const mapping of filteredMappings.value) {
    counts[mapping.implementation_status] += 1;
  }

  return counts;
});

function formatLabel(value?: string | null): string {
  if (!value) return "—";
  return value
    .split("_")
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(" ");
}

function formatStatus(value?: RequirementImplementationStatus | ""): string {
  if (!value) return "—";
  return formatLabel(value);
}

function formatAnnexPart(value?: AnnexPart | null): string {
  if (value === "part_i") return "Part I";
  if (value === "part_ii") return "Part II";
  return "—";
}

function statusClass(status: RequirementImplementationStatus): string {
  return `status-${status}`;
}

function resetFilters(): void {
  filters.annexPart = "";
  filters.implementationStatus = "";
  filters.search = "";
}

function syncEditForm(): void {
  if (!selectedMapping.value) return;

  editForm.engineering_requirement_ref = selectedMapping.value.engineering_requirement_ref ?? "";
  editForm.implementation_status = selectedMapping.value.implementation_status;
  editForm.sdl_activity = selectedMapping.value.sdl_activity;
  editForm.evidence_summary = selectedMapping.value.evidence_summary ?? "";
}

function selectMapping(mapping: RequirementMappingMatrixRead): void {
  selectedMapping.value = mapping;
  syncEditForm();
}

async function loadData(): Promise<void> {
  loading.value = true;
  errorMessage.value = "";
  successMessage.value = "";

  try {
    mappings.value = (await requirementMappingService.list({
      matrix: true,
    })) as RequirementMappingMatrixRead[];

    if (!selectedMapping.value && mappings.value.length > 0) {
      selectedMapping.value = mappings.value[0];
      syncEditForm();
      return;
    }

    if (selectedMapping.value) {
      const refreshed =
        mappings.value.find((item) => item.id === selectedMapping.value?.id) ?? null;
      selectedMapping.value = refreshed;
      if (refreshed) syncEditForm();
    }
  } catch (error: any) {
    errorMessage.value = error?.message ?? "Failed to load requirement mapping matrix.";
    mappings.value = [];
    selectedMapping.value = null;
  } finally {
    loading.value = false;
  }
}

async function updateSelectedMapping(): Promise<void> {
  if (!selectedMapping.value) return;

  saving.value = true;
  errorMessage.value = "";
  successMessage.value = "";

  try {
    const payload: RequirementMappingUpdate = {
      engineering_requirement_ref: editForm.engineering_requirement_ref.trim() || null,
      implementation_status: editForm.implementation_status || undefined,
      sdl_activity: editForm.sdl_activity || undefined,
      evidence_summary: editForm.evidence_summary.trim() || null,
    };

    await requirementMappingService.update(selectedMapping.value.id, payload);
    successMessage.value = "Requirement mapping updated successfully.";
    await loadData();
  } catch (error: any) {
    errorMessage.value = error?.message ?? "Failed to update mapping.";
  } finally {
    saving.value = false;
  }
}

onMounted(async () => {
  await loadData();
});
</script>

<style scoped>
:root {
  color-scheme: light;
}

* {
  box-sizing: border-box;
}

.page {
  display: flex;
  flex-direction: column;
  gap: 1rem;
  color: #0f172a;
}

.hero {
  display: flex;
  justify-content: space-between;
  align-items: flex-end;
  gap: 1rem;
  padding: 1.25rem 1.25rem 0.25rem;
  border-radius: 20px;
  background:
    radial-gradient(circle at top left, rgba(59, 130, 246, 0.12), transparent 32%),
    linear-gradient(180deg, #ffffff 0%, #f8fbff 100%);
  border: 1px solid #e2e8f0;
}

.hero-copy h1 {
  margin: 0;
  font-size: 1.9rem;
  line-height: 1.1;
  letter-spacing: -0.03em;
}

.eyebrow {
  margin: 0 0 0.35rem;
  text-transform: uppercase;
  letter-spacing: 0.12em;
  font-size: 0.74rem;
  font-weight: 700;
  color: #2563eb;
}

.page-subtitle,
.panel-subtitle {
  margin: 0.45rem 0 0;
  color: #64748b;
  line-height: 1.5;
}

.hero-actions,
.form-actions {
  display: flex;
  gap: 0.75rem;
  flex-wrap: wrap;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 0.9rem;
}

.stat-card {
  background: #ffffff;
  border: 1px solid #e2e8f0;
  border-radius: 18px;
  padding: 1rem 1.1rem;
  box-shadow: 0 1px 2px rgba(15, 23, 42, 0.03);
}

.stat-label {
  display: block;
  color: #64748b;
  font-size: 0.88rem;
  margin-bottom: 0.45rem;
}

.stat-value {
  font-size: 1.5rem;
  line-height: 1;
  letter-spacing: -0.03em;
}

.panel {
  background: rgba(255, 255, 255, 0.96);
  border: 1px solid #e2e8f0;
  border-radius: 20px;
  padding: 1rem;
  box-shadow: 0 8px 24px rgba(15, 23, 42, 0.04);
}

.filters-panel {
  position: sticky;
  top: 1rem;
  z-index: 5;
  backdrop-filter: blur(10px);
}

.panel-header {
  display: flex;
  justify-content: space-between;
  gap: 1rem;
  align-items: flex-start;
  margin-bottom: 1rem;
}

.panel-header-tight {
  margin-bottom: 0.85rem;
}

.panel-header h2,
.section-header h3,
.evidence-section h3 {
  margin: 0;
}

.quick-statuses {
  display: flex;
  gap: 0.5rem;
  flex-wrap: wrap;
}

.quick-chip {
  appearance: none;
  border: 1px solid #dbe4f0;
  background: #f8fafc;
  color: #334155;
  border-radius: 999px;
  padding: 0.5rem 0.8rem;
  font: inherit;
  font-size: 0.88rem;
  cursor: pointer;
  transition: all 140ms ease;
}

.quick-chip:hover,
.quick-chip.active {
  background: #eff6ff;
  border-color: #bfdbfe;
  color: #1d4ed8;
}

.filters-grid,
.form-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 1rem;
}

.field {
  display: flex;
  flex-direction: column;
  gap: 0.4rem;
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
  min-height: 46px;
  border: 1px solid #cbd5e1;
  border-radius: 14px;
  padding: 0.8rem 0.9rem;
  font: inherit;
  background: #fff;
  transition: border-color 120ms ease, box-shadow 120ms ease, background 120ms ease;
}

.field textarea {
  resize: vertical;
  min-height: 120px;
}

.field input:focus,
.field select:focus,
.field textarea:focus {
  outline: none;
  border-color: #60a5fa;
  box-shadow: 0 0 0 4px rgba(96, 165, 250, 0.18);
}

.field-full {
  grid-column: 1 / -1;
}

.field-search {
  grid-column: span 1;
}

.search-input-wrap {
  position: relative;
}

.search-input-wrap input {
  padding-right: 2.5rem;
}

.clear-search {
  position: absolute;
  top: 50%;
  right: 0.65rem;
  transform: translateY(-50%);
  width: 1.7rem;
  height: 1.7rem;
  border-radius: 999px;
  border: none;
  background: #e2e8f0;
  color: #334155;
  cursor: pointer;
  font-size: 1rem;
  line-height: 1;
}

.primary-button,
.ghost-button {
  border-radius: 14px;
  padding: 0.78rem 1rem;
  font: inherit;
  font-weight: 600;
  cursor: pointer;
  border: 1px solid transparent;
  transition: transform 120ms ease, box-shadow 120ms ease, background 120ms ease;
}

.primary-button:hover,
.ghost-button:hover {
  transform: translateY(-1px);
}

.primary-button:disabled,
.ghost-button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
  transform: none;
}

.primary-button {
  background: linear-gradient(180deg, #0f172a 0%, #1e293b 100%);
  color: #fff;
  box-shadow: 0 10px 20px rgba(15, 23, 42, 0.14);
}

.ghost-button {
  background: #fff;
  color: #0f172a;
  border-color: #dbe4f0;
}

.alert {
  display: flex;
  align-items: center;
  gap: 0.65rem;
  border-radius: 14px;
  padding: 0.85rem 1rem;
  border: 1px solid;
}

.alert-error {
  background: #fef2f2;
  border-color: #fecaca;
  color: #b91c1c;
}

.alert-success {
  background: #f0fdf4;
  border-color: #bbf7d0;
  color: #15803d;
}

.matrix-layout {
  display: grid;
  grid-template-columns: minmax(0, 1.45fr) minmax(360px, 0.95fr);
  gap: 1rem;
  align-items: start;
}

.list-panel,
.side-panel {
  min-width: 0;
}

.side-panel {
  position: sticky;
  top: 7.5rem;
}

.list-header {
  align-items: center;
}

.count-badge {
  min-width: 2rem;
  text-align: center;
  padding: 0.35rem 0.7rem;
  border-radius: 999px;
  background: #e2e8f0;
  color: #0f172a;
  font-weight: 700;
  font-size: 0.9rem;
}

.count-badge.subtle {
  background: #f1f5f9;
}

.table-wrapper {
  overflow: auto;
  border: 1px solid #e8eef5;
  border-radius: 16px;
}

.data-table {
  width: 100%;
  border-collapse: separate;
  border-spacing: 0;
  min-width: 980px;
}

.data-table thead th {
  position: sticky;
  top: 0;
  z-index: 1;
  background: #f8fafc;
  color: #475569;
  font-size: 0.82rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.03em;
  padding: 0.95rem 0.8rem;
  border-bottom: 1px solid #e2e8f0;
  text-align: left;
}

.data-table td {
  padding: 0.95rem 0.8rem;
  border-bottom: 1px solid #eef2f7;
  vertical-align: top;
  background: #fff;
}

.table-row-link {
  cursor: pointer;
  transition: background 120ms ease, box-shadow 120ms ease;
}

.table-row-link:hover td,
.table-row-link:focus td {
  background: #f8fbff;
}

.table-row-link.selected td {
  background: #eff6ff;
}

.table-row-link:focus {
  outline: none;
}

.table-row-link.selected td:first-child {
  box-shadow: inset 4px 0 0 #2563eb;
}

.primary-cell {
  display: flex;
  flex-direction: column;
  gap: 0.2rem;
}

.annex-code {
  font-size: 0.88rem;
  color: #1d4ed8;
}

.cell-title {
  color: #0f172a;
  line-height: 1.4;
}

.cell-meta {
  color: #64748b;
  font-size: 0.85rem;
}

.inline-tag {
  display: inline-flex;
  align-items: center;
  border-radius: 999px;
  background: #f1f5f9;
  color: #334155;
  padding: 0.3rem 0.6rem;
  font-size: 0.8rem;
  font-weight: 600;
}

.status-pill {
  display: inline-flex;
  align-items: center;
  border-radius: 999px;
  padding: 0.34rem 0.65rem;
  font-size: 0.82rem;
  font-weight: 700;
  white-space: nowrap;
  border: 1px solid transparent;
}

.status-planned {
  background: #fff7ed;
  color: #c2410c;
  border-color: #fed7aa;
}

.status-in_progress {
  background: #eff6ff;
  color: #1d4ed8;
  border-color: #bfdbfe;
}

.status-implemented {
  background: #ecfdf5;
  color: #047857;
  border-color: #a7f3d0;
}

.status-verified {
  background: #eef2ff;
  color: #4338ca;
  border-color: #c7d2fe;
}

.status-not_applicable {
  background: #f8fafc;
  color: #475569;
  border-color: #cbd5e1;
}

.evidence-count {
  display: inline-flex;
  min-width: 1.8rem;
  justify-content: center;
  align-items: center;
  border-radius: 999px;
  background: #f1f5f9;
  color: #0f172a;
  padding: 0.25rem 0.5rem;
  font-weight: 700;
}

.selected-summary {
  padding: 1rem;
  border-radius: 18px;
  background: linear-gradient(180deg, #f8fbff 0%, #ffffff 100%);
  border: 1px solid #e2e8f0;
  margin-bottom: 1rem;
}

.selected-topline {
  display: flex;
  justify-content: space-between;
  gap: 0.75rem;
  align-items: center;
  margin-bottom: 0.7rem;
}

.selected-code {
  color: #1d4ed8;
  font-size: 0.92rem;
}

.selected-title {
  margin: 0 0 0.5rem;
  font-size: 1.15rem;
  line-height: 1.35;
}

.selected-description {
  margin: 0;
  color: #475569;
  line-height: 1.55;
}

.detail-list {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 0.8rem;
  margin: 0 0 1rem;
}

.detail-card {
  padding: 0.85rem 0.9rem;
  border: 1px solid #e2e8f0;
  border-radius: 14px;
  background: #fff;
}

.detail-card dt {
  font-size: 0.8rem;
  color: #64748b;
  margin-bottom: 0.25rem;
}

.detail-card dd {
  margin: 0;
  color: #0f172a;
}

.evidence-section {
  margin-top: 1rem;
  border-top: 1px solid #e2e8f0;
  padding-top: 1rem;
}

.section-header {
  display: flex;
  justify-content: space-between;
  gap: 0.75rem;
  align-items: center;
  margin-bottom: 0.75rem;
}

.evidence-list {
  list-style: none;
  margin: 0;
  padding: 0;
  display: grid;
  gap: 0.75rem;
}

.evidence-item {
  padding: 0.85rem 0.9rem;
  border-radius: 14px;
  background: #f8fafc;
  border: 1px solid #e2e8f0;
}

.evidence-title-row {
  display: flex;
  justify-content: space-between;
  gap: 0.75rem;
  align-items: flex-start;
  margin-bottom: 0.4rem;
}

.evidence-meta {
  display: block;
  color: #64748b;
  font-size: 0.86rem;
  word-break: break-all;
}

.mono {
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
}

.state-block {
  padding: 1rem;
}

.empty-state {
  display: grid;
  place-items: start;
  gap: 0.45rem;
  min-height: 180px;
}

.empty-state h3,
.empty-state p {
  margin: 0;
}

.side-empty {
  min-height: 280px;
}

.small {
  min-height: 0;
  padding: 0.5rem 0;
}

.skeleton-row {
  height: 62px;
  border-radius: 14px;
  margin-bottom: 0.75rem;
  background: linear-gradient(
    90deg,
    rgba(226, 232, 240, 0.55) 25%,
    rgba(241, 245, 249, 0.95) 37%,
    rgba(226, 232, 240, 0.55) 63%
  );
  background-size: 400% 100%;
  animation: shimmer 1.5s infinite linear;
}

.truncate-2 {
  display: -webkit-box;
  -webkit-line-clamp: 2;
  line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 160ms ease, transform 160ms ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
  transform: translateY(-4px);
}

@keyframes shimmer {
  0% {
    background-position: 100% 0;
  }
  100% {
    background-position: 0 0;
  }
}

@media (max-width: 1200px) {
  .stats-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .matrix-layout {
    grid-template-columns: 1fr;
  }

  .side-panel {
    position: static;
  }
}

@media (max-width: 900px) {
  .hero,
  .panel-header,
  .hero-actions {
    flex-direction: column;
    align-items: stretch;
  }

  .filters-grid,
  .form-grid,
  .detail-list {
    grid-template-columns: 1fr;
  }

  .field-search {
    grid-column: auto;
  }

  .stats-grid {
    grid-template-columns: 1fr;
  }

  .table-wrapper {
    border: none;
    overflow: visible;
  }

  .data-table,
  .data-table thead,
  .data-table tbody,
  .data-table th,
  .data-table td,
  .data-table tr {
    display: block;
    min-width: 0;
    width: 100%;
  }

  .data-table thead {
    display: none;
  }

  .data-table tbody {
    display: grid;
    gap: 0.8rem;
  }

  .data-table tr {
    border: 1px solid #e2e8f0;
    border-radius: 16px;
    overflow: hidden;
    background: #fff;
  }

  .data-table td {
    border: none;
    padding: 0.8rem 0.95rem;
  }

  .data-table td::before {
    display: block;
    margin-bottom: 0.25rem;
    font-size: 0.76rem;
    font-weight: 700;
    letter-spacing: 0.03em;
    text-transform: uppercase;
    color: #64748b;
  }

  .data-table td:nth-child(1)::before { content: "Requirement"; }
  .data-table td:nth-child(2)::before { content: "Risk"; }
  .data-table td:nth-child(3)::before { content: "SDL"; }
  .data-table td:nth-child(4)::before { content: "Engineering Ref"; }
  .data-table td:nth-child(5)::before { content: "Status"; }
  .data-table td:nth-child(6)::before { content: "Evidence"; }
}
</style>