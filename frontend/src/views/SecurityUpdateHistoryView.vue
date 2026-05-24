<template>
  <section class="page">
    <header class="page-header">
      <div>
        <h1 class="page-title">Security updates</h1>
        <p class="muted page-subtitle">
          Track security updates issued for a product release, including CVEs addressed,
          affected versions, distribution mechanism, and retention availability.
        </p>
      </div>

      <div class="page-actions">
        <label class="field">
          <span class="field-label">Search products</span>
          <input
            v-model.trim="productQuery"
            type="text"
            placeholder="Search by product name or code"
          />
        </label>

        <label class="field">
          <span class="field-label">Product</span>
          <select v-model="selectedProductId" :disabled="isLoadingProducts || filteredProducts.length === 0">
            <option value="">{{ isLoadingProducts ? "Loading products..." : "All products" }}</option>
            <option v-for="product in filteredProducts" :key="product.id" :value="product.id">
              {{ product.name }} ({{ product.product_code }})
            </option>
          </select>
        </label>

        <label class="field">
          <span class="field-label">Release display_version</span>
          <select
            v-model="selectedReleaseId"
            :disabled="!selectedProductId || isLoadingReleases || releases.length === 0"
          >
            <option value="">
              {{
                !selectedProductId
                  ? "Select a product first"
                  : isLoadingReleases
                    ? "Loading releases..."
                    : releases.length === 0
                      ? "No releases found"
                      : "Select a release"
              }}
            </option>
            <option v-for="release in releases" :key="release.id" :value="release.id">
              {{ formatReleaseOption(release) }}
            </option>
          </select>
        </label>

        <button
          class="button"
          type="button"
          @click="showCreateModal = true"
        >
          + New security update
        </button>
      </div>

      <p v-if="selectedProduct && selectedRelease" class="selection-summary muted">
        Selected release: {{ selectedProduct.name }} · {{ selectedRelease.display_version }}
        ({{ formatLabel(selectedRelease.release_status) }})
      </p>
    </header>

    <div v-if="errorMessage" class="card feedback feedback-error">
      {{ errorMessage }}
    </div>

    <div v-if="successMessage" class="card feedback feedback-success">
      {{ successMessage }}
    </div>

    <section class="card">
      <div class="section-header">
        <div>
          <h2 class="section-title">History</h2>
          <p class="muted">{{ updates.length }} update(s) — click a row to view details</p>
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
              <th>Severity</th>
              <th>Type</th>
              <th>CVEs</th>
              <th>Released</th>
              <th>Available until</th>
              <th></th>
            </tr>
          </thead>

          <tbody>
            <tr
              v-for="item in updates"
              :key="item.id"
              class="table-row-clickable"
              @click="openDetail(item)"
              tabindex="0"
              @keydown.enter="openDetail(item)"
              @keydown.space.prevent="openDetail(item)"
              :aria-label="`View details for ${item.title}`"
            >
              <td>
                <strong>{{ item.title }}</strong>
                <p v-if="item.description" class="cell-text cell-desc">{{ item.description }}</p>
              </td>
              <td>
                <span v-if="item.severity" class="severity-badge" :class="`severity-${item.severity}`">
                  {{ item.severity }}
                </span>
                <span v-else class="muted">—</span>
              </td>
              <td>
                <span class="type-badge" :class="item.is_security_only ? 'type-security' : 'type-mixed'">
                  {{ item.is_security_only ? "Security only" : "Mixed" }}
                </span>
              </td>
              <td>
                <template v-if="Array.isArray(item.cves_addressed_json) && item.cves_addressed_json.length">
                  <span class="cve-pill" v-for="cve in (item.cves_addressed_json as string[]).slice(0, 3)" :key="cve">{{ cve }}</span>
                  <span v-if="(item.cves_addressed_json as string[]).length > 3" class="muted">+{{ (item.cves_addressed_json as string[]).length - 3 }} more</span>
                </template>
                <span v-else class="muted">—</span>
              </td>
              <td class="nowrap">{{ formatDateTime(item.released_at) }}</td>
              <td class="nowrap">{{ formatDateTime(item.available_until) }}</td>
              <td class="row-arrow">›</td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>
  </section>

  <!-- ── Create Security Update Modal ── -->
  <AppModal
    v-model="showCreateModal"
    title="Create security update"
    size="lg"
    :persistent="true"
  >
    <form id="create-security-update-form" class="form-grid" @submit.prevent="createUpdate">
      <!-- Selected release indicator -->
      <div class="field field-span-2">
        <span class="field-label">Selected release</span>
        <div class="selection-card" :class="{ 'selection-card-empty': !selectedRelease || !selectedProduct }">
          <template v-if="selectedRelease && selectedProduct">
            <strong>{{ selectedProduct.name }} · Release {{ selectedRelease.display_version }}</strong>
            <span class="muted">
              Product code {{ selectedProduct.product_code }} ·
              Status {{ formatLabel(selectedRelease.release_status) }}
            </span>
          </template>
          <span v-else class="muted">
            Close this dialog, search for a product and select a release, then re-open to create an update.
          </span>
        </div>
      </div>

      <label class="field">
        <span class="field-label">Title</span>
        <input v-model.trim="createForm.title" type="text" required />
      </label>

      <label class="field">
        <span class="field-label">Severity (CVSS)</span>
        <select v-model="createForm.severity">
          <option value="">— Not specified —</option>
          <option value="critical">Critical</option>
          <option value="high">High</option>
          <option value="medium">Medium</option>
          <option value="low">Low</option>
          <option value="informational">Informational</option>
        </select>
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
        <span class="field-label">Release date</span>
        <input v-model="createForm.released_at" type="date" />
      </label>

      <div class="field">
        <span class="field-label">Available until</span>
        <input v-model="createForm.available_until" type="date" />
        <div v-if="retentionMinDate" class="retention-hint" :class="{ 'retention-warning': isAvailableUntilTooEarly }">
          <span v-if="isAvailableUntilTooEarly">⚠ CRA requires availability until at least {{ formatDate(retentionMinDate) }}</span>
          <span v-else class="muted">CRA minimum: {{ formatDate(retentionMinDate) }}</span>
        </div>
      </div>

      <label class="field field-span-2">
        <span class="field-label">Update channels</span>
        <div class="channels-list">
          <div v-for="(ch, idx) in createForm.update_channels_json" :key="idx" class="channel-row">
            <input
              :value="ch"
              type="text"
              placeholder="e.g. https://updates.example.com or Package repo"
              @input="updateChannel(idx, ($event.target as HTMLInputElement).value)"
            />
            <button type="button" class="btn btn-icon btn-remove" @click="removeChannel(idx)" title="Remove">✕</button>
          </div>
          <button type="button" class="btn btn-secondary btn-sm" @click="addChannel">+ Add channel</button>
        </div>
      </label>

      <label class="field field-span-2">
        <span class="field-label">Integrity / authenticity info</span>
        <textarea
          v-model.trim="createForm.integrity_info"
          rows="2"
          placeholder="Paste SHA256 hash, or note that code signing is used (e.g. 'Signed with EV certificate, SHA256: abc123...')"
        />
      </label>

      <label class="field field-span-2">
        <span class="field-label">CVEs addressed (comma separated)</span>
        <input v-model.trim="cveInput" type="text" placeholder="CVE-2026-0001, CVE-2026-0002" />
      </label>

      <div class="field field-span-2">
        <span class="field-label">Affected versions</span>
        <div v-if="!selectedProductId" class="versions-empty">
          Select a product first to choose affected versions.
        </div>
        <div v-else-if="releases.length === 0" class="versions-empty">
          No releases found for this product.
        </div>
        <div v-else class="versions-checklist">
          <label
            v-for="release in releases"
            :key="release.id"
            class="display_version-option"
          >
            <input
              type="checkbox"
              :value="release.display_version"
              v-model="selectedVersions"
            />
            <span class="display_version-label">
              <strong>{{ release.display_version }}</strong>
              <span class="display_version-status">{{ formatLabel(release.release_status) }}</span>
              <span v-if="release.actual_release_date ?? release.planned_release_date" class="display_version-date muted">
                · {{ formatDate(release.actual_release_date ?? release.planned_release_date) }}
              </span>
            </span>
          </label>
        </div>
      </div>

      <!-- Gap 5 — CVSS numeric score and vector -->
      <label class="field">
        <span class="field-label">CVSS score (0.0 – 10.0)</span>
        <input v-model.number="createForm.cvss_score" type="number" min="0" max="10" step="0.1" placeholder="e.g. 8.1" />
      </label>

      <label class="field">
        <span class="field-label">CVSS vector string</span>
        <input v-model.trim="createForm.cvss_vector" type="text" placeholder="e.g. CVSS:3.1/AV:N/AC:L/..." />
      </label>

      <!-- Gap 8 — SLA: vulnerability discovery date and remediation deadline -->
      <label class="field">
        <span class="field-label">Vulnerability discovered</span>
        <input v-model="createForm.vulnerability_discovered_at" type="date" />
      </label>

      <label class="field">
        <span class="field-label">Remediation deadline</span>
        <input v-model="createForm.remediation_deadline" type="date" />
        <p class="muted" style="font-size: var(--text-xs); margin-top: 0.25rem;">
          CRA "without delay" — typically 90 days from discovery
        </p>
      </label>

      <div class="field field-span-2">
        <label class="checkbox-label">
          <input type="checkbox" v-model="createForm.is_security_only" />
          <span>
            <strong>Security-only update</strong>
            <span class="muted"> — this update contains only security fixes, with no functional changes (CRA Art. 14)</span>
          </span>
        </label>
      </div>

      <!-- Gap 9 — free of charge flag -->
      <div class="field field-span-2">
        <label class="checkbox-label">
          <input type="checkbox" v-model="createForm.is_free_of_charge" />
          <span>
            <strong>Free of charge</strong>
            <span class="muted"> — Annex I Part II §8 requires security updates to be provided free of charge</span>
          </span>
        </label>
        <div v-if="!createForm.is_free_of_charge" class="retention-warning" style="margin-top: 0.4rem;">
          ⚠ This update is marked as paid. CRA compliance requires security updates to be free.
        </div>
      </div>
    </form>

    <template #footer>
      <button
        class="btn btn-secondary"
        type="button"
        :disabled="isCreating"
        @click="showCreateModal = false"
      >
        Cancel
      </button>
      <button
        class="btn btn-primary"
        type="submit"
        form="create-security-update-form"
        :disabled="isCreating || !createForm.product_release_id.trim()"
      >
        {{ isCreating ? "Saving..." : "Create security update" }}
      </button>
    </template>
  </AppModal>

  <!-- ── Security Update Detail Modal ── -->
  <Teleport to="body">
    <Transition name="modal">
      <div
        v-if="detailItem"
        class="modal-backdrop"
        @click.self="closeDetail"
        role="dialog"
        aria-modal="true"
        :aria-label="detailItem.title"
      >
        <div class="detail-modal" @keydown.esc="closeDetail">
          <!-- Header -->
          <div class="detail-header">
            <div class="detail-header-left">
              <div class="detail-badges">
                <span
                  v-if="detailItem.severity"
                  class="severity-badge"
                  :class="`severity-${detailItem.severity}`"
                >
                  {{ detailItem.severity.toUpperCase() }}
                </span>
                <span class="type-badge" :class="detailItem.is_security_only ? 'type-security' : 'type-mixed'">
                  {{ detailItem.is_security_only ? "Security only" : "Mixed update" }}
                </span>
              </div>
              <h2 class="detail-title">{{ detailItem.title }}</h2>
              <p v-if="detailItem.description" class="detail-description">{{ detailItem.description }}</p>
            </div>
            <button class="btn btn-icon btn-close" @click="closeDetail" aria-label="Close">✕</button>
          </div>

          <!-- Body -->
          <div class="detail-body">

            <!-- Timeline row -->
            <div class="detail-timeline">
              <div class="timeline-item">
                <span class="timeline-label">Released</span>
                <span class="timeline-value">{{ formatDateTime(detailItem.released_at) }}</span>
              </div>
              <div class="timeline-sep">→</div>
              <div class="timeline-item">
                <span class="timeline-label">Available until</span>
                <span class="timeline-value">{{ formatDateTime(detailItem.available_until) }}</span>
              </div>
            </div>

            <!-- Two-column detail grid -->
            <div class="detail-grid">

              <!-- Distribution -->
              <div class="detail-section">
                <h3 class="detail-section-title">Distribution</h3>
                <div class="detail-kv">
                  <span class="detail-key">Mechanism</span>
                  <span class="detail-val">{{ formatDistribution(detailItem.distribution_mechanism) }}</span>
                </div>
                <div class="detail-kv">
                  <span class="detail-key">Channels</span>
                  <div class="detail-val">
                    <template v-if="detailItem.update_channels_json && detailItem.update_channels_json.length">
                      <div
                        v-for="(ch, i) in detailItem.update_channels_json"
                        :key="i"
                        class="channel-chip"
                      >
                        <span class="channel-icon">⇡</span>{{ ch }}
                      </div>
                    </template>
                    <span v-else class="muted">Not specified</span>
                  </div>
                </div>
              </div>

              <!-- Integrity & Authenticity -->
              <div class="detail-section">
                <h3 class="detail-section-title">Integrity &amp; Authenticity</h3>
                <div class="detail-kv">
                  <span class="detail-key">Info</span>
                  <div class="detail-val">
                    <span v-if="detailItem.integrity_info" class="integrity-block">{{ detailItem.integrity_info }}</span>
                    <span v-else class="muted">Not specified</span>
                  </div>
                </div>
              </div>

              <!-- CVEs -->
              <div class="detail-section">
                <h3 class="detail-section-title">CVEs Addressed</h3>
                <div class="detail-val">
                  <template v-if="Array.isArray(detailItem.cves_addressed_json) && (detailItem.cves_addressed_json as string[]).length">
                    <div class="cve-list">
                      <span
                        v-for="cve in (detailItem.cves_addressed_json as string[])"
                        :key="cve"
                        class="cve-pill cve-pill-lg"
                      >{{ cve }}</span>
                    </div>
                  </template>
                  <span v-else class="muted">None recorded</span>
                </div>
              </div>

              <!-- Affected versions -->
              <div class="detail-section">
                <h3 class="detail-section-title">Affected Versions</h3>
                <div class="detail-val">
                  <template v-if="Array.isArray(detailItem.affected_versions_json) && (detailItem.affected_versions_json as string[]).length">
                    <div class="display_version-tags">
                      <span
                        v-for="v in (detailItem.affected_versions_json as string[])"
                        :key="v"
                        class="display_version-tag"
                      >{{ v }}</span>
                    </div>
                  </template>
                  <span v-else class="muted">None recorded</span>
                </div>
              </div>

            </div>
          </div>

          <!-- Footer -->
          <div class="detail-footer">
            <span class="muted detail-id">ID: {{ detailItem.id }}</span>
            <button class="btn btn-secondary" @click="closeDetail">Close</button>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref, watch } from "vue";

