import { createPinia, setActivePinia } from "pinia"
import { beforeEach, vi } from "vitest"

beforeEach(() => {
  setActivePinia(createPinia())
})

// Mock window.matchMedia for components that use dark mode detection
Object.defineProperty(window, "matchMedia", {
  writable: true,
  value: vi.fn().mockImplementation((query) => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: vi.fn(),
    removeListener: vi.fn(),
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
    dispatchEvent: vi.fn(),
  })),
})
