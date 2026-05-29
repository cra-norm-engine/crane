<template>
  <button
    :type="type"
    :disabled="disabled"
    class="app-btn"
    :class="[`app-btn--${variant}`, `app-btn--${size}`]"
  >
    <slot />
  </button>
</template>

<script setup lang="ts">
withDefaults(
  defineProps<{
    /** Visual style of the button. */
    variant?: "primary" | "secondary" | "ghost" | "danger";
    /** Height / padding scale. */
    size?: "sm" | "md";
    /** Native button type attribute. */
    type?: "button" | "submit" | "reset";
    /** Disables the button and dims it. */
    disabled?: boolean;
  }>(),
  {
    variant: "secondary",
    size: "md",
    type: "button",
    disabled: false,
  },
);
</script>

<style scoped>
/* ── Base ────────────────────────────────────────── */
.app-btn {
  display: inline-flex;
  align-items: center;
  gap: 7px;
  border-radius: 6px;
  border: 1px solid var(--color-border);
  background: var(--color-surface);
  color: var(--color-text);
  font: 500 13px/1 inherit;
  cursor: pointer;
  white-space: nowrap;
  transition: background 0.12s, border-color 0.12s, opacity 0.12s;
  flex-shrink: 0;
}
.app-btn:focus-visible {
  outline: 2px solid var(--color-primary);
  outline-offset: 2px;
}

/* ── Sizes ───────────────────────────────────────── */
.app-btn--md { height: 34px; padding: 0 13px; font-size: 13px; }
.app-btn--sm { height: 28px; padding: 0 10px; font-size: 12.5px; gap: 5px; }

/* ── Variants ────────────────────────────────────── */

/* Secondary (default) — neutral surface */
.app-btn--secondary:hover { background: var(--color-surface-elevated); }

/* Primary — green */
.app-btn--primary {
  background: var(--color-primary);
  color: #fff;
  border-color: var(--color-primary);
}
.app-btn--primary:hover {
  background: var(--color-primary-2);
  border-color: var(--color-primary-2);
}

/* Ghost — no background, no border */
.app-btn--ghost {
  background: transparent;
  border-color: transparent;
  color: var(--color-text-muted);
}
.app-btn--ghost:hover {
  background: var(--color-surface-elevated);
  color: var(--color-text);
}

/* Danger */
.app-btn--danger {
  background: var(--color-danger-bg);
  color: var(--color-danger-text);
  border-color: var(--color-danger-border);
}
.app-btn--danger:hover { opacity: 0.85; }

/* ── Disabled ────────────────────────────────────── */
.app-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
  pointer-events: none;
}
</style>