import AppModal from "@/components/AppModal.vue";
import { apiClient } from "@/services/api";
import { productReleaseService } from "@/services/product-release-service";
import { productService } from "@/services/product-service";
import { securityUpdateService } from "@/services/security-update-service";
import { supportPeriodService } from "@/services/support-period-service";
import type { ProductReleaseRead } from "@/types/release-gate";
import type {
  DistributionMechanism,
  ProductSummaryRead,
  SecurityUpdateCreate,
  SecurityUpdateRead,
  SecurityUpdateSeverity,
} from "@/types/product";

const updates = ref<SecurityUpdateRead[]>([]);
const detailItem = ref<SecurityUpdateRead | null>(null);
const showCreateModal = ref(false);
const isLoading = ref(false);
const isCreating = ref(false);
const isLoadingProducts = ref(false);
const isLoadingReleases = ref(false);
const errorMessage = ref("");
const successMessage = ref("");
const products = ref<ProductSummaryRead[]>([]);
const releases = ref<ProductReleaseRead[]>([]);
const productQuery = ref("");
const selectedProductId = ref("");
const selectedReleaseId = ref("");
const supportEndDate = ref<string | null>(null);

const cveInput = ref("");
const selectedVersions = ref<string[]>([]);

const createForm = reactive({
  product_release_id: "",
  title: "",
  description: "",
  severity: "" as SecurityUpdateSeverity | "",
  is_security_only: true,
  integrity_info: "",
  update_channels_json: [] as string[],
  distribution_mechanism: "vendor_download" as DistributionMechanism,
  released_at: "",
  available_until: "",
  // Gap 5 — CVSS score and vector
  cvss_score: null as number | null,
  cvss_vector: "",
  // Gap 8 — SLA tracking
  vulnerability_discovered_at: "",
  remediation_deadline: "",
  // Gap 9 — free of charge
  is_free_of_charge: true,
});

