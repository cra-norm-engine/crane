<!--
  CRANE — CRA Norm Engine
  Copyright (C) 2026 Ali Mohammad Hosseini
  SPDX-License-Identifier: AGPL-3.0-or-later
  This file is part of CRANE, free software under the GNU AGPL v3.0 or later.
  See <https://www.gnu.org/licenses/>.
-->
<template>
  <section class="annex-page">

    <!-- ── Header ────────────────────────────────────────── -->
    <header class="page-header" data-guide="annex-header">
      <div>
        <h1 class="page-title">CRA requirements</h1>
        <p class="muted">Select a product, review every CRA Annex I requirement, and trace each one to risk items, rationale, and supporting artifacts.</p>
      </div>
      <div class="page-actions">
        <AppButton class="embedded-guide-trigger" variant="secondary" type="button" @click="startGuide"><span aria-hidden="true">?</span> Guide</AppButton>
        <AppButton variant="secondary" type="button" @click="showFilterModal = true">
          Filter matrix
          <span v-if="activeFilterCount > 0" class="filter-badge">{{ activeFilterCount }}</span>
        </AppButton>
      </div>
    </header>

    <!-- ── Compliance readiness overview (all products) ───── -->
    <div data-guide="annex-readiness"><ProductReadinessPanel @select="onReadinessSelect" /></div>

    <!-- ── Alerts ─────────────────────────────────────────── -->
    <transition name="fade">
      <div v-if="errorMessage" class="alert error" role="alert">{{ errorMessage }}</div>
    </transition>
    <transition name="fade">
      <div v-if="successMessage" class="alert success" role="status">{{ successMessage }}</div>
    </transition>

    <!-- ── Product selector ───────────────────────────────── -->
    <article class="card selector-card" data-guide="annex-scope">
      <div class="section-heading">
        <div>
          <h2 class="section-title">Product scope</h2>
        </div>
      </div>

      <div class="selector-grid">
        <label class="field">
          <span>Search products</span>
          <input
            v-model.trim="productQuery"
            class="input"
            type="search"
            placeholder="Search by product name or code"
          />
        </label>

        <label class="field">
          <span>Select product</span>
          <select v-model="selectedProductId" class="select">
            <option value="">Choose a product</option>
            <option v-for="product in filteredProducts" :key="product.id" :value="product.id">
              {{ product.name }} · {{ product.product_code }}
            </option>
          </select>
        </label>

        <label class="field field-full">
          <span>Select release <span class="field-hint">— requirement mappings are per release</span></span>
          <select
            v-model="selectedReleaseId"
            class="select"
            :disabled="!selectedProductId || productReleases.length === 0"
          >
            <option value="">Choose a release</option>
            <option v-for="rel in productReleases" :key="rel.id" :value="rel.id">
              v{{ rel.display_version }} · {{ formatLabel(rel.release_status) }}
            </option>
          </select>
        </label>
      </div>
    </article>

    <!-- ── Matrix list ─────────────────────────────────────── -->
    <section v-if="selectedProduct && selectedReleaseId" class="card matrix-card" data-guide="annex-matrix">
      <div class="section-heading">
        <div>
          <h2 class="section-title">{{ selectedProduct.name }}</h2>
          <p class="muted">
            v{{ selectedRelease?.display_version }} ·
            {{ filteredRows.length }} requirement{{ filteredRows.length === 1 ? "" : "s" }} shown ·
            {{ stats.finalized }} finalized · {{ stats.notFinalized }} remaining
          </p>
        </div>
        <span class="meta-pill release-status-pill" :class="`status-${selectedRelease?.release_status}`">
          {{ formatLabel(selectedRelease?.release_status) }}
        </span>
      </div>

      <!-- ── Assessment approval banner ───────────────────────── -->
      <div
        v-if="assessment"
        class="assessment-banner"
        :class="assessment.is_locked ? 'assessment-banner--approved' : 'assessment-banner--draft'"
      >
        <div class="assessment-banner-info">
          <span class="badge" :class="assessment.is_locked ? 'badge-success' : 'badge-neutral'">
            {{ assessment.is_locked ? `🔒 Approved · v${assessment.version}` : "Draft" }}
          </span>
          <span v-if="assessment.is_locked" class="assessment-meta">
            Approved by <strong>{{ assessment.approved_by_name || "—" }}</strong>
            <template v-if="assessment.approved_at"> on {{ formatDateTime(assessment.approved_at) }}</template>
          </span>
          <span v-else class="assessment-meta">
            Finalise the assessment to lock it and allow the release gate to be approved.
          </span>
          <span
            v-if="!assessment.is_locked && assessment.unfinalized_codes.length"
            class="assessment-warn"
          >
            {{ assessment.unfinalized_codes.length }} requirement(s) not yet finalized.
          </span>
        </div>
        <div class="assessment-banner-actions">
          <AppButton
            v-if="!assessment.is_locked"
            variant="primary"
            size="sm"
            :disabled="!assessment.can_approve || assessmentBusy"
            :title="approveButtonTitle"
            @click="approveAssessment"
          >
            {{ assessmentBusy ? "Approving…" : "Approve assessment" }}
          </AppButton>
          <AppButton
            v-else
            variant="secondary"
            size="sm"
            :disabled="assessmentBusy"
            title="Reopen for amendment (creates a new version on re-approval)"
            @click="reopenAssessment"
          >
            {{ assessmentBusy ? "Reopening…" : "Amend" }}
          </AppButton>
        </div>
      </div>

      <!-- Coverage bar -->
      <div class="release-coverage-bar">
        <div class="coverage-numbers">
          <strong>{{ stats.finalized }}</strong> / {{ filteredRows.length }} requirements finalized
          <span class="coverage-pct" :class="coveragePct >= 80 ? 'pct-good' : coveragePct >= 40 ? 'pct-partial' : 'pct-low'">
            {{ coveragePct }}%
          </span>
          <button
            v-if="stats.notFinalized > 0"
            type="button"
            class="needs-decision-chip"
            :class="{ active: filters.finalization === 'not_finalized' }"
            :title="filters.finalization === 'not_finalized' ? 'Show all requirements' : 'Show only requirements that are not finalized'"
            @click="toggleNotFinalizedFilter"
          >
            <span class="pill-dot" aria-hidden="true" />
            {{ stats.notFinalized }} not finalized
          </button>
        </div>
        <div class="progress-track">
          <div
            class="progress-fill"
            :class="coveragePct >= 80 ? 'fill-good' : coveragePct >= 40 ? 'fill-partial' : 'fill-low'"
            :style="{ width: `${coveragePct}%` }"
          />
        </div>
      </div>

      <!-- Loading skeleton -->
      <div v-if="loading" class="state-block">
        <div v-for="i in 7" :key="i" class="skeleton-row"></div>
      </div>

      <!-- Empty state -->
      <div v-else-if="filteredRows.length === 0" class="state-block">
        <h3>No requirements match these filters</h3>
        <p class="muted">Try changing the search term or status filter.</p>
      </div>

      <!-- Compact row list -->
      <div v-else class="matrix-list">
        <div
          v-for="row in filteredRows"
          :key="row.annex_requirement.id"
          class="matrix-row-wrapper"
        >
          <!-- Compact clickable row -->
          <button
            class="matrix-row"
            type="button"
            :class="{
              active: selectedRequirementId === row.annex_requirement.id,
              'needs-decision': row.applicability === 'needs_decision',
            }"
            @click="openDetail(row)"
          >
            <!-- Code + title -->
            <div class="row-left">
              <span class="requirement-code">{{ row.annex_requirement.code }}</span>
              <strong class="row-title">{{ row.annex_requirement.title }}</strong>
            </div>

            <!-- Pills + expand button -->
            <div class="row-right">
              <span
                class="meta-pill applicability-pill"
                :class="`app-${row.applicability}`"
              >
                <span v-if="row.applicability === 'needs_decision'" class="pill-dot" aria-hidden="true" />
                {{ formatApplicability(row.applicability) }}
              </span>
              <span
                v-if="row.applicability === 'applicable'"
                class="meta-pill"
                :class="`progress-${row.implementation_status}`"
              >
                {{ formatLabel(row.implementation_status) }}
              </span>
              <span
                class="meta-pill"
                :class="row.finalized ? 'finalized-pill' : 'unfinalized-pill'"
              >
                {{ row.finalized ? "✓ Finalized" : "In progress" }}
              </span>
              <span class="mini-stat">{{ rowRiskCount(row) }} risks</span>
              <span class="mini-stat">{{ row.artifacts.length }} artifacts</span>

              <!-- Expand-description toggle (does not open modal) -->
              <span
                class="expand-btn"
                role="button"
                tabindex="0"
                :title="expandedRowIds.has(row.annex_requirement.id) ? 'Collapse description' : 'Show description'"
                :aria-expanded="expandedRowIds.has(row.annex_requirement.id)"
                @click.stop="toggleExpand(row.annex_requirement.id)"
                @keydown.enter.stop.prevent="toggleExpand(row.annex_requirement.id)"
              >
                <svg
                  viewBox="0 0 16 16"
                  width="14"
                  height="14"
                  fill="none"
                  stroke="currentColor"
                  stroke-width="2"
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  aria-hidden="true"
                  :class="{ 'chevron-open': expandedRowIds.has(row.annex_requirement.id) }"
                >
                  <polyline points="3,5 8,11 13,5" />
                </svg>
              </span>
            </div>
          </button>

          <!-- Inline description panel (expand-in-place) -->
          <transition name="expand">
            <div
              v-if="expandedRowIds.has(row.annex_requirement.id)"
              class="row-description-panel"
            >
              <p>{{ row.annex_requirement.description }}</p>
            </div>
          </transition>
        </div>
      </div>
    </section>

    <!-- ── Empty product selection state ─────────────────── -->
    <section v-else class="card state-block">
      <h2 class="section-title">Select a product to start</h2>
      <p class="muted">
        Select a product and release to assess every CRA Annex I requirement for that specific version.
      </p>
    </section>

    <!-- ── Filter modal ────────────────────────────────────── -->
    <AppModal v-model="showFilterModal" title="Filter matrix" size="sm">
      <div class="filter-grid">
        <label class="field">
          <span>Annex part</span>
          <select v-model="filters.annexPart" class="select">
            <option value="">All parts</option>
            <option value="part_i">Part I</option>
            <option value="part_ii">Part II</option>
          </select>
        </label>

        <label class="field">
          <span>Status</span>
          <select v-model="filters.status" class="select">
            <option value="">All statuses</option>
            <option value="unmapped">Unmapped</option>
            <option v-for="status in implementationStatuses" :key="status" :value="status">
              {{ formatLabel(status) }}
            </option>
          </select>
        </label>

        <label class="field field-full">
          <span>Search requirements</span>
          <input
            v-model.trim="filters.search"
            class="input"
            type="search"
            placeholder="Search requirement text, risk title, engineering ref, notes, or artifacts"
          />
        </label>
      </div>

      <template #footer>
        <AppButton
          variant="secondary"
          type="button"
          @click="resetFilters(); showFilterModal = false"
        >
          Clear all
        </AppButton>
        <AppButton variant="primary" type="button" @click="showFilterModal = false">Apply</AppButton>
      </template>
    </AppModal>

    <!-- ── Requirement detail modal ────────────────────────── -->
    <AppModal
      v-if="selectedRow"
      v-model="showDetailModal"
      :title="`${selectedRow.annex_requirement.code} — ${selectedRow.annex_requirement.title}`"
      size="lg"
    >
      <div class="detail-modal-body">

        <!-- Locked notice -->
        <div v-if="isLocked" class="alert info detail-lock-note" role="status">
          🔒 This assessment is approved (v{{ assessment?.version }}) and read-only.
          Use <strong>Amend</strong> on the matrix to make changes.
        </div>

        <!-- Compact status header -->
        <div class="detail-status-head">
          <span class="meta-pill" :class="`app-${selectedRow.applicability}`">
            {{ formatApplicability(selectedRow.applicability) }}
          </span>
          <span
            v-if="selectedRow.applicability === 'applicable'"
            class="meta-pill"
            :class="`progress-${selectedRow.implementation_status}`"
          >
            {{ formatLabel(selectedRow.implementation_status) }}
          </span>
          <span
            class="meta-pill"
            :class="selectedRow.finalized ? 'finalized-pill' : 'unfinalized-pill'"
          >
            {{ selectedRow.finalized ? "✓ Finalized" : "In progress" }}
          </span>
        </div>

        <!-- Tab strip -->
        <div class="detail-tabs" role="tablist">
          <button
            v-for="tab in detailTabs"
            :key="tab.id"
            type="button"
            role="tab"
            class="detail-tab"
            :class="{ active: activeTab === tab.id }"
            :aria-selected="activeTab === tab.id"
            @click="activeTab = tab.id"
          >
            {{ tab.label }}
            <span v-if="tab.count !== undefined" class="detail-tab-count">{{ tab.count }}</span>
          </button>
        </div>

        <!-- ── TAB 1: Applicability assessment ───────────────── -->
        <div v-show="activeTab === 'applicability'" class="detail-tab-panel" role="tabpanel">
          <p class="detail-description">{{ selectedRow.annex_requirement.description }}</p>

          <section class="detail-section">
            <div class="section-heading tight">
              <div>
                <h3 class="section-title">Applicability decision</h3>
                <p class="muted">Decide explicitly whether this requirement applies to the selected product.</p>
              </div>
            </div>
            <form id="applicability-form" class="editor-grid" @submit.prevent="saveApplicabilityDecision">
              <label class="field">
                <span>Decision</span>
                <select v-model="applicabilityForm.applicability_decision" class="select" :disabled="isLocked">
                  <option v-for="option in applicabilityDecisions" :key="option" :value="option">
                    {{ formatApplicabilityDecision(option) }}
                  </option>
                </select>
              </label>

              <label class="field field-full">
                <span>Rationale</span>
                <textarea
                  v-model.trim="applicabilityForm.rationale"
                  class="textarea"
                  rows="3"
                  :disabled="isLocked"
                  placeholder="Explain why this requirement applies or why it is not applicable for this product."
                />
              </label>

              <div v-if="!isLocked" class="editor-actions">
                <AppButton variant="primary" type="submit" :disabled="busy">
                  {{ busy ? "Saving..." : "Save decision" }}
                </AppButton>
              </div>
            </form>
          </section>
        </div>

        <!-- ── TAB 2: Justification by risk ──────────────────── -->
        <div v-show="activeTab === 'risk'" class="detail-tab-panel" role="tabpanel">
          <section class="trace-section">
            <div class="section-heading tight">
              <div>
                <h3 class="section-title">Justification by risk</h3>
                <p class="muted">
                  Link the risk item(s) this requirement addresses and justify how — this is the
                  traceability record and the basis of the compliance report.
                </p>
              </div>
              <AppButton v-if="!isLocked" variant="secondary" type="button" @click="startCreateTrace">
                New justification
              </AppButton>
            </div>

            <!-- Report-style summary of all risk justifications -->
            <div v-if="rowRisks(selectedRow).length" class="risk-trace-list risk-summary">
              <article v-for="risk in rowRisks(selectedRow)" :key="`sum-${risk.id}`" class="risk-trace-card">
                <div class="risk-trace-head">
                  <strong>{{ risk.title }}</strong>
                  <span class="badge" :class="riskLevelBadge(risk.risk_level)">
                    {{ formatLabel(risk.risk_level) }}
                  </span>
                </div>
                <div class="risk-trace-meta">
                  <span class="mini-stat">Status: {{ formatLabel(risk.status) }}</span>
                  <span v-if="risk.residual_risk_level" class="mini-stat">
                    Residual: {{ formatLabel(risk.residual_risk_level) }}
                  </span>
                </div>
                <ul class="risk-trace-vias">
                  <li
                    v-for="trace in tracesForRisk(selectedRow, risk.id)"
                    :key="trace.id"
                    class="risk-trace-via"
                  >
                    <template v-if="trace.evidence_summary">{{ trace.evidence_summary }}</template>
                    <em v-else class="muted">No justification note</em>
                  </li>
                </ul>
              </article>
            </div>

            <div
              v-if="!selectedRow.artifact_traceability_available"
              class="alert warning"
              role="status"
            >
              Artifact linking is temporarily unavailable because the database migration for
              requirement-to-artifact links has not been applied yet. The matrix still works for
              risk-based trace records and justification notes.
            </div>

            <div v-if="selectedRow.trace_records.length === 0" class="state-block compact">
              <h4>No risk justification yet</h4>
              <p class="muted">
                Link the risk(s) this requirement addresses and justify how. A risk justification
                is required to finalize the requirement — even when it is not applicable.
              </p>
            </div>

            <div v-else class="section-heading tight detail-subhead">
              <h4 class="section-title">Justification records</h4>
            </div>
            <div v-if="selectedRow.trace_records.length" class="trace-list">
              <article
                v-for="trace in selectedRow.trace_records"
                :key="trace.id"
                class="trace-card"
                :class="{ selected: selectedTraceId === trace.id }"
              >
                <button class="trace-top" type="button" :disabled="isLocked" @click="editTrace(trace)">
                  <div>
                    <strong>{{ trace.risk_item?.title || "Direct requirement rationale" }}</strong>
                    <p class="trace-subline">
                      {{ formatLabel(trace.sdl_activity) }}
                      <span v-if="trace.engineering_requirement_ref">
                        · {{ trace.engineering_requirement_ref }}
                      </span>
                    </p>
                  </div>
                </button>

                <p v-if="trace.evidence_summary" class="trace-notes">{{ trace.evidence_summary }}</p>

                <div class="artifact-strip">
                  <article
                    v-for="artifact in trace.artifacts"
                    :key="artifact.id"
                    class="artifact-card"
                  >
                    <div class="artifact-info">
                      <strong>{{ artifact.title }}</strong>
                      <small>{{ formatLabel(artifact.artifact_type) }}</small>
                    </div>
                    <div class="artifact-actions-inline">
                      <AppButton
                        v-if="artifact.latest_revision?.storage_path"
                        variant="secondary"
                        size="sm"
                        @click="downloadArtifact(artifact)"
                      >
                        Download
                      </AppButton>
                      <a
                        v-else-if="artifact.latest_revision?.external_url"
                        class="button secondary small-button link-button"
                        :href="artifact.latest_revision.external_url"
                        target="_blank"
                        rel="noreferrer"
                      >
                        Open
                      </a>
                    </div>
                  </article>
                </div>

                <div v-if="!isLocked" class="trace-actions">
                  <AppButton variant="secondary" :disabled="busy" @click="editTrace(trace)">
                    Edit
                  </AppButton>
                  <AppButton variant="danger" :disabled="busy" @click="removeTrace(trace.id)">
                    Delete
                  </AppButton>
                </div>
              </article>
            </div>

            <!-- Risk justification editor (hidden when locked) -->
            <section v-if="!isLocked" class="editor-card">
              <div class="section-heading tight">
                <div>
                  <h3 class="section-title">{{ editingExisting ? "Edit justification" : "New risk justification" }}</h3>
                  <p class="muted">
                    Pick the risk this requirement addresses and explain how it is addressed (or,
                    for a non-applicable requirement, why the risk does not apply).
                  </p>
                </div>
              </div>

              <form class="editor-grid" @submit.prevent="saveTrace">
                <label class="field">
                  <span>Risk item <span class="field-hint">(required)</span></span>
                  <select v-model="traceForm.risk_item_id" class="select" required>
                    <option value="">Select a risk item…</option>
                    <option v-for="risk in productRiskItems" :key="risk.id" :value="risk.id">
                      {{ risk.title }} · {{ formatLabel(risk.risk_level) }}
                    </option>
                  </select>
                </label>

                <label class="field">
                  <span>SDL activity</span>
                  <select v-model="traceForm.sdl_activity" class="select">
                    <option v-for="activity in sdlActivities" :key="activity" :value="activity">
                      {{ formatLabel(activity) }}
                    </option>
                  </select>
                </label>

                <label class="field">
                  <span>Engineering reference <span class="field-hint">(optional)</span></span>
                  <input
                    v-model.trim="traceForm.engineering_requirement_ref"
                    class="input"
                    type="text"
                    placeholder="e.g. ENG-SEC-014"
                  />
                </label>

                <label class="field field-full">
                  <span>Justification</span>
                  <textarea
                    v-model.trim="traceForm.evidence_summary"
                    class="textarea"
                    rows="4"
                    placeholder="Explain how this requirement addresses the selected risk, or why the risk is not applicable."
                  />
                </label>

                <div class="editor-actions">
                  <AppButton variant="primary" type="submit" :disabled="busy || !selectedRow || !traceForm.risk_item_id">
                    {{ busy ? "Saving..." : editingExisting ? "Save changes" : "Add justification" }}
                  </AppButton>
                  <AppButton variant="secondary" type="button" :disabled="busy" @click="resetEditor">
                    Clear editor
                  </AppButton>
                </div>
              </form>
            </section>
          </section>
        </div>

        <!-- ── TAB 3: Linked artifacts ───────────────────────── -->
        <div v-show="activeTab === 'artifacts'" class="detail-tab-panel" role="tabpanel">
          <section class="detail-section">
            <div class="section-heading tight">
              <div>
                <h3 class="section-title">Linked artifacts</h3>
                <p class="muted">
                  Evidence artifacts attached to this requirement. Applicable requirements need at
                  least one linked artifact to be finalized.
                </p>
              </div>
            </div>

            <!-- Currently linked artifacts -->
            <div v-if="selectedRow.artifacts.length === 0" class="state-block compact">
              <p class="muted">No artifacts linked yet. Select one or more below.</p>
            </div>
            <div v-else class="compact-list">
              <article
                v-for="artifact in selectedRow.artifacts"
                :key="artifact.id"
                class="compact-item compact-item-actions"
              >
                <div class="artifact-info">
                  <strong>{{ artifact.title }}</strong>
                  <span class="muted">{{ formatLabel(artifact.artifact_type) }}</span>
                </div>
                <div class="artifact-actions-inline">
                  <AppButton
                    v-if="artifact.latest_revision?.storage_path"
                    variant="secondary"
                    size="sm"
                    @click="downloadArtifact(artifact)"
                  >
                    Download
                  </AppButton>
                  <a
                    v-else-if="artifact.latest_revision?.external_url"
                    class="button secondary small-button link-button"
                    :href="artifact.latest_revision.external_url"
                    target="_blank"
                    rel="noreferrer"
                  >
                    Open
                  </a>
                </div>
              </article>
            </div>

            <!-- Artifact selector (manage links here) -->
            <div v-if="!isLocked" class="artifact-link-editor">
              <div class="section-heading tight detail-subhead">
                <h4 class="section-title">Select artifacts</h4>
              </div>
              <div
                v-if="!selectedRow.artifact_traceability_available"
                class="artifact-selection-note"
              >
                Artifact linking is unavailable until the latest database migration is applied.
              </div>
              <div v-else-if="selectedRow.applicability === 'needs_decision'" class="artifact-selection-note">
                Decide applicability first (Applicability tab) before linking artifacts.
              </div>
              <div v-else-if="productArtifacts.length === 0" class="artifact-selection-note">
                No product artifacts found yet. Upload artifacts in the release workflow first.
              </div>
              <div v-else class="artifact-selector-grid">
                <label
                  v-for="artifact in productArtifacts"
                  :key="`link-${artifact.id}`"
                  class="artifact-option"
                  :class="{ selected: isArtifactLinked(artifact.id) }"
                >
                  <input
                    type="checkbox"
                    :checked="isArtifactLinked(artifact.id)"
                    :disabled="busy"
                    @change="toggleRequirementArtifact(artifact.id)"
                  />
                  <div class="artifact-option-copy">
                    <strong>{{ artifact.title }}</strong>
                    <span>{{ formatLabel(artifact.artifact_type) }}</span>
                  </div>
                </label>
              </div>
            </div>
          </section>
        </div>

        <!-- ── TAB 4: Implementation status ──────────────────── -->
        <div v-show="activeTab === 'implementation'" class="detail-tab-panel" role="tabpanel">
          <section class="detail-section">
            <div class="section-heading tight">
              <div>
                <h3 class="section-title">Implementation status</h3>
                <p class="muted">
                  Track delivery of this requirement. An applicable requirement must reach
                  <strong>Validated</strong> (with a risk justification and a linked artifact) to be
                  finalized. Not-applicable requirements do not need an implementation status.
                </p>
              </div>
            </div>

            <div v-if="selectedRow.applicability === 'not_applicable'" class="state-block compact">
              <p class="muted">
                This requirement is marked <strong>Not applicable</strong> — no implementation is
                required. It is finalized once a risk justification is recorded.
              </p>
            </div>

            <template v-else>
              <div class="impl-status-picker">
                <button
                  v-for="opt in progressStatuses"
                  :key="opt"
                  type="button"
                  class="impl-status-option"
                  :class="{ active: selectedRow.implementation_status === opt }"
                  :disabled="isLocked || busy || selectedRow.applicability === 'needs_decision'"
                  @click="setImplementationStatus(opt)"
                >
                  <span class="impl-status-dot" :class="`progress-dot-${opt}`" />
                  {{ formatLabel(opt) }}
                </button>
              </div>

              <p v-if="selectedRow.applicability === 'needs_decision'" class="assessment-warn">
                Decide applicability first (Applicability assessment tab).
              </p>

              <!-- Finalization checklist for applicable requirements -->
              <ul class="finalize-checklist">
                <li :class="{ done: selectedRow.applicability !== 'needs_decision' }">
                  <span class="check-mark">{{ selectedRow.applicability !== 'needs_decision' ? '✓' : '○' }}</span>
                  Applicability decided
                </li>
                <li :class="{ done: rowRisks(selectedRow).length > 0 }">
                  <span class="check-mark">{{ rowRisks(selectedRow).length > 0 ? '✓' : '○' }}</span>
                  At least one risk justification
                </li>
                <li :class="{ done: selectedRow.artifacts.length > 0 }">
                  <span class="check-mark">{{ selectedRow.artifacts.length > 0 ? '✓' : '○' }}</span>
                  At least one linked artifact
                </li>
                <li :class="{ done: selectedRow.implementation_status === 'validated' }">
                  <span class="check-mark">{{ selectedRow.implementation_status === 'validated' ? '✓' : '○' }}</span>
                  Implementation validated
                </li>
              </ul>
            </template>

            <div class="finalize-banner" :class="selectedRow.finalized ? 'is-final' : 'not-final'">
              {{ selectedRow.finalized ? "✓ This requirement is finalized." : "Not finalized yet." }}
            </div>
          </section>
        </div>

      </div>
    </AppModal>

  </section>
