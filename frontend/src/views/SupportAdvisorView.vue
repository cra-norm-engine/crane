<template>
  <section class="page advisor-page">
    <nav class="breadcrumbs" aria-label="Breadcrumb">
      <RouterLink :to="{ name: 'products' }">Products</RouterLink><span aria-hidden="true">/</span>
      <RouterLink :to="{ name: 'product-detail', params: { productId } }">{{ productName || 'Product workspace' }}</RouterLink>
      <span aria-hidden="true">/</span><span aria-current="page">Support-Period Advisor</span>
    </nav>

    <header class="page-header">
      <div>
        <div class="heading-label">PRODUCT LIFECYCLE <span aria-hidden="true">·</span> CRA ART. 13(8)</div>
        <h1 class="page-title">Support-Period Advisor</h1>
        <p class="muted page-subtitle">Build a support commitment you can explain, sustain, and review.</p>
      </div>
      <div class="actions">
        <AppButton :disabled="busy || !releaseId" @click="requestContext(releaseId)">Refresh source records</AppButton>
        <AppButton variant="primary" :disabled="!context" @click="scrollTo('decision-history')">View decisions <span class="button-count">{{ releaseAssessments.length }}</span></AppButton>
      </div>
    </header>

    <div v-if="error" class="feedback-banner feedback-banner-error" role="alert"><strong>We couldn’t complete that action.</strong><span>{{ error }}</span><AppButton size="sm" :disabled="busy" @click="retry">{{ context ? 'Dismiss' : 'Try again' }}</AppButton></div>
    <div v-if="notice" class="feedback-banner feedback-banner-success" role="status">{{ notice }}<RouterLink v-if="taskCreated" :to="{ name: 'my-tasks' }">Open My Tasks →</RouterLink></div>

    <div class="card scope-bar">
      <label class="field release-field" for="advisor-release"><span class="field-label">Assessment scope</span>
        <select id="advisor-release" class="select" :value="releaseId" :disabled="busy || !releases.length" @change="changeRelease">
          <option value="">Select a product release</option><option v-for="r in releases" :key="r.id" :value="r.id">{{ r.user_version || `v${r.system_version}` }} · System version {{ r.system_version }}</option>
        </select>
      </label>
      <div class="scope-note"><StatusBadge :label="dirty ? 'Unsaved changes' : 'Source records loaded'" :variant="dirty ? 'warning' : 'neutral'" v-if="context" /><p class="muted">Each saved assessment preserves this release’s configuration and evidence.</p></div>
      <RouterLink v-if="releaseId" class="text-link" :to="{ name: 'release-gate', params: { releaseId } }">Open release →</RouterLink>
    </div>

    <div v-if="busy && !context" class="card loading-state"><AppSpinner size="lg" label="Loading support context" /><p class="muted">Gathering support dates, dependencies, and evidence…</p></div>
    <EmptyState v-else-if="!context && !error" :title="releases.length ? 'Choose a release to begin' : 'Create a product release first'" description="The advisor uses release-specific components and evidence to build a traceable assessment.">
      <template #action><RouterLink :to="{ name: 'product-detail', params: { productId } }">Return to product workspace →</RouterLink></template>
    </EmptyState>

    <template v-if="context">
      <section class="summary-grid" aria-label="Assessment overview">
        <div class="summary-card"><span class="metric-label">Proposed support</span><strong>{{ supportDuration }}</strong><span class="muted">{{ calendarDate(form.support_start) }} → {{ calendarDate(form.support_end) }}</span></div>
        <a href="#supplier-timeline" class="summary-card"><span class="metric-label">Linked components</span><strong>{{ context.components.length }}</strong><span class="muted">{{ highRiskCount }} core or high-risk · Inspect timeline →</span></a>
        <a href="#supplier-timeline" class="summary-card" :class="{ 'metric-warning': unknownCount }"><span class="metric-label">Unknown commitments</span><strong>{{ unknownCount }}</strong><span class="muted">{{ !context.components.length ? 'Link component inventory to assess coverage →' : unknownCount ? 'Confirm supplier dates and evidence →' : 'Verification recorded for linked components' }}</span></a>
        <a href="#justification-evidence" class="summary-card"><span class="metric-label">Justification evidence</span><strong>{{ form.evidence_ids.length }}<small> / {{ context.evidence.length }}</small></strong><span class="muted">Selected from this release →</span></a>
      </section>

      <nav class="section-nav" aria-label="Advisor sections"><a href="#support-justification">01 <span>Support justification</span></a><a href="#supplier-timeline">02 <span>Supplier coverage</span></a><a href="#decision-history">03 <span>Decisions & evidence</span><span class="nav-count">{{ releaseAssessments.length }}</span></a></nav>

      <div v-if="draftOrigin" class="feedback-banner feedback-banner-info" role="status"><strong>New draft from a saved assessment</strong><span>Reasoning and applicable evidence have been copied from {{ format(draftOrigin) }}. Source records are current; the original assessment is preserved.</span></div>
      <div class="workspace-grid">
        <form id="support-assessment-form" class="assessment-form" @submit.prevent="save" @invalid.capture="revealInvalid">
          <fieldset class="editor-fields" :disabled="busy">
            <section id="support-justification" class="card section-card" aria-labelledby="justification-title">
              <header class="section-heading"><div class="section-number" aria-hidden="true">01</div><div><h2 id="justification-title">Support justification</h2><p class="muted">Define the commitment and explain how it reflects expected use.</p></div><StatusBadge label="Manufacturer input" variant="info" /></header>
              <div v-if="context.support" class="source-note"><span class="source-dot" aria-hidden="true" /><span>Support dates and rationale are prefilled from the existing manufacturer record. Expected-use dates require your determination.</span></div>
              <div v-else class="feedback-banner feedback-banner-warning">No declared support period was found. Enter proposed dates for this assessment.</div>
              <div class="date-grid">
                <label class="field" for="support-start"><span class="field-label">Proposed support start <span aria-hidden="true">*</span></span><input id="support-start" v-model="form.support_start" class="input" type="date" :readonly="!canWrite" required :max="form.support_end || undefined"></label>
                <label class="field" for="support-end"><span class="field-label">Proposed support end <span aria-hidden="true">*</span></span><input id="support-end" v-model="form.support_end" class="input" type="date" :readonly="!canWrite" required :min="nextDay(form.support_start)"></label>
                <label class="field" for="expected-end"><span class="field-label">Expected-use end <span aria-hidden="true">*</span></span><input id="expected-end" v-model="form.expected_use_end" class="input" type="date" :readonly="!canWrite" required :min="nextDay(form.support_start)" aria-describedby="expected-hint"><span id="expected-hint" class="field-hint">When is the product reasonably expected to leave use?</span></label>
              </div>
              <div v-if="form.support_end && form.expected_use_end && form.support_end < form.expected_use_end" class="feedback-banner feedback-banner-warning"><strong>Support ends before expected use.</strong><span>Explain the proportionality of this commitment below. This requires review, not automatic rejection.</span></div>
              <label class="field" for="expected-basis"><span class="field-label">Basis for expected use</span><select id="expected-basis" v-model="form.expected_use_basis" class="select" :disabled="!canWrite"><option value="assumption">Manufacturer assumption</option><option value="estimate">Estimate</option><option value="documented">Documented by evidence</option></select><span class="field-hint">Assumptions and estimates remain visible to reviewers. Approval requires documented evidence.</span></label>
              <details v-if="existingReasoning.length" class="disclosure"><summary>Existing product reasoning <span class="muted">{{ existingReasoning.length }} reference notes</span></summary><dl class="reference-notes"><template v-for="note in existingReasoning" :key="note.label"><dt>{{ note.label }}</dt><dd>{{ note.value }}</dd></template></dl></details>
              <label class="field" for="support-rationale"><span class="field-label">Article 13(8) rationale <span aria-hidden="true">*</span></span><textarea id="support-rationale" v-model="form.rationale" class="textarea" :readonly="!canWrite" required minlength="10" maxlength="20000" rows="5" placeholder="Explain why this support period is appropriate for the product and its users…" aria-describedby="rationale-hint" /><span id="rationale-hint" class="field-hint">Consider user expectations, intended purpose, applicable Union law, operating environment, comparable products, and core supplier constraints.</span></label>

              <div id="justification-evidence" class="evidence-section"><div class="subsection-heading"><h3>Supporting evidence</h3><StatusBadge :label="`${form.evidence_ids.length} selected`" /></div><p class="muted">Select the release documents that support your expected-use determination and rationale.</p>
                <div v-if="context.evidence.length" class="evidence-list"><label v-for="e in context.evidence" :key="e.id" class="evidence-option" :class="{ selected: form.evidence_ids.includes(e.id) }"><input v-model="form.evidence_ids" type="checkbox" :disabled="!canWrite" :value="e.id"><svg class="document-icon" width="15" height="17" viewBox="0 0 16 18" fill="none" stroke="currentColor" stroke-width="1.2" aria-hidden="true"><path d="M9 1H2v16h12V6L9 1Z"/><path d="M9 1v5h5M5 10h6M5 13h6"/></svg><span>{{ e.title }}</span><span v-if="form.evidence_ids.includes(e.id)" class="selection-label">Selected</span></label></div>
                <EmptyState v-else compact title="No release evidence yet" description="Add evidence to this release, then refresh the source records before submitting for approval."><template #action><RouterLink :to="{ name: 'release-gate', params: { releaseId } }">Open release workspace →</RouterLink></template></EmptyState>
              </div>
            </section>

            <section id="supplier-timeline" class="card section-card" aria-labelledby="timeline-title">
              <header class="section-heading"><div class="section-number" aria-hidden="true">02</div><div><h2 id="timeline-title">Supplier coverage</h2><p class="muted">Compare version-specific commitments on one calendar.</p></div></header>
              <div class="coverage-toolbar"><label class="search-field"><span class="sr-only">Search components or suppliers</span><input v-model="componentSearch" class="input" type="search" placeholder="Search components or suppliers…"></label><label class="coverage-filter"><span class="sr-only">Coverage status</span><select v-model="coverageFilter" class="select"><option value="all">All commitments</option><option value="attention">Needs attention</option><option value="gaps">Support gaps</option><option value="unknown">Unknown / unverified</option><option value="covered">Window covered</option></select></label><label class="check"><input v-model="criticalOnly" type="checkbox">Core or high-risk only</label></div>
              <div class="timeline-legend"><span><i class="legend-dot committed" />Recorded support</span><span><i class="legend-dot gap" />Outside supplier window</span><span><i class="legend-dot unknown" />Unknown / unverified</span></div>
              <div v-if="validSupportWindow" class="timeline-axis"><span>{{ calendarDate(form.support_start) }}</span><span>Proposed product support</span><span>{{ calendarDate(form.support_end) }}</span></div>
              <div v-else class="source-note">Enter a valid proposed support window to display the calendar timeline.</div>
              <EmptyState v-if="!context.components.length" compact title="Component coverage is unknown" description="No component inventory is linked to this release. Link components in Supplier Assurance to assess their commitments."><template #action><RouterLink :to="{ name: 'supplier-assurance', query: { tab: 'traceability', productId } }">Open supplier traceability →</RouterLink></template></EmptyState>
              <EmptyState v-else-if="!visibleComponents.length" compact title="No components match" description="Try another name or include components with lower criticality."><template #action><AppButton size="sm" @click="clearFilters">Clear filters</AppButton></template></EmptyState>
              <article v-for="c in pagedComponents" :key="c.link_id" class="component-row" :id="`component-${c.link_id}`">
                <div class="component-heading"><div><RouterLink :to="{ name: 'third-party-component-detail', params: { componentId: c.id } }" class="component-name">{{ c.name }} <span class="muted">{{ c.version || 'Version unspecified' }}</span></RouterLink><p class="muted small-text">{{ c.supplier_name }}<span v-if="c.is_core_function"> · Core function</span> · {{ humanize(c.criticality) }} criticality</p></div><StatusBadge :label="commitmentLabel(c)" :variant="!verified(c) ? 'neutral' : hasGap(c) ? 'warning' : 'success'" /></div>
                <div v-if="validSupportWindow" class="timeline-track" :class="{ 'timeline-unknown': !verified(c) }" role="img" :aria-label="`${c.name}: recorded support ${calendarDate(c.support_start_date)} to ${calendarDate(c.support_end_date)}. ${commitmentLabel(c)}.`"><span v-if="verified(c)" class="timeline-bar" :style="barStyle(c)" /></div>
                <div class="component-dates"><span>Supplier window: {{ calendarDate(c.support_start_date) }} → {{ calendarDate(c.support_end_date) }}</span><span v-if="!verified(c)">Missing dates or commitment evidence</span><span v-else-if="currentCheck?.components.find(row => row.link_id === c.link_id)?.gap_days" class="warning-text">{{ currentCheck.components.find(row => row.link_id === c.link_id)!.gap_days!.toLocaleString() }} gap days · remediation review required</span><span v-else-if="hasGap(c)" class="warning-text">Review alternative remediation</span></div>
                <details class="remediation-disclosure" :open="!!remedies[c.link_id]?.approach"><summary>{{ remedies[c.link_id]?.approach ? humanize(remedies[c.link_id].approach) : 'Document a remediation approach' }}<span class="muted">Scope, capacity & evidence</span></summary>
                  <div class="remediation-fields"><p v-if="c.support_scope" class="small-text muted">Recorded supplier scope: {{ c.support_scope }}</p><label class="field" :for="`approach-${c.link_id}`"><span class="field-label">Remediation approach</span><select :id="`approach-${c.link_id}`" v-model="remedy(c.link_id).approach" class="select" :disabled="!canWrite"><option value="">No documented remediation</option><option value="supplier_extension">Supplier extension</option><option value="independent_patching">Independent patching</option><option value="replacement">Component replacement</option><option value="architecture_mitigation">Architecture-level mitigation</option></select></label>
                    <template v-if="remedy(c.link_id).approach"><label class="field" :for="`remediation-${c.link_id}`"><span class="field-label">Feasibility and residual risk</span><textarea :id="`remediation-${c.link_id}`" v-model="remedy(c.link_id).rationale" class="textarea" :readonly="!canWrite" minlength="10" maxlength="10000" rows="3" required placeholder="Describe engineering capacity, version scope, contractual feasibility, and remaining risk…" /></label>
                      <fieldset class="evidence-fieldset"><legend class="field-label">Evidence for reviewer verification</legend><label v-for="e in context.evidence" :key="e.id" class="evidence-option"><input v-model="remedy(c.link_id).evidence_ids" type="checkbox" :disabled="!canWrite" :value="e.id"><span>{{ e.title }}</span></label><p v-if="!context.evidence.length" class="small-text muted">No evidence is linked to this release. Add the relevant documents in the release workspace, then refresh source records.</p><p v-if="!remedy(c.link_id).evidence_ids.length" class="warning-text small-text">Select at least one evidence document for this approach.</p></fieldset>
                    </template>
                  </div>
                </details>
              </article>
              <div v-if="visibleComponents.length" class="component-pagination"><p class="muted small-text">Showing {{ (componentPage - 1) * componentsPerPage + 1 }}–{{ Math.min(componentPage * componentsPerPage, visibleComponents.length) }} of {{ visibleComponents.length }} matching components<span v-if="visibleComponents.length !== context.components.length"> · {{ context.components.length }} total</span></p><div v-if="componentPages > 1" class="actions"><AppButton size="sm" :disabled="componentPage === 1" aria-label="Previous component page" @click="componentPage--">← Previous</AppButton><span class="muted small-text" role="status">{{ componentPage }} / {{ componentPages }}</span><AppButton size="sm" :disabled="componentPage === componentPages" aria-label="Next component page" @click="componentPage++">Next →</AppButton></div></div>
              <p v-if="context.components.length" class="muted small-text coverage-count">Recorded dates and references require reviewer assessment of scope and adequacy. Draft checks include every linked component, including those outside the current page or filters.</p>
            </section>
          </fieldset>
          <section id="draft-check" class="card draft-check" aria-labelledby="draft-check-title">
            <div class="subsection-heading"><div><h2 id="draft-check-title">Check before you save</h2><p class="muted small-text">Run the same deterministic rules used by the saved assessment. No version is created.</p></div><StatusBadge v-if="draftCheck" :label="currentCheck ? 'Checked draft' : 'Changes need rechecking'" :variant="currentCheck ? 'info' : 'warning'" /></div>
            <div v-if="!draftCheck" class="source-note">Complete the dates and rationale, then check the draft to inspect missing evidence and component gaps.</div>
            <div v-else-if="!currentCheck" class="source-note">The draft changed after its last check. Check it again to see findings for the current inputs.</div>
            <template v-if="currentCheck">
              <div class="check-outcome" role="status"><StatusBadge :label="currentCheck.approval_blockers.length ? 'Actions needed before approval' : 'Independent review required'" :variant="currentCheck.approval_blockers.length ? 'warning' : 'info'" /><span class="muted small-text">{{ currentCheck.rules_version }} · {{ currentCheck.findings.length }} findings</span></div>
              <div class="outcomes"><div><span>Five-year baseline</span><strong>{{ currentCheck.general_minimum_met ? 'Minimum met' : 'Review shorter-use exception' }}</strong></div><div><span>Technical readiness</span><strong>{{ humanize(currentCheck.technical_readiness) }}</strong></div><div><span>Economic assessment</span><strong>{{ humanize(currentCheck.economic_attractiveness) }}</strong></div></div>
              <div class="check-findings"><article v-for="group in groupedFindings(currentCheck)" :key="group.rule" class="finding-group"><div class="finding-group-heading"><span class="rule-label">{{ group.rule }}</span><strong>{{ findingHelp(group.rule).title }}</strong><StatusBadge :label="currentCheck.approval_blockers.includes(group.rule) ? 'Resolve before approval' : 'Reviewer judgment'" :variant="currentCheck.approval_blockers.includes(group.rule) ? 'warning' : 'info'" /></div><p class="muted small-text">{{ findingHelp(group.rule).detail }}</p><details v-if="group.messages.length > 1"><summary>{{ group.messages.length }} related findings</summary><ul><li v-for="message in group.messages" :key="message">{{ message }}</li></ul></details><p v-else class="small-text">{{ group.messages[0] }}</p><AppButton size="sm" variant="ghost" @click="focusSection(findingHelp(group.rule).target)">{{ findingHelp(group.rule).action }} →</AppButton></article><p v-if="!currentCheck.findings.length" class="source-note">No screening findings recorded. This still requires independent review of the evidence and remediation capability.</p></div>
            </template>
            <div class="actions"><AppButton v-if="canWrite" :disabled="busy" @click="checkDraft">{{ checking ? 'Checking draft…' : currentCheck ? 'Check again' : 'Check draft' }}</AppButton><span class="muted small-text">A check is decision support and does not certify compliance.</span></div>
          </section>
          <div class="save-bar"><div><strong>{{ canWrite ? 'Ready to record this assessment?' : 'You have read-only access' }}</strong><p class="muted small-text">{{ canWrite ? 'Save an immutable version for an independent reviewer.' : 'Support-period write permission is required to submit changes.' }}</p></div><AppButton v-if="canWrite" variant="primary" type="submit" :disabled="busy">{{ saving ? 'Saving assessment…' : 'Save for human review' }}</AppButton></div>
          <p v-if="formIssue" class="field-error" role="alert">{{ formIssue }}</p>
        </form>

        <aside class="advisor-sidebar" aria-label="Assessment guidance">
          <section class="card checklist-card"><div class="subsection-heading"><h2>Before you submit</h2><StatusBadge :label="`${completedChecks} / ${readiness.length}`" variant="primary" /></div><p class="muted small-text">A complete record helps the reviewer assess your decision.</p><ul class="checklist"><li v-for="check in readiness" :key="check.label"><span class="check-marker" :class="{ complete: check.done }" aria-hidden="true">{{ check.done ? '✓' : '·' }}</span><div><button type="button" class="checklist-link" @click="focusSection(check.target)">{{ check.label }}</button><p class="muted small-text">{{ check.detail }}</p></div><span class="sr-only">{{ check.done ? 'Complete' : 'Needs attention' }}</span></li></ul><div class="sidebar-note">Saving does not approve the proposed commitment. Evidence and remediation adequacy need independent human review.</div></section>
          <section class="card context-card"><h2>Release evidence context</h2><dl class="context-counts"><div><dt>SBOM records</dt><dd>{{ context.sboms.length }}</dd></div><div><dt>Risk assessments</dt><dd>{{ context.risk_assessments.length }}</dd></div><div><dt>Vulnerability reports</dt><dd>{{ context.vulnerabilities.length }}</dd></div></dl><details v-if="context.risk_assessments.length || context.vulnerabilities.length" class="disclosure"><summary>Inspect source records</summary><ul class="context-records"><li v-for="r in context.risk_assessments" :key="r.id"><RouterLink :to="{ name: 'risk-assessment-detail', params: { assessmentId: r.id } }">{{ r.title }}</RouterLink><span class="muted small-text">Risk assessment</span></li><li v-for="v in context.vulnerabilities" :key="v.id">{{ v.title }}<span class="muted small-text">Vulnerability report</span></li></ul></details><p class="muted small-text">Source records are preserved with every saved version. Their presence alone does not establish remediation capability.</p></section>
          <section class="guidance-note"><span class="heading-label">DECISION SUPPORT</span><h3>Keep the three questions separate</h3><p><strong>Justification</strong> — is the commitment supported by proportionate reasoning?</p><p><strong>Readiness</strong> — can you sustain vulnerability handling?</p><p><strong>Economics</strong> — cost comparison has not been assessed.</p><a href="https://eur-lex.europa.eu/eli/reg/2024/2847/2024-11-20/eng" target="_blank" rel="noopener noreferrer">Read CRA Article 13(8) ↗</a></section>
        </aside>
      </div>

      <section id="decision-history" class="card section-card history-section" aria-labelledby="history-title">
        <header class="section-heading"><div class="section-number" aria-hidden="true">03</div><div><h2 id="history-title">Decisions & evidence</h2><p class="muted">Review the saved record, resolve open findings, and preserve the decision.</p></div><StatusBadge :label="`${releaseAssessments.length} saved`" /></header>
        <EmptyState v-if="!releaseAssessments.length" compact title="No assessment saved for this release" description="Complete the support justification and save a version to start an independent review." />
        <div v-else class="history-grid">
          <nav class="version-list" aria-label="Saved assessment versions"><button v-for="(a, index) in releaseAssessments" :key="a.id" type="button" class="version-item" :class="{ active: selectedAssessment?.id === a.id }" :aria-current="selectedAssessment?.id === a.id ? 'true' : undefined" @click="selectedId = a.id"><span class="version-top"><strong>Assessment {{ releaseAssessments.length - index }}</strong><span v-if="index === 0" class="latest-label">Latest</span></span><span class="muted small-text">{{ format(a.created_at) }}</span><StatusBadge :label="humanize(a.status)" :variant="a.status === 'approved' ? 'success' : a.status === 'returned' ? 'warning' : 'info'" /><span v-if="a.needs_refresh" class="warning-text small-text">Source changes detected</span></button></nav>
          <article v-if="selectedAssessment" class="decision-detail">
            <div class="decision-heading"><div><h3>{{ humanize(selectedAssessment.status) }}</h3><p class="muted small-text">Saved {{ format(selectedAssessment.created_at) }} · {{ selectedAssessment.result.rules_version }}</p></div><div class="actions"><AppButton v-if="canWrite" size="sm" :disabled="busy" @click="requestRevision(selectedAssessment)">Start a revision</AppButton><AppButton size="sm" :disabled="busy" @click="download(selectedAssessment)">Export report <span class="muted">JSON ↓</span></AppButton></div></div>
            <div v-if="selectedAssessment.needs_refresh" class="feedback-banner feedback-banner-warning"><strong>SP-007 · Source records changed</strong><span>This snapshot is preserved. Create a new assessment from current records before approving.</span></div>
            <dl class="decision-dates"><div><dt>Support window</dt><dd>{{ calendarDate(selectedAssessment.inputs.support_start) }} → {{ calendarDate(selectedAssessment.inputs.support_end) }}</dd></div><div><dt>Expected-use end</dt><dd>{{ calendarDate(selectedAssessment.inputs.expected_use_end) }}</dd></div></dl>
            <div class="outcomes"><div><span>Legal admissibility</span><strong>{{ humanize(selectedAssessment.result.legal_admissibility) }}</strong></div><div><span>Technical readiness</span><strong>{{ humanize(selectedAssessment.result.technical_readiness) }}</strong></div><div><span>Economic attractiveness</span><strong>{{ humanize(selectedAssessment.result.economic_attractiveness) }}</strong></div></div>
            <p class="muted small-text">Preliminary screening · {{ selectedAssessment.result.general_minimum_met ? 'General five-year minimum met.' : 'Shorter-use exception needs documented justification.' }} Human approval records a decision and does not certify compliance.</p>
            <h4>Recorded rationale</h4><p class="rationale-copy">{{ selectedAssessment.inputs.rationale }}</p>
            <div class="subsection-heading"><h4>Review findings</h4><StatusBadge :label="`${selectedAssessment.result.findings.length} findings`" :variant="selectedAssessment.result.findings.length ? 'warning' : 'neutral'" /></div>
            <ul v-if="selectedAssessment.result.findings.length" class="findings"><li v-for="(f, i) in selectedAssessment.result.findings" :key="i"><span class="rule-label">{{ f.rule }}</span><div><span>{{ f.message }}</span><p class="muted small-text saved-finding-help">{{ findingHelp(f.rule).detail }}</p></div></li></ul><p v-else class="muted small-text">No screening findings recorded. Independent review is still required.</p>
            <details class="disclosure"><summary>Component coverage snapshot <span class="muted">{{ selectedAssessment.result.components.length }} components</span></summary><div class="table-scroll" tabindex="0" role="region" aria-label="Saved component coverage"><table class="table"><thead><tr><th scope="col">Component</th><th scope="col">Coverage</th><th scope="col">Gap</th></tr></thead><tbody><tr v-for="c in selectedAssessment.result.components" :key="c.link_id"><td>{{ c.name }} {{ c.version }}</td><td>{{ coverageLabel(c.status) }}</td><td>{{ c.gap_days == null ? 'Unknown' : `${c.gap_days.toLocaleString()} days` }}</td></tr></tbody></table></div></details>
            <details class="disclosure"><summary>Supporting documents & remediation <span class="muted">{{ selectedAssessment.inputs.evidence_ids.length }} documents</span></summary><ul class="document-list"><li v-for="id in selectedAssessment.inputs.evidence_ids" :key="id">{{ evidenceTitle(selectedAssessment, id) }}</li><li v-if="!selectedAssessment.inputs.evidence_ids.length" class="muted">No justification evidence selected.</li></ul><div v-for="r in selectedAssessment.inputs.remediations" :key="r.component_link_id" class="saved-remediation"><strong>{{ savedComponentName(selectedAssessment, r.component_link_id) }} · {{ humanize(r.approach) }}</strong><p>{{ r.rationale }}</p><ul class="document-list"><li v-for="id in r.evidence_ids" :key="id">{{ evidenceTitle(selectedAssessment, id) }}</li></ul></div></details>
            <div v-if="selectedAssessment.review_reason" class="review-record"><StatusBadge :label="humanize(selectedAssessment.status)" :variant="selectedAssessment.status === 'approved' ? 'success' : 'warning'" /><p>{{ selectedAssessment.review_reason }}</p><p class="muted small-text">Reviewed {{ format(selectedAssessment.reviewed_at) }} · Reviewer reference {{ selectedAssessment.reviewer_id }}</p></div>
            <form v-if="canReview(selectedAssessment)" class="review-form" @submit.prevent="review(selectedAssessment, 'approved')"><h4>Independent review</h4><p v-if="approvalReason(selectedAssessment)" class="warning-text small-text">{{ approvalReason(selectedAssessment) }}</p><label class="field" :for="`review-${selectedAssessment.id}`"><span class="field-label">Decision rationale</span><textarea :id="`review-${selectedAssessment.id}`" v-model="reviewReasons[selectedAssessment.id]" class="textarea" required minlength="10" maxlength="20000" rows="3" placeholder="Explain your review of proportionality, evidence, and remediation adequacy…" /></label><div class="actions"><AppButton variant="primary" type="submit" :disabled="busy || !!approvalReason(selectedAssessment) || !validReviewReason(selectedAssessment)">Approve decision record</AppButton><AppButton :disabled="busy || !validReviewReason(selectedAssessment)" @click="review(selectedAssessment, 'returned')">Return with reasons</AppButton></div></form>
            <p v-else-if="selectedAssessment.status === 'pending_review'" class="source-note">{{ selectedAssessment.author_id === auth.user?.id ? 'Your assessment is waiting for an independent reviewer. Authors cannot approve their own decisions.' : 'Review requires support-period write and supplier-assessment approval permissions.' }}</p>
            <div v-if="auth.hasPermission('task_assign')" class="follow-up"><span class="muted small-text">Need evidence or remediation work?</span><AppButton size="sm" :disabled="busy" @click="createTask(selectedAssessment)">Create follow-up task for me</AppButton></div>
          </article>
        </div>
      </section>
    </template>
    <AppModal v-model="showDiscard" title="Discard unsaved assessment changes?" size="sm"><p>Leaving this page, changing the release, or refreshing source records will discard your unsaved dates, reasoning, and evidence selections.</p><template #footer><AppButton @click="showDiscard = false">Keep editing</AppButton><AppButton variant="danger" @click="discardAndLoad">Discard and continue</AppButton></template></AppModal>
  </section>