const filteredProducts = computed(() => {
  const query = productQuery.value.trim().toLowerCase();
  const productList = [...products.value].sort((left, right) => left.name.localeCompare(right.name));
  if (!query) {
    return productList;
  }

  return productList.filter((product) => {
    const haystack = [
      product.name,
      product.product_code,
      product.manufacturer_name,
      product.product_type,
    ]
      .join(" ")
      .toLowerCase();
    return haystack.includes(query);
  });
});

const selectedProduct = computed(
  () => products.value.find((product: ProductSummaryRead) => product.id === selectedProductId.value) ?? null,
);

const selectedRelease = computed(
  () => releases.value.find((release: ProductReleaseRead) => release.id === selectedReleaseId.value) ?? null,
);

const retentionMinDate = computed((): string | null => {
  const releasedAt = createForm.released_at;
  if (!releasedAt && !supportEndDate.value) return null;

  const candidates: Date[] = [];

  if (releasedAt) {
    const d = new Date(`${releasedAt}T00:00:00Z`);
    d.setUTCFullYear(d.getUTCFullYear() + 10);
    candidates.push(d);
  }

  if (supportEndDate.value) {
    candidates.push(new Date(supportEndDate.value));
  }

  if (candidates.length === 0) return null;
  const max = new Date(Math.max(...candidates.map((c) => c.getTime())));
  return max.toISOString().slice(0, 10);
});

