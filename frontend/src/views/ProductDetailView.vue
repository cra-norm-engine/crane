<template>
  <!--
    ProductDetailView — minimalist product workspace.

    Layout:
      • Page header   — product name + refresh
      • Stats bar     — 5 key metrics in compact cards
      • Workspace     — 2-column grid
          Main column : product info (read-only), releases (slim rows),
                        remote processing elements, child products
          Side column : support period summary, scope wizard, audit timeline
      • Three AppModals rendered via Teleport:
          – Edit product
          – Support period (create / update)
          – New release
      • Scope wizard modal (bespoke, kept as-is)
  -->
  <section class="page">

    <!-- ── Page header ─────────────────────────────────── -->
    <header class="page-header card">
      <div>
        <h1 class="page-title">{{ product?.name || "Product Detail" }}</h1>
        <p class="muted page-subtitle">
          CRA compliance workspace — scope, releases, and support lifecycle.
        </p>
      </div>

      <!-- Refresh is the only top-level action; editing lives inside each card -->
      <div class="page-actions">
        <button
          class="btn btn-secondary"
          type="button"
          :disabled="isLoading || isSaving || isSavingSupportPeriod"
          @click="loadProduct"
        >
          {{ isLoading ? "Refreshing…" : "Refresh" }}
        </button>
      </div>
    </header>

    <!-- ── Page-level feedback banners ─────────────────── -->
    <div v-if="errorMessage" class="feedback-banner feedback-banner-danger" role="alert">
      {{ errorMessage }}
    </div>

    <div v-if="successMessage" class="feedback-banner feedback-banner-success" role="status">
      {{ successMessage }}
    </div>

    <div v-if="supportPeriodSuccess" class="feedback-banner feedback-banner-success" role="status">
      {{ supportPeriodSuccess }}
    </div>

    <!-- ── Loading state ───────────────────────────────── -->
    <div v-if="isLoading && !product" class="card loading-card">
      <span class="spinner spinner-sm" aria-hidden="true" />
      Loading product…
    </div>

    <template v-else-if="product">

      <!-- ── Stats bar ───────────────────────────────────── -->
      <!--
        Five at-a-glance facts. Wide enough to stay in one row on
        ≥1280px; collapses to 3 then 2 columns on smaller viewports.
      -->
      <div class="stats-grid">
        <article class="card stat-card">
          <span class="stat-label">Product code</span>
          <strong class="stat-value stat-value-code">{{ product.product_code }}</strong>
        </article>

        <article class="card stat-card">
          <span class="stat-label">Classification</span>
          <strong class="stat-value">
            <span class="badge" :class="classificationClass(product.current_classification)">
              {{ formatClassification(product.current_classification) }}
            </span>
          </strong>
        </article>

        <article class="card stat-card">
          <span class="stat-label">Scope</span>
          <strong class="stat-value">
            <span class="badge" :class="scopeClass(product.scope_status)">
              {{ formatScopeStatus(product.scope_status) }}
            </span>
          </strong>
        </article>

        <article class="card stat-card">
          <span class="stat-label">Releases</span>
          <strong class="stat-value">{{ product.releases.length }}</strong>
        </article>

        <article class="card stat-card">
          <span class="stat-label">Support end</span>
          <strong class="stat-value stat-value-date">
            {{ activeSupportPeriod ? formatDate(activeSupportPeriod.support_end_date) : "—" }}
          </strong>
        </article>
      </div>

      <!-- ── Two-column workspace ──────────────────────── -->
      <div class="workspace">

        <!-- ╔══════════════════════════════════════════════╗
             ║  Main column                                 ║
             ╚══════════════════════════════════════════════╝ -->
        <main class="main-column">

          <!-- Product information — read-only; edit opens AppModal -->
          <section class="card">
            <div class="section-header">
              <div>
                <h2 class="section-title">Product information</h2>
                <p class="muted section-sub">Core identity and lifecycle metadata.</p>
              </div>
              <!-- Edit button opens the product edit modal -->
              <button class="btn btn-secondary btn-compact" type="button" @click="startEditing">
                Edit
              </button>
            </div>

            <!--
              Read-only field list.
              Layout: two parallel columns of label→value rows.
              Short metadata fields are paired side-by-side;
              longer prose fields (description, intended use) run full-width.
            -->
            <div class="info-grid">

              <!-- ── Short metadata — 2-column pairing ── -->
              <div class="info-item">
                <span class="detail-label">Manufacturer</span>
                <span class="info-value">{{ product.manufacturer_name }}</span>
              </div>

              <div class="info-item">
                <span class="detail-label">Type</span>
                <span class="info-value">{{ product.product_type }}</span>
              </div>

              <div class="info-item">
                <span class="detail-label">Parent product</span>
                <span class="info-value">{{ product.parent_product_id || "None" }}</span>
              </div>

              <div class="info-item">
                <span class="detail-label">Last updated</span>
                <span class="info-value">{{ formatDateTime(product.updated_at) }}</span>
              </div>

              <!-- Gap 4 — Art. 69(2) pre-CRA status -->
              <div class="info-item">
                <span class="detail-label">Pre-CRA</span>
                <span class="badge" :class="product.is_pre_cra ? 'badge-warning' : 'badge-neutral'">
                  {{ product.is_pre_cra ? "Yes — Art. 69(2)" : "No" }}
                </span>
              </div>

              <div class="info-item">
                <span class="detail-label">First placed</span>
                <span class="info-value">{{ formatDate(product.first_placed_on_market_date) }}</span>
              </div>

              <!-- ── Prose fields — full width ── -->
              <div class="info-item info-item-span-2">
                <span class="detail-label">Description</span>
                <span class="info-value">{{ product.description || "No description provided." }}</span>
              </div>

              <div class="info-item info-item-span-2">
                <span class="detail-label">Intended use</span>
                <span class="info-value">{{ product.intended_use }}</span>
              </div>

            </div>
          </section>

          <!-- Releases — compact single-row list; new release opens AppModal -->
          <section class="card">
            <div class="section-header">
              <div>
                <h2 class="section-title">Releases</h2>
                <p class="muted section-sub">
                  {{ product.releases.length }} release(s) · each has its own evidence workspace.
                </p>
              </div>
              <button
                class="btn btn-primary btn-compact"
                type="button"
                :disabled="isCreatingRelease"
                @click="openReleaseModal"
              >
                New release
              </button>
            </div>

            <!-- Empty state -->
            <p v-if="product.releases.length === 0" class="muted empty-inline">
              No releases yet. Create the first release to start the workflow.
            </p>

            <!-- Compact release list — one row per release, entire row is a link -->
            <div v-else class="release-list" role="list">
              <RouterLink
                v-for="release in product.releases"
                :key="release.id"
                class="release-row"
                role="listitem"
                :to="{ name: 'release-gate', params: { releaseId: release.id } }"
              >
                <!-- Version label + CRA lineage micro-tags -->
                <div class="release-row-left">
                  <span class="release-display_version">v{{ release.display_version }}</span>
                  <!-- Gap 5 — Art. 13(10) consolidated support designation tag -->
                  <span v-if="release.is_consolidated_support_version" class="release-tag release-tag-amber">
                    Art. 13(10)
                  </span>
                  <!-- Gap 2 — non-substantial update lineage tag -->
                  <span v-if="release.parent_release_id" class="release-tag release-tag-blue">
                    Non-substantial
                  </span>
                </div>

                <!-- Status badge -->
                <span class="badge badge-neutral release-status-badge">
                  {{ formatReleaseStatus(release.release_status) }}
                </span>

                <!-- Conformity route — secondary meta -->
                <span class="release-row-meta">
                  {{ formatConformityRoute(release.conformity_route_snapshot) }}
                </span>

                <!-- Planned date -->
                <span class="release-row-date">
                  {{ formatDate(release.planned_release_date) }}
                </span>

                <!-- Chevron hint — indicates the row is a link -->
                <svg
                  class="release-row-arrow"
                  viewBox="0 0 16 16"
                  fill="none"
                  stroke="currentColor"
                  stroke-width="2"
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  aria-hidden="true"
                >
                  <polyline points="6 3 11 8 6 13" />
                </svg>
              </RouterLink>
            </div>
          </section>

          <!-- Remote processing elements — table unchanged -->
          <section class="card">
            <div class="section-header">
              <div>
                <h2 class="section-title">Remote processing elements</h2>
                <p class="muted section-sub">{{ product.remote_processing_elements.length }} element(s)</p>
              </div>
            </div>

            <p v-if="product.remote_processing_elements.length === 0" class="muted empty-inline">
              No remote processing elements recorded.
            </p>

            <div v-else class="table-wrapper">
              <table class="data-table">
                <thead>
                  <tr>
                    <th>Name</th>
                    <th>Provider</th>
                    <th>Location</th>
                    <th>Criticality</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="element in product.remote_processing_elements" :key="element.id">
                    <td><strong>{{ element.name }}</strong></td>
                    <td>{{ element.provider_name || "—" }}</td>
                    <td>{{ element.geographic_location || "—" }}</td>
                    <td>{{ element.criticality || "—" }}</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </section>

          <!-- Child products — table unchanged -->
          <section class="card">
            <div class="section-header">
              <div>
                <h2 class="section-title">Child products</h2>
                <p class="muted section-sub">{{ product.child_products.length }} child product(s)</p>
              </div>
            </div>

            <p v-if="product.child_products.length === 0" class="muted empty-inline">
              No child products linked.
            </p>

            <div v-else class="table-wrapper">
              <table class="data-table">
                <thead>
                  <tr>
                    <th>Name</th>
                    <th>Code</th>
                    <th>Classification</th>
                    <th>Scope</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="child in product.child_products" :key="child.id">
                    <td>{{ child.name }}</td>
                    <td><code>{{ child.product_code }}</code></td>
                    <td>
                      <span class="badge" :class="classificationClass(child.current_classification)">
                        {{ formatClassification(child.current_classification) }}
                      </span>
                    </td>
                    <td>
                      <span class="badge" :class="scopeClass(child.scope_status)">
                        {{ formatScopeStatus(child.scope_status) }}
                      </span>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </section>

        </main>

        <!-- ╔══════════════════════════════════════════════╗
             ║  Side column — support, wizard, audit        ║
             ╚══════════════════════════════════════════════╝ -->
        <aside class="side-column">

          <!-- Support period summary — full form opens in AppModal -->
          <section class="card">
            <div class="section-header">
              <div>
                <h2 class="section-title">Support period</h2>
                <!-- Show number of historical versions recorded -->
                <p class="muted section-sub">{{ supportHistoryCount }} display_version(s) on record.</p>
              </div>
              <!-- Label adapts: "Set up" if none exists, "Edit" if one is active -->
              <button
                class="btn btn-primary btn-compact"
                type="button"
                @click="showSupportModal = true"
              >
                {{ activeSupportPeriod ? "Edit" : "Set up" }}
              </button>
            </div>

            <!-- Summary rows — shown when an active support period is loaded -->
            <div v-if="activeSupportPeriod" class="support-summary">
              <div class="summary-row">
                <span class="detail-label">Period</span>
                <span>
                  {{ formatDate(activeSupportPeriod.support_start_date) }}
                  →
                  {{ formatDate(activeSupportPeriod.support_end_date) }}
                </span>
              </div>

              <div class="summary-row">
                <span class="detail-label">Type</span>
                <span class="badge badge-neutral">{{ activeSupportPeriod.support_type }}</span>
              </div>

              <div class="summary-row">
                <span class="detail-label">EOS alert</span>
                <span>{{ activeSupportPeriod.notify_before_days }} days before end</span>
              </div>

              <!-- Show recipient count if any are set -->
              <div v-if="activeSupportPeriod.recipient_user_ids.length > 0" class="summary-row">
                <span class="detail-label">Recipients</span>
                <span>{{ activeSupportPeriod.recipient_user_ids.length }} user(s)</span>
              </div>
            </div>

            <!-- Placeholder when no support period exists yet -->
            <p v-else class="muted empty-inline">
              No support period recorded yet.
            </p>

            <!-- Inline error from support period operations -->
            <div v-if="supportPeriodError" class="feedback-banner feedback-banner-danger" role="alert">
              {{ supportPeriodError }}
            </div>
          </section>

          <!-- CRA scope wizard trigger card -->
          <section class="card wizard-trigger-card">
            <div class="wizard-trigger-body">
              <div class="wizard-trigger-icon" aria-hidden="true">
                <svg xmlns="http://www.w3.org/2000/svg" width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
                  <circle cx="11" cy="11" r="8"/>
                  <line x1="21" y1="21" x2="16.65" y2="16.65"/>
                  <line x1="11" y1="8" x2="11" y2="14"/>
                  <line x1="8" y1="11" x2="14" y2="11"/>
                </svg>
              </div>
              <div>
                <h2 class="section-title wizard-trigger-title">CRA scope wizard</h2>
                <p class="muted wizard-trigger-copy">Evaluate scope and get a recommended classification.</p>
              </div>
            </div>

            <!-- Last evaluation result pill (if available) -->
            <div v-if="scopeResult" class="wizard-last-result">
              <span class="detail-label">Last result</span>
              <div class="wizard-last-result-badges">
                <span class="badge" :class="scopeResult.in_scope ? 'badge-success' : 'badge-danger'">
                  {{ scopeResult.in_scope ? "In scope" : "Out of scope" }}
                </span>
                <span class="badge" :class="classificationClass(scopeResult.recommended_classification)">
                  {{ formatClassification(scopeResult.recommended_classification) }}
                </span>
              </div>
            </div>

            <button class="btn btn-primary wizard-open-btn" type="button" @click="showWizardModal = true">
              Open scope wizard
            </button>
          </section>

          <!-- Audit timeline — only visible when the user has audit_read permission -->
          <AuditTimeline
            v-if="canViewAudit"
            title="Product timeline"
            eyebrow="Traceability"
            description="High-value actions for this product — releases, evidence, support, and admin changes."
            :events="auditEvents"
            :loading="isAuditLoading"
            :error-message="auditErrorMessage"
            :show-refresh="true"
            :compact="true"
            @refresh="loadAuditEvents"
          />

        </aside>
      </div>

      <!-- ════════════════════════════════════════════════════
           MODAL — Edit product
           Opens when the user clicks "Edit" in the product
           information card.  All fields are pre-filled via
           syncEditForm() before the modal opens.
           ════════════════════════════════════════════════════ -->
      <AppModal v-model="showEditModal" title="Edit product" size="lg">
        <!-- Error inside the modal so the user sees it in context -->
        <div v-if="errorMessage" class="feedback-banner feedback-banner-danger" role="alert">
          {{ errorMessage }}
        </div>

        <form class="modal-edit-grid" @submit.prevent="saveProduct">
          <label class="field">
            <span class="field-label">Name</span>
            <input v-model.trim="editForm.name" type="text" maxlength="255" />
          </label>

          <label class="field">
            <span class="field-label">Product code</span>
            <input v-model.trim="editForm.product_code" type="text" maxlength="100" />
          </label>

          <label class="field">
            <span class="field-label">Manufacturer</span>
            <input v-model.trim="editForm.manufacturer_name" type="text" maxlength="255" />
          </label>

          <label class="field">
            <span class="field-label">Type</span>
            <input v-model.trim="editForm.product_type" type="text" maxlength="100" />
          </label>

          <label class="field modal-field-span-2">
            <span class="field-label">Description</span>
            <textarea v-model.trim="editForm.description" rows="3" />
          </label>

          <label class="field modal-field-span-2">
            <span class="field-label">Intended use</span>
            <textarea v-model.trim="editForm.intended_use" rows="3" />
          </label>

          <label class="field">
            <span class="field-label">Parent product ID</span>
            <input v-model.trim="editForm.parent_product_id" type="text" maxlength="36" placeholder="Optional" />
          </label>

          <label class="field">
            <span class="field-label">Current classification</span>
            <select v-model="editForm.current_classification">
              <option value="normal">Normal</option>
              <option value="important_class_1">Important Class I</option>
              <option value="important_class_2">Important Class II</option>
              <option value="critical">Critical</option>
            </select>
          </label>

          <label class="field">
            <span class="field-label">Scope status</span>
            <select v-model="editForm.scope_status">
              <option value="undecided">Undecided</option>
              <option value="in_scope">In scope</option>
              <option value="out_of_scope">Out of scope</option>
            </select>
          </label>

          <!-- Gap 4 — Article 69(2): flag products already on market before CRA -->
          <label class="field">
            <span class="field-label">Pre-CRA product (Art. 69(2))</span>
            <select v-model="editForm.is_pre_cra">
              <option :value="false">No — first placed after CRA applicability</option>
              <option :value="true">Yes — already on market before CRA</option>
            </select>
          </label>

          <!-- Gap 4 — Earliest known EU market placement date -->
          <label class="field">
            <span class="field-label">First placed on market</span>
            <input v-model="editForm.first_placed_on_market_date" type="date" />
          </label>
        </form>

        <!-- Footer slot — Cancel and Save actions -->
        <template #footer>
          <button class="btn btn-secondary" type="button" :disabled="isSaving" @click="cancelEditing">
            Cancel
          </button>
          <button class="btn btn-primary" type="button" :disabled="isSaving" @click="saveProduct">
            {{ isSaving ? "Saving…" : "Save changes" }}
          </button>
        </template>
      </AppModal>

      <!-- ════════════════════════════════════════════════════
           MODAL — Support period
           Opens when the user clicks "Set up" or "Edit" in
           the support period summary card.  Fields are
           pre-filled via syncSupportForm().
           ════════════════════════════════════════════════════ -->
      <AppModal
        v-model="showSupportModal"
        :title="activeSupportPeriod ? 'Edit support period' : 'Create support period'"
        size="lg"
        :persistent="isSavingSupportPeriod"
      >
        <!-- Inline error within the modal -->
        <div v-if="supportPeriodError" class="feedback-banner feedback-banner-danger" role="alert">
          {{ supportPeriodError }}
        </div>

        <form class="modal-edit-grid" @submit.prevent="saveSupportPeriod">
          <!-- Gap 1 — Link this support period to a specific release (CRA §117) -->
          <label class="field modal-field-span-2">
            <span class="field-label">
              Applies to release
              <span class="field-label-hint">(optional — leave blank for product-level record)</span>
            </span>
            <select v-model="supportForm.product_release_id">
              <option value="">Product-level (no specific release)</option>
              <option
                v-for="rel in product?.releases ?? []"
                :key="rel.id"
                :value="rel.id"
              >
                v{{ rel.display_version }}
                <template v-if="rel.placed_on_market_date"> · placed {{ formatDate(rel.placed_on_market_date) }}</template>
                <template v-else> · not yet placed</template>
              </option>
            </select>
          </label>

          <!-- Core scheduling fields -->
          <label class="field">
            <span class="field-label">Support start date</span>
            <input v-model="supportForm.support_start_date" type="date" />
          </label>

          <label class="field">
            <span class="field-label">Support end date</span>
            <input v-model="supportForm.support_end_date" type="date" />
          </label>

          <label class="field">
            <span class="field-label">Support type</span>
            <select v-model="supportForm.support_type">
              <option value="standard">Standard</option>
              <option value="limited">Limited</option>
              <option value="extended">Extended</option>
              <option value="custom">Custom</option>
            </select>
          </label>

          <label class="field">
            <span class="field-label">Notify before EOS (days)</span>
            <input v-model.number="supportForm.notify_before_days" type="number" min="1" max="3650" step="1" />
          </label>

          <!-- Alert preview — read-only computed value -->
          <div class="support-preview modal-field-span-2">
            <span class="detail-label">Alert fires on</span>
            <span class="muted">{{ notificationSchedulePreview }}</span>
          </div>

          <!-- Notification recipients dropdown -->
          <div class="field modal-field-span-2 recipient-dropdown-field">
            <span class="field-label">Notification recipients</span>
            <div v-if="notificationRecipientOptions.length === 0" class="muted">
              No active users available.
            </div>
            <div v-else ref="recipientDropdownRef" class="recipient-dropdown">
              <button
                class="recipient-trigger"
                type="button"
                :aria-expanded="isRecipientDropdownOpen ? 'true' : 'false'"
                @click="toggleRecipientDropdown"
              >
                <span class="recipient-trigger-copy">
                  <strong>{{ selectedRecipientsSummary }}</strong>
                  <small class="muted">Choose users to receive end-of-support alerts.</small>
                </span>
                <span class="recipient-trigger-icon">{{ isRecipientDropdownOpen ? "▲" : "▼" }}</span>
              </button>

              <div v-if="isRecipientDropdownOpen" class="recipient-menu">
                <label
                  v-for="option in notificationRecipientOptions"
                  :key="option.id"
                  class="recipient-option"
                >
                  <input
                    class="recipient-checkbox"
                    type="checkbox"
                    :checked="supportForm.recipient_user_ids.includes(option.id)"
                    @change="toggleRecipient(option.id)"
                  />
                  <span class="recipient-copy">
                    <strong class="recipient-name">{{ option.full_name }}</strong>
                    <small class="recipient-meta">{{ option.email }}</small>
                    <small class="recipient-meta">{{ option.roles.join(", ") }}</small>
                  </span>
                </label>
              </div>
            </div>
          </div>

          <!-- Documentation fields toggle -->
          <div class="modal-field-span-2">
            <button
              class="toggle-section-btn"
              type="button"
              @click="showDocFields = !showDocFields"
            >
              <svg
                xmlns="http://www.w3.org/2000/svg"
                width="14"
                height="14"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                stroke-width="2.5"
                stroke-linecap="round"
                stroke-linejoin="round"
                :style="{ transform: showDocFields ? 'rotate(90deg)' : 'rotate(0deg)', transition: 'transform 180ms ease' }"
              >
                <polyline points="9 18 15 12 9 6" />
              </svg>
              {{ showDocFields ? "Hide documentation fields" : "Show documentation fields" }}
            </button>
          </div>

          <!-- Collapsible documentation fields -->
          <template v-if="showDocFields">
            <label class="field modal-field-span-2">
              <span class="field-label">Justification text</span>
              <textarea v-model.trim="supportForm.justification_text" rows="3" />
            </label>

            <label class="field">
              <span class="field-label">Expected use time</span>
              <textarea v-model.trim="supportForm.expected_use_time_text" rows="3" />
            </label>

            <label class="field">
              <span class="field-label">Comparable products</span>
              <textarea v-model.trim="supportForm.comparable_products_text" rows="3" />
            </label>

            <label class="field modal-field-span-2">
              <span class="field-label">Third-party support constraints</span>
              <textarea v-model.trim="supportForm.third_party_support_constraints_text" rows="3" />
            </label>

            <label class="field modal-field-span-2">
              <span class="field-label">User-facing summary</span>
              <textarea v-model.trim="supportForm.user_facing_summary" rows="3" />
            </label>

            <label class="field modal-field-span-2">
              <span class="field-label">Packaging summary</span>
              <textarea v-model.trim="supportForm.packaging_summary" rows="3" />
            </label>
          </template>
        </form>

        <!-- Footer slot — snippet generator + save action -->
        <template #footer>
          <button
            class="btn btn-secondary"
            type="button"
            :disabled="isSavingSupportPeriod"
            @click="generateSupportSnippets"
          >
            Generate snippets
          </button>
          <button
            class="btn btn-primary"
            type="button"
            :disabled="isSavingSupportPeriod"
            @click="saveSupportPeriod"
          >
            {{ isSavingSupportPeriod
              ? "Saving…"
              : activeSupportPeriod
                ? "Save new display_version"
                : "Create support period" }}
          </button>
        </template>
      </AppModal>

      <!-- ════════════════════════════════════════════════════
           MODAL — New release
           Opens when the user clicks "New release".
           Substantial changes are loaded before the modal
           opens so the causal link picker is populated.
           ════════════════════════════════════════════════════ -->
      <AppModal
        v-model="showReleaseModal"
        title="New release"
        size="lg"
        :persistent="isCreatingRelease"
      >
        <!-- Error inside the modal -->
        <div v-if="errorMessage" class="feedback-banner feedback-banner-danger" role="alert">
          {{ errorMessage }}
        </div>

        <form class="modal-edit-grid" @submit.prevent="createRelease">
          <label class="field">
            <span class="field-label">Version</span>
            <input
              v-model.trim="releaseForm.display_version"
              type="text"
              maxlength="100"
              required
              placeholder="1.0.0"
            />
          </label>

          <label class="field">
            <span class="field-label">Planned release date</span>
            <input v-model="releaseForm.planned_release_date" type="date" />
          </label>

          <label class="field">
            <span class="field-label">Classification snapshot</span>
            <select v-model="releaseForm.classification_snapshot">
              <option value="normal">Normal</option>
              <option value="important_class_1">Important Class I</option>
              <option value="important_class_2">Important Class II</option>
              <option value="critical">Critical</option>
            </select>
          </label>

          <label class="field">
            <span class="field-label">Conformity route</span>
            <select v-model="releaseForm.conformity_route_snapshot">
              <option value="undecided">Undecided</option>
              <option value="self_assessment">Self assessment</option>
              <option value="third_party_assessment">Third-party assessment</option>
              <option value="not_applicable">Not applicable</option>
            </select>
          </label>

          <label class="field modal-field-span-2">
            <span class="field-label">Release notes</span>
            <textarea v-model.trim="releaseForm.release_notes" rows="3" placeholder="Optional release notes" />
          </label>

          <!-- Gap 3 — Formal EU placement date (CRA Art. 3(20)) -->
          <label class="field">
            <span class="field-label">
              Placed on market date
              <span class="field-label-hint">(optional — set when EU placement occurs)</span>
            </span>
            <input v-model="releaseForm.placed_on_market_date" type="date" />
          </label>

          <!-- CRA Art. 28 — EU Declaration of Conformity metadata -->
          <label class="field">
            <span class="field-label">
              EU DoC draw-up date
              <span class="field-label-hint">(Art. 28 — must be on or before placement date)</span>
            </span>
            <input v-model="releaseForm.eu_doc_date" type="date" />
          </label>

          <label class="field">
            <span class="field-label">
              EU DoC reference number
              <span class="field-label-hint">(optional — Annex V unique identifier)</span>
            </span>
            <input v-model.trim="releaseForm.eu_doc_number" type="text" placeholder="e.g. DOC-2027-001" />
          </label>

          <label class="field">
            <span class="field-label">
              Notified body
              <span class="field-label-hint">(optional — required for third-party conformity route only)</span>
            </span>
            <input v-model.trim="releaseForm.eu_doc_notified_body" type="text" placeholder="e.g. TÜV SÜD — NB 0123" />
          </label>

          <!-- Gap 2 — Non-substantial update lineage (CRA guidance §15) -->
          <label class="field">
            <span class="field-label">
              Non-substantial update of
              <span class="field-label-hint">(optional — inherits that release's placement date)</span>
            </span>
            <select v-model="releaseForm.parent_release_id">
              <option value="">Not a non-substantial update</option>
              <option
                v-for="rel in product?.releases ?? []"
                :key="rel.id"
                :value="rel.id"
              >
                v{{ rel.display_version }}
                <template v-if="rel.placed_on_market_date"> · placed {{ formatDate(rel.placed_on_market_date) }}</template>
              </option>
            </select>
          </label>


          <!-- Art. 13(7) — link the substantiality analysis for this release (required for v2+) -->
          <div class="field modal-field-span-2">
            <span class="field-label">
              Substantiality analysis
              <span class="field-label-hint">(required for v2+ releases — select the assessed change that documents whether this is a substantial modification)</span>
            </span>
            <select v-model="releaseForm.substantiality_analysis_id">
              <option value="">Not linked</option>
              <option
                v-for="c in assessedChanges"
                :key="c.id"
                :value="c.assessment_id"
              >
                {{ c.title }} · {{ formatDate(c.change_date) }}
                <template v-if="c.is_substantial"> — Substantial</template>
                <template v-else-if="c.is_substantial === false"> — Not substantial</template>
              </option>
            </select>
            <p v-if="assessedChanges.length === 0" class="field-hint muted">
              No assessed changes found for this product. Assess a change first.
            </p>
          </div>

          <!-- CRA Art. 13(8) traceability — link to the substantial change that triggered this release -->
          <div class="field modal-field-span-2">
            <span class="field-label">
              Triggered by substantial change
              <span class="field-label-hint">(optional — leave blank for planned releases)</span>
            </span>
            <select v-model="releaseForm.caused_by_change_id">
              <option value="">Not triggered by a substantial change</option>
              <!-- Each option includes title, display_version, and date for unambiguous identification -->
              <option
                v-for="c in substantialChanges"
                :key="c.id"
                :value="c.id"
              >
                {{ c.title }}
                <template v-if="c.release_version"> (v{{ c.release_version }})</template>
                · {{ formatDate(c.change_date) }}
              </option>
            </select>
            <p v-if="substantialChanges.length === 0" class="field-hint muted">
              No substantial changes found for this product.
            </p>
          </div>
        </form>

        <!-- Footer slot — reset + create actions -->
        <template #footer>
          <button
            class="btn btn-secondary"
            type="button"
            :disabled="isCreatingRelease"
            @click="resetReleaseForm"
          >
            Reset
          </button>
          <button
            class="btn btn-primary"
            type="button"
            :disabled="isCreatingRelease"
            @click="createRelease"
          >
            {{ isCreatingRelease ? "Creating…" : "Create release and open workflow" }}
          </button>
        </template>
      </AppModal>

      <!-- ════════════════════════════════════════════════════
           MODAL — CRA scope wizard
           Bespoke implementation kept as-is; uses its own
           Teleport + Transition so it sits above all content.
           ════════════════════════════════════════════════════ -->
      <Teleport to="body">
        <Transition name="modal">
          <div
            v-if="showWizardModal"
            class="wizard-modal-backdrop"
            @click.self="showWizardModal = false"
          >
            <div
              class="wizard-modal"
              role="dialog"
              aria-modal="true"
              aria-labelledby="wizard-modal-title"
            >
              <!-- Modal header -->
              <div class="wizard-modal-header">
                <div class="wizard-trigger-body">
                  <div class="wizard-trigger-icon" aria-hidden="true">
                    <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
                      <circle cx="11" cy="11" r="8"/>
                      <line x1="21" y1="21" x2="16.65" y2="16.65"/>
                      <line x1="11" y1="8" x2="11" y2="14"/>
                      <line x1="8" y1="11" x2="14" y2="11"/>
                    </svg>
                  </div>
                  <div>
                    <p class="timeline-eyebrow">Compliance</p>
                    <h2 id="wizard-modal-title" class="section-title">CRA scope wizard</h2>
                  </div>
                </div>
                <button class="icon-close-btn" type="button" title="Close" @click="showWizardModal = false">
                  <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <line x1="18" y1="6" x2="6" y2="18"/>
                    <line x1="6" y1="6" x2="18" y2="18"/>
                  </svg>
                </button>
              </div>

              <!-- Modal body — wizard form + result panel -->
              <div class="wizard-modal-body">
                <form class="wizard-grid" @submit.prevent="runScopeEvaluation">
                  <label class="check-field">
                    <input v-model="scopeForm.is_digital_product" type="checkbox" />
                    <span>Digital product</span>
                  </label>

                  <label class="check-field">
                    <input v-model="scopeForm.has_network_connectivity" type="checkbox" />
                    <span>Has network connectivity</span>
                  </label>

                  <label class="check-field">
                    <input v-model="scopeForm.performs_remote_data_processing" type="checkbox" />
                    <span>Performs remote data processing</span>
                  </label>

                  <label class="check-field">
                    <input v-model="scopeForm.safety_component" type="checkbox" />
                    <span>Safety component</span>
                  </label>

                  <label class="check-field">
                    <input v-model="scopeForm.used_in_critical_sector" type="checkbox" />
                    <span>Used in critical sector</span>
                  </label>

                  <label class="check-field">
                    <input v-model="scopeForm.handles_sensitive_functions" type="checkbox" />
                    <span>Handles sensitive functions</span>
                  </label>

                  <label class="check-field">
                    <input v-model="scopeForm.excluded_category" type="checkbox" />
                    <span>Excluded category</span>
                  </label>

                  <label class="field field-span-full">
                    <span class="field-label">Notes</span>
                    <textarea v-model.trim="scopeForm.notes" rows="3" />
                  </label>

                  <div class="form-actions field-span-full">
                    <p v-if="scopeError" class="form-error">{{ scopeError }}</p>
                    <button class="btn btn-primary" type="submit" :disabled="isEvaluatingScope">
                      {{ isEvaluatingScope ? "Evaluating…" : "Run scope evaluation" }}
                    </button>
                  </div>
                </form>

                <!-- Scope evaluation result panel -->
                <div v-if="scopeResult" class="result-panel">
                  <div class="result-row">
                    <span class="detail-label">In scope</span>
                    <span class="badge" :class="scopeResult.in_scope ? 'badge-success' : 'badge-danger'">
                      {{ scopeResult.in_scope ? "Yes" : "No" }}
                    </span>
                  </div>

                  <div class="result-row">
                    <span class="detail-label">Recommended classification</span>
                    <span class="badge" :class="classificationClass(scopeResult.recommended_classification)">
                      {{ formatClassification(scopeResult.recommended_classification) }}
                    </span>
                  </div>

                  <div class="result-row">
                    <span class="detail-label">Suggested conformity route</span>
                    <span class="badge badge-neutral">
                      {{ formatConformityRoute(scopeResult.suggested_conformity_route) }}
                    </span>
                  </div>

                  <div>
                    <span class="detail-label">Rationale</span>
                    <p class="result-rationale">{{ scopeResult.rationale }}</p>
                  </div>
                </div>
              </div>

            </div>
          </div>
        </Transition>
      </Teleport>

    </template>
  </section>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, reactive, ref, watch } from "vue";
