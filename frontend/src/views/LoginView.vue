<!--
  CRANE — CRA Norm Engine
  Copyright (C) 2026 Ali Mohammad Hosseini
  SPDX-License-Identifier: AGPL-3.0-or-later
  This file is part of CRANE, free software under the GNU AGPL v3.0 or later.
  See <https://www.gnu.org/licenses/>.
-->
<template>
  <div class="auth-layout">

    <!-- ═══════════ Brand panel (always dark) ═══════════ -->
    <section class="brand-panel">

      <!-- Floating particles -->
      <div class="bp-particles" aria-hidden="true">
        <span style="--px: 8%;  --ps: 5px; --pd: 16s; --pdelay: -2s;"></span>
        <span style="--px: 22%; --ps: 8px; --pd: 22s; --pdelay: -9s;"></span>
        <span style="--px: 38%; --ps: 4px; --pd: 14s; --pdelay: -5s;"></span>
        <span style="--px: 53%; --ps: 7px; --pd: 24s; --pdelay: -14s;"></span>
        <span style="--px: 67%; --ps: 5px; --pd: 18s; --pdelay: -3s;"></span>
        <span style="--px: 79%; --ps: 9px; --pd: 26s; --pdelay: -11s;"></span>
        <span style="--px: 91%; --ps: 4px; --pd: 15s; --pdelay: -7s;"></span>
        <span style="--px: 14%; --ps: 6px; --pd: 20s; --pdelay: -16s;"></span>
        <span style="--px: 60%; --ps: 4px; --pd: 13s; --pdelay: -1s;"></span>
        <span style="--px: 85%; --ps: 6px; --pd: 19s; --pdelay: -6s;"></span>
      </div>

      <div class="bp-mark">
        <AppLogo on-dark :scale="1.4" />
        <span class="bp-status"><span aria-hidden="true"></span>Secure workspace</span>
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

        <h1 class="bp-heading">Move from CRA requirements<br>to defensible evidence.</h1>

        <p class="bp-desc">
          CRANE connects product scope, risk, vulnerability handling, and
          technical documentation in one traceable workflow.
        </p>

        <ul class="bp-feats">
          <li class="bp-feat">
            <span class="bp-feat-check">
              <svg class="bp-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round"><path d="M20 6L9 17l-5-5"/></svg>
            </span>
            Guide every product through its compliance journey
          </li>
          <li class="bp-feat">
            <span class="bp-feat-check">
              <svg class="bp-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round"><path d="M20 6L9 17l-5-5"/></svg>
            </span>
            Coordinate risks, vulnerabilities, and releases
          </li>
          <li class="bp-feat">
            <span class="bp-feat-check">
              <svg class="bp-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round"><path d="M20 6L9 17l-5-5"/></svg>
            </span>
            Maintain audit-ready evidence and reports
          </li>
        </ul>
      </div>

      <!-- Footer -->
      <div class="bp-foot">
        <span>© 2026 Ali Mohammad Hosseini</span>
        <span class="bp-dot" aria-hidden="true"></span>
        <a href="https://github.com/cra-norm-engine/crane" target="_blank" rel="noopener">Source (AGPL-3.0)</a>
        <span class="bp-dot" aria-hidden="true"></span>
        <span>CRANE v1.2.0</span>
      </div>
    </section>

    <!-- ═══════════ Form panel ═══════════ -->
    <section class="form-panel">
      <div class="form-wrap">

        <!-- Mobile-only logo (brand panel hidden on small screens) -->
        <div class="mobile-brand">
          <AppLogo :scale="1.1" />
        </div>

        <div class="auth-card">
          <!-- Heading -->
          <div class="form-head">
            <span class="form-eyebrow">
              <svg class="bp-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
                <rect x="5" y="10" width="14" height="11" rx="2"/><path d="M8 10V7a4 4 0 0 1 8 0v3"/>
              </svg>
              Secure sign-in
            </span>
            <h2>Welcome back</h2>
            <p>Sign in to continue to your CRANE workspace.</p>
          </div>

          <!-- Error banner -->
          <p v-if="error" id="login-error" class="login-error" role="alert" aria-live="assertive">
            <svg class="login-error-icon" viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
              <circle cx="10" cy="10" r="8"/><line x1="10" y1="6" x2="10" y2="10"/><circle cx="10" cy="13.5" r="0.5" fill="currentColor"/>
            </svg>
            <span><strong>Unable to sign in</strong>{{ error }}</span>
          </p>

          <!-- Login form -->
          <form class="login-form" @submit.prevent="handleLogin">

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
                placeholder="you@company.com"
                required
                autocomplete="username"
                autocapitalize="none"
                spellcheck="false"
                autofocus
                :disabled="loading"
                :aria-invalid="!!error"
                :aria-describedby="error ? 'login-error' : undefined"
                @input="error = null"
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
                :disabled="loading"
                :aria-invalid="!!error"
                :aria-describedby="error ? 'login-error' : undefined"
                @input="error = null"
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

          <!-- Submit -->
          <button class="btn btn-primary" type="submit" :disabled="loading" :aria-busy="loading">
            <span v-if="loading" class="btn-loading">
              <span class="spinner spinner-sm" aria-hidden="true" />
              Signing in…
            </span>
            <template v-else>
              Sign in
              <svg class="bp-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
                <path d="M5 12h14M13 6l6 6-6 6"/>
              </svg>
            </template>
          </button>

          </form>

        <!-- Divider -->
          <div class="divider"><span>or use your organisation</span></div>

        <!-- SSO -->
          <button class="btn btn-ghost" type="button" :disabled="loading" @click="handleSso">
          <svg class="bp-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round">
            <circle cx="12" cy="12" r="9"/>
            <path d="M12 8v4l3 3"/>
            <path d="M3.6 9h16.8"/>
            <path d="M3.6 15h16.8"/>
          </svg>
            Continue with SSO / LDAP
          </button>

          <!-- Admin contact -->
          <p class="admin-note">Need access? Contact your CRANE administrator.</p>
        </div>

        <p class="security-note">
          <svg class="bp-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/><path d="M9 12l2 2 4-4"/></svg>
          Protected access · Activity is recorded for auditability
        </p>

      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import { ref } from "vue";
