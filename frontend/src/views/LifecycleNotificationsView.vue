<template>
  <section class="page">
    <header class="page-header">
      <div>
        <h1 class="page-title">Lifecycle alerts</h1>
        <p class="muted page-subtitle">
          Run End of Support (EOS) analysis from active support periods and review products nearing end of support.
        </p>
      </div>

      <div class="page-actions">
        <AppButton variant="primary" type="button" @click="runScheduler" :disabled="isRunningScheduler">
          {{ isRunningScheduler ? "Running..." : "Run EOS check" }}
        </AppButton>
      </div>
    </header>

    <section class="card filters-card">
      <div class="section-header">
        <div>
          <h2 class="section-title">Analysis filters</h2>
        </div>
      </div>

      <div class="filters-grid">
        <label class="field field-search">
          <span class="field-label">Search</span>
          <input
            v-model.trim="filters.search"
            type="search"
            class="input"
            placeholder="Search by code, product, manufacturer, or type"
          />
        </label>

        <label class="field">
          <span class="field-label">Threshold</span>
          <select v-model="filters.thresholdPreset" class="select">
            <option value="">All products with support</option>
            <option value="30">Less than 30 days</option>
            <option value="90">Less than 3 months</option>
            <option value="180">Less than 6 months</option>
            <option value="365">Less than 1 year</option>
            <option value="expired">Expired only</option>
            <option value="custom">Custom</option>
          </select>
        </label>

        <label v-if="filters.thresholdPreset === 'custom'" class="field">
          <span class="field-label">Custom days</span>
          <input
            v-model.number="filters.customThresholdDays"
            type="number"
            min="1"
            step="1"
            class="input"
            placeholder="120"
          />
        </label>

        <label class="field">
          <span class="field-label">Classification</span>
          <select v-model="filters.classification" class="select">
            <option value="">All</option>
            <option value="normal">Normal</option>
            <option value="important_class_1">Important Class I</option>
            <option value="important_class_2">Important Class II</option>
            <option value="critical">Critical</option>
          </select>
        </label>

        <label class="field">
          <span class="field-label">EOS state</span>
          <select v-model="filters.eosStatus" class="select">
            <option value="">All</option>
            <option value="active">Active</option>
            <option value="approaching_eos">Approaching EOS</option>
            <option value="expired">Expired</option>
          </select>
        </label>

        <label class="field">
          <span class="field-label">Sort by</span>
          <select v-model="filters.sortBy" class="select">
            <option value="days_left_asc">Days left</option>
            <option value="support_end_asc">Support end date</option>
            <option value="support_end_desc">Support end date (latest)</option>
            <option value="updated_desc">Latest updated</option>
            <option value="name_asc">Name A–Z</option>
            <option value="code_asc">Code A–Z</option>
          </select>
        </label>
      </div>
    </section>

    <section class="summary-grid">
      <article class="card stat-card">
        <p class="muted stat-label">Products with support</p>
        <strong class="stat-value">{{ eosRows.length }}</strong>
      </article>

      <article class="card stat-card">
        <p class="muted stat-label">Expired</p>
        <strong class="stat-value">{{ expiredCount }}</strong>
      </article>
    </section>

    <div v-if="errorMessage" class="card feedback feedback-error">
      {{ errorMessage }}
    </div>

    <div v-if="successMessage" class="card feedback feedback-success">
      {{ successMessage }}
    </div>

    <section class="card">
      <div class="section-header">
        <div>
          <h2 class="section-title">EOS analysis</h2>
          <p class="muted">{{ filteredRows.length }} result(s)</p>
        </div>
      </div>

      <div v-if="isLoading" class="empty-panel">
        Loading EOS analysis…
      </div>

      <div v-else-if="filteredRows.length === 0" class="empty-panel">
        No products matched the current EOS criteria.
      </div>

      <div v-else class="table-wrapper">
        <table class="data-table">
          <thead>
            <tr>
              <th>Product</th>
              <th>Code</th>
              <th>Manufacturer</th>
              <th>Classification</th>
              <th>Support ends</th>
              <th>Days left</th>
              <th>EOS status</th>
            </tr>
          </thead>

          <tbody>
            <tr v-for="row in filteredRows" :key="row.product.id">
              <td>
                <div class="product-cell">
                  <strong>{{ row.product.name }}</strong>
                  <p class="muted">{{ row.product.product_type }}</p>
                </div>
              </td>

              <td><code>{{ row.product.product_code }}</code></td>
              <td>{{ row.product.manufacturer_name }}</td>

              <td>
                <span class="badge" :class="classificationClass(row.product.current_classification)">
                  {{ formatClassification(row.product.current_classification) }}
                </span>
              </td>

              <td>{{ formatDate(row.support.support_end_date) }}</td>

              <td>
                <span :class="daysLeftClass(row.daysLeft)">
                  {{ formatDaysLeft(row.daysLeft) }}
                </span>
              </td>

              <td>
                <span class="badge" :class="supportStatusClass(row.eosStatus)">
                  {{ formatSupportStatus(row.eosStatus) }}
                </span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>

    <!-- Security update alerts -->
    <section class="card">
      <div class="section-header">
        <div>
          <h2 class="section-title">Security update alerts</h2>
          <p class="muted">
            Alerts generated automatically when a security update is published for a product
            with an active support period (CRA Annex I Part II §8).
          </p>
        </div>
      </div>

      <div v-if="isLoadingSecurityAlerts" class="empty-panel">
        Loading security update alerts…
      </div>

      <div v-else-if="securityAlerts.length === 0" class="empty-panel">
        No security update alerts. Alerts appear automatically when a security update is
        published for a product with an active support period.
      </div>

      <div v-else class="table-wrapper">
        <table class="data-table">
          <thead>
            <tr>
              <th>Status</th>
              <th>Alert</th>
              <th>Details</th>
              <th>Created</th>
              <th>Actions</th>
            </tr>
          </thead>

          <tbody>
            <tr v-for="alert in securityAlerts" :key="alert.id">
              <td>
                <span class="badge" :class="alertStatusClass(alert.status)">
                  {{ formatAlertStatus(alert.status) }}
                </span>
              </td>

              <td>
                <div class="product-cell">
                  <strong>{{ alert.title }}</strong>
                  <p class="muted small-text">
                    {{ alert.recipient_user ? alert.recipient_user.full_name : "All recipients" }}
                  </p>
                </div>
              </td>

              <td class="message-cell">{{ alert.message }}</td>

              <td>{{ formatDate(alert.created_at) }}</td>

              <td>
                <div class="row-actions">
                  <AppButton
                    v-if="alert.status === 'pending'"
                    variant="secondary"
                    size="sm"
                    :disabled="isActioning"
                    @click="markAlertSent(alert.id)"
                  >
                    Mark sent
                  </AppButton>
                  <AppButton
                    v-if="alert.status !== 'dismissed'"
                    variant="secondary"
                    size="sm"
                    :disabled="isActioning"
                    @click="dismissAlert(alert.id)"
                  >
                    Dismiss
                  </AppButton>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from "vue";
