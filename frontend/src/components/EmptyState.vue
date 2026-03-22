<template>
  <div class="card" style="text-align: center;">
    <h3 style="margin-top: 0;">{{ title }}</h3>
    <p class="muted">{{ description }}</p>
  </div>
</template>

<script setup lang="ts">
defineProps<{
  title: string;
  description: string;
}>();
</script>