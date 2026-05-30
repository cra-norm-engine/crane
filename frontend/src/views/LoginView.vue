<template>
  <div class="auth-layout">

    <!-- ═══════════ Brand panel (always dark) ═══════════ -->
    <section class="brand-panel">

      <div class="bp-mark">
        <AppLogo on-dark :scale="1.4" />
      </div>

      <!-- Centre content -->
      <div class="bp-center">
        <span class="bp-eyebrow">
          <svg class="bp-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round">
            <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
            <path d="M9 12l2 2 4-4"/>
          </svg>
          EU Cyber Resilience Act
        </span>

        <h1 class="bp-heading">Compliance,<br>under control.</h1>

        <p class="bp-desc">
          One workspace for CRA conformity — from product scope and risk
          to vulnerability handling and audit-ready evidence.
        </p>

        <ul class="bp-feats">
          <li class="bp-feat">
            <span class="bp-feat-check">
              <svg class="bp-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round"><path d="M20 6L9 17l-5-5"/></svg>
            </span>
            Continuous conformity tracking
          </li>
          <li class="bp-feat">
            <span class="bp-feat-check">
              <svg class="bp-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round"><path d="M20 6L9 17l-5-5"/></svg>
            </span>
            Vulnerability handling &amp; PSIRT
          </li>
          <li class="bp-feat">
            <span class="bp-feat-check">
              <svg class="bp-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round"><path d="M20 6L9 17l-5-5"/></svg>
            </span>
            Audit-ready evidence &amp; reporting
          </li>
        </ul>
      </div>

      <!-- Footer -->
      <div class="bp-foot">
        <span>© 2026 Cyber Resilience Act Norm Engine</span>
        <span class="bp-dot" aria-hidden="true"></span>
        <span>Privacy</span>
        <span class="bp-dot" aria-hidden="true"></span>
        <span>Security</span>
      </div>
    </section>

    <!-- ═══════════ Form panel ═══════════ -->
    <section class="form-panel">
      <div class="form-wrap">

        <!-- Mobile-only logo (brand panel hidden on small screens) -->
        <div class="mobile-brand">
          <AppLogo :scale="1.1" />
        </div>

        <!-- Heading -->
        <div class="form-head">
          <h2>Sign in</h2>
          <p>Access your CRA compliance workspace.</p>
        </div>

        <!-- Login form -->
        <form class="login-form" novalidate @submit.prevent="handleLogin">

          <!-- Email -->
          <div class="f-field">
            <label class="f-label" for="email">Email</label>
            <div class="inp-wrap">
              <svg class="inp-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round">
                <rect x="3" y="5" width="18" height="14" rx="2"/>
                <path d="m3 7 9 6 9-6"/>
              </svg>
              <input
                id="email"
                v-model.trim="email"
                class="inp"
                type="email"
                placeholder="admin@example.com"
                required
                autocomplete="username"
                :aria-invalid="!!error"
              />
            </div>
          </div>

          <!-- Password -->
          <div class="f-field">
            <div class="f-label-row">
              <label class="f-label" for="password">Password</label>
            </div>
            <div class="inp-wrap">
              <svg class="inp-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round">
                <rect x="3" y="11" width="18" height="10" rx="2"/>
                <path d="M7 11V7a5 5 0 0 1 10 0v4"/>
              </svg>
              <input
                id="password"
                v-model="password"
                class="inp inp--has-toggle"
                :type="showPassword ? 'text' : 'password'"
                placeholder="Enter your password"
                required
                autocomplete="current-password"
                :aria-invalid="!!error"
              />
              <button
                class="pw-toggle"
                type="button"
                :aria-label="showPassword ? 'Hide password' : 'Show password'"
                :aria-pressed="showPassword"
                @click="showPassword = !showPassword"
              >
                <!-- Eye open -->
                <svg v-if="!showPassword" class="bp-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round">
                  <path d="M2 12s3.5-7 10-7 10 7 10 7-3.5 7-10 7-10-7-10-7z"/>
                  <circle cx="12" cy="12" r="3"/>
                </svg>
                <!-- Eye off -->
                <svg v-else class="bp-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round">
                  <path d="M2 12s3.5-7 10-7c2 0 3.8.6 5.3 1.5M22 12s-3.5 7-10 7c-2 0-3.8-.6-5.3-1.5"/>
                  <path d="M9.5 9.5a3 3 0 0 0 4.2 4.2"/>
                  <path d="M3 3l18 18"/>
                </svg>
              </button>
            </div>
          </div>

          <!-- Remember me -->
          <label class="remember">
            <input v-model="remember" class="remember-ck" type="checkbox" />
            <span>Keep me signed in on this device</span>
          </label>

          <!-- Submit -->
          <button class="btn btn-primary" type="submit" :disabled="loading" :aria-busy="loading">
            <span v-if="loading" class="btn-loading">
              <span class="spinner spinner-sm" aria-hidden="true" />
              Signing in…
            </span>
            <template v-else>
              Sign in
              <svg class="bp-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round">
                <path d="M5 12h14M13 6l6 6-6 6"/>
              </svg>
            </template>
          </button>

        </form>

        <!-- Error banner -->
        <p v-if="error" class="login-error" role="alert" aria-live="assertive">
          <svg class="login-error-icon" viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
            <path d="M10 2 2 16h16L10 2z"/>
            <line x1="10" y1="9" x2="10" y2="12"/>
            <circle cx="10" cy="14.5" r="0.5" fill="currentColor"/>
          </svg>
          {{ error }}
        </p>

        <!-- Divider -->
        <div class="divider"><span>or</span></div>

        <!-- SSO -->
        <button class="btn btn-ghost" type="button" @click="handleSso">
          <svg class="bp-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round">
            <circle cx="12" cy="12" r="9"/>
            <path d="M12 8v4l3 3"/>
            <path d="M3.6 9h16.8"/>
            <path d="M3.6 15h16.8"/>
          </svg>
          Continue with SSO / LDAP
        </button>

        <!-- Admin contact -->
        <p class="admin-note">New to CRANE? <a href="#">Contact your administrator</a></p>

      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import { ref } from "vue";
