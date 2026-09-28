<template>
  <section class="transfer-page">
    <header class="page-header" data-guide="data-header">
      <div>
        <p class="eyebrow">Controlled data exchange</p>
        <h1 class="page-title">Product data transfer</h1>
        <p class="page-subtitle">Export or import versioned CRANE records with validation, integrity checks and an audit trail.</p>
      </div>
      <AppButton variant="secondary" @click="startGuide">? Guide</AppButton>
    </header>

    <nav class="mode-tabs" aria-label="Product data transfer sections">
      <button v-if="canExport" :class="{ active: mode === 'export' }" @click="mode = 'export'">Export</button>
      <button v-if="canImport" :class="{ active: mode === 'import' }" @click="mode = 'import'">Import</button>
      <button v-if="canExport" :class="{ active: mode === 'history' }" @click="openHistory">Transfer history</button>
    </nav>

    <div v-if="!canExport && !canImport" class="notice error">You do not have product-data export or import permission.</div>

    <div v-else-if="mode === 'export'" class="workspace" data-guide="data-export">
      <main class="card flow-card">
        <div class="section-heading">
          <span class="step-number">1</span>
          <div><h2>Select the product and release scope</h2><p>The exported file creates a new product when imported. Existing products are never changed.</p></div>
        </div>

        <label class="field">
          <span>Product</span>
          <select v-model="exportProductId" :disabled="exportBusy" @change="loadReleases">
            <option value="">Choose a product</option>
            <option v-for="product in products" :key="product.id" :value="product.id">{{ product.name }} · {{ product.product_code }}</option>
          </select>
        </label>

        <fieldset v-if="releases.length" class="release-scope">
          <legend>Release scope</legend>
          <label><input v-model="selectedOnly" type="radio" :value="false"> All releases ({{ releases.length }})</label>
          <label><input v-model="selectedOnly" type="radio" :value="true"> Selected releases</label>
          <div v-if="selectedOnly" class="release-list">
            <label v-for="release in releases" :key="release.id">
              <input v-model="selectedReleaseIds" type="checkbox" :value="release.id">
              <span><strong>{{ release.display_version }}</strong><small>{{ label(release.release_status) }}</small></span>
            </label>
          </div>
        </fieldset>

        <div class="section-heading compact">
          <span class="step-number">2</span>
          <div><h2>Protect the transfer</h2><p>Choose the sensitivity and the minimum data needed by the recipient.</p></div>
        </div>
        <div class="form-grid">
          <label class="field"><span>Sensitivity</span><select v-model="sensitivity"><option value="internal">Internal</option><option value="confidential">Confidential</option><option value="restricted">Restricted</option></select></label>
          <label class="check"><input v-model="redactPersonalData" type="checkbox"><span><strong>Remove reporter personal data</strong><small>Recommended for data minimisation.</small></span></label>
          <label class="check"><input v-model="includeEmbargoed" type="checkbox"><span><strong>Include embargoed advisories</strong><small>Only for an authorised recipient and secure channel.</small></span></label>
        </div>

        <div class="action-row">
          <p v-if="exportError" class="form-error">{{ exportError }}</p>
          <AppButton variant="primary" :disabled="!exportReady || exportBusy" @click="runExport">{{ exportBusy ? 'Preparing secure export…' : 'Download CRANE bundle' }}</AppButton>
        </div>
      </main>

      <aside class="card manifest" data-guide="data-schema">
        <div class="manifest-title"><div><h2>Transfer manifest</h2><p>Schema v{{ EXPORT_SCHEMA_VERSION }}</p></div><AppButton size="sm" variant="ghost" @click="productDataService.downloadSchema">Schema</AppButton></div>
        <h3>Included</h3>
        <ul><li v-for="item in included" :key="item">✓ {{ item }}</li></ul>
        <h3>Not included</h3>
        <ul class="excluded"><li v-for="item in excluded" :key="item">— {{ item }}</li></ul>
        <div class="security-note"><strong>Sensitive security information</strong><span>Store and send the downloaded file through an access-controlled, encrypted channel.</span></div>
      </aside>
    </div>

    <div v-else-if="mode === 'import'" class="import-flow" data-guide="data-import">
      <ol class="stepper" aria-label="Import progress">
        <li :class="{ active: importStep === 1, done: importStep > 1 }">1 <span>Select file</span></li>
        <li :class="{ active: importStep === 2, done: importStep > 2 }">2 <span>Validate</span></li>
        <li :class="{ active: importStep === 3, done: importStep > 3 }">3 <span>Review</span></li>
        <li :class="{ active: importStep === 4 }">4 <span>Complete</span></li>
      </ol>

      <main class="card import-card">
        <label v-if="!importFile" class="drop-zone" data-guide="data-drop" @dragover.prevent @drop.prevent="dropFile">
          <input ref="fileInput" class="sr-only" type="file" accept=".json,application/json" @change="chooseFile">
          <span class="upload-mark">↑</span><h2>Select a CRANE JSON bundle</h2><p>Drop a file here or press Enter to browse · maximum 50 MB</p>
        </label>

        <template v-else>
          <div class="file-row"><div><strong>{{ importFile.name }}</strong><small>{{ fileSize(importFile.size) }}</small></div><AppButton size="sm" variant="ghost" :disabled="importBusy" @click="clearImport">Choose another</AppButton></div>
          <div v-if="validating" class="working"><span class="spinner" /> Validating structure, relationships, permissions and integrity…</div>
          <p v-if="importError" class="form-error">{{ importError }}</p>

          <template v-if="validation">
            <div class="validation-head" :class="validation.valid ? 'valid' : 'invalid'">
              <div><strong>{{ validation.valid ? 'Validation passed' : 'Import blocked' }}</strong><span>Schema {{ validation.schema_version }} · {{ signatureLabel }}</span></div>
              <code :title="validation.digest">{{ validation.digest.slice(0, 12) }}…</code>
            </div>

            <div class="form-grid identity-grid">
              <label class="field"><span>Import as product name</span><input v-model="importName" maxlength="255" @input="reviewStale = true"></label>
              <label class="field"><span>Unique product code</span><input v-model="importCode" maxlength="100" @input="reviewStale = true"></label>
            </div>
            <div v-if="reviewStale" class="notice warning">Name or code changed. Validate again before importing. <AppButton size="sm" @click="validateImport">Validate again</AppButton></div>

            <section class="review-section">
              <h2>Records found</h2>
              <div class="count-grid"><div v-for="entry in counts" :key="entry[0]"><strong>{{ entry[1] }}</strong><span>{{ label(entry[0]) }}</span></div></div>
            </section>

            <section class="review-section">
              <h2>Validation findings</h2>
              <div v-for="group in issueGroups" :key="group.level" class="issue-group" :class="group.level">
                <h3>{{ issueHeading(group.level) }} <span>{{ group.items.length }}</span></h3>
                <div v-for="issue in group.items" :key="`${issue.path}-${issue.message}`" class="issue-row"><code>{{ issue.path }}</code><span>{{ issue.message }}</span></div>
              </div>
            </section>

            <details class="manifest-details"><summary>Included and excluded data</summary><div class="manifest-columns"><div><h3>Included</h3><ul><li v-for="item in validation.included" :key="item">{{ item }}</li></ul></div><div><h3>Excluded</h3><ul><li v-for="item in validation.excluded" :key="item">{{ item }}</li></ul></div></div></details>

            <label class="check confirmation"><input v-model="confirmed" type="checkbox" :disabled="!validation.valid || reviewStale"><span><strong>Create this as a new product</strong><small>I understand that imported workflows start in safe review states and the transaction will roll back if any write fails.</small></span></label>
            <div class="action-row"><AppButton variant="primary" :disabled="!validation.valid || reviewStale || !confirmed || importBusy" @click="runImport">{{ importBusy ? 'Importing atomically…' : 'Import validated product' }}</AppButton></div>
          </template>
        </template>

        <div v-if="importResult" class="success-card"><span>✓</span><div><h2>Import complete</h2><p>{{ totalImported }} records created in one transaction · {{ importResult.adjusted }} adjusted · {{ importResult.skipped }} skipped.</p><RouterLink :to="{ name: 'product-detail', params: { productId: importResult.product_id } }">Open product →</RouterLink></div></div>
      </main>
    </div>

    <div v-else class="card history-card">
      <div class="manifest-title"><div><h2>Transfer history</h2><p>Product-data exports and imports recorded in CRANE’s audit ledger.</p></div><AppButton size="sm" :disabled="historyBusy" @click="loadHistory">Refresh</AppButton></div>
      <div v-if="historyBusy" class="working"><span class="spinner" /> Loading transfer history…</div>
      <div v-else-if="!history.length" class="empty">No recorded transfers yet.</div>
      <div v-else class="table-wrap"><table><thead><tr><th>When</th><th>Action</th><th>Product</th><th>Records</th><th>Digest</th></tr></thead><tbody><tr v-for="item in history" :key="`${item.occurred_at}-${item.bundle_id}`"><td>{{ formatDate(item.occurred_at) }}</td><td><span class="action-chip">{{ item.action }}</span></td><td>{{ item.product_name || 'Unknown product' }}</td><td>{{ Object.values(item.counts).reduce((sum, value) => sum + value, 0) }}</td><td><code>{{ item.digest?.slice(0, 12) || '—' }}</code></td></tr></tbody></table></div>
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { RouterLink } from "vue-router";
import AppButton from "@/components/AppButton.vue";
import { productDataService, MAX_IMPORT_BYTES } from "@/services/export-service";
import { productReleaseService } from "@/services/product-release-service";
import { productService } from "@/services/product-service";
import { useAuthStore } from "@/stores/auth";
import { EXPORT_SCHEMA_VERSION } from "@/types/export";
import type { ProductDataHistoryItem, ProductDataImportResult, ProductDataIssueLevel, ProductDataValidation } from "@/types/export";
import type { ProductSummaryRead } from "@/types/product";
import type { ProductReleaseRead } from "@/types/release-gate";