</template>

<script setup lang="ts">
import { computed, nextTick, onMounted, reactive, ref, watch } from "vue";
import { useRoute } from "vue-router";

import AppModal from "@/components/AppModal.vue";
import AppButton from "@/components/AppButton.vue";
import ProductReadinessPanel from "@/components/ProductReadinessPanel.vue";
import { artifactService } from "@/services/artifact-service";
import { productReleaseService } from "@/services/product-release-service";
import { productService } from "@/services/product-service";
import { requirementMappingService } from "@/services/requirement-mapping-service";
import { riskAssessmentService } from "@/services/risk-assessment-service";
import { riskItemService } from "@/services/risk-item-service";
import type { AnnexPart } from "@/types/annex-requirement";
import type { ArtifactListRead } from "@/types/artifact";
function startGuide(): void { window.dispatchEvent(new Event("crane-guide-start")); }
import type { ProductSummaryRead } from "@/types/product";
import type {
  ProductRequirementDecisionUpdate,
  ProductRequirementMatrixRowRead,
  RequirementApplicabilityDecision,
  RequirementAssessmentRead,
  RequirementImplementationStatus,
  RequirementProgressStatus,
  RequirementMappingCreate,
  RequirementMappingMatrixRead,
  RequirementMappingUpdate,
  SdlActivity,
} from "@/types/requirement-mapping";
import type { RiskAssessmentRead } from "@/types/risk-assessment";
import type { RiskItemRead, RiskItemSummaryRead } from "@/types/risk-item";
import type { ProductReleaseRead } from "@/types/release-gate";

