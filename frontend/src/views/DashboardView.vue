<template>
  <section class="page dashboard-page">

    <!-- ── Page header ─────────────────────────────── -->
    <div class="page-header">
      <div class="page-header-info">
        <div class="page-eyebrow">
          <span class="eyebrow-chip">CRANE — CRA Norm Engine</span>
          <span class="live-indicator" aria-label="Live data">
            <span class="live-dot" />
            Live
          </span>
        </div>
        <h1 class="page-title">Dashboard</h1>
        <p class="muted dashboard-subtitle">Compliance pulse across products, lifecycle, releases, and recent activity.</p>
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

    <!-- ── Hero banner — logo + tagline ──────────────── -->
    <section class="hero-banner" aria-label="CRANE branding">
      <div class="hero-glow" aria-hidden="true" />
      <img src="/logo/darkText.svg"  alt="CRANE — CRA Norm Engine" class="hero-logo logo-dark"  />
      <img src="/logo/lightText.svg" alt="CRANE — CRA Norm Engine" class="hero-logo logo-light" />
      <div class="hero-copy">
        <h2 class="hero-title">CRA Compliance, End-to-End</h2>
        <p class="hero-tagline muted">
          CRANE guides your team through every obligation of the EU Cyber Resilience Act —
          from product scoping and classification to security updates, lifecycle management, and conformity.
        </p>
      </div>
    </section>

    <!-- ── CRA key-requirement cards ─────────────────── -->
    <section aria-labelledby="cra-overview-heading">
      <div class="cra-section-header">
        <h2 id="cra-overview-heading" class="section-title">CRA Compliance Areas</h2>
        <p class="muted cra-section-sub">Six pillars of the Cyber Resilience Act — explore each in the tool.</p>
      </div>

      <div class="cra-cards-grid">

        <!-- Card 1 — Product inventory & scope -->
        <article class="card cra-card">
          <div class="cra-card-icon cra-icon-blue" aria-hidden="true">
            <!-- Box / package icon -->
            <svg viewBox="0 0 20 20" fill="currentColor"><path d="M4 5.5 10 3l6 2.5v9L10 17l-6-2.5zm6 .2L6.2 7.2 10 8.8l3.8-1.6zM5.5 8.4v5l3.8 1.6v-5zm9 0-3.8 1.6v5l3.8-1.6z"/></svg>
          </div>
          <span class="cra-article-badge">Art. 2 · Annex III</span>
          <h3 class="cra-card-title">Product Inventory &amp; Scope</h3>
          <p class="cra-card-desc">
            Determine which products fall under CRA scope and assign the correct classification —
            normal, Important Class I or II, or Critical. Scope and classification drive every
            subsequent compliance obligation.
          </p>
          <RouterLink class="button primary cra-explore-btn" :to="{ name: 'products' }">
            Explore products
          </RouterLink>
        </article>

        <!-- Card 2 — Annex I cybersecurity requirements -->
        <article class="card cra-card">
          <div class="cra-card-icon cra-icon-purple" aria-hidden="true">
            <!-- Table / matrix icon -->
            <svg viewBox="0 0 20 20" fill="currentColor"><path d="M3 4h14v12H3zm2 2v2h10V6zm0 4v4h3v-4zm5 0v4h5v-4z"/></svg>
          </div>
          <span class="cra-article-badge">Annex I</span>
          <h3 class="cra-card-title">Cybersecurity Requirements</h3>
          <p class="cra-card-desc">
            CRA Annex I defines essential security requirements for product design, development,
            and post-market phases. Track your compliance against each requirement and map
            evidence across your product portfolio.
          </p>
          <RouterLink
            v-if="canViewAnnexMatrix"
            class="button primary cra-explore-btn"
            :to="{ name: 'annex-matrix' }"
          >
            Explore Annex I matrix
          </RouterLink>
          <span v-else class="cra-permission-note">Requires Annex matrix permission</span>
        </article>

        <!-- Card 3 — Security updates & vulnerability handling -->
        <article class="card cra-card">
          <div class="cra-card-icon cra-icon-green" aria-hidden="true">
            <!-- Shield icon -->
            <svg viewBox="0 0 20 20" fill="currentColor"><path d="M10 2 4 5v4c0 4.1 2.4 7.8 6 9 3.6-1.2 6-4.9 6-9V5zm0 3.2a2.3 2.3 0 0 1 1.3 4.2v2.9H8.7V9.4A2.3 2.3 0 0 1 10 5.2z"/></svg>
          </div>
          <span class="cra-article-badge">Art. 13(3) · Art. 14</span>
          <h3 class="cra-card-title">Security Updates &amp; Reporting</h3>
          <p class="cra-card-desc">
            Security vulnerabilities must be remediated and updates delivered without undue delay.
            Actively exploited vulnerabilities must be reported to ENISA within 24 hours of
            discovery (Art. 14).
          </p>
          <RouterLink
            v-if="canViewSecurityUpdates"
            class="button primary cra-explore-btn"
            :to="{ name: 'security-updates' }"
          >
            Explore security updates
          </RouterLink>
          <span v-else class="cra-permission-note">Requires security update permission</span>
        </article>

        <!-- Card 4 — Support period & lifecycle -->
        <article class="card cra-card">
          <div class="cra-card-icon cra-icon-amber" aria-hidden="true">
            <!-- Clock icon -->
            <svg viewBox="0 0 20 20" fill="currentColor"><path d="M10 2a8 8 0 1 0 0 16A8 8 0 0 0 10 2zm0 2a6 6 0 1 1 0 12A6 6 0 0 1 10 4zm-1 3v4.4l3.2 1.9.8-1.4L10.5 10.5V7z"/></svg>
          </div>
          <span class="cra-article-badge">Art. 13(8)</span>
          <h3 class="cra-card-title">Support Period &amp; Lifecycle</h3>
          <p class="cra-card-desc">
            Manufacturers must commit to a support period commensurate with the product's expected
            use time — at least 5 years for most products. End-of-support dates must be communicated
            clearly to users.
          </p>
          <RouterLink class="button primary cra-explore-btn" :to="{ name: 'products' }">
            Explore product lifecycle
          </RouterLink>
        </article>

        <!-- Card 5 — Risk assessments -->
        <article class="card cra-card">
          <div class="cra-card-icon cra-icon-red" aria-hidden="true">
            <!-- Warning triangle icon -->
            <svg viewBox="0 0 20 20" fill="currentColor"><path d="M10 2 2 16h16zm0 4.4 4.5 7.6h-9zM9 8h2v3H9zm0 4h2v2H9z"/></svg>
          </div>
          <span class="cra-article-badge">Art. 13(2) · Annex II</span>
          <h3 class="cra-card-title">Risk Assessments</h3>
          <p class="cra-card-desc">
            A cybersecurity risk assessment is mandatory throughout the product lifecycle.
            CRA Annex II requires manufacturers to document and address all foreseeable risks
            associated with intended and reasonably foreseeable use.
          </p>
          <RouterLink
            v-if="canViewRiskAssessments"
            class="button primary cra-explore-btn"
            :to="{ name: 'risk-assessments' }"
          >
            Explore risk assessments
          </RouterLink>
          <span v-else class="cra-permission-note">Requires risk assessment permission</span>
        </article>

        <!-- Card 6 — Substantial changes & conformity -->
        <article class="card cra-card">
          <div class="cra-card-icon cra-icon-teal" aria-hidden="true">
            <!-- Edit / changes icon -->
            <svg viewBox="0 0 20 20" fill="currentColor"><path d="M3 5h14v2H3zm0 4h9v2H3zm0 4h6v2H3zm11-1 1.5-1.5L17 8l-4 4v3h3v-4z"/></svg>
          </div>
          <span class="cra-article-badge">Art. 3(4) · Art. 27–32</span>
          <h3 class="cra-card-title">Substantial Changes &amp; Conformity</h3>
          <p class="cra-card-desc">
            Modifications that affect a product's security posture may constitute a substantial change,
            requiring a new conformity assessment. Important Class II and Critical products must undergo
            third-party assessment before market placement.
          </p>
          <RouterLink
            v-if="canViewChanges"
            class="button primary cra-explore-btn"
            :to="{ name: 'changes' }"
          >
            Explore substantial changes
          </RouterLink>
          <span v-else class="cra-permission-note">Requires change management permission</span>
        </article>

      </div>
    </section>

    <!-- ── Overview: Compliance ring + 3 metric cards ── -->
    <section class="overview-row">

      <article class="card compliance-card">
        <div class="compliance-inner">
          <div class="ring-container">
            <svg class="ring-svg" viewBox="0 0 100 100" aria-hidden="true">
              <circle class="ring-track" cx="50" cy="50" r="42" stroke-width="7" />
              <circle
                class="ring-fill"
                cx="50" cy="50" r="42"
                stroke-width="7"
                stroke-linecap="round"
                :stroke-dasharray="`${(complianceScore / 100) * 263.9} 263.9`"
                :style="{ stroke: complianceScoreColor }"
              />
            </svg>
            <div class="ring-center">
              <strong class="ring-number">{{ complianceScore }}</strong>
              <span class="ring-pct">%</span>
            </div>
          </div>

          <div class="compliance-details">
            <span class="compliance-detail-label">Compliance Health</span>
            <span class="compliance-badge" :class="complianceScoreBadgeClass">
              {{ complianceScoreLabel }}
            </span>
            <p class="compliance-hint muted">Scope · Release · Security</p>
          </div>
        </div>
      </article>

      <div class="metrics-grid">
        <article class="card metric-card metric-card-primary">
          <span class="metric-label">Products</span>
          <strong class="metric-value">{{ totalProducts }}</strong>
          <span class="metric-foot">Total portfolio</span>
        </article>

        <article class="card metric-card">
          <span class="metric-label">In-Scope</span>
          <strong class="metric-value">{{ inScopeProducts }}</strong>
          <div class="metric-bar-wrap">
            <div class="metric-bar">
              <span class="metric-bar-fill metric-bar-indigo" :style="{ width: `${scopeCoverage}%` }" />
            </div>
            <span class="metric-foot">{{ scopeCoverage }}% coverage</span>
          </div>
        </article>

        <article class="card metric-card">
          <span class="metric-label">Released</span>
          <strong class="metric-value">{{ releasedProducts }}</strong>
          <div class="metric-bar-wrap">
            <div class="metric-bar">
              <span class="metric-bar-fill metric-bar-green" :style="{ width: `${releasedCoverage}%` }" />
            </div>
            <span class="metric-foot">{{ releasedCoverage }}% released</span>
          </div>
        </article>
      </div>
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
          <svg class="empty-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" aria-hidden="true">
            <path stroke-linecap="round" stroke-linejoin="round" d="M9 12.75L11.25 15 15 9.75M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          No current alerts
        </div>

        <div v-else class="compact-list">
          <RouterLink
            v-for="item in eosAlerts.slice(0, 4)"
            :key="item.id"
            class="compact-list-item"
            :to="{ name: 'product-detail', params: { productId: item.id } }"
          >
            <div class="eos-item-left">
              <span class="eos-dot" :class="eosUrgencyClass(item.days)" />
              <span>{{ item.name }}</span>
            </div>
            <span class="eos-badge" :class="eosUrgencyClass(item.days)">{{ item.days }}d</span>
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
          <div class="avail-stat">
            <span class="avail-dot avail-dot-on" />
            {{ productsWithSecurityUpdates }} covered
          </div>
          <div class="avail-stat">
            <span class="avail-dot avail-dot-off" />
            {{ productsWithoutSecurityUpdates }} uncovered
          </div>
        </div>
      </article>
    </section>

    <section class="card activity-card">
      <div class="section-header">
        <div>
          <h2 class="section-title">Recent Activities</h2>
          <p class="muted">Latest regulated actions and audit events</p>
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
const canViewAnnexMatrix = computed(
  () =>
    authStore.hasPermission("annex_requirement_read") ||
    authStore.hasPermission("requirement_mapping_read"),
);
const canViewRiskAssessments = computed(() => authStore.hasPermission("risk_assessment_read"));
const canViewChanges = computed(() => authStore.hasPermission("change_read"));
const canViewSecurityUpdates = computed(() => authStore.hasPermission("security_update_read"));

