<template>
  <!--
    StatusBadge — semantic inline pill for status labels.

    Usage:
      <StatusBadge label="In scope"   variant="success" />
      <StatusBadge label="Critical"   variant="danger"  />
      <StatusBadge label="Undecided"  variant="neutral" />
      <StatusBadge label="Draft"      variant="info"    />

    Variants map to the global badge-* classes defined in styles.css
    so colours are automatically correct in both dark and light themes.
  -->
  <span
    class="badge"
    :class="variantClass"
    :aria-label="ariaLabel ?? label"
  >{{ label }}</span>
</template>

<script setup lang="ts">
import { computed } from "vue";

/* ── Prop types ──────────────────────────────────────── */

/**
 * All semantic colour variants available for the badge.
 * Maps 1-to-1 with the global .badge-* CSS classes in styles.css.
 */
export type BadgeVariant =
  | "neutral"   // grey  — undecided / unknown
  | "success"   // green — active / approved / in-scope
  | "warning"   // amber — approaching deadline / moderate risk
  | "danger"    // red   — expired / critical / out-of-scope
  | "info"      // blue  — informational
  | "primary"   // lime  — brand highlight
  | "purple"    // violet — special classification
  | "emerald";  // teal  — extended / consolidated support

const props = withDefaults(
  defineProps<{
    /** Visible text rendered inside the badge */
    label: string;
    /**
     * Semantic colour variant.
     * Defaults to "neutral" so the badge is always legible
     * even when a variant is not explicitly provided.
     */
    variant?: BadgeVariant;
    /**
     * Optional accessible label override.
     * If omitted, the badge text (label) is used for screen readers.
     */
    ariaLabel?: string;
  }>(),
  {
    variant: "neutral",
    ariaLabel: undefined,
  },
);

/* Derive the CSS modifier class from the variant prop */
const variantClass = computed(() => `badge-${props.variant}`);
</script>