const loading = ref(false);
const busy = ref(false);
const errorMessage = ref("");
const successMessage = ref("");

// Release-level requirement assessment approval state.
const assessment = ref<RequirementAssessmentRead | null>(null);
const assessmentBusy = ref(false);
// Convenience: is the matrix locked (assessment approved) → forms become read-only.
const isLocked = computed(() => assessment.value?.is_locked === true);

// Tooltip explaining why the Approve button is enabled/disabled.
const approveButtonTitle = computed(() => {
  const a = assessment.value;
  if (!a) return "";
  if (a.can_approve) return "Approve and lock this assessment";
  if (a.unfinalized_codes.length) {
    return `Finalize all requirements first — ${a.unfinalized_codes.length} remaining`;
  }
  return "Finalize all requirements first";
});

const products = ref<ProductSummaryRead[]>([]);
const matrixRows = ref<ProductRequirementMatrixRowRead[]>([]);
const productRiskItems = ref<RiskItemRead[]>([]);
const productArtifacts = ref<ArtifactListRead[]>([]);

const productQuery = ref("");
const selectedProductId = ref("");
const selectedReleaseId = ref("");

/**
 * Readiness panel release clicked → open that specific release's matrix.
 * Sets the product (which loads its releases via the watcher), waits for the
 * releases to arrive, then selects the requested release. Scrolls the matrix
 * into view so the deep-dive is visible below the overview.
 */
async function onReadinessSelect(productId: string, releaseId: string): Promise<void> {
  if (selectedProductId.value !== productId) {
    selectedProductId.value = productId;
    // The product watcher loads releases asynchronously; wait for it.
    await nextTick();
    await loadProductContext(productId);
  }
  selectedReleaseId.value = releaseId;
  await nextTick();
  document.querySelector(".matrix-card")?.scrollIntoView({ behavior: "smooth", block: "start" });
}
const selectedRequirementId = ref("");
const selectedTraceId = ref("");

