// CRANE — CRA Norm Engine
// Copyright (C) 2026 Ali Mohammad Hosseini
// SPDX-License-Identifier: AGPL-3.0-or-later
// This file is part of CRANE, free software under the GNU AGPL v3.0 or later.
// See <https://www.gnu.org/licenses/>.

import { ref } from "vue"
import { useToast } from "@/composables/useToast"
import { handleApiError } from "@/services/error-handler"
import type { ApiError } from "@/services/error-handler"

export function useAsyncState() {
  const isLoading = ref(false)
  const errorMessage = ref("")

  async function execute<T>(task: () => Promise<T>): Promise<T> {
    isLoading.value = true
    errorMessage.value = ""
    try {
      return await task()
    } catch (error) {
      // Parse error to get user-friendly message
      let userMessage = "Unknown error"
      if (error instanceof Error) {
        const apiError = error as ApiError
        userMessage = apiError.userMessage || apiError.message || "Unknown error"
      }

      errorMessage.value = userMessage

      // Show toast for user feedback
      const { showToast } = useToast()
      showToast({ type: "error", message: userMessage })

      throw error
    } finally {
      isLoading.value = false
    }
  }

  return {
    isLoading,
    errorMessage,
    execute,
  }
}