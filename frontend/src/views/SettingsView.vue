<!--
  CRANE — CRA Norm Engine
  Copyright (C) 2026 Ali Mohammad Hosseini
  SPDX-License-Identifier: AGPL-3.0-or-later
  This file is part of CRANE, free software under the GNU AGPL v3.0 or later.
  See <https://www.gnu.org/licenses/>.
-->
<template>
  <section class="settings">
    <header class="page-header" data-guide="settings-header">
      <div>
        <h1 class="page-title">Settings</h1>
        <p class="muted settings-sub">Manage your account, appearance, and personal preferences.</p>
      </div>
      <AppButton class="embedded-guide-trigger" variant="secondary" type="button" @click="startGuide"><span aria-hidden="true">?</span> Guide</AppButton>
    </header>

    <div class="settings-cols">
      <!-- ── Section navigation (scrollspy) ───────────── -->
      <nav class="settings-nav" data-guide="settings-nav" aria-label="Settings sections">
        <button
          v-for="item in navItems"
          :key="item.id"
          type="button"
          class="snav-link"
          :class="{ active: activeSection === item.id }"
          @click="scrollTo(item.id)"
        >
          <span class="snav-ic" aria-hidden="true" v-html="item.icon" />
          {{ item.label }}
        </button>
      </nav>

      <!-- ── Content ──────────────────────────────────── -->
      <div class="settings-content">
        <!-- Account -->
        <section id="account" class="s-card" data-guide="settings-account">
          <div class="s-card-head">
            <h2 class="s-card-title">Account</h2>
            <p class="muted">Your identity and access within CRANE.</p>
          </div>

          <div class="s-card-body">
            <div class="identity">
              <div class="avatar" aria-hidden="true"><img v-if="authStore.user?.avatar_data" :src="authStore.user.avatar_data" alt="" /><span v-else>{{ userEmoji }}</span></div>
              <div class="who">
                <span class="who-name">{{ authStore.userFullName || "—" }}</span>
                <span class="who-email">{{ authStore.userEmail }}</span>
              </div>
              <div class="who-badges">
                <StatusBadge
                  :label="authStore.user?.is_active ? 'Active' : 'Inactive'"
                  :variant="authStore.user?.is_active ? 'success' : 'danger'"
                />
                <StatusBadge
                  v-for="role in authStore.roles"
                  :key="role"
                  :label="formatRole(role)"
                  variant="neutral"
                />
              </div>
            </div>

            <div class="s-row">
              <div class="s-label"><div class="s-label-t">Profile photo</div><div class="s-label-h">Optional JPEG, PNG, or WebP image up to 2 MB. It appears beside your assigned tasks.</div></div>
              <div class="s-control avatar-actions"><input ref="avatarInput" type="file" accept="image/jpeg,image/png,image/webp" @change="uploadAvatar" /><AppButton v-if="authStore.user?.avatar_data" variant="secondary" size="sm" :disabled="avatarBusy" @click="removeAvatar">Remove</AppButton></div>
            </div>

            <div class="s-row">
              <div class="s-label">
                <div class="s-label-t">Full name</div>
                <div class="s-label-h">The name shown across CRANE.</div>
              </div>
              <div class="s-control grow">
                <input
                  v-model.trim="fullName"
                  class="input"
                  type="text"
                  maxlength="255"
                  autocomplete="name"
                  :disabled="!isLocalUser"
                />
              </div>
            </div>

            <div class="s-row">
              <div class="s-label">
                <div class="s-label-t">Email</div>
                <div class="s-label-h">Used for sign-in and notifications.</div>
              </div>
              <div class="s-control">
                <span class="value-pill">{{ authStore.userEmail }}</span>
              </div>
            </div>

            <div class="s-row">
              <div class="s-label">
                <div class="s-label-t">Authentication</div>
                <div class="s-label-h">How you sign in to this instance.</div>
              </div>
              <div class="s-control">
                <StatusBadge :label="isLocalUser ? 'Local account' : 'LDAP / SSO'" variant="info" />
              </div>
            </div>
          </div>

          <div v-if="isLocalUser" class="s-card-foot">
            <Transition name="fade">
              <span v-if="accountSaved" class="saved-tag">
                <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round"><path d="M20 6 9 17l-5-5" /></svg>
                Saved
              </span>
            </Transition>
            <span class="foot-spacer" />
            <AppButton
              variant="primary"
              size="sm"
              :disabled="profileState.isLoading.value || !fullNameChanged"
              @click="saveProfile"
            >
              {{ profileState.isLoading.value ? "Saving…" : "Save changes" }}
            </AppButton>
          </div>
        </section>

        <!-- Appearance -->
        <section id="appearance" class="s-card" data-guide="settings-appearance">
          <div class="s-card-head">
            <h2 class="s-card-title">Appearance</h2>
            <p class="muted">Choose how CRANE looks. Synced to your account.</p>
          </div>
          <div class="s-card-body">
            <div class="s-row">
              <div class="s-label">
                <div class="s-label-t">Theme</div>
                <div class="s-label-h">Applies instantly and is remembered across your devices.</div>
              </div>
              <div class="s-control">
                <div class="theme-seg">
                  <button
                    v-for="opt in themeOptions"
                    :key="opt.value"
                    type="button"
                    class="theme-opt"
                    :class="{ on: appStore.themeMode === opt.value }"
                    :aria-pressed="appStore.themeMode === opt.value"
                    @click="pickTheme(opt.value)"
                  >
                    <span class="theme-sw" :class="opt.value" />
                    <span class="theme-nm">{{ opt.label }}</span>
                  </button>
                </div>
              </div>
            </div>
          </div>
        </section>

        <!-- Preferences -->
        <section id="preferences" class="s-card" data-guide="settings-preferences">
          <div class="s-card-head">
            <h2 class="s-card-title">Preferences</h2>
            <p class="muted">Regional formatting and where you start.</p>
          </div>
          <div class="s-card-body">
            <div class="s-row">
              <div class="s-label">
                <div class="s-label-t">Timezone</div>
                <div class="s-label-h">Used to display dates and times.</div>
              </div>
              <div class="s-control grow">
                <select v-model="timezone" class="select">
                  <option v-for="tz in timezones" :key="tz" :value="tz">{{ tz }}</option>
                </select>
              </div>
            </div>

            <div class="s-row">
              <div class="s-label">
                <div class="s-label-t">Date format</div>
                <div class="s-label-h">How calendar dates are written.</div>
              </div>
              <div class="s-control grow">
                <select v-model="dateFormat" class="select">
                  <option v-for="fmt in dateFormatOptions" :key="fmt" :value="fmt">{{ fmt }}</option>
                </select>
                <div class="preview-note">Preview: <b>{{ datePreview }}</b></div>
              </div>
            </div>

            <div class="s-row">
              <div class="s-label">
                <div class="s-label-t">Default landing page</div>
                <div class="s-label-h">The page you see right after signing in.</div>
              </div>
              <div class="s-control grow">
                <select v-model="landingPage" class="select">
                  <option v-for="opt in landingOptions" :key="opt.name" :value="opt.name">
                    {{ opt.label }}
                  </option>
                </select>
              </div>
            </div>
          </div>

          <div class="s-card-foot">
            <Transition name="fade">
              <span v-if="prefsSaved" class="saved-tag">
                <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round"><path d="M20 6 9 17l-5-5" /></svg>
                Saved
              </span>
            </Transition>
            <span class="foot-spacer" />
            <AppButton
              variant="primary"
              size="sm"
              :disabled="prefsState.isLoading.value || !preferencesChanged"
              @click="savePreferences"
            >
              {{ prefsState.isLoading.value ? "Saving…" : "Save preferences" }}
            </AppButton>
          </div>
        </section>

        <!-- Security -->
        <section id="security" class="s-card" data-guide="settings-security">
          <div class="s-card-head">
            <h2 class="s-card-title">Security</h2>
            <p class="muted">Password and active sessions.</p>
          </div>
          <div class="s-card-body">
            <div class="s-row">
              <div class="s-label">
                <div class="s-label-t">Password</div>
                <div class="s-label-h">
                  {{ isLocalUser ? "Change your account password." : "Managed by your identity provider." }}
                </div>
              </div>
              <div class="s-control">
                <AppButton
                  v-if="isLocalUser"
                  variant="secondary"
                  size="sm"
                  @click="router.push({ name: 'change-password' })"
                >
                  Change password
                </AppButton>
                <span v-else class="muted">Not available</span>
              </div>
            </div>

            <div class="s-row">
              <div class="s-label">
                <div class="s-label-t">Active sessions</div>
                <div class="s-label-h">Sign out of CRANE on all devices, including this one.</div>
              </div>
              <div class="s-control">
                <AppButton variant="danger" size="sm" @click="confirmLogoutAll = true">
                  Log out everywhere
                </AppButton>
              </div>
            </div>
          </div>
        </section>

        <!-- Jira -->
        <section id="jira" class="s-card" data-guide="settings-jira">
          <div class="s-card-head">
            <h2 class="s-card-title">Jira Cloud</h2>
            <p class="muted">Create Jira issues from CRANE tasks and synchronize their status and details.</p>
          </div>
          <div class="s-card-body">
            <div class="jira-guide">
              <strong>Jira setup guide</strong>
              <span>1. Connect your site</span><span>2. Choose the destination project</span><span>3. Map statuses and users (optional)</span>
              <small>Use the project key shown in Jira, for example <code>SCRUM</code>. CRANE uses this connection for task export and board sync.</small>
            </div>
            <div v-if="!jiraConnections.length" class="s-row">
              <div class="s-label">
                <div class="s-label-t">Connect Atlassian</div>
                <div class="s-label-h">Authorization uses Atlassian OAuth. CRANE never stores your Jira password.</div>
              </div>
              <div class="s-control">
                <AppButton variant="primary" size="sm" :disabled="jiraBusy" @click="connectJira">
                  {{ jiraBusy ? "Opening…" : "Connect Jira Cloud" }}
                </AppButton>
              </div>
            </div>
            <template v-for="connection in jiraConnections" :key="connection.id">
              <div class="s-row jira-site-row">
                <div class="s-label">
                  <div class="s-label-t">{{ connection.site_name }}</div>
                  <div class="s-label-h"><a :href="connection.site_url" target="_blank" rel="noopener">{{ connection.site_url }}</a></div>
                </div>
                <StatusBadge :label="connection.is_active ? 'Connected' : 'Disconnected'" :variant="connection.is_active ? 'success' : 'neutral'" />
              </div>
              <div class="s-row">
                <div class="s-label">
                  <div class="s-label-t">Destination project <span class="jira-tag required">Required</span></div>
                  <div class="s-label-h">Project key and Jira issue type used for exported CRANE tasks.</div>
                </div>
                <div class="s-control grow jira-fields">
                  <input v-model.trim="connection.project_key" class="input" placeholder="Project key (e.g. CRA)" maxlength="50" />
                  <input v-model.trim="connection.issue_type" class="input" placeholder="Issue type" maxlength="100" />
                </div>
              </div>
              <div class="s-row">
                <div class="s-label">
                  <div class="s-label-t">Workflow mapping <span class="jira-tag optional">Optional</span></div>
                  <div class="s-label-h">Optional Jira status IDs for CRANE open, in progress, and completed states.</div>
                </div>
                <div class="s-control grow jira-fields">
                  <input v-model.trim="connection.status_mapping_json.open" class="input" placeholder="Open status ID" />
                  <input v-model.trim="connection.status_mapping_json.in_progress" class="input" placeholder="In progress status ID" />
                  <input v-model.trim="connection.status_mapping_json.completed" class="input" placeholder="Completed status ID" />
                </div>
              </div>
              <div class="s-row">
                <div class="s-label">
                  <div class="s-label-t">Priority mapping <span class="jira-tag optional">Optional</span></div>
                  <div class="s-label-h">Optional Jira priorities corresponding to CRANE low, medium, and high.</div>
                </div>
                <div class="s-control grow jira-fields">
                  <input v-model.trim="connection.priority_mapping_json.low" class="input" placeholder="Low" />
                  <input v-model.trim="connection.priority_mapping_json.medium" class="input" placeholder="Medium" />
                  <input v-model.trim="connection.priority_mapping_json.high" class="input" placeholder="High" />
                </div>
              </div>
              <div class="s-row">
                <div class="s-label">
                  <div class="s-label-t">Assignee mapping <span class="jira-tag optional">Optional</span></div>
                  <div class="s-label-h">Map CRANE users to Atlassian account IDs so exported issues retain their assignee.</div>
                </div>
                <div class="s-control grow jira-user-map">
                  <label v-for="user in craneUsers" :key="user.id">
                    <span>{{ userService.displayName(user) }}</span>
                    <input v-model.trim="jiraAccountIds[connection.id][user.id]" class="input" placeholder="Atlassian account ID" />
                  </label>
                </div>
              </div>
              <div class="s-card-foot jira-actions">
                <AppButton variant="danger" size="sm" :disabled="jiraBusy" @click="disconnectJira(connection.id)">Disconnect</AppButton>
                <span class="foot-spacer" />
                <AppButton variant="primary" size="sm" :disabled="jiraBusy || !connection.project_key" @click="saveJira(connection)">Save Jira settings</AppButton>
              </div>
            </template>
          </div>
        </section>

        <!-- About -->
        <section id="about" class="s-card" data-guide="settings-about">
          <div class="s-card-head">
            <h2 class="s-card-title">About</h2>
            <p class="muted">Version, licensing, and resources.</p>
          </div>
          <div class="s-card-body">
            <!-- Brand header -->
            <div class="about-brand">
              <AppLogo :scale="1.5" />
              <div class="about-brand-text">
                <div class="about-fullname">CRA Norm Engine <span class="ver-tag">v{{ appVersion }}</span></div>
                <p class="about-tagline">
                  Open-source compliance management for the EU Cyber Resilience Act
                  (Regulation (EU) 2024/2847).
                </p>
              </div>
            </div>

            <!-- Meta grid -->
            <div class="about-grid">
              <div class="about-item">
                <div class="about-k">Application</div>
                <div class="about-v">{{ appStore.appName }}</div>
              </div>
              <div class="about-item">
                <div class="about-k">Version</div>
                <div class="about-v"><span class="ver-tag">v{{ appVersion }}</span></div>
              </div>
              <div class="about-item">
                <div class="about-k">Environment</div>
                <div class="about-v">
                  <StatusBadge
                    :label="environment"
                    :variant="environment === 'Production' ? 'success' : 'info'"
                  />
                </div>
              </div>
              <div class="about-item">
                <div class="about-k">License</div>
                <div class="about-v mono">AGPL-3.0</div>
              </div>
              <div class="about-item wide">
                <div class="about-k">Copyright</div>
                <div class="about-v">© {{ currentYear }} {{ copyrightHolder }}</div>
              </div>
            </div>

            <!-- Resource links -->
            <div class="about-links">
              <a class="about-link" :href="sourceUrl" target="_blank" rel="noopener">
                <svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="M12 2a10 10 0 0 0-3.16 19.49c.5.09.68-.22.68-.48l-.01-1.7c-2.78.6-3.37-1.34-3.37-1.34-.45-1.16-1.11-1.47-1.11-1.47-.91-.62.07-.61.07-.61 1 .07 1.53 1.03 1.53 1.03.89 1.53 2.34 1.09 2.91.83.09-.65.35-1.09.63-1.34-2.22-.25-4.55-1.11-4.55-4.94 0-1.09.39-1.98 1.03-2.68-.1-.25-.45-1.27.1-2.65 0 0 .84-.27 2.75 1.02a9.6 9.6 0 0 1 5 0c1.91-1.29 2.75-1.02 2.75-1.02.55 1.38.2 2.4.1 2.65.64.7 1.03 1.59 1.03 2.68 0 3.84-2.34 4.69-4.57 4.94.36.31.68.92.68 1.85l-.01 2.74c0 .27.18.58.69.48A10 10 0 0 0 12 2z" /></svg>
                Source code
              </a>
              <a class="about-link" :href="docsUrl" target="_blank" rel="noopener">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20" /><path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z" /></svg>
                Documentation
              </a>
              <a class="about-link" :href="issuesUrl" target="_blank" rel="noopener">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="8" y="6" width="8" height="14" rx="4" /><path d="M19 7l-2 2M5 7l2 2M3 13h3M18 13h3M19 18l-2-1.5M5 18l2-1.5M12 2v2" /></svg>
                Report an issue
              </a>
              <a class="about-link" :href="securityUrl" target="_blank" rel="noopener">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" /><path d="M9 12l2 2 4-4" /></svg>
                Security policy
              </a>
              <a class="about-link" :href="licenseUrl" target="_blank" rel="noopener">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M12 3v18M5 7h14M5 7l-3 7a4 4 0 0 0 6 0L5 7zM19 7l-3 7a4 4 0 0 0 6 0l-3-7z" /></svg>
                License
              </a>
            </div>

            <!-- AGPL network-use note -->
            <p class="about-note">
              CRANE is free software under the GNU AGPL-3.0. As network server software, the complete
              corresponding source of the running version is available at the
              <a :href="sourceUrl" target="_blank" rel="noopener">source repository</a> (AGPL §13).
            </p>
          </div>
        </section>
      </div>
    </div>

    <!-- Log out everywhere confirmation -->
    <AppModal v-model="confirmLogoutAll" title="Log out everywhere?" size="sm">
      <p>
        This signs you out of CRANE on every device, including this one. You'll need to log in
        again. Use this if you think your account may be compromised.
      </p>
      <template #footer>
        <AppButton variant="secondary" size="sm" @click="confirmLogoutAll = false">Cancel</AppButton>
        <AppButton
          variant="danger"
          size="sm"
          :disabled="logoutState.isLoading.value"
          @click="logoutEverywhere"
        >
          {{ logoutState.isLoading.value ? "Signing out…" : "Log out everywhere" }}
        </AppButton>
      </template>
    </AppModal>
  </section>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref } from "vue";
