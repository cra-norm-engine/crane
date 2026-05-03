<template>
  <section class="page">

    <!-- ══════════════════════════════════════════
         PAGE HEADER
         ══════════════════════════════════════════ -->
    <header class="page-header card">
      <div>
        <h1 class="page-title">Support Hub</h1>
        <p class="muted page-subtitle">
          CRA-oriented tools for customer support and lifecycle management — product
          support lookups, EOS watchlist, notification queue, and CVE lookup.
        </p>
      </div>

      <div class="page-actions">
        <button class="btn btn-secondary" type="button" :disabled="isLoading" @click="loadAll">
          {{ isLoading ? "Refreshing…" : "Refresh" }}
        </button>
      </div>
    </header>

    <!-- ══════════════════════════════════════════
         LOADING / ERROR FEEDBACK
         ══════════════════════════════════════════ -->
    <div v-if="isLoading && products.length === 0" class="card empty-panel">
      Loading Support Hub data…
    </div>

    <div v-if="loadError" class="card feedback feedback-error" role="alert">
      {{ loadError }}
    </div>

    <template v-if="!isLoading || products.length > 0">

      <!-- ══════════════════════════════════════════
           SUMMARY STAT CARDS
           ══════════════════════════════════════════ -->
      <section class="stats-grid" aria-label="Summary statistics">

        <article class="card stat-card">
          <p class="muted stat-label">Products tracked</p>
          <strong class="stat-value">{{ products.length }}</strong>
        </article>

        <article class="card stat-card">
          <p class="muted stat-label">Active support periods</p>
          <strong class="stat-value">{{ activeSupportPeriods.length }}</strong>
        </article>

        <article class="card stat-card">
          <!-- Products with active support period and ≤ 90 days remaining -->
          <p class="muted stat-label">Approaching EOS (≤ 90 days)</p>
          <strong class="stat-value" :class="approachingEosCount > 0 ? 'text-warning' : ''">
            {{ approachingEosCount }}
          </strong>
        </article>

        <article class="card stat-card">
          <p class="muted stat-label">Pending notifications</p>
          <strong class="stat-value" :class="pendingNotifications.length > 0 ? 'text-warning' : ''">
            {{ pendingNotifications.length }}
          </strong>
        </article>

      </section>

      <!-- ══════════════════════════════════════════
           PANEL 1 — PRODUCT SUPPORT LOOKUP
           Agent types a product name or code to instantly
           see its CRA Art. 13(7) support status and recent
           security updates.
           ══════════════════════════════════════════ -->
      <section class="card panel">

        <div class="panel-header">
          <div>
            <h2 class="section-title">Product support lookup</h2>
            <p class="muted">
              Search for a product to view support status, Art. 13(7) disclosure text, and recent security patches.
            </p>
          </div>
        </div>

        <!-- Search input -->
        <div class="lookup-search-row">
          <label class="field field-grow">
            <span class="field-label">Search product</span>
            <input
              v-model.trim="lookupQuery"
              type="search"
              class="input"
              placeholder="Product name or code…"
              autocomplete="off"
              @focus="showDropdown = true"
              @blur="onLookupBlur"
            />
          </label>

          <!-- Clear selection -->
          <button
            v-if="selectedProductId"
            class="btn btn-secondary"
            type="button"
            style="align-self: flex-end;"
            @click="clearLookup"
          >
            Clear
          </button>
        </div>

        <!-- Autocomplete dropdown -->
        <ul
          v-if="showDropdown && lookupQuery && lookupDropdownItems.length > 0"
          class="lookup-dropdown"
          role="listbox"
        >
          <li
            v-for="product in lookupDropdownItems"
            :key="product.id"
            class="lookup-option"
            role="option"
            @mousedown.prevent="selectProduct(product.id)"
          >
            <span class="lookup-option-name">{{ product.name }}</span>
            <code class="lookup-option-code muted">{{ product.product_code }}</code>
          </li>
        </ul>

        <div v-if="showDropdown && lookupQuery && lookupDropdownItems.length === 0" class="lookup-no-results muted">
          No products matched "{{ lookupQuery }}".
        </div>

        <!-- ── Selected product result card ── -->
        <div v-if="selectedProduct" class="lookup-result">

          <!-- Product identity + classification -->
          <div class="result-identity">
            <div>
              <h3 class="result-product-name">{{ selectedProduct.name }}</h3>
              <p class="muted result-product-meta">
                {{ selectedProduct.manufacturer_name }} · <code>{{ selectedProduct.product_code }}</code>
              </p>
            </div>
            <span class="badge" :class="classificationBadge(selectedProduct.current_classification)">
              {{ formatClassification(selectedProduct.current_classification) }}
            </span>
          </div>

          <!-- Support status -->
          <div v-if="selectedSupport" class="result-section">
            <h4 class="result-section-title">Support period (CRA Art. 13(7))</h4>

            <div class="support-meta-row">
              <span class="badge" :class="supportStatusBadge(selectedEosStatus)">
                {{ formatEosStatus(selectedEosStatus) }}
              </span>
              <span class="muted">
                {{ formatDate(selectedSupport.support_start_date) }} –
                {{ formatDate(selectedSupport.support_end_date) }}
              </span>
              <span :class="daysLeftClass(selectedDaysLeft)">
                {{ formatDaysLeft(selectedDaysLeft) }}
              </span>
              <span class="badge badge-neutral">
                {{ formatSupportType(selectedSupport.support_type) }}
              </span>
            </div>

            <!-- Art. 13(7) disclosure text — ready for copy-paste into customer communications -->
            <div v-if="selectedSupport.user_facing_summary" class="disclosure-block">
              <div class="disclosure-header">
                <span class="field-label">User-facing disclosure text (Art. 13(7))</span>
                <button class="btn-copy" type="button" @click="copyText(selectedSupport.user_facing_summary!)">
                  {{ copySuccessId === 'user' ? 'Copied!' : 'Copy' }}
                </button>
              </div>
              <p class="disclosure-text">{{ selectedSupport.user_facing_summary }}</p>
            </div>

            <div v-if="selectedSupport.packaging_summary" class="disclosure-block">
              <div class="disclosure-header">
                <span class="field-label">Packaging summary</span>
                <button class="btn-copy" type="button" @click="copyText(selectedSupport.packaging_summary!, 'pkg')">
                  {{ copySuccessId === 'pkg' ? 'Copied!' : 'Copy' }}
                </button>
              </div>
              <p class="disclosure-text">{{ selectedSupport.packaging_summary }}</p>
            </div>

            <p v-if="!selectedSupport.user_facing_summary && !selectedSupport.packaging_summary" class="muted">
              No disclosure text has been generated yet. Generate it from the product's support period record.
            </p>
          </div>

          <div v-else class="result-section">
            <p class="muted">No active support period record found for this product.</p>
          </div>

          <!-- Recent security updates for this product -->
          <div class="result-section">
            <h4 class="result-section-title">Recent security updates</h4>

            <div v-if="selectedSecurityUpdates.length === 0" class="muted">
              No security update records found for this product.
            </div>

            <div v-else class="table-wrapper">
              <table class="data-table">
                <thead>
                  <tr>
                    <th>Title</th>
                    <th>Severity</th>
                    <th>CVEs addressed</th>
                    <th>Affected versions</th>
                    <th>Released</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="upd in selectedSecurityUpdates.slice(0, 8)" :key="upd.id">
                    <td>{{ upd.title }}</td>
                    <td>
                      <span class="badge" :class="severityBadge(upd.severity)">
                        {{ formatSeverity(upd.severity) }}
                      </span>
                    </td>
                    <td>
                      <span
                        v-for="cve in normaliseCves(upd.cves_addressed_json)"
                        :key="cve"
                        class="cve-chip"
                      >{{ cve }}</span>
                      <span v-if="normaliseCves(upd.cves_addressed_json).length === 0" class="muted">—</span>
                    </td>
                    <td class="muted">{{ normaliseVersions(upd.affected_versions_json).join(', ') || '—' }}</td>
                    <td class="muted">{{ upd.released_at ? formatDate(upd.released_at) : '—' }}</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>

        </div><!-- /lookup-result -->

        <!-- Empty state when no product selected yet -->
        <div v-else-if="!lookupQuery" class="empty-panel muted">
          Start typing a product name or code above to look up its CRA support status.
        </div>

      </section>

      <!-- ══════════════════════════════════════════
           PANEL 2 — EOS WATCH LIST
           Lifecycle management team monitors products
           approaching or past end-of-support. Helps
           ensure Art. 13(7) communications are issued
           on time.
           ══════════════════════════════════════════ -->
      <section class="card panel">

        <div class="panel-header">
          <div>
            <h2 class="section-title">EOS watch list</h2>
            <p class="muted">
              Products with active support periods ordered by days remaining. Filter by urgency threshold.
            </p>
          </div>

          <!-- Threshold quick-filter -->
          <div class="eos-filter-row">
            <label class="field">
              <span class="field-label">Show</span>
              <select v-model="eosThreshold" class="select">
                <option value="">All with support</option>
                <option value="30">≤ 30 days</option>
                <option value="60">≤ 60 days</option>
                <option value="90">≤ 90 days</option>
                <option value="180">≤ 180 days</option>
                <option value="expired">Expired only</option>
              </select>
            </label>
          </div>
        </div>

        <div v-if="filteredEosRows.length === 0" class="empty-panel muted">
          No products match the selected threshold.
        </div>

        <div v-else class="table-wrapper">
          <table class="data-table">
            <thead>
              <tr>
                <th>Product</th>
                <th>Classification</th>
                <th>Support end</th>
                <th>Days left</th>
                <th>Status</th>
                <th>Support type</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="row in filteredEosRows" :key="row.product.id">
                <td>
                  <div class="product-cell">
                    <strong>{{ row.product.name }}</strong>
                    <code class="muted">{{ row.product.product_code }}</code>
                  </div>
                </td>

                <td>
                  <span class="badge" :class="classificationBadge(row.product.current_classification)">
                    {{ formatClassification(row.product.current_classification) }}
                  </span>
                </td>

                <td class="muted">{{ formatDate(row.support.support_end_date) }}</td>

                <td>
                  <span :class="daysLeftClass(row.daysLeft)">
                    {{ formatDaysLeft(row.daysLeft) }}
                  </span>
                </td>

                <td>
                  <span class="badge" :class="supportStatusBadge(row.eosStatus)">
                    {{ formatEosStatus(row.eosStatus) }}
                  </span>
                </td>

                <td class="muted">{{ formatSupportType(row.support.support_type) }}</td>
              </tr>
            </tbody>
          </table>
        </div>

      </section>

      <!-- ══════════════════════════════════════════
           PANEL 3 — NOTIFICATION QUEUE
           All pending lifecycle notifications across
           all products. Agents mark them as sent once
           communications have been dispatched.
           ══════════════════════════════════════════ -->
      <section class="card panel">

        <div class="panel-header">
          <div>
            <h2 class="section-title">Notification queue</h2>
            <p class="muted">
              Pending lifecycle notifications awaiting dispatch. Mark sent once the communication has been issued.
            </p>
          </div>
        </div>

        <div v-if="notifActionError" class="feedback feedback-error" role="alert">
          {{ notifActionError }}
        </div>

        <div v-if="pendingNotifications.length === 0" class="empty-panel muted">
          No pending notifications — all lifecycle communications are up to date.
        </div>

        <div v-else class="table-wrapper">
          <table class="data-table">
            <thead>
              <tr>
                <th>Product</th>
                <th>Notification</th>
                <th>Recipient</th>
                <th>Scheduled for</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="notif in pendingNotifications" :key="notif.id">
                <!-- Resolve product name via support period record → product map -->
                <td>
                  <span v-if="notifProduct(notif)" class="product-cell">
                    <strong>{{ notifProduct(notif)!.name }}</strong>
                    <code class="muted">{{ notifProduct(notif)!.product_code }}</code>
                  </span>
                  <span v-else class="muted">—</span>
                </td>

                <td>
                  <div class="notif-cell">
                    <strong>{{ notif.title }}</strong>
                    <p class="muted notif-message">{{ notif.message }}</p>
                  </div>
                </td>

                <td class="muted">
                  {{ notif.recipient_user?.full_name ?? '—' }}
                  <br v-if="notif.recipient_user?.email" />
                  <small v-if="notif.recipient_user?.email" class="muted">{{ notif.recipient_user.email }}</small>
                </td>

                <td class="muted">{{ formatDate(notif.scheduled_for) }}</td>

                <td>
                  <div class="action-row">
                    <button
                      class="btn btn-primary btn-sm"
                      type="button"
                      :disabled="!!actionLoading[notif.id]"
                      @click="markSent(notif.id)"
                    >
                      {{ actionLoading[notif.id] === 'sent' ? 'Saving…' : 'Mark sent' }}
                    </button>
                    <button
                      class="btn btn-secondary btn-sm"
                      type="button"
                      :disabled="!!actionLoading[notif.id]"
                      @click="dismiss(notif.id)"
                    >
                      {{ actionLoading[notif.id] === 'dismiss' ? 'Saving…' : 'Dismiss' }}
                    </button>
                  </div>
                </td>
              </tr>
            </tbody>
          </table>
        </div>

      </section>

      <!-- ══════════════════════════════════════════
           PANEL 4 — CVE LOOKUP
           Customer support agents search by CVE ID to
           instantly see which security updates address
           it and which product versions are covered.
           ══════════════════════════════════════════ -->
      <section class="card panel">

        <div class="panel-header">
          <div>
            <h2 class="section-title">CVE lookup</h2>
            <p class="muted">
              Enter a CVE identifier (e.g. <code>CVE-2024-12345</code>) to find the matching security update records.
            </p>
          </div>
        </div>

        <label class="field field-grow">
          <span class="field-label">CVE identifier</span>
          <input
            v-model.trim="cveQuery"
            type="search"
            class="input"
            placeholder="CVE-YYYY-NNNNN"
            autocomplete="off"
            style="max-width: 28rem;"
          />
        </label>

        <!-- CVE search results -->
        <template v-if="cveQuery">
          <div v-if="cveResults.length === 0" class="empty-panel muted">
            No security update records found for <strong>{{ cveQuery }}</strong>.
            This may mean no patch has been published yet, or the CVE ID was entered incorrectly.
          </div>

          <div v-else class="table-wrapper">
            <p class="muted" style="margin-bottom: 0.75rem;">
              {{ cveResults.length }} record(s) found for <strong>{{ cveQuery }}</strong>.
            </p>
            <table class="data-table">
              <thead>
                <tr>
                  <th>Product</th>
                  <th>Security update</th>
                  <th>Severity</th>
                  <th>All CVEs addressed</th>
                  <th>Affected versions</th>
                  <th>Released</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="upd in cveResults" :key="upd.id">
                  <td>
                    <span v-if="productByReleaseId(upd.product_release_id)" class="product-cell">
                      <strong>{{ productByReleaseId(upd.product_release_id)!.name }}</strong>
                      <code class="muted">{{ productByReleaseId(upd.product_release_id)!.product_code }}</code>
                    </span>
                    <code v-else class="muted">{{ upd.product_release_id.slice(0, 8) }}…</code>
                  </td>

                  <td>
                    <strong>{{ upd.title }}</strong>
                  </td>

                  <td>
                    <span class="badge" :class="severityBadge(upd.severity)">
                      {{ formatSeverity(upd.severity) }}
                    </span>
                  </td>

                  <td>
                    <div class="cve-chips">
                      <span
                        v-for="cve in normaliseCves(upd.cves_addressed_json)"
                        :key="cve"
                        class="cve-chip"
                        :class="cve.toUpperCase() === cveQuery.toUpperCase() ? 'cve-chip-highlight' : ''"
                      >{{ cve }}</span>
                    </div>
                  </td>

                  <td class="muted">{{ normaliseVersions(upd.affected_versions_json).join(', ') || '—' }}</td>
                  <td class="muted">{{ upd.released_at ? formatDate(upd.released_at) : '—' }}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </template>

        <div v-else class="empty-panel muted">
          Enter a CVE identifier above to search across all security update records.
        </div>

      </section>

    </template>

  </section>