import { useRouter } from "vue-router";

import AppModal from "@/components/AppModal.vue";
import AuditTimeline from "@/components/AuditTimeline.vue";
import { auditService } from "@/services/audit-service";
import { productService } from "@/services/product-service";
import { productReleaseService } from "@/services/product-release-service";
import { supportPeriodService } from "@/services/support-period-service";
import { changeService } from "@/services/change-service";
import type { ChangeSummary } from "@/types/change";
import { useAuthStore } from "@/stores/auth";
import type { AuditEventRead } from "@/types/audit";
import type {
  ConformityRoute,
  ProductClassification,
  ProductDetailRead,
  ProductReleaseCreate,
  ProductScopeEvaluationRead,
  ProductScopeEvaluationRequest,
  SupportPeriodNotificationRecipientOptionRead,
  ProductUpdate,
  SupportPeriodRecordRead,
  SupportType,
} from "@/types/product";

/* ── Props & composables ────────────────────────────── */
const props = defineProps<{
  productId: string;
}>();
const router    = useRouter();
const authStore = useAuthStore();

/* ── Data refs ──────────────────────────────────────── */
const product                      = ref<ProductDetailRead | null>(null);
const activeSupportPeriod          = ref<SupportPeriodRecordRead | null>(null);
const supportHistoryCount          = ref(0);
const notificationRecipientOptions = ref<SupportPeriodNotificationRecipientOptionRead[]>([]);
const recipientDropdownRef         = ref<HTMLElement | null>(null);
const isRecipientDropdownOpen      = ref(false);
const auditEvents                  = ref<AuditEventRead[]>([]);
const substantialChanges           = ref<ChangeSummary[]>([]);
// All assessed changes (any outcome) — used to populate the substantiality analysis picker
const assessedChanges              = ref<ChangeSummary[]>([]);
const scopeResult                  = ref<ProductScopeEvaluationRead | null>(null);

