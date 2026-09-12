<template>
  <div class="dt-settings">
    <p class="dt-intro">Dependency-Track scans your software inventory. CRANE imports its findings and assessment decisions into the matching product release.</p>
    <div v-if="loadError" class="dt-error" role="alert">{{ loadError }} <AppButton size="sm" variant="secondary" :disabled="loading" @click="load">Retry</AppButton></div>
    <p v-if="loading" role="status" class="dt-note">Loading connections…</p>

    <article v-for="connection in connections" :key="connection.id" class="dt-connection">
      <div class="dt-connection-head"><h3>{{ connection.project_name }}</h3><StatusBadge :label="connection.last_error ? 'Sync failed' : connection.last_synced_at ? 'Connected' : 'Ready to sync'" :variant="connection.last_error ? 'danger' : connection.last_synced_at ? 'success' : 'neutral'" /></div>
      <p class="dt-note">{{ connection.server_url }}</p>
      <p><span class="dt-note">Imports into</span><br />{{ sbomLabel(connection.sbom_record_id) }}</p>
      <p v-if="connection.last_error" class="dt-error" role="alert">{{ connection.last_error }}</p>
      <p v-if="connection.last_synced_at" class="dt-note">Last successful sync: {{ formatDateTime(connection.last_synced_at) }}</p>
      <p v-if="connection.last_result" class="dt-note">{{ connection.last_result.created }} added · {{ connection.last_result.updated }} updated · {{ connection.last_result.unchanged }} unchanged</p>
      <div v-if="connection.last_result?.assessment_conflicts.length" class="dt-warning">
        {{ connection.last_result.assessment_conflicts.length }} local assessment(s) kept. Review the differences in <RouterLink :to="{ name: 'vulnerability-handling' }">Vulnerability handling</RouterLink>.
        <details><summary>Show affected finding IDs</summary><ul><li v-for="id in connection.last_result.assessment_conflicts" :key="id">{{ id }}</li></ul></details>
      </div>
      <div class="dt-actions">
        <label class="dt-check"><input type="checkbox" :checked="connection.automatic_sync" :disabled="!!busy" @change="setSchedule(connection, $event)" />Sync every hour</label>
        <AppButton size="sm" :disabled="!!busy" @click="sync(connection)">{{ busy === connection.id ? 'Syncing…' : 'Sync now' }}</AppButton>
        <AppButton size="sm" variant="secondary" :disabled="!!busy" @click="disconnect(connection)">Disconnect</AppButton>
      </div>
    </article>

    <form class="dt-setup" @submit.prevent="tested ? connect() : test()">
      <h3>{{ connections.length ? 'Connect another project' : 'Connect Dependency-Track' }}</h3>
      <ol class="dt-progress" aria-label="Connection steps"><li :class="{ current: !tested }">1. Test connection</li><li :class="{ current: tested }">2. Match your SBOM</li><li>3. Sync findings</li></ol>
      <p v-if="error" class="dt-error" role="alert">{{ error }}</p>
      <div data-guide="settings-dtrack-credentials">
        <label class="dt-field" for="dt-url"><span>Dependency-Track backend URL</span><input id="dt-url" v-model.trim="serverUrl" type="url" required placeholder="https://dependency-track-api.example.com" :disabled="!!busy" @input="resetTest" /><small>Use the backend/API address reachable from the CRANE server. The standard Docker backend port is 8081.</small></label>
        <label class="dt-field" for="dt-api-key"><span>Dependency-Track API key</span><input id="dt-api-key" v-model.trim="apiKey" type="password" autocomplete="new-password" required :disabled="!!busy" @input="resetTest" /><small>In Dependency-Track, open Administration → Access Management → Teams. Create a key for a team with VIEW_PORTFOLIO, VIEW_VULNERABILITY, and access to your project.</small></label>
      </div>
      <div v-if="!tested" class="dt-actions"><AppButton type="submit" size="sm" :disabled="!!busy || loading || !!loadError">{{ busy === 'test' ? 'Testing…' : 'Test connection' }}</AppButton></div>
      <template v-else>
        <p class="dt-success" role="status">Connection verified. {{ projects.length }} project(s) available.</p>
        <div data-guide="settings-dtrack-mapping">
          <label class="dt-field" for="dt-project"><span>Dependency-Track project</span><select id="dt-project" v-model="projectId" required :disabled="!!busy"><option value="">Choose a project</option><option v-for="project in projects" :key="project.uuid" :value="project.uuid">{{ project.name }}{{ project.version ? ` · ${project.version}` : '' }}</option></select></label>
          <label class="dt-field" for="dt-sbom"><span>Matching CRANE product release and SBOM</span><select id="dt-sbom" v-model="sbomId" required :disabled="!!busy"><option value="">Choose the matching SBOM</option><option v-for="sbom in sboms" :key="sbom.id" :value="sbom.id">{{ sbom.label }}</option></select><small>Choose the same product version and software inventory. CRANE links findings to this release; it does not upload the SBOM to Dependency-Track.</small></label>
          <p v-if="!sboms.length" class="dt-warning">Upload a release SBOM in <RouterLink :to="{ name: 'sbom-records' }">SBOM records</RouterLink> first, then return here.</p>
          <p v-if="!projects.length" class="dt-warning">No projects are visible. Add a project in Dependency-Track or grant this API key's team access.</p>
          <label class="dt-check"><input v-model="automaticSync" type="checkbox" :disabled="!!busy" />Keep findings updated every hour</label>
        </div>
        <div class="dt-actions"><AppButton type="submit" size="sm" :disabled="!!busy || !projectId || !sbomId">{{ busy === 'connect' ? 'Connecting…' : 'Connect and sync' }}</AppButton></div>
      </template>
      <p class="dt-note">Local CRANE assessment edits are preserved. You can turn off built-in scanning under Workspace → Vulnerability scanning when Dependency-Track is your authoritative scanner.</p>
    </form>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue';