</template>

<script setup lang="ts">
import { computed, ref } from "vue";

import { lifecycleNotificationService } from "@/services/lifecycle-notification-service";
import { productReleaseService } from "@/services/product-release-service";
import { productService } from "@/services/product-service";
import { securityUpdateService } from "@/services/security-update-service";
import { supportPeriodService } from "@/services/support-period-service";

import type { ProductReleaseRead } from "@/types/release-gate";
import type {
  LifecycleNotificationRead,
  ProductClassification,
  ProductSummaryRead,
  SecurityUpdateRead,
  SecurityUpdateSeverity,
  SupportPeriodRecordRead,
  SupportType,
} from "@/types/product";

/* ── EOS status label used throughout the page ── */
type EosStatus = "active" | "approaching_eos" | "expired";

/* ── Row shape for the EOS watch list table ── */
type EosRow = {
  product: ProductSummaryRead;
  support: SupportPeriodRecordRead;
  daysLeft: number;
  eosStatus: EosStatus;
};

/* ─────────────────────────────────────────────────
   REACTIVE DATA — raw API results
   ───────────────────────────────────────────────── */
const products              = ref<ProductSummaryRead[]>([]);
const activeSupportPeriods  = ref<SupportPeriodRecordRead[]>([]);
const pendingNotifications  = ref<LifecycleNotificationRead[]>([]);
const allSecurityUpdates    = ref<SecurityUpdateRead[]>([]);
const allReleases           = ref<ProductReleaseRead[]>([]);

