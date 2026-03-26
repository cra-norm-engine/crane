<template>
  <section class="page">
    <header class="page-header">
      <div>
        <p class="eyebrow">Annex I Mapping Matrix</p>
        <h1>Annex Requirement Mapping Matrix</h1>
        <p class="page-subtitle">
          Trace Annex I obligations to risk findings, SDL activities, engineering requirements, and evidence.
        </p>
      </div>
      <div class="header-actions">
        <button class="secondary-button" type="button" @click="loadData" :disabled="loading">
          {{ loading ? "Refreshing..." : "Refresh" }}
        </button>
      </div>
    </header>

    <p v-if="errorMessage" class="error-text">{{ errorMessage }}</p>
    <p v-if="successMessage" class="success-text">{{ successMessage }}</p>

    <section class="panel">
      <div class="panel-header">
        <h2>Filters</h2>
      </div>

      <div class="filters-grid">
        <label class="field">
          <span>Annex Part</span>
          <select v-model="filters.annexPart">
            <option value="">All</option>
            <option value="part_i">Part I</option>
            <option value="part_ii">Part II</option>
          </select>
        </label>

        <label class="field">
          <span>Implementation Status</span>
          <select v-model="filters.implementationStatus">
            <option value="">All</option>
            <option v-for="option in implementationStatuses" :key="option" :value="option">
              {{ option }}
            </option>
          </select>
        </label>

        <label class="field">
          <span>Search</span>
          <input
            v-model="filters.search"
            type="text"
            placeholder="Search code, title, SDL activity, engineering ref, evidence..."
          />
        </label>
      </div>
    </section>

    <section class="matrix-layout">
      <article class="panel">
        <div class="panel-header">
          <h2>Mappings</h2>
          <span class="count-badge">{{ filteredMappings.length }}</span>
        </div>

        <div v-if="loading" class="loading-state">Loading matrix...</div>

        <div v-else-if="filteredMappings.length === 0" class="empty-state">
          No mappings match the current filters.
        </div>

        <div v-else class="table-wrapper">
          <table class="data-table">
            <thead>
              <tr>
                <th>Annex Code</th>
                <th>Annex Title</th>
                <th>Risk Item</th>
                <th>SDL Activity</th>
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
                @click="selectMapping(mapping)"
              >
                <td>{{ mapping.annex_requirement?.code ?? mapping.annex_requirement_id }}</td>
                <td>{{ mapping.annex_requirement?.title ?? "—" }}</td>
                <td>{{ mapping.risk_item?.title ?? "Unlinked" }}</td>
                <td>{{ mapping.sdl_activity }}</td>
                <td>{{ mapping.engineering_requirement_ref ?? "—" }}</td>
                <td><span class="status-pill">{{ mapping.implementation_status }}</span></td>
                <td>{{ mapping.evidence_items?.length ?? 0 }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </article>

      <article class="panel side-panel">
        <div class="panel-header">
          <h2>Selected Mapping</h2>
        </div>

        <div v-if="!selectedMapping" class="empty-state">
          Select a row to inspect mapping detail or update fields.
        </div>

        <template v-else>
          <dl class="detail-list">
            <div>
              <dt>Mapping ID</dt>
              <dd class="mono">{{ selectedMapping.id }}</dd>
            </div>
            <div>
              <dt>Annex Code</dt>
              <dd>{{ selectedMapping.annex_requirement?.code ?? "—" }}</dd>
            </div>
            <div>
              <dt>Annex Title</dt>
              <dd>{{ selectedMapping.annex_requirement?.title ?? "—" }}</dd>
            </div>
            <div>
              <dt>Annex Part</dt>
              <dd>{{ selectedMapping.annex_requirement?.annex_part ?? "—" }}</dd>
            </div>
            <div>
              <dt>Risk Item</dt>
              <dd>{{ selectedMapping.risk_item?.title ?? "Unlinked" }}</dd>
            </div>
            <div>
              <dt>Risk Item ID</dt>
              <dd class="mono">{{ selectedMapping.risk_item_id ?? "—" }}</dd>
            </div>
            <div class="detail-full">
              <dt>Annex Description</dt>
              <dd>{{ selectedMapping.annex_requirement?.description ?? "—" }}</dd>
            </div>
          </dl>

          <form class="form-grid" @submit.prevent="updateSelectedMapping">
            <label class="field">
              <span>Engineering Requirement Ref</span>
              <input v-model="editForm.engineering_requirement_ref" type="text" maxlength="255" />
            </label>

            <label class="field">
              <span>Implementation Status</span>
              <select v-model="editForm.implementation_status">
                <option value="">No change</option>
                <option v-for="option in implementationStatuses" :key="option" :value="option">
                  {{ option }}
                </option>
              </select>
            </label>

            <label class="field field-full">
              <span>SDL Activity</span>
              <input v-model="editForm.sdl_activity" type="text" maxlength="255" />
            </label>

            <label class="field field-full">
              <span>Evidence Summary</span>
              <textarea v-model="editForm.evidence_summary" rows="4" />
            </label>

            <div class="form-actions field-full">
              <button class="primary-button" type="submit" :disabled="saving">
                {{ saving ? "Saving..." : "Save Mapping" }}
              </button>
            </div>
          </form>

          <div class="evidence-section">
            <h3>Evidence Links</h3>
            <div
              v-if="!selectedMapping.evidence_items || selectedMapping.evidence_items.length === 0"
              class="empty-state small"
            >
              No evidence items linked yet.
            </div>
            <ul v-else class="evidence-list">
              <li v-for="item in selectedMapping.evidence_items" :key="item.id">
                <strong>{{ item.title }}</strong>
                <span class="evidence-meta">
                  {{ item.evidence_type }}
                  <template v-if="item.external_url"> · {{ item.external_url }}</template>
                  <template v-else-if="item.file_path"> · {{ item.file_path }}</template>
                </span>
              </li>
            </ul>
          </div>
        </template>
      </article>
    </section>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from "vue";

import riskService from "@/services/risk-service";
import type {
  AnnexPart,
  RequirementImplementationStatus,
  RequirementMappingRead,
  RequirementMappingUpdate,
} from "@/types/risk";

const loading = ref(false);
const saving = ref(false);
const errorMessage = ref("");
const successMessage = ref("");

const mappings = ref<RequirementMappingRead[]>([]);
const selectedMapping = ref<RequirementMappingRead | null>(null);

const implementationStatuses: RequirementImplementationStatus[] = [
  "planned",
  "in_progress",
  "implemented",
  "verified",
  "not_applicable",
];

const filters = reactive({
  annexPart: "" as AnnexPart | "",
  implementationStatus: "" as RequirementImplementationStatus | "",
  search: "",
});

const editForm = reactive({
  engineering_requirement_ref: "",
  implementation_status: "" as RequirementImplementationStatus | "",
  sdl_activity: "",
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

    if (!term) {
      return true;
    }

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

function syncEditForm(): void {
  if (!selectedMapping.value) return;

  editForm.engineering_requirement_ref = selectedMapping.value.engineering_requirement_ref ?? "";
  editForm.implementation_status = selectedMapping.value.implementation_status;
  editForm.sdl_activity = selectedMapping.value.sdl_activity;
  editForm.evidence_summary = selectedMapping.value.evidence_summary ?? "";
}

function selectMapping(mapping: RequirementMappingRead): void {
  selectedMapping.value = mapping;
  syncEditForm();
}

async function loadData(): Promise<void> {
  loading.value = true;
  errorMessage.value = "";
  successMessage.value = "";

  try {
    mappings.value = await riskService.listRequirementMappings({ matrix: true });

    if (selectedMapping.value) {
      const refreshed = mappings.value.find((item) => item.id === selectedMapping.value?.id) ?? null;
      selectedMapping.value = refreshed;
      if (refreshed) {
        syncEditForm();
      }
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
      sdl_activity: editForm.sdl_activity.trim() || undefined,
      evidence_summary: editForm.evidence_summary.trim() || null,
    };

    await riskService.updateRequirementMapping(selectedMapping.value.id, payload);
    successMessage.value = "Requirement mapping updated.";
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
.page {
  display: flex;
  flex-direction: column;
  gap: 1.25rem;
}

.eyebrow {
  margin: 0 0 0.25rem;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  font-size: 0.78rem;
  color: #64748b;
}

.page-header,
.panel-header {
  display: flex;
  justify-content: space-between;
  gap: 1rem;
  align-items: flex-start;
}

.page-header h1,
.panel-header h2 {
  margin: 0;
}

.page-subtitle {
  margin: 0.4rem 0 0;
  color: #64748b;
}

.header-actions,
.form-actions {
  display: flex;
  gap: 0.75rem;
}

.panel {
  background: #fff;
  border: 1px solid #e2e8f0;
  border-radius: 14px;
  padding: 1rem;
}

.filters-grid,
.form-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 1rem;
}

.matrix-layout {
  display: grid;
  grid-template-columns: minmax(0, 1.4fr) minmax(320px, 0.9fr);
  gap: 1.25rem;
}

.side-panel {
  align-self: start;
}

.field {
  display: flex;
  flex-direction: column;
  gap: 0.35rem;
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
  border: 1px solid #cbd5e1;
  border-radius: 10px;
  padding: 0.75rem 0.85rem;
  font: inherit;
  background: #fff;
  box-sizing: border-box;
}

.field textarea {
  resize: vertical;
}

.field-full {
  grid-column: 1 / -1;
}

.primary-button,
.secondary-button {
  border-radius: 10px;
  padding: 0.75rem 1rem;
  font: inherit;
  cursor: pointer;
  border: 1px solid transparent;
}

.primary-button {
  background: #0f172a;
  color: #fff;
}

.secondary-button {
  background: #e2e8f0;
  color: #0f172a;
}

.count-badge {
  min-width: 2rem;
  text-align: center;
  padding: 0.35rem 0.65rem;
  border-radius: 999px;
  background: #e2e8f0;
  color: #0f172a;
  font-weight: 700;
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
  padding: 0.9rem 0.75rem;
  border-top: 1px solid #e2e8f0;
  text-align: left;
  vertical-align: top;
}

.data-table th {
  color: #475569;
  font-size: 0.9rem;
  font-weight: 700;
}

.table-row-link {
  cursor: pointer;
}

.table-row-link:hover {
  background: #f8fafc;
}

.status-pill {
  display: inline-flex;
  align-items: center;
  border-radius: 999px;
  background: #eff6ff;
  color: #1d4ed8;
  padding: 0.25rem 0.55rem;
  font-size: 0.85rem;
  font-weight: 600;
}

.detail-list {
  display: grid;
  grid-template-columns: 1fr;
  gap: 0.9rem;
  margin: 0 0 1rem;
}

.detail-list dt {
  font-size: 0.85rem;
  color: #64748b;
  margin-bottom: 0.25rem;
}

.detail-list dd {
  margin: 0;
  color: #0f172a;
}

.detail-full {
  grid-column: 1 / -1;
}

.evidence-section {
  margin-top: 1rem;
  border-top: 1px solid #e2e8f0;
  padding-top: 1rem;
}

.evidence-section h3 {
  margin: 0 0 0.75rem;
}

.evidence-list {
  margin: 0;
  padding-left: 1.2rem;
}

.evidence-list li {
  margin-bottom: 0.6rem;
}

.evidence-meta {
  display: block;
  color: #64748b;
  font-size: 0.9rem;
}

.mono {
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
  word-break: break-all;
}

.loading-state,
.empty-state,
.error-text,
.success-text {
  padding: 0.75rem 0;
}

.small {
  padding: 0.25rem 0;
}

.error-text {
  color: #b91c1c;
}

.success-text {
  color: #15803d;
}

@media (max-width: 1100px) {
  .matrix-layout {
    grid-template-columns: 1fr;
  }

  .filters-grid,
  .form-grid {
    grid-template-columns: 1fr;
  }

  .page-header,
  .panel-header,
  .header-actions,
  .form-actions {
    flex-direction: column;
    align-items: stretch;
  }
}
</style>