<template>
  <section class="annex-page">
    <header class="hero card">
      <div class="hero-copy">
        <p class="eyebrow">Annex I compliance matrix</p>
        <h1>Requirement coverage by product</h1>
        <p class="hero-text">
          Select a product, review every CRA Annex I requirement, and trace each one to risk items,
          rationale, and supporting artifacts.
        </p>
      </div>

      <div class="hero-actions">
        <button class="button secondary" type="button" :disabled="loading" @click="resetFilters">
          Reset filters
        </button>
        <button
          class="button"
          type="button"
          :disabled="loading || !selectedProductId"
          @click="loadMatrix"
        >
          {{ loading ? "Refreshing..." : "Refresh matrix" }}
        </button>
      </div>
    </header>

    <transition name="fade">
      <div v-if="errorMessage" class="alert error" role="alert">{{ errorMessage }}</div>
    </transition>
    <transition name="fade">
      <div v-if="successMessage" class="alert success" role="status">{{ successMessage }}</div>
    </transition>

    <section class="controls-grid">
      <article class="card selector-card">
        <div class="section-heading">
          <div>
            <h2>Product scope</h2>
            <p class="muted">Search by name or product code, then load one matrix at a time.</p>
          </div>
        </div>

        <div class="selector-grid">
          <label class="field">
            <span>Search products</span>
            <input
              v-model.trim="productQuery"
              class="input"
              type="search"
              placeholder="Search by product name or code"
            />
          </label>

          <label class="field">
            <span>Select product</span>
            <select v-model="selectedProductId" class="select">
              <option value="">Choose a product</option>
              <option v-for="product in filteredProducts" :key="product.id" :value="product.id">
                {{ product.name }} · {{ product.product_code }}
              </option>
            </select>
          </label>
        </div>
      </article>

      <article class="card filter-card">
        <div class="section-heading">
          <div>
            <h2>Filter matrix</h2>
            <p class="muted">Narrow the requirement list without losing the complete product view.</p>
          </div>
        </div>

        <div class="selector-grid">
          <label class="field">
            <span>Annex part</span>
            <select v-model="filters.annexPart" class="select">
              <option value="">All parts</option>
              <option value="part_i">Part I</option>
              <option value="part_ii">Part II</option>
            </select>
          </label>

          <label class="field">
            <span>Status</span>
            <select v-model="filters.status" class="select">
              <option value="">All statuses</option>
              <option v-for="status in implementationStatuses" :key="status" :value="status">
                {{ formatLabel(status) }}
              </option>
            </select>
          </label>

          <label class="field field-full">
            <span>Search requirements</span>
            <input
              v-model.trim="filters.search"
              class="input"
              type="search"
              placeholder="Search requirement text, risk title, engineering ref, notes, or artifacts"
            />
          </label>
        </div>
      </article>
    </section>

    <section v-if="selectedProduct" class="matrix-layout">
      <article class="card matrix-card">
        <div class="section-heading">
          <div>
            <h2>{{ selectedProduct.name }}</h2>
            <p class="muted">
              {{ filteredRows.length }} requirement{{ filteredRows.length === 1 ? "" : "s" }} shown ·
              {{ stats.verified }} verified ·
              {{ stats.needsDecision }} need decision
            </p>
          </div>
        </div>

        <div v-if="loading" class="state-block">
          <div v-for="i in 7" :key="i" class="skeleton-row"></div>
        </div>

        <div v-else-if="filteredRows.length === 0" class="state-block">
          <h3>No requirements match these filters</h3>
          <p class="muted">Try changing the search term or status filter.</p>
        </div>

        <div v-else class="matrix-list">
          <button
            v-for="row in filteredRows"
            :key="row.annex_requirement.id"
            type="button"
            class="matrix-row"
            :class="{ active: selectedRequirementId === row.annex_requirement.id }"
            @click="selectRow(row)"
          >
            <div class="row-main">
              <div class="row-title-wrap">
                <span class="requirement-code">{{ row.annex_requirement.code }}</span>
                <strong>{{ row.annex_requirement.title }}</strong>
              </div>
              <p class="row-description">{{ row.annex_requirement.description }}</p>
            </div>

            <div class="row-meta">
              <span class="meta-pill" :class="`app-${row.applicability}`">
                {{ formatApplicability(row.applicability) }}
              </span>
              <span
                class="meta-pill"
                :class="row.overall_status ? `status-${row.overall_status}` : 'status-empty'"
              >
                {{ row.overall_status ? formatLabel(row.overall_status) : "No trace record" }}
              </span>
              <span class="mini-stat">{{ row.risk_items.length }} risks</span>
              <span class="mini-stat">{{ row.artifacts.length }} artifacts</span>
            </div>
          </button>
        </div>
      </article>

      <aside class="card detail-card">
        <div v-if="!selectedRow" class="state-block">
          <h3>Select a requirement</h3>
          <p class="muted">
            Pick a row from the matrix to review traceability, add rationale, and link artifacts.
          </p>
        </div>

        <template v-else>
          <div class="detail-header">
            <div>
              <p class="eyebrow">{{ selectedRow.annex_requirement.code }}</p>
              <h2>{{ selectedRow.annex_requirement.title }}</h2>
            </div>
            <span
              class="meta-pill"
              :class="selectedRow.overall_status ? `status-${selectedRow.overall_status}` : 'status-empty'"
            >
              {{ selectedRow.overall_status ? formatLabel(selectedRow.overall_status) : "Unmapped" }}
            </span>
          </div>

          <p class="detail-description">{{ selectedRow.annex_requirement.description }}</p>

          <div class="summary-bar">
            <span class="meta-pill" :class="`app-${selectedRow.applicability}`">
              {{ formatApplicability(selectedRow.applicability) }}
            </span>
            <span class="mini-stat">
              Decision: {{ formatApplicabilityDecision(selectedRow.applicability_decision) }}
            </span>
            <span class="mini-stat">{{ formatTraceability(selectedRow.traceability_strength) }}</span>
            <span class="mini-stat">{{ selectedRow.risk_items.length }} risk links</span>
            <span class="mini-stat">{{ selectedRow.artifacts.length }} artifacts</span>
          </div>

          <section class="detail-section">
            <div class="section-heading tight">
              <div>
                <h3>Applicability decision</h3>
                <p class="muted">Decide explicitly whether this requirement applies to the selected product.</p>
              </div>
            </div>
            <form class="editor-grid" @submit.prevent="saveApplicabilityDecision">
              <label class="field">
                <span>Decision</span>
                <select v-model="applicabilityForm.applicability_decision" class="select">
                  <option v-for="option in applicabilityDecisions" :key="option" :value="option">
                    {{ formatApplicabilityDecision(option) }}
                  </option>
                </select>
              </label>

              <label class="field field-full">
                <span>Rationale</span>
                <textarea
                  v-model.trim="applicabilityForm.rationale"
                  class="textarea"
                  rows="3"
                  placeholder="Explain why this requirement applies or why it is not applicable for this product."
                />
              </label>

              <div class="editor-actions">
                <button class="button" type="submit" :disabled="busy">
                  {{ busy ? "Saving..." : "Save decision" }}
                </button>
              </div>
            </form>
          </section>

          <section class="detail-section">
            <div class="section-heading tight">
              <div>
                <h3>Linked risks</h3>
              </div>
            </div>
            <div v-if="selectedRow.risk_items.length === 0" class="state-block compact">
              <p class="muted">No risk items linked yet.</p>
            </div>
            <div v-else class="compact-list">
              <article v-for="risk in selectedRow.risk_items" :key="risk.id" class="compact-item">
                <strong>{{ risk.title }}</strong>
                <span class="muted">{{ formatLabel(risk.risk_level) }} · {{ formatLabel(risk.status) }}</span>
              </article>
            </div>
          </section>

          <section class="detail-section">
            <div class="section-heading tight">
              <div>
                <h3>Linked artifacts</h3>
              </div>
            </div>
            <div v-if="selectedRow.artifacts.length === 0" class="state-block compact">
              <p class="muted">No artifacts linked yet.</p>
            </div>
            <div v-else class="compact-list">
              <article
                v-for="artifact in selectedRow.artifacts"
                :key="artifact.id"
                class="compact-item compact-item-actions"
              >
                <div class="artifact-info">
                  <strong>{{ artifact.title }}</strong>
                  <span class="muted">{{ formatLabel(artifact.artifact_type) }}</span>
                </div>
                <div class="artifact-actions-inline">
                  <button
                    v-if="artifact.latest_revision?.storage_path"
                    class="button secondary small-button"
                    type="button"
                    @click="downloadArtifact(artifact)"
                  >
                    Download
                  </button>
                  <a
                    v-else-if="artifact.latest_revision?.external_url"
                    class="button secondary small-button link-button"
                    :href="artifact.latest_revision.external_url"
                    target="_blank"
                    rel="noreferrer"
                  >
                    Open
                  </a>
                </div>
              </article>
            </div>
          </section>

          <section class="trace-section">
            <div class="section-heading tight">
              <div>
                <h3>Trace records</h3>
                <p class="muted">
                  One requirement can map to multiple risk items, justifications, and artifacts.
                </p>
              </div>
              <button class="button secondary" type="button" @click="startCreateTrace">
                New trace record
              </button>
            </div>

            <div
              v-if="!selectedRow.artifact_traceability_available"
              class="alert warning"
              role="status"
            >
              Artifact linking is temporarily unavailable because the database migration for
              requirement-to-artifact links has not been applied yet. The matrix still works for
              risk-based trace records and justification notes.
            </div>

            <div v-if="selectedRow.trace_records.length === 0" class="state-block compact">
              <h4>No trace record yet</h4>
              <p class="muted">
                Create a trace record to show fulfillment or justify why this requirement is not
                applicable for the selected product.
              </p>
            </div>

            <div v-else class="trace-list">
              <article
                v-for="trace in selectedRow.trace_records"
                :key="trace.id"
                class="trace-card"
                :class="{ selected: selectedTraceId === trace.id }"
              >
                <button class="trace-top" type="button" @click="editTrace(trace)">
                  <div>
                    <strong>{{ trace.risk_item?.title || "Direct requirement rationale" }}</strong>
                    <p class="trace-subline">
                      {{ formatLabel(trace.implementation_status) }} ·
                      {{ formatLabel(trace.sdl_activity) }}
                      <span v-if="trace.engineering_requirement_ref">
                        · {{ trace.engineering_requirement_ref }}
                      </span>
                    </p>
                  </div>
                </button>

                <p v-if="trace.evidence_summary" class="trace-notes">{{ trace.evidence_summary }}</p>

                <div class="artifact-strip">
                  <article
                    v-for="artifact in trace.artifacts"
                    :key="artifact.id"
                    class="artifact-card"
                  >
                    <div class="artifact-info">
                      <strong>{{ artifact.title }}</strong>
                      <small>{{ formatLabel(artifact.artifact_type) }}</small>
                    </div>
                    <div class="artifact-actions-inline">
                      <button
                        v-if="artifact.latest_revision?.storage_path"
                        class="button secondary small-button"
                        type="button"
                        @click="downloadArtifact(artifact)"
                      >
                        Download
                      </button>
                      <a
                        v-else-if="artifact.latest_revision?.external_url"
                        class="button secondary small-button link-button"
                        :href="artifact.latest_revision.external_url"
                        target="_blank"
                        rel="noreferrer"
                      >
                        Open
                      </a>
                    </div>
                  </article>
                </div>

                <div class="trace-actions">
                  <button
                    class="button secondary"
                    type="button"
                    :disabled="busy"
                    @click="editTrace(trace)"
                  >
                    Edit
                  </button>
                  <button
                    class="button danger"
                    type="button"
                    :disabled="busy"
                    @click="removeTrace(trace.id)"
                  >
                    Delete
                  </button>
                </div>
              </article>
            </div>
          </section>

          <section class="editor-card">
            <div class="section-heading tight">
              <div>
                <h3>{{ editingExisting ? "Edit trace record" : "Create trace record" }}</h3>
                <p class="muted">
                  Use notes to record implementation rationale or not-applicable justification.
                </p>
              </div>
            </div>

            <form class="editor-grid" @submit.prevent="saveTrace">
              <label class="field">
                <span>Risk item</span>
                <select v-model="traceForm.risk_item_id" class="select">
                  <option value="">Select a risk item</option>
                  <option v-for="risk in productRiskItems" :key="risk.id" :value="risk.id">
                    {{ risk.title }} · {{ formatLabel(risk.risk_level) }}
                  </option>
                </select>
              </label>

              <label class="field">
                <span>Implementation status</span>
                <select v-model="traceForm.implementation_status" class="select">
                  <option v-for="status in implementationStatuses" :key="status" :value="status">
                    {{ formatLabel(status) }}
                  </option>
                </select>
              </label>

              <label class="field">
                <span>SDL activity</span>
                <select v-model="traceForm.sdl_activity" class="select">
                  <option v-for="activity in sdlActivities" :key="activity" :value="activity">
                    {{ formatLabel(activity) }}
                  </option>
                </select>
              </label>

              <label class="field">
                <span>Engineering reference</span>
                <input
                  v-model.trim="traceForm.engineering_requirement_ref"
                  class="input"
                  type="text"
                  placeholder="e.g. ENG-SEC-014"
                />
              </label>

              <label class="field field-full">
                <span>Traceability notes / justification</span>
                <textarea
                  v-model.trim="traceForm.evidence_summary"
                  class="textarea"
                  rows="5"
                  placeholder="Explain how this requirement is fulfilled, or justify why it is not applicable based on risk."
                />
              </label>

              <div class="field field-full">
                <span>Supporting artifacts</span>
                <div
                  v-if="!selectedRow.artifact_traceability_available"
                  class="artifact-selection-note"
                >
                  Apply the latest migration to select artifacts directly from the trace editor.
                </div>
                <div v-else-if="productArtifacts.length === 0" class="artifact-selection-note">
                  No product artifacts found yet. Attach artifacts in the release workflow first.
                </div>
                <div v-else class="artifact-selector-grid">
                  <label
                    v-for="artifact in productArtifacts"
                    :key="`editor-${artifact.id}`"
                    class="artifact-option"
                    :class="{ selected: traceForm.artifact_ids.includes(artifact.id) }"
                  >
                    <input
                      type="checkbox"
                      :checked="traceForm.artifact_ids.includes(artifact.id)"
                      :disabled="busy"
                      @change="toggleTraceArtifact(artifact.id)"
                    />
                    <div class="artifact-option-copy">
                      <strong>{{ artifact.title }}</strong>
                      <span>{{ formatLabel(artifact.artifact_type) }}</span>
                    </div>
                  </label>
                </div>
              </div>

              <div class="editor-actions">
                <button class="button" type="submit" :disabled="busy || !selectedRow">
                  {{ busy ? "Saving..." : editingExisting ? "Save changes" : "Create trace record" }}
                </button>
                <button class="button secondary" type="button" :disabled="busy" @click="resetEditor">
                  Clear editor
                </button>
              </div>
            </form>
          </section>
        </template>
      </aside>
    </section>

    <section v-else class="card state-block">
      <h2>Select a product to start</h2>
      <p class="muted">
        The matrix is now product-scoped, not release-scoped, so each product can be assessed
        against every Annex I requirement in one place.
      </p>
    </section>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref, watch } from "vue";