const auth = useAuthStore();
const canExport = computed(() => auth.hasPermission("product_data_export"));
const canImport = computed(() => auth.hasPermission("product_data_import"));
const mode = ref<"export" | "import" | "history">(canExport.value ? "export" : "import");
const products = ref<ProductSummaryRead[]>([]);
const releases = ref<ProductReleaseRead[]>([]);
const exportProductId = ref("");
const selectedOnly = ref(false);
const selectedReleaseIds = ref<string[]>([]);
const sensitivity = ref<"internal" | "confidential" | "restricted">("confidential");
const redactPersonalData = ref(true);
const includeEmbargoed = ref(false);
const exportBusy = ref(false);
const exportError = ref("");
const included = ["Product record", "Selected releases", "Risk assessments and risk items", "Vulnerability, advisory, update and SBOM records", "CVD, support, certification and change records"];
const excluded = ["Attachments and artifact binaries", "Users, roles, assignments and approvals", "Audit entries and system settings", "Release-gate signatures"];
const exportReady = computed(() => exportProductId.value && (!selectedOnly.value || selectedReleaseIds.value.length > 0));

const fileInput = ref<HTMLInputElement | null>(null);
const importFile = ref<File | null>(null);
const validation = ref<ProductDataValidation | null>(null);
const importResult = ref<ProductDataImportResult | null>(null);
const importName = ref("");
const importCode = ref("");
const validating = ref(false);
const importBusy = ref(false);
const importError = ref("");
const reviewStale = ref(false);
const confirmed = ref(false);
const importStep = computed(() => importResult.value ? 4 : validation.value ? 3 : importFile.value ? 2 : 1);
const counts = computed(() => Object.entries(validation.value?.counts ?? {}).filter(([, value]) => value > 0));
const totalImported = computed(() => Object.values(importResult.value?.counts ?? {}).reduce((sum, value) => sum + value, 1));
const signatureLabel = computed(() => ({ verified: "authenticated bundle", unsigned: "checksum only", unverified: "signature not verifiable here", invalid: "integrity failure" }[validation.value?.signature_status ?? "unsigned"]));
const issueGroups = computed(() => (["must_fix", "will_adjust", "will_skip", "ready"] as ProductDataIssueLevel[]).map(level => ({ level, items: validation.value?.issues.filter(issue => issue.level === level) ?? [] })).filter(group => group.items.length));

