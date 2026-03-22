import axios, { AxiosError } from "axios";

import { handleApiError } from "@/services/error-handler";

const apiBaseUrl = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000/api/v1";
const requestTimeout = Number(import.meta.env.VITE_REQUEST_TIMEOUT_MS || 15000);

export const apiClient = axios.create({
  baseURL: apiBaseUrl,
  timeout: requestTimeout,
  headers: {
    "Content-Type": "application/json",
  },
});

apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem("cra_access_token");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  config.headers["X-Correlation-ID"] = crypto.randomUUID();
  return config;
});

apiClient.interceptors.response.use(
  (response) => response,
  (error: AxiosError) => Promise.reject(handleApiError(error)),
);