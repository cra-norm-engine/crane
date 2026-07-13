<!--
  CRANE — CRA Norm Engine
  Copyright (C) 2026 Ali Mohammad Hosseini
  SPDX-License-Identifier: AGPL-3.0-or-later
  This file is part of CRANE, free software under the GNU AGPL v3.0 or later.
  See <https://www.gnu.org/licenses/>.
-->
<template>
  <!--
    DeclarationView — per-release EU Declaration of Conformity (CRA Art. 28 /
    Annex V). Shows a preview of the DoC content that backs the PDF, drives the
    draft -> approved -> signed workflow, and offers PDF downloads for both the
    DoC and the package label.
  -->
  <section class="doc-page">
    <div v-if="isLoading && !doc" class="doc-loading">Loading declaration…</div>

    <template v-else-if="doc">
      <header class="doc-head">
        <div>
          <div class="doc-eyebrow">Cyber Resilience Act · EU Declaration of Conformity</div>
          <h1 class="doc-title">{{ doc.product.name }} <span class="muted">{{ disp(doc.product.model) }}</span></h1>
          <div class="doc-meta">Manufacturer <b>{{ disp(doc.manufacturer.name) }}</b> · {{ doc.meta.generated_at }}</div>
        </div>
        <div class="doc-actions">
          <StatusBadge :label="statusLabel" :variant="statusVariant" />
          <AppButton
            v-if="canWrite && status === 'draft' && !editing"
            variant="secondary"
            size="sm"
            :disabled="busy"
            @click="startEdit"
          >Edit</AppButton>
          <AppButton variant="secondary" size="sm" :disabled="busy" @click="downloadDoc">
            {{ busy ? "Working…" : "Download DoC PDF" }}
          </AppButton>
          <AppButton variant="secondary" size="sm" :disabled="busy" @click="downloadLabel">
            Download package label
          </AppButton>
        </div>
      </header>

      <!-- Workflow controls (draft -> approved -> signed). Gated by release_write. -->
      <div v-if="canWrite" class="doc-flow">
        <div class="doc-flow-steps">
          <span :class="['flow-step', { on: order(doc.meta) >= 0 }]">Draft</span>
          <span class="flow-arrow">→</span>
          <span :class="['flow-step', { on: order(doc.meta) >= 1 }]">Approved</span>
          <span class="flow-arrow">→</span>
          <span :class="['flow-step', { on: doc.meta.is_signed }]">Signed</span>
        </div>
        <div class="doc-flow-actions">
          <AppButton
            v-if="status === 'draft'"
            variant="primary"
            size="sm"
            :disabled="busy"
            @click="approve"
          >Approve</AppButton>
          <AppButton
            v-if="status === 'approved'"
            variant="primary"
            size="sm"
            :disabled="busy"
            @click="sign"
          >Sign &amp; draw up</AppButton>
          <AppButton
            v-if="status === 'approved'"
            variant="ghost"
            size="sm"
            :disabled="busy"
            @click="reopen"
          >Return to draft</AppButton>
          <span v-if="status === 'signed'" class="doc-locked">Signed and locked — this declaration cannot be edited.</span>
        </div>
      </div>

      <!-- Editable DoC form (draft only). Only the manufacturer-supplied Annex V
           fields are editable here; product identity comes from the product record. -->
      <form v-if="editing" class="doc-edit" @submit.prevent="saveEdit">
        <div class="doc-edit-grid">
          <label class="field">
            <span>Declaration reference number</span>
            <input v-model.trim="form.eu_doc_number" type="text" maxlength="100" placeholder="e.g. DOC-2026-001" />
          </label>
          <label class="field">
            <span>Date of issue</span>
            <input v-model="form.eu_doc_date" type="date" />
          </label>
          <label class="field">
            <span>Signatory (name &amp; function)</span>
            <input v-model.trim="form.eu_doc_signatory" type="text" maxlength="255" placeholder="e.g. Jane Doe, CTO" />
          </label>
          <label class="field">
            <span>Simplified DoC URL</span>
            <input v-model.trim="form.eu_doc_url" type="url" maxlength="2048" placeholder="https://…" />
          </label>
          <label class="field">
            <span>Conformity module</span>
            <input v-model.trim="form.conformity_module" type="text" maxlength="255" placeholder="e.g. Module A" />
          </label>
          <label class="field">
            <span>Notified body</span>
            <input v-model.trim="form.eu_doc_notified_body" type="text" maxlength="255" />
          </label>
          <label class="field">
            <span>Notified body number</span>
            <input v-model.trim="form.notified_body_number" type="text" maxlength="255" />
          </label>
          <label class="field doc-edit-span-2">
            <span>Standards / specifications applied</span>
            <textarea v-model.trim="form.standards_applied" rows="2" placeholder="e.g. EN 18031-1:2024" />
          </label>
          <label class="field doc-edit-span-2">
            <span>CE marking details</span>
            <textarea v-model.trim="form.ce_marking_info" rows="2" placeholder="Notes on how/where the CE mark is affixed" />
          </label>
        </div>
        <div class="doc-edit-actions">
          <AppButton type="submit" variant="primary" size="sm" :disabled="busy">
            {{ busy ? "Saving…" : "Save" }}
          </AppButton>
          <AppButton type="button" variant="ghost" size="sm" :disabled="busy" @click="cancelEdit">Cancel</AppButton>
        </div>
      </form>

      <!-- Annex V preview: mirrors the generated PDF. -->
      <article v-else class="doc-body">
        <section class="doc-item">
          <div class="doc-n">1 · Declaration reference number</div>
          <div>{{ disp(doc.reference_no) }}</div>
        </section>

        <section class="doc-item">
          <div class="doc-n">2 · Manufacturer</div>
          <div><b>{{ disp(doc.manufacturer.name) }}</b></div>
          <div class="doc-addr">{{ disp(doc.manufacturer.address) }}</div>
          <dl class="kv">
            <div><dt>Contact e-mail</dt><dd>{{ disp(doc.manufacturer.contact_email) }}</dd></div>
            <div><dt>Contact URL</dt><dd>{{ disp(doc.manufacturer.contact_url) }}</dd></div>
            <div><dt>Authorised representative</dt><dd>{{ disp(doc.authorised_rep) }}</dd></div>
          </dl>
        </section>

        <section class="doc-item">
          <div class="doc-n">3 · Statement</div>
          <p class="doc-statement">{{ doc.sole_responsibility }}</p>
        </section>

        <section class="doc-item">
          <div class="doc-n">4 · Object of the declaration</div>
          <dl class="kv">
            <div><dt>Product name</dt><dd>{{ disp(doc.product.name) }}</dd></div>
            <div><dt>Model / identifier</dt><dd>{{ disp(doc.product.model) }}</dd></div>
            <div><dt>Type</dt><dd>{{ disp(doc.product.type) }}</dd></div>
            <div><dt>Version</dt><dd>{{ disp(doc.product.version) }}</dd></div>
            <div><dt>Hardware version</dt><dd>{{ disp(doc.product.hardware_version) }}</dd></div>
            <div><dt>Description</dt><dd>{{ disp(doc.product.description) }}</dd></div>
          </dl>
        </section>

        <section class="doc-item">
          <div class="doc-n">5 · Conformity assessment</div>
          <dl class="kv">
            <div><dt>Route</dt><dd>{{ disp(doc.conformity.route) }}</dd></div>
            <div><dt>Module</dt><dd>{{ disp(doc.conformity.module) }}</dd></div>
            <div><dt>Standards applied</dt><dd>{{ disp(doc.conformity.standards) }}</dd></div>
            <div><dt>Notified body</dt><dd>{{ disp(doc.conformity.notified_body) }}</dd></div>
            <div><dt>Notified body number</dt><dd>{{ disp(doc.conformity.nb_number) }}</dd></div>
          </dl>
        </section>

        <section class="doc-item">
          <div class="doc-n">6 · Additional information</div>
          <dl class="kv">
            <div><dt>CE marking</dt><dd>{{ disp(doc.ce_marking) }}</dd></div>
            <div><dt>Simplified DoC URL</dt><dd>{{ disp(doc.simplified_url) }}</dd></div>
          </dl>
        </section>

        <section class="doc-item">
          <div class="doc-n">Signature</div>
          <dl class="kv">
            <div><dt>Signatory</dt><dd>{{ disp(doc.signature.signatory) }}</dd></div>
            <div><dt>Date of issue</dt><dd>{{ disp(doc.signature.date) }}</dd></div>
            <div v-if="doc.meta.is_signed"><dt>Signed at</dt><dd>{{ disp(doc.signature.signed_at) }}</dd></div>
          </dl>
        </section>
      </article>
    </template>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from "vue";
