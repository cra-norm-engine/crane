<template>
  <section class="page ops-hub-page">

    <!-- ── Deadline banner (top of page) ────────────────────────────────── -->
    <div class="deadline-banner" :class="daysToDeadline < 365 ? 'deadline-urgent' : 'deadline-ok'">
      <div class="deadline-eyebrow">CRA Enforcement Deadline</div>
      <div class="deadline-banner-center">
        <span class="deadline-count" :class="daysToDeadline < 365 ? 'text-amber' : 'text-green'">
          {{ daysToDeadline.toLocaleString() }}
        </span>
        <span class="deadline-unit">days remaining</span>
      </div>
      <div class="deadline-date-row">
        <svg viewBox="0 0 16 16" fill="currentColor" width="12" height="12" aria-hidden="true">
          <path d="M4 1a1 1 0 0 1 1 1v.5h6V2a1 1 0 1 1 2 0v.5h.5A1.5 1.5 0 0 1 15 4v9a1.5 1.5 0 0 1-1.5 1.5h-11A1.5 1.5 0 0 1 1 13V4a1.5 1.5 0 0 1 1.5-1.5H3V2a1 1 0 0 1 1-1zm8.5 3.5h-9A.5.5 0 0 0 3 5v7.5A.5.5 0 0 0 3.5 13h9a.5.5 0 0 0 .5-.5V5a.5.5 0 0 0-.5-.5z"/>
        </svg>
        11 December 2027
      </div>
    </div>


    <!-- ── Error ───────────────────────────────────────────────────────────── -->
    <div v-if="error" class="hub-error">
      <svg viewBox="0 0 20 20" fill="currentColor" width="16" height="16"><path fill-rule="evenodd" d="M8.485 2.495c.673-1.167 2.357-1.167 3.03 0l6.28 10.875c.673 1.167-.17 2.625-1.516 2.625H3.72c-1.347 0-2.189-1.458-1.515-2.625L8.485 2.495zM10 5a.75.75 0 0 1 .75.75v3.5a.75.75 0 0 1-1.5 0v-3.5A.75.75 0 0 1 10 5zm0 9a1 1 0 1 0 0-2 1 1 0 0 0 0 2z" clip-rule="evenodd"/></svg>
      {{ error }}
    </div>

    <!-- ── Skeleton loading ────────────────────────────────────────────────── -->
    <div v-if="loading && !data" class="skeleton-grid">
      <div class="skeleton-card" v-for="n in 4" :key="n"></div>
    </div>

    <template v-if="data">

      <!-- ── Posture hero ──────────────────────────────────────────────────── -->
      <div class="posture-hero">

        <!-- Ring gauge -->
        <div class="posture-ring-wrap">
          <svg class="posture-ring" viewBox="0 0 112 112" aria-label="Compliance readiness ring">
            <circle cx="56" cy="56" r="45" fill="none" stroke="var(--ring-track)" stroke-width="8"/>
            <circle
              cx="56" cy="56" r="45" fill="none"
              :stroke="ringColor"
              stroke-width="8"
              stroke-linecap="round"
              stroke-dasharray="282.74"
              :stroke-dashoffset="ringOffset"
              transform="rotate(-90 56 56)"
            />
          </svg>
          <div class="ring-center">
            <div class="ring-pct" :style="{ color: ringColor }">{{ postureScore }}%</div>
            <div class="ring-sub">Ready</div>
          </div>
        </div>

        <!-- Copy + status chips -->
        <div class="posture-copy">
          <h2 class="posture-title">Compliance Readiness</h2>
          <p class="posture-desc">
            Based on open vulnerabilities, approved risk assessments, active support periods, and outstanding compliance actions.
          </p>
          <div class="posture-chips">
            <span class="posture-chip" :class="data.vulnerability_summary.critical === 0 ? 'pchip-ok' : 'pchip-danger'">
              <svg viewBox="0 0 12 12" fill="currentColor" width="10" height="10"><path v-if="data.vulnerability_summary.critical === 0" d="M1 6l3.5 3.5L11 2"/><path v-else d="M2 2l8 8M10 2 2 10"/></svg>
              Vulnerabilities
            </span>
            <span class="posture-chip" :class="data.risk_summary.approved > 0 ? 'pchip-ok' : 'pchip-warn'">
              <svg viewBox="0 0 12 12" fill="currentColor" width="10" height="10"><path v-if="data.risk_summary.approved > 0" d="M1 6l3.5 3.5L11 2"/><path v-else d="M6 2v5M6 9v1"/></svg>
              Risk Assessments
            </span>
            <span class="posture-chip" :class="data.lifecycle_summary.expired === 0 ? 'pchip-ok' : 'pchip-danger'">
              <svg viewBox="0 0 12 12" fill="currentColor" width="10" height="10"><path v-if="data.lifecycle_summary.expired === 0" d="M1 6l3.5 3.5L11 2"/><path v-else d="M2 2l8 8M10 2 2 10"/></svg>
              Lifecycle
            </span>
            <span class="posture-chip" :class="data.change_summary.action_required === 0 ? 'pchip-ok' : 'pchip-warn'">
              <svg viewBox="0 0 12 12" fill="currentColor" width="10" height="10"><path v-if="data.change_summary.action_required === 0" d="M1 6l3.5 3.5L11 2"/><path v-else d="M6 2v5M6 9v1"/></svg>
              Pending Actions
            </span>
          </div>
          <!-- Plain-language posture summary -->
          <p class="posture-summary" :class="postureScore === 100 ? 'posture-summary--ok' : 'posture-summary--warn'">
            {{ postureSummary }}
          </p>
        </div>


      </div>

      <!-- ── KPI strip ──────────────────────────────────────────────────────── -->
      <div class="kpi-strip">

        <!-- Products -->
        <div class="kpi-card" @click="$router.push({ name: 'products' })">
          <div class="kpi-icon kpi-icon-neutral">
            <svg viewBox="0 0 20 20" fill="currentColor" width="18" height="18"><path d="M2 4.5A2.5 2.5 0 0 1 4.5 2h11A2.5 2.5 0 0 1 18 4.5v11a2.5 2.5 0 0 1-2.5 2.5h-11A2.5 2.5 0 0 1 2 15.5v-11zM4.5 3.5A1 1 0 0 0 3.5 4.5v11a1 1 0 0 0 1 1h11a1 1 0 0 0 1-1v-11a1 1 0 0 0-1-1h-11z"/><path d="M6 7h8v1.5H6V7zm0 3h8v1.5H6V10zm0 3h5v1.5H6V13z"/></svg>
          </div>
          <div class="kpi-card-text">
            <span class="kpi-num-sm">{{ data.product_summary.total }}</span>
            <span class="kpi-label">Products</span>
            <span class="kpi-sub muted">{{ data.product_summary.in_scope }} in scope · {{ data.product_summary.released }} released</span>
          </div>
        </div>

        <!-- Open vulnerabilities -->
        <div
          class="kpi-card"
          :class="{ 'kpi-danger': data.vulnerability_summary.critical > 0 }"
          @click="$router.push({ name: 'vulnerability-handling' })"
        >
          <div class="kpi-icon" :class="data.vulnerability_summary.critical > 0 ? 'kpi-icon-danger' : 'kpi-icon-neutral'">
            <svg viewBox="0 0 20 20" fill="currentColor" width="18" height="18"><path fill-rule="evenodd" d="M8.485 2.495c.673-1.167 2.357-1.167 3.03 0l6.28 10.875c.673 1.167-.17 2.625-1.516 2.625H3.72c-1.347 0-2.189-1.458-1.515-2.625L8.485 2.495zM10 5a.75.75 0 0 1 .75.75v3.5a.75.75 0 0 1-1.5 0v-3.5A.75.75 0 0 1 10 5zm0 9a1 1 0 1 0 0-2 1 1 0 0 0 0 2z" clip-rule="evenodd"/></svg>
          </div>
          <div class="kpi-card-text">
            <span class="kpi-num-sm" :class="{ 'num-danger': data.vulnerability_summary.critical > 0 }">{{ data.vulnerability_summary.total_open }}</span>
            <span class="kpi-label">Open Vulnerabilities</span>
            <span class="kpi-sub" :class="data.vulnerability_summary.critical > 0 ? 'sub-danger' : 'muted'">
              <template v-if="data.vulnerability_summary.critical > 0">{{ data.vulnerability_summary.critical }} critical</template>
              <template v-else>{{ data.vulnerability_summary.overdue }} overdue</template>
            </span>
          </div>
        </div>

        <!-- Risk assessments -->
        <div
          class="kpi-card"
          :class="{ 'kpi-warn': data.risk_summary.draft > 0 && data.risk_summary.approved === 0 }"
          @click="$router.push({ name: 'risk-assessments' })"
        >
          <div class="kpi-icon" :class="(data.risk_summary.draft > 0 && data.risk_summary.approved === 0) ? 'kpi-icon-warn' : 'kpi-icon-neutral'">
            <svg viewBox="0 0 20 20" fill="currentColor" width="18" height="18"><path fill-rule="evenodd" d="M10 1a9 9 0 1 0 0 18A9 9 0 0 0 10 1zm-1 5a1 1 0 1 1 2 0v4a1 1 0 1 1-2 0V6zm1 8a1.25 1.25 0 1 1 0-2.5A1.25 1.25 0 0 1 10 14z" clip-rule="evenodd"/></svg>
          </div>
          <div class="kpi-card-text">
            <span class="kpi-num-sm" :class="{ 'num-warn': data.risk_summary.draft > 0 && data.risk_summary.approved === 0 }">{{ data.risk_summary.total }}</span>
            <span class="kpi-label">Risk Assessments</span>
            <span class="kpi-sub" :class="data.risk_summary.approved > 0 ? 'muted' : 'sub-warn'">
              <template v-if="data.risk_summary.approved > 0">{{ data.risk_summary.approved }} approved</template>
              <template v-else-if="data.risk_summary.in_review > 0">{{ data.risk_summary.in_review }} in review</template>
              <template v-else>None approved yet</template>
            </span>
          </div>
        </div>

        <!-- My tasks -->
        <div
          class="kpi-card"
          :class="{ 'kpi-danger': data.task_summary.overdue > 0 }"
          @click="$router.push({ name: 'my-tasks' })"
        >
          <div class="kpi-icon" :class="data.task_summary.overdue > 0 ? 'kpi-icon-danger' : 'kpi-icon-neutral'">
            <svg viewBox="0 0 20 20" fill="currentColor" width="18" height="18"><path fill-rule="evenodd" d="M16.704 4.153a.75.75 0 0 1 .143 1.052l-8 10.5a.75.75 0 0 1-1.127.075l-4.5-4.5a.75.75 0 0 1 1.06-1.06l3.894 3.893 7.48-9.817a.75.75 0 0 1 1.05-.143z" clip-rule="evenodd"/></svg>
          </div>
          <div class="kpi-card-text">
            <span class="kpi-num-sm" :class="{ 'num-danger': data.task_summary.overdue > 0 }">{{ data.task_summary.total_open }}</span>
            <span class="kpi-label">My Tasks</span>
            <span class="kpi-sub" :class="data.task_summary.overdue > 0 ? 'sub-danger' : 'muted'">
              <template v-if="data.task_summary.overdue > 0">{{ data.task_summary.overdue }} overdue</template>
              <template v-else>{{ data.task_summary.due_this_week }} due this week</template>
            </span>
          </div>
        </div>

      </div>

      <!-- ── Main grid ──────────────────────────────────────────────────────── -->
      <div class="hub-grid">

        <!-- ── LEFT column ──────────────────────────────────────────────────── -->
        <div class="hub-left">

          <!-- Vulnerability pipeline -->
          <div class="hub-card">
            <div class="hub-card-header">
              <h3 class="hub-card-title">Vulnerability Pipeline</h3>
              <button class="link-btn" @click="$router.push({ name: 'vulnerability-handling' })">View all →</button>
            </div>
            <div class="bar-chart">
              <div
                v-for="row in vulnRows"
                :key="row.label"
                class="bar-row"
              >
                <span class="bar-label">{{ row.label }}</span>
                <div class="bar-track">
                  <div
                    class="bar-fill"
                    :style="{ width: barWidth(row.value, vulnMax) + '%', background: row.color }"
                  ></div>
                </div>
                <span class="bar-value">{{ row.value }}</span>
              </div>
              <p v-if="data.vulnerability_summary.total_open === 0" class="bar-empty muted">No open vulnerabilities</p>
            </div>
            <div v-if="data.vulnerability_summary.overdue > 0" class="hub-alert hub-alert-danger">
              <svg viewBox="0 0 16 16" fill="currentColor" width="13" height="13"><path d="M8 1a7 7 0 1 0 0 14A7 7 0 0 0 8 1zm0 3.5a.75.75 0 0 1 .75.75v3a.75.75 0 0 1-1.5 0v-3A.75.75 0 0 1 8 4.5zm0 6.5a.75.75 0 1 1 0-1.5.75.75 0 0 1 0 1.5z"/></svg>
              {{ data.vulnerability_summary.overdue }} overdue — remediation deadline passed
            </div>
          </div>

          <!-- Risk assessments -->
          <div class="hub-card">
            <div class="hub-card-header">
              <h3 class="hub-card-title">Risk Assessments</h3>
              <button class="link-btn" @click="$router.push({ name: 'risk-assessments' })">View all →</button>
            </div>
            <div class="bar-chart">
              <div v-for="row in riskRows" :key="row.label" class="bar-row">
                <span class="bar-label">{{ row.label }}</span>
                <div class="bar-track">
                  <div
                    class="bar-fill"
                    :style="{ width: barWidth(row.value, riskMax) + '%', background: row.color }"
                  ></div>
                </div>
                <span class="bar-value">{{ row.value }}</span>
              </div>
              <p v-if="data.risk_summary.total === 0" class="bar-empty muted">No risk assessments yet</p>
            </div>
          </div>

          <!-- Substantial changes -->
          <div class="hub-card">
            <div class="hub-card-header">
              <h3 class="hub-card-title">Substantial Changes</h3>
              <button class="link-btn" @click="$router.push({ name: 'changes' })">View all →</button>
            </div>
            <div class="change-grid">
              <div class="change-cell">
                <span class="change-cell-num">{{ data.change_summary.total_open }}</span>
                <span class="change-cell-label">Open</span>
                <span class="change-cell-hint muted">Under assessment</span>
              </div>
              <div class="change-cell" :class="{ 'change-cell-warn': data.change_summary.action_required > 0 }">
                <span class="change-cell-num" :class="{ 'num-warn': data.change_summary.action_required > 0 }">{{ data.change_summary.action_required }}</span>
                <span class="change-cell-label">Action Required</span>
                <span class="change-cell-hint muted">Compliance tasks pending</span>
              </div>
              <div class="change-cell" :class="{ 'change-cell-danger': data.change_summary.substantial_open > 0 }">
                <span class="change-cell-num" :class="{ 'num-danger': data.change_summary.substantial_open > 0 }">{{ data.change_summary.substantial_open }}</span>
                <span class="change-cell-label">Substantial</span>
                <span class="change-cell-hint muted">Require re-assessment</span>
              </div>
            </div>
            <div v-if="data.change_summary.action_required > 0" class="hub-alert hub-alert-warn">
              <svg viewBox="0 0 16 16" fill="currentColor" width="13" height="13"><path d="M8 1a7 7 0 1 0 0 14A7 7 0 0 0 8 1zm0 3.5a.75.75 0 0 1 .75.75v3a.75.75 0 0 1-1.5 0v-3A.75.75 0 0 1 8 4.5zm0 6.5a.75.75 0 1 1 0-1.5.75.75 0 0 1 0 1.5z"/></svg>
              {{ data.change_summary.action_required }} change{{ data.change_summary.action_required > 1 ? 's' : '' }} awaiting compliance action
            </div>
          </div>

          <!-- Lifecycle alerts -->
          <div class="hub-card" :class="{ 'hub-card-alert': data.lifecycle_summary.expired > 0 }">
            <div class="hub-card-header">
              <h3 class="hub-card-title">Lifecycle &amp; Support Period Alerts</h3>
              <button class="link-btn" @click="$router.push({ name: 'support-hub' })">View all →</button>
            </div>

            <div class="lc-grid">
              <!-- Expired -->
              <div class="lc-cell" :class="{ 'lc-danger': data.lifecycle_summary.expired > 0 }">
                <span class="lc-num" :class="{ 'num-danger': data.lifecycle_summary.expired > 0 }">
                  {{ data.lifecycle_summary.expired }}
                </span>
                <span class="lc-label">Expired</span>
                <span class="lc-hint muted">Past end-of-support</span>
              </div>

              <!-- Expiring within 90 days -->
              <div class="lc-cell" :class="{ 'lc-warn': data.lifecycle_summary.expiring_90d > 0 }">
                <span class="lc-num" :class="{ 'num-warn': data.lifecycle_summary.expiring_90d > 0 }">
                  {{ data.lifecycle_summary.expiring_90d }}
                </span>
                <span class="lc-label">Within 90 days</span>
                <span class="lc-hint muted">Expiring soon</span>
              </div>

              <!-- Expiring within 180 days -->
              <div class="lc-cell">
                <span class="lc-num">{{ data.lifecycle_summary.expiring_180d }}</span>
                <span class="lc-label">Within 180 days</span>
                <span class="lc-hint muted">Plan ahead</span>
              </div>

              <!-- On Track -->
              <div class="lc-cell">
                <span class="lc-num lc-num-ok">
                  {{ data.lifecycle_summary.total_active - data.lifecycle_summary.expired - data.lifecycle_summary.expiring_180d }}
                </span>
                <span class="lc-label">On Track</span>
                <span class="lc-hint muted">Over 180 days</span>
              </div>
            </div>

            <div
              v-if="data.lifecycle_summary.expired > 0"
              class="hub-alert hub-alert-danger"
            >
              <svg viewBox="0 0 16 16" fill="currentColor" width="13" height="13"><path d="M8 1a7 7 0 1 0 0 14A7 7 0 0 0 8 1zm0 3.5a.75.75 0 0 1 .75.75v3a.75.75 0 0 1-1.5 0v-3A.75.75 0 0 1 8 4.5zm0 6.5a.75.75 0 1 1 0-1.5.75.75 0 0 1 0 1.5z"/></svg>
              {{ data.lifecycle_summary.expired }} product{{ data.lifecycle_summary.expired > 1 ? 's' : '' }} — Support period expired — security update obligations have ended;
            </div>
            <div
              v-else-if="data.lifecycle_summary.pending_alerts > 0"
              class="hub-alert hub-alert-info"
            >
              <svg viewBox="0 0 16 16" fill="currentColor" width="13" height="13"><path d="M8 1a7 7 0 1 0 0 14A7 7 0 0 0 8 1zm0 3.5a.75.75 0 0 1 .75.75v3a.75.75 0 0 1-1.5 0v-3A.75.75 0 0 1 8 4.5zm0 6.5a.75.75 0 1 1 0-1.5.75.75 0 0 1 0 1.5z"/></svg>
              {{ data.lifecycle_summary.pending_alerts }} pending notification{{ data.lifecycle_summary.pending_alerts > 1 ? 's' : '' }} awaiting delivery
            </div>
          </div>

        </div>

        <!-- ── RIGHT column ─────────────────────────────────────────────────── -->
        <div class="hub-right">

          <!-- Upcoming releases -->
          <div class="hub-card">
            <div class="hub-card-header">
              <h3 class="hub-card-title">Upcoming Releases</h3>
            </div>
            <ul class="release-list" v-if="data.upcoming_releases.length">
              <li
                v-for="rel in data.upcoming_releases"
                :key="rel.id"
                class="release-item"
                @click="$router.push({ name: 'products' })"
              >
                <div class="release-item-left">
                  <span class="release-name">{{ rel.product_name ?? '—' }}</span>
                  <span class="release-display_version muted">v{{ rel.display_version }}</span>
                </div>
                <div class="release-item-right">
                  <span
                    class="days-chip"
                    :class="daysChipClass(rel.days_until)"
                  >
                    <template v-if="rel.days_until !== null">
                      {{ rel.days_until === 0 ? 'Today' : rel.days_until < 0 ? `${Math.abs(rel.days_until)}d ago` : `${rel.days_until}d` }}
                    </template>
                    <template v-else>–</template>
                  </span>
                  <span class="release-status muted">{{ formatStatus(rel.release_status) }}</span>
                </div>
              </li>
            </ul>
            <p v-else class="bar-empty muted">No upcoming releases in the next 90 days</p>
          </div>

          <!-- Recent activity -->
          <div class="hub-card hub-card-activity">
            <div class="hub-card-header">
              <h3 class="hub-card-title">Recent Activity</h3>
            </div>
            <ul class="activity-list" v-if="data.recent_activity.length">
              <li
                v-for="item in data.recent_activity"
                :key="item.id"
                class="activity-item"
              >
                <span class="activity-dot" :class="activityDotClass(item.entity_type)"></span>
                <div class="activity-body">
                  <p class="activity-summary">{{ item.summary }}</p>
                  <span class="activity-meta muted">
                    {{ item.actor_email ?? 'System' }} · {{ timeAgo(item.created_at) }}
                  </span>
                </div>
              </li>
            </ul>
            <p v-else class="bar-empty muted">No recent activity</p>
          </div>

        </div>
      </div>

    </template>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { useRouter } from "vue-router";
