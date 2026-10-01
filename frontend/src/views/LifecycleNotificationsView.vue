<!--
  CRANE — CRA Norm Engine
  Copyright (C) 2026 Ali Mohammad Hosseini
  SPDX-License-Identifier: AGPL-3.0-or-later
  See <https://www.gnu.org/licenses/>.
-->
<template>
  <section class="lifecycle-page">
    <header class="page-header" data-guide="lifecycle-header">
      <div class="page-heading">
        <h1 class="page-title">Lifecycle alerts</h1>
        <p class="muted page-subtitle">Review notifications, plan support transitions, and address supplier coverage gaps.</p>
      </div>
      <AppButton class="embedded-guide-trigger" variant="secondary" @click="startGuide"><span aria-hidden="true">?</span> Guide</AppButton>
      <div class="page-actions">
        <AppButton :disabled="isRefreshing || isRunningScheduler" @click="refresh">{{ isRefreshing ? 'Refreshing…' : 'Refresh' }}</AppButton>
        <AppButton v-if="canWrite" variant="primary" :disabled="isRunningScheduler || isRefreshing" @click="runScheduler">{{ isRunningScheduler ? 'Checking…' : 'Check support deadlines' }}</AppButton>
      </div>
    </header>
    <p class="muted small-text">Checks use each support record’s notification settings. Filters below only change what you see.</p>
    <div v-if="actionError" class="feedback feedback-error" role="alert">{{ actionError }}</div>
    <div v-if="successMessage" class="feedback feedback-success" role="status">{{ successMessage }}</div>

    <section class="summary-grid" aria-label="Lifecycle overview" data-guide="lifecycle-summary">
      <button class="summary-card" :disabled="loading.queue || !!errors.queue" @click="showPending">
        <span>Awaiting review</span><strong>{{ loading.queue || errors.queue ? '—' : pendingCount }}</strong><small>Notifications in your queue →</small>
      </button>
      <button v-if="canReadSupport" class="summary-card danger" :disabled="loading.products || !!errors.products" @click="showSupport('ended')">
        <span>Support periods ended</span><strong>{{ loading.products || errors.products ? '—' : endedCount }}</strong><small>Review support transitions →</small>
      </button>
      <button v-if="canReadSupport" class="summary-card warning" :disabled="loading.products || !!errors.products" @click="showSupport('90')">
        <span>Ending within 90 days</span><strong>{{ loading.products || errors.products ? '—' : upcomingCount }}</strong><small>Prepare your next steps →</small>
      </button>
      <button v-if="canReadComponents" class="summary-card warning" :disabled="loading.components || !!errors.components" @click="showCoverage">
        <span>Coverage needs review</span><strong>{{ loading.components || errors.components ? '—' : componentRiskCount }}</strong><small>Component–release relationships →</small>
      </button>
    </section>

    <section class="card workspace" data-guide="lifecycle-results">
      <nav class="section-nav" aria-label="Lifecycle views">
        <button v-for="item in sections" :key="item.id" :data-guide="`lifecycle-${item.id}`" :aria-current="section === item.id ? 'page' : undefined" :aria-controls="`lifecycle-${item.id}`" @click="section = item.id">{{ item.label }}</button>
      </nav>
      <div class="workspace-body" :id="`lifecycle-${section}`">
        <div class="section-header">
          <div><h2 ref="resultsHeading" tabindex="-1">{{ sectionTitle }}</h2><p class="muted">{{ sectionDescription }}</p></div>
          <span v-if="!loading[section] && !errors[section]" class="result-count" role="status">{{ resultCount }} {{ section === 'queue' ? 'notifications' : section === 'products' ? 'support records / products' : 'relationships' }}</span>
        </div>
        <div class="filters" data-guide="lifecycle-filters">
          <label class="search-field">Search {{ section === 'queue' ? 'notifications' : section === 'products' ? 'products' : 'components' }}<input v-model.trim="search" type="search" :placeholder="section === 'queue' ? 'Title, message, or recipient' : section === 'products' ? 'Name, code, or manufacturer' : 'Component, supplier, or product'" /></label>
          <template v-if="section === 'queue'">
            <label>Status<select v-model="queueStatus"><option value="pending">Awaiting review</option><option value="sent">Recorded as sent</option><option value="dismissed">Dismissed</option><option value="all">All statuses</option></select></label>
            <label>Notification type<select v-model="notificationType"><option value="">All types</option><option value="end_of_support_upcoming">Product support</option><option value="component_end_of_support_upcoming">Component support</option><option value="security_update_available">Security update</option></select></label>
          </template>
          <template v-else-if="section === 'products'">
            <label>Support window<select v-model="supportWindow"><option value="all">All support records</option><option value="ended">Support ended</option><option value="30">Ends within 30 days</option><option value="90">Ends within 90 days</option><option value="180">Ends within 180 days</option><option value="365">Ends within 1 year</option><option value="custom">Custom window</option><option value="missing">No active support record</option></select></label>
            <label v-if="supportWindow === 'custom'">Days from today<input v-model.number="customDays" type="number" min="1" max="36500" step="1" :aria-invalid="!validCustomDays" aria-describedby="custom-days-error" /></label>
            <label>CRA classification<select v-model="classification"><option value="">All classifications</option><option value="normal">Default</option><option value="important_class_1">Important Class I</option><option value="important_class_2">Important Class II</option><option value="critical">Critical</option><option value="foss">FOSS</option></select></label>
          </template>
          <label v-else>Coverage<select v-model="coverageStatus"><option value="attention">Needs review</option><option value="all">All relationships</option><option value="ended">Supplier support ended</option><option value="gap">Support gap</option><option value="unknown">Support dates unknown</option><option value="expiring">Supplier support ending soon</option><option value="covered">Covered</option></select></label>
          <label>Sort by<select v-model="sortOrder"><option value="attention">{{ section === 'queue' ? 'Awaiting review, oldest first' : section === 'products' ? 'Earliest support end' : 'Highest severity first' }}</option><option value="newest">{{ section === 'queue' ? 'Newest first' : section === 'products' ? 'Latest updated' : 'Latest supplier support end' }}</option><option value="name">Name A–Z</option></select></label>
          <AppButton variant="ghost" @click="resetFilters">Reset filters</AppButton>
        </div>
        <p v-if="section === 'products' && supportWindow === 'custom' && !validCustomDays" id="custom-days-error" class="feedback-error" role="alert">Enter a whole number between 1 and 36,500 days.</p>
        <div v-if="loading[section]" class="empty-state" role="status">Loading {{ sectionTitle.toLowerCase() }}…</div>
        <div v-else-if="errors[section]" class="empty-state feedback-error" role="alert"><h3>Could not load {{ sectionTitle.toLowerCase() }}</h3><p>{{ errors[section] }}</p><AppButton @click="refresh">Try again</AppButton></div>
        <template v-else>
          <div v-if="resultCount === 0" class="empty-state">
            <h3>{{ section === 'queue' && queueStatus === 'pending' && !search && !notificationType ? 'No notifications awaiting review' : 'No matching results' }}</h3>
            <p class="muted">{{ section === 'queue' ? 'Review notification history or check support deadlines for new notifications.' : 'Adjust your filters. Support dates and component links are managed in their source records.' }}</p>
            <AppButton @click="resetFilters">Show all {{ section === 'queue' ? 'notifications' : 'records' }}</AppButton>
          </div>
          <div v-if="section === 'queue'" class="alert-list">
            <article v-for="alert in pageAlerts" :key="alert.id" class="alert-card">
              <div class="alert-heading"><span class="badge" :class="alert.status === 'pending' ? 'badge-warning' : 'badge-neutral'">{{ statusLabel(alert.status) }}</span><span class="muted small-text">{{ typeLabel(alert.notification_type) }}</span><time class="alert-date muted small-text" :datetime="alert.created_at">Created {{ formatDate(alert.created_at) }}</time></div>
              <h3>{{ alert.title }}</h3><p class="alert-message">{{ alert.message }}</p>
              <div class="alert-footer">
                <div class="alert-context muted small-text">
                  <span>Recipient: {{ alert.recipient_user?.full_name || 'Not specified' }}</span>
                  <span v-if="alert.status === 'sent' && alert.sent_at">Recorded as sent {{ formatDate(alert.sent_at) }}</span><span v-if="alert.status === 'dismissed' && alert.dismissed_at">Dismissed {{ formatDate(alert.dismissed_at) }}</span>
                  <RouterLink v-if="alert.third_party_component_id && canReadComponents" :to="{ name: 'third-party-component-detail', params: { componentId: alert.third_party_component_id } }">Review component →</RouterLink>
                  <RouterLink v-else-if="alert.support_period_record_id && supportProductId(alert.support_period_record_id)" :to="{ name: 'product-detail', params: { productId: supportProductId(alert.support_period_record_id) } }">Review product →</RouterLink>
                  <RouterLink v-else-if="alert.security_update_id && auth.hasPermission('security_update_read')" :to="{ name: 'security-updates' }">Review security updates →</RouterLink>
                </div>
                <div v-if="canWrite && alert.status === 'pending'" class="row-actions"><AppButton :disabled="!!actioningId" @click="openAction(alert, 'sent')">Record as sent</AppButton><AppButton variant="ghost" :disabled="!!actioningId" @click="openAction(alert, 'dismissed')">Dismiss</AppButton></div>
              </div>
            </article>
            <p class="muted small-text">“Recorded as sent” tracks communication completed outside this queue. It does not send a message or resolve the underlying support risk.</p>
            <p v-if="!canWrite" class="muted small-text">You have read-only access to notifications.</p>
          </div>
          <div v-else-if="section === 'products'">
            <div v-if="resultCount" class="table-wrapper" tabindex="0" role="region" aria-label="Product support records, scroll horizontally for more columns">
              <table><caption class="sr-only">Product and release support records, earliest end dates first by default</caption><thead><tr><th scope="col">Product / scope</th><th scope="col">CRA classification</th><th scope="col">Support ends</th><th scope="col">Support status</th><th scope="col">Next step</th></tr></thead>
                <tbody><tr v-for="row in pageProducts" :key="row.support?.id || row.product.id">
                  <td><RouterLink :to="{ name: 'product-detail', params: { productId: row.product.id } }"><strong>{{ row.product.name }}</strong></RouterLink><p class="muted small-text">{{ row.product.product_code }} · {{ row.product.manufacturer_name }}</p><p class="muted small-text"><RouterLink v-if="row.support?.product_release_id && auth.hasPermission('release_read')" :to="{ name: 'release-gate', params: { releaseId: row.support.product_release_id } }">Release {{ releaseLabels[row.support.product_release_id] || 'details' }} →</RouterLink><template v-else>{{ row.support?.product_release_id ? 'Release-specific support' : row.support ? 'Product-wide support' : 'No active support record' }}</template></p></td>
                  <td>{{ classificationLabel(row.product.current_classification) }}</td><td>{{ row.support ? formatDate(row.support.support_end_date) : 'Not defined' }}<p v-if="row.days !== null" class="muted small-text">{{ daysLabel(row.days) }}</p></td>
                  <td><span class="badge" :class="row.days === null ? 'badge-neutral' : row.days < 0 ? 'badge-danger' : row.days <= 180 ? 'badge-warning' : 'badge-success'">{{ row.days === null ? 'No active record' : row.days < 0 ? 'Support ended' : row.days <= 180 ? 'Ends within 180 days' : row.support && row.support.support_start_date > today ? 'Support scheduled' : 'Support ongoing' }}</span></td>
                  <td><p class="next-step">{{ row.days === null ? 'Define support dates and recipients.' : row.days < 0 ? 'Review transition plans and customer communication.' : row.days <= 180 ? 'Plan the support transition and notify recipients.' : 'Keep support commitments and recipients current.' }}</p><RouterLink :to="{ name: 'product-detail', params: { productId: row.product.id } }">Review support →</RouterLink></td>
                </tr></tbody>
              </table>
            </div><p class="muted small-text">Each active product-wide or release-specific support record is shown separately. Products without any active record are included for follow-up.</p>
          </div>
          <div v-else>
            <div v-if="resultCount" class="table-wrapper" tabindex="0" role="region" aria-label="Component support coverage, scroll horizontally for more columns">
              <table><caption class="sr-only">Supplier component coverage for each linked product release</caption><thead><tr><th scope="col">Component / supplier</th><th scope="col">Affected release</th><th scope="col">Support dates</th><th scope="col">Coverage</th><th scope="col">Next step</th></tr></thead>
                <tbody><tr v-for="row in pageComponents" :key="row.link_id">
                  <td><RouterLink :to="{ name: 'third-party-component-detail', params: { componentId: row.component_id } }"><strong>{{ row.component_name }} {{ row.component_version }}</strong></RouterLink><p class="muted small-text">{{ row.supplier_name }}</p></td>
                  <td><RouterLink v-if="auth.hasPermission('product_read')" :to="{ name: 'product-detail', params: { productId: row.product_id } }">{{ row.product_name }}</RouterLink><strong v-else>{{ row.product_name }}</strong><p class="muted small-text">{{ row.release_version }}<template v-if="row.is_core_function"> · Core function</template></p></td>
                  <td><p class="small-text">Supplier: {{ formatDate(row.component_support_end_date) }}</p><p class="small-text">Product: {{ formatDate(row.product_support_end_date) }}</p></td>
                  <td><span class="badge" :class="row.status === 'covered' ? 'badge-success' : row.status === 'unknown' ? 'badge-neutral' : ['critical', 'high'].includes(row.severity) ? 'badge-danger' : 'badge-warning'">{{ coverageLabel(row.status) }}</span><p v-if="row.support_gap_days" class="muted small-text">{{ row.support_gap_days }} days of coverage gap</p></td>
                  <td><p class="next-step">{{ coverageNextStep(row.status) }}</p><RouterLink :to="{ name: 'third-party-component-detail', params: { componentId: row.component_id } }">Review component →</RouterLink></td>
                </tr></tbody>
              </table>
            </div><p class="muted small-text">Supplier support ending is a risk input. It does not shorten your product’s support commitment. Counts represent component–release relationships, not unique components.</p>
          </div>
          <nav v-if="resultCount > pageSize" class="pagination" aria-label="Results pagination"><span class="muted small-text" aria-live="polite">{{ (page - 1) * pageSize + 1 }}–{{ Math.min(page * pageSize, resultCount) }} of {{ resultCount }} · Page {{ page }} of {{ pageCount }}</span><div class="row-actions"><AppButton :disabled="page === 1" @click="page--">Previous</AppButton><AppButton :disabled="page === pageCount" @click="page++">Next</AppButton></div></nav>
        </template>
      </div>
    </section>
    <dialog ref="actionDialog" class="action-dialog" aria-labelledby="lifecycle-action-title" aria-describedby="lifecycle-action-description" @cancel="preventBusyClose" @close="selectedAction = null">
      <template v-if="selectedAction">
        <h2 id="lifecycle-action-title">{{ selectedAction.status === 'sent' ? 'Record this notification as sent?' : 'Dismiss this notification?' }}</h2><p><strong>{{ selectedAction.alert.title }}</strong></p>
        <p id="lifecycle-action-description">{{ selectedAction.status === 'sent' ? 'Confirm that the communication has already been sent outside CRANE. This action records its status; it does not deliver an email or message.' : 'This removes the notification from the review queue. It remains in dismissed history and does not resolve the underlying support risk.' }}</p>
        <p v-if="dialogError" class="feedback feedback-error" role="alert">{{ dialogError }}</p>
        <div class="dialog-actions"><AppButton :disabled="!!actioningId" autofocus @click="actionDialog?.close()">Cancel</AppButton><AppButton variant="primary" :disabled="!!actioningId" @click="confirmAction">{{ actioningId ? 'Saving…' : selectedAction.status === 'sent' ? 'Confirm sent' : 'Confirm dismissal' }}</AppButton></div>
      </template>
    </dialog>
  </section>
