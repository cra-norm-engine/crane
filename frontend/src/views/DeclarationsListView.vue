<!--
  CRANE — CRA Norm Engine
  Copyright (C) 2026 Ali Mohammad Hosseini
  SPDX-License-Identifier: AGPL-3.0-or-later
  This file is part of CRANE, free software under the GNU AGPL v3.0 or later.
  See <https://www.gnu.org/licenses/>.
-->
<template>
  <!--
    DeclarationsListView — top-level page listing every release with its EU
    Declaration of Conformity status (CRA Art. 28). Each row links to the
    per-release DeclarationView where the DoC can be previewed, signed and
    downloaded.
  -->
  <section class="dl-page">
    <header class="dl-head">
      <div>
        <div class="dl-eyebrow">Cyber Resilience Act · Article 28</div>
        <h1 class="dl-title">Declarations of Conformity</h1>
        <p class="dl-sub">
          Draw up and sign the EU Declaration of Conformity for each product release, and
          generate the matching package label.
        </p>
      </div>
    </header>

    <div v-if="isLoading" class="dl-loading">Loading declarations…</div>

    <EmptyState
      v-else-if="rows.length === 0"
      title="No releases yet"
      description="Create a product release to draw up its Declaration of Conformity."
    />

    <div v-else class="dl-table-wrap">
      <table class="dl-table">
        <thead>
          <tr>
            <th>Product</th>
            <th>Version</th>
            <th>DoC ref.</th>
            <th>Status</th>
            <th>Signatory</th>
            <th class="right">Actions</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="row in rows" :key="row.release_id">
            <td>
              <div class="dl-pname">{{ row.product_name }}</div>
              <div class="dl-pcode">{{ row.product_code }}</div>
            </td>
            <td>{{ row.version_label }}</td>
            <td>{{ row.doc_number ?? "—" }}</td>
            <td><StatusBadge :label="statusLabel(row.doc_status)" :variant="statusVariant(row.doc_status)" /></td>
            <td>{{ row.signatory ?? "—" }}</td>
            <td class="right">
              <RouterLink
                class="dl-link"
                :to="{ name: 'release-declaration', params: { releaseId: row.release_id } }"
              >Open</RouterLink>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </section>
</template>

<script setup lang="ts">
import { onMounted, ref } from "vue";
import { RouterLink } from "vue-router";
import EmptyState from "@/components/EmptyState.vue";
import StatusBadge from "@/components/StatusBadge.vue";
import type { BadgeVariant } from "@/components/StatusBadge.vue";
import { useToast } from "@/composables/useToast";
import { euDeclarationService } from "@/services/eu-declaration-service";
import type { DeclarationSummary, DocStatus } from "@/types/declaration";

const { showToast } = useToast();

const rows = ref<DeclarationSummary[]>([]);
const isLoading = ref(false);

// Title-case the status for display.
function statusLabel(s: DocStatus): string {
  return s.charAt(0).toUpperCase() + s.slice(1);
}

// Map DoC status to a badge colour variant.
function statusVariant(s: DocStatus): BadgeVariant {
  switch (s) {
    case "signed":
      return "success";
    case "approved":
      return "info";
    default:
      return "neutral";
  }
}

async function load(): Promise<void> {
  isLoading.value = true;
  try {
    rows.value = await euDeclarationService.list();
  } catch {
    showToast({ type: "error", message: "Failed to load declarations." });
  } finally {
    isLoading.value = false;
  }
}

onMounted(load);
</script>

<style scoped>
.dl-page {
  max-width: 1100px;
  margin: 0 auto;
  padding: 24px 20px 60px;
}
.dl-eyebrow {
  font-family: monospace;
  font-size: 11px;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  color: var(--color-text-muted, #8b9290);
}
.dl-title {
  font-size: 24px;
  margin: 4px 0 4px;
}
.dl-sub {
  color: var(--color-text-muted, #5b6260);
  font-size: 14px;
  max-width: 640px;
  margin: 0 0 20px;
}
.dl-loading {
  color: var(--color-text-muted, #5b6260);
  padding: 40px 0;
}
.dl-table-wrap {
  overflow-x: auto;
  border: 1px solid var(--color-border, #e7e1d2);
  border-radius: 8px;
}
.dl-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 14px;
  min-width: 640px;
}
.dl-table th {
  text-align: left;
  font-family: monospace;
  font-size: 11px;
  letter-spacing: 0.05em;
  text-transform: uppercase;
  color: var(--color-text-muted, #8b9290);
  padding: 10px 14px;
  border-bottom: 1px solid var(--color-border, #dcd6c6);
  font-weight: 400;
  background: var(--color-surface-elevated);
}
.dl-table td {
  padding: 11px 14px;
  border-bottom: 1px solid var(--color-border, #efeadf);
  vertical-align: top;
}
.dl-table th.right,
.dl-table td.right {
  text-align: right;
}
.dl-pname {
  font-weight: 600;
}
.dl-pcode {
  font-family: monospace;
  font-size: 12px;
  color: var(--color-text-muted, #8b9290);
}
.dl-link {
  color: var(--color-primary);
  font-weight: 600;
  text-decoration: none;
}
.dl-link:hover {
  text-decoration: underline;
}
</style>