import { dashboardService } from "@/services/dashboard-service";
import { useAuthStore } from "@/stores/auth";
import type { DashboardRead } from "@/types/dashboard";

// ── Router + auth ─────────────────────────────────────────────────────────────
const router    = useRouter();
const authStore = useAuthStore();

// ── State ─────────────────────────────────────────────────────────────────────
const data    = ref<DashboardRead | null>(null);
const loading = ref(false);
const error   = ref<string | null>(null);

// ── Load ──────────────────────────────────────────────────────────────────────
async function load(): Promise<void> {
  loading.value = true;
  error.value   = null;
  try {
    data.value = await dashboardService.get();
  } catch {
    error.value = "Failed to load dashboard data. Please refresh.";
  } finally {
    loading.value = false;
  }
}
onMounted(load);

// ── Bar charts ────────────────────────────────────────────────────────────────
const vulnRows = computed(() => {
  const v = data.value?.vulnerability_summary;
  if (!v) return [];
  return [
    { label: "Critical", value: v.critical, color: "var(--color-danger)"   },
    { label: "High",     value: v.high,     color: "var(--color-bar-high)" },
    { label: "Medium",   value: v.medium,   color: "var(--color-warning)"  },
    { label: "Low",      value: v.low,      color: "var(--color-success)"  },
  ];
});