import { useRouter } from "vue-router";

import {
  deleteAvatarRequest,
  logoutAllRequest,
  uploadAvatarRequest,
  updatePreferencesRequest,
  updateProfileRequest,
} from "@/services/auth-service";
import { useAuthStore } from "@/stores/auth";
import { useAppStore } from "@/stores/app";
import { useToast } from "@/composables/useToast";
import { useAsyncState } from "@/composables/useAsyncState";
import { DATE_FORMAT_OPTIONS, formatDate } from "@/composables/useDateFormat";
import { jiraService, type JiraConnection } from "@/services/jira-service";
import { userService, type UserSummary } from "@/services/user-service";
import AppButton from "@/components/AppButton.vue";
function startGuide(): void { window.dispatchEvent(new Event("crane-guide-start")); }
import AppLogo from "@/components/AppLogo.vue";
import AppModal from "@/components/AppModal.vue";
import StatusBadge from "@/components/StatusBadge.vue";

const authStore = useAuthStore();
const appStore = useAppStore();
const router = useRouter();
const { showToast } = useToast();

const profileState = useAsyncState();
const prefsState = useAsyncState();
const logoutState = useAsyncState();
const avatarInput = ref<HTMLInputElement | null>(null);
const avatarBusy = ref(false);

async function uploadAvatar(event: Event): Promise<void> {
  const file = (event.target as HTMLInputElement).files?.[0];
  if (!file) return;
  avatarBusy.value = true;
  try { const result = await uploadAvatarRequest(file); authStore.updateUser({ avatar_data: result.avatar_data }); }
  finally { avatarBusy.value = false; if (avatarInput.value) avatarInput.value.value = ""; }
}