const isLoading  = ref(false);
const loadError  = ref<string | null>(null);

/* ─────────────────────────────────────────────────
   LOOKUP MAPS — computed from raw data
   ───────────────────────────────────────────────── */

/** product.id → ProductSummaryRead */
const productById = computed<Record<string, ProductSummaryRead>>(() =>
  Object.fromEntries(products.value.map((p) => [p.id, p])),
);

/** support_period_record.product_id → SupportPeriodRecordRead (active only) */
const supportByProductId = computed<Record<string, SupportPeriodRecordRead>>(() =>
  Object.fromEntries(activeSupportPeriods.value.map((s) => [s.product_id, s])),
);

/** support_period_record.id → SupportPeriodRecordRead (for notification → product resolution) */
const supportByRecordId = computed<Record<string, SupportPeriodRecordRead>>(() =>
  Object.fromEntries(activeSupportPeriods.value.map((s) => [s.id, s])),
);

/** product_release.id → product_id (to resolve security updates → product name) */
const releaseProductIdMap = computed<Record<string, string>>(() =>
  Object.fromEntries(allReleases.value.map((r) => [r.id, r.product_id])),
);

/* ─────────────────────────────────────────────────
   DATA LOADING
   ───────────────────────────────────────────────── */
async function loadAll(): Promise<void> {
  isLoading.value = true;
  loadError.value = null;

  try {
    /* Fetch all five data sources in parallel to minimise wait time. */
    const [loadedProducts, loadedSupports, loadedNotifs, loadedUpdates, loadedReleases] =
      await Promise.all([
        productService.list(),
        supportPeriodService.list({ active_only: true }),
        lifecycleNotificationService.list({ status: "pending" }),
        securityUpdateService.list(),
        productReleaseService.list(),
      ]);

    products.value             = loadedProducts;
    activeSupportPeriods.value = loadedSupports;
    pendingNotifications.value = loadedNotifs;
    allSecurityUpdates.value   = loadedUpdates;
    allReleases.value          = loadedReleases;
  } catch (err) {
    loadError.value = err instanceof Error ? err.message : "Failed to load Support Hub data.";
  } finally {
    isLoading.value = false;
  }
}

