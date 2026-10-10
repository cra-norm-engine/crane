<!--
  CRANE — CRA Norm Engine
  Copyright (C) 2026 Ali Mohammad Hosseini
  SPDX-License-Identifier: AGPL-3.0-or-later
  This file is part of CRANE, free software under the GNU AGPL v3.0 or later.
  See <https://www.gnu.org/licenses/>.
-->
<template>
  <div class="auth-layout">
    <section class="brand-panel" aria-labelledby="brand-heading">
      <div class="brand-orbit" aria-hidden="true"><span /><span /><span /></div>
      <header class="brand-header">
        <AppLogo on-dark :scale="1.45" />
        <a class="source-link" href="https://github.com/cra-norm-engine/crane" target="_blank" rel="noopener noreferrer">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" aria-hidden="true"><path d="m8 7-5 5 5 5m8-10 5 5-5 5m-3-13-2 16" /></svg>
          Open source <span aria-hidden="true">↗</span>
        </a>
      </header>

      <div class="brand-content">
        <span class="brand-eyebrow"><span aria-hidden="true" />Built for the Cyber Resilience Act</span>
        <h1 id="brand-heading">Build products.<br /><span>Prove resilience.</span></h1>
        <p class="brand-description">From your first SBOM to your next release. Bring products, vulnerabilities, and compliance evidence into one connected workspace.</p>

        <div class="journey-visual" aria-label="CRANE workflow: register products, analyze SBOMs, assess vulnerabilities, and collect evidence">
          <div class="journey-heading"><span class="journey-symbol" aria-hidden="true">✳</span><span>Evidence, connected.<small>Your compliance journey in CRANE</small></span><span class="journey-tag">Workflow preview</span></div>
          <ol class="journey-track">
            <li><span class="journey-node" aria-hidden="true"><svg viewBox="0 0 24 24"><path d="m12 3 9 5-9 5-9-5 9-5Zm-9 5v9l9 5 9-5V8M12 13v9" /></svg></span><strong>Products</strong><small>Define scope</small></li>
            <li><span class="journey-node" aria-hidden="true"><svg viewBox="0 0 24 24"><path d="M6 3h8l4 4v14H6V3Zm8 0v5h4M9 12h6m-6 4h6" /></svg></span><strong>SBOMs</strong><small>Know your software</small></li>
            <li><span class="journey-node" aria-hidden="true"><svg viewBox="0 0 24 24"><path d="m12 3 8 4v5c0 5-8 9-8 9s-8-4-8-9V7l8-4Zm-3 9 2 2 4-4" /></svg></span><strong>Vulnerabilities</strong><small>Assess & resolve</small></li>
            <li><span class="journey-node journey-node--evidence" aria-hidden="true"><svg viewBox="0 0 24 24"><path d="M5 3h14v18H5V3Zm4 4h6m-6 4h6m-7 5 2 2 5-4" /></svg></span><strong>Evidence</strong><small>Support your release</small></li>
          </ol>
          <div class="journey-bottom"><span><span aria-hidden="true">↳</span> One traceable workflow</span><span>Scope → assess → document</span></div>
        </div>

        <div class="brand-values"><span>Open source</span><span>Self-hosted</span><span>SBOM native</span></div>
      </div>

      <footer class="brand-footer"><span>CRA Norm Engine · Conformity by design</span><a href="https://cra-norm-engine.github.io/crane/" target="_blank" rel="noopener noreferrer">Discover CRANE <span aria-hidden="true">↗</span></a></footer>
    </section>

    <section class="form-panel" aria-labelledby="login-heading">
      <div class="form-wrap">
        <div class="form-topline"><span>{{ isPublicDemo ? 'TAKE CRANE FOR A SPIN' : 'YOUR COMPLIANCE WORKSPACE' }}</span><span class="access-badge"><span aria-hidden="true" />{{ isPublicDemo ? 'Public demo' : 'Sign in' }}</span></div>
        <div class="auth-card">
          <div class="form-head">
            <h2 id="login-heading">{{ isPublicDemo ? 'See it. Try it. Own it.' : 'Welcome to CRANE.' }}</h2>
            <p>{{ isPublicDemo ? 'Explore the platform. No signup, no installation. Just sign in and make yourself at home.' : 'Sign in to bring your compliance work together.' }}</p>
          </div>

          <aside v-if="isPublicDemo" class="demo-account" aria-labelledby="demo-heading">
            <div class="demo-heading"><span class="demo-icon" aria-hidden="true">↗</span><div><h3 id="demo-heading">Your demo pass</h3><p>This account is ready to use.</p></div><button class="demo-fill" type="button" :disabled="loading" @click="useDemoAccount">Use demo account</button></div>
            <dl class="demo-credentials"><div><dt>Username / email</dt><dd>{{ demoEmail }}</dd></div><div><dt>Password</dt><dd>{{ demoPassword }}</dd></div></dl>
            <p class="demo-notice"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true"><circle cx="12" cy="12" r="9"/><path d="M12 11v6m0-10v1"/></svg>Shared public workspace. Please use sample data only.</p>
          </aside>

          <p v-if="error" id="login-error" class="login-error" role="alert">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true"><circle cx="12" cy="12" r="9"/><path d="M12 7v6m0 3v1"/></svg>
            <span><strong>Unable to sign in</strong>{{ error }}</span>
          </p>

          <form class="login-form" @submit.prevent="handleLogin">
            <div class="f-field">
              <label for="email">Email address</label>
              <div class="inp-wrap">
                <svg class="inp-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" aria-hidden="true"><rect x="3" y="5" width="18" height="14" rx="3"/><path d="m3 7 9 6 9-6"/></svg>
                <input id="email" v-model.trim="email" class="inp" type="email" placeholder="you@company.com" required autocomplete="username" autocapitalize="none" spellcheck="false" :disabled="loading" :aria-invalid="!!error" :aria-describedby="error ? 'login-error' : undefined" @input="error = null" />
              </div>
            </div>
            <div class="f-field">
              <label for="password">Password</label>
              <div class="inp-wrap">
                <svg class="inp-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" aria-hidden="true"><rect x="4" y="10" width="16" height="11" rx="3"/><path d="M8 10V7a4 4 0 0 1 8 0v3"/></svg>
                <input id="password" v-model="password" class="inp inp--has-toggle" :type="showPassword ? 'text' : 'password'" placeholder="Enter your password" required autocomplete="current-password" :disabled="loading" :aria-invalid="!!error" :aria-describedby="error ? 'login-error' : undefined" @input="error = null" />
                <button class="pw-toggle" type="button" :disabled="loading" :aria-label="showPassword ? 'Hide password' : 'Show password'" :aria-pressed="showPassword" @click="showPassword = !showPassword">
                  <svg v-if="!showPassword" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" aria-hidden="true"><path d="M2 12s3.5-7 10-7 10 7 10 7-3.5 7-10 7-10-7-10-7Z"/><circle cx="12" cy="12" r="3"/></svg>
                  <svg v-else viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" aria-hidden="true"><path d="M3 3l18 18M10 5a12 12 0 0 1 2 0c6.5 0 10 7 10 7a17 17 0 0 1-3 4M6 6a20 20 0 0 0-4 6s3.5 7 10 7c2 0 4-.7 5-1.5"/></svg>
                </button>
              </div>
            </div>
            <button class="btn btn-primary" type="submit" :disabled="loading" :aria-busy="loading">
              <template v-if="loading"><span class="spinner spinner-sm" aria-hidden="true" />Signing in…</template>
              <template v-else>{{ isPublicDemo ? 'Explore the demo' : 'Sign in to workspace' }}<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true"><path d="M4 12h16m-6-6 6 6-6 6"/></svg></template>
            </button>
          </form>

          <template v-if="!isPublicDemo">
            <div class="divider"><span>or use your organisation</span></div>
            <button class="btn btn-ghost" type="button" :disabled="loading" @click="handleSso">Continue with SSO / LDAP</button>
            <p class="admin-note">Need access? Contact your CRANE administrator.</p>
          </template>
          <p v-else class="demo-footnote">No account to create. No installation to manage.</p>
        </div>

        <p class="form-footer"><a href="https://github.com/cra-norm-engine/crane" target="_blank" rel="noopener noreferrer">Source code</a><span aria-hidden="true">·</span><span>AGPL-3.0</span><span aria-hidden="true">·</span><span>© {{ new Date().getFullYear() }} <a href="https://www.linkedin.com/in/ali-m-hosseini-216b24121/" target="_blank" rel="noopener noreferrer">Ali Mohammad Hosseini</a></span></p>
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

