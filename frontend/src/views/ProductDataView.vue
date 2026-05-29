<template>
  <section class="page">

    <!-- ── Page header ── -->
    <header class="page-header">
      <div>
        <h1 class="page-title">Data export / import</h1>
        <p class="muted page-subtitle">
          Export a complete product record as a portable JSON file, or import one to create a new product with all its data.
        </p>
      </div>
    </header>

    <!-- ── Two-panel layout ── -->
    <div class="panels">

      <!-- ══════════════════════════════════════════
           EXPORT PANEL
           ══════════════════════════════════════════ -->
      <div class="panel card">
        <div class="panel-header">
          <div class="panel-icon icon-export">
            <svg viewBox="0 0 20 20" fill="currentColor">
              <path d="M10 2a1 1 0 0 1 1 1v8.586l2.293-2.293a1 1 0 1 1 1.414 1.414l-4 4a1 1 0 0 1-1.414 0l-4-4a1 1 0 1 1 1.414-1.414L9 11.586V3a1 1 0 0 1 1-1zM3 17a1 1 0 0 1 1-1h12a1 1 0 0 1 0 2H4a1 1 0 0 1-1-1z"/>
            </svg>
          </div>
          <div>
            <h2 class="panel-title section-title">Export product</h2>
            <p class="muted panel-desc">
              Select a product to download all its data as a single JSON file — including releases, risk assessments, CVD policies, advisories, SBOMs, certifications, and more.
            </p>
          </div>
        </div>

        <div class="panel-body">

          <!-- Product selector -->
          <label class="field">
            <span class="field-label">Select product <span class="required">*</span></span>
            <select v-model="exportProductId" class="select" :disabled="isExporting">
              <option value="">— choose a product —</option>
              <option v-for="p in products" :key="p.id" :value="p.id">
                {{ p.name }} <span v-if="p.product_code">({{ p.product_code }})</span>
              </option>
            </select>
          </label>

          <!-- Export progress -->
          <div v-if="isExporting" class="progress-box">
            <div class="spinner" />
            <span class="progress-label">{{ exportStep }}</span>
          </div>

          <!-- Errors -->
          <p v-if="exportError" class="form-error">{{ exportError }}</p>

          <!-- Export button -->
          <AppButton
            variant="primary"
            type="button"
            style="width:100%"
            :disabled="!exportProductId || isExporting"
            @click="runExport"
          >
            <svg viewBox="0 0 16 16" fill="currentColor" style="width:1rem;height:1rem">
              <path d="M8 1a1 1 0 0 1 1 1v6.586l1.793-1.793a1 1 0 1 1 1.414 1.414l-3.5 3.5a1 1 0 0 1-1.414 0l-3.5-3.5a1 1 0 1 1 1.414-1.414L7 8.586V2a1 1 0 0 1 1-1zM2 14a1 1 0 0 1 1-1h10a1 1 0 0 1 0 2H3a1 1 0 0 1-1-1z"/>
            </svg>
            {{ isExporting ? "Building export…" : "Download JSON" }}
          </AppButton>

          <!-- Schema info -->
          <div class="schema-info">
            <svg viewBox="0 0 16 16" fill="currentColor" style="width:0.85rem;height:0.85rem;flex-shrink:0;margin-top:0.05rem">
              <path fill-rule="evenodd" d="M8 15A7 7 0 1 0 8 1a7 7 0 0 0 0 14zm.93-9.412-3 .75a.75.75 0 0 0 .36 1.456l1.061-.265-.812 3.25a.75.75 0 0 0 1.454.363l1-4a.75.75 0 0 0-.563-.9l-.5-.124V5.588zm.07-1.838a.75.75 0 0 0 0-1.5.75.75 0 0 0 0 1.5z" clip-rule="evenodd"/>
            </svg>
            <div class="schema-info-body">
              <span>Schema v<strong>{{ EXPORT_SCHEMA_VERSION }}</strong> · Includes all product entities except file attachments.</span>
              <button class="schema-dl-link" type="button" @click="downloadSchemaReference">
                Download schema reference (JSON)
              </button>
            </div>
          </div>
        </div>
      </div>

      <!-- ══════════════════════════════════════════
           IMPORT PANEL
           ══════════════════════════════════════════ -->
      <div class="panel card">
        <div class="panel-header">
          <div class="panel-icon icon-import">
            <svg viewBox="0 0 20 20" fill="currentColor">
              <path d="M10 18a1 1 0 0 1-1-1V8.414l-2.293 2.293a1 1 0 1 1-1.414-1.414l4-4a1 1 0 0 1 1.414 0l4 4a1 1 0 0 1-1.414 1.414L11 8.414V17a1 1 0 0 1-1 1zM3 3a1 1 0 0 1 1-1h12a1 1 0 0 1 0 2H4a1 1 0 0 1-1-1z"/>
            </svg>
          </div>
          <div>
            <h2 class="panel-title section-title">Import product</h2>
            <p class="muted panel-desc">
              Upload a CRANE export JSON file to create a new product with all its associated data.
              A preview is shown before any data is written.
            </p>
          </div>
        </div>

        <div class="panel-body">

          <!-- File drop zone -->
          <div
            v-if="!importBundle"
            class="drop-zone"
            :class="{ 'drop-zone-hover': isDragging }"
            @dragover.prevent="isDragging = true"
            @dragleave.prevent="isDragging = false"
            @drop.prevent="onFileDrop"
            @click="fileInput?.click()"
          >
            <input ref="fileInput" type="file" accept=".json,application/json" class="hidden-input" @change="onFileChange" />
            <div class="drop-icon">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.4">
                <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
                <polyline points="17 8 12 3 7 8"/>
                <line x1="12" y1="3" x2="12" y2="15"/>
              </svg>
            </div>
            <p class="drop-label">Drop a CRANE export JSON here</p>
            <p class="muted drop-sub">or <span class="link">click to browse</span></p>
          </div>

          <!-- Parse error -->
          <p v-if="parseError" class="form-error">{{ parseError }}</p>

          <!-- ── Import preview ── -->
          <template v-if="importBundle && importSummary">

            <div class="preview-card">
              <div class="preview-header">
                <div class="preview-product">
                  <div class="preview-avatar">{{ productInitials(importSummary.product_name) }}</div>
                  <div>
                    <div class="preview-name">{{ importSummary.product_name }}</div>
                    <div class="preview-meta muted">
                      Exported {{ formatDate(importSummary.exported_at) }} ·
                      Schema v{{ importSummary.schema_version }}
                    </div>
                  </div>
                </div>
                <button class="btn-icon" type="button" title="Clear" @click="clearImport">
                  <svg viewBox="0 0 16 16" fill="currentColor"><path d="M3.5 3.5 8 8l4.5-4.5 1 1L9 9l4.5 4.5-1 1L8 10l-4.5 4.5-1-1L7 9 2.5 4.5z"/></svg>
                </button>
              </div>

              <!-- Count grid -->
              <div class="count-grid">
                <div v-for="item in countItems" :key="item.label" class="count-cell">
                  <span class="count-num">{{ item.value }}</span>
                  <span class="count-lbl muted">{{ item.label }}</span>
                </div>
              </div>
            </div>

            <!-- Optional: rename product on import -->
            <label class="field">
              <span class="field-label">Import as product name</span>
              <input
                v-model="importProductName"
                class="input"
                maxlength="255"
                :placeholder="importSummary.product_name"
              />
              <span class="field-hint muted">Leave blank to keep the original name.</span>
            </label>

            <!-- Warnings -->
            <div class="warning-box">
              <svg viewBox="0 0 16 16" fill="currentColor" style="width:0.9rem;flex-shrink:0;margin-top:0.1rem">
                <path d="M8.982 1.566a1.13 1.13 0 0 0-1.96 0L.165 13.233c-.457.778.091 1.767.98 1.767h13.713c.889 0 1.438-.99.98-1.767zM8 5c.535 0 .954.462.9.995l-.35 3.507a.552.552 0 0 1-1.1 0L7.1 5.995A.905.905 0 0 1 8 5zm.002 6a1 1 0 1 1 0 2 1 1 0 0 1 0-2z"/>
              </svg>
              <div>
                <strong>This will create a new product</strong> — existing products are never modified.
                File attachments, user assignments, and approved workflow states are not transferred.
                Changes linked to unmapped releases will be skipped.
              </div>
            </div>

            <!-- Import progress -->
            <div v-if="isImporting" class="progress-box">
              <div class="spinner" />
              <div class="progress-right">
                <span class="progress-label">{{ importProgress.step }}</span>
                <div class="progress-bar-wrap">
                  <div
                    class="progress-bar-fill"
                    :style="{ width: `${importPct}%` }"
                  />
                </div>
                <span class="progress-pct muted">{{ importProgress.done }} / {{ importProgress.total }}</span>
              </div>
            </div>

            <p v-if="importError" class="form-error">{{ importError }}</p>

            <div v-if="importedProductId" class="success-box">
              <svg viewBox="0 0 16 16" fill="currentColor" style="width:1rem;flex-shrink:0">
                <path d="M16 8A8 8 0 1 1 0 8a8 8 0 0 1 16 0zm-3.97-3.03a.75.75 0 0 0-1.08.022L7.477 9.417 5.384 7.323a.75.75 0 0 0-1.06 1.06L6.97 11.03a.75.75 0 0 0 1.079-.02l3.992-4.99a.75.75 0 0 0-.01-1.05z"/>
              </svg>
              <div>
                Import complete!
                <RouterLink :to="{ name: 'product-detail', params: { productId: importedProductId } }" class="link">
                  Open the new product →
                </RouterLink>
              </div>
            </div>

            <AppButton
              v-if="!importedProductId"
              variant="primary"
              type="button"
              style="width:100%"
              :disabled="isImporting"
              @click="runImport"
            >
              <svg viewBox="0 0 16 16" fill="currentColor" style="width:1rem;height:1rem">
                <path d="M8 17a1 1 0 0 1-1-1V9.414l-1.793 1.793a1 1 0 0 1-1.414-1.414l3.5-3.5a1 1 0 0 1 1.414 0l3.5 3.5a1 1 0 0 1-1.414 1.414L9 9.414V16a1 1 0 0 1-1 1zM3 3a1 1 0 0 1 1-1h8a1 1 0 0 1 0 2H4a1 1 0 0 1-1-1z"/>
              </svg>
              {{ isImporting ? "Importing…" : "Start import" }}
            </AppButton>
          </template>

        </div>
      </div>

    </div>

  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { RouterLink } from "vue-router";