/* Load on component mount */
void loadAll();

/* ─────────────────────────────────────────────────
   PANEL 1 — PRODUCT SUPPORT LOOKUP
   ───────────────────────────────────────────────── */
const lookupQuery      = ref("");
const selectedProductId = ref<string | null>(null);
const showDropdown     = ref(false);
const copySuccessId    = ref<string | null>(null);

/** Autocomplete candidates — first 8 products matching the query */
const lookupDropdownItems = computed<ProductSummaryRead[]>(() => {
  const q = lookupQuery.value.toLowerCase();
  if (!q) return [];
  return products.value
    .filter(
      (p) =>
        p.name.toLowerCase().includes(q) ||
        p.product_code.toLowerCase().includes(q),
    )
    .slice(0, 8);
});

const selectedProduct = computed<ProductSummaryRead | null>(() =>
  selectedProductId.value ? (productById.value[selectedProductId.value] ?? null) : null,
);

const selectedSupport = computed<SupportPeriodRecordRead | null>(() =>
  selectedProductId.value ? (supportByProductId.value[selectedProductId.value] ?? null) : null,
);

/** Days remaining until the selected product's support period ends */
const selectedDaysLeft = computed<number>(() =>
  selectedSupport.value ? getDaysLeft(selectedSupport.value.support_end_date) : 0,
);

