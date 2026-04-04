<template>
  <section class="release-page">
    <header class="hero card" v-if="releaseDetail">
      <div>
        <p class="eyebrow">Release Workspace</p>
        <h1>Release {{ releaseDetail.release.version }}</h1>
        <p class="hero-copy">
          Prepare, review, and approve the evidence required to release this product version.
        </p>
      </div>

      <div class="hero-actions">
        <button class="secondary-button" type="button" @click="loadWorkspace" :disabled="loading || busy">
          {{ loading ? "Refreshing..." : "Refresh" }}
        </button>
        <button
          class="primary-button"
          type="button"
          @click="submitForReview"
          :disabled="busy || !canSubmit"
        >
          {{ busyAction === "submit" ? "Submitting..." : "Submit for review" }}
        </button>
        <button
          v-if="canApprove"
          class="primary-button"
          type="button"
          @click="approveGate"
          :disabled="busy"
        >
          {{ busyAction === "approve" ? "Approving..." : "Approve gate" }}
        </button>
      </div>
    </header>

    <div v-if="errorMessage" class="card feedback feedback-error">{{ errorMessage }}</div>
    <div v-if="successMessage" class="card feedback feedback-success">{{ successMessage }}</div>

    <div v-if="loading && !releaseDetail" class="card feedback">Loading release workspace…</div>

    <template v-else-if="releaseDetail">
      <section class="card progress-card">
        <div class="progress-header">
          <div>
            <p class="eyebrow">Gate Progress</p>
            <h2>{{ acceptedCount }} of {{ requiredCount }} required items accepted</h2>
          </div>
          <span class="status-pill" :class="`status-${releaseDetail.gate.status}`">
            {{ formatLabel(releaseDetail.gate.status) }}
          </span>
        </div>
        <div class="progress-track">
          <span class="progress-fill" :style="{ width: `${progressPercent}%` }" />
        </div>
        <div class="progress-meta">
          <span>Release status: {{ formatLabel(releaseDetail.release.release_status) }}</span>
          <span>Conformity route: {{ formatLabel(releaseDetail.release.conformity_route_snapshot) }}</span>
          <span>Classification: {{ formatLabel(releaseDetail.release.classification_snapshot) }}</span>
          <span v-if="releaseDetail.gate.submitted_by_user">
            Submitted by: {{ formatUser(releaseDetail.gate.submitted_by_user) }}
          </span>
          <span v-if="releaseDetail.gate.approved_by_user">
            Approved by: {{ formatUser(releaseDetail.gate.approved_by_user) }}
          </span>
        </div>
      </section>

      <div class="workspace-grid">
        <section class="card checklist-card">
          <div class="section-head">
            <div>
              <p class="eyebrow">Checklist</p>
              <h2>Required evidence</h2>
            </div>
            <span class="muted">{{ releaseDetail.gate.items.length }} gate item(s)</span>
          </div>

          <div class="checklist">
            <button
              v-for="item in releaseDetail.gate.items"
              :key="item.id"
              class="gate-item"
              :class="{
                selected: selectedItem?.id === item.id,
                accepted: item.status === 'accepted',
                blocked: item.status === 'rejected' || item.status === 'needs_update',
              }"
              type="button"
              @click="selectedItemId = item.id"
            >
              <div class="gate-item-main">
                <strong>{{ item.title }}</strong>
                <p>{{ item.description }}</p>
              </div>
              <div class="gate-item-side">
                <span class="mini-pill" :class="`decision-${item.status}`">{{ formatLabel(item.status) }}</span>
                <span class="muted">{{ item.evidence_links.length }} artifact(s)</span>
              </div>
            </button>
          </div>
        </section>

        <section class="card detail-card" v-if="selectedItem">
          <div class="section-head">
            <div>
              <p class="eyebrow">Gate Item</p>
              <h2>{{ selectedItem.title }}</h2>
            </div>
            <span class="mini-pill" :class="`decision-${selectedItem.status}`">
              {{ formatLabel(selectedItem.status) }}
            </span>
          </div>

          <p class="detail-copy">{{ selectedItem.description }}</p>

          <div class="guidance-box">
            <p class="guidance-title">What to do here</p>
            <p class="guidance-copy">
              Add the evidence that proves this requirement is covered for the selected release. Start with upload if
              you have a file ready. Use an existing file only if it already matches this release.
            </p>
          </div>

          <div class="artifact-actions">
            <button class="primary-button" type="button" @click="toggleUploadMode('upload')">
              Upload evidence
            </button>
            <button class="secondary-button" type="button" @click="toggleUploadMode('external')">
              Add web link
            </button>
            <button class="ghost-button" type="button" @click="toggleExistingEvidence">
              {{ showExistingEvidence ? "Hide existing evidence" : "Use evidence already on file" }}
            </button>
          </div>

          <form v-if="uploadMode === 'upload'" class="upload-panel" @submit.prevent="uploadArtifact">
            <h3>Upload evidence file</h3>
            <label class="field">
              <span>Evidence name</span>
              <input v-model.trim="uploadForm.title" type="text" required maxlength="255" placeholder="e.g. Threat model v1.2" />
            </label>
            <label class="field">
              <span>Evidence type</span>
              <input :value="formatLabel(derivedArtifactType)" type="text" disabled />
            </label>
            <label class="field field-span">
              <span>What does this file show?</span>
              <textarea v-model.trim="uploadForm.description" rows="3" placeholder="Short explanation for reviewers" />
            </label>
            <label class="field field-span">
              <span>Version note</span>
              <textarea v-model.trim="uploadForm.change_summary" rows="2" placeholder="Optional version or update note" />
            </label>
            <label class="field field-span">
              <span>Choose file</span>
              <input
                type="file"
                accept=".pdf,image/*,.png,.jpg,.jpeg,.webp,.svg,.txt,.md,.csv,.json,.xml,.spdx,.cdx,.zip"
                required
                @change="onFileSelected"
              />
            </label>
            <p v-if="selectedFile" class="file-selection">
              Selected: <strong>{{ selectedFile.name }}</strong>
            </p>
            <div class="inline-actions">
              <button class="primary-button" type="submit" :disabled="busy || !selectedFile">
                {{ busyAction === "upload" ? "Uploading..." : "Upload evidence" }}
              </button>
            </div>
          </form>

          <form v-else-if="uploadMode === 'external'" class="upload-panel" @submit.prevent="createExternalLink">
            <h3>Add evidence by web link</h3>
            <label class="field">
              <span>Evidence name</span>
              <input v-model.trim="externalForm.title" type="text" required maxlength="255" />
            </label>
            <label class="field">
              <span>Evidence type</span>
              <input :value="formatLabel(derivedArtifactType)" type="text" disabled />
            </label>
            <label class="field field-span">
              <span>Link</span>
              <input v-model.trim="externalForm.external_url" type="url" required />
            </label>
            <label class="field field-span">
              <span>What does this link show?</span>
              <textarea v-model.trim="externalForm.description" rows="3" />
            </label>
            <div class="inline-actions">
              <button class="primary-button" type="submit" :disabled="busy">
                {{ busyAction === "external" ? "Saving..." : "Save evidence link" }}
              </button>
            </div>
          </form>

          <div v-if="showExistingEvidence" class="library-panel">
            <div class="section-head">
              <div>
                <h3>Evidence already on file</h3>
                <p class="muted">Use this only when an existing file already fits this release and this requirement.</p>
              </div>
              <button class="secondary-button" type="button" @click="refreshLibrary" :disabled="libraryLoading">
                {{ libraryLoading ? "Refreshing..." : "Refresh list" }}
              </button>
            </div>
            <label class="field field-span">
              <span>Search existing evidence</span>
              <input v-model.trim="artifactQuery" type="search" placeholder="Search title or description" @input="filterLibrary" />
            </label>
            <div v-if="filteredLibrary.length === 0" class="empty-panel">No existing evidence found for this product yet.</div>
            <div v-else class="library-list">
              <article v-for="artifact in filteredLibrary" :key="artifact.id" class="library-item">
                <div>
                  <strong>{{ artifact.title }}</strong>
                  <p class="muted">{{ artifact.description || "No description provided." }}</p>
                  <p class="library-meta">
                    {{ formatLabel(artifact.artifact_type) }}
                    <span v-if="artifact.latest_revision">· Revision {{ artifact.latest_revision.revision_number }}</span>
                  </p>
                </div>
                <button
                  class="secondary-button"
                  type="button"
                  :disabled="busy || !artifact.latest_revision"
                  @click="attachRevision(artifact.latest_revision!.id)"
                >
                  Use this file
                </button>
              </article>
            </div>
          </div>

          <div class="evidence-panel">
            <div class="section-head">
              <div>
                <p class="eyebrow">Attached Evidence</p>
                <h3>{{ selectedItem.evidence_links.length }} linked artifact(s)</h3>
              </div>
            </div>

            <div v-if="selectedItem.evidence_links.length === 0" class="empty-panel">
              No evidence linked yet.
            </div>

            <div v-else class="evidence-list">
              <article v-for="link in selectedItem.evidence_links" :key="link.id" class="evidence-card">
                <div class="evidence-card-head">
                  <div class="evidence-identity">
                    <div class="file-badge">{{ fileTypeLabel(link.artifact_revision.original_filename) }}</div>
                    <div>
                      <strong>{{ link.artifact_revision.original_filename || `Revision ${link.artifact_revision.revision_number}` }}</strong>
                      <p class="muted">
                        Revision {{ link.artifact_revision.revision_number }}
                        · {{ formatLabel(link.artifact_revision.source_type) }}
                        <span v-if="link.artifact_revision.file_size_bytes"> · {{ formatSize(link.artifact_revision.file_size_bytes) }}</span>
                      </p>
                    </div>
                  </div>
                  <span class="mini-pill" :class="`decision-${link.decision}`">{{ formatLabel(link.decision) }}</span>
                </div>

                <p v-if="link.artifact_revision.change_summary" class="evidence-note">
                  {{ link.artifact_revision.change_summary }}
                </p>

                <div class="activity-list">
                  <div class="activity-item">
                    <div class="activity-avatar">{{ userInitials(link.artifact_revision.uploaded_by_user) }}</div>
                    <div class="activity-content">
                      <div class="activity-head">
                        <strong>Uploaded</strong>
                        <span class="activity-time">{{ formatDateTime(link.artifact_revision.created_at) }}</span>
                      </div>
                      <p class="activity-copy">
                        {{ formatUser(link.artifact_revision.uploaded_by_user) }}
                        <span class="activity-role">Contributor</span>
                      </p>
                    </div>
                  </div>

                  <div v-if="link.reviewed_by_user || link.reviewed_at || link.rationale" class="activity-item">
                    <div class="activity-avatar review-avatar">{{ userInitials(link.reviewed_by_user) }}</div>
                    <div class="activity-content">
                      <div class="activity-head">
                        <strong>{{ reviewActionLabel(link.decision) }}</strong>
                        <span v-if="link.reviewed_at" class="activity-time">{{ formatDateTime(link.reviewed_at) }}</span>
                      </div>
                      <p class="activity-copy">
                        {{ formatUser(link.reviewed_by_user) }}
                        <span class="activity-role">Security reviewer</span>
                      </p>
                      <p v-if="link.rationale" class="activity-note">{{ link.rationale }}</p>
                    </div>
                  </div>
                </div>

                <div class="inline-actions">
                  <button
                    v-if="link.artifact_revision.storage_path"
                    class="secondary-button"
                    type="button"
                    @click="downloadRevision(link.artifact_revision.id, link.artifact_revision.original_filename || 'artifact')"
                  >
                    Download
                  </button>
                  <a
                    v-else-if="link.artifact_revision.external_url"
                    class="secondary-button external-link"
                    :href="link.artifact_revision.external_url"
                    target="_blank"
                    rel="noreferrer"
                  >
                    Open link
                  </a>
                </div>

                <div v-if="canReview" class="review-grid">
                  <div class="review-box-label">Reviewer note</div>
                  <textarea
                    v-model.trim="reviewNotes[link.id]"
                    rows="2"
                    placeholder="Explain your review decision"
                  />
                  <div class="review-actions">
                    <button class="primary-button" type="button" :disabled="busy" @click="reviewLink(link.id, 'accepted')">Accept</button>
                    <button class="ghost-button" type="button" :disabled="busy" @click="reviewLink(link.id, 'needs_update')">Request update</button>
                    <button class="ghost-button" type="button" :disabled="busy" @click="reviewLink(link.id, 'rejected')">Reject</button>
                    <button class="secondary-button" type="button" :disabled="busy" @click="reviewLink(link.id, 'waived')">Waive</button>
                  </div>
                </div>
              </article>
            </div>
          </div>
        </section>
      </div>
    </template>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from "vue";