/* ── Loading / saving flags ─────────────────────────── */
const isLoading              = ref(false);
const isSaving               = ref(false);
const isEvaluatingScope      = ref(false);
const isSavingSupportPeriod  = ref(false);
const isCreatingRelease      = ref(false);
const isAuditLoading         = ref(false);

/* ── Modal visibility flags ─────────────────────────── */
// Three modals replace the three formerly-inline forms.
const showEditModal    = ref(false); // Edit product
const showSupportModal = ref(false); // Support period (create / update)
const showReleaseModal = ref(false); // New release
const showWizardModal  = ref(false); // CRA scope wizard (bespoke implementation)
const showDocFields    = ref(false); // Collapsible doc fields inside support modal

/* ── Message strings ────────────────────────────────── */
const errorMessage         = ref("");
const successMessage       = ref("");
const supportPeriodError   = ref("");
const supportPeriodSuccess = ref("");
const scopeError           = ref("");
const auditErrorMessage    = ref("");

/* ── Reactive form objects ──────────────────────────── */

// Scope wizard answers — reset each time the wizard is opened
const scopeForm = reactive<ProductScopeEvaluationRequest>({
  is_digital_product:            false,
  has_network_connectivity:      false,
  performs_remote_data_processing: false,
  safety_component:              false,
  used_in_critical_sector:       false,
  handles_sensitive_functions:   false,
  excluded_category:             false,
  notes:                         "",
});