const totalProducts = computed(() => products.value.length);
const inScopeProducts = computed(() =>
  products.value.filter((product: ProductSummaryRead) => product.scope_status === "in_scope").length,
);

const releasedProducts = computed(() => {
  const releasedProductIds = new Set(
    releases.value
      .filter((release: ProductReleaseRead) => release.release_status === "released")
      .map((release: ProductReleaseRead) => release.product_id),
  );
  return releasedProductIds.size;
});

const scopeCoverage = computed(() => {
  if (totalProducts.value === 0) return 0;
  return Math.round((inScopeProducts.value / totalProducts.value) * 100);
});

const releasedCoverage = computed(() => {
  if (totalProducts.value === 0) return 0;
  return Math.round((releasedProducts.value / totalProducts.value) * 100);
});

const eosAlerts = computed(() => {
  const now = new Date();
  const byProduct = new Map(products.value.map((product: ProductSummaryRead) => [product.id, product]));

  return supportPeriods.value
    .map((record) => {
      const product = byProduct.get(record.product_id);
      if (!product) return null;
      const endDate = new Date(`${record.support_end_date}T00:00:00`);
      const days = Math.ceil((endDate.getTime() - now.getTime()) / (1000 * 60 * 60 * 24));
      if (days < 0 || days > 180) return null;
      return { id: product.id, name: product.name, days };
    })
    .filter((item): item is { id: string; name: string; days: number } => item !== null)
    .sort((a, b) => a.days - b.days);
});

