import { flushPromises, mount } from "@vue/test-utils";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { useAuthStore } from "@/stores/auth";
import ChangePasswordView from "@/views/ChangePasswordView.vue";

const mocks = vi.hoisted(() => ({
  changePassword: vi.fn(),
  fetchCurrentUser: vi.fn(),
  login: vi.fn(),
  push: vi.fn(),
}));

vi.mock("vue-router", () => ({
  RouterLink: { template: "<a><slot /></a>" },
  useRouter: () => ({ push: mocks.push }),
}));

vi.mock("@/services/auth-service", () => ({
  changePasswordRequest: mocks.changePassword,
  fetchCurrentUser: mocks.fetchCurrentUser,
  loginRequest: mocks.login,
}));

const user = {
  id: "user-1",
  email: "new@example.com",
  full_name: "New User",
  avatar_data: null,
  is_active: true,
  roles: [],
  permissions: [],
  auth_provider: "local",
  must_change_password: false,
  preferences: { theme: "light", timezone: "UTC", date_format: "YYYY-MM-DD", default_landing_page: "dashboard" },
};

describe("first-login password change", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    const storage = new Map<string, string>();
    Object.defineProperty(window, "localStorage", { configurable: true, value: {
      getItem: (key: string) => storage.get(key) ?? null,
      setItem: (key: string, value: string) => storage.set(key, value),
      removeItem: (key: string) => storage.delete(key),
    } });
    mocks.changePassword.mockResolvedValue(undefined);
    mocks.login.mockResolvedValue({ access_token: "new-access", refresh_token: "new-refresh", token_type: "bearer" });
    mocks.fetchCurrentUser.mockResolvedValue(user);
    useAuthStore().login("old-access", "old-refresh", { ...user, must_change_password: true });
  });

  it("replaces the tokens invalidated by the password change", async () => {
    const wrapper = mount(ChangePasswordView, { global: { stubs: { AppLogo: true } } });
    const inputs = wrapper.findAll("input");
    await inputs[0]!.setValue("Temporary1!");
    await inputs[1]!.setValue("Permanent123!");
    await inputs[2]!.setValue("Permanent123!");
    await wrapper.get("form").trigger("submit");
    await flushPromises();

    expect(mocks.login).toHaveBeenCalledWith({ email: "new@example.com", password: "Permanent123!" });
    expect(useAuthStore().accessToken).toBe("new-access");
    expect(useAuthStore().user?.must_change_password).toBe(false);
    expect(mocks.push).toHaveBeenCalledWith({ name: "dashboard" });
  });
});