// Product edit form — synced from the loaded product before modal opens
const editForm = reactive({
  name:                       "",
  product_code:               "",
  manufacturer_name:          "",
  product_type:               "",
  description:                "",
  intended_use:               "",
  parent_product_id:          "",
  current_classification:     "normal" as ProductClassification,
  scope_status:               "undecided",
  // Gap 4 — Article 69(2): pre-CRA flag and first placement date
  is_pre_cra:                      false as boolean,
  first_placed_on_market_date:     "" as string,
});

// Support period form — synced from the active record before modal opens
const supportForm = reactive({
  // Gap 1 — per-display_version support period target release; empty string = product-level
  product_release_id:                   "" as string,
  support_start_date:                   "",
  support_end_date:                     "",
  notify_before_days:                   180,
  support_type:                         "standard" as SupportType,
  recipient_user_ids:                   [] as string[],
  justification_text:                   "",
  expected_use_time_text:               "",
  comparable_products_text:             "",
  third_party_support_constraints_text: "",
  user_facing_summary:                  "",
  packaging_summary:                    "",
});

// New release form — reset before each modal open
const releaseForm = reactive({
  display_version:                        "",
  planned_release_date:           "",
  classification_snapshot:        "normal" as ProductClassification,
  conformity_route_snapshot:      "undecided" as ConformityRoute,
  release_notes:                  "",
  // Gap 3 — formal EU placement date; empty = not yet placed
  placed_on_market_date:          "" as string,
  // Gap 2 — parent release for non-substantial update lineage; empty = none
  parent_release_id:              "" as string,
  // Art. 13(7) — substantiality analysis assessment ID; required for v2+ releases
  substantiality_analysis_id:     "" as string,
  // Art. 13(10) consolidated support version flag
  is_consolidated_support_version: false as boolean,
  // CRA Art. 13(8) — link to the substantial change that triggered this release; empty = none
  caused_by_change_id:            "" as string,
  // CRA Art. 28 + Annex V — EU Declaration of Conformity metadata
  eu_doc_date:                    "" as string,
  eu_doc_number:                  "" as string,
  eu_doc_notified_body:           "" as string,
});

/* ── Computed ───────────────────────────────────────── */

// Preview the exact date the EOS notification will fire based on current form values
const notificationSchedulePreview = computed(() => {
  if (!supportForm.support_end_date) {
    return "Select a support end date to preview the alert timing.";
  }

  const endDate = new Date(`${supportForm.support_end_date}T00:00:00`);
  if (Number.isNaN(endDate.getTime())) {
    return "Enter a valid support end date.";
  }

  const previewDate = new Date(endDate);
  previewDate.setDate(previewDate.getDate() - Number(supportForm.notify_before_days || 0));

  return new Intl.DateTimeFormat(undefined, {
    year: "numeric", month: "short", day: "2-digit",
  }).format(previewDate);
});

// Gate the audit timeline behind the audit_read permission
const canViewAudit = computed(() => authStore.hasPermission("audit_read"));

// Human-readable summary of selected notification recipients for the dropdown trigger
const selectedRecipientsSummary = computed(() => {
  const count = supportForm.recipient_user_ids.length;

  if (count === 0) return "Select users";
  if (count === 1) {
    const selected = notificationRecipientOptions.value.find(
      (o: SupportPeriodNotificationRecipientOptionRead) => o.id === supportForm.recipient_user_ids[0],
    );
    return selected?.full_name ?? "1 user selected";
  }
  return `${count} users selected`;
});

/* ── Form sync helpers ──────────────────────────────── */

/** Copy loaded product values into the edit form before the modal opens. */
function syncEditForm(): void {
  if (!product.value) return;

  editForm.name                    = product.value.name ?? "";
  editForm.product_code            = product.value.product_code ?? "";
  editForm.manufacturer_name       = product.value.manufacturer_name ?? "";
  editForm.product_type            = product.value.product_type ?? "";
  editForm.description             = product.value.description ?? "";
  editForm.intended_use            = product.value.intended_use ?? "";
  editForm.parent_product_id       = product.value.parent_product_id ?? "";
  editForm.current_classification  = product.value.current_classification;
  editForm.scope_status            = product.value.scope_status;
  // Gap 4 — sync pre-CRA flag and first placement date
  editForm.is_pre_cra                  = product.value.is_pre_cra ?? false;
  editForm.first_placed_on_market_date = product.value.first_placed_on_market_date ?? "";
  // Keep release form classification in sync with the product default
  releaseForm.classification_snapshot  = product.value.current_classification;
}

