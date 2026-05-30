<template>
  <section class="page">

    <!-- ══════════════════════════════════════════
         PAGE HEADER
         ══════════════════════════════════════════ -->
    <header class="page-header">
      <div>
        <h1 class="page-title">Support Hub</h1>
        <p class="muted page-subtitle">
          Customer support and lifecycle tooling — track support periods, manage Art. 13(7)
          disclosures, and look up CVEs across the product fleet.
        </p>
      </div>
      <div class="page-actions">
        <AppButton variant="secondary" :disabled="isLoading" @click="loadAll">
          <svg class="btn-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round">
            <path d="M21 12a9 9 0 1 1-3-6.7L21 8"/><path d="M21 3v5h-5"/>
          </svg>
          Refresh
        </AppButton>
        <AppButton variant="primary" @click="downloadEosList">
          <svg class="btn-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round">
            <path d="M12 3v12m0 0l-4-4m4 4l4-4M5 21h14"/>
          </svg>
          Export watch list
        </AppButton>
      </div>
    </header>

    <!-- ══════════════════════════════════════════
         LOADING / ERROR FEEDBACK
         ══════════════════════════════════════════ -->
    <div v-if="isLoading && products.length === 0" class="empty-panel muted">
      Loading Support Hub data…
    </div>
    <div v-if="loadError" class="feedback feedback-error" role="alert">
      {{ loadError }}
    </div>

    <template v-if="!isLoading || products.length > 0">

      <!-- ══════════════════════════════════════════
           KPI STRIP
           ══════════════════════════════════════════ -->
      <section class="kpi-strip" aria-label="Summary statistics">

        <article class="kpi-card">
          <div class="kpi-top">
            <span class="kpi-label">Products tracked</span>
            <span class="kpi-icon">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round">
                <path d="M20 7l-8-4-8 4v6c0 5 3.5 7.5 8 9 4.5-1.5 8-4 8-9V7z"/>
              </svg>
            </span>
          </div>
          <strong class="kpi-value">{{ products.length }}</strong>
          <p class="kpi-sub muted">Across the inventory</p>
        </article>

        <article class="kpi-card">
          <div class="kpi-top">
            <span class="kpi-label">Active support periods</span>
            <span class="kpi-icon kpi-icon--green">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round">
                <circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/>
              </svg>
            </span>
          </div>
          <strong class="kpi-value">{{ activeSupportPeriods.length }}</strong>
          <p class="kpi-sub">
            <span v-if="expiredCount > 0" class="badge badge-danger">{{ expiredCount }} expired</span>
            <span v-else class="muted">None expired</span>
          </p>
        </article>

        <article class="kpi-card">
          <div class="kpi-top">
            <span class="kpi-label">Approaching EOS</span>
            <span class="kpi-icon">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round">
                <rect x="3" y="5" width="18" height="16" rx="2"/><path d="M16 3v4M8 3v4M3 10h18"/>
              </svg>
            </span>
          </div>
          <strong class="kpi-value" :class="approachingEosCount > 0 ? 'kpi-value--warn' : 'kpi-value--muted'">
            {{ approachingEosCount }}
          </strong>
          <p class="kpi-sub muted">Within 90 days</p>
        </article>

        <article class="kpi-card">
          <div class="kpi-top">
            <span class="kpi-label">Pending notifications</span>
            <span class="kpi-icon">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round">
                <path d="M6 8a6 6 0 0 1 12 0c0 7 3 9 3 9H3s3-2 3-9"/><path d="M10 21a2 2 0 0 0 4 0"/>
              </svg>
            </span>
          </div>
          <strong class="kpi-value" :class="pendingNotifications.length > 0 ? 'kpi-value--warn' : 'kpi-value--muted'">
            {{ pendingNotifications.length }}
          </strong>
          <p class="kpi-sub">
            <span v-if="pendingNotifications.length === 0" class="badge badge-success">All dispatched</span>
            <span v-else class="muted">Awaiting dispatch</span>
          </p>
        </article>

        <article class="kpi-card">
          <div class="kpi-top">
            <span class="kpi-label">Active market actions</span>
            <span class="kpi-icon">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round">
                <path d="M12 9v4M12 17h.01M10.3 3.86 1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/>
              </svg>
            </span>
          </div>
          <strong class="kpi-value" :class="activeMarketActionsCount > 0 ? 'kpi-value--danger' : 'kpi-value--muted'">
            {{ activeMarketActionsCount }}
          </strong>
          <p class="kpi-sub muted">No recalls or withdrawals</p>
        </article>

      </section>

      <!-- ══════════════════════════════════════════
           TWO-COLUMN GRID — main content + right rail
           ══════════════════════════════════════════ -->
      <div class="hub-grid">

        <!-- ── MAIN COLUMN ── -->
        <div class="hub-main">

          <!-- ════════════════════════════════════
               PANEL 1 — EOS WATCH LIST (hero)
               ════════════════════════════════════ -->
          <section class="card panel">

            <div class="panel-header">
              <div>
                <h2 class="section-title">EOS watch list</h2>
                <p class="muted">
                  Products with a defined support period, ordered by urgency.
                </p>
              </div>
              <div class="eos-filter-row">
                <label class="field-inline">
                  <span class="field-label-xs">Show</span>
                  <select v-model="eosThreshold" class="select-sm">
                    <option value="">All with support</option>
                    <option value="expired">Expired only</option>
                    <option value="30">≤ 30 days</option>
                    <option value="60">≤ 60 days</option>
                    <option value="90">≤ 90 days</option>
                    <option value="180">≤ 180 days</option>
                  </select>
                </label>
              </div>
            </div>

            <div v-if="filteredEosRows.length === 0" class="empty-panel muted">
              No products match the selected threshold.
            </div>

            <div v-else class="table-wrapper">
              <table class="data-table eos-table">
                <thead>
                  <tr>
                    <th>Product</th>
                    <th>Classification</th>
                    <th>Support end</th>
                    <th>Time remaining</th>
                    <th>Status</th>
                    <th>Type</th>
                  </tr>
                </thead>
                <tbody>
                  <tr
                    v-for="row in filteredEosRows"
                    :key="row.product.id"
                    :class="row.daysLeft < 0 ? 'eos-row--expired' : ''"
                  >
                    <td>
                      <div class="eos-product-cell">
                        <div class="eos-mark">{{ productInitials(row.product) }}</div>
                        <div>
                          <div class="eos-product-name">{{ row.product.name }}</div>
                          <code class="eos-product-code muted">{{ row.product.product_code }}</code>
                        </div>
                      </div>
                    </td>

                    <td>
                      <span class="badge" :class="classificationBadge(row.product.current_classification)">
                        {{ formatClassification(row.product.current_classification) }}
                      </span>
                    </td>

                    <td>
                      <div class="eos-date-main">{{ formatDate(row.support.support_end_date) }}</div>
                      <div class="eos-date-rel muted">{{ formatRelativeDate(row.support.support_end_date) }}</div>
                    </td>

                    <td>
                      <div :class="eosDaysClass(row.daysLeft)">
                        <div class="eos-days-label">
                          {{ formatDaysLeft(row.daysLeft) }}
                        </div>
                        <div class="eos-bar">
                          <span
                            class="eos-bar-fill"
                            :style="{ width: eosBarWidth(row.daysLeft) }"
                          />
                        </div>
                      </div>
                    </td>

                    <td>
                      <span class="badge" :class="supportStatusBadge(row.eosStatus)">
                        {{ formatEosStatus(row.eosStatus) }}
                      </span>
                    </td>

                    <td class="muted">{{ formatSupportType(row.support.support_type) }}</td>
                  </tr>
                </tbody>
              </table>
            </div>

            <!-- Panel footer -->
            <div v-if="expiredCount > 0" class="eos-footer">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round" class="eos-footer-icon">
                <circle cx="12" cy="12" r="9"/><path d="M12 8v4"/><circle cx="12" cy="16" r="0.5" fill="currentColor"/>
              </svg>
              <span>
                <strong>{{ expiredCount }} product{{ expiredCount > 1 ? 's' : '' }}</strong>
                {{ expiredCount > 1 ? 'need' : 'needs' }} a support-period decision —
                {{ firstExpiredProduct }} lapsed {{ formatDaysOverdue(eosRows.find(r => r.daysLeft < 0)?.daysLeft ?? 0) }}.
              </span>
            </div>

          </section>

          <!-- ════════════════════════════════════
               PANEL 2 — PRODUCT SUPPORT LOOKUP
               ════════════════════════════════════ -->
          <section class="card panel">

            <div class="panel-header">
              <div>
                <h2 class="section-title">Product support lookup</h2>
                <p class="muted">
                  Find support status, Art. 13(7) disclosure text, and recent security patches.
                </p>
              </div>
            </div>

            <!-- Search input -->
            <div class="lookup-search-row">
              <label class="field field-grow">
                <span class="field-label">Search product</span>
                <input
                  v-model.trim="lookupQuery"
                  type="search"
                  class="input"
                  placeholder="Product name or code…"
                  autocomplete="off"
                  @focus="showDropdown = true"
                  @blur="onLookupBlur"
                />
              </label>
              <AppButton
                v-if="selectedProductId"
                variant="secondary"
                size="sm"
                style="align-self: flex-end;"
                @click="clearLookup"
              >
                Clear
              </AppButton>
            </div>

            <!-- Autocomplete dropdown -->
            <ul
              v-if="showDropdown && lookupQuery && lookupDropdownItems.length > 0"
              class="lookup-dropdown"
              role="listbox"
            >
              <li
                v-for="product in lookupDropdownItems"
                :key="product.id"
                class="lookup-option"
                role="option"
                @mousedown.prevent="selectProduct(product.id)"
              >
                <span class="lookup-option-name">{{ product.name }}</span>
                <code class="lookup-option-code muted">{{ product.product_code }}</code>
              </li>
            </ul>

            <div v-if="showDropdown && lookupQuery && lookupDropdownItems.length === 0" class="lookup-no-results muted">
              No products matched "{{ lookupQuery }}".
            </div>

            <!-- ── Selected product result ── -->
            <div v-if="selectedProduct" class="lookup-result">

              <div class="result-identity">
                <div>
                  <h3 class="result-product-name">{{ selectedProduct.name }}</h3>
                  <p class="muted result-product-meta">
                    {{ selectedProduct.manufacturer_name }} · <code>{{ selectedProduct.product_code }}</code>
                  </p>
                </div>
                <span class="badge" :class="classificationBadge(selectedProduct.current_classification)">
                  {{ formatClassification(selectedProduct.current_classification) }}
                </span>
              </div>

              <div v-if="selectedSupport" class="result-section">
                <h4 class="result-section-title">Support period (CRA Art. 13(7))</h4>

                <div class="support-meta-row">
                  <span class="badge" :class="supportStatusBadge(selectedEosStatus)">
                    {{ formatEosStatus(selectedEosStatus) }}
                  </span>
                  <span class="muted">
                    {{ formatDate(selectedSupport.support_start_date) }} –
                    {{ formatDate(selectedSupport.support_end_date) }}
                  </span>
                  <span :class="daysLeftClass(selectedDaysLeft)">
                    {{ formatDaysLeft(selectedDaysLeft) }}
                  </span>
                  <span class="badge badge-neutral">
                    {{ formatSupportType(selectedSupport.support_type) }}
                  </span>
                </div>

                <div v-if="selectedSupport.user_facing_summary" class="disclosure-block">
                  <div class="disclosure-header">
                    <span class="field-label">User-facing disclosure text (Art. 13(7))</span>
                    <button class="btn-copy" type="button" @click="copyText(selectedSupport.user_facing_summary!)">
                      {{ copySuccessId === 'user' ? 'Copied!' : 'Copy' }}
                    </button>
                  </div>
                  <p class="disclosure-text">{{ selectedSupport.user_facing_summary }}</p>
                </div>

                <div v-if="selectedSupport.packaging_summary" class="disclosure-block">
                  <div class="disclosure-header">
                    <span class="field-label">Packaging summary</span>
                    <button class="btn-copy" type="button" @click="copyText(selectedSupport.packaging_summary!, 'pkg')">
                      {{ copySuccessId === 'pkg' ? 'Copied!' : 'Copy' }}
                    </button>
                  </div>
                  <p class="disclosure-text">{{ selectedSupport.packaging_summary }}</p>
                </div>

                <p v-if="!selectedSupport.user_facing_summary && !selectedSupport.packaging_summary" class="muted">
                  No disclosure text generated yet. Generate it from the product's support period record.
                </p>
              </div>

              <div v-else class="result-section">
                <p class="muted">No active support period record found for this product.</p>
              </div>

              <div class="result-section">
                <h4 class="result-section-title">Recent security updates</h4>
                <div v-if="selectedSecurityUpdates.length === 0" class="muted">
                  No security update records found for this product.
                </div>
                <div v-else class="table-wrapper">
                  <table class="data-table">
                    <thead>
                      <tr>
                        <th>Title</th>
                        <th>Severity</th>
                        <th>CVEs addressed</th>
                        <th>Affected versions</th>
                        <th>Released</th>
                      </tr>
                    </thead>
                    <tbody>
                      <tr v-for="upd in selectedSecurityUpdates.slice(0, 8)" :key="upd.id">
                        <td>{{ upd.title }}</td>
                        <td>
                          <span class="badge" :class="severityBadge(upd.severity)">
                            {{ formatSeverity(upd.severity) }}
                          </span>
                        </td>
                        <td>
                          <div class="cve-chips">
                            <span
                              v-for="cve in normaliseCves(upd.cves_addressed_json)"
                              :key="cve"
                              class="cve-chip"
                            >{{ cve }}</span>
                            <span v-if="normaliseCves(upd.cves_addressed_json).length === 0" class="muted">—</span>
                          </div>
                        </td>
                        <td class="muted">{{ normaliseVersions(upd.affected_versions_json).join(', ') || '—' }}</td>
                        <td class="muted">{{ upd.released_at ? formatDate(upd.released_at) : '—' }}</td>
                      </tr>
                    </tbody>
                  </table>
                </div>
              </div>

            </div><!-- /lookup-result -->

            <div v-else-if="!lookupQuery" class="empty-panel muted">
              Start typing a product name or code above to look up its CRA support status.
            </div>

          </section>

        </div><!-- /hub-main -->

        <!-- ── RIGHT RAIL ── -->
        <div class="hub-rail">

          <!-- ════════════════════════════════════
               PANEL 3 — CVE LOOKUP
               ════════════════════════════════════ -->
          <section class="card panel">

            <div class="panel-header">
              <div>
                <h2 class="section-title">CVE lookup</h2>
                <p class="muted">
                  Match a CVE to security-update records.
                </p>
              </div>
            </div>

            <label class="field">
              <span class="field-label">CVE identifier</span>
              <input
                v-model.trim="cveQuery"
                type="search"
                class="input input-mono"
                placeholder="CVE-YYYY-NNNNN"
                autocomplete="off"
              />
            </label>

            <!-- Quick chips -->
            <div class="cve-chips-row">
              <span class="field-label-xs">Try</span>
              <button class="chip" type="button" @click="cveQuery = 'CVE-2024-12345'">CVE-2024-12345</button>
              <button class="chip" type="button" @click="cveQuery = 'CVE-2025-0042'">CVE-2025-0042</button>
            </div>

            <template v-if="cveQuery">
              <div v-if="cveResults.length === 0" class="empty-panel muted">
                No records found for <strong>{{ cveQuery }}</strong>.
              </div>
              <div v-else>
                <p class="muted" style="margin-bottom: 0.6rem; font-size: var(--text-sm);">
                  {{ cveResults.length }} record(s) for <strong>{{ cveQuery }}</strong>
                </p>
                <div class="table-wrapper">
                  <table class="data-table">
                    <thead>
                      <tr>
                        <th>Product</th>
                        <th>Update</th>
                        <th>Severity</th>
                        <th>Released</th>
                      </tr>
                    </thead>
                    <tbody>
                      <tr v-for="upd in cveResults" :key="upd.id">
                        <td>
                          <span v-if="productByReleaseId(upd.product_release_id)" class="product-cell">
                            <strong>{{ productByReleaseId(upd.product_release_id)!.name }}</strong>
                            <code class="muted">{{ productByReleaseId(upd.product_release_id)!.product_code }}</code>
                          </span>
                          <code v-else class="muted">{{ upd.product_release_id.slice(0, 8) }}…</code>
                        </td>
                        <td><strong>{{ upd.title }}</strong></td>
                        <td>
                          <span class="badge" :class="severityBadge(upd.severity)">
                            {{ formatSeverity(upd.severity) }}
                          </span>
                        </td>
                        <td class="muted">{{ upd.released_at ? formatDate(upd.released_at) : '—' }}</td>
                      </tr>
                    </tbody>
                  </table>
                </div>
              </div>
            </template>

            <div v-else class="empty-panel muted">
              Enter a CVE identifier to search across all security update records.
            </div>

          </section>

          <!-- ════════════════════════════════════
               PANEL 4 — NOTIFICATION QUEUE
               ════════════════════════════════════ -->
          <section class="card panel">

            <div class="panel-header">
              <div>
                <h2 class="section-title">
                  Notification queue
                </h2>
                <p class="muted">Lifecycle communications awaiting dispatch.</p>
              </div>
              <span class="badge badge-neutral">{{ pendingNotifications.length }}</span>
            </div>

            <div v-if="notifActionError" class="feedback feedback-error" role="alert">
              {{ notifActionError }}
            </div>

            <!-- All-clear state -->
            <div v-if="pendingNotifications.length === 0" class="all-clear">
              <div class="all-clear-icon">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round">
                  <path d="M20 6L9 17l-5-5"/>
                </svg>
              </div>
              <div>
                <div class="all-clear-title">Queue is clear</div>
                <div class="muted all-clear-desc">
                  All lifecycle notifications have been dispatched. New EOS or security update events will appear here.
                </div>
              </div>
            </div>

            <!-- Notifications list -->
            <div v-else class="notif-list">
              <div
                v-for="notif in pendingNotifications"
                :key="notif.id"
                class="notif-item"
              >
                <div class="notif-body">
                  <div class="notif-product">
                    <span v-if="notifProduct(notif)">
                      <strong>{{ notifProduct(notif)!.name }}</strong>
                      <code class="muted">{{ notifProduct(notif)!.product_code }}</code>
                    </span>
                    <span v-else class="muted">—</span>
                  </div>
                  <strong class="notif-title">{{ notif.title }}</strong>
                  <p class="muted notif-message">{{ notif.message }}</p>
                  <div class="notif-meta muted">
                    {{ notif.recipient_user?.full_name ?? '—' }}
                    <span v-if="notif.recipient_user?.email"> · {{ notif.recipient_user.email }}</span>
                    · {{ formatDate(notif.scheduled_for) }}
                  </div>
                </div>
                <div class="notif-actions">
                  <AppButton
                    variant="primary"
                    size="sm"
                    :disabled="!!actionLoading[notif.id]"
                    @click="markSent(notif.id)"
                  >
                    {{ actionLoading[notif.id] === 'sent' ? 'Saving…' : 'Mark sent' }}
                  </AppButton>
                  <AppButton
                    variant="secondary"
                    size="sm"
                    :disabled="!!actionLoading[notif.id]"
                    @click="dismiss(notif.id)"
                  >
                    {{ actionLoading[notif.id] === 'dismiss' ? 'Saving…' : 'Dismiss' }}
                  </AppButton>
                </div>
              </div>
            </div>

          </section>

        </div><!-- /hub-rail -->

      </div><!-- /hub-grid -->

      <!-- ══════════════════════════════════════════
           PANEL 5 — PRODUCT RECALLS & WITHDRAWALS
           Full-width below the grid
           ══════════════════════════════════════════ -->
      <section class="card panel">

        <div class="panel-header">
          <div>
            <h2 class="section-title">Product recalls &amp; withdrawals</h2>
            <p class="muted">
              CRA Art. 35 workflow — initiate, track, and close recalls and withdrawals of non-compliant products.
            </p>
          </div>
          <div class="page-actions">
            <AppButton
              variant="secondary"
              size="sm"
              :disabled="showMarketActionForm"
              @click="openMarketActionForm('recall')"
            >
              Initiate recall
            </AppButton>
            <AppButton
              variant="secondary"
              size="sm"
              :disabled="showMarketActionForm"
              @click="openMarketActionForm('withdrawal')"
            >
              Initiate withdrawal
            </AppButton>
          </div>
        </div>

        <!-- Inline create / edit form -->
        <div v-if="showMarketActionForm" class="ma-form-panel">
          <h3 class="ma-form-title">
            {{ editingMarketAction ? 'Edit market action' : (marketActionFormType === 'recall' ? 'Initiate recall' : 'Initiate withdrawal') }}
          </h3>

          <div v-if="maFormError" class="feedback feedback-error" role="alert">
            {{ maFormError }}
          </div>

          <div class="form-grid">
            <label class="field">
              <span class="field-label">Product release <span class="required">*</span></span>
              <select v-model="maForm.product_release_id" class="select" :disabled="!!editingMarketAction">
                <option value="">— select release —</option>
                <option v-for="rel in allReleases" :key="rel.id" :value="rel.id">
                  {{ productById[rel.product_id]?.name ?? rel.product_id.slice(0, 8) }} — v{{ rel.display_version }}
                  ({{ rel.release_status }})
                </option>
              </select>
            </label>

            <label class="field">
              <span class="field-label">Reason <span class="required">*</span></span>
              <textarea v-model="maForm.reason" class="input textarea" rows="3" placeholder="Describe why this action is necessary (min 10 characters)…" />
            </label>

            <label class="field">
              <span class="field-label">Affected scope</span>
              <textarea v-model="maForm.affected_scope" class="input textarea" rows="2" placeholder="Which product batches / serial ranges are affected?" />
            </label>

            <label class="field">
              <span class="field-label">Corrective action</span>
              <textarea v-model="maForm.corrective_action" class="input textarea" rows="2" placeholder="What remediation or replacement is being provided?" />
            </label>

            <label class="field">
              <span class="field-label">User notice text</span>
              <textarea v-model="maForm.user_notice_text" class="input textarea" rows="3" placeholder="Public-facing notice for end users…" />
            </label>

            <label class="field">
              <span class="field-label">Authority reference number</span>
              <input v-model="maForm.authority_reference_number" type="text" class="input" placeholder="e.g. BSI-2025-MA-001" maxlength="255" />
            </label>

            <label class="field">
              <span class="field-label">Internal notes</span>
              <textarea v-model="maForm.internal_notes" class="input textarea" rows="2" placeholder="Internal tracking notes (not shown to end users)…" />
            </label>
          </div>

          <div class="form-actions">
            <AppButton variant="primary" size="sm" :disabled="maFormSaving" @click="saveMarketAction">
              {{ maFormSaving ? 'Saving…' : (editingMarketAction ? 'Save changes' : 'Create draft') }}
            </AppButton>
            <AppButton variant="secondary" size="sm" :disabled="maFormSaving" @click="cancelMarketActionForm">
              Cancel
            </AppButton>
          </div>
        </div>

        <div v-if="maListError" class="feedback feedback-error" role="alert">
          {{ maListError }}
        </div>

        <div v-if="marketActions.length === 0 && !showMarketActionForm" class="empty-panel muted">
          No market actions recorded yet. Use the buttons above to initiate a recall or withdrawal under CRA Art. 35.
        </div>

        <div v-else-if="marketActions.length > 0" class="table-wrapper">
          <table class="data-table">
            <thead>
              <tr>
                <th>Product / release</th>
                <th>Type</th>
                <th>Status</th>
                <th>Authority notified</th>
                <th>Initiated</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="ma in marketActions" :key="ma.id">
                <td>
                  <div class="product-cell">
                    <strong>
                      {{ productById[ma.product_release?.product_id ?? '']?.name ?? '—' }}
                    </strong>
                    <code class="muted">v{{ ma.product_release?.display_version ?? '?' }}</code>
                  </div>
                </td>

                <td>
                  <span class="badge" :class="ma.action_type === 'recall' ? 'badge-danger' : 'badge-warning'">
                    {{ ma.action_type === 'recall' ? 'Recall' : 'Withdrawal' }}
                  </span>
                </td>

                <td>
                  <span class="badge" :class="maStatusBadge(ma.status)">
                    {{ formatMaStatus(ma.status) }}
                  </span>
                </td>

                <td class="muted">
                  {{ ma.authority_notified_at ? formatDate(ma.authority_notified_at) : '—' }}
                </td>

                <td class="muted">{{ formatDate(ma.created_at) }}</td>

                <td>
                  <div class="action-row">
                    <AppButton
                      v-if="ma.status !== 'closed'"
                      variant="secondary"
                      size="sm"
                      :disabled="!!maActionLoading[ma.id] || showMarketActionForm"
                      @click="editMarketAction(ma)"
                    >
                      Edit
                    </AppButton>
                    <AppButton
                      v-if="ma.status === 'draft'"
                      variant="secondary"
                      size="sm"
                      :disabled="!!maActionLoading[ma.id]"
                      @click="activateMarketAction(ma.id)"
                    >
                      {{ maActionLoading[ma.id] === 'activate' ? 'Activating…' : 'Activate' }}
                    </AppButton>
                    <AppButton
                      v-if="ma.user_notice_text"
                      variant="secondary"
                      size="sm"
                      @click="copyNoticeText(ma)"
                    >
                      {{ maCopySuccessId === ma.id ? 'Copied!' : 'Copy notice' }}
                    </AppButton>
                    <AppButton
                      v-if="ma.status === 'active'"
                      variant="secondary"
                      size="sm"
                      :disabled="!!maActionLoading[ma.id]"
                      @click="notifyAuthority(ma.id)"
                    >
                      {{ maActionLoading[ma.id] === 'notify' ? 'Saving…' : 'Mark notified' }}
                    </AppButton>
                    <AppButton
                      v-if="ma.status === 'active' || ma.status === 'authority_notified'"
                      variant="secondary"
                      size="sm"
                      :disabled="!!maActionLoading[ma.id]"
                      @click="closeMarketAction(ma.id)"
                    >
                      {{ maActionLoading[ma.id] === 'close' ? 'Closing…' : 'Close' }}
                    </AppButton>
                    <AppButton
                      v-if="ma.status === 'draft'"
                      variant="danger"
                      size="sm"
                      :disabled="!!maActionLoading[ma.id]"
                      @click="deleteMarketAction(ma.id)"
                    >
                      {{ maActionLoading[ma.id] === 'delete' ? 'Deleting…' : 'Delete' }}
                    </AppButton>
                  </div>
                </td>
              </tr>
            </tbody>
          </table>
        </div>

      </section>

    </template>

  </section>
