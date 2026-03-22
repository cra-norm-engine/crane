import { computed, ref } from "vue";
import { defineStore } from "pinia";

const STORAGE_KEY = "cra-compliance-auth";

interface AuthState {
  accessToken: string | null;
  userEmail: string | null;
}

export const useAuthStore = defineStore("auth", () => {
  const accessToken = ref<string | null>(null);
  const userEmail = ref<string | null>(null);
  const isInitialized = ref(false);

  const isAuthenticated = computed(() => Boolean(accessToken.value));

  function initializeFromStorage(): void {
    const raw = window.localStorage.getItem(STORAGE_KEY);
    if (raw) {
      try {
        const parsed = JSON.parse(raw) as AuthState;
        accessToken.value = parsed.accessToken;
        userEmail.value = parsed.userEmail;
      } catch {
        window.localStorage.removeItem(STORAGE_KEY);
      }
    }
    isInitialized.value = true;
  }

  function login(email: string, token: string): void {
    accessToken.value = token;
    userEmail.value = email;
    window.localStorage.setItem(
      STORAGE_KEY,
      JSON.stringify({
        accessToken: token,
        userEmail: email,
      }),
    );
  }

  function logout(): void {
    accessToken.value = null;
    userEmail.value = null;
    window.localStorage.removeItem(STORAGE_KEY);
  }

  return {
    accessToken,
    userEmail,
    isInitialized,
    isAuthenticated,
    initializeFromStorage,
    login,
    logout,
  };
});