/** Copy the active support period record into the support form before the modal opens. */
function syncSupportForm(): void {
  if (!activeSupportPeriod.value) {
    supportForm.product_release_id                   = "";
    supportForm.support_start_date                   = "";
    supportForm.support_end_date                     = "";
    supportForm.notify_before_days                   = 180;
    supportForm.support_type                         = "standard";
    supportForm.recipient_user_ids                   = [];
    supportForm.justification_text                   = "";
    supportForm.expected_use_time_text               = "";
    supportForm.comparable_products_text             = "";
    supportForm.third_party_support_constraints_text = "";
    supportForm.user_facing_summary                  = "";
    supportForm.packaging_summary                    = "";
    return;
  }

  // Gap 1 — restore the release-level link if the loaded record has one
  supportForm.product_release_id                   = activeSupportPeriod.value.product_release_id ?? "";
  supportForm.support_start_date                   = activeSupportPeriod.value.support_start_date ?? "";
  supportForm.support_end_date                     = activeSupportPeriod.value.support_end_date ?? "";
  supportForm.notify_before_days                   = activeSupportPeriod.value.notify_before_days ?? 180;
  supportForm.support_type                         = activeSupportPeriod.value.support_type;
  supportForm.recipient_user_ids                   = [...activeSupportPeriod.value.recipient_user_ids];
  supportForm.justification_text                   = activeSupportPeriod.value.justification_text ?? "";
  supportForm.expected_use_time_text               = activeSupportPeriod.value.expected_use_time_text ?? "";
  supportForm.comparable_products_text             = activeSupportPeriod.value.comparable_products_text ?? "";
  supportForm.third_party_support_constraints_text =
    activeSupportPeriod.value.third_party_support_constraints_text ?? "";
  supportForm.user_facing_summary  = activeSupportPeriod.value.user_facing_summary ?? "";
  supportForm.packaging_summary    = activeSupportPeriod.value.packaging_summary ?? "";
}

/* ── Modal open / close helpers ────────────────────── */

/** Open the product edit modal after syncing the form with current data. */
function startEditing(): void {
  syncEditForm();
  successMessage.value = "";
  errorMessage.value   = "";
  showEditModal.value  = true;
}

/** Close the edit modal and restore the form to the current product state. */
function cancelEditing(): void {
  syncEditForm();
  showEditModal.value = false;
}

/**
 * Open the new release modal.
 * Loads the list of substantial changes first so the causal link
 * picker is populated with up-to-date data.
 */
function openReleaseModal(): void {
  void loadSubstantialChanges();
  void loadAssessedChanges();
  showReleaseModal.value = true;
}

/** Reset all release form fields back to their defaults. */
function resetReleaseForm(): void {
  releaseForm.display_version                        = "";
  releaseForm.planned_release_date           = "";
  releaseForm.classification_snapshot        = product.value?.current_classification ?? "normal";
  releaseForm.conformity_route_snapshot      = "undecided";
  releaseForm.release_notes                  = "";
  // Gap 3 / 2 / 5 — clear CRA placement fields
  releaseForm.placed_on_market_date          = "";
  releaseForm.parent_release_id              = "";
  releaseForm.substantiality_analysis_id     = "";
  releaseForm.is_consolidated_support_version = false;
  releaseForm.caused_by_change_id            = "";
  // CRA Art. 28 — clear EU DoC fields
  releaseForm.eu_doc_date                    = "";
  releaseForm.eu_doc_number                  = "";
  releaseForm.eu_doc_notified_body           = "";
}

/* ── Recipient dropdown helpers ─────────────────────── */

function toggleRecipientDropdown(): void {
  isRecipientDropdownOpen.value = !isRecipientDropdownOpen.value;
}

function closeRecipientDropdown(): void {
  isRecipientDropdownOpen.value = false;
}

function toggleRecipient(userId: string): void {
  if (supportForm.recipient_user_ids.includes(userId)) {
    supportForm.recipient_user_ids = supportForm.recipient_user_ids.filter((id: string) => id !== userId);
    return;
  }
  supportForm.recipient_user_ids = [...supportForm.recipient_user_ids, userId];
}

/**
 * Close the recipient dropdown when the user clicks outside it.
 * Attached to window click so it works for any click location.
 */
function handleWindowClick(event: MouseEvent): void {
  if (!isRecipientDropdownOpen.value) return;

  const target = event.target;
  if (!(target instanceof Node)) return;
  if (recipientDropdownRef.value?.contains(target)) return;

  closeRecipientDropdown();
}

/* ── Formatters ────────────────────────────────────── */

function formatClassification(value: ProductClassification): string {
  switch (value) {
    case "important_class_1": return "Important Class I";
    case "important_class_2": return "Important Class II";
    case "critical":          return "Critical";
    default:                  return "Normal";
  }
}

function formatConformityRoute(value: ConformityRoute): string {
  switch (value) {
    case "self_assessment":       return "Self assessment";
    case "third_party_assessment": return "Third-party assessment";
    case "not_applicable":        return "Not applicable";
    default:                      return "Undecided";
  }
}

function formatReleaseStatus(value: string): string {
  return value.replaceAll("_", " ");
}

function formatScopeStatus(value: string): string {
  switch (value) {
    case "in_scope":     return "In scope";
    case "out_of_scope": return "Out of scope";
    default:             return "Undecided";
  }
}

function classificationClass(value: ProductClassification): string {
  switch (value) {
    case "critical":          return "badge-danger";
    case "important_class_1":
    case "important_class_2": return "badge-warning";
    default:                  return "badge-neutral";
  }
}

function scopeClass(value: string): string {
  switch (value) {
    case "in_scope":     return "badge-success";
    case "out_of_scope": return "badge-danger";
    default:             return "badge-neutral";
  }
}

function formatDate(value: string | null): string {
  if (!value) return "—";
  return new Intl.DateTimeFormat(undefined, {
    year: "numeric", month: "short", day: "2-digit",
  }).format(new Date(value));
}

function formatDateTime(value: string): string {
  return new Intl.DateTimeFormat(undefined, {
    year: "numeric", month: "short", day: "2-digit",
    hour: "2-digit", minute: "2-digit",
  }).format(new Date(value));
}

/* ── Data loaders ──────────────────────────────────── */

async function loadSupportPeriod(): Promise<void> {
  if (!props.productId) return;

  supportPeriodError.value = "";

  try {
    activeSupportPeriod.value = await supportPeriodService.getActiveForProduct(props.productId);
  } catch {
    activeSupportPeriod.value = null;
  }

  try {
    const history = await supportPeriodService.getHistoryForProduct(props.productId);
    supportHistoryCount.value = history.records.length;
  } catch {
    supportHistoryCount.value = activeSupportPeriod.value ? 1 : 0;
  }

  syncSupportForm();
}

async function loadNotificationRecipients(): Promise<void> {
  try {
    notificationRecipientOptions.value = await supportPeriodService.listNotificationRecipients();
  } catch {
    notificationRecipientOptions.value = [];
  }
}

async function loadAuditEvents(): Promise<void> {
  if (!props.productId || !canViewAudit.value) {
    auditEvents.value = [];
    return;
  }

  isAuditLoading.value    = true;
  auditErrorMessage.value = "";

  try {
    const response = await auditService.listEvents({
      product_id: props.productId,
      limit: 40,
    });
    auditEvents.value = response.items;
  } catch (error) {
    auditErrorMessage.value =
      error instanceof Error ? error.message : "Failed to load product audit history.";
  } finally {
    isAuditLoading.value = false;
  }
}

/**
 * Load all assessed substantial changes for the causal link picker.
 * No status filter is applied — a release can be linked to any substantial
 * change for CRA traceability purposes.
 */
async function loadSubstantialChanges(): Promise<void> {
  try {
    substantialChanges.value = await changeService.list({
      is_substantial: true,
      product_id: product.value?.id,
    });
  } catch {
    // Non-fatal — user can still create the release without a causal link
    substantialChanges.value = [];
  }
}

async function loadAssessedChanges(): Promise<void> {
  try {
    // Load all assessed changes (regardless of outcome) so any assessment can be
    // linked as the substantiality analysis for this release (Art. 13(7)).
    const all = await changeService.list({ product_id: product.value?.id });
    assessedChanges.value = all.filter((c) => c.assessment_id !== null);
  } catch {
    assessedChanges.value = [];
  }
}

async function loadProduct(): Promise<void> {
  isLoading.value      = true;
  errorMessage.value   = "";

  try {
    product.value = await productService.get(props.productId);
    syncEditForm();
    await Promise.all([loadSupportPeriod(), loadNotificationRecipients(), loadAuditEvents()]);
  } catch (error) {
    errorMessage.value =
      error instanceof Error ? error.message : "Failed to load product.";
  } finally {
    isLoading.value = false;
  }
}

/* ── Mutation actions ──────────────────────────────── */

async function saveProduct(): Promise<void> {
  if (!product.value) return;

  errorMessage.value   = "";
  successMessage.value = "";
  isSaving.value       = true;

  try {
    const payload: ProductUpdate = {
      name:                        editForm.name.trim(),
      product_code:                editForm.product_code.trim(),
      manufacturer_name:           editForm.manufacturer_name.trim(),
      product_type:                editForm.product_type.trim(),
      description:                 editForm.description.trim() || null,
      intended_use:                editForm.intended_use.trim(),
      parent_product_id:           editForm.parent_product_id.trim() || null,
      current_classification:      editForm.current_classification,
      scope_status:                editForm.scope_status,
      // Gap 4 — include pre-CRA flag and first placement date in every product save
      is_pre_cra:                      editForm.is_pre_cra,
      first_placed_on_market_date:     editForm.first_placed_on_market_date || null,
    };

    await productService.update(props.productId, payload);
    successMessage.value = "Product updated.";
    // Close the edit modal on success
    showEditModal.value  = false;
    await loadProduct();
  } catch (error) {
    errorMessage.value =
      error instanceof Error ? error.message : "Failed to save product.";
  } finally {
    isSaving.value = false;
  }
}

