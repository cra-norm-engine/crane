<template>
  <!--
    AppHeader — the sticky top bar inside the main content column.

    Responsibilities:
    • Desktop: greet the user by first name, surface the theme toggle.
    • Mobile: show a hamburger button that triggers sidebar overlay;
               the greeting is hidden to save vertical space.

    The "Sign out" action lives in the AppSidebar footer so it is
    always reachable — we intentionally do not duplicate it here.
  -->
  <header class="topbar" role="banner">

    <!-- ── Left side ──────────────────────────────────── -->
    <div class="topbar-left">

      <!-- Hamburger — only rendered on mobile (hidden via CSS on desktop) -->
      <button
        class="hamburger"
        type="button"
        aria-label="Open navigation menu"
        @click="$emit('toggle-sidebar')"
      >
        <!-- Three-line "hamburger" icon drawn with inline SVG -->
        <svg
          class="hamburger-icon"
          viewBox="0 0 20 20"
          fill="none"
          stroke="currentColor"
          stroke-width="1.8"
          stroke-linecap="round"
          aria-hidden="true"
        >
          <line x1="3" y1="5"  x2="17" y2="5"  />
          <line x1="3" y1="10" x2="17" y2="10" />
          <line x1="3" y1="15" x2="17" y2="15" />
        </svg>
      </button>

      <!-- Greeting — visible only on desktop where there is space -->
      <div class="topbar-greeting" aria-label="Greeting">
        {{ greeting }}, <strong>{{ firstName }}</strong>
      </div>

    </div>

    <!-- ── Right side ─────────────────────────────────── -->
    <div class="topbar-right">

      <!--
        Theme toggle — pill-shaped track with a sliding thumb.
        Uses a hidden checkbox so the :checked state drives the CSS.
      -->
      <label
        class="theme-switch"
        :aria-label="`Switch to ${isLightMode ? 'dark' : 'light'} mode`"
      >
        <input
          :checked="isLightMode"
          type="checkbox"
          class="theme-switch-input"
          @change="appStore.toggleTheme()"
        />
        <span class="theme-switch-track">
          <!-- Dark label (left slot) -->
          <span class="theme-switch-label theme-switch-label-dark">Dark</span>
          <!-- Sliding thumb that moves from left to right when checked -->
          <span class="theme-switch-thumb" aria-hidden="true" />
          <!-- Light label (right slot) -->
          <span class="theme-switch-label theme-switch-label-light">Light</span>
        </span>
      </label>

    </div>

  </header>
</template>

<script setup lang="ts">
import { computed } from "vue";

import { useAppStore } from "@/stores/app";
import { useAuthStore } from "@/stores/auth";

/* ── Stores ──────────────────────────────────────────── */
const appStore  = useAppStore();
const authStore = useAuthStore();

/* ── Emitted events ──────────────────────────────────── */
/* Parent (AppLayout) listens to this to toggle the sidebar overlay */
defineEmits<{
  "toggle-sidebar": [];
}>();

/* ── Computed properties ─────────────────────────────── */

/* true when the user has explicitly chosen the light theme */
const isLightMode = computed(() => appStore.themeMode === "light");

/* Extract only the first segment (name or local email part) for brevity */
const firstName = computed(() => {
  const full = authStore.userFullName || authStore.userEmail || "there";
  return full.split(/[\s@]/)[0] ?? "there";
});

/* Time-of-day greeting so the UI feels personal */
const greeting = computed(() => {
  const h = new Date().getHours();
  if (h < 12) return "Good morning";
  if (h < 17) return "Good afternoon";
  return "Good evening";
});
</script>

<style scoped>
/* ── Topbar shell ─────────────────────────────── */
.topbar {
  /* Sits on top of the scrollable page content */
  position: sticky;
  top: 0;
  z-index: 10;

  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;

  padding: 0.75rem 1.5rem;
  border-bottom: 1px solid var(--color-border);
  background: var(--color-header-bg);
  backdrop-filter: blur(16px);
  -webkit-backdrop-filter: blur(16px);

  /* Smooth transition when switching themes */
  transition: background var(--t-base), border-color var(--t-base);
}

