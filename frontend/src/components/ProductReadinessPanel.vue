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
    <div v-if="loading" class="readiness-empty">Calculating readiness…</div>
    <div v-else-if="!products.length" class="readiness-empty">No products yet.</div>

    <div v-else class="readiness-groups">
      <article v-for="product in products" :key="product.product_id" class="product-group">
        <header class="product-head">
          <div class="product-identity">
            <strong>{{ product.name }}</strong>
            <span>{{ product.product_code }}</span>
          </div>
          <div class="product-badges">
            <span class="scope-badge" :class="'scope-' + product.scope_status">{{ formatScope(product.scope_status) }}</span>
            <span v-if="product.is_conformant" class="conformant-badge">Conformant</span>
          </div>
        </header>

        <p v-if="!product.releases.length" class="readiness-empty compact">No releases yet.</p>
        <div v-else class="release-list">
          <button
            v-for="rel in product.releases"
            :key="rel.release_id"
            type="button"
            class="release-row"
            :class="{ representative: rel.release_id === product.representative_release_id }"
            @click="$emit('select', product.product_id, rel.release_id)"
          >
            <span class="release-identity">
              <strong>{{ rel.version_label }}</strong>
              <span>{{ formatReleaseStatus(rel.release_status) }}</span>
            </span>

            <span class="release-progress">
              <span class="progress-meta">
                <span>Readiness</span>
                <span>{{ rel.coverage.met }} / {{ rel.coverage.total }}</span>
              </span>
              <span class="progress-track">
                <span class="progress-fill" :class="readinessTone(rel)" :style="{ width: rel.coverage.met_pct + '%' }" />
              </span>
            </span>

            <strong class="release-percent">{{ rel.coverage.met_pct }}%</strong>
            <span class="approval-badge" :class="{ approved: rel.is_approved }">
              {{ rel.is_approved ? "Approved" : "Open" }}
            </span>
            <svg class="release-chevron" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><path d="M9 6l6 6-6 6"/></svg>
          </button>
        </div>
      </article>
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

function readinessTone(rel: ReleaseReadinessRead): string {
  if (rel.coverage.met_pct >= 80) return "tone-good";
  if (rel.coverage.met_pct >= 40) return "tone-progress";
  return "tone-low";
}

function formatScope(scope: string): string {
  switch (scope) {
    case "in_scope":     return "In scope";
    case "out_of_scope": return "Out of scope";
    default:             return "Undecided";
  }
}

function formatReleaseStatus(status: string): string {
  return status.replace(/_/g, " ").replace(/\b\w/g, (letter) => letter.toUpperCase());
}
</script>

<style scoped>
.readiness-panel {
  padding: 0.25rem;
}

.readiness-groups {
  display: grid;
  gap: 0.75rem;
}

.product-group {
  overflow: hidden;
  border: 1px solid var(--color-border);
  border-radius: 12px;
  background: var(--color-surface);
}

.product-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  padding: 0.85rem 1rem;
  border-bottom: 1px solid var(--color-border);
  background: var(--color-surface-elevated);
}

.product-identity {
  display: flex;
  min-width: 0;
  flex-direction: column;
  gap: 0.15rem;
}

.product-identity strong {
  overflow: hidden;
  color: var(--color-text);
  font-size: var(--text-sm);
  text-overflow: ellipsis;
  white-space: nowrap;
}

.product-identity span {
  color: var(--color-text-muted);
  font-size: var(--text-xs);
}

.product-badges {
  display: flex;
  flex-shrink: 0;
  gap: 0.4rem;
}

.scope-badge,
.conformant-badge,
.approval-badge {
  padding: 0.25rem 0.55rem;
  border: 1px solid var(--color-border);
  border-radius: 999px;
  color: var(--color-text-muted);
  font-size: var(--text-xs);
  font-weight: 700;
}

.scope-in_scope,
.conformant-badge,
.approval-badge.approved {
  border-color: color-mix(in srgb, var(--color-success) 35%, var(--color-border));
  background: color-mix(in srgb, var(--color-success) 10%, transparent);
  color: var(--color-success-text);
}

.release-list {
  display: flex;
  flex-direction: column;
}

.release-row {
  display: grid;
  grid-template-columns: minmax(130px, 0.8fr) minmax(180px, 1.4fr) 3.5rem auto 1rem;
  align-items: center;
  gap: 1rem;
  width: 100%;
  padding: 0.8rem 1rem;
  border: 0;
  border-bottom: 1px solid var(--color-border);
  background: transparent;
  color: inherit;
  cursor: pointer;
  text-align: left;
  transition: background var(--t-fast, 120ms);
}

.release-row:last-child {
  border-bottom: 0;
}

.release-row:hover,
.release-row:focus-visible {
  background: color-mix(in srgb, var(--color-primary) 7%, transparent);
}

.release-row:focus-visible {
  outline: 2px solid var(--color-primary);
  outline-offset: -2px;
}

.release-row.representative .release-identity strong::after {
  content: "Current";
  margin-left: 0.45rem;
  color: var(--color-primary);
  font-size: var(--text-xs);
  font-weight: 700;
}

.release-identity,
.release-progress {
  display: flex;
  min-width: 0;
  flex-direction: column;
}

.release-identity {
  gap: 0.2rem;
}

.release-identity strong {
  overflow: hidden;
  font-size: var(--text-sm);
  text-overflow: ellipsis;
  white-space: nowrap;
}

.release-identity span,
.progress-meta {
  color: var(--color-text-muted);
  font-size: var(--text-xs);
}

.release-progress {
  gap: 0.4rem;
}

.progress-meta {
  display: flex;
  justify-content: space-between;
}

.progress-track {
  height: 7px;
  overflow: hidden;
  border-radius: 999px;
  background: var(--color-surface-elevated-strong, var(--color-border));
}

.progress-fill {
  display: block;
  height: 100%;
  border-radius: inherit;
  transition: width 0.3s ease;
}

.tone-good { background: var(--color-success); }
.tone-progress { background: var(--color-warning); }
.tone-low { background: var(--color-danger); }

.release-percent {
  font-size: var(--text-sm);
  text-align: right;
}

.release-chevron {
  width: 1rem;
  color: var(--color-text-muted);
}

.readiness-empty {
  padding: 1.25rem;
  color: var(--color-text-muted);
  text-align: center;
}

.readiness-empty.compact {
  margin: 0;
  padding: 1rem;
}

@media (max-width: 720px) {
  .release-row {
    grid-template-columns: minmax(0, 1fr) auto 1rem;
    gap: 0.6rem;
  }

  .release-progress {
    grid-column: 1 / -1;
    grid-row: 2;
  }

  .release-percent {
    grid-column: 2;
    grid-row: 1;
  }

  .approval-badge {
    display: none;
  }

  .release-chevron {
    grid-column: 3;
    grid-row: 1;
  }
}

@media (max-width: 480px) {
  .product-head {
    align-items: flex-start;
    flex-direction: column;
  }
}
</style>