async function generateSupportSnippets(): Promise<void> {
  if (!props.productId) return;

  supportPeriodError.value   = "";
  supportPeriodSuccess.value = "";

  try {
    const snippets = await supportPeriodService.generateSnippets({
      product_id:                          props.productId,
      support_start_date:                  supportForm.support_start_date,
      support_end_date:                    supportForm.support_end_date,
      support_type:                        supportForm.support_type,
      justification_text:                  supportForm.justification_text.trim(),
      expected_use_time_text:              supportForm.expected_use_time_text.trim() || null,
      comparable_products_text:            supportForm.comparable_products_text.trim() || null,
      third_party_support_constraints_text:
        supportForm.third_party_support_constraints_text.trim() || null,
    });

    supportForm.user_facing_summary  = snippets.user_facing_summary;
    supportForm.packaging_summary    = snippets.packaging_summary;
    supportPeriodSuccess.value       = "Support snippets generated.";
    // Expand doc fields so the user can immediately see the generated text
    showDocFields.value = true;
  } catch (error) {
    supportPeriodError.value =
      error instanceof Error ? error.message : "Failed to generate support snippets.";
  }
}

async function saveSupportPeriod(): Promise<void> {
  if (!props.productId) return;

  isSavingSupportPeriod.value = true;
  supportPeriodError.value    = "";
  supportPeriodSuccess.value  = "";

  try {
    if (activeSupportPeriod.value) {
      // Update path: creates a new immutable display_version of the support record
      await supportPeriodService.update(activeSupportPeriod.value.id, {
        support_start_date:                  supportForm.support_start_date,
        support_end_date:                    supportForm.support_end_date,
        notify_before_days:                  supportForm.notify_before_days,
        support_type:                        supportForm.support_type,
        recipient_user_ids:                  supportForm.recipient_user_ids,
        justification_text:                  supportForm.justification_text.trim(),
        expected_use_time_text:              supportForm.expected_use_time_text.trim() || null,
        comparable_products_text:            supportForm.comparable_products_text.trim() || null,
        third_party_support_constraints_text:
          supportForm.third_party_support_constraints_text.trim() || null,
        user_facing_summary:  supportForm.user_facing_summary.trim() || null,
        packaging_summary:    supportForm.packaging_summary.trim() || null,
      });
      supportPeriodSuccess.value = "Support period display_version recorded.";
    } else {
      // Create path: new product-level or release-level support record
      await supportPeriodService.create({
        product_id: props.productId,
        // Gap 1 — pass the release-level FK if the user selected a specific release
        product_release_id:                  supportForm.product_release_id || null,
        support_start_date:                  supportForm.support_start_date,
        support_end_date:                    supportForm.support_end_date,
        notify_before_days:                  supportForm.notify_before_days,
        support_type:                        supportForm.support_type,
        recipient_user_ids:                  supportForm.recipient_user_ids,
        justification_text:                  supportForm.justification_text.trim(),
        expected_use_time_text:              supportForm.expected_use_time_text.trim() || null,
        comparable_products_text:            supportForm.comparable_products_text.trim() || null,
        third_party_support_constraints_text:
          supportForm.third_party_support_constraints_text.trim() || null,
        user_facing_summary:  supportForm.user_facing_summary.trim() || null,
        packaging_summary:    supportForm.packaging_summary.trim() || null,
      });
      supportPeriodSuccess.value = "Support period created.";
    }

    // Close the support period modal on success and refresh data
    showSupportModal.value = false;
    await Promise.all([loadSupportPeriod(), loadAuditEvents()]);
  } catch (error) {
    supportPeriodError.value =
      error instanceof Error ? error.message : "Failed to save support period.";
  } finally {
    isSavingSupportPeriod.value = false;
  }
}

async function runScopeEvaluation(): Promise<void> {
  scopeError.value        = "";
  isEvaluatingScope.value = true;

  try {
    scopeResult.value = await productService.evaluateScope(props.productId, {
      ...scopeForm,
      notes: scopeForm.notes?.trim() || null,
    });
    // Reload product so the scope/classification stats bar reflects the result
    await loadProduct();
  } catch (error) {
    scopeError.value =
      error instanceof Error ? error.message : "Failed to run scope evaluation.";
  } finally {
    isEvaluatingScope.value = false;
  }
}

async function createRelease(): Promise<void> {
  if (!product.value) return;

  errorMessage.value   = "";
  successMessage.value = "";
  isCreatingRelease.value = true;

  try {
    const payload: ProductReleaseCreate = {
      product_id:            product.value.id,
      user_version:          releaseForm.display_version.trim() || null,
      release_status:        "draft",
      classification_snapshot:   releaseForm.classification_snapshot,
      conformity_route_snapshot: releaseForm.conformity_route_snapshot,
      planned_release_date:  releaseForm.planned_release_date
        ? `${releaseForm.planned_release_date}T00:00:00Z`
        : null,
      actual_release_date:   null,
      // Gap 3 — formal EU placement date; null until the market placement event occurs
      placed_on_market_date: releaseForm.placed_on_market_date || null,
      release_notes:         releaseForm.release_notes.trim() || null,
      // Gap 2 — base release for non-substantial update lineage
      parent_release_id:     releaseForm.parent_release_id || null,
      // Art. 13(7) — substantiality analysis assessment link (required for v2+)
      substantiality_analysis_id: releaseForm.substantiality_analysis_id || null,
      // Art. 13(10) consolidated support version flag
      is_consolidated_support_version: releaseForm.is_consolidated_support_version,
      // Pass causal change ID only when selected; empty string means no link
      caused_by_change_id:   releaseForm.caused_by_change_id || null,
      // CRA Art. 28 — EU DoC metadata; optional at creation time
      eu_doc_date:           releaseForm.eu_doc_date || null,
      eu_doc_number:         releaseForm.eu_doc_number.trim() || null,
      eu_doc_notified_body:  releaseForm.eu_doc_notified_body.trim() || null,
    };

    const createdRelease = await productReleaseService.create(payload);
    successMessage.value = `Release ${createdRelease.display_version} created.`;
    // Close modal, reset form, then navigate straight to the new release workflow
    showReleaseModal.value = false;
    resetReleaseForm();
    await loadProduct();
    await router.push({ name: "release-gate", params: { releaseId: createdRelease.id } });
  } catch (error) {
    errorMessage.value =
      error instanceof Error ? error.message : "Failed to create release.";
  } finally {
    isCreatingRelease.value = false;
  }
}

/* ── Watchers & lifecycle ───────────────────────────── */

// Reload everything whenever the route changes to a different product
watch(
  () => props.productId,
  () => {
    // Reset transient state so stale data from the previous product is never shown
    scopeResult.value          = null;
    showEditModal.value        = false;
    showSupportModal.value     = false;
    showReleaseModal.value     = false;
    successMessage.value       = "";
    supportPeriodSuccess.value = "";
    supportPeriodError.value   = "";
    activeSupportPeriod.value  = null;
    auditEvents.value          = [];
    auditErrorMessage.value    = "";
    closeRecipientDropdown();
    supportHistoryCount.value  = 0;
    resetReleaseForm();
    void loadProduct();
  },
  { immediate: true },
);

onMounted(() => {
  // Global click handler closes the recipient dropdown when the user
  // clicks anywhere outside the dropdown widget.
  window.addEventListener("click", handleWindowClick);
});

onBeforeUnmount(() => {
  window.removeEventListener("click", handleWindowClick);
});
</script>

<style scoped>
/* ── Page layout ───────────────────────────────────── */
.page {
  display: grid;
  gap: 1rem;
}

/* Page header: product name on the left, actions on the right */
.page-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 1rem;
  flex-wrap: wrap;
}

.page-actions {
  display: flex;
  gap: 0.75rem;
  flex-wrap: wrap;
}

.page-subtitle {
  margin-top: 0.35rem;
}

/* Subtle loading card while the first page load is in flight */
.loading-card {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  color: var(--color-text-muted);
  font-size: var(--text-sm);
}

/* ── Stats bar ─────────────────────────────────────── */
/* 5 equal columns; collapses on narrow screens */
.stats-grid {
  display: grid;
  grid-template-columns: repeat(5, minmax(0, 1fr));
  gap: 1rem;
  align-items: stretch;  /* equal-height stat cards */
}

.stat-card {
  display: grid;
  gap: 0.5rem;
}

.stat-label {
  color: var(--color-text-muted);
  font-size: var(--text-xs);
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.04em;
}

.stat-value {
  font-size: 1.35rem;
  font-weight: 700;
}

/* Dates and product codes need smaller text to fit in narrow cells */
.stat-value-date,
.stat-value-code {
  font-size: 1rem;
  word-break: break-word;
}

/* ── Two-column workspace ──────────────────────────── */
.workspace {
  display: grid;
  grid-template-columns: minmax(0, 1.5fr) minmax(300px, 400px);
  gap: 1rem;
  align-items: start;
}

.main-column,
.side-column {
  display: grid;
  gap: 1rem;
}

/* Sidebar sticks to the top of the viewport as the user scrolls */
.side-column {
  position: sticky;
  top: 1rem;
}

/* ── Shared card + section-header layout ───────────── */
.card {
  display: grid;
  gap: 0.9rem;
}

/* Section header: title block on the left, action button on the right */
.section-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 1rem;
  flex-wrap: wrap;
}

.section-title {
  margin: 0;
}

.section-sub {
  margin: 0.2rem 0 0;
  font-size: var(--text-sm);
}

/* ── Typography helpers ────────────────────────────── */
.detail-label {
  color: var(--color-text-muted);
  font-size: var(--text-sm);
  font-weight: 600;
}

.field-label-hint {
  font-size: 0.78rem;
  opacity: 0.75;
  font-weight: 400;
}

.field-hint {
  font-size: 0.78rem;
  margin: 0.25rem 0 0;
}

/* ── Compact button variant — used in section headers ─ */
.btn-compact {
  padding: 0.4rem 0.8rem;
  font-size: var(--text-sm);
  border-radius: var(--radius-md, 0.65rem);
}

/* ── Info grid (read-only product fields) ──────────── */
/*
  Two-column grid of label→value rows.
  Each .info-item is a horizontal flex row: label on the left at a
  fixed width, value fills the remaining space.  A subtle bottom
  border acts as the row separator so there is no need for vertical gap.
*/
.info-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 0 1.5rem; /* column gap only; rows are separated by border-bottom */
}

.info-item {
  display: flex;
  align-items: baseline;
  gap: 0.75rem;
  padding: 0.5rem 0;
  border-bottom: 1px solid var(--color-border);
  min-width: 0;
}

/* Remove the bottom border from the last two items (last row) */
.info-item:last-child,
.info-item:nth-last-child(2):not(.info-item-span-2) {
  border-bottom: none;
}

