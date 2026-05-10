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

        <!-- Upload & Analyze: primary action for new SBOMs -->
        <button class="btn btn-primary" @click="showUploadModal = true">
          Upload &amp; Analyze
        </button>

        <!-- Manual metadata entry: secondary action -->
        <button class="btn btn-secondary" @click="showCreateModal = true">
          + Manual entry
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
      <div v-else-if="records.length === 0" class="empty-panel">
        No SBOM records found. Upload an SBOM file to satisfy CRA Annex I Part II §1.
      </div>

      <div v-else class="table-wrapper">
        <table class="data-table">
          <thead>
            <tr>
              <th>Format</th>
              <th>Spec version</th>
              <th>Components</th>
              <th>Quality</th>
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
              <!-- Quality score badge -->
              <td>
                <span
                  v-if="r.quality_score !== null && r.quality_score !== undefined"
                  class="quality-badge"
                  :class="qualityClass(r.quality_score)"
                >
                  {{ r.quality_score }}/100
                </span>
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

  <!-- ── Upload & Analyze Modal ── -->
  <AppModal v-model="showUploadModal" title="Upload & Analyze SBOM" size="lg" :persistent="true">
    <form id="sbom-upload-form" class="form-grid" @submit.prevent="uploadRecord">
      <div class="field field-span-2">
        <span class="field-label">Release <span class="req">*</span></span>
        <select v-model="uploadForm.product_release_id" required>
          <option value="">— Select a release —</option>
          <option v-for="r in releases" :key="r.id" :value="r.id">{{ r.version }}</option>
        </select>
        <p v-if="!selectedProductId" class="muted hint">Select a product and release in the filters first.</p>
      </div>

      <div class="field field-span-2">
        <span class="field-label">SBOM file <span class="req">*</span></span>
        <input
          ref="fileInput"
          type="file"
          accept=".json,.xml,.spdx,.cdx,.txt"
          required
          @change="onFileChange"
          class="file-input"
        />
        <p class="muted hint">
          CycloneDX (JSON/XML 1.4–1.7) or SPDX (JSON/tag-value 2.2–3.0).
          sbom-tools will run quality scoring and CRA+NTIA compliance validation automatically.
        </p>
      </div>

      <label class="field field-span-2">
        <span class="field-label">Notes</span>
        <textarea v-model.trim="uploadForm.notes" rows="2" placeholder="Scope exclusions, known gaps…" />
      </label>
    </form>

    <template #footer>
      <button class="btn btn-secondary" :disabled="isUploading" @click="showUploadModal = false">Cancel</button>
      <button
        class="btn btn-primary"
        type="submit"
        form="sbom-upload-form"
        :disabled="isUploading || !uploadForm.product_release_id || !uploadForm.file"
      >
        {{ isUploading ? "Analyzing…" : "Upload & Analyze" }}
      </button>
    </template>
  </AppModal>

  <!-- ── Manual Create Modal ── -->
  <AppModal v-model="showCreateModal" title="New SBOM record (manual)" size="lg" :persistent="true">
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
        <p class="muted hint">Leave blank to auto-derive from the uploaded SBOM</p>
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
    <!-- Tab bar -->
    <div class="detail-tabs">
      <button
        v-for="tab in detailTabs"
        :key="tab.id"
        class="detail-tab"
        :class="{ active: activeDetailTab === tab.id }"
        @click="activeDetailTab = tab.id"
      >
        {{ tab.label }}
      </button>
    </div>

    <!-- Tab: Overview -->
    <div v-if="activeDetailTab === 'overview'" class="tab-panel">
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
          <div class="detail-kv">
            <span class="detail-key">Quality</span>
            <span
              v-if="detailItem.quality_score !== null && detailItem.quality_score !== undefined"
              class="quality-badge"
              :class="qualityClass(detailItem.quality_score)"
            >
              {{ detailItem.quality_score }}/100
            </span>
            <span v-else class="muted">Not analyzed</span>
          </div>
        </div>
      </div>

      <div v-if="detailItem.notes" class="detail-block">
        <h3 class="detail-section-title">Notes</h3>
        <p>{{ detailItem.notes }}</p>
      </div>
    </div>

    <!-- Tab: CRA / NTIA Compliance -->
    <div v-else-if="activeDetailTab === 'compliance'" class="tab-panel">
      <div v-if="!detailItem.analysis_findings" class="empty-panel">
        No compliance analysis available.
        <span v-if="detailItem.sbom_content">Click "Re-analyze" to run sbom-tools.</span>
        <span v-else>Upload the SBOM file using "Upload &amp; Analyze" to enable analysis.</span>
      </div>
      <div v-else-if="validateList.length" class="standards-list">
        <!-- Each item in the list is one standard's results -->
        <div
          v-for="(std, idx) in validateList"
          :key="idx"
          class="standard-block"
        >
          <div class="standard-header">
            <span class="standard-name">{{ std.level ?? `Standard ${idx + 1}` }}</span>
            <span
              class="compliance-verdict"
              :class="std.is_compliant ? 'verdict-pass' : 'verdict-fail'"
            >
              {{ std.is_compliant ? "PASS" : "FAIL" }}
            </span>
          </div>
          <ul v-if="(std.violations as unknown[])?.length" class="findings-list">
            <li
              v-for="(v, i) in (std.violations as Record<string,unknown>[])"
              :key="i"
              class="finding-item"
              :class="v.severity === 'Error' ? 'finding-fail' : 'finding-warn'"
            >
              <span class="finding-severity">{{ v.severity }}</span>
              {{ v.message }}
              <span v-if="v.element" class="finding-element">({{ v.element }})</span>
            </li>
          </ul>
          <p v-else class="finding-none">All checks passed.</p>
        </div>
      </div>
      <div v-else class="empty-panel muted">Validation output not available in findings.</div>
    </div>

    <!-- Tab: Quality & Recommendations -->
    <div v-else-if="activeDetailTab === 'quality'" class="tab-panel">
      <div v-if="!detailItem.analysis_findings" class="empty-panel">
        No quality analysis available. Upload the SBOM file to enable analysis.
      </div>
      <div v-else-if="qualityReport">
        <div class="quality-score-row">
          <span class="quality-score-label">Quality score</span>
          <span
            v-if="detailItem.quality_score !== null && detailItem.quality_score !== undefined"
            class="quality-score-large"
            :class="qualityClass(detailItem.quality_score)"
          >
            {{ detailItem.quality_score }}<span class="quality-score-max">/100</span>
          </span>
          <span v-else class="muted">—</span>
          <span v-if="qualityReport.grade" class="quality-grade">Grade: {{ qualityReport.grade }}</span>
        </div>

        <!-- Prioritised recommendations from sbom-tools -->
        <div v-if="qualityRecommendations.length" class="recommendations">
          <h3 class="detail-section-title" style="margin-bottom:0.5rem;">
            Recommendations ({{ qualityRecommendations.length }})
          </h3>
          <ul class="rec-list">
            <li
              v-for="(rec, i) in (qualityRecommendations as Record<string,unknown>[])"
              :key="i"
              class="rec-item"
            >
              <span class="rec-priority">P{{ rec.priority ?? i + 1 }}</span>
              <span class="rec-body">
                {{ rec.message ?? rec.text ?? JSON.stringify(rec) }}
                <span v-if="rec.affected_count" class="rec-count">
                  ({{ rec.affected_count }} component{{ (rec.affected_count as number) !== 1 ? 's' : '' }})
                </span>
              </span>
              <span v-if="rec.impact" class="rec-impact">+{{ rec.impact }} pts</span>
            </li>
          </ul>
        </div>
        <p v-else class="muted" style="margin-top:0.75rem;">No recommendations — SBOM is well-formed.</p>
      </div>
      <div v-else class="empty-panel muted">Quality output not available in findings.</div>
    </div>

    <!-- Tab: Diff -->
    <div v-else-if="activeDetailTab === 'diff'" class="tab-panel">
      <div v-if="!detailItem.analysis_findings?.diff" class="empty-panel">
        No diff available. A diff is generated automatically when a newer SBOM is uploaded
        for the same release and a previous version exists.
      </div>
      <div v-else>
        <!-- Added components -->
        <div v-if="diffAdded.length" class="diff-section">
          <h3 class="detail-section-title diff-added-title">Added ({{ diffAdded.length }})</h3>
          <ul class="diff-list">
            <li v-for="(c, i) in diffAdded" :key="i" class="diff-item diff-item-added">
              {{ formatComponent(c) }}
            </li>
          </ul>
        </div>

        <!-- Removed components -->
        <div v-if="diffRemoved.length" class="diff-section">
          <h3 class="detail-section-title diff-removed-title">Removed ({{ diffRemoved.length }})</h3>
          <ul class="diff-list">
            <li v-for="(c, i) in diffRemoved" :key="i" class="diff-item diff-item-removed">
              {{ formatComponent(c) }}
            </li>
          </ul>
        </div>

        <!-- Changed components -->
        <div v-if="diffChanged.length" class="diff-section">
          <h3 class="detail-section-title diff-changed-title">Changed ({{ diffChanged.length }})</h3>
          <ul class="diff-list">
            <li v-for="(c, i) in diffChanged" :key="i" class="diff-item diff-item-changed">
              {{ formatComponent(c) }}
            </li>
          </ul>
        </div>

        <!-- Raw diff fallback -->
        <div v-if="!diffAdded.length && !diffRemoved.length && !diffChanged.length" class="raw-json">
          <pre>{{ JSON.stringify(detailItem.analysis_findings.diff, null, 2) }}</pre>
        </div>
      </div>
    </div>

    <template #footer>
      <!-- Re-analyze button — only shown when sbom_content is stored -->
      <button
        v-if="detailItem.sbom_content"
        class="btn btn-secondary"
        :disabled="isReanalyzing"
        @click="reanalyzeRecord"
      >
        {{ isReanalyzing ? "Analyzing…" : "Re-analyze" }}
      </button>
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
const isUploading = ref(false);
const isDeleting = ref(false);
const isReanalyzing = ref(false);
const errorMessage = ref("");
const successMessage = ref("");
const showCreateModal = ref(false);
const showUploadModal = ref(false);
const showDetailModal = ref(false);
const detailItem = ref<SbomRecordRead | null>(null);
const activeDetailTab = ref("overview");

