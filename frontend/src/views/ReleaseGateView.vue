<template>
  <section class="rg-page">

    <!-- ── Page header ── -->
    <header class="rg-head card" v-if="releaseDetail">
      <div class="rg-head-body">
        <div class="rg-head-title-group">
          <p class="rg-eyebrow">Release Workspace</p>
          <h1 class="rg-head-title">
            <span v-if="releaseDetail.release.product_name" class="rg-head-product">{{ releaseDetail.release.product_name }}</span>
            <span class="rg-head-version">{{ releaseDetail.release.display_version }}</span>
          </h1>
        </div>
        <div class="rg-head-meta">
          <span class="rg-chip" :class="`rg-chip--${releaseDetail.release.release_status}`">
            {{ formatLabel(releaseDetail.release.release_status) }}
          </span>
          <span class="rg-chip rg-chip--neutral">
            {{ formatLabel(releaseDetail.release.classification_snapshot) }}
          </span>
          <span class="rg-chip rg-chip--neutral">
            {{ formatLabel(releaseDetail.release.conformity_route_snapshot) }}
          </span>
          <span v-if="releaseDetail.release.planned_release_date" class="rg-chip rg-chip--neutral">
            Planned {{ formatDate(releaseDetail.release.planned_release_date) }}
          </span>
        </div>
      </div>

      <div class="rg-head-actions">
        <AppButton variant="ghost" @click="loadWorkspace" :disabled="loading || busy">
          <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="1 4 1 10 7 10"/><path d="M3.51 15a9 9 0 1 0 .49-4.9"/></svg>
          {{ loading ? "Refreshing…" : "Refresh" }}
        </AppButton>
        <AppButton
          v-if="!isApproved"
          variant="secondary"
          @click="submitForReview"
          :disabled="busy || !canSubmit"
        >
          {{ busyAction === "submit" ? "Submitting…" : "Submit for review" }}
        </AppButton>
        <AppButton
          v-if="canApprove"
          variant="primary"
          @click="approveGate"
          :disabled="busy"
        >
          <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg>
          {{ busyAction === "approve" ? "Approving…" : "Approve gate" }}
        </AppButton>
        <AppButton
          v-if="isApproved && canDownload && releaseDetail.gate.bundle_sha256"
          variant="secondary"
          @click="downloadBundle"
          :disabled="busy"
        >
          <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>
          {{ busyAction === "download" ? "Downloading…" : "Technical Documentation" }}
        </AppButton>
        <!-- Compliance report PDF — available for any non-draft release -->
        <AppButton
          v-if="releaseDetail && releaseDetail.release.release_status !== 'draft'"
          variant="secondary"
          @click="downloadReport"
          :disabled="busy"
        >
          <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/><polyline points="10 9 9 9 8 9"/></svg>
          {{ busyAction === "report" ? "Generating…" : "Compliance Report (PDF)" }}
        </AppButton>
      </div>
    </header>

    <div v-if="errorMessage" class="rg-feedback rg-feedback--error">{{ errorMessage }}</div>
    <div v-if="successMessage" class="rg-feedback rg-feedback--success">{{ successMessage }}</div>
    <div v-if="loading && !releaseDetail" class="rg-feedback">Loading release workspace…</div>

    <template v-else-if="releaseDetail">

      <!-- ── Progress strip ── -->
      <section class="rg-progress card">
        <div class="rg-progress-top">
          <div class="rg-progress-title-group">
            <p class="rg-eyebrow">Gate Progress</p>
            <h2 class="rg-progress-heading">{{ acceptedCount }} / {{ requiredCount }} required items accepted</h2>
          </div>
          <span class="rg-status-pill" :class="`rg-status--${releaseDetail.gate.status}`">
            {{ formatLabel(releaseDetail.gate.status) }}
          </span>
        </div>

        <div class="rg-progress-bar-wrap">
          <div class="rg-progress-track">
            <span class="rg-progress-fill" :style="{ width: `${progressPercent}%` }" />
          </div>
          <span class="rg-progress-pct">{{ progressPercent }}%</span>
        </div>

        <div class="rg-progress-chips">
          <span v-if="releaseDetail.gate.submitted_by_user" class="rg-prog-chip">
            <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="8" r="4"/><path d="M4 20c0-4 3.6-7 8-7s8 3 8 7"/></svg>
            Submitted by {{ formatUser(releaseDetail.gate.submitted_by_user) }}
          </span>
          <span v-if="releaseDetail.gate.approved_by_user" class="rg-prog-chip rg-prog-chip--green">
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
      <div class="rg-workspace">

        <!-- Left: gate item checklist -->
        <section class="card rg-checklist-card">
          <div class="rg-checklist-head">
            <p class="rg-eyebrow">Evidence checklist</p>
            <div class="rg-checklist-head-right">
              <span class="rg-item-count">{{ acceptedCount }}/{{ releaseDetail.gate.items.length }}</span>
              <AppButton
                v-if="canEdit && !isApproved"
                variant="ghost"
                size="sm"
                @click="showAddItemForm = !showAddItemForm"
              >
                <svg xmlns="http://www.w3.org/2000/svg" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>
                Add item
              </AppButton>
            </div>
          </div>

          <!-- Add checklist item form -->
          <form v-if="showAddItemForm && canEdit && !isApproved" class="rg-add-item-form" @submit.prevent="addChecklistItem">
            <label class="rg-field">
              <span class="rg-field-label">Item title</span>
              <input v-model.trim="addItemForm.title" type="text" required maxlength="255" placeholder="e.g. Penetration test report" />
            </label>
            <label class="rg-field">
              <span class="rg-field-label">Description <span class="rg-field-optional">(optional)</span></span>
              <input v-model.trim="addItemForm.description" type="text" maxlength="2000" placeholder="What evidence is required?" />
            </label>
            <div class="rg-add-item-actions">
              <AppButton variant="primary" type="submit" :disabled="busy || !addItemForm.title.trim()">
                {{ busyAction === "add-item" ? "Adding…" : "Add to checklist" }}
              </AppButton>
              <AppButton variant="ghost" size="sm" @click="showAddItemForm = false">Cancel</AppButton>
            </div>
          </form>

          <nav class="rg-checklist" aria-label="Gate items">
            <div
              v-for="item in releaseDetail.gate.items"
              :key="item.id"
              class="rg-ck-row"
            >
              <button
                class="rg-ck-item"
                :class="{
                  'rg-ck-item--selected': selectedItem?.id === item.id,
                  'rg-ck-item--accepted': item.status === 'accepted',
                  'rg-ck-item--blocked': item.status === 'rejected' || item.status === 'needs_update',
                  'rg-ck-item--waived': item.status === 'waived',
                }"
                type="button"
                @click="selectedItemId = item.id"
              >
                <div class="rg-ck-icon" aria-hidden="true">
                  <!-- accepted -->
                  <svg v-if="item.status === 'accepted'" xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg>
                  <!-- blocked -->
                  <svg v-else-if="item.status === 'rejected' || item.status === 'needs_update'" xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>
                  <!-- waived -->
                  <svg v-else-if="item.status === 'waived'" xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><line x1="8" y1="12" x2="16" y2="12"/></svg>
                  <!-- pending -->
                  <svg v-else xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/></svg>
                </div>

                <div class="rg-ck-body">
                  <span class="rg-ck-title">{{ item.title }}</span>
                  <span class="rg-ck-sub">{{ item.evidence_links.length }} artifact{{ item.evidence_links.length !== 1 ? 's' : '' }}</span>
                </div>

                <span class="rg-mini-pill" :class="`rg-decision--${item.status}`">
                  {{ formatLabel(item.status) }}
                </span>
              </button>
              <button
                v-if="canEdit && !isApproved"
                class="rg-ck-delete"
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
        <section class="card rg-detail-card" v-if="selectedItem">

          <!-- Detail header -->
          <div class="rg-detail-header">
            <div class="rg-detail-header-left">
              <p class="rg-eyebrow">Gate Item</p>
              <h2 class="rg-detail-title">{{ selectedItem.title }}</h2>
              <p class="rg-detail-copy">{{ selectedItem.description }}</p>
            </div>
            <span class="rg-mini-pill" :class="`rg-decision--${selectedItem.status}`">
              {{ formatLabel(selectedItem.status) }}
            </span>
          </div>

          <!-- Frozen banner -->
          <div v-if="isApproved" class="rg-frozen-banner">
            <div class="rg-frozen-icon" aria-hidden="true">
              <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <rect x="3" y="11" width="18" height="11" rx="2" ry="2"/>
                <path d="M7 11V7a5 5 0 0 1 10 0v4"/>
              </svg>
            </div>
            <div>
              <p class="rg-frozen-title">Approved — evidence frozen</p>
              <p class="rg-frozen-copy">
                Approved
                <template v-if="releaseDetail.gate.approved_by_user">by <strong>{{ formatUser(releaseDetail.gate.approved_by_user) }}</strong></template>
                <template v-if="releaseDetail.gate.approved_at"> on {{ formatDateTime(releaseDetail.gate.approved_at) }}</template>.
                No changes are permitted.
              </p>
              <p v-if="releaseDetail.gate.bundle_sha256" class="rg-frozen-hash">
                <span class="rg-hash-label">Bundle SHA-256:</span>
                <code class="rg-hash-value" :title="releaseDetail.gate.bundle_sha256">{{ releaseDetail.gate.bundle_sha256.slice(0, 16) }}…</code>
                <button class="rg-btn-copy" type="button" @click="copyHash(releaseDetail.gate.bundle_sha256!)">
                  <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/></svg>
                  Copy
                </button>
              </p>
            </div>
          </div>

          <!-- ── Add evidence zone (hidden when frozen) ── -->
          <div v-if="!isApproved" class="rg-add-evidence-zone">
            <div class="rg-add-evidence-header">
              <p class="rg-add-evidence-label">Add evidence</p>
              <div class="rg-add-tabs" role="tablist">
                <button
                  class="rg-add-tab"
                  :class="{ 'rg-add-tab--active': uploadMode === 'upload' && !showExistingEvidence }"
                  type="button"
                  role="tab"
                  @click="uploadMode = 'upload'; showExistingEvidence = false"
                >
                  <svg xmlns="http://www.w3.org/2000/svg" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" y1="3" x2="12" y2="15"/></svg>
                  Upload file
                </button>
                <button
                  class="rg-add-tab"
                  :class="{ 'rg-add-tab--active': uploadMode === 'external' && !showExistingEvidence }"
                  type="button"
                  role="tab"
                  @click="uploadMode = 'external'; showExistingEvidence = false"
                >
                  <svg xmlns="http://www.w3.org/2000/svg" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"/><path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"/></svg>
                  Web link
                </button>
                <button
                  class="rg-add-tab"
                  :class="{ 'rg-add-tab--active': showExistingEvidence }"
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
            <form v-if="!showExistingEvidence && uploadMode === 'upload'" class="rg-evidence-form" @submit.prevent="uploadArtifact">
              <div class="rg-form-grid">
                <label class="rg-field">
                  <span class="rg-field-label">Evidence name</span>
                  <input v-model.trim="uploadForm.title" type="text" required maxlength="255" placeholder="e.g. Threat model v1.2" />
                </label>
                <label class="rg-field">
                  <span class="rg-field-label">Evidence type</span>
                  <input :value="formatLabel(derivedArtifactType)" type="text" disabled />
                </label>
                <label class="rg-field rg-field--full">
                  <span class="rg-field-label">What does this file show?</span>
                  <textarea v-model.trim="uploadForm.description" rows="2" placeholder="Short explanation for reviewers" />
                </label>
                <label class="rg-field rg-field--full">
                  <span class="rg-field-label">Version note <span class="rg-field-optional">(optional)</span></span>
                  <textarea v-model.trim="uploadForm.change_summary" rows="2" placeholder="Describe what changed in this display_version" />
                </label>
                <div class="rg-field rg-field--full">
                  <span class="rg-field-label">Choose file</span>
                  <DropZone
                    accept=".pdf,image/*,.png,.jpg,.jpeg,.webp,.svg,.txt,.md,.csv,.json,.xml,.spdx,.cdx,.zip"
                    :multiple="false"
                    hint="Supports: PDF, images, SBOM files, test reports"
                    @files-selected="onFilesSelected"
                  />
                  <div v-if="selectedFile" class="rg-file-selected">
                    <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>
                    {{ selectedFile.name }}
                  </div>
                </div>
              </div>
              <div class="rg-form-footer">
                <AppButton variant="primary" type="submit" :disabled="busy || !selectedFile">
                  {{ busyAction === "upload" ? "Uploading…" : "Upload evidence" }}
                </AppButton>
              </div>
            </form>

            <!-- Web link form -->
            <form v-else-if="!showExistingEvidence && uploadMode === 'external'" class="rg-evidence-form" @submit.prevent="createExternalLink">
              <div class="rg-form-grid">
                <label class="rg-field">
                  <span class="rg-field-label">Evidence name</span>
                  <input v-model.trim="externalForm.title" type="text" required maxlength="255" />
                </label>
                <label class="rg-field">
                  <span class="rg-field-label">Evidence type</span>
                  <input :value="formatLabel(derivedArtifactType)" type="text" disabled />
                </label>
                <label class="rg-field rg-field--full">
                  <span class="rg-field-label">URL</span>
                  <input v-model.trim="externalForm.external_url" type="url" required placeholder="https://…" />
                </label>
                <label class="rg-field rg-field--full">
                  <span class="rg-field-label">Description <span class="rg-field-optional">(optional)</span></span>
                  <textarea v-model.trim="externalForm.description" rows="2" placeholder="What does this link show?" />
                </label>
              </div>
              <div class="rg-form-footer">
                <AppButton variant="primary" type="submit" :disabled="busy">
                  {{ busyAction === "external" ? "Saving…" : "Save evidence link" }}
                </AppButton>
              </div>
            </form>

            <!-- Library panel -->
            <div v-else-if="showExistingEvidence" class="rg-library-panel">
              <div class="rg-library-toolbar">
                <input v-model.trim="artifactQuery" type="search" class="rg-library-search" placeholder="Search title or description…" @input="filterLibrary" />
                <AppButton variant="ghost" @click="refreshLibrary" :disabled="libraryLoading">
                  {{ libraryLoading ? "Refreshing…" : "Refresh" }}
                </AppButton>
              </div>
              <p class="rg-library-hint">Use only when an existing file already fits this release and this requirement.</p>
              <div v-if="filteredLibrary.length === 0" class="rg-empty-panel">No existing evidence found for this product yet.</div>
              <div v-else class="rg-library-list">
                <article v-for="artifact in filteredLibrary" :key="artifact.id" class="rg-library-item">
                  <div class="rg-library-item-info">
                    <strong>{{ artifact.title }}</strong>
                    <p class="rg-muted">{{ artifact.description || "No description provided." }}</p>
                    <p class="rg-library-meta">
                      {{ formatLabel(artifact.artifact_type) }}
                      <span v-if="artifact.latest_revision">· Rev {{ artifact.latest_revision.revision_number }}</span>
                    </p>
                  </div>
                  <AppButton
                    variant="secondary"
                    size="sm"
                    :disabled="busy || !artifact.latest_revision"
                    @click="attachRevision(artifact.latest_revision!.id)"
                  >
                    Use this
                  </AppButton>
                </article>
              </div>
            </div>
          </div>

          <!-- ── Detail tabs navigation ── -->
          <div class="rg-detail-tabs">
            <button
              class="rg-detail-tab"
              :class="{ 'rg-detail-tab--active': detailTabsActive === 'evidence' }"
              type="button"
              @click="detailTabsActive = 'evidence'"
            >
              <svg xmlns="http://www.w3.org/2000/svg" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>
              Evidence
            </button>
            <button
              class="rg-detail-tab"
              :class="{ 'rg-detail-tab--active': detailTabsActive === 'history' }"
              type="button"
              @click="loadRevisionHistory"
            >
              <svg xmlns="http://www.w3.org/2000/svg" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>
              History
            </button>
            <button
              v-if="selectedItem.code === 'sbom'"
              class="rg-detail-tab"
              :class="{ 'rg-detail-tab--active': detailTabsActive === 'diff' }"
              type="button"
              @click="loadSbomDiff"
            >
              <svg xmlns="http://www.w3.org/2000/svg" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M9 11l3 3L22 4"/><path d="M20.24 12.52a6.5 6.5 0 0 0-9.26-9.26M4.2 4.2a6.5 6.5 0 0 0 9.26 9.26"/></svg>
              Diff
            </button>
            <button
              class="rg-detail-tab"
              :class="{ 'rg-detail-tab--active': detailTabsActive === 'dependencies' }"
              type="button"
              @click="detailTabsActive = 'dependencies'"
            >
              <svg xmlns="http://www.w3.org/2000/svg" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 3v18M3 12h18"/></svg>
              Dependencies
            </button>
            <button
              v-if="isApproved"
              class="rg-detail-tab"
              :class="{ 'rg-detail-tab--active': detailTabsActive === 'snapshot' }"
              type="button"
              @click="detailTabsActive = 'snapshot'"
            >
              <svg xmlns="http://www.w3.org/2000/svg" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="11" width="18" height="11" rx="2" ry="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/></svg>
              Snapshot
            </button>
          </div>

          <!-- ── Evidence tab ── -->
          <div v-if="detailTabsActive === 'evidence'" class="rg-evidence-section">
            <div class="rg-evidence-section-header">
              <div class="rg-evidence-section-title">
                <svg v-if="isApproved" xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="3" y="11" width="18" height="11" rx="2" ry="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/></svg>
                <span>{{ isApproved ? "Frozen snapshot" : "Attached evidence" }}</span>
              </div>
              <span class="rg-evidence-count">{{ selectedItem.evidence_links.length }}</span>
            </div>

            <div v-if="selectedItem.evidence_links.length === 0" class="rg-empty-panel">
              No evidence linked yet. Use the panel above to attach your first artifact.
            </div>

            <div v-else class="rg-evidence-list">
              <article
                v-for="link in selectedItem.evidence_links"
                :key="link.id"
                class="rg-ev-card"
                :class="`rg-ev--${link.decision}`"
              >
                <!-- Card top row -->
                <div class="rg-ev-top">
                  <div class="rg-ev-identity">
                    <div class="rg-file-badge">{{ fileTypeLabel(link.artifact_revision.original_filename) }}</div>
                    <div class="rg-ev-name-group">
                      <strong class="rg-ev-name">{{ link.artifact_revision.original_filename || `Revision ${link.artifact_revision.revision_number}` }}</strong>
                      <span class="rg-ev-meta">
                        Rev {{ link.artifact_revision.revision_number }}
                        · {{ formatLabel(link.artifact_revision.source_type) }}
                        <template v-if="link.artifact_revision.file_size_bytes"> · {{ formatSize(link.artifact_revision.file_size_bytes) }}</template>
                      </span>
                    </div>
                  </div>
                  <span class="rg-mini-pill" :class="`rg-decision--${link.decision}`">{{ formatLabel(link.decision) }}</span>
                </div>

                <!-- Change summary -->
                <p v-if="link.artifact_revision.change_summary" class="rg-ev-note">
                  {{ link.artifact_revision.change_summary }}
                </p>

                <!-- Activity row -->
                <div class="rg-ev-activity">
                  <div class="rg-ev-activity-item">
                    <div class="rg-ev-avatar">{{ userInitials(link.artifact_revision.uploaded_by_user) }}</div>
                    <div class="rg-ev-activity-text">
                      <span class="rg-ev-activity-action">Uploaded</span>
                      <span class="rg-ev-activity-who">{{ formatUser(link.artifact_revision.uploaded_by_user) }}</span>
                      <span class="rg-ev-activity-when">{{ formatDateTime(link.artifact_revision.created_at) }}</span>
                    </div>
                  </div>
                  <div v-if="link.reviewed_by_user || link.reviewed_at" class="rg-ev-activity-item">
                    <div class="rg-ev-avatar rg-ev-avatar--review">{{ userInitials(link.reviewed_by_user) }}</div>
                    <div class="rg-ev-activity-text">
                      <span class="rg-ev-activity-action">{{ reviewActionLabel(link.decision) }}</span>
                      <span class="rg-ev-activity-who">{{ formatUser(link.reviewed_by_user) }}</span>
                      <span v-if="link.reviewed_at" class="rg-ev-activity-when">{{ formatDateTime(link.reviewed_at) }}</span>
                    </div>
                  </div>
                </div>

                <!-- Rationale note -->
                <p v-if="link.rationale" class="rg-ev-rationale">{{ link.rationale }}</p>

                <!-- Actions row -->
                <div class="rg-ev-actions">
                  <AppButton
                    v-if="link.artifact_revision.storage_path"
                    variant="ghost"
                    size="sm"
                    @click="downloadRevision(link.artifact_revision.id, link.artifact_revision.original_filename || 'artifact')"
                  >
                    <svg xmlns="http://www.w3.org/2000/svg" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>
                    Download
                  </AppButton>
                  <a
                    v-else-if="link.artifact_revision.external_url"
                    class="rg-link-btn"
                    :href="link.artifact_revision.external_url"
                    target="_blank"
                    rel="noreferrer"
                  >
                    <svg xmlns="http://www.w3.org/2000/svg" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/><polyline points="15 3 21 3 21 9"/><line x1="10" y1="14" x2="21" y2="3"/></svg>
                    Open link
                  </a>
                  <AppButton
                    v-if="!isApproved"
                    variant="danger"
                    size="sm"
                    :disabled="busy"
                    @click="detachEvidence(link.id)"
                  >
                    {{ busyAction === `detach-${link.id}` ? "Removing…" : "Remove" }}
                  </AppButton>
                </div>

                <!-- Review panel -->
                <div v-if="canReview && !isApproved" class="rg-review-panel">
                  <label class="rg-field">
                    <span class="rg-field-label">Reviewer note</span>
                    <textarea v-model.trim="reviewNotes[link.id]" rows="2" placeholder="Explain your decision (optional)" />
                  </label>
                  <div class="rg-review-actions">
                    <AppButton variant="primary" size="sm" :disabled="busy" @click="reviewLink(link.id, 'accepted')">
                      <svg xmlns="http://www.w3.org/2000/svg" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg>
                      Accept
                    </AppButton>
                    <AppButton variant="ghost" size="sm" :disabled="busy" @click="reviewLink(link.id, 'needs_update')">Request update</AppButton>
                    <AppButton variant="ghost" size="sm" :disabled="busy" @click="reviewLink(link.id, 'rejected')">Reject</AppButton>
                    <AppButton variant="ghost" size="sm" :disabled="busy" @click="reviewLink(link.id, 'waived')">Waive</AppButton>
                  </div>
                </div>
              </article>
            </div>
          </div>

          <!-- ── History tab ── -->
          <div v-if="detailTabsActive === 'history'" class="rg-history-section">
            <div v-if="revisionHistoryLoading" class="rg-loading-panel">
              <div class="rg-spinner"></div>
              <p>Loading revision history…</p>
            </div>
            <div v-else-if="!revisionHistory" class="rg-empty-panel">
              No artifact linked to this item yet.
            </div>
            <div v-else class="rg-revision-panel">
              <p class="rg-revision-title">{{ revisionHistory.title }}</p>
              <p class="rg-revision-meta">{{ revisionHistory.artifact_type }} · {{ revisionHistory.revisions?.length ?? 0 }} revision{{ (revisionHistory.revisions?.length ?? 0) !== 1 ? 's' : '' }}</p>
              <div v-if="!revisionHistory.revisions || revisionHistory.revisions.length === 0" class="rg-empty-panel">
                No revisions available.
              </div>
              <div v-else class="rg-revisions-list">
                <article v-for="rev in revisionHistory.revisions" :key="rev.id" class="rg-revision-card">
                  <div class="rg-revision-header">
                    <span class="rg-revision-number">Rev {{ rev.revision_number }}</span>
                    <span class="rg-revision-date">{{ formatDateTime(rev.created_at) }}</span>
                  </div>
                  <p v-if="rev.change_summary" class="rg-revision-summary">{{ rev.change_summary }}</p>
                  <p class="rg-revision-uploader">Uploaded by {{ formatUser(rev.uploaded_by_user) }}</p>
                  <div class="rg-revision-meta-row">
                    <span>{{ formatLabel(rev.source_type) }}</span>
                    <span v-if="rev.file_size_bytes">{{ formatSize(rev.file_size_bytes) }}</span>
                    <span v-if="rev.sha256" class="rg-sha-label">{{ rev.sha256.slice(0, 12) }}…</span>
                  </div>
                </article>
              </div>
            </div>
          </div>

          <!-- ── SBOM Diff tab ── -->
          <div v-if="detailTabsActive === 'diff'" class="rg-diff-section">
            <div v-if="sbomDiffData === null && !revisionHistoryLoading" class="rg-empty-panel">
              No SBOM found for this item. Ensure an SBOM file is attached above.
            </div>
            <SbomDiffPanel v-else :diff="sbomDiffData" :loading="revisionHistoryLoading" />
          </div>

          <!-- ── Dependencies tab ── -->
          <div v-if="detailTabsActive === 'dependencies'" class="rg-dependencies-section">
            <p class="rg-section-hint">Define prerequisite relationships between checklist items.</p>
            <div class="rg-dep-graph">
              <div v-for="item in releaseDetail.gate.items" :key="item.id" class="rg-dep-node">
                <div class="rg-dep-node-card" :class="`rg-dep-node--${item.status}`">
                  <strong class="rg-dep-node-title">{{ item.title }}</strong>
                  <span class="rg-dep-node-status">{{ formatLabel(item.status) }}</span>
                </div>
                <div v-if="item.prerequisites && item.prerequisites.length > 0" class="rg-dep-prereqs">
                  <p class="rg-dep-prereq-label">Requires:</p>
                  <div v-for="prereq in item.prerequisites" :key="prereq.id" class="rg-dep-prereq-item">
                    {{ prereq.title }}
                  </div>
                </div>
              </div>
            </div>
            <div v-if="canEdit && !isApproved" class="rg-dep-editor">
              <p class="rg-dep-editor-label">Add prerequisite</p>
              <p class="rg-dep-editor-hint">Mark {{ selectedItem.title }} as requiring another item to be completed first.</p>
              <AppButton variant="secondary" size="sm" @click="showDependenciesEditor = !showDependenciesEditor">
                {{ showDependenciesEditor ? "Cancel" : "Add prerequisite" }}
              </AppButton>
            </div>
          </div>

          <!-- ── Snapshot tab ── -->
          <div v-if="detailTabsActive === 'snapshot' && isApproved && releaseDetail.gate.snapshot_json" class="rg-snapshot-section">
            <div class="rg-snapshot-info">
              <p class="rg-snapshot-label">Approved at</p>
              <p class="rg-snapshot-value">{{ formatDateTime(releaseDetail.gate.approved_at) }}</p>
              <p class="rg-snapshot-label">Approved by</p>
              <p class="rg-snapshot-value">{{ formatUser(releaseDetail.gate.approved_by_user) }}</p>
              <p class="rg-snapshot-label">Bundle SHA-256</p>
              <p class="rg-snapshot-hash">{{ releaseDetail.gate.bundle_sha256?.slice(0, 20) }}…</p>
            </div>
            <details class="rg-snapshot-json-view">
              <summary>View snapshot JSON</summary>
              <pre class="rg-snapshot-json"><code>{{ JSON.stringify(releaseDetail.gate.snapshot_json, null, 2) }}</code></pre>
            </details>
          </div>

        </section>
      </div>
    </template>

    <!-- ── Remove checklist item confirmation modal ── -->
    <div v-if="removeConfirm.item" class="rg-modal-backdrop" @click.self="removeConfirm.item = null">
      <div class="rg-modal" role="dialog" aria-modal="true">
        <div class="rg-modal-header">
          <h3 class="rg-modal-title">Remove checklist item?</h3>
          <AppButton variant="ghost" size="sm" @click="removeConfirm.item = null">
            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
          </AppButton>
        </div>
        <p class="rg-modal-body">
          You are about to remove <strong>{{ removeConfirm.item?.title }}</strong> from the checklist.
          <template v-if="removeConfirm.hasEvidence">
            This item has <strong>{{ removeConfirm.evidenceCount }} attached artifact{{ removeConfirm.evidenceCount !== 1 ? 's' : '' }}</strong> which will also be permanently deleted.
          </template>
          This cannot be undone.
        </p>
        <div class="rg-modal-actions">
          <AppButton variant="danger" :disabled="busy" @click="removeChecklistItem">
            {{ busyAction === "remove-item" ? "Removing…" : "Yes, remove item" }}
          </AppButton>
          <AppButton variant="ghost" size="sm" @click="removeConfirm.item = null">Cancel</AppButton>
        </div>
      </div>
    </div>

  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from "vue";
