<!--
  CRANE — CRA Norm Engine
  Copyright (C) 2026 Ali Mohammad Hosseini
  SPDX-License-Identifier: AGPL-3.0-or-later
  This file is part of CRANE, free software under the GNU AGPL v3.0 or later.
  See <https://www.gnu.org/licenses/>.

  Compliance readiness by RELEASE, grouped under each product. Readiness is a
  per-release property — each release has its own Annex I Part I coverage and its
  own approval — so every release gets its own row. Met % = requirements fully
  finalized; Assessed % = applicability decided. A release is "conformant" when
  its requirement assessment is approved. Used on the CRA requirements page;
  clicking a release loads its matrix.
-->
<template>
  <div class="readiness-panel">
    <div class="readiness-head">
      <h2 class="rp-title">Readiness by release</h2>
      <span class="rp-hint">Met % of Annex I Part I requirements · click a release to open it</span>
      <span class="rp-legend">
        <span class="rp-lg"><span class="rr-dot dot-onmarket"></span>On market</span>
        <span class="rp-lg"><span class="rr-dot dot-internal"></span>Not on market</span>
      </span>
    </div>

    <div v-if="loading" class="readiness-empty">Calculating…</div>
    <div v-else-if="!products.length" class="readiness-empty">
      No products yet.
    </div>

    <div v-else class="readiness-groups">
      <section v-for="product in products" :key="product.product_id" class="rg-group">
        <!-- Product header (compact) -->
        <div class="rg-head">
          <span class="rg-name">{{ product.name }}</span>
          <span class="rg-scope" :class="`scope-${product.scope_status}`">{{ formatScope(product.scope_status) }}</span>
          <span v-if="product.is_conformant" class="rg-conformant" title="Latest released version is approved">✓</span>
          <!-- one muted dot per active secondary flag, detail on hover -->
          <span
            v-if="hasFlags(product)"
            class="rg-flagdot"
            :title="flagSummary(product)"
          >⚠ {{ flagCount(product) }}</span>
        </div>

        <!-- Per-release rows: one compact line each -->
        <div v-if="!product.releases.length" class="rg-norel">No releases yet.</div>
        <ul v-else class="release-list">
          <li
            v-for="rel in product.releases"
            :key="rel.release_id"
            class="release-row"
            :class="{ 'is-representative': rel.release_id === product.representative_release_id }"
            tabindex="0"
            role="button"
            :title="`${rel.coverage.met}/${rel.coverage.total} met · ${rel.coverage.assessed}/${rel.coverage.total} assessed`"
            @click="$emit('select', product.product_id, rel.release_id)"
            @keydown.enter="$emit('select', product.product_id, rel.release_id)"
          >
            <span class="rr-version">{{ rel.version_label }}</span>
            <span class="rr-dot" :class="rel.is_released ? 'dot-onmarket' : 'dot-internal'" :title="formatReleaseStatus(rel.release_status)"></span>

            <div class="rr-bar">
              <div class="rr-bar-met" :style="{ width: rel.coverage.met_pct + '%', background: barColor(rel) }"></div>
            </div>
            <span class="rr-pct" :style="{ color: barColor(rel) }">{{ rel.coverage.met_pct }}%</span>

            <span v-if="rel.is_approved" class="rr-approved" title="Assessment approved">✓</span>
            <svg class="rr-chev" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M9 6l6 6-6 6"/></svg>
          </li>
        </ul>
      </section>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from "vue";

import { dashboardService } from "@/services/dashboard-service";
import type { ProductReadinessRead, ReleaseReadinessRead } from "@/types/dashboard";

defineEmits<{ (e: "select", productId: string, releaseId: string): void }>();

const products = ref<ProductReadinessRead[]>([]);
const loading = ref(false);

async function load(): Promise<void> {
  loading.value = true;
  try {
    products.value = await dashboardService.getProductReadiness();
  } catch {
    products.value = [];
  } finally {
    loading.value = false;
  }
}
onMounted(load);
defineExpose({ reload: load });

/** Bar fill colour driven by a release's Met %. */
function barColor(rel: ReleaseReadinessRead): string {
  const pct = rel.coverage.met_pct;
  if (pct >= 80) return "oklch(0.48 0.092 150)";
  if (pct >= 40) return "oklch(0.74 0.135 75)";
  return "oklch(0.58 0.175 25)";
}

function formatScope(scope: string): string {
  switch (scope) {
    case "in_scope":     return "In scope";
    case "out_of_scope": return "Out of scope";
    default:             return "Undecided";
  }
}

