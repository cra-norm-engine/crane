<template>
  <section class="page">
    <!-- ── Page header ── -->
    <header class="page-header">
      <div class="header-text">
        <h1 class="page-title">Certifications</h1>
        <p class="muted page-subtitle">
          Track third-party certifications (IEC 62443, Common Criteria, ETSI EN 303 645, EUCC, etc.)
          for critical and important products. Required under CRA Article 32 for products subject to
          third-party conformity assessment.
        </p>
      </div>

      <div class="filter-row">
        <label class="field">
          <span class="field-label">Filter by product</span>
          <select v-model="selectedProductId">
            <option value="">All products</option>
            <option v-for="p in products" :key="p.id" :value="p.id">
              {{ p.name }} ({{ p.product_code }})
            </option>
          </select>
        </label>
        <label class="field">
          <span class="field-label">Filter by status</span>
          <select v-model="selectedStatus">
            <option value="">All statuses</option>
            <option v-for="(label, value) in STATUS_LABELS" :key="value" :value="value">{{ label }}</option>
          </select>
        </label>
      </div>
    </header>

    <!-- ── Feedback banners ── -->
    <div v-if="errorMessage" class="card feedback feedback-error">{{ errorMessage }}</div>
    <div v-if="successMessage" class="card feedback feedback-success">{{ successMessage }}</div>

    <!-- ── Records table ── -->
    <section class="card">
      <div class="section-header">
        <div>
          <h2 class="section-title">Records</h2>
          <p class="muted section-subtitle">
            {{ filteredRecords.length }} record{{ filteredRecords.length !== 1 ? "s" : "" }} —
            click a row to view details
          </p>
        </div>
        <AppButton v-if="canWrite" variant="primary" type="button" @click="openCreateModal">
          Add record
        </AppButton>
      </div>

      <div v-if="isLoading" class="empty-panel muted">Loading…</div>

      <div v-else-if="filteredRecords.length === 0" class="empty-panel muted">
        No certification records found.<span v-if="canWrite"> Use the Add record button to create one.</span>
      </div>

      <div v-else class="table-wrapper">
        <table class="data-table">
          <thead>
            <tr>
              <th>Product</th>
              <th>Scheme</th>
              <th>Body</th>
              <th>Status</th>
              <th>Issued</th>
              <th>Valid until</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="rec in filteredRecords"
              :key="rec.id"
              class="table-row-clickable"
              tabindex="0"
              @click="openDetail(rec)"
              @keydown.enter="openDetail(rec)"
              @keydown.space.prevent="openDetail(rec)"
              :aria-label="`View details for ${SCHEME_LABELS[rec.certification_scheme]} — ${productName(rec.product_id)}`"
            >
              <td>
                <span class="cell-primary">{{ productName(rec.product_id) }}</span>
              </td>
              <td>
                <span class="scheme-badge">{{ schemeDisplay(rec) }}</span>
              </td>
              <td>{{ rec.certification_body_name }}</td>
              <td>
                <span class="status-badge" :class="`status-${rec.status}`">
                  {{ STATUS_LABELS[rec.status] }}
                </span>
              </td>
              <td class="nowrap">{{ rec.issued_date ?? "—" }}</td>
              <td class="nowrap" :class="{ 'text-warning': isExpiringSoon(rec.valid_until_date) }">
                {{ rec.valid_until_date ?? "—" }}
                <span v-if="isExpiringSoon(rec.valid_until_date)" class="expiry-hint">· expiring soon</span>
              </td>
              <td class="row-arrow">›</td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>
  </section>

  <!-- ── Detail modal ── -->
  <Teleport to="body">
    <Transition name="modal">
      <div
        v-if="detailRec"
        class="modal-backdrop"
        @click.self="closeDetail"
        role="dialog"
        aria-modal="true"
        :aria-label="`${SCHEME_LABELS[detailRec.certification_scheme]} — ${productName(detailRec.product_id)}`"
      >
        <div class="detail-modal">
          <!-- Modal header -->
          <div class="detail-header">
            <div class="detail-header-left">
              <div class="detail-badges">
                <span class="status-badge" :class="`status-${detailRec.status}`">
                  {{ STATUS_LABELS[detailRec.status] }}
                </span>
                <span class="scheme-badge">{{ schemeDisplay(detailRec) }}</span>
              </div>
              <h2 class="detail-title">{{ productName(detailRec.product_id) }}</h2>
              <p class="detail-body-name muted">{{ detailRec.certification_body_name }}</p>
            </div>
            <button class="btn btn-icon btn-close" @click="closeDetail" aria-label="Close">✕</button>
          </div>

          <!-- Modal body -->
          <div class="detail-body">

            <!-- Date strip -->
            <div class="date-strip">
              <div class="date-item">
                <span class="date-label">Issued</span>
                <span class="date-value">{{ detailRec.issued_date ?? "—" }}</span>
              </div>
              <div class="date-sep">→</div>
              <div class="date-item">
                <span class="date-label">Valid until</span>
                <span class="date-value" :class="{ 'text-warning': isExpiringSoon(detailRec.valid_until_date) }">
                  {{ detailRec.valid_until_date ?? "—" }}
                </span>
              </div>
              <div v-if="detailRec.recertification_required_by" class="date-sep">·</div>
              <div v-if="detailRec.recertification_required_by" class="date-item">
                <span class="date-label">Recertify by</span>
                <span class="date-value text-warning">{{ detailRec.recertification_required_by }}</span>
              </div>
            </div>

            <!-- Details grid -->
            <div class="detail-grid">

              <div class="detail-section">
                <h3 class="detail-section-title">Certificate</h3>
                <div class="detail-kv">
                  <span class="detail-key">Number</span>
                  <span class="detail-val">{{ detailRec.certificate_number ?? "—" }}</span>
                </div>
                <div class="detail-kv">
                  <span class="detail-key">Body</span>
                  <span class="detail-val">{{ detailRec.certification_body_name }}</span>
                </div>
                <div class="detail-kv">
                  <span class="detail-key">Scheme</span>
                  <span class="detail-val">{{ schemeDisplay(detailRec) }}</span>
                </div>
              </div>

              <div class="detail-section">
                <h3 class="detail-section-title">Scope</h3>
                <p class="detail-val scope-text">{{ detailRec.scope_description }}</p>
              </div>

              <div v-if="detailRec.notes" class="detail-section detail-section-full">
                <h3 class="detail-section-title">Notes</h3>
                <p class="detail-val scope-text">{{ detailRec.notes }}</p>
              </div>

            </div>

            <!-- Evidence section -->
            <div class="evidence-section">
              <div class="evidence-header">
                <h3 class="evidence-title">Supporting Evidence</h3>
                <span v-if="detailRec.artifact_links" class="evidence-count">{{ detailRec.artifact_links.length }}</span>
              </div>

              <div v-if="!detailRec.artifact_links || detailRec.artifact_links.length === 0" class="empty-evidence">
                No evidence attached yet. Upload certification documentation, test reports, or audit results.
              </div>

              <div v-else class="evidence-list">
                <article v-for="link in detailRec.artifact_links" :key="link.id" class="evidence-item">
                  <div class="evidence-info">
                    <strong class="evidence-name">{{ link.artifact_revision.original_filename || 'Artifact' }}</strong>
                    <p class="evidence-meta">
                      Rev {{ link.artifact_revision.revision_number }}
                      · {{ formatLabel(link.artifact_revision.source_type) }}
                      <template v-if="link.artifact_revision.file_size_bytes">· {{ formatSize(link.artifact_revision.file_size_bytes) }}</template>
                    </p>
                  </div>
                  <div v-if="canWrite" class="evidence-actions">
                    <button
                      v-if="link.artifact_revision.storage_path"
                      class="btn btn-sm btn-ghost"
                      type="button"
                      @click="downloadArtifact(link.artifact_revision.id, link.artifact_revision.original_filename || 'artifact')"
                    >
                      Download
                    </button>
                    <a
                      v-else-if="link.artifact_revision.external_url"
                      class="btn btn-sm btn-ghost"
                      :href="link.artifact_revision.external_url"
                      target="_blank"
                      rel="noreferrer"
                    >
                      Open link
                    </a>
                    <button
                      class="btn btn-sm btn-danger-soft"
                      type="button"
                      :disabled="isActing"
                      @click="removeEvidence(link.id)"
                    >
                      {{ isActing ? 'Removing…' : 'Remove' }}
                    </button>
                  </div>
                </article>
              </div>

              <div v-if="canWrite && detailRec" class="evidence-upload">
                <button
                  class="btn btn-secondary"
                  type="button"
                  @click="showEvidenceUpload = !showEvidenceUpload"
                >
                  {{ showEvidenceUpload ? 'Cancel' : 'Upload evidence' }}
                </button>

                <form v-if="showEvidenceUpload" class="evidence-form" @submit.prevent="uploadEvidence">
                  <label class="field">
                    <span class="field-label">File *</span>
                    <input type="file" @change="onEvidenceFileSelected" required />
                  </label>
                  <label class="field">
                    <span class="field-label">Title *</span>
                    <input
                      v-model.trim="evidenceForm.title"
                      type="text"
                      maxlength="255"
                      placeholder="e.g. Certification audit report"
                      required
                    />
                  </label>
                  <label class="field">
                    <span class="field-label">Type *</span>
                    <select v-model="evidenceForm.artifact_type" required>
                      <option value="">Select type</option>
                      <option value="document">Document</option>
                      <option value="test_report">Test Report</option>
                      <option value="certificate">Certificate</option>
                      <option value="audit">Audit Report</option>
                    </select>
                  </label>
                  <label class="field">
                    <span class="field-label">Description</span>
                    <textarea v-model.trim="evidenceForm.description" rows="2" placeholder="What does this file show?" />
                  </label>
                  <div class="form-actions">
                    <button type="submit" class="btn btn-primary" :disabled="!evidenceFile || isActing">
                      {{ isActing ? 'Uploading…' : 'Upload' }}
                    </button>
                  </div>
                </form>
              </div>
            </div>
          </div>

          <!-- Modal footer -->
          <div class="detail-footer">
            <div class="footer-actions">
              <button
                v-if="canWrite"
                class="btn btn-danger-soft"
                @click="deleteFromModal(detailRec.id)"
              >
                Delete record
              </button>
            </div>
            <AppButton variant="secondary" @click="closeDetail">Close</AppButton>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>

  <!-- ── Create record modal ── -->
  <Teleport to="body">
    <Transition name="modal">
      <div
        v-if="showCreateModal"
        class="modal-backdrop"
        @click.self="closeCreateModal"
        role="dialog"
        aria-modal="true"
        aria-label="Add certification record"
      >
        <div class="detail-modal">
          <!-- Modal header -->
          <div class="detail-header">
            <div class="detail-header-left">
              <h2 class="detail-title">Add certification record</h2>
              <p class="detail-body-name muted">Record a new certificate or pending third-party assessment.</p>
            </div>
            <button class="btn btn-icon btn-close" type="button" @click="closeCreateModal" aria-label="Close">✕</button>
          </div>

          <!-- Modal body -->
          <div class="detail-body">
            <form id="create-cert-form" class="form-grid" @submit.prevent="createRecord">
              <label class="field">
                <span class="field-label">Product *</span>
                <select v-model="form.product_id" required>
                  <option value="">Select a product</option>
                  <option v-for="p in products" :key="p.id" :value="p.id">
                    {{ p.name }} ({{ p.product_code }}) — {{ p.current_classification }}
                  </option>
                </select>
              </label>

              <label class="field">
                <span class="field-label">Certification scheme *</span>
                <select v-model="form.certification_scheme" required>
                  <option value="">Select a scheme</option>
                  <option v-for="(label, value) in SCHEME_LABELS" :key="value" :value="value">{{ label }}</option>
                </select>
              </label>

              <label v-if="form.certification_scheme === 'other'" class="field field-span-2">
                <span class="field-label">Scheme name *</span>
                <input
                  v-model.trim="form.certification_scheme_label"
                  type="text"
                  required
                  placeholder="e.g. ISO/SAE 21434, NIST CSF, SESIP…"
                />
              </label>

              <label class="field">
                <span class="field-label">Certification body *</span>
                <input v-model.trim="form.certification_body_name" type="text" required
                  placeholder="e.g. TÜV Rheinland, BSI, SGS" />
              </label>

              <label class="field">
                <span class="field-label">Certificate number</span>
                <input v-model.trim="form.certificate_number" type="text" placeholder="e.g. CC-2025-12345" />
              </label>

              <label class="field">
                <span class="field-label">Status *</span>
                <select v-model="form.status" required>
                  <option v-for="(label, value) in STATUS_LABELS" :key="value" :value="value">{{ label }}</option>
                </select>
              </label>

              <label class="field">
                <span class="field-label">Issued date</span>
                <input v-model="form.issued_date" type="date" />
              </label>

              <label class="field">
                <span class="field-label">Valid until</span>
                <input v-model="form.valid_until_date" type="date" />
              </label>

              <label class="field">
                <span class="field-label">Recertification required by</span>
                <input v-model="form.recertification_required_by" type="date" />
              </label>

              <label class="field field-span-2">
                <span class="field-label">Scope description *</span>
                <textarea v-model.trim="form.scope_description" rows="3" required
                  placeholder="Describe what is covered — product display_version, features, deployment model…" />
              </label>

              <label class="field field-span-2">
                <span class="field-label">Notes</span>
                <textarea v-model.trim="form.notes" rows="2"
                  placeholder="Conditions, surveillance audits, limitations…" />
              </label>
            </form>
          </div>

          <!-- Modal footer -->
          <div class="detail-footer">
            <div class="footer-actions"></div>
            <div class="footer-actions">
              <AppButton variant="secondary" type="button" @click="closeCreateModal">Cancel</AppButton>
              <AppButton variant="primary" type="submit" form="create-cert-form" :disabled="isSubmitting">
                {{ isSubmitting ? "Saving…" : "Add record" }}
              </AppButton>
            </div>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from "vue";
