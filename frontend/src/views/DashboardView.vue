<template>
  <section class="page dashboard-page">
    <div class="page-header">
      <div>
        <h1 class="page-title">Dashboard</h1>
        <p class="muted dashboard-subtitle">CRA compliance pulse across products, lifecycle, releases, and recent activity.</p>
      </div>

      <div class="dashboard-actions">
        <RouterLink class="button secondary" :to="{ name: 'products' }">
          Product inventory
        </RouterLink>
        <RouterLink
          v-if="canViewAudit"
          class="button secondary"
          :to="{ name: 'audit-history' }"
        >
          Audit history
        </RouterLink>
      </div>
    </div>

    <div v-if="errorMessage" class="card feedback feedback-error">
      {{ errorMessage }}
    </div>

    <section class="grid metrics-grid">
      <article class="card metric-card metric-card-primary">
        <span class="metric-label">Products</span>
        <strong class="metric-value">{{ totalProducts }}</strong>
        <span class="metric-foot">Total portfolio</span>
      </article>

      <article class="card metric-card">
        <span class="metric-label">In-Scope Products</span>
        <strong class="metric-value">{{ inScopeProducts }}</strong>
        <span class="metric-foot">{{ scopeCoverage }}% coverage</span>
      </article>

      <article class="card metric-card">
        <span class="metric-label">Released Products</span>
        <strong class="metric-value">{{ releasedProducts }}</strong>
        <span class="metric-foot">{{ releasedCoverage }}% released</span>
      </article>
    </section>

    <section class="grid highlights-grid">
      <article class="card spotlight-card">
        <div class="spotlight-header">
          <div>
            <span class="metric-label">End of Support Alert</span>
            <strong class="spotlight-value">{{ eosAlertCount }}</strong>
          </div>
          <div class="spotlight-orb spotlight-orb-danger" />
        </div>

        <div v-if="eosAlerts.length === 0" class="empty-state-inline">
          No current alerts
        </div>

        <div v-else class="compact-list">
          <RouterLink
            v-for="item in eosAlerts.slice(0, 4)"
            :key="item.id"
            class="compact-list-item"
            :to="{ name: 'product-detail', params: { productId: item.id } }"
          >
            <span>{{ item.name }}</span>
            <small>{{ item.days }}d</small>
          </RouterLink>
        </div>
      </article>

      <article class="card spotlight-card">
        <div class="spotlight-header">
          <div>
            <span class="metric-label">Security Update Availability</span>
            <strong class="spotlight-value">{{ securityAvailabilityPercent }}%</strong>
          </div>
          <div class="spotlight-orb spotlight-orb-success" />
        </div>

        <div class="availability-track">
          <span class="availability-fill" :style="{ width: `${securityAvailabilityPercent}%` }" />
        </div>

        <div class="availability-meta">
          <span>{{ productsWithSecurityUpdates }} covered</span>
          <span>{{ productsWithoutSecurityUpdates }} uncovered</span>
        </div>
      </article>
    </section>

    <section class="card activity-card">
      <div class="section-header">
        <div>
          <h2 class="section-title">Recent Activities</h2>
          <p class="muted">Latest regulated actions</p>
        </div>
        <span class="activity-count">{{ recentActivities.length }}</span>
      </div>

      <div v-if="recentActivities.length === 0" class="empty-state-inline">
        No recent activities
      </div>

      <div v-else class="activity-list">
        <article
          v-for="event in recentActivities"
          :key="event.id"
          class="activity-row"
        >
          <span class="activity-dot" />
          <div class="activity-copy">
            <strong>{{ event.summary }}</strong>
            <small class="muted">{{ formatDateTime(event.occurred_at) }}</small>
          </div>
        </article>
      </div>
    </section>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { RouterLink } from "vue-router";

import { auditService } from "@/services/audit-service";
import { productReleaseService } from "@/services/product-release-service";
import { productService } from "@/services/product-service";
import { securityUpdateService } from "@/services/security-update-service";
import { supportPeriodService } from "@/services/support-period-service";
import { useAuthStore } from "@/stores/auth";
import type { AuditEventRead } from "@/types/audit";
import type { ProductSummaryRead, SecurityUpdateRead, SupportPeriodRecordRead } from "@/types/product";
import type { ProductReleaseRead } from "@/types/release-gate";

