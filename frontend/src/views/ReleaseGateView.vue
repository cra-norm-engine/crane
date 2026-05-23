<template>
  <section class="release-page">

    <!-- ── Page header ── -->
    <header class="hero card" v-if="releaseDetail">
      <div class="hero-body">
        <div>
          <p class="eyebrow">Release Workspace</p>
          <h1 class="hero-title">{{ releaseDetail.release.display_version }}</h1>
        </div>
        <div class="hero-meta-row">
          <span class="meta-chip" :class="`chip-${releaseDetail.release.release_status}`">
            {{ formatLabel(releaseDetail.release.release_status) }}
          </span>
          <span class="meta-chip chip-neutral">
            {{ formatLabel(releaseDetail.release.classification_snapshot) }}
          </span>
          <span class="meta-chip chip-neutral">
            {{ formatLabel(releaseDetail.release.conformity_route_snapshot) }}
          </span>
          <span v-if="releaseDetail.release.planned_release_date" class="meta-chip chip-neutral">
            Planned {{ formatDate(releaseDetail.release.planned_release_date) }}
          </span>
        </div>
      </div>

      <div class="hero-actions">
        <button class="btn-ghost" type="button" @click="loadWorkspace" :disabled="loading || busy">
          <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="1 4 1 10 7 10"/><path d="M3.51 15a9 9 0 1 0 .49-4.9"/></svg>
          {{ loading ? "Refreshing…" : "Refresh" }}
        </button>
        <button
          v-if="!isApproved"
          class="btn-secondary"
          type="button"
          @click="submitForReview"
          :disabled="busy || !canSubmit"
        >
          {{ busyAction === "submit" ? "Submitting…" : "Submit for review" }}
        </button>
        <button
          v-if="canApprove"
          class="btn-primary"
          type="button"
          @click="approveGate"
          :disabled="busy"
        >
          <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg>
          {{ busyAction === "approve" ? "Approving…" : "Approve gate" }}
        </button>
        <button
          v-if="isApproved && canDownload && releaseDetail.gate.bundle_sha256"
          class="btn-secondary"
          type="button"
          @click="downloadBundle"
          :disabled="busy"
        >
          <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>
          {{ busyAction === "download" ? "Downloading…" : "Technical Documentation" }}
        </button>
      </div>
    </header>

    <div v-if="errorMessage" class="feedback feedback-error">{{ errorMessage }}</div>
    <div v-if="successMessage" class="feedback feedback-success">{{ successMessage }}</div>
    <div v-if="loading && !releaseDetail" class="feedback">Loading release workspace…</div>

    <template v-else-if="releaseDetail">

      <!-- ── Progress strip ── -->
      <section class="card progress-card">
        <div class="progress-top">
          <div class="progress-title-group">
            <p class="eyebrow">Gate Progress</p>
            <h2 class="progress-heading">{{ acceptedCount }} / {{ requiredCount }} required items accepted</h2>
          </div>
          <span class="status-pill" :class="`status-${releaseDetail.gate.status}`">
            {{ formatLabel(releaseDetail.gate.status) }}
          </span>
        </div>

        <div class="progress-bar-wrap">
          <div class="progress-track">
            <span class="progress-fill" :style="{ width: `${progressPercent}%` }" />
          </div>
          <span class="progress-pct">{{ progressPercent }}%</span>
        </div>

        <div class="progress-chips">
          <span v-if="releaseDetail.gate.submitted_by_user" class="prog-chip">
            <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="8" r="4"/><path d="M4 20c0-4 3.6-7 8-7s8 3 8 7"/></svg>
            Submitted by {{ formatUser(releaseDetail.gate.submitted_by_user) }}
          </span>
          <span v-if="releaseDetail.gate.approved_by_user" class="prog-chip prog-chip-green">
            <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg>
            Approved by {{ formatUser(releaseDetail.gate.approved_by_user) }}
          </span>
        </div>
      </section>

      <!-- CRA Art. 13(2) — Known Exploitable Vulnerabilities blocking banner -->
      <div
        v-if="releaseDetail.release.has_known_exploitable_vulnerabilities"
        class="kev-banner"
        role="alert"
      >
        <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none"
          stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/>
          <line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/>
        </svg>
        <div class="kev-banner-body">
          <strong>Known exploitable vulnerabilities detected</strong>
          <p>This release contains known exploitable vulnerabilities (CRA Art. 13(2)). Gate approval is blocked until all exploitable findings are resolved in the Vulnerability Reports section.</p>
          <p v-if="releaseDetail.release.kev_notes" class="kev-notes">{{ releaseDetail.release.kev_notes }}</p>
        </div>
      </div>

      <!-- ── Workspace ── -->
      <div class="workspace-grid">

        <!-- Left: gate item checklist -->
        <section class="card checklist-card">
          <div class="checklist-head">
            <p class="eyebrow">Evidence checklist</p>
            <div class="checklist-head-right">
              <span class="item-count">{{ acceptedCount }}/{{ releaseDetail.gate.items.length }}</span>
              <button
                v-if="canEdit && !isApproved"
                class="btn-ghost btn-sm"
                type="button"
                @click="showAddItemForm = !showAddItemForm"
              >
                <svg xmlns="http://www.w3.org/2000/svg" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>
                Add item
              </button>
            </div>
          </div>

          <!-- Add checklist item form -->
          <form v-if="showAddItemForm && canEdit && !isApproved" class="add-item-form" @submit.prevent="addChecklistItem">
            <label class="field">
              <span class="field-label">Item title</span>
              <input v-model.trim="addItemForm.title" type="text" required maxlength="255" placeholder="e.g. Penetration test report" />
            </label>
            <label class="field">
              <span class="field-label">Description <span class="field-optional">(optional)</span></span>
              <input v-model.trim="addItemForm.description" type="text" maxlength="2000" placeholder="What evidence is required?" />
            </label>
            <div class="add-item-actions">
              <button class="btn-primary" type="submit" :disabled="busy || !addItemForm.title.trim()">
                {{ busyAction === "add-item" ? "Adding…" : "Add to checklist" }}
              </button>
              <button class="btn-ghost btn-sm" type="button" @click="showAddItemForm = false">Cancel</button>
            </div>
          </form>

          <nav class="checklist" aria-label="Gate items">
            <div
              v-for="item in releaseDetail.gate.items"
              :key="item.id"
              class="gate-item-row"
            >
              <button
                class="gate-item"
                :class="{
                  'gate-item--selected': selectedItem?.id === item.id,
                  'gate-item--accepted': item.status === 'accepted',
                  'gate-item--blocked': item.status === 'rejected' || item.status === 'needs_update',
                  'gate-item--waived': item.status === 'waived',
                }"
                type="button"
                @click="selectedItemId = item.id"
              >
                <div class="gate-item-icon" aria-hidden="true">
                  <!-- accepted -->
                  <svg v-if="item.status === 'accepted'" xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg>
                  <!-- blocked -->
                  <svg v-else-if="item.status === 'rejected' || item.status === 'needs_update'" xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>
                  <!-- waived -->
                  <svg v-else-if="item.status === 'waived'" xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><line x1="8" y1="12" x2="16" y2="12"/></svg>
                  <!-- pending -->
                  <svg v-else xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/></svg>
                </div>

                <div class="gate-item-body">
                  <span class="gate-item-title">{{ item.title }}</span>
                  <span class="gate-item-count">{{ item.evidence_links.length }} artifact{{ item.evidence_links.length !== 1 ? 's' : '' }}</span>
                </div>

                <span class="mini-pill" :class="`decision-${item.status}`">
                  {{ formatLabel(item.status) }}
                </span>
              </button>
              <button
                v-if="canEdit && !isApproved"
                class="gate-item-delete"
                type="button"
                :title="`Remove &quot;${item.title}&quot; from checklist`"
                @click.stop="confirmRemoveItem(item)"
              >
                <svg xmlns="http://www.w3.org/2000/svg" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="3 6 5 6 21 6"/><path d="M19 6l-1 14a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2L5 6"/><path d="M10 11v6"/><path d="M14 11v6"/><path d="M9 6V4a1 1 0 0 1 1-1h4a1 1 0 0 1 1 1v2"/></svg>
              </button>
            </div>
          </nav>
        </section>

        <!-- Right: detail panel -->
        <section class="card detail-card" v-if="selectedItem">

          <!-- Detail header -->
          <div class="detail-header">
            <div class="detail-header-left">
              <p class="eyebrow">Gate Item</p>
              <h2 class="detail-title">{{ selectedItem.title }}</h2>
              <p class="detail-copy">{{ selectedItem.description }}</p>
            </div>
            <span class="mini-pill" :class="`decision-${selectedItem.status}`">
              {{ formatLabel(selectedItem.status) }}
            </span>
          </div>

          <!-- Frozen banner -->
          <div v-if="isApproved" class="frozen-banner">
            <div class="frozen-banner-icon" aria-hidden="true">
              <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <rect x="3" y="11" width="18" height="11" rx="2" ry="2"/>
                <path d="M7 11V7a5 5 0 0 1 10 0v4"/>
              </svg>
            </div>
            <div>
              <p class="frozen-banner-title">Approved — evidence frozen</p>
              <p class="frozen-banner-copy">
                Approved
                <template v-if="releaseDetail.gate.approved_by_user">by <strong>{{ formatUser(releaseDetail.gate.approved_by_user) }}</strong></template>
                <template v-if="releaseDetail.gate.approved_at"> on {{ formatDateTime(releaseDetail.gate.approved_at) }}</template>.
                No changes are permitted.
              </p>
              <p v-if="releaseDetail.gate.bundle_sha256" class="frozen-banner-hash">
                <span class="hash-label">Bundle SHA-256:</span>
                <code class="hash-value" :title="releaseDetail.gate.bundle_sha256">{{ releaseDetail.gate.bundle_sha256.slice(0, 16) }}…</code>
                <button class="btn-copy" type="button" @click="copyHash(releaseDetail.gate.bundle_sha256!)">
                  <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/></svg>
                  Copy
                </button>
              </p>
            </div>
          </div>

          <!-- ── Add evidence zone (hidden when frozen) ── -->
          <div v-if="!isApproved" class="add-evidence-zone">
            <div class="add-evidence-header">
              <p class="add-evidence-label">Add evidence</p>
              <div class="add-tabs" role="tablist">
                <button
                  class="add-tab"
                  :class="{ 'add-tab--active': uploadMode === 'upload' && !showExistingEvidence }"
                  type="button"
                  role="tab"
                  @click="uploadMode = 'upload'; showExistingEvidence = false"
                >
                  <svg xmlns="http://www.w3.org/2000/svg" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" y1="3" x2="12" y2="15"/></svg>
                  Upload file
                </button>
                <button
                  class="add-tab"
                  :class="{ 'add-tab--active': uploadMode === 'external' && !showExistingEvidence }"
                  type="button"
                  role="tab"
                  @click="uploadMode = 'external'; showExistingEvidence = false"
                >
                  <svg xmlns="http://www.w3.org/2000/svg" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"/><path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"/></svg>
                  Web link
                </button>
                <button
                  class="add-tab"
                  :class="{ 'add-tab--active': showExistingEvidence }"
                  type="button"
                  role="tab"
                  @click="toggleExistingEvidence"
                >
                  <svg xmlns="http://www.w3.org/2000/svg" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>
                  From library
                </button>
              </div>
            </div>

            <!-- Upload file form -->
            <form v-if="!showExistingEvidence && uploadMode === 'upload'" class="evidence-form" @submit.prevent="uploadArtifact">
              <div class="form-grid">
                <label class="field">
                  <span class="field-label">Evidence name</span>
                  <input v-model.trim="uploadForm.title" type="text" required maxlength="255" placeholder="e.g. Threat model v1.2" />
                </label>
                <label class="field">
                  <span class="field-label">Evidence type</span>
                  <input :value="formatLabel(derivedArtifactType)" type="text" disabled />
                </label>
                <label class="field field-full">
                  <span class="field-label">What does this file show?</span>
                  <textarea v-model.trim="uploadForm.description" rows="2" placeholder="Short explanation for reviewers" />
                </label>
                <label class="field field-full">
                  <span class="field-label">Version note <span class="field-optional">(optional)</span></span>
                  <textarea v-model.trim="uploadForm.change_summary" rows="2" placeholder="Describe what changed in this display_version" />
                </label>
                <div class="field field-full">
                  <span class="field-label">Choose file</span>
                  <DropZone
                    accept=".pdf,image/*,.png,.jpg,.jpeg,.webp,.svg,.txt,.md,.csv,.json,.xml,.spdx,.cdx,.zip"
                    :multiple="false"
                    hint="Supports: PDF, images, SBOM files, test reports"
                    @files-selected="onFilesSelected"
                  />
                  <div v-if="selectedFile" class="file-selected-info">
                    <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>
                    {{ selectedFile.name }}
                  </div>
                </div>
              </div>
              <div class="form-footer">
                <button class="btn-primary" type="submit" :disabled="busy || !selectedFile">
                  {{ busyAction === "upload" ? "Uploading…" : "Upload evidence" }}
                </button>
              </div>
            </form>

            <!-- Web link form -->
            <form v-else-if="!showExistingEvidence && uploadMode === 'external'" class="evidence-form" @submit.prevent="createExternalLink">
              <div class="form-grid">
                <label class="field">
                  <span class="field-label">Evidence name</span>
                  <input v-model.trim="externalForm.title" type="text" required maxlength="255" />
                </label>
                <label class="field">
                  <span class="field-label">Evidence type</span>
                  <input :value="formatLabel(derivedArtifactType)" type="text" disabled />
                </label>
                <label class="field field-full">
                  <span class="field-label">URL</span>
                  <input v-model.trim="externalForm.external_url" type="url" required placeholder="https://…" />
                </label>
                <label class="field field-full">
                  <span class="field-label">Description <span class="field-optional">(optional)</span></span>
                  <textarea v-model.trim="externalForm.description" rows="2" placeholder="What does this link show?" />
                </label>
              </div>
              <div class="form-footer">
                <button class="btn-primary" type="submit" :disabled="busy">
                  {{ busyAction === "external" ? "Saving…" : "Save evidence link" }}
                </button>
              </div>
            </form>

            <!-- Library panel -->
            <div v-else-if="showExistingEvidence" class="library-panel">
              <div class="library-toolbar">
                <input v-model.trim="artifactQuery" type="search" class="library-search" placeholder="Search title or description…" @input="filterLibrary" />
                <button class="btn-ghost" type="button" @click="refreshLibrary" :disabled="libraryLoading">
                  {{ libraryLoading ? "Refreshing…" : "Refresh" }}
                </button>
              </div>
              <p class="library-hint">Use only when an existing file already fits this release and this requirement.</p>
              <div v-if="filteredLibrary.length === 0" class="empty-panel">No existing evidence found for this product yet.</div>
              <div v-else class="library-list">
                <article v-for="artifact in filteredLibrary" :key="artifact.id" class="library-item">
                  <div class="library-item-info">
                    <strong>{{ artifact.title }}</strong>
                    <p class="muted">{{ artifact.description || "No description provided." }}</p>
                    <p class="library-meta">
                      {{ formatLabel(artifact.artifact_type) }}
                      <span v-if="artifact.latest_revision">· Rev {{ artifact.latest_revision.revision_number }}</span>
                    </p>
                  </div>
                  <button
                    class="btn-secondary"
                    type="button"
                    :disabled="busy || !artifact.latest_revision"
                    @click="attachRevision(artifact.latest_revision!.id)"
                  >
                    Use this
                  </button>
                </article>
              </div>
            </div>
          </div>

          <!-- ── Detail tabs navigation ── -->
          <div class="detail-tabs-nav">
            <button
              class="detail-tab"
              :class="{ 'detail-tab--active': detailTabsActive === 'evidence' }"
              type="button"
              @click="detailTabsActive = 'evidence'"
            >
              <svg xmlns="http://www.w3.org/2000/svg" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>
              Evidence
            </button>
            <button
              class="detail-tab"
              :class="{ 'detail-tab--active': detailTabsActive === 'history' }"
              type="button"
              @click="loadRevisionHistory"
            >
              <svg xmlns="http://www.w3.org/2000/svg" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>
              History
            </button>
            <button
              v-if="selectedItem.code === 'sbom'"
              class="detail-tab"
              :class="{ 'detail-tab--active': detailTabsActive === 'diff' }"
              type="button"
              @click="loadSbomDiff"
            >
              <svg xmlns="http://www.w3.org/2000/svg" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M9 11l3 3L22 4"/><path d="M20.24 12.52a6.5 6.5 0 0 0-9.26-9.26M4.2 4.2a6.5 6.5 0 0 0 9.26 9.26"/></svg>
              Diff
            </button>
            <button
              class="detail-tab"
              :class="{ 'detail-tab--active': detailTabsActive === 'dependencies' }"
              type="button"
              @click="detailTabsActive = 'dependencies'"
            >
              <svg xmlns="http://www.w3.org/2000/svg" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 3v18M3 12h18"/></svg>
              Dependencies
            </button>
            <button
              v-if="isApproved"
              class="detail-tab"
              :class="{ 'detail-tab--active': detailTabsActive === 'snapshot' }"
              type="button"
              @click="detailTabsActive = 'snapshot'"
            >
              <svg xmlns="http://www.w3.org/2000/svg" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="11" width="18" height="11" rx="2" ry="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/></svg>
              Snapshot
            </button>
          </div>

          <!-- ── Evidence tab ── -->
          <div v-if="detailTabsActive === 'evidence'" class="evidence-section">
            <div class="evidence-section-header">
              <div class="evidence-section-title">
                <svg v-if="isApproved" xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="3" y="11" width="18" height="11" rx="2" ry="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/></svg>
                <span>{{ isApproved ? "Frozen snapshot" : "Attached evidence" }}</span>
              </div>
              <span class="evidence-count">{{ selectedItem.evidence_links.length }}</span>
            </div>

            <div v-if="selectedItem.evidence_links.length === 0" class="empty-panel">
              No evidence linked yet. Use the panel above to attach your first artifact.
            </div>

            <div v-else class="evidence-list">
              <article
                v-for="link in selectedItem.evidence_links"
                :key="link.id"
                class="evidence-card"
                :class="`ev-${link.decision}`"
              >
                <!-- Card top row -->
                <div class="ev-top">
                  <div class="ev-identity">
                    <div class="file-badge">{{ fileTypeLabel(link.artifact_revision.original_filename) }}</div>
                    <div class="ev-name-group">
                      <strong class="ev-name">{{ link.artifact_revision.original_filename || `Revision ${link.artifact_revision.revision_number}` }}</strong>
                      <span class="ev-meta">
                        Rev {{ link.artifact_revision.revision_number }}
                        · {{ formatLabel(link.artifact_revision.source_type) }}
                        <template v-if="link.artifact_revision.file_size_bytes"> · {{ formatSize(link.artifact_revision.file_size_bytes) }}</template>
                      </span>
                    </div>
                  </div>
                  <span class="mini-pill" :class="`decision-${link.decision}`">{{ formatLabel(link.decision) }}</span>
                </div>

                <!-- Change summary -->
                <p v-if="link.artifact_revision.change_summary" class="ev-note">
                  {{ link.artifact_revision.change_summary }}
                </p>

                <!-- Activity row -->
                <div class="ev-activity">
                  <div class="ev-activity-item">
                    <div class="ev-avatar">{{ userInitials(link.artifact_revision.uploaded_by_user) }}</div>
                    <div class="ev-activity-text">
                      <span class="ev-activity-action">Uploaded</span>
                      <span class="ev-activity-who">{{ formatUser(link.artifact_revision.uploaded_by_user) }}</span>
                      <span class="ev-activity-when">{{ formatDateTime(link.artifact_revision.created_at) }}</span>
                    </div>
                  </div>
                  <div v-if="link.reviewed_by_user || link.reviewed_at" class="ev-activity-item">
                    <div class="ev-avatar ev-avatar--review">{{ userInitials(link.reviewed_by_user) }}</div>
                    <div class="ev-activity-text">
                      <span class="ev-activity-action">{{ reviewActionLabel(link.decision) }}</span>
                      <span class="ev-activity-who">{{ formatUser(link.reviewed_by_user) }}</span>
                      <span v-if="link.reviewed_at" class="ev-activity-when">{{ formatDateTime(link.reviewed_at) }}</span>
                    </div>
                  </div>
                </div>

                <!-- Rationale note -->
                <p v-if="link.rationale" class="ev-rationale">{{ link.rationale }}</p>

                <!-- Actions row -->
                <div class="ev-actions">
                  <button
                    v-if="link.artifact_revision.storage_path"
                    class="btn-ghost btn-sm"
                    type="button"
                    @click="downloadRevision(link.artifact_revision.id, link.artifact_revision.original_filename || 'artifact')"
                  >
                    <svg xmlns="http://www.w3.org/2000/svg" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>
                    Download
                  </button>
                  <a
                    v-else-if="link.artifact_revision.external_url"
                    class="btn-ghost btn-sm"
                    :href="link.artifact_revision.external_url"
                    target="_blank"
                    rel="noreferrer"
                  >
                    <svg xmlns="http://www.w3.org/2000/svg" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/><polyline points="15 3 21 3 21 9"/><line x1="10" y1="14" x2="21" y2="3"/></svg>
                    Open link
                  </a>
                  <button
                    v-if="!isApproved"
                    class="btn-danger btn-sm"
                    type="button"
                    :disabled="busy"
                    @click="detachEvidence(link.id)"
                  >
                    {{ busyAction === `detach-${link.id}` ? "Removing…" : "Remove" }}
                  </button>
                </div>

                <!-- Review panel -->
                <div v-if="canReview && !isApproved" class="review-panel">
                  <label class="field">
                    <span class="field-label">Reviewer note</span>
                    <textarea v-model.trim="reviewNotes[link.id]" rows="2" placeholder="Explain your decision (optional)" />
                  </label>
                  <div class="review-actions">
                    <button class="btn-accept" type="button" :disabled="busy" @click="reviewLink(link.id, 'accepted')">
                      <svg xmlns="http://www.w3.org/2000/svg" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg>
                      Accept
                    </button>
                    <button class="btn-ghost btn-sm" type="button" :disabled="busy" @click="reviewLink(link.id, 'needs_update')">Request update</button>
                    <button class="btn-ghost btn-sm" type="button" :disabled="busy" @click="reviewLink(link.id, 'rejected')">Reject</button>
                    <button class="btn-ghost btn-sm" type="button" :disabled="busy" @click="reviewLink(link.id, 'waived')">Waive</button>
                  </div>
                </div>
              </article>
            </div>
          </div>

          <!-- ── History tab ── -->
          <div v-if="detailTabsActive === 'history'" class="history-section">
            <div v-if="revisionHistoryLoading" class="loading-panel">
              <div class="spinner-small"></div>
              <p>Loading revision history…</p>
            </div>
            <div v-else-if="!revisionHistory" class="empty-panel">
              No artifact linked to this item yet.
            </div>
            <div v-else class="revision-panel">
              <p class="revision-title">{{ revisionHistory.title }}</p>
              <p class="revision-meta">{{ revisionHistory.artifact_type }} · {{ revisionHistory.revisions?.length ?? 0 }} revision{{ (revisionHistory.revisions?.length ?? 0) !== 1 ? 's' : '' }}</p>
              <div v-if="!revisionHistory.revisions || revisionHistory.revisions.length === 0" class="empty-panel">
                No revisions available.
              </div>
              <div v-else class="revisions-list">
                <article v-for="rev in revisionHistory.revisions" :key="rev.id" class="revision-card">
                  <div class="revision-header">
                    <span class="revision-number">Rev {{ rev.revision_number }}</span>
                    <span class="revision-date">{{ formatDateTime(rev.created_at) }}</span>
                  </div>
                  <p v-if="rev.change_summary" class="revision-summary">{{ rev.change_summary }}</p>
                  <p class="revision-uploader">Uploaded by {{ formatUser(rev.uploaded_by_user) }}</p>
                  <div class="revision-meta-row">
                    <span>{{ formatLabel(rev.source_type) }}</span>
                    <span v-if="rev.file_size_bytes">{{ formatSize(rev.file_size_bytes) }}</span>
                    <span v-if="rev.sha256" class="sha-label">{{ rev.sha256.slice(0, 12) }}…</span>
                  </div>
                </article>
              </div>
            </div>
          </div>

          <!-- ── SBOM Diff tab ── -->
          <div v-if="detailTabsActive === 'diff'" class="diff-section">
            <div v-if="sbomDiffData === null && !revisionHistoryLoading" class="empty-panel">
              No SBOM found for this item. Ensure an SBOM file is attached above.
            </div>
            <SbomDiffPanel v-else :diff="sbomDiffData" :loading="revisionHistoryLoading" />
          </div>

          <!-- ── Dependencies tab ── -->
          <div v-if="detailTabsActive === 'dependencies'" class="dependencies-section">
            <p class="section-hint">Define prerequisite relationships between checklist items.</p>
            <div class="dependencies-graph">
              <div v-for="item in releaseDetail.gate.items" :key="item.id" class="dep-node">
                <div class="node-card" :class="`node-${item.status}`">
                  <strong class="node-title">{{ item.title }}</strong>
                  <span class="node-status">{{ formatLabel(item.status) }}</span>
                </div>
                <div v-if="item.prerequisites && item.prerequisites.length > 0" class="node-prereqs">
                  <p class="prereq-label">Requires:</p>
                  <div v-for="prereq in item.prerequisites" :key="prereq.id" class="prereq-item">
                    {{ prereq.title }}
                  </div>
                </div>
              </div>
            </div>
            <div v-if="canEdit && !isApproved" class="dependencies-editor">
              <p class="editor-label">Add prerequisite</p>
              <p class="editor-hint">Mark {{ selectedItem.title }} as requiring another item to be completed first.</p>
              <button class="btn-secondary btn-sm" type="button" @click="showDependenciesEditor = !showDependenciesEditor">
                {{ showDependenciesEditor ? "Cancel" : "Add prerequisite" }}
              </button>
            </div>
          </div>

          <!-- ── Snapshot tab ── -->
          <div v-if="detailTabsActive === 'snapshot' && isApproved && releaseDetail.gate.snapshot_json" class="snapshot-section">
            <div class="snapshot-info">
              <p class="snapshot-label">Approved at</p>
              <p class="snapshot-value">{{ formatDateTime(releaseDetail.gate.approved_at) }}</p>
              <p class="snapshot-label">Approved by</p>
              <p class="snapshot-value">{{ formatUser(releaseDetail.gate.approved_by_user) }}</p>
              <p class="snapshot-label">Bundle SHA-256</p>
              <p class="snapshot-hash">{{ releaseDetail.gate.bundle_sha256?.slice(0, 20) }}…</p>
            </div>
            <details class="snapshot-json-view">
              <summary>View snapshot JSON</summary>
              <pre class="snapshot-json"><code>{{ JSON.stringify(releaseDetail.gate.snapshot_json, null, 2) }}</code></pre>
            </details>
          </div>

        </section>
      </div>
    </template>

    <!-- ── Remove checklist item confirmation modal ── -->
    <div v-if="removeConfirm.item" class="modal-backdrop" @click.self="removeConfirm.item = null">
      <div class="modal-box" role="dialog" aria-modal="true">
        <div class="modal-header">
          <h3 class="modal-title">Remove checklist item?</h3>
          <button class="btn-ghost btn-sm" type="button" @click="removeConfirm.item = null">
            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
          </button>
        </div>
        <p class="modal-body">
          You are about to remove <strong>{{ removeConfirm.item?.title }}</strong> from the checklist.
          <template v-if="removeConfirm.hasEvidence">
            This item has <strong>{{ removeConfirm.evidenceCount }} attached artifact{{ removeConfirm.evidenceCount !== 1 ? 's' : '' }}</strong> which will also be permanently deleted.
          </template>
          This cannot be undone.
        </p>
        <div class="modal-actions">
          <button class="btn-danger" type="button" :disabled="busy" @click="removeChecklistItem">
            {{ busyAction === "remove-item" ? "Removing…" : "Yes, remove item" }}
          </button>
          <button class="btn-ghost btn-sm" type="button" @click="removeConfirm.item = null">Cancel</button>
        </div>
      </div>
    </div>

  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from "vue";
