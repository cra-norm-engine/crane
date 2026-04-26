<template>
  <section class="page">
    <div class="page-header">
      <div>
        <h1 class="page-title">Admin · LDAP</h1>
        <p class="muted">Configure LDAP/Active Directory integration for user authentication.</p>
      </div>
      <div class="page-actions">
        <button class="button secondary" type="button" :disabled="statusLoading" @click="loadStatus">
          Refresh status
        </button>
      </div>
    </div>

    <!-- Connection status -->
    <div class="card status-card">
      <div class="section-header">
        <div>
          <h2 class="section-title">Connection status</h2>
          <p class="muted">Current state of the LDAP server connection.</p>
        </div>
      </div>

      <div v-if="statusLoading" class="feedback">Checking connection…</div>
      <div v-else-if="statusError" class="feedback feedback-error">{{ statusError }}</div>
      <div v-else-if="ldapStatus" class="status-grid">
        <div class="status-row">
          <span class="status-label">LDAP enabled</span>
          <span class="badge" :class="ldapStatus.enabled ? 'badge-success' : 'badge-neutral'">
            {{ ldapStatus.enabled ? "Yes" : "No" }}
          </span>
        </div>
        <div class="status-row">
          <span class="status-label">Server reachable</span>
          <span class="badge" :class="ldapStatus.connected ? 'badge-success' : 'badge-danger'">
            {{ ldapStatus.connected ? "Connected" : "Unreachable" }}
          </span>
        </div>
        <div v-if="ldapStatus.server" class="status-row">
          <span class="status-label">Server URL</span>
          <code class="mono">{{ ldapStatus.server }}</code>
        </div>
        <div v-if="ldapStatus.base_dn" class="status-row">
          <span class="status-label">Base DN</span>
          <code class="mono">{{ ldapStatus.base_dn }}</code>
        </div>
        <div class="status-row">
          <span class="status-label">Message</span>
          <span>{{ ldapStatus.message }}</span>
        </div>
      </div>

      <div v-if="!ldapStatus?.enabled" class="info-box">
        <strong>LDAP is disabled.</strong> Set <code>LDAP_ENABLED=true</code> and the other
        <code>LDAP_*</code> environment variables in your <code>.env</code> file, then restart the
        backend.
      </div>
    </div>

    <!-- Test credentials -->
    <div class="card form-card">
      <div class="section-header">
        <div>
          <h2 class="section-title">Test credentials</h2>
          <p class="muted">Verify that a user can authenticate against LDAP without creating a local account.</p>
        </div>
      </div>

      <form class="grid form-grid" @submit.prevent="testCredentials">
        <label class="field">
          <span class="field-label">Email / username</span>
          <input
            v-model.trim="testForm.email"
            type="email"
            required
            placeholder="user@example.com"
          />
        </label>

        <label class="field">
          <span class="field-label">Password</span>
          <input v-model="testForm.password" type="password" required />
        </label>

        <div class="form-actions field-span-2">
          <div v-if="testResult" class="test-result" :class="testResult.success ? 'result-ok' : 'result-fail'">
            <template v-if="testResult.success">
              Authentication successful — <strong>{{ testResult.full_name }}</strong>
              ({{ testResult.email }})
            </template>
            <template v-else>
              {{ testResult.message ?? "Authentication failed" }}
            </template>
          </div>
          <p v-if="testError" class="form-error">{{ testError }}</p>
          <button class="button" type="submit" :disabled="testLoading || !ldapStatus?.enabled">
            {{ testLoading ? "Testing…" : "Test bind" }}
          </button>
        </div>
      </form>
    </div>

    <!-- Sync users -->
    <div class="card form-card">
      <div class="section-header">
        <div>
          <h2 class="section-title">Import LDAP users</h2>
          <p class="muted">
            Search LDAP and create local accounts for matching users so they can log in and be
            assigned roles. Existing users are skipped.
          </p>
        </div>
      </div>

      <form class="grid form-grid" @submit.prevent="syncUsers">
        <label class="field field-span-2">
          <span class="field-label">Search filter (optional)</span>
          <input
            v-model.trim="syncForm.search"
            type="text"
            placeholder="Leave blank to import all users (max 200)"
          />
        </label>

        <label class="field field-span-2">
          <span class="field-label">Assign roles to imported users</span>
          <div class="checkbox-grid">
            <label v-for="role in roles" :key="role.id" class="checkbox-option">
              <input
                type="checkbox"
                :checked="syncForm.role_ids.includes(role.id)"
                @change="toggleSyncRole(role.id)"
              />
              <span>{{ role.name }}</span>
            </label>
          </div>
        </label>

        <div class="form-actions field-span-2">
          <div v-if="syncResult" class="sync-result">
            Import complete — <strong>{{ syncResult.created }}</strong> created,
            <strong>{{ syncResult.skipped }}</strong> already existed
            ({{ syncResult.total }} found in LDAP).
          </div>
          <p v-if="syncError" class="form-error">{{ syncError }}</p>
          <button class="button" type="submit" :disabled="syncLoading || !ldapStatus?.enabled">
            {{ syncLoading ? "Importing…" : "Import users" }}
          </button>
        </div>
      </form>
    </div>

    <!-- Config reference -->
    <div class="card config-card">
      <div class="section-header">
        <div>
          <h2 class="section-title">Configuration reference</h2>
          <p class="muted">Set these environment variables in your <code>.env</code> file.</p>
        </div>
      </div>

      <table class="config-table">
        <thead>
          <tr>
            <th>Variable</th>
            <th>Default</th>
            <th>Description</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="row in configRows" :key="row.var">
            <td><code>{{ row.var }}</code></td>
            <td><code>{{ row.default }}</code></td>
            <td class="muted">{{ row.description }}</td>
          </tr>
        </tbody>
      </table>
    </div>
  </section>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref } from "vue";