const eosAlertCount = computed(() => eosAlerts.value.length);

const productsWithSecurityUpdates = computed(() => {
  const productIdByReleaseId = new Map(releases.value.map((release: ProductReleaseRead) => [release.id, release.product_id]));
  return new Set(
    securityUpdates.value
      .map((update: SecurityUpdateRead) => productIdByReleaseId.get(update.product_release_id))
      .filter((value): value is string => Boolean(value)),
  ).size;
});

const productsWithoutSecurityUpdates = computed(() =>
  Math.max(totalProducts.value - productsWithSecurityUpdates.value, 0),
);

const securityAvailabilityPercent = computed(() => {
  if (totalProducts.value === 0) return 0;
  return Math.round((productsWithSecurityUpdates.value / totalProducts.value) * 100);
});

const complianceScore = computed(() => {
  if (totalProducts.value === 0) return 0;
  const avg = (scopeCoverage.value + releasedCoverage.value + securityAvailabilityPercent.value) / 3;
  return Math.round(avg);
});

const complianceScoreColor = computed(() => {
  if (complianceScore.value >= 80) return "var(--color-success)";
  if (complianceScore.value >= 55) return "var(--color-warning)";
  return "var(--color-danger)";
});

const complianceScoreLabel = computed(() => {
  if (complianceScore.value >= 80) return "Healthy";
  if (complianceScore.value >= 55) return "Moderate";
  return "At Risk";
});