import { useRoute } from "vue-router";

import { artifactService } from "@/services/artifact-service";
import { releaseGateService } from "@/services/release-gate-service";
import { useAuthStore } from "@/stores/auth";
import type { ArtifactListRead, ArtifactType } from "@/types/artifact";
import type { GateDecision, ReleaseGateDetailRead, ReleaseGateItemRead } from "@/types/release-gate";

const props = defineProps<{ releaseId: string }>();

const route = useRoute();
const authStore = useAuthStore();

const loading = ref(false);
const busy = ref(false);
const busyAction = ref("");
const errorMessage = ref("");
const successMessage = ref("");
const releaseDetail = ref<ReleaseGateDetailRead | null>(null);
const selectedItemId = ref<string>("");
const library = ref<ArtifactListRead[]>([]);
const filteredLibrary = ref<ArtifactListRead[]>([]);
const libraryLoading = ref(false);
const artifactQuery = ref("");
const uploadMode = ref<"upload" | "external" | "reuse">("upload");
const showExistingEvidence = ref(false);
const selectedFile = ref<File | null>(null);
const reviewNotes = reactive<Record<string, string>>({});

const uploadForm = reactive({
  title: "",
  description: "",
  change_summary: "",
});

const externalForm = reactive({
  title: "",
  external_url: "",
  description: "",
});

