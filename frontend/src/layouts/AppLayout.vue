<template>
  <!--
    AppLayout — the root shell for all authenticated views.

    Layout model (desktop):
      ┌──────────────┬──────────────────────────┐
      │  AppSidebar  │  AppHeader (sticky top)  │
      │  (sticky)    │  ─────────────────────── │
      │              │  <router-view>            │
      └──────────────┴──────────────────────────┘

    On mobile (<= 960 px) the sidebar is off-screen and slides in
    as a fixed overlay when the hamburger button in AppHeader is
    tapped.  A semi-transparent backdrop sits between the overlay
    and the main content, and clicking it closes the sidebar.
  -->
  <div class="app-shell">

    <!-- ── Mobile backdrop — closes the sidebar when clicked ── -->
    <Transition name="backdrop">
      <div
        v-if="sidebarOpen"
        class="mobile-backdrop"
        aria-hidden="true"
        @click="sidebarOpen = false"
      />
    </Transition>

    <!-- ── Sidebar — always visible on desktop, overlay on mobile ── -->
    <AppSidebar
      :open="sidebarOpen"
      @close="sidebarOpen = false"
    />

    <!-- ── Main column: header + page content ── -->
    <div class="app-main">
      <!-- AppHeader emits 'toggle-sidebar' when the hamburger is clicked -->
      <AppHeader @toggle-sidebar="sidebarOpen = !sidebarOpen" />

      <main class="app-content">
        <router-view />
      </main>
    </div>

  </div>
</template>

<script setup lang="ts">
import { ref } from "vue";

import AppHeader from "@/components/AppHeader.vue";
import AppSidebar from "@/components/AppSidebar.vue";

/* Tracks whether the sidebar overlay is open on mobile.
   On desktop this value is irrelevant — the sidebar is
   always visible via CSS. */
const sidebarOpen = ref(false);
</script>

<style scoped>
/* ── Shell grid ───────────────────────────────── */
.app-shell {
  min-height: 100vh;
  display: grid;
  /* The var is defined in styles.css so both layout and sidebar stay in sync */
  grid-template-columns: var(--sidebar-width) minmax(0, 1fr);
  background: transparent;
  position: relative; /* needed for the fixed backdrop stacking context */
}

/* ── Right-hand column ────────────────────────── */
.app-main {
  min-width: 0;      /* prevents grid blowout from long content */
  display: flex;
  flex-direction: column;
}

/* ── Page content area ────────────────────────── */
.app-content {
  padding: 1.75rem 2rem;
  flex: 1;           /* fills remaining vertical space */
}

/* ── Mobile backdrop ──────────────────────────── */
/* Hidden by default; shown only when sidebar is open on mobile */
.mobile-backdrop {
  display: none;     /* block only inside the mobile media query */
  position: fixed;
  inset: 0;
  z-index: 40;       /* sits above content but below the sidebar (z-index 50) */
  background: var(--color-modal-backdrop);
  backdrop-filter: blur(4px);
}

/* Fade the backdrop in/out smoothly */
.backdrop-enter-active,
.backdrop-leave-active {
  transition: opacity 0.22s ease;
}

.backdrop-enter-from,
.backdrop-leave-to {
  opacity: 0;
}

/* ── Responsive breakpoint ────────────────────── */
@media (max-width: 960px) {
  /* Collapse the sidebar column — the sidebar becomes a fixed overlay */
  .app-shell {
    grid-template-columns: 1fr;
  }

  /* Activate the backdrop so it can be clicked to close the sidebar */
  .mobile-backdrop {
    display: block;
  }

  /* Tighter page padding on small screens */
  .app-content {
    padding: 1.25rem;
  }
}
</style>
