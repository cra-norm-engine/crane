<template>
  <section class="page">
    <div class="card" style="max-width: 420px; margin: 48px auto;">
      <h1 class="page-title">Login</h1>
      <p class="muted">Sign in to your account</p>

      <form @submit.prevent="handleLogin" style="display: grid; gap: 12px; margin-top: 16px;">
        <input v-model="email" type="email" placeholder="Email" required />
        <input v-model="password" type="password" placeholder="Password" required minlength="8" />
        <button type="submit" :disabled="loading">
          {{ loading ? "Signing in..." : "Sign in" }}
        </button>
      </form>

      <p v-if="error" class="error" style="margin-top: 12px;">
        {{ error }}
      </p>
    </div>
  </section>
</template>

<script setup lang="ts">
import { ref } from "vue";
import { useRoute, useRouter } from "vue-router";
import { useAuthStore } from "@/stores/auth";
import { loginRequest, fetchCurrentUser } from "@/services/auth-service";

const email = ref("");
const password = ref("");
const loading = ref(false);
const error = ref<string | null>(null);

const authStore = useAuthStore();
const router = useRouter();
const route = useRoute();

async function handleLogin(): Promise<void> {
  loading.value = true;
  error.value = null;

  try {
    const tokenResponse = await loginRequest({
      email: email.value,
      password: password.value,
    });

    const user = await fetchCurrentUser(tokenResponse.access_token);

    authStore.login(
      tokenResponse.access_token,
      tokenResponse.refresh_token,
      user,
    );

    const redirect =
      typeof route.query.redirect === "string" ? route.query.redirect : "/";

    await router.push(redirect);
  } catch (err: any) {
    error.value = err?.response?.data?.detail ?? "Login failed";
  } finally {
    loading.value = false;
  }
}
</script>

<style scoped>
.error {
  color: #d32f2f;
  font-size: 0.9rem;
}
</style>