const complianceScoreBadgeClass = computed(() => ({
  "score-healthy": complianceScore.value >= 80,
  "score-moderate": complianceScore.value >= 55 && complianceScore.value < 80,
  "score-risk": complianceScore.value < 55,
}));

function eosUrgencyClass(days: number): string {
  if (days <= 30) return "eos-critical";
  if (days <= 90) return "eos-warning";
  return "eos-caution";
}

async function loadDashboard(): Promise<void> {
  errorMessage.value = "";
  try {
    const tasks: Promise<unknown>[] = [];
    if (canViewProducts.value) tasks.push(productService.list().then((d) => { products.value = d; }));
    if (canViewReleases.value) tasks.push(productReleaseService.list().then((d) => { releases.value = d; }));
    if (canViewSupport.value) tasks.push(supportPeriodService.list({ active_only: true }).then((d) => { supportPeriods.value = d; }));
    if (canViewSecurity.value) tasks.push(securityUpdateService.list().then((d) => { securityUpdates.value = d; }));
    if (canViewAudit.value) tasks.push(auditService.listEvents({ limit: 6 }).then((d) => { recentActivities.value = d.items; }));
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
  gap: 1.5rem;
}

/* ── Page header ─────────────────────────────── */
.dashboard-subtitle {
  margin: 0.25rem 0 0;
}

.page-eyebrow {
  display: flex;
  align-items: center;
  gap: 0.6rem;
  margin-bottom: 0.45rem;
}

.eyebrow-chip {
  font-size: 0.72rem;
  font-weight: 700;
  letter-spacing: 0.07em;
  text-transform: uppercase;
  padding: 0.22rem 0.65rem;
  border-radius: 999px;
  background: var(--color-success-bg);
  color: var(--color-success-text);
  border: 1px solid var(--color-success-border);
}

.live-indicator {
  display: flex;
  align-items: center;
  gap: 0.38rem;
  font-size: 0.72rem;
  font-weight: 700;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  color: var(--color-success);
}

.live-dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: var(--color-success);
  animation: pulse-live 2.4s ease-in-out infinite;
}

@keyframes pulse-live {
  0%, 100% { box-shadow: 0 0 0 0 rgba(127, 203, 45, 0); }
  50% { box-shadow: 0 0 0 5px rgba(127, 203, 45, 0.18); }
}

.dashboard-actions {
  display: flex;
  gap: 0.75rem;
  flex-wrap: wrap;
}

/* ── Error feedback ───────────────────────────── */
.feedback {
  padding: 0.9rem 1rem;
}

.feedback-error {
  border-color: rgba(251, 113, 133, 0.28);
  background: rgba(251, 113, 133, 0.1);
  color: #fecdd3;
}

