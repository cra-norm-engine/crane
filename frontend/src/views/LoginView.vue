<template>
  <!--
    LoginView — full-screen authentication page.

    Layout: a centred card containing:
      • CRANE logo + product name
      • "Sign in" heading + tagline
      • Email + Password fields
      • Submit button with loading state
      • Inline error message on failure

    The .auth-shell and .auth-card classes are defined globally in
    styles.css.  All other styles are scoped to this view.
  -->
  <section class="auth-shell">
    <div class="auth-card card login-card">

      <!-- ── Brand block ──────────────────────────────── -->
      <div class="brand">
        <img src="/logo/darkFullLogo.svg"  alt="CRANE logo" class="brand-logo logo-dark"  />
        <img src="/logo/lightFullLogo.svg" alt="CRANE logo" class="brand-logo logo-light" />
      </div>

      <!-- Visual separator between logo and the form section -->
      <div class="divider" role="separator" />

      <!-- ── Heading ──────────────────────────────────── -->
      <div class="heading-block">
        <h1 class="page-title login-heading">Sign in</h1>
        <p class="muted login-tagline">Access your CRA compliance workspace.</p>
      </div>

      <!-- ── Login form ───────────────────────────────── -->
      <!--
        @submit.prevent stops the browser from doing a full-page POST.
        All submission logic is handled in handleLogin().
      -->
      <form class="login-form" novalidate @submit.prevent="handleLogin">

        <!-- Email field -->
        <label class="field">
          <span class="field-label">Email</span>
          <input
            v-model.trim="email"
            class="input"
            type="email"
            placeholder="admin@example.com"
            required
            autocomplete="username"
            :aria-invalid="!!error"
          />
        </label>

        <!-- Password field -->
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
            :aria-invalid="!!error"
          />
        </label>

        <!-- Submit button — shows spinner text while the request is in flight -->
        <button
          class="button login-btn"
          type="submit"
          :disabled="loading"
          :aria-busy="loading"
        >
          <span v-if="loading" class="login-btn-loading">
            <!--
              Inline spinner ring — uses global .spinner + .spinner-sm classes.
              aria-hidden because the button's text already communicates the state.
            -->
            <span class="spinner spinner-sm" aria-hidden="true" />
            Signing in…
          </span>
          <span v-else>Sign in</span>
        </button>

      </form>

      <!-- ── Error message ─────────────────────────────── -->
      <!--
        v-if keeps the element out of the DOM when there is no error
        so screen readers do not announce an empty region.
        role="alert" causes assistive technology to announce the error
        automatically when it appears.
      -->
      <p
        v-if="error"
        class="login-error"
        role="alert"
        aria-live="assertive"
      >
        <!-- Warning icon for quick visual scan -->
        <svg
          class="login-error-icon"
          viewBox="0 0 20 20"
          fill="none"
          stroke="currentColor"
          stroke-width="1.8"
          stroke-linecap="round"
          stroke-linejoin="round"
          aria-hidden="true"
        >
          <path d="M10 2 2 16h16L10 2z" />
          <line x1="10" y1="9"  x2="10" y2="12" />
          <circle cx="10" cy="14.5" r="0.5" fill="currentColor" />
        </svg>
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
import type { ApiError } from "@/services/error-handler";

/* ── Reactive form state ─────────────────────────── */
const email    = ref("");
const password = ref("");
const loading  = ref(false);
const error    = ref<string | null>(null);

/* ── Composables ─────────────────────────────────── */
const authStore = useAuthStore();
const router    = useRouter();
const route     = useRoute();

/* ── Login handler ───────────────────────────────── */
/**
 * Submits credentials, stores the returned tokens and user profile,
 * then redirects to the originally requested URL (or "/").
 */
async function handleLogin(): Promise<void> {
  loading.value = true;
  error.value   = null;

  try {
    /* Step 1 — exchange email + password for access + refresh tokens */
    const tokenResponse = await loginRequest({
      email:    email.value,
      password: password.value,
    });

    /* Step 2 — fetch the authenticated user's profile */
    const user = await fetchCurrentUser(tokenResponse.access_token);

    /* Step 3 — persist auth state in the Pinia store */
    authStore.login(
      tokenResponse.access_token,
      tokenResponse.refresh_token,
      user,
    );

    /* Step 4 — navigate to the redirect target or home */
    const redirect =
      typeof route.query.redirect === "string" ? route.query.redirect : "/";
    await router.push(redirect);

  } catch (err: unknown) {
    /* Show the user-friendly error message from ApiError, or fallback to generic message */
    if (err instanceof Error && 'userMessage' in err) {
      error.value = (err as ApiError).userMessage || err.message;
    } else if (err instanceof Error) {
      error.value = err.message;
    } else {
      error.value = "Login failed. Please try again.";
    }
  } finally {
    loading.value = false;
  }
}
</script>

<style scoped>
/* ── Login card ───────────────────────────────────── */
/* Provides the grid layout inside the .card shell */
.login-card {
  display: grid;
  gap: 1.15rem;
  /* Slightly extra padding for a more comfortable login experience */
  padding: 1.75rem;
}

/* ── Brand block ──────────────────────────────────── */
.brand {
  display: flex;
  justify-content: center;
  align-items: center;
}

.brand-logo {
  max-width: 220px;
  max-height: 100px;
  width: 100%;
  object-fit: contain;
}

/* Show dark logo by default; swap to light logo in light mode */
.logo-light { display: none; }
:root[data-theme="light"] .logo-dark  { display: none; }
:root[data-theme="light"] .logo-light { display: block; }

/* ── Heading block ────────────────────────────────── */
.heading-block {
  display: grid;
  gap: 0.2rem;
}

/* Override the global page-title size — login heading should be smaller */
.login-heading {
  font-size: 1.5rem;
}

.login-tagline {
  margin: 0;
  font-size: var(--text-sm);
}

/* ── Form ─────────────────────────────────────────── */
.login-form {
  display: grid;
  gap: 0.9rem;
}

/* ── Submit button ────────────────────────────────── */
/* Fills the full width of the form for an obvious call-to-action */
.login-btn {
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.55rem;
  margin-top: 0.25rem;
}

/* Row inside the button when loading — spinner + label side by side */
.login-btn-loading {
  display: inline-flex;
  align-items: center;
  gap: 0.55rem;
}

/* ── Error message ────────────────────────────────── */
.login-error {
  /* Flex row: icon + text */
  display: flex;
  align-items: flex-start;
  gap: 0.5rem;
  margin: 0;

  /* Use the danger palette for consistency with other error states */
  color: var(--color-danger-text);
  background: var(--color-danger-bg);
  border: 1px solid var(--color-danger-border);
  border-radius: var(--radius-md);
  padding: 0.75rem 0.9rem;
  font-size: var(--text-sm);
  line-height: 1.5;
}

.login-error-icon {
  width: 16px;
  height: 16px;
  flex-shrink: 0;
  margin-top: 0.1rem; /* align icon with the first line of text */
}
</style>