const selectedEosStatus = computed<EosStatus>(() =>
  selectedSupport.value ? deriveEosStatus(selectedDaysLeft.value) : "active",
);

/** Release IDs belonging to the selected product (for security update lookup) */
const selectedReleaseIds = computed<Set<string>>(() => {
  if (!selectedProductId.value) return new Set();
  return new Set(
    allReleases.value
      .filter((r) => r.product_id === selectedProductId.value)
      .map((r) => r.id),
  );
});

/** Security updates that belong to any release of the selected product, newest first */
const selectedSecurityUpdates = computed<SecurityUpdateRead[]>(() =>
  allSecurityUpdates.value
    .filter((u) => selectedReleaseIds.value.has(u.product_release_id))
    .sort((a, b) => {
      const dateA = a.released_at ?? a.created_at;
      const dateB = b.released_at ?? b.created_at;
      return new Date(dateB).getTime() - new Date(dateA).getTime();
    }),
);

function selectProduct(productId: string): void {
  selectedProductId.value = productId;
  const product = productById.value[productId];
  lookupQuery.value = product?.name ?? "";
  showDropdown.value = false;
}

function clearLookup(): void {
  selectedProductId.value = null;
  lookupQuery.value = "";
  showDropdown.value = false;
}

function onLookupBlur(): void {
  /* Delay so the mousedown on a dropdown item fires first */
  setTimeout(() => {
    showDropdown.value = false;
  }, 150);
}

async function copyText(text: string, id = "user"): Promise<void> {
  try {
    await navigator.clipboard.writeText(text);
    copySuccessId.value = id;
    setTimeout(() => {
      copySuccessId.value = null;
    }, 1800);
  } catch {
    /* Clipboard access denied — silently ignore */
  }
}

/* ─────────────────────────────────────────────────
   PANEL 2 — EOS WATCH LIST
   ───────────────────────────────────────────────── */
const eosThreshold = ref<"30" | "60" | "90" | "180" | "expired" | "">("");

/** All products that have an active support period, sorted by days remaining ascending */
const eosRows = computed<EosRow[]>(() =>
  products.value
    .flatMap((product) => {
      const support = supportByProductId.value[product.id];
      if (!support) return [];
      const daysLeft = getDaysLeft(support.support_end_date);
      return [{ product, support, daysLeft, eosStatus: deriveEosStatus(daysLeft) }];
    })
    .sort((a, b) => a.daysLeft - b.daysLeft),
);

const filteredEosRows = computed<EosRow[]>(() => {
  switch (eosThreshold.value) {
    case "30":
      return eosRows.value.filter((r) => r.daysLeft >= 0 && r.daysLeft <= 30);
    case "60":
      return eosRows.value.filter((r) => r.daysLeft >= 0 && r.daysLeft <= 60);
    case "90":
      return eosRows.value.filter((r) => r.daysLeft >= 0 && r.daysLeft <= 90);
    case "180":
      return eosRows.value.filter((r) => r.daysLeft >= 0 && r.daysLeft <= 180);
    case "expired":
      return eosRows.value.filter((r) => r.daysLeft < 0);
    default:
      return eosRows.value;
  }
});

/** Count of products with ≤ 90 days of support remaining (used in stat card) */
const approachingEosCount = computed<number>(
  () => eosRows.value.filter((r) => r.daysLeft >= 0 && r.daysLeft <= 90).length,
);

/* ─────────────────────────────────────────────────
   PANEL 3 — NOTIFICATION QUEUE
   ───────────────────────────────────────────────── */

/** Per-notification action state: notif.id → 'sent' | 'dismiss' | null */
const actionLoading    = ref<Record<string, "sent" | "dismiss" | null>>({});
const notifActionError = ref<string | null>(null);

/**
 * Resolves the product for a given lifecycle notification by traversing:
 * notification.support_period_record_id → support period → product_id → product
 */
function notifProduct(notif: LifecycleNotificationRead): ProductSummaryRead | null {
  const support = supportByRecordId.value[notif.support_period_record_id];
  if (!support) return null;
  return productById.value[support.product_id] ?? null;
}

