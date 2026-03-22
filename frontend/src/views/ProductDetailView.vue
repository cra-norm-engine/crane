<template>
  <section class="page">
    <div class="page-header">
      <div>
        <h1 class="page-title">Product Detail</h1>
        <p class="muted">Detailed product compliance view scaffold.</p>
      </div>
    </div>

    <div class="card">
      <p>Selected product ID: {{ productId }}</p>
    </div>
  </section>
</template>

<script setup lang="ts">
defineProps<{
  productId: string;
}>();
</script>