</template>

<script setup lang="ts">
import { computed, nextTick, onMounted, onUnmounted, reactive, ref, watch } from 'vue';
import { onBeforeRouteLeave, useRoute } from 'vue-router';
import AppButton from '@/components/AppButton.vue';
import AppModal from '@/components/AppModal.vue';
import AppSpinner from '@/components/AppSpinner.vue';
import EmptyState from '@/components/EmptyState.vue';
import StatusBadge from '@/components/StatusBadge.vue';
import { useDateFormat, formatDate } from '@/composables/useDateFormat';
import { useAuthStore } from '@/stores/auth';
import { productService } from '@/services/product-service';
import { taskService } from '@/services/task-service';
import { supportAdvisorService as service, type Assessment, type AssessmentInput, type Component, type Context, type Remediation } from '@/services/support-advisor-service';

const productId = String(useRoute().params.productId);
const auth = useAuthStore();
const { format, dateFormat } = useDateFormat();
const calendarDate = (value?: string | null) => value ? formatDate(value, { timezone: 'UTC', format: dateFormat.value }) : 'Unknown';
const releases = ref<{ id: string; user_version: string | null; system_version: number }[]>([]);
const productName = ref('');
const releaseId = ref('');
const context = ref<Context | null>(null);
const assessments = ref<Assessment[]>([]);
const busy = ref(false);
const saving = ref(false);
const checking = ref(false);
const draftCheck = ref<{ signature: string; result: Assessment['result'] } | null>(null);
const draftOrigin = ref('');
const pendingRevision = ref<Assessment | null>(null);
const error = ref('');
const notice = ref('');
const taskCreated = ref(false);
const criticalOnly = ref(false);
const componentSearch = ref('');
const coverageFilter = ref('all');
const componentPage = ref(1);
const componentsPerPage = 20;
const selectedId = ref('');
const formIssue = ref('');
const showDiscard = ref(false);
const pendingRelease = ref('');
let resolveNavigation: ((leave: boolean) => void) | undefined;
const baseline = ref('');
const reviewReasons = reactive<Record<string, string>>({});
const remedies = reactive<Record<string, Remediation>>({});
const form = reactive<AssessmentInput>({ context_version: '', product_release_id: '', support_start: '', support_end: '', expected_use_end: '', expected_use_basis: 'assumption', rationale: '', evidence_ids: [], remediations: [] });
const canWrite = computed(() => auth.hasPermission('support_period_write'));
const activeRemedies = computed(() => Object.values(remedies).filter(r => r.approach));
const draftSnapshot = () => JSON.stringify({ ...form, remediations: activeRemedies.value });
const currentCheck = computed(() => draftCheck.value?.signature === draftSnapshot() ? draftCheck.value.result : null);
const dirty = computed(() => !!context.value && !!baseline.value && baseline.value !== draftSnapshot());
const validSupportWindow = computed(() => !!form.support_start && !!form.support_end && form.support_end > form.support_start);
const supportDuration = computed(() => {
  if (!validSupportWindow.value) return 'Not defined';
  const years = (Date.parse(form.support_end) - Date.parse(form.support_start)) / (365.2425 * 86400000);
  return `~${Number(years.toFixed(1))} years`;
});
const highRisk = (c: Component) => c.is_core_function || ['high', 'critical'].includes(c.criticality);
const highRiskCount = computed(() => context.value?.components.filter(highRisk).length || 0);
function verified(c: Component) { return !!(c.support_start_date && c.support_end_date && c.support_end_date >= c.support_start_date && c.support_verified_at && c.support_reference_url && c.support_scope); }
const unknownCount = computed(() => context.value?.components.filter(c => !verified(c)).length || 0);
function hasGap(c: Component) { return validSupportWindow.value && !!c.support_start_date && !!c.support_end_date && (c.support_start_date > form.support_start || c.support_end_date < form.support_end); }
function commitmentLabel(c: Component) { return !verified(c) ? 'Unknown / unverified' : !validSupportWindow.value ? 'Dates recorded' : hasGap(c) ? 'Support gap' : 'Window covered'; }
const visibleComponents = computed(() => (context.value?.components || []).filter(c => {
  const matchesCoverage = coverageFilter.value === 'all' || (coverageFilter.value === 'attention' && (!verified(c) || hasGap(c))) || (coverageFilter.value === 'gaps' && verified(c) && hasGap(c)) || (coverageFilter.value === 'unknown' && !verified(c)) || (coverageFilter.value === 'covered' && verified(c) && validSupportWindow.value && !hasGap(c));
  return matchesCoverage && (!criticalOnly.value || highRisk(c)) && `${c.name} ${c.version || ''} ${c.supplier_name}`.toLowerCase().includes(componentSearch.value.toLowerCase().trim());
}));
const componentPages = computed(() => Math.max(1, Math.ceil(visibleComponents.value.length / componentsPerPage)));
const pagedComponents = computed(() => visibleComponents.value.slice((componentPage.value - 1) * componentsPerPage, componentPage.value * componentsPerPage));
watch([componentSearch, criticalOnly, coverageFilter, releaseId], () => { componentPage.value = 1; });
watch(componentPages, total => { componentPage.value = Math.min(componentPage.value, total); });
function clearFilters() { componentSearch.value = ''; criticalOnly.value = false; coverageFilter.value = 'all'; }
const releaseAssessments = computed(() => assessments.value.filter(a => a.product_release_id === releaseId.value));
const selectedAssessment = computed(() => releaseAssessments.value.find(a => a.id === selectedId.value) || releaseAssessments.value[0]);
const existingReasoning = computed(() => [
  { label: 'Expected use', value: context.value?.support?.expected_use_time_text },
  { label: 'Comparable products', value: context.value?.support?.comparable_products_text },
  { label: 'Supplier constraints', value: context.value?.support?.third_party_support_constraints_text },
].filter(note => note.value));
const readiness = computed(() => [
  { label: 'Support window defined', target: 'support-start', done: validSupportWindow.value, detail: 'Record actual start and end dates.' },
  { label: 'Expected use documented', target: 'expected-end', done: !!form.support_start && !!form.expected_use_end && form.expected_use_end > form.support_start && form.expected_use_basis === 'documented', detail: 'Confirm the date and its evidence basis.' },
  { label: 'Reasoning recorded', target: 'support-rationale', done: form.rationale.trim().length >= 10, detail: 'Explain the proportionality of the commitment.' },
  { label: 'Evidence linked', target: 'justification-evidence', done: !!form.evidence_ids.length, detail: 'Select documents supporting your determination.' },
  { label: 'Supplier commitments recorded', target: 'supplier-timeline', done: !!context.value?.components.length && unknownCount.value === 0, detail: 'Confirm dates, scope, and verification references.' },
]);
const completedChecks = computed(() => readiness.value.filter(c => c.done).length);
function remedy(id: string) { return remedies[id] ??= { component_link_id: id, approach: '', rationale: '', evidence_ids: [] }; }
function humanize(value?: string) { return value ? value.toLowerCase().split('_').map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(' ') : 'Not assessed'; }
function evidenceTitle(a: Assessment, id: string) { return a.context_snapshot?.evidence?.find(e => e.id === id)?.title || `Evidence reference ${id}`; }
function savedComponentName(a: Assessment, linkId: string) {
  const c = a.context_snapshot?.components.find(row => row.link_id === linkId);
  return c ? `${c.name} ${c.version || ''}`.trim() : `Component reference ${linkId}`;
}
function coverageLabel(status?: string) {
  return ({ UNKNOWN: 'Coverage unknown', COVERED: 'Window covered', ACTION_REQUIRED: 'Remediation needed', REMEDIATION_REVIEW: 'Remediation awaiting review' } as Record<string, string>)[status || ''] || humanize(status);
}
function groupedFindings(result: Assessment['result']) {
  const groups = new Map<string, string[]>();
  for (const finding of result.findings) groups.set(finding.rule, [...(groups.get(finding.rule) || []), finding.message]);
  return [...groups].map(([rule, messages]) => ({ rule, messages }));
}
function findingHelp(rule: string) {
  const help: Record<string, { title: string; detail: string; action: string; target: string }> = {
    'SP-001': { title: 'Explain shorter support', detail: 'Document the shorter expected-use determination and corresponding support dates.', action: 'Review dates and rationale', target: 'support-justification' },
    'SP-002': { title: 'Explain the expected-use difference', detail: 'Record proportionate reasoning for the difference between support and expected use.', action: 'Review justification', target: 'support-rationale' },
    'SP-003': { title: 'Assess supplier coverage gaps', detail: 'Inspect the actual supplier dates and plan version-specific alternatives.', action: 'Inspect supplier timeline', target: 'supplier-timeline' },
    'SP-004': { title: 'Document remediation capability', detail: 'Select an approach and link evidence of feasibility, capacity, and residual risk.', action: 'Plan remediation', target: 'supplier-timeline' },
    'SP-005': { title: 'Resolve unknown dependency coverage', detail: 'Confirm supplier commitments and link missing SBOM versions in the release inventory.', action: 'Inspect dependency coverage', target: 'supplier-timeline' },
    'SP-006': { title: 'Complete supporting evidence', detail: 'Use a documented expected-use basis and select the documents supporting the rationale.', action: 'Select justification evidence', target: 'justification-evidence' },
  };
  return help[rule] || { title: 'Review this finding', detail: 'Inspect the source evidence and determination.', action: 'Review justification', target: 'support-justification' };
}
function focusSection(id: string) {
  clearFilters();
  scrollTo(id);
  const element = document.getElementById(id);
  if (element?.matches('input, textarea, select')) element.focus({ preventScroll: true });
}
function canReview(a: Assessment) { return a.status === 'pending_review' && a.author_id !== auth.user?.id && canWrite.value && auth.hasPermission('supplier_assessment_approve'); }
function validReviewReason(a: Assessment) { return (reviewReasons[a.id]?.trim().length || 0) >= 10; }
function approvalReason(a: Assessment) { return a.needs_refresh ? 'Refresh required: save a new assessment from current source records.' : a.result.approval_blockers.length ? 'Resolve missing evidence or remediation in a new assessment before approval. You can return this record with reasons.' : ''; }
function revealInvalid(event: Event) {
  const target = event.target as HTMLElement;
  const details = target.closest('details');
  if (details) details.open = true;
}
function nextDay(value: string) { if (!value) return undefined; const date = new Date(`${value}T00:00:00Z`); date.setUTCDate(date.getUTCDate() + 1); return Number.isFinite(date.getTime()) ? date.toISOString().slice(0, 10) : undefined; }
function scrollTo(id: string) {
  document.getElementById(id)?.scrollIntoView({ behavior: window.matchMedia('(prefers-reduced-motion: reduce)').matches ? 'auto' : 'smooth', block: 'start' });
}
async function run(action: () => Promise<void>) {
  busy.value = true; error.value = ''; notice.value = ''; taskCreated.value = false;
  try { await action(); } catch (e: unknown) {
    const response = e as { response?: { status?: number; data?: { error?: { message?: string }; detail?: unknown } } };
    if (response.response?.status === 409) draftCheck.value = null;
    error.value = response.response?.data?.error?.message || (response.response?.data?.detail ? JSON.stringify(response.response.data.detail) : e instanceof Error ? e.message : 'Request failed');
  } finally { busy.value = false; }
}
function changeRelease(event: Event) {
  const select = event.target as HTMLSelectElement;
  const id = select.value;
  select.value = releaseId.value;
  if (id) requestContext(id);
}
function requestContext(id: string) { pendingRevision.value = null; pendingRelease.value = id; if (dirty.value) { showDiscard.value = true; return; } void loadContext(id); }
function requestRevision(a: Assessment) {
  pendingRevision.value = a;
  if (dirty.value) { showDiscard.value = true; return; }
  void loadContext(a.product_release_id, a);
}
function discardAndLoad() {
  if (resolveNavigation) {
    const resolve = resolveNavigation;
    resolveNavigation = undefined;
    showDiscard.value = false;
    resolve(true);
  } else {
    showDiscard.value = false;
    const revision = pendingRevision.value;
    pendingRevision.value = null;
    void loadContext(revision?.product_release_id || pendingRelease.value, revision || undefined);
  }
}
watch(showDiscard, open => {
  if (!open && resolveNavigation) {
    resolveNavigation(false);
    resolveNavigation = undefined;
  }
});
onBeforeRouteLeave(() => {
  if (!dirty.value) return true;
  showDiscard.value = true;
  return new Promise<boolean>(resolve => { resolveNavigation = resolve; });
});
function warnBeforeUnload(event: BeforeUnloadEvent) {
  if (dirty.value) { event.preventDefault(); event.returnValue = ''; }
}
onMounted(() => window.addEventListener('beforeunload', warnBeforeUnload));
onUnmounted(() => {
  window.removeEventListener('beforeunload', warnBeforeUnload);
  resolveNavigation?.(false);
});
async function loadContext(id: string, revision?: Assessment) {
  await run(async () => {
    const loaded = await service.context(productId, id);
    context.value = loaded; releaseId.value = id; productName.value = loaded.product.name;
    const s = loaded.support;
    Object.keys(remedies).forEach(k => delete remedies[k]);
    Object.assign(form, { context_version: loaded.context_version, product_release_id: id, support_start: s?.support_start_date || '', support_end: s?.support_end_date || '', expected_use_end: '', expected_use_basis: 'assumption', rationale: s?.justification_text || '', evidence_ids: [], remediations: [] });
    clearFilters(); formIssue.value = ''; draftCheck.value = null; draftOrigin.value = ''; baseline.value = draftSnapshot();
    if (revision) {
      const evidence = new Set(loaded.evidence.map(e => e.id));
      const stillApplicable = (r: Remediation) => {
        const previous = revision.context_snapshot.components.find(c => c.link_id === r.component_link_id);
        return previous && loaded.components.some(c => c.link_id === r.component_link_id && c.id === previous.id && c.version === previous.version);
      };
      Object.assign(form, { ...revision.inputs, context_version: loaded.context_version, product_release_id: id, evidence_ids: revision.inputs.evidence_ids.filter(e => evidence.has(e)), remediations: [] });
      for (const r of revision.inputs.remediations.filter(stillApplicable)) remedies[r.component_link_id] = { ...r, evidence_ids: r.evidence_ids.filter(e => evidence.has(e)) };
      draftOrigin.value = revision.created_at;
      notice.value = 'Revision started with current source records. Unavailable evidence and remediations for changed component versions were excluded; review the draft before saving.';
      scrollTo('support-justification');
    }
  });
}
async function initialize() {
  await run(async () => {
    const [p, history] = await Promise.all([productService.get(productId), service.history(productId)]);
    productName.value = p.name; releases.value = p.releases; assessments.value = history;
    releaseId.value = p.releases[0]?.id || '';
  });
  if (!error.value && releaseId.value) await loadContext(releaseId.value);
}
function retry() { if (!context.value) { if (releaseId.value) void loadContext(releaseId.value); else void initialize(); } else { error.value = ''; } }
async function revealRemediation(linkId: string) {
  clearFilters();
  await nextTick();
  const index = visibleComponents.value.findIndex(c => c.link_id === linkId);
  componentPage.value = Math.max(1, Math.floor(index / componentsPerPage) + 1);
  await nextTick();
  const row = document.getElementById(`component-${linkId}`);
  const details = row?.querySelector('details');
  if (details) details.open = true;
  scrollTo(`component-${linkId}`);
  row?.querySelector<HTMLElement>('textarea, select')?.focus({ preventScroll: true });
}
function validateDraft() {
  formIssue.value = '';
  if (!validSupportWindow.value || !form.expected_use_end || form.expected_use_end <= form.support_start || form.rationale.trim().length < 10) { formIssue.value = 'Complete the support dates, expected-use date, and rationale before checking or saving.'; return false; }
  const incomplete = activeRemedies.value.find(r => r.rationale.trim().length < 10 || !r.evidence_ids.length);
  if (incomplete) { formIssue.value = 'Each selected remediation needs a rationale and at least one evidence document. Open the component’s remediation section to complete it.'; void revealRemediation(incomplete.component_link_id); return false; }
  return true;
}
async function checkDraft() {
  if (!canWrite.value || !validateDraft()) return;
  checking.value = true;
  draftCheck.value = null;
  await run(async () => {
    const signature = draftSnapshot();
    const result = await service.preview(productId, { ...form, remediations: activeRemedies.value });
    draftCheck.value = { signature, result };
    scrollTo('draft-check');
  });
  checking.value = false;
}
async function save() {
  if (!canWrite.value || !validateDraft()) return;
  saving.value = true;
  await run(async () => {
    const created = await service.create(productId, { ...form, remediations: activeRemedies.value });
    baseline.value = draftSnapshot();
    assessments.value = [created, ...assessments.value]; selectedId.value = created.id;
    notice.value = 'Assessment saved for independent review.';
    scrollTo('decision-history');
  });
  saving.value = false;
}
async function review(a: Assessment, decision: string) {
  if (!canReview(a) || !validReviewReason(a) || (decision === 'approved' && approvalReason(a))) return;
  await run(async () => { const reviewed = await service.review(productId, a.id, decision, reviewReasons[a.id].trim()); assessments.value = assessments.value.map(item => item.id === reviewed.id ? reviewed : item); notice.value = decision === 'approved' ? 'Reviewer decision recorded.' : 'Assessment returned with your reasons.'; });
}
async function download(a: Assessment) { await run(async () => { await service.report(productId, a.id); }); }
async function createTask(a: Assessment) { await run(async () => {
  await taskService.create({ title: 'Review support-period evidence and remediation', product_id: productId, product_release_id: a.product_release_id, assigned_to_user_id: auth.user?.id, priority: 'high', description: `Support assessment ${a.id}\n${a.result.findings.map(f => `${f.rule}: ${f.message}`).join('\n')}` });
  notice.value = 'Follow-up task created in My Tasks.'; taskCreated.value = true;
}); }
function barStyle(c: Component) {
  const start = Date.parse(form.support_start), end = Date.parse(form.support_end), cs = Date.parse(c.support_start_date || ''), ce = Date.parse(c.support_end_date || '');
  if (![start, end, cs, ce].every(Number.isFinite) || end <= start) return { width: '0%' };
  const left = Math.max(0, Math.min(1, (cs - start) / (end - start)));
  const right = Math.max(left, Math.min(1, (ce - start) / (end - start)));
  return { marginLeft: `${left * 100}%`, width: `${(right - left) * 100}%` };
}
onMounted(initialize);
</script>

