import { describe, it, expect, beforeEach, afterEach, vi } from "vitest"
import { useAuthStore } from "@/stores/auth"

describe("useAuthStore", () => {
  beforeEach(() => {
    localStorage.clear()
    vi.clearAllMocks()
  })

  afterEach(() => {
    localStorage.clear()
  })

  describe("isAuthenticated computed", () => {
    it("returns false when no access token", () => {
      const store = useAuthStore()
      expect(store.isAuthenticated).toBe(false)
    })

    it("returns true when access token is set", () => {
      const store = useAuthStore()
      store.login("test-token", "refresh-token", null)
      expect(store.isAuthenticated).toBe(true)
    })

    it("returns false after logout", () => {
      const store = useAuthStore()
      store.login("test-token", "refresh-token", null)
      expect(store.isAuthenticated).toBe(true)
      store.logout()
      expect(store.isAuthenticated).toBe(false)
    })
  })

  describe("hasRole", () => {
    it("returns false when user has no roles", () => {
      const store = useAuthStore()
      expect(store.hasRole("admin")).toBe(false)
    })

    it("returns true when user has the role", () => {
      const store = useAuthStore()
      const user = {
        id: "1",
        email: "admin@example.com",
        full_name: "Admin User",
        roles: ["admin", "editor"],
        permissions: [],
        is_active: true,
        auth_provider: "local",
        must_change_password: false,
      }
      store.login("token", "refresh", user)
      expect(store.hasRole("admin")).toBe(true)
    })

    it("returns false when user does not have the role", () => {
      const store = useAuthStore()
      const user = {
        id: "1",
        email: "user@example.com",
        full_name: "Regular User",
        roles: ["viewer"],
        permissions: [],
        is_active: true,
        auth_provider: "local",
        must_change_password: false,
      }
      store.login("token", "refresh", user)
      expect(store.hasRole("admin")).toBe(false)
    })
  })

  describe("hasAnyRole", () => {
    it("returns false when user has none of the requested roles", () => {
      const store = useAuthStore()
      const user = {
        id: "1",
        email: "user@example.com",
        full_name: "User",
        roles: ["viewer"],
        permissions: [],
        is_active: true,
        auth_provider: "local",
        must_change_password: false,
      }
      store.login("token", "refresh", user)
      expect(store.hasAnyRole(["admin", "editor"])).toBe(false)
    })

    it("returns true when user has at least one of the requested roles", () => {
      const store = useAuthStore()
      const user = {
        id: "1",
        email: "user@example.com",
        full_name: "User",
        roles: ["editor", "viewer"],
        permissions: [],
        is_active: true,
        auth_provider: "local",
        must_change_password: false,
      }
      store.login("token", "refresh", user)
      expect(store.hasAnyRole(["admin", "editor"])).toBe(true)
    })
  })

  describe("hasPermission", () => {
    it("returns false when user has no permissions", () => {
      const store = useAuthStore()
      expect(store.hasPermission("products:read")).toBe(false)
    })

    it("returns true when user has the permission", () => {
      const store = useAuthStore()
      const user = {
        id: "1",
        email: "user@example.com",
        full_name: "User",
        roles: [],
        permissions: ["products:read", "products:write"],
        is_active: true,
        auth_provider: "local",
        must_change_password: false,
      }
      store.login("token", "refresh", user)
      expect(store.hasPermission("products:read")).toBe(true)
    })

    it("returns false when user does not have the permission", () => {
      const store = useAuthStore()
      const user = {
        id: "1",
        email: "user@example.com",
        full_name: "User",
        roles: [],
        permissions: ["products:read"],
        is_active: true,
        auth_provider: "local",
        must_change_password: false,
      }
      store.login("token", "refresh", user)
      expect(store.hasPermission("products:delete")).toBe(false)
    })
  })

  describe("hasAnyPermission", () => {
    it("returns false when user has none of the requested permissions", () => {
      const store = useAuthStore()
      const user = {
        id: "1",
        email: "user@example.com",
        full_name: "User",
        roles: [],
        permissions: ["products:read"],
        is_active: true,
        auth_provider: "local",
        must_change_password: false,
      }
      store.login("token", "refresh", user)
      expect(store.hasAnyPermission(["products:delete", "products:admin"])).toBe(false)
    })

    it("returns true when user has at least one of the requested permissions", () => {
      const store = useAuthStore()
      const user = {
        id: "1",
        email: "user@example.com",
        full_name: "User",
        roles: [],
        permissions: ["products:read", "products:write"],
        is_active: true,
        auth_provider: "local",
        must_change_password: false,
      }
      store.login("token", "refresh", user)
      expect(store.hasAnyPermission(["products:delete", "products:write"])).toBe(true)
    })
  })

  describe("login", () => {
    it("sets access token and user info", () => {
      const store = useAuthStore()
      const user = {
        id: "1",
        email: "admin@example.com",
        full_name: "Admin",
        roles: ["admin"],
        permissions: ["products:read"],
        is_active: true,
        auth_provider: "local",
        must_change_password: false,
      }
      store.login("access-token", "refresh-token", user)
      expect(store.isAuthenticated).toBe(true)
      expect(store.userEmail).toBe("admin@example.com")
      expect(store.userFullName).toBe("Admin")
    })

    it("persists auth state to localStorage", () => {
      const store = useAuthStore()
      const user = {
        id: "1",
        email: "user@example.com",
        full_name: "User",
        roles: [],
        permissions: [],
        is_active: true,
        auth_provider: "local",
        must_change_password: false,
      }
      store.login("token", "refresh", user)
      const stored = localStorage.getItem("cra-compliance-auth")
      expect(stored).toBeTruthy()
      const parsed = JSON.parse(stored!)
      expect(parsed.accessToken).toBe("token")
      expect(parsed.user.email).toBe("user@example.com")
    })
  })

  describe("logout", () => {
    it("clears all auth state", () => {
      const store = useAuthStore()
      const user = {
        id: "1",
        email: "user@example.com",
        full_name: "User",
        roles: ["admin"],
        permissions: ["products:read"],
        is_active: true,
        auth_provider: "local",
        must_change_password: false,
      }
      store.login("token", "refresh", user)
      expect(store.isAuthenticated).toBe(true)
      store.logout()
      expect(store.isAuthenticated).toBe(false)
      expect(store.userEmail).toBe("")
    })

    it("clears localStorage", () => {
      const store = useAuthStore()
      const user = {
        id: "1",
        email: "user@example.com",
        full_name: "User",
        roles: [],
        permissions: [],
        is_active: true,
        auth_provider: "local",
        must_change_password: false,
      }
      store.login("token", "refresh", user)
      expect(localStorage.getItem("cra-compliance-auth")).toBeTruthy()
      store.logout()
      expect(localStorage.getItem("cra-compliance-auth")).toBeNull()
    })
  })

  describe("initializeFromStorage", () => {
    it("loads auth state from localStorage", () => {
      const authState = {
        accessToken: "saved-token",
        refreshToken: "saved-refresh",
        user: {
          id: "1",
          email: "saved@example.com",
          full_name: "Saved User",
          roles: ["admin"],
          permissions: ["products:read"],
          is_active: true,
          auth_provider: "local",
          must_change_password: false,
        },
      }
      localStorage.setItem("cra-compliance-auth", JSON.stringify(authState))

      const store = useAuthStore()
      store.initializeFromStorage()

      expect(store.isAuthenticated).toBe(true)
      expect(store.userEmail).toBe("saved@example.com")
    })

    it("handles corrupted localStorage gracefully", () => {
      localStorage.setItem("cra-compliance-auth", "invalid json{")

      const store = useAuthStore()
      store.initializeFromStorage()

      expect(store.isAuthenticated).toBe(false)
      expect(localStorage.getItem("cra-compliance-auth")).toBeNull()
    })

    it("marks store as initialized", () => {
      const store = useAuthStore()
      expect((store as any).isInitialized).toBe(false)
      store.initializeFromStorage()
      expect((store as any).isInitialized).toBe(true)
    })
  })

  describe("computed properties", () => {
    it("returns empty array for roles when no user", () => {
      const store = useAuthStore()
      expect(store.roles).toEqual([])
    })

    it("returns user roles", () => {
      const store = useAuthStore()
      const user = {
        id: "1",
        email: "user@example.com",
        full_name: "User",
        roles: ["admin", "editor"],
        permissions: [],
        is_active: true,
        auth_provider: "local",
        must_change_password: false,
      }
      store.login("token", "refresh", user)
      expect(store.roles).toEqual(["admin", "editor"])
    })

    it("returns empty array for permissions when no user", () => {
      const store = useAuthStore()
      expect(store.permissions).toEqual([])
    })

    it("returns user permissions", () => {
      const store = useAuthStore()
      const user = {
        id: "1",
        email: "user@example.com",
        full_name: "User",
        roles: [],
        permissions: ["products:read", "products:write"],
        is_active: true,
        auth_provider: "local",
        must_change_password: false,
      }
      store.login("token", "refresh", user)
      expect(store.permissions).toEqual(["products:read", "products:write"])
    })
  })
})