async function markSent(notifId: string): Promise<void> {
  actionLoading.value[notifId] = "sent";
  notifActionError.value = null;
  try {
    await lifecycleNotificationService.markSent(notifId);
    /* Remove from local queue immediately for optimistic UI update */
    pendingNotifications.value = pendingNotifications.value.filter((n) => n.id !== notifId);
  } catch (err) {
    notifActionError.value = err instanceof Error ? err.message : "Failed to mark notification as sent.";
  } finally {
    actionLoading.value[notifId] = null;
  }
}

async function dismiss(notifId: string): Promise<void> {
  actionLoading.value[notifId] = "dismiss";
  notifActionError.value = null;
  try {
    await lifecycleNotificationService.dismiss(notifId);
    /* Remove from local queue */
    pendingNotifications.value = pendingNotifications.value.filter((n) => n.id !== notifId);
  } catch (err) {
    notifActionError.value = err instanceof Error ? err.message : "Failed to dismiss notification.";
  } finally {
    actionLoading.value[notifId] = null;
  }
}

/* ─────────────────────────────────────────────────
   PANEL 4 — CVE LOOKUP
   ───────────────────────────────────────────────── */
const cveQuery = ref("");

/** Security updates whose cves_addressed_json contains the searched CVE (case-insensitive) */
const cveResults = computed<SecurityUpdateRead[]>(() => {
  const q = cveQuery.value.trim().toUpperCase();
  if (!q) return [];
  return allSecurityUpdates.value.filter((upd) =>
    normaliseCves(upd.cves_addressed_json).some((cve) =>
      cve.toUpperCase().includes(q),
    ),
  );
});

/**
 * Resolves the product that owns a given product release ID.
 * Uses the precomputed releaseProductIdMap to avoid per-row API calls.
 */
function productByReleaseId(releaseId: string): ProductSummaryRead | null {
  const productId = releaseProductIdMap.value[releaseId];
  return productId ? (productById.value[productId] ?? null) : null;
}

/* ─────────────────────────────────────────────────
   SHARED HELPER FUNCTIONS
   ───────────────────────────────────────────────── */

/** Returns whole days remaining until the given ISO date string. Negative = overdue. */
function getDaysLeft(endDateValue: string): number {
  const today = new Date();
  today.setHours(0, 0, 0, 0);
  const end = new Date(`${endDateValue}T00:00:00`);
  end.setHours(0, 0, 0, 0);
  return Math.ceil((end.getTime() - today.getTime()) / 86_400_000);
}

function deriveEosStatus(daysLeft: number): EosStatus {
  if (daysLeft < 0) return "expired";
  if (daysLeft <= 180) return "approaching_eos";
  return "active";
}

/** Normalise cves_addressed_json to a flat string array regardless of backend shape */
function normaliseCves(raw: string[] | Record<string, unknown>): string[] {
  if (Array.isArray(raw)) return raw as string[];
  return Object.keys(raw);
}

/** Normalise affected_versions_json to a flat string array */
function normaliseVersions(raw: string[] | Record<string, unknown>): string[] {
  if (Array.isArray(raw)) return raw as string[];
  return Object.keys(raw);
}

function formatDate(value: string): string {
  return new Intl.DateTimeFormat(undefined, {
    year: "numeric",
    month: "short",
    day: "2-digit",
  }).format(new Date(value));
}

function formatDaysLeft(daysLeft: number): string {
  if (daysLeft < 0) return `${Math.abs(daysLeft)}d overdue`;
  if (daysLeft === 0) return "Ends today";
  return `${daysLeft}d remaining`;
}

function daysLeftClass(daysLeft: number): string {
  if (daysLeft < 0) return "text-danger fw-600";
  if (daysLeft <= 90) return "text-warning fw-600";
  return "text-success fw-600";
}

function formatEosStatus(status: EosStatus): string {
  switch (status) {
    case "active":          return "Active";
    case "approaching_eos": return "Approaching EOS";
    case "expired":         return "Expired";
  }
}

function supportStatusBadge(status: EosStatus): string {
  switch (status) {
    case "active":          return "badge-success";
    case "approaching_eos": return "badge-warning";
    case "expired":         return "badge-danger";
  }
}

function formatClassification(value: ProductClassification): string {
  switch (value) {
    case "important_class_1": return "Important Class I";
    case "important_class_2": return "Important Class II";
    case "critical":          return "Critical";
    default:                  return "Normal";
  }
}

function classificationBadge(value: ProductClassification): string {
  switch (value) {
    case "critical":         return "badge-danger";
    case "important_class_1":
    case "important_class_2": return "badge-warning";
    default:                  return "badge-neutral";
  }
}

function formatSupportType(type: SupportType): string {
  switch (type) {
    case "standard": return "Standard";
    case "limited":  return "Limited";
    case "extended": return "Extended";
    case "custom":   return "Custom";
  }
}

function formatSeverity(severity: SecurityUpdateSeverity | null): string {
  if (!severity) return "None";
  return severity.charAt(0).toUpperCase() + severity.slice(1);
}

function severityBadge(severity: SecurityUpdateSeverity | null): string {
  switch (severity) {
    case "critical":      return "badge-danger";
    case "high":          return "badge-danger";
    case "medium":        return "badge-warning";
    case "low":           return "badge-success";
    case "informational": return "badge-neutral";
    default:              return "badge-neutral";
  }
}
</script>