import AppButton from "@/components/AppButton.vue";

import { lifecycleNotificationService } from "@/services/lifecycle-notification-service";
import { productService } from "@/services/product-service";
import { supportPeriodService } from "@/services/support-period-service";

import type {
  LifecycleNotificationRead,
  LifecycleNotificationStatus,
  ProductClassification,
  ProductSummaryRead,
  SupportPeriodRecordRead,
} from "@/types/product";

type ThresholdPreset = "" | "30" | "90" | "180" | "365" | "custom" | "expired";
type EosStatus = "active" | "approaching_eos" | "expired";

type EosRow = {
  product: ProductSummaryRead;
  support: SupportPeriodRecordRead;
  daysLeft: number;
  eosStatus: EosStatus;
};

const products = ref<ProductSummaryRead[]>([]);
const supportByProductId = ref<Record<string, SupportPeriodRecordRead | null>>({});

const isLoading = ref(false);
const isRunningScheduler = ref(false);
const errorMessage = ref("");
const successMessage = ref("");

// Security update alerts
const securityAlerts = ref<LifecycleNotificationRead[]>([]);
const isLoadingSecurityAlerts = ref(false);
const isActioning = ref(false);

const filters = reactive({
  search: "",
  thresholdPreset: "" as ThresholdPreset,
  customThresholdDays: 120,
  classification: "" as ProductClassification | "",
  eosStatus: "" as EosStatus | "",
  sortBy: "days_left_asc" as
    | "days_left_asc"
    | "support_end_asc"
    | "support_end_desc"
    | "updated_desc"
    | "name_asc"
    | "code_asc",
});