import AppButton from "@/components/AppButton.vue";
import StatusBadge from "@/components/StatusBadge.vue";
import type { BadgeVariant } from "@/components/StatusBadge.vue";
import { useToast } from "@/composables/useToast";
import { useAuthStore } from "@/stores/auth";
import { euDeclarationService } from "@/services/eu-declaration-service";
import { packageLabelService } from "@/services/package-label-service";
import {
  DOC_PLACEHOLDER,
  type DeclarationData,
  type DeclarationEditFields,
  type DocStatus,
} from "@/types/declaration";

// releaseId comes from the route (props: true).
const props = defineProps<{ releaseId: string }>();

const auth = useAuthStore();
const { showToast } = useToast();

const doc = ref<DeclarationData | null>(null);
const isLoading = ref(false);
const busy = ref(false);
const editing = ref(false);

// Editable Annex V fields (draft only). Empty strings map to null on save.
const form = reactive<Record<keyof DeclarationEditFields, string>>({
  eu_doc_number: "",
  eu_doc_date: "",
  eu_doc_signatory: "",
  eu_doc_url: "",
  eu_doc_notified_body: "",
  notified_body_number: "",
  conformity_module: "",
  standards_applied: "",
  ce_marking_info: "",
});

// Only users who can write releases may drive the DoC workflow.
const canWrite = computed(() => auth.hasPermission("release_write"));