/* ── Hero banner ──────────────────────────────── */
.hero-banner {
  position: relative;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 1.5rem;
  padding: 3rem 2rem 3.5rem;
  border-radius: var(--radius-xl, 20px);
  border: 1px solid rgba(112, 185, 23, 0.15);
  background:
    radial-gradient(ellipse 70% 55% at 50% 0%, rgba(112, 185, 23, 0.1), transparent),
    linear-gradient(175deg, rgba(18, 40, 18, 0.95), rgba(8, 16, 8, 0.92));
  overflow: hidden;
  text-align: center;
}

/* Decorative glow orb behind the logo */
.hero-glow {
  position: absolute;
  top: -60px;
  left: 50%;
  transform: translateX(-50%);
  width: 340px;
  height: 340px;
  border-radius: 50%;
  background: radial-gradient(circle, rgba(112, 185, 23, 0.14) 0%, transparent 70%);
  pointer-events: none;
}

.hero-logo {
  max-width: 260px;
  max-height: 120px;
  width: 100%;
  object-fit: contain;
  filter: drop-shadow(0 8px 32px rgba(112, 185, 23, 0.18));
  position: relative;
  z-index: 1;
}

/* Theme-aware logo swap */
.logo-light { display: none; }
:root[data-theme="light"] .logo-dark  { display: none; }
:root[data-theme="light"] .logo-light { display: block; }

.hero-copy {
  position: relative;
  z-index: 1;
  max-width: 560px;
}

.hero-title {
  margin: 0 0 0.6rem;
  font-size: clamp(1.45rem, 3vw, 1.9rem);
  font-weight: 800;
  line-height: 1.2;
  background: linear-gradient(135deg, #d4f0a0, #7cb922);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.hero-tagline {
  margin: 0;
  font-size: 0.97rem;
  line-height: 1.6;
}

/* ── CRA cards section ────────────────────────── */
.cra-section-header {
  display: flex;
  flex-direction: column;
  gap: 0.3rem;
  margin-bottom: 1.1rem;
}

.cra-section-sub {
  margin: 0;
  font-size: 0.9rem;
}

.cra-cards-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 1.1rem;
}

/* Individual CRA card */
.cra-card {
  display: flex;
  flex-direction: column;
  gap: 0.65rem;
  padding: 1.4rem;
}