import { useRoute, useRouter } from "vue-router";

import { fetchCurrentUser, loginRequest } from "@/services/auth-service";
import { useAuthStore } from "@/stores/auth";
import type { ApiError } from "@/services/error-handler";
import AppLogo from "@/components/AppLogo.vue";

/* ── Reactive form state ─────────────────────── */
const email        = ref("");
const password     = ref("");
const loading      = ref(false);
const error        = ref<string | null>(null);
const showPassword = ref(false);
const remember     = ref(false);

/* ── Composables ─────────────────────────────── */
const authStore = useAuthStore();
const router    = useRouter();
const route     = useRoute();

/* ── Login handler ───────────────────────────── */
async function handleLogin(): Promise<void> {
  loading.value = true;
  error.value   = null;

  try {
    const tokenResponse = await loginRequest({ email: email.value, password: password.value });
    const user = await fetchCurrentUser(tokenResponse.access_token);
    authStore.login(tokenResponse.access_token, tokenResponse.refresh_token, user);

    const redirect = typeof route.query.redirect === "string" ? route.query.redirect : "/";
    await router.push(redirect);
  } catch (err: unknown) {
    if (err instanceof Error && "userMessage" in err) {
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

function handleSso(): void {
  /* SSO/LDAP flow — placeholder for future integration */
}
</script>

<style scoped>
/* ── Full-screen two-column layout ─────────────── */
.auth-layout {
  display: grid;
  grid-template-columns: 1.08fr 0.92fr;
  min-height: 100vh;
}

/* ═══════════════ Brand panel ═══════════════ */
.brand-panel {
  position: relative;
  overflow: hidden;
  padding: 44px 52px;
  display: flex;
  flex-direction: column;
  /* Always dark regardless of app theme */
  background:
    radial-gradient(120% 90% at 18% 8%, oklch(0.34 0.07 150) 0%, transparent 52%),
    radial-gradient(90% 70% at 95% 100%, oklch(0.30 0.06 160) 0%, transparent 55%),
    linear-gradient(158deg, oklch(0.19 0.026 155) 0%, oklch(0.125 0.016 150) 62%, oklch(0.10 0.01 150) 100%);
  color: oklch(0.88 0.012 150);
}

/* Faint dot-grid texture */
.brand-panel::before {
  content: '';
  position: absolute;
  inset: 0;
  background-image:
    linear-gradient(oklch(0.7 0.05 150 / 0.05) 1px, transparent 1px),
    linear-gradient(90deg, oklch(0.7 0.05 150 / 0.05) 1px, transparent 1px);
  background-size: 46px 46px;
  mask-image: radial-gradient(circle at 30% 30%, black 0%, transparent 78%);
  pointer-events: none;
}

.brand-panel > * { position: relative; z-index: 1; }

.bp-mark { display: flex; align-items: flex-start; }

/* Centre block */
.bp-center { margin: auto 0; max-width: 30rem; }

.bp-eyebrow {
  display: inline-flex;
  align-items: center;
  gap: 7px;
  font-size: 11.5px;
  font-weight: 600;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  color: oklch(0.80 0.08 150);
  background: oklch(0.5 0.08 150 / 0.16);
  border: 1px solid oklch(0.6 0.08 150 / 0.25);
  padding: 5px 11px;
  border-radius: 999px;
  margin-bottom: 22px;
}

.bp-heading {
  font-size: 34px;
  font-weight: 700;
  letter-spacing: -0.02em;
  line-height: 1.12;
  margin: 0 0 14px;
  color: white;
}

.bp-desc {
  font-size: 15px;
  color: oklch(0.80 0.015 150);
  margin: 0 0 30px;
  max-width: 26rem;
  line-height: 1.55;
}

.bp-feats {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.bp-feat {
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 14px;
  color: oklch(0.86 0.012 150);
}

.bp-feat-check {
  width: 26px;
  height: 26px;
  border-radius: 8px;
  flex-shrink: 0;
  background: oklch(0.5 0.10 150 / 0.18);
  border: 1px solid oklch(0.6 0.09 150 / 0.3);
  color: oklch(0.72 0.16 145);
  display: grid;
  place-items: center;
}

/* Footer */
.bp-foot {
  display: flex;
  align-items: center;
  gap: 14px;
  margin-top: 40px;
  font-size: 12px;
  color: oklch(0.66 0.012 150);
}

.bp-dot {
  width: 3px;
  height: 3px;
  border-radius: 50%;
  background: currentColor;
  opacity: 0.5;
}

/* Icon sizing */
.bp-icon { width: 14px; height: 14px; stroke-width: 1.8; flex-shrink: 0; }

/* ═══════════════ Form panel ═══════════════ */
.form-panel {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 44px;
  background: var(--color-bg);
}

.form-wrap { width: 100%; max-width: 380px; }

/* Mobile brand — hidden on desktop */
.mobile-brand {
  display: none;
  margin-bottom: 28px;
}

.form-head h2 {
  font-size: 24px;
  font-weight: 700;
  letter-spacing: -0.015em;
  margin: 0 0 6px;
  color: var(--color-text);
}

.form-head p {
  color: var(--color-text-muted);
  margin: 0 0 28px;
  font-size: 14px;
}

/* ── Field layout ─────────────────── */
.login-form { display: flex; flex-direction: column; gap: 16px; }

.f-field { display: flex; flex-direction: column; gap: 6px; }

.f-label {
  font-size: 12.5px;
  font-weight: 600;
  color: var(--color-text-muted);
}

.f-label-row {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
}

.inp-wrap { position: relative; display: flex; align-items: center; }

.inp-icon {
  position: absolute;
  left: 13px;
  width: 15px;
  height: 15px;
  flex-shrink: 0;
  color: var(--color-text-muted);
  opacity: 0.5;
  pointer-events: none;
}

.inp {
  width: 100%;
  height: 46px;
  padding: 0 14px 0 40px;
  border-radius: var(--radius-md);
  border: 1px solid var(--color-border-strong, var(--color-border));
  background: var(--color-surface);
  color: var(--color-text);
  font: inherit;
  font-size: 14px;
  transition: border-color var(--t-fast), box-shadow var(--t-fast);
}

.inp::placeholder { color: var(--color-text-muted); opacity: 0.5; }

.inp:focus {
  outline: none;
  border-color: var(--color-primary);
  box-shadow: 0 0 0 3px color-mix(in srgb, var(--color-primary) 15%, transparent);
}

.inp--has-toggle { padding-right: 46px; }

.pw-toggle {
  position: absolute;
  right: 6px;
  width: 34px;
  height: 34px;
  border: none;
  background: transparent;
  color: var(--color-text-muted);
  cursor: pointer;
  display: grid;
  place-items: center;
  border-radius: var(--radius-md);
  transition: background var(--t-fast), color var(--t-fast);
}

.pw-toggle:hover {
  background: var(--color-surface-elevated);
  color: var(--color-text);
}

/* ── Remember me ──────────────────── */
.remember {
  display: flex;
  align-items: center;
  gap: 9px;
  cursor: pointer;
  user-select: none;
  margin: 2px 0 4px;
}

.remember-ck {
  appearance: none;
  -webkit-appearance: none;
  width: 18px;
  height: 18px;
  flex-shrink: 0;
  border: 1.5px solid var(--color-border-strong, var(--color-border));
  border-radius: 5px;
  background: var(--color-surface);
  cursor: pointer;
  position: relative;
  transition: background var(--t-fast), border-color var(--t-fast);
}

.remember-ck:hover  { border-color: var(--color-primary); }

.remember-ck:focus-visible {
  outline: 2px solid var(--color-primary);
  outline-offset: 2px;
}

.remember-ck:checked {
  background: var(--color-primary);
  border-color: var(--color-primary);
  background-image: url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='white' stroke-width='3.4' stroke-linecap='round' stroke-linejoin='round'><path d='M20 6L9 17l-5-5'/></svg>");
  background-size: 11px 11px;
  background-position: center;
  background-repeat: no-repeat;
}

.remember span { font-size: 13px; color: var(--color-text-muted); }

/* ── Buttons ──────────────────────── */
.btn {
  width: 100%;
  height: 46px;
  border-radius: var(--radius-md);
  border: 1px solid transparent;
  cursor: pointer;
  font: 600 14px/1 inherit;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  transition: filter var(--t-fast), background var(--t-fast), border-color var(--t-fast);
}

.btn-primary {
  color: white;
  background: linear-gradient(180deg, var(--color-primary-2, var(--color-primary)) 0%, var(--color-primary) 100%);
  box-shadow: 0 1px 2px rgba(20, 40, 25, 0.18);
}

.btn-primary:hover:not(:disabled)  { filter: brightness(1.06); }
.btn-primary:active:not(:disabled) { filter: brightness(0.97); }
.btn-primary:disabled { opacity: 0.6; cursor: not-allowed; }

.btn-ghost {
  background: var(--color-surface);
  border-color: var(--color-border-strong, var(--color-border));
  color: var(--color-text);
}

.btn-ghost:hover { background: var(--color-surface-elevated); }

.btn-loading {
  display: inline-flex;
  align-items: center;
  gap: 8px;
}

/* ── Error banner ─────────────────── */
.login-error {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  margin: 4px 0 0;
  color: var(--color-danger-text);
  background: var(--color-danger-bg);
  border: 1px solid var(--color-danger-border);
  border-radius: var(--radius-md);
  padding: 12px 14px;
  font-size: 13px;
  line-height: 1.5;
}

.login-error-icon { width: 15px; height: 15px; flex-shrink: 0; margin-top: 1px; }

/* ── Divider ──────────────────────── */
.divider {
  display: flex;
  align-items: center;
  gap: 12px;
  margin: 20px 0;
  color: var(--color-text-muted);
  font-size: 12px;
  opacity: 0.6;
}

.divider::before,
.divider::after {
  content: '';
  flex: 1;
  height: 1px;
  background: var(--color-border);
}

/* ── Admin note ───────────────────── */
.admin-note {
  text-align: center;
  margin: 14px 0 0;
  font-size: 13px;
  color: var(--color-text-muted);
}

.admin-note a {
  color: var(--color-primary);
  font-weight: 600;
  text-decoration: none;
}

.admin-note a:hover { text-decoration: underline; }

/* ═══════════════ Responsive ═══════════════ */
@media (max-width: 860px) {
  .auth-layout { grid-template-columns: 1fr; }
  .brand-panel { display: none; }
  .mobile-brand { display: block; }
  .form-panel { padding: 32px 24px; align-items: flex-start; padding-top: 9vh; }
}
</style>