</template>

<script setup lang="ts">
import { computed, ref } from "vue";

import AppButton from "@/components/AppButton.vue";
import { lifecycleNotificationService } from "@/services/lifecycle-notification-service";
import { marketActionService } from "@/services/market-action-service";
import { productReleaseService } from "@/services/product-release-service";
import { productService } from "@/services/product-service";
import { securityUpdateService } from "@/services/security-update-service";
import { supportPeriodService } from "@/services/support-period-service";

import type { MarketActionRead, MarketActionStatus, MarketActionType } from "@/types/market-action";
import type { ProductReleaseRead } from "@/types/release-gate";
import type {
  LifecycleNotificationRead,
  ProductClassification,
  ProductSummaryRead,
  SecurityUpdateRead,
  SecurityUpdateSeverity,
  SupportPeriodRecordRead,
  SupportType,
} from "@/types/product";

/* ── EOS status label used throughout the page ── */
type EosStatus = "active" | "approaching_eos" | "expired";

/* ── Row shape for the EOS watch list table ── */
type EosRow = {
  product: ProductSummaryRead;
  support: SupportPeriodRecordRead;
  daysLeft: number;
  eosStatus: EosStatus;
};

/* ─────────────────────────────────────────────────
   REACTIVE DATA — raw API results
   ───────────────────────────────────────────────── */