import { artifactService } from "@/services/artifact-service";
import { productService } from "@/services/product-service";
import { requirementMappingService } from "@/services/requirement-mapping-service";
import { riskAssessmentService } from "@/services/risk-assessment-service";
import { riskItemService } from "@/services/risk-item-service";
import type { AnnexPart } from "@/types/annex-requirement";
import type { ArtifactListRead } from "@/types/artifact";
import type { ProductSummaryRead } from "@/types/product";
import type {
  ProductRequirementDecisionUpdate,
  ProductRequirementMatrixRowRead,
  RequirementApplicabilityDecision,
  RequirementImplementationStatus,
  RequirementMappingCreate,
  RequirementMappingMatrixRead,
  RequirementMappingUpdate,
  SdlActivity,
} from "@/types/requirement-mapping";
import type { RiskItemRead } from "@/types/risk-item";

const loading = ref(false);
const busy = ref(false);
const errorMessage = ref("");
const successMessage = ref("");

const products = ref<ProductSummaryRead[]>([]);
const matrixRows = ref<ProductRequirementMatrixRowRead[]>([]);
const productRiskItems = ref<RiskItemRead[]>([]);
const productArtifacts = ref<ArtifactListRead[]>([]);

const productQuery = ref("");
const selectedProductId = ref("");
const selectedRequirementId = ref("");
const selectedTraceId = ref("");