<style scoped>
/* ═══════════════════════════════════════════════
   PAGE SHELL
   ═══════════════════════════════════════════════ */
.page {
  display: grid;
  gap: 1rem;
}

.page-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 1rem;
  flex-wrap: wrap;
}

.page-actions {
  display: flex;
  gap: 0.75rem;
  align-items: center;
}

.page-title {
  margin: 0;
}

.page-subtitle {
  margin-top: 0.35rem;
}

/* ═══════════════════════════════════════════════
   STAT CARDS
   ═══════════════════════════════════════════════ */
.stats-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 1rem;
}

.stat-card {
  display: grid;
  gap: 0.35rem;
}

.stat-label {
  margin: 0;
  font-size: var(--text-sm);
}

.stat-value {
  font-size: 1.65rem;
}

/* ═══════════════════════════════════════════════
   PANELS — shared card layout
   ═══════════════════════════════════════════════ */
.panel {
  display: grid;
  gap: 1rem;
}

.panel-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 1rem;
  flex-wrap: wrap;
}

.section-title {
  margin: 0;
  font-size: 1.05rem;
}

/* ═══════════════════════════════════════════════
   PANEL 1 — PRODUCT LOOKUP
   ═══════════════════════════════════════════════ */
.lookup-search-row {
  display: flex;
  gap: 0.75rem;
  align-items: flex-end;
  flex-wrap: wrap;
  position: relative;
}

.field-grow {
  flex: 1;
  min-width: 0;
}