import AppButton from "@/components/AppButton.vue";
import { useAuthStore } from "@/stores/auth";
import { certificationRecordService } from "@/services/certification-record-service";
import { productService } from "@/services/product-service";
import {
  SCHEME_LABELS,
  STATUS_LABELS,
  type CertificationRecord,
  type CertificationStatus,
} from "@/types/certification-record";

const authStore = useAuthStore();
const canWrite = computed(() => authStore.hasPermission("certification_record_write"));

const records = ref<CertificationRecord[]>([]);
const products = ref<{ id: string; name: string; product_code: string; current_classification: string }[]>([]);
const isLoading = ref(false);
const isSubmitting = ref(false);
const errorMessage = ref("");
const successMessage = ref("");
const detailRec = ref<CertificationRecord | null>(null);
const showCreateModal = ref(false);

const selectedProductId = ref("");
const selectedStatus = ref<CertificationStatus | "">("");

const form = reactive({
  product_id: "",
  certification_scheme: "" as any,
  certification_scheme_label: "",
  certification_body_name: "",
  certificate_number: "",
  scope_description: "",
  issued_date: "",
  valid_until_date: "",
  status: "pending" as CertificationStatus,
  notes: "",
  recertification_required_by: "",
});

// Evidence management state
const showEvidenceUpload = ref(false);
const evidenceFile = ref<File | null>(null);
const isActing = ref(false);
const evidenceForm = reactive({
  title: "",
  artifact_type: "",
  description: "",
});