async function removeAvatar(): Promise<void> {
  avatarBusy.value = true;
  try { await deleteAvatarRequest(); authStore.updateUser({ avatar_data: null }); }
  finally { avatarBusy.value = false; }
}

const isLocalUser = computed(() => authStore.user?.auth_provider === "local");
const userEmoji = computed(() => ({
  admin: "🛡️",
  product_owner: "🧭",
  cybersecurity_engineer: "🔐",
  legal_team: "⚖️",
  development_team: "🧑‍💻",
  product_management: "📊",
  lifecycle_manager: "♻️",
}[authStore.roles?.[0] ?? ""] ?? "👤"));

/* ── Section nav / scrollspy ─────────────────── */
const navItems = [
  { id: "account", label: "Account", icon: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="8" r="4"/><path d="M5.5 21a8.4 8.4 0 0 1 13 0"/></svg>' },
  { id: "appearance", label: "Appearance", icon: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="13.5" cy="6.5" r="1.5"/><circle cx="17.5" cy="10.5" r="1.5"/><circle cx="6.5" cy="12.5" r="1.5"/><circle cx="8.5" cy="7.5" r="1.5"/><path d="M12 2a10 10 0 1 0 0 20 2.5 2.5 0 0 0 2-4 2.5 2.5 0 0 1 2-4h2a4 4 0 0 0 4-4 10 10 0 0 0-10-8z"/></svg>' },
  { id: "preferences", label: "Preferences", icon: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M4 21v-7M4 10V3M12 21v-9M12 8V3M20 21v-5M20 12V3M1 14h6M9 8h6M17 16h6"/></svg>' },
  { id: "security", label: "Security", icon: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="4" y="10" width="16" height="11" rx="2"/><path d="M8 10V7a4 4 0 0 1 8 0v3"/></svg>' },
  { id: "jira", label: "Jira Cloud", icon: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 3 5 10l7 7 7-7-7-7Z"/><path d="m8.5 13.5-3.5 3.5 7 4 7-4-3.5-3.5"/></svg>' },
  { id: "about", label: "About", icon: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="9"/><path d="M12 11v5M12 8h.01"/></svg>' },
];

const activeSection = ref("account");
let observer: IntersectionObserver | null = null;

function scrollTo(id: string): void {
  document.getElementById(id)?.scrollIntoView({ behavior: "smooth", block: "start" });
  activeSection.value = id;
}

const jiraConnections = ref<JiraConnection[]>([]);
const jiraBusy = ref(false);
const craneUsers = ref<UserSummary[]>([]);
const jiraAccountIds = ref<Record<string, Record<string, string>>>({});

async function loadJira(): Promise<void> {
  try {
    const [connections, users] = await Promise.all([jiraService.connections(), userService.listSummary()]);
    craneUsers.value = users;
    const accountIds: Record<string, Record<string, string>> = {};
    const mappingLists = await Promise.all(connections.map((connection) => jiraService.userMappings(connection.id)));
    connections.forEach((connection, index) => {
      const values: Record<string, string> = {};
      for (const user of users) values[user.id] = "";
      for (const mapping of mappingLists[index]) values[mapping.crane_user_id] = mapping.jira_account_id;
      accountIds[connection.id] = values;
    });
    jiraAccountIds.value = accountIds;
    jiraConnections.value = connections;
  } catch { /* global API error handler */ }
}

async function connectJira(): Promise<void> {
  jiraBusy.value = true;
  try { window.location.assign(await jiraService.authorizationUrl()); }
  finally { jiraBusy.value = false; }
}

async function saveJira(connection: JiraConnection): Promise<void> {
  jiraBusy.value = true;
  try {
    const updated = await jiraService.configure(connection.id, {
      project_key: connection.project_key || "",
      issue_type: connection.issue_type,
      status_mapping_json: connection.status_mapping_json,
      priority_mapping_json: connection.priority_mapping_json,
    });
    Object.assign(connection, updated);
    const mappings = jiraAccountIds.value[connection.id] || {};
    await Promise.all(Object.entries(mappings)
      .filter(([, accountId]) => accountId.trim())
      .map(([userId, accountId]) => jiraService.setUserMapping(connection.id, userId, accountId.trim())));
    showToast({ type: "success", message: "Jira settings saved." });
  } finally { jiraBusy.value = false; }
}

async function disconnectJira(id: string): Promise<void> {
  if (!window.confirm("Disconnect this Jira Cloud site? Existing task links will remain visible.")) return;
  jiraBusy.value = true;
  try { await jiraService.disconnect(id); await loadJira(); }
  finally { jiraBusy.value = false; }
}

onMounted(() => {
  void loadJira();
  observer = new IntersectionObserver(
    (entries) => {
      for (const entry of entries) {
        if (entry.isIntersecting) activeSection.value = entry.target.id;
      }
    },
    { rootMargin: "-20% 0px -70% 0px" },
  );
  for (const item of navItems) {
    const el = document.getElementById(item.id);
    if (el) observer.observe(el);
  }
});

onBeforeUnmount(() => observer?.disconnect());

/* ── Account ─────────────────────────────────── */
const fullName = ref(authStore.userFullName);
const accountSaved = ref(false);
const fullNameChanged = computed(
  () => fullName.value.trim().length > 0 && fullName.value.trim() !== authStore.userFullName,
);

async function saveProfile(): Promise<void> {
  if (!isLocalUser.value || !fullNameChanged.value) return;
  try {
    const updated = await profileState.execute(() =>
      updateProfileRequest({ full_name: fullName.value.trim() }),
    );
    authStore.updateUser({ full_name: updated.full_name });
    flash(accountSaved);
  } catch {
    /* error toast handled by useAsyncState */
  }
}

/* ── Appearance ──────────────────────────────── */
const themeOptions = [
  { value: "light" as const, label: "Light" },
  { value: "dark" as const, label: "Dark" },
];

async function pickTheme(value: "dark" | "light"): Promise<void> {
  if (appStore.themeMode === value) return;
  appStore.setTheme(value); // apply immediately
  try {
    const prefs = await updatePreferencesRequest({ theme: value });
    authStore.updateUser({ preferences: prefs });
  } catch {
    showToast({ type: "error", message: "Theme applied locally but could not be saved." });
  }
}

/* ── Preferences ─────────────────────────────── */
const dateFormatOptions = DATE_FORMAT_OPTIONS;
const landingOptions = [
  { name: "dashboard", label: "Dashboard" },
  { name: "my-tasks", label: "My Tasks" },
  { name: "products", label: "Products" },
  { name: "product-data", label: "Product Data" },
];

const timezones = (() => {
  const intl = Intl as unknown as { supportedValuesOf?: (key: string) => string[] };
  if (typeof intl.supportedValuesOf === "function") {
    try {
      return intl.supportedValuesOf("timeZone");
    } catch {
      /* fall through */
    }
  }
  return ["UTC", "Europe/London", "Europe/Berlin", "Europe/Paris", "America/New_York", "America/Los_Angeles", "Asia/Tokyo"];
})();

const timezone = ref(authStore.preferences?.timezone ?? "UTC");
const dateFormat = ref(authStore.preferences?.date_format ?? "YYYY-MM-DD");
const landingPage = ref(authStore.preferences?.default_landing_page ?? "dashboard");
const prefsSaved = ref(false);

const datePreview = computed(() =>
  formatDate(new Date(), { timezone: timezone.value, format: dateFormat.value }),
);

const preferencesChanged = computed(
  () =>
    timezone.value !== (authStore.preferences?.timezone ?? "UTC") ||
    dateFormat.value !== (authStore.preferences?.date_format ?? "YYYY-MM-DD") ||
    landingPage.value !== (authStore.preferences?.default_landing_page ?? "dashboard"),
);

async function savePreferences(): Promise<void> {
  if (!preferencesChanged.value) return;
  try {
    const prefs = await prefsState.execute(() =>
      updatePreferencesRequest({
        timezone: timezone.value,
        date_format: dateFormat.value,
        default_landing_page: landingPage.value,
      }),
    );
    authStore.updateUser({ preferences: prefs });
    flash(prefsSaved);
  } catch {
    /* error toast handled by useAsyncState */
  }
}

/* ── Security ────────────────────────────────── */
const confirmLogoutAll = ref(false);

async function logoutEverywhere(): Promise<void> {
  try {
    await logoutState.execute(() => logoutAllRequest());
    confirmLogoutAll.value = false;
    authStore.logout();
    showToast({ type: "success", message: "Signed out of all sessions." });
    await router.push({ name: "login" });
  } catch {
    /* error toast handled by useAsyncState */
  }
}

/* ── About ───────────────────────────────────── */
const appVersion = "1.0.0";
const environment = import.meta.env.MODE === "production" ? "Production" : "Development";
const currentYear = new Date().getFullYear();
const copyrightHolder = "Ali Mohammad Hosseini";
const sourceUrl = "https://github.com/cra-norm-engine/crane";
const docsUrl = "https://cra-norm-engine.github.io/crane";
const issuesUrl = "https://github.com/cra-norm-engine/crane/issues";
const securityUrl = "https://github.com/cra-norm-engine/crane/blob/main/SECURITY.md";
const licenseUrl = "https://github.com/cra-norm-engine/crane/blob/main/LICENSE";

/* ── helpers ─────────────────────────────────── */
function formatRole(role: string): string {
  return role.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
}

function flash(flag: { value: boolean }): void {
  flag.value = true;
  window.setTimeout(() => {
    flag.value = false;
  }, 2200);
}
</script>

<style scoped>
.jira-fields { display: grid; grid-template-columns: repeat(auto-fit, minmax(140px, 1fr)); gap: .6rem; }
.avatar img { width: 100%; height: 100%; border-radius: inherit; object-fit: cover; }
.avatar-actions { display: flex; align-items: center; gap: .6rem; }
.jira-guide { display: grid; gap: .35rem; padding: .85rem 1rem; margin-bottom: 1rem; border: 1px solid var(--color-border); border-radius: 7px; background: var(--color-surface-elevated); font-size: .8rem; }
.jira-guide strong { font-size: .88rem; }
.jira-guide span { color: var(--color-text-muted); }
.jira-guide small { color: var(--color-text-muted); margin-top: .2rem; }
.jira-guide code { font-size: .75rem; }
.jira-tag { display: inline-block; margin-left: .35rem; padding: .12rem .38rem; border-radius: 999px; font-size: .62rem; font-weight: 700; text-transform: uppercase; letter-spacing: .03em; vertical-align: middle; }
.jira-tag.required { color: var(--color-danger); background: var(--color-danger-bg); }
.jira-tag.optional { color: var(--color-text-muted); background: var(--color-surface-elevated); border: 1px solid var(--color-border); }
.jira-site-row a { color: var(--color-primary, #2563eb); }
.jira-actions { margin: 0; border-top: 0; }
.jira-user-map { display: grid; gap: .5rem; }
.jira-user-map label { display: grid; grid-template-columns: minmax(120px, 1fr) 2fr; gap: .6rem; align-items: center; font-size: .82rem; }
.settings-sub {
  margin: 0.35rem 0 0;
  font-size: var(--text-sm);
}

.settings-cols {
  display: grid;
  grid-template-columns: 210px 1fr;
  gap: 2rem;
  align-items: start;
  max-width: 1040px;
}

/* ── Section nav ─────────────────────────────── */
.settings-nav {
  position: sticky;
  top: 1rem;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.snav-link {
  appearance: none;
  cursor: pointer;
  border: none;
  background: transparent;
  text-align: left;
  display: flex;
  align-items: center;
  gap: 0.7rem;
  padding: 0.55rem 0.7rem;
  border-radius: var(--radius-md);
  font-size: var(--text-sm);
  font-weight: 600;
  color: var(--color-text-muted);
  transition: background var(--t-fast), color var(--t-fast);
}

.snav-link:hover {
  background: var(--color-surface-elevated);
  color: var(--color-text);
}

.snav-link.active {
  background: var(--color-status-bg);
  color: var(--color-primary-2);
}

.snav-ic :deep(svg) {
  width: 17px;
  height: 17px;
  display: block;
  opacity: 0.9;
}

/* ── Cards ───────────────────────────────────── */
.settings-content {
  display: grid;
  gap: 1.25rem;
  min-width: 0;
}

.s-card {
  background: linear-gradient(180deg, var(--color-card-start), var(--color-card-end));
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-lg);
  backdrop-filter: blur(14px);
  overflow: hidden;
  scroll-margin-top: 1.25rem;
}

.s-card-head {
  padding: 1.15rem 1.4rem 0.2rem;
}

.s-card-title {
  margin: 0;
  font-size: var(--text-lg);
  font-weight: 700;
}

.s-card-head .muted {
  margin: 0.3rem 0 0;
  font-size: var(--text-sm);
}

.s-card-body {
  padding: 0.5rem 1.4rem 1rem;
}

/* ── Rows ────────────────────────────────────── */
.s-row {
  display: flex;
  align-items: center;
  gap: 1.25rem;
  padding: 0.95rem 0;
  border-top: 1px solid var(--color-divider);
}

.s-row:first-child {
  border-top: none;
}

.s-label {
  flex: 1;
  min-width: 0;
}

.s-label-t {
  font-size: var(--text-sm);
  font-weight: 600;
}

.s-label-h {
  margin-top: 0.15rem;
  font-size: var(--text-xs);
  color: var(--color-text-muted);
  line-height: 1.45;
}

.s-control {
  flex: none;
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 0.4rem;
}

.s-control.grow {
  flex: 1;
  max-width: 320px;
  align-items: stretch;
}

.value-pill {
  font-size: var(--text-sm);
  color: var(--color-text-muted);
  background: var(--color-surface-elevated);
  border: 1px solid var(--color-border);
  border-radius: 999px;
  padding: 0.28rem 0.72rem;
}

/* tighter inputs than the global default for settings rows */
.s-control .input,
.s-control .select {
  padding: 0.6rem 0.8rem;
  font-size: var(--text-sm);
  border-radius: var(--radius-md);
}

.preview-note {
  font-size: var(--text-xs);
  color: var(--color-text-muted);
}

.preview-note b {
  color: var(--color-text);
  font-weight: 600;
}

/* ── Identity header ─────────────────────────── */
.identity {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 0.6rem 0 0.4rem;
}

.avatar {
  width: 54px;
  height: 54px;
  flex: none;
  border-radius: var(--radius-md);
  display: grid;
  place-items: center;
  font-size: 1.55rem;
  background: linear-gradient(140deg, var(--color-primary), var(--color-primary-3));
}

.who {
  display: flex;
  flex-direction: column;
  gap: 0.15rem;
  min-width: 0;
}

.who-name {
  font-size: var(--text-base);
  font-weight: 700;
}

.who-email {
  font-size: var(--text-sm);
  color: var(--color-text-muted);
  word-break: break-word;
}

.who-badges {
  margin-left: auto;
  display: flex;
  flex-wrap: wrap;
  gap: 0.4rem;
  justify-content: flex-end;
}

/* ── Theme segmented picker ──────────────────── */
.theme-seg {
  display: inline-flex;
  gap: 0.6rem;
}

.theme-opt {
  appearance: none;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 0.6rem;
  padding: 0.6rem 0.85rem;
  min-width: 116px;
  border-radius: var(--radius-md);
  border: 1.5px solid var(--color-border);
  background: var(--color-surface-soft);
  color: var(--color-text);
  transition: border-color var(--t-fast), background var(--t-fast);
}

.theme-opt:hover {
  border-color: var(--color-primary);
}

.theme-opt.on {
  border-color: var(--color-primary);
  background: var(--color-status-bg);
}

.theme-sw {
  width: 28px;
  height: 28px;
  flex: none;
  border-radius: 8px;
  border: 1px solid var(--color-border-strong);
}

.theme-sw.light {
  background: linear-gradient(135deg, #ffffff 50%, #e8efe9 50%);
}

.theme-sw.dark {
  background: linear-gradient(135deg, #2b332e 50%, #14181d 50%);
}

.theme-nm {
  font-size: var(--text-sm);
  font-weight: 600;
}

/* ── Card footer ─────────────────────────────── */
.s-card-foot {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.85rem 1.4rem;
  border-top: 1px solid var(--color-divider);
  background: var(--color-surface-soft);
}

.foot-spacer {
  flex: 1;
}

.saved-tag {
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
  font-size: var(--text-sm);
  font-weight: 600;
  color: var(--color-primary-2);
}

/* ── About grid ──────────────────────────────── */
.about-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 1rem 1.6rem;
  padding: 0.4rem 0;
}

.about-item.wide {
  grid-column: 1 / -1;
}

.about-k {
  font-size: var(--text-xs);
  font-weight: 700;
  letter-spacing: 0.04em;
  text-transform: uppercase;
  color: var(--color-text-muted);
}

.about-v {
  margin-top: 0.2rem;
  font-size: var(--text-sm);
  font-weight: 600;
  word-break: break-word;
}

.about-v.mono {
  font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
  font-weight: 500;
}

.ver-tag {
  font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
  font-size: var(--text-xs);
  background: var(--color-surface-elevated);
  border: 1px solid var(--color-border);
  padding: 0.1rem 0.45rem;
  border-radius: 7px;
  color: var(--color-text-muted);
}

/* ── About: brand header ─────────────────────── */
.about-brand {
  display: flex;
  align-items: center;
  gap: 1.25rem;
  padding-bottom: 1rem;
  margin-bottom: 1rem;
  border-bottom: 1px solid var(--color-divider);
}

.about-fullname {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: var(--text-base);
  font-weight: 700;
  color: var(--color-text);
}

.about-tagline {
  margin: 0.3rem 0 0;
  font-size: var(--text-sm);
  color: var(--color-text-muted);
  line-height: 1.5;
}

/* ── About: resource links ───────────────────── */
.about-links {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
  margin-top: 1rem;
}

.about-link {
  display: inline-flex;
  align-items: center;
  gap: 0.45rem;
  font-size: var(--text-sm);
  font-weight: 600;
  color: var(--color-text);
  background: var(--color-surface-soft);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  padding: 0.5rem 0.8rem;
  transition: border-color var(--t-fast), background var(--t-fast);
}

.about-link:hover {
  border-color: var(--color-primary);
  background: var(--color-surface-elevated);
  text-decoration: none;
}

.about-link svg {
  width: 15px;
  height: 15px;
  opacity: 0.85;
}

/* ── About: AGPL note ────────────────────────── */
.about-note {
  margin: 1rem 0 0;
  padding-top: 0.85rem;
  border-top: 1px solid var(--color-divider);
  font-size: var(--text-xs);
  color: var(--color-text-muted);
  line-height: 1.55;
}

/* ── Transitions ─────────────────────────────── */
.fade-enter-active,
.fade-leave-active {
  transition: opacity var(--t-base);
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

/* ── Responsive ──────────────────────────────── */
@media (max-width: 860px) {
  .settings-cols {
    grid-template-columns: 1fr;
    gap: 1rem;
  }

  .settings-nav {
    position: static;
    flex-direction: row;
    flex-wrap: wrap;
  }

  .s-row {
    flex-direction: column;
    align-items: stretch;
  }

  .s-control,
  .s-control.grow {
    align-items: stretch;
    max-width: none;
  }

  .who-badges {
    margin-left: 0;
  }

  .about-grid {
    grid-template-columns: 1fr;
  }
}
</style>