import { useRoute } from "vue-router";

import AppButton from "@/components/AppButton.vue";
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

async function downloadReport(): Promise<void> {
  if (!releaseDetail.value) return;
  busy.value = true;
  busyAction.value = "report";
  errorMessage.value = "";
  successMessage.value = "";
  try {
    await releaseGateService.downloadReport(releaseDetail.value.release.id);
  } catch (error: any) {
    errorMessage.value = error?.message ?? "Failed to generate compliance report.";
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
/* ── Page shell ── */
.rg-page { display: grid; gap: 1.25rem; }

/* ── Shared typography ── */
.rg-eyebrow {
  margin: 0 0 0.25rem;
  text-transform: uppercase;
  letter-spacing: 0.11em;
  font-size: 0.7rem;
  font-weight: 700;
  color: var(--color-primary);
}
.rg-detail-copy,
.rg-muted {
  margin: 0;
  color: var(--color-text-muted);
  font-size: 0.88rem;
  line-height: 1.55;
}

/* ── Feedback banners ── */
.rg-feedback {
  padding: 0.75rem 1rem;
  border-radius: 8px;
  background: var(--color-surface);
  border: 1px dashed var(--color-border);
  color: var(--color-text-muted);
  font-size: 0.9rem;
}
.rg-feedback--error {
  background: var(--color-danger-bg);
  border: 1px solid var(--color-danger-border);
  color: var(--color-danger-text);
}
.rg-feedback--success {
  background: var(--color-success-bg);
  border: 1px solid var(--color-success-border);
  color: var(--color-success-text);
}

/* ── Status / decision pills ── */
.rg-status-pill,
.rg-mini-pill {
  display: inline-flex;
  align-items: center;
  padding: 0.25rem 0.65rem;
  border-radius: 999px;
  font-weight: 700;
  font-size: 0.75rem;
  letter-spacing: 0.02em;
  white-space: nowrap;
}
.rg-status--draft,
.rg-decision--pending_review {
  background: var(--color-warning-bg);
  color: var(--color-warning-text);
}
.rg-status--in_review {
  background: var(--color-surface-elevated);
  color: var(--color-text-muted);
  border: 1px solid var(--color-border);
}
.rg-decision--waived {
  background: var(--color-surface-elevated);
  color: var(--color-text-muted);
  border: 1px solid var(--color-border);
}
.rg-status--approved,
.rg-decision--accepted {
  background: var(--color-success-bg);
  color: var(--color-success-text);
}
.rg-status--blocked,
.rg-decision--rejected,
.rg-decision--needs_update {
  background: var(--color-danger-bg);
  color: var(--color-danger-text);
}

/* ── Meta chips (header) ── */
.rg-chip {
  display: inline-flex;
  align-items: center;
  padding: 0.28rem 0.7rem;
  border-radius: 999px;
  font-size: 0.78rem;
  font-weight: 600;
  border: 1px solid var(--color-border);
  background: var(--color-surface-elevated);
  color: var(--color-text-muted);
}
.rg-chip--neutral { background: var(--color-surface-elevated); color: var(--color-text-muted); }
.rg-chip--draft     { background: var(--color-warning-bg);  color: var(--color-warning-text); }
.rg-chip--in_review { background: var(--color-surface-elevated); color: var(--color-text-muted); }
.rg-chip--approved  { background: var(--color-success-bg);  color: var(--color-success-text); }
.rg-chip--blocked   { background: var(--color-danger-bg);   color: var(--color-danger-text); }

/* ── Page header card — CRANE left-accent style ── */
.rg-head {
  position: relative;
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 1rem;
  padding-left: 1.5rem;
  overflow: hidden;
}
.rg-head::before {
  content: "";
  position: absolute;
  left: 0;
  top: 0;
  bottom: 0;
  width: 4px;
  background: var(--color-primary);
  border-radius: 4px 0 0 4px;
}
.rg-head-body {
  display: flex;
  flex-direction: column;
  gap: 0.55rem;
  min-width: 0;
}
.rg-head-title-group { display: flex; flex-direction: column; gap: 0.1rem; }
.rg-head-title {
  margin: 0;
  font-size: 1.5rem;
  font-weight: 700;
  color: var(--color-text);
  line-height: 1.2;
  display: flex;
  align-items: baseline;
  gap: 0.45rem;
  flex-wrap: wrap;
}
.rg-head-product {
  color: var(--color-text);
}
.rg-head-version {
  color: var(--color-text-muted);
  font-weight: 500;
  font-size: 1.1rem;
}
.rg-head-meta { display: flex; flex-wrap: wrap; gap: 0.45rem; }
.rg-head-actions {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  flex-shrink: 0;
  flex-wrap: wrap;
}

/* ── Progress card ── */
.rg-progress { display: grid; gap: 0.85rem; }
.rg-progress-top {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 1rem;
}
.rg-progress-title-group { display: flex; flex-direction: column; gap: 0.1rem; }
.rg-progress-heading {
  margin: 0;
  font-size: 0.95rem;
  font-weight: 600;
  color: var(--color-text);
}
.rg-progress-bar-wrap {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}
.rg-progress-track {
  flex: 1;
  height: 7px;
  background: var(--color-border);
  border-radius: 999px;
  overflow: hidden;
}
.rg-progress-fill {
  display: block;
  height: 100%;
  border-radius: 999px;
  background: var(--color-primary);
  transition: width 0.4s ease;
}
.rg-progress-pct {
  font-size: 0.85rem;
  font-weight: 700;
  color: var(--color-primary);
  min-width: 2.5rem;
  text-align: right;
}
.rg-progress-chips { display: flex; flex-wrap: wrap; gap: 0.45rem; }
.rg-prog-chip {
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
  padding: 0.25rem 0.65rem;
  border-radius: 999px;
  font-size: 0.76rem;
  background: var(--color-surface-elevated);
  border: 1px solid var(--color-border);
  color: var(--color-text-muted);
}
.rg-prog-chip--green {
  background: var(--color-success-bg);
  border-color: var(--color-success-border);
  color: var(--color-success-text);
}

/* ── Workspace 2-col grid ── */
.rg-workspace {
  display: grid;
  grid-template-columns: minmax(260px, 340px) minmax(0, 1fr);
  gap: 1.25rem;
  align-items: start;
}

/* ── Checklist card (left column) ── */
.rg-checklist-card { position: sticky; top: 1.25rem; }
.rg-checklist-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.75rem;
}
.rg-checklist-head-right { display: flex; align-items: center; gap: 0.5rem; }
.rg-item-count {
  font-size: 0.8rem;
  font-weight: 700;
  padding: 0.18rem 0.55rem;
  border-radius: 999px;
  background: var(--color-surface-elevated);
  border: 1px solid var(--color-border);
  color: var(--color-text-muted);
}
.rg-checklist { display: flex; flex-direction: column; gap: 0.4rem; }

/* ── Checklist item (ck-item) ── */
.rg-ck-row { display: flex; align-items: stretch; gap: 0.25rem; }
.rg-ck-row .rg-ck-item { flex: 1 1 0; min-width: 0; }
.rg-ck-item {
  display: flex;
  align-items: center;
  gap: 0.65rem;
  width: 100%;
  padding: 0.6rem 0.75rem;
  border: 1px solid var(--color-border);
  border-radius: 8px;
  background: var(--color-surface);
  text-align: left;
  cursor: pointer;
  transition: border-color 0.12s, background 0.12s;
}
.rg-ck-item:hover { background: var(--color-surface-elevated); }
.rg-ck-item--selected {
  border-color: var(--color-primary);
  background: var(--color-success-bg);
}
.rg-ck-item--accepted {
  border-color: var(--color-success-border);
  background: var(--color-success-bg);
}
.rg-ck-item--blocked {
  border-color: var(--color-danger-border);
  background: var(--color-danger-bg);
}
.rg-ck-item--waived {
  border-color: var(--color-border);
  opacity: 0.7;
}
.rg-ck-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 1.55rem;
  height: 1.55rem;
  border-radius: 50%;
  flex-shrink: 0;
  background: var(--color-surface-elevated);
  border: 1px solid var(--color-border);
  color: var(--color-text-muted);
}
.rg-ck-item--accepted .rg-ck-icon { background: var(--color-success-bg); border-color: var(--color-success-border); color: var(--color-success-text); }
.rg-ck-item--blocked  .rg-ck-icon { background: var(--color-danger-bg);  border-color: var(--color-danger-border);  color: var(--color-danger-text); }
.rg-ck-body { flex: 1; min-width: 0; display: flex; flex-direction: column; gap: 0.1rem; }
.rg-ck-title {
  font-size: 0.86rem;
  font-weight: 600;
  color: var(--color-text);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.rg-ck-sub { font-size: 0.74rem; color: var(--color-text-muted); }
.rg-ck-delete {
  flex: 0 0 auto;
  display: flex;
  align-items: center;
  padding: 0 0.4rem;
  border-radius: 6px;
  border: 1px solid transparent;
  background: transparent;
  color: var(--color-text-muted);
  cursor: pointer;
  transition: background 0.12s, color 0.12s;
}
.rg-ck-delete:hover { background: var(--color-danger-bg); color: var(--color-danger-text); }

/* ── Add checklist item form ── */
.rg-add-item-form {
  display: grid;
  gap: 0.6rem;
  padding: 0.75rem;
  background: var(--color-surface);
  border: 1px dashed var(--color-border);
  border-radius: 8px;
  margin-bottom: 0.75rem;
}
.rg-add-item-actions { display: flex; gap: 0.5rem; align-items: center; }

/* ── Detail card (right column) ── */
.rg-detail-card { display: flex; flex-direction: column; gap: 1.25rem; }
.rg-detail-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 1rem;
}
.rg-detail-header-left { display: flex; flex-direction: column; gap: 0.3rem; }
.rg-detail-title {
  margin: 0;
  font-size: 1.1rem;
  font-weight: 700;
  color: var(--color-text);
}