const filteredRecords = computed(() => {
  let result = records.value;
  if (selectedProductId.value) result = result.filter((r) => r.product_id === selectedProductId.value);
  if (selectedStatus.value) result = result.filter((r) => r.status === selectedStatus.value);
  return result;
});

function productName(productId: string): string {
  const p = products.value.find((p) => p.id === productId);
  return p ? `${p.name} (${p.product_code})` : productId;
}

function schemeDisplay(rec: CertificationRecord): string {
  if (rec.certification_scheme === "other" && rec.certification_scheme_label) {
    return rec.certification_scheme_label;
  }
  return SCHEME_LABELS[rec.certification_scheme];
}

function isExpiringSoon(date: string | null): boolean {
  if (!date) return false;
  const d = new Date(date);
  const now = new Date();
  const diff = (d.getTime() - now.getTime()) / (1000 * 60 * 60 * 24);
  return diff >= 0 && diff <= 90;
}

function clearMessages() {
  errorMessage.value = "";
  successMessage.value = "";
}

function openDetail(rec: CertificationRecord) {
  detailRec.value = rec;
  document.body.style.overflow = "hidden";
}

function closeDetail() {
  detailRec.value = null;
  document.body.style.overflow = "";
}

function openCreateModal() {
  showCreateModal.value = true;
  document.body.style.overflow = "hidden";
}

