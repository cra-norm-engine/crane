import { createApp } from "vue"
import { createPinia } from "pinia"

import App from "./App.vue"
import router from "./router"
import "./styles.css"
import { useAppStore } from "@/stores/app"

const app = createApp(App)

app.use(createPinia())
app.use(router)

// Global Vue error handler for uncaught render and lifecycle errors
app.config.errorHandler = (err, _instance, info) => {
  console.error("[Vue Error]", err, info)
  // Wire to toast system (use() calls are already done, so store access is safe)
  const appStore = useAppStore()
  appStore.setGlobalError("An unexpected error occurred. Please refresh the page.")
}

app.mount("#app")