const products = ref<ProductSummaryRead[]>([]);
const releases = ref<ProductReleaseSummaryRead[]>([]);
const records = ref<SbomRecordRead[]>([]);

const productQuery = ref("");
const selectedProductId = ref("");
const selectedReleaseId = ref("");

const fileInput = ref<HTMLInputElement | null>(null);

// Detail tabs definition
const detailTabs = [
  { id: "overview", label: "Overview" },
  { id: "compliance", label: "CRA / NTIA" },
  { id: "quality", label: "Quality" },
  { id: "diff", label: "Diff" },
];

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

const uploadForm = reactive({
  product_release_id: "",
  file: null as File | null,
  notes: "",
});

// Computed helpers for detail modal analysis findings

// validate output is a list of per-standard results:
// [ { level: "CraPhase2", is_compliant: bool, violations: [...] }, ... ]
const validateList = computed((): Record<string, unknown>[] => {
  const f = detailItem.value?.analysis_findings;
  if (!f) return [];
  const v = f.validate;
  if (Array.isArray(v)) return v as Record<string, unknown>[];
  return [];
});

const qualityReport = computed((): Record<string, unknown> | null => {
  const f = detailItem.value?.analysis_findings;
  if (!f) return null;
  const q = f.quality as Record<string, unknown> | undefined;
  if (!q) return null;
  // score and recommendations live under q.report
  return (q.report as Record<string, unknown>) ?? q;
});