/* ── Frozen banner ── */
.rg-frozen-banner {
  display: flex;
  align-items: flex-start;
  gap: 0.85rem;
  padding: 0.85rem 1rem;
  border-radius: 10px;
  border: 1px solid var(--color-success-border);
  background: var(--color-success-bg);
}
.rg-frozen-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 2rem;
  height: 2rem;
  border-radius: 50%;
  flex-shrink: 0;
  background: var(--color-success-border);
  color: var(--color-success-text);
}
.rg-frozen-title {
  margin: 0 0 0.15rem;
  font-size: 0.88rem;
  font-weight: 700;
  color: var(--color-success-text);
}
.rg-frozen-copy {
  margin: 0;
  font-size: 0.83rem;
  color: var(--color-success-text);
  opacity: 0.8;
  line-height: 1.5;
}
.rg-frozen-hash {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  margin: 0.35rem 0 0;
  font-size: 0.8rem;
  flex-wrap: wrap;
}
.rg-hash-label { color: var(--color-text-muted); font-weight: 600; }
.rg-hash-value {
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: 4px;
  padding: 0.1rem 0.4rem;
  font-size: 0.78rem;
  color: var(--color-text);
}
.rg-btn-copy {
  display: inline-flex;
  align-items: center;
  gap: 0.25rem;
  padding: 0.15rem 0.45rem;
  border-radius: 4px;
  border: 1px solid var(--color-border);
  background: transparent;
  color: var(--color-text-muted);
  font-size: 0.76rem;
  cursor: pointer;
  transition: background 0.12s;
}
.rg-btn-copy:hover { background: var(--color-surface-elevated); }