function closeCreateModal() {
  showCreateModal.value = false;
  document.body.style.overflow = "";
}

async function loadRecords() {
  isLoading.value = true;
  clearMessages();
  try {
    records.value = await certificationRecordService.list();
  } catch {
    errorMessage.value = "Failed to load certification records.";
  } finally {
    isLoading.value = false;
  }
}

async function loadProducts() {
  try {
    const data = await productService.list();
    products.value = data;
  } catch {
    // non-fatal
  }
}

async function createRecord() {
  clearMessages();
  isSubmitting.value = true;
  try {
    const payload = {
      product_id: form.product_id,
      certification_scheme: form.certification_scheme,
      certification_scheme_label: form.certification_scheme === "other" ? (form.certification_scheme_label || null) : null,
      certification_body_name: form.certification_body_name,
      certificate_number: form.certificate_number || null,
      scope_description: form.scope_description,
      issued_date: form.issued_date || null,
      valid_until_date: form.valid_until_date || null,
      status: form.status,
      notes: form.notes || null,
      recertification_required_by: form.recertification_required_by || null,
    };
    const created = await certificationRecordService.create(payload);
    records.value.unshift(created);
    successMessage.value = "Certification record added.";
    closeCreateModal();
    Object.assign(form, {
      product_id: "", certification_scheme: "", certification_scheme_label: "",
      certification_body_name: "", certificate_number: "", scope_description: "",
      issued_date: "", valid_until_date: "", status: "pending", notes: "",
      recertification_required_by: "",
    });
  } catch (err: any) {
    errorMessage.value = err?.response?.data?.detail ?? "Failed to create record.";
  } finally {
    isSubmitting.value = false;
  }
}

