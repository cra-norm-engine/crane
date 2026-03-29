<template>
  <section class="page">
    <header class="page-header card">
      <div>
        <h1 class="page-title">Security update history</h1>
        <p class="muted page-subtitle">
          Track security updates issued for a product release, including CVEs addressed,
          affected versions, distribution mechanism, and retention availability.
        </p>
      </div>

      <div class="page-actions">
        <input
          v-model.trim="productReleaseId"
          type="text"
          placeholder="Product release ID"
        />
        <button class="btn btn-secondary" type="button" @click="loadUpdates" :disabled="isLoading">
          {{ isLoading ? "Refreshing..." : "Load" }}
        </button>
      </div>
    </header>

    <div v-if="errorMessage" class="card feedback feedback-error">
      {{ errorMessage }}
    </div>

    <div v-if="successMessage" class="card feedback feedback-success">
      {{ successMessage }}
    </div>

    <section class="card form-card">
      <div class="section-header">
        <div>
          <h2 class="section-title">Create security update</h2>
          <p class="muted">Development Team can add updates for the selected release.</p>
        </div>
      </div>

      <form class="form-grid" @submit.prevent="createUpdate">
        <label class="field">
          <span class="field-label">Product release ID</span>
          <input v-model.trim="createForm.product_release_id" type="text" required />
        </label>

        <label class="field">
          <span class="field-label">Title</span>
          <input v-model.trim="createForm.title" type="text" required />
        </label>

        <label class="field field-span-2">
          <span class="field-label">Description</span>
          <textarea v-model.trim="createForm.description" rows="3" />
        </label>

        <label class="field">
          <span class="field-label">Distribution mechanism</span>
          <select v-model="createForm.distribution_mechanism">
            <option value="automatic_update">Automatic update</option>
            <option value="in_app_update">In-app update</option>
            <option value="package_repository">Package repository</option>
            <option value="vendor_download">Vendor download</option>
            <option value="manual_install">Manual install</option>
            <option value="field_service">Field service</option>
            <option value="other">Other</option>
          </select>
        </label>

        <label class="field">
          <span class="field-label">Released at</span>
          <input v-model="createForm.released_at" type="datetime-local" />
        </label>

        <label class="field">
          <span class="field-label">Available until</span>
          <input v-model="createForm.available_until" type="datetime-local" />
        </label>

        <label class="field field-span-2">
          <span class="field-label">CVEs addressed (comma separated)</span>
          <input v-model.trim="cveInput" type="text" placeholder="CVE-2026-0001, CVE-2026-0002" />
        </label>

        <label class="field field-span-2">
          <span class="field-label">Affected versions (comma separated)</span>
          <input v-model.trim="versionsInput" type="text" placeholder="1.0.0, 1.0.1" />
        </label>

        <div class="field field-span-2 inline-actions">
          <button class="btn btn-primary" type="submit" :disabled="isCreating">
            {{ isCreating ? "Saving..." : "Create security update" }}
          </button>
        </div>
      </form>
    </section>

    <section class="card">
      <div class="section-header">
        <div>
          <h2 class="section-title">History</h2>
          <p class="muted">{{ updates.length }} update(s)</p>
        </div>
      </div>

      <div v-if="isLoading" class="empty-panel">
        Loading security updates…
      </div>

      <div v-else-if="updates.length === 0" class="empty-panel">
        No security updates found.
      </div>

      <div v-else class="table-wrapper">
        <table class="data-table">
          <thead>
            <tr>
              <th>Title</th>
              <th>Distribution</th>
              <th>Released</th>
              <th>Available until</th>
              <th>CVEs</th>
              <th>Affected versions</th>
            </tr>
          </thead>

          <tbody>
            <tr v-for="item in updates" :key="item.id">
              <td>
                <strong>{{ item.title }}</strong>
                <p class="cell-text">{{ item.description || "No description provided." }}</p>
              </td>
              <td>{{ formatDistribution(item.distribution_mechanism) }}</td>
              <td>{{ formatDateTime(item.released_at) }}</td>
              <td>{{ formatDateTime(item.available_until) }}</td>
              <td>
                <template v-if="Array.isArray(item.cves_addressed_json)">
                  {{ item.cves_addressed_json.join(", ") || "—" }}
                </template>
                <template v-else>
                  {{ JSON.stringify(item.cves_addressed_json) }}
                </template>
              </td>
              <td>
                <template v-if="Array.isArray(item.affected_versions_json)">
                  {{ item.affected_versions_json.join(", ") || "—" }}
                </template>
                <template v-else>
                  {{ JSON.stringify(item.affected_versions_json) }}
                </template>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>
  </section>
</template>