/* ── Release-level data ───────────────────────────── */
const productReleases = ref<ProductReleaseRead[]>([]);

/* ── Modal visibility ─────────────────────────────── */
const showFilterModal = ref(false);
const showDetailModal = ref(false);

/* ── Detail modal tabs ────────────────────────────── */
type DetailTabId = "applicability" | "risk" | "artifacts" | "implementation";
const activeTab = ref<DetailTabId>("applicability");

/* ── Expanded description rows ────────────────────── */
const expandedRowIds = ref(new Set<string>());

const filters = reactive({
  annexPart: "" as AnnexPart | "",
  /* "unmapped" is a UI-only sentinel for rows with no trace record */
  status: "" as RequirementImplementationStatus | "unmapped" | "",
  /* quick filter for the "not finalized" chip */
  finalization: "" as "not_finalized" | "",
  search: "",
});

const traceForm = reactive({
  id: "",
  risk_item_id: "",
  implementation_status: "planned" as RequirementImplementationStatus,
  sdl_activity: "requirements" as SdlActivity,
  engineering_requirement_ref: "",
  evidence_summary: "",
});

const applicabilityForm = reactive({
  applicability_decision: "undecided" as RequirementApplicabilityDecision,
  rationale: "",
});

const implementationStatuses: RequirementImplementationStatus[] = [
  "planned",
  "in_progress",
  "implemented",
  "verified",
  "not_applicable",
];

// Per-requirement implementation progress (the new model).
const progressStatuses: RequirementProgressStatus[] = ["planned", "implemented", "validated"];

const applicabilityDecisions: RequirementApplicabilityDecision[] = [
  "undecided",
  "applicable",
  "not_applicable",
];

const sdlActivities: SdlActivity[] = [
  "requirements",
  "design",
  "implementation",
  "verification",
  "validation",
  "vulnerability_management",
  "documentation",
  "post_market",
];

/* ── Computed ─────────────────────────────────────── */

const filteredProducts = computed(() => {
  const term = productQuery.value.trim().toLowerCase();
  if (!term) return products.value;
  return products.value.filter((product: ProductSummaryRead) =>
    [product.name, product.product_code].some((value: string) => value.toLowerCase().includes(term)),
  );
});

const selectedProduct = computed(
  () => products.value.find((product: ProductSummaryRead) => product.id === selectedProductId.value) ?? null,
);

const filteredRows = computed(() => {
  const term = filters.search.trim().toLowerCase();
  return [...matrixRows.value]
    .sort((a: ProductRequirementMatrixRowRead, b: ProductRequirementMatrixRowRead) =>
      compareRequirementCodes(a.annex_requirement.code, b.annex_requirement.code),
    )
    .filter((row: ProductRequirementMatrixRowRead) => {
      if (filters.annexPart && row.annex_requirement.annex_part !== filters.annexPart) {
        return false;
      }
      /* "unmapped" = rows where no trace record exists yet */
      if (filters.status === "unmapped") {
        if (row.overall_status) return false;
      } else if (filters.status && row.overall_status !== filters.status) {
        return false;
      }
      if (filters.finalization === "not_finalized" && row.finalized) {
        return false;
      }
      if (!term) return true;

      const haystack = [
        row.annex_requirement.code,
        row.annex_requirement.title,
        row.annex_requirement.description,
        ...row.risk_items.map((risk: RiskItemSummaryRead) => risk.title),
        ...row.artifacts.map((artifact: ArtifactListRead) => artifact.title),
        ...row.engineering_requirement_refs,
        ...row.notes,
      ]
        .join(" ")
        .toLowerCase();

      return haystack.includes(term);
    });
});

const selectedRow = computed(
  () =>
    filteredRows.value.find((row: ProductRequirementMatrixRowRead) => row.annex_requirement.id === selectedRequirementId.value) ??
    matrixRows.value.find((row: ProductRequirementMatrixRowRead) => row.annex_requirement.id === selectedRequirementId.value) ??
    null,
);

const editingExisting = computed(() => Boolean(traceForm.id));

// Tabs for the requirement detail modal, with live counts on the relevant ones.
const detailTabs = computed(() => {
  const row = selectedRow.value;
  return [
    { id: "applicability" as DetailTabId, label: "Applicability", count: undefined as number | undefined },
    {
      id: "risk" as DetailTabId,
      label: "Justification by risk",
      count: row ? rowRiskCount(row) : 0,
    },
    {
      id: "artifacts" as DetailTabId,
      label: "Linked artifacts",
      count: row?.artifacts.length ?? 0,
    },
    { id: "implementation" as DetailTabId, label: "Implementation", count: undefined as number | undefined },
  ];
});

const stats = computed(() => ({
  finalized: filteredRows.value.filter((row: ProductRequirementMatrixRowRead) => row.finalized).length,
  // Count from the full set so the "not finalized" chip always reflects the true
  // total even while the chip's own filter is active.
  notFinalized: matrixRows.value.filter((row: ProductRequirementMatrixRowRead) => !row.finalized).length,
  needsDecision: matrixRows.value.filter((row: ProductRequirementMatrixRowRead) => row.applicability === "needs_decision").length,
}));

/** Number of active non-empty filters — shown as a badge on the Filter button. */
const activeFilterCount = computed(() => {
  let count = 0;
  if (filters.annexPart) count++;
  if (filters.status) count++;
  if (filters.finalization) count++;
  if (filters.search) count++;
  return count;
});

/** Toggle the "not finalized" quick filter from the coverage chip. */
function toggleNotFinalizedFilter(): void {
  filters.finalization = filters.finalization === "not_finalized" ? "" : "not_finalized";
}

/** The selected release object, used for display. */
const selectedRelease = computed(
  () => productReleases.value.find((r: ProductReleaseRead) => r.id === selectedReleaseId.value) ?? null,
);

/** Percentage of visible requirements that are finalized for the current release. */
const coveragePct = computed(() => {
  const total = filteredRows.value.length;
  if (total === 0) return 0;
  return Math.round((stats.value.finalized / total) * 100);
});

/* ── Helpers ──────────────────────────────────────── */

/**
 * Unique risks linked to a requirement. Primarily uses the row's `risk_items`,
 * but falls back to risks carried on individual trace records so the count is
 * never 0 when a trace is in fact linked to a risk.
 */
function rowRisks(row: ProductRequirementMatrixRowRead): RiskItemSummaryRead[] {
  const byId = new Map<string, RiskItemSummaryRead>();
  for (const risk of row.risk_items) byId.set(risk.id, risk);
  for (const trace of row.trace_records) {
    if (trace.risk_item) byId.set(trace.risk_item.id, trace.risk_item);
  }
  return [...byId.values()];
}

function rowRiskCount(row: ProductRequirementMatrixRowRead): number {
  return rowRisks(row).length;
}

/** Trace records on a requirement that link to the given risk id. */
function tracesForRisk(
  row: ProductRequirementMatrixRowRead,
  riskId: string,
): RequirementMappingMatrixRead[] {
  return row.trace_records.filter((trace) => trace.risk_item?.id === riskId);
}

/** Map a risk level to a semantic badge class. */
function riskLevelBadge(level: string): string {
  if (level === "critical") return "badge-danger";
  if (level === "high") return "badge-danger";
  if (level === "medium") return "badge-warning";
  if (level === "low") return "badge-success";
  return "badge-neutral";
}

function compareRequirementCodes(a: string, b: string): number {
  const aMatch = a.match(/PART-(I|II)-(\d+)/);
  const bMatch = b.match(/PART-(I|II)-(\d+)/);
  if (!aMatch || !bMatch) return a.localeCompare(b);
  const partDiff = aMatch[1].localeCompare(bMatch[1]);
  if (partDiff !== 0) return partDiff;
  return Number(aMatch[2]) - Number(bMatch[2]);
}

function formatLabel(value?: string | null): string {
  if (!value) return "—";
  return value
    .split("_")
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(" ");
}

function formatApplicability(value: ProductRequirementMatrixRowRead["applicability"]): string {
  if (value === "not_applicable") return "Not applicable";
  if (value === "applicable") return "Applicable";
  return "Needs decision";
}

function formatApplicabilityDecision(value: RequirementApplicabilityDecision): string {
  return formatLabel(value);
}

/* ── UI interaction ───────────────────────────────── */

function resetFilters(): void {
  filters.annexPart = "";
  filters.status = "";
  filters.finalization = "";
  filters.search = "";
}

function resetEditor(): void {
  traceForm.id = "";
  traceForm.risk_item_id = "";
  traceForm.implementation_status = "planned";
  traceForm.sdl_activity = "requirements";
  traceForm.engineering_requirement_ref = "";
  traceForm.evidence_summary = "";
  applicabilityForm.applicability_decision = "undecided";
  applicabilityForm.rationale = "";
  selectedTraceId.value = "";
}

/** Toggle the inline description panel for a row without opening the detail modal. */
function toggleExpand(reqId: string): void {
  const next = new Set(expandedRowIds.value);
  if (next.has(reqId)) {
    next.delete(reqId);
  } else {
    next.add(reqId);
  }
  expandedRowIds.value = next;
}

/** Populate the detail forms from the selected row. */
function selectRow(row: ProductRequirementMatrixRowRead): void {
  selectedRequirementId.value = row.annex_requirement.id;
  applicabilityForm.applicability_decision = row.applicability_decision;
  applicabilityForm.rationale = row.applicability_rationale ?? "";
  if (row.trace_records.length > 0) {
    const matchingTrace =
      row.trace_records.find((trace) => trace.id === selectedTraceId.value) ?? row.trace_records[0];
    editTrace(matchingTrace);
    return;
  }
  resetEditor();
}

/** Open the requirement detail modal for the given row. */
function openDetail(row: ProductRequirementMatrixRowRead): void {
  selectRow(row);
  activeTab.value = "applicability";
  showDetailModal.value = true;
}

function startCreateTrace(): void {
  resetEditor();
}