import AppButton from "@/components/AppButton.vue";
import { productService } from "@/services/product-service";
import {
  buildExportBundle,
  downloadBundleAsJson,
  parseBundleFile,
  summariseBundle,
  importBundle as executeImport,
  MAX_IMPORT_BYTES,
} from "@/services/export-service";
import { EXPORT_SCHEMA_VERSION } from "@/types/export";
import type { ProductSummaryRead } from "@/types/product";
import type { ProductExportBundle, ImportSummary, ImportProgress } from "@/types/export";

/* ─── State ─────────────────────────────────────────── */
const products       = ref<ProductSummaryRead[]>([]);
const exportProductId = ref("");
const isExporting    = ref(false);
const exportStep     = ref("");
const exportError    = ref("");

const fileInput      = ref<HTMLInputElement | null>(null);
const isDragging     = ref(false);
const parseError     = ref("");
const importBundleRef = ref<ProductExportBundle | null>(null);
const importBundle   = importBundleRef;
const importSummary  = ref<ImportSummary | null>(null);
const importProductName = ref("");
const isImporting    = ref(false);
const importError    = ref("");
const importedProductId = ref<string | null>(null);
const importProgress = ref<ImportProgress>({ step: "", done: 0, total: 0 });

/* ─── Computed ──────────────────────────────────────── */
const importPct = computed(() => {
  const { done, total } = importProgress.value;
  if (!total) return 0;
  return Math.round((done / total) * 100);
});

