<template>
  <span class="badge">{{ label }}</span>
</template>

<script setup lang="ts">
defineProps<{
  label: string;
}>();
</script>