const qualityRecommendations = computed((): unknown[] => {
  const r = qualityReport.value;
  if (!r) return [];
  const recs = r.recommendations;
  if (Array.isArray(recs)) return recs;
  return [];
});

const diffFindings = computed(() => {
  const f = detailItem.value?.analysis_findings;
  if (!f) return null;
  return (f.diff as Record<string, unknown>) ?? null;
});

const diffAdded = computed((): unknown[] => {
  const d = diffFindings.value;
  if (!d) return [];
  for (const key of ["added", "new_components", "additions"]) {
    const val = d[key];
    if (Array.isArray(val)) return val;
  }
  return [];
});

const diffRemoved = computed((): unknown[] => {
  const d = diffFindings.value;
  if (!d) return [];
  for (const key of ["removed", "deleted_components", "removals"]) {
    const val = d[key];
    if (Array.isArray(val)) return val;
  }
  return [];
});

const diffChanged = computed((): unknown[] => {
  const d = diffFindings.value;
  if (!d) return [];
  for (const key of ["changed", "modified_components", "modifications", "updated"]) {
    const val = d[key];
    if (Array.isArray(val)) return val;
  }
  return [];
});

const filteredProducts = computed(() => {
  const q = productQuery.value.trim().toLowerCase();
  const sorted = [...products.value].sort((a, b) => a.name.localeCompare(b.name));
  if (!q) return sorted;
  return sorted.filter((p) =>
    [p.name, p.product_code].join(" ").toLowerCase().includes(q),
  );
});