function startOfDay(date: Date): Date {
  return new Date(date.getFullYear(), date.getMonth(), date.getDate());
}

function getDaysLeft(endDateValue: string): number {
  const today = startOfDay(new Date());
  const end = startOfDay(new Date(`${endDateValue}T00:00:00`));
  const diffMs = end.getTime() - today.getTime();
  return Math.ceil(diffMs / (1000 * 60 * 60 * 24));
}

function getThresholdDays(): number | null {
  switch (filters.thresholdPreset) {
    case "30":
      return 30;
    case "90":
      return 90;
    case "180":
      return 180;
    case "365":
      return 365;
    case "custom":
      return filters.customThresholdDays > 0 ? filters.customThresholdDays : null;
    default:
      return null;
  }
}

function getEosStatusFromSupport(support: SupportPeriodRecordRead): EosStatus {
  const daysLeft = getDaysLeft(support.support_end_date);

  if (daysLeft < 0) {
    return "expired";
  }

  if (daysLeft <= 180) {
    return "approaching_eos";
  }

  return "active";
}

const eosRows = computed<EosRow[]>(() =>
  products.value
    .map((product) => {
      const support = supportByProductId.value[product.id];
      if (!support) return null;

      const daysLeft = getDaysLeft(support.support_end_date);
      const eosStatus = getEosStatusFromSupport(support);

      return {
        product,
        support,
        daysLeft,
        eosStatus,
      };
    })
    .filter((row): row is EosRow => Boolean(row)),
);

const filteredRows = computed(() => {
  const query = filters.search.trim().toLowerCase();
  const thresholdDays = getThresholdDays();

  const filtered = eosRows.value.filter((row) => {
    const matchesSearch =
      !query ||
      [
        row.product.product_code,
        row.product.name,
        row.product.manufacturer_name,
        row.product.product_type,
        row.support.support_end_date,
      ]
        .join(" ")
        .toLowerCase()
        .includes(query);

    const matchesClassification =
      !filters.classification || row.product.current_classification === filters.classification;

    const matchesEosStatus =
      !filters.eosStatus || row.eosStatus === filters.eosStatus;

    const matchesThreshold =
      filters.thresholdPreset === ""
        ? true
        : filters.thresholdPreset === "expired"
          ? row.daysLeft < 0
          : thresholdDays !== null
            ? row.daysLeft >= 0 && row.daysLeft < thresholdDays
            : true;

    return matchesSearch && matchesClassification && matchesEosStatus && matchesThreshold;
  });

  return [...filtered].sort((a, b) => {
    switch (filters.sortBy) {
      case "support_end_asc":
        return new Date(a.support.support_end_date).getTime() - new Date(b.support.support_end_date).getTime();
      case "support_end_desc":
        return new Date(b.support.support_end_date).getTime() - new Date(a.support.support_end_date).getTime();
      case "updated_desc":
        return new Date(b.product.updated_at).getTime() - new Date(a.product.updated_at).getTime();
      case "name_asc":
        return a.product.name.localeCompare(b.product.name);
      case "code_asc":
        return a.product.product_code.localeCompare(b.product.product_code);
      case "days_left_asc":
      default:
        return a.daysLeft - b.daysLeft;
    }
  });
});

const expiredCount = computed(() => eosRows.value.filter((row) => row.daysLeft < 0).length);

function formatSupportStatus(value: EosStatus): string {
  switch (value) {
    case "active":
      return "Active";
    case "approaching_eos":
      return "Approaching EOS";
    case "expired":
      return "Expired";
  }
}

function supportStatusClass(value: EosStatus): string {
  switch (value) {
    case "active":
      return "badge-success";
    case "approaching_eos":
      return "badge-warning";
    case "expired":
      return "badge-danger";
  }
}