import { adminService } from "@/services/admin-service";
import type { LDAPStatusResult, LDAPSyncResult, LDAPTestResult, RoleRead } from "@/types/admin";

const ldapStatus = ref<LDAPStatusResult | null>(null);
const statusLoading = ref(false);
const statusError = ref("");

const testForm = reactive({ email: "", password: "" });
const testResult = ref<LDAPTestResult | null>(null);
const testLoading = ref(false);
const testError = ref("");

const syncForm = reactive<{ search: string; role_ids: string[] }>({ search: "", role_ids: [] });
const syncResult = ref<LDAPSyncResult | null>(null);
const syncLoading = ref(false);
const syncError = ref("");

const roles = ref<RoleRead[]>([]);

const configRows = [
  { var: "LDAP_ENABLED", default: "false", description: "Enable LDAP authentication" },
  { var: "LDAP_SERVER_URL", default: "ldap://localhost:389", description: "LDAP server URL (use ldaps:// for SSL)" },
  { var: "LDAP_BIND_DN", default: "", description: "Service account DN for directory searches" },
  { var: "LDAP_BIND_PASSWORD", default: "", description: "Service account password" },
  { var: "LDAP_BASE_DN", default: "", description: "Base DN to search for users" },
  { var: "LDAP_USER_FILTER", default: "(mail={email})", description: "LDAP filter to locate a user by email ({email} is replaced)" },
  { var: "LDAP_ATTR_EMAIL", default: "mail", description: "Attribute holding the user's email address" },
  { var: "LDAP_ATTR_FULL_NAME", default: "displayName", description: "Attribute holding the user's display name" },
  { var: "LDAP_USE_TLS", default: "false", description: "Enable STARTTLS on the connection" },
  { var: "LDAP_CONNECTION_TIMEOUT", default: "5", description: "Connection timeout in seconds" },
];

async function loadStatus(): Promise<void> {
  statusLoading.value = true;
  statusError.value = "";
  try {
    const [status, rolesData] = await Promise.all([
      adminService.getLdapStatus(),
      adminService.listRoles(),
    ]);
    ldapStatus.value = status;
    roles.value = rolesData;
  } catch (err) {
    statusError.value = err instanceof Error ? err.message : "Failed to load LDAP status.";
  } finally {
    statusLoading.value = false;
  }
}

function toggleSyncRole(roleId: string): void {
  if (syncForm.role_ids.includes(roleId)) {
    syncForm.role_ids = syncForm.role_ids.filter((id) => id !== roleId);
  } else {
    syncForm.role_ids = [...syncForm.role_ids, roleId];
  }
}

async function testCredentials(): Promise<void> {
  testLoading.value = true;
  testError.value = "";
  testResult.value = null;
  try {
    testResult.value = await adminService.testLdapCredentials({
      email: testForm.email,
      password: testForm.password,
    });
  } catch (err) {
    testError.value = err instanceof Error ? err.message : "Test failed.";
  } finally {
    testLoading.value = false;
  }
}

async function syncUsers(): Promise<void> {
  syncLoading.value = true;
  syncError.value = "";
  syncResult.value = null;
  try {
    syncResult.value = await adminService.syncLdapUsers({
      search: syncForm.search || undefined,
      role_ids: syncForm.role_ids.length ? syncForm.role_ids : undefined,
    });
  } catch (err) {
    syncError.value = err instanceof Error ? err.message : "Sync failed.";
  } finally {
    syncLoading.value = false;
  }
}