// Public credentials published in the project's GitHub README.
const demoEmail = "crane@cra-norm-engine.com";
const demoPassword = "8hARz]9$]>r3Tn";
const isPublicDemo = import.meta.env.VITE_PUBLIC_DEMO === "true";

/* ── Reactive form state ─────────────────────── */
const email        = ref(isPublicDemo ? demoEmail : "");
const password     = ref(isPublicDemo ? demoPassword : "");
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
  if (loading.value) return;
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

function useDemoAccount(): void {
  email.value = demoEmail;
  password.value = demoPassword;
  error.value = null;
}

function handleSso(): void {
  showToast({ type: "info", message: "SSO / LDAP sign-in is disabled by your administrator." });
}
</script>

<style scoped>
.auth-layout {
  display: grid;
  grid-template-columns: minmax(0, 1.15fr) minmax(0, 1fr);
  min-height: 100dvh;
  background: var(--color-bg-secondary);
}
.brand-panel {
  position: relative;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  overflow: hidden;
  padding: clamp(28px, 3vw, 48px);
  color: #eef5e6;
  background: radial-gradient(ellipse at 10% 10%, #21412b 0%, transparent 55%), radial-gradient(ellipse at 100% 80%, #203c18 0%, transparent 60%), #0c160f;
}
.brand-panel::before {
  content: '';
  position: absolute;
  inset: 0;
  background-image: radial-gradient(#badf9126 1px, transparent 1px);
  background-size: 24px 24px;
  mask-image: linear-gradient(transparent, #000 35%, transparent);
  pointer-events: none;
}
.brand-panel > :not(.brand-orbit) { position: relative; z-index: 1; }
.brand-orbit { position: absolute; width: 750px; height: 750px; top: 20%; left: 22%; pointer-events: none; }
.brand-orbit span { position: absolute; inset: 0; border: 1px solid #b5e57712; border-radius: 50%; }
.brand-orbit span:nth-child(2) { inset: 85px; }
.brand-orbit span:nth-child(3) { inset: 170px; }
.brand-header { display: flex; align-items: center; justify-content: space-between; gap: 20px; }
.source-link { display: inline-flex; align-items: center; gap: 8px; color: #d1dfc6; font-size: 12px; text-decoration: none; }
.source-link svg { width: 18px; height: 18px; }
.source-link:hover, .brand-footer a:hover { color: #c3f26a; }
.brand-content { width: 100%; max-width: 600px; margin: 36px 0; }
.brand-eyebrow { display: inline-flex; align-items: center; gap: 9px; color: #c3dfb2; font-size: 11px; font-weight: 600; letter-spacing: .09em; text-transform: uppercase; }
.brand-eyebrow > span { width: 6px; height: 6px; border-radius: 50%; background: #c3f26a; box-shadow: 0 0 0 4px #c3f26a15; }
h1 { margin: 24px 0; font-size: clamp(42px, 4.5vw, 76px); font-weight: 750; line-height: 1.05; letter-spacing: -.055em; color: #fff; }
h1 > span { color: #c3f26a; }
.brand-description { max-width: 450px; margin: 0; color: #bfd0b9; font-size: 16px; line-height: 1.7; }
.journey-visual { margin-top: 36px; padding: 22px; border: 1px solid #bbdf952b; border-radius: 18px; background: linear-gradient(135deg, #263c2cd9, #142218ee); box-shadow: 0 20px 70px #0003; }
.journey-heading { display: flex; align-items: center; gap: 10px; font-size: 14px; font-weight: 650; }
.journey-symbol { display: grid; place-items: center; width: 34px; height: 34px; border-radius: 10px; color: #c3f26a; background: #c3f26a12; font-size: 23px; }
.journey-heading small { display: block; color: #b2c1aa; font-size: 11px; font-weight: 400; margin-top: 3px; }
.journey-tag { margin-left: auto; color: #c4d6b5; font-size: 9px; padding: 4px 7px; border: 1px solid #b4d59130; border-radius: 5px; white-space: nowrap; }
.journey-track { position: relative; display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 8px; list-style: none; padding: 0; margin: 28px 0; }
.journey-track::before { content: ''; position: absolute; left: 12.5%; right: 12.5%; top: 23px; height: 1px; background: linear-gradient(90deg, #76905d, #c3f26a); }
.journey-track li { position: relative; display: flex; flex-direction: column; align-items: center; gap: 8px; text-align: center; min-width: 0; }
.journey-node { display: grid; place-items: center; width: 46px; height: 46px; border: 1px solid #9dbc763b; border-radius: 13px; background: #24362a; color: #c4d6b5; box-shadow: 0 0 0 7px #1a2c20; }
.journey-node svg { width: 22px; height: 22px; fill: none; stroke: currentColor; stroke-width: 1.5; stroke-linejoin: round; stroke-linecap: round; }
.journey-node--evidence { color: #10200a; background: #c3f26a; border-color: #c3f26a; box-shadow: 0 0 0 7px #1a2c20, 0 0 30px #c3f26a25; }
.journey-track strong { font-size: 11px; font-weight: 600; margin-top: 4px; }
.journey-track small { color: #b2c1aa; font-size: 9px; }
.journey-bottom { display: flex; justify-content: space-between; flex-wrap: wrap; gap: 8px; border-top: 1px solid #bbdf951f; padding-top: 14px; color: #b8cbaa; font-size: 10px; }
.journey-bottom > span:first-child { color: #d4ecbe; }
.brand-values { display: flex; gap: 22px; margin-top: 24px; color: #b8cbaa; font-size: 12px; }
.brand-values span { display: inline-flex; align-items: center; gap: 8px; }
.brand-values span::before { content: '✓'; color: #c3f26a; }
.brand-footer { display: flex; justify-content: space-between; flex-wrap: wrap; gap: 12px; color: #a6b89e; font-size: 11px; }
.brand-footer a { color: #c8d9bd; text-decoration: none; }

.form-panel { display: flex; align-items: center; justify-content: center; min-width: 0; padding: 40px clamp(24px, 4vw, 64px); background: radial-gradient(circle at 90% 0%, var(--color-status-bg), transparent 45%), var(--color-bg-secondary); }
.form-wrap { width: 100%; max-width: 460px; }
.form-topline { display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 12px; margin-bottom: 20px; font-size: 9px; font-weight: 650; letter-spacing: .12em; color: var(--color-text-muted); }
.access-badge { display: inline-flex; align-items: center; gap: 7px; padding: 6px 10px; border: 1px solid var(--color-status-border); border-radius: 999px; background: var(--color-status-bg); color: var(--color-primary-2); font-size: 11px; letter-spacing: 0; }
.access-badge > span { width: 5px; height: 5px; border-radius: 50%; background: currentColor; }
.auth-card { padding: 30px; border: 1px solid var(--color-border); border-radius: 22px; background: var(--color-surface); box-shadow: 0 20px 70px #00000012; }
.form-head h2 { margin: 0 0 10px; color: var(--color-text); font-size: clamp(25px, 2.3vw, 32px); line-height: 1.2; letter-spacing: -.04em; }
.form-head > p { margin: 0 0 24px; font-size: 13px; line-height: 1.65; color: var(--color-text-muted); }
.demo-account { margin-bottom: 24px; padding: 16px; border: 1px solid var(--color-status-border); border-radius: 14px; background: var(--color-status-bg); }
.demo-heading { display: flex; align-items: center; flex-wrap: wrap; gap: 9px; }
.demo-icon { display: grid; place-items: center; width: 30px; height: 30px; border-radius: 9px; background: var(--color-surface-elevated); color: var(--color-primary-2); font-size: 19px; }
.demo-heading h3 { margin: 0; font-size: 13px; color: var(--color-text); }
.demo-heading p { margin: 2px 0 0; font-size: 10px; color: var(--color-text-muted); }
.demo-fill { margin-left: auto; padding: 7px 8px; border: 1px solid var(--color-border-strong); border-radius: 7px; color: var(--color-text); background: var(--color-surface); cursor: pointer; font: inherit; font-size: 10px; }
.demo-fill:hover:not(:disabled) { border-color: var(--color-primary); }
.demo-credentials { margin: 15px 0 12px; display: grid; gap: 9px; }
.demo-credentials > div { display: grid; gap: 3px; }
.demo-credentials dt { font-size: 10px; color: var(--color-text-muted); }
.demo-credentials dd { margin: 0; color: var(--color-text); font: 13px/1.5 ui-monospace, SFMono-Regular, Menlo, monospace; overflow-wrap: anywhere; user-select: all; }
.demo-notice { display: flex; align-items: flex-start; gap: 6px; margin: 0; padding-top: 10px; border-top: 1px solid var(--color-status-border); font-size: 10px; line-height: 1.5; color: var(--color-text-muted); }
.demo-notice svg { width: 13px; height: 13px; flex: none; margin-top: 1px; }
.login-form { display: grid; gap: 18px; }
.f-field { display: grid; gap: 7px; }
.f-field label { font-size: 12px; font-weight: 600; color: var(--color-text); }
.inp-wrap { position: relative; display: flex; align-items: center; min-width: 0; }
.inp-icon { position: absolute; left: 14px; width: 17px; height: 17px; color: var(--color-text-muted); pointer-events: none; }
.inp { width: 100%; min-width: 0; height: 48px; padding: 0 14px 0 41px; border: 1px solid var(--color-border-strong); border-radius: 10px; background: var(--color-surface-soft); color: var(--color-text); font: inherit; font-size: 14px; transition: border-color var(--t-fast), box-shadow var(--t-fast); }
.inp::placeholder { color: var(--color-text-muted); }
.inp:hover:not(:disabled) { border-color: var(--color-primary); }
.inp:focus { outline: none; border-color: var(--color-primary); box-shadow: 0 0 0 3px var(--color-status-bg); }
.inp[aria-invalid="true"] { border-color: var(--color-danger); }
.inp--has-toggle { padding-right: 50px; }
.pw-toggle { position: absolute; right: 3px; display: grid; place-items: center; width: 42px; height: 42px; border: 0; border-radius: 8px; background: transparent; color: var(--color-text-muted); cursor: pointer; }
.pw-toggle svg, .btn svg { width: 18px; height: 18px; flex: none; }
.pw-toggle:hover:not(:disabled) { background: var(--color-surface-elevated); color: var(--color-text); }
.btn { width: 100%; min-height: 48px; display: inline-flex; align-items: center; justify-content: center; gap: 12px; padding: 12px 16px; border: 1px solid transparent; border-radius: 10px; font-family: inherit; font-size: 14px; font-weight: 650; cursor: pointer; transition: transform var(--t-fast), box-shadow var(--t-fast); }
.btn-primary { margin-top: 4px; color: #13210a; background: #c3f26a; box-shadow: 0 4px 20px #9ad34615; }
.btn-primary:hover:not(:disabled) { transform: translateY(-1px); box-shadow: 0 6px 24px #9ad34630; }
.btn-primary:active:not(:disabled) { transform: translateY(0); }
.btn-ghost { background: var(--color-surface-soft); border-color: var(--color-border-strong); color: var(--color-text); }
button:disabled, .inp:disabled { opacity: .65; cursor: wait; }
button:focus-visible, a:focus-visible { outline: 2px solid var(--color-primary-2); outline-offset: 4px; }
.login-error { display: flex; align-items: flex-start; gap: 9px; margin: 0 0 18px; padding: 12px; border: 1px solid var(--color-danger-border); border-radius: 10px; color: var(--color-danger-text); background: var(--color-danger-bg); font-size: 12px; }
.login-error svg { width: 18px; height: 18px; flex: none; }
.login-error span { display: grid; gap: 3px; }
.divider { display: flex; align-items: center; gap: 12px; margin: 20px 0; font-size: 11px; color: var(--color-text-muted); }
.divider::before, .divider::after { content: ''; flex: 1; height: 1px; background: var(--color-border); }
.admin-note, .demo-footnote { margin: 14px 0 0; font-size: 11px; text-align: center; color: var(--color-text-muted); }
.form-footer { display: flex; justify-content: center; flex-wrap: wrap; gap: 10px; margin: 20px 0 0; color: var(--color-text-muted); font-size: 10px; }
.form-footer a { color: inherit; text-decoration: none; }
.form-footer a:hover { color: var(--color-primary-2); }

@media (max-width: 1100px) and (min-width: 901px) {
  .brand-panel { padding: 32px; }
  .form-panel { padding: 28px; }
  .auth-card { padding: 24px; }
  .journey-visual { padding: 18px 12px; }
  .journey-tag, .journey-track small { display: none; }
}
@media (max-width: 900px) {
  .auth-layout { grid-template-columns: 1fr; }
  .brand-panel { padding: 24px 32px 28px; }
  .brand-content { max-width: none; margin: 30px 0 0; }
  h1 { margin: 14px 0; font-size: clamp(34px, 6.5vw, 52px); }
  h1 br { display: none; }
  h1 > span::before { content: ' '; }
  .brand-description { max-width: 600px; font-size: 13px; }
  .journey-visual, .brand-values, .brand-footer { display: none; }
  .brand-eyebrow { font-size: 9px; }
  .form-panel { padding: 28px 24px; }
  .form-wrap { max-width: 480px; }
}
@media (max-width: 480px) {
  .brand-panel { padding: 22px; }
  .brand-content { margin-top: 24px; }
  .brand-header :deep(.logo-motto) { display: none; }
  .source-link { font-size: 11px; }
  .source-link svg { display: none; }
  .brand-description { display: none; }
  h1 { font-size: 36px; }
  .form-panel { padding: 24px 16px; }
  .auth-card { padding: 24px 20px; border-radius: 18px; }
  .demo-fill { min-height: 36px; }
  .inp { font-size: 16px; }
}
@media (prefers-reduced-motion: reduce) {
  .inp, .btn { transition: none; }
}
</style>
