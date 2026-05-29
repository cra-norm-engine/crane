<template>
  <section class="annex-page">

    <!-- ── Header ────────────────────────────────────────── -->
    <header class="page-header">
      <div>
        <h1 class="page-title">CRA requirements</h1>
        <p class="muted">Select a product, review every CRA Annex I requirement, and trace each one to risk items, rationale, and supporting artifacts.</p>
      </div>
      <div class="page-actions">
        <AppButton variant="secondary" type="button" @click="showFilterModal = true">
          Filter matrix
          <span v-if="activeFilterCount > 0" class="filter-badge">{{ activeFilterCount }}</span>
        </AppButton>
      </div>
    </header>

    <!-- ── Alerts ─────────────────────────────────────────── -->
    <transition name="fade">
      <div v-if="errorMessage" class="alert error" role="alert">{{ errorMessage }}</div>
    </transition>
    <transition name="fade">
      <div v-if="successMessage" class="alert success" role="status">{{ successMessage }}</div>
    </transition>

    <!-- ── Product selector ───────────────────────────────── -->
    <article class="card selector-card">
      <div class="section-heading">
        <div>
          <h2 class="section-title">Product scope</h2>
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

        <label class="field field-full">
          <span>Select release <span class="field-hint">— requirement mappings are per release</span></span>
          <select
            v-model="selectedReleaseId"
            class="select"
            :disabled="!selectedProductId || productReleases.length === 0"
          >
            <option value="">Choose a release</option>
            <option v-for="rel in productReleases" :key="rel.id" :value="rel.id">
              v{{ rel.display_version }} · {{ formatLabel(rel.release_status) }}
            </option>
          </select>
        </label>
      </div>
    </article>

    <!-- ── Matrix list ─────────────────────────────────────── -->
    <section v-if="selectedProduct && selectedReleaseId" class="card matrix-card">
      <div class="section-heading">
        <div>
          <h2 class="section-title">{{ selectedProduct.name }}</h2>
          <p class="muted">
            v{{ selectedRelease?.display_version }} ·
            {{ filteredRows.length }} requirement{{ filteredRows.length === 1 ? "" : "s" }} shown ·
            {{ stats.verified }} verified · {{ stats.needsDecision }} need decision
          </p>
        </div>
        <span class="meta-pill release-status-pill" :class="`status-${selectedRelease?.release_status}`">
          {{ formatLabel(selectedRelease?.release_status) }}
        </span>
      </div>

      <!-- Coverage bar -->
      <div class="release-coverage-bar">
        <div class="coverage-numbers">
          <strong>{{ stats.verified }}</strong> / {{ filteredRows.length }} requirements verified
          <span class="coverage-pct" :class="coveragePct >= 80 ? 'pct-good' : coveragePct >= 40 ? 'pct-partial' : 'pct-low'">
            {{ coveragePct }}%
          </span>
        </div>
        <div class="progress-track">
          <div
            class="progress-fill"
            :class="coveragePct >= 80 ? 'fill-good' : coveragePct >= 40 ? 'fill-partial' : 'fill-low'"
            :style="{ width: `${coveragePct}%` }"
          />
        </div>
      </div>

      <!-- Loading skeleton -->
      <div v-if="loading" class="state-block">
        <div v-for="i in 7" :key="i" class="skeleton-row"></div>
      </div>

      <!-- Empty state -->
      <div v-else-if="filteredRows.length === 0" class="state-block">
        <h3>No requirements match these filters</h3>
        <p class="muted">Try changing the search term or status filter.</p>
      </div>

      <!-- Compact row list -->
      <div v-else class="matrix-list">
        <div
          v-for="row in filteredRows"
          :key="row.annex_requirement.id"
          class="matrix-row-wrapper"
        >
          <!-- Compact clickable row -->
          <button
            class="matrix-row"
            type="button"
            :class="{ active: selectedRequirementId === row.annex_requirement.id }"
            @click="openDetail(row)"
          >
            <!-- Code + title -->
            <div class="row-left">
              <span class="requirement-code">{{ row.annex_requirement.code }}</span>
              <strong class="row-title">{{ row.annex_requirement.title }}</strong>
            </div>

            <!-- Pills + expand button -->
            <div class="row-right">
              <span class="meta-pill" :class="`app-${row.applicability}`">
                {{ formatApplicability(row.applicability) }}
              </span>
              <span
                class="meta-pill"
                :class="row.overall_status ? `status-${row.overall_status}` : 'status-empty'"
              >
                {{ row.overall_status ? formatLabel(row.overall_status) : "Unmapped" }}
              </span>
              <span class="mini-stat">{{ row.risk_items.length }} risks</span>
              <span class="mini-stat">{{ row.artifacts.length }} artifacts</span>
              <span class="mini-stat">{{ row.trace_records.length }} traces</span>

              <!-- Expand-description toggle (does not open modal) -->
              <span
                class="expand-btn"
                role="button"
                tabindex="0"
                :title="expandedRowIds.has(row.annex_requirement.id) ? 'Collapse description' : 'Show description'"
                :aria-expanded="expandedRowIds.has(row.annex_requirement.id)"
                @click.stop="toggleExpand(row.annex_requirement.id)"
                @keydown.enter.stop.prevent="toggleExpand(row.annex_requirement.id)"
              >
                <svg
                  viewBox="0 0 16 16"
                  width="14"
                  height="14"
                  fill="none"
                  stroke="currentColor"
                  stroke-width="2"
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  aria-hidden="true"
                  :class="{ 'chevron-open': expandedRowIds.has(row.annex_requirement.id) }"
                >
                  <polyline points="3,5 8,11 13,5" />
                </svg>
              </span>
            </div>
          </button>

          <!-- Inline description panel (expand-in-place) -->
          <transition name="expand">
            <div
              v-if="expandedRowIds.has(row.annex_requirement.id)"
              class="row-description-panel"
            >
              <p>{{ row.annex_requirement.description }}</p>
            </div>
          </transition>
        </div>
      </div>
    </section>

    <!-- ── Empty product selection state ─────────────────── -->
    <section v-else class="card state-block">
      <h2 class="section-title">Select a product to start</h2>
      <p class="muted">
        Select a product and release to assess every CRA Annex I requirement for that specific version.
      </p>
    </section>

    <!-- ── Filter modal ────────────────────────────────────── -->
    <AppModal v-model="showFilterModal" title="Filter matrix" size="sm">
      <div class="filter-grid">
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
            <option value="unmapped">Unmapped</option>
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

      <template #footer>
        <AppButton
          variant="secondary"
          type="button"
          @click="resetFilters(); showFilterModal = false"
        >
          Clear all
        </AppButton>
        <AppButton variant="primary" type="button" @click="showFilterModal = false">Apply</AppButton>
      </template>
    </AppModal>

    <!-- ── Requirement detail modal ────────────────────────── -->
    <AppModal
      v-if="selectedRow"
      v-model="showDetailModal"
      :title="`${selectedRow.annex_requirement.code} — ${selectedRow.annex_requirement.title}`"
      size="lg"
    >
      <div class="detail-modal-body">

        <!-- Description -->
        <p class="detail-description">{{ selectedRow.annex_requirement.description }}</p>

        <!-- Summary bar -->
        <div class="summary-bar">
          <span class="meta-pill" :class="`app-${selectedRow.applicability}`">
            {{ formatApplicability(selectedRow.applicability) }}
          </span>
          <span
            class="meta-pill"
            :class="selectedRow.overall_status ? `status-${selectedRow.overall_status}` : 'status-empty'"
          >
            {{ selectedRow.overall_status ? formatLabel(selectedRow.overall_status) : "Unmapped" }}
          </span>
          <span class="mini-stat">Decision: {{ formatApplicabilityDecision(selectedRow.applicability_decision) }}</span>
          <span class="mini-stat">{{ formatTraceability(selectedRow.traceability_strength) }}</span>
          <span class="mini-stat">{{ selectedRow.risk_items.length }} risk links</span>
          <span class="mini-stat">{{ selectedRow.artifacts.length }} artifacts</span>
        </div>

        <!-- Applicability decision form -->
        <section class="detail-section">
          <div class="section-heading tight">
            <div>
              <h3 class="section-title">Applicability decision</h3>
              <p class="muted">Decide explicitly whether this requirement applies to the selected product.</p>
            </div>
          </div>
          <form id="applicability-form" class="editor-grid" @submit.prevent="saveApplicabilityDecision">
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
              <AppButton variant="primary" type="submit" :disabled="busy">
                {{ busy ? "Saving..." : "Save decision" }}
              </AppButton>
            </div>
          </form>
        </section>

        <!-- Linked risks -->
        <section class="detail-section">
          <div class="section-heading tight">
            <h3 class="section-title">Linked risks</h3>
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

        <!-- Linked artifacts -->
        <section class="detail-section">
          <div class="section-heading tight">
            <h3 class="section-title">Linked artifacts</h3>
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
                <AppButton
                  v-if="artifact.latest_revision?.storage_path"
                  variant="secondary"
                  size="sm"
                  @click="downloadArtifact(artifact)"
                >
                  Download
                </AppButton>
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

        <!-- Trace records -->
        <section class="trace-section">
          <div class="section-heading tight">
            <div>
              <h3 class="section-title">
                Trace records
                <span v-if="selectedReleaseId" class="release-scope-tag">
                  — v{{ selectedRelease?.display_version }} only
                </span>
              </h3>
              <p class="muted">
                <template v-if="selectedReleaseId">
                  Showing only records linked to risk items from this release's assessments.
                  <button class="link-btn" type="button" @click="selectedReleaseId = ''">Show all</button>
                </template>
                <template v-else>
                  One requirement can map to multiple risk items, justifications, and artifacts.
                </template>
              </p>
            </div>
            <AppButton variant="secondary" type="button" @click="startCreateTrace">
              New trace record
            </AppButton>
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
              applicable for the selected release.
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
                    <AppButton
                      v-if="artifact.latest_revision?.storage_path"
                      variant="secondary"
                      size="sm"
                      @click="downloadArtifact(artifact)"
                    >
                      Download
                    </AppButton>
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
                <AppButton
                  variant="secondary"
                  :disabled="busy"
                  @click="editTrace(trace)"
                >
                  Edit
                </AppButton>
                <AppButton
                  variant="danger"
                  :disabled="busy"
                  @click="removeTrace(trace.id)"
                >
                  Delete
                </AppButton>
              </div>
            </article>
          </div>
        </section>

        <!-- Trace record editor -->
        <section class="editor-card">
          <div class="section-heading tight">
            <div>
              <h3 class="section-title">{{ editingExisting ? "Edit trace record" : "Create trace record" }}</h3>
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
              <AppButton variant="primary" type="submit" :disabled="busy || !selectedRow">
                {{ busy ? "Saving..." : editingExisting ? "Save changes" : "Create trace record" }}
              </AppButton>
              <AppButton variant="secondary" type="button" :disabled="busy" @click="resetEditor">
                Clear editor
              </AppButton>
            </div>
          </form>
        </section>

      </div>
    </AppModal>

  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref, watch } from "vue";