async function deleteFromModal(id: string) {
  if (!confirm("Delete this certification record? This cannot be undone.")) return;
  clearMessages();
  try {
    await certificationRecordService.delete(id);
    records.value = records.value.filter((r) => r.id !== id);
    successMessage.value = "Record deleted.";
    closeDetail();
  } catch {
    errorMessage.value = "Failed to delete record.";
  }
}

function onEvidenceFileSelected(event: Event): void {
  const input = event.target as HTMLInputElement;
  evidenceFile.value = input.files?.[0] ?? null;
}

async function uploadEvidence(): Promise<void> {
  if (!evidenceFile.value || !detailRec.value) return;
  isActing.value = true;
  clearMessages();

  try {
    const formData = new FormData();
    formData.append("title", evidenceForm.title);
    formData.append("artifact_type", evidenceForm.artifact_type);
    formData.append("description", evidenceForm.description);
    formData.append("upload", evidenceFile.value);

    const headers: Record<string, string> = {};
    if (authStore.accessToken) {
      headers['Authorization'] = `Bearer ${authStore.accessToken}`;
    }

    const response = await fetch(`/api/v1/certification-records/${detailRec.value.id}/evidence/upload`, {
      method: "POST",
      headers,
      body: formData,
      credentials: 'include'
    });

    if (!response.ok) throw new Error("Upload failed");

    detailRec.value = await response.json();
    successMessage.value = "Evidence uploaded successfully.";
    evidenceFile.value = null;
    evidenceForm.title = "";
    evidenceForm.artifact_type = "";
    evidenceForm.description = "";
    showEvidenceUpload.value = false;
  } catch (err) {
    errorMessage.value = err instanceof Error ? err.message : "Failed to upload evidence.";
  } finally {
    isActing.value = false;
  }
}

async function removeEvidence(linkId: string): Promise<void> {
  if (!detailRec.value) return;
  isActing.value = true;
  clearMessages();

  try {
    const headers: Record<string, string> = {};
    if (authStore.accessToken) {
      headers['Authorization'] = `Bearer ${authStore.accessToken}`;
    }

    const response = await fetch(
      `/api/v1/certification-records/${detailRec.value.id}/evidence/${linkId}`,
      { method: "DELETE", headers, credentials: 'include' }
    );

    if (!response.ok) throw new Error("Removal failed");

    detailRec.value = await response.json();
    successMessage.value = "Evidence removed.";
  } catch (err) {
    errorMessage.value = err instanceof Error ? err.message : "Failed to remove evidence.";
  } finally {
    isActing.value = false;
  }
}

async function downloadArtifact(revisionId: string, filename: string): Promise<void> {
  try {
    const headers: Record<string, string> = {};
    if (authStore.accessToken) {
      headers['Authorization'] = `Bearer ${authStore.accessToken}`;
    }

    const response = await fetch(`/api/v1/artifacts/revisions/${revisionId}/download`, {
      headers,
      credentials: 'include'
    });
    if (!response.ok) throw new Error("Download failed");
    const blob = await response.blob();
    const blobUrl = window.URL.createObjectURL(blob);
    const anchor = document.createElement("a");
    anchor.href = blobUrl;
    anchor.download = filename;
    document.body.appendChild(anchor);
    anchor.click();
    anchor.remove();
    window.URL.revokeObjectURL(blobUrl);
  } catch (err) {
    errorMessage.value = "Failed to download artifact.";
  }
}