/* ── Add evidence zone ── */
.rg-add-evidence-zone {
  border: 1px solid var(--color-border);
  border-radius: 10px;
  overflow: hidden;
}
.rg-add-evidence-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  padding: 0.65rem 1rem;
  background: var(--color-surface);
  border-bottom: 1px solid var(--color-border);
}
.rg-add-evidence-label {
  font-size: 0.75rem;
  font-weight: 700;
  color: var(--color-text-muted);
  text-transform: uppercase;
  letter-spacing: 0.08em;
}
.rg-add-tabs { display: flex; gap: 0.2rem; }
.rg-add-tab {
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
  padding: 0.32rem 0.7rem;
  border: 1px solid transparent;
  border-radius: 6px;
  background: transparent;
  color: var(--color-text-muted);
  font: inherit;
  font-size: 0.8rem;
  font-weight: 500;
  cursor: pointer;
  transition: background 0.12s, color 0.12s, border-color 0.12s;
}
.rg-add-tab:hover { background: var(--color-surface-elevated); color: var(--color-text); }
.rg-add-tab--active {
  background: var(--color-success-bg);
  border-color: var(--color-success-border);
  color: var(--color-success-text);
}

/* ── Evidence form ── */
.rg-evidence-form { padding: 1rem; display: flex; flex-direction: column; gap: 1rem; }
.rg-form-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 0.75rem; }
.rg-field { display: flex; flex-direction: column; gap: 0.3rem; }
.rg-field--full { grid-column: 1 / -1; }
.rg-field-label { font-size: 0.78rem; font-weight: 600; color: var(--color-text-muted); }
.rg-field-optional { font-weight: 400; opacity: 0.7; }
.rg-field input,
.rg-field select,
.rg-field textarea {
  width: 100%;
  border: 1px solid var(--color-border);
  border-radius: 7px;
  padding: 0.55rem 0.8rem;
  background: var(--color-surface);
  color: var(--color-text);
  font: inherit;
  font-size: 0.88rem;
  resize: vertical;
  transition: border-color 0.12s;
}
.rg-field input:focus,
.rg-field select:focus,
.rg-field textarea:focus {
  outline: none;
  border-color: var(--color-primary);
}
.rg-field input:disabled,
.rg-field select:disabled { opacity: 0.5; cursor: not-allowed; }
.rg-file-selected {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  margin-top: 0.4rem;
  font-size: 0.84rem;
  color: var(--color-primary);
}
.rg-form-footer { display: flex; justify-content: flex-end; gap: 0.5rem; }

