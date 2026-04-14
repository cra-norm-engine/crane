<template>
  <section class="auth-shell">
    <div class="auth-card card login-card">
      <div class="brand">
        <div class="brand-mark" aria-hidden="true">SA</div>
        <div>
          <div class="brand-title">SICH'AMAN</div>
          <div class="brand-sub">Single Source of Truth</div>
        </div>
      </div>

      <div class="separator"></div>

      <div class="heading-block">
        <h1 class="page-title">Sign in</h1>
        <p class="muted">Access your CRA compliance workspace.</p>
      </div>

      <form class="login-form" @submit.prevent="handleLogin">
        <label class="field">
          <span class="field-label">Email</span>
          <input
            v-model.trim="email"
            class="input"
            type="email"
            placeholder="admin@example.com"
            required
            autocomplete="username"
          />
        </label>

        <label class="field">
          <span class="field-label">Password</span>
          <input
            v-model="password"
            class="input"
            type="password"
            placeholder="Enter your password"
            required
            minlength="8"
            autocomplete="current-password"
          />
        </label>

        <button class="button" type="submit" :disabled="loading">
          {{ loading ? "Signing in..." : "Sign in" }}
        </button>
      </form>

      <p v-if="error" class="error-text">
        {{ error }}
      </p>
    </div>
  </section>
</template>

<script setup lang="ts">
import { ref } from "vue";
import { useRoute, useRouter } from "vue-router";

import { fetchCurrentUser, loginRequest } from "@/services/auth-service";
import { useAuthStore } from "@/stores/auth";

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

    authStore.login(tokenResponse.access_token, tokenResponse.refresh_token, user);

    const redirect = typeof route.query.redirect === "string" ? route.query.redirect : "/";
    await router.push(redirect);
  } catch (err: unknown) {
    if (err instanceof Error) {
      error.value = err.message;
    } else {
      error.value = "Login failed";
    }
  } finally {
    loading.value = false;
  }
}
</script>

<style scoped>
.login-card {
  display: grid;
  gap: 1rem;
}

.brand {
  display: flex;
  gap: 0.75rem;
  align-items: center;
}

.brand-mark {
  width: 44px;
  height: 44px;
  border-radius: 14px;
  display: grid;
  place-items: center;
  background: linear-gradient(145deg, rgba(14, 20, 14, 0.95), rgba(6, 10, 6, 0.92));
  border: 1px solid rgba(173, 214, 84, 0.22);
  box-shadow: 0 14px 30px rgba(0, 0, 0, 0.28);
  font-weight: 900;
  color: var(--color-primary-2);
}

.brand-title {
  font-weight: 800;
  letter-spacing: 0.05em;
}

.brand-sub {
  font-size: 0.8rem;
  color: var(--color-text-muted);
}

.separator {
  height: 1px;
  background: var(--color-border);
}

.heading-block {
  display: grid;
  gap: 0.25rem;
}

.login-form {
  display: grid;
  gap: 0.9rem;
}

.field {
  display: grid;
  gap: 0.4rem;
}

.field-label {
  font-size: 0.85rem;
  color: var(--color-text-muted);
}

.error-text {
  margin: 0;
  color: #fda4af;
  font-size: 0.95rem;
}
</style>