import { useRoute, useRouter } from "vue-router";

import { fetchCurrentUser, loginRequest } from "@/services/auth-service";
import { useAuthStore } from "@/stores/auth";
import { useAppStore } from "@/stores/app";
import { useToast } from "@/composables/useToast";
import type { ApiError } from "@/services/error-handler";
import AppLogo from "@/components/AppLogo.vue";

/* ── Reactive form state ─────────────────────── */
const email        = ref("");
const password     = ref("");
const loading      = ref(false);
const error        = ref<string | null>(null);
const showPassword = ref(false);

/* ── Composables ─────────────────────────────── */
const authStore = useAuthStore();
const appStore  = useAppStore();
const router    = useRouter();
const route     = useRoute();
const { showToast } = useToast();

/* ── Login handler ───────────────────────────── */
async function handleLogin(): Promise<void> {
  loading.value = true;
  error.value   = null;

  try {
    const tokenResponse = await loginRequest({ email: email.value, password: password.value });
    const user = await fetchCurrentUser(tokenResponse.access_token);
    authStore.login(tokenResponse.access_token, tokenResponse.refresh_token, user);

    // Apply the user's server-synced theme so the choice follows them across devices.
    if (user.preferences?.theme === "dark" || user.preferences?.theme === "light") {
      appStore.setTheme(user.preferences.theme);
    }

    // Honour an explicit deep-link redirect; otherwise use the user's preferred
    // landing page. Lazy import avoids a router <-> view circular import.
    if (typeof route.query.redirect === "string") {
      await router.push(route.query.redirect);
    } else {
      const { resolveLandingRouteName } = await import("@/router");
      await router.push({ name: resolveLandingRouteName() });
    }
    setTimeout(() => window.dispatchEvent(new Event("crane-guide-hint")), 200);
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
  showToast({ type: "info", message: "SSO / LDAP sign-in is disabled by your administrator." });
}
</script>

<style scoped>
/* ── Full-screen two-column layout ─────────────── */
.auth-layout {
  display: grid;
  grid-template-columns: minmax(480px, 1.06fr) minmax(440px, 0.94fr);
  min-height: 100vh;
  background: var(--color-bg);
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

/* Roaming glow orbs */
.brand-panel::after {
  content: '';
  position: absolute;
  inset: -20%;
  background:
    radial-gradient(30rem 30rem at 50% 50%, oklch(0.58 0.11 155 / 0.26) 0%, transparent 58%),
    radial-gradient(24rem 24rem at 50% 50%, oklch(0.64 0.10 168 / 0.20) 0%, transparent 60%);
  background-position: 15% 20%, 80% 75%;
  background-repeat: no-repeat;
  filter: blur(6px);
  animation: bp-drift 20s ease-in-out infinite alternate;
  pointer-events: none;
}

@keyframes bp-drift {
  0%   { background-position: 12% 18%, 82% 78%; transform: scale(1)    rotate(0deg); }
  33%  { background-position: 40% 60%, 60% 30%; transform: scale(1.12) rotate(4deg); }
  66%  { background-position: 70% 25%, 25% 70%; transform: scale(0.96) rotate(-3deg); }
  100% { background-position: 12% 18%, 82% 78%; transform: scale(1)    rotate(0deg); }
}

/* Floating particles rising through the panel */
.bp-particles {
  position: absolute;
  inset: 0;
  overflow: hidden;
  pointer-events: none;
}

.bp-particles span {
  position: absolute;
  bottom: -8%;
  width: var(--ps, 6px);
  height: var(--ps, 6px);
  border-radius: 50%;
  background: oklch(0.78 0.09 155 / 0.5);
  box-shadow: 0 0 10px 1px oklch(0.78 0.09 155 / 0.35);
  left: var(--px, 50%);
  animation: bp-float var(--pd, 18s) linear infinite;
  animation-delay: var(--pdelay, 0s);
}

@keyframes bp-float {
  0%   { transform: translateY(0) translateX(0);    opacity: 0; }
  10%  { opacity: 0.8; }
  50%  { transform: translateY(-58vh) translateX(14px); }
  90%  { opacity: 0.5; }
  100% { transform: translateY(-118vh) translateX(-10px); opacity: 0; }
}

@media (prefers-reduced-motion: reduce) {
  .brand-panel::after { animation: none; }
  .bp-particles span { animation: none; display: none; }
}

.brand-panel > * { position: relative; z-index: 1; }
.brand-panel > .bp-particles { z-index: 0; }

.bp-mark {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 24px;
}

.bp-status {
  display: inline-flex;
  align-items: center;
  gap: 7px;
  padding: 6px 10px;
  border: 1px solid oklch(0.7 0.05 150 / 0.2);
  border-radius: 999px;
  color: oklch(0.76 0.025 150);
  background: oklch(0.2 0.025 150 / 0.7);
  font-size: 11px;
  font-weight: 600;
  letter-spacing: 0.02em;
}

.bp-status > span {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: oklch(0.76 0.16 145);
  box-shadow: 0 0 0 4px oklch(0.76 0.16 145 / 0.12);
}

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
  font-size: clamp(34px, 3.1vw, 48px);
  font-weight: 700;
  letter-spacing: -0.035em;
  line-height: 1.08;
  margin: 0 0 18px;
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

.bp-foot a {
  color: inherit;
  text-decoration: none;
}

.bp-foot a:hover { color: white; }

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
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 48px;
  background:
    radial-gradient(circle at 100% 0%, color-mix(in srgb, var(--color-primary) 8%, transparent), transparent 34rem),
    var(--color-bg-secondary);
}

.form-wrap { width: 100%; max-width: 440px; }

.auth-card {
  padding: 38px;
  border: 1px solid var(--color-border);
  border-radius: 20px;
  background: color-mix(in srgb, var(--color-surface) 94%, transparent);
  box-shadow: 0 24px 70px rgba(0, 0, 0, 0.18);
  backdrop-filter: blur(16px);
}

/* Mobile brand — hidden on desktop */
.mobile-brand {
  display: none;
  margin-bottom: 28px;
}

.form-head h2 {
  font-size: 28px;
  font-weight: 700;
  letter-spacing: -0.025em;
  margin: 9px 0 7px;
  color: var(--color-text);
}

.form-head p {
  color: var(--color-text-muted);
  margin: 0 0 26px;
  font-size: 14px;
}

.form-eyebrow {
  display: inline-flex;
  align-items: center;
  gap: 7px;
  color: var(--color-primary);
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.07em;
  text-transform: uppercase;
}

/* ── Field layout ─────────────────── */
.login-form { display: flex; flex-direction: column; gap: 18px; }

.f-field { display: flex; flex-direction: column; gap: 6px; }

.f-label {
  font-size: 13px;
  font-weight: 650;
  color: var(--color-text);
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
  height: 48px;
  padding: 0 14px 0 40px;
  border-radius: var(--radius-md);
  border: 1px solid var(--color-border-strong, var(--color-border));
  background: var(--color-surface);
  color: var(--color-text);
  font: inherit;
  font-size: 14px;
  transition: border-color var(--t-fast), box-shadow var(--t-fast);
}

.inp:hover:not(:disabled) { border-color: color-mix(in srgb, var(--color-primary) 42%, var(--color-border)); }

.inp:disabled { cursor: wait; opacity: 0.72; }

.inp[aria-invalid="true"] { border-color: var(--color-danger-border); }

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

.pw-toggle:focus-visible,
.btn:focus-visible,
.bp-foot a:focus-visible {
  outline: 2px solid var(--color-primary-2);
  outline-offset: 2px;
}

/* ── Buttons ──────────────────────── */
.btn {
  width: 100%;
  min-height: 48px;
  border-radius: var(--radius-md);
  border: 1px solid transparent;
  cursor: pointer;
  font: 600 14px/1 inherit;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  transition: filter var(--t-fast), background var(--t-fast), border-color var(--t-fast), transform var(--t-fast);
}

.btn-primary {
  color: white;
  background: linear-gradient(180deg, var(--color-primary-2, var(--color-primary)) 0%, var(--color-primary) 100%);
  box-shadow: 0 1px 2px rgba(20, 40, 25, 0.18);
}

.btn-primary:hover:not(:disabled)  { filter: brightness(1.06); }
.btn-primary:active:not(:disabled) { filter: brightness(0.97); transform: translateY(1px); }
.btn-primary:disabled { opacity: 0.6; cursor: not-allowed; }

.btn-ghost {
  background: var(--color-surface);
  border-color: var(--color-border-strong, var(--color-border));
  color: var(--color-text);
}

.btn-ghost:hover:not(:disabled) { background: var(--color-surface-elevated); border-color: var(--color-primary); }
.btn-ghost:disabled { opacity: 0.6; cursor: not-allowed; }

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
  margin: 0 0 20px;
  color: var(--color-danger-text);
  background: var(--color-danger-bg);
  border: 1px solid var(--color-danger-border);
  border-radius: var(--radius-md);
  padding: 12px 14px;
  font-size: 13px;
  line-height: 1.5;
}