/* Coloured icon container */
.cra-card-icon {
  width: 42px;
  height: 42px;
  border-radius: 11px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.cra-card-icon svg {
  width: 20px;
  height: 20px;
}

/* Icon colour variants */
.cra-icon-blue   { background: rgba(96, 165, 250, 0.12); color: #60a5fa; border: 1px solid rgba(96, 165, 250, 0.2); }
.cra-icon-purple { background: rgba(167, 139, 250, 0.12); color: #a78bfa; border: 1px solid rgba(167, 139, 250, 0.2); }
.cra-icon-green  { background: rgba(52, 211, 153, 0.12); color: #34d399; border: 1px solid rgba(52, 211, 153, 0.2); }
.cra-icon-amber  { background: rgba(251, 191, 36, 0.12); color: #fbbf24; border: 1px solid rgba(251, 191, 36, 0.2); }
.cra-icon-red    { background: rgba(251, 113, 133, 0.12); color: #fb7185; border: 1px solid rgba(251, 113, 133, 0.2); }
.cra-icon-teal   { background: rgba(45, 212, 191, 0.12); color: #2dd4bf; border: 1px solid rgba(45, 212, 191, 0.2); }

.cra-article-badge {
  font-size: 0.68rem;
  font-weight: 700;
  letter-spacing: 0.07em;
  text-transform: uppercase;
  padding: 0.2rem 0.6rem;
  border-radius: 999px;
  width: fit-content;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.1);
  color: var(--color-text-muted);
}

.cra-card-title {
  margin: 0;
  font-size: 1rem;
  font-weight: 700;
  line-height: 1.3;
}

.cra-card-desc {
  margin: 0;
  font-size: 0.875rem;
  line-height: 1.65;
  color: var(--color-text-muted);
  flex: 1; /* push the button to the bottom */
}

.cra-explore-btn {
  margin-top: auto;
  align-self: flex-start;
  font-size: 0.85rem;
  padding: 0.48rem 1rem;
}

.cra-permission-note {
  margin-top: auto;
  font-size: 0.78rem;
  color: var(--color-text-muted);
  font-style: italic;
}

/* ── Overview row ────────────────────────────── */
.overview-row {
  display: grid;
  grid-template-columns: 300px 1fr;
  gap: 1.25rem;
  align-items: start;
}

/* ── Compliance card ─────────────────────────── */
.compliance-card {
  padding: 1.5rem;
}

.compliance-inner {
  display: flex;
  align-items: center;
  gap: 1.4rem;
}

.ring-container {
  position: relative;
  width: 108px;
  height: 108px;
  flex-shrink: 0;
}

.ring-svg {
  width: 100%;
  height: 100%;
  transform: rotate(-90deg);
}

.ring-track {
  fill: none;
  stroke: rgba(255, 255, 255, 0.08);
}

.ring-fill {
  fill: none;
  transition: stroke-dasharray 0.8s cubic-bezier(0.4, 0, 0.2, 1);
}

.ring-center {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 1px;
}

.ring-number {
  font-size: 1.75rem;
  line-height: 1;
  font-weight: 800;
}

.ring-pct {
  font-size: 0.82rem;
  font-weight: 700;
  opacity: 0.65;
  align-self: flex-start;
  margin-top: 0.36rem;
}

.compliance-details {
  display: grid;
  gap: 0.55rem;
}

.compliance-detail-label {
  font-size: 0.82rem;
  color: var(--color-text-muted);
  font-weight: 600;
  letter-spacing: 0.03em;
}

.compliance-badge {
  display: inline-block;
  font-size: 0.76rem;
  font-weight: 700;
  letter-spacing: 0.07em;
  text-transform: uppercase;
  padding: 0.26rem 0.72rem;
  border-radius: 999px;
  width: fit-content;
}

.score-healthy {
  background: var(--color-success-bg);
  color: var(--color-success-text);
  border: 1px solid var(--color-success-border);
}

.score-moderate {
  background: rgba(223, 232, 95, 0.1);
  color: var(--color-warning);
  border: 1px solid rgba(223, 232, 95, 0.24);
}

.score-risk {
  background: var(--color-danger-bg);
  color: var(--color-danger-text);
  border: 1px solid var(--color-danger-border);
}

.compliance-hint {
  margin: 0;
  font-size: 0.8rem;
}

/* ── Metrics grid ────────────────────────────── */
.metrics-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 1.25rem;
}

.metric-card {
  min-height: 155px;
  display: grid;
  align-content: space-between;
  position: relative;
  overflow: hidden;
  padding: 1.25rem;
}

.metric-card::after {
  content: "";
  position: absolute;
  right: -30px;
  bottom: -30px;
  width: 110px;
  height: 110px;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.035);
  pointer-events: none;
}

.metric-card-primary {
  background:
    radial-gradient(circle at top right, rgba(112, 185, 23, 0.18), transparent 50%),
    linear-gradient(145deg, rgba(18, 36, 18, 0.94), rgba(10, 20, 10, 0.9));
}

.metric-label {
  font-size: 0.82rem;
  color: var(--color-text-muted);
  font-weight: 600;
  letter-spacing: 0.025em;
}

.metric-value {
  font-size: clamp(2.6rem, 5vw, 3.5rem);
  line-height: 0.92;
  font-weight: 800;
}

.metric-bar-wrap {
  display: grid;
  gap: 0.45rem;
}

.metric-bar {
  height: 4px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.08);
  overflow: hidden;
}

.metric-bar-fill {
  display: block;
  height: 100%;
  border-radius: inherit;
  transition: width 0.7s ease;
}

.metric-bar-indigo {
  background: linear-gradient(90deg, rgba(110, 168, 254, 0.9), rgba(139, 92, 246, 0.85));
}

.metric-bar-green {
  background: linear-gradient(90deg, rgba(52, 211, 153, 0.9), rgba(112, 185, 23, 0.9));
}

.metric-foot {
  font-size: 0.84rem;
  color: var(--color-text-muted);
}

/* ── Highlights grid ─────────────────────────── */
.highlights-grid {
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

.spotlight-card {
  min-height: 215px;
  display: grid;
  gap: 1rem;
  align-content: start;
  padding: 1.35rem;
}

.spotlight-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 1rem;
}

.spotlight-value {
  display: block;
  margin-top: 0.28rem;
  font-size: 2.6rem;
  font-weight: 800;
  line-height: 0.92;
}

.spotlight-orb {
  width: 42px;
  height: 42px;
  border-radius: 50%;
  flex-shrink: 0;
}

.spotlight-orb-danger {
  background: linear-gradient(160deg, rgba(251, 113, 133, 0.95), rgba(244, 63, 94, 0.55));
  box-shadow: 0 0 0 8px rgba(251, 113, 133, 0.08), 0 0 22px rgba(244, 63, 94, 0.16);
}

.spotlight-orb-success {
  background: linear-gradient(160deg, rgba(52, 211, 153, 0.95), rgba(16, 185, 129, 0.55));
  box-shadow: 0 0 0 8px rgba(52, 211, 153, 0.08), 0 0 22px rgba(16, 185, 129, 0.16);
}

/* ── EOS compact list ────────────────────────── */
.compact-list {
  display: grid;
  gap: 0.5rem;
}

.compact-list-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 0.75rem;
  padding: 0.72rem 0.9rem;
  border-radius: 12px;
  border: 1px solid rgba(233, 238, 252, 0.07);
  background: rgba(255, 255, 255, 0.025);
  transition: background 0.14s ease, border-color 0.14s ease;
}

.compact-list-item:hover {
  background: rgba(255, 255, 255, 0.05);
  border-color: rgba(233, 238, 252, 0.13);
}

.eos-item-left {
  display: flex;
  align-items: center;
  gap: 0.55rem;
  min-width: 0;
}

.eos-item-left span:last-child {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.eos-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  flex-shrink: 0;
}

.eos-dot.eos-critical { background: var(--color-danger); }
.eos-dot.eos-warning { background: var(--color-warning); }
.eos-dot.eos-caution { background: var(--color-primary-2); }

.eos-badge {
  font-size: 0.76rem;
  font-weight: 700;
  padding: 0.2rem 0.55rem;
  border-radius: 999px;
  white-space: nowrap;
  flex-shrink: 0;
}

.eos-badge.eos-critical {
  background: var(--color-danger-bg);
  color: var(--color-danger-text);
  border: 1px solid var(--color-danger-border);
}

.eos-badge.eos-warning {
  background: rgba(223, 232, 95, 0.1);
  color: var(--color-warning);
  border: 1px solid rgba(223, 232, 95, 0.22);
}

.eos-badge.eos-caution {
  background: var(--color-success-bg);
  color: var(--color-success-text);
  border: 1px solid var(--color-success-border);
}

/* ── Security availability ───────────────────── */
.availability-track {
  width: 100%;
  height: 10px;
  border-radius: 999px;
  overflow: hidden;
  background: rgba(255, 255, 255, 0.07);
}

.availability-fill {
  display: block;
  height: 100%;
  border-radius: inherit;
  background: linear-gradient(90deg, rgba(52, 211, 153, 0.95), rgba(112, 185, 23, 0.9));
  transition: width 0.8s ease;
}

.availability-meta {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 0.84rem;
  color: var(--color-text-muted);
}

.avail-stat {
  display: flex;
  align-items: center;
  gap: 0.48rem;
}

.avail-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  flex-shrink: 0;
}

.avail-dot-on { background: var(--color-success); }
.avail-dot-off { background: rgba(255, 255, 255, 0.22); border: 1px solid rgba(255, 255, 255, 0.28); }

/* ── Activity section ────────────────────────── */
.activity-card {
  display: grid;
  gap: 1.25rem;
  padding: 1.35rem;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 1rem;
  flex-wrap: wrap;
}

.section-title {
  margin: 0;
  font-size: 1.15rem;
  font-weight: 700;
}

.activity-count {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 38px;
  height: 38px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(233, 238, 252, 0.1);
  font-weight: 700;
  font-size: 0.9rem;
}

.activity-list {
  display: grid;
  gap: 0.55rem;
}

.activity-row {
  display: grid;
  grid-template-columns: 10px minmax(0, 1fr);
  align-items: start;
  gap: 0.9rem;
  padding: 0.88rem 1rem;
  border-radius: 12px;
  border: 1px solid rgba(233, 238, 252, 0.07);
  background: rgba(255, 255, 255, 0.025);
  transition: background 0.14s ease;
}

.activity-row:hover {
  background: rgba(255, 255, 255, 0.045);
}

.activity-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  margin-top: 0.28rem;
  background: linear-gradient(180deg, var(--color-success), var(--color-primary));
  box-shadow: 0 0 0 4px rgba(112, 185, 23, 0.1);
  flex-shrink: 0;
}