function formatClassification(value: ProductClassification): string {
  switch (value) {
    case "important_class_1":
      return "Important Class I";
    case "important_class_2":
      return "Important Class II";
    case "critical":
      return "Critical";
    default:
      return "Normal";
  }
}

function classificationClass(value: ProductClassification): string {
  switch (value) {
    case "critical":
      return "badge-danger";
    case "important_class_1":
    case "important_class_2":
      return "badge-warning";
    default:
      return "badge-neutral";
  }
}

function formatDaysLeft(daysLeft: number): string {
  if (daysLeft < 0) return `${Math.abs(daysLeft)} day(s) overdue`;
  if (daysLeft === 0) return "Ends today";
  return `${daysLeft} day(s)`;
}

function daysLeftClass(daysLeft: number): string {
  if (daysLeft < 0) return "text-danger";
  if (daysLeft <= 180) return "text-warning";
  return "text-success";
}

function formatDate(value: string): string {
  return new Intl.DateTimeFormat(undefined, {
    year: "numeric",
    month: "short",
    day: "2-digit",
  }).format(new Date(value));
}


async function loadSupportPeriods(productList: ProductSummaryRead[]): Promise<void> {
  const entries = await Promise.all(
    productList.map(async (product) => {
      try {
        const record = await supportPeriodService.getActiveForProduct(product.id);
        return [product.id, record] as const;
      } catch {
        return [product.id, null] as const;
      }
    }),
  );

  supportByProductId.value = Object.fromEntries(entries);
}

async function loadPageData(): Promise<void> {
  isLoading.value = true;
  errorMessage.value = "";

  try {
    const loadedProducts = await productService.list();
    products.value = loadedProducts;
    await loadSupportPeriods(loadedProducts);
  } catch (error) {
    errorMessage.value =
      error instanceof Error ? error.message : "Failed to load EOS page.";
  } finally {
    isLoading.value = false;
  }
}

async function runScheduler(): Promise<void> {
  isRunningScheduler.value = true;
  errorMessage.value = "";
  successMessage.value = "";

  try {
    const thresholdDays = getThresholdDays();
    const created = await lifecycleNotificationService.scheduleEosCheck(
      thresholdDays ? { threshold_days: thresholdDays } : undefined,
    );

    successMessage.value = thresholdDays
      ? `EOS check completed for threshold ${thresholdDays} day(s). ${created.length} notification(s) created.`
      : `EOS check completed. ${created.length} notification(s) created.`;
  } catch (error) {
    errorMessage.value =
      error instanceof Error ? error.message : "Failed to run EOS scheduling check.";
  } finally {
    isRunningScheduler.value = false;
  }
}

function alertStatusClass(status: LifecycleNotificationStatus): string {
  switch (status) {
    case "sent":
      return "badge-success";
    case "dismissed":
      return "badge-neutral";
    default:
      return "badge-warning";
  }
}

function formatAlertStatus(status: LifecycleNotificationStatus): string {
  switch (status) {
    case "sent":
      return "Sent";
    case "dismissed":
      return "Dismissed";
    default:
      return "Pending";
  }
}

async function loadSecurityUpdateAlerts(): Promise<void> {
  isLoadingSecurityAlerts.value = true;
  try {
    securityAlerts.value = await lifecycleNotificationService.list({
      notification_type: "security_update_available",
    });
  } catch {
    // Non-fatal — EOS section still works independently.
  } finally {
    isLoadingSecurityAlerts.value = false;
  }
}

async function markAlertSent(notificationId: string): Promise<void> {
  isActioning.value = true;
  try {
    await lifecycleNotificationService.markSent(notificationId);
    await loadSecurityUpdateAlerts();
  } catch {
    // Silently ignore — the alert list will not change.
  } finally {
    isActioning.value = false;
  }
}

async function dismissAlert(notificationId: string): Promise<void> {
  isActioning.value = true;
  try {
    await lifecycleNotificationService.dismiss(notificationId);
    await loadSecurityUpdateAlerts();
  } catch {
    // Silently ignore — the alert list will not change.
  } finally {
    isActioning.value = false;
  }
}

