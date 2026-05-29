<template>
  <section class="page">
    <header class="page-header">
      <div>
        <h1 class="page-title">SBOM analyzer</h1>
        <p class="muted page-subtitle">
          Manage machine-readable Software Bills of Materials per product release.
          A machine-readable SBOM listing top-level dependencies is required under
          CRA Annex I Part II §1.
        </p>
      </div>

      <div class="page-actions">
        <label class="field">
          <span class="field-label">Search products</span>
          <input v-model.trim="productQuery" type="text" placeholder="Product name or code" />
        </label>

        <label class="field">
          <span class="field-label">Product</span>
          <select v-model="selectedProductId" :disabled="isLoadingProducts">
            <option value="">{{ isLoadingProducts ? "Loading…" : "All products" }}</option>
            <option v-for="p in filteredProducts" :key="p.id" :value="p.id">
              {{ p.name }} ({{ p.product_code }})
            </option>
          </select>
        </label>

        <label class="field">
          <span class="field-label">Release</span>
          <select v-model="selectedReleaseId" :disabled="!selectedProductId || isLoadingReleases">
            <option value="">{{ !selectedProductId ? "Select a product first" : "All releases" }}</option>
            <option v-for="r in releases" :key="r.id" :value="r.id">{{ r.display_version }}</option>
          </select>
        </label>

        <!-- Import from release gate artifact -->
        <button
          class="btn btn-secondary"
          :disabled="!selectedReleaseId || isImporting"
          :title="!selectedReleaseId ? 'Select a release first' : 'Re-create SBOM record from the artifact already attached in the release gate'"
          @click="importFromArtifact"
        >
          {{ isImporting ? "Importing…" : "Import from artifact" }}
        </button>

        <!-- Upload & Analyze: primary action for new SBOMs -->
        <button class="btn btn-primary" @click="showUploadModal = true">
          Upload &amp; Analyze
        </button>

        <!-- Manual metadata entry: secondary action -->
        <button class="btn btn-secondary" @click="showCreateModal = true">
          + Manual entry
        </button>
      </div>
    </header>

    <div v-if="errorMessage" class="card feedback feedback-error">{{ errorMessage }}</div>
    <div v-if="successMessage" class="card feedback feedback-success">{{ successMessage }}</div>

    <section class="card">
      <div class="section-header">
        <h2 class="section-title">SBOM records</h2>
        <p class="muted">{{ records.length }} record(s)</p>
      </div>

      <div v-if="isLoading" class="empty-panel">Loading SBOM records…</div>
      <div v-else-if="records.length === 0" class="empty-panel">
        No SBOM records found. Upload an SBOM file to satisfy CRA Annex I Part II §1.
      </div>

      <div v-else class="table-wrapper">
        <table class="data-table">
          <thead>
            <tr>
              <th>Format</th>
              <th>Spec display_version</th>
              <th>Components</th>
              <th>Quality</th>
              <th>Tool</th>
              <th>Generated</th>
              <th>File</th>
              <th>Added</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="r in records"
              :key="r.id"
              class="table-row-clickable"
              @click="openDetail(r)"
              tabindex="0"
              @keydown.enter="openDetail(r)"
            >
              <td><span class="format-badge" :class="`format-${r.format}`">{{ r.format.toUpperCase() }}</span></td>
              <td>{{ r.spec_version || "—" }}</td>
              <td>
                <span v-if="r.component_count !== null" class="component-count">{{ r.component_count }}</span>
                <span v-else class="muted">—</span>
              </td>
              <!-- Quality score badge -->
              <td>
                <span
                  v-if="r.quality_score !== null && r.quality_score !== undefined"
                  class="quality-badge"
                  :class="qualityClass(r.quality_score)"
                >
                  {{ r.quality_score }}/100
                </span>
                <span v-else class="muted">—</span>
              </td>
              <td>{{ r.tool_name ? `${r.tool_name}${r.tool_version ? " " + r.tool_version : ""}` : "—" }}</td>
              <td class="nowrap">{{ formatDate(r.generated_at) }}</td>
              <td>
                <span v-if="r.file_name" class="file-name">{{ r.file_name }}</span>
                <span v-else class="muted">—</span>
              </td>
              <td class="nowrap">{{ formatDate(r.created_at) }}</td>
              <td class="row-arrow">›</td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>
  </section>

  <!-- ── Upload & Analyze Modal ── -->
  <AppModal v-model="showUploadModal" title="Upload & Analyze SBOM" size="lg" :persistent="true">
    <form id="sbom-upload-form" class="form-grid" @submit.prevent="uploadRecord">
      <div class="field field-span-2">
        <span class="field-label">Release <span class="req">*</span></span>
        <select v-model="uploadForm.product_release_id" required>
          <option value="">— Select a release —</option>
          <option v-for="r in releases" :key="r.id" :value="r.id">{{ r.display_version }}</option>
        </select>
        <p v-if="!selectedProductId" class="muted hint">Select a product and release in the filters first.</p>
      </div>

      <div class="field field-span-2">
        <span class="field-label">SBOM file <span class="req">*</span></span>
        <input
          ref="fileInput"
          type="file"
          accept=".json,.xml,.spdx,.cdx,.txt"
          required
          @change="onFileChange"
          class="file-input"
        />
        <p class="muted hint">
          CycloneDX (JSON/XML 1.4–1.7) or SPDX (JSON/tag-value 2.2–3.0).
          sbom-tools will run quality scoring and CRA+NTIA compliance validation automatically.
        </p>
      </div>

      <label class="field field-span-2">
        <span class="field-label">Notes</span>
        <textarea v-model.trim="uploadForm.notes" rows="2" placeholder="Scope exclusions, known gaps…" />
      </label>
    </form>

    <template #footer>
      <button class="btn btn-secondary" :disabled="isUploading" @click="showUploadModal = false">Cancel</button>
      <button
        class="btn btn-primary"
        type="submit"
        form="sbom-upload-form"
        :disabled="isUploading || !uploadForm.product_release_id || !uploadForm.file"
      >
        {{ isUploading ? "Analyzing…" : "Upload & Analyze" }}
      </button>
    </template>
  </AppModal>

  <!-- ── Manual Create Modal ── -->
  <AppModal v-model="showCreateModal" title="New SBOM record (manual)" size="lg" :persistent="true">
    <form id="sbom-create-form" class="form-grid" @submit.prevent="createRecord">
      <div class="field field-span-2">
        <span class="field-label">Release</span>
        <select v-model="createForm.product_release_id" required>
          <option value="">— Select a release —</option>
          <option v-for="r in releases" :key="r.id" :value="r.id">{{ r.display_version }}</option>
        </select>
      </div>

      <label class="field">
        <span class="field-label">Format</span>
        <select v-model="createForm.format">
          <option value="cyclonedx">CycloneDX</option>
          <option value="spdx">SPDX</option>
          <option value="swid">SWID</option>
          <option value="other">Other</option>
        </select>
      </label>

      <label class="field">
        <span class="field-label">Specification display_version</span>
        <input v-model.trim="createForm.spec_version" type="text" placeholder="e.g. 1.5" />
      </label>

      <label class="field">
        <span class="field-label">Tool name</span>
        <input v-model.trim="createForm.tool_name" type="text" placeholder="e.g. CycloneDX CLI" />
      </label>

      <label class="field">
        <span class="field-label">Tool display_version</span>
        <input v-model.trim="createForm.tool_version" type="text" placeholder="e.g. 2.4.1" />
      </label>

      <label class="field">
        <span class="field-label">File name</span>
        <input v-model.trim="createForm.file_name" type="text" placeholder="sbom.cdx.json" />
      </label>

      <label class="field">
        <span class="field-label">Generated at</span>
        <input v-model="createForm.generated_at" type="datetime-local" />
      </label>

      <label class="field field-span-2">
        <span class="field-label">Notes</span>
        <textarea v-model.trim="createForm.notes" rows="2" placeholder="Scope exclusions, known gaps…" />
      </label>

      <div class="field field-span-2">
        <span class="field-label">Component count</span>
        <input v-model.number="createForm.component_count" type="number" min="0" placeholder="Auto-derived if omitted" />
        <p class="muted hint">Leave blank to auto-derive from the uploaded SBOM</p>
      </div>
    </form>

    <template #footer>
      <button class="btn btn-secondary" :disabled="isCreating" @click="showCreateModal = false">Cancel</button>
      <button class="btn btn-primary" type="submit" form="sbom-create-form"
        :disabled="isCreating || !createForm.product_release_id">
        {{ isCreating ? "Saving…" : "Create SBOM record" }}
      </button>
    </template>
  </AppModal>

  <!-- ── Detail Modal ── -->
  <AppModal v-if="detailItem" v-model="showDetailModal" :title="detailItem.file_name || 'SBOM record'" size="lg">
    <div class="sbom-detail-layout">

      <!-- ── Left sidebar: permanent metadata ── -->
      <aside class="sbom-sidebar">
        <!-- Quality score hero -->
        <div class="sidebar-score-hero">
          <span class="sidebar-score-label">Quality score</span>
          <span
            v-if="detailItem.quality_score !== null && detailItem.quality_score !== undefined"
            class="sidebar-score-value"
            :class="qualityClass(detailItem.quality_score)"
          >{{ detailItem.quality_score }}<span class="score-denom">/100</span></span>
          <span v-else class="sidebar-score-value muted">—</span>
          <div v-if="qualityReport?.grade" class="sidebar-grade-row">
            <span class="sidebar-grade">Grade {{ qualityReport.grade }}</span>
            <span
              class="grade-info-icon"
              title="Grading scale — A: 80–100 · B: 60–79 · C: 40–59 · D: 20–39 · F: 0–19"
            >ⓘ</span>
          </div>
        </div>

        <!-- Compliance status pills (one per standard) -->
        <div v-if="validateList.length" class="sidebar-compliance-pills">
          <span
            v-for="(std, i) in validateList"
            :key="i"
            class="compliance-pill"
            :class="std.is_compliant ? 'pill-pass' : 'pill-fail'"
            :title="`${standardName(std.level)}${standardDescription(std.level) ? '\n\n' + standardDescription(std.level) : ''}`"
          >
            {{ std.level ?? `STD ${i + 1}` }}&nbsp;{{ std.is_compliant ? "✓" : "✗" }}
          </span>
        </div>

        <div class="sidebar-divider" />

        <!-- Key-value metadata -->
        <dl class="sidebar-meta">
          <dt>Format</dt>
          <dd><span class="format-badge" :class="`format-${detailItem.format}`">{{ detailItem.format.toUpperCase() }}</span></dd>

          <dt>Spec display_version</dt>
          <dd>{{ detailItem.spec_version || "—" }}</dd>

          <dt>Components</dt>
          <dd>
            <span v-if="detailItem.component_count !== null" class="component-count">{{ detailItem.component_count }}</span>
            <span v-else class="muted">—</span>
          </dd>

          <dt>Tool</dt>
          <dd>{{ detailItem.tool_name ? `${detailItem.tool_name}${detailItem.tool_version ? " " + detailItem.tool_version : ""}` : "—" }}</dd>

          <dt>Generated</dt>
          <dd>{{ formatDate(detailItem.generated_at) }}</dd>

          <dt>Added</dt>
          <dd>{{ formatDate(detailItem.created_at) }}</dd>
        </dl>

        <!-- Notes -->
        <div v-if="detailItem.notes" class="sidebar-notes">
          <span class="sidebar-notes-label">Notes</span>
          <p class="sidebar-notes-text">{{ detailItem.notes }}</p>
        </div>
      </aside>

      <!-- ── Right pane: tabbed analysis ── -->
      <div class="sbom-analysis-pane">
        <div class="detail-tabs">
          <button
            v-for="tab in detailTabs"
            :key="tab.id"
            class="detail-tab"
            :class="{ active: activeDetailTab === tab.id }"
            @click="activeDetailTab = tab.id"
          >
            {{ tab.label }}
          </button>
        </div>

        <div class="tab-scroll-area">

          <!-- Tab: CRA compliance -->
          <div v-if="activeDetailTab === 'compliance'" class="tab-panel">
            <div v-if="!detailItem.analysis_findings" class="empty-panel">
              No compliance analysis available.
              <span v-if="detailItem.sbom_content">Click "Re-analyze" to run sbom-tools.</span>
              <span v-else>Upload the SBOM file using "Upload &amp; Analyze" to enable analysis.</span>
            </div>
            <div v-else-if="validateList.length" class="standards-list">
              <div v-for="(std, idx) in validateList" :key="idx" class="standard-block">
                <!-- Standard header: human name + PASS/FAIL -->
                <div class="standard-header">
                  <div class="standard-name-group">
                    <span class="standard-name">{{ standardName(std.level) }}</span>
                    <span v-if="standardDescription(std.level)" class="standard-desc">{{ standardDescription(std.level) }}</span>
                  </div>
                  <span class="compliance-verdict" :class="std.is_compliant ? 'verdict-pass' : 'verdict-fail'">
                    {{ std.is_compliant ? "PASS" : "FAIL" }}
                  </span>
                </div>

                <template v-if="(std.violations as unknown[])?.length">
                  <!-- Errors section -->
                  <div v-if="violationErrors(std.violations as Record<string,unknown>[]).length" class="violation-group">
                    <span class="violation-group-label violation-group-error">
                      Errors ({{ violationErrors(std.violations as Record<string,unknown>[]).length }})
                    </span>
                    <ul class="findings-list">
                      <li
                        v-for="(v, i) in violationErrors(std.violations as Record<string,unknown>[])"
                        :key="`e-${i}`"
                        class="finding-item finding-fail"
                      >
                        {{ v.message }}
                        <span v-if="v.element" class="finding-element">{{ v.element }}</span>
                      </li>
                    </ul>
                  </div>

                  <!-- Warnings section -->
                  <div v-if="violationWarnings(std.violations as Record<string,unknown>[]).length" class="violation-group">
                    <span class="violation-group-label violation-group-warn">
                      Warnings ({{ violationWarnings(std.violations as Record<string,unknown>[]).length }})
                    </span>
                    <ul class="findings-list">
                      <li
                        v-for="(v, i) in violationWarnings(std.violations as Record<string,unknown>[])"
                        :key="`w-${i}`"
                        class="finding-item finding-warn"
                      >
                        {{ v.message }}
                        <span v-if="v.element" class="finding-element">{{ v.element }}</span>
                      </li>
                    </ul>
                  </div>
                </template>
                <p v-else class="finding-none">All checks passed.</p>
              </div>
            </div>
            <div v-else class="empty-panel muted">Validation output not available in findings.</div>
          </div>

          <!-- Tab: Quality -->
          <div v-else-if="activeDetailTab === 'quality'" class="tab-panel">
            <div v-if="!detailItem.analysis_findings" class="empty-panel">
              No quality analysis available. Upload the SBOM file to enable analysis.
            </div>
            <div v-else-if="qualityReport">
              <div v-if="qualityRecommendations.length" class="recommendations">
                <h3 class="tab-section-title">Recommendations ({{ qualityRecommendations.length }})</h3>
                <ul class="rec-list">
                  <li
                    v-for="(rec, i) in (qualityRecommendations as Record<string,unknown>[])"
                    :key="i"
                    class="rec-item"
                  >
                    <span class="rec-priority">P{{ rec.priority ?? i + 1 }}</span>
                    <span class="rec-body">
                      {{ rec.message ?? rec.text ?? JSON.stringify(rec) }}
                      <span v-if="rec.affected_count" class="rec-count">
                        ({{ rec.affected_count }} component{{ (rec.affected_count as number) !== 1 ? "s" : "" }})
                      </span>
                    </span>
                    <span v-if="rec.impact" class="rec-impact">+{{ rec.impact }} pts</span>
                  </li>
                </ul>
              </div>
              <p v-else class="empty-panel muted">No recommendations — SBOM is well-formed.</p>
            </div>
            <div v-else class="empty-panel muted">Quality output not available in findings.</div>
          </div>

          <!-- Tab: Differential analysis -->
          <div v-else-if="activeDetailTab === 'diff'" class="tab-panel">
            <div v-if="!detailItem.analysis_findings?.diff" class="diff-empty-state">
              <p class="diff-empty-title">No differential analysis available</p>
              <p class="diff-empty-hint">
                A differential analysis is generated automatically when you upload a <strong>new display_version</strong>
                of the SBOM for the same release. It compares the new SBOM against the immediately preceding one
                and shows which components were added, removed, or updated — making it easy to audit supply-chain
                changes between releases.
              </p>
            </div>
            <div v-else>
              <!-- Explanation note -->
              <p class="diff-context-note">
                This diff compares the SBOM you are viewing against the record that existed
                immediately before it was uploaded for this release. It is computed once at
                upload time and does not change if newer records are added later.
              </p>

              <!-- Summary banner -->
              <div class="diff-summary-bar">
                <span class="diff-summary-chip diff-chip-added">+{{ diffAdded.length }} added</span>
                <span class="diff-summary-chip diff-chip-removed">−{{ diffRemoved.length }} removed</span>
                <span class="diff-summary-chip diff-chip-changed">~{{ diffChanged.length }} changed</span>
                <span class="diff-summary-note">compared to the previous SBOM for this release</span>
              </div>

              <div v-if="diffAdded.length" class="diff-section">
                <h3 class="tab-section-title diff-added-title">Added components ({{ diffAdded.length }})</h3>
                <ul class="diff-list">
                  <li v-for="(c, i) in diffAdded" :key="i" class="diff-item diff-item-added">{{ formatComponent(c) }}</li>
                </ul>
              </div>
              <div v-if="diffRemoved.length" class="diff-section">
                <h3 class="tab-section-title diff-removed-title">Removed components ({{ diffRemoved.length }})</h3>
                <ul class="diff-list">
                  <li v-for="(c, i) in diffRemoved" :key="i" class="diff-item diff-item-removed">{{ formatComponent(c) }}</li>
                </ul>
              </div>
              <div v-if="diffChanged.length" class="diff-section">
                <h3 class="tab-section-title diff-changed-title">Changed components ({{ diffChanged.length }})</h3>
                <ul class="diff-list">
                  <li v-for="(c, i) in diffChanged" :key="i" class="diff-item diff-item-changed">{{ formatComponent(c) }}</li>
                </ul>
              </div>
              <div v-if="!diffAdded.length && !diffRemoved.length && !diffChanged.length" class="finding-none" style="margin-top:0.5rem;">
                No component changes detected — the two SBOMs are identical in composition.
              </div>
              <div v-if="!diffAdded.length && !diffRemoved.length && !diffChanged.length && detailItem.analysis_findings?.diff" class="raw-json" style="margin-top:0.75rem;">
                <pre>{{ JSON.stringify(detailItem.analysis_findings.diff, null, 2) }}</pre>
              </div>
            </div>
          </div>

          <!-- Tab: Vulnerabilities (CRA Art. 13(2) — multi-scanner CVE analysis) -->
          <div v-else-if="activeDetailTab === 'vulnerabilities'" class="tab-panel">
            <!-- Header: description + scanner legend + scan button -->
            <div class="vuln-scan-header">
              <div>
                <p class="tab-description muted" style="margin-bottom:0.4rem">
                  Multi-scanner CVE analysis — OSV · Trivy · NVD — CRA Art. 13(2)
                </p>
                <!-- Scanner legend: shows which databases are queried -->
                <div class="scanner-legend">
                  <span class="scanner-legend-item">
                    <span class="source-badge source-badge-osv">OSV</span>
                    <span class="scanner-legend-label">Open Source Vulnerabilities (PyPI, npm, Go…)</span>
                  </span>
                  <span class="scanner-legend-item">
                    <span class="source-badge source-badge-trivy">TRIVY</span>
                    <span class="scanner-legend-label">Aqua Trivy (NVD, GHSA, Ubuntu, Debian, Alpine…)</span>
                  </span>
                  <span class="scanner-legend-item">
                    <span class="source-badge source-badge-nvd">NVD</span>
                    <span class="scanner-legend-label">NIST NVD — CVSS enrichment</span>
                  </span>
                </div>
              </div>
              <button class="btn btn-primary btn-sm" :disabled="isScanningVulns" @click="scanVulnerabilities"
                title="Runs OSV + Trivy (if installed) and enriches via NVD">
                {{ isScanningVulns ? "Scanning…" : "Scan for vulnerabilities" }}
              </button>
            </div>

            <div v-if="vulnScanError" class="feedback feedback-error" style="margin-bottom:0.75rem">{{ vulnScanError }}</div>

            <!-- Empty state -->
            <div v-if="!vulnFindings.length" class="empty-panel">
              No findings yet. Run a scan to check components against known CVEs.
            </div>

            <template v-else>
              <!-- Sort + source filter bar -->
              <div class="vuln-sort-bar">
                <span class="vuln-sort-label">Source:</span>
                <button
                  v-for="src in [{ key: 'all', label: 'All' }, { key: 'osv', label: 'OSV' }, { key: 'trivy', label: 'Trivy' }]"
                  :key="src.key"
                  class="sort-btn"
                  :class="{ 'sort-btn-active': vulnSourceFilter === src.key }"
                  @click="vulnSourceFilter = src.key as 'all' | 'osv' | 'trivy'"
                >{{ src.label }}</button>

                <span class="vuln-sort-divider" />

                <span class="vuln-sort-label">Sort:</span>
                <button
                  v-for="opt in [
                    { key: 'epss',     label: 'EPSS' },
                    { key: 'cvss',     label: 'CVSS' },
                    { key: 'severity', label: 'Severity' },
                    { key: 'none',     label: 'Default' },
                  ]"
                  :key="opt.key"
                  class="sort-btn"
                  :class="{ 'sort-btn-active': vulnSortKey === opt.key }"
                  @click="toggleVulnSort(opt.key as 'epss' | 'cvss' | 'severity' | 'none')"
                >
                  {{ opt.label }}
                  <span v-if="vulnSortKey === opt.key && opt.key !== 'none'" class="sort-arrow">
                    {{ vulnSortDir === 'desc' ? '↓' : '↑' }}
                  </span>
                </button>

                <span class="vuln-sort-count muted">{{ sortedVulnFindings.length }} of {{ vulnFindings.length }}</span>
              </div>

              <!-- Severity summary strip -->
              <div class="vuln-severity-summary">
                <span v-if="vulnCountBySeverity.critical" class="sev-chip sev-chip-critical">{{ vulnCountBySeverity.critical }} Critical</span>
                <span v-if="vulnCountBySeverity.high"     class="sev-chip sev-chip-high"    >{{ vulnCountBySeverity.high }} High</span>
                <span v-if="vulnCountBySeverity.medium"   class="sev-chip sev-chip-medium"  >{{ vulnCountBySeverity.medium }} Medium</span>
                <span v-if="vulnCountBySeverity.low"      class="sev-chip sev-chip-low"     >{{ vulnCountBySeverity.low }} Low</span>
                <span v-if="vulnCountBySeverity.unknown"  class="sev-chip sev-chip-unknown" >{{ vulnCountBySeverity.unknown }} Unknown</span>
                <span class="sev-total muted">{{ vulnFindings.length }} finding{{ vulnFindings.length !== 1 ? "s" : "" }} total</span>
              </div>

              <!-- Findings cards -->
              <div class="vuln-list">
                <div
                  v-for="f in sortedVulnFindings"
                  :key="f.id"
                  class="vuln-card"
                  :class="[`vuln-card-${(f.severity || 'unknown').toLowerCase()}`, { 'vuln-card-expanded': expandedFindingId === f.id }]"
                  role="button"
                  tabindex="0"
                  :aria-expanded="expandedFindingId === f.id"
                  @click="toggleFinding(f.id)"
                  @keydown.enter.prevent="toggleFinding(f.id)"
                  @keydown.space.prevent="toggleFinding(f.id)"
                >
                  <!-- Row 1: CVE ID + aliases + severity badge + CVSS score + chevron -->
                  <div class="vuln-card-top">
                    <div class="vuln-id-group">
                      <code class="vuln-id">{{ f.vuln_id }}</code>
                      <span v-if="f.aliases_json.length" class="vuln-aliases muted" :title="f.aliases_json.join(', ')">
                        +{{ f.aliases_json.length }} alias{{ f.aliases_json.length !== 1 ? "es" : "" }}
                      </span>
                    </div>
                    <div class="vuln-badge-group">
                      <!-- Source attribution badges — which scanner(s) found this CVE -->
                      <span
                        v-for="src in (f.sources_json ?? ['osv'])"
                        :key="src"
                        class="source-badge"
                        :class="`source-badge-${src}`"
                        :title="`Detected by ${src.toUpperCase()}`"
                      >{{ src.toUpperCase() }}</span>
                      <span class="severity-badge" :class="f.severity ? `severity-${f.severity.toLowerCase()}` : 'severity-unknown'">
                        {{ f.severity ?? "UNKNOWN" }}
                      </span>
                      <span v-if="f.cvss_score !== null" class="cvss-score">CVSS&nbsp;{{ f.cvss_score.toFixed(1) }}</span>
                      <!-- EPSS exploit probability badge — colour-coded by risk tier -->
                      <span
                        v-if="f.epss_score !== null && f.epss_score !== undefined"
                        class="epss-badge"
                        :class="epssClass(f.epss_score)"
                        :title="`EPSS: ${(f.epss_score * 100).toFixed(2)}% exploit probability (${f.epss_percentile !== null && f.epss_percentile !== undefined ? (f.epss_percentile * 100).toFixed(0) + 'th percentile' : 'percentile n/a'})`"
                      >EPSS&nbsp;{{ (f.epss_score * 100).toFixed(1) }}%</span>
                      <!-- Expand/collapse chevron -->
                      <svg
                        class="vuln-chevron"
                        :class="{ 'vuln-chevron-open': expandedFindingId === f.id }"
                        viewBox="0 0 16 16"
                        fill="none"
                        xmlns="http://www.w3.org/2000/svg"
                      >
                        <path d="M4 6l4 4 4-4" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
                      </svg>
                    </div>
                  </div>

                  <!-- Row 2: Component name + version -->
                  <div class="vuln-component-row">
                    <svg class="vuln-pkg-icon" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg">
                      <path d="M8 1L14 4.5V11.5L8 15L2 11.5V4.5L8 1Z" stroke="currentColor" stroke-width="1.3" stroke-linejoin="round"/>
                      <path d="M8 1V15M2 4.5L8 8L14 4.5" stroke="currentColor" stroke-width="1.3" stroke-linejoin="round"/>
                    </svg>
                    <span class="vuln-component-name">{{ f.component_name }}</span>
                    <span v-if="f.component_version" class="vuln-component-version">@{{ f.component_version }}</span>
                  </div>

                  <!-- Row 3: Summary text (collapsed: 2-line clamp) -->
                  <p v-if="f.summary" class="vuln-summary-text" :class="{ 'vuln-summary-full': expandedFindingId === f.id }">{{ f.summary }}</p>

                  <!-- Row 4: Footer — fixed-in · published · report badge -->
                  <div class="vuln-card-footer">
                    <span v-if="f.fixed_in_versions_json.length" class="vuln-fixed">
                      Fixed in: <code>{{ f.fixed_in_versions_json.slice(0, 3).join(", ") }}{{ !expandedFindingId && f.fixed_in_versions_json.length > 3 ? "…" : "" }}</code>
                    </span>
                    <span v-else class="vuln-no-fix">No fix available</span>
                    <span class="vuln-footer-spacer" />
                    <span v-if="f.published_at" class="vuln-published muted">Published {{ formatDate(f.published_at) }}</span>
                    <span v-if="f.linked_report_id" class="vuln-linked-badge">Report linked ✓</span>
                  </div>

                  <!-- ── Expanded detail section ── -->
                  <div v-if="expandedFindingId === f.id" class="vuln-detail-body" @click.stop>

                    <!-- Aliases -->
                    <div v-if="f.aliases_json.length" class="vuln-detail-row">
                      <span class="vuln-detail-label">Also known as</span>
                      <div class="vuln-aliases-list">
                        <code v-for="alias in f.aliases_json" :key="alias" class="vuln-alias-chip">{{ alias }}</code>
                      </div>
                    </div>

                    <!-- CVSS -->
                    <div v-if="f.cvss_score !== null || f.cvss_vector" class="vuln-detail-row">
                      <span class="vuln-detail-label">CVSS</span>
                      <div class="vuln-detail-value">
                        <span v-if="f.cvss_score !== null" class="vuln-cvss-score-large">{{ f.cvss_score.toFixed(1) }}</span>
                        <code v-if="f.cvss_vector" class="vuln-cvss-vector">{{ f.cvss_vector }}</code>
                      </div>
                    </div>

                    <!-- Component purl -->
                    <div v-if="f.component_purl" class="vuln-detail-row">
                      <span class="vuln-detail-label">Package URL</span>
                      <code class="vuln-purl">{{ f.component_purl }}</code>
                    </div>

                    <!-- Fix info -->
                    <div class="vuln-detail-row">
                      <span class="vuln-detail-label">Fix available</span>
                      <div v-if="f.fixed_in_versions_json.length" class="vuln-aliases-list">
                        <code v-for="v in f.fixed_in_versions_json" :key="v" class="vuln-alias-chip vuln-fix-chip">{{ v }}</code>
                      </div>
                      <span v-else class="vuln-no-fix">No fix available</span>
                    </div>

                    <!-- Dates -->
                    <div v-if="f.published_at" class="vuln-detail-row">
                      <span class="vuln-detail-label">Published</span>
                      <span class="vuln-detail-value">{{ formatDate(f.published_at) }}</span>
                    </div>

                    <!-- External links -->
                    <div class="vuln-detail-actions">
                      <a
                        v-if="f.vuln_id.startsWith('CVE-') || f.vuln_id.startsWith('UBUNTU-CVE-')"
                        :href="nvdUrl(f.vuln_id)"
                        target="_blank"
                        rel="noopener noreferrer"
                        class="btn btn-secondary btn-xs"
                        @click.stop
                      >
                        View on NVD ↗
                      </a>
                      <a
                        :href="osvUrl(f.vuln_id)"
                        target="_blank"
                        rel="noopener noreferrer"
                        class="btn btn-secondary btn-xs"
                        @click.stop
                      >
                        View on OSV ↗
                      </a>
                      <span v-if="f.linked_report_id" class="vuln-linked-badge">
                        Vulnerability report linked ✓
                      </span>
                    </div>
                  </div>
                </div>
              </div>
            </template>
          </div>

        </div><!-- end tab-scroll-area -->
      </div><!-- end sbom-analysis-pane -->
    </div><!-- end sbom-detail-layout -->

    <template #footer>
      <button
        v-if="detailItem.sbom_content"
        class="btn btn-secondary"
        :disabled="isReanalyzing"
        @click="reanalyzeRecord"
      >
        {{ isReanalyzing ? "Analyzing…" : "Re-analyze" }}
      </button>
      <button class="btn btn-danger-outline" :disabled="isDeleting" @click="deleteRecord">
        {{ isDeleting ? "Deleting…" : "Delete" }}
      </button>
      <button class="btn btn-secondary" @click="showDetailModal = false">Close</button>
    </template>
  </AppModal>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref, watch } from "vue";