const products              = ref<ProductSummaryRead[]>([]);
const activeSupportPeriods  = ref<SupportPeriodRecordRead[]>([]);
const pendingNotifications  = ref<LifecycleNotificationRead[]>([]);
const allSecurityUpdates    = ref<SecurityUpdateRead[]>([]);
const allReleases           = ref<ProductReleaseRead[]>([]);
const marketActions         = ref<MarketActionRead[]>([]);

const isLoading   = ref(false);
const loadError   = ref<string | null>(null);
const maListError = ref<string | null>(null);

/* ─────────────────────────────────────────────────
   LOOKUP MAPS — computed from raw data
   ───────────────────────────────────────────────── */

/** product.id → ProductSummaryRead */
const productById = computed<Record<string, ProductSummaryRead>>(() =>
  Object.fromEntries(products.value.map((p) => [p.id, p])),
);

/** support_period_record.product_id → SupportPeriodRecordRead (active only) */
const supportByProductId = computed<Record<string, SupportPeriodRecordRead>>(() =>
  Object.fromEntries(activeSupportPeriods.value.map((s) => [s.product_id, s])),
);

/** support_period_record.id → SupportPeriodRecordRead (for notification → product resolution) */
const supportByRecordId = computed<Record<string, SupportPeriodRecordRead>>(() =>
  Object.fromEntries(activeSupportPeriods.value.map((s) => [s.id, s])),
);

