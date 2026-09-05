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
  <section class="page declarations-page">
    <header class="page-header" data-guide="declarations-header">
      <div>
        <span class="eyebrow">Cyber Resilience Act · Article 28</span>
        <h1 class="page-title">Declarations of Conformity</h1>
        <p class="muted page-subtitle">
          Draw up and sign the EU Declaration of Conformity for each product release, and
          generate the matching package label.
        </p>
      </div>
      <AppButton variant="secondary" type="button" @click="startGuide"><span aria-hidden="true">?</span> Guide</AppButton>
    </header>

    <section class="panel" data-guide="declarations-list">
      <div class="panel-header">
        <div>
          <h2 class="section-title">Release declarations</h2>
          <p class="muted section-subtitle">{{ rows.length }} declaration{{ rows.length === 1 ? "" : "s" }} across all product releases</p>
        </div>
      </div>

      <div v-if="isLoading" class="empty-panel muted">Loading declarations…</div>

      <EmptyState
        v-else-if="rows.length === 0"
        title="No releases yet"
        description="Create a product release to draw up its Declaration of Conformity."
      />

      <div v-else class="table-wrapper">
      <table class="data-table">
        <thead>
          <tr>
            <th>Product</th>
            <th>Version</th>
            <th>DoC ref.</th>
            <th>Status</th>
            <th>Signatory</th>
            <th aria-label="Open declaration"></th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="row in rows"
            :key="row.release_id"
            class="table-row-clickable"
            tabindex="0"
            @click="openDeclaration(row.release_id)"
            @keydown.enter="openDeclaration(row.release_id)"
            @keydown.space.prevent="openDeclaration(row.release_id)"
          >
            <td>
              <div class="cell-primary">{{ row.product_name }}</div>
              <div class="product-code">{{ row.product_code }}</div>
            </td>
            <td>{{ row.version_label }}</td>
            <td>{{ row.doc_number ?? "—" }}</td>
            <td><StatusBadge :label="statusLabel(row.doc_status)" :variant="statusVariant(row.doc_status)" /></td>
            <td>{{ row.signatory ?? "—" }}</td>
            <td class="row-arrow" aria-hidden="true">›</td>
          </tr>
        </tbody>
      </table>
      </div>
    </section>
  </section>
</template>

<script setup lang="ts">
import { onMounted, ref } from "vue";
import { useRouter } from "vue-router";
import EmptyState from "@/components/EmptyState.vue";
import AppButton from "@/components/AppButton.vue";
import StatusBadge from "@/components/StatusBadge.vue";
import type { BadgeVariant } from "@/components/StatusBadge.vue";
import { useToast } from "@/composables/useToast";
import { euDeclarationService } from "@/services/eu-declaration-service";
import type { DeclarationSummary, DocStatus } from "@/types/declaration";

const { showToast } = useToast();
const router = useRouter();
function startGuide(): void { window.dispatchEvent(new Event("crane-guide-start")); }

const rows = ref<DeclarationSummary[]>([]);
const isLoading = ref(false);

function openDeclaration(releaseId: string): void {
  void router.push({ name: "release-declaration", params: { releaseId } });
}

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
.declarations-page { gap: var(--space-5); }
.page-title { margin: var(--space-1) 0 0; }
.page-subtitle, .section-subtitle { margin: var(--space-1) 0 0; }
.panel { background: linear-gradient(180deg, var(--color-card-start), var(--color-card-end)); border: 1px solid var(--color-border); border-radius: var(--radius-lg); padding: var(--space-5); box-shadow: var(--shadow-lg); }
.panel-header { display: flex; justify-content: space-between; align-items: center; gap: var(--space-4); margin-bottom: var(--space-4); }
.section-title { margin: 0; font-size: var(--text-xl); }
.empty-panel { padding: var(--space-8); text-align: center; }
.table-wrapper { overflow-x: auto; }
.data-table { width: 100%; min-width: 640px; border-collapse: collapse; }
.data-table th, .data-table td { padding: .8rem .75rem; border-top: 1px solid var(--color-divider); text-align: left; }
.data-table th { color: var(--color-text-muted); font-size: var(--text-xs); text-transform: uppercase; letter-spacing: .06em; }
.table-row-clickable { cursor: pointer; }
.table-row-clickable:hover, .table-row-clickable:focus-visible { background: var(--color-surface-soft); outline: none; }
.cell-primary { font-weight: 600; }
.product-code {
  font-family: monospace;
  font-size: var(--text-xs);
  color: var(--color-text-muted);
}
.row-arrow { width: 2rem; text-align: right !important; color: var(--color-text-muted); font-size: var(--text-xl); }
</style>