import AppModal from "@/components/AppModal.vue";
import { apiClient } from "@/services/api";
import { sbomRecordService } from "@/services/sbom-record-service";
import type {
  ProductReleaseSummaryRead,
  ProductSummaryRead,
  SbomFormat,
  SbomRecordCreate,
  SbomRecordRead,
  SbomVulnerabilityFindingRead,
} from "@/types/product";

const isLoadingProducts = ref(false);
const isLoadingReleases = ref(false);
const isLoading = ref(false);
const isCreating = ref(false);
const isUploading = ref(false);
const isDeleting = ref(false);
const isReanalyzing = ref(false);
const isImporting = ref(false);
const isScanningVulns = ref(false);
const errorMessage = ref("");
const successMessage = ref("");
const showCreateModal = ref(false);
const showUploadModal = ref(false);
const showDetailModal = ref(false);
const detailItem = ref<SbomRecordRead | null>(null);
const activeDetailTab = ref("overview");
const vulnFindings = ref<SbomVulnerabilityFindingRead[]>([]);
const vulnScanError = ref("");
const expandedFindingId = ref<string | null>(null);
const vulnSortKey = ref<"epss" | "cvss" | "severity" | "none">("none");
const vulnSortDir = ref<"asc" | "desc">("desc");
const vulnSourceFilter = ref<"all" | "osv" | "trivy">("all");

