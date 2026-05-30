<template>
  <!--
    AppLogo — pure typography wordmark for CRANE.

    Split: "CRA" in brand green · "NE" in a secondary accent.
    Below the wordmark: "Conformity by design" motto in small caps.

    Prop `on-dark` forces white/light palette for always-dark surfaces.
    Prop `compact`  hides the motto row (e.g. collapsed sidebar).
    Prop `scale`    multiplies all sizes proportionally.
  -->
  <div class="crane-logo" :class="onDark && 'crane-logo--on-dark'" :style="sizeVars">

    <!-- Wordmark row: CRA · NE -->
    <div class="logo-wordmark">
      <span class="logo-cra">CRA</span><span class="logo-ne">NE</span>
    </div>

    <!-- Motto -->
    <div v-if="!compact" class="logo-motto">Conformity by design</div>

  </div>
</template>

<script setup lang="ts">
import { computed } from "vue";

const props = withDefaults(defineProps<{
  /** Force light text — use on permanently dark surfaces. */
  onDark?: boolean;
  /** Hide the motto row (e.g. collapsed sidebar). */
  compact?: boolean;
  /** Scale factor relative to the base size (default 1). */
  scale?: number;
}>(), {
  onDark: false,
  compact: false,
  scale: 1,
});

const sizeVars = computed(() => ({
  "--logo-scale": props.scale,
}));
</script>

<style scoped>
.crane-logo {
  display: inline-flex;
  flex-direction: column;
  gap: calc(4px * var(--logo-scale, 1));
  line-height: 1;
  user-select: none;
}

/* ── Wordmark ────────────────────────────────── */
.logo-wordmark {
  font-family: system-ui, -apple-system, "Inter", "Segoe UI", Helvetica, Arial, sans-serif;
  font-size: calc(22px * var(--logo-scale, 1));
  font-weight: 800;
  letter-spacing: 0.14em;
  line-height: 1;
}

/* "CRA" — brand green, surface the acronym */
.logo-cra {
  color: var(--color-primary);
}

/* "NE" — lighter accent to contrast with CRA */
.logo-ne {
  color: var(--color-primary-2);
}

/* ── Motto ───────────────────────────────────── */
.logo-motto {
  font-family: system-ui, -apple-system, "Inter", "Segoe UI", Helvetica, Arial, sans-serif;
  font-size: calc(8.5px * var(--logo-scale, 1));
  font-weight: 500;
  letter-spacing: 0.18em;
  text-transform: uppercase;
  color: var(--color-text-muted);
}

/* ── on-dark override ────────────────────────── */
.crane-logo--on-dark .logo-ne {
  color: oklch(0.82 0.14 145);
}
.crane-logo--on-dark .logo-motto {
  color: oklch(0.68 0.04 150);
}
</style>