<style scoped>
.draft-check { display: grid; gap: 17px; padding: 20px; scroll-margin-top: 90px; }
.draft-check .subsection-heading p { margin-top: 6px; }
.check-outcome { display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 10px; }
.saved-finding-help { margin-top: 5px !important; }
.check-findings { display: grid; gap: 12px; }
.finding-group { border: 1px solid var(--color-border); border-radius: 7px; padding: 14px; display: grid; gap: 10px; }
.finding-group-heading { display: flex; align-items: center; flex-wrap: wrap; gap: 9px; font-size: 12px; }
.finding-group-heading .badge { margin-left: auto; font-size: 10px; }
.finding-group details { font-size: 12px; line-height: 1.7; }
.finding-group summary { cursor: pointer; color: var(--color-text-muted); }
.finding-group ul { padding-left: 18px; }
.finding-group .app-btn { justify-self: start; }
.component-pagination { display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 10px; }
.coverage-filter { flex: 0 1 180px; min-width: 130px; }
.checklist-link { text-align: left; color: var(--color-text); background: transparent; border: 0; padding: 0; font: inherit; font-size: 12px; font-weight: 500; cursor: pointer; }
.checklist-link:hover { color: var(--color-primary); text-decoration: underline; text-underline-offset: 3px; }
@media (max-height: 760px) { .advisor-sidebar { position: static !important; } }

