// CRANE — CRA Norm Engine
// Copyright (C) 2026 Ali Mohammad Hosseini
// SPDX-License-Identifier: AGPL-3.0-or-later
// This file is part of CRANE, free software under the GNU AGPL v3.0 or later.
// See <https://www.gnu.org/licenses/>.

import { onMounted, watch } from "vue";
import { useRoute } from "vue-router";

/**
 * Scroll to the element named by the current route hash (e.g. "#support-periods").
 *
 * Pages that deep-link from the Compliance Journey load their data asynchronously,
 * so the target element may not exist on the first tick. This retries for a short
 * window until the element appears, then smooth-scrolls and briefly highlights it.
 * Call once from a view's <script setup>.
 */
export function useScrollToHash(): void {
  const route = useRoute();

  function scrollToHash(hash: string): void {
    if (!hash) return;
    const id = hash.startsWith("#") ? hash.slice(1) : hash;

    let attempts = 0;
    const tryScroll = (): void => {
      const el = document.getElementById(id);
      if (el) {
        el.scrollIntoView({ behavior: "smooth", block: "start" });
        // Brief highlight so the user sees which section they landed on.
        el.classList.add("anchor-flash");
        window.setTimeout(() => el.classList.remove("anchor-flash"), 1600);
        return;
      }
      // Retry while async content is still rendering (~3s max).
      if (attempts++ < 20) window.setTimeout(tryScroll, 150);
    };
    tryScroll();
  }

  onMounted(() => scrollToHash(route.hash));
  // Re-run if the hash changes while already on the page.
  watch(() => route.hash, (hash) => scrollToHash(hash));
}