const selectedItem = computed<ReleaseGateItemRead | null>(() => {
  if (!releaseDetail.value) return null;
  return releaseDetail.value.gate.items.find((item) => item.id === selectedItemId.value) ?? releaseDetail.value.gate.items[0] ?? null;
});
const derivedArtifactType = computed<ArtifactType>(() => {
  switch (selectedItem.value?.code) {
    case "sbom":
      return "sbom";
    case "test_report":
      return "test_report";
    case "declaration_of_conformity":
      return "declaration";
    case "annex_mapping":
      return "annex_output";
    case "technical_documentation":
    case "risk_assessment":
    default:
      return "document";
  }
});

const acceptedCount = computed(() => releaseDetail.value?.gate.accepted_items_count ?? 0);
const requiredCount = computed(() => releaseDetail.value?.gate.required_items_count ?? 0);
const progressPercent = computed(() => {
  if (!requiredCount.value) return 0;
  return Math.round((acceptedCount.value / requiredCount.value) * 100);
});
const canReview = computed(() => authStore.hasPermission("release_lifecycle_write"));
const canApprove = computed(() => canReview.value && releaseDetail.value?.gate.status !== "approved");
const canSubmit = computed(() => {
  const detail = releaseDetail.value;
  if (!detail) return false;
  return detail.gate.items.some((item) => item.evidence_links.length > 0);
});