</template>

<script setup lang="ts">
import { computed, nextTick, onMounted, onBeforeUnmount, reactive, ref, watch } from 'vue';
import { RouterLink } from 'vue-router';
import AppButton from '@/components/AppButton.vue';
import { useAuthStore } from '@/stores/auth';
import { lifecycleNotificationService } from '@/services/lifecycle-notification-service';
import { productService } from '@/services/product-service';
import { productReleaseService } from '@/services/product-release-service';
import { supplierAssessmentService } from '@/services/supplier-assessment-service';
import { supportPeriodService } from '@/services/support-period-service';
import type { LifecycleNotificationRead, LifecycleNotificationStatus, ProductSummaryRead, SupportPeriodRecordRead } from '@/types/product';
import type { ComponentSupportGap } from '@/types/supplier-assessment';

type Section = 'queue' | 'products' | 'components';
type SupportRow = { product: ProductSummaryRead; support: SupportPeriodRecordRead | null; days: number | null };
function startGuide(): void { window.dispatchEvent(new Event("crane-guide-start")); }
const auth = useAuthStore();
const canWrite = computed(() => auth.hasPermission('lifecycle_notification_write'));
const canReadSupport = computed(() => auth.hasPermission('product_read') && auth.hasPermission('support_period_read'));
const canReadComponents = computed(() => auth.hasPermission('supplier_assessment_read'));
const section = ref<Section>('queue');
const sections = computed(() => [
  { id: 'queue' as const, label: 'Notification queue' },
  ...(canReadSupport.value ? [{ id: 'products' as const, label: 'Product support' }] : []),
  ...(canReadComponents.value ? [{ id: 'components' as const, label: 'Component coverage' }] : []),
]);
const sectionTitle = computed(() => ({ queue: 'Notification queue', products: 'Product support', components: 'Component coverage' })[section.value]);
const sectionDescription = computed(() => ({
  queue: 'Review the source, complete the communication, then record the outcome. This queue shows notifications assigned to you.',
  products: 'Check support commitments across products and releases. Open a product to review dates and notification recipients.',
  components: 'Identify supplier support that ends before your product commitment and plan mitigation.',
})[section.value]);
const alerts = ref<LifecycleNotificationRead[]>([]);
const products = ref<ProductSummaryRead[]>([]);
const supportRecords = ref<SupportPeriodRecordRead[]>([]);
const releaseLabels = ref<Record<string, string>>({});
const components = ref<ComponentSupportGap[]>([]);
const loading = reactive({ queue: true, products: true, components: true });
const errors = reactive({ queue: '', products: '', components: '' });
const isRefreshing = ref(false);
const isRunningScheduler = ref(false);
const successMessage = ref('');
const actionError = ref('');
const search = ref('');
const queueStatus = ref<LifecycleNotificationStatus | 'all'>('pending');
const notificationType = ref('');
const supportWindow = ref('all');
const customDays = ref<number | string>(120);
const validCustomDays = computed(() => Number.isInteger(customDays.value) && Number(customDays.value) >= 1 && Number(customDays.value) <= 36500);
const classification = ref('');
const coverageStatus = ref('attention');
const sortOrder = ref('attention');
const page = ref(1);
const pageSize = 20;
// UTC date-only arithmetic matches the scheduler and avoids daylight-saving shifts.
const today = ref(new Date().toISOString().slice(0, 10));
const daysUntil = (date: string) => Math.round((Date.parse(date.slice(0, 10)) - Date.parse(today.value)) / 86400000);
const dateFormatter = new Intl.DateTimeFormat(undefined, { year: 'numeric', month: 'short', day: 'numeric' });
function formatDate(value: string | null): string {
  if (!value) return 'Unknown';
  const date = new Date(value.length === 10 ? `${value}T12:00:00` : value);
  return Number.isNaN(date.getTime()) ? 'Unknown' : dateFormatter.format(date);
}
function daysLabel(days: number): string {
  if (days === 0) return 'Ends today';
  const count = Math.abs(days);
  return days < 0 ? `Ended ${count} ${count === 1 ? 'day' : 'days'} ago` : `${count} ${count === 1 ? 'day' : 'days'} remaining`;
}
const statusLabels: Record<string, string> = { pending: 'Awaiting review', sent: 'Recorded as sent', dismissed: 'Dismissed' };
const typeLabels: Record<string, string> = { end_of_support_upcoming: 'Product support', component_end_of_support_upcoming: 'Component support', security_update_available: 'Security update' };
const classificationLabels: Record<string, string> = { normal: 'Default', important_class_1: 'Important Class I', important_class_2: 'Important Class II', critical: 'Critical', foss: 'FOSS' };
const coverageLabels: Record<string, string> = { unknown: 'Support dates unknown', ended: 'Supplier support ended', gap: 'Support gap', expiring: 'Supplier support ending soon', covered: 'Covered' };
const coverageNextSteps: Record<string, string> = { unknown: 'Confirm supplier and product support dates.', ended: 'Review replacement, extended support, or internal maintenance.', gap: 'Plan coverage for the remaining product support period.', expiring: 'Confirm a transition or support extension.', covered: 'Monitor supplier commitments.' };
const statusLabel = (value: string) => statusLabels[value] || value;
const typeLabel = (value: string) => typeLabels[value] || value;
const classificationLabel = (value: string) => classificationLabels[value] || value;
const coverageLabel = (value: string) => coverageLabels[value] || value;
const coverageNextStep = (value: string) => coverageNextSteps[value] || 'Review the source record.';
const query = computed(() => search.value.toLowerCase());
const matches = (...values: unknown[]) => values.join(' ').toLowerCase().includes(query.value);
const supportById = computed(() => new Map(supportRecords.value.map(record => [record.id, record])));
const supportProductId = (id: string) => supportById.value.get(id)?.product_id;
const supportRows = computed<SupportRow[]>(() => {
  const grouped = new Map<string, SupportPeriodRecordRead[]>();
  for (const record of supportRecords.value) {
    if (!record.is_active) continue;
    const records = grouped.get(record.product_id) || [];
    records.push(record); grouped.set(record.product_id, records);
  }
  return products.value.flatMap<SupportRow>(product => {
    const records = grouped.get(product.id);
    return records?.length ? records.map(support => ({ product, support, days: daysUntil(support.support_end_date) })) : [{ product, support: null, days: null }];
  });
});
const pendingCount = computed(() => alerts.value.filter(alert => alert.status === 'pending').length);
const endedCount = computed(() => supportRows.value.filter(row => row.days !== null && row.days < 0).length);
const upcomingCount = computed(() => supportRows.value.filter(row => row.days !== null && row.days >= 0 && row.days <= 90).length);
const componentRiskCount = computed(() => components.value.filter(row => row.status !== 'covered').length);
const filteredAlerts = computed(() => alerts.value.filter(alert =>
  (queueStatus.value === 'all' || alert.status === queueStatus.value) && (!notificationType.value || alert.notification_type === notificationType.value) && matches(alert.title, alert.message, alert.recipient_user?.full_name, alert.third_party_component?.name),
).sort((a, b) => sortOrder.value === 'name' ? a.title.localeCompare(b.title) : sortOrder.value === 'newest' ? b.created_at.localeCompare(a.created_at) : Number(b.status === 'pending') - Number(a.status === 'pending') || a.created_at.localeCompare(b.created_at)));
const filteredProducts = computed(() => supportRows.value.filter(row => {
  const window = supportWindow.value;
  const limit = window === 'custom' ? Number(customDays.value) : Number(window);
  const withinWindow = window === 'all' || (window === 'missing' ? row.days === null : row.days !== null && (window === 'ended' ? row.days < 0 : (window !== 'custom' || validCustomDays.value) && row.days >= 0 && row.days <= limit));
  return withinWindow && (!classification.value || row.product.current_classification === classification.value) && matches(row.product.name, row.product.product_code, row.product.manufacturer_name, row.product.product_type);
}).sort((a, b) => sortOrder.value === 'name' ? a.product.name.localeCompare(b.product.name) : sortOrder.value === 'newest' ? b.product.updated_at.localeCompare(a.product.updated_at) : (a.days ?? Infinity) - (b.days ?? Infinity)));
const severityRank: Record<string, number> = { critical: 0, high: 1, medium: 2, low: 3, info: 4 };
const filteredComponents = computed(() => components.value.filter(row =>
  (coverageStatus.value === 'all' || (coverageStatus.value === 'attention' ? row.status !== 'covered' : row.status === coverageStatus.value)) && matches(row.component_name, row.component_version, row.supplier_name, row.product_name, row.release_version),
).sort((a, b) => sortOrder.value === 'name' ? a.component_name.localeCompare(b.component_name) : sortOrder.value === 'newest' ? (b.component_support_end_date || '').localeCompare(a.component_support_end_date || '') : (severityRank[a.severity] ?? 4) - (severityRank[b.severity] ?? 4) || (a.days_until_eos ?? Infinity) - (b.days_until_eos ?? Infinity)));
const resultCount = computed(() => section.value === 'queue' ? filteredAlerts.value.length : section.value === 'products' ? filteredProducts.value.length : filteredComponents.value.length);
const pageCount = computed(() => Math.max(1, Math.ceil(resultCount.value / pageSize)));
const pageAlerts = computed(() => filteredAlerts.value.slice((page.value - 1) * pageSize, page.value * pageSize));
const pageProducts = computed(() => filteredProducts.value.slice((page.value - 1) * pageSize, page.value * pageSize));
const pageComponents = computed(() => filteredComponents.value.slice((page.value - 1) * pageSize, page.value * pageSize));
watch([section, search, queueStatus, notificationType, supportWindow, customDays, classification, coverageStatus, sortOrder], () => { page.value = 1; });
watch(pageCount, count => { page.value = Math.min(page.value, count); });
watch(section, () => { search.value = ''; sortOrder.value = 'attention'; });
function resetFilters(): void {
  search.value = ''; queueStatus.value = 'all'; notificationType.value = ''; supportWindow.value = 'all'; classification.value = ''; coverageStatus.value = 'all'; sortOrder.value = 'attention'; page.value = 1;
}
function showPending(): void { resetFilters(); section.value = 'queue'; queueStatus.value = 'pending'; }
function showSupport(window: string): void { resetFilters(); section.value = 'products'; supportWindow.value = window; }
function showCoverage(): void { resetFilters(); section.value = 'components'; coverageStatus.value = 'attention'; }
async function loadSection(target: Section): Promise<void> {
  loading[target] = true; errors[target] = '';
  try {
    if (target === 'queue') alerts.value = await lifecycleNotificationService.list();
    else if (target === 'products' && canReadSupport.value) {
      const [loadedProducts, records, releases] = await Promise.all([
        productService.list(),
        supportPeriodService.list({ active_only: true }),
        auth.hasPermission('release_read') ? productReleaseService.list() : Promise.resolve([]),
      ]);
      products.value = loadedProducts; supportRecords.value = records;
      releaseLabels.value = Object.fromEntries(releases.map(release => [release.id, release.display_version]));
    } else if (target === 'components' && canReadComponents.value) components.value = await supplierAssessmentService.componentSupport();
  } catch { errors[target] = 'The data could not be retrieved. Check your connection and access permissions, then try again.'; }
  finally { loading[target] = false; }
}
async function refresh(): Promise<void> {
  if (isRefreshing.value) return;
  isRefreshing.value = true; today.value = new Date().toISOString().slice(0, 10);
  try { await Promise.all([loadSection('queue'), loadSection('products'), loadSection('components')]); }
  finally { isRefreshing.value = false; }
}
async function runScheduler(): Promise<void> {
  if (!canWrite.value || isRunningScheduler.value) return;
  isRunningScheduler.value = true; actionError.value = ''; successMessage.value = '';
  try {
    const created = await lifecycleNotificationService.scheduleEosCheck();
    successMessage.value = `Support check complete. ${created.length} new ${created.length === 1 ? 'notification' : 'notifications'} created across configured recipients. Your queue shows notifications available to you.`;
    await refresh();
  } catch { actionError.value = 'The support check failed. Please try again.'; }
  finally { isRunningScheduler.value = false; }
}
const resultsHeading = ref<HTMLElement | null>(null);
const actionDialog = ref<HTMLDialogElement | null>(null);
const selectedAction = ref<{ alert: LifecycleNotificationRead; status: 'sent' | 'dismissed' } | null>(null);
const actioningId = ref('');
const dialogError = ref('');
async function openAction(alert: LifecycleNotificationRead, status: 'sent' | 'dismissed'): Promise<void> {
  if (!canWrite.value || actioningId.value) return;
  selectedAction.value = { alert, status }; dialogError.value = '';
  await nextTick(); actionDialog.value?.showModal();
}
function preventBusyClose(event: Event): void { if (actioningId.value) event.preventDefault(); }
async function confirmAction(): Promise<void> {
  if (!selectedAction.value || !canWrite.value || actioningId.value) return;
  const { alert, status } = selectedAction.value;
  actioningId.value = alert.id; dialogError.value = ''; successMessage.value = ''; actionError.value = '';
  try {
    const updated = status === 'sent' ? await lifecycleNotificationService.markSent(alert.id) : await lifecycleNotificationService.dismiss(alert.id);
    alerts.value = alerts.value.map(item => item.id === updated.id ? updated : item);
    successMessage.value = `“${alert.title}” ${status === 'sent' ? 'recorded as sent' : 'dismissed'}.`;
    actionDialog.value?.close();
    await nextTick(); resultsHeading.value?.focus();
  } catch { dialogError.value = 'Could not confirm this change was saved. Close this dialog and refresh the queue to check its status before retrying.'; }
  finally { actioningId.value = ''; }
}
function revealGuideSection(event: Event): void {
  const target = (event as CustomEvent<string>).detail;
  if (target === '[data-guide="lifecycle-filters"]') section.value = 'queue';
  else {
    const item = sections.value.find(item => target === `[data-guide="lifecycle-${item.id}"]`);
    if (item) section.value = item.id;
  }
}
onMounted(() => {
  window.addEventListener('crane-guide-reveal', revealGuideSection);
  void refresh();
});
onBeforeUnmount(() => window.removeEventListener('crane-guide-reveal', revealGuideSection));
</script>

