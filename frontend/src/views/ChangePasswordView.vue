<template>
  <section class="auth-shell">
    <div class="auth-card card change-card">

      <!-- Brand -->
      <div class="brand">
        <AppLogo :scale="1.2" />
      </div>

      <div class="divider" role="separator" />

      <!-- Heading -->
      <div class="heading-block">
        <h1 class="page-title change-heading">
          {{ isForced ? "Set a new password" : "Change password" }}
        </h1>
        <p v-if="isForced" class="muted change-tagline forced-note">
          Your account has a temporary password. Please set a new one before continuing.
        </p>
        <p v-else class="muted change-tagline">
          Enter your current password and choose a new one.
        </p>
      </div>

      <!-- Form -->
      <form class="change-form" novalidate @submit.prevent="handleSubmit">

        <label class="field">
          <span class="field-label">Current password</span>
          <input
            v-model="currentPassword"
            class="input"
            type="password"
            required
            autocomplete="current-password"
            :aria-invalid="!!error"
          />
        </label>

        <label class="field">
          <span class="field-label">New password</span>
          <input
            v-model="newPassword"
            class="input"
            type="password"
            required
            minlength="8"
            autocomplete="new-password"
            :aria-invalid="!!error"
          />
        </label>

        <label class="field">
          <span class="field-label">Confirm new password</span>
          <input
            v-model="confirmPassword"
            class="input"
            type="password"
            required
            minlength="8"
            autocomplete="new-password"
            :aria-invalid="!!error"
          />
        </label>

        <button
          class="button change-btn"
          type="submit"
          :disabled="loading"
          :aria-busy="loading"
        >
          <span v-if="loading" class="change-btn-loading">
            <span class="spinner spinner-sm" aria-hidden="true" />
            Saving…
          </span>
          <span v-else>Set new password</span>
        </button>

      </form>

      <!-- Error -->
      <p v-if="error" class="change-error" role="alert" aria-live="assertive">
        <svg
          class="change-error-icon"
          viewBox="0 0 20 20"
          fill="none"
          stroke="currentColor"
          stroke-width="1.8"
          stroke-linecap="round"
          stroke-linejoin="round"
          aria-hidden="true"
        >
          <path d="M10 2 2 16h16L10 2z" />
          <line x1="10" y1="9" x2="10" y2="12" />
          <circle cx="10" cy="14.5" r="0.5" fill="currentColor" />
        </svg>
        {{ error }}
      </p>

      <!-- Back link — only when not forced -->
      <RouterLink
        v-if="!isForced"
        :to="{ name: 'dashboard' }"
        class="back-link muted"
      >
        ← Back to dashboard
      </RouterLink>

    </div>
  </section>
</template>

<script setup lang="ts">
import { computed, ref } from "vue";
import { RouterLink, useRouter } from "vue-router";

import { changePasswordRequest } from "@/services/auth-service";
import { useAuthStore } from "@/stores/auth";
import AppLogo from "@/components/AppLogo.vue";

const authStore = useAuthStore();
const router    = useRouter();

const currentPassword  = ref("");
const newPassword      = ref("");
const confirmPassword  = ref("");
const loading          = ref(false);
const error            = ref<string | null>(null);

// Forced when the user still has must_change_password set.
const isForced = computed(() => authStore.user?.must_change_password === true);

async function handleSubmit(): Promise<void> {
  error.value = null;

  if (newPassword.value !== confirmPassword.value) {
    error.value = "New passwords do not match.";
    return;
  }

  if (newPassword.value.length < 8) {
    error.value = "New password must be at least 8 characters.";
    return;
  }

  loading.value = true;
  try {
    await changePasswordRequest({
      current_password: currentPassword.value,
      new_password:     newPassword.value,
    });

    // Clear the forced-change flag in the local store so the guard passes.
    authStore.updateUser({ must_change_password: false });

    await router.push({ name: "dashboard" });
  } catch (err: unknown) {
    error.value =
      err instanceof Error ? err.message : "Failed to change password. Please try again.";
  } finally {
    loading.value = false;
  }
}
</script>

<style scoped>
.change-card {
  display: grid;
  gap: 1.15rem;
  padding: 1.75rem;
}

.brand {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.65rem;
}


.heading-block {
  display: grid;
  gap: 0.2rem;
}

.change-heading {
  font-size: 1.5rem;
}

.change-tagline {
  margin: 0;
  font-size: var(--text-sm);
}

.forced-note {
  color: var(--color-warning-text);
  background: var(--color-warning-bg);
  border: 1px solid var(--color-warning-border);
  border-radius: var(--radius-md);
  padding: 0.6rem 0.8rem;
  font-size: var(--text-sm);
}

.change-form {
  display: grid;
  gap: 0.9rem;
}

.change-btn {
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.55rem;
  margin-top: 0.25rem;
}

.change-btn-loading {
  display: inline-flex;
  align-items: center;
  gap: 0.55rem;
}

.change-error {
  display: flex;
  align-items: flex-start;
  gap: 0.5rem;
  margin: 0;
  color: var(--color-danger-text);
  background: var(--color-danger-bg);
  border: 1px solid var(--color-danger-border);
  border-radius: var(--radius-md);
  padding: 0.75rem 0.9rem;
  font-size: var(--text-sm);
  line-height: 1.5;
}

.change-error-icon {
  width: 16px;
  height: 16px;
  flex-shrink: 0;
  margin-top: 0.1rem;
}

.back-link {
  text-align: center;
  font-size: var(--text-sm);
  text-decoration: none;
}

.back-link:hover {
  color: var(--color-text);
}
</style>