import { RouterLink } from 'vue-router';
import { isAxiosError } from 'axios';
import AppButton from '@/components/AppButton.vue';
import StatusBadge from '@/components/StatusBadge.vue';
import { dependencyTrackService as service, type DependencyTrackConnection, type DependencyTrackProject, type DependencyTrackSbom } from '@/services/dependency-track-service';

const connections = ref<DependencyTrackConnection[]>([]);
const sboms = ref<DependencyTrackSbom[]>([]);
const projects = ref<DependencyTrackProject[]>([]);
const serverUrl = ref('');
const apiKey = ref('');
const projectId = ref('');
const sbomId = ref('');
const automaticSync = ref(true);
const tested = ref(false);
const busy = ref('');
const loading = ref(false);
const error = ref('');
const loadError = ref('');
function message(err: unknown): string {
  if (isAxiosError(err)) return err.response?.data?.error?.message || 'Could not reach CRANE. Check the connection and retry.';
  return 'The request failed. Please retry.';
}
function resetTest() { tested.value = false; projects.value = []; projectId.value = ''; error.value = ''; }
function sbomLabel(id: string) { return sboms.value.find(sbom => sbom.id === id)?.label || 'SBOM no longer available'; }
function formatDateTime(value: string) { return new Date(value).toLocaleString(); }
function replace(item: DependencyTrackConnection) { connections.value = connections.value.map(row => row.id === item.id ? item : row); }
async function load() {
  loading.value = true; loadError.value = '';
  try { [connections.value, sboms.value] = await Promise.all([service.list(), service.sboms()]); }
  catch (err) { loadError.value = message(err); }
  finally { loading.value = false; }
}
async function test() {
  busy.value = 'test'; error.value = '';
  try { projects.value = await service.test({ server_url: serverUrl.value, api_key: apiKey.value }); tested.value = true; }
  catch (err) { error.value = message(err); }
  finally { busy.value = ''; }
}
async function connect() {
  busy.value = 'connect'; error.value = '';
  try {
    const item = await service.connect({ server_url: serverUrl.value, api_key: apiKey.value, project_id: projectId.value, sbom_record_id: sbomId.value, automatic_sync: automaticSync.value });
    connections.value.unshift(item); apiKey.value = ''; tested.value = false; projectId.value = ''; sbomId.value = '';
    busy.value = item.id;
    replace(await service.sync(item.id));
  } catch (err) { error.value = message(err); }
  finally { busy.value = ''; }
}
async function sync(item: DependencyTrackConnection) {
  busy.value = item.id; error.value = '';
  try { replace(await service.sync(item.id)); }
  catch (err) { error.value = message(err); }
  finally { busy.value = ''; }
}
async function setSchedule(item: DependencyTrackConnection, event: Event) {
  const input = event.target as HTMLInputElement;
  busy.value = 'schedule'; error.value = '';
  try { replace(await service.schedule(item.id, input.checked)); }
  catch (err) { input.checked = item.automatic_sync; error.value = message(err); }
  finally { busy.value = ''; }
}
async function disconnect(item: DependencyTrackConnection) {
  if (!window.confirm(`Disconnect ${item.project_name}? Imported findings and assessments will stay in CRANE.`)) return;
  busy.value = 'disconnect'; error.value = '';
  try { await service.disconnect(item.id); connections.value = connections.value.filter(row => row.id !== item.id); }
  catch (err) { error.value = message(err); }
  finally { busy.value = ''; }
}
onMounted(load);
</script>