const products = ref<ProductSummaryRead[]>([]);
const releases = ref<ProductReleaseSummaryRead[]>([]);
const records = ref<SbomRecordRead[]>([]);

const productQuery = ref("");
const selectedProductId = ref("");
const selectedReleaseId = ref("");

const fileInput = ref<HTMLInputElement | null>(null);

// Detail tabs — Overview is replaced by the permanent sidebar
const detailTabs = [
  { id: "compliance", label: "CRA" },
  { id: "quality", label: "Quality" },
  { id: "diff", label: "Differential analysis" },
  { id: "vulnerabilities", label: "Vulnerabilities" },
];

const createForm = reactive({
  product_release_id: "",
  format: "cyclonedx" as SbomFormat,
  spec_version: "",
  tool_name: "",
  tool_version: "",
  file_name: "",
  generated_at: "",
  notes: "",
  component_count: null as number | null,
});

const uploadForm = reactive({
  product_release_id: "",
  file: null as File | null,
  notes: "",
});

// Computed helpers for detail modal analysis findings

// validate output is a list of per-standard results:
// [ { level: "CraPhase2", is_compliant: bool, violations: [...] }, ... ]
const validateList = computed((): Record<string, unknown>[] => {
  const f = detailItem.value?.analysis_findings;
  if (!f) return [];
  const v = f.validate;
  if (Array.isArray(v)) return v as Record<string, unknown>[];
  return [];
});

