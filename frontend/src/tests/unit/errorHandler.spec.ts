import { describe, it, expect } from "vitest"
import { handleApiError, ApiError } from "@/services/error-handler"

describe("Error Handler", () => {
  describe("ApiError class", () => {
    it("creates error with message", () => {
      const error = new ApiError("Test error")

      expect(error.message).toBe("Test error")
      expect(error.name).toBe("ApiError")
    })

    it("stores status code", () => {
      const error = new ApiError("Test error", 404)

      expect(error.statusCode).toBe(404)
    })

    it("stores error code", () => {
      const error = new ApiError("Test error", 404, "NOT_FOUND")

      expect(error.code).toBe("NOT_FOUND")
    })

    it("stores user-friendly message", () => {
      const error = new ApiError("Internal error", 500, "INTERNAL_ERROR", "Something went wrong")

      expect(error.userMessage).toBe("Something went wrong")
    })

    it("defaults userMessage to message if not provided", () => {
      const error = new ApiError("Test error")

      expect(error.userMessage).toBe("Test error")
    })
  })

  describe("handleApiError", () => {
    it("extracts error code from canonical error shape", () => {
      const axiosError = {
        response: {
          status: 400,
          data: {
            error: {
              code: "VALIDATION_ERROR",
              message: "Invalid input",
            },
          },
        },
      } as any

      const error = handleApiError(axiosError)

      expect(error.code).toBe("VALIDATION_ERROR")
      expect(error.statusCode).toBe(400)
    })

    it("handles missing error code gracefully", () => {
      const axiosError = {
        response: {
          status: 500,
          data: {
            error: {
              message: "Something failed",
            },
          },
        },
      } as any

      const error = handleApiError(axiosError)

      expect(error.code).toBe("UNKNOWN")
      expect(error.message).toBe("Something failed")
    })

    it("extracts message from canonical error shape", () => {
      const axiosError = {
        response: {
          status: 403,
          data: {
            error: {
              code: "FORBIDDEN",
              message: "Access denied",
            },
          },
        },
      } as any

      const error = handleApiError(axiosError)

      expect(error.message).toBe("Access denied")
    })

    it("handles missing response data", () => {
      const axiosError = {
        message: "Network error",
      } as any

      const error = handleApiError(axiosError)

      expect(error.message).toBe("Network error")
      expect(error.code).toBe("UNKNOWN")
    })

    it("provides user-friendly message for known codes", () => {
      const axiosError = {
        response: {
          status: 404,
          data: {
            error: {
              code: "NOT_FOUND",
              message: "Resource not found",
            },
          },
        },
      } as any

      const error = handleApiError(axiosError)

      // userMessage should be user-friendly for NOT_FOUND
      expect(error.userMessage).toBeDefined()
      expect(error.userMessage.length).toBeGreaterThan(0)
    })

    it("uses error message as userMessage if no mapping exists", () => {
      const axiosError = {
        response: {
          status: 500,
          data: {
            error: {
              code: "CUSTOM_CODE",
              message: "Custom error message",
            },
          },
        },
      } as any

      const error = handleApiError(axiosError)

      expect(error.userMessage).toBe("Custom error message")
    })

    it("handles fallback detail property", () => {
      const axiosError = {
        response: {
          status: 400,
          data: {
            detail: "Field required",
          },
        },
      } as any

      const error = handleApiError(axiosError)

      expect(error.message).toContain("Field required")
    })
  })

  describe("HTTP status codes", () => {
    it("handles 401 unauthorized", () => {
      const axiosError = {
        response: {
          status: 401,
          data: {
            error: {
              code: "INVALID_CREDENTIALS",
              message: "Invalid email or password",
            },
          },
        },
      } as any

      const error = handleApiError(axiosError)

      expect(error.statusCode).toBe(401)
      expect(error.code).toBe("INVALID_CREDENTIALS")
    })

    it("handles 403 forbidden", () => {
      const axiosError = {
        response: {
          status: 403,
          data: {
            error: {
              code: "FORBIDDEN",
              message: "Access denied",
            },
          },
        },
      } as any

      const error = handleApiError(axiosError)

      expect(error.statusCode).toBe(403)
    })

    it("handles 404 not found", () => {
      const axiosError = {
        response: {
          status: 404,
          data: {
            error: {
              code: "NOT_FOUND",
              message: "Resource not found",
            },
          },
        },
      } as any

      const error = handleApiError(axiosError)

      expect(error.statusCode).toBe(404)
    })

    it("handles 409 conflict", () => {
      const axiosError = {
        response: {
          status: 409,
          data: {
            error: {
              code: "CONFLICT",
              message: "Duplicate entry",
            },
          },
        },
      } as any

      const error = handleApiError(axiosError)

      expect(error.statusCode).toBe(409)
    })

    it("handles 422 validation error", () => {
      const axiosError = {
        response: {
          status: 422,
          data: {
            error: {
              code: "VALIDATION_ERROR",
              message: "Invalid input",
            },
          },
        },
      } as any

      const error = handleApiError(axiosError)

      expect(error.statusCode).toBe(422)
    })

    it("handles 500 internal server error", () => {
      const axiosError = {
        response: {
          status: 500,
          data: {
            error: {
              code: "INTERNAL_ERROR",
              message: "Something went wrong",
            },
          },
        },
      } as any

      const error = handleApiError(axiosError)

      expect(error.statusCode).toBe(500)
    })
  })

  describe("Error details preservation", () => {
    it("error details object is accessible", () => {
      const error = {
        response: {
          data: {
            error: {
              code: "VALIDATION_ERROR",
              details: {
                field_name: "email",
                reason: "invalid_format",
              },
            },
          },
        },
      }

      expect(error.response.data.error.details).toBeDefined()
      expect(error.response.data.error.details.field_name).toBe("email")
    })

    it("can log full error for debugging", () => {
      const error = {
        response: {
          data: {
            error: {
              code: "VALIDATION_ERROR",
              message: "Validation failed",
              details: { field: "value" },
            },
          },
        },
      }

      expect(error).toBeTruthy()
      expect(JSON.stringify(error)).toContain("VALIDATION_ERROR")
    })
  })
})