function formatReleaseStatus(status: string): string {
  return status.replace(/_/g, " ");
}

// ── Secondary flags collapsed to a single hover-summary chip ──
function flagCount(p: ProductReadinessRead): number {
  return (
    (p.has_open_critical_vuln ? 1 : 0) +
    (p.risk_unapproved ? 1 : 0) +
    (p.support_expired ? 1 : 0) +
    (p.change_action_required ? 1 : 0)
  );
}
function hasFlags(p: ProductReadinessRead): boolean {
  return flagCount(p) > 0;
}
function flagSummary(p: ProductReadinessRead): string {
  const parts: string[] = [];
  if (p.has_open_critical_vuln) parts.push(`${p.open_critical_vuln_count} critical vuln`);
  if (p.risk_unapproved) parts.push("risk unapproved");
  if (p.support_expired) parts.push("support expired");
  if (p.change_action_required) parts.push("change action required");
  return parts.join(" · ");
}
</script>

<style scoped>
.readiness-panel {
  padding: 0.9rem 1rem;
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: 12px;
}
.readiness-head {
  display: flex; align-items: baseline; gap: 0.6rem; flex-wrap: wrap;
  margin-bottom: 0.6rem;
}
.rp-title { margin: 0; font-size: 0.9rem; font-weight: 700; color: var(--color-text); }
.rp-hint { font-size: 0.7rem; color: var(--color-text-muted); }
.rp-legend { display: inline-flex; gap: 0.75rem; margin-left: auto; }
.rp-lg { display: inline-flex; align-items: center; gap: 5px; font-size: 0.66rem; color: var(--color-text-muted); }

.readiness-empty { padding: 0.9rem; text-align: center; color: var(--color-text-muted); font-size: 0.8rem; }

.readiness-groups { display: flex; flex-direction: column; }

/* Product group — a labelled block, no heavy borders */
.rg-group { padding: 0.35rem 0; border-top: 1px solid var(--color-border); }
.rg-group:first-child { border-top: none; }
.rg-head {
  display: flex; align-items: center; gap: 0.4rem;
  padding: 0.15rem 0.25rem;
}
.rg-name { font-size: 0.78rem; font-weight: 600; color: var(--color-text); }
.rg-scope { font-size: 0.58rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.04em; color: var(--color-text-muted); }
.scope-in_scope { color: var(--color-success-text); }
.rg-conformant { font-size: 0.68rem; font-weight: 700; color: var(--color-success-text); }
.rg-flagdot { margin-left: auto; font-size: 0.62rem; font-weight: 600; color: var(--color-warning-text); cursor: help; }

.rg-norel { padding: 0.2rem 0.5rem; font-size: 0.7rem; color: var(--color-text-muted); }

/* Compact single-line release rows */
.release-list { list-style: none; margin: 0; padding: 0; }
.release-row {
  display: grid;
  grid-template-columns: minmax(56px, auto) 6px 90px 30px 10px 10px;
  align-items: center;
  gap: 0.4rem;
  padding: 0.12rem 0.4rem;
  border-radius: 5px;
  cursor: pointer;
  transition: background 0.1s;
}
.release-row:hover { background: var(--color-surface-elevated); }
.release-row:focus-visible { outline: 2px solid var(--color-primary); outline-offset: -2px; }
.release-row.is-representative .rr-version { font-weight: 700; }

.rr-version { font-size: 0.7rem; color: var(--color-text); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.rr-dot { width: 6px; height: 6px; border-radius: 50%; }
.dot-onmarket { background: var(--color-success); }
.dot-internal { background: var(--color-border-strong, #c9d2cc); }

/* Thin progress bar — fixed narrow width. The track uses a real theme token so
   it stays visible against the white surface in light mode. A hairline border
   keeps a 0% bar legible as a control. */
.rr-bar {
  height: 4px;
  background: var(--color-surface-elevated-strong, #e2e8e4);
  border: 1px solid var(--color-border);
  border-radius: 999px;
  overflow: hidden;
}
.rr-bar-met { height: 100%; border-radius: 999px; transition: width 0.5s ease; }

.rr-pct { font-size: 0.64rem; font-weight: 700; font-family: 'JetBrains Mono', monospace; text-align: right; }
.rr-approved { font-size: 0.66rem; font-weight: 700; color: var(--color-success-text); text-align: center; }
.rr-chev { width: 10px; height: 10px; color: var(--color-text-muted); opacity: 0; }
.release-row:hover .rr-chev { opacity: 1; }
</style>