const qualityReport = computed((): Record<string, unknown> | null => {
  const f = detailItem.value?.analysis_findings;
  if (!f) return null;
  const q = f.quality as Record<string, unknown> | undefined;
  if (!q) return null;
  // score and recommendations live under q.report
  return (q.report as Record<string, unknown>) ?? q;
});

const qualityRecommendations = computed((): unknown[] => {
  const r = qualityReport.value;
  if (!r) return [];
  const recs = r.recommendations;
  if (Array.isArray(recs)) return recs;
  return [];
});

const diffFindings = computed(() => {
  const f = detailItem.value?.analysis_findings;
  if (!f) return null;
  return (f.diff as Record<string, unknown>) ?? null;
});

const diffAdded = computed((): unknown[] => {
  const d = diffFindings.value;
  if (!d) return [];
  for (const key of ["added", "new_components", "additions"]) {
    const val = d[key];
    if (Array.isArray(val)) return val;
  }
  return [];
});

const diffRemoved = computed((): unknown[] => {
  const d = diffFindings.value;
  if (!d) return [];
  for (const key of ["removed", "deleted_components", "removals"]) {
    const val = d[key];
    if (Array.isArray(val)) return val;
  }
  return [];
});

const diffChanged = computed((): unknown[] => {
  const d = diffFindings.value;
  if (!d) return [];
  for (const key of ["changed", "modified_components", "modifications", "updated"]) {
    const val = d[key];
    if (Array.isArray(val)) return val;
  }
  return [];
});

const filteredProducts = computed(() => {
  const q = productQuery.value.trim().toLowerCase();
  const sorted = [...products.value].sort((a, b) => a.name.localeCompare(b.name));
  if (!q) return sorted;
  return sorted.filter((p) =>
    [p.name, p.product_code].join(" ").toLowerCase().includes(q),
  );
});

function qualityClass(score: number): string {
  if (score >= 80) return "quality-high";
  if (score >= 50) return "quality-medium";
  return "quality-low";
}

// Maps sbom-tools internal standard identifiers to human-readable names + descriptions.
const STANDARD_META: Record<string, { name: string; description: string }> = {
  CraPhase2: {
    name: "EU Cyber Resilience Act — Phase 2",
    description:
      "Checks SBOM completeness against the requirements of the EU Cyber Resilience Act (CRA), " +
      "Annex I Part II §1. Phase 2 corresponds to the obligations that apply to manufacturers " +
      "of products with digital elements from August 2027.",
  },
  NtiaMinimum: {
    name: "NTIA Minimum Elements",
    description:
      "Checks the seven minimum data fields defined by the US National Telecommunications and " +
      "Information Administration (NTIA): supplier name, component name, component display_version, " +
      "other unique identifiers, dependency relationships, author of SBOM data, and timestamp.",
  },
};

function standardName(level: unknown): string {
  return STANDARD_META[String(level)]?.name ?? String(level);
}

function standardDescription(level: unknown): string {
  return STANDARD_META[String(level)]?.description ?? "";
}

function violationErrors(violations: Record<string, unknown>[]): Record<string, unknown>[] {
  return violations.filter((v) => v.severity === "Error");
}

function violationWarnings(violations: Record<string, unknown>[]): Record<string, unknown>[] {
  return violations.filter((v) => v.severity !== "Error");
}

function formatDate(val: string | null | undefined): string {
  if (!val) return "—";
  return new Date(val).toLocaleDateString(undefined, { dateStyle: "medium" });
}

function toIsoOrNull(val: string): string | null {
  if (!val) return null;
  return val.includes("T") ? new Date(val).toISOString() : `${val}T00:00:00Z`;
}

function formatComponent(c: unknown): string {
  if (typeof c === "string") return c;
  if (c && typeof c === "object") {
    const obj = c as Record<string, unknown>;
    const name = obj.name ?? obj.component ?? "";
    const display_version = obj.display_version ? `@${obj.display_version}` : "";
    return `${name}${display_version}`;
  }
  return JSON.stringify(c);
}

function onFileChange(event: Event): void {
  const input = event.target as HTMLInputElement;
  uploadForm.file = input.files?.[0] ?? null;
}

async function loadProducts(): Promise<void> {
  isLoadingProducts.value = true;
  try {
    const { data } = await apiClient.get<ProductSummaryRead[]>("/products/");
    products.value = data;
  } finally {
    isLoadingProducts.value = false;
  }
}