function formatLabel(value: string): string {
  return value
    .replaceAll("_", " ")
    .replace(/\b\w/g, (character) => character.toUpperCase());
}

function formatSize(value: number): string {
  if (value < 1024) return `${value} B`;
  if (value < 1024 * 1024) return `${(value / 1024).toFixed(1)} KB`;
  return `${(value / (1024 * 1024)).toFixed(1)} MB`;
}

onMounted(async () => {
  await Promise.all([loadRecords(), loadProducts()]);
});
</script>

<style scoped>
/* ── Layout ── */
.page {
  display: grid;
  gap: 1rem;
}

.page-header {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.header-text {
  display: flex;
  flex-direction: column;
  gap: 0.35rem;
}

.page-title {
  margin: 0;
}

.page-subtitle,
.section-subtitle {
  margin: 0;
}

.filter-row {
  display: flex;
  gap: 0.75rem;
  flex-wrap: wrap;
}

.filter-row .field {
  flex: 1 1 14rem;
  min-width: 14rem;
}

.section-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 1rem;
  margin-bottom: 1.25rem;
}

.section-title {
  margin: 0;
}

/* ── Form ── */
.form-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 1rem;
}

.field {
  display: grid;
  gap: 0.4rem;
}

.field-span-2 {
  grid-column: span 2;
}

.field-label {
  font-size: var(--text-xs);
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: var(--color-text-muted);
}

input,
select,
textarea {
  width: 100%;
  padding: 0.72rem 0.9rem;
  border-radius: 0.85rem;
  border: 1px solid var(--color-border);
  background: var(--color-surface-soft);
  color: inherit;
  box-sizing: border-box;
  font: inherit;
}

input:focus,
select:focus,
textarea:focus {
  outline: none;
  border-color: rgba(175, 214, 46, 0.45);
  box-shadow: 0 0 0 4px rgba(112, 185, 23, 0.12);
}

.form-actions {
  display: flex;
  justify-content: flex-end;
}

/* ── Feedback ── */
.feedback {
  padding: 1rem 1.1rem;
  border-radius: 1rem;
}

.feedback-error  { color: var(--color-danger-text); border-color: var(--color-danger-border); }
.feedback-success { color: var(--color-success-text); border-color: var(--color-success-border); }

/* ── Empty / loading ── */
.empty-panel {
  padding: 1.5rem 1rem;
  text-align: center;
  font-size: var(--text-sm);
}

/* ── Table ── */
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

.data-table tbody tr:last-child td {
  border-bottom: none;
}

.table-row-clickable {
  cursor: pointer;
  transition: background 0.12s;
}

.table-row-clickable:hover {
  background: var(--color-surface-elevated);
}

.table-row-clickable:focus-visible {
  outline: 2px solid var(--color-primary);
  outline-offset: -2px;
}

.row-arrow {
  color: var(--color-text-muted);
  font-size: var(--text-lg);
  text-align: right;
  opacity: 0;
  transition: opacity 0.12s;
}

.table-row-clickable:hover .row-arrow,
.table-row-clickable:focus-visible .row-arrow {
  opacity: 1;
}

.cell-primary {
  font-weight: 500;
}

.nowrap {
  white-space: nowrap;
}

/* ── Status badges ── */
.status-badge {
  display: inline-flex;
  align-items: center;
  padding: 0.2rem 0.6rem;
  border-radius: 999px;
  font-size: var(--text-xs);
  font-weight: 600;
  white-space: nowrap;
}

.status-active    { background: var(--color-emerald-bg);  color: var(--color-emerald-text);  border: 1px solid var(--color-emerald-border); }
.status-pending   { background: var(--color-warning-bg);  color: var(--color-warning-text);  border: 1px solid var(--color-warning-border); }
.status-expired   { background: var(--color-danger-bg);   color: var(--color-danger-text);   border: 1px solid var(--color-danger-border); }
.status-suspended { background: var(--color-pink-bg);     color: var(--color-pink-text);     border: 1px solid var(--color-pink-border); }
.status-withdrawn { background: var(--color-slate-bg);    color: var(--color-slate-text);    border: 1px solid var(--color-slate-border); }

