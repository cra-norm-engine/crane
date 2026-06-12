<!--
  CRANE — CRA Norm Engine
  Copyright (C) 2026 Ali Mohammad Hosseini
  SPDX-License-Identifier: AGPL-3.0-or-later
  This file is part of CRANE, free software under the GNU AGPL v3.0 or later.
  See <https://www.gnu.org/licenses/>.
-->
<template>
  <!-- App.vue — root component. The "page" transition maps to .page-enter-* / .page-leave-* in styles.css. -->
  <RouterView v-slot="{ Component }">
    <Transition name="page">
      <component :is="Component" />
    </Transition>
  </RouterView>
  <AppToast />
</template>

<script setup lang="ts">
import { onMounted } from "vue";
import { RouterView } from "vue-router";

import { useAppStore } from "@/stores/app";
import AppToast from "@/components/AppToast.vue";

const appStore = useAppStore();

/*
  Apply the persisted theme (dark / light) as early as possible so
  there is no flash of the wrong theme on first load.
*/
onMounted(() => {
  appStore.initializeTheme();
});
</script>