async function loadReleases(productId: string): Promise<void> {
  isLoadingReleases.value = true;
  releases.value = [];
  try {
    const { data } = await apiClient.get<{ releases: ProductReleaseSummaryRead[] }>(
      `/products/${productId}`,
    );
    releases.value = data.releases ?? [];
  } finally {
    isLoadingReleases.value = false;
  }
}

async function loadSbomRecords(): Promise<void> {
  isLoading.value = true;
  errorMessage.value = "";
  try {
    const params: Record<string, string> = {};
    if (selectedReleaseId.value) {
      params.product_release_id = selectedReleaseId.value;
    } else if (selectedProductId.value) {
      params.product_id = selectedProductId.value;
    }
    const { data } = await apiClient.get<SbomRecordRead[]>("/sbom-records/", { params });
    records.value = data;
  } catch {
    errorMessage.value = "Failed to load SBOM records.";
  } finally {
    isLoading.value = false;
  }
}

watch(selectedProductId, (id) => {
  releases.value = [];
  selectedReleaseId.value = "";
  if (id) loadReleases(id);
  loadSbomRecords();
});

watch(selectedReleaseId, (id) => {
  createForm.product_release_id = id;
  uploadForm.product_release_id = id;
  loadSbomRecords();
});

async function createRecord(): Promise<void> {
  isCreating.value = true;
  errorMessage.value = "";
  try {
    const payload: SbomRecordCreate = {
      product_release_id: createForm.product_release_id,
      format: createForm.format,
      spec_version: createForm.spec_version || null,
      tool_name: createForm.tool_name || null,
      tool_version: createForm.tool_version || null,
      file_name: createForm.file_name || null,
      generated_at: toIsoOrNull(createForm.generated_at),
      notes: createForm.notes || null,
      component_count: createForm.component_count,
    };
    await sbomRecordService.create(payload);
    showCreateModal.value = false;
    successMessage.value = "SBOM record created.";
    Object.assign(createForm, {
      product_release_id: selectedReleaseId.value,
      format: "cyclonedx",
      spec_version: "",
      tool_name: "",
      tool_version: "",
      file_name: "",
      generated_at: "",
      notes: "",
      component_count: null,
    });
    await loadSbomRecords();
  } catch (err) {
    errorMessage.value = err instanceof Error ? err.message : "Failed to create SBOM record.";
  } finally {
    isCreating.value = false;
  }
}

async function uploadRecord(): Promise<void> {
  if (!uploadForm.file || !uploadForm.product_release_id) return;
  isUploading.value = true;
  errorMessage.value = "";
  try {
    const formData = new FormData();
    formData.append("product_release_id", uploadForm.product_release_id);
    formData.append("file", uploadForm.file);
    if (uploadForm.notes) formData.append("notes", uploadForm.notes);
    await apiClient.post("/sbom-records/upload", formData, {
      headers: { "Content-Type": "multipart/form-data" },
    });
    showUploadModal.value = false;
    successMessage.value = "SBOM uploaded and analyzed successfully.";
    Object.assign(uploadForm, { product_release_id: selectedReleaseId.value, file: null, notes: "" });
    if (fileInput.value) fileInput.value.value = "";
    await loadSbomRecords();
  } catch (err) {
    errorMessage.value = err instanceof Error ? err.message : "Failed to upload SBOM.";
  } finally {
    isUploading.value = false;
  }
}

function openDetail(item: SbomRecordRead): void {
  detailItem.value = item;
  activeDetailTab.value = "compliance";
  showDetailModal.value = true;
}

async function importFromArtifact(): Promise<void> {
  if (!selectedReleaseId.value) return;
  isImporting.value = true;
  errorMessage.value = "";
  try {
    await apiClient.post("/sbom-records/import-from-artifact", null, {
      params: { product_release_id: selectedReleaseId.value },
    });
    successMessage.value = "SBOM imported from release gate artifact and analyzed successfully.";
    await loadSbomRecords();
  } catch (err) {
    errorMessage.value =
      err instanceof Error ? err.message : "No SBOM artifact found in the release gate for this release.";
  } finally {
    isImporting.value = false;
  }
}

async function reanalyzeRecord(): Promise<void> {
  if (!detailItem.value) return;
  isReanalyzing.value = true;
  errorMessage.value = "";
  try {
    const { data } = await apiClient.post<SbomRecordRead>(
      `/sbom-records/${detailItem.value.id}/analyze`,
    );
    detailItem.value = data;
    successMessage.value = "Re-analysis complete.";
    // Refresh the list too
    await loadSbomRecords();
  } catch {
    errorMessage.value = "Re-analysis failed.";
  } finally {
    isReanalyzing.value = false;
  }
}

async function deleteRecord(): Promise<void> {
  if (!detailItem.value) return;
  isDeleting.value = true;
  try {
    await sbomRecordService.remove(detailItem.value.id);
    showDetailModal.value = false;
    detailItem.value = null;
    successMessage.value = "SBOM record deleted.";
    await loadSbomRecords();
  } catch {
    errorMessage.value = "Failed to delete SBOM record.";
  } finally {
    isDeleting.value = false;
  }
}

async function loadVulnFindings(sbomId: string): Promise<void> {
  try {
    vulnFindings.value = await sbomRecordService.listVulnerabilityFindings(sbomId);
  } catch {
    vulnFindings.value = [];
  }
}

async function scanVulnerabilities(): Promise<void> {
  if (!detailItem.value) return;
  isScanningVulns.value = true;
  vulnScanError.value = "";
  errorMessage.value = "";
  try {
    const result = await sbomRecordService.scanVulnerabilities(detailItem.value.id);
    await loadVulnFindings(detailItem.value.id);

    if (!result.osv_reachable) {
      vulnScanError.value = "OSV vulnerability database unreachable — check backend internet connectivity. No findings were recorded.";
    } else if (result.components_scanned === 0) {
      vulnScanError.value = "No components with a recognised ecosystem PURL found. Upload a CycloneDX or SPDX SBOM with package URLs to enable scanning.";
    } else {
      // Build a human-readable per-scanner breakdown
      const ps = result.per_scanner ?? {};
      const scannerParts: string[] = [];
      if ((ps.osv ?? 0) > 0)   scannerParts.push(`OSV: ${ps.osv}`);
      if ((ps.trivy ?? 0) > 0) scannerParts.push(`Trivy: ${ps.trivy}`);
      if ((ps.both ?? 0) > 0)  scannerParts.push(`Both: ${ps.both}`);
      const scannerDetail = scannerParts.length ? ` (${scannerParts.join(" · ")})` : "";
      const nvdDetail = (result.nvd_enrichments ?? 0) > 0 ? ` · NVD enriched ${result.nvd_enrichments}` : "";
      const trivyNote = result.trivy_available === false ? " · Trivy not installed" : "";

      successMessage.value =
        `Scanned ${result.components_scanned} component${result.components_scanned !== 1 ? "s" : ""} — ` +
        `${result.findings_created} new finding${result.findings_created !== 1 ? "s" : ""}, ` +
        `${result.reports_created} report${result.reports_created !== 1 ? "s" : ""} created.` +
        scannerDetail + nvdDetail + trivyNote;
    }
  } catch {
    vulnScanError.value = "Scan request failed. Check that the backend is running and try again.";
  } finally {
    isScanningVulns.value = false;
  }
}

/* Severity rank for sorting */
const SEVERITY_RANK: Record<string, number> = { critical: 4, high: 3, medium: 2, low: 1, informational: 0 };

/* Findings after source filter + sort applied */
const sortedVulnFindings = computed(() => {
  let list = vulnFindings.value;

  /* Source filter */
  if (vulnSourceFilter.value !== "all") {
    list = list.filter((f) => (f.sources_json ?? ["osv"]).includes(vulnSourceFilter.value));
  }

  /* Sort */
  if (vulnSortKey.value === "none") return list;
  const dir = vulnSortDir.value === "asc" ? 1 : -1;
  return [...list].sort((a, b) => {
    if (vulnSortKey.value === "epss") {
      return ((a.epss_score ?? -1) - (b.epss_score ?? -1)) * dir;
    }
    if (vulnSortKey.value === "cvss") {
      return ((a.cvss_score ?? -1) - (b.cvss_score ?? -1)) * dir;
    }
    if (vulnSortKey.value === "severity") {
      const ra = SEVERITY_RANK[a.severity?.toLowerCase() ?? ""] ?? -1;
      const rb = SEVERITY_RANK[b.severity?.toLowerCase() ?? ""] ?? -1;
      return (ra - rb) * dir;
    }
    return 0;
  });
});

function toggleVulnSort(key: typeof vulnSortKey.value): void {
  if (vulnSortKey.value === key) {
    vulnSortDir.value = vulnSortDir.value === "asc" ? "desc" : "asc";
  } else {
    vulnSortKey.value = key;
    vulnSortDir.value = "desc";
  }
}

// Severity breakdown for the summary strip
const vulnCountBySeverity = computed(() => {
  const counts: Record<string, number> = { critical: 0, high: 0, medium: 0, low: 0, unknown: 0 };
  for (const f of vulnFindings.value) {
    const key = (f.severity ?? "unknown").toLowerCase();
    counts[key] = (counts[key] ?? 0) + 1;
  }
  return counts;
});

function toggleFinding(id: string): void {
  expandedFindingId.value = expandedFindingId.value === id ? null : id;
}

/**
 * Returns a CSS class for the EPSS badge based on exploit probability tiers.
 * > 10% → high risk (red), 1–10% → medium (amber), < 1% → low (grey).
 */