// Resolve the current DoC status from the preview meta.
const status = computed<DocStatus>(() => {
  if (!doc.value) return "draft";
  if (doc.value.meta.is_signed) return "signed";
  const s = doc.value.meta.status.toLowerCase();
  return s.includes("approved") ? "approved" : "draft";
});

const statusLabel = computed(() => doc.value?.meta.status ?? "Draft");
const statusVariant = computed<BadgeVariant>(() => {
  switch (status.value) {
    case "signed":
      return "success";
    case "approved":
      return "info";
    default:
      return "neutral";
  }
});

// Render the placeholder sentinel as a friendly dash.
function disp(v: string | null | undefined): string {
  if (v == null || v === DOC_PLACEHOLDER || v === "") return "—";
  return v;
}

// Map status to a step index for the progress strip.
function order(meta: DeclarationData["meta"]): number {
  if (meta.is_signed) return 2;
  return meta.status.toLowerCase().includes("approved") ? 1 : 0;
}

async function load(): Promise<void> {
  isLoading.value = true;
  try {
    doc.value = await euDeclarationService.getData(props.releaseId);
  } catch {
    showToast({ type: "error", message: "Failed to load the declaration." });
  } finally {
    isLoading.value = false;
  }
}

// Convert a preview value to a form value (placeholder / dash -> empty string).
function toField(v: string | null | undefined): string {
  if (v == null || v === DOC_PLACEHOLDER || v === "" || v === "—") return "";
  return v;
}

// Open the edit form, seeding it from the current preview values.
function startEdit(): void {
  if (!doc.value) return;
  const d = doc.value;
  form.eu_doc_number = toField(d.reference_no);
  // eu_doc_date is shown formatted in the preview; the user re-enters it here if
  // needed (approval also auto-stamps today when left blank).
  form.eu_doc_date = "";
  form.eu_doc_signatory = toField(d.signature.signatory);
  form.eu_doc_url = toField(d.simplified_url);
  form.eu_doc_notified_body = toField(d.conformity.notified_body);
  form.notified_body_number = toField(d.conformity.nb_number);
  form.conformity_module = toField(d.conformity.module);
  form.standards_applied = toField(d.conformity.standards);
  form.ce_marking_info = toField(d.ce_marking);
  editing.value = true;
}

function cancelEdit(): void {
  editing.value = false;
}

async function saveEdit(): Promise<void> {
  busy.value = true;
  try {
    // Send empty strings as null so cleared fields are stored as "not recorded".
    const payload: Partial<DeclarationEditFields> = {};
    (Object.keys(form) as (keyof DeclarationEditFields)[]).forEach((k) => {
      payload[k] = form[k].trim() === "" ? null : form[k].trim();
    });
    await euDeclarationService.update(props.releaseId, payload);
    showToast({ type: "success", message: "Declaration updated." });
    editing.value = false;
    await load();
  } catch (e) {
    showToast({ type: "error", message: errMsg(e, "Could not save the declaration.") });
  } finally {
    busy.value = false;
  }
}

async function approve(): Promise<void> {
  busy.value = true;
  try {
    await euDeclarationService.approve(props.releaseId);
    showToast({ type: "success", message: "Declaration approved and signature recorded." });
    await load();
  } catch (e) {
    showToast({ type: "error", message: errMsg(e, "Approval failed.") });
  } finally {
    busy.value = false;
  }
}

async function sign(): Promise<void> {
  busy.value = true;
  try {
    await euDeclarationService.sign(props.releaseId);
    showToast({ type: "success", message: "Declaration signed and drawn up." });
    await load();
  } catch (e) {
    showToast({ type: "error", message: errMsg(e, "Signing failed.") });
  } finally {
    busy.value = false;
  }
}

