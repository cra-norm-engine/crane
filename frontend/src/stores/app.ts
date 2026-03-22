import { defineStore } from "pinia";

export const useAppStore = defineStore("app", {
  state: () => ({
    appName: import.meta.env.VITE_APP_NAME || "CRA Compliance Tool",
    globalError: "" as string,
  }),
  actions: {
    setGlobalError(message: string) {
      this.globalError = message;
    },
    clearGlobalError() {
      this.globalError = "";
    },
  },
});