/* ── Library panel ── */
.rg-library-panel { padding: 1rem; display: flex; flex-direction: column; gap: 0.75rem; }
.rg-library-toolbar { display: flex; gap: 0.5rem; align-items: center; }
.rg-library-search {
  flex: 1;
  border: 1px solid var(--color-border);
  border-radius: 7px;
  padding: 0.48rem 0.8rem;
  background: var(--color-surface);
  color: var(--color-text);
  font: inherit;
  font-size: 0.86rem;
}
.rg-library-search:focus { outline: none; border-color: var(--color-primary); }
.rg-library-hint { margin: 0; font-size: 0.78rem; color: var(--color-text-muted); font-style: italic; }
.rg-library-list { display: flex; flex-direction: column; gap: 0.45rem; max-height: 22rem; overflow-y: auto; }
.rg-library-item {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 1rem;
  padding: 0.7rem 0.85rem;
  border: 1px solid var(--color-border);
  border-radius: 8px;
  background: var(--color-surface);
}
.rg-library-item-info { display: flex; flex-direction: column; gap: 0.2rem; min-width: 0; }
.rg-library-item-info strong { font-size: 0.88rem; color: var(--color-text); }
.rg-library-meta { margin: 0; font-size: 0.76rem; color: var(--color-text-muted); }