.activity-copy {
  display: grid;
  gap: 0.18rem;
}

.activity-copy strong {
  font-size: 0.93rem;
  line-height: 1.45;
}

.activity-copy small {
  font-size: 0.8rem;
}

/* ── Empty states ────────────────────────────── */
.empty-state-inline {
  min-height: 88px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 0.55rem;
  color: var(--color-text-muted);
  font-size: 0.88rem;
  border-radius: 12px;
  border: 1px dashed rgba(233, 238, 252, 0.1);
  background: rgba(255, 255, 255, 0.018);
}

.empty-icon {
  width: 26px;
  height: 26px;
  opacity: 0.45;
}

/* ── Responsive ──────────────────────────────── */
@media (max-width: 1180px) {
  .cra-cards-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .overview-row {
    grid-template-columns: 1fr;
  }

  .compliance-card {
    max-width: 440px;
  }
}

@media (max-width: 1040px) {
  .metrics-grid,
  .highlights-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 680px) {
  .cra-cards-grid {
    grid-template-columns: 1fr;
  }

  .hero-logo {
    width: 160px;
    height: 160px;
  }

  .hero-banner {
    padding: 2rem 1.25rem 2.5rem;
  }
}

@media (max-width: 560px) {
  .compliance-inner {
    flex-direction: column;
    align-items: flex-start;
  }
}
</style>