const riskRows = computed(() => {
  const r = data.value?.risk_summary;
  if (!r) return [];
  return [
    { label: "Draft",     value: r.draft,     color: "var(--color-slate-text)"  },
    { label: "In review", value: r.in_review, color: "var(--color-info)"        },
    { label: "Approved",  value: r.approved,  color: "var(--color-success)"     },
    { label: "Archived",  value: r.archived,  color: "var(--color-text-muted)"  },
  ];
});

const vulnMax = computed(() => Math.max(...vulnRows.value.map((r: { value: number }) => r.value), 1));
const riskMax = computed(() => Math.max(...riskRows.value.map((r: { value: number }) => r.value), 1));

// ── Posture ring ──────────────────────────────────────────────────────────────
/** 0-100 compliance readiness score across 4 key pillars (25 pts each) */
const postureScore = computed(() => {
  if (!data.value) return 0;
  let pts = 0;
  if (data.value.vulnerability_summary.critical === 0) pts += 25;
  if (data.value.risk_summary.approved > 0)           pts += 25;
  if (data.value.lifecycle_summary.expired === 0)     pts += 25;
  if (data.value.change_summary.action_required === 0) pts += 25;
  return pts;
});

/** Calendar days between today and the CRA enforcement deadline (11 Dec 2027) */
const daysToDeadline = computed(() => {
  const deadline = new Date("2027-12-11");
  const today    = new Date();
  return Math.ceil((deadline.getTime() - today.getTime()) / 86_400_000);
});