const isAvailableUntilTooEarly = computed((): boolean => {
  if (!retentionMinDate.value || !createForm.available_until) return false;
  return createForm.available_until < retentionMinDate.value;
});

function addChannel(): void {
  createForm.update_channels_json.push("");
}

function removeChannel(idx: number): void {
  createForm.update_channels_json.splice(idx, 1);
}

function updateChannel(idx: number, value: string): void {
  createForm.update_channels_json[idx] = value;
}

function toIsoOrNull(value: string): string | null {
  if (!value) return null;
  return new Date(`${value}T00:00:00Z`).toISOString();
}

function formatDate(value: string | null): string {
  if (!value) return "No date";
  return new Intl.DateTimeFormat(undefined, {
    year: "numeric",
    month: "short",
    day: "2-digit",
  }).format(new Date(value));
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

function formatLabel(value: string): string {
  return value.replaceAll("_", " ");
}

function formatReleaseOption(release: ProductReleaseRead): string {
  const releaseDate = release.actual_release_date ?? release.planned_release_date;
  return `Release ${release.display_version} · ${formatLabel(release.release_status)} · ${formatDate(releaseDate)}`;
}

function parseCommaSeparated(value: string): string[] {
  return value
    .split(",")
    .map((entry) => entry.trim())
    .filter(Boolean);
}

async function loadProducts(): Promise<void> {
  isLoadingProducts.value = true;

  try {
    products.value = await productService.list();
  } catch (error) {
    errorMessage.value =
      error instanceof Error ? error.message : "Failed to load products for release selection.";
  } finally {
    isLoadingProducts.value = false;
  }
}

async function loadReleasesForProduct(productId: string): Promise<void> {
  isLoadingReleases.value = true;

  try {
    const productReleases = await productReleaseService.list(productId);
    releases.value = productReleases;

    const currentSelectionStillExists = productReleases.some(
      (release) => release.id === selectedReleaseId.value,
    );
    if (currentSelectionStillExists) {
      return;
    }

    selectedReleaseId.value =
      productReleases.find((release) => release.release_status === "released")?.id ??
      productReleases.find((release) => release.release_status === "approved")?.id ??
      productReleases[0]?.id ??
      "";
  } catch (error) {
    releases.value = [];
    selectedReleaseId.value = "";
    errorMessage.value =
      error instanceof Error ? error.message : "Failed to load releases for the selected product.";
  } finally {
    isLoadingReleases.value = false;
  }
}

async function loadSupportPeriod(productId: string): Promise<void> {
  try {
    const record = await supportPeriodService.getActiveForProduct(productId);
    supportEndDate.value = record.support_end_date ?? null;
  } catch {
    supportEndDate.value = null;
  }
}

async function loadUpdates(): Promise<void> {
  isLoading.value = true;
  errorMessage.value = "";

  try {
    const params: Record<string, string> = {};
    if (selectedReleaseId.value) {
      params.product_release_id = selectedReleaseId.value;
    } else if (selectedProductId.value) {
      params.product_id = selectedProductId.value;
    }
    const { data } = await apiClient.get<SecurityUpdateRead[]>("/security-updates/", { params });
    updates.value = data;
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
      severity: createForm.severity || null,
      is_security_only: createForm.is_security_only,
      integrity_info: createForm.integrity_info.trim() || null,
      update_channels_json: createForm.update_channels_json.filter((ch: string) => ch.trim()),
      distribution_mechanism: createForm.distribution_mechanism,
      cves_addressed_json: parseCommaSeparated(cveInput.value),
      affected_versions_json: selectedVersions.value,
      released_at: toIsoOrNull(createForm.released_at),
      available_until: toIsoOrNull(createForm.available_until),
      // Gap 5, 8, 9 — new CRA fields
      cvss_score: createForm.cvss_score,
      cvss_vector: createForm.cvss_vector.trim() || null,
      cve_links_json: [],
      vulnerability_discovered_at: toIsoOrNull(createForm.vulnerability_discovered_at),
      remediation_deadline: toIsoOrNull(createForm.remediation_deadline),
      is_free_of_charge: createForm.is_free_of_charge,
    };

    await securityUpdateService.create(payload);
    showCreateModal.value = false;
    successMessage.value = "Security update created.";

    createForm.title = "";
    createForm.description = "";
    createForm.severity = "";
    createForm.is_security_only = true;
    createForm.integrity_info = "";
    createForm.update_channels_json = [];
    createForm.released_at = "";
    createForm.available_until = "";
    createForm.cvss_score = null;
    createForm.cvss_vector = "";
    createForm.vulnerability_discovered_at = "";
    createForm.remediation_deadline = "";
    createForm.is_free_of_charge = true;
    cveInput.value = "";
    selectedVersions.value = [];

    await loadUpdates();
  } catch (error) {
    errorMessage.value =
      error instanceof Error ? error.message : "Failed to create security update.";
  } finally {
    isCreating.value = false;
  }
}

