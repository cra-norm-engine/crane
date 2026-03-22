<template>
  <div style="min-height: 100vh; font-family: Arial, sans-serif; background: #f8fafc; color: #0f172a;">
    <header style="padding: 16px 24px; border-bottom: 1px solid #e2e8f0; background: white;">
      <nav style="display: flex; gap: 16px; align-items: center;">
        <RouterLink to="/">Dashboard</RouterLink>
        <RouterLink to="/products">Products</RouterLink>
      </nav>
    </header>

    <main style="padding: 24px;">
      <router-view />
    </main>
  </div>
</template>

<script setup lang="ts">
import { RouterLink } from "vue-router";
</script>