const filters = reactive({
  annexPart: "" as AnnexPart | "",
  status: "" as RequirementImplementationStatus | "",
  search: "",
});

const traceForm = reactive({
  id: "",
  risk_item_id: "",
  implementation_status: "planned" as RequirementImplementationStatus,
  sdl_activity: "requirements" as SdlActivity,
  engineering_requirement_ref: "",
  evidence_summary: "",
  artifact_ids: [] as string[],
});

const applicabilityForm = reactive({
  applicability_decision: "undecided" as RequirementApplicabilityDecision,
  rationale: "",
});

const implementationStatuses: RequirementImplementationStatus[] = [
  "planned",
  "in_progress",
  "implemented",
  "verified",
  "not_applicable",
];

const applicabilityDecisions: RequirementApplicabilityDecision[] = [
  "undecided",
  "applicable",
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

const filteredProducts = computed(() => {
  const term = productQuery.value.trim().toLowerCase();
  if (!term) return products.value;
  return products.value.filter((product) =>
    [product.name, product.product_code].some((value) => value.toLowerCase().includes(term)),
  );
});

const selectedProduct = computed(
  () => products.value.find((product) => product.id === selectedProductId.value) ?? null,
);

const filteredRows = computed(() => {
  const term = filters.search.trim().toLowerCase();
  return [...matrixRows.value]
    .sort((a, b) => compareRequirementCodes(a.annex_requirement.code, b.annex_requirement.code))
    .filter((row) => {
      if (filters.annexPart && row.annex_requirement.annex_part !== filters.annexPart) {
        return false;
      }
      if (filters.status && row.overall_status !== filters.status) {
        return false;
      }
      if (!term) return true;

      const haystack = [
        row.annex_requirement.code,
        row.annex_requirement.title,
        row.annex_requirement.description,
        ...row.risk_items.map((risk) => risk.title),
        ...row.artifacts.map((artifact) => artifact.title),
        ...row.engineering_requirement_refs,
        ...row.notes,
      ]
        .join(" ")
        .toLowerCase();

      return haystack.includes(term);
    });
});

const selectedRow = computed(
  () => filteredRows.value.find((row) => row.annex_requirement.id === selectedRequirementId.value)
    ?? matrixRows.value.find((row) => row.annex_requirement.id === selectedRequirementId.value)
    ?? null,
);

const editingExisting = computed(() => Boolean(traceForm.id));

const stats = computed(() => ({
  verified: filteredRows.value.filter((row) => row.overall_status === "verified").length,
  needsDecision: filteredRows.value.filter((row) => row.applicability === "needs_decision").length,
  traceGaps: filteredRows.value.filter((row) => row.traceability_strength !== "complete").length,
}));

function compareRequirementCodes(a: string, b: string): number {
  const aMatch = a.match(/PART-(I|II)-(\d+)/);
  const bMatch = b.match(/PART-(I|II)-(\d+)/);
  if (!aMatch || !bMatch) return a.localeCompare(b);
  const partDiff = aMatch[1].localeCompare(bMatch[1]);
  if (partDiff !== 0) return partDiff;
  return Number(aMatch[2]) - Number(bMatch[2]);
}

function formatLabel(value?: string | null): string {
  if (!value) return "—";
  return value
    .split("_")
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(" ");
}

function formatApplicability(value: ProductRequirementMatrixRowRead["applicability"]): string {
  if (value === "not_applicable") return "Not applicable";
  if (value === "applicable") return "Applicable";
  return "Needs decision";
}

function formatApplicabilityDecision(value: RequirementApplicabilityDecision): string {
  return formatLabel(value);
}

function formatTraceability(value: ProductRequirementMatrixRowRead["traceability_strength"]): string {
  if (value === "complete") return "Risk + artifact";
  if (value === "partial") return "Partially traced";
  if (value === "weak") return "Weak traceability";
  return "No trace";
}

function resetFilters(): void {
  filters.annexPart = "";
  filters.status = "";
  filters.search = "";
}

function resetEditor(): void {
  traceForm.id = "";
  traceForm.risk_item_id = "";
  traceForm.implementation_status = "planned";
  traceForm.sdl_activity = "requirements";
  traceForm.engineering_requirement_ref = "";
  traceForm.evidence_summary = "";
  traceForm.artifact_ids = [];
  applicabilityForm.applicability_decision = "undecided";
  applicabilityForm.rationale = "";
  selectedTraceId.value = "";
}

function selectRow(row: ProductRequirementMatrixRowRead): void {
  selectedRequirementId.value = row.annex_requirement.id;
  applicabilityForm.applicability_decision = row.applicability_decision;
  applicabilityForm.rationale = row.applicability_rationale ?? "";
  if (row.trace_records.length > 0) {
    const matchingTrace =
      row.trace_records.find((trace) => trace.id === selectedTraceId.value) ?? row.trace_records[0];
    editTrace(matchingTrace);
    return;
  }
  resetEditor();
}

function startCreateTrace(): void {
  resetEditor();
}

function editTrace(trace: RequirementMappingMatrixRead): void {
  selectedTraceId.value = trace.id;
  traceForm.id = trace.id;
  traceForm.risk_item_id = trace.risk_item_id ?? "";
  traceForm.implementation_status = trace.implementation_status;
  traceForm.sdl_activity = trace.sdl_activity;
  traceForm.engineering_requirement_ref = trace.engineering_requirement_ref ?? "";
  traceForm.evidence_summary = trace.evidence_summary ?? "";
  traceForm.artifact_ids = trace.artifacts.map((artifact) => artifact.id);
}

function toggleTraceArtifact(artifactId: string): void {
  if (traceForm.artifact_ids.includes(artifactId)) {
    traceForm.artifact_ids = traceForm.artifact_ids.filter((id) => id !== artifactId);
    return;
  }
  traceForm.artifact_ids = [...traceForm.artifact_ids, artifactId];
}

async function loadProducts(): Promise<void> {
  products.value = await productService.list();
}

async function loadProductContext(productId: string): Promise<void> {
  const [rows, assessments, artifacts] = await Promise.all([
    requirementMappingService.productMatrix(productId),
    riskAssessmentService.list({ product_id: productId }),
    artifactService.list({ product_id: productId }),
  ]);

  matrixRows.value = rows;
  productArtifacts.value = artifacts;

  const riskLists = await Promise.all(
    assessments.map((assessment) => riskItemService.listByAssessment(assessment.id)),
  );
  productRiskItems.value = riskLists.flat();

  const activeRow =
    rows.find((row) => row.annex_requirement.id === selectedRequirementId.value) ?? rows[0] ?? null;
  if (activeRow) {
    selectRow(activeRow);
  } else {
    selectedRequirementId.value = "";
    resetEditor();
  }
}

async function loadMatrix(): Promise<void> {
  if (!selectedProductId.value) {
    matrixRows.value = [];
    productRiskItems.value = [];
    productArtifacts.value = [];
    selectedRequirementId.value = "";
    resetEditor();
    return;
  }

  loading.value = true;
  errorMessage.value = "";
  successMessage.value = "";

  try {
    await loadProductContext(selectedProductId.value);
  } catch (error: any) {
    errorMessage.value = error?.message ?? "Failed to load Annex I matrix.";
  } finally {
    loading.value = false;
  }
}

async function saveTrace(): Promise<void> {
  if (!selectedRow.value) return;
  if (!traceForm.risk_item_id) {
    errorMessage.value = "Select a product risk item so the trace record stays linked to this product.";
    return;
  }

  busy.value = true;
  errorMessage.value = "";
  successMessage.value = "";

  try {
    let savedTraceId = traceForm.id;
    const existingArtifactIds = editingExisting.value
      ? selectedRow.value.trace_records.find((trace) => trace.id === traceForm.id)?.artifacts.map((artifact) => artifact.id) ?? []
      : [];

    if (editingExisting.value) {
      const payload: RequirementMappingUpdate = {
        risk_item_id: traceForm.risk_item_id || null,
        engineering_requirement_ref: traceForm.engineering_requirement_ref || null,
        implementation_status: traceForm.implementation_status,
        sdl_activity: traceForm.sdl_activity,
        evidence_summary: traceForm.evidence_summary || null,
      };
      const updated = await requirementMappingService.update(traceForm.id, payload);
      savedTraceId = updated.id;
      successMessage.value = "Trace record updated.";
    } else {
      const payload: RequirementMappingCreate = {
        annex_requirement_id: selectedRow.value.annex_requirement.id,
        risk_item_id: traceForm.risk_item_id || null,
        engineering_requirement_ref: traceForm.engineering_requirement_ref || null,
        implementation_status: traceForm.implementation_status,
        sdl_activity: traceForm.sdl_activity,
        evidence_summary: traceForm.evidence_summary || null,
      };
      const created = await requirementMappingService.create(payload);
      savedTraceId = created.id;
      successMessage.value = "Trace record created.";
    }

    if (selectedRow.value.artifact_traceability_available && savedTraceId) {
      await syncTraceArtifacts(savedTraceId, existingArtifactIds, traceForm.artifact_ids);
    }

    await loadMatrix();
  } catch (error: any) {
    errorMessage.value = error?.message ?? "Failed to save trace record.";
  } finally {
    busy.value = false;
  }
}

async function removeTrace(traceId: string): Promise<void> {
  busy.value = true;
  errorMessage.value = "";
  successMessage.value = "";
  try {
    await requirementMappingService.remove(traceId);
    successMessage.value = "Trace record deleted.";
    await loadMatrix();
  } catch (error: any) {
    errorMessage.value = error?.message ?? "Failed to delete trace record.";
  } finally {
    busy.value = false;
  }
}

async function syncTraceArtifacts(
  traceId: string,
  existingArtifactIds: string[],
  desiredArtifactIds: string[],
): Promise<void> {
  const existing = new Set(existingArtifactIds);
  const desired = new Set(desiredArtifactIds);

  for (const artifactId of desiredArtifactIds) {
    if (!existing.has(artifactId)) {
      await requirementMappingService.attachArtifact(traceId, { artifact_id: artifactId });
    }
  }

  for (const artifactId of existingArtifactIds) {
    if (!desired.has(artifactId)) {
      await requirementMappingService.detachArtifact(traceId, artifactId);
    }
  }
}

async function downloadArtifact(artifact: ArtifactListRead): Promise<void> {
  const revision = artifact.latest_revision;
  if (!revision?.id || !revision.storage_path) return;

  errorMessage.value = "";
  try {
    await artifactService.downloadRevision(
      revision.id,
      revision.original_filename || artifact.title || "artifact",
    );
  } catch (error: any) {
    errorMessage.value = error?.message ?? "Failed to download artifact.";
  }
}

async function saveApplicabilityDecision(): Promise<void> {
  if (!selectedRow.value || !selectedProductId.value) return;

  busy.value = true;
  errorMessage.value = "";
  successMessage.value = "";
  try {
    const payload: ProductRequirementDecisionUpdate = {
      applicability_decision: applicabilityForm.applicability_decision,
      rationale: applicabilityForm.rationale.trim() || null,
    };
    await requirementMappingService.updateProductRequirementDecision(
      selectedProductId.value,
      selectedRow.value.annex_requirement.id,
      payload,
    );
    successMessage.value = "Applicability decision saved.";
    await loadMatrix();
  } catch (error: any) {
    errorMessage.value = error?.message ?? "Failed to save applicability decision.";
  } finally {
    busy.value = false;
  }
}

watch(selectedProductId, async () => {
  resetEditor();
  await loadMatrix();
});

onMounted(async () => {
  try {
    await loadProducts();
  } catch (error: any) {
    errorMessage.value = error?.message ?? "Failed to load products.";
  }
});
</script>

<style scoped>
.annex-page {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.hero {
  display: flex;
  justify-content: space-between;
  gap: 1.5rem;
  flex-wrap: wrap;
  padding: 1.4rem;
  background:
    radial-gradient(circle at top left, rgba(110, 168, 254, 0.24), transparent 38%),
    linear-gradient(145deg, rgba(255, 255, 255, 0.08), rgba(255, 255, 255, 0.03));
}

.hero-copy {
  max-width: 56rem;
}

.hero-copy h1,
.detail-header h2,
.section-heading h2,
.section-heading h3 {
  margin: 0;
}

.hero-text,
.detail-description,
.row-description,
.trace-notes,
.trace-subline {
  color: var(--color-text-muted);
}

.eyebrow {
  margin: 0 0 0.35rem;
  text-transform: uppercase;
  letter-spacing: 0.12em;
  font-size: 0.74rem;
  color: var(--color-primary);
  font-weight: 700;
}

.hero-actions,
.editor-actions,
.trace-actions {
  display: flex;
  gap: 0.75rem;
  flex-wrap: wrap;
  align-items: end;
}

.controls-grid,
.matrix-layout,
.selector-grid,
.editor-grid {
  display: grid;
  gap: 1rem;
}

.controls-grid {
  grid-template-columns: 1.15fr 1fr;
}

.selector-grid,
.editor-grid {
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

.matrix-layout {
  grid-template-columns: minmax(18rem, 24rem) minmax(0, 1fr);
  align-items: start;
}

.section-heading {
  display: flex;
  justify-content: space-between;
  gap: 1rem;
  align-items: start;
  margin-bottom: 1rem;
}

.section-heading.tight {
  margin-bottom: 0.85rem;
}

.field {
  display: flex;
  flex-direction: column;
  gap: 0.45rem;
}

.field span {
  font-size: 0.85rem;
  color: var(--color-text-muted);
}

.field-full {
  grid-column: 1 / -1;
}

.matrix-list,
.trace-list {
  display: flex;
  flex-direction: column;
  gap: 0.85rem;
}

.matrix-row {
  width: 100%;
  border: 1px solid rgba(233, 238, 252, 0.08);
  background: rgba(255, 255, 255, 0.03);
  color: inherit;
  border-radius: 16px;
  padding: 1rem;
  display: grid;
  gap: 0.85rem;
  cursor: pointer;
  transition: border-color 0.12s ease, transform 0.12s ease, background 0.12s ease;
  text-align: left;
}

.matrix-row:hover,
.matrix-row.active,
.trace-card.selected {
  border-color: rgba(110, 168, 254, 0.42);
  background: rgba(110, 168, 254, 0.08);
  transform: translateY(-1px);
}

.row-title-wrap {
  display: flex;
  flex-direction: column;
  gap: 0.2rem;
}

.requirement-code {
  color: #9cc0ff;
  font-size: 0.8rem;
  font-weight: 700;
}

.row-description,
.detail-description {
  margin: 0.45rem 0 0;
  line-height: 1.55;
}

.row-meta {
  display: flex;
  gap: 0.6rem;
  flex-wrap: wrap;
  align-items: center;
}

.meta-pill,
.mini-stat {
  border-radius: 999px;
  border: 1px solid rgba(233, 238, 252, 0.1);
  padding: 0.38rem 0.7rem;
  font-size: 0.77rem;
}

.mini-stat {
  color: var(--color-text-muted);
  background: rgba(255, 255, 255, 0.03);
}

.detail-header {
  display: flex;
  justify-content: space-between;
  gap: 1rem;
  align-items: start;
}

.trace-section,
.editor-card {
  margin-top: 1.15rem;
}

.trace-card,
.editor-card {
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(233, 238, 252, 0.08);
  border-radius: 16px;
  padding: 1rem;
}

.detail-section,
.editor-card,
.trace-section {
  margin-top: 1rem;
}

.summary-bar {
  display: flex;
  gap: 0.6rem;
  flex-wrap: wrap;
  margin-top: 1rem;
}

.trace-top {
  width: 100%;
  border: 0;
  padding: 0;
  background: transparent;
  color: inherit;
  text-align: left;
  cursor: pointer;
}

.trace-subline,
.trace-notes {
  margin: 0.35rem 0 0;
}

.artifact-strip {
  display: flex;
  gap: 0.55rem;
  flex-wrap: wrap;
  margin-top: 0.85rem;
}

.artifact-card,
.compact-item {
  display: flex;
  justify-content: space-between;
  gap: 0.75rem;
  align-items: center;
  padding: 0.85rem 0.95rem;
  border-radius: 14px;
  border: 1px solid rgba(233, 238, 252, 0.1);
  background: rgba(255, 255, 255, 0.03);
}

.artifact-selector-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 0.75rem;
}

.artifact-option {
  display: flex;
  gap: 0.75rem;
  align-items: start;
  padding: 0.85rem 0.95rem;
  border-radius: 14px;
  border: 1px solid rgba(233, 238, 252, 0.1);
  background: rgba(255, 255, 255, 0.03);
  cursor: pointer;
}

.artifact-option.selected {
  border-color: rgba(110, 168, 254, 0.38);
  background: rgba(110, 168, 254, 0.08);
}

.artifact-option input {
  margin-top: 0.2rem;
}

.artifact-option-copy {
  display: flex;
  flex-direction: column;
  gap: 0.2rem;
}

.artifact-option-copy span,
.artifact-selection-note {
  color: var(--color-text-muted);
  font-size: 0.84rem;
}

.alert {
  border-radius: 14px;
  padding: 0.85rem 1rem;
  border: 1px solid transparent;
}

.alert.error {
  background: rgba(251, 113, 133, 0.12);
  border-color: rgba(251, 113, 133, 0.26);
  color: #fecdd3;
}

.alert.success {
  background: rgba(52, 211, 153, 0.12);
  border-color: rgba(52, 211, 153, 0.26);
  color: #bbf7d0;
}

.alert.warning {
  background: rgba(251, 191, 36, 0.12);
  border-color: rgba(251, 191, 36, 0.26);
  color: #fde68a;
}

.state-block {
  border: 1px dashed rgba(233, 238, 252, 0.14);
  border-radius: 16px;
  padding: 1.2rem;
  background: rgba(255, 255, 255, 0.02);
}

.state-block.compact {
  padding: 1rem;
}

.skeleton-row {
  height: 5.2rem;
  border-radius: 16px;
  background:
    linear-gradient(90deg, rgba(255, 255, 255, 0.04), rgba(255, 255, 255, 0.08), rgba(255, 255, 255, 0.04));
  background-size: 200% 100%;
  animation: shimmer 1.4s linear infinite;
}

.app-applicable {
  background: rgba(96, 165, 250, 0.12);
  border-color: rgba(96, 165, 250, 0.24);
}

.app-not_applicable {
  background: rgba(251, 191, 36, 0.12);
  border-color: rgba(251, 191, 36, 0.26);
}

.app-needs_decision,
.status-empty {
  background: rgba(148, 163, 184, 0.14);
  border-color: rgba(148, 163, 184, 0.18);
}

.status-planned {
  background: rgba(250, 204, 21, 0.12);
  border-color: rgba(250, 204, 21, 0.22);
}

.status-in_progress {
  background: rgba(251, 146, 60, 0.12);
  border-color: rgba(251, 146, 60, 0.24);
}

.status-implemented {
  background: rgba(96, 165, 250, 0.12);
  border-color: rgba(96, 165, 250, 0.24);
}

.status-verified {
  background: rgba(52, 211, 153, 0.12);
  border-color: rgba(52, 211, 153, 0.26);
}

.status-not_applicable {
  background: rgba(217, 119, 6, 0.14);
  border-color: rgba(217, 119, 6, 0.24);
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.18s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

@keyframes shimmer {
  from {
    background-position: 200% 0;
  }
  to {
    background-position: -200% 0;
  }
}

@media (max-width: 1100px) {
  .controls-grid,
  .matrix-layout {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 720px) {
  .selector-grid,
  .editor-grid,
  .artifact-selector-grid {
    grid-template-columns: 1fr;
  }

  .hero,
  .detail-header,
  .section-heading {
    flex-direction: column;
  }
}

.compact-list {
  display: flex;
  flex-direction: column;
  gap: 0.7rem;
}

.compact-item {
  align-items: flex-start;
  flex-direction: column;
}

.compact-item-actions,
.artifact-card {
  align-items: center;
  flex-direction: row;
}

.artifact-info {
  display: flex;
  flex-direction: column;
  gap: 0.2rem;
  min-width: 0;
}

.artifact-actions-inline {
  display: flex;
  gap: 0.5rem;
  flex-wrap: wrap;
  flex-shrink: 0;
}

.small-button {
  padding: 0.45rem 0.75rem;
  border-radius: 10px;
}

.link-button {
  display: inline-flex;
  align-items: center;
}
</style>