/** product_release.id → product_id (to resolve security updates → product name) */
const releaseProductIdMap = computed<Record<string, string>>(() =>
  Object.fromEntries(allReleases.value.map((r) => [r.id, r.product_id])),
);

/* ─────────────────────────────────────────────────
   DATA LOADING
   ───────────────────────────────────────────────── */
async function loadAll(): Promise<void> {
  isLoading.value = true;
  loadError.value = null;
  maListError.value = null;

  try {
    /* Fetch core data sources in parallel. Market actions are fetched separately
       so that a migration-not-applied or permission error does not break the rest
       of the page. */
    const [loadedProducts, loadedSupports, loadedNotifs, loadedUpdates, loadedReleases] =
      await Promise.all([
        productService.list(),
        supportPeriodService.list({ active_only: true }),
        lifecycleNotificationService.list({ status: "pending" }),
        securityUpdateService.list(),
        productReleaseService.list(),
      ]);

    products.value             = loadedProducts;
    activeSupportPeriods.value = loadedSupports;
    pendingNotifications.value = loadedNotifs;
    allSecurityUpdates.value   = loadedUpdates;
    allReleases.value          = loadedReleases;
  } catch (err) {
    loadError.value = err instanceof Error ? err.message : "Failed to load Support Hub data.";
  } finally {
    isLoading.value = false;
  }

  /* Market actions — isolated so failures don't affect the rest of the page. */
  try {
    marketActions.value = await marketActionService.list();
  } catch (err) {
    maListError.value =
      err instanceof Error ? err.message : "Failed to load market actions.";
  }
}

/* Load on component mount */
void loadAll();

/* ─────────────────────────────────────────────────
   PANEL 1 — PRODUCT SUPPORT LOOKUP
   ───────────────────────────────────────────────── */
const lookupQuery      = ref("");
const selectedProductId = ref<string | null>(null);
const showDropdown     = ref(false);
const copySuccessId    = ref<string | null>(null);

/** Autocomplete candidates — first 8 products matching the query */
const lookupDropdownItems = computed<ProductSummaryRead[]>(() => {
  const q = lookupQuery.value.toLowerCase();
  if (!q) return [];
  return products.value
    .filter(
      (p) =>
        p.name.toLowerCase().includes(q) ||
        p.product_code.toLowerCase().includes(q),
    )
    .slice(0, 8);
});

const selectedProduct = computed<ProductSummaryRead | null>(() =>
  selectedProductId.value ? (productById.value[selectedProductId.value] ?? null) : null,
);

const selectedSupport = computed<SupportPeriodRecordRead | null>(() =>
  selectedProductId.value ? (supportByProductId.value[selectedProductId.value] ?? null) : null,
);

/** Days remaining until the selected product's support period ends */
const selectedDaysLeft = computed<number>(() =>
  selectedSupport.value ? getDaysLeft(selectedSupport.value.support_end_date) : 0,
);

const selectedEosStatus = computed<EosStatus>(() =>
  selectedSupport.value ? deriveEosStatus(selectedDaysLeft.value) : "active",
);

/** Release IDs belonging to the selected product (for security update lookup) */
const selectedReleaseIds = computed<Set<string>>(() => {
  if (!selectedProductId.value) return new Set();
  return new Set(
    allReleases.value
      .filter((r) => r.product_id === selectedProductId.value)
      .map((r) => r.id),
  );
});

/** Security updates that belong to any release of the selected product, newest first */
const selectedSecurityUpdates = computed<SecurityUpdateRead[]>(() =>
  allSecurityUpdates.value
    .filter((u) => selectedReleaseIds.value.has(u.product_release_id))
    .sort((a, b) => {
      const dateA = a.released_at ?? a.created_at;
      const dateB = b.released_at ?? b.created_at;
      return new Date(dateB).getTime() - new Date(dateA).getTime();
    }),
);

function selectProduct(productId: string): void {
  selectedProductId.value = productId;
  const product = productById.value[productId];
  lookupQuery.value = product?.name ?? "";
  showDropdown.value = false;
}

function clearLookup(): void {
  selectedProductId.value = null;
  lookupQuery.value = "";
  showDropdown.value = false;
}

function onLookupBlur(): void {
  /* Delay so the mousedown on a dropdown item fires first */
  setTimeout(() => {
    showDropdown.value = false;
  }, 150);
}

async function copyText(text: string, id = "user"): Promise<void> {
  try {
    await navigator.clipboard.writeText(text);
    copySuccessId.value = id;
    setTimeout(() => {
      copySuccessId.value = null;
    }, 1800);
  } catch {
    /* Clipboard access denied — silently ignore */
  }
}

/* ─────────────────────────────────────────────────
   PANEL 2 — EOS WATCH LIST
   ───────────────────────────────────────────────── */
const eosThreshold = ref<"30" | "60" | "90" | "180" | "expired" | "">("");

/** All products that have an active support period, sorted by days remaining ascending */
const eosRows = computed<EosRow[]>(() =>
  products.value
    .flatMap((product) => {
      const support = supportByProductId.value[product.id];
      if (!support) return [];
      const daysLeft = getDaysLeft(support.support_end_date);
      return [{ product, support, daysLeft, eosStatus: deriveEosStatus(daysLeft) }];
    })
    .sort((a, b) => a.daysLeft - b.daysLeft),
);

const filteredEosRows = computed<EosRow[]>(() => {
  switch (eosThreshold.value) {
    case "30":
      return eosRows.value.filter((r) => r.daysLeft >= 0 && r.daysLeft <= 30);
    case "60":
      return eosRows.value.filter((r) => r.daysLeft >= 0 && r.daysLeft <= 60);
    case "90":
      return eosRows.value.filter((r) => r.daysLeft >= 0 && r.daysLeft <= 90);
    case "180":
      return eosRows.value.filter((r) => r.daysLeft >= 0 && r.daysLeft <= 180);
    case "expired":
      return eosRows.value.filter((r) => r.daysLeft < 0);
    default:
      return eosRows.value;
  }
});

/** Count of products with ≤ 90 days of support remaining (used in KPI card) */
const approachingEosCount = computed<number>(
  () => eosRows.value.filter((r) => r.daysLeft >= 0 && r.daysLeft <= 90).length,
);

/** Count of expired support periods (used in KPI card) */
const expiredCount = computed<number>(
  () => eosRows.value.filter((r) => r.daysLeft < 0).length,
);

/** Name of the first expired product for the EOS footer message */
const firstExpiredProduct = computed<string | null>(
  () => eosRows.value.find((r) => r.daysLeft < 0)?.product.name ?? null,
);