/* ── Left cluster ─────────────────────────────── */
.topbar-left {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  min-width: 0; /* prevent flex blowout */
}

/* ── Greeting text ────────────────────────────── */
.topbar-greeting {
  font-size: 0.9rem;
  font-weight: 500;
  color: var(--color-text-muted);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.topbar-greeting strong {
  color: var(--color-text);
  font-weight: 700;
}

/* ── Right cluster ────────────────────────────── */
.topbar-right {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  flex-shrink: 0;
}

/* ── Hamburger button — mobile only ───────────── */
.hamburger {
  /* Hidden on desktop; shown on mobile via the media query below */
  display: none;
  align-items: center;
  justify-content: center;
  width: 2.2rem;
  height: 2.2rem;
  border-radius: var(--radius-md);
  border: 1px solid var(--color-border);
  background: var(--color-surface-soft);
  color: var(--color-text-muted);
  cursor: pointer;
  flex-shrink: 0;
  transition: background var(--t-fast), color var(--t-fast), border-color var(--t-fast);
}

.hamburger:hover {
  background: var(--color-surface-elevated);
  color: var(--color-text);
  border-color: var(--color-border-strong);
}

.hamburger-icon {
  width: 18px;
  height: 18px;
}

/* ── Theme toggle ─────────────────────────────── */
.theme-switch {
  display: inline-flex;
  align-items: center;
  cursor: pointer;
  /* Prevent the label from accidentally receiving accidental clicks
     from sibling text nodes */
  user-select: none;
}

/* The actual checkbox is visually hidden but remains accessible */
.theme-switch-input {
  position: absolute;
  opacity: 0;
  pointer-events: none;
  width: 0;
  height: 0;
}

/* Pill-shaped track that contains the two labels and the sliding thumb */
.theme-switch-track {
  position: relative;
  display: inline-grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  align-items: center;
  min-width: 122px;
  padding: 0.25rem;
  border-radius: 999px;
  border: 1px solid var(--color-border);
  background: var(--color-surface-soft);
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.04);
  transition: border-color var(--t-base);
}

/* Text labels inside the track */
.theme-switch-label {
  position: relative;
  z-index: 1;           /* sits above the sliding thumb */
  text-align: center;
  font-size: 0.7rem;
  font-weight: 700;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  color: var(--color-text-muted);
  padding: 0.28rem 0.5rem;
  transition: color var(--t-base);
  pointer-events: none; /* clicks pass through to the label element */
}

/* Sliding thumb — animates left ↔ right using translateX */
.theme-switch-thumb {
  position: absolute;
  top: 0.22rem;
  bottom: 0.22rem;
  left: 0.22rem;
  width: calc(50% - 0.22rem);
  border-radius: 999px;
  background: linear-gradient(135deg, rgba(175, 214, 46, 0.95), rgba(28, 107, 39, 0.95));
  box-shadow: 0 6px 18px rgba(28, 107, 39, 0.24);
  transition: transform 0.22s cubic-bezier(0.4, 0, 0.2, 1);
  pointer-events: none;
}

/* Move the thumb to the right slot when the checkbox is checked (light mode) */
.theme-switch-input:checked + .theme-switch-track .theme-switch-thumb {
  transform: translateX(100%);
}

/* Whichever label is "active" gets white text for contrast on the thumb */
.theme-switch-input:not(:checked) + .theme-switch-track .theme-switch-label-dark,
.theme-switch-input:checked     + .theme-switch-track .theme-switch-label-light {
  color: #fff;
}

/* ── Responsive ───────────────────────────────── */
@media (max-width: 960px) {
  /* Show the hamburger on mobile */
  .hamburger {
    display: inline-flex;
  }

  /* Hide the greeting to save space on small screens — the sidebar footer
     already shows the user's name */
  .topbar-greeting {
    display: none;
  }
}
</style>
