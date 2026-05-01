<template>
  <!--
    AppSpinner — accessible loading indicator.

    Usage:
      <!-- default medium size -->
      <AppSpinner />

      <!-- small, for use inside buttons -->
      <AppSpinner size="sm" />

      <!-- large, for full-section loading states -->
      <AppSpinner size="lg" label="Loading products…" />

      <!-- centred in a container -->
      <div class="spinner-center">
        <AppSpinner size="lg" />
        <span class="muted">Loading…</span>
      </div>

    Accessibility:
    • role="status" broadcasts loading state to screen readers.
    • aria-label provides the audible description.
    • The visual ring is aria-hidden so the label text is not duplicated.
  -->
  <span
    class="spinner-wrap"
    role="status"
    :aria-label="label"
  >
    <!-- Rotating ring — purely visual, hidden from assistive technology -->
    <span
      class="spinner"
      :class="`spinner-${size}`"
      aria-hidden="true"
    />

    <!--
      Visually hidden label text — read by screen readers but not
      visible on screen (uses the global .sr-only utility class).
    -->
    <span class="sr-only">{{ label }}</span>
  </span>
</template>

<script setup lang="ts">
/**
 * AppSpinner — thin rotating ring that signals an async operation.
 *
 * The spinner uses the global `.spinner` / `.spinner-{size}` classes
 * and the `@keyframes crane-spin` animation defined in styles.css.
 */
withDefaults(
  defineProps<{
    /**
     * Visual size of the spinner ring:
     *   sm — 1 rem   (inside buttons, compact cells)
     *   md — 1.5 rem (default; general loading states)
     *   lg — 2.25 rem (section-level / full-card loaders)
     */
    size?: "sm" | "md" | "lg";
    /**
     * Accessible description announced to screen readers.
     * Override with a more specific message when context allows,
     * e.g. "Loading products…" or "Saving changes…".
     */
    label?: string;
  }>(),
  {
    size: "md",
    label: "Loading…",
  },
);
</script>

<style scoped>
/*
  .spinner-wrap keeps the role="status" element as inline-flex
  so it can be dropped anywhere without disrupting document flow.
  The actual ring animation lives in styles.css under .spinner.
*/
.spinner-wrap {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  vertical-align: middle;
  flex-shrink: 0;
}
</style>