async function reopen(): Promise<void> {
  busy.value = true;
  try {
    await euDeclarationService.submit(props.releaseId);
    showToast({ type: "success", message: "Declaration returned to draft." });
    await load();
  } catch (e) {
    showToast({ type: "error", message: errMsg(e, "Could not reopen the declaration.") });
  } finally {
    busy.value = false;
  }
}

async function downloadDoc(): Promise<void> {
  busy.value = true;
  try {
    await euDeclarationService.downloadPdf(props.releaseId);
  } catch {
    showToast({ type: "error", message: "Failed to generate the DoC PDF." });
  } finally {
    busy.value = false;
  }
}

async function downloadLabel(): Promise<void> {
  busy.value = true;
  try {
    await packageLabelService.downloadPdf(props.releaseId);
  } catch {
    showToast({ type: "error", message: "Failed to generate the package label." });
  } finally {
    busy.value = false;
  }
}

// Extract a human-readable message from an Axios-style error (backend conflicts
// carry a `detail` string explaining why a transition was rejected).
function errMsg(e: unknown, fallback: string): string {
  const detail = (e as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
  return typeof detail === "string" ? detail : fallback;
}

onMounted(load);
</script>

<style scoped>
.doc-page {
  max-width: 900px;
  margin: 0 auto;
  padding: 24px 20px 60px;
}
.doc-loading {
  color: var(--color-text-muted);
  padding: 40px 0;
}
.doc-head {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 16px;
  flex-wrap: wrap;
  margin-bottom: 16px;
}
.doc-eyebrow {
  font-family: monospace;
  font-size: 11px;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  color: var(--color-text-muted, #8b9290);
}
.doc-title {
  font-size: 22px;
  margin: 4px 0 2px;
}
.doc-title .muted,
.muted {
  color: var(--color-text-muted, #8b9290);
  font-weight: 400;
}
.doc-meta {
  font-size: 13px;
  color: var(--color-text-muted, #5b6260);
}
.doc-actions {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}
.doc-flow {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 16px;
  flex-wrap: wrap;
  padding: 12px 16px;
  border: 1px solid var(--color-border);
  border-radius: 8px;
  background: var(--color-surface-elevated);
  margin-bottom: 20px;
}
.doc-flow-steps {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
}
.flow-step {
  color: var(--color-text-muted, #8b9290);
  font-family: monospace;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  font-size: 11px;
}
.flow-step.on {
  color: var(--color-primary);
  font-weight: 600;
}
.flow-arrow {
  color: var(--color-text-muted, #b0b0b0);
}
.doc-flow-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}
.doc-locked {
  font-size: 12.5px;
  color: var(--color-primary);
}
.doc-item {
  padding: 14px 0;
  border-bottom: 1px solid var(--color-border, #efeadf);
}
.doc-n {
  font-family: monospace;
  font-size: 11px;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  color: var(--color-text-muted, #8b9290);
  margin-bottom: 6px;
}
.doc-addr {
  white-space: pre-line;
  color: var(--color-text-muted, #5b6260);
  margin-top: 2px;
}
.doc-statement {
  background: var(--color-surface-elevated);
  border-left: 3px solid var(--color-primary);
  padding: 10px 14px;
  margin: 4px 0 0;
  font-size: 14px;
  color: var(--color-text);
}
dl.kv {
  margin: 8px 0 0;
}
dl.kv > div {
  display: flex;
  gap: 12px;
  padding: 4px 0;
}
dl.kv dt {
  flex: 0 0 34%;
  font-family: monospace;
  font-size: 11px;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  color: var(--color-text-muted, #8b9290);
}
dl.kv dd {
  margin: 0;
  font-size: 14px;
}

/* Editable DoC form (draft only). */
.doc-edit {
  border: 1px solid var(--color-border);
  border-radius: 8px;
  background: var(--color-surface-elevated);
  padding: 16px;
  margin-bottom: 20px;
}
.doc-edit-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px 16px;
}
.doc-edit .field {
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.doc-edit .field.doc-edit-span-2 {
  grid-column: 1 / -1;
}
.doc-edit .field > span {
  font-family: monospace;
  font-size: 11px;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  color: var(--color-text-muted);
}
.doc-edit input,
.doc-edit textarea {
  width: 100%;
  padding: 7px 10px;
  border: 1px solid var(--color-border);
  border-radius: 6px;
  background: var(--color-bg);
  color: var(--color-text);
  font: inherit;
  font-size: 14px;
}
.doc-edit textarea {
  resize: vertical;
}
.doc-edit-actions {
  display: flex;
  gap: 8px;
  margin-top: 14px;
}
@media (max-width: 640px) {
  .doc-edit-grid {
    grid-template-columns: 1fr;
  }
}
</style>