function epssClass(score: number): string {
  if (score >= 0.10) return "epss-high";
  if (score >= 0.01) return "epss-medium";
  return "epss-low";
}

function nvdUrl(vulnId: string): string {
  // Extract canonical CVE ID from Ubuntu advisory IDs like "UBUNTU-CVE-2022-1234"
  const cveMatch = vulnId.match(/CVE-\d{4}-\d+/);
  const cveId = cveMatch ? cveMatch[0] : vulnId;
  return `https://nvd.nist.gov/vuln/detail/${cveId}`;
}

function osvUrl(vulnId: string): string {
  return `https://osv.dev/vulnerability/${vulnId}`;
}

// Load vulnerability findings when the tab becomes active
watch(activeDetailTab, (tab) => {
  if (tab === "vulnerabilities" && detailItem.value) {
    expandedFindingId.value = null;
    loadVulnFindings(detailItem.value.id);
  }
});

onMounted(async () => {
  await loadProducts();
  loadSbomRecords();
});
</script>

<style scoped>
/* ── Page layout ── */
.page-actions {
  display: flex;
  align-items: flex-end;
  gap: 0.75rem;
  flex-wrap: wrap;
}

/* ── Buttons ── */
.btn {
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
  border: 1px solid transparent;
  border-radius: 0.85rem;
  padding: 0.6rem 1.1rem;
  font: inherit;
  font-size: var(--text-sm);
  font-weight: 600;
  cursor: pointer;
  transition: opacity 0.12s, transform 0.12s, box-shadow 0.12s;
  white-space: nowrap;
}

.btn:disabled { opacity: 0.55; cursor: not-allowed; }

.btn-primary {
  background: linear-gradient(135deg, rgba(175, 214, 46, 0.95), rgba(28, 107, 39, 0.95));
  color: #fff;
  box-shadow: 0 6px 16px rgba(28, 107, 39, 0.22);
}

.btn-primary:not(:disabled):hover {
  transform: translateY(-1px);
  box-shadow: 0 10px 20px rgba(28, 107, 39, 0.3);
}

.btn-secondary {
  background: transparent;
  border-color: var(--color-border);
  color: inherit;
}

.btn-secondary:not(:disabled):hover { background: var(--color-surface-elevated); }

.btn-danger-outline {
  background: transparent;
  border-color: var(--color-danger-border);
  color: var(--color-danger-text);
}

.btn-danger-outline:not(:disabled):hover { background: var(--color-danger-bg); }

/* ── Feedback banners ── */
.feedback {
  padding: 0.85rem 1.1rem;
  border-radius: 1rem;
  font-size: var(--text-sm);
  border: 1px solid transparent;
}

.feedback-error   { background: var(--color-danger-bg);  border-color: var(--color-danger-border);  color: var(--color-danger-text); }
.feedback-success { background: var(--color-success-bg); border-color: var(--color-success-border); color: var(--color-success-text); }

/* ── Empty / loading panel ── */
.empty-panel {
  padding: 2rem 1rem;
  text-align: center;
  color: var(--color-text-muted);
  font-size: var(--text-sm);
}

/* ── Form ── */
.form-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 1rem;
}

.field { display: grid; gap: 0.4rem; }
.field-label { font-size: var(--text-sm); font-weight: 600; color: var(--color-text-muted); }
.field-span-2 { grid-column: span 2; }
.req { color: var(--color-danger-text); }
.hint { font-size: var(--text-xs); color: var(--color-text-muted); margin-top: 0.2rem; }

input, select, textarea {
  width: 100%;
  padding: 0.65rem 0.9rem;
  border-radius: 0.75rem;
  border: 1px solid var(--color-border);
  background: var(--color-surface-soft);
  color: inherit;
  font: inherit;
}

input:focus, select:focus, textarea:focus {
  outline: none;
  border-color: rgba(175, 214, 46, 0.45);
  box-shadow: 0 0 0 3px rgba(112, 185, 23, 0.12);
}

/* File input has its own look */
.file-input { padding: 0.45rem 0.9rem; }

/* ── Table ── */
.table-wrapper { overflow-x: auto; }

.data-table {
  width: 100%;
  border-collapse: collapse;
}

.data-table th, .data-table td {
  padding: 0.8rem 0.75rem;
  text-align: left;
  border-bottom: 1px solid var(--color-divider);
  vertical-align: middle;
}

.data-table th {
  color: var(--color-text-muted);
  font-size: var(--text-xs);
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  white-space: nowrap;
}

.data-table tbody tr:last-child td { border-bottom: none; }
.table-row-clickable { cursor: pointer; transition: background 0.12s; }
.table-row-clickable:hover { background: var(--color-surface-elevated); }
.table-row-clickable:focus-visible { outline: 2px solid var(--color-primary); outline-offset: -2px; }

/* ── Format badges ── */
.format-badge {
  display: inline-block;
  padding: 0.15rem 0.55rem;
  border-radius: 999px;
  font-size: var(--text-xs);
  font-weight: 700;
  letter-spacing: 0.04em;
}

.format-cyclonedx { background: var(--color-info-bg);     color: var(--color-info-text);     border: 1px solid var(--color-info-border); }
.format-spdx      { background: var(--color-purple-bg);   color: var(--color-purple-text);   border: 1px solid rgba(139, 92, 246, 0.3); }
.format-swid      { background: var(--color-warning-bg);  color: var(--color-warning-text);  border: 1px solid var(--color-warning-border); }
.format-other     { background: var(--color-slate-bg);    color: var(--color-slate-text);    border: 1px solid var(--color-slate-border); }

/* ── Quality score badge ── */
.quality-badge {
  display: inline-block;
  padding: 0.15rem 0.6rem;
  border-radius: 999px;
  font-size: var(--text-xs);
  font-weight: 700;
  letter-spacing: 0.03em;
  border: 1px solid transparent;
}

.quality-high   { background: var(--color-success-bg); color: var(--color-success-text); border-color: var(--color-success-border); }
.quality-medium { background: var(--color-warning-bg); color: var(--color-warning-text); border-color: var(--color-warning-border); }
.quality-low    { background: var(--color-danger-bg);  color: var(--color-danger-text);  border-color: var(--color-danger-border); }

.component-count { font-weight: 700; font-size: var(--text-sm); }
.file-name { font-family: monospace; font-size: var(--text-xs); }

/* ── Two-column detail layout ── */
.sbom-detail-layout {
  display: flex;
  gap: 0;
  height: 460px; /* fixed — modal never resizes when switching tabs */
}

/* ── Left sidebar ── */
.sbom-sidebar {
  width: 200px;
  flex-shrink: 0;
  padding-right: 1.25rem;
  border-right: 1px solid var(--color-border);
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 0.9rem;
  scrollbar-width: thin;
  scrollbar-color: var(--color-border) transparent;
}

.sidebar-score-hero {
  display: flex;
  flex-direction: column;
  gap: 0.2rem;
  padding-bottom: 0.1rem;
}

.sidebar-score-label {
  font-size: var(--text-xs);
  font-weight: 600;
  color: var(--color-text-muted);
  text-transform: uppercase;
  letter-spacing: 0.06em;
}

.sidebar-score-value {
  font-size: 2.4rem;
  font-weight: 800;
  line-height: 1;
  padding: 0.3rem 0.6rem;
  border-radius: 0.65rem;
  border: 1px solid transparent;
  align-self: flex-start;
}

.score-denom { font-size: var(--text-base); font-weight: 500; opacity: 0.6; }

.sidebar-grade-row {
  display: flex;
  align-items: center;
  gap: 0.35rem;
  margin-top: 0.1rem;
}

.sidebar-grade {
  font-size: var(--text-xs);
  font-weight: 700;
  color: var(--color-text-muted);
  letter-spacing: 0.04em;
}

.grade-info-icon {
  font-size: var(--text-xs);
  color: var(--color-text-muted);
  cursor: help;
  opacity: 0.7;
  user-select: none;
}

/* Compliance status pills in sidebar */
.sidebar-compliance-pills {
  display: flex;
  flex-wrap: wrap;
  gap: 0.35rem;
}

.compliance-pill {
  display: inline-block;
  padding: 0.18rem 0.55rem;
  border-radius: 999px;
  font-size: var(--text-xs);
  font-weight: 700;
  letter-spacing: 0.04em;
  text-transform: uppercase;
  white-space: nowrap;
}

.pill-pass { background: var(--color-success-bg); color: var(--color-success-text); border: 1px solid var(--color-success-border); }
.pill-fail { background: var(--color-danger-bg);  color: var(--color-danger-text);  border: 1px solid var(--color-danger-border); }

.sidebar-divider {
  border: none;
  border-top: 1px solid var(--color-border);
  margin: 0;
}

/* Key-value pairs */
.sidebar-meta {
  display: grid;
  grid-template-columns: auto 1fr;
  gap: 0.45rem 0.65rem;
  align-items: start;
  margin: 0;
}

.sidebar-meta dt {
  font-size: var(--text-xs);
  font-weight: 600;
  color: var(--color-text-muted);
  white-space: nowrap;
  padding-top: 0.1rem;
}

.sidebar-meta dd {
  font-size: var(--text-xs);
  margin: 0;
  word-break: break-all;
}

/* Notes at the bottom of the sidebar */
.sidebar-notes {
  border-top: 1px solid var(--color-border);
  padding-top: 0.75rem;
}

.sidebar-notes-label {
  font-size: var(--text-xs);
  font-weight: 600;
  color: var(--color-text-muted);
  text-transform: uppercase;
  letter-spacing: 0.06em;
  display: block;
  margin-bottom: 0.3rem;
}

.sidebar-notes-text {
  font-size: var(--text-xs);
  margin: 0;
  color: var(--color-text-muted);
  line-height: 1.5;
}