function setWorkspace(detail: ReleaseGateDetailRead): void {
  releaseDetail.value = detail;
  if (!selectedItemId.value || !detail.gate.items.some((item) => item.id === selectedItemId.value)) {
    selectedItemId.value = detail.gate.items[0]?.id ?? "";
  }
}

async function loadWorkspace(): Promise<void> {
  loading.value = true;
  errorMessage.value = "";
  try {
    const detail = await releaseGateService.getByRelease(props.releaseId);
    setWorkspace(detail);
    await refreshLibrary();
  } catch (error: any) {
    errorMessage.value = error?.message ?? "Failed to load release workspace.";
  } finally {
    loading.value = false;
  }
}

async function refreshLibrary(): Promise<void> {
  if (!releaseDetail.value) return;
  libraryLoading.value = true;
  try {
    library.value = await artifactService.list({ product_id: releaseDetail.value.release.product_id });
    filterLibrary();
  } catch {
    // Keep existing list if refresh fails.
  } finally {
    libraryLoading.value = false;
  }
}

function filterLibrary(): void {
  const query = artifactQuery.value.trim().toLowerCase();
  filteredLibrary.value = !query
    ? [...library.value]
    : library.value.filter((artifact) =>
        [artifact.title, artifact.description ?? ""].some((value) => value.toLowerCase().includes(query)),
      );
}

