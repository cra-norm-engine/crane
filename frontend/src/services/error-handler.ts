import type { AxiosError } from "axios"

// User-friendly messages for common error codes
const ERROR_CODE_MESSAGES: Record<string, string> = {
  NOT_FOUND: "The requested item could not be found.",
  CONFLICT: "This record conflicts with existing data.",
  FORBIDDEN: "You do not have permission to perform this action.",
  VALIDATION_ERROR: "Please check your input and try again.",
  INTERNAL_ERROR: "Something went wrong. Please try again later.",
}

export class ApiError extends Error {
  statusCode?: number
  code?: string
  userMessage?: string

  constructor(message: string, statusCode?: number, code?: string, userMessage?: string) {
    super(message)
    this.name = "ApiError"
    this.statusCode = statusCode
    this.code = code
    this.userMessage = userMessage || message
  }
}

export function handleApiError(error: AxiosError): ApiError {
  const statusCode = error.response?.status
  const responseData = error.response?.data as Record<string, any> | undefined

  // Read from canonical error shape: { error: { code, message, details } }
  let code = "UNKNOWN"
  let message = "Something went wrong. Please try again."

  if (responseData?.error) {
    const errorObj = responseData.error
    code = errorObj.code || "UNKNOWN"
    message = errorObj.message || message
  } else if (responseData?.detail) {
    // Fallback to old detail shape (shouldn't happen after migration)
    message = String(responseData.detail)
  } else if (error.message) {
    message = error.message
  }

  // Use user-friendly message if available
  const userMessage = ERROR_CODE_MESSAGES[code] || message

  return new ApiError(message, statusCode, code, userMessage)
}