const history = ref<ProductDataHistoryItem[]>([]);
const historyBusy = ref(false);

function startGuide(): void { window.dispatchEvent(new Event("crane-guide-start")); }
function label(value: string): string { return value.replaceAll("_", " ").replace(/\b\w/g, char => char.toUpperCase()); }
function issueHeading(level: ProductDataIssueLevel): string { return ({ must_fix: "Must fix", will_adjust: "Will be adjusted", will_skip: "Will be skipped", ready: "Ready" })[level]; }
function fileSize(bytes: number): string { return `${(bytes / 1024 / 1024).toFixed(1)} MB`; }
function formatDate(value: string): string { return new Date(value).toLocaleString(); }

async function loadReleases(): Promise<void> {
  selectedReleaseIds.value = [];
  releases.value = exportProductId.value ? await productReleaseService.list(exportProductId.value) : [];
}
async function runExport(): Promise<void> {
  if (!exportReady.value) return;
  exportBusy.value = true; exportError.value = "";
  try {
    await productDataService.export(exportProductId.value, { releaseIds: selectedOnly.value ? selectedReleaseIds.value : undefined, redactPersonalData: redactPersonalData.value, includeEmbargoed: includeEmbargoed.value, sensitivity: sensitivity.value });
  } catch (error) { exportError.value = error instanceof Error ? error.message : "Export failed."; }
  finally { exportBusy.value = false; }
}
function chooseFile(event: Event): void { const file = (event.target as HTMLInputElement).files?.[0]; if (file) void acceptFile(file); }
function dropFile(event: DragEvent): void { const file = event.dataTransfer?.files[0]; if (file) void acceptFile(file); }
async function acceptFile(file: File): Promise<void> {
  clearImport();
  if (file.size > MAX_IMPORT_BYTES) { importError.value = "The file exceeds the 50 MB import limit."; return; }
  if (!file.name.toLowerCase().endsWith(".json")) { importError.value = "Select a CRANE JSON export file."; return; }
  importFile.value = file;
  await validateImport(true);
}
async function validateImport(initial = false): Promise<void> {
  if (!importFile.value) return;
  validating.value = true; importError.value = ""; confirmed.value = false;
  try {
    const result = await productDataService.validate(importFile.value, initial ? undefined : importName.value, initial ? undefined : importCode.value);
    validation.value = result;
    if (initial) { importName.value = result.source_product_name; importCode.value = result.suggested_product_code; }
    reviewStale.value = false;
  } catch (error) { validation.value = null; importError.value = error instanceof Error ? error.message : "Validation failed."; }
  finally { validating.value = false; }
}
async function runImport(): Promise<void> {
  if (!importFile.value || !validation.value?.valid || reviewStale.value || !confirmed.value) return;
  importBusy.value = true; importError.value = "";
  try {
    importResult.value = await productDataService.import(importFile.value, importName.value, importCode.value);
    if (canExport.value) void loadHistory();
  } catch (error) { importError.value = error instanceof Error ? error.message : "Import failed and was rolled back."; }
  finally { importBusy.value = false; }
}
function clearImport(): void {
  importFile.value = null; validation.value = null; importResult.value = null; importName.value = ""; importCode.value = ""; importError.value = ""; confirmed.value = false; reviewStale.value = false;
  if (fileInput.value) fileInput.value.value = "";
}
async function loadHistory(): Promise<void> { historyBusy.value = true; try { history.value = await productDataService.history(); } finally { historyBusy.value = false; } }
function openHistory(): void { mode.value = "history"; void loadHistory(); }

