import type { AxiosError } from "axios";

export class ApiError extends Error {
  statusCode?: number;
  detail?: string;

  constructor(message: string, statusCode?: number, detail?: string) {
    super(message);
    this.name = "ApiError";
    this.statusCode = statusCode;
    this.detail = detail;
  }
}

export function handleApiError(error: AxiosError): ApiError {
  const statusCode = error.response?.status;
  const detail =
    typeof error.response?.data === "object" && error.response?.data && "detail" in error.response.data
      ? String((error.response.data as Record<string, unknown>).detail)
      : undefined;

  return new ApiError(detail || error.message || "Unexpected API error", statusCode, detail);
}