const authStore = useAuthStore();

const errorMessage = ref("");

const products = ref<ProductSummaryRead[]>([]);
const releases = ref<ProductReleaseRead[]>([]);
const supportPeriods = ref<SupportPeriodRecordRead[]>([]);
const securityUpdates = ref<SecurityUpdateRead[]>([]);
const recentActivities = ref<AuditEventRead[]>([]);

const canViewProducts = computed(() => authStore.hasPermission("product_read"));
const canViewReleases = computed(() => authStore.hasPermission("release_read"));
const canViewSupport = computed(() => authStore.hasPermission("support_period_read"));
const canViewSecurity = computed(() => authStore.hasPermission("security_update_read"));
const canViewAudit = computed(() => authStore.hasPermission("audit_read"));

const totalProducts = computed(() => products.value.length);
const inScopeProducts = computed(() =>
  products.value.filter((product) => product.scope_status === "in_scope").length,
);

const releasedProducts = computed(() => {
  const releasedProductIds = new Set(
    releases.value
      .filter((release) => release.release_status === "released")
      .map((release) => release.product_id),
  );
  return releasedProductIds.size;
});

const scopeCoverage = computed(() => {
  if (totalProducts.value === 0) {
    return 0;
  }
  return Math.round((inScopeProducts.value / totalProducts.value) * 100);
});

const releasedCoverage = computed(() => {
  if (totalProducts.value === 0) {
    return 0;
  }
  return Math.round((releasedProducts.value / totalProducts.value) * 100);
});

const eosAlerts = computed(() => {
  const now = new Date();
  const byProduct = new Map(products.value.map((product) => [product.id, product]));

  return supportPeriods.value
    .map((record) => {
      const product = byProduct.get(record.product_id);
      if (!product) {
        return null;
      }

      const endDate = new Date(`${record.support_end_date}T00:00:00`);
      const days = Math.ceil((endDate.getTime() - now.getTime()) / (1000 * 60 * 60 * 24));

      if (days < 0 || days > 180) {
        return null;
      }

      return {
        id: product.id,
        name: product.name,
        days,
      };
    })
    .filter((item): item is { id: string; name: string; days: number } => item !== null)
    .sort((a, b) => a.days - b.days);
});

const eosAlertCount = computed(() => eosAlerts.value.length);

const productsWithSecurityUpdates = computed(() => {
  const productIdByReleaseId = new Map(releases.value.map((release) => [release.id, release.product_id]));
  return new Set(
    securityUpdates.value
      .map((update) => productIdByReleaseId.get(update.product_release_id))
      .filter((value): value is string => Boolean(value)),
  ).size;
});

const productsWithoutSecurityUpdates = computed(() =>
  Math.max(totalProducts.value - productsWithSecurityUpdates.value, 0),
);

const securityAvailabilityPercent = computed(() => {
  if (totalProducts.value === 0) {
    return 0;
  }
  return Math.round((productsWithSecurityUpdates.value / totalProducts.value) * 100);
});

async function loadDashboard(): Promise<void> {
  errorMessage.value = "";

  try {
    const tasks: Promise<unknown>[] = [];

    if (canViewProducts.value) {
      tasks.push(productService.list().then((data) => { products.value = data; }));
    }

    if (canViewReleases.value) {
      tasks.push(productReleaseService.list().then((data) => { releases.value = data; }));
    }

    if (canViewSupport.value) {
      tasks.push(
        supportPeriodService.list({ active_only: true }).then((data) => { supportPeriods.value = data; }),
      );
    }

    if (canViewSecurity.value) {
      tasks.push(securityUpdateService.list().then((data) => { securityUpdates.value = data; }));
    }

    if (canViewAudit.value) {
      tasks.push(
        auditService.listEvents({ limit: 6 }).then((data) => {
          recentActivities.value = data.items;
        }),
      );
    }

    await Promise.all(tasks);
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : "Failed to load dashboard.";
  }
}

function formatDateTime(value: string): string {
  return new Intl.DateTimeFormat(undefined, {
    month: "short",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  }).format(new Date(value));
}

onMounted(() => {
  void loadDashboard();
});
</script>

<style scoped>
.dashboard-page {
  gap: 1rem;
}

.dashboard-subtitle {
  margin: 0.25rem 0 0;
}