/* Full-width field — spans both columns (description, intended use) */
.info-item-span-2 {
  grid-column: span 2;
}

/* Fixed-width label so all values align vertically */
.info-item .detail-label {
  flex-shrink: 0;
  width: 7.5rem;
}

/* Value text — allow wrapping for long prose */
.info-value {
  flex: 1;
  min-width: 0;
  font-size: var(--text-sm);
  line-height: 1.55;
  word-break: break-word;
}

/* ── Releases compact list ─────────────────────────── */
.release-list {
  display: grid;
  gap: 0.35rem;
}

/* Each release is a full-row link — no nested buttons */
.release-row {
  display: grid;
  /* display_version+tags | status | conformity | date | arrow */
  grid-template-columns: 1fr auto auto auto auto;
  align-items: center;
  gap: 0.75rem;
  padding: 0.7rem 0.9rem;
  border-radius: var(--radius-md, 0.75rem);
  border: 1px solid var(--color-border);
  background: var(--color-surface-elevated);
  text-decoration: none;
  color: inherit;
  transition: background var(--t-fast, 120ms), border-color var(--t-fast, 120ms);
}

.release-row:hover {
  background: var(--color-surface-elevated-strong);
  border-color: var(--color-primary);
}

/* Left cluster: display_version text + CRA micro-tags */
.release-row-left {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  flex-wrap: wrap;
  min-width: 0;
}

.release-display_version {
  font-weight: 700;
  font-size: var(--text-sm);
}

/* CRA metadata micro-tags (non-substantial, Art. 13(10)) */
.release-tag {
  display: inline-flex;
  align-items: center;
  padding: 0.15rem 0.5rem;
  border-radius: 999px;
  font-size: 0.7rem;
  font-weight: 600;
}

/* Gap 2 — non-substantial update lineage — blue tint */
.release-tag-blue {
  background: var(--color-info-bg);
  color: var(--color-info-text);
  border: 1px solid var(--color-info-border);
}

/* Gap 5 — Art. 13(10) consolidated tag — amber tint */
.release-tag-amber {
  background: var(--color-warning-bg);
  color: var(--color-warning-text);
  border: 1px solid var(--color-warning-border);
}

/* Secondary meta columns — muted, right-aligned on narrow rows */
.release-status-badge {
  flex-shrink: 0;
}

.release-row-meta,
.release-row-date {
  color: var(--color-text-muted);
  font-size: var(--text-sm);
  white-space: nowrap;
}

.release-row-arrow {
  width: 1rem;
  height: 1rem;
  flex-shrink: 0;
  color: var(--color-text-muted);
}

/* ── Support period summary rows ───────────────────── */
.support-summary {
  display: grid;
  gap: 0.55rem;
}

.summary-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  font-size: var(--text-sm);
}

/* ── Modal form grid (used in all three AppModals) ─── */
/* 2-column adaptive grid; wide fields can span both columns */
.modal-edit-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 1rem;
}

.modal-field-span-2 {
  grid-column: span 2;
}

/* ── Support period alert preview ─────────────────── */
.support-preview {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  padding: 0.75rem 1rem;
  border-radius: var(--radius-md, 0.75rem);
  border: 1px solid rgba(148, 163, 184, 0.1);
  background: rgba(255, 255, 255, 0.02);
  font-size: var(--text-sm);
}

/* ── Recipient dropdown ─────────────────────────────── */
.recipient-dropdown-field {
  position: relative;
}

.recipient-dropdown {
  position: relative;
}

.recipient-trigger {
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  padding: 0.85rem 0.95rem;
  border-radius: 0.9rem;
  border: 1px solid var(--color-border, rgba(148, 163, 184, 0.25));
  background: var(--color-surface-soft, rgba(15, 23, 42, 0.5));
  color: inherit;
  text-align: left;
  cursor: pointer;
}

.recipient-trigger-copy {
  display: grid;
  gap: 0.2rem;
  min-width: 0;
}

.recipient-trigger-icon {
  flex-shrink: 0;
  color: var(--color-text-muted);
  font-size: 0.8rem;
}

.recipient-menu {
  position: absolute;
  top: calc(100% + 0.5rem);
  left: 0;
  right: 0;
  z-index: 20;
  display: grid;
  gap: 0.65rem;
  max-height: 18rem;
  overflow-y: auto;
  padding: 0.75rem;
  border: 1px solid rgba(15, 23, 42, 0.1);
  border-radius: 0.95rem;
  background: rgba(248, 250, 252, 0.98);
  box-shadow: 0 18px 38px rgba(15, 23, 42, 0.22);
}

.recipient-option {
  display: grid;
  grid-template-columns: auto minmax(0, 1fr);
  gap: 0.8rem;
  align-items: start;
  padding: 0.8rem 0.9rem;
  border: 1px solid rgba(15, 23, 42, 0.08);
  border-radius: 0.8rem;
  background: rgba(255, 255, 255, 0.72);
  cursor: pointer;
}

.recipient-checkbox {
  width: auto;
  margin-top: 0.2rem;
}

.recipient-copy {
  display: grid;
  gap: 0.2rem;
  min-width: 0;
}

.recipient-name {
  color: #0f172a;
}

.recipient-meta {
  display: block;
  color: rgba(15, 23, 42, 0.64);
  overflow-wrap: anywhere;
}

/* ── Toggle button for collapsible sections ────────── */
.toggle-section-btn {
  display: inline-flex;
  align-items: center;
  gap: 0.45rem;
  padding: 0.5rem 0.8rem;
  border-radius: 0.75rem;
  border: 1px solid var(--color-border);
  background: var(--color-surface-elevated);
  color: var(--color-text-muted);
  font-size: 0.84rem;
  font-weight: 600;
  cursor: pointer;
  transition: background 150ms, color 150ms, border-color 150ms;
}

.toggle-section-btn:hover {
  background: var(--color-surface-elevated-strong);
  border-color: var(--color-primary);
  color: var(--color-text);
}

/* ── Tables (remote processing / child products) ───── */
.table-wrapper {
  overflow-x: auto;
}

.data-table {
  width: 100%;
  border-collapse: collapse;
}

.data-table th,
.data-table td {
  padding: 0.85rem 0.75rem;
  text-align: left;
  border-bottom: 1px solid var(--color-border, rgba(148, 163, 184, 0.18));
  vertical-align: top;
}

.data-table th {
  color: var(--color-text-muted);
  font-size: var(--text-sm);
  font-weight: 600;
  white-space: nowrap;
}

/* ── Scope wizard trigger card ─────────────────────── */
.wizard-trigger-card {
  gap: 1rem;
}

.wizard-trigger-body {
  display: flex;
  align-items: center;
  gap: 0.85rem;
}

.wizard-trigger-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 2.6rem;
  height: 2.6rem;
  border-radius: 0.85rem;
  flex-shrink: 0;
  background: linear-gradient(135deg, rgba(139, 92, 246, 0.22), rgba(110, 168, 254, 0.18));
  border: 1px solid rgba(139, 92, 246, 0.25);
  color: #c4b5fd;
}

.wizard-trigger-title {
  margin: 0 0 0.15rem;
}

.wizard-trigger-copy {
  margin: 0;
  font-size: var(--text-sm);
}

.wizard-last-result {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.75rem;
  padding: 0.7rem 0.9rem;
  border-radius: 0.85rem;
  background: var(--color-surface-elevated);
  border: 1px solid var(--color-border);
}

.wizard-last-result-badges {
  display: flex;
  gap: 0.45rem;
  flex-wrap: wrap;
}

/* Full-width wizard open button */
.wizard-open-btn {
  width: 100%;
  justify-content: center;
}

/* ── Scope wizard modal (bespoke) ──────────────────── */
.wizard-modal-backdrop {
  position: fixed;
  inset: 0;
  z-index: 1000;
  background: rgba(5, 10, 20, 0.72);
  backdrop-filter: blur(6px);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 1.5rem;
}

.wizard-modal {
  width: 100%;
  max-width: 540px;
  max-height: 90vh;
  display: flex;
  flex-direction: column;
  border-radius: 20px;
  background: #0c1524;
  border: 1px solid rgba(233, 238, 252, 0.1);
  box-shadow:
    0 32px 80px rgba(0, 0, 0, 0.55),
    0 0 0 1px rgba(110, 168, 254, 0.06);
  overflow: hidden;
}

.wizard-modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  padding: 1.4rem 1.5rem 1rem;
  border-bottom: 1px solid rgba(233, 238, 252, 0.07);
  flex-shrink: 0;
  background: radial-gradient(circle at top right, rgba(139, 92, 246, 0.1), transparent 50%);
}

.wizard-modal-body {
  overflow-y: auto;
  padding: 1.25rem 1.5rem 1.5rem;
  display: grid;
  gap: 1rem;
  scrollbar-width: thin;
  scrollbar-color: rgba(110, 168, 254, 0.3) transparent;
}

/* Close button inside the wizard modal header */
.icon-close-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 2rem;
  height: 2rem;
  border-radius: 8px;
  border: 1px solid rgba(233, 238, 252, 0.14);
  background: rgba(255, 255, 255, 0.05);
  color: rgba(233, 238, 252, 0.7);
  cursor: pointer;
  flex-shrink: 0;
  transition: background 150ms, color 150ms, border-color 150ms;
}

.icon-close-btn:hover {
  background: rgba(251, 113, 133, 0.14);
  border-color: rgba(251, 113, 133, 0.3);
  color: #fda4af;
}

/* Small uppercase eyebrow label above the wizard title */
.timeline-eyebrow {
  margin: 0 0 0.2rem;
  text-transform: uppercase;
  letter-spacing: 0.14em;
  font-size: 0.72rem;
  color: rgba(233, 238, 252, 0.5);
}

/* Vue Transition for wizard modal — backdrop fade + panel scale */
.modal-enter-active,
.modal-leave-active {
  transition: opacity 200ms ease;
}

.modal-enter-active .wizard-modal,
.modal-leave-active .wizard-modal {
  transition: transform 200ms ease, opacity 200ms ease;
}

.modal-enter-from,
.modal-leave-to {
  opacity: 0;
}

.modal-enter-from .wizard-modal,
.modal-leave-to .wizard-modal {
  transform: scale(0.96) translateY(10px);
  opacity: 0;
}

/* ── Wizard form ───────────────────────────────────── */
.wizard-grid {
  display: grid;
  grid-template-columns: 1fr;
  gap: 0.9rem;
}