onMounted(() => {
  void loadStatus();
});
</script>

<style scoped>
.page {
  display: grid;
  gap: 1rem;
}

.page-header,
.section-header,
.form-actions {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  flex-wrap: wrap;
}

.page-actions {
  display: flex;
  gap: 0.75rem;
}

.page-title,
.section-title {
  margin: 0;
}

.status-card,
.form-card,
.config-card {
  display: grid;
  gap: 1rem;
}

.status-grid {
  display: grid;
  gap: 0.65rem;
}

.status-row {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  flex-wrap: wrap;
}

.status-label {
  min-width: 10rem;
  font-size: 0.875rem;
  color: var(--color-text-muted, #94a3b8);
}

.mono {
  font-family: monospace;
  font-size: 0.85rem;
  background: var(--color-surface-soft, rgba(15, 23, 42, 0.45));
  padding: 0.15rem 0.4rem;
  border-radius: 0.3rem;
}

.info-box {
  padding: 0.85rem 1rem;
  border-radius: 0.5rem;
  background: var(--color-warning-bg, rgba(251, 191, 36, 0.08));
  border: 1px solid var(--color-warning-border, rgba(251, 191, 36, 0.2));
  color: var(--color-warning-text, #fbbf24);
  font-size: 0.875rem;
}

.info-box code {
  font-family: monospace;
  font-size: 0.85em;
}

.grid {
  display: grid;
  gap: 1rem;
}

.form-grid {
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

.field {
  display: grid;
  gap: 0.4rem;
}

.field-span-2 {
  grid-column: span 2;
}

.field-label {
  font-size: 0.875rem;
  color: var(--color-text-muted, #94a3b8);
}

.checkbox-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 0.75rem;
  margin-top: 0.25rem;
}

.checkbox-option {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.9rem;
}

.feedback {
  padding: 1rem;
  border-radius: 0.75rem;
  background: var(--color-surface-soft, rgba(15, 23, 42, 0.45));
}

.feedback-error,
.form-error {
  color: var(--color-danger-text, #fda4af);
}

.test-result,
.sync-result {
  padding: 0.65rem 0.9rem;
  border-radius: 0.5rem;
  font-size: 0.9rem;
}

.result-ok {
  background: var(--color-emerald-bg, rgba(52, 211, 153, 0.1));
  color: var(--color-emerald-text, #6ee7b7);
  border: 1px solid var(--color-emerald-border, rgba(52, 211, 153, 0.2));
}

.result-fail {
  background: var(--color-danger-bg, rgba(251, 113, 133, 0.08));
  color: var(--color-danger-text, #fda4af);
  border: 1px solid var(--color-danger-border, rgba(251, 113, 133, 0.2));
}

.sync-result {
  background: var(--color-info-bg, rgba(56, 189, 248, 0.08));
  color: var(--color-info-text, #7dd3fc);
  border: 1px solid var(--color-info-border, rgba(56, 189, 248, 0.2));
}

.config-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.875rem;
}

.config-table th,
.config-table td {
  padding: 0.75rem 0.6rem;
  text-align: left;
  border-bottom: 1px solid var(--color-border, rgba(148, 163, 184, 0.18));
  vertical-align: top;
}

.config-table th {
  color: var(--color-text-muted, #94a3b8);
  font-weight: 600;
}

.config-table code {
  font-family: monospace;
  font-size: 0.85em;
}

.badge-neutral {
  background: rgba(148, 163, 184, 0.15);
  color: #cbd5e1;
}

.badge-success {
  background: rgba(52, 211, 153, 0.15);
  color: #86efac;
}

.badge-danger {
  background: rgba(251, 113, 133, 0.15);
  color: #fda4af;
}

@media (max-width: 760px) {
  .form-grid,
  .checkbox-grid {
    grid-template-columns: 1fr;
  }
  .field-span-2 {
    grid-column: span 1;
  }
}
</style>

<style>
:root[data-theme="light"] .badge-neutral { background: rgba(71,85,105,0.1);  color: #475569; }
:root[data-theme="light"] .badge-success { background: rgba(21,128,61,0.1);  color: #15803d; }
:root[data-theme="light"] .badge-danger  { background: rgba(239,68,68,0.1);  color: #be123c; }
:root[data-theme="light"] .mono { background: rgba(71,85,105,0.08); }
:root[data-theme="light"] .info-box { background: rgba(161,98,7,0.07); border-color: rgba(161,98,7,0.2); color: #92400e; }
</style>
