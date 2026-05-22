import { describe, it, expect, beforeEach, vi } from "vitest"
import { useAsyncState } from "@/composables/useAsyncState"
import { useToast } from "@/composables/useToast"

vi.mock("@/composables/useToast")

describe("useAsyncState", () => {
  beforeEach(() => {
    vi.clearAllMocks()
    vi.mocked(useToast).mockReturnValue({
      showToast: vi.fn(),
      dismissToast: vi.fn(),
      toasts: [],
    } as any)
  })

  describe("initial state", () => {
    it("initializes with loading false and empty error", () => {
      const { isLoading, errorMessage } = useAsyncState()

      expect(isLoading.value).toBe(false)
      expect(errorMessage.value).toBe("")
    })
  })

  describe("execute function", () => {
    it("executes async function successfully", async () => {
      const { execute, isLoading } = useAsyncState()
      const asyncFn = vi.fn(async () => ({ result: "success" }))

      const result = await execute(asyncFn)

      expect(asyncFn).toHaveBeenCalled()
      expect(result).toEqual({ result: "success" })
      expect(isLoading.value).toBe(false)
    })

    it("sets loading state during execution", async () => {
      const { isLoading, execute } = useAsyncState()
      let loadingDuringExecution = false

      const asyncFn = async () => {
        loadingDuringExecution = isLoading.value
        return "done"
      }

      await execute(asyncFn)

      expect(loadingDuringExecution).toBe(true)
      expect(isLoading.value).toBe(false)
    })

    it("clears loading state after completion", async () => {
      const { isLoading, execute } = useAsyncState()

      await execute(async () => "result")

      expect(isLoading.value).toBe(false)
    })

    it("handles errors and sets error message", async () => {
      const { errorMessage, execute } = useAsyncState()

      await expect(execute(async () => {
        throw new Error("Test error")
      })).rejects.toThrow()

      expect(errorMessage.value).toContain("Test error")
    })

    it("clears error message before execution", async () => {
      const { errorMessage, execute } = useAsyncState()

      // Set an error first
      await expect(execute(async () => {
        throw new Error("First error")
      })).rejects.toThrow()

      expect(errorMessage.value).toContain("First error")

      // Execute successfully
      await execute(async () => "success")

      expect(errorMessage.value).toBe("")
    })
  })

  describe("error handling", () => {
    it("extracts error message from Error object", async () => {
      const { errorMessage, execute } = useAsyncState()

      await expect(execute(async () => {
        throw new Error("Custom error message")
      })).rejects.toThrow()

      expect(errorMessage.value).toContain("Custom error message")
    })

    it("handles unknown error types", async () => {
      const { errorMessage, execute } = useAsyncState()

      await expect(execute(async () => {
        throw "String error"
      })).rejects.toThrow()

      expect(errorMessage.value).toBe("Unknown error")
    })
  })

  describe("toast integration", () => {
    it("shows error toast on failure", async () => {
      const mockShowToast = vi.fn()
      vi.mocked(useToast).mockReturnValue({
        showToast: mockShowToast,
        dismissToast: vi.fn(),
        toasts: [],
      } as any)

      const { execute } = useAsyncState()

      await expect(execute(async () => {
        throw new Error("Test error")
      })).rejects.toThrow()

      expect(mockShowToast).toHaveBeenCalledWith({
        type: "error",
        message: expect.any(String),
      })
    })

    it("does not show toast on success", async () => {
      const mockShowToast = vi.fn()
      vi.mocked(useToast).mockReturnValue({
        showToast: mockShowToast,
        dismissToast: vi.fn(),
        toasts: [],
      } as any)

      const { execute } = useAsyncState()

      await execute(async () => "success")

      expect(mockShowToast).not.toHaveBeenCalled()
    })
  })

  describe("reactive properties", () => {
    it("isLoading is reactive", async () => {
      const { isLoading, execute } = useAsyncState()

      expect(isLoading.value).toBe(false)

      const promise = execute(async () => {
        await new Promise((resolve) => setTimeout(resolve, 10))
        return "done"
      })

      // Note: isLoading might have changed to true by now
      await promise

      expect(isLoading.value).toBe(false)
    })

    it("errorMessage is reactive", async () => {
      const { errorMessage, execute } = useAsyncState()

      await expect(execute(async () => {
        throw new Error("Test")
      })).rejects.toThrow()

      expect(errorMessage.value).toBeTruthy()

      // Next execution clears it
      await execute(async () => "success")

      expect(errorMessage.value).toBe("")
    })
  })
})
