import { describe, it, expect, beforeEach, vi } from "vitest"
import { useToast } from "@/composables/useToast"

describe("useToast", () => {
  beforeEach(() => {
    // Clear all toasts before each test by getting fresh instance
    const { toasts, dismissToast } = useToast()
    // Dismiss all current toasts
    while (toasts.length > 0) {
      dismissToast(toasts[0].id)
    }
  })

  describe("showToast", () => {
    it("adds a toast to the queue", () => {
      const { showToast, toasts } = useToast()

      showToast({
        type: "success",
        message: "Test message",
      })

      expect(toasts.length).toBeGreaterThan(0)
    })

    it("creates toast with unique id", () => {
      const { showToast, toasts } = useToast()

      showToast({ type: "success", message: "Toast 1" })
      showToast({ type: "error", message: "Toast 2" })

      const ids = toasts.map((t) => t.id)
      expect(new Set(ids).size).toBe(ids.length) // All unique
    })

    it("supports different toast types", () => {
      const { showToast, toasts } = useToast()

      showToast({ type: "success", message: "Success" })
      showToast({ type: "error", message: "Error" })
      showToast({ type: "warning", message: "Warning" })
      showToast({ type: "info", message: "Info" })

      expect(toasts.length).toBe(4)
      expect(toasts[0].type).toBe("success")
      expect(toasts[1].type).toBe("error")
      expect(toasts[2].type).toBe("warning")
      expect(toasts[3].type).toBe("info")
    })

    it("includes custom duration if provided", () => {
      const { showToast, toasts } = useToast()

      showToast({
        type: "success",
        message: "Test",
        duration: 5000,
      })

      expect(toasts[0].duration).toBe(5000)
    })

    it("uses default duration if not provided", () => {
      const { showToast, toasts } = useToast()

      showToast({
        type: "info",
        message: "Test",
      })

      expect(toasts[0].duration).toBe(5000) // default value
    })

    it("auto-dismisses toast after duration", async () => {
      vi.useFakeTimers()
      const { showToast, toasts } = useToast()

      showToast({
        type: "success",
        message: "Auto dismiss",
        duration: 1000,
      })

      expect(toasts.length).toBe(1)

      vi.advanceTimersByTime(1000)

      expect(toasts.length).toBe(0)

      vi.useRealTimers()
    })
  })

  describe("dismissToast", () => {
    it("removes toast by id", () => {
      const { showToast, dismissToast, toasts } = useToast()

      showToast({ type: "success", message: "Test" })
      const toastId = toasts[0].id

      dismissToast(toastId)

      expect(toasts.length).toBe(0)
    })

    it("only removes the specified toast", () => {
      const { showToast, dismissToast, toasts } = useToast()

      showToast({ type: "success", message: "Toast 1" })
      showToast({ type: "error", message: "Toast 2" })
      showToast({ type: "warning", message: "Toast 3" })

      const toastId = toasts[1].id
      dismissToast(toastId)

      expect(toasts.length).toBe(2)
      expect(toasts.some((t) => t.id === toastId)).toBe(false)
    })

    it("handles dismissing nonexistent toast gracefully", () => {
      const { dismissToast } = useToast()

      expect(() => {
        dismissToast("nonexistent-id")
      }).not.toThrow()
    })
  })

  describe("toast composition", () => {
    it("can show multiple toasts simultaneously", () => {
      const { showToast, toasts } = useToast()

      showToast({ type: "success", message: "Success message" })
      showToast({ type: "error", message: "Error message" })
      showToast({ type: "info", message: "Info message" })

      expect(toasts.length).toBe(3)
    })

    it("maintains toast order (FIFO)", () => {
      const { showToast, toasts } = useToast()

      showToast({ type: "info", message: "First" })
      showToast({ type: "info", message: "Second" })
      showToast({ type: "info", message: "Third" })

      expect(toasts[0].message).toBe("First")
      expect(toasts[1].message).toBe("Second")
      expect(toasts[2].message).toBe("Third")
    })
  })

  describe("error toast handling", () => {
    it("creates error toast with proper type", () => {
      const { showToast, toasts } = useToast()

      showToast({
        type: "error",
        message: "Something went wrong",
      })

      const toast = toasts[0]
      expect(toast.type).toBe("error")
      expect(toast.message).toBe("Something went wrong")
    })

    it("formats error messages for display", () => {
      const { showToast, toasts } = useToast()

      const errorMessage = "Failed to save: Permission denied"
      showToast({
        type: "error",
        message: errorMessage,
      })

      expect(toasts[0].message).toBe(errorMessage)
    })
  })

  describe("success toast handling", () => {
    it("creates success toast", () => {
      const { showToast, toasts } = useToast()

      showToast({
        type: "success",
        message: "Saved successfully",
      })

      expect(toasts[0].type).toBe("success")
    })
  })

  describe("reactive toast updates", () => {
    it("toast list is reactive", () => {
      const { showToast, toasts } = useToast()

      const initialLength = toasts.length

      showToast({ type: "info", message: "New toast" })

      expect(toasts.length).toBeGreaterThan(initialLength)
    })
  })

  describe("toast persistence", () => {
    it("toasts are not persisted to localStorage", () => {
      const { showToast } = useToast()

      showToast({ type: "success", message: "Test" })

      // Toasts should not be in localStorage (transient only)
      const stored = localStorage.getItem("toasts")
      expect(stored).toBeNull()
    })
  })
})