import { useRoute } from "vue-router";

import DropZone from "@/components/DropZone.vue";
import SbomDiffPanel from "@/components/SbomDiffPanel.vue";
import { artifactService } from "@/services/artifact-service";
import { releaseGateService } from "@/services/release-gate-service";
import { sbomRecordService } from "@/services/sbom-record-service";
import { useAuthStore } from "@/stores/auth";
import { extractDiffData, formatComponent } from "@/utils/sbomDiff";
import type { ArtifactRead, ArtifactListRead, ArtifactType } from "@/types/artifact";
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
const showAddItemForm = ref(false);
const addItemForm = reactive({ title: "", description: "" });
const removeConfirm = reactive<{
  item: ReleaseGateItemRead | null;
  hasEvidence: boolean;
  evidenceCount: number;
}>({ item: null, hasEvidence: false, evidenceCount: 0 });

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

// Detail panel tabs and state
const detailTabsActive = ref<"evidence" | "history" | "diff" | "dependencies" | "snapshot">("evidence");
const revisionHistory = ref<ArtifactRead | null>(null);
const revisionHistoryLoading = ref(false);
const sbomDiffData = ref<ReturnType<typeof extractDiffData> | null>(null);
const showDependenciesEditor = ref(false);

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
const isApproved = computed(() => releaseDetail.value?.gate.status === "approved");
const canReview = computed(() => authStore.hasPermission("release_lifecycle_write"));
const canApprove = computed(() => canReview.value && !isApproved.value);
const canEdit = computed(() => authStore.hasPermission("release_write"));
const canDownload = computed(() => authStore.hasPermission("release_lifecycle_write"));
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

