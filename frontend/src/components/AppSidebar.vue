<template>
  <aside class="card" style="min-width: 240px; height: fit-content;">
    <nav style="display: flex; flex-direction: column; gap: 0.5rem;">
      <RouterLink class="button secondary" :to="{ name: 'dashboard' }">Dashboard</RouterLink>
      <RouterLink class="button secondary" :to="{ name: 'products' }">Products</RouterLink>
    </nav>
  </aside>
</template>

<script setup lang="ts">
import { RouterLink } from "vue-router";
</script>