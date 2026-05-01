<template>
  <!--
    App.vue — root component.

    Wraps every route in a <Transition> so navigation between pages
    feels smooth.  The "page" transition name maps to the
    .page-enter-* / .page-leave-* keyframes defined in styles.css.

    mode="out-in" ensures the leaving page finishes its exit before
    the entering page starts, preventing a visual overlap flash.
  -->
  <RouterView v-slot="{ Component }">
    <Transition name="page" mode="out-in">
      <component :is="Component" />
    </Transition>
  </RouterView>
</template>

<script setup lang="ts">
import { onMounted } from "vue";
import { RouterView } from "vue-router";

import { useAppStore } from "@/stores/app";

const appStore = useAppStore();

/*
  Apply the persisted theme (dark / light) as early as possible so
  there is no flash of the wrong theme on first load.
*/
onMounted(() => {
  appStore.initializeTheme();
});
</script>