/** Plain-language summary of the current compliance posture */
const postureSummary = computed(() => {
  if (!data.value) return "";
  const issues: string[] = [];
  if (data.value.vulnerability_summary.critical > 0)
    issues.push(`${data.value.vulnerability_summary.critical} critical vulnerability${data.value.vulnerability_summary.critical > 1 ? "ies" : ""} open`);
  if (data.value.risk_summary.approved === 0)
    issues.push("no approved risk assessments");
  if (data.value.lifecycle_summary.expired > 0)
    issues.push(`${data.value.lifecycle_summary.expired} support period${data.value.lifecycle_summary.expired > 1 ? "s" : ""} expired`);
  if (data.value.change_summary.action_required > 0)
    issues.push(`${data.value.change_summary.action_required} change${data.value.change_summary.action_required > 1 ? "s" : ""} awaiting compliance action`);

  if (issues.length === 0)
    return "All four compliance pillars are met. No critical vulnerabilities, risk assessments approved, all support periods active, and no outstanding change actions.";
  const issueText = issues.length === 1
    ? issues[0]
    : issues.slice(0, -1).join(", ") + " and " + issues[issues.length - 1];
  return `Score reduced by ${issues.length} issue${issues.length > 1 ? "s" : ""}: ${issueText}.`;
});