function toggleUploadMode(mode: "upload" | "external"): void {
  uploadMode.value = mode;
}

function toggleExistingEvidence(): void {
  showExistingEvidence.value = !showExistingEvidence.value;
  if (showExistingEvidence.value) {
    void refreshLibrary();
  }
}

function onFileSelected(event: Event): void {
  const input = event.target as HTMLInputElement;
  selectedFile.value = input.files?.[0] ?? null;
  if (!selectedFile.value) {
    return;
  }

  if (!uploadForm.title.trim()) {
    uploadForm.title = selectedFile.value.name.replace(/\.[^/.]+$/, "");
  }
}

async function uploadArtifact(): Promise<void> {
  if (!releaseDetail.value || !selectedItem.value || !selectedFile.value) return;
  busy.value = true;
  busyAction.value = "upload";
  errorMessage.value = "";
  successMessage.value = "";
  try {
    const formData = new FormData();
    formData.append("title", uploadForm.title);
    formData.append(
      "artifact_type",
      selectedFile.value.type.startsWith("image/") ? "screenshot" : derivedArtifactType.value,
    );
    formData.append("description", uploadForm.description);
    formData.append("change_summary", uploadForm.change_summary);
    formData.append("upload", selectedFile.value);
    const detail = await releaseGateService.uploadEvidence(
      releaseDetail.value.release.id,
      selectedItem.value.id,
      formData,
    );
    setWorkspace(detail);
    successMessage.value = "Evidence uploaded and attached to this requirement.";
    uploadForm.title = "";
    uploadForm.description = "";
    uploadForm.change_summary = "";
    selectedFile.value = null;
    await refreshLibrary();
  } catch (error: any) {
    errorMessage.value = error?.message ?? "Failed to upload artifact.";
  } finally {
    busy.value = false;
    busyAction.value = "";
  }
}

async function createExternalLink(): Promise<void> {
  if (!releaseDetail.value || !selectedItem.value) return;
  busy.value = true;
  busyAction.value = "external";
  errorMessage.value = "";
  successMessage.value = "";
  try {
    const formData = new FormData();
    formData.append("title", externalForm.title);
    formData.append("artifact_type", derivedArtifactType.value);
    formData.append("external_url", externalForm.external_url);
    formData.append("description", externalForm.description);
    formData.append("change_summary", externalForm.description);
    const detail = await releaseGateService.addEvidenceLink(
      releaseDetail.value.release.id,
      selectedItem.value.id,
      formData,
    );
    setWorkspace(detail);
    successMessage.value = "Evidence link saved and attached to this requirement.";
    externalForm.title = "";
    externalForm.description = "";
    externalForm.external_url = "";
    await refreshLibrary();
  } catch (error: any) {
    errorMessage.value = error?.message ?? "Failed to attach external evidence.";
  } finally {
    busy.value = false;
    busyAction.value = "";
  }
}

async function attachRevision(revisionId: string): Promise<void> {
  if (!releaseDetail.value || !selectedItem.value) return;
  busy.value = true;
  busyAction.value = "attach";
  errorMessage.value = "";
  successMessage.value = "";
  try {
    const detail = await releaseGateService.attachEvidence(releaseDetail.value.release.id, selectedItem.value.id, revisionId);
    setWorkspace(detail);
    successMessage.value = "Artifact revision attached to the selected gate item.";
  } catch (error: any) {
    errorMessage.value = error?.message ?? "Failed to attach artifact revision.";
  } finally {
    busy.value = false;
    busyAction.value = "";
  }
}

async function reviewLink(linkId: string, decision: GateDecision): Promise<void> {
  busy.value = true;
  busyAction.value = "review";
  errorMessage.value = "";
  successMessage.value = "";
  try {
    const detail = await releaseGateService.reviewEvidence(linkId, decision, reviewNotes[linkId]);
    setWorkspace(detail);
    successMessage.value = `Evidence ${formatLabel(decision)}.`;
  } catch (error: any) {
    errorMessage.value = error?.message ?? "Failed to review evidence.";
  } finally {
    busy.value = false;
    busyAction.value = "";
  }
}