/* ── Right analysis pane ── */
.sbom-analysis-pane {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-width: 0;
  padding-left: 1.25rem;
  overflow: hidden;
}

/* Tab bar */
.detail-tabs {
  display: flex;
  gap: 0;
  border-bottom: 1px solid var(--color-border);
  flex-shrink: 0;
}

.detail-tab {
  background: none;
  border: none;
  border-bottom: 2px solid transparent;
  padding: 0.55rem 1rem;
  font: inherit;
  font-size: var(--text-sm);
  font-weight: 600;
  color: var(--color-text-muted);
  cursor: pointer;
  margin-bottom: -1px;
  transition: color 0.12s, border-color 0.12s;
}

.detail-tab:hover { color: inherit; }
.detail-tab.active { color: inherit; border-bottom-color: rgba(175, 214, 46, 0.9); }

/* Scrollable tab content — fills remaining height, never changes size */
.tab-scroll-area {
  flex: 1;
  overflow-y: auto;
  padding-top: 0.9rem;
  scrollbar-width: thin;
  scrollbar-color: var(--color-border) transparent;
}

.tab-panel { /* no min-height — parent is fixed-height */ }

.tab-section-title {
  font-size: var(--text-sm);
  font-weight: 700;
  color: var(--color-text-muted);
  margin: 0 0 0.6rem;
}

/* ── Compliance tab ── */
.compliance-verdict {
  display: inline-block;
  padding: 0.2rem 0.7rem;
  border-radius: 999px;
  font-size: var(--text-xs);
  font-weight: 700;
  letter-spacing: 0.05em;
}

.verdict-pass { background: var(--color-success-bg); color: var(--color-success-text); border: 1px solid var(--color-success-border); }
.verdict-fail { background: var(--color-danger-bg);  color: var(--color-danger-text);  border: 1px solid var(--color-danger-border); }

.standards-list { display: flex; flex-direction: column; gap: 1rem; }

.standard-block {
  padding: 0.85rem;
  border-radius: 0.75rem;
  border: 1px solid var(--color-border);
  background: var(--color-surface-soft);
}

.standard-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 0.75rem;
  margin-bottom: 0.65rem;
}

.standard-name-group {
  display: flex;
  flex-direction: column;
  gap: 0.2rem;
  flex: 1;
  min-width: 0;
}

.standard-name {
  font-size: var(--text-sm);
  font-weight: 700;
}

.standard-desc {
  font-size: var(--text-xs);
  color: var(--color-text-muted);
  line-height: 1.45;
}

/* Violation group (errors / warnings) */
.violation-group { margin-bottom: 0.65rem; }
.violation-group:last-child { margin-bottom: 0; }

.violation-group-label {
  display: inline-block;
  font-size: var(--text-xs);
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  margin-bottom: 0.35rem;
  padding: 0.1rem 0.45rem;
  border-radius: 999px;
}

.violation-group-error {
  background: var(--color-danger-bg);
  color: var(--color-danger-text);
  border: 1px solid var(--color-danger-border);
}

.violation-group-warn {
  background: var(--color-warning-bg);
  color: var(--color-warning-text);
  border: 1px solid var(--color-warning-border);
}

.findings-list { margin: 0; padding-left: 0; list-style: none; display: flex; flex-direction: column; gap: 0.3rem; }
.finding-item { font-size: var(--text-sm); display: flex; align-items: baseline; gap: 0.4rem; flex-wrap: wrap; padding: 0.25rem 0; }
.finding-fail { color: var(--color-danger-text); }
.finding-warn { color: var(--color-warning-text); }
.finding-none { font-size: var(--text-sm); color: var(--color-text-muted); margin-top: 0.25rem; }
.finding-element { font-family: monospace; font-size: var(--text-xs); opacity: 0.7; }

/* ── Quality tab ── */
.rec-list { margin: 0; padding: 0; list-style: none; display: flex; flex-direction: column; gap: 0.5rem; }
.rec-item { display: flex; align-items: baseline; gap: 0.5rem; padding: 0.5rem 0.75rem; border-radius: 0.6rem; background: var(--color-surface-soft); border: 1px solid var(--color-border); font-size: var(--text-sm); flex-wrap: wrap; }
.rec-priority { font-size: var(--text-xs); font-weight: 800; color: var(--color-text-muted); flex-shrink: 0; min-width: 1.8rem; }
.rec-body { flex: 1; }
.rec-count { color: var(--color-text-muted); font-size: var(--text-xs); }
.rec-impact { font-size: var(--text-xs); font-weight: 700; color: var(--color-success-text); margin-left: auto; flex-shrink: 0; }
.recommendations { display: flex; flex-direction: column; gap: 0.5rem; }

/* ── Diff tab ── */
.diff-empty-state {
  padding: 1.25rem;
  border: 1px dashed var(--color-border);
  border-radius: 0.75rem;
  background: var(--color-surface-soft);
}

.diff-empty-title {
  font-weight: 700;
  font-size: var(--text-sm);
  margin: 0 0 0.5rem;
}

.diff-empty-hint {
  font-size: var(--text-sm);
  color: var(--color-text-muted);
  margin: 0;
  line-height: 1.55;
}

.diff-summary-bar {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  flex-wrap: wrap;
  padding: 0.6rem 0.85rem;
  border-radius: 0.65rem;
  background: var(--color-surface-soft);
  border: 1px solid var(--color-border);
  margin-bottom: 1rem;
  font-size: var(--text-xs);
}

.diff-summary-chip {
  font-weight: 700;
  padding: 0.15rem 0.55rem;
  border-radius: 999px;
}

.diff-chip-added   { background: var(--color-success-bg); color: var(--color-success-text); border: 1px solid var(--color-success-border); }
.diff-chip-removed { background: var(--color-danger-bg);  color: var(--color-danger-text);  border: 1px solid var(--color-danger-border); }
.diff-chip-changed { background: var(--color-warning-bg); color: var(--color-warning-text); border: 1px solid var(--color-warning-border); }

.diff-summary-note { color: var(--color-text-muted); margin-left: 0.25rem; }

.diff-context-note {
  font-size: var(--text-xs);
  color: var(--color-text-muted);
  margin: 0 0 0.75rem;
  padding: 0.5rem 0.75rem;
  border-left: 2px solid var(--color-border);
  line-height: 1.5;
}

.diff-section { margin-bottom: 1rem; }
.diff-added-title   { color: var(--color-success-text); }
.diff-removed-title { color: var(--color-danger-text);  }
.diff-changed-title { color: var(--color-warning-text); }

.diff-list { margin: 0.4rem 0 0; padding-left: 1.2rem; display: flex; flex-direction: column; gap: 0.2rem; }
.diff-item { font-size: var(--text-sm); font-family: monospace; }
.diff-item-added   { color: var(--color-success-text); }
.diff-item-removed { color: var(--color-danger-text);  }
.diff-item-changed { color: var(--color-warning-text); }

/* ── Raw JSON fallback ── */
.raw-json {
  background: var(--color-surface-soft);
  border: 1px solid var(--color-border);
  border-radius: 0.75rem;
  padding: 0.75rem;
  overflow-x: auto;
  overflow-y: auto;
}

.raw-json pre {
  margin: 0;
  font-size: var(--text-xs);
  font-family: monospace;
  white-space: pre-wrap;
  word-break: break-word;
}

.nowrap { white-space: nowrap; }
.row-arrow { color: var(--color-text-muted); font-size: var(--text-lg); text-align: right; opacity: 0; transition: opacity 0.12s; }
.table-row-clickable:hover .row-arrow,
.table-row-clickable:focus-visible .row-arrow { opacity: 1; }

/* ── Vulnerabilities tab ── */
.vuln-scan-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  margin-bottom: 0.85rem;
  flex-wrap: wrap;
}
.tab-description { margin: 0; font-size: var(--text-sm); }
.btn-sm { padding: 0.35rem 0.8rem; font-size: var(--text-sm); }

/* Severity summary strip */
.vuln-severity-summary {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  flex-wrap: wrap;
  margin-bottom: 0.85rem;
}

.sev-chip {
  display: inline-flex;
  align-items: center;
  gap: 0.25rem;
  padding: 0.2rem 0.65rem;
  border-radius: 999px;
  font-size: var(--text-xs);
  font-weight: 700;
  letter-spacing: 0.03em;
  border: 1px solid transparent;
}