onMounted(async () => { if (canExport.value) products.value = await productService.list(); });
</script>

<style scoped>
.transfer-page{max-width:1280px;margin:0 auto;display:grid;gap:20px}.page-header,.manifest-title,.file-row,.validation-head,.action-row{display:flex;align-items:center;justify-content:space-between;gap:16px}.eyebrow{margin:0 0 5px;color:var(--color-primary);font-size:11px;font-weight:750;letter-spacing:.1em;text-transform:uppercase}.page-title{margin:0;font-size:30px;letter-spacing:-.035em}.page-subtitle,.section-heading p,.manifest p,.manifest-title p{margin:6px 0 0;color:var(--color-text-muted);font-size:13px}.mode-tabs{display:flex;gap:4px;border-bottom:1px solid var(--color-border)}.mode-tabs button{padding:11px 16px;border:0;border-bottom:2px solid transparent;background:transparent;color:var(--color-text-muted);font:650 13px/1 inherit;cursor:pointer}.mode-tabs button.active{border-bottom-color:var(--color-primary);color:var(--color-text)}.workspace{display:grid;grid-template-columns:minmax(0,1.7fr) minmax(290px,.8fr);gap:18px;align-items:start}.card{padding:22px;border:1px solid var(--color-border);border-radius:14px;background:var(--color-surface);box-shadow:0 10px 30px rgba(0,0,0,.04)}.flow-card,.import-card{display:grid;gap:20px}.section-heading{display:grid;grid-template-columns:30px 1fr;gap:12px}.section-heading.compact{margin-top:8px}.section-heading h2,.manifest h2,.review-section h2,.success-card h2,.history-card h2{margin:0;font-size:16px}.step-number{width:28px;height:28px;display:grid;place-items:center;border-radius:8px;background:color-mix(in srgb,var(--color-primary) 14%,var(--color-surface));color:var(--color-primary);font-size:12px;font-weight:750}.field{display:grid;gap:7px}.field>span,.release-scope legend{color:var(--color-text-muted);font-size:11px;font-weight:700;letter-spacing:.05em;text-transform:uppercase}.field input,.field select{width:100%;box-sizing:border-box;padding:10px;border:1px solid var(--color-border);border-radius:8px;background:var(--color-surface);color:inherit;font:inherit;font-size:13px}.release-scope{display:grid;gap:10px;margin:0;padding:15px;border:1px solid var(--color-border);border-radius:10px}.release-scope>label{display:flex;gap:8px;font-size:13px}.release-list{max-height:220px;display:grid;gap:5px;overflow:auto;padding:8px;border-radius:8px;background:var(--color-surface-elevated)}.release-list label{display:flex;align-items:center;gap:9px;padding:6px}.release-list span{display:grid}.release-list small,.file-row small,.check small{color:var(--color-text-muted);font-size:11px}.form-grid{display:grid;grid-template-columns:1fr 1fr;gap:14px}.check{display:flex;align-items:flex-start;gap:9px;padding:10px;border:1px solid var(--color-border);border-radius:9px;font-size:12px}.check input{margin-top:2px}.check span{display:grid;gap:3px}.action-row{justify-content:flex-end}.form-error{margin:0 auto 0 0;color:var(--color-danger-text);font-size:12px}.manifest{position:sticky;top:16px}.manifest h3,.manifest-details h3{margin:18px 0 7px;font-size:11px;text-transform:uppercase;letter-spacing:.06em}.manifest ul,.manifest-details ul{display:grid;gap:7px;margin:0;padding:0;list-style:none;color:var(--color-text-muted);font-size:12px}.manifest .excluded{color:var(--color-text-muted)}.security-note{display:grid;gap:4px;margin-top:20px;padding:12px;border:1px solid var(--color-warning-border);border-radius:9px;background:var(--color-warning-bg);color:var(--color-warning-text);font-size:12px}.security-note span{line-height:1.5}.stepper{display:grid;grid-template-columns:repeat(4,1fr);margin:0;padding:0;list-style:none}.stepper li{position:relative;display:grid;place-items:center;gap:6px;color:var(--color-text-muted);font-size:11px}.stepper li:before{position:absolute;z-index:-1;top:13px;right:50%;left:-50%;height:2px;background:var(--color-border);content:""}.stepper li:first-child:before{display:none}.stepper li.active,.stepper li.done{color:var(--color-primary);font-weight:700}.stepper li.done:before,.stepper li.active:before{background:var(--color-primary)}.import-flow{max-width:960px;width:100%;display:grid;gap:20px;margin:0 auto}.drop-zone{display:grid;place-items:center;padding:60px 20px;border:2px dashed var(--color-border);border-radius:12px;text-align:center;cursor:pointer}.drop-zone:hover{border-color:var(--color-primary);background:color-mix(in srgb,var(--color-primary) 4%,var(--color-surface))}.drop-zone h2{margin:12px 0 5px;font-size:17px}.drop-zone p{margin:0;color:var(--color-text-muted);font-size:12px}.upload-mark{width:48px;height:48px;display:grid;place-items:center;border-radius:14px;background:var(--color-surface-elevated);font-size:24px}.file-row{padding-bottom:15px;border-bottom:1px solid var(--color-border)}.file-row>div{display:grid;gap:4px}.working{display:flex;align-items:center;gap:9px;padding:13px;border-radius:9px;background:var(--color-surface-elevated);font-size:12px}.spinner{width:14px;height:14px;border:2px solid var(--color-border);border-top-color:var(--color-primary);border-radius:50%;animation:spin .8s linear infinite}.validation-head{padding:14px;border:1px solid;border-radius:10px}.validation-head.valid{border-color:var(--color-success-border);background:var(--color-success-bg)}.validation-head.invalid{border-color:var(--color-danger-border);background:var(--color-danger-bg)}.validation-head>div{display:grid;gap:4px}.validation-head span{font-size:11px}.validation-head code,.history-card code{font-size:11px}.notice{display:flex;align-items:center;justify-content:space-between;gap:12px;padding:11px;border:1px solid;border-radius:9px;font-size:12px}.notice.warning{border-color:var(--color-warning-border);background:var(--color-warning-bg);color:var(--color-warning-text)}.notice.error{border-color:var(--color-danger-border);background:var(--color-danger-bg);color:var(--color-danger-text)}.review-section{display:grid;gap:10px;padding-top:4px}.count-grid{display:grid;grid-template-columns:repeat(4,1fr);gap:8px}.count-grid div{display:grid;gap:3px;padding:10px;border:1px solid var(--color-border);border-radius:8px}.count-grid strong{font-size:18px}.count-grid span{color:var(--color-text-muted);font-size:10px}.issue-group{overflow:hidden;border:1px solid var(--color-border);border-radius:9px}.issue-group h3{display:flex;justify-content:space-between;margin:0;padding:9px 11px;background:var(--color-surface-elevated);font-size:11px}.issue-group.must_fix{border-color:var(--color-danger-border)}.issue-group.will_adjust{border-color:var(--color-warning-border)}.issue-row{display:grid;grid-template-columns:minmax(120px,.6fr) 1.4fr;gap:10px;padding:9px 11px;border-top:1px solid var(--color-border);font-size:11px}.issue-row code{overflow-wrap:anywhere;color:var(--color-text-muted)}.manifest-details{padding:12px;border:1px solid var(--color-border);border-radius:9px;font-size:12px}.manifest-details summary{cursor:pointer;font-weight:650}.manifest-columns{display:grid;grid-template-columns:1fr 1fr;gap:20px}.confirmation{background:var(--color-surface-elevated)}.success-card{display:flex;gap:14px;padding:18px;border:1px solid var(--color-success-border);border-radius:11px;background:var(--color-success-bg);color:var(--color-success-text)}.success-card>span{font-size:22px}.success-card p{margin:5px 0;font-size:12px}.success-card a{color:inherit;font-weight:700}.history-card{display:grid;gap:18px}.table-wrap{overflow:auto;border:1px solid var(--color-border);border-radius:10px}table{width:100%;border-collapse:collapse}th,td{padding:11px 13px;text-align:left;white-space:nowrap}th{background:var(--color-surface-elevated);color:var(--color-text-muted);font-size:10px;text-transform:uppercase}td{border-top:1px solid var(--color-border);font-size:12px}.action-chip{padding:3px 7px;border-radius:6px;background:var(--color-surface-elevated);text-transform:capitalize}.empty{padding:35px;color:var(--color-text-muted);text-align:center}.sr-only{position:absolute;width:1px;height:1px;padding:0;margin:-1px;overflow:hidden;clip:rect(0,0,0,0);white-space:nowrap;border:0}@keyframes spin{to{transform:rotate(360deg)}}@media(max-width:850px){.workspace{grid-template-columns:1fr}.manifest{position:static}.form-grid,.manifest-columns{grid-template-columns:1fr}.count-grid{grid-template-columns:repeat(2,1fr)}.issue-row{grid-template-columns:1fr}.page-header{align-items:flex-start}.stepper li span{display:none}}
</style>