<script setup lang="ts">
import { reactive, ref } from "vue";

import { securityUpdateService } from "@/services/security-update-service";
import type { DistributionMechanism, SecurityUpdateCreate, SecurityUpdateRead } from "@/types/product";

const updates = ref<SecurityUpdateRead[]>([]);
const productReleaseId = ref("");
const isLoading = ref(false);
const isCreating = ref(false);
const errorMessage = ref("");
const successMessage = ref("");

const cveInput = ref("");
const versionsInput = ref("");

const createForm = reactive({
  product_release_id: "",
  title: "",
  description: "",
  distribution_mechanism: "vendor_download" as DistributionMechanism,
  released_at: "",
  available_until: "",
});

function toIsoOrNull(value: string): string | null {
  if (!value) return null;
  return new Date(value).toISOString();
}

function formatDateTime(value: string | null): string {
  if (!value) return "—";
  return new Intl.DateTimeFormat(undefined, {
    year: "numeric",
    month: "short",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  }).format(new Date(value));
}

function formatDistribution(value: string): string {
  return value.replaceAll("_", " ");
}

function parseCommaSeparated(value: string): string[] {
  return value
    .split(",")
    .map((entry) => entry.trim())
    .filter(Boolean);
}

async function loadUpdates(): Promise<void> {
  if (!productReleaseId.value.trim()) {
    updates.value = [];
    return;
  }

  isLoading.value = true;
  errorMessage.value = "";

  try {
    updates.value = await securityUpdateService.list(productReleaseId.value.trim());
  } catch (error) {
    errorMessage.value =
      error instanceof Error ? error.message : "Failed to load security updates.";
  } finally {
    isLoading.value = false;
  }
}

async function createUpdate(): Promise<void> {
  isCreating.value = true;
  errorMessage.value = "";
  successMessage.value = "";

  try {
    const payload: SecurityUpdateCreate = {
      product_release_id: createForm.product_release_id.trim(),
      title: createForm.title.trim(),
      description: createForm.description.trim() || null,
      distribution_mechanism: createForm.distribution_mechanism,
      cves_addressed_json: parseCommaSeparated(cveInput.value),
      affected_versions_json: parseCommaSeparated(versionsInput.value),
      released_at: toIsoOrNull(createForm.released_at),
      available_until: toIsoOrNull(createForm.available_until),
    };

    await securityUpdateService.create(payload);
    successMessage.value = "Security update created.";

    productReleaseId.value = payload.product_release_id;
    createForm.title = "";
    createForm.description = "";
    createForm.released_at = "";
    createForm.available_until = "";
    cveInput.value = "";
    versionsInput.value = "";

    await loadUpdates();
  } catch (error) {
    errorMessage.value =
      error instanceof Error ? error.message : "Failed to create security update.";
  } finally {
    isCreating.value = false;
  }
}
</script>

<style scoped>
.page {
  display: grid;
  gap: 1rem;
}

.page-header,
.section-header,
.inline-actions {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 1rem;
  flex-wrap: wrap;
}

.page-actions {
  display: flex;
  gap: 0.75rem;
  flex-wrap: wrap;
}

.page-title,
.section-title {
  margin: 0;
}

.page-subtitle {
  margin-top: 0.35rem;
}

.form-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 1rem;
}

.field {
  display: grid;
  gap: 0.45rem;
}

.field-span-2 {
  grid-column: span 2;
}

.field-label {
  color: var(--color-text-muted, #94a3b8);
  font-size: 0.85rem;
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
  box-sizing: border-box;
}

.feedback,
.empty-panel {
  padding: 1rem 1.1rem;
  border-radius: 1rem;
  background: var(--color-surface-soft, rgba(15, 23, 42, 0.45));
}

.feedback-error {
  color: #fda4af;
}

.feedback-success {
  color: #86efac;
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
  padding: 0.85rem 0.75rem;
  text-align: left;
  border-bottom: 1px solid var(--color-border, rgba(148, 163, 184, 0.18));
  vertical-align: top;
}

.data-table th {
  color: var(--color-text-muted, #94a3b8);
  font-size: 0.85rem;
  font-weight: 600;
  white-space: nowrap;
}

.cell-text {
  margin: 0.35rem 0 0;
  line-height: 1.5;
}

.btn {
  border: 1px solid transparent;
  border-radius: 0.85rem;
  padding: 0.75rem 1rem;
  font: inherit;
  cursor: pointer;
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

.muted {
  color: var(--color-text-muted, #94a3b8);
}

@media (max-width: 800px) {
  .form-grid {
    grid-template-columns: 1fr;
  }

  .field-span-2 {
    grid-column: span 1;
  }
}
</style>