.sev-chip-critical { background: #fff1f2; color: #991b1b; border-color: #fca5a5; }
.sev-chip-high     { background: #fff7ed; color: #9a3412; border-color: #fdba74; }
.sev-chip-medium   { background: #fffbeb; color: #92400e; border-color: #fcd34d; }
.sev-chip-low      { background: var(--color-info-bg); color: var(--color-info-text); border-color: var(--color-info-border); }
.sev-chip-unknown  { background: var(--color-surface-soft); color: var(--color-text-muted); border-color: var(--color-border); }
.sev-total         { font-size: var(--text-xs); margin-left: 0.25rem; }

/* Findings card list */
.vuln-list {
  display: flex;
  flex-direction: column;
  gap: 0.55rem;
}

.vuln-card {
  border: 1px solid var(--color-border);
  border-left-width: 3px;
  border-radius: 0.75rem;
  padding: 0.75rem 1rem;
  background: var(--color-surface-soft);
  display: flex;
  flex-direction: column;
  gap: 0.4rem;
}

/* Left-border accent per severity */
.vuln-card-critical { border-left-color: #ef4444; }
.vuln-card-high     { border-left-color: #f97316; }
.vuln-card-medium   { border-left-color: #f59e0b; }
.vuln-card-low      { border-left-color: var(--color-info-text, #3b82f6); }
.vuln-card-unknown  { border-left-color: var(--color-border); }

/* Top row: ID group + badge group */
.vuln-card-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.5rem;
  flex-wrap: wrap;
}

.vuln-id-group {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.vuln-id {
  font-family: monospace;
  font-size: var(--text-sm);
  font-weight: 700;
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  padding: 0.1rem 0.45rem;
  border-radius: 0.4rem;
}

.vuln-aliases {
  font-size: var(--text-xs);
  cursor: default;
}

.vuln-badge-group {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  flex-shrink: 0;
}

/* Severity fill badges */
.severity-badge {
  display: inline-block;
  padding: 0.18rem 0.6rem;
  border-radius: 999px;
  font-size: var(--text-xs);
  font-weight: 700;
  letter-spacing: 0.04em;
  text-transform: uppercase;
  border: 1px solid transparent;
}

.severity-critical { background: #fee2e2; color: #991b1b; border-color: #fca5a5; }
.severity-high     { background: #ffedd5; color: #9a3412; border-color: #fdba74; }
.severity-medium   { background: #fef9c3; color: #92400e; border-color: #fde047; }
.severity-low      { background: var(--color-info-bg); color: var(--color-info-text); border-color: var(--color-info-border); }
.severity-unknown  { background: var(--color-surface-soft); color: var(--color-text-muted); border-color: var(--color-border); }

.cvss-score {
  font-size: var(--text-xs);
  font-weight: 700;
  color: var(--color-text-muted);
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  padding: 0.15rem 0.45rem;
  border-radius: 0.4rem;
  font-family: monospace;
  white-space: nowrap;
}

/* Component row */
.vuln-component-row {
  display: flex;
  align-items: center;
  gap: 0.3rem;
  font-size: var(--text-sm);
}

.vuln-pkg-icon {
  width: 13px;
  height: 13px;
  color: var(--color-text-muted);
  flex-shrink: 0;
}

.vuln-component-name { font-weight: 600; }
.vuln-component-version { color: var(--color-text-muted); font-family: monospace; font-size: var(--text-xs); }

/* Summary line */
.vuln-summary-text {
  margin: 0;
  font-size: var(--text-sm);
  color: var(--color-text-muted);
  line-height: 1.45;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

/* Card footer */
.vuln-card-footer {
  display: flex;
  align-items: center;
  gap: 0.6rem;
  flex-wrap: wrap;
  padding-top: 0.25rem;
  border-top: 1px solid var(--color-divider);
  font-size: var(--text-xs);
  margin-top: 0.1rem;
}

.vuln-fixed code { font-family: monospace; font-size: var(--text-xs); }
.vuln-no-fix { color: var(--color-text-muted); font-style: italic; }
.vuln-footer-spacer { flex: 1; }
.vuln-published { }
.vuln-linked-badge {
  display: inline-flex;
  align-items: center;
  gap: 0.2rem;
  padding: 0.1rem 0.5rem;
  border-radius: 999px;
  background: var(--color-success-bg);
  color: var(--color-success-text);
  border: 1px solid var(--color-success-border);
  font-weight: 600;
  font-size: var(--text-xs);
}

/* ── Scanner source badges ── */
.source-badge {
  display: inline-flex;
  align-items: center;
  padding: 0.1rem 0.45rem;
  border-radius: 4px;
  font-size: var(--text-xs);
  font-weight: 700;
  letter-spacing: 0.04em;
  border: 1px solid transparent;
  line-height: 1.4;
}
/* OSV — blue */
.source-badge-osv    { background: #dbeafe; color: #1e40af; border-color: #bfdbfe; }
/* Trivy — purple */
.source-badge-trivy  { background: #ede9fe; color: #5b21b6; border-color: #ddd6fe; }
/* NVD — green */
.source-badge-nvd    { background: #dcfce7; color: #166534; border-color: #bbf7d0; }

/* ── EPSS exploit probability badge ── */
.epss-badge {
  display: inline-flex;
  align-items: center;
  padding: 0.15rem 0.45rem;
  border-radius: 4px;
  font-size: var(--text-xs);
  font-weight: 600;
  letter-spacing: 0.02em;
  border: 1px solid transparent;
  cursor: default;
}
/* > 10% — high exploit probability */
.epss-high   { background: #fee2e2; color: #991b1b; border-color: #fca5a5; }
/* 1–10% — moderate exploit probability */
.epss-medium { background: #fef3c7; color: #92400e; border-color: #fcd34d; }
/* < 1% — low exploit probability */
.epss-low    { background: #f3f4f6; color: #6b7280; border-color: #e5e7eb; }

:root[data-theme="light"] .epss-high   { background: #fee2e2; color: #7f1d1d; border-color: #f87171; }
:root[data-theme="light"] .epss-medium { background: #fef9c3; color: #713f12; border-color: #fde047; }
:root[data-theme="light"] .epss-low    { background: #f9fafb; color: #374151; border-color: #d1d5db; }

/* ── Vuln sort + source filter bar ── */
.vuln-sort-bar {
  display: flex;
  align-items: center;
  gap: 0.35rem;
  flex-wrap: wrap;
  margin-bottom: 0.65rem;
  padding: 0.4rem 0.6rem;
  background: var(--color-surface-soft);
  border: 1px solid var(--color-border);
  border-radius: 0.6rem;
}
.vuln-sort-label {
  font-size: var(--text-xs);
  font-weight: 600;
  color: var(--color-text-muted);
  text-transform: uppercase;
  letter-spacing: 0.05em;
  margin-right: 0.1rem;
}
.vuln-sort-divider {
  width: 1px;
  height: 14px;
  background: var(--color-border);
  margin: 0 0.3rem;
  flex-shrink: 0;
}
.vuln-sort-count {
  margin-left: auto;
  font-size: var(--text-xs);
}
.sort-btn {
  display: inline-flex;
  align-items: center;
  gap: 0.2rem;
  padding: 0.18rem 0.6rem;
  border-radius: 999px;
  border: 1px solid var(--color-border);
  background: transparent;
  font: inherit;
  font-size: var(--text-xs);
  font-weight: 600;
  color: var(--color-text-muted);
  cursor: pointer;
  transition: background 0.1s, color 0.1s, border-color 0.1s;
}
.sort-btn:hover { background: var(--color-surface-elevated); color: inherit; }
.sort-btn-active {
  background: rgba(175, 214, 46, 0.12);
  border-color: rgba(175, 214, 46, 0.5);
  color: inherit;
}
.sort-arrow { font-size: 0.8em; }

/* ── Scanner legend (shown in header below description) ── */
.scanner-legend {
  display: flex;
  flex-wrap: wrap;
  gap: 0.6rem 1.2rem;
}
.scanner-legend-item {
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
}
.scanner-legend-label {
  font-size: var(--text-xs);
  color: var(--color-text-muted);
}

/* ── Clickable vuln cards ── */
.vuln-card {
  cursor: pointer;
  transition: box-shadow 0.13s, border-color 0.13s, background 0.13s;
}
.vuln-card:hover {
  background: var(--color-surface-elevated, var(--color-surface-soft));
  box-shadow: 0 2px 8px rgba(0,0,0,0.07);
}
.vuln-card:focus-visible {
  outline: 2px solid rgba(175, 214, 46, 0.7);
  outline-offset: 1px;
}
.vuln-card-expanded {
  box-shadow: 0 3px 12px rgba(0,0,0,0.09);
}

/* Expand/collapse chevron */
.vuln-chevron {
  width: 14px;
  height: 14px;
  color: var(--color-text-muted);
  flex-shrink: 0;
  transition: transform 0.18s;
}
.vuln-chevron-open {
  transform: rotate(180deg);
}

/* Summary clamp removed when expanded */
.vuln-summary-full {
  -webkit-line-clamp: unset;
  overflow: visible;
}

/* ── Expanded detail body ── */
.vuln-detail-body {
  display: flex;
  flex-direction: column;
  gap: 0.65rem;
  padding-top: 0.75rem;
  border-top: 1px solid var(--color-divider);
  margin-top: 0.2rem;
  cursor: default; /* inner clicks don't trigger card toggle */
}

.vuln-detail-row {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.vuln-detail-label {
  font-size: var(--text-xs);
  font-weight: 700;
  color: var(--color-text-muted);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.vuln-detail-value {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 0.4rem;
  font-size: var(--text-sm);
}
.vuln-detail-sep { color: var(--color-text-muted); opacity: 0.5; }

.vuln-aliases-list {
  display: flex;
  flex-wrap: wrap;
  gap: 0.3rem;
}

.vuln-alias-chip {
  font-family: monospace;
  font-size: var(--text-xs);
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  padding: 0.1rem 0.45rem;
  border-radius: 0.4rem;
}
.vuln-fix-chip {
  background: var(--color-success-bg);
  color: var(--color-success-text);
  border-color: var(--color-success-border);
}

.vuln-cvss-score-large {
  font-size: var(--text-lg);
  font-weight: 800;
  font-family: monospace;
}

.vuln-cvss-vector {
  font-size: var(--text-xs);
  font-family: monospace;
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  padding: 0.1rem 0.45rem;
  border-radius: 0.4rem;
  word-break: break-all;
}

.vuln-purl {
  font-size: var(--text-xs);
  font-family: monospace;
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  padding: 0.15rem 0.5rem;
  border-radius: 0.4rem;
  word-break: break-all;
}

.vuln-detail-actions {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  flex-wrap: wrap;
  padding-top: 0.1rem;
}

.btn-xs {
  padding: 0.25rem 0.65rem;
  font-size: var(--text-xs);
  text-decoration: none;
}
</style>
