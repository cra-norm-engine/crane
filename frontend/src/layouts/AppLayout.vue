<template>
  <div class="app-shell">
    <AppSidebar />

    <div class="app-main">
      <AppHeader />
      <main class="app-content">
        <router-view />
      </main>
    </div>
  </div>
</template>

<script setup lang="ts">
import AppHeader from "@/components/AppHeader.vue";
import AppSidebar from "@/components/AppSidebar.vue";
</script>

<style scoped>
.app-shell {
  min-height: 100vh;
  display: grid;
  grid-template-columns: 280px minmax(0, 1fr);
  background: transparent;
}

.app-main {
  min-width: 0;
  display: flex;
  flex-direction: column;
}

.app-content {
  padding: 1.25rem;
}

@media (max-width: 960px) {
  .app-shell {
    grid-template-columns: 1fr;
  }

  .app-content {
    padding: 1rem;
  }
}
</style>