/** CSV export of the current (filtered) EOS watch list */
function downloadEosList(): void {
  const headers = ["Product", "Code", "Classification", "Support End", "Days Left", "Status", "Support Type"];
  const rows = filteredEosRows.value.map((r) => [
    r.product.name,
    r.product.product_code,
    formatClassification(r.product.current_classification),
    r.support.support_end_date,
    r.daysLeft.toString(),
    formatEosStatus(r.eosStatus),
    formatSupportType(r.support.support_type),
  ]);
  const csv = [headers, ...rows].map((row) => row.map((cell) => `"${cell}"`).join(",")).join("\n");
  const blob = new Blob([csv], { type: "text/csv" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = "eos-watch-list.csv";
  a.click();
  URL.revokeObjectURL(url);
}

/* ─────────────────────────────────────────────────
   PANEL 3 — NOTIFICATION QUEUE
   ───────────────────────────────────────────────── */

/** Per-notification action state: notif.id → 'sent' | 'dismiss' | null */
const actionLoading    = ref<Record<string, "sent" | "dismiss" | null>>({});
const notifActionError = ref<string | null>(null);

/**
 * Resolves the product for a given lifecycle notification by traversing:
 * notification.support_period_record_id → support period → product_id → product
 */
function notifProduct(notif: LifecycleNotificationRead): ProductSummaryRead | null {
  if (!notif.support_period_record_id) return null;
  const support = supportByRecordId.value[notif.support_period_record_id];
  if (!support) return null;
  return productById.value[support.product_id] ?? null;
}

async function markSent(notifId: string): Promise<void> {
  actionLoading.value[notifId] = "sent";
  notifActionError.value = null;
  try {
    await lifecycleNotificationService.markSent(notifId);
    /* Remove from local queue immediately for optimistic UI update */
    pendingNotifications.value = pendingNotifications.value.filter((n) => n.id !== notifId);
  } catch (err) {
    notifActionError.value = err instanceof Error ? err.message : "Failed to mark notification as sent.";
  } finally {
    actionLoading.value[notifId] = null;
  }
}

async function dismiss(notifId: string): Promise<void> {
  actionLoading.value[notifId] = "dismiss";
  notifActionError.value = null;
  try {
    await lifecycleNotificationService.dismiss(notifId);
    /* Remove from local queue */
    pendingNotifications.value = pendingNotifications.value.filter((n) => n.id !== notifId);
  } catch (err) {
    notifActionError.value = err instanceof Error ? err.message : "Failed to dismiss notification.";
  } finally {
    actionLoading.value[notifId] = null;
  }
}

/* ─────────────────────────────────────────────────
   PANEL 4 — CVE LOOKUP
   ───────────────────────────────────────────────── */
const cveQuery = ref("");

/** Security updates whose cves_addressed_json contains the searched CVE (case-insensitive) */
const cveResults = computed<SecurityUpdateRead[]>(() => {
  const q = cveQuery.value.trim().toUpperCase();
  if (!q) return [];
  return allSecurityUpdates.value.filter((upd) =>
    normaliseCves(upd.cves_addressed_json).some((cve) =>
      cve.toUpperCase().includes(q),
    ),
  );
});

/**
 * Resolves the product that owns a given product release ID.
 * Uses the precomputed releaseProductIdMap to avoid per-row API calls.
 */
function productByReleaseId(releaseId: string): ProductSummaryRead | null {
  const productId = releaseProductIdMap.value[releaseId];
  return productId ? (productById.value[productId] ?? null) : null;
}

/* ─────────────────────────────────────────────────
   PANEL 5 — PRODUCT RECALLS & WITHDRAWALS
   ───────────────────────────────────────────────── */

/** Count of market actions that are not yet closed (draft + active + authority_notified). */
const activeMarketActionsCount = computed<number>(
  () => marketActions.value.filter((ma) => ma.status !== "closed").length,
);

/* ── Form state ── */
const showMarketActionForm   = ref(false);
const marketActionFormType   = ref<MarketActionType>("recall");
const editingMarketAction    = ref<MarketActionRead | null>(null);
const maFormSaving           = ref(false);
const maFormError            = ref<string | null>(null);
const maCopySuccessId        = ref<string | null>(null);

/** Per-action loading key: action.id → operation name */
const maActionLoading = ref<Record<string, "activate" | "notify" | "close" | "delete" | null>>({});

const emptyMaForm = () => ({
  product_release_id: "",
  reason: "",
  affected_scope: "",
  corrective_action: "",
  authority_reference_number: "",
  user_notice_text: "",
  internal_notes: "",
});

const maForm = ref(emptyMaForm());

function openMarketActionForm(type: MarketActionType): void {
  marketActionFormType.value = type;
  editingMarketAction.value  = null;
  maForm.value               = emptyMaForm();
  maFormError.value          = null;
  showMarketActionForm.value = true;
}

function editMarketAction(ma: MarketActionRead): void {
  editingMarketAction.value      = ma;
  marketActionFormType.value     = ma.action_type;
  maForm.value = {
    product_release_id:         ma.product_release_id,
    reason:                     ma.reason,
    affected_scope:             ma.affected_scope ?? "",
    corrective_action:          ma.corrective_action ?? "",
    authority_reference_number: ma.authority_reference_number ?? "",
    user_notice_text:           ma.user_notice_text ?? "",
    internal_notes:             ma.internal_notes ?? "",
  };
  maFormError.value          = null;
  showMarketActionForm.value = true;
}

function cancelMarketActionForm(): void {
  showMarketActionForm.value = false;
  editingMarketAction.value  = null;
  maFormError.value          = null;
}

async function saveMarketAction(): Promise<void> {
  if (!maForm.value.product_release_id) {
    maFormError.value = "Please select a product release.";
    return;
  }
  if (maForm.value.reason.trim().length < 10) {
    maFormError.value = "Reason must be at least 10 characters.";
    return;
  }

  maFormSaving.value = true;
  maFormError.value  = null;

  try {
    const nullify = (v: string) => v.trim() || null;

    if (editingMarketAction.value) {
      const updated = await marketActionService.update(editingMarketAction.value.id, {
        reason:                     maForm.value.reason.trim(),
        affected_scope:             nullify(maForm.value.affected_scope),
        corrective_action:          nullify(maForm.value.corrective_action),
        authority_reference_number: nullify(maForm.value.authority_reference_number),
        user_notice_text:           nullify(maForm.value.user_notice_text),
        internal_notes:             nullify(maForm.value.internal_notes),
      });
      const idx = marketActions.value.findIndex((m) => m.id === updated.id);
      if (idx !== -1) marketActions.value[idx] = updated;
    } else {
      const created = await marketActionService.create({
        product_release_id:         maForm.value.product_release_id,
        action_type:                marketActionFormType.value,
        reason:                     maForm.value.reason.trim(),
        affected_scope:             nullify(maForm.value.affected_scope),
        corrective_action:          nullify(maForm.value.corrective_action),
        authority_reference_number: nullify(maForm.value.authority_reference_number),
        user_notice_text:           nullify(maForm.value.user_notice_text),
        internal_notes:             nullify(maForm.value.internal_notes),
      });
      marketActions.value.unshift(created);
    }

    showMarketActionForm.value = false;
    editingMarketAction.value  = null;
  } catch (err) {
    maFormError.value = err instanceof Error ? err.message : "Failed to save market action.";
  } finally {
    maFormSaving.value = false;
  }
}

async function activateMarketAction(actionId: string): Promise<void> {
  maActionLoading.value[actionId] = "activate";
  maListError.value = null;
  try {
    const updated = await marketActionService.update(actionId, { status: "active" });
    const idx = marketActions.value.findIndex((m) => m.id === actionId);
    if (idx !== -1) marketActions.value[idx] = updated;
    allReleases.value = await productReleaseService.list();
  } catch (err) {
    maListError.value = err instanceof Error ? err.message : "Failed to activate market action.";
  } finally {
    maActionLoading.value[actionId] = null;
  }
}

async function notifyAuthority(actionId: string): Promise<void> {
  maActionLoading.value[actionId] = "notify";
  maListError.value = null;
  try {
    const updated = await marketActionService.markAuthorityNotified(actionId);
    const idx = marketActions.value.findIndex((m) => m.id === actionId);
    if (idx !== -1) marketActions.value[idx] = updated;
  } catch (err) {
    maListError.value = err instanceof Error ? err.message : "Failed to mark authority notified.";
  } finally {
    maActionLoading.value[actionId] = null;
  }
}

async function closeMarketAction(actionId: string): Promise<void> {
  maActionLoading.value[actionId] = "close";
  maListError.value = null;
  try {
    const updated = await marketActionService.close(actionId);
    const idx = marketActions.value.findIndex((m) => m.id === actionId);
    if (idx !== -1) marketActions.value[idx] = updated;
  } catch (err) {
    maListError.value = err instanceof Error ? err.message : "Failed to close market action.";
  } finally {
    maActionLoading.value[actionId] = null;
  }
}

async function deleteMarketAction(actionId: string): Promise<void> {
  maActionLoading.value[actionId] = "delete";
  maListError.value = null;
  try {
    await marketActionService.remove(actionId);
    marketActions.value = marketActions.value.filter((m) => m.id !== actionId);
  } catch (err) {
    maListError.value = err instanceof Error ? err.message : "Failed to delete market action.";
  } finally {
    maActionLoading.value[actionId] = null;
  }
}

async function copyNoticeText(ma: MarketActionRead): Promise<void> {
  if (!ma.user_notice_text) return;
  try {
    await navigator.clipboard.writeText(ma.user_notice_text);
    maCopySuccessId.value = ma.id;
    setTimeout(() => { maCopySuccessId.value = null; }, 1800);
  } catch {
    /* Clipboard access denied */
  }
}

function maStatusBadge(status: MarketActionStatus): string {
  switch (status) {
    case "draft":               return "badge-neutral";
    case "active":              return "badge-danger";
    case "authority_notified":  return "badge-warning";
    case "closed":              return "badge-success";
  }
}

function formatMaStatus(status: MarketActionStatus): string {
  switch (status) {
    case "draft":               return "Draft";
    case "active":              return "Active";
    case "authority_notified":  return "Authority notified";
    case "closed":              return "Closed";
  }
}

/* ─────────────────────────────────────────────────
   SHARED HELPER FUNCTIONS
   ───────────────────────────────────────────────── */

/** Returns whole days remaining until the given ISO date string. Negative = overdue. */
function getDaysLeft(endDateValue: string): number {
  const today = new Date();
  today.setHours(0, 0, 0, 0);
  const end = new Date(`${endDateValue}T00:00:00`);
  end.setHours(0, 0, 0, 0);
  return Math.ceil((end.getTime() - today.getTime()) / 86_400_000);
}

function deriveEosStatus(daysLeft: number): EosStatus {
  if (daysLeft < 0) return "expired";
  if (daysLeft <= 180) return "approaching_eos";
  return "active";
}

/** Two-letter monogram from product name for the EOS table avatar. */
function productInitials(product: ProductSummaryRead): string {
  return product.name.slice(0, 2).toUpperCase();
}

/** Progress bar width for the EOS days-remaining bar (0–100%). */
function eosBarWidth(daysLeft: number): string {
  if (daysLeft < 0) return "100%";
  return `${Math.min(100, Math.round((daysLeft / 730) * 100))}%`;
}

/** CSS class for the EOS days indicator block. */
function eosDaysClass(daysLeft: number): string {
  if (daysLeft < 0) return "eos-days eos-days--over";
  if (daysLeft <= 90) return "eos-days eos-days--warn";
  return "eos-days eos-days--ok";
}

/** Human-readable relative date for the EOS table (e.g. "29 days ago", "in ~22 months"). */
function formatRelativeDate(isoDate: string): string {
  const date = new Date(`${isoDate}T00:00:00`);
  const now = new Date();
  const diffDays = Math.ceil((now.getTime() - date.getTime()) / 86_400_000);
  if (diffDays < 0) {
    const months = Math.round(Math.abs(diffDays) / 30);
    return `in ~${months} month${months !== 1 ? "s" : ""}`;
  }
  if (diffDays === 0) return "today";
  return `${diffDays} day${diffDays !== 1 ? "s" : ""} ago`;
}

/** EOS footer message: how many days overdue (absolute value). */
function formatDaysOverdue(daysLeft: number): string {
  const abs = Math.abs(daysLeft);
  return `${abs} day${abs !== 1 ? "s" : ""} ago`;
}

/** Normalise cves_addressed_json to a flat string array regardless of backend shape */
function normaliseCves(raw: string[] | Record<string, unknown>): string[] {
  if (Array.isArray(raw)) return raw as string[];
  return Object.keys(raw);
}

/** Normalise affected_versions_json to a flat string array */
function normaliseVersions(raw: string[] | Record<string, unknown>): string[] {
  if (Array.isArray(raw)) return raw as string[];
  return Object.keys(raw);
}

function formatDate(value: string): string {
  return new Intl.DateTimeFormat(undefined, {
    year: "numeric",
    month: "short",
    day: "2-digit",
  }).format(new Date(value));
}

function formatDaysLeft(daysLeft: number): string {
  if (daysLeft < 0) return `${Math.abs(daysLeft)}d overdue`;
  if (daysLeft === 0) return "Ends today";
  return `${daysLeft}d remaining`;
}

function daysLeftClass(daysLeft: number): string {
  if (daysLeft < 0) return "text-danger fw-600";
  if (daysLeft <= 90) return "text-warning fw-600";
  return "text-success fw-600";
}

function formatEosStatus(status: EosStatus): string {
  switch (status) {
    case "active":          return "Active";
    case "approaching_eos": return "Approaching EOS";
    case "expired":         return "Expired";
  }
}

function supportStatusBadge(status: EosStatus): string {
  switch (status) {
    case "active":          return "badge-success";
    case "approaching_eos": return "badge-warning";
    case "expired":         return "badge-danger";
  }
}

function formatClassification(value: ProductClassification): string {
  switch (value) {
    case "important_class_1": return "Important Class I";
    case "important_class_2": return "Important Class II";
    case "critical":          return "Critical";
    default:                  return "Default";
  }
}

function classificationBadge(value: ProductClassification): string {
  switch (value) {
    case "critical":         return "badge-danger";
    case "important_class_1":
    case "important_class_2": return "badge-warning";
    default:                  return "badge-neutral";
  }
}

function formatSupportType(type: SupportType): string {
  switch (type) {
    case "standard": return "Standard";
    case "limited":  return "Limited";
    case "extended": return "Extended";
    case "custom":   return "Custom";
  }
}

function formatSeverity(severity: SecurityUpdateSeverity | null): string {
  if (!severity) return "None";
  return severity.charAt(0).toUpperCase() + severity.slice(1);
}

function severityBadge(severity: SecurityUpdateSeverity | null): string {
  switch (severity) {
    case "critical":      return "badge-danger";
    case "high":          return "badge-danger";
    case "medium":        return "badge-warning";
    case "low":           return "badge-success";
    case "informational": return "badge-neutral";
    default:              return "badge-neutral";
  }
}
</script>

<style scoped>
/* ═══════════════════════════════════════════════
   PAGE SHELL
   ═══════════════════════════════════════════════ */
.page {
  display: grid;
  gap: 1rem;
}

.page-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 1rem;
  flex-wrap: wrap;
}

.page-actions {
  display: flex;
  gap: 0.5rem;
  align-items: center;
  flex-shrink: 0;
}

.btn-icon {
  width: 14px;
  height: 14px;
  flex-shrink: 0;
}

.page-subtitle {
  margin-top: 0.35rem;
}

/* ═══════════════════════════════════════════════
   KPI STRIP
   ═══════════════════════════════════════════════ */
.kpi-strip {
  display: grid;
  grid-template-columns: repeat(5, minmax(0, 1fr));
  gap: 0.75rem;
}

.kpi-card {
  background: var(--color-surface, #0f172a);
  border: 1px solid var(--color-border, rgba(148, 163, 184, 0.2));
  border-radius: var(--radius-md, 0.85rem);
  padding: 0.9rem 1rem;
  display: flex;
  flex-direction: column;
  gap: 0.6rem;
}

.kpi-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.kpi-label {
  font-size: var(--text-xs, 0.75rem);
  font-weight: 500;
  color: var(--color-text-muted, #94a3b8);
  line-height: 1.3;
}

.kpi-icon {
  width: 26px;
  height: 26px;
  border-radius: 7px;
  background: rgba(148, 163, 184, 0.1);
  display: grid;
  place-items: center;
  color: var(--color-text-muted, #94a3b8);
  flex-shrink: 0;
}

.kpi-icon svg {
  width: 13px;
  height: 13px;
  stroke-width: 1.75;
}

.kpi-icon--green {
  background: rgba(52, 211, 153, 0.12);
  color: #86efac;
}

.kpi-value {
  font-size: 1.65rem;
  font-weight: 600;
  letter-spacing: -0.02em;
  line-height: 1;
  color: inherit;
  font-variant-numeric: tabular-nums;
}

.kpi-value--muted { color: var(--color-text-muted, #94a3b8); }
.kpi-value--warn  { color: #fde68a; }
.kpi-value--danger { color: #fda4af; }

.kpi-sub {
  margin: 0;
  font-size: var(--text-xs, 0.75rem);
  display: flex;
  align-items: center;
  gap: 0.4rem;
  min-height: 1.4rem;
}

/* ═══════════════════════════════════════════════
   TWO-COLUMN GRID
   ═══════════════════════════════════════════════ */
.hub-grid {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 340px;
  gap: 1rem;
  align-items: start;
}

.hub-main,
.hub-rail {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

/* ═══════════════════════════════════════════════
   PANELS — shared card layout
   ═══════════════════════════════════════════════ */
.panel {
  display: grid;
  gap: 1rem;
}

.panel-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 1rem;
  flex-wrap: wrap;
}

.section-title {
  margin: 0;
  font-size: var(--text-base, 1rem);
  font-weight: 600;
}

/* ═══════════════════════════════════════════════
   EOS WATCH LIST — enhanced table
   ═══════════════════════════════════════════════ */
.eos-filter-row {
  display: flex;
  align-items: flex-end;
  gap: 0.5rem;
}

.field-inline {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.field-label-xs {
  font-size: var(--text-xs, 0.75rem);
  font-weight: 600;
  color: var(--color-text-muted, #94a3b8);
  text-transform: uppercase;
  letter-spacing: 0.06em;
  white-space: nowrap;
}

.select-sm {
  height: 30px;
  padding: 0 26px 0 9px;
  border-radius: 0.55rem;
  border: 1px solid var(--color-border, rgba(148, 163, 184, 0.2));
  background: var(--color-surface-soft, rgba(15, 23, 42, 0.45));
  color: inherit;
  font: 500 var(--text-sm, 0.875rem) / 1 inherit;
  cursor: pointer;
  appearance: none;
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='%2394a3b8' stroke-width='1.75'%3E%3Cpath d='M6 9l6 6 6-6'/%3E%3C/svg%3E");
  background-repeat: no-repeat;
  background-position: right 7px center;
  background-size: 14px;
}

/* EOS product avatar */
.eos-product-cell {
  display: flex;
  align-items: center;
  gap: 0.65rem;
}

.eos-mark {
  width: 30px;
  height: 30px;
  border-radius: 7px;
  background: rgba(148, 163, 184, 0.1);
  border: 1px solid var(--color-border, rgba(148, 163, 184, 0.2));
  display: grid;
  place-items: center;
  font-size: var(--text-xs, 0.75rem);
  font-weight: 700;
  color: var(--color-text-muted, #94a3b8);
  flex-shrink: 0;
  letter-spacing: 0.03em;
}

.eos-product-name {
  font-weight: 600;
  font-size: var(--text-sm, 0.875rem);
  color: inherit;
}

.eos-product-code {
  display: block;
  font-size: var(--text-xs, 0.75rem);
  margin-top: 1px;
}

.eos-date-main {
  font-weight: 500;
  font-size: var(--text-sm, 0.875rem);
}

.eos-date-rel {
  font-size: var(--text-xs, 0.75rem);
  margin-top: 1px;
}

/* Days remaining block with progress bar */
.eos-days {
  display: flex;
  flex-direction: column;
  gap: 5px;
  min-width: 110px;
}

.eos-days-label {
  font-weight: 600;
  font-size: var(--text-sm, 0.875rem);
  font-variant-numeric: tabular-nums;
}

.eos-days--over .eos-days-label { color: #fda4af; }
.eos-days--warn .eos-days-label { color: #fde68a; }
.eos-days--ok   .eos-days-label { color: #86efac; }

.eos-bar {
  height: 4px;
  border-radius: 999px;
  background: rgba(148, 163, 184, 0.12);
  overflow: hidden;
}

.eos-bar-fill {
  display: block;
  height: 100%;
  border-radius: 999px;
  transition: width 0.3s ease;
}

.eos-days--over .eos-bar-fill { background: #fda4af; }
.eos-days--warn .eos-bar-fill { background: #fde68a; }
.eos-days--ok   .eos-bar-fill { background: #86efac; }

/* Expired row left-border accent */
.eos-table tbody tr.eos-row--expired td:first-child {
  box-shadow: inset 3px 0 0 rgba(253, 164, 175, 0.6);
}

/* EOS panel footer */
.eos-footer {
  display: flex;
  align-items: center;
  gap: 0.6rem;
  padding: 0.7rem 1rem;
  border-top: 1px solid var(--color-border, rgba(148, 163, 184, 0.18));
  background: rgba(148, 163, 184, 0.04);
  font-size: var(--text-sm, 0.875rem);
  color: var(--color-text-muted, #94a3b8);
  border-radius: 0 0 var(--radius-md, 0.85rem) var(--radius-md, 0.85rem);
  margin: 0 -1rem -1rem;
}

.eos-footer strong {
  color: inherit;
}

.eos-footer-icon {
  width: 15px;
  height: 15px;
  flex-shrink: 0;
  stroke-width: 1.75;
}

/* ═══════════════════════════════════════════════
   PRODUCT LOOKUP
   ═══════════════════════════════════════════════ */
.lookup-search-row {
  display: flex;
  gap: 0.75rem;
  align-items: flex-end;
  flex-wrap: wrap;
  position: relative;
}

.field-grow {
  flex: 1;
  min-width: 0;
}

.lookup-dropdown {
  list-style: none;
  margin: 0;
  padding: 0.3rem;
  border: 1px solid var(--color-border, rgba(148, 163, 184, 0.2));
  border-radius: var(--radius-md, 0.85rem);
  background: var(--color-surface, #0f172a);
  box-shadow: var(--shadow-lg);
  max-height: 260px;
  overflow-y: auto;
  position: relative;
  z-index: 10;
}

.lookup-option {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 0.75rem;
  padding: 0.6rem 0.8rem;
  border-radius: 0.6rem;
  cursor: pointer;
  transition: background var(--t-fast);
}

.lookup-option:hover {
  background: var(--color-nav-hover-bg, rgba(148, 163, 184, 0.08));
}

.lookup-option-name {
  font-weight: 600;
  font-size: var(--text-sm, 0.875rem);
}

.lookup-option-code {
  font-size: var(--text-xs, 0.75rem);
}

.lookup-no-results {
  padding: 0.6rem 0;
  font-size: var(--text-sm, 0.875rem);
}

.lookup-result {
  display: grid;
  gap: 1.25rem;
  padding: 1.1rem;
  border: 1px solid var(--color-border, rgba(148, 163, 184, 0.18));
  border-radius: var(--radius-md, 0.85rem);
  background: var(--color-surface-soft, rgba(15, 23, 42, 0.45));
}

.result-identity {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 1rem;
  flex-wrap: wrap;
}

.result-product-name {
  margin: 0;
  font-size: var(--text-lg, 1.125rem);
}

.result-product-meta {
  margin: 0.2rem 0 0;
  font-size: var(--text-sm, 0.875rem);
}

.result-section {
  display: grid;
  gap: 0.65rem;
}

.result-section-title {
  margin: 0;
  font-size: var(--text-xs, 0.75rem);
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: var(--color-text-muted, #94a3b8);
}

.support-meta-row {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  flex-wrap: wrap;
}

.disclosure-block {
  display: grid;
  gap: 0.5rem;
}

.disclosure-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.5rem;
}

.disclosure-text {
  margin: 0;
  font-size: var(--text-sm, 0.875rem);
  line-height: 1.6;
  padding: 0.75rem 0.9rem;
  border: 1px solid var(--color-border, rgba(148, 163, 184, 0.15));
  border-radius: 0.65rem;
  background: var(--color-surface, rgba(15, 23, 42, 0.6));
  white-space: pre-wrap;
}

.btn-copy {
  font: inherit;
  font-size: var(--text-xs, 0.75rem);
  padding: 0.25rem 0.6rem;
  border-radius: 0.5rem;
  border: 1px solid var(--color-border, rgba(148, 163, 184, 0.25));
  background: transparent;
  color: var(--color-primary-2, #add654);
  cursor: pointer;
  transition: background var(--t-fast);
  flex-shrink: 0;
}

.btn-copy:hover {
  background: rgba(173, 214, 84, 0.1);
}

/* ═══════════════════════════════════════════════
   CVE LOOKUP — chip suggestions
   ═══════════════════════════════════════════════ */
.cve-chips-row {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  flex-wrap: wrap;
}

.chip {
  font-size: var(--text-xs, 0.75rem);
  font-weight: 500;
  color: var(--color-text-muted, #94a3b8);
  background: rgba(148, 163, 184, 0.08);
  border: 1px solid var(--color-border, rgba(148, 163, 184, 0.2));
  padding: 0.2rem 0.6rem;
  border-radius: 999px;
  cursor: pointer;
  font-family: var(--font-mono, monospace);
  transition: background var(--t-fast);
}

.chip:hover {
  background: rgba(148, 163, 184, 0.15);
  color: inherit;
}

/* ═══════════════════════════════════════════════
   NOTIFICATION QUEUE — all-clear + compact list
   ═══════════════════════════════════════════════ */
.all-clear {
  display: flex;
  align-items: flex-start;
  gap: 0.85rem;
  padding: 0.25rem 0;
}

.all-clear-icon {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background: rgba(52, 211, 153, 0.12);
  color: #86efac;
  display: grid;
  place-items: center;
  flex-shrink: 0;
}

.all-clear-icon svg {
  width: 16px;
  height: 16px;
  stroke-width: 2;
}

.all-clear-title {
  font-weight: 600;
  font-size: var(--text-sm, 0.875rem);
  margin-bottom: 0.2rem;
}

.all-clear-desc {
  font-size: var(--text-xs, 0.75rem);
  line-height: 1.5;
}

.notif-list {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.notif-item {
  display: flex;
  flex-direction: column;
  gap: 0.6rem;
  padding: 0.85rem;
  border: 1px solid var(--color-border, rgba(148, 163, 184, 0.18));
  border-radius: 0.7rem;
  background: var(--color-surface-soft, rgba(15, 23, 42, 0.3));
}

.notif-body {
  display: grid;
  gap: 0.25rem;
}

.notif-product {
  font-size: var(--text-xs, 0.75rem);
  display: flex;
  gap: 0.4rem;
  align-items: baseline;
}

.notif-title {
  font-size: var(--text-sm, 0.875rem);
}

.notif-message {
  font-size: var(--text-xs, 0.75rem);
  margin: 0;
  line-height: 1.4;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.notif-meta {
  font-size: var(--text-xs, 0.75rem);
  margin-top: 0.1rem;
}

.notif-actions {
  display: flex;
  gap: 0.4rem;
}

/* ═══════════════════════════════════════════════
   SHARED TABLE STYLES
   ═══════════════════════════════════════════════ */
.table-wrapper {
  overflow-x: auto;
}

.data-table {
  width: 100%;
  border-collapse: collapse;
}

.data-table th,
.data-table td {
  padding: 0.7rem 0.75rem;
  text-align: left;
  border-bottom: 1px solid var(--color-border, rgba(148, 163, 184, 0.18));
  vertical-align: middle;
}

.data-table th {
  color: var(--color-text-muted, #94a3b8);
  font-size: var(--text-xs, 0.75rem);
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  white-space: nowrap;
}

.data-table tbody tr:last-child td {
  border-bottom: 0;
}

.data-table tbody tr:hover {
  background: rgba(148, 163, 184, 0.04);
}

.product-cell {
  display: grid;
  gap: 0.15rem;
}

.action-row {
  display: flex;
  gap: 0.4rem;
  flex-wrap: nowrap;
}

/* ═══════════════════════════════════════════════
   BADGES
   ═══════════════════════════════════════════════ */
.badge {
  display: inline-flex;
  align-items: center;
  border-radius: 999px;
  padding: 0.2rem 0.55rem;
  font-size: var(--text-xs, 0.75rem);
  font-weight: 600;
  width: fit-content;
  white-space: nowrap;
}

.badge-neutral {
  background: rgba(148, 163, 184, 0.15);
  color: #cbd5e1;
}

.badge-success {
  background: rgba(52, 211, 153, 0.15);
  color: #86efac;
}

.badge-warning {
  background: rgba(251, 191, 36, 0.15);
  color: #fde68a;
}

.badge-danger {
  background: rgba(251, 113, 133, 0.15);
  color: #fda4af;
}

/* ═══════════════════════════════════════════════
   TEXT UTILITIES
   ═══════════════════════════════════════════════ */
.text-success { color: #86efac; }
.text-warning { color: #fde68a; }
.text-danger  { color: #fda4af; }
.fw-600       { font-weight: 600; }

/* ═══════════════════════════════════════════════
   CVE chips in security updates table
   ═══════════════════════════════════════════════ */
.cve-chips {
  display: flex;
  flex-wrap: wrap;
  gap: 0.3rem;
}

.cve-chip {
  display: inline-block;
  font-size: var(--text-xs, 0.75rem);
  font-family: var(--font-mono, monospace);
  padding: 0.15rem 0.45rem;
  border-radius: 0.4rem;
  background: rgba(148, 163, 184, 0.12);
  color: var(--color-text-muted, #94a3b8);
}

.cve-chip-highlight {
  background: rgba(251, 191, 36, 0.18);
  color: #fde68a;
  font-weight: 700;
}

/* ═══════════════════════════════════════════════
   FORM CONTROLS
   ═══════════════════════════════════════════════ */
.field {
  display: grid;
  gap: 0.4rem;
}

.field-label {
  font-size: var(--text-xs, 0.75rem);
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: var(--color-text-muted, #94a3b8);
}

.input,
.select {
  width: 100%;
  box-sizing: border-box;
  min-height: 2.5rem;
  border-radius: 0.75rem;
  border: 1px solid var(--color-border, rgba(148, 163, 184, 0.2));
  background: var(--color-surface-soft, rgba(15, 23, 42, 0.45));
  color: inherit;
  padding: 0.65rem 0.9rem;
  font: inherit;
  font-size: var(--text-sm, 0.875rem);
}

.input-mono {
  font-family: var(--font-mono, monospace);
  font-size: var(--text-sm, 0.875rem);
}

/* ═══════════════════════════════════════════════
   FEEDBACK & EMPTY STATE
   ═══════════════════════════════════════════════ */
.feedback,
.empty-panel {
  padding: 0.85rem 1rem;
  border-radius: var(--radius-md, 0.85rem);
  font-size: var(--text-sm, 0.875rem);
}

.empty-panel {
  background: var(--color-surface-soft, rgba(15, 23, 42, 0.35));
}

.feedback-error {
  background: rgba(251, 113, 133, 0.08);
  border: 1px solid rgba(251, 113, 133, 0.2);
  color: #fda4af;
}

/* ═══════════════════════════════════════════════
   MARKET ACTIONS FORM
   ═══════════════════════════════════════════════ */
.ma-form-panel {
  display: grid;
  gap: 1rem;
  padding: 1.1rem;
  border: 1px solid var(--color-border, rgba(148, 163, 184, 0.18));
  border-radius: var(--radius-md, 0.85rem);
  background: var(--color-surface-soft, rgba(15, 23, 42, 0.45));
}

.ma-form-title {
  margin: 0;
  font-size: var(--text-base, 1rem);
  font-weight: 600;
}

.form-grid {
  display: grid;
  gap: 0.85rem;
}

.textarea {
  resize: vertical;
  min-height: 4rem;
  font-family: inherit;
  line-height: 1.5;
}

.form-actions {
  display: flex;
  gap: 0.5rem;
}

.required {
  color: #fda4af;
}

/* ═══════════════════════════════════════════════
   RESPONSIVE BREAKPOINTS
   ═══════════════════════════════════════════════ */
@media (max-width: 1400px) {
  .kpi-strip {
    grid-template-columns: repeat(3, minmax(0, 1fr));
  }
}

@media (max-width: 1100px) {
  .hub-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 900px) {
  .kpi-strip {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 700px) {
  .kpi-strip {
    grid-template-columns: 1fr;
  }

  .panel-header {
    flex-direction: column;
  }
}
</style>

<!-- Light-theme overrides (non-scoped so :root selector works) -->
<style>
:root[data-theme="light"] .kpi-card              { background: #ffffff; }
:root[data-theme="light"] .lookup-dropdown       { background: #ffffff; }
:root[data-theme="light"] .disclosure-text       { background: rgba(241, 245, 249, 0.8); }
:root[data-theme="light"] .lookup-result         { background: rgba(241, 245, 249, 0.6); }
:root[data-theme="light"] .notif-item            { background: rgba(241, 245, 249, 0.5); }
:root[data-theme="light"] .ma-form-panel         { background: rgba(241, 245, 249, 0.6); }
:root[data-theme="light"] .eos-mark              { background: rgba(71, 85, 105, 0.08); border-color: rgba(71, 85, 105, 0.15); }
:root[data-theme="light"] .select-sm             { background: #ffffff; }
:root[data-theme="light"] .badge-neutral  { background: rgba(71, 85, 105, 0.1);  color: #475569; }
:root[data-theme="light"] .badge-success  { background: rgba(21, 128, 61, 0.1);  color: #15803d; }
:root[data-theme="light"] .badge-warning  { background: rgba(184, 155, 18, 0.1); color: #78350f; }
:root[data-theme="light"] .badge-danger   { background: rgba(239, 68, 68, 0.1);  color: #be123c; }
:root[data-theme="light"] .text-success   { color: #15803d; }
:root[data-theme="light"] .text-warning   { color: #78350f; }
:root[data-theme="light"] .text-danger    { color: #be123c; }
:root[data-theme="light"] .feedback-error { background: rgba(239, 68, 68, 0.06); border-color: rgba(239, 68, 68, 0.2); color: #be123c; }
:root[data-theme="light"] .cve-chip       { background: rgba(71, 85, 105, 0.1); color: #475569; }
:root[data-theme="light"] .cve-chip-highlight { background: rgba(184, 155, 18, 0.15); color: #78350f; }
:root[data-theme="light"] .required       { color: #be123c; }
:root[data-theme="light"] .all-clear-icon { background: rgba(21, 128, 61, 0.1); color: #15803d; }
:root[data-theme="light"] .kpi-value--warn   { color: #78350f; }
:root[data-theme="light"] .kpi-value--danger { color: #be123c; }
:root[data-theme="light"] .eos-days--over .eos-days-label { color: #be123c; }
:root[data-theme="light"] .eos-days--warn .eos-days-label { color: #78350f; }
:root[data-theme="light"] .eos-days--ok .eos-days-label   { color: #15803d; }
:root[data-theme="light"] .eos-days--over .eos-bar-fill { background: #f87171; }
:root[data-theme="light"] .eos-days--warn .eos-bar-fill { background: #f59e0b; }
:root[data-theme="light"] .eos-days--ok   .eos-bar-fill { background: #22c55e; }
:root[data-theme="light"] .eos-row--expired td:first-child { box-shadow: inset 3px 0 0 rgba(239, 68, 68, 0.5); }
</style>
