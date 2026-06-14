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
import { useAuthStore } from "@/stores/auth";
import AppToast from "@/components/AppToast.vue";

const appStore = useAppStore();
const authStore = useAuthStore();

/*
  Apply the persisted theme (dark / light) as early as possible so
  there is no flash of the wrong theme on first load. If the signed-in
  user has a server-synced theme preference, it takes precedence so the
  choice follows them across devices.
*/
onMounted(() => {
  if (!authStore.isInitialized) {
    authStore.initializeFromStorage();
  }
  appStore.initializeTheme();

  const preferredTheme = authStore.preferences?.theme;
  if (preferredTheme === "dark" || preferredTheme === "light") {
    appStore.setTheme(preferredTheme);
  }
});
</script>