function onFilesSelected(files: File[]): void {
  selectedFile.value = files[0] ?? null;
  if (!selectedFile.value) {
    return;
  }

  if (!uploadForm.title.trim()) {
    uploadForm.title = selectedFile.value.name.replace(/\.[^/.]+$/, "");
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

async function detachEvidence(linkId: string): Promise<void> {
  if (!releaseDetail.value) return;
  busy.value = true;
  busyAction.value = `detach-${linkId}`;
  errorMessage.value = "";
  successMessage.value = "";
  try {
    const detail = await releaseGateService.detachEvidence(linkId);
    setWorkspace(detail);
    successMessage.value = "Evidence removed from this gate item.";
  } catch (error: any) {
    errorMessage.value = error?.message ?? "Failed to remove evidence.";
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

async function addChecklistItem(): Promise<void> {
  if (!releaseDetail.value || !addItemForm.title.trim()) return;
  busy.value = true;
  busyAction.value = "add-item";
  errorMessage.value = "";
  successMessage.value = "";
  try {
    const detail = await releaseGateService.addChecklistItem(
      releaseDetail.value.release.id,
      addItemForm.title,
      addItemForm.description || undefined,
    );
    setWorkspace(detail);
    successMessage.value = `"${addItemForm.title}" added to the checklist.`;
    addItemForm.title = "";
    addItemForm.description = "";
    showAddItemForm.value = false;
  } catch (error: any) {
    errorMessage.value = error?.message ?? "Failed to add checklist item.";
  } finally {
    busy.value = false;
    busyAction.value = "";
  }
}

function confirmRemoveItem(item: ReleaseGateItemRead): void {
  removeConfirm.item = item;
  removeConfirm.evidenceCount = item.evidence_links.length;
  removeConfirm.hasEvidence = item.evidence_links.length > 0;
}

async function removeChecklistItem(): Promise<void> {
  if (!releaseDetail.value || !removeConfirm.item) return;
  busy.value = true;
  busyAction.value = "remove-item";
  errorMessage.value = "";
  successMessage.value = "";
  const itemTitle = removeConfirm.item.title;
  try {
    const detail = await releaseGateService.removeChecklistItem(
      releaseDetail.value.release.id,
      removeConfirm.item.id,
    );
    setWorkspace(detail);
    successMessage.value = `"${itemTitle}" removed from the checklist.`;
    removeConfirm.item = null;
  } catch (error: any) {
    errorMessage.value = error?.message ?? "Failed to remove checklist item.";
  } finally {
    busy.value = false;
    busyAction.value = "";
  }
}

async function downloadBundle(): Promise<void> {
  if (!releaseDetail.value) return;
  busy.value = true;
  busyAction.value = "download";
  errorMessage.value = "";
  successMessage.value = "";
  try {
    await releaseGateService.downloadBundle(releaseDetail.value.release.id);
  } catch (error: any) {
    errorMessage.value = error?.message ?? "Failed to download documentation bundle.";
  } finally {
    busy.value = false;
    busyAction.value = "";
  }
}

function copyHash(hash: string): void {
  navigator.clipboard.writeText(hash).catch(() => {
    // Clipboard API not available — silently ignore.
  });
}

function formatLabel(value: string): string {
  return value
    .replaceAll("_", " ")
    .replace(/\b\w/g, (character) => character.toUpperCase());
}

function formatDate(value: string | null): string {
  if (!value) return "—";
  return new Intl.DateTimeFormat("en", { dateStyle: "medium" }).format(new Date(value));
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

async function loadRevisionHistory(): Promise<void> {
  detailTabsActive.value = "history";
  if (!selectedItem.value || !selectedItem.value.evidence_links.length) {
    revisionHistory.value = null;
    return;
  }

  revisionHistoryLoading.value = true;
  try {
    const artifact = selectedItem.value.evidence_links[0]?.artifact_revision;
    if (artifact?.artifact_id) {
      const history = await artifactService.getById(artifact.artifact_id);
      revisionHistory.value = history;
    }
  } catch (error: any) {
    errorMessage.value = error?.message ?? "Failed to load revision history.";
    revisionHistory.value = null;
  } finally {
    revisionHistoryLoading.value = false;
  }
}

async function loadSbomDiff(): Promise<void> {
  detailTabsActive.value = "diff";
  if (!releaseDetail.value || selectedItem.value?.code !== "sbom") {
    sbomDiffData.value = null;
    return;
  }

  revisionHistoryLoading.value = true;
  try {
    const sbomRecords = await sbomRecordService.list({ productReleaseId: releaseDetail.value.release.id });
    const latestSbom = sbomRecords[0];
    if (latestSbom?.analysis_findings) {
      sbomDiffData.value = extractDiffData(latestSbom.analysis_findings);
    } else {
      sbomDiffData.value = null;
    }
  } catch (error: any) {
    errorMessage.value = error?.message ?? "Failed to load SBOM diff.";
    sbomDiffData.value = null;
  } finally {
    revisionHistoryLoading.value = false;
  }
}

onMounted(() => {
  if (route.params.releaseId) {
    loadWorkspace();
  }
});
</script>

<style scoped>
/* ─────────────────────────────────────────
   Page shell
───────────────────────────────────────── */
.release-page {
  display: grid;
  gap: 1.25rem;
}

/* ─────────────────────────────────────────
   Shared typography helpers
───────────────────────────────────────── */
.eyebrow {
  margin: 0 0 0.3rem;
  text-transform: uppercase;
  letter-spacing: 0.12em;
  font-size: 0.72rem;
  font-weight: 600;
  color: var(--color-primary, #6ea8fe);
}

.detail-copy,
.muted {
  margin: 0;
  color: var(--color-text-muted, rgba(233, 238, 252, 0.65));
  font-size: 0.9rem;
  line-height: 1.55;
}

/* ─────────────────────────────────────────
   Feedback / toast banners
───────────────────────────────────────── */
.feedback {
  padding: 0.8rem 1rem;
  border-radius: 0.85rem;
  background: rgba(255, 255, 255, 0.04);
  border: 1px dashed rgba(233, 238, 252, 0.18);
  color: var(--color-text-muted, rgba(233, 238, 252, 0.7));
  font-size: 0.9rem;
}

.feedback-error {
  background: rgba(251, 113, 133, 0.1);
  border: 1px solid rgba(251, 113, 133, 0.3);
  color: #fda4af;
}

.feedback-success {
  background: rgba(52, 211, 153, 0.08);
  border: 1px solid rgba(52, 211, 153, 0.25);
  color: #86efac;
}

/* ─────────────────────────────────────────
   Unified button system
───────────────────────────────────────── */
.btn-primary,
.btn-secondary,
.btn-ghost,
.btn-danger,
.btn-accept {
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
  border: 1px solid transparent;
  border-radius: 10px;
  padding: 0.6rem 1.05rem;
  font: inherit;
  font-size: 0.9rem;
  font-weight: 600;
  cursor: pointer;
  text-decoration: none;
  transition: transform 0.13s ease, opacity 0.13s ease, border-color 0.13s ease, background 0.13s ease;
}

.btn-primary:hover,
.btn-secondary:hover,
.btn-ghost:hover,
.btn-danger:hover,
.btn-accept:hover {
  transform: translateY(-1px);
}

.btn-primary:disabled,
.btn-secondary:disabled,
.btn-ghost:disabled,
.btn-danger:disabled,
.btn-accept:disabled {
  opacity: 0.55;
  cursor: not-allowed;
  transform: none;
}

.btn-primary {
  background: linear-gradient(135deg, #6ea8fe, #8b5cf6);
  color: #fff;
  border-color: transparent;
  box-shadow: 0 2px 8px rgba(110, 168, 254, 0.25);
}

.btn-secondary {
  background: rgba(110, 168, 254, 0.12);
  color: #93c5fd;
  border-color: rgba(110, 168, 254, 0.3);
}

.btn-secondary:hover {
  background: rgba(110, 168, 254, 0.2);
}

.btn-ghost {
  background: transparent;
  color: var(--color-text-muted, rgba(233, 238, 252, 0.7));
  border-color: rgba(233, 238, 252, 0.16);
}

.btn-ghost:hover {
  background: rgba(255, 255, 255, 0.05);
  color: var(--color-text, #e9eefc);
}

.btn-danger {
  background: rgba(251, 113, 133, 0.1);
  color: #fda4af;
  border-color: rgba(251, 113, 133, 0.28);
}

.btn-danger:hover {
  background: rgba(251, 113, 133, 0.2);
  border-color: rgba(251, 113, 133, 0.45);
}

.btn-accept {
  background: rgba(52, 211, 153, 0.12);
  color: #6ee7b7;
  border-color: rgba(52, 211, 153, 0.3);
}

.btn-accept:hover {
  background: rgba(52, 211, 153, 0.22);
}

.btn-sm {
  padding: 0.38rem 0.75rem;
  font-size: 0.82rem;
  border-radius: 8px;
}

/* ─────────────────────────────────────────
   Status / decision pills
───────────────────────────────────────── */
.status-pill,
.mini-pill {
  display: inline-flex;
  align-items: center;
  padding: 0.28rem 0.7rem;
  border-radius: 999px;
  font-weight: 700;
  font-size: 0.78rem;
  letter-spacing: 0.02em;
  white-space: nowrap;
}

.status-draft,
.decision-pending_review {
  background: rgba(251, 191, 36, 0.14);
  color: #fde68a;
}

.status-in_review {
  background: rgba(110, 168, 254, 0.14);
  color: #bfdbfe;
}

.decision-waived {
  background: rgba(148, 163, 184, 0.14);
  color: #cbd5e1;
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

/* ─────────────────────────────────────────
   Meta chips (hero + library)
───────────────────────────────────────── */
.meta-chip {
  display: inline-flex;
  align-items: center;
  padding: 0.3rem 0.75rem;
  border-radius: 999px;
  font-size: 0.8rem;
  font-weight: 600;
  border: 1px solid transparent;
}

.chip-neutral {
  background: rgba(255, 255, 255, 0.07);
  border-color: rgba(255, 255, 255, 0.1);
  color: rgba(233, 238, 252, 0.75);
}

.chip-draft       { background: rgba(251,191,36,0.14); color: #fde68a; }
.chip-in_review   { background: rgba(110,168,254,0.14); color: #bfdbfe; }
.chip-approved    { background: rgba(52,211,153,0.14); color: #86efac; }
.chip-blocked     { background: rgba(251,113,133,0.14); color: #fda4af; }

/* ─────────────────────────────────────────
   Hero card
───────────────────────────────────────── */
.hero {
  display: flex;
  justify-content: space-between;
  gap: 1rem;
  align-items: flex-start;
  background:
    radial-gradient(circle at top right, rgba(110, 168, 254, 0.18), transparent 42%),
    linear-gradient(135deg, rgba(139, 92, 246, 0.16), rgba(15, 26, 46, 0.72) 55%);
}

.hero-body {
  display: flex;
  flex-direction: column;
  gap: 0.65rem;
}

.hero-title {
  margin: 0;
  font-size: 1.55rem;
  font-weight: 700;
  color: var(--color-text, #e9eefc);
  line-height: 1.25;
}

.hero-meta-row {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
}

.hero-actions {
  display: flex;
  align-items: center;
  gap: 0.6rem;
  flex-shrink: 0;
  flex-wrap: wrap;
}

/* ─────────────────────────────────────────
   Progress card
───────────────────────────────────────── */
.progress-card {
  display: grid;
  gap: 0.9rem;
}

.progress-top {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 1rem;
}

.progress-title-group {
  display: flex;
  flex-direction: column;
  gap: 0.15rem;
}

.progress-heading {
  margin: 0;
  font-size: 1rem;
  font-weight: 600;
  color: var(--color-text, #e9eefc);
}

.progress-bar-wrap {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.progress-track {
  flex: 1;
  height: 0.55rem;
  background: rgba(255, 255, 255, 0.08);
  border-radius: 999px;
  overflow: hidden;
}

.progress-fill {
  display: block;
  height: 100%;
  border-radius: 999px;
  background: linear-gradient(90deg, #8b5cf6, #6ea8fe);
  transition: width 0.4s ease;
}

.progress-pct {
  font-size: 0.85rem;
  font-weight: 700;
  color: #93c5fd;
  min-width: 2.5rem;
  text-align: right;
}

.progress-chips {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
}

.prog-chip {
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
  padding: 0.28rem 0.7rem;
  border-radius: 999px;
  font-size: 0.78rem;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.1);
  color: rgba(233, 238, 252, 0.65);
}

.prog-chip-green {
  background: rgba(52, 211, 153, 0.1);
  border-color: rgba(52, 211, 153, 0.25);
  color: #86efac;
}

/* ─────────────────────────────────────────
   Workspace 2-column grid
───────────────────────────────────────── */
.workspace-grid {
  display: grid;
  grid-template-columns: minmax(260px, 340px) minmax(0, 1fr);
  gap: 1.25rem;
  align-items: start;
}

/* ─────────────────────────────────────────
   Checklist (left column)
───────────────────────────────────────── */
.checklist-card {
  position: sticky;
  top: 1.25rem;
}

.checklist-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.75rem;
}

.item-count {
  font-size: 0.82rem;
  font-weight: 700;
  padding: 0.2rem 0.6rem;
  border-radius: 999px;
  background: rgba(110, 168, 254, 0.14);
  color: #93c5fd;
}

.checklist {
  display: flex;
  flex-direction: column;
  gap: 0.45rem;
}

.gate-item {
  display: flex;
  align-items: center;
  gap: 0.7rem;
  width: 100%;
  padding: 0.65rem 0.8rem;
  border: 1px solid rgba(233, 238, 252, 0.1);
  border-radius: 10px;
  background: rgba(255, 255, 255, 0.02);
  text-align: left;
  cursor: pointer;
  transition: border-color 0.13s, background 0.13s;
}

.gate-item:hover {
  background: rgba(255, 255, 255, 0.05);
}

.gate-item--selected {
  border-color: rgba(110, 168, 254, 0.5);
  background: rgba(110, 168, 254, 0.07);
  box-shadow: 0 0 0 2px rgba(110, 168, 254, 0.12);
}

.gate-item--accepted {
  border-color: rgba(52, 211, 153, 0.3);
  background: rgba(52, 211, 153, 0.05);
}

.gate-item--blocked {
  border-color: rgba(251, 113, 133, 0.3);
  background: rgba(251, 113, 133, 0.05);
}

.gate-item--waived {
  border-color: rgba(148, 163, 184, 0.2);
  background: rgba(148, 163, 184, 0.04);
}

.gate-item-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 1.6rem;
  height: 1.6rem;
  border-radius: 50%;
  flex-shrink: 0;
  background: rgba(255, 255, 255, 0.05);
  color: rgba(233, 238, 252, 0.5);
}

.gate-item--accepted .gate-item-icon  { background: rgba(52,211,153,0.15);  color: #6ee7b7; }
.gate-item--blocked  .gate-item-icon  { background: rgba(251,113,133,0.15); color: #fda4af; }
.gate-item--waived   .gate-item-icon  { background: rgba(148,163,184,0.12); color: #94a3b8; }

.gate-item-body {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 0.1rem;
}

.gate-item-title {
  font-size: 0.88rem;
  font-weight: 600;
  color: var(--color-text, #e9eefc);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.gate-item-count {
  font-size: 0.76rem;
  color: rgba(233, 238, 252, 0.5);
}

/* ─────────────────────────────────────────
   Detail panel (right column)
───────────────────────────────────────── */
.detail-card {
  display: flex;
  flex-direction: column;
  gap: 1.25rem;
}

.detail-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 1rem;
}

.detail-header-left {
  display: flex;
  flex-direction: column;
  gap: 0.3rem;
}

.detail-title {
  margin: 0;
  font-size: 1.15rem;
  font-weight: 700;
  color: var(--color-text, #e9eefc);
}

/* ─────────────────────────────────────────
   Frozen banner
───────────────────────────────────────── */
.frozen-banner {
  display: flex;
  align-items: flex-start;
  gap: 0.85rem;
  padding: 0.9rem 1.05rem;
  border-radius: 12px;
  border: 1px solid rgba(52, 211, 153, 0.28);
  background: rgba(52, 211, 153, 0.06);
}

.frozen-banner-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 2rem;
  height: 2rem;
  border-radius: 50%;
  flex-shrink: 0;
  background: rgba(52, 211, 153, 0.15);
  color: #86efac;
}

.frozen-banner-title {
  margin: 0 0 0.2rem;
  font-size: 0.9rem;
  font-weight: 700;
  color: #86efac;
}

.frozen-banner-copy {
  margin: 0;
  font-size: 0.84rem;
  color: rgba(134, 239, 172, 0.75);
  line-height: 1.5;
}

/* ─────────────────────────────────────────
   Add evidence zone
───────────────────────────────────────── */
.add-evidence-zone {
  display: flex;
  flex-direction: column;
  gap: 0;
  border: 1px solid rgba(233, 238, 252, 0.1);
  border-radius: 12px;
  overflow: hidden;
}

.add-evidence-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  padding: 0.7rem 1rem;
  background: rgba(255, 255, 255, 0.03);
  border-bottom: 1px solid rgba(233, 238, 252, 0.08);
}

.add-evidence-label {
  font-size: 0.8rem;
  font-weight: 600;
  color: rgba(233, 238, 252, 0.55);
  text-transform: uppercase;
  letter-spacing: 0.08em;
}

/* Tab bar */
.add-tabs {
  display: flex;
  gap: 0.25rem;
}

.add-tab {
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
  padding: 0.35rem 0.75rem;
  border: 1px solid transparent;
  border-radius: 8px;
  background: transparent;
  color: rgba(233, 238, 252, 0.5);
  font: inherit;
  font-size: 0.82rem;
  font-weight: 500;
  cursor: pointer;
  transition: background 0.12s, color 0.12s, border-color 0.12s;
}

.add-tab:hover {
  background: rgba(255, 255, 255, 0.06);
  color: rgba(233, 238, 252, 0.8);
}

.add-tab--active {
  background: rgba(110, 168, 254, 0.14);
  border-color: rgba(110, 168, 254, 0.3);
  color: #93c5fd;
}

/* ─────────────────────────────────────────
   Evidence forms
───────────────────────────────────────── */
.evidence-form {
  padding: 1rem;
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.form-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 0.75rem;
}

.field {
  display: flex;
  flex-direction: column;
  gap: 0.3rem;
}

.field-full {
  grid-column: 1 / -1;
}

.field-label {
  font-size: 0.8rem;
  font-weight: 600;
  color: rgba(233, 238, 252, 0.6);
}

.field-optional {
  font-weight: 400;
  opacity: 0.7;
}

.field input,
.field select,
.field textarea {
  width: 100%;
  border: 1px solid rgba(233, 238, 252, 0.14);
  border-radius: 8px;
  padding: 0.6rem 0.85rem;
  background: rgba(255, 255, 255, 0.04);
  color: var(--color-text, #e9eefc);
  font: inherit;
  font-size: 0.9rem;
  resize: vertical;
  transition: border-color 0.12s;
}

.field input:focus,
.field select:focus,
.field textarea:focus {
  outline: none;
  border-color: rgba(110, 168, 254, 0.45);
}

.field input:disabled,
.field select:disabled {
  opacity: 0.55;
  cursor: not-allowed;
}

/* File drop zone */
.file-drop {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 5rem;
  border: 2px dashed rgba(233, 238, 252, 0.18);
  border-radius: 10px;
  cursor: pointer;
  transition: border-color 0.13s, background 0.13s;
  background: rgba(255, 255, 255, 0.02);
  position: relative;
}

.file-drop:hover {
  border-color: rgba(110, 168, 254, 0.4);
  background: rgba(110, 168, 254, 0.04);
}

.file-drop input[type="file"] {
  position: absolute;
  inset: 0;
  opacity: 0;
  cursor: pointer;
  width: 100%;
  height: 100%;
}

.file-drop-prompt {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.4rem;
  color: rgba(233, 238, 252, 0.45);
  font-size: 0.85rem;
  pointer-events: none;
}

.file-drop-selected {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  color: #93c5fd;
  font-size: 0.88rem;
  font-weight: 500;
  pointer-events: none;
}

.form-footer {
  display: flex;
  justify-content: flex-end;
  gap: 0.5rem;
}

/* ─────────────────────────────────────────
   Library panel
───────────────────────────────────────── */
.library-panel {
  padding: 1rem;
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.library-toolbar {
  display: flex;
  gap: 0.5rem;
  align-items: center;
}

.library-search {
  flex: 1;
  border: 1px solid rgba(233, 238, 252, 0.14);
  border-radius: 8px;
  padding: 0.5rem 0.85rem;
  background: rgba(255, 255, 255, 0.04);
  color: var(--color-text, #e9eefc);
  font: inherit;
  font-size: 0.88rem;
}

.library-search:focus {
  outline: none;
  border-color: rgba(110, 168, 254, 0.4);
}

.library-hint {
  margin: 0;
  font-size: 0.8rem;
  color: rgba(233, 238, 252, 0.4);
  font-style: italic;
}

.library-list {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  max-height: 22rem;
  overflow-y: auto;
}

.library-item {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 1rem;
  padding: 0.75rem;
  border: 1px solid rgba(233, 238, 252, 0.1);
  border-radius: 10px;
  background: rgba(255, 255, 255, 0.02);
}

.library-item-info {
  display: flex;
  flex-direction: column;
  gap: 0.2rem;
  min-width: 0;
}

.library-item-info strong {
  font-size: 0.9rem;
  color: var(--color-text, #e9eefc);
}

.library-meta {
  margin: 0;
  font-size: 0.78rem;
  color: rgba(233, 238, 252, 0.45);
}

/* ─────────────────────────────────────────
   Evidence snapshot section
───────────────────────────────────────── */
.evidence-section {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.evidence-section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.75rem;
}

.evidence-section-title {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  font-size: 0.88rem;
  font-weight: 600;
  color: rgba(233, 238, 252, 0.7);
}

.evidence-count {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 1.5rem;
  height: 1.5rem;
  padding: 0 0.45rem;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.07);
  font-size: 0.78rem;
  font-weight: 700;
  color: rgba(233, 238, 252, 0.6);
}

.empty-panel {
  padding: 1.25rem 1rem;
  border-radius: 10px;
  background: rgba(255, 255, 255, 0.025);
  border: 1px dashed rgba(233, 238, 252, 0.12);
  color: rgba(233, 238, 252, 0.45);
  font-size: 0.88rem;
  text-align: center;
}

.evidence-list {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

/* ─────────────────────────────────────────
   Evidence card
───────────────────────────────────────── */
.evidence-card {
  border: 1px solid rgba(233, 238, 252, 0.1);
  border-radius: 12px;
  padding: 0;
  overflow: hidden;
  background: rgba(255, 255, 255, 0.025);
  display: flex;
  flex-direction: column;
}

/* Decision tints */
.ev-accepted   { border-color: rgba(52,211,153,0.25);  background: rgba(52,211,153,0.04); }
.ev-rejected   { border-color: rgba(251,113,133,0.25); background: rgba(251,113,133,0.04); }
.ev-needs_update { border-color: rgba(251,191,36,0.25); background: rgba(251,191,36,0.04); }
.ev-waived     { border-color: rgba(148,163,184,0.2);  background: rgba(148,163,184,0.03); }
.ev-pending_review { border-color: rgba(233,238,252,0.1); }

/* Card top row */
.ev-top {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 0.75rem;
  padding: 0.85rem 1rem 0.6rem;
}

.ev-identity {
  display: flex;
  align-items: flex-start;
  gap: 0.65rem;
  min-width: 0;
}

.file-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 2.6rem;
  padding: 0.35rem 0.5rem;
  border-radius: 7px;
  background: rgba(110, 168, 254, 0.14);
  color: #93c5fd;
  font-size: 0.7rem;
  font-weight: 800;
  letter-spacing: 0.08em;
  flex-shrink: 0;
}

.ev-name-group {
  display: flex;
  flex-direction: column;
  gap: 0.15rem;
  min-width: 0;
}

.ev-name {
  font-size: 0.92rem;
  font-weight: 600;
  color: var(--color-text, #e9eefc);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.ev-meta {
  font-size: 0.78rem;
  color: rgba(233, 238, 252, 0.45);
}

/* Change note */
.ev-note {
  margin: 0;
  padding: 0 1rem 0.6rem;
  font-size: 0.85rem;
  color: rgba(233, 238, 252, 0.6);
  font-style: italic;
}

/* Activity trail */
.ev-activity {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  padding: 0.6rem 1rem;
  border-top: 1px solid rgba(233, 238, 252, 0.06);
  background: rgba(0, 0, 0, 0.12);
}

.ev-activity-item {
  display: flex;
  align-items: center;
  gap: 0.6rem;
}

.ev-avatar {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 1.8rem;
  height: 1.8rem;
  border-radius: 50%;
  flex-shrink: 0;
  background: rgba(110, 168, 254, 0.18);
  color: #bfdbfe;
  font-size: 0.7rem;
  font-weight: 800;
}

.ev-avatar--review {
  background: rgba(52, 211, 153, 0.16);
  color: #86efac;
}

.ev-activity-text {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 0.25rem 0.4rem;
  font-size: 0.8rem;
}

.ev-activity-action {
  color: rgba(233, 238, 252, 0.5);
}

.ev-activity-who {
  color: rgba(233, 238, 252, 0.8);
  font-weight: 500;
}

.ev-activity-when {
  color: rgba(233, 238, 252, 0.35);
  font-size: 0.76rem;
}

/* Rationale */
.ev-rationale {
  margin: 0;
  padding: 0.6rem 1rem;
  font-size: 0.83rem;
  color: rgba(233, 238, 252, 0.55);
  border-top: 1px solid rgba(233, 238, 252, 0.06);
  font-style: italic;
}

/* Card actions row */
.ev-actions {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  flex-wrap: wrap;
  padding: 0.55rem 1rem;
  border-top: 1px solid rgba(233, 238, 252, 0.06);
}

/* ─────────────────────────────────────────
   Review panel
───────────────────────────────────────── */
.review-panel {
  display: flex;
  flex-direction: column;
  gap: 0.65rem;
  padding: 0.85rem 1rem;
  border-top: 1px solid rgba(233, 238, 252, 0.08);
  background: rgba(0, 0, 0, 0.2);
}

.review-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 0.4rem;
  align-items: center;
}

/* ─────────────────────────────────────────
   Loading and empty states
───────────────────────────────────────── */
.loading-panel {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 0.75rem;
  padding: 2rem;
  color: var(--color-text-muted, rgba(233, 238, 252, 0.65));
  text-align: center;
}

.spinner-small {
  width: 1.5rem;
  height: 1.5rem;
  border: 2px solid rgba(110, 168, 254, 0.3);
  border-top-color: #6ea8fe;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

/* ─────────────────────────────────────────
   Detail tabs navigation
───────────────────────────────────────── */
.detail-tabs-nav {
  display: flex;
  gap: 0.25rem;
  border-bottom: 1px solid rgba(233, 238, 252, 0.08);
  margin-bottom: 1rem;
  flex-wrap: wrap;
}

.detail-tab {
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
  padding: 0.6rem 1rem;
  border: none;
  background: transparent;
  color: rgba(233, 238, 252, 0.55);
  font-size: 0.9rem;
  font-weight: 500;
  cursor: pointer;
  border-bottom: 2px solid transparent;
  transition: color 0.2s ease, border-color 0.2s ease;
}

.detail-tab:hover {
  color: rgba(233, 238, 252, 0.75);
}

.detail-tab--active {
  color: #6ea8fe;
  border-bottom-color: #6ea8fe;
}

/* ─────────────────────────────────────────
   History section
───────────────────────────────────────── */
.history-section {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.revision-title {
  margin: 0 0 0.25rem;
  font-size: 0.95rem;
  font-weight: 600;
  color: var(--color-text, #e9eefc);
}

.revision-meta {
  margin: 0 0 1rem;
  font-size: 0.85rem;
  color: rgba(233, 238, 252, 0.5);
}

.revisions-list {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.revision-card {
  padding: 0.75rem 1rem;
  border-radius: 0.5rem;
  background: rgba(255, 255, 255, 0.02);
  border: 1px solid rgba(233, 238, 252, 0.08);
  transition: background 0.2s ease;
}

.revision-card:hover {
  background: rgba(255, 255, 255, 0.04);
}

.revision-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.4rem;
}

.revision-number {
  font-size: 0.85rem;
  font-weight: 600;
  color: #93c5fd;
}

.revision-date {
  font-size: 0.8rem;
  color: rgba(233, 238, 252, 0.4);
}

.revision-summary {
  margin: 0.4rem 0;
  font-size: 0.85rem;
  color: rgba(233, 238, 252, 0.7);
}

.revision-uploader {
  margin: 0.25rem 0;
  font-size: 0.8rem;
  color: rgba(233, 238, 252, 0.5);
}

.revision-meta-row {
  display: flex;
  gap: 1rem;
  margin-top: 0.5rem;
  font-size: 0.75rem;
  color: rgba(233, 238, 252, 0.35);
}

.sha-label {
  font-family: monospace;
  letter-spacing: -0.02em;
}

/* ─────────────────────────────────────────
   SBOM Diff section
───────────────────────────────────────── */
.diff-section {
  display: flex;
  flex-direction: column;
}

/* ─────────────────────────────────────────
   Dependencies section
───────────────────────────────────────── */
.dependencies-section {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.section-hint {
  margin: 0;
  font-size: 0.85rem;
  color: rgba(233, 238, 252, 0.5);
  font-style: italic;
}

.dependencies-graph {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1rem;
}

.dep-node {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.node-card {
  padding: 1rem;
  border-radius: 0.65rem;
  border: 2px solid rgba(233, 238, 252, 0.1);
  background: rgba(255, 255, 255, 0.02);
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 0.5rem;
}

.node-card.node-accepted {
  border-color: rgba(52, 211, 153, 0.3);
  background: rgba(52, 211, 153, 0.08);
}

.node-card.node-pending_review {
  border-color: rgba(245, 158, 11, 0.3);
  background: rgba(245, 158, 11, 0.08);
}

.node-card.node-rejected,
.node-card.node-needs_update {
  border-color: rgba(239, 68, 68, 0.3);
  background: rgba(239, 68, 68, 0.08);
}

.node-title {
  font-size: 0.9rem;
  color: var(--color-text, #e9eefc);
}

.node-status {
  font-size: 0.7rem;
  padding: 0.2rem 0.5rem;
  border-radius: 0.3rem;
  background: rgba(110, 168, 254, 0.15);
  color: #93c5fd;
  font-weight: 600;
  white-space: nowrap;
}

.node-prereqs {
  padding: 0.5rem 0.75rem;
  border-radius: 0.5rem;
  background: rgba(0, 0, 0, 0.15);
  border-left: 3px solid rgba(110, 168, 254, 0.4);
}

.prereq-label {
  margin: 0 0 0.25rem;
  font-size: 0.75rem;
  color: rgba(233, 238, 252, 0.4);
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.prereq-item {
  margin: 0.15rem 0;
  font-size: 0.8rem;
  color: rgba(233, 238, 252, 0.6);
  padding-left: 0.5rem;
}

.dependencies-editor {
  padding: 1rem;
  border-radius: 0.65rem;
  background: rgba(110, 168, 254, 0.08);
  border: 1px solid rgba(110, 168, 254, 0.2);
}

.editor-label {
  margin: 0 0 0.25rem;
  font-size: 0.9rem;
  font-weight: 600;
  color: var(--color-text, #e9eefc);
}

.editor-hint {
  margin: 0 0 0.75rem;
  font-size: 0.8rem;
  color: rgba(233, 238, 252, 0.5);
}

/* ─────────────────────────────────────────
   Snapshot section
───────────────────────────────────────── */
.snapshot-section {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.snapshot-info {
  padding: 1rem;
  border-radius: 0.65rem;
  background: rgba(52, 211, 153, 0.08);
  border: 1px solid rgba(52, 211, 153, 0.2);
  display: grid;
  grid-template-columns: auto 1fr;
  gap: 0.5rem 1rem;
}

.snapshot-label {
  margin: 0;
  font-size: 0.8rem;
  color: rgba(233, 238, 252, 0.5);
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.snapshot-value {
  margin: 0;
  font-size: 0.9rem;
  color: rgba(233, 238, 252, 0.8);
}

.snapshot-hash {
  margin: 0;
  font-size: 0.85rem;
  color: #86efac;
  font-family: monospace;
  letter-spacing: -0.02em;
}

.snapshot-json-view {
  border: 1px solid rgba(233, 238, 252, 0.1);
  border-radius: 0.65rem;
  padding: 1rem;
  cursor: pointer;
}

.snapshot-json-view > summary {
  color: #6ea8fe;
  font-weight: 600;
  user-select: none;
}

.snapshot-json-view > summary:hover {
  text-decoration: underline;
}

.snapshot-json {
  margin: 1rem 0 0;
  padding: 0.75rem;
  background: rgba(0, 0, 0, 0.3);
  border-radius: 0.4rem;
  overflow-x: auto;
  font-size: 0.75rem;
  color: rgba(233, 238, 252, 0.7);
  line-height: 1.4;
}

.snapshot-json code {
  font-family: monospace;
}

/* ─────────────────────────────────────────
   Responsive
───────────────────────────────────────── */
@media (max-width: 1100px) {
  .workspace-grid {
    grid-template-columns: 1fr;
  }

  .checklist-card {
    position: static;
  }
}

@media (max-width: 720px) {
  .hero {
    flex-direction: column;
  }

  .hero-actions {
    width: 100%;
    justify-content: flex-end;
  }

  .form-grid {
    grid-template-columns: 1fr;
  }

  .add-evidence-header {
    flex-direction: column;
    align-items: flex-start;
  }
}

/* ── Checklist head right-side controls ── */
.checklist-head-right {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

/* ── Gate item row (wraps button + delete) ── */
.gate-item-row {
  display: flex;
  align-items: stretch;
  gap: 0.25rem;
}

.gate-item-row .gate-item {
  flex: 1 1 0;
  min-width: 0;
}

.gate-item-delete {
  flex: 0 0 auto;
  display: flex;
  align-items: center;
  padding: 0 0.4rem;
  border-radius: var(--radius-md, 0.5rem);
  border: 1px solid transparent;
  background: transparent;
  color: var(--color-text-muted);
  cursor: pointer;
  transition: background 0.15s, color 0.15s;
}

.gate-item-delete:hover {
  background: rgba(239, 68, 68, 0.1);
  color: #f87171;
}

/* ── Add checklist item form ── */
.add-item-form {
  display: grid;
  gap: 0.6rem;
  padding: 0.75rem;
  background: var(--color-surface-soft, rgba(255,255,255,0.04));
  border: 1px dashed var(--color-border);
  border-radius: var(--radius-md, 0.5rem);
  margin-bottom: 0.75rem;
}

.add-item-actions {
  display: flex;
  gap: 0.5rem;
  align-items: center;
}

/* ── Bundle hash in frozen banner ── */
.frozen-banner-hash {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  margin: 0.4rem 0 0;
  font-size: 0.82rem;
  flex-wrap: wrap;
}

.hash-label {
  color: var(--color-text-muted);
  font-weight: 600;
}

.hash-value {
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
  background: var(--color-surface-soft, rgba(255,255,255,0.06));
  border: 1px solid var(--color-border);
  border-radius: 4px;
  padding: 0.1rem 0.4rem;
  font-size: 0.8rem;
}

.btn-copy {
  display: inline-flex;
  align-items: center;
  gap: 0.25rem;
  padding: 0.15rem 0.45rem;
  border-radius: 4px;
  border: 1px solid var(--color-border);
  background: transparent;
  color: var(--color-text-muted);
  font-size: 0.78rem;
  cursor: pointer;
  transition: background 0.15s;
}

.btn-copy:hover {
  background: var(--color-surface-soft);
}

/* ── Confirmation modal ── */
.modal-backdrop {
  position: fixed;
  inset: 0;
  background: var(--color-modal-backdrop, rgba(5, 10, 20, 0.72));
  z-index: 100;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 1rem;
}

.modal-box {
  background: var(--color-modal-bg, #0c1524);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg, 1rem);
  padding: 1.5rem;
  max-width: 28rem;
  width: 100%;
  display: grid;
  gap: 1rem;
  box-shadow: var(--shadow-lg);
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.modal-title {
  margin: 0;
  font-size: 1.05rem;
  font-weight: 700;
}

.modal-body {
  margin: 0;
  line-height: 1.6;
  color: var(--color-text);
}

.modal-actions {
  display: flex;
  gap: 0.6rem;
  align-items: center;
}
</style>

<style>
:root[data-theme="light"] .feedback {
  background: rgba(28, 107, 39, 0.04);
  border-color: rgba(28, 107, 39, 0.15);
  color: var(--color-text-muted);
}
:root[data-theme="light"] .feedback-error {
  background: rgba(239, 68, 68, 0.08);
  border-color: rgba(239, 68, 68, 0.28);
  color: #be123c;
}
:root[data-theme="light"] .feedback-success {
  background: rgba(21, 128, 61, 0.08);
  border-color: rgba(21, 128, 61, 0.25);
  color: #15803d;
}
:root[data-theme="light"] .btn-primary {
  background: linear-gradient(135deg, #2563eb, #7c3aed);
  box-shadow: 0 2px 8px rgba(37, 99, 235, 0.25);
}
:root[data-theme="light"] .btn-secondary {
  background: rgba(37, 99, 235, 0.1);
  color: #1d4ed8;
  border-color: rgba(37, 99, 235, 0.28);
}
:root[data-theme="light"] .btn-secondary:hover {
  background: rgba(37, 99, 235, 0.16);
}
:root[data-theme="light"] .btn-ghost {
  color: var(--color-text-muted);
  border-color: rgba(28, 107, 39, 0.18);
}
:root[data-theme="light"] .btn-ghost:hover {
  background: rgba(28, 107, 39, 0.06);
  color: var(--color-text);
}
:root[data-theme="light"] .btn-danger {
  background: rgba(239, 68, 68, 0.08);
  color: #be123c;
  border-color: rgba(239, 68, 68, 0.28);
}
:root[data-theme="light"] .btn-danger:hover {
  background: rgba(239, 68, 68, 0.14);
  border-color: rgba(239, 68, 68, 0.4);
}
:root[data-theme="light"] .btn-accept {
  background: rgba(21, 128, 61, 0.1);
  color: #15803d;
  border-color: rgba(21, 128, 61, 0.28);
}
:root[data-theme="light"] .btn-accept:hover {
  background: rgba(21, 128, 61, 0.16);
}
:root[data-theme="light"] .status-draft,
:root[data-theme="light"] .decision-pending_review {
  background: rgba(184, 155, 18, 0.1);
  color: #78350f;
}
:root[data-theme="light"] .status-in_review {
  background: rgba(37, 99, 235, 0.1);
  color: #1d4ed8;
}
:root[data-theme="light"] .decision-waived {
  background: rgba(71, 85, 105, 0.1);
  color: #475569;
}
:root[data-theme="light"] .status-approved,
:root[data-theme="light"] .decision-accepted {
  background: rgba(21, 128, 61, 0.1);
  color: #15803d;
}
:root[data-theme="light"] .status-blocked,
:root[data-theme="light"] .decision-rejected,
:root[data-theme="light"] .decision-needs_update {
  background: rgba(239, 68, 68, 0.1);
  color: #be123c;
}
:root[data-theme="light"] .chip-neutral {
  background: rgba(28, 107, 39, 0.06);
  border-color: rgba(28, 107, 39, 0.14);
  color: var(--color-text-muted);
}
:root[data-theme="light"] .chip-draft       { background: rgba(184,155,18,0.1);   color: #78350f; }
:root[data-theme="light"] .chip-in_review   { background: rgba(37,99,235,0.1);    color: #1d4ed8; }
:root[data-theme="light"] .chip-approved    { background: rgba(21,128,61,0.1);    color: #15803d; }
:root[data-theme="light"] .chip-blocked     { background: rgba(239,68,68,0.1);    color: #be123c; }
:root[data-theme="light"] .hero {
  background:
    radial-gradient(circle at top right, rgba(37, 99, 235, 0.1), transparent 42%),
    linear-gradient(135deg, rgba(124, 58, 237, 0.08), rgba(238, 244, 232, 0.8) 55%);
}
:root[data-theme="light"] .progress-track {
  background: rgba(20, 33, 15, 0.08);
}
:root[data-theme="light"] .progress-fill {
  background: linear-gradient(90deg, #7c3aed, #2563eb);
}
:root[data-theme="light"] .progress-pct {
  color: #1d4ed8;
}
:root[data-theme="light"] .prog-chip {
  background: rgba(28, 107, 39, 0.06);
  border-color: rgba(28, 107, 39, 0.14);
  color: var(--color-text-muted);
}
:root[data-theme="light"] .prog-chip-green {
  background: rgba(21, 128, 61, 0.1);
  border-color: rgba(21, 128, 61, 0.25);
  color: #15803d;
}
:root[data-theme="light"] .item-count {
  background: rgba(37, 99, 235, 0.1);
  color: #1d4ed8;
}
:root[data-theme="light"] .gate-item--accepted .gate-item-icon { background: rgba(21,128,61,0.12);   color: #15803d; }
:root[data-theme="light"] .gate-item--blocked  .gate-item-icon { background: rgba(239,68,68,0.1);    color: #be123c; }
:root[data-theme="light"] .gate-item--waived   .gate-item-icon { background: rgba(71,85,105,0.1);    color: #475569; }
:root[data-theme="light"] .add-evidence-zone {
  border-color: rgba(28, 107, 39, 0.14);
}
:root[data-theme="light"] .add-evidence-header {
  background: rgba(28, 107, 39, 0.04);
  border-bottom-color: rgba(28, 107, 39, 0.1);
}
:root[data-theme="light"] .add-evidence-label {
  color: rgba(20, 33, 15, 0.55);
}
:root[data-theme="light"] .add-tab {
  color: rgba(20, 33, 15, 0.5);
}
:root[data-theme="light"] .add-tab:hover {
  background: rgba(28, 107, 39, 0.06);
  color: rgba(20, 33, 15, 0.8);
}
:root[data-theme="light"] .add-tab--active {
  background: rgba(37, 99, 235, 0.1);
  border-color: rgba(37, 99, 235, 0.28);
  color: #1d4ed8;
}
:root[data-theme="light"] .field-label {
  color: rgba(20, 33, 15, 0.6);
}
:root[data-theme="light"] .field input,
:root[data-theme="light"] .field select,
:root[data-theme="light"] .field textarea {
  border-color: rgba(28, 107, 39, 0.18);
  background: rgba(255, 255, 255, 0.7);
}
:root[data-theme="light"] .field input:focus,
:root[data-theme="light"] .field select:focus,
:root[data-theme="light"] .field textarea:focus {
  border-color: rgba(37, 99, 235, 0.45);
}
:root[data-theme="light"] .file-drop {
  border-color: rgba(28, 107, 39, 0.2);
  background: rgba(28, 107, 39, 0.02);
}
:root[data-theme="light"] .file-drop:hover {
  border-color: rgba(37, 99, 235, 0.4);
  background: rgba(37, 99, 235, 0.04);
}
:root[data-theme="light"] .file-drop-prompt {
  color: rgba(20, 33, 15, 0.45);
}
:root[data-theme="light"] .file-drop-selected {
  color: #1d4ed8;
}
:root[data-theme="light"] .library-search {
  border-color: rgba(28, 107, 39, 0.18);
  background: rgba(255, 255, 255, 0.7);
}
:root[data-theme="light"] .library-search:focus {
  border-color: rgba(37, 99, 235, 0.4);
}
:root[data-theme="light"] .library-hint {
  color: rgba(20, 33, 15, 0.4);
}
:root[data-theme="light"] .library-item {
  border-color: rgba(28, 107, 39, 0.12);
  background: rgba(255, 255, 255, 0.6);
}
:root[data-theme="light"] .library-meta {
  color: rgba(20, 33, 15, 0.45);
}
:root[data-theme="light"] .evidence-section-title {
  color: rgba(20, 33, 15, 0.7);
}
:root[data-theme="light"] .evidence-count {
  background: rgba(28, 107, 39, 0.08);
  color: rgba(20, 33, 15, 0.6);
}
:root[data-theme="light"] .empty-panel {
  background: rgba(28, 107, 39, 0.03);
  border-color: rgba(28, 107, 39, 0.15);
  color: rgba(20, 33, 15, 0.45);
}
:root[data-theme="light"] .evidence-card {
  border-color: rgba(28, 107, 39, 0.12);
  background: rgba(255, 255, 255, 0.6);
}
:root[data-theme="light"] .ev-accepted   { border-color: rgba(21,128,61,0.25);    background: rgba(21,128,61,0.05); }
:root[data-theme="light"] .ev-rejected   { border-color: rgba(239,68,68,0.25);    background: rgba(239,68,68,0.04); }
:root[data-theme="light"] .ev-needs_update { border-color: rgba(184,155,18,0.25); background: rgba(184,155,18,0.04); }
:root[data-theme="light"] .ev-waived     { border-color: rgba(71,85,105,0.2);     background: rgba(71,85,105,0.04); }
:root[data-theme="light"] .ev-pending_review { border-color: rgba(28,107,39,0.12); }
:root[data-theme="light"] .add-item-form { background: rgba(28,107,39,0.03); border-color: rgba(28,107,39,0.2); }
:root[data-theme="light"] .gate-item-delete { color: rgba(20,33,15,0.4); }
:root[data-theme="light"] .gate-item-delete:hover { background: rgba(239,68,68,0.08); color: #be123c; }
:root[data-theme="light"] .hash-value { background: rgba(28,107,39,0.05); border-color: rgba(28,107,39,0.15); color: rgba(20,33,15,0.75); }
:root[data-theme="light"] .btn-copy { border-color: rgba(28,107,39,0.2); color: rgba(20,33,15,0.5); }
:root[data-theme="light"] .btn-copy:hover { background: rgba(28,107,39,0.06); }
:root[data-theme="light"] .modal-box { background: #ffffff; }
:root[data-theme="light"] .modal-backdrop { background: rgba(20,33,15,0.5); }

/* ── KEV warning banner (CRA Art. 13(2)) ── */
.kev-banner {
  display: flex;
  align-items: flex-start;
  gap: 0.75rem;
  padding: 1rem 1.25rem;
  background: var(--color-danger-bg, #fff1f2);
  border: 1px solid var(--color-danger-border, #fca5a5);
  border-radius: var(--radius-md, 8px);
  color: var(--color-danger-text, #991b1b);
  margin-bottom: 1rem;
}
.kev-banner svg { flex-shrink: 0; margin-top: 2px; }
.kev-banner-body strong { display: block; font-weight: 600; margin-bottom: 0.25rem; }
.kev-banner-body p { margin: 0; font-size: var(--text-sm); }
.kev-notes { margin-top: 0.25rem !important; font-style: italic; }
</style>
