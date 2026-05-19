<template>
  <div class="sbom-diff-panel">
    <div v-if="loading" class="diff-loading">
      <div class="spinner"></div>
      <p>Loading differential analysis…</p>
    </div>

    <div v-else-if="!diff" class="diff-empty-state">
      <p class="diff-empty-title">No differential analysis available</p>
      <p class="diff-empty-hint">
        A differential analysis is generated automatically when you upload a <strong>new display_version</strong>
        of the SBOM.
      </p>
    </div>

    <div v-else class="diff-content">
      <!-- Context note -->
      <p class="diff-context-note">
        <strong>Comparison:</strong> This diff compares the SBOM you are viewing against the record that existed
        before. Components are tagged by change type (added, removed, or modified).
      </p>

      <!-- Summary bar -->
      <div class="diff-summary-bar">
        <span class="diff-summary-chip diff-chip-added">+{{ diff.added.length }} added</span>
        <span class="diff-summary-chip diff-chip-removed">−{{ diff.removed.length }} removed</span>
        <span class="diff-summary-chip diff-chip-changed">~{{ diff.changed.length }} changed</span>
        <span class="diff-summary-note">compared to the previous SBOM</span>
      </div>

      <!-- Added components -->
      <div v-if="diff.added.length" class="diff-section">
        <h3 class="diff-section-title diff-added-title">Added components ({{ diff.added.length }})</h3>
        <ul class="diff-list">
          <li v-for="(c, i) in diff.added" :key="`added-${i}`" class="diff-item diff-item-added">
            {{ formatComponent(c) }}
          </li>
        </ul>
      </div>

      <!-- Removed components -->
      <div v-if="diff.removed.length" class="diff-section">
        <h3 class="diff-section-title diff-removed-title">Removed components ({{ diff.removed.length }})</h3>
        <ul class="diff-list">
          <li v-for="(c, i) in diff.removed" :key="`removed-${i}`" class="diff-item diff-item-removed">
            {{ formatComponent(c) }}
          </li>
        </ul>
      </div>

      <!-- Changed components -->
      <div v-if="diff.changed.length" class="diff-section">
        <h3 class="diff-section-title diff-changed-title">Changed components ({{ diff.changed.length }})</h3>
        <ul class="diff-list">
          <li v-for="(c, i) in diff.changed" :key="`changed-${i}`" class="diff-item diff-item-changed">
            {{ formatComponent(c) }}
          </li>
        </ul>
      </div>

      <!-- Empty state when no changes -->
      <div v-if="!diff.added.length && !diff.removed.length && !diff.changed.length" class="finding-none">
        <p>No component changes detected between this SBOM and the previous display_version.</p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { formatComponent, type SbomDiffData } from "@/utils/sbomDiff";

const props = withDefaults(defineProps<{
  diff: SbomDiffData | null;
  loading?: boolean;
}>(), {
  loading: false,
});
</script>

<style scoped>
.sbom-diff-panel {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

/* Loading state */
.diff-loading {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 0.75rem;
  padding: 2rem;
  color: var(--color-text-muted);
  text-align: center;
}

.spinner {
  width: 2rem;
  height: 2rem;
  border: 2px solid var(--color-border);
  border-top-color: var(--color-primary);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

/* Empty state */
.diff-empty-state {
  padding: 2rem;
  border-radius: 0.85rem;
  background: var(--color-surface-soft);
  text-align: center;
}

.diff-empty-title {
  margin: 0 0 0.5rem;
  font-weight: 600;
  color: var(--color-text);
}

.diff-empty-hint {
  margin: 0;
  font-size: 0.9rem;
  color: var(--color-text-muted);
  line-height: 1.5;
}

/* Content */
.diff-content {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.diff-context-note {
  margin: 0;
  padding: 0.75rem 1rem;
  border-left: 3px solid var(--color-border);
  background: var(--color-surface-soft);
  font-size: 0.9rem;
  color: var(--color-text);
  line-height: 1.5;
}

/* Summary bar */
.diff-summary-bar {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  flex-wrap: wrap;
  padding: 0.75rem;
  border-radius: 0.85rem;
  background: var(--color-surface-soft);
  border: 1px solid var(--color-inset-border);
}

.diff-summary-chip {
  display: inline-flex;
  align-items: center;
  padding: 0.35rem 0.75rem;
  border-radius: 999px;
  font-size: 0.85rem;
  font-weight: 600;
  white-space: nowrap;
}

.diff-chip-added {
  background: var(--color-emerald-bg);
  color: var(--color-emerald-text);
  border: 1px solid var(--color-emerald-border);
}

.diff-chip-removed {
  background: var(--color-danger-bg);
  color: var(--color-danger-text);
  border: 1px solid var(--color-danger-border);
}

.diff-chip-changed {
  background: var(--color-warning-bg);
  color: var(--color-warning-text);
  border: 1px solid var(--color-warning-border);
}

.diff-summary-note {
  font-size: 0.8rem;
  color: var(--color-text-muted);
  margin-left: auto;
}

/* Sections */
.diff-section {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.diff-section-title {
  margin: 0;
  font-size: 0.9rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.03em;
}

.diff-added-title {
  color: var(--color-emerald-text);
}

.diff-removed-title {
  color: var(--color-danger-text);
}

.diff-changed-title {
  color: var(--color-warning-text);
}

.diff-list {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.diff-item {
  padding: 0.4rem 0.75rem;
  border-radius: 0.5rem;
  font-size: 0.9rem;
  word-break: break-word;
}

.diff-item-added {
  background: rgba(16, 185, 129, 0.1);
  color: var(--color-emerald-text);
  border-left: 3px solid var(--color-emerald-text);
}

.diff-item-removed {
  background: rgba(239, 68, 68, 0.1);
  color: var(--color-danger-text);
  border-left: 3px solid var(--color-danger-text);
}

.diff-item-changed {
  background: rgba(245, 158, 11, 0.1);
  color: var(--color-warning-text);
  border-left: 3px solid var(--color-warning-text);
}

/* Empty finding state */
.finding-none {
  padding: 1rem;
  border-radius: 0.85rem;
  background: var(--color-surface-soft);
  text-align: center;
  color: var(--color-text-muted);
  font-size: 0.9rem;
}

.finding-none p {
  margin: 0;
}
</style>