import AppModal from "@/components/AppModal.vue";
import AppButton from "@/components/AppButton.vue";
import { artifactService } from "@/services/artifact-service";
import { productReleaseService } from "@/services/product-release-service";
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
import type { RiskAssessmentRead } from "@/types/risk-assessment";
import type { RiskItemRead, RiskItemSummaryRead } from "@/types/risk-item";
import type { ProductReleaseRead } from "@/types/release-gate";

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
const selectedReleaseId = ref("");
const selectedRequirementId = ref("");
const selectedTraceId = ref("");

/* ── Release-level data ───────────────────────────── */
const productReleases = ref<ProductReleaseRead[]>([]);

/* ── Modal visibility ─────────────────────────────── */
const showFilterModal = ref(false);
const showDetailModal = ref(false);

/* ── Expanded description rows ────────────────────── */
const expandedRowIds = ref(new Set<string>());

const filters = reactive({
  annexPart: "" as AnnexPart | "",
  /* "unmapped" is a UI-only sentinel for rows with no trace record */
  status: "" as RequirementImplementationStatus | "unmapped" | "",
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

/* ── Computed ─────────────────────────────────────── */

const filteredProducts = computed(() => {
  const term = productQuery.value.trim().toLowerCase();
  if (!term) return products.value;
  return products.value.filter((product: ProductSummaryRead) =>
    [product.name, product.product_code].some((value: string) => value.toLowerCase().includes(term)),
  );
});

const selectedProduct = computed(
  () => products.value.find((product: ProductSummaryRead) => product.id === selectedProductId.value) ?? null,
);

const filteredRows = computed(() => {
  const term = filters.search.trim().toLowerCase();
  return [...matrixRows.value]
    .sort((a: ProductRequirementMatrixRowRead, b: ProductRequirementMatrixRowRead) =>
      compareRequirementCodes(a.annex_requirement.code, b.annex_requirement.code),
    )
    .filter((row: ProductRequirementMatrixRowRead) => {
      if (filters.annexPart && row.annex_requirement.annex_part !== filters.annexPart) {
        return false;
      }
      /* "unmapped" = rows where no trace record exists yet */
      if (filters.status === "unmapped") {
        if (row.overall_status) return false;
      } else if (filters.status && row.overall_status !== filters.status) {
        return false;
      }
      if (!term) return true;

      const haystack = [
        row.annex_requirement.code,
        row.annex_requirement.title,
        row.annex_requirement.description,
        ...row.risk_items.map((risk: RiskItemSummaryRead) => risk.title),
        ...row.artifacts.map((artifact: ArtifactListRead) => artifact.title),
        ...row.engineering_requirement_refs,
        ...row.notes,
      ]
        .join(" ")
        .toLowerCase();

      return haystack.includes(term);
    });
});

const selectedRow = computed(
  () =>
    filteredRows.value.find((row: ProductRequirementMatrixRowRead) => row.annex_requirement.id === selectedRequirementId.value) ??
    matrixRows.value.find((row: ProductRequirementMatrixRowRead) => row.annex_requirement.id === selectedRequirementId.value) ??
    null,
);

const editingExisting = computed(() => Boolean(traceForm.id));

const stats = computed(() => ({
  verified: filteredRows.value.filter((row: ProductRequirementMatrixRowRead) => row.overall_status === "verified").length,
  needsDecision: filteredRows.value.filter((row: ProductRequirementMatrixRowRead) => row.applicability === "needs_decision").length,
  traceGaps: filteredRows.value.filter((row: ProductRequirementMatrixRowRead) => row.traceability_strength !== "complete").length,
}));

/** Number of active non-empty filters — shown as a badge on the Filter button. */
const activeFilterCount = computed(() => {
  let count = 0;
  if (filters.annexPart) count++;
  if (filters.status) count++;
  if (filters.search) count++;
  return count;
});

/** The selected release object, used for display. */
const selectedRelease = computed(
  () => productReleases.value.find((r: ProductReleaseRead) => r.id === selectedReleaseId.value) ?? null,
);

/** Percentage of visible requirements that are verified for the current release. */
const coveragePct = computed(() => {
  const total = filteredRows.value.length;
  if (total === 0) return 0;
  return Math.round((stats.value.verified / total) * 100);
});

/* ── Helpers ──────────────────────────────────────── */

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

/* ── UI interaction ───────────────────────────────── */

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

/** Toggle the inline description panel for a row without opening the detail modal. */
function toggleExpand(reqId: string): void {
  const next = new Set(expandedRowIds.value);
  if (next.has(reqId)) {
    next.delete(reqId);
  } else {
    next.add(reqId);
  }
  expandedRowIds.value = next;
}

/** Populate the detail forms from the selected row. */
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

/** Open the requirement detail modal for the given row. */
function openDetail(row: ProductRequirementMatrixRowRead): void {
  selectRow(row);
  showDetailModal.value = true;
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
    traceForm.artifact_ids = traceForm.artifact_ids.filter((id: string) => id !== artifactId);
    return;
  }
  traceForm.artifact_ids = [...traceForm.artifact_ids, artifactId];
}

/* ── Data loading ─────────────────────────────────── */

async function loadProducts(): Promise<void> {
  products.value = await productService.list();
}

async function loadProductContext(productId: string): Promise<void> {
  const [artifacts, releases] = await Promise.all([
    artifactService.list({ product_id: productId }),
    productReleaseService.list(productId),
  ]);
  productArtifacts.value = artifacts;
  productReleases.value = releases;
}

async function loadReleaseMatrix(releaseId: string): Promise<void> {
  const [rows, assessments] = await Promise.all([
    requirementMappingService.releaseMatrix(releaseId),
    riskAssessmentService.list({ product_id: selectedProductId.value }),
  ]);

  matrixRows.value = rows;

  const riskLists = await Promise.all(
    assessments.map((assessment: RiskAssessmentRead) => riskItemService.listByAssessment(assessment.id)),
  );
  productRiskItems.value = riskLists.flat();

  const activeRow =
    rows.find((row: ProductRequirementMatrixRowRead) => row.annex_requirement.id === selectedRequirementId.value) ?? rows[0] ?? null;
  if (activeRow) {
    selectRow(activeRow);
  } else {
    selectedRequirementId.value = "";
    resetEditor();
  }
}

async function loadMatrix(): Promise<void> {
  if (!selectedProductId.value || !selectedReleaseId.value) {
    matrixRows.value = [];
    productRiskItems.value = [];
    selectedRequirementId.value = "";
    resetEditor();
    return;
  }

  loading.value = true;
  errorMessage.value = "";
  successMessage.value = "";

  try {
    await loadReleaseMatrix(selectedReleaseId.value);
  } catch (error: any) {
    errorMessage.value = error?.message ?? "Failed to load Annex I matrix.";
  } finally {
    loading.value = false;
  }
}

/* ── Save / mutate ────────────────────────────────── */

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
      ? selectedRow.value.trace_records
          .find((trace: RequirementMappingMatrixRead) => trace.id === traceForm.id)
          ?.artifacts.map((artifact: ArtifactListRead) => artifact.id) ?? []
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
        product_release_id: selectedReleaseId.value,
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
  if (!selectedRow.value || !selectedReleaseId.value) return;

  busy.value = true;
  errorMessage.value = "";
  successMessage.value = "";
  try {
    const payload: ProductRequirementDecisionUpdate = {
      applicability_decision: applicabilityForm.applicability_decision,
      rationale: applicabilityForm.rationale.trim() || null,
    };
    await requirementMappingService.updateReleaseRequirementDecision(
      selectedReleaseId.value,
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

/* ── Watchers ─────────────────────────────────────── */

watch(selectedProductId, async (productId) => {
  selectedReleaseId.value = "";
  productReleases.value = [];
  matrixRows.value = [];
  productRiskItems.value = [];
  resetEditor();
  if (productId) await loadProductContext(productId);
});

watch(selectedReleaseId, async () => {
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
/* ── Page layout ──────────────────────────────────── */
.annex-page {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.page-title { margin: 0; }

.page-actions {
  display: flex;
  align-items: flex-end;
  gap: 0.75rem;
  flex-wrap: wrap;
  flex-shrink: 0;
}

.section-heading h1,
.section-heading h2,
.section-heading h3 {
  margin: 0;
}

.editor-actions,
.trace-actions {
  display: flex;
  gap: 0.75rem;
  flex-wrap: wrap;
  align-items: end;
}

/* ── Release banner ───────────────────────────────── */
.release-banner {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 1.5rem;
  flex-wrap: wrap;
  padding: 0.9rem 1.1rem;
  margin-bottom: 1rem;
  border-radius: 12px;
  background: rgba(110, 168, 254, 0.07);
  border: 1px solid rgba(110, 168, 254, 0.2);
}

.release-banner-left {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.release-label {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-weight: 600;
  font-size: var(--text-sm);
}

.release-note {
  color: var(--color-text-muted);
  font-size: var(--text-xs);
}

.release-coverage-bar {
  display: flex;
  flex-direction: column;
  gap: 0.4rem;
  min-width: 220px;
}

.coverage-numbers {
  font-size: var(--text-sm);
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.coverage-pct {
  margin-left: auto;
  font-weight: 700;
  font-size: var(--text-sm);
}

.pct-good    { color: #34d399; }
.pct-partial { color: #fbbf24; }
.pct-low     { color: #f87171; }

.progress-track {
  height: 6px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.08);
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  border-radius: 999px;
  transition: width 0.4s ease;
}

.fill-good    { background: #34d399; }
.fill-partial { background: #fbbf24; }
.fill-low     { background: #f87171; }

/* ── Release trace count mini-stat ────────────────── */
.release-trace-count {
  font-weight: 600;
}

.has-release-evidence {
  background: rgba(52, 211, 153, 0.12);
  border-color: rgba(52, 211, 153, 0.26);
  color: #34d399;
}

.no-release-evidence {
  background: rgba(248, 113, 113, 0.1);
  border-color: rgba(248, 113, 113, 0.22);
  color: #f87171;
}

/* ── Release scope tag in modal ───────────────────── */
.release-scope-tag {
  font-size: var(--text-xs);
  font-weight: 400;
  color: #9cc0ff;
}

/* ── Link button (inline text action) ────────────── */
.link-btn {
  background: none;
  border: none;
  padding: 0;
  color: #9cc0ff;
  cursor: pointer;
  font-size: inherit;
  text-decoration: underline;
  text-underline-offset: 2px;
}

.link-btn:hover {
  color: var(--color-text);
}

/* ── Field hint text ──────────────────────────────── */
.field-hint {
  font-size: var(--text-xs);
  color: var(--color-text-muted);
  font-weight: 400;
}

/* ── Filter badge on button ───────────────────────── */
.filter-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 1.2rem;
  height: 1.2rem;
  border-radius: 999px;
  background: var(--color-primary);
  color: #fff;
  font-size: var(--text-xs);
  font-weight: 700;
  padding: 0 0.3rem;
  margin-left: 0.35rem;
}

/* ── Selector card ────────────────────────────────── */
.selector-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 1rem;
}

/* ── Matrix card ──────────────────────────────────── */
.matrix-card {
  width: 100%;
}

/* ── Compact row list ─────────────────────────────── */
.matrix-list {
  display: flex;
  flex-direction: column;
  gap: 0.55rem;
}

.matrix-row-wrapper {
  display: flex;
  flex-direction: column;
}

/* Compact row — horizontal layout */
.matrix-row {
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.85rem;
  padding: 0.75rem 1rem;
  border: 1px solid rgba(233, 238, 252, 0.08);
  background: rgba(255, 255, 255, 0.03);
  color: inherit;
  border-radius: 14px;
  cursor: pointer;
  text-align: left;
  transition: border-color 0.12s ease, background 0.12s ease, transform 0.12s ease;
}

.matrix-row:hover,
.matrix-row.active {
  border-color: rgba(110, 168, 254, 0.42);
  background: rgba(110, 168, 254, 0.08);
  transform: translateY(-1px);
}

.row-left {
  display: flex;
  flex-direction: column;
  gap: 0.15rem;
  min-width: 0;
  flex: 1;
}

.row-title {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  font-size: var(--text-sm);
}

.requirement-code {
  color: #9cc0ff;
  font-size: var(--text-xs);
  font-weight: 700;
}

.row-right {
  display: flex;
  align-items: center;
  gap: 0.45rem;
  flex-wrap: wrap;
  flex-shrink: 0;
}

/* Expand/collapse chevron button */
.expand-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 1.6rem;
  height: 1.6rem;
  border-radius: 8px;
  color: var(--color-text-muted);
  cursor: pointer;
  transition: background 0.14s ease, color 0.14s ease;
  outline: none;
}

.expand-btn:hover {
  background: rgba(110, 168, 254, 0.12);
  color: var(--color-text);
}

.expand-btn svg {
  transition: transform 0.18s ease;
  pointer-events: none;
}

.expand-btn svg.chevron-open {
  transform: rotate(180deg);
}

/* Inline description panel */
.row-description-panel {
  padding: 0.7rem 1rem 0.7rem 2.5rem;
  border-left: 2px solid rgba(110, 168, 254, 0.3);
  margin: 0.15rem 0 0 1rem;
  border-radius: 0 0 10px 10px;
  background: rgba(110, 168, 254, 0.04);
}

.row-description-panel p {
  margin: 0;
  color: var(--color-text-muted);
  font-size: var(--text-sm);
  line-height: 1.6;
}

/* ── Expand transition ────────────────────────────── */
.expand-enter-active,
.expand-leave-active {
  transition: opacity 0.16s ease, max-height 0.2s ease;
  overflow: hidden;
  max-height: 20rem;
}

.expand-enter-from,
.expand-leave-to {
  opacity: 0;
  max-height: 0;
}

/* ── Detail modal body ────────────────────────────── */
.detail-modal-body {
  display: flex;
  flex-direction: column;
  gap: 0;
}

.detail-description {
  margin: 0 0 1rem;
  color: var(--color-text-muted);
  line-height: 1.6;
}

.summary-bar {
  display: flex;
  gap: 0.55rem;
  flex-wrap: wrap;
  margin-bottom: 1.1rem;
}

.detail-section,
.trace-section,
.editor-card {
  margin-top: 1.1rem;
  padding-top: 1.1rem;
  border-top: 1px solid var(--color-border, rgba(233, 238, 252, 0.1));
}

/* ── Filter modal grid ────────────────────────────── */
.filter-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 1rem;
}

/* ── Shared form / editor grid ────────────────────── */
.editor-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 1rem;
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
  font-size: var(--text-xs);
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: var(--color-text-muted);
}

.field-full {
  grid-column: 1 / -1;
}

/* ── Pill badges ──────────────────────────────────── */
.meta-pill,
.mini-stat {
  border-radius: 999px;
  border: 1px solid rgba(233, 238, 252, 0.1);
  padding: 0.32rem 0.65rem;
  font-size: var(--text-xs);
  white-space: nowrap;
}

.mini-stat {
  color: var(--color-text-muted);
  background: rgba(255, 255, 255, 0.03);
}

/* ── Trace records ────────────────────────────────── */
.trace-list {
  display: flex;
  flex-direction: column;
  gap: 0.85rem;
}

.trace-card,
.editor-card {
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(233, 238, 252, 0.08);
  border-radius: 14px;
  padding: 1rem;
}

.trace-card.selected {
  border-color: rgba(110, 168, 254, 0.42);
  background: rgba(110, 168, 254, 0.08);
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
  color: var(--color-text-muted);
}

/* ── Artifacts ────────────────────────────────────── */
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
  padding: 0.75rem 0.9rem;
  border-radius: 12px;
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
  border-radius: 12px;
  border: 1px solid rgba(233, 238, 252, 0.1);
  background: rgba(255, 255, 255, 0.03);
  cursor: pointer;
}

.artifact-option.selected {
  border-color: rgba(110, 168, 254, 0.38);
  background: rgba(110, 168, 254, 0.08);
}

.artifact-option input { margin-top: 0.2rem; }

.artifact-option-copy {
  display: flex;
  flex-direction: column;
  gap: 0.2rem;
}

.artifact-option-copy span,
.artifact-selection-note {
  color: var(--color-text-muted);
  font-size: var(--text-sm);
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

/* ── Compact list (risks / artifacts in detail) ───── */
.compact-list {
  display: flex;
  flex-direction: column;
  gap: 0.65rem;
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

/* ── Alerts / states ──────────────────────────────── */
.alert {
  border-radius: 12px;
  padding: 0.85rem 1rem;
  border: 1px solid transparent;
  margin-bottom: 0.75rem;
}

.alert.error   { background: rgba(251, 113, 133, 0.12); border-color: rgba(251, 113, 133, 0.26); color: #fecdd3; }
.alert.success { background: rgba(52, 211, 153, 0.12);  border-color: rgba(52, 211, 153, 0.26);  color: #bbf7d0; }
.alert.warning { background: rgba(251, 191, 36, 0.12);  border-color: rgba(251, 191, 36, 0.26);  color: #fde68a; }

.state-block {
  border: 1px dashed rgba(233, 238, 252, 0.14);
  border-radius: 14px;
  padding: 1.2rem;
  background: rgba(255, 255, 255, 0.02);
}

.state-block.compact { padding: 1rem; }

/* ── Skeletons ────────────────────────────────────── */
.skeleton-row {
  height: 3.2rem;
  border-radius: 12px;
  margin-bottom: 0.55rem;
  background:
    linear-gradient(90deg, rgba(255, 255, 255, 0.04), rgba(255, 255, 255, 0.08), rgba(255, 255, 255, 0.04));
  background-size: 200% 100%;
  animation: shimmer 1.4s linear infinite;
}

/* ── Applicability pills ──────────────────────────── */
.app-applicable     { background: rgba(96, 165, 250, 0.12);  border-color: rgba(96, 165, 250, 0.24); }
.app-not_applicable { background: rgba(251, 191, 36, 0.12);  border-color: rgba(251, 191, 36, 0.26); }
.app-needs_decision,
.status-empty       { background: rgba(148, 163, 184, 0.14); border-color: rgba(148, 163, 184, 0.18); }

/* ── Status pills ─────────────────────────────────── */
.status-planned     { background: rgba(250, 204, 21, 0.12);  border-color: rgba(250, 204, 21, 0.22); }
.status-in_progress { background: rgba(251, 146, 60, 0.12);  border-color: rgba(251, 146, 60, 0.24); }
.status-implemented { background: rgba(96, 165, 250, 0.12);  border-color: rgba(96, 165, 250, 0.24); }
.status-verified    { background: rgba(52, 211, 153, 0.12);  border-color: rgba(52, 211, 153, 0.26); }
.status-not_applicable { background: rgba(217, 119, 6, 0.14); border-color: rgba(217, 119, 6, 0.24); }

/* ── Button utilities ─────────────────────────────── */
.small-button {
  padding: 0.4rem 0.7rem;
  border-radius: 9px;
  font-size: var(--text-xs);
}

.link-button {
  display: inline-flex;
  align-items: center;
}

/* ── Fade transition (alerts) ─────────────────────── */
.fade-enter-active,
.fade-leave-active { transition: opacity 0.18s ease; }
.fade-enter-from,
.fade-leave-to     { opacity: 0; }

/* ── Shimmer animation ────────────────────────────── */
@keyframes shimmer {
  from { background-position: 200% 0; }
  to   { background-position: -200% 0; }
}

/* ── Responsive ───────────────────────────────────── */
@media (max-width: 900px) {
  .selector-grid,
  .filter-grid,
  .editor-grid,
  .artifact-selector-grid {
    grid-template-columns: 1fr;
  }

  .section-heading {
    flex-direction: column;
  }

  .row-right {
    flex-wrap: wrap;
  }
}

@media (max-width: 640px) {
  .row-title {
    white-space: normal;
  }

  .matrix-row {
    flex-direction: column;
    align-items: flex-start;
  }

  .row-right {
    width: 100%;
  }
}
</style>

<style>
/* ── Light theme overrides ────────────────────────── */
:root[data-theme="light"] .matrix-row {
  border-color: rgba(28, 107, 39, 0.1);
  background: rgba(255, 255, 255, 0.6);
}
:root[data-theme="light"] .matrix-row:hover,
:root[data-theme="light"] .matrix-row.active {
  border-color: rgba(37, 99, 235, 0.35);
  background: rgba(37, 99, 235, 0.07);
}
:root[data-theme="light"] .trace-card.selected {
  border-color: rgba(37, 99, 235, 0.35);
  background: rgba(37, 99, 235, 0.07);
}
:root[data-theme="light"] .requirement-code { color: #1d4ed8; }
:root[data-theme="light"] .meta-pill        { border-color: rgba(28, 107, 39, 0.12); }
:root[data-theme="light"] .mini-stat        { background: rgba(28, 107, 39, 0.04); }
:root[data-theme="light"] .artifact-option  { border-color: rgba(28, 107, 39, 0.12); background: rgba(255, 255, 255, 0.6); }
:root[data-theme="light"] .artifact-option.selected {
  border-color: rgba(37, 99, 235, 0.35);
  background: rgba(37, 99, 235, 0.07);
}
:root[data-theme="light"] .row-description-panel {
  border-left-color: rgba(37, 99, 235, 0.3);
  background: rgba(37, 99, 235, 0.04);
}
:root[data-theme="light"] .alert.error   { background: rgba(239,68,68,0.08);   border-color: rgba(239,68,68,0.26);   color: #be123c; }
:root[data-theme="light"] .alert.success { background: rgba(21,128,61,0.08);   border-color: rgba(21,128,61,0.26);   color: #15803d; }
:root[data-theme="light"] .alert.warning { background: rgba(184,155,18,0.08);  border-color: rgba(184,155,18,0.26);  color: #78350f; }
:root[data-theme="light"] .state-block   { border-color: rgba(28, 107, 39, 0.15); background: rgba(28, 107, 39, 0.03); }
:root[data-theme="light"] .skeleton-row  {
  background: linear-gradient(90deg, rgba(28,107,39,0.04), rgba(28,107,39,0.08), rgba(28,107,39,0.04));
}
:root[data-theme="light"] .app-applicable     { background: rgba(37,99,235,0.08);   border-color: rgba(37,99,235,0.22); }
:root[data-theme="light"] .app-not_applicable { background: rgba(184,155,18,0.08);  border-color: rgba(184,155,18,0.24); }
:root[data-theme="light"] .app-needs_decision,
:root[data-theme="light"] .status-empty       { background: rgba(71,85,105,0.08);   border-color: rgba(71,85,105,0.18); }
:root[data-theme="light"] .status-planned     { background: rgba(184,155,18,0.08);  border-color: rgba(184,155,18,0.2); }
:root[data-theme="light"] .status-in_progress { background: rgba(234,88,12,0.08);   border-color: rgba(234,88,12,0.22); }
:root[data-theme="light"] .status-implemented { background: rgba(37,99,235,0.08);   border-color: rgba(37,99,235,0.22); }
:root[data-theme="light"] .status-verified    { background: rgba(21,128,61,0.08);   border-color: rgba(21,128,61,0.24); }
:root[data-theme="light"] .status-not_applicable { background: rgba(180,83,9,0.08); border-color: rgba(180,83,9,0.22); }

/* ── Card border visibility in light mode ── */
[data-theme="light"] .annex-page .card {
  box-shadow: 0 2px 6px rgba(0,0,0,0.09), 0 0 0 1px rgba(0,0,0,0.16);
  border-color: transparent;
}
[data-theme="light"] .annex-page .trace-card {
  box-shadow: 0 1px 3px rgba(0,0,0,0.07), 0 0 0 1px rgba(0,0,0,0.13);
  border-color: transparent;
}
[data-theme="light"] .annex-page .artifact-card {
  box-shadow: 0 1px 3px rgba(0,0,0,0.07), 0 0 0 1px rgba(0,0,0,0.13);
  border-color: transparent;
}
[data-theme="light"] .annex-page .editor-card {
  box-shadow: 0 2px 6px rgba(0,0,0,0.09), 0 0 0 1px rgba(0,0,0,0.16);
  border-color: transparent;
}
</style>