function qualityClass(score: number): string {
  if (score >= 80) return "quality-high";
  if (score >= 50) return "quality-medium";
  return "quality-low";
}

function formatDate(val: string | null | undefined): string {
  if (!val) return "—";
  return new Date(val).toLocaleDateString(undefined, { dateStyle: "medium" });
}

function toIsoOrNull(val: string): string | null {
  if (!val) return null;
  return val.includes("T") ? new Date(val).toISOString() : `${val}T00:00:00Z`;
}

function formatComponent(c: unknown): string {
  if (typeof c === "string") return c;
  if (c && typeof c === "object") {
    const obj = c as Record<string, unknown>;
    const name = obj.name ?? obj.component ?? "";
    const version = obj.version ? `@${obj.version}` : "";
    return `${name}${version}`;
  }
  return JSON.stringify(c);
}

function onFileChange(event: Event): void {
  const input = event.target as HTMLInputElement;
  uploadForm.file = input.files?.[0] ?? null;
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
    const params: Record<string, string> = {};
    if (selectedReleaseId.value) {
      params.product_release_id = selectedReleaseId.value;
    } else if (selectedProductId.value) {
      params.product_id = selectedProductId.value;
    }
    const { data } = await apiClient.get<SbomRecordRead[]>("/sbom-records/", { params });
    records.value = data;
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
  uploadForm.product_release_id = id;
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

async function uploadRecord(): Promise<void> {
  if (!uploadForm.file || !uploadForm.product_release_id) return;
  isUploading.value = true;
  errorMessage.value = "";
  try {
    const formData = new FormData();
    formData.append("product_release_id", uploadForm.product_release_id);
    formData.append("file", uploadForm.file);
    if (uploadForm.notes) formData.append("notes", uploadForm.notes);
    await apiClient.post("/sbom-records/upload", formData, {
      headers: { "Content-Type": "multipart/form-data" },
    });
    showUploadModal.value = false;
    successMessage.value = "SBOM uploaded and analyzed successfully.";
    Object.assign(uploadForm, { product_release_id: selectedReleaseId.value, file: null, notes: "" });
    if (fileInput.value) fileInput.value.value = "";
    await loadSbomRecords();
  } catch (err) {
    errorMessage.value = err instanceof Error ? err.message : "Failed to upload SBOM.";
  } finally {
    isUploading.value = false;
  }
}

function openDetail(item: SbomRecordRead): void {
  detailItem.value = item;
  activeDetailTab.value = "overview";
  showDetailModal.value = true;
}

async function reanalyzeRecord(): Promise<void> {
  if (!detailItem.value) return;
  isReanalyzing.value = true;
  errorMessage.value = "";
  try {
    const { data } = await apiClient.post<SbomRecordRead>(
      `/sbom-records/${detailItem.value.id}/analyze`,
    );
    detailItem.value = data;
    successMessage.value = "Re-analysis complete.";
    // Refresh the list too
    await loadSbomRecords();
  } catch {
    errorMessage.value = "Re-analysis failed.";
  } finally {
    isReanalyzing.value = false;
  }
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
.req { color: var(--color-danger-text); }
.hint { font-size: var(--text-xs); color: var(--color-text-muted); margin-top: 0.2rem; }

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

/* File input has its own look */
.file-input { padding: 0.45rem 0.9rem; }

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

/* ── Format badges ── */
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

/* ── Quality score badge ── */
.quality-badge {
  display: inline-block;
  padding: 0.15rem 0.6rem;
  border-radius: 999px;
  font-size: var(--text-xs);
  font-weight: 700;
  letter-spacing: 0.03em;
  border: 1px solid transparent;
}

.quality-high   { background: var(--color-success-bg); color: var(--color-success-text); border-color: var(--color-success-border); }
.quality-medium { background: var(--color-warning-bg); color: var(--color-warning-text); border-color: var(--color-warning-border); }
.quality-low    { background: var(--color-danger-bg);  color: var(--color-danger-text);  border-color: var(--color-danger-border); }

.component-count { font-weight: 700; font-size: var(--text-sm); }
.file-name { font-family: monospace; font-size: var(--text-xs); }

/* ── Detail tabs ── */
.detail-tabs {
  display: flex;
  gap: 0;
  border-bottom: 1px solid var(--color-border);
  margin-bottom: 1.25rem;
}

.detail-tab {
  background: none;
  border: none;
  border-bottom: 2px solid transparent;
  padding: 0.55rem 1rem;
  font: inherit;
  font-size: var(--text-sm);
  font-weight: 600;
  color: var(--color-text-muted);
  cursor: pointer;
  margin-bottom: -1px;
  transition: color 0.12s, border-color 0.12s;
}

.detail-tab:hover { color: inherit; }
.detail-tab.active { color: inherit; border-bottom-color: rgba(175, 214, 46, 0.9); }

.tab-panel { min-height: 120px; }

/* ── Detail panels ── */
.detail-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 1.25rem; margin-bottom: 1rem; }
.detail-section { display: flex; flex-direction: column; gap: 0.5rem; }
.detail-section-title { font-size: var(--text-sm); font-weight: 700; color: var(--color-text-muted); margin-bottom: 0.25rem; }
.detail-kv { display: flex; gap: 0.5rem; align-items: flex-start; }
.detail-key { font-size: var(--text-sm); color: var(--color-text-muted); min-width: 90px; flex-shrink: 0; }
.detail-block { margin-top: 1rem; padding-top: 1rem; border-top: 1px solid var(--color-border); }

/* ── Compliance tab ── */
.compliance-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 1rem;
}