onMounted(() => {
  void loadPageData();
  void loadSecurityUpdateAlerts();
});
</script>

<style scoped>
.page {
  display: grid;
  gap: 1rem;
}

.page-header,
.section-header {
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
  align-items: center;
}

.page-title,
.section-title {
  margin: 0;
}

.page-subtitle {
  margin-top: 0.35rem;
}

.filters-card {
  display: grid;
  gap: 1rem;
}

.filters-grid {
  display: grid;
  grid-template-columns: repeat(5, minmax(0, 1fr));
  gap: 1rem;
  align-items: end;
}

.field {
  display: grid;
  gap: 0.4rem;
}

.field-search {
  min-width: 0;
}

.field-label {
  font-size: var(--text-xs);
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: var(--color-text-muted, #94a3b8);
}

.summary-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 1rem;
}

.stat-card {
  display: grid;
  gap: 0.35rem;
}

.stat-label {
  margin: 0;
}

.stat-value {
  font-size: var(--text-2xl);
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
  font-size: var(--text-xs);
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  white-space: nowrap;
}

.product-cell {
  display: grid;
  gap: 0.25rem;
}

.message-cell {
  max-width: 28rem;
  font-size: var(--text-sm);
  color: var(--color-text-muted, #94a3b8);
  line-height: 1.4;
}

.small-text {
  font-size: var(--text-xs);
  margin: 0;
}

.row-actions {
  display: flex;
  gap: 0.5rem;
  flex-wrap: wrap;
}

.action-btn {
  font-size: var(--text-xs);
  padding: 0.4rem 0.75rem;
  white-space: nowrap;
}

.badge {
  display: inline-flex;
  align-items: center;
  border-radius: 999px;
  padding: 0.35rem 0.65rem;
  font-size: var(--text-xs);
  font-weight: 600;
  width: fit-content;
  text-transform: capitalize;
}

.badge-neutral {
  background: rgba(148, 163, 184, 0.15);
  color: #cbd5e1;
}

.badge-success {
  background: rgba(52, 211, 153, 0.15);
  color: #86efac;
}

.badge-warning {
  background: rgba(251, 191, 36, 0.15);
  color: #fde68a;
}

.badge-danger {
  background: rgba(251, 113, 133, 0.15);
  color: #fda4af;
}

.text-success {
  color: #86efac;
  font-weight: 600;
}

.text-warning {
  color: #fde68a;
  font-weight: 600;
}

.text-danger {
  color: #fda4af;
  font-weight: 600;
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

.input,
.select {
  width: 100%;
  box-sizing: border-box;
  min-height: 2.7rem;
  border-radius: 0.85rem;
  border: 1px solid var(--color-border, rgba(148, 163, 184, 0.2));
  background: var(--color-surface-soft, rgba(15, 23, 42, 0.45));
  color: inherit;
  padding: 0.75rem 0.9rem;
  font: inherit;
}

.muted {
  color: var(--color-text-muted, #94a3b8);
}

@media (max-width: 1400px) {
  .filters-grid {
    grid-template-columns: repeat(3, minmax(0, 1fr));
  }
}

@media (max-width: 900px) {
  .summary-grid,
  .filters-grid {
    grid-template-columns: 1fr;
  }
}
</style>

<style>
:root[data-theme="light"] .feedback-error  { color: #be123c; }
:root[data-theme="light"] .feedback-success { color: #15803d; }
:root[data-theme="light"] .badge-neutral { background: rgba(71,85,105,0.1);   color: #475569; }
:root[data-theme="light"] .badge-success { background: rgba(21,128,61,0.1);   color: #15803d; }
:root[data-theme="light"] .badge-warning { background: rgba(184,155,18,0.1);  color: #78350f; }
:root[data-theme="light"] .badge-danger  { background: rgba(239,68,68,0.1);   color: #be123c; }
:root[data-theme="light"] .text-success  { color: #15803d; }
:root[data-theme="light"] .text-warning  { color: #78350f; }
:root[data-theme="light"] .text-danger   { color: #be123c; }
:root[data-theme="light"] .btn-primary { background: linear-gradient(135deg, rgba(175, 214, 46, 0.95), rgba(28, 107, 39, 0.95)); }
</style>