const countItems = computed(() => {
  if (!importSummary.value) return [];
  const c = importSummary.value.counts;
  return [
    { label: "Releases",        value: c.releases },
    { label: "Risk assessments", value: c.risk_assessments },
    { label: "Risk items",      value: c.risk_items },
    { label: "Vuln. reports",   value: c.vulnerability_reports },
    { label: "Advisories",      value: c.security_advisories },
    { label: "Security updates", value: c.security_updates },
    { label: "SBOMs",           value: c.sbom_records },
    { label: "CVD policies",    value: c.cvd_policies },
    { label: "Support periods", value: c.support_periods },
    { label: "Certifications",  value: c.certification_records },
    { label: "Changes",         value: c.changes },
  ];
});

const schemaSections = [
  { key: "_meta",                label: "Export metadata",      hint: "Schema display_version, timestamp, exporting user, tool name." },
  { key: "product",              label: "Product record",        hint: "Core product fields — name, code, classification, scope status, manufacturer." },
  { key: "releases[]",           label: "Product releases",      hint: "All releases with their status, dates, conformity route, and four nested entity types below." },
  { key: "releases[].vulnerability_reports", label: "Vulnerability reports", hint: "Per-release PSIRT intake records with lifecycle status and severity." },
  { key: "releases[].security_advisories",  label: "Security advisories",   hint: "Published advisories with CVE IDs, affected versions, and remediation steps." },
  { key: "releases[].security_updates",     label: "Security updates",      hint: "Patch records with CVSS scores, distribution mechanism, and CVE links." },
  { key: "releases[].sbom_records",         label: "SBOM records",          hint: "Software bill-of-materials in CycloneDX, SPDX, or SWID format." },
  { key: "risk_assessments[]",   label: "Risk assessments",     hint: "Assessment records with nested risk items (threats, likelihood, impact, mitigation)." },
  { key: "cvd_policies[]",       label: "CVD policies",          hint: "Coordinated vulnerability disclosure contacts and disclosure window." },
  { key: "support_periods[]",    label: "Support periods",       hint: "CRA Art. 13(8) support commitments with start/end dates and justification text." },
  { key: "certification_records[]", label: "Certifications",    hint: "Third-party certification records with scheme, body, certificate number, and expiry." },
  { key: "changes[]",            label: "Substantial changes",   hint: "Change log entries with type, date, and title (draft status, no workflow state)." },
];