async function submitForReview(): Promise<void> {
  if (!releaseDetail.value) return;
  busy.value = true;
  busyAction.value = "submit";
  errorMessage.value = "";
  successMessage.value = "";
  try {
    const detail = await releaseGateService.submit(releaseDetail.value.release.id);
    setWorkspace(detail);
    successMessage.value = "Release gate submitted for review.";
  } catch (error: any) {
    errorMessage.value = error?.message ?? "Failed to submit release gate.";
  } finally {
    busy.value = false;
    busyAction.value = "";
  }
}

async function approveGate(): Promise<void> {
  if (!releaseDetail.value) return;
  busy.value = true;
  busyAction.value = "approve";
  errorMessage.value = "";
  successMessage.value = "";
  try {
    const detail = await releaseGateService.approve(releaseDetail.value.release.id);
    setWorkspace(detail);
    successMessage.value = "Release gate approved.";
  } catch (error: any) {
    errorMessage.value = error?.message ?? "Failed to approve release gate.";
  } finally {
    busy.value = false;
    busyAction.value = "";
  }
}

async function downloadRevision(revisionId: string, filename: string): Promise<void> {
  try {
    await artifactService.downloadRevision(revisionId, filename);
  } catch (error: any) {
    errorMessage.value = error?.message ?? "Failed to download artifact revision.";
  }
}

function formatLabel(value: string): string {
  return value
    .replaceAll("_", " ")
    .replace(/\b\w/g, (character) => character.toUpperCase());
}