/** Ring stroke color driven by posture score */
const ringColor = computed(() => {
  if (postureScore.value >= 75) return "oklch(0.48 0.092 150)";
  if (postureScore.value >= 50) return "oklch(0.74 0.135 75)";
  return "oklch(0.58 0.175 25)";
});

/** SVG stroke-dashoffset for the posture ring (circumference = 2π × 45 ≈ 282.74) */
const ringOffset = computed(() => 282.74 * (1 - postureScore.value / 100));

function barWidth(val: number, max: number): number {
  return Math.round((val / max) * 100);
}

// ── Helpers ───────────────────────────────────────────────────────────────────
function daysChipClass(days: number | null): string {
  if (days === null) return "chip-muted";
  if (days < 0)  return "chip-muted";
  if (days <= 7) return "chip-danger";
  if (days <= 30) return "chip-warn";
  return "chip-ok";
}

function activityDotClass(entityType: string | null): string {
  const map: Record<string, string> = {
    vulnerability_report: "dot-red",
    risk_item:            "dot-amber",
    change:               "dot-blue",
    release_gate_item:    "dot-green",
    product:              "dot-purple",
  };
  return map[entityType ?? ""] ?? "dot-grey";
}

function formatStatus(s: string): string {
  return s.replace(/_/g, " ");
}

function timeAgo(iso: string): string {
  const diff = Date.now() - new Date(iso).getTime();
  const m = Math.floor(diff / 60000);
  if (m < 1)  return "just now";
  if (m < 60) return `${m}m ago`;
  const h = Math.floor(m / 60);
  if (h < 24) return `${h}h ago`;
  const d = Math.floor(h / 24);
  return `${d}d ago`;
}
</script>

<style scoped>
/* ── Font import ───────────────────────────────────────────────────────────── */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=JetBrains+Mono:wght@500;700&display=swap');

/* ── Page ─────────────────────────────────────────────────────────────────── */
.ops-hub-page {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
  font-family: 'Inter', var(--font-sans, system-ui), sans-serif;

  /* Light-mode local tokens matching CRANE Dashboard reference */
  --ring-track: var(--color-inset-border, #e8edea);
}

/* ── Topbar ───────────────────────────────────────────────────────────────── */
/* ── Deadline banner (top of page) ───────────────────────────────────────── */
.deadline-banner {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0.7rem 1.25rem;
  border-radius: 10px;
  border-left: 3px solid;
}
.deadline-banner.deadline-ok {
  background: var(--color-surface);
  border-left-color: var(--color-success);
  border-top: 1px solid var(--color-border);
  border-right: 1px solid var(--color-border);
  border-bottom: 1px solid var(--color-border);
}
.deadline-banner.deadline-urgent {
  background: var(--color-surface);
  border-left-color: var(--color-warning);
  border-top: 1px solid var(--color-border);
  border-right: 1px solid var(--color-border);
  border-bottom: 1px solid var(--color-border);
}
.deadline-banner-center {
  display: flex;
  align-items: baseline;
  gap: 0.5rem;
}

@keyframes spin { to { transform: rotate(360deg); } }

/* ── Error ────────────────────────────────────────────────────────────────── */
.hub-error {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.75rem 1rem;
  border-radius: 8px;
  background: var(--color-danger-bg);
  border: 1px solid var(--color-danger-border);
  color: var(--color-danger-text);
  font-size: 0.875rem;
}

/* ── Skeleton ─────────────────────────────────────────────────────────────── */
.skeleton-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 1rem;
}

.skeleton-card {
  height: 100px;
  border-radius: 12px;
  background: linear-gradient(
    90deg,
    var(--color-surface-elevated) 25%,
    var(--color-surface-elevated-strong) 50%,
    var(--color-surface-elevated) 75%
  );
  background-size: 200% 100%;
  animation: shimmer 1.4s infinite;
}

@keyframes shimmer {
  0%   { background-position: 200% 0; }
  100% { background-position: -200% 0; }
}