/* ─── Helpers ───────────────────────────────────────── */
function productInitials(name: string): string {
  return name.trim().split(/\s+/).map((p: string) => p[0]?.toUpperCase() ?? "").slice(0, 2).join("");
}

function formatDate(iso: string): string {
  try {
    return new Date(iso).toLocaleString(undefined, { dateStyle: "medium", timeStyle: "short" });
  } catch {
    return iso;
  }
}

/* ─── Export ─────────────────────────────────────────── */
async function runExport(): Promise<void> {
  if (!exportProductId.value) return;
  isExporting.value = true;
  exportError.value = "";
  exportStep.value  = "Preparing…";

  try {
    const bundle = await buildExportBundle(exportProductId.value, (step: string) => {
      exportStep.value = step;
    });
    downloadBundleAsJson(bundle);
  } catch (err) {
    exportError.value = err instanceof Error ? err.message : "Export failed.";
  } finally {
    isExporting.value = false;
    exportStep.value  = "";
  }
}

/* ─── Import — file handling ─────────────────────────── */
function onFileChange(event: Event): void {
  const file = (event.target as HTMLInputElement).files?.[0];
  if (file) readFile(file);
}

function onFileDrop(event: DragEvent): void {
  isDragging.value = false;
  const file = event.dataTransfer?.files[0];
  if (file) readFile(file);
}