.lookup-dropdown {
  list-style: none;
  margin: 0;
  padding: 0.3rem;
  border: 1px solid var(--color-border, rgba(148, 163, 184, 0.2));
  border-radius: var(--radius-md, 0.85rem);
  background: var(--color-surface, #0f172a);
  box-shadow: var(--shadow-lg);
  max-height: 260px;
  overflow-y: auto;
  position: relative;
  z-index: 10;
}

.lookup-option {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 0.75rem;
  padding: 0.6rem 0.8rem;
  border-radius: 0.6rem;
  cursor: pointer;
  transition: background var(--t-fast);
}

.lookup-option:hover {
  background: var(--color-nav-hover-bg, rgba(148, 163, 184, 0.08));
}

.lookup-option-name {
  font-weight: 600;
  font-size: var(--text-sm);
}

.lookup-option-code {
  font-size: 0.75rem;
}

.lookup-no-results {
  padding: 0.6rem 0;
  font-size: var(--text-sm);
}

/* Selected product result card */
.lookup-result {
  display: grid;
  gap: 1.25rem;
  padding: 1.1rem;
  border: 1px solid var(--color-border, rgba(148, 163, 184, 0.18));
  border-radius: var(--radius-md, 0.85rem);
  background: var(--color-surface-soft, rgba(15, 23, 42, 0.45));
}

.result-identity {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 1rem;
  flex-wrap: wrap;
}

.result-product-name {
  margin: 0;
  font-size: 1.1rem;
}

.result-product-meta {
  margin: 0.2rem 0 0;
  font-size: var(--text-sm);
}

.result-section {
  display: grid;
  gap: 0.65rem;
}

.result-section-title {
  margin: 0;
  font-size: 0.85rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: var(--color-text-muted, #94a3b8);
}

.support-meta-row {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  flex-wrap: wrap;
}

/* Disclosure text blocks for Art. 13(7) copy-paste */
.disclosure-block {
  display: grid;
  gap: 0.5rem;
}

.disclosure-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.5rem;
}

.disclosure-text {
  margin: 0;
  font-size: var(--text-sm);
  line-height: 1.6;
  padding: 0.75rem 0.9rem;
  border: 1px solid var(--color-border, rgba(148, 163, 184, 0.15));
  border-radius: 0.65rem;
  background: var(--color-surface, rgba(15, 23, 42, 0.6));
  white-space: pre-wrap;
}

/* Inline copy button */
.btn-copy {
  font: inherit;
  font-size: 0.75rem;
  padding: 0.25rem 0.6rem;
  border-radius: 0.5rem;
  border: 1px solid var(--color-border, rgba(148, 163, 184, 0.25));
  background: transparent;
  color: var(--color-primary-2, #add654);
  cursor: pointer;
  transition: background var(--t-fast);
  flex-shrink: 0;
}

.btn-copy:hover {
  background: rgba(173, 214, 84, 0.1);
}

/* CVE chips in the security updates table */
.cve-chips {
  display: flex;
  flex-wrap: wrap;
  gap: 0.3rem;
}

.cve-chip {
  display: inline-block;
  font-size: 0.72rem;
  font-family: var(--font-mono, monospace);
  padding: 0.15rem 0.45rem;
  border-radius: 0.4rem;
  background: rgba(148, 163, 184, 0.12);
  color: var(--color-text-muted, #94a3b8);
}

.cve-chip-highlight {
  background: rgba(251, 191, 36, 0.18);
  color: #fde68a;
  font-weight: 700;
}

/* ═══════════════════════════════════════════════
   PANEL 2 — EOS WATCH LIST
   ═══════════════════════════════════════════════ */
.eos-filter-row {
  display: flex;
  gap: 0.75rem;
  align-items: flex-end;
}

/* ═══════════════════════════════════════════════
   PANEL 3 — NOTIFICATION QUEUE
   ═══════════════════════════════════════════════ */
.notif-cell {
  display: grid;
  gap: 0.2rem;
  max-width: 26rem;
}

.notif-message {
  font-size: var(--text-sm);
  margin: 0;
  line-height: 1.4;
  /* Clamp long messages to 2 lines for table readability */
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.action-row {
  display: flex;
  gap: 0.4rem;
  flex-wrap: nowrap;
}

/* ═══════════════════════════════════════════════
   SHARED TABLE STYLES
   ═══════════════════════════════════════════════ */
.table-wrapper {
  overflow-x: auto;
}

.data-table {
  width: 100%;
  border-collapse: collapse;
}

.data-table th,
.data-table td {
  padding: 0.8rem 0.75rem;
  text-align: left;
  border-bottom: 1px solid var(--color-border, rgba(148, 163, 184, 0.18));
  vertical-align: top;
}

.data-table th {
  color: var(--color-text-muted, #94a3b8);
  font-size: 0.82rem;
  font-weight: 600;
  white-space: nowrap;
}

.product-cell {
  display: grid;
  gap: 0.2rem;
}

/* ═══════════════════════════════════════════════
   BADGES
   ═══════════════════════════════════════════════ */
.badge {
  display: inline-flex;
  align-items: center;
  border-radius: 999px;
  padding: 0.3rem 0.65rem;
  font-size: 0.75rem;
  font-weight: 600;
  width: fit-content;
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

/* ═══════════════════════════════════════════════
   TEXT UTILITIES
   ═══════════════════════════════════════════════ */
.text-success { color: #86efac; }
.text-warning { color: #fde68a; }
.text-danger  { color: #fda4af; }
.fw-600       { font-weight: 600; }

/* ═══════════════════════════════════════════════
   FORM CONTROLS (self-contained so this view has
   no dependency on global .input / .select)
   ═══════════════════════════════════════════════ */
.field {
  display: grid;
  gap: 0.4rem;
}

.field-label {
  font-size: 0.875rem;
  color: var(--color-text-muted, #94a3b8);
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

.btn {
  border: 1px solid transparent;
  border-radius: 0.85rem;
  padding: 0.65rem 1rem;
  font: inherit;
  cursor: pointer;
  white-space: nowrap;
}

.btn-sm {
  padding: 0.4rem 0.7rem;
  font-size: var(--text-sm);
  border-radius: 0.6rem;
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

.btn:disabled {
  opacity: 0.55;
  cursor: not-allowed;
}

/* ═══════════════════════════════════════════════
   FEEDBACK & EMPTY STATE
   ═══════════════════════════════════════════════ */
.feedback,
.empty-panel {
  padding: 1rem 1.1rem;
  border-radius: var(--radius-md, 0.85rem);
  font-size: var(--text-sm);
}

.empty-panel {
  background: var(--color-surface-soft, rgba(15, 23, 42, 0.35));
}

.feedback-error {
  background: rgba(251, 113, 133, 0.08);
  border: 1px solid rgba(251, 113, 133, 0.2);
  color: #fda4af;
}

/* ═══════════════════════════════════════════════
   RESPONSIVE BREAKPOINTS
   ═══════════════════════════════════════════════ */
@media (max-width: 1200px) {
  .stats-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 700px) {
  .stats-grid {
    grid-template-columns: 1fr;
  }

  .panel-header {
    flex-direction: column;
  }
}
</style>

<!-- Light-theme overrides (non-scoped so :root selector works) -->
<style>
:root[data-theme="light"] .lookup-dropdown                { background: #ffffff; }
:root[data-theme="light"] .disclosure-text                { background: rgba(241, 245, 249, 0.8); }
:root[data-theme="light"] .lookup-result                  { background: rgba(241, 245, 249, 0.6); }
:root[data-theme="light"] .badge-neutral  { background: rgba(71,85,105,0.1);   color: #475569; }
:root[data-theme="light"] .badge-success  { background: rgba(21,128,61,0.1);   color: #15803d; }
:root[data-theme="light"] .badge-warning  { background: rgba(184,155,18,0.1);  color: #78350f; }
:root[data-theme="light"] .badge-danger   { background: rgba(239,68,68,0.1);   color: #be123c; }
:root[data-theme="light"] .text-success   { color: #15803d; }
:root[data-theme="light"] .text-warning   { color: #78350f; }
:root[data-theme="light"] .text-danger    { color: #be123c; }
:root[data-theme="light"] .feedback-error { background: rgba(239,68,68,0.06); border-color: rgba(239,68,68,0.2); color: #be123c; }
:root[data-theme="light"] .cve-chip       { background: rgba(71,85,105,0.1); color: #475569; }
:root[data-theme="light"] .cve-chip-highlight { background: rgba(184,155,18,0.15); color: #78350f; }
:root[data-theme="light"] .btn-primary    { background: linear-gradient(135deg, #7c3aed, #2563eb); }
</style>