<style scoped>
.dt-settings { font-size: var(--text-sm); line-height: 1.5; }
.dt-intro, .dt-note { color: var(--color-text-muted); }
.dt-note { font-size: var(--text-xs); overflow-wrap: anywhere; }
h3 { margin: 0; font-size: var(--text-base); font-weight: 600; }
.dt-connection { margin: 1rem 0; padding: 1.25rem; border: 1px solid var(--color-border); border-radius: var(--radius-md); }
.dt-setup { margin: 1.5rem 0 0; }
.dt-connection { background: var(--color-surface-elevated); }
.dt-connection-head, .dt-actions { display: flex; align-items: center; gap: .65rem; flex-wrap: wrap; }
.dt-connection-head { justify-content: space-between; }
.dt-actions { margin-top: 1rem; }
.dt-actions .dt-check { margin-right: auto; }
.dt-progress { display: flex; flex-wrap: wrap; gap: .5rem 1rem; padding: 0 0 .75rem; margin: .75rem 0; border-bottom: 1px solid var(--color-border); list-style: none; color: var(--color-text-muted); font-size: var(--text-xs); }
.dt-progress .current { color: var(--color-primary-2); font-weight: 700; }
.dt-field { display: grid; gap: .5rem; margin-top: 1.25rem; min-width: 0; }
.dt-field > span { font-weight: 600; }
.dt-field small { color: var(--color-text-muted); font-size: var(--text-xs); line-height: 1.5; }
.dt-field input, .dt-field select { box-sizing: border-box; width: 100%; min-width: 0; padding: .65rem .75rem; font: inherit; color: var(--color-text); background: var(--color-surface); border: 1px solid var(--color-border); border-radius: var(--radius-md); }
.dt-field input:focus-visible, .dt-field select:focus-visible { outline: 2px solid var(--color-primary); outline-offset: 2px; }
.dt-check { display: flex; align-items: center; gap: .5rem; margin-top: .75rem; }
.dt-check input { width: 1rem; height: 1rem; accent-color: var(--color-primary); }
.dt-error, .dt-warning { padding: .75rem; border-radius: var(--radius-md); overflow-wrap: anywhere; }
.dt-error { color: var(--color-danger-text); background: var(--color-danger-bg); }
.dt-warning { color: var(--color-text); background: var(--color-surface-elevated); }
.dt-success { color: var(--color-success); }
a { color: var(--color-primary-2); }
</style>