function formatDateTime(value: string | null): string {
  if (!value) return "—";
  return new Intl.DateTimeFormat("en", {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(new Date(value));
}

function formatSize(value: number): string {
  if (value < 1024) return `${value} B`;
  if (value < 1024 * 1024) return `${(value / 1024).toFixed(1)} KB`;
  return `${(value / (1024 * 1024)).toFixed(1)} MB`;
}

function formatUser(user: { full_name: string; email: string } | null): string {
  if (!user) return "Unknown user";
  const fullName = user.full_name?.trim();
  return fullName ? `${fullName} (${user.email})` : user.email;
}

function userInitials(user: { full_name: string; email: string } | null): string {
  if (!user) return "NA";
  const source = user.full_name?.trim() || user.email;
  const parts = source.split(/\s+/).filter(Boolean);
  if (parts.length === 1) {
    return parts[0].slice(0, 2).toUpperCase();
  }
  return `${parts[0][0] ?? ""}${parts[1][0] ?? ""}`.toUpperCase();
}

function reviewActionLabel(decision: GateDecision): string {
  switch (decision) {
    case "accepted":
      return "Approved";
    case "needs_update":
      return "Requested update";
    case "rejected":
      return "Rejected";
    case "waived":
      return "Waived";
    default:
      return "Reviewed";
  }
}

function fileTypeLabel(filename: string | null): string {
  if (!filename || !filename.includes(".")) return "FILE";
  return filename.split(".").pop()?.slice(0, 4).toUpperCase() ?? "FILE";
}

onMounted(() => {
  if (route.params.releaseId) {
    loadWorkspace();
  }
});
</script>

<style scoped>
.release-page {
  display: grid;
  gap: 1.25rem;
}

.hero {
  display: flex;
  justify-content: space-between;
  gap: 1rem;
  align-items: start;
  background:
    radial-gradient(circle at top right, rgba(110, 168, 254, 0.18), transparent 42%),
    linear-gradient(135deg, rgba(139, 92, 246, 0.16), rgba(15, 26, 46, 0.72) 55%);
}

.hero-copy,
.detail-copy,
.muted {
  color: var(--color-text-muted, rgba(233, 238, 252, 0.72));
}

.eyebrow {
  margin: 0 0 0.35rem;
  text-transform: uppercase;
  letter-spacing: 0.12em;
  font-size: 0.75rem;
  color: var(--color-primary, #6ea8fe);
}

.hero h1,
.progress-card h2,
.section-head h2,
.section-head h3 {
  margin: 0;
  color: var(--color-text, #e9eefc);
}

.hero-actions,
.artifact-actions,
.inline-actions,
.review-actions {
  display: flex;
  gap: 0.75rem;
  flex-wrap: wrap;
}

.progress-header,
.section-head,
.evidence-card-head {
  display: flex;
  justify-content: space-between;
  gap: 1rem;
  align-items: start;
}

.progress-track {
  margin-top: 1rem;
  height: 0.75rem;
  background: rgba(255, 255, 255, 0.08);
  border-radius: 999px;
  overflow: hidden;
}

.progress-fill {
  display: block;
  height: 100%;
  background: linear-gradient(90deg, var(--color-primary-2, #8b5cf6), var(--color-primary, #6ea8fe));
}

.progress-meta {
  margin-top: 0.85rem;
  display: flex;
  gap: 1rem;
  flex-wrap: wrap;
  color: var(--color-text-muted, rgba(233, 238, 252, 0.72));
  font-size: 0.92rem;
}

.workspace-grid {
  display: grid;
  grid-template-columns: minmax(280px, 360px) minmax(0, 1fr);
  gap: 1.25rem;
}

.checklist {
  display: grid;
  gap: 0.75rem;
}

.gate-item {
  border: 1px solid var(--color-border, rgba(233, 238, 252, 0.14));
  background: var(--color-surface-soft, rgba(255, 255, 255, 0.03));
  border-radius: 0.95rem;
  padding: 1rem;
  display: flex;
  justify-content: space-between;
  gap: 1rem;
  text-align: left;
}

.gate-item.selected {
  border-color: rgba(110, 168, 254, 0.55);
  box-shadow: 0 0 0 2px rgba(110, 168, 254, 0.14);
}

.gate-item.accepted {
  background: rgba(52, 211, 153, 0.08);
}

.gate-item.blocked {
  background: rgba(251, 113, 133, 0.08);
}

.gate-item-main p {
  margin: 0.35rem 0 0;
  color: var(--color-text-muted, rgba(233, 238, 252, 0.72));
}

.gate-item-side {
  display: grid;
  justify-items: end;
  gap: 0.5rem;
}

.status-pill,
.mini-pill {
  display: inline-flex;
  align-items: center;
  padding: 0.32rem 0.7rem;
  border-radius: 999px;
  font-weight: 700;
  font-size: 0.8rem;
}

.status-draft,
.decision-pending_review {
  background: rgba(251, 191, 36, 0.14);
  color: #fde68a;
}

.status-in_review,
.decision-waived {
  background: rgba(110, 168, 254, 0.14);
  color: #bfdbfe;
}

.status-approved,
.decision-accepted {
  background: rgba(52, 211, 153, 0.14);
  color: #86efac;
}

.status-blocked,
.decision-rejected,
.decision-needs_update {
  background: rgba(251, 113, 133, 0.14);
  color: #fda4af;
}

.detail-card {
  display: grid;
  gap: 1.25rem;
}

.primary-button,
.secondary-button,
.ghost-button {
  border: 1px solid transparent;
  border-radius: 10px;
  padding: 0.75rem 1rem;
  font: inherit;
  cursor: pointer;
  transition: transform 0.15s ease, border-color 0.15s ease, background 0.15s ease;
}

.primary-button:hover,
.secondary-button:hover,
.ghost-button:hover {
  transform: translateY(-1px);
}

.primary-button {
  background: #0f172a;
  color: #fff;
}

.secondary-button {
  background: #e2e8f0;
  color: #0f172a;
}

.ghost-button {
  background: transparent;
  color: #334155;
  border-color: #cbd5e1;
}

.primary-button:disabled,
.secondary-button:disabled,
.ghost-button:disabled {
  opacity: 0.65;
  cursor: not-allowed;
  transform: none;
}

.guidance-box {
  border: 1px solid rgba(148, 163, 184, 0.2);
  border-radius: 12px;
  padding: 1rem;
  background: rgba(255, 255, 255, 0.04);
}

.guidance-title {
  margin: 0 0 0.35rem;
  font-weight: 700;
}

.guidance-copy {
  margin: 0;
}

.upload-panel,
.library-panel,
.evidence-panel {
  display: grid;
  gap: 0.85rem;
  padding-top: 1rem;
  border-top: 1px solid rgba(125, 92, 39, 0.1);
}

.field {
  display: grid;
  gap: 0.35rem;
}

.field-span {
  grid-column: 1 / -1;
}

.field input,
.field select,
.field textarea,
.review-grid textarea {
  width: 100%;
  border: 1px solid var(--color-border, rgba(233, 238, 252, 0.14));
  border-radius: 0.8rem;
  padding: 0.75rem 0.9rem;
  background: rgba(255, 255, 255, 0.04);
  color: var(--color-text, #e9eefc);
}

.file-selection {
  margin: 0;
  color: var(--color-text-muted, rgba(233, 238, 252, 0.72));
}

.library-list,
.evidence-list {
  display: grid;
  gap: 0.75rem;
}

.library-item,
.evidence-card {
  border: 1px solid var(--color-border, rgba(233, 238, 252, 0.14));
  border-radius: 0.9rem;
  padding: 1rem;
  background: var(--color-surface-soft, rgba(255, 255, 255, 0.03));
}

.library-item {
  display: flex;
  justify-content: space-between;
  gap: 1rem;
  align-items: start;
}

.evidence-identity {
  display: flex;
  gap: 0.9rem;
  align-items: flex-start;
}

.file-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 3rem;
  padding: 0.45rem 0.6rem;
  border-radius: 0.85rem;
  background: rgba(110, 168, 254, 0.14);
  color: #bfdbfe;
  font-size: 0.74rem;
  font-weight: 800;
  letter-spacing: 0.08em;
}

.library-meta,
.evidence-meta,
.evidence-note,
.review-rationale {
  margin: 0.35rem 0 0;
  color: var(--color-text-muted, rgba(233, 238, 252, 0.72));
}

.activity-list {
  display: grid;
  gap: 0.85rem;
}

.activity-item {
  display: grid;
  grid-template-columns: auto minmax(0, 1fr);
  gap: 0.85rem;
  align-items: start;
}

.activity-avatar {
  width: 2.25rem;
  height: 2.25rem;
  border-radius: 999px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  background: rgba(110, 168, 254, 0.18);
  color: #dbeafe;
  font-weight: 800;
  font-size: 0.8rem;
}

.review-avatar {
  background: rgba(52, 211, 153, 0.16);
  color: #bbf7d0;
}

.activity-content {
  display: grid;
  gap: 0.2rem;
  min-width: 0;
}

.activity-head {
  display: flex;
  justify-content: space-between;
  gap: 1rem;
  align-items: center;
  flex-wrap: wrap;
}

.activity-time,
.activity-copy,
.activity-note,
.review-box-label {
  color: var(--color-text-muted, rgba(233, 238, 252, 0.72));
}

.activity-copy,
.activity-note {
  margin: 0;
}

.activity-role {
  display: inline-flex;
  align-items: center;
  margin-left: 0.5rem;
  padding: 0.18rem 0.48rem;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.06);
  font-size: 0.75rem;
}

.activity-note {
  padding: 0.7rem 0.85rem;
  border-radius: 0.8rem;
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid var(--color-border, rgba(233, 238, 252, 0.14));
}

.evidence-meta {
  display: flex;
  gap: 1rem;
  flex-wrap: wrap;
  font-size: 0.9rem;
}

.review-grid {
  display: grid;
  gap: 0.75rem;
  margin-top: 0.9rem;
}

.external-link {
  text-decoration: none;
  display: inline-flex;
  align-items: center;
}

.empty-panel,
.feedback {
  padding: 1rem 1.1rem;
  border-radius: 0.9rem;
  background: rgba(255, 255, 255, 0.03);
  border: 1px dashed var(--color-border, rgba(233, 238, 252, 0.14));
  color: var(--color-text-muted, rgba(233, 238, 252, 0.72));
}

@media (max-width: 1080px) {
  .workspace-grid {
    grid-template-columns: 1fr;
  }

  .hero {
    flex-direction: column;
  }
}
</style>
