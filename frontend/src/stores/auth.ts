import { computed, ref } from "vue";
import { defineStore } from "pinia";

const STORAGE_KEY = "cra-compliance-auth";

interface AuthUser {
  id: string;
  email: string;
  full_name: string;
  roles: string[];
  permissions: string[];
  is_active: boolean;
  auth_provider: string;
  must_change_password: boolean;
}

interface AuthState {
  accessToken: string | null;
  refreshToken: string | null;
  user: AuthUser | null;
}

export const useAuthStore = defineStore("auth", () => {
  const accessToken = ref<string | null>(null);
  const refreshToken = ref<string | null>(null);
  const user = ref<AuthUser | null>(null);
  const isInitialized = ref(false);

  const isAuthenticated = computed(() => Boolean(accessToken.value));
  const userRoles = computed(() => user.value?.roles ?? []);
  const roles = computed(() => user.value?.roles ?? []);
  const permissions = computed(() => user.value?.permissions ?? []);
  const userEmail = computed(() => user.value?.email ?? "");
  const userFullName = computed(() => user.value?.full_name ?? "");

  function hasRole(role: string): boolean {
    return userRoles.value.includes(role);
  }

  function hasAnyRole(roleNames: string[]): boolean {
    return roleNames.some((role) => userRoles.value.includes(role));
  }

  function hasPermission(permission: string): boolean {
    return permissions.value.includes(permission);
  }

  function hasAnyPermission(permissionNames: string[]): boolean {
    return permissionNames.some((permission) => permissions.value.includes(permission));
  }

  function initializeFromStorage(): void {
    const raw = window.localStorage.getItem(STORAGE_KEY);

    if (raw) {
      try {
        const parsed = JSON.parse(raw) as AuthState;
        accessToken.value = parsed.accessToken;
        refreshToken.value = parsed.refreshToken;
        user.value = parsed.user;
      } catch {
        window.localStorage.removeItem(STORAGE_KEY);
      }
    }

    isInitialized.value = true;
  }

  function setAuthState(state: AuthState): void {
    accessToken.value = state.accessToken;
    refreshToken.value = state.refreshToken;
    user.value = state.user;

    window.localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
  }

  function clearAuthState(): void {
    accessToken.value = null;
    refreshToken.value = null;
    user.value = null;
    window.localStorage.removeItem(STORAGE_KEY);
  }

  function login(
    accessTokenValue: string,
    refreshTokenValue: string,
    userData: AuthUser | null,
  ): void {
    setAuthState({
      accessToken: accessTokenValue,
      refreshToken: refreshTokenValue,
      user: userData,
    });
  }

  function logout(): void {
    clearAuthState();
  }

  function updateUser(patch: Partial<AuthUser>): void {
    if (!user.value) return;
    user.value = { ...user.value, ...patch };
    window.localStorage.setItem(
      STORAGE_KEY,
      JSON.stringify({ accessToken: accessToken.value, refreshToken: refreshToken.value, user: user.value }),
    );
  }

  return {
    accessToken,
    refreshToken,
    user,
    isInitialized,
    isAuthenticated,
    userRoles,
    roles,
    permissions,
    userEmail,
    userFullName,
    hasRole,
    hasAnyRole,
    hasPermission,
    hasAnyPermission,
    initializeFromStorage,
    login,
    logout,
    updateUser,
    setAuthState,
    clearAuthState,
  };
});