.dashboard-actions {
  display: flex;
  gap: 0.75rem;
  flex-wrap: wrap;
}

.feedback {
  padding: 0.9rem 1rem;
}

.feedback-error {
  border: 1px solid rgba(251, 113, 133, 0.28);
  background: rgba(251, 113, 133, 0.12);
  color: #fecdd3;
}

.metrics-grid {
  grid-template-columns: repeat(3, minmax(0, 1fr));
}

.metric-card {
  min-height: 180px;
  display: grid;
  align-content: space-between;
  position: relative;
  overflow: hidden;
}

.metric-card::after {
  content: "";
  position: absolute;
  right: -28px;
  bottom: -28px;
  width: 120px;
  height: 120px;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.04);
}

.metric-card-primary {
  background:
    radial-gradient(circle at top right, rgba(110, 168, 254, 0.18), transparent 34%),
    linear-gradient(145deg, rgba(18, 36, 64, 0.92), rgba(12, 22, 41, 0.88));
}

.metric-label {
  font-size: 0.84rem;
  color: var(--color-text-muted);
}

.metric-value {
  font-size: clamp(2.9rem, 6vw, 4.1rem);
  line-height: 0.95;
}

.metric-foot {
  color: var(--color-text-muted);
  font-size: 0.88rem;
}

.highlights-grid {
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

.spotlight-card {
  min-height: 230px;
  display: grid;
  gap: 1rem;
}

.spotlight-header,
.availability-meta,
.section-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 1rem;
  flex-wrap: wrap;
}

.spotlight-value {
  display: block;
  margin-top: 0.35rem;
  font-size: 2.8rem;
  line-height: 0.95;
}

.spotlight-orb {
  width: 44px;
  height: 44px;
  border-radius: 50%;
  box-shadow: 0 0 0 10px rgba(255, 255, 255, 0.03);
}

.spotlight-orb-danger {
  background: linear-gradient(180deg, rgba(251, 113, 133, 0.92), rgba(244, 63, 94, 0.55));
}

.spotlight-orb-success {
  background: linear-gradient(180deg, rgba(52, 211, 153, 0.92), rgba(16, 185, 129, 0.55));
}

.compact-list,
.activity-list {
  display: grid;
  gap: 0.75rem;
}

.compact-list-item,
.activity-row {
  border-radius: 14px;
  border: 1px solid rgba(233, 238, 252, 0.08);
  background: rgba(255, 255, 255, 0.03);
}

.compact-list-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 0.75rem;
  padding: 0.85rem 0.95rem;
}

.compact-list-item small {
  color: var(--color-warning);
  font-weight: 700;
}

.availability-track {
  width: 100%;
  height: 14px;
  border-radius: 999px;
  overflow: hidden;
  background: rgba(255, 255, 255, 0.06);
}

.availability-fill {
  display: block;
  height: 100%;
  border-radius: inherit;
  background: linear-gradient(90deg, rgba(52, 211, 153, 0.95), rgba(110, 168, 254, 0.95));
}

.availability-meta {
  color: var(--color-text-muted);
  font-size: 0.88rem;
}

.activity-card {
  display: grid;
  gap: 1rem;
}

.activity-count {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 42px;
  height: 42px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.06);
  border: 1px solid rgba(233, 238, 252, 0.12);
}

.activity-row {
  display: grid;
  grid-template-columns: 12px minmax(0, 1fr);
  align-items: start;
  gap: 0.8rem;
  padding: 0.9rem 1rem;
}

.activity-dot {
  width: 12px;
  height: 12px;
  border-radius: 50%;
  margin-top: 0.18rem;
  background: linear-gradient(180deg, var(--color-success), var(--color-primary));
  box-shadow: 0 0 0 6px rgba(110, 168, 254, 0.08);
}

.activity-copy {
  display: grid;
  gap: 0.2rem;
}

.empty-state-inline {
  min-height: 108px;
  display: grid;
  place-items: center;
  color: var(--color-text-muted);
  border-radius: 14px;
  border: 1px dashed rgba(233, 238, 252, 0.12);
  background: rgba(255, 255, 255, 0.03);
}

@media (max-width: 1040px) {
  .metrics-grid,
  .highlights-grid {
    grid-template-columns: 1fr;
  }
}
</style>
