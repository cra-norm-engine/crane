import { defineStore } from "pinia"
import { useToast } from "@/composables/useToast"

type ThemeMode = "dark" | "light";

export const useAppStore = defineStore("app", {
  state: () => ({
    appName: import.meta.env.VITE_APP_NAME || "CRANE",
    globalError: "" as string,
    themeMode: "dark" as ThemeMode,
    themeInitialized: false,
  }),
  actions: {
    setGlobalError(message: string) {
      this.globalError = message;
      const { showToast } = useToast()
      showToast({ type: 'error', message })
    },
    clearGlobalError() {
      this.globalError = "";
    },
    initializeTheme() {
      if (this.themeInitialized) {
        this.applyTheme();
        return;
      }

      if (typeof window !== "undefined") {
        const savedTheme = window.localStorage.getItem("crane-theme");
        if (savedTheme === "dark" || savedTheme === "light") {
          this.themeMode = savedTheme;
        }
      }

      this.themeInitialized = true;
      this.applyTheme();
    },
    setTheme(theme: ThemeMode) {
      this.themeMode = theme;
      this.themeInitialized = true;
      this.applyTheme();
    },
    toggleTheme() {
      this.setTheme(this.themeMode === "dark" ? "light" : "dark");
    },
    applyTheme() {
      if (typeof document !== "undefined") {
        document.documentElement.dataset.theme = this.themeMode;
      }

      if (typeof window !== "undefined") {
        window.localStorage.setItem("crane-theme", this.themeMode);
      }
    },
  },
});
