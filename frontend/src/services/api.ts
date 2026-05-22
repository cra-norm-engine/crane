import axios, { AxiosError } from "axios"

import { handleApiError } from "@/services/error-handler"
import { useToast } from "@/composables/useToast"

const AUTH_STORAGE_KEY = "cra-compliance-auth"
const apiBaseUrl = import.meta.env.VITE_API_BASE_URL || "/api/v1"
const requestTimeout = Number(import.meta.env.VITE_REQUEST_TIMEOUT_MS || 15000)

function getStoredAccessToken(): string | null {
  const raw = window.localStorage.getItem(AUTH_STORAGE_KEY)

  if (!raw) {
    return null
  }

  try {
    const parsed = JSON.parse(raw) as { accessToken?: string | null }
    return parsed.accessToken ?? null
  } catch {
    window.localStorage.removeItem(AUTH_STORAGE_KEY)
    return null
  }
}

export const apiClient = axios.create({
  baseURL: apiBaseUrl,
  timeout: requestTimeout,
  headers: {
    "Content-Type": "application/json",
  },
})

apiClient.interceptors.request.use((config) => {
  const token = getStoredAccessToken()

  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }

  config.headers["X-Correlation-ID"] = Math.random().toString(36).substring(2, 11)
  return config
})

apiClient.interceptors.response.use(
  (response) => response,
  (error: AxiosError) => {
    // Handle 401 with auto-redirect to login
    if (error.response?.status === 401) {
      // Lazy-load router to avoid circular imports
      import("@/router").then((mod) => {
        mod.default.push({ name: "login" })
      })
      return Promise.reject(handleApiError(error))
    }

    // Handle 403 with toast notification
    if (error.response?.status === 403) {
      const { showToast } = useToast()
      showToast({
        type: "error",
        message: "You do not have permission to perform this action.",
      })
    }

    return Promise.reject(handleApiError(error))
  },
)