/* ── Scheme badge ── */
.scheme-badge {
  display: inline-flex;
  align-items: center;
  padding: 0.18rem 0.55rem;
  border-radius: 999px;
  font-size: var(--text-xs);
  font-weight: 500;
  background: var(--color-info-bg);
  color: var(--color-info-text);
  border: 1px solid var(--color-info-border);
  white-space: nowrap;
}

/* ── Expiry warning ── */
.text-warning {
  color: var(--color-warning-text);
}

.expiry-hint {
  font-size: var(--text-xs);
  opacity: 0.8;
}

/* ── Buttons ── */
.btn {
  border: 1px solid transparent;
  border-radius: 0.85rem;
  padding: 0.72rem 1.1rem;
  font: inherit;
  cursor: pointer;
  transition: opacity 0.12s, transform 0.12s;
}

.btn:disabled {
  opacity: 0.55;
  cursor: not-allowed;
}

.btn-primary {
  background: linear-gradient(135deg, rgba(175, 214, 46, 0.95), rgba(28, 107, 39, 0.95));
  color: #fff;
  font-weight: 700;
  box-shadow: 0 8px 20px rgba(28, 107, 39, 0.25);
}

.btn-primary:not(:disabled):hover {
  transform: translateY(-1px);
  box-shadow: 0 12px 24px rgba(28, 107, 39, 0.32);
}

.btn-secondary {
  background: transparent;
  border-color: var(--color-border);
  color: inherit;
}

.btn-danger-soft {
  background: var(--color-danger-bg);
  color: var(--color-danger-text);
  border-color: var(--color-danger-border);
}

.btn-icon {
  padding: 0.4rem 0.65rem;
  font-size: var(--text-xs);
  line-height: 1;
}

.btn-close {
  background: transparent;
  border-color: var(--color-border);
  color: var(--color-text-muted);
  border-radius: 0.6rem;
  flex-shrink: 0;
  transition: color 0.12s, border-color 0.12s;
}

.btn-close:hover {
  color: var(--color-danger-text);
  border-color: var(--color-danger-border);
}

/* ── Modal ── */
.modal-backdrop {
  position: fixed;
  inset: 0;
  background: var(--color-modal-backdrop);
  z-index: 200;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 1rem;
}

.detail-modal {
  background: var(--color-modal-bg);
  border: 1px solid var(--color-modal-border);
  border-radius: 1.2rem;
  width: 100%;
  max-width: 48rem;
  max-height: 90vh;
  display: flex;
  flex-direction: column;
  box-shadow: 0 24px 80px rgba(0, 0, 0, 0.55);
  overflow: hidden;
}

.detail-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 1rem;
  padding: 1.4rem 1.5rem 1.1rem;
  border-bottom: 1px solid var(--color-modal-header-border);
  flex-shrink: 0;
}

.detail-header-left {
  display: flex;
  flex-direction: column;
  gap: 0.45rem;
  min-width: 0;
}

.detail-badges {
  display: flex;
  gap: 0.45rem;
  flex-wrap: wrap;
}

.detail-title {
  margin: 0;
  font-size: var(--text-lg);
  font-weight: 700;
  line-height: 1.3;
}

.detail-body-name {
  margin: 0;
  font-size: var(--text-sm);
}

.detail-body {
  flex: 1;
  overflow-y: auto;
  padding: 1.25rem 1.5rem;
  display: flex;
  flex-direction: column;
  gap: 1.1rem;
}

/* Date strip */
.date-strip {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  flex-wrap: wrap;
  padding: 0.9rem 1rem;
  border-radius: 0.85rem;
  background: var(--color-surface-soft);
  border: 1px solid var(--color-inset-border);
}

.date-item {
  display: flex;
  flex-direction: column;
  gap: 0.15rem;
}

.date-label {
  font-size: var(--text-xs);
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--color-text-muted);
}

.date-value {
  font-size: var(--text-sm);
  font-weight: 500;
}

.date-sep {
  color: var(--color-text-muted);
  font-size: var(--text-sm);
}

/* Detail grid */
.detail-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 0.85rem;
}

.detail-section {
  padding: 1rem;
  border-radius: 0.85rem;
  border: 1px solid var(--color-inset-border);
  background: var(--color-inset-surface);
  display: flex;
  flex-direction: column;
  gap: 0.6rem;
}

.detail-section-full {
  grid-column: span 2;
}