/* ── Posture hero ─────────────────────────────────────────────────────────── */
.posture-hero {
  display: grid;
  grid-template-columns: auto 1fr;
  align-items: center;
  gap: 1.75rem;
  padding: 1.5rem 1.75rem;
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: 14px;
}

/* Ring gauge wrapper */
.posture-ring-wrap {
  position: relative;
  width: 112px;
  height: 112px;
  flex-shrink: 0;
}

.posture-ring {
  width: 112px;
  height: 112px;
  display: block;
}

.posture-ring circle {
  transition: stroke-dashoffset 0.8s cubic-bezier(0.4, 0, 0.2, 1),
              stroke 0.4s ease;
}

.ring-center {
  position: absolute;
  inset: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 0.1rem;
}

.ring-pct {
  font-size: 1.4rem;
  font-weight: 800;
  line-height: 1;
  font-family: 'JetBrains Mono', monospace;
  letter-spacing: -0.03em;
  transition: color 0.4s ease;
}

.ring-sub {
  font-size: 0.62rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.1em;
  color: var(--color-text-muted);
}

/* Copy section */
.posture-copy {
  min-width: 0;
}

.posture-title {
  margin: 0 0 0.3rem;
  font-size: 1.05rem;
  font-weight: 700;
  color: var(--color-text);
  letter-spacing: -0.01em;
}

.posture-desc {
  margin: 0 0 0.75rem;
  font-size: 0.8rem;
  line-height: 1.55;
  color: var(--color-text-muted);
}

.posture-summary {
  margin: 0.65rem 0 0;
  font-size: 0.8rem;
  line-height: 1.6;
  border-radius: 6px;
  padding: 0.45rem 0.7rem;
}
.posture-summary--ok {
  background: var(--color-success-bg, oklch(0.955 0.024 150));
  color: oklch(0.38 0.092 150);
  border: 1px solid oklch(0.85 0.05 150);
}
.posture-summary--warn {
  background: var(--color-warning-bg);
  color: var(--color-warning-text, oklch(0.52 0.12 75));
  border: 1px solid var(--color-warning-border);
}

.posture-chips {
  display: flex;
  flex-wrap: wrap;
  gap: 0.4rem;
}

.posture-chip {
  display: inline-flex;
  align-items: center;
  gap: 0.3rem;
  padding: 0.22rem 0.65rem;
  border-radius: 999px;
  font-size: 0.72rem;
  font-weight: 600;
}
.pchip-ok {
  background: var(--color-success-bg, oklch(0.955 0.024 150));
  color: oklch(0.38 0.092 150);
  border: 1px solid oklch(0.85 0.05 150);
}
.pchip-warn {
  background: var(--color-warning-bg);
  color: var(--color-warning-text, oklch(0.52 0.12 75));
  border: 1px solid var(--color-warning-border);
}
.pchip-danger {
  background: var(--color-danger-bg);
  color: var(--color-danger-text);
  border: 1px solid var(--color-danger-border);
}

/* Deadline countdown card */
.deadline-eyebrow {
  font-size: 0.65rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.1em;
  color: var(--color-text-muted);
  white-space: nowrap;
}

.deadline-count {
  font-size: 1.5rem;
  font-weight: 800;
  line-height: 1;
  font-family: 'JetBrains Mono', monospace;
  letter-spacing: -0.03em;
}

.deadline-unit {
  font-size: 0.72rem;
  font-weight: 600;
  color: var(--color-text-muted);
}

.deadline-date-row {
  display: flex;
  align-items: center;
  gap: 0.35rem;
  font-size: 0.72rem;
  font-weight: 600;
  color: var(--color-text-secondary);
  white-space: nowrap;
}
.deadline-date-row svg {
  color: var(--color-text-muted);
  flex-shrink: 0;
}

.text-green { color: var(--color-success); }
.text-amber { color: var(--color-warning); }

/* ── KPI strip ────────────────────────────────────────────────────────────── */
/* One local token for "high severity" orange — not in global palette */
.ops-hub-page { --color-bar-high: #f97316; }

.kpi-strip {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 1rem;
  align-items: stretch;   /* equal-height KPI cards */
}

.kpi-card {
  display: flex;
  align-items: center;
  gap: 0.9rem;
  padding: 1rem 1.15rem;
  border-radius: 12px;
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  cursor: pointer;
  transition: border-color 0.15s, box-shadow 0.15s;
}
.kpi-card:hover {
  border-color: var(--color-primary);
  box-shadow: 0 0 0 2px var(--color-surface-soft);
}


.kpi-card.kpi-danger { border-color: var(--color-danger-border); }
.kpi-card.kpi-warn   { border-color: var(--color-warning-border); }

/* Icon badge */
.kpi-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 40px;
  height: 40px;
  border-radius: 10px;
  flex-shrink: 0;
}
.kpi-icon-neutral { background: var(--color-surface-elevated); color: var(--color-primary); }
.kpi-icon-danger  { background: var(--color-danger-bg);        color: var(--color-danger);  }
.kpi-icon-warn    { background: var(--color-warning-bg);       color: var(--color-warning); }

.kpi-num-sm {
  font-size: 1.65rem;
  font-weight: 800;
  line-height: 1;
  color: var(--color-text);
  letter-spacing: -0.03em;
}
.num-danger { color: var(--color-danger); }
.num-warn   { color: var(--color-warning); }

.kpi-card-text {
  display: flex;
  flex-direction: column;
  gap: 0.1rem;
  min-width: 0;
}

.kpi-label {
  font-size: 0.79rem;
  font-weight: 700;
  color: var(--color-text);
  white-space: nowrap;
}

.kpi-sub { font-size: 0.73rem; }
.sub-danger { color: var(--color-danger); }
.sub-warn   { color: var(--color-warning); }

/* ── Main grid ────────────────────────────────────────────────────────────── */
.hub-grid {
  display: grid;
  grid-template-columns: 1fr 380px;
  gap: 1rem;
  align-items: stretch;  /* both columns same height */
}

