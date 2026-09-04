// CRANE — CRA Norm Engine
// Copyright (C) 2026 Ali Mohammad Hosseini
// SPDX-License-Identifier: AGPL-3.0-or-later
// This file is part of CRANE, free software under the GNU AGPL v3.0 or later.
// See <https://www.gnu.org/licenses/>.

import axios, { AxiosError } from "axios"

import { handleApiError } from "@/services/error-handler"
import { useToast } from "@/composables/useToast"
import { useAuthStore } from "@/stores/auth"

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

function getStoredRefreshToken(): string | null {
  const raw = window.localStorage.getItem(AUTH_STORAGE_KEY)

  if (!raw) {
    return null
  }

  try {
    const parsed = JSON.parse(raw) as { refreshToken?: string | null }
    return parsed.refreshToken ?? null
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
  // Let the browser add the multipart boundary for file uploads.
  if (config.data instanceof FormData) {
    delete config.headers["Content-Type"]
  }
  return config
})

// ── Silent token refresh (sliding session) ─────────────────────────────
// When the short-lived access token expires, the first request to get a 401
// triggers a single refresh using the stored refresh token; any other requests
// that 401 in the meantime wait on that same in-flight refresh (single-flight)
// rather than firing N parallel refresh calls. On success the original requests
// are retried with the new access token; only if the refresh itself fails do we
// clear auth and redirect to login.

// Holds the in-flight refresh promise so concurrent 401s share one refresh.
let refreshPromise: Promise<string> | null = null

// Performs the actual refresh against /auth/refresh. Uses a bare axios call (not
// apiClient) so it never recurses back through this response interceptor. The
// backend rotates the refresh token on every call, so we persist BOTH new tokens.
async function performTokenRefresh(): Promise<string> {
  const storedRefresh = getStoredRefreshToken()

  if (!storedRefresh) {
    throw new Error("No refresh token available")
  }

  const response = await axios.post<{ access_token: string; refresh_token: string }>(
    `${apiBaseUrl}/auth/refresh`,
    { refresh_token: storedRefresh },
    { headers: { "Content-Type": "application/json" }, timeout: requestTimeout },
  )

  const { access_token, refresh_token } = response.data
  // Persist the rotated token pair so the request interceptor (which reads from
  // localStorage) and the next refresh both use the latest values.
  useAuthStore().setTokens(access_token, refresh_token)
  return access_token
}

// Coalesces concurrent refreshes into a single network call.
function refreshAccessToken(): Promise<string> {
  if (!refreshPromise) {
    refreshPromise = performTokenRefresh().finally(() => {
      refreshPromise = null
    })
  }
  return refreshPromise
}

// Redirect to login after an unrecoverable auth failure (no/expired refresh
// token, or the refresh call itself was rejected).
function forceLogout(): void {
  useAuthStore().clearAuthState()

  const { showToast } = useToast()
  showToast({
    type: "warning",
    message: "Your session has expired. Please log in again.",
  })

  // Capture the current path synchronously before the async router import.
  const redirectPath = window.location.pathname + window.location.search
  // Lazy-load router to avoid circular imports (router → auth → api would loop).
  void import("@/router").then((mod) => {
    void mod.default.push({ name: "login", query: { redirect: redirectPath } })
  })
}

apiClient.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    // Handle 401 — the access token is missing/expired or otherwise invalid.
    // Instead of logging out immediately, try a one-time silent refresh and
    // replay the original request; only fall back to logout if that fails.
    const originalRequest = error.config as
      | (typeof error.config & { _retry?: boolean })
      | undefined

    if (error.response?.status === 401 && originalRequest) {
      const requestUrl = originalRequest.url ?? ""
      // Never try to refresh for the auth endpoints themselves: a 401 from
      // /auth/login means bad credentials, and a 401 from /auth/refresh means
      // the refresh token is dead — both are terminal.
      const isAuthEndpoint =
        requestUrl.includes("/auth/login") || requestUrl.includes("/auth/refresh")

      // Only attempt a refresh if we actually have a refresh token and haven't
      // already retried this request once.
      if (!isAuthEndpoint && !originalRequest._retry && getStoredRefreshToken()) {
        originalRequest._retry = true
        try {
          const newAccessToken = await refreshAccessToken()
          // Replay the original request with the freshly minted access token.
          originalRequest.headers = originalRequest.headers ?? {}
          originalRequest.headers.Authorization = `Bearer ${newAccessToken}`
          return apiClient(originalRequest)
        } catch {
          // Refresh failed (expired/revoked refresh token) — terminal.
          forceLogout()
          return Promise.reject(handleApiError(error))
        }
      }

      // No refresh possible, already retried, or an auth endpoint → log out.
      forceLogout()
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