.compliance-verdict {
  display: inline-block;
  padding: 0.2rem 0.7rem;
  border-radius: 999px;
  font-size: var(--text-xs);
  font-weight: 700;
  letter-spacing: 0.05em;
}

.verdict-pass { background: var(--color-success-bg); color: var(--color-success-text); border: 1px solid var(--color-success-border); }
.verdict-fail { background: var(--color-danger-bg);  color: var(--color-danger-text);  border: 1px solid var(--color-danger-border); }

.standards-list { display: flex; flex-direction: column; gap: 1rem; }
.standard-block { padding: 0.75rem; border-radius: 0.75rem; border: 1px solid var(--color-border); background: var(--color-surface-soft); }
.standard-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 0.5rem; }
.standard-name { font-size: var(--text-sm); font-weight: 700; text-transform: uppercase; letter-spacing: 0.05em; }

.findings-list { margin: 0.4rem 0 0; padding-left: 0; list-style: none; display: flex; flex-direction: column; gap: 0.35rem; }
.finding-item { font-size: var(--text-sm); display: flex; align-items: baseline; gap: 0.4rem; flex-wrap: wrap; }
.finding-fail { color: var(--color-danger-text); }
.finding-warn { color: var(--color-warning-text); }
.finding-none { font-size: var(--text-sm); color: var(--color-text-muted); margin-top: 0.25rem; }
.finding-severity { font-size: var(--text-xs); font-weight: 700; text-transform: uppercase; letter-spacing: 0.05em; opacity: 0.8; }
.finding-element { font-family: monospace; font-size: var(--text-xs); opacity: 0.7; }