.hub-left,
.hub-right {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

/* Activity card expands to fill remaining right-column height */
.hub-card-activity {
  flex: 1;
}

/* ── Hub cards ────────────────────────────────────────────────────────────── */
.hub-card {
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: 12px;
  padding: 1.2rem 1.3rem;
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.hub-card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.5rem;
  /* Extend the header edge-to-edge to get a full-width border-bottom separator */
  margin: -1.2rem -1.3rem 0;
  padding: 0.9rem 1.3rem 0.85rem;
  border-bottom: 1px solid var(--color-border);
}

.hub-card-title {
  margin: 0;
  font-size: 0.875rem;
  font-weight: 700;
  color: var(--color-text);
  letter-spacing: -0.01em;
  font-family: 'Inter', var(--font-sans, system-ui), sans-serif;
}

.hub-card-sub {
  font-size: 0.78rem;
  margin: -0.25rem 0 0;
  line-height: 1.5;
}

.hub-card-alert { border-color: var(--color-danger-border); }

.link-btn {
  background: none;
  border: none;
  padding: 0;
  font-size: 0.78rem;
  font-weight: 600;
  color: var(--color-primary);
  cursor: pointer;
  white-space: nowrap;
  transition: color 0.12s;
}
.link-btn:hover { color: var(--color-primary-2); }

/* ── Bar chart ────────────────────────────────────────────────────────────── */
.bar-chart {
  display: flex;
  flex-direction: column;
  gap: 0.55rem;
}

.bar-row {
  display: grid;
  grid-template-columns: 4.5rem 1fr 2rem;
  align-items: center;
  gap: 0.65rem;
}

.bar-label {
  font-size: 0.78rem;
  font-weight: 600;
  color: var(--color-text-muted);
  text-align: right;
}

.bar-track {
  height: 8px;
  border-radius: 4px;
  background: var(--color-inset-border);
  overflow: hidden;
}

.bar-fill {
  height: 100%;
  border-radius: 4px;
  transition: width 0.5s cubic-bezier(0.4, 0, 0.2, 1);
  min-width: 2px;
}

.bar-value {
  font-size: 0.78rem;
  font-weight: 700;
  color: var(--color-text);
  text-align: right;
}

.bar-empty {
  font-size: 0.82rem;
  margin: 0;
  padding: 0.5rem 0;
}

/* ── Hub alerts ───────────────────────────────────────────────────────────── */
.hub-alert {
  display: flex;
  align-items: center;
  gap: 0.45rem;
  font-size: 0.78rem;
  font-weight: 600;
  padding: 0.5rem 0.75rem;
  border-radius: 6px;
}
.hub-alert-danger {
  background: var(--color-danger-bg);
  border: 1px solid var(--color-danger-border);
  color: var(--color-danger-text);
}
.hub-alert-info {
  background: var(--color-info-bg);
  border: 1px solid var(--color-info-border);
  color: var(--color-info-text);
}

/* ── Substantial changes grid ─────────────────────────────────────────────── */
.change-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 0.5rem;
}

.change-cell {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.15rem;
  padding: 0.75rem 0.5rem;
  border-radius: 8px;
  background: var(--color-surface-elevated);
  border: 1px solid var(--color-border);
  text-align: center;
}

.change-cell.change-cell-warn   { border-color: var(--color-warning-border); background: var(--color-warning-bg); }
.change-cell.change-cell-danger { border-color: var(--color-danger-border);  background: var(--color-danger-bg);  }


.change-cell-num {
  font-size: 1.6rem;
  font-weight: 800;
  line-height: 1;
  letter-spacing: -0.03em;
  color: var(--color-text);
}

.change-cell-label {
  font-size: 0.72rem;
  font-weight: 700;
  color: var(--color-text);
  white-space: nowrap;
}

.change-cell-hint { font-size: 0.67rem; }

/* ── Upcoming releases ────────────────────────────────────────────────────── */
.release-list {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.release-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.75rem;
  padding: 0.6rem 0.75rem;
  border-radius: 8px;
  background: var(--color-surface-elevated);
  border: 1px solid var(--color-border);
  cursor: pointer;
  transition: border-color 0.12s;
}
.release-item:hover { border-color: var(--color-primary); }

.release-item-left { display: flex; flex-direction: column; gap: 0.1rem; min-width: 0; }

.release-name {
  font-size: 0.84rem;
  font-weight: 700;
  color: var(--color-text);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.release-display_version { font-size: 0.75rem; }

.release-item-right {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 0.1rem;
  flex-shrink: 0;
}

.days-chip {
  font-size: 0.72rem;
  font-weight: 700;
  padding: 0.15rem 0.45rem;
  border-radius: 4px;
  white-space: nowrap;
}
.chip-danger { background: var(--color-danger-bg);  color: var(--color-danger-text);  border: 1px solid var(--color-danger-border); }
.chip-warn   { background: var(--color-warning-bg); color: var(--color-warning-text); border: 1px solid var(--color-warning-border); }
.chip-ok     { background: var(--color-success-bg); color: var(--color-success-text); border: 1px solid var(--color-success-border); }
.chip-muted  { background: var(--color-slate-bg);   color: var(--color-slate-text);   border: 1px solid var(--color-slate-border); }

.release-status { font-size: 0.72rem; text-transform: capitalize; }

/* ── Activity feed ────────────────────────────────────────────────────────── */
.hub-card-activity { overflow: hidden; min-height: 0; }

.activity-list {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
}

.activity-item {
  display: flex;
  align-items: flex-start;
  gap: 0.65rem;
  padding: 0.6rem 0;
  border-bottom: 1px solid var(--color-divider);
}
.activity-item:last-child { border-bottom: none; }

.activity-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  flex-shrink: 0;
  margin-top: 0.35rem;
}
.dot-red    { background: var(--color-danger); }
.dot-amber  { background: var(--color-bar-high); }
.dot-blue   { background: var(--color-info); }
.dot-green  { background: var(--color-success); }
.dot-purple { background: var(--color-purple); }
.dot-grey   { background: var(--color-text-muted); }