.detail-section-title {
  margin: 0;
  font-size: var(--text-xs);
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: var(--color-text-muted);
}

.detail-kv {
  display: grid;
  grid-template-columns: 5.5rem 1fr;
  gap: 0.3rem 0.75rem;
  align-items: baseline;
}

.detail-key {
  font-size: var(--text-xs);
  color: var(--color-text-muted);
}

.detail-val {
  font-size: var(--text-sm);
  word-break: break-word;
}

.scope-text {
  margin: 0;
  font-size: var(--text-sm);
  line-height: 1.55;
  color: var(--color-meta-text);
}

/* Evidence section */
.evidence-section {
  display: flex;
  flex-direction: column;
  gap: 1rem;
  padding: 1rem 0;
  border-top: 1px solid var(--color-modal-header-border);
}

.evidence-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.evidence-title {
  margin: 0;
  font-size: var(--text-sm);
  font-weight: 600;
  color: var(--color-text);
}

.evidence-count {
  font-size: var(--text-sm);
  padding: 0.25rem 0.5rem;
  background: rgba(110, 168, 254, 0.15);
  color: #93c5fd;
  border-radius: 0.3rem;
  font-weight: 600;
}

.empty-evidence {
  padding: 1rem;
  border-radius: 0.65rem;
  background: rgba(255, 255, 255, 0.02);
  border: 1px dashed rgba(233, 238, 252, 0.15);
  text-align: center;
  font-size: var(--text-sm);
  color: rgba(233, 238, 252, 0.5);
}

.evidence-list {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.evidence-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 1rem;
  padding: 0.75rem;
  border-radius: 0.5rem;
  background: rgba(255, 255, 255, 0.02);
  border: 1px solid rgba(233, 238, 252, 0.08);
}

.evidence-info {
  flex: 1;
}

.evidence-name {
  display: block;
  font-size: var(--text-sm);
  font-weight: 600;
  color: var(--color-text);
  word-break: break-word;
}

.evidence-meta {
  margin: 0.25rem 0 0;
  font-size: var(--text-xs);
  color: rgba(233, 238, 252, 0.5);
}

.evidence-actions {
  display: flex;
  gap: 0.5rem;
  flex-wrap: wrap;
}

.evidence-upload {
  display: flex;
  flex-direction: column;
  gap: 1rem;
  padding: 1rem;
  border-radius: 0.65rem;
  background: rgba(110, 168, 254, 0.08);
  border: 1px solid rgba(110, 168, 254, 0.2);
}

.evidence-form {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 0.75rem;
}

.evidence-form .field:nth-child(3) {
  grid-column: 1 / -1;
}

.form-actions {
  display: flex;
  gap: 0.5rem;
  grid-column: 1 / -1;
}

/* Modal footer */
.detail-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 1rem 1.5rem;
  border-top: 1px solid var(--color-modal-header-border);
  flex-shrink: 0;
  gap: 1rem;
}

.footer-actions {
  display: flex;
  gap: 0.5rem;
}

/* Modal transition */
.modal-enter-active,
.modal-leave-active {
  transition: opacity 0.18s ease;
}

.modal-enter-active .detail-modal,
.modal-leave-active .detail-modal {
  transition: transform 0.18s ease, opacity 0.18s ease;
}

.modal-enter-from,
.modal-leave-to {
  opacity: 0;
}

.modal-enter-from .detail-modal,
.modal-leave-to .detail-modal {
  transform: translateY(14px) scale(0.98);
  opacity: 0;
}

/* ── Responsive ── */
@media (max-width: 800px) {
  .form-grid {
    grid-template-columns: 1fr;
  }

  .field-span-2 {
    grid-column: span 1;
  }

  .detail-grid {
    grid-template-columns: 1fr;
  }

  .detail-section-full {
    grid-column: span 1;
  }
}
</style>

<style>
:root[data-theme="light"] .feedback-error  { color: var(--color-danger-text); }
:root[data-theme="light"] .feedback-success { color: var(--color-success-text); }
:root[data-theme="light"] .table-row-clickable:hover { background: var(--color-surface-elevated); }
:root[data-theme="light"] .detail-modal { background: var(--color-modal-bg); }
:root[data-theme="light"] .modal-backdrop { background: var(--color-modal-backdrop); }
:root[data-theme="light"] .date-strip { background: var(--color-inset-surface); }
:root[data-theme="light"] .detail-section { background: var(--color-inset-surface); }
</style>