function readFile(file: File): void {
  parseError.value = "";
  clearImport();

  /* Reject files that exceed the size limit before reading into memory. */
  if (file.size > MAX_IMPORT_BYTES) {
    parseError.value = `File is too large (${(file.size / 1024 / 1024).toFixed(1)} MB). Maximum allowed size is ${MAX_IMPORT_BYTES / 1024 / 1024} MB.`;
    return;
  }

  const reader = new FileReader();
  reader.onload = (e) => {
    try {
      const text = e.target?.result as string;
      /* parseBundleFile validates structure AND sanitizes all fields. */
      const bundle = parseBundleFile(text);
      importBundleRef.value = bundle;
      importSummary.value   = summariseBundle(bundle);
    } catch (err) {
      parseError.value = err instanceof Error ? err.message : "Failed to parse file.";
    }
  };
  reader.readAsText(file);
}

function clearImport(): void {
  importBundleRef.value = null;
  importSummary.value   = null;
  importProductName.value = "";
  importError.value     = "";
  importedProductId.value = null;
  importProgress.value  = { step: "", done: 0, total: 0 };
  if (fileInput.value) fileInput.value.value = "";
}

/* ─── Import — execution ─────────────────────────────── */
async function runImport(): Promise<void> {
  if (!importBundleRef.value) return;
  isImporting.value  = true;
  importError.value  = "";

  try {
    const newId = await executeImport(
      importBundleRef.value,
      { productName: importProductName.value.trim() || undefined },
      (p: ImportProgress) => { importProgress.value = p; },
    );
    importedProductId.value = newId;
    /* Refresh product list so export dropdown reflects the new product. */
    products.value = await productService.list();
  } catch (err) {
    importError.value = err instanceof Error ? err.message : "Import failed.";
  } finally {
    isImporting.value = false;
  }
}

/* ─── Data loading ──────────────────────────────────── */
async function loadProducts(): Promise<void> {
  try {
    products.value = await productService.list();
  } catch {
    /* Non-fatal — user can still import. */
  }
}

onMounted(() => { void loadProducts(); });