function openDetail(item: SecurityUpdateRead): void {
  detailItem.value = item;
  document.body.style.overflow = "hidden";
}

function closeDetail(): void {
  detailItem.value = null;
  document.body.style.overflow = "";
}

watch(
  selectedProductId,
  async (productId: string) => {
    releases.value = [];
    selectedReleaseId.value = "";
    selectedVersions.value = [];
    updates.value = [];
    supportEndDate.value = null;

    if (!productId) {
      await loadUpdates();
      return;
    }

    errorMessage.value = "";
    await Promise.all([
      loadReleasesForProduct(productId),
      loadSupportPeriod(productId),
      loadUpdates(),
    ]);
  },
);

watch(selectedReleaseId, async (releaseId: string) => {
  createForm.product_release_id = releaseId;
  await loadUpdates();
});

onMounted(() => {
  void loadProducts();
  void loadUpdates();
});
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
  align-items: flex-end;
  gap: 0.75rem;
  flex-wrap: wrap;
  width: 100%;
}

.page-actions .field {
  flex: 1 1 15rem;
  min-width: 15rem;
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

.selection-summary {
  margin: 0;
}

.selection-card {
  display: grid;
  gap: 0.35rem;
  padding: 0.9rem 1rem;
  border-radius: 0.9rem;
  border: 1px solid var(--color-border, rgba(148, 163, 184, 0.25));
  background: var(--color-surface-soft, rgba(15, 23, 42, 0.35));
}

.selection-card-empty {
  border-style: dashed;
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
  padding: 0.6rem 1.1rem;
  font: inherit;
  font-size: var(--text-sm);
  font-weight: 600;
  cursor: pointer;
  white-space: nowrap;
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

.btn-sm {
  padding: 0.4rem 0.8rem;
  font-size: 0.85rem;
}

.btn-icon {
  padding: 0.4rem 0.6rem;
  font-size: 0.8rem;
  line-height: 1;
}

.btn-remove {
  background: transparent;
  border-color: rgba(248, 113, 113, 0.35);
  color: #f87171;
  flex-shrink: 0;
  align-self: stretch;
}

.muted {
  color: var(--color-text-muted, #94a3b8);
}

.versions-empty {
  padding: 0.7rem 1rem;
  border-radius: 0.85rem;
  border: 1px dashed var(--color-border, rgba(148, 163, 184, 0.25));
  color: var(--color-text-muted, #94a3b8);
  font-size: 0.9rem;
}

.versions-checklist {
  display: flex;
  flex-direction: column;
  gap: 0.4rem;
  padding: 0.6rem 0.8rem;
  border-radius: 0.85rem;
  border: 1px solid var(--color-border, rgba(148, 163, 184, 0.25));
  background: var(--color-surface-soft, rgba(15, 23, 42, 0.5));
  max-height: 14rem;
  overflow-y: auto;
}

.display_version-option {
  display: flex;
  align-items: center;
  gap: 0.6rem;
  padding: 0.45rem 0.5rem;
  border-radius: 0.5rem;
  cursor: pointer;
  transition: background 0.13s;
}

.display_version-option:hover {
  background: var(--color-surface-elevated, rgba(255, 255, 255, 0.05));
}

.display_version-option input[type="checkbox"] {
  width: auto;
  padding: 0;
  border: none;
  background: none;
  accent-color: var(--color-primary, #6ea8fe);
  cursor: pointer;
  flex-shrink: 0;
}

.display_version-label {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  flex-wrap: wrap;
  font-size: 0.9rem;
}

.display_version-status {
  padding: 0.1rem 0.45rem;
  border-radius: 999px;
  background: var(--color-surface-elevated, rgba(255, 255, 255, 0.07));
  font-size: 0.78rem;
  text-transform: capitalize;
}

.display_version-date {
  font-size: 0.82rem;
}

/* Channels */
.channels-list {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.channel-row {
  display: flex;
  gap: 0.5rem;
  align-items: stretch;
}

.channel-row input {
  flex: 1;
}

/* Checkbox label */
.checkbox-label {
  display: flex;
  align-items: flex-start;
  gap: 0.65rem;
  cursor: pointer;
  font-size: 0.95rem;
}

.checkbox-label input[type="checkbox"] {
  width: auto;
  padding: 0;
  border: none;
  background: none;
  accent-color: var(--color-primary, #6ea8fe);
  cursor: pointer;
  flex-shrink: 0;
  margin-top: 0.15rem;
}

/* Retention hint */
.retention-hint {
  font-size: 0.82rem;
  padding: 0.3rem 0.6rem;
  border-radius: 0.5rem;
  background: var(--color-surface-elevated, rgba(255, 255, 255, 0.04));
}

.retention-warning {
  color: #fbbf24;
  background: rgba(251, 191, 36, 0.08);
}

/* Severity badges */
.severity-badge {
  display: inline-block;
  padding: 0.15rem 0.5rem;
  border-radius: 999px;
  font-size: 0.8rem;
  font-weight: 600;
  text-transform: capitalize;
}

.severity-critical { background: rgba(239, 68, 68, 0.2); color: #f87171; }
.severity-high     { background: rgba(249, 115, 22, 0.2); color: #fb923c; }
.severity-medium   { background: rgba(234, 179, 8, 0.2);  color: #fbbf24; }
.severity-low      { background: rgba(34, 197, 94, 0.2);  color: #4ade80; }
.severity-informational { background: rgba(99, 102, 241, 0.2); color: #818cf8; }

/* Type badges */
.type-badge {
  display: inline-block;
  padding: 0.15rem 0.5rem;
  border-radius: 999px;
  font-size: 0.8rem;
  font-weight: 500;
}

.type-security { background: rgba(34, 197, 94, 0.15); color: #4ade80; }
.type-mixed    { background: rgba(148, 163, 184, 0.15); color: #94a3b8; }

/* Integrity cell */
.integrity-cell {
  font-size: 0.8rem;
  font-family: monospace;
  word-break: break-all;
  max-width: 18rem;
}

/* Channels in table */
.channel-entry {
  font-size: 0.82rem;
  word-break: break-all;
}

/* Clickable table rows */
.table-row-clickable {
  cursor: pointer;
  transition: background 0.13s;
}

.table-row-clickable:hover {
  background: var(--color-surface-elevated, rgba(255, 255, 255, 0.04));
}

.table-row-clickable:focus-visible {
  outline: 2px solid var(--color-primary, #6ea8fe);
  outline-offset: -2px;
}

.row-arrow {
  color: var(--color-text-muted, #94a3b8);
  font-size: 1.1rem;
  text-align: right;
  opacity: 0;
  transition: opacity 0.13s;
}

.table-row-clickable:hover .row-arrow,
.table-row-clickable:focus-visible .row-arrow {
  opacity: 1;
}

.nowrap { white-space: nowrap; }

.cell-desc {
  display: -webkit-box;
  -webkit-line-clamp: 2;
  line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  color: var(--color-text-muted, #94a3b8);
  font-size: 0.82rem;
  margin-top: 0.25rem;
}

/* CVE pills in table */
.cve-pill {
  display: inline-block;
  padding: 0.1rem 0.45rem;
  border-radius: 999px;
  background: rgba(99, 102, 241, 0.15);
  color: #818cf8;
  font-size: 0.78rem;
  font-weight: 500;
  margin-right: 0.25rem;
  white-space: nowrap;
}

.cve-pill-lg {
  font-size: 0.85rem;
  padding: 0.2rem 0.6rem;
}

/* ── Detail modal ── */
.modal-backdrop {
  position: fixed;
  inset: 0;
  background: var(--color-modal-backdrop, rgba(5, 10, 20, 0.78));
  z-index: 200;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 1rem;
}

.detail-modal {
  background: var(--color-modal-bg, #0c1524);
  border: 1px solid var(--color-border, rgba(148, 163, 184, 0.2));
  border-radius: 1.2rem;
  width: 100%;
  max-width: 52rem;
  max-height: 90vh;
  display: flex;
  flex-direction: column;
  box-shadow: 0 24px 80px rgba(0, 0, 0, 0.6);
  overflow: hidden;
}

.detail-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 1rem;
  padding: 1.5rem 1.5rem 1.2rem;
  border-bottom: 1px solid var(--color-border, rgba(148, 163, 184, 0.15));
  flex-shrink: 0;
}

.detail-header-left {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  min-width: 0;
}

.detail-badges {
  display: flex;
  gap: 0.5rem;
  flex-wrap: wrap;
}

.detail-title {
  margin: 0;
  font-size: 1.2rem;
  font-weight: 700;
  line-height: 1.3;
}

.detail-description {
  margin: 0;
  color: var(--color-text-muted, #94a3b8);
  line-height: 1.55;
  font-size: 0.92rem;
}

.btn-close {
  background: transparent;
  border-color: var(--color-border, rgba(148, 163, 184, 0.2));
  color: var(--color-text-muted, #94a3b8);
  border-radius: 0.6rem;
  flex-shrink: 0;
  transition: color 0.12s, border-color 0.12s;
}

.btn-close:hover {
  color: #f87171;
  border-color: rgba(248, 113, 113, 0.4);
}

.detail-body {
  flex: 1;
  overflow-y: auto;
  padding: 1.25rem 1.5rem;
  display: flex;
  flex-direction: column;
  gap: 1.25rem;
}

/* Timeline */
.detail-timeline {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  flex-wrap: wrap;
  padding: 0.9rem 1rem;
  border-radius: 0.85rem;
  background: var(--color-surface-soft, rgba(255, 255, 255, 0.03));
  border: 1px solid var(--color-border, rgba(148, 163, 184, 0.12));
}

.timeline-item {
  display: flex;
  flex-direction: column;
  gap: 0.15rem;
}

.timeline-label {
  font-size: 0.72rem;
  color: var(--color-text-muted, #94a3b8);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.timeline-value {
  font-size: 0.88rem;
  font-weight: 500;
}

.timeline-sep {
  color: var(--color-text-muted, #94a3b8);
  font-size: 1rem;
}

/* Detail grid */
.detail-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 1rem;
}

.detail-section {
  padding: 1rem;
  border-radius: 0.85rem;
  border: 1px solid var(--color-border, rgba(148, 163, 184, 0.15));
  background: var(--color-surface-soft, rgba(255, 255, 255, 0.02));
  display: flex;
  flex-direction: column;
  gap: 0.65rem;
}

.detail-section-title {
  margin: 0;
  font-size: 0.78rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: var(--color-text-muted, #94a3b8);
}

.detail-kv {
  display: grid;
  grid-template-columns: 6rem 1fr;
  gap: 0.4rem 0.75rem;
  align-items: baseline;
}

.detail-key {
  font-size: 0.8rem;
  color: var(--color-text-muted, #94a3b8);
}

.detail-val {
  font-size: 0.9rem;
  word-break: break-word;
}

/* Channel chips */
.channel-chip {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  padding: 0.3rem 0.6rem;
  border-radius: 0.5rem;
  background: rgba(110, 168, 254, 0.1);
  border: 1px solid rgba(110, 168, 254, 0.2);
  font-size: 0.83rem;
  word-break: break-all;
  margin-bottom: 0.3rem;
}

.channel-icon {
  font-size: 0.9rem;
  color: #6ea8fe;
  flex-shrink: 0;
}

/* CVE list in modal */
.cve-list {
  display: flex;
  flex-wrap: wrap;
  gap: 0.35rem;
}

/* Version tags */
.display_version-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 0.35rem;
}

.display_version-tag {
  display: inline-block;
  padding: 0.2rem 0.55rem;
  border-radius: 999px;
  background: rgba(148, 163, 184, 0.12);
  color: var(--color-text-muted, #94a3b8);
  font-size: 0.82rem;
  font-weight: 500;
}

/* Integrity block */
.integrity-block {
  font-family: monospace;
  font-size: 0.82rem;
  word-break: break-all;
  background: var(--color-surface-soft, rgba(15, 23, 42, 0.5));
  border: 1px solid var(--color-border, rgba(148, 163, 184, 0.15));
  border-radius: 0.5rem;
  padding: 0.5rem 0.65rem;
  display: block;
  line-height: 1.5;
}

/* Footer */
.detail-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 1rem 1.5rem;
  border-top: 1px solid var(--color-border, rgba(148, 163, 184, 0.15));
  flex-shrink: 0;
  gap: 1rem;
}

.detail-id {
  font-size: 0.75rem;
  font-family: monospace;
  word-break: break-all;
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
  transform: translateY(16px) scale(0.98);
  opacity: 0;
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

<style>
:root[data-theme="light"] .feedback-error  { color: #be123c; }
:root[data-theme="light"] .feedback-success { color: #15803d; }
:root[data-theme="light"] .btn-primary { background: linear-gradient(135deg, rgba(175, 214, 46, 0.95), rgba(28, 107, 39, 0.95)); }
:root[data-theme="light"] .table-row:hover { background: rgba(28, 107, 39, 0.04); }
:root[data-theme="light"] .severity-critical { background: rgba(239, 68, 68, 0.12); color: #dc2626; }
:root[data-theme="light"] .severity-high     { background: rgba(249, 115, 22, 0.12); color: #ea580c; }
:root[data-theme="light"] .severity-medium   { background: rgba(234, 179, 8, 0.12);  color: #ca8a04; }
:root[data-theme="light"] .severity-low      { background: rgba(34, 197, 94, 0.12);  color: #16a34a; }
:root[data-theme="light"] .severity-informational { background: rgba(99, 102, 241, 0.12); color: #4f46e5; }
:root[data-theme="light"] .type-security { background: rgba(34, 197, 94, 0.1); color: #16a34a; }
:root[data-theme="light"] .type-mixed    { background: rgba(100, 116, 139, 0.1); color: #475569; }
:root[data-theme="light"] .retention-warning { color: #b45309; background: rgba(217, 119, 6, 0.08); }
:root[data-theme="light"] .detail-modal { background: #ffffff; }
:root[data-theme="light"] .modal-backdrop { background: rgba(15, 23, 42, 0.55); }
:root[data-theme="light"] .detail-timeline { background: rgba(0, 0, 0, 0.03); }
:root[data-theme="light"] .detail-section { background: rgba(0, 0, 0, 0.02); }
:root[data-theme="light"] .integrity-block { background: rgba(0, 0, 0, 0.04); }
:root[data-theme="light"] .channel-chip { background: rgba(37, 99, 235, 0.07); border-color: rgba(37, 99, 235, 0.18); }
:root[data-theme="light"] .table-row-clickable:hover { background: rgba(37, 99, 235, 0.04); }
:root[data-theme="light"] .cve-pill { background: rgba(79, 70, 229, 0.1); color: #4f46e5; }
:root[data-theme="light"] .display_version-tag { background: rgba(100, 116, 139, 0.1); color: #475569; }
</style>