/* ── Detail tabs ── */
.rg-detail-tabs {
  display: flex;
  gap: 0.15rem;
  border-bottom: 1px solid var(--color-border);
  margin-bottom: 0.85rem;
  flex-wrap: wrap;
}
.rg-detail-tab {
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
  padding: 0.55rem 0.9rem;
  border: none;
  background: transparent;
  color: var(--color-text-muted);
  font-size: 0.86rem;
  font-weight: 500;
  cursor: pointer;
  border-bottom: 2px solid transparent;
  margin-bottom: -1px;
  transition: color 0.15s, border-color 0.15s;
}
.rg-detail-tab:hover { color: var(--color-text); }
.rg-detail-tab--active { color: var(--color-primary); border-bottom-color: var(--color-primary); }

/* ── Evidence section ── */
.rg-evidence-section { display: flex; flex-direction: column; gap: 0.75rem; }
.rg-evidence-section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.75rem;
}
.rg-evidence-section-title {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  font-size: 0.86rem;
  font-weight: 600;
  color: var(--color-text-muted);
}
.rg-evidence-count {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 1.45rem;
  height: 1.45rem;
  padding: 0 0.4rem;
  border-radius: 999px;
  background: var(--color-surface-elevated);
  border: 1px solid var(--color-border);
  font-size: 0.75rem;
  font-weight: 700;
  color: var(--color-text-muted);
}
.rg-empty-panel {
  padding: 1.25rem 1rem;
  border-radius: 8px;
  background: var(--color-surface);
  border: 1px dashed var(--color-border);
  color: var(--color-text-muted);
  font-size: 0.86rem;
  text-align: center;
}
.rg-evidence-list { display: flex; flex-direction: column; gap: 0.7rem; }