/* ─── Schema reference download ──────────────────────── */
function downloadSchemaReference(): void {
  const schemaDoc = {
    schema_version: EXPORT_SCHEMA_VERSION,
    description: "CRANE export bundle schema reference",
    note: "Includes all product entities except file attachments.",
    sections: schemaSections,
  };
  const blob = new Blob([JSON.stringify(schemaDoc, null, 2)], { type: "application/json" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `crane-export-schema-v${EXPORT_SCHEMA_VERSION}.json`;
  a.click();
  URL.revokeObjectURL(url);
}
</script>

<style scoped>
/* ── Layout ─────────────────────────────────────────── */
.page { display: grid; gap: 1rem; }

.page-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 1rem;
  flex-wrap: wrap;
}
.page-title    { margin: 0; }
.page-subtitle { margin-top: 0.35rem; font-size: var(--text-sm); }

/* Equal-height side-by-side panels */
.panels {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1rem;
  align-items: stretch;
}

/* ── Panel ───────────────────────────────────────────── */
.panel {
  padding: 0;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.panel-header {
  display: flex;
  align-items: flex-start;
  gap: 1rem;
  padding: 1.4rem 1.5rem 1rem;
  border-bottom: 1px solid var(--color-border, rgba(148,163,184,0.18));
}

.panel-icon {
  width: 2.5rem;
  height: 2.5rem;
  border-radius: 0.6rem;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}
.panel-icon svg { width: 1.25rem; height: 1.25rem; }
.icon-export { background: rgba(99,102,241,0.15); color: #818cf8; }
.icon-import { background: rgba(16,185,129,0.15); color: #6ee7b7; }

/* panel-title uses global section-title class; override margin only */
.panel-title { margin: 0; }
.panel-desc  { margin-top: 0.3rem; font-size: var(--text-sm); }

.panel-body {
  padding: 1.25rem 1.5rem;
  display: flex;
  flex-direction: column;
  flex: 1;
  gap: 1rem;
}

/* ── Form elements ───────────────────────────────────── */
.field { display: grid; gap: 0.4rem; }
.field-label {
  font-size: var(--text-xs);
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: var(--color-text-muted, #94a3b8);
}
.field-hint  { font-size: var(--text-xs); }
.required    { color: #f87171; }

.select, .input {
  padding: 0.55rem 0.8rem;
  background: var(--color-surface-soft, rgba(15,23,42,0.4));
  border: 1px solid var(--color-border, rgba(148,163,184,0.18));
  border-radius: 0.55rem;
  color: inherit;
  font-size: var(--text-sm);
  width: 100%;
  box-sizing: border-box;
  outline: none;
}
.select:focus, .input:focus { border-color: var(--color-primary, #6366f1); }

/* ── Icon close button ───────────────────────────────── */
.btn-icon {
  width: 1.8rem; height: 1.8rem;
  display: flex; align-items: center; justify-content: center;
  border: none; background: transparent; cursor: pointer; color: inherit;
  border-radius: 0.4rem; opacity: 0.6; transition: opacity 0.12s; flex-shrink: 0;
}
.btn-icon:hover { opacity: 1; }
.btn-icon svg { width: 0.85rem; height: 0.85rem; }

/* ── Spinner ─────────────────────────────────────────── */
.spinner {
  width: 1.3rem; height: 1.3rem; flex-shrink: 0;
  border: 2px solid var(--color-border, rgba(148,163,184,0.2));
  border-top-color: var(--color-primary, #6366f1);
  border-radius: 50%;
  animation: spin 0.7s linear infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }

/* ── Progress ────────────────────────────────────────── */
.progress-box {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.85rem 1rem;
  background: var(--color-surface-soft, rgba(148,163,184,0.07));
  border-radius: 0.65rem;
  border: 1px solid var(--color-border, rgba(148,163,184,0.15));
}
.progress-right  { flex: 1; display: flex; flex-direction: column; gap: 0.35rem; }
.progress-label  { font-size: var(--text-sm); }
.progress-pct    { font-size: var(--text-xs); }
.progress-bar-wrap { height: 4px; background: var(--color-border, rgba(148,163,184,0.2)); border-radius: 2px; overflow: hidden; }
.progress-bar-fill { height: 100%; background: var(--color-primary, #6366f1); border-radius: 2px; transition: width 0.2s; }

/* ── Schema info ─────────────────────────────────────── */
.schema-info {
  display: flex;
  align-items: flex-start;
  gap: 0.5rem;
  font-size: var(--text-xs);
  color: var(--color-text-muted, #94a3b8);
  padding: 0.65rem 0.85rem;
  background: var(--color-surface-soft, rgba(148,163,184,0.06));
  border-radius: 0.55rem;
}
.schema-info-body { display: flex; flex-direction: column; gap: 0.3rem; }
.schema-dl-link {
  display: inline-flex;
  align-items: center;
  gap: 0.3rem;
  background: none;
  border: none;
  padding: 0;
  cursor: pointer;
  color: var(--color-primary, #818cf8);
  font-size: var(--text-xs);
  text-decoration: underline;
  text-underline-offset: 2px;
}
.schema-dl-link:hover { opacity: 0.8; }

/* ── Errors / warnings / success ─────────────────────── */
.form-error {
  color: #fda4af;
  font-size: var(--text-sm);
  margin: 0;
}

.warning-box {
  display: flex;
  align-items: flex-start;
  gap: 0.6rem;
  padding: 0.85rem 1rem;
  background: rgba(251,191,36,0.07);
  border: 1px solid rgba(251,191,36,0.25);
  border-radius: 0.65rem;
  font-size: var(--text-sm);
  color: #fbbf24;
  line-height: 1.5;
}

.success-box {
  display: flex;
  align-items: flex-start;
  gap: 0.6rem;
  padding: 0.85rem 1rem;
  background: rgba(52,211,153,0.1);
  border: 1px solid rgba(52,211,153,0.25);
  border-radius: 0.65rem;
  font-size: var(--text-sm);
  color: #86efac;
}

/* ── Drop zone ───────────────────────────────────────── */
.drop-zone {
  border: 2px dashed var(--color-border, rgba(148,163,184,0.3));
  border-radius: 0.85rem;
  padding: 2.5rem 1rem;
  text-align: center;
  cursor: pointer;
  transition: border-color 0.15s, background 0.15s;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.5rem;
}
.drop-zone:hover, .drop-zone-hover {
  border-color: var(--color-primary, #6366f1);
  background: rgba(99,102,241,0.05);
}
.drop-icon {
  width: 2.5rem; height: 2.5rem;
  color: var(--color-text-muted, #94a3b8);
  opacity: 0.6;
}
.drop-icon svg { width: 100%; height: 100%; }
.drop-label { font-size: var(--text-sm); font-weight: 600; }
.drop-sub   { font-size: var(--text-xs); }
.hidden-input { display: none; }
.link { color: var(--color-primary, #818cf8); cursor: pointer; text-decoration: underline; }

/* ── Import preview card ─────────────────────────────── */
.preview-card {
  border: 1px solid var(--color-border, rgba(148,163,184,0.18));
  border-radius: 0.75rem;
  overflow: hidden;
}
.preview-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 0.75rem;
  padding: 1rem;
  background: var(--color-surface-soft, rgba(148,163,184,0.05));
  border-bottom: 1px solid var(--color-border, rgba(148,163,184,0.18));
}
.preview-product { display: flex; align-items: center; gap: 0.75rem; }
.preview-avatar {
  width: 2.5rem; height: 2.5rem;
  border-radius: 0.5rem;
  background: rgba(99,102,241,0.2); color: #818cf8;
  display: flex; align-items: center; justify-content: center;
  font-size: var(--text-sm); font-weight: 700; flex-shrink: 0;
}
.preview-name { font-size: var(--text-base); font-weight: 700; }
.preview-meta { font-size: var(--text-xs); margin-top: 0.2rem; }

.count-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  padding: 0.75rem;
  gap: 0.5rem;
}
.count-cell {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 0.5rem;
  border-radius: 0.5rem;
  background: var(--color-surface-soft, rgba(148,163,184,0.05));
  gap: 0.15rem;
}
.count-num { font-size: var(--text-xl); font-weight: 700; }
.count-lbl { font-size: var(--text-xs); text-align: center; }

/* ── Responsive ──────────────────────────────────────── */
@media (max-width: 860px) {
  .panels     { grid-template-columns: 1fr; }
  .count-grid { grid-template-columns: repeat(3, 1fr); }
}
</style>

<style>
:root[data-theme="light"] .icon-export { background: rgba(79,70,229,0.1); color: #4f46e5; }
:root[data-theme="light"] .icon-import { background: rgba(5,150,105,0.1); color: #059669; }
:root[data-theme="light"] .warning-box { background: rgba(180,130,0,0.07); color: #92400e; border-color: rgba(180,130,0,0.25); }
:root[data-theme="light"] .success-box { background: rgba(21,128,61,0.08); color: #15803d; border-color: rgba(21,128,61,0.25); }
:root[data-theme="light"] .link { color: #4f46e5; }
</style>