function editTrace(trace: RequirementMappingMatrixRead): void {
  selectedTraceId.value = trace.id;
  traceForm.id = trace.id;
  traceForm.risk_item_id = trace.risk_item_id ?? "";
  traceForm.implementation_status = trace.implementation_status;
  traceForm.sdl_activity = trace.sdl_activity;
  traceForm.engineering_requirement_ref = trace.engineering_requirement_ref ?? "";
  traceForm.evidence_summary = trace.evidence_summary ?? "";
}

/** Whether an artifact is currently linked to the selected requirement. */
function isArtifactLinked(artifactId: string): boolean {
  return selectedRow.value?.artifacts.some((a) => a.id === artifactId) ?? false;
}

/**
 * Attach/detach an artifact at the requirement level (Linked artifacts tab).
 *
 * Artifacts are stored against a requirement's justification record. To keep the
 * artifact concern fully separate from the risk UI, we resolve the underlying
 * record(s) here:
 *   - detach: remove the artifact from every justification record that carries it.
 *   - attach: add it to the requirement's first justification record.
 * A justification record always exists for any requirement that can have
 * artifacts (applicable requirements require at least one risk justification).
 */
async function toggleRequirementArtifact(artifactId: string): Promise<void> {
  const row = selectedRow.value;
  if (!row || !selectedReleaseId.value) return;

  const linkedTraces = row.trace_records.filter((t) =>
    t.artifacts.some((a) => a.id === artifactId),
  );

  busy.value = true;
  errorMessage.value = "";
  successMessage.value = "";
  try {
    if (linkedTraces.length > 0) {
      // Detach from every record that holds it.
      for (const trace of linkedTraces) {
        await requirementMappingService.detachArtifact(trace.id, artifactId);
      }
    } else {
      const target = row.trace_records[0];
      if (!target) {
        errorMessage.value =
          "Add a risk justification first (Justification by risk tab) before linking artifacts.";
        return;
      }
      await requirementMappingService.attachArtifact(target.id, { artifact_id: artifactId });
    }
    await refreshRow(row.annex_requirement.id);
    await loadAssessment(selectedReleaseId.value);
  } catch (error: any) {
    errorMessage.value = error?.message ?? "Failed to update linked artifacts.";
  } finally {
    busy.value = false;
  }
}

/* ── Data loading ─────────────────────────────────── */

async function loadProducts(): Promise<void> {
  products.value = await productService.list();
}

async function loadProductContext(productId: string): Promise<void> {
  const [artifacts, releases] = await Promise.all([
    artifactService.list({ product_id: productId }),
    productReleaseService.list(productId),
    loadProductRiskItems(productId),
  ]);
  productArtifacts.value = artifacts;
  productReleases.value = releases;
}

/**
 * Load the product's risk items (for the trace editor's risk-item dropdown).
 * Tied to product selection rather than matrix loads, so it runs once per
 * product instead of on every matrix refresh.
 */
async function loadProductRiskItems(productId: string): Promise<void> {
  const assessments = await riskAssessmentService.list({ product_id: productId });
  const riskLists = await Promise.all(
    assessments.map((assessment: RiskAssessmentRead) => riskItemService.listByAssessment(assessment.id)),
  );
  productRiskItems.value = riskLists.flat();
}

async function loadReleaseMatrix(releaseId: string): Promise<void> {
  const rows = await requirementMappingService.releaseMatrix(releaseId);
  matrixRows.value = rows;

  const activeRow =
    rows.find((row: ProductRequirementMatrixRowRead) => row.annex_requirement.id === selectedRequirementId.value) ?? rows[0] ?? null;
  if (activeRow) {
    selectRow(activeRow);
  } else {
    selectedRequirementId.value = "";
    resetEditor();
  }
}

async function loadMatrix(): Promise<void> {
  if (!selectedProductId.value || !selectedReleaseId.value) {
    matrixRows.value = [];
    productRiskItems.value = [];
    selectedRequirementId.value = "";
    assessment.value = null;
    resetEditor();
    return;
  }

  loading.value = true;
  errorMessage.value = "";
  successMessage.value = "";

  try {
    await Promise.all([
      loadReleaseMatrix(selectedReleaseId.value),
      loadAssessment(selectedReleaseId.value),
    ]);
  } catch (error: any) {
    errorMessage.value = error?.message ?? "Failed to load Annex I matrix.";
  } finally {
    loading.value = false;
  }
}

/* ── Requirement assessment approval ───────────────── */

async function loadAssessment(releaseId: string): Promise<void> {
  assessment.value = await requirementMappingService.getAssessment(releaseId);
}

async function approveAssessment(): Promise<void> {
  if (!selectedReleaseId.value) return;
  assessmentBusy.value = true;
  errorMessage.value = "";
  successMessage.value = "";
  try {
    assessment.value = await requirementMappingService.approveAssessment(selectedReleaseId.value);
    successMessage.value = `Assessment approved (v${assessment.value.version}). The matrix is now locked.`;
  } catch (error: any) {
    errorMessage.value = error?.message ?? "Failed to approve assessment.";
  } finally {
    assessmentBusy.value = false;
  }
}

async function reopenAssessment(): Promise<void> {
  if (!selectedReleaseId.value) return;
  assessmentBusy.value = true;
  errorMessage.value = "";
  successMessage.value = "";
  try {
    assessment.value = await requirementMappingService.reopenAssessment(selectedReleaseId.value);
    successMessage.value = "Assessment reopened for amendment. Re-approve when done.";
  } catch (error: any) {
    errorMessage.value = error?.message ?? "Failed to reopen assessment.";
  } finally {
    assessmentBusy.value = false;
  }
}

/** Format an ISO timestamp for display (e.g. "Jun 27, 2026, 02:14 PM"). */
function formatDateTime(iso: string): string {
  const d = new Date(iso);
  return Number.isNaN(d.getTime())
    ? iso
    : d.toLocaleString(undefined, {
        year: "numeric",
        month: "short",
        day: "numeric",
        hour: "2-digit",
        minute: "2-digit",
      });
}

/* ── Save / mutate ────────────────────────────────── */

/**
 * Replace a single row in the matrix in place, keyed by annex requirement id.
 * Used after a save so we reflect the server's authoritative row without
 * re-fetching the entire matrix (which previously timed out).
 */
function applyRow(row: ProductRequirementMatrixRowRead): void {
  const index = matrixRows.value.findIndex(
    (existing) => existing.annex_requirement.id === row.annex_requirement.id,
  );
  if (index === -1) {
    matrixRows.value.push(row);
  } else {
    matrixRows.value[index] = row;
  }
}

/** Refresh just the affected requirement row from the server. */
async function refreshRow(annexRequirementId: string): Promise<void> {
  const row = await requirementMappingService.releaseRequirementRow(
    selectedReleaseId.value,
    annexRequirementId,
  );
  applyRow(row);
}

async function saveTrace(): Promise<void> {
  if (!selectedRow.value) return;

  busy.value = true;
  errorMessage.value = "";
  successMessage.value = "";

  try {
    if (editingExisting.value) {
      const payload: RequirementMappingUpdate = {
        risk_item_id: traceForm.risk_item_id || null,
        engineering_requirement_ref: traceForm.engineering_requirement_ref || null,
        sdl_activity: traceForm.sdl_activity,
        evidence_summary: traceForm.evidence_summary || null,
      };
      await requirementMappingService.update(traceForm.id, payload);
      successMessage.value = "Justification updated.";
    } else {
      const payload: RequirementMappingCreate = {
        product_release_id: selectedReleaseId.value,
        annex_requirement_id: selectedRow.value.annex_requirement.id,
        risk_item_id: traceForm.risk_item_id || null,
        engineering_requirement_ref: traceForm.engineering_requirement_ref || null,
        implementation_status: traceForm.implementation_status,
        sdl_activity: traceForm.sdl_activity,
        evidence_summary: traceForm.evidence_summary || null,
      };
      await requirementMappingService.create(payload);
      successMessage.value = "Justification added.";
    }

    // Refresh only the affected requirement row instead of reloading the whole
    // matrix, which previously caused request timeouts on large data sets.
    await refreshRow(selectedRow.value.annex_requirement.id);
    // Adding the first justification can flip the finalized state.
    await loadAssessment(selectedReleaseId.value);
    resetEditor();
  } catch (error: any) {
    errorMessage.value = error?.message ?? "Failed to save justification.";
  } finally {
    busy.value = false;
  }
}

async function removeTrace(traceId: string): Promise<void> {
  // Capture the owning requirement before deletion so we can refresh that row.
  const annexRequirementId = matrixRows.value.find((row) =>
    row.trace_records.some((trace) => trace.id === traceId),
  )?.annex_requirement.id;

  busy.value = true;
  errorMessage.value = "";
  successMessage.value = "";
  try {
    await requirementMappingService.remove(traceId);
    successMessage.value = "Trace record deleted.";
    if (annexRequirementId) {
      await refreshRow(annexRequirementId);
    }
  } catch (error: any) {
    errorMessage.value = error?.message ?? "Failed to delete trace record.";
  } finally {
    busy.value = false;
  }
}

async function downloadArtifact(artifact: ArtifactListRead): Promise<void> {
  const revision = artifact.latest_revision;
  if (!revision?.id || !revision.storage_path) return;

  errorMessage.value = "";
  try {
    await artifactService.downloadRevision(
      revision.id,
      revision.original_filename || artifact.title || "artifact",
    );
  } catch (error: any) {
    errorMessage.value = error?.message ?? "Failed to download artifact.";
  }
}

async function saveApplicabilityDecision(): Promise<void> {
  if (!selectedRow.value || !selectedReleaseId.value) return;

  busy.value = true;
  errorMessage.value = "";
  successMessage.value = "";
  try {
    const payload: ProductRequirementDecisionUpdate = {
      applicability_decision: applicabilityForm.applicability_decision,
      rationale: applicabilityForm.rationale.trim() || null,
    };
    const updatedRow = await requirementMappingService.updateReleaseRequirementDecision(
      selectedReleaseId.value,
      selectedRow.value.annex_requirement.id,
      payload,
    );
    // Apply the server's authoritative row in place — no full matrix reload.
    applyRow(updatedRow);
    // Deciding a requirement can flip can_approve / undecided_codes, so refresh
    // the assessment banner state.
    await loadAssessment(selectedReleaseId.value);
    successMessage.value = "Applicability decision saved.";
  } catch (error: any) {
    errorMessage.value = error?.message ?? "Failed to save applicability decision.";
  } finally {
    busy.value = false;
  }
}