/* ── Evidence card ── */
.rg-ev-card {
  border: 1px solid var(--color-border);
  border-radius: 10px;
  overflow: hidden;
  background: var(--color-surface);
  display: flex;
  flex-direction: column;
}
.rg-ev--accepted   { border-color: var(--color-success-border); }
.rg-ev--rejected   { border-color: var(--color-danger-border); }
.rg-ev--needs_update { border-color: var(--color-warning-border); }
.rg-ev-top {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 0.75rem;
  padding: 0.85rem 1rem 0.6rem;
}
.rg-ev-identity { display: flex; align-items: flex-start; gap: 0.6rem; min-width: 0; }
.rg-file-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 2.5rem;
  padding: 0.3rem 0.45rem;
  border-radius: 6px;
  background: var(--color-surface-elevated);
  border: 1px solid var(--color-border);
  color: var(--color-text-muted);
  font-size: 0.68rem;
  font-weight: 800;
  letter-spacing: 0.06em;
  flex-shrink: 0;
}
.rg-ev-name-group { display: flex; flex-direction: column; gap: 0.12rem; min-width: 0; }
.rg-ev-name {
  font-size: 0.9rem;
  font-weight: 600;
  color: var(--color-text);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.rg-ev-meta { font-size: 0.75rem; color: var(--color-text-muted); }
.rg-ev-note {
  margin: 0;
  padding: 0 1rem 0.6rem;
  font-size: 0.83rem;
  color: var(--color-text-muted);
  font-style: italic;
}
.rg-ev-activity {
  display: flex;
  flex-direction: column;
  gap: 0.45rem;
  padding: 0.55rem 1rem;
  border-top: 1px solid var(--color-border);
  background: var(--color-surface-elevated);
}
.rg-ev-activity-item { display: flex; align-items: center; gap: 0.55rem; }
.rg-ev-avatar {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 1.75rem;
  height: 1.75rem;
  border-radius: 50%;
  flex-shrink: 0;
  background: var(--color-surface-elevated);
  border: 1px solid var(--color-border);
  color: var(--color-text-muted);
  font-size: 0.68rem;
  font-weight: 800;
}
.rg-ev-avatar--review {
  background: var(--color-success-bg);
  border-color: var(--color-success-border);
  color: var(--color-success-text);
}
.rg-ev-activity-text {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 0.2rem 0.35rem;
  font-size: 0.78rem;
}
.rg-ev-activity-action { color: var(--color-text-muted); }
.rg-ev-activity-who { color: var(--color-text); font-weight: 500; }
.rg-ev-activity-when { color: var(--color-text-muted); font-size: 0.73rem; }
.rg-ev-rationale {
  margin: 0;
  padding: 0.55rem 1rem;
  font-size: 0.81rem;
  color: var(--color-text-muted);
  border-top: 1px solid var(--color-border);
  font-style: italic;
}
.rg-ev-actions {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  flex-wrap: wrap;
  padding: 0.5rem 1rem;
  border-top: 1px solid var(--color-border);
}
/* Open link styled like ghost btn-sm */
.rg-link-btn {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  height: 28px;
  padding: 0 10px;
  border-radius: 6px;
  border: 1px solid var(--color-border);
  background: transparent;
  color: var(--color-text-muted);
  font: 500 12.5px/1 inherit;
  text-decoration: none;
  white-space: nowrap;
  transition: background 0.12s, color 0.12s;
}
.rg-link-btn:hover { background: var(--color-surface-elevated); color: var(--color-text); }

/* ── Review panel ── */
.rg-review-panel {
  display: flex;
  flex-direction: column;
  gap: 0.6rem;
  padding: 0.8rem 1rem;
  border-top: 1px solid var(--color-border);
  background: var(--color-surface-elevated);
}
.rg-review-actions { display: flex; flex-wrap: wrap; gap: 0.4rem; align-items: center; }

/* ── Loading / empty states ── */
.rg-loading-panel {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.75rem;
  padding: 2rem;
  color: var(--color-text-muted);
  text-align: center;
}
.rg-spinner {
  width: 1.4rem;
  height: 1.4rem;
  border: 2px solid var(--color-border);
  border-top-color: var(--color-primary);
  border-radius: 50%;
  animation: spin 0.7s linear infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }

/* ── History section ── */
.rg-history-section { display: flex; flex-direction: column; gap: 0.75rem; }
.rg-revision-title { margin: 0 0 0.2rem; font-size: 0.93rem; font-weight: 600; color: var(--color-text); }
.rg-revision-meta { margin: 0 0 1rem; font-size: 0.83rem; color: var(--color-text-muted); }
.rg-revisions-list { display: flex; flex-direction: column; gap: 0.45rem; }
.rg-revision-card {
  padding: 0.7rem 0.9rem;
  border-radius: 8px;
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  transition: background 0.12s;
}
.rg-revision-card:hover { background: var(--color-surface-elevated); }
.rg-revision-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.35rem; }
.rg-revision-number { font-size: 0.83rem; font-weight: 700; color: var(--color-primary); }
.rg-revision-date { font-size: 0.78rem; color: var(--color-text-muted); }
.rg-revision-summary { margin: 0.3rem 0; font-size: 0.83rem; color: var(--color-text); }
.rg-revision-uploader { margin: 0.2rem 0; font-size: 0.78rem; color: var(--color-text-muted); }
.rg-revision-meta-row { display: flex; gap: 1rem; margin-top: 0.4rem; font-size: 0.73rem; color: var(--color-text-muted); }
.rg-sha-label { font-family: monospace; letter-spacing: -0.02em; }

