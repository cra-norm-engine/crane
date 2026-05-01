<template>
  <!--
    EmptyState — displayed when a list, table, or section has no data.

    Usage — minimal:
      <EmptyState
        title="No products found"
        description="Create your first product to get started."
      />

    Usage — with custom icon and action button:
      <EmptyState title="No results" description="…">
        <template #icon>
          <svg>…</svg>
        </template>
        <template #action>
          <button class="button" @click="openForm">Add product</button>
        </template>
      </EmptyState>

    The component renders as a centred block inside whatever card or
    container wraps it.  It does NOT provide its own card shell — the
    parent is responsible for that so sizing stays flexible.
  -->
  <div class="empty-state" :class="{ 'empty-state-compact': compact }">

    <!-- ── Icon area — either the named slot or the default placeholder ── -->
    <div class="empty-icon-wrap" aria-hidden="true">
      <slot name="icon">
        <!--
          Default icon: a dotted circle with an X, universally understood
          as "nothing here".  Replaced by parent via #icon slot when a
          more domain-specific icon is appropriate.
        -->
        <svg
          class="empty-icon-default"
          viewBox="0 0 48 48"
          fill="none"
          stroke="currentColor"
          stroke-width="1.5"
          stroke-linecap="round"
          stroke-linejoin="round"
          aria-hidden="true"
        >
          <!-- Outer dashed circle -->
          <circle cx="24" cy="24" r="20" stroke-dasharray="4 3" opacity="0.4" />
          <!-- Inner solid circle — subtle background fill -->
          <circle cx="24" cy="24" r="12" stroke-width="1" opacity="0.2" />
          <!-- Magnifier / search hint — indicates "nothing found" -->
          <circle cx="21" cy="21" r="6" stroke-width="1.6" opacity="0.55" />
          <line   x1="25.4" y1="25.4" x2="30" y2="30" stroke-width="1.8" opacity="0.55" />
        </svg>
      </slot>
    </div>

    <!-- ── Text block ──────────────────────────────────── -->
    <div class="empty-text">
      <h3 class="empty-title">{{ title }}</h3>
      <p v-if="description" class="empty-description">{{ description }}</p>
    </div>

    <!-- ── Optional action (e.g. "Create first product" button) ── -->
    <div v-if="$slots.action" class="empty-action">
      <slot name="action" />
    </div>

  </div>
</template>

<script setup lang="ts">
withDefaults(
  defineProps<{
    /** Primary heading — keep short, e.g. "No products found" */
    title: string;
    /** Secondary sentence that guides the user's next step */
    description?: string;
    /**
     * compact mode reduces padding and icon size.
     * Use inside table cells or tight card sections.
     */
    compact?: boolean;
  }>(),
  {
    description: "",
    compact: false,
  },
);
</script>

<style scoped>
/* ── Shell ────────────────────────────────────── */
.empty-state {
  /* Centre everything vertically and horizontally */
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 1rem;
  text-align: center;

  /* Generous padding so the state feels "present", not squeezed */
  padding: 3rem 2rem;

  /* Subtle dashed border to visually define the empty area */
  border: 1px dashed var(--color-inset-border-dashed);
  border-radius: var(--radius-lg);
  background: var(--color-inset-surface);

  /* Smooth appearance when the parent loads */
  animation: empty-fade-in 0.3s ease;
}

/* Compact variant — less padding, suitable for inline empty areas */
.empty-state-compact {
  padding: 1.5rem 1rem;
  gap: 0.65rem;
}

/* ── Icon wrapper ─────────────────────────────── */
.empty-icon-wrap {
  /* Circular tinted backdrop behind the icon */
  display: flex;
  align-items: center;
  justify-content: center;
  width: 72px;
  height: 72px;
  border-radius: 50%;
  background: var(--color-surface-elevated);
  border: 1px solid var(--color-border);
  color: var(--color-text-muted);
  flex-shrink: 0;
}

/* Compact variant — smaller icon circle */
.empty-state-compact .empty-icon-wrap {
  width: 48px;
  height: 48px;
}

/* Default placeholder icon sizing */
.empty-icon-default {
  width: 32px;
  height: 32px;
  color: var(--color-text-muted);
}

.empty-state-compact .empty-icon-default {
  width: 22px;
  height: 22px;
}

/* ── Text block ───────────────────────────────── */
.empty-text {
  display: flex;
  flex-direction: column;
  gap: 0.35rem;
  max-width: 320px; /* prevent lines from getting too wide to read */
}

.empty-title {
  margin: 0;
  font-size: var(--text-lg);
  font-weight: 700;
  color: var(--color-text);
  line-height: 1.3;
}

.empty-state-compact .empty-title {
  font-size: var(--text-base);
}

.empty-description {
  margin: 0;
  font-size: var(--text-sm);
  color: var(--color-text-muted);
  line-height: 1.55;
}

/* ── Action slot ──────────────────────────────── */
.empty-action {
  margin-top: 0.25rem;
}

/* ── Entry animation ──────────────────────────── */
@keyframes empty-fade-in {
  from {
    opacity: 0;
    transform: translateY(6px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}
</style>