async function setImplementationStatus(status: RequirementProgressStatus): Promise<void> {
  if (!selectedRow.value || !selectedReleaseId.value) return;
  if (selectedRow.value.implementation_status === status) return;

  busy.value = true;
  errorMessage.value = "";
  successMessage.value = "";
  try {
    const updatedRow = await requirementMappingService.updateReleaseRequirementStatus(
      selectedReleaseId.value,
      selectedRow.value.annex_requirement.id,
      { implementation_status: status },
    );
    applyRow(updatedRow);
    // Reaching/leaving "validated" can flip the finalized state, so refresh the banner.
    await loadAssessment(selectedReleaseId.value);
    successMessage.value = `Implementation status set to ${formatLabel(status)}.`;
  } catch (error: any) {
    errorMessage.value = error?.message ?? "Failed to update implementation status.";
  } finally {
    busy.value = false;
  }
}

/* ── Watchers ─────────────────────────────────────── */

watch(selectedProductId, async (productId) => {
  selectedReleaseId.value = "";
  productReleases.value = [];
  matrixRows.value = [];
  productRiskItems.value = [];
  assessment.value = null;
  resetEditor();
  if (productId) await loadProductContext(productId);
});

watch(selectedReleaseId, async () => {
  await loadMatrix();
});

const route = useRoute();

onMounted(async () => {
  try {
    await loadProducts();

    // Deep-link support: the Compliance Journey links here with
    // ?product_id=&release_id= so the matrix opens pre-filtered to that release.
    const qProduct = route.query.product_id;
    const qRelease = route.query.release_id;
    if (typeof qProduct === "string" && products.value.some((p) => p.id === qProduct)) {
      selectedProductId.value = qProduct;
      // The selectedProductId watcher resets the release and loads its context;
      // wait for it, then ensure releases are loaded before selecting one.
      await nextTick();
      await loadProductContext(qProduct);
      if (
        typeof qRelease === "string" &&
        productReleases.value.some((r) => r.id === qRelease)
      ) {
        selectedReleaseId.value = qRelease;
      }
    }
  } catch (error: any) {
    errorMessage.value = error?.message ?? "Failed to load products.";
  }
});
</script>