/* Bordered checkbox row inside the wizard form */
.check-field {
  display: flex;
  gap: 0.65rem;
  align-items: center;
  padding: 0.8rem 0.9rem;
  border-radius: 0.85rem;
  border: 1px solid var(--color-border, rgba(148, 163, 184, 0.2));
  background: var(--color-surface-soft, rgba(15, 23, 42, 0.45));
}

/* Inline checkbox row used in modal grids (release form, edit form) */
.check-field-inline {
  display: flex;
  align-items: flex-start;
  gap: 0.7rem;
  padding: 0.8rem 0.9rem;
  border-radius: 0.85rem;
  border: 1px solid var(--color-border, rgba(148, 163, 184, 0.2));
  background: var(--color-surface-soft, rgba(15, 23, 42, 0.45));
}

/* Question-mark tooltip */
.info-tip {
  position: relative;
  display: inline-flex;
  align-items: center;
  margin-left: 0.35rem;
  vertical-align: middle;
}

.info-tip-trigger {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 1.1rem;
  height: 1.1rem;
  border-radius: 50%;
  border: 1px solid var(--color-text-muted, #94a3b8);
  background: none;
  color: var(--color-text-muted, #94a3b8);
  font-size: 0.65rem;
  font-weight: 700;
  line-height: 1;
  cursor: pointer;
  padding: 0;
  flex-shrink: 0;
}

.info-tip-trigger:hover,
.info-tip-trigger:focus {
  border-color: inherit;
  color: inherit;
  outline: none;
}

.info-tip-popover {
  display: none;
  position: absolute;
  bottom: calc(100% + 0.5rem);
  left: 50%;
  transform: translateX(-50%);
  width: 22rem;
  max-width: 90vw;
  background: var(--color-surface, #0f172a);
  border: 1px solid var(--color-border, rgba(148, 163, 184, 0.25));
  border-radius: 0.75rem;
  padding: 0.75rem 0.9rem;
  font-size: 0.82rem;
  line-height: 1.55;
  color: var(--color-text, #e9eefc);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.35);
  z-index: 200;
  pointer-events: none;
  white-space: normal;
  font-weight: 400;
}

.info-tip-trigger:hover + .info-tip-popover,
.info-tip-trigger:focus + .info-tip-popover {
  display: block;
}

.field {
  display: grid;
  gap: 0.45rem;
}

.field-span-full {
  grid-column: span 1;
}

/* ── Form controls (inside wizard and AppModal forms) ─ */
input,
textarea,
select {
  width: 100%;
  padding: 0.75rem 0.9rem;
  border-radius: 0.85rem;
  border: 1px solid var(--color-border, rgba(148, 163, 184, 0.25));
  background: var(--color-surface-soft, rgba(15, 23, 42, 0.5));
  color: inherit;
  box-sizing: border-box;
}

textarea {
  resize: vertical;
}

/* ── Buttons ───────────────────────────────────────── */
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
  background: var(--color-surface-elevated);
  border-color: var(--color-border-strong);
  color: var(--color-text);
}

.btn-secondary:not(:disabled):hover {
  background: var(--color-surface-elevated-strong);
  border-color: var(--color-primary);
}

.btn-danger-outline {
  background: transparent;
  border-color: var(--color-danger-border);
  color: var(--color-danger-text);
}

.btn-danger-outline:not(:disabled):hover { background: var(--color-danger-bg); }

/* ── Wizard evaluation result panel ───────────────── */
.result-panel {
  display: grid;
  gap: 0.85rem;
  padding: 1rem;
  border-radius: 1rem;
  background: rgba(255, 255, 255, 0.03);
}

.result-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
}

.result-rationale {
  margin: 0.35rem 0 0;
  line-height: 1.5;
}

/* ── Inline form action row ────────────────────────── */
.form-actions {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  flex-wrap: wrap;
}

.form-error {
  color: var(--color-danger-text);
  margin: 0;
}

/* ── Badges ────────────────────────────────────────── */
.badge {
  display: inline-flex;
  align-items: center;
  border-radius: 999px;
  padding: 0.35rem 0.65rem;
  font-size: var(--text-xs);
  font-weight: 600;
}

.badge-neutral {
  background: var(--color-surface-elevated-strong);
  color: var(--color-text-muted);
  border: 1px solid var(--color-border);
}

.badge-success {
  background: var(--color-success-bg);
  color: var(--color-success-text);
  border: 1px solid var(--color-success-border);
}

.badge-warning {
  background: var(--color-warning-bg);
  color: var(--color-warning-text);
  border: 1px solid var(--color-warning-border);
}

.badge-danger {
  background: var(--color-danger-bg);
  color: var(--color-danger-text);
  border: 1px solid var(--color-danger-border);
}

/* ── Responsive breakpoints ────────────────────────── */
@media (max-width: 1200px) {
  /* Collapse 5-column stats bar to 3 */
  .stats-grid {
    grid-template-columns: repeat(3, minmax(0, 1fr));
  }
}

@media (max-width: 1100px) {
  /* Stack workspace columns on medium viewports */
  .workspace {
    grid-template-columns: 1fr;
  }

  /* Un-stick sidebar once it wraps below the main column */
  .side-column {
    position: static;
  }
}

@media (max-width: 800px) {
  /* Collapse stats bar, info grid, modal form grid to single column */
  .stats-grid,
  .info-grid,
  .modal-edit-grid {
    grid-template-columns: 1fr;
  }

  .info-item-span-2,
  .modal-field-span-2 {
    grid-column: span 1;
  }

  /* Release rows: stack fields vertically on small screens */
  .release-row {
    grid-template-columns: 1fr auto;
    grid-template-rows: auto auto;
  }

  .release-row-meta,
  .release-row-date {
    display: none; /* hide secondary meta on very small screens */
  }
}
</style>

<style>
/* ── Light-theme overrides ─────────────────────────── */
/* These rules target specific dark-mode colours that need
   to be inverted when the user switches to light theme.
   Scoped styles cannot target data-theme on :root, hence
   they live in the global <style> block. */

:root[data-theme="light"] .feedback-banner-danger { color: #be123c; }
:root[data-theme="light"] .feedback-banner-success { color: #15803d; }

:root[data-theme="light"] .badge-neutral {
  background: rgba(71, 85, 105, 0.1);
  color: #475569;
}
:root[data-theme="light"] .badge-success {
  background: rgba(21, 128, 61, 0.1);
  color: #15803d;
}
:root[data-theme="light"] .badge-warning {
  background: rgba(184, 155, 18, 0.1);
  color: #78350f;
}
:root[data-theme="light"] .badge-danger {
  background: rgba(239, 68, 68, 0.1);
  color: #be123c;
}

:root[data-theme="light"] .release-tag-blue {
  background: rgba(37, 99, 235, 0.1);
  color: #1d4ed8;
}
:root[data-theme="light"] .release-tag-amber {
  background: rgba(180, 140, 12, 0.1);
  color: #78350f;
}

:root[data-theme="light"] .release-row:hover {
  background: rgba(37, 99, 235, 0.05);
  border-color: rgba(37, 99, 235, 0.18);
}

:root[data-theme="light"] .wizard-trigger-icon {
  background: linear-gradient(135deg, rgba(124, 58, 237, 0.12), rgba(37, 99, 235, 0.1));
  border-color: rgba(124, 58, 237, 0.2);
  color: #5b21b6;
}
:root[data-theme="light"] .wizard-last-result {
  background: rgba(28, 107, 39, 0.04);
  border-color: rgba(28, 107, 39, 0.12);
}
:root[data-theme="light"] .wizard-modal-backdrop {
  background: rgba(20, 33, 15, 0.5);
}
:root[data-theme="light"] .wizard-modal {
  background: #ffffff;
  border-color: rgba(28, 107, 39, 0.15);
  box-shadow: 0 32px 80px rgba(20, 33, 15, 0.12), 0 0 0 1px rgba(28, 107, 39, 0.08);
}
:root[data-theme="light"] .wizard-modal-header {
  border-bottom-color: rgba(28, 107, 39, 0.1);
  background: radial-gradient(circle at top right, rgba(124, 58, 237, 0.06), transparent 50%);
}
:root[data-theme="light"] .wizard-modal-body {
  scrollbar-color: rgba(79, 156, 19, 0.3) transparent;
}
:root[data-theme="light"] .icon-close-btn {
  border-color: rgba(28, 107, 39, 0.16);
  background: rgba(28, 107, 39, 0.06);
  color: rgba(20, 33, 15, 0.65);
}
:root[data-theme="light"] .icon-close-btn:hover {
  background: rgba(239, 68, 68, 0.1);
  border-color: rgba(239, 68, 68, 0.28);
  color: #be123c;
}
:root[data-theme="light"] .timeline-eyebrow {
  color: rgba(20, 33, 15, 0.5);
}
:root[data-theme="light"] .toggle-section-btn {
  border-color: rgba(28, 107, 39, 0.2);
  background: rgba(28, 107, 39, 0.04);
  color: rgba(20, 33, 15, 0.75);
}
:root[data-theme="light"] .toggle-section-btn:hover {
  background: rgba(37, 99, 235, 0.08);
  border-color: rgba(37, 99, 235, 0.25);
  color: #1d4ed8;
}
:root[data-theme="light"] .result-panel {
  background: rgba(28, 107, 39, 0.04);
}
:root[data-theme="light"] .support-preview {
  background: rgba(28, 107, 39, 0.04);
  border-color: rgba(28, 107, 39, 0.12);
}

:root[data-theme="light"] .info-tip-popover {
  background: #ffffff;
  color: #0f172a;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.12);
}

/* Card border visibility — replace faint border with shadow ring */
[data-theme="light"] .page .card {
  box-shadow: 0 2px 6px rgba(0,0,0,0.08), 0 0 0 1px rgba(0,0,0,0.14);
  border-color: transparent;
}
/* Stat cards in the stats bar */
[data-theme="light"] .page .stat-card {
  box-shadow: 0 1px 4px rgba(0,0,0,0.07), 0 0 0 1px rgba(0,0,0,0.13);
  border-color: transparent;
}
/* Release rows */
[data-theme="light"] .page .release-row {
  border-color: transparent;
  box-shadow: 0 1px 3px rgba(0,0,0,0.07), 0 0 0 1px rgba(0,0,0,0.12);
}
[data-theme="light"] .page .release-row:hover {
  border-color: transparent;
  box-shadow: 0 1px 4px rgba(0,0,0,0.09), 0 0 0 1.5px rgba(79,156,19,0.5);
}
</style>