/* ── Diff / Dependencies / Snapshot sections ── */
.rg-diff-section { display: flex; flex-direction: column; }
.rg-dependencies-section { display: flex; flex-direction: column; gap: 1rem; }
.rg-section-hint { margin: 0; font-size: 0.83rem; color: var(--color-text-muted); font-style: italic; }
.rg-dep-graph { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1rem; }
.rg-dep-node { display: flex; flex-direction: column; gap: 0.5rem; }
.rg-dep-node-card {
  padding: 0.85rem;
  border-radius: 8px;
  border: 1px solid var(--color-border);
  background: var(--color-surface);
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 0.5rem;
}
.rg-dep-node--accepted { border-color: var(--color-success-border); background: var(--color-success-bg); }
.rg-dep-node--rejected,
.rg-dep-node--needs_update { border-color: var(--color-danger-border); background: var(--color-danger-bg); }
.rg-dep-node-title { font-size: 0.88rem; color: var(--color-text); }
.rg-dep-node-status {
  font-size: 0.68rem;
  padding: 0.18rem 0.45rem;
  border-radius: 4px;
  background: var(--color-surface-elevated);
  color: var(--color-text-muted);
  font-weight: 600;
  white-space: nowrap;
}
.rg-dep-prereqs {
  padding: 0.45rem 0.7rem;
  border-radius: 6px;
  background: var(--color-surface-elevated);
  border-left: 3px solid var(--color-primary);
}
.rg-dep-prereq-label {
  margin: 0 0 0.2rem;
  font-size: 0.72rem;
  color: var(--color-text-muted);
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}
.rg-dep-prereq-item { margin: 0.12rem 0; font-size: 0.78rem; color: var(--color-text-muted); padding-left: 0.4rem; }
.rg-dep-editor {
  padding: 0.9rem;
  border-radius: 8px;
  background: var(--color-success-bg);
  border: 1px solid var(--color-success-border);
}
.rg-dep-editor-label { margin: 0 0 0.2rem; font-size: 0.88rem; font-weight: 600; color: var(--color-text); }
.rg-dep-editor-hint { margin: 0 0 0.7rem; font-size: 0.78rem; color: var(--color-text-muted); }

/* Snapshot section */
.rg-snapshot-section { display: flex; flex-direction: column; gap: 1.25rem; }
.rg-snapshot-info {
  padding: 1rem;
  border-radius: 8px;
  background: var(--color-success-bg);
  border: 1px solid var(--color-success-border);
  display: grid;
  grid-template-columns: auto 1fr;
  gap: 0.45rem 1rem;
}
.rg-snapshot-label {
  margin: 0;
  font-size: 0.76rem;
  color: var(--color-text-muted);
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}
.rg-snapshot-value { margin: 0; font-size: 0.88rem; color: var(--color-text); }
.rg-snapshot-hash {
  margin: 0;
  font-size: 0.83rem;
  color: var(--color-success-text);
  font-family: monospace;
  letter-spacing: -0.02em;
}
.rg-snapshot-json-view {
  border: 1px solid var(--color-border);
  border-radius: 8px;
  padding: 0.9rem;
  cursor: pointer;
}
.rg-snapshot-json-view > summary {
  color: var(--color-primary);
  font-weight: 600;
  user-select: none;
}
.rg-snapshot-json-view > summary:hover { text-decoration: underline; }
.rg-snapshot-json {
  margin: 0.85rem 0 0;
  padding: 0.7rem;
  background: var(--color-surface-elevated);
  border-radius: 6px;
  overflow-x: auto;
  font-size: 0.73rem;
  color: var(--color-text-muted);
  line-height: 1.4;
}
.rg-snapshot-json code { font-family: monospace; }

/* ── Confirmation modal ── */
.rg-modal-backdrop {
  position: fixed;
  inset: 0;
  background: var(--color-modal-backdrop, rgba(5, 10, 20, 0.72));
  z-index: 100;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 1rem;
}
.rg-modal {
  background: var(--color-modal-bg, var(--color-surface));
  border: 1px solid var(--color-border);
  border-radius: 12px;
  padding: 1.5rem;
  max-width: 28rem;
  width: 100%;
  display: grid;
  gap: 1rem;
  box-shadow: var(--shadow-lg, 0 8px 32px rgba(0,0,0,0.25));
}
.rg-modal-header { display: flex; justify-content: space-between; align-items: center; }
.rg-modal-title { margin: 0; font-size: 1.02rem; font-weight: 700; color: var(--color-text); }
.rg-modal-body { margin: 0; line-height: 1.6; color: var(--color-text); }
.rg-modal-actions { display: flex; gap: 0.6rem; align-items: center; }

/* ── Responsive ── */
@media (max-width: 1100px) {
  .rg-workspace { grid-template-columns: 1fr; }
  .rg-checklist-card { position: static; }
}
@media (max-width: 720px) {
  .rg-head { flex-direction: column; }
  .rg-head-actions { width: 100%; justify-content: flex-end; }
  .rg-form-grid { grid-template-columns: 1fr; }
  .rg-add-evidence-header { flex-direction: column; align-items: flex-start; }
}
</style>

<style>
/* ── KEV warning banner (CRA Art. 13(2)) — unscoped so it works globally ── */
.kev-banner {
  display: flex;
  align-items: flex-start;
  gap: 0.75rem;
  padding: 1rem 1.25rem;
  background: var(--color-danger-bg, #fff1f2);
  border: 1px solid var(--color-danger-border, #fca5a5);
  border-radius: 8px;
  color: var(--color-danger-text, #991b1b);
}
.kev-banner svg { flex-shrink: 0; margin-top: 2px; }
.kev-banner-body strong { display: block; font-weight: 600; margin-bottom: 0.25rem; }
.kev-banner-body p { margin: 0; font-size: 0.88rem; }
.kev-notes { margin-top: 0.25rem !important; font-style: italic; }
</style>