<style scoped>
/* ── Page layout ──────────────────────────────────── */
.annex-page {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.page-title { margin: 0; }

.page-actions {
  display: flex;
  align-items: flex-end;
  gap: 0.75rem;
  flex-wrap: wrap;
  flex-shrink: 0;
}

.section-heading h1,
.section-heading h2,
.section-heading h3 {
  margin: 0;
}

.editor-actions,
.trace-actions {
  display: flex;
  gap: 0.75rem;
  flex-wrap: wrap;
  align-items: end;
}

/* ── Release banner ───────────────────────────────── */
.release-banner {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 1.5rem;
  flex-wrap: wrap;
  padding: 0.9rem 1.1rem;
  margin-bottom: 1rem;
  border-radius: 12px;
  background: rgba(110, 168, 254, 0.07);
  border: 1px solid rgba(110, 168, 254, 0.2);
}

.release-banner-left {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.release-label {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-weight: 600;
  font-size: var(--text-sm);
}

.release-note {
  color: var(--color-text-muted);
  font-size: var(--text-xs);
}

.release-coverage-bar {
  display: flex;
  flex-direction: column;
  gap: 0.4rem;
  min-width: 220px;
}

.coverage-numbers {
  font-size: var(--text-sm);
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.coverage-pct {
  margin-left: auto;
  font-weight: 700;
  font-size: var(--text-sm);
}

.pct-good    { color: #34d399; }
.pct-partial { color: #fbbf24; }
.pct-low     { color: #f87171; }

/* Quick "needs decision" filter chip in the coverage bar. */
.needs-decision-chip {
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
  padding: 0.25rem 0.65rem;
  border-radius: 999px;
  border: 1px solid rgba(245, 158, 11, 0.45);
  background: rgba(245, 158, 11, 0.12);
  color: #fbbf24;
  font-size: var(--text-xs);
  font-weight: 700;
  cursor: pointer;
  transition: background var(--t-fast, 120ms), border-color var(--t-fast, 120ms);
}
.needs-decision-chip:hover { background: rgba(245, 158, 11, 0.2); }
.needs-decision-chip.active {
  background: rgba(245, 158, 11, 0.28);
  border-color: rgba(245, 158, 11, 0.7);
}
:root[data-theme="light"] .needs-decision-chip {
  color: #b45309;
  border-color: rgba(217, 119, 6, 0.45);
  background: rgba(217, 119, 6, 0.1);
}

.progress-track {
  height: 6px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.08);
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  border-radius: 999px;
  transition: width 0.4s ease;
}

.fill-good    { background: #34d399; }
.fill-partial { background: #fbbf24; }
.fill-low     { background: #f87171; }

/* ── Release trace count mini-stat ────────────────── */
.release-trace-count {
  font-weight: 600;
}

.has-release-evidence {
  background: rgba(52, 211, 153, 0.12);
  border-color: rgba(52, 211, 153, 0.26);
  color: #34d399;
}

.no-release-evidence {
  background: rgba(248, 113, 113, 0.1);
  border-color: rgba(248, 113, 113, 0.22);
  color: #f87171;
}

/* ── Release scope tag in modal ───────────────────── */
.release-scope-tag {
  font-size: var(--text-xs);
  font-weight: 400;
  color: #9cc0ff;
}

/* ── Link button (inline text action) ────────────── */
.link-btn {
  background: none;
  border: none;
  padding: 0;
  color: #9cc0ff;
  cursor: pointer;
  font-size: inherit;
  text-decoration: underline;
  text-underline-offset: 2px;
}

.link-btn:hover {
  color: var(--color-text);
}

/* ── Field hint text ──────────────────────────────── */
.field-hint {
  font-size: var(--text-xs);
  color: var(--color-text-muted);
  font-weight: 400;
}

/* ── Filter badge on button ───────────────────────── */
.filter-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 1.2rem;
  height: 1.2rem;
  border-radius: 999px;
  background: var(--color-primary);
  color: #fff;
  font-size: var(--text-xs);
  font-weight: 700;
  padding: 0 0.3rem;
  margin-left: 0.35rem;
}

/* ── Selector card ────────────────────────────────── */
.selector-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 1rem;
}

/* ── Matrix card ──────────────────────────────────── */
.matrix-card {
  width: 100%;
}

/* ── Compact row list ─────────────────────────────── */
.matrix-list {
  display: flex;
  flex-direction: column;
  gap: 0.55rem;
}

.matrix-row-wrapper {
  display: flex;
  flex-direction: column;
}

/* Compact row — horizontal layout */
.matrix-row {
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.85rem;
  padding: 0.75rem 1rem;
  border: 1px solid rgba(233, 238, 252, 0.08);
  background: rgba(255, 255, 255, 0.03);
  color: inherit;
  border-radius: 14px;
  cursor: pointer;
  text-align: left;
  transition: border-color 0.12s ease, background 0.12s ease, transform 0.12s ease;
}

.matrix-row:hover,
.matrix-row.active {
  border-color: rgba(110, 168, 254, 0.42);
  background: rgba(110, 168, 254, 0.08);
  transform: translateY(-1px);
}

.row-left {
  display: flex;
  flex-direction: column;
  gap: 0.15rem;
  min-width: 0;
  flex: 1;
}

.row-title {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  font-size: var(--text-sm);
}

.requirement-code {
  color: #9cc0ff;
  font-size: var(--text-xs);
  font-weight: 700;
}

.row-right {
  display: flex;
  align-items: center;
  gap: 0.45rem;
  flex-wrap: wrap;
  flex-shrink: 0;
}

/* Expand/collapse chevron button */
.expand-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 1.6rem;
  height: 1.6rem;
  border-radius: 8px;
  color: var(--color-text-muted);
  cursor: pointer;
  transition: background 0.14s ease, color 0.14s ease;
  outline: none;
}

.expand-btn:hover {
  background: rgba(110, 168, 254, 0.12);
  color: var(--color-text);
}

.expand-btn svg {
  transition: transform 0.18s ease;
  pointer-events: none;
}

.expand-btn svg.chevron-open {
  transform: rotate(180deg);
}

/* Inline description panel */
.row-description-panel {
  padding: 0.7rem 1rem 0.7rem 2.5rem;
  border-left: 2px solid rgba(110, 168, 254, 0.3);
  margin: 0.15rem 0 0 1rem;
  border-radius: 0 0 10px 10px;
  background: rgba(110, 168, 254, 0.04);
}

.row-description-panel p {
  margin: 0;
  color: var(--color-text-muted);
  font-size: var(--text-sm);
  line-height: 1.6;
}

/* ── Expand transition ────────────────────────────── */
.expand-enter-active,
.expand-leave-active {
  transition: opacity 0.16s ease, max-height 0.2s ease;
  overflow: hidden;
  max-height: 20rem;
}

.expand-enter-from,
.expand-leave-to {
  opacity: 0;
  max-height: 0;
}

/* ── Detail modal body ────────────────────────────── */
.detail-modal-body {
  display: flex;
  flex-direction: column;
  gap: 0;
}

/* ── Assessment approval banner ───────────────────────── */
.assessment-banner {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-3, 0.75rem);
  flex-wrap: wrap;
  padding: var(--space-3, 0.75rem) var(--space-4, 1rem);
  border: 1px solid var(--color-border, #2a2a2a);
  border-radius: var(--radius-md, 12px);
  margin-bottom: var(--space-4, 1rem);
}
.assessment-banner--approved {
  border-color: var(--color-success, #4f9c13);
  background: color-mix(in srgb, var(--color-success, #4f9c13) 10%, transparent);
}
.assessment-banner--draft {
  background: var(--color-surface-soft, rgba(255, 255, 255, 0.03));
}
.assessment-banner-info {
  display: flex;
  align-items: center;
  gap: var(--space-3, 0.75rem);
  flex-wrap: wrap;
}
.assessment-meta {
  font-size: var(--text-sm, 0.875rem);
  color: var(--color-text-muted, #9aa);
}
.assessment-warn {
  font-size: var(--text-sm, 0.875rem);
  color: var(--color-warning, #c98a00);
}
.assessment-banner-actions {
  display: flex;
  gap: var(--space-2, 0.5rem);
}

/* ── Detail modal: status head + tabs + lock ──────────── */
.detail-lock-note {
  margin-bottom: var(--space-3, 0.75rem);
}
.detail-status-head {
  display: flex;
  gap: 0.55rem;
  flex-wrap: wrap;
  margin-bottom: var(--space-3, 0.75rem);
}
.detail-tabs {
  display: flex;
  gap: var(--space-1, 0.25rem);
  border-bottom: 1px solid var(--color-border, #2a2a2a);
  margin-bottom: var(--space-4, 1rem);
}
.detail-tab {
  appearance: none;
  background: transparent;
  border: none;
  border-bottom: 2px solid transparent;
  padding: var(--space-2, 0.5rem) var(--space-3, 0.75rem);
  color: var(--color-text-muted, #9aa);
  font: inherit;
  font-weight: 600;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  gap: var(--space-2, 0.5rem);
  transition: color var(--t-fast, 120ms), border-color var(--t-fast, 120ms);
}
.detail-tab:hover {
  color: var(--color-text, #eee);
}
.detail-tab.active {
  color: var(--color-primary, #4f9c13);
  border-bottom-color: var(--color-primary, #4f9c13);
}
.detail-tab-count {
  font-size: var(--text-xs, 0.75rem);
  font-weight: 600;
  background: var(--color-surface-soft, rgba(255, 255, 255, 0.06));
  border-radius: 999px;
  padding: 0 0.45rem;
  min-width: 1.25rem;
  text-align: center;
}
.detail-tab-panel {
  display: flex;
  flex-direction: column;
  /* Fix the panel height so the dialog stays exactly the same size on every
     tab. Each tab fills this box and scrolls internally, instead of letting
     taller tabs (Traceability) grow the window and shorter ones (Overview)
     shrink it. */
  height: 56vh;
  overflow-y: auto;
  /* Room so the internal scrollbar doesn't sit flush against content. */
  padding-right: 0.25rem;
}

/* ── Risk traceability tab ────────────────────────── */
.risk-trace-list {
  display: flex;
  flex-direction: column;
  gap: 0.6rem;
}
.risk-trace-card {
  border: 1px solid rgba(233, 238, 252, 0.08);
  background: rgba(255, 255, 255, 0.03);
  border-radius: 12px;
  padding: 0.75rem 0.9rem;
}
.risk-trace-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.6rem;
}
.risk-trace-meta {
  display: flex;
  gap: 0.75rem;
  flex-wrap: wrap;
  margin-top: 0.3rem;
}
.risk-trace-vias {
  margin: 0.5rem 0 0;
  padding-left: 1rem;
  display: flex;
  flex-direction: column;
  gap: 0.2rem;
}
.risk-trace-via {
  font-size: var(--text-xs);
  color: var(--color-text-muted);
}
:root[data-theme="light"] .risk-trace-card {
  border-color: rgba(28, 107, 39, 0.12);
  background: rgba(28, 107, 39, 0.02);
}

.detail-description {
  margin: 0 0 1rem;
  color: var(--color-text-muted);
  line-height: 1.6;
}

.summary-bar {
  display: flex;
  gap: 0.55rem;
  flex-wrap: wrap;
  margin-bottom: 1.1rem;
}

.detail-section,
.trace-section,
.editor-card {
  margin-top: 1.1rem;
  padding-top: 1.1rem;
  border-top: 1px solid var(--color-border, rgba(233, 238, 252, 0.1));
}

/* ── Filter modal grid ────────────────────────────── */
.filter-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 1rem;
}

/* ── Shared form / editor grid ────────────────────── */
.editor-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 1rem;
}

.section-heading {
  display: flex;
  justify-content: space-between;
  gap: 1rem;
  align-items: start;
  margin-bottom: 1rem;
}

.section-heading.tight {
  margin-bottom: 0.85rem;
}

.field {
  display: flex;
  flex-direction: column;
  gap: 0.45rem;
}

.field span {
  font-size: var(--text-xs);
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: var(--color-text-muted);
}

.field-full {
  grid-column: 1 / -1;
}

/* ── Pill badges ──────────────────────────────────── */
.meta-pill,
.mini-stat {
  border-radius: 999px;
  border: 1px solid rgba(233, 238, 252, 0.1);
  padding: 0.32rem 0.65rem;
  font-size: var(--text-xs);
  white-space: nowrap;
}

.mini-stat {
  color: var(--color-text-muted);
  background: rgba(255, 255, 255, 0.03);
}

/* ── Trace records ────────────────────────────────── */
.trace-list {
  display: flex;
  flex-direction: column;
  gap: 0.85rem;
}

.trace-card,
.editor-card {
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(233, 238, 252, 0.08);
  border-radius: 14px;
  padding: 1rem;
}

.trace-card.selected {
  border-color: rgba(110, 168, 254, 0.42);
  background: rgba(110, 168, 254, 0.08);
}

.trace-top {
  width: 100%;
  border: 0;
  padding: 0;
  background: transparent;
  color: inherit;
  text-align: left;
  cursor: pointer;
}

.trace-subline,
.trace-notes {
  margin: 0.35rem 0 0;
  color: var(--color-text-muted);
}

/* ── Artifacts ────────────────────────────────────── */
.artifact-strip {
  display: flex;
  gap: 0.55rem;
  flex-wrap: wrap;
  margin-top: 0.85rem;
}

.artifact-card,
.compact-item {
  display: flex;
  justify-content: space-between;
  gap: 0.75rem;
  align-items: center;
  padding: 0.75rem 0.9rem;
  border-radius: 12px;
  border: 1px solid rgba(233, 238, 252, 0.1);
  background: rgba(255, 255, 255, 0.03);
}

.artifact-selector-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 0.75rem;
}

.artifact-option {
  display: flex;
  gap: 0.75rem;
  align-items: start;
  padding: 0.85rem 0.95rem;
  border-radius: 12px;
  border: 1px solid rgba(233, 238, 252, 0.1);
  background: rgba(255, 255, 255, 0.03);
  cursor: pointer;
}

.artifact-option.selected {
  border-color: rgba(110, 168, 254, 0.38);
  background: rgba(110, 168, 254, 0.08);
}

.artifact-option input { margin-top: 0.2rem; }

.artifact-option-copy {
  display: flex;
  flex-direction: column;
  gap: 0.2rem;
}

.artifact-option-copy span,
.artifact-selection-note {
  color: var(--color-text-muted);
  font-size: var(--text-sm);
}

.artifact-info {
  display: flex;
  flex-direction: column;
  gap: 0.2rem;
  min-width: 0;
}

.artifact-actions-inline {
  display: flex;
  gap: 0.5rem;
  flex-wrap: wrap;
  flex-shrink: 0;
}

/* ── Compact list (risks / artifacts in detail) ───── */
.compact-list {
  display: flex;
  flex-direction: column;
  gap: 0.65rem;
}

.compact-item {
  align-items: flex-start;
  flex-direction: column;
}

.compact-item-actions,
.artifact-card {
  align-items: center;
  flex-direction: row;
}

/* ── Alerts / states ──────────────────────────────── */
.alert {
  border-radius: 12px;
  padding: 0.85rem 1rem;
  border: 1px solid transparent;
  margin-bottom: 0.75rem;
}

.alert.error   { background: rgba(251, 113, 133, 0.12); border-color: rgba(251, 113, 133, 0.26); color: #fecdd3; }
.alert.success { background: rgba(52, 211, 153, 0.12);  border-color: rgba(52, 211, 153, 0.26);  color: #bbf7d0; }
.alert.warning { background: rgba(251, 191, 36, 0.12);  border-color: rgba(251, 191, 36, 0.26);  color: #fde68a; }

.state-block {
  border: 1px dashed rgba(233, 238, 252, 0.14);
  border-radius: 14px;
  padding: 1.2rem;
  background: rgba(255, 255, 255, 0.02);
}

.state-block.compact { padding: 1rem; }

/* ── Skeletons ────────────────────────────────────── */
.skeleton-row {
  height: 3.2rem;
  border-radius: 12px;
  margin-bottom: 0.55rem;
  background:
    linear-gradient(90deg, rgba(255, 255, 255, 0.04), rgba(255, 255, 255, 0.08), rgba(255, 255, 255, 0.04));
  background-size: 200% 100%;
  animation: shimmer 1.4s linear infinite;
}

/* ── Applicability pills ──────────────────────────── */
.app-applicable     { background: rgba(96, 165, 250, 0.12);  border-color: rgba(96, 165, 250, 0.24); }
.app-not_applicable { background: rgba(251, 191, 36, 0.12);  border-color: rgba(251, 191, 36, 0.26); }
.status-empty       { background: rgba(148, 163, 184, 0.14); border-color: rgba(148, 163, 184, 0.18); }

/* "Needs decision" stands out: warm amber, bolder text, leading dot. */
.app-needs_decision {
  background: rgba(245, 158, 11, 0.16);
  border-color: rgba(245, 158, 11, 0.45);
  color: #fbbf24;
  font-weight: 700;
}
.applicability-pill {
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
}
.pill-dot {
  width: 0.5rem;
  height: 0.5rem;
  border-radius: 50%;
  background: #f59e0b;
  box-shadow: 0 0 0 0 rgba(245, 158, 11, 0.55);
  animation: pulse-dot 2s ease-out infinite;
}
@keyframes pulse-dot {
  0%   { box-shadow: 0 0 0 0 rgba(245, 158, 11, 0.5); }
  70%  { box-shadow: 0 0 0 6px rgba(245, 158, 11, 0); }
  100% { box-shadow: 0 0 0 0 rgba(245, 158, 11, 0); }
}
@media (prefers-reduced-motion: reduce) {
  .pill-dot { animation: none; }
}

/* Row accent when a requirement still needs a decision — makes remaining
   items easy to spot while scanning the list. */
.matrix-row.needs-decision {
  border-left: 3px solid #f59e0b;
  background: rgba(245, 158, 11, 0.05);
}
.matrix-row.needs-decision:hover,
.matrix-row.needs-decision.active {
  border-left-color: #f59e0b;
}

/* ── Status pills ─────────────────────────────────── */
.status-planned     { background: rgba(250, 204, 21, 0.12);  border-color: rgba(250, 204, 21, 0.22); }
.status-in_progress { background: rgba(251, 146, 60, 0.12);  border-color: rgba(251, 146, 60, 0.24); }
.status-implemented { background: rgba(96, 165, 250, 0.12);  border-color: rgba(96, 165, 250, 0.24); }
.status-verified    { background: rgba(52, 211, 153, 0.12);  border-color: rgba(52, 211, 153, 0.26); }
.status-not_applicable { background: rgba(217, 119, 6, 0.14); border-color: rgba(217, 119, 6, 0.24); }

/* ── Implementation progress pills ────────────────── */
.progress-planned     { background: rgba(148, 163, 184, 0.14); border-color: rgba(148, 163, 184, 0.22); }
.progress-implemented { background: rgba(96, 165, 250, 0.12);  border-color: rgba(96, 165, 250, 0.26); }
.progress-validated   { background: rgba(52, 211, 153, 0.14);  border-color: rgba(52, 211, 153, 0.3); }

/* ── Finalized state pills ────────────────────────── */
.finalized-pill   { background: rgba(52, 211, 153, 0.16); border-color: rgba(52, 211, 153, 0.4); color: #34d399; font-weight: 700; }
.unfinalized-pill { background: rgba(148, 163, 184, 0.12); border-color: rgba(148, 163, 184, 0.22); }

/* ── Implementation tab: status picker ────────────── */
.impl-status-picker {
  display: flex;
  gap: 0.5rem;
  flex-wrap: wrap;
  margin-bottom: 1rem;
}
.impl-status-option {
  display: inline-flex;
  align-items: center;
  gap: 0.45rem;
  padding: 0.5rem 0.9rem;
  border-radius: 999px;
  border: 1px solid rgba(233, 238, 252, 0.12);
  background: rgba(255, 255, 255, 0.03);
  color: inherit;
  font: inherit;
  font-weight: 600;
  cursor: pointer;
  transition: border-color var(--t-fast, 120ms), background var(--t-fast, 120ms);
}
.impl-status-option:hover:not(:disabled) { border-color: rgba(110, 168, 254, 0.4); }
.impl-status-option:disabled { opacity: 0.55; cursor: not-allowed; }
.impl-status-option.active {
  border-color: var(--color-primary, #4f9c13);
  background: color-mix(in srgb, var(--color-primary, #4f9c13) 14%, transparent);
}
.impl-status-dot {
  width: 0.6rem;
  height: 0.6rem;
  border-radius: 50%;
  background: currentColor;
}
.progress-dot-planned     { color: #94a3b8; }
.progress-dot-implemented { color: #60a5fa; }
.progress-dot-validated   { color: #34d399; }

/* ── Finalization checklist ───────────────────────── */
.finalize-checklist {
  list-style: none;
  margin: 0 0 1rem;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 0.4rem;
}
.finalize-checklist li {
  display: flex;
  align-items: center;
  gap: 0.55rem;
  color: var(--color-text-muted);
  font-size: var(--text-sm);
}
.finalize-checklist li.done { color: var(--color-text); }
.finalize-checklist .check-mark {
  display: inline-flex;
  width: 1.25rem;
  justify-content: center;
  font-weight: 700;
}
.finalize-checklist li.done .check-mark { color: #34d399; }

.finalize-banner {
  padding: 0.7rem 0.95rem;
  border-radius: 12px;
  font-weight: 600;
  border: 1px solid transparent;
}
.finalize-banner.is-final {
  background: rgba(52, 211, 153, 0.12);
  border-color: rgba(52, 211, 153, 0.35);
  color: #34d399;
}
.finalize-banner.not-final {
  background: rgba(148, 163, 184, 0.1);
  border-color: rgba(148, 163, 184, 0.22);
  color: var(--color-text-muted);
}

.detail-subhead { margin-top: 0.5rem; }
.risk-summary { margin-bottom: 1rem; }

/* ── Button utilities ─────────────────────────────── */
.small-button {
  padding: 0.4rem 0.7rem;
  border-radius: 9px;
  font-size: var(--text-xs);
}

.link-button {
  display: inline-flex;
  align-items: center;
}

/* ── Fade transition (alerts) ─────────────────────── */
.fade-enter-active,
.fade-leave-active { transition: opacity 0.18s ease; }
.fade-enter-from,
.fade-leave-to     { opacity: 0; }

/* ── Shimmer animation ────────────────────────────── */
@keyframes shimmer {
  from { background-position: 200% 0; }
  to   { background-position: -200% 0; }
}

/* ── Responsive ───────────────────────────────────── */
@media (max-width: 900px) {
  .selector-grid,
  .filter-grid,
  .editor-grid,
  .artifact-selector-grid {
    grid-template-columns: 1fr;
  }

  .section-heading {
    flex-direction: column;
  }

  .row-right {
    flex-wrap: wrap;
  }
}

@media (max-width: 640px) {
  .row-title {
    white-space: normal;
  }

  .matrix-row {
    flex-direction: column;
    align-items: flex-start;
  }

  .row-right {
    width: 100%;
  }
}
</style>

<style>
/* ── Light theme overrides ────────────────────────── */
:root[data-theme="light"] .matrix-row {
  border-color: rgba(28, 107, 39, 0.1);
  background: rgba(255, 255, 255, 0.6);
}
:root[data-theme="light"] .matrix-row:hover,
:root[data-theme="light"] .matrix-row.active {
  border-color: rgba(37, 99, 235, 0.35);
  background: rgba(37, 99, 235, 0.07);
}
:root[data-theme="light"] .trace-card.selected {
  border-color: rgba(37, 99, 235, 0.35);
  background: rgba(37, 99, 235, 0.07);
}
:root[data-theme="light"] .requirement-code { color: #1d4ed8; }
:root[data-theme="light"] .meta-pill        { border-color: rgba(28, 107, 39, 0.12); }
:root[data-theme="light"] .mini-stat        { background: rgba(28, 107, 39, 0.04); }
:root[data-theme="light"] .artifact-option  { border-color: rgba(28, 107, 39, 0.12); background: rgba(255, 255, 255, 0.6); }
:root[data-theme="light"] .artifact-option.selected {
  border-color: rgba(37, 99, 235, 0.35);
  background: rgba(37, 99, 235, 0.07);
}
:root[data-theme="light"] .row-description-panel {
  border-left-color: rgba(37, 99, 235, 0.3);
  background: rgba(37, 99, 235, 0.04);
}
:root[data-theme="light"] .alert.error   { background: rgba(239,68,68,0.08);   border-color: rgba(239,68,68,0.26);   color: #be123c; }
:root[data-theme="light"] .alert.success { background: rgba(21,128,61,0.08);   border-color: rgba(21,128,61,0.26);   color: #15803d; }
:root[data-theme="light"] .alert.warning { background: rgba(184,155,18,0.08);  border-color: rgba(184,155,18,0.26);  color: #78350f; }
:root[data-theme="light"] .state-block   { border-color: rgba(28, 107, 39, 0.15); background: rgba(28, 107, 39, 0.03); }
:root[data-theme="light"] .skeleton-row  {
  background: linear-gradient(90deg, rgba(28,107,39,0.04), rgba(28,107,39,0.08), rgba(28,107,39,0.04));
}
:root[data-theme="light"] .app-applicable     { background: rgba(37,99,235,0.08);   border-color: rgba(37,99,235,0.22); }
:root[data-theme="light"] .app-not_applicable { background: rgba(184,155,18,0.08);  border-color: rgba(184,155,18,0.24); }
:root[data-theme="light"] .status-empty       { background: rgba(71,85,105,0.08);   border-color: rgba(71,85,105,0.18); }
:root[data-theme="light"] .app-needs_decision {
  background: rgba(217, 119, 6, 0.12);
  border-color: rgba(217, 119, 6, 0.45);
  color: #b45309;
}
:root[data-theme="light"] .matrix-row.needs-decision {
  background: rgba(217, 119, 6, 0.05);
  border-left-color: #d97706;
}
:root[data-theme="light"] .status-planned     { background: rgba(184,155,18,0.08);  border-color: rgba(184,155,18,0.2); }
:root[data-theme="light"] .status-in_progress { background: rgba(234,88,12,0.08);   border-color: rgba(234,88,12,0.22); }
:root[data-theme="light"] .status-implemented { background: rgba(37,99,235,0.08);   border-color: rgba(37,99,235,0.22); }
:root[data-theme="light"] .status-verified    { background: rgba(21,128,61,0.08);   border-color: rgba(21,128,61,0.24); }
:root[data-theme="light"] .status-not_applicable { background: rgba(180,83,9,0.08); border-color: rgba(180,83,9,0.22); }

/* ── Card border visibility in light mode ── */
[data-theme="light"] .annex-page .card {
  box-shadow: 0 2px 6px rgba(0,0,0,0.09), 0 0 0 1px rgba(0,0,0,0.16);
  border-color: transparent;
}
[data-theme="light"] .annex-page .trace-card {
  box-shadow: 0 1px 3px rgba(0,0,0,0.07), 0 0 0 1px rgba(0,0,0,0.13);
  border-color: transparent;
}
[data-theme="light"] .annex-page .artifact-card {
  box-shadow: 0 1px 3px rgba(0,0,0,0.07), 0 0 0 1px rgba(0,0,0,0.13);
  border-color: transparent;
}
[data-theme="light"] .annex-page .editor-card {
  box-shadow: 0 2px 6px rgba(0,0,0,0.09), 0 0 0 1px rgba(0,0,0,0.16);
  border-color: transparent;
}
</style>