<style scoped>
.page-heading { flex: 1 1 20rem; min-width: 0; }
.lifecycle-page { display: grid; gap: 1rem; min-width: 0; }
.section-header, .row-actions, .alert-heading, .alert-footer, .pagination, .dialog-actions { display: flex; align-items: center; justify-content: space-between; gap: .75rem; flex-wrap: wrap; }
.page-actions { display: flex; align-items: flex-end; gap: .75rem; flex-wrap: wrap; width: 100%; }
.page-subtitle { margin-top: .35rem; }
.row-actions { justify-content: flex-start; }
h1, h2, h3, p { margin: 0; }
h2 { font-size: var(--text-lg); } h3 { font-size: var(--text-base); }
.section-header p { margin-top: .4rem; max-width: 75ch; line-height: 1.55; }
.muted { color: var(--color-text-muted); } .small-text { font-size: var(--text-xs); line-height: 1.6; }
.summary-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(190px, 1fr)); gap: .85rem; }
.summary-card { display: grid; gap: .4rem; padding: 1.1rem; text-align: left; border: 1px solid var(--color-border); border-radius: var(--radius-lg, 12px); background: var(--color-surface); color: var(--color-text); font: inherit; cursor: pointer; }
.summary-card:hover { border-color: var(--color-primary); background: var(--color-surface-elevated); } .summary-card:disabled { cursor: default; opacity: .65; }
.summary-card span { font-size: var(--text-sm); font-weight: 600; } .summary-card strong { font-size: 2rem; line-height: 1.2; font-variant-numeric: tabular-nums; } .summary-card small { color: var(--color-text-muted); }
.danger strong { color: var(--color-danger-text); } .warning strong { color: var(--color-warning-text); }
.workspace { padding: 0; min-width: 0; overflow: hidden; }
.section-nav { display: flex; flex-wrap: wrap; gap: .25rem; padding: .5rem 1rem 0; border-bottom: 1px solid var(--color-border); }
.section-nav button { padding: .85rem .9rem; border: 0; border-bottom: 3px solid transparent; background: transparent; font: inherit; font-size: var(--text-sm); font-weight: 600; color: var(--color-text-muted); cursor: pointer; }
.section-nav button[aria-current] { border-bottom-color: var(--color-primary); color: var(--color-text); background: var(--color-surface-elevated); }
.workspace-body { display: grid; gap: 1.25rem; padding: 1.25rem; min-width: 0; } .result-count { color: var(--color-text-muted); font-size: var(--text-xs); }
.filters { display: flex; flex-wrap: wrap; gap: .85rem; align-items: flex-end; padding: 1rem; background: var(--color-surface-elevated); border: 1px solid var(--color-border); border-radius: var(--radius-md, 8px); }
.filters label { display: grid; gap: .4rem; min-width: 160px; flex: 1; font-size: var(--text-xs); font-weight: 600; } .filters .search-field { flex: 2; min-width: 220px; }
input, select { width: 100%; min-width: 0; box-sizing: border-box; min-height: 40px; padding: .55rem .65rem; color: var(--color-text); background: var(--color-surface); border: 1px solid var(--color-border); border-radius: 6px; font: inherit; font-size: var(--text-sm); }
button:focus-visible, input:focus-visible, select:focus-visible, a:focus-visible, .table-wrapper:focus-visible { outline: 2px solid var(--color-primary); outline-offset: 3px; }
.alert-list { display: grid; gap: .85rem; } .alert-card { display: grid; gap: .8rem; padding: 1.1rem; border: 1px solid var(--color-border); border-radius: var(--radius-md, 8px); background: var(--color-surface); min-width: 0; overflow-wrap: anywhere; }
.alert-heading { justify-content: flex-start; } .alert-date { margin-left: auto; } .alert-message { color: var(--color-text-muted); line-height: 1.6; white-space: pre-line; max-width: 100ch; }
.alert-footer { padding-top: .75rem; border-top: 1px solid var(--color-border); } .alert-context { display: flex; flex-wrap: wrap; gap: .4rem 1.25rem; }
.badge { display: inline-flex; padding: .2rem .55rem; border-radius: 5px; font-size: var(--text-xs); font-weight: 600; line-height: 1.5; }
.badge-neutral { color: var(--color-text-muted); background: var(--color-surface-elevated); border: 1px solid var(--color-border); }
.badge-warning { color: var(--color-warning-text); background: var(--color-warning-bg); border: 1px solid var(--color-warning-border); }
.badge-danger { color: var(--color-danger-text); background: var(--color-danger-bg); border: 1px solid var(--color-danger-border); }
.badge-success { color: var(--color-success-text); background: var(--color-success-bg); border: 1px solid var(--color-success-border); }
.table-wrapper { overflow-x: auto; max-width: 100%; } table { width: 100%; border-collapse: collapse; font-size: var(--text-sm); }
th, td { padding: .9rem .75rem; text-align: left; border-bottom: 1px solid var(--color-border); vertical-align: top; min-width: 130px; }
th { font-size: var(--text-xs); color: var(--color-text-muted); font-weight: 600; background: var(--color-surface-elevated); } td:first-child { min-width: 200px; } td p { margin-top: .35rem; }
td .next-step { min-width: 180px; max-width: 30ch; margin: 0 0 .5rem; color: var(--color-text-muted); } a { color: var(--color-primary); text-underline-offset: 3px; }
.pagination { border-top: 1px solid var(--color-border); padding-top: 1rem; } .empty-state { display: grid; justify-items: center; gap: .8rem; padding: 2.5rem 1rem; text-align: center; } .empty-state p { max-width: 65ch; line-height: 1.6; }
.feedback { border-radius: 8px; padding: .85rem 1rem; line-height: 1.6; } .feedback-error { color: var(--color-danger-text); background: var(--color-danger-bg); } .feedback-success { color: var(--color-success-text); background: var(--color-success-bg); }
.action-dialog { max-width: 520px; width: calc(100% - 2rem); box-sizing: border-box; max-height: 85vh; overflow-y: auto; padding: 1.5rem; color: var(--color-text); background: var(--color-surface); border: 1px solid var(--color-border); border-radius: 12px; }
.action-dialog::backdrop { background: rgba(0, 0, 0, .6); } .action-dialog p { margin-top: 1rem; line-height: 1.6; overflow-wrap: anywhere; } .dialog-actions { margin-top: 1.5rem; justify-content: flex-end; }
.sr-only { position: absolute; width: 1px; height: 1px; padding: 0; overflow: hidden; clip: rect(0, 0, 0, 0); white-space: nowrap; }
@media (max-width: 640px) {
  .summary-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); } .summary-card { padding: .85rem; } .workspace-body { padding: .85rem; }
  .section-nav { padding-inline: .4rem; } .section-nav button { flex: 1; padding: .75rem .5rem; }
  .filters label, .filters .search-field { flex-basis: 100%; min-width: 0; } .alert-date { margin-left: 0; }
}
</style>