<style>
/* ── Light theme overrides ───────────────────── */
:root[data-theme="light"] .feedback-error {
  border-color: rgba(239, 68, 68, 0.28);
  background: rgba(239, 68, 68, 0.08);
  color: #be123c;
}
:root[data-theme="light"] .ring-track {
  stroke: rgba(20, 33, 15, 0.1);
}
:root[data-theme="light"] .score-moderate {
  background: rgba(184, 155, 18, 0.1);
  color: #78350f;
  border-color: rgba(184, 155, 18, 0.28);
}
:root[data-theme="light"] .metric-card::after {
  background: rgba(28, 107, 39, 0.04);
}
:root[data-theme="light"] .metric-card-primary {
  background:
    radial-gradient(circle at top right, rgba(112, 185, 23, 0.15), transparent 50%),
    linear-gradient(145deg, rgba(255, 255, 255, 0.96), rgba(240, 250, 236, 0.92));
}
:root[data-theme="light"] .metric-bar {
  background: rgba(20, 33, 15, 0.08);
}
:root[data-theme="light"] .compact-list-item {
  border-color: rgba(28, 107, 39, 0.1);
  background: rgba(28, 107, 39, 0.03);
}
:root[data-theme="light"] .compact-list-item:hover {
  background: rgba(28, 107, 39, 0.07);
  border-color: rgba(28, 107, 39, 0.15);
}
:root[data-theme="light"] .eos-badge.eos-warning {
  background: rgba(184, 155, 18, 0.1);
  color: #78350f;
  border-color: rgba(184, 155, 18, 0.28);
}
:root[data-theme="light"] .availability-track {
  background: rgba(20, 33, 15, 0.08);
}
:root[data-theme="light"] .avail-dot-off {
  background: rgba(20, 33, 15, 0.15);
  border-color: rgba(20, 33, 15, 0.2);
}
:root[data-theme="light"] .activity-count {
  background: rgba(28, 107, 39, 0.06);
  border-color: rgba(28, 107, 39, 0.12);
}
:root[data-theme="light"] .activity-row {
  border-color: rgba(28, 107, 39, 0.1);
  background: rgba(28, 107, 39, 0.03);
}
:root[data-theme="light"] .activity-row:hover {
  background: rgba(28, 107, 39, 0.07);
}
:root[data-theme="light"] .empty-state-inline {
  border-color: rgba(28, 107, 39, 0.14);
  background: rgba(28, 107, 39, 0.02);
}
:root[data-theme="light"] .hero-banner {
  background:
    radial-gradient(ellipse 70% 55% at 50% 0%, rgba(112, 185, 23, 0.08), transparent),
    linear-gradient(175deg, rgba(245, 252, 240, 0.98), rgba(235, 248, 230, 0.95));
  border-color: rgba(112, 185, 23, 0.2);
}
:root[data-theme="light"] .hero-title {
  background: linear-gradient(135deg, #3d7c0a, #7cb922);
  -webkit-background-clip: text;
  background-clip: text;
}
:root[data-theme="light"] .cra-article-badge {
  background: rgba(20, 33, 15, 0.05);
  border-color: rgba(20, 33, 15, 0.1);
}
:root[data-theme="light"] .cra-icon-blue   { background: rgba(59, 130, 246, 0.08); }
:root[data-theme="light"] .cra-icon-purple { background: rgba(139, 92, 246, 0.08); }
:root[data-theme="light"] .cra-icon-green  { background: rgba(16, 185, 129, 0.08); }
:root[data-theme="light"] .cra-icon-amber  { background: rgba(217, 119, 6, 0.08); }
:root[data-theme="light"] .cra-icon-red    { background: rgba(239, 68, 68, 0.08); }
:root[data-theme="light"] .cra-icon-teal   { background: rgba(20, 184, 166, 0.08); }
</style>