.activity-body { display: flex; flex-direction: column; gap: 0.15rem; min-width: 0; }

.activity-summary {
  margin: 0;
  font-size: 0.82rem;
  font-weight: 500;
  color: var(--color-text);
  line-height: 1.4;
}

.activity-meta { font-size: 0.72rem; }

/* ── Lifecycle grid ───────────────────────────────────────────────────────── */
.lc-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 0.5rem;
}

.lc-cell {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.15rem;
  padding: 0.65rem 0.5rem;
  border-radius: 8px;
  background: var(--color-surface-elevated);
  border: 1px solid var(--color-border);
  text-align: center;
}

.lc-cell.lc-danger { border-color: var(--color-danger-border); background: var(--color-danger-bg); }
.lc-cell.lc-warn   { border-color: var(--color-warning-border); background: var(--color-warning-bg); }


.lc-num {
  font-size: 1.6rem;
  font-weight: 800;
  line-height: 1;
  letter-spacing: -0.03em;
  color: var(--color-text);
}
.lc-num-ok { color: var(--color-success); }

.lc-label { font-size: 0.72rem; font-weight: 700; color: var(--color-text); white-space: nowrap; }

.lc-hint { font-size: 0.68rem; }

/* ── hub-alert-warn ───────────────────────────────────────────────────────── */
.hub-alert-warn {
  background: var(--color-warning-bg);
  border: 1px solid var(--color-warning-border);
  color: var(--color-warning-text);
}

/* ── Responsive ───────────────────────────────────────────────────────────── */
@media (max-width: 1100px) {
  .kpi-strip { grid-template-columns: repeat(2, 1fr); }
  .hub-grid  { grid-template-columns: 1fr; }
}

@media (max-width: 680px) {
  .kpi-strip           { grid-template-columns: 1fr 1fr; }
  .posture-hero        { grid-template-columns: 1fr; }
  .posture-ring-wrap   { margin: 0 auto; }
  .deadline-banner     { flex-direction: column; align-items: flex-start; gap: 0.4rem; }
  .deadline-banner-center { flex-direction: row; gap: 0.4rem; align-items: baseline; }
}
</style>

<!-- Light-mode overrides — must be non-scoped to reach the [data-theme] root selector -->
<style>
/* Light mode page background uses the CRANE Dashboard reference token */
[data-theme="light"] .ops-hub-page {
  --ring-track: oklch(0.92 0.015 150);
}

/* Hub cards: drop explicit border in light mode; use shadow instead */
[data-theme="light"] .ops-hub-page .hub-card {
  border-color: transparent;
  box-shadow: 0 1px 3px rgba(0,0,0,0.06), 0 0 0 1px rgba(0,0,0,0.11);
}
[data-theme="light"] .ops-hub-page .hub-card-header {
  border-bottom-color: oklch(0.91 0.012 150);
}
[data-theme="light"] .ops-hub-page .hub-card.hub-card-alert {
  border-color: transparent;
  box-shadow: 0 1px 3px rgba(0,0,0,0.06), 0 0 0 1.5px rgba(200,95,95,0.45);
}

/* Posture hero shadow in light mode */
[data-theme="light"] .ops-hub-page .posture-hero {
  border-color: transparent;
  box-shadow: 0 2px 8px rgba(0,0,0,0.07), 0 0 0 1px rgba(0,0,0,0.11);
  background: #ffffff;
}
/* KPI cards */
[data-theme="light"] .ops-hub-page .kpi-card {
  border-color: transparent;
  box-shadow: 0 2px 6px rgba(0,0,0,0.08), 0 0 0 1px rgba(0,0,0,0.12);
}
[data-theme="light"] .ops-hub-page .kpi-card:hover {
  box-shadow: 0 2px 8px rgba(0,0,0,0.11), 0 0 0 2px oklch(0.48 0.092 150 / 0.35);
}
[data-theme="light"] .ops-hub-page .kpi-card.kpi-danger {
  box-shadow: 0 2px 6px rgba(0,0,0,0.08), 0 0 0 1.5px rgba(200,95,95,0.45);
}
[data-theme="light"] .ops-hub-page .kpi-card.kpi-warn {
  box-shadow: 0 2px 6px rgba(0,0,0,0.08), 0 0 0 1.5px rgba(183,155,18,0.45);
}

/* Release items, change cells, lifecycle cells */
[data-theme="light"] .ops-hub-page .release-item {
  border-color: transparent;
  box-shadow: 0 1px 3px rgba(0,0,0,0.06), 0 0 0 1px rgba(0,0,0,0.11);
}
[data-theme="light"] .ops-hub-page .release-item:hover {
  box-shadow: 0 1px 4px rgba(0,0,0,0.09), 0 0 0 1.5px oklch(0.48 0.092 150 / 0.4);
}
[data-theme="light"] .ops-hub-page .change-cell {
  border-color: transparent;
  box-shadow: 0 0 0 1px rgba(0,0,0,0.11);
}
[data-theme="light"] .ops-hub-page .change-cell.change-cell-warn {
  box-shadow: 0 0 0 1.5px rgba(183,155,18,0.45);
}
[data-theme="light"] .ops-hub-page .change-cell.change-cell-danger {
  box-shadow: 0 0 0 1.5px rgba(200,95,95,0.45);
}
[data-theme="light"] .ops-hub-page .lc-cell {
  border-color: transparent;
  box-shadow: 0 0 0 1px rgba(0,0,0,0.11);
}
[data-theme="light"] .ops-hub-page .lc-cell.lc-danger {
  box-shadow: 0 0 0 1.5px rgba(200,95,95,0.45);
}
[data-theme="light"] .ops-hub-page .lc-cell.lc-warn {
  box-shadow: 0 0 0 1.5px rgba(183,155,18,0.45);
}

/* Active state color in kpi-icon uses oklch green */
[data-theme="light"] .ops-hub-page .kpi-icon-neutral {
  background: oklch(0.955 0.024 150);
  color: oklch(0.38 0.092 150);
}
</style>