/* ── Recommendations list ── */
.rec-list { margin: 0; padding: 0; list-style: none; display: flex; flex-direction: column; gap: 0.5rem; }
.rec-item { display: flex; align-items: baseline; gap: 0.5rem; padding: 0.5rem 0.75rem; border-radius: 0.6rem; background: var(--color-surface-soft); border: 1px solid var(--color-border); font-size: var(--text-sm); flex-wrap: wrap; }
.rec-priority { font-size: var(--text-xs); font-weight: 800; color: var(--color-text-muted); flex-shrink: 0; min-width: 1.8rem; }
.rec-body { flex: 1; }
.rec-count { color: var(--color-text-muted); font-size: var(--text-xs); }
.rec-impact { font-size: var(--text-xs); font-weight: 700; color: var(--color-success-text); margin-left: auto; flex-shrink: 0; }
.quality-grade { font-size: var(--text-sm); font-weight: 700; color: var(--color-text-muted); margin-left: 0.5rem; }

/* ── Quality tab ── */
.quality-score-row {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 1rem 0;
  border-bottom: 1px solid var(--color-border);
  margin-bottom: 1rem;
}

.quality-score-label { font-weight: 600; font-size: var(--text-sm); color: var(--color-text-muted); }

.quality-score-large {
  font-size: 1.75rem;
  font-weight: 800;
  padding: 0.2rem 0.8rem;
  border-radius: 0.75rem;
  border: 1px solid transparent;
}

.quality-score-max { font-size: 0.9rem; font-weight: 500; opacity: 0.7; }

.recommendations { margin-top: 0.5rem; }

/* ── Diff tab ── */
.diff-section { margin-bottom: 1rem; }
.diff-added-title   { color: var(--color-success-text); }
.diff-removed-title { color: var(--color-danger-text);  }
.diff-changed-title { color: var(--color-warning-text); }

.diff-list { margin: 0.4rem 0 0; padding-left: 1.2rem; display: flex; flex-direction: column; gap: 0.2rem; }
.diff-item { font-size: var(--text-sm); font-family: monospace; }
.diff-item-added   { color: var(--color-success-text); }
.diff-item-removed { color: var(--color-danger-text);  }
.diff-item-changed { color: var(--color-warning-text); }

/* ── Raw JSON fallback ── */
.raw-json {
  background: var(--color-surface-soft);
  border: 1px solid var(--color-border);
  border-radius: 0.75rem;
  padding: 0.75rem;
  overflow-x: auto;
  max-height: 320px;
  overflow-y: auto;
}

.raw-json pre {
  margin: 0;
  font-size: var(--text-xs);
  font-family: monospace;
  white-space: pre-wrap;
  word-break: break-word;
}

.nowrap { white-space: nowrap; }
.row-arrow { color: var(--color-text-muted); font-size: 1.1rem; text-align: right; opacity: 0; transition: opacity 0.12s; }
.table-row-clickable:hover .row-arrow,
.table-row-clickable:focus-visible .row-arrow { opacity: 1; }
</style>