.login-error-icon { width: 15px; height: 15px; flex-shrink: 0; margin-top: 1px; }

.login-error span { display: grid; gap: 2px; }
.login-error strong { color: var(--color-danger-text); font-size: 12px; }

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

.security-note {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 7px;
  margin: 18px 0 0;
  color: var(--color-text-muted);
  font-size: 11.5px;
  text-align: center;
}

/* ═══════════════ Responsive ═══════════════ */
@media (max-width: 860px) {
  .auth-layout { grid-template-columns: 1fr; }
  .brand-panel { display: none; }
  .mobile-brand { display: block; }
  .form-panel { padding: max(32px, 7vh) 24px; align-items: flex-start; }
}

@media (max-width: 480px) {
  .form-panel { padding: 28px 18px; background: var(--color-bg); }
  .mobile-brand { margin: 2px 0 28px 4px; }
  .auth-card { padding: 28px 22px; border-radius: 16px; }
  .form-head h2 { font-size: 26px; }
  .security-note { padding: 0 12px; }
}

@media (max-height: 720px) and (min-width: 861px) {
  .brand-panel { padding-block: 30px; }
  .bp-feats { gap: 9px; }
  .bp-desc { margin-bottom: 20px; }
  .auth-card { padding-block: 28px; }
  .form-head p { margin-bottom: 20px; }
  .login-form { gap: 12px; }
}
</style>