.advisor-page { gap: 20px; min-width: 0; }
.advisor-page h2, .advisor-page h3, .advisor-page h4, .advisor-page p { margin: 0; }
.advisor-page h2 { font-size: 16px; font-weight: 700; } .advisor-page h3 { font-size: 15px; } .advisor-page h4 { font-size: 13px; }
.advisor-page a { text-underline-offset: 3px; } .breadcrumbs { display: flex; flex-wrap: wrap; align-items: center; gap: 9px; font-size: 12px; color: var(--color-text-muted); }
.breadcrumbs a { color: var(--color-text-muted); text-decoration: none; } .breadcrumbs a:hover { color: var(--color-text); }
.heading-label { font-size: 10px; letter-spacing: .12em; font-weight: 700; color: var(--color-text-muted); margin-bottom: 8px; } .heading-label span { margin: 0 6px; }
.page-subtitle { font-size: 13px; line-height: 1.6; margin-top: 7px !important; }
.actions { display: flex; align-items: center; flex-wrap: wrap; gap: 8px; } .button-count { padding: 1px 6px; border-radius: 4px; background: var(--color-surface-elevated-strong); }
.scope-bar { display: flex; gap: 24px; align-items: center; padding: 16px 20px; } .release-field { flex: 0 1 320px; } .scope-note { display: grid; gap: 7px; font-size: 12px; } .scope-note .badge { justify-self: start; } .text-link { margin-left: auto; font-size: 12px; white-space: nowrap; }
.advisor-page .input, .advisor-page .select, .advisor-page .textarea { box-sizing: border-box; border-radius: 6px; font: inherit; font-size: 13px; padding: 9px 11px; min-width: 0; background: var(--color-surface-soft); } .advisor-page .textarea { line-height: 1.65; }
.advisor-page .field-label { font-size: 12px; letter-spacing: 0; } .field-label span { color: var(--color-primary); } .advisor-page .field-hint { line-height: 1.5; }
.summary-grid { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 12px; }
.summary-card { display: grid; gap: 10px; padding: 18px; border: 1px solid var(--color-border); background: var(--color-surface); border-radius: var(--radius-lg); color: var(--color-text); text-decoration: none; }
a.summary-card:hover { border-color: var(--color-primary); } .metric-label { font-size: 12px; color: var(--color-text-muted); } .summary-card strong { font-size: 25px; font-weight: 750; letter-spacing: -.04em; line-height: 1.25; } .summary-card strong small { font-size: 16px; color: var(--color-text-muted); font-weight: 400; } .summary-card > .muted { font-size: 11px; line-height: 1.6; } .metric-warning strong { color: var(--color-warning-text); }
.section-nav { display: flex; gap: 6px; border-bottom: 1px solid var(--color-border); padding-bottom: 10px; } .section-nav a { display: flex; gap: 8px; align-items: center; font-size: 11px; color: var(--color-text-muted); text-decoration: none; padding: 9px 12px; border-radius: 6px; } .section-nav a span { font-size: 13px; color: var(--color-text); } .section-nav a:hover { background: var(--color-surface-elevated); } .section-nav .nav-count { font-size: 11px; background: var(--color-surface-elevated); padding: 1px 6px; border-radius: 4px; }
.workspace-grid { display: grid; grid-template-columns: minmax(0, 1fr) 300px; align-items: start; gap: 20px; } .assessment-form, .editor-fields, .advisor-sidebar { display: grid; gap: 20px; min-width: 0; } .editor-fields { padding: 0; margin: 0; border: 0; } .editor-fields:disabled { opacity: .8; }
.section-card { padding: 22px; display: grid; gap: 20px; min-width: 0; scroll-margin-top: 90px; } #justification-evidence, #supplier-timeline, #support-justification { scroll-margin-top: 90px; }
.section-heading { display: flex; gap: 12px; align-items: flex-start; } .section-heading > .badge { margin-left: auto; flex-shrink: 0; } .section-heading p { font-size: 12px; line-height: 1.6; margin-top: 5px; } .section-number { width: 29px; height: 29px; display: grid; place-items: center; background: var(--color-success-bg); border: 1px solid var(--color-success-border); color: var(--color-success-text); border-radius: 7px; font-size: 11px; font-weight: 700; flex-shrink: 0; }
.source-note { display: flex; align-items: baseline; gap: 9px; padding: 11px 13px; font-size: 12px; line-height: 1.65; color: var(--color-text-muted); background: var(--color-surface-elevated); border-radius: 6px; } .source-dot { width: 6px; height: 6px; border-radius: 50%; background: var(--color-primary); flex-shrink: 0; }
.date-grid { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 14px; align-items: start; } .disclosure { border: 1px solid var(--color-border); border-radius: 6px; } .disclosure summary, .remediation-disclosure summary { padding: 11px 13px; cursor: pointer; font-size: 12px; font-weight: 600; } summary .muted { font-size: 11px; font-weight: 400; margin-left: 8px; } .reference-notes { margin: 0; padding: 0 14px 14px; font-size: 12px; } .reference-notes dt { font-weight: 600; margin-top: 10px; } .reference-notes dd { color: var(--color-text-muted); margin: 5px 0 0; line-height: 1.6; white-space: pre-wrap; }
.evidence-section { display: grid; gap: 12px; } .evidence-section > p { font-size: 12px; line-height: 1.6; } .subsection-heading { display: flex; align-items: center; justify-content: space-between; gap: 12px; } .evidence-list { display: grid; gap: 7px; max-height: 300px; overflow-y: auto; } .evidence-option { display: flex; align-items: center; gap: 10px; padding: 12px; font-size: 12px; border: 1px solid var(--color-border); border-radius: 6px; cursor: pointer; } .evidence-option.selected { background: var(--color-success-bg); border-color: var(--color-success-border); } .evidence-option input, .check input { accent-color: var(--color-primary); flex-shrink: 0; width: 15px; height: 15px; } .document-icon { color: var(--color-text-muted); } .selection-label { color: var(--color-success-text); margin-left: auto; font-size: 10px; }
.coverage-toolbar { display: flex; flex-wrap: wrap; align-items: center; justify-content: space-between; gap: 16px; } .search-field { flex: 1; max-width: 350px; } .check { display: flex; align-items: center; gap: 8px; font-size: 12px; cursor: pointer; } .timeline-legend { display: flex; flex-wrap: wrap; gap: 15px; color: var(--color-text-muted); font-size: 10px; } .timeline-legend span { display: flex; gap: 6px; align-items: center; } .legend-dot { display: inline-block; width: 9px; height: 9px; border-radius: 2px; } .committed { background: var(--color-primary); } .gap { background: var(--color-warning-bg); border: 1px solid var(--color-warning-border); } .unknown { background: var(--color-surface-elevated-strong); border: 1px dashed var(--color-text-muted); }
.timeline-axis { display: flex; justify-content: space-between; gap: 10px; font-size: 10px; color: var(--color-text-muted); } .timeline-axis span:nth-child(2) { color: var(--color-subtle-text); }
.component-row { scroll-margin-top: 90px; padding-bottom: 18px; border-bottom: 1px solid var(--color-border); min-width: 0; } .component-heading { display: flex; justify-content: space-between; gap: 12px; align-items: flex-start; margin-bottom: 13px; } .component-name { font-size: 13px; font-weight: 600; text-decoration: none; } .component-heading p { margin-top: 5px; } .component-name .muted { font-weight: 400; margin-left: 4px; } .component-heading .badge { font-size: 10px; white-space: nowrap; }
.timeline-track { height: 11px; border-radius: 3px; background: var(--color-warning-bg); border: 1px solid var(--color-warning-border); overflow: hidden; } .timeline-bar { height: 100%; display: block; background: var(--color-primary); } .timeline-unknown { background: repeating-linear-gradient(135deg, var(--color-surface-elevated), var(--color-surface-elevated) 5px, var(--color-surface-elevated-strong) 5px, var(--color-surface-elevated-strong) 9px); border: 1px dashed var(--color-border); }
.component-dates { display: flex; justify-content: space-between; flex-wrap: wrap; gap: 5px 12px; margin: 8px 0 12px; font-size: 10px; color: var(--color-text-muted); } .warning-text { color: var(--color-warning-text); } .small-text { font-size: 11px; line-height: 1.65; } .remediation-disclosure { border-radius: 6px; background: var(--color-surface-elevated); } .remediation-disclosure summary { font-weight: 500; } .remediation-fields { padding: 3px 13px 13px; display: grid; gap: 13px; } .evidence-fieldset { border: 0; padding: 0; margin: 0; display: grid; gap: 8px; } .evidence-fieldset legend { margin-bottom: 8px; } .coverage-count { margin-top: -5px !important; }
.save-bar { display: flex; align-items: center; justify-content: space-between; gap: 14px; border: 1px solid var(--color-border); background: var(--color-surface); border-radius: 8px; padding: 16px; } .save-bar strong { font-size: 12px; } .save-bar p { margin-top: 4px; } .advisor-sidebar { position: sticky; top: 85px; } .checklist-card, .context-card { display: grid; gap: 15px; padding: 18px; } .advisor-sidebar h2 { font-size: 13px; } .checklist { list-style: none; padding: 0; margin: 0; display: grid; gap: 17px; } .checklist li { display: flex; gap: 10px; align-items: flex-start; } .checklist strong { font-size: 12px; font-weight: 500; } .checklist p { margin-top: 3px; } .check-marker { border: 1px solid var(--color-border); color: var(--color-text-muted); border-radius: 50%; width: 19px; height: 19px; display: grid; place-items: center; flex-shrink: 0; font-size: 12px; } .check-marker.complete { background: var(--color-success-bg); color: var(--color-success-text); border-color: var(--color-success-border); } .sidebar-note { border-top: 1px solid var(--color-border); padding-top: 12px; color: var(--color-text-muted); font-size: 11px; line-height: 1.7; }
.context-counts { margin: 0; display: grid; gap: 12px; } .context-counts div { display: flex; justify-content: space-between; font-size: 12px; } .context-counts dt { color: var(--color-text-muted); } .context-counts dd { margin: 0; font-weight: 600; } .context-records { padding: 0 15px 12px 30px; display: grid; gap: 10px; font-size: 12px; } .context-records span { display: block; } .guidance-note { display: grid; gap: 12px; padding: 0 8px; font-size: 11px; line-height: 1.7; color: var(--color-text-muted); } .guidance-note h3 { font-size: 12px; color: var(--color-text); } .guidance-note .heading-label { margin: 0; } .guidance-note strong { color: var(--color-text); font-weight: 500; }
.history-grid { display: grid; grid-template-columns: 210px minmax(0, 1fr); gap: 24px; } .version-list { display: flex; flex-direction: column; gap: 8px; max-height: 650px; overflow-y: auto; } .version-item { display: grid; gap: 9px; background: transparent; border: 1px solid var(--color-border); color: var(--color-text); border-radius: 7px; padding: 13px; text-align: left; cursor: pointer; font: inherit; } .version-item.active { border-color: var(--color-primary); background: var(--color-success-bg); } .version-item .badge { justify-self: start; font-size: 10px; } .version-top { display: flex; justify-content: space-between; align-items: center; gap: 5px; font-size: 12px; } .latest-label { font-size: 9px; font-weight: 500; color: var(--color-text-muted); } .decision-detail { display: grid; gap: 17px; min-width: 0; } .decision-heading { display: flex; justify-content: space-between; align-items: center; gap: 12px; } .decision-heading p { margin-top: 5px; } .decision-dates { display: flex; flex-wrap: wrap; gap: 20px 35px; margin: 0; font-size: 12px; } .decision-dates dt { font-size: 10px; color: var(--color-text-muted); margin-bottom: 6px; } .decision-dates dd { margin: 0; } .outcomes { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); border: 1px solid var(--color-border); border-radius: 7px; } .outcomes div { padding: 13px; display: grid; gap: 7px; } .outcomes div + div { border-left: 1px solid var(--color-border); } .outcomes span { font-size: 10px; color: var(--color-text-muted); } .outcomes strong { font-size: 12px; font-weight: 500; } .rationale-copy, .saved-remediation p { font-size: 12px; line-height: 1.75; white-space: pre-wrap; overflow-wrap: anywhere; }
.findings { list-style: none; margin: 0; padding: 0; display: grid; gap: 9px; } .findings li { display: flex; align-items: baseline; gap: 10px; padding: 11px 13px; background: var(--color-surface-elevated); border-radius: 6px; font-size: 12px; line-height: 1.65; } .rule-label { font-size: 10px; font-weight: 600; color: var(--color-text-muted); white-space: nowrap; } .table-scroll { overflow: auto; padding: 0 10px 8px; } .table { font-size: 11px; } .table th { font-weight: 500; color: var(--color-text-muted); } .document-list { font-size: 12px; line-height: 1.7; padding: 0 16px 0 30px; overflow-wrap: anywhere; } .saved-remediation { padding: 12px 15px; border-top: 1px solid var(--color-border); font-size: 12px; } .saved-remediation p { margin-top: 8px; } .review-record { background: var(--color-surface-elevated); border-radius: 6px; padding: 15px; display: grid; gap: 10px; font-size: 12px; overflow-wrap: anywhere; } .review-form { display: grid; gap: 12px; padding-top: 18px; border-top: 1px solid var(--color-border); } .follow-up { display: flex; justify-content: space-between; gap: 15px; align-items: center; border-top: 1px solid var(--color-border); padding-top: 15px; }
.feedback-banner { display: flex; flex-wrap: wrap; gap: 8px 12px; align-items: center; font-size: 12px; line-height: 1.6; } .feedback-banner > span { flex: 1 1 200px; } .loading-state { display: grid; justify-items: center; gap: 14px; padding: 60px; font-size: 13px; } .advisor-page :is(a, button, summary, input):focus-visible { outline: 2px solid var(--color-primary); outline-offset: 3px; }
@media (max-width: 1200px) { .workspace-grid { grid-template-columns: minmax(0, 1fr) 260px; gap: 14px; } .section-card { padding: 18px; } .date-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); } .date-grid .field:last-child { grid-column: 1 / -1; } .summary-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); } .scope-note { max-width: 280px; } }
@media (max-width: 1000px) { .workspace-grid { grid-template-columns: minmax(0, 1fr); } .advisor-sidebar { position: static; display: grid; grid-template-columns: 1fr 1fr; } .guidance-note { grid-column: 1 / -1; padding: 10px; } .scope-bar { flex-wrap: wrap; gap: 16px; } .release-field { flex: 1 1 250px; } .scope-note { flex: 1; } .text-link { margin-left: 0; } }
@media (max-width: 640px) { .coverage-filter { flex: initial; width: 100%; } .draft-check { padding: 15px; }  .advisor-page { gap: 15px; } .page-title { font-size: 24px; } .page-header .actions { width: 100%; } .summary-grid { gap: 8px; } .summary-card { padding: 13px; gap: 8px; } .summary-card strong { font-size: 22px; } .summary-card > .muted { font-size: 10px; } .scope-bar { padding: 14px; } .scope-note { flex-basis: 100%; max-width: none; } .section-nav { gap: 0; overflow-x: auto; } .section-nav a { white-space: nowrap; padding: 8px; } .section-nav a span { font-size: 11px; } .section-nav .nav-count { display: none; } .section-card { padding: 15px; gap: 17px; } .section-heading { flex-wrap: wrap; gap: 10px; } .section-heading > div:nth-child(2) { flex: 1; } .section-heading > .badge { margin-left: 39px; } .date-grid { grid-template-columns: 1fr; } .advisor-sidebar { grid-template-columns: 1fr; } .save-bar, .coverage-toolbar, .follow-up { flex-direction: column; align-items: stretch; } .search-field { max-width: none; } .component-heading { flex-direction: column; gap: 8px; } .timeline-axis span:nth-child(2) { display: none; } .history-grid { grid-template-columns: minmax(0, 1fr); } .version-list { flex-direction: row; max-height: none; overflow-x: auto; padding-bottom: 5px; } .version-item { min-width: 180px; flex-shrink: 0; } .outcomes { grid-template-columns: 1fr; } .outcomes div + div { border-left: 0; border-top: 1px solid var(--color-border); } .decision-heading { flex-wrap: wrap; } .disclosure summary .muted, .remediation-disclosure summary .muted { display: block; margin: 5px 0 0 13px; } }
@media (prefers-reduced-motion: reduce) { .advisor-page * { scroll-behavior: auto; } }
</style>
