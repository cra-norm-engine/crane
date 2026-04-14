<template>
  <section class="page">
    <header class="page-header card">
      <div>
        <h1 class="page-title">{{ product?.name || "Product Detail" }}</h1>
        <p class="muted page-subtitle">
          Review CRA scope, classification, releases, remote processing elements, and edit core product details.
        </p>
      </div>

      <div class="page-actions">
        <button class="btn btn-secondary" type="button" @click="loadProduct" :disabled="isLoading || isSaving || isSavingSupportPeriod">
          {{ isLoading ? "Refreshing..." : "Refresh" }}
        </button>
        <button
          v-if="product && !isEditing"
          class="btn btn-primary"
          type="button"
          @click="startEditing"
          :disabled="isLoading || isSaving || isSavingSupportPeriod"
        >
          Edit product
        </button>
        <template v-else-if="product && isEditing">
          <button
            class="btn btn-secondary"
            type="button"
            @click="cancelEditing"
            :disabled="isSaving"
          >
            Cancel
          </button>
          <button class="btn btn-primary" type="button" @click="saveProduct" :disabled="isSaving">
            {{ isSaving ? "Saving..." : "Save changes" }}
          </button>
        </template>
      </div>
    </header>

    <div v-if="errorMessage" class="card feedback feedback-error">
      {{ errorMessage }}
    </div>

    <div v-if="successMessage" class="card feedback feedback-success">
      {{ successMessage }}
    </div>

    <div v-else-if="isLoading" class="card feedback">
      Loading product…
    </div>

    <template v-else-if="product">
      <div class="grid stats-grid">
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
      </div>

      <div class="workspace">
        <main class="main-column">
          <section class="card info-card">
            <div class="section-header">
              <div>
                <h2 class="section-title">Product information</h2>
                <p class="muted">Core identity and lifecycle metadata.</p>
              </div>
              <span v-if="isEditing" class="badge badge-warning">Editing enabled</span>
            </div>

            <div v-if="!isEditing" class="info-grid">
              <div class="info-item">
                <span class="detail-label">Manufacturer</span>
                <p>{{ product.manufacturer_name }}</p>
              </div>

              <div class="info-item">
                <span class="detail-label">Type</span>
                <p>{{ product.product_type }}</p>
              </div>

              <div class="info-item info-item-span-2">
                <span class="detail-label">Description</span>
                <p>{{ product.description || "No description provided" }}</p>
              </div>

              <div class="info-item info-item-span-2">
                <span class="detail-label">Intended use</span>
                <p>{{ product.intended_use }}</p>
              </div>

              <div class="info-item">
                <span class="detail-label">Parent product</span>
                <p>{{ product.parent_product_id || "None" }}</p>
              </div>

              <div class="info-item">
                <span class="detail-label">Updated</span>
                <p>{{ formatDateTime(product.updated_at) }}</p>
              </div>
            </div>

            <form v-else class="edit-grid" @submit.prevent="saveProduct">
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

              <label class="field field-span-2">
                <span class="field-label">Description</span>
                <textarea v-model.trim="editForm.description" rows="4" />
              </label>

              <label class="field field-span-2">
                <span class="field-label">Intended use</span>
                <textarea v-model.trim="editForm.intended_use" rows="4" />
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

              <div class="field field-span-2 inline-actions">
                <button class="btn btn-secondary" type="button" @click="cancelEditing" :disabled="isSaving">
                  Cancel
                </button>
                <button class="btn btn-primary" type="submit" :disabled="isSaving">
                  {{ isSaving ? "Saving..." : "Save changes" }}
                </button>
              </div>
            </form>
          </section>

          <section class="card">
            <div class="section-header">
              <div>
                <h2 class="section-title">Support period</h2>
                <p class="muted">
                  Guided lifecycle record for support duration, rationale, user-facing summary,
                  packaging text, and versioned history.
                </p>
              </div>
              <span class="badge badge-neutral">
                {{ supportHistoryCount }} record(s)
              </span>
            </div>

            <div v-if="supportPeriodError" class="feedback feedback-error">
              {{ supportPeriodError }}
            </div>

            <div v-if="supportPeriodSuccess" class="feedback feedback-success">
              {{ supportPeriodSuccess }}
            </div>

            <form class="edit-grid" @submit.prevent="saveSupportPeriod">
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
                <span class="field-label">Notify before EOS</span>
                <input v-model.number="supportForm.notify_before_days" type="number" min="1" max="3650" step="1" />
              </label>

              <div class="info-item">
                <span class="detail-label">Current status</span>
                <p>
                  {{ activeSupportPeriod ? "Active record loaded" : "No support period recorded yet" }}
                </p>
              </div>

              <div class="info-item">
                <span class="detail-label">Alert schedule preview</span>
                <p>{{ notificationSchedulePreview }}</p>
              </div>

              <div class="field field-span-2 recipient-dropdown-field">
                <span class="field-label">Notification recipients</span>
                <div v-if="notificationRecipientOptions.length === 0" class="checkbox-panel muted">
                  No active users are currently available.
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
                      <small class="muted">
                        Choose one or more users to receive end-of-support alerts.
                      </small>
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
                        :checked="supportForm.recipient_user_ids.includes(option.id)"
                        type="checkbox"
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

              <label class="field field-span-2">
                <span class="field-label">Justification text</span>
                <textarea v-model.trim="supportForm.justification_text" rows="4" />
              </label>

              <label class="field">
                <span class="field-label">Expected use time</span>
                <textarea v-model.trim="supportForm.expected_use_time_text" rows="3" />
              </label>

              <label class="field">
                <span class="field-label">Comparable products</span>
                <textarea v-model.trim="supportForm.comparable_products_text" rows="3" />
              </label>

              <label class="field field-span-2">
                <span class="field-label">Third-party support constraints</span>
                <textarea v-model.trim="supportForm.third_party_support_constraints_text" rows="3" />
              </label>

              <label class="field field-span-2">
                <span class="field-label">User-facing summary</span>
                <textarea v-model.trim="supportForm.user_facing_summary" rows="4" />
              </label>

              <label class="field field-span-2">
                <span class="field-label">Packaging summary</span>
                <textarea v-model.trim="supportForm.packaging_summary" rows="3" />
              </label>

              <div class="field field-span-2 inline-actions">
                <button class="btn btn-secondary" type="button" @click="generateSupportSnippets" :disabled="isSavingSupportPeriod">
                  Generate snippets
                </button>
                <button class="btn btn-primary" type="submit" :disabled="isSavingSupportPeriod">
                  {{ isSavingSupportPeriod ? "Saving..." : activeSupportPeriod ? "Save new version" : "Create support period" }}
                </button>
              </div>
            </form>
          </section>

          <section class="card">
            <div class="section-header">
              <div>
                <h2 class="section-title">Release workflow</h2>
                <p class="muted">
                  Each release has its own evidence workspace and approval gate. Open a release to upload artifacts,
                  submit evidence for review, and approve the gate.
                </p>
              </div>
              <button class="btn btn-primary" type="button" @click="showReleaseForm = !showReleaseForm" :disabled="isCreatingRelease">
                {{ showReleaseForm ? "Close release form" : "Create release" }}
              </button>
            </div>

            <form v-if="showReleaseForm" class="edit-grid release-form" @submit.prevent="createRelease">
              <label class="field">
                <span class="field-label">Version</span>
                <input v-model.trim="releaseForm.version" type="text" maxlength="100" required placeholder="1.0.0" />
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

              <label class="field field-span-2">
                <span class="field-label">Release notes</span>
                <textarea v-model.trim="releaseForm.release_notes" rows="3" placeholder="Optional release notes" />
              </label>

              <div class="field field-span-2 inline-actions">
                <button class="btn btn-secondary" type="button" @click="resetReleaseForm" :disabled="isCreatingRelease">
                  Reset
                </button>
                <button class="btn btn-primary" type="submit" :disabled="isCreatingRelease">
                  {{ isCreatingRelease ? "Creating..." : "Create release and open workflow" }}
                </button>
              </div>
            </form>

            <div v-if="product.releases.length === 0" class="empty-panel">
              Create a release to start the release workflow for this product.
            </div>

            <div v-else class="release-workflow-grid">
              <article v-for="release in product.releases" :key="`workflow-${release.id}`" class="release-workflow-card">
                <div class="release-workflow-head">
                  <div>
                    <p class="release-workflow-version">Release {{ release.version }}</p>
                    <p class="muted">
                      {{ formatConformityRoute(release.conformity_route_snapshot) }}
                      · {{ formatClassification(release.classification_snapshot) }}
                    </p>
                  </div>
                  <span class="badge badge-neutral">
                    {{ formatReleaseStatus(release.release_status) }}
                  </span>
                </div>

                <div class="release-workflow-meta">
                  <span>Planned: {{ formatDate(release.planned_release_date) }}</span>
                  <span>Actual: {{ formatDate(release.actual_release_date) }}</span>
                </div>

                <RouterLink
                  class="release-workspace-link release-workspace-link-prominent"
                  :to="{ name: 'release-gate', params: { releaseId: release.id } }"
                >
                  Open release workflow
                </RouterLink>
              </article>
            </div>
          </section>

          <section class="card">
            <div class="section-header">
              <div>
                <h2 class="section-title">Releases</h2>
                <p class="muted">{{ product.releases.length }} release(s)</p>
              </div>
            </div>

            <div v-if="product.releases.length === 0" class="empty-panel">
              No releases yet.
            </div>

            <div v-else class="table-wrapper">
              <table class="data-table">
                <thead>
                  <tr>
                    <th>Version</th>
                    <th>Status</th>
                    <th>Classification</th>
                    <th>Conformity route</th>
                    <th>Planned</th>
                    <th>Actual</th>
                    <th>Workflow</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="release in product.releases" :key="release.id">
                    <td>
                      <RouterLink class="release-link" :to="{ name: 'release-gate', params: { releaseId: release.id } }">
                        <strong>{{ release.version }}</strong>
                      </RouterLink>
                    </td>
                    <td>
                      <span class="badge badge-neutral">
                        {{ formatReleaseStatus(release.release_status) }}
                      </span>
                    </td>
                    <td>
                      <span class="badge" :class="classificationClass(release.classification_snapshot)">
                        {{ formatClassification(release.classification_snapshot) }}
                      </span>
                    </td>
                    <td>{{ formatConformityRoute(release.conformity_route_snapshot) }}</td>
                    <td>{{ formatDate(release.planned_release_date) }}</td>
                    <td>{{ formatDate(release.actual_release_date) }}</td>
                    <td>
                      <RouterLink class="release-workspace-link" :to="{ name: 'release-gate', params: { releaseId: release.id } }">
                        Open workspace
                      </RouterLink>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </section>

          <section class="card">
            <div class="section-header">
              <div>
                <h2 class="section-title">Remote processing elements</h2>
                <p class="muted">{{ product.remote_processing_elements.length }} element(s)</p>
              </div>
            </div>

            <div v-if="product.remote_processing_elements.length === 0" class="empty-panel">
              No remote processing elements yet.
            </div>

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

          <section class="card">
            <div class="section-header">
              <div>
                <h2 class="section-title">Child products</h2>
                <p class="muted">{{ product.child_products.length }} child product(s)</p>
              </div>
            </div>

            <div v-if="product.child_products.length === 0" class="empty-panel">
              No child products linked.
            </div>

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

        <aside class="side-column">
          <section class="card summary-card">
            <div class="section-header">
              <div>
                <h2 class="section-title">Summary</h2>
                <p class="muted">At-a-glance product status.</p>
              </div>
            </div>

            <div class="summary-list">
              <div class="summary-row">
                <span class="detail-label">Name</span>
                <strong>{{ product.name }}</strong>
              </div>

              <div class="summary-row">
                <span class="detail-label">Code</span>
                <strong class="summary-code">{{ product.product_code }}</strong>
              </div>

              <div class="summary-row">
                <span class="detail-label">Classification</span>
                <span class="badge" :class="classificationClass(product.current_classification)">
                  {{ formatClassification(product.current_classification) }}
                </span>
              </div>

              <div class="summary-row">
                <span class="detail-label">Scope</span>
                <span class="badge" :class="scopeClass(product.scope_status)">
                  {{ formatScopeStatus(product.scope_status) }}
                </span>
              </div>

              <div class="summary-row">
                <span class="detail-label">Releases</span>
                <strong>{{ product.releases.length }}</strong>
              </div>

              <div class="summary-row">
                <span class="detail-label">Remote elements</span>
                <strong>{{ product.remote_processing_elements.length }}</strong>
              </div>

              <div class="summary-row">
                <span class="detail-label">Child products</span>
                <strong>{{ product.child_products.length }}</strong>
              </div>

              <div class="summary-row">
                <span class="detail-label">Active support period</span>
                <strong>{{ activeSupportPeriod ? formatDate(activeSupportPeriod.support_end_date) : "—" }}</strong>
              </div>
            </div>
          </section>

          <AuditTimeline
            v-if="canViewAudit"
            title="Product timeline"
            eyebrow="Traceability"
            description="Follow the high-value actions for this product, including release, evidence, support, security, and admin-linked changes."
            :events="auditEvents"
            :loading="isAuditLoading"
            :error-message="auditErrorMessage"
            :show-refresh="true"
            @refresh="loadAuditEvents"
          />

          <section class="card">
            <div class="section-header">
              <div>
                <h2 class="section-title">CRA scope wizard</h2>
                <p class="muted">Run the backend rule engine and store the evaluation result.</p>
              </div>
            </div>

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
                  {{ isEvaluatingScope ? "Evaluating..." : "Run scope evaluation" }}
                </button>
              </div>
            </form>

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
          </section>
        </aside>
      </div>
    </template>
  </section>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, reactive, ref, watch } from "vue";
import { useRouter } from "vue-router";

import AuditTimeline from "@/components/AuditTimeline.vue";
import { auditService } from "@/services/audit-service";
import { productService } from "@/services/product-service";
import { productReleaseService } from "@/services/product-release-service";
import { supportPeriodService } from "@/services/support-period-service";
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

const props = defineProps<{
  productId: string;
}>();
const router = useRouter();
const authStore = useAuthStore();

const product = ref<ProductDetailRead | null>(null);
const activeSupportPeriod = ref<SupportPeriodRecordRead | null>(null);
const supportHistoryCount = ref(0);
const notificationRecipientOptions = ref<SupportPeriodNotificationRecipientOptionRead[]>([]);
const recipientDropdownRef = ref<HTMLElement | null>(null);
const isRecipientDropdownOpen = ref(false);
const auditEvents = ref<AuditEventRead[]>([]);

const isLoading = ref(false);
const isSaving = ref(false);
const isEditing = ref(false);
const isEvaluatingScope = ref(false);
const isSavingSupportPeriod = ref(false);
const isCreatingRelease = ref(false);
const showReleaseForm = ref(false);
const isAuditLoading = ref(false);

const errorMessage = ref("");
const successMessage = ref("");
const supportPeriodError = ref("");
const supportPeriodSuccess = ref("");
const scopeError = ref("");
const scopeResult = ref<ProductScopeEvaluationRead | null>(null);
const auditErrorMessage = ref("");

const scopeForm = reactive<ProductScopeEvaluationRequest>({
  is_digital_product: false,
  has_network_connectivity: false,
  performs_remote_data_processing: false,
  safety_component: false,
  used_in_critical_sector: false,
  handles_sensitive_functions: false,
  excluded_category: false,
  notes: "",
});

const editForm = reactive({
  name: "",
  product_code: "",
  manufacturer_name: "",
  product_type: "",
  description: "",
  intended_use: "",
  parent_product_id: "",
  current_classification: "normal" as ProductClassification,
  scope_status: "undecided",
});

const supportForm = reactive({
  support_start_date: "",
  support_end_date: "",
  notify_before_days: 180,
  support_type: "standard" as SupportType,
  recipient_user_ids: [] as string[],
  justification_text: "",
  expected_use_time_text: "",
  comparable_products_text: "",
  third_party_support_constraints_text: "",
  user_facing_summary: "",
  packaging_summary: "",
});

const releaseForm = reactive({
  version: "",
  planned_release_date: "",
  classification_snapshot: "normal" as ProductClassification,
  conformity_route_snapshot: "undecided" as ConformityRoute,
  release_notes: "",
});

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
    year: "numeric",
    month: "short",
    day: "2-digit",
  }).format(previewDate);
});

const canViewAudit = computed(() => authStore.hasPermission("audit_read"));

const selectedRecipientsSummary = computed(() => {
  const count = supportForm.recipient_user_ids.length;

  if (count === 0) {
    return "Select users";
  }

  if (count === 1) {
    const selected = notificationRecipientOptions.value.find(
      (option) => option.id === supportForm.recipient_user_ids[0],
    );
    return selected?.full_name ?? "1 user selected";
  }

  return `${count} users selected`;
});

function syncEditForm(): void {
  if (!product.value) return;

  editForm.name = product.value.name ?? "";
  editForm.product_code = product.value.product_code ?? "";
  editForm.manufacturer_name = product.value.manufacturer_name ?? "";
  editForm.product_type = product.value.product_type ?? "";
  editForm.description = product.value.description ?? "";
  editForm.intended_use = product.value.intended_use ?? "";
  editForm.parent_product_id = product.value.parent_product_id ?? "";
  editForm.current_classification = product.value.current_classification;
  editForm.scope_status = product.value.scope_status;
  releaseForm.classification_snapshot = product.value.current_classification;
}

function syncSupportForm(): void {
  if (!activeSupportPeriod.value) {
    supportForm.support_start_date = "";
    supportForm.support_end_date = "";
    supportForm.notify_before_days = 180;
    supportForm.support_type = "standard";
    supportForm.recipient_user_ids = [];
    supportForm.justification_text = "";
    supportForm.expected_use_time_text = "";
    supportForm.comparable_products_text = "";
    supportForm.third_party_support_constraints_text = "";
    supportForm.user_facing_summary = "";
    supportForm.packaging_summary = "";
    return;
  }

  supportForm.support_start_date = activeSupportPeriod.value.support_start_date ?? "";
  supportForm.support_end_date = activeSupportPeriod.value.support_end_date ?? "";
  supportForm.notify_before_days = activeSupportPeriod.value.notify_before_days ?? 180;
  supportForm.support_type = activeSupportPeriod.value.support_type;
  supportForm.recipient_user_ids = [...activeSupportPeriod.value.recipient_user_ids];
  supportForm.justification_text = activeSupportPeriod.value.justification_text ?? "";
  supportForm.expected_use_time_text = activeSupportPeriod.value.expected_use_time_text ?? "";
  supportForm.comparable_products_text = activeSupportPeriod.value.comparable_products_text ?? "";
  supportForm.third_party_support_constraints_text =
    activeSupportPeriod.value.third_party_support_constraints_text ?? "";
  supportForm.user_facing_summary = activeSupportPeriod.value.user_facing_summary ?? "";
  supportForm.packaging_summary = activeSupportPeriod.value.packaging_summary ?? "";
}

function startEditing(): void {
  syncEditForm();
  successMessage.value = "";
  errorMessage.value = "";
  isEditing.value = true;
}

function cancelEditing(): void {
  syncEditForm();
  isEditing.value = false;
}

function resetReleaseForm(): void {
  releaseForm.version = "";
  releaseForm.planned_release_date = "";
  releaseForm.classification_snapshot = product.value?.current_classification ?? "normal";
  releaseForm.conformity_route_snapshot = "undecided";
  releaseForm.release_notes = "";
}

function toggleRecipientDropdown(): void {
  isRecipientDropdownOpen.value = !isRecipientDropdownOpen.value;
}

function closeRecipientDropdown(): void {
  isRecipientDropdownOpen.value = false;
}

function toggleRecipient(userId: string): void {
  if (supportForm.recipient_user_ids.includes(userId)) {
    supportForm.recipient_user_ids = supportForm.recipient_user_ids.filter((value) => value !== userId);
    return;
  }

  supportForm.recipient_user_ids = [...supportForm.recipient_user_ids, userId];
}

function handleWindowClick(event: MouseEvent): void {
  if (!isRecipientDropdownOpen.value) {
    return;
  }

  const target = event.target;
  if (!(target instanceof Node)) {
    return;
  }

  if (recipientDropdownRef.value?.contains(target)) {
    return;
  }

  closeRecipientDropdown();
}

function formatClassification(value: ProductClassification): string {
  switch (value) {
    case "important_class_1":
      return "Important Class I";
    case "important_class_2":
      return "Important Class II";
    case "critical":
      return "Critical";
    default:
      return "Normal";
  }
}

function formatConformityRoute(value: ConformityRoute): string {
  switch (value) {
    case "self_assessment":
      return "Self assessment";
    case "third_party_assessment":
      return "Third-party assessment";
    case "not_applicable":
      return "Not applicable";
    default:
      return "Undecided";
  }
}

function formatReleaseStatus(value: string): string {
  return value.replaceAll("_", " ");
}

function formatScopeStatus(value: string): string {
  switch (value) {
    case "in_scope":
      return "In scope";
    case "out_of_scope":
      return "Out of scope";
    default:
      return "Undecided";
  }
}

function classificationClass(value: ProductClassification): string {
  switch (value) {
    case "critical":
      return "badge-danger";
    case "important_class_1":
    case "important_class_2":
      return "badge-warning";
    default:
      return "badge-neutral";
  }
}

function scopeClass(value: string): string {
  switch (value) {
    case "in_scope":
      return "badge-success";
    case "out_of_scope":
      return "badge-danger";
    default:
      return "badge-neutral";
  }
}

function formatDate(value: string | null): string {
  if (!value) return "—";
  return new Intl.DateTimeFormat(undefined, {
    year: "numeric",
    month: "short",
    day: "2-digit",
  }).format(new Date(value));
}

function formatDateTime(value: string): string {
  return new Intl.DateTimeFormat(undefined, {
    year: "numeric",
    month: "short",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  }).format(new Date(value));
}

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

  isAuditLoading.value = true;
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

async function loadProduct(): Promise<void> {
  isLoading.value = true;
  errorMessage.value = "";

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

async function saveProduct(): Promise<void> {
  if (!product.value) return;

  errorMessage.value = "";
  successMessage.value = "";
  isSaving.value = true;

  try {
    const payload: ProductUpdate = {
      name: editForm.name.trim(),
      product_code: editForm.product_code.trim(),
      manufacturer_name: editForm.manufacturer_name.trim(),
      product_type: editForm.product_type.trim(),
      description: editForm.description.trim() || null,
      intended_use: editForm.intended_use.trim(),
      parent_product_id: editForm.parent_product_id.trim() || null,
      current_classification: editForm.current_classification,
      scope_status: editForm.scope_status,
    };

    await productService.update(props.productId, payload);
    successMessage.value = "Product updated.";
    isEditing.value = false;
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

  supportPeriodError.value = "";
  supportPeriodSuccess.value = "";

  try {
    const snippets = await supportPeriodService.generateSnippets({
      product_id: props.productId,
      support_start_date: supportForm.support_start_date,
      support_end_date: supportForm.support_end_date,
      support_type: supportForm.support_type,
      justification_text: supportForm.justification_text.trim(),
      expected_use_time_text: supportForm.expected_use_time_text.trim() || null,
      comparable_products_text: supportForm.comparable_products_text.trim() || null,
      third_party_support_constraints_text:
        supportForm.third_party_support_constraints_text.trim() || null,
    });

    supportForm.user_facing_summary = snippets.user_facing_summary;
    supportForm.packaging_summary = snippets.packaging_summary;
    supportPeriodSuccess.value = "Support snippets generated.";
  } catch (error) {
    supportPeriodError.value =
      error instanceof Error ? error.message : "Failed to generate support snippets.";
  }
}

async function saveSupportPeriod(): Promise<void> {
  if (!props.productId) return;

  isSavingSupportPeriod.value = true;
  supportPeriodError.value = "";
  supportPeriodSuccess.value = "";

  try {
    if (activeSupportPeriod.value) {
      await supportPeriodService.update(activeSupportPeriod.value.id, {
        support_start_date: supportForm.support_start_date,
        support_end_date: supportForm.support_end_date,
        notify_before_days: supportForm.notify_before_days,
        support_type: supportForm.support_type,
        recipient_user_ids: supportForm.recipient_user_ids,
        justification_text: supportForm.justification_text.trim(),
        expected_use_time_text: supportForm.expected_use_time_text.trim() || null,
        comparable_products_text: supportForm.comparable_products_text.trim() || null,
        third_party_support_constraints_text:
          supportForm.third_party_support_constraints_text.trim() || null,
        user_facing_summary: supportForm.user_facing_summary.trim() || null,
        packaging_summary: supportForm.packaging_summary.trim() || null,
      });
      supportPeriodSuccess.value = "Support period version recorded.";
    } else {
      await supportPeriodService.create({
        product_id: props.productId,
        support_start_date: supportForm.support_start_date,
        support_end_date: supportForm.support_end_date,
        notify_before_days: supportForm.notify_before_days,
        support_type: supportForm.support_type,
        recipient_user_ids: supportForm.recipient_user_ids,
        justification_text: supportForm.justification_text.trim(),
        expected_use_time_text: supportForm.expected_use_time_text.trim() || null,
        comparable_products_text: supportForm.comparable_products_text.trim() || null,
        third_party_support_constraints_text:
          supportForm.third_party_support_constraints_text.trim() || null,
        user_facing_summary: supportForm.user_facing_summary.trim() || null,
        packaging_summary: supportForm.packaging_summary.trim() || null,
      });
      supportPeriodSuccess.value = "Support period created.";
    }

    await Promise.all([loadSupportPeriod(), loadAuditEvents()]);
  } catch (error) {
    supportPeriodError.value =
      error instanceof Error ? error.message : "Failed to save support period.";
  } finally {
    isSavingSupportPeriod.value = false;
  }
}

async function runScopeEvaluation(): Promise<void> {
  scopeError.value = "";
  isEvaluatingScope.value = true;

  try {
    scopeResult.value = await productService.evaluateScope(props.productId, {
      ...scopeForm,
      notes: scopeForm.notes?.trim() || null,
    });
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

  errorMessage.value = "";
  successMessage.value = "";
  isCreatingRelease.value = true;

  try {
    const payload: ProductReleaseCreate = {
      product_id: product.value.id,
      version: releaseForm.version.trim(),
      release_status: "draft",
      classification_snapshot: releaseForm.classification_snapshot,
      conformity_route_snapshot: releaseForm.conformity_route_snapshot,
      planned_release_date: releaseForm.planned_release_date
        ? `${releaseForm.planned_release_date}T00:00:00Z`
        : null,
      actual_release_date: null,
      release_notes: releaseForm.release_notes.trim() || null,
    };

    const createdRelease = await productReleaseService.create(payload);
    successMessage.value = `Release ${createdRelease.version} created.`;
    showReleaseForm.value = false;
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

watch(
  () => props.productId,
  () => {
    scopeResult.value = null;
    isEditing.value = false;
    successMessage.value = "";
    supportPeriodSuccess.value = "";
    supportPeriodError.value = "";
    activeSupportPeriod.value = null;
    auditEvents.value = [];
    auditErrorMessage.value = "";
    closeRecipientDropdown();
    supportHistoryCount.value = 0;
    showReleaseForm.value = false;
    resetReleaseForm();
    void loadProduct();
  },
  { immediate: true },
);

onMounted(() => {
  window.addEventListener("click", handleWindowClick);
});

onBeforeUnmount(() => {
  window.removeEventListener("click", handleWindowClick);
});
</script>

<style scoped>
.page {
  display: grid;
  gap: 1rem;
}

.page-header,
.section-header,
.form-actions,
.inline-actions {
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

.checkbox-panel {
  display: grid;
  gap: 0.75rem;
  padding: 0.9rem;
  border: 1px solid rgba(15, 23, 42, 0.08);
  border-radius: 0.9rem;
  background: rgba(248, 250, 252, 0.85);
}

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
  color: var(--color-text-muted, #94a3b8);
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

.page-title,
.section-title {
  margin: 0;
}

.page-subtitle {
  margin-top: 0.35rem;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 1rem;
}

.workspace {
  display: grid;
  grid-template-columns: minmax(0, 1.5fr) minmax(320px, 420px);
  gap: 1rem;
  align-items: start;
}

.main-column,
.side-column {
  display: grid;
  gap: 1rem;
}

.side-column {
  position: sticky;
  top: 1rem;
}

.card,
.stat-card {
  display: grid;
  gap: 0.9rem;
}

.stat-label,
.detail-label,
.field-label {
  color: var(--color-text-muted, #94a3b8);
  font-size: 0.85rem;
}

.stat-value {
  font-size: 1.35rem;
  font-weight: 700;
}

.stat-value-code,
.summary-code {
  word-break: break-word;
}

.info-grid,
.edit-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 1rem;
}

.info-item {
  display: grid;
  gap: 0.35rem;
  min-width: 0;
}

.info-item-span-2,
.field-span-2 {
  grid-column: span 2;
}

.info-item p,
.result-rationale,
.summary-row strong,
.summary-row span:last-child {
  margin: 0;
  line-height: 1.5;
}

.summary-list {
  display: grid;
  gap: 0.85rem;
}

.summary-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
}

.wizard-grid {
  display: grid;
  grid-template-columns: 1fr;
  gap: 0.9rem;
}

.check-field {
  display: flex;
  gap: 0.65rem;
  align-items: center;
  padding: 0.8rem 0.9rem;
  border-radius: 0.85rem;
  border: 1px solid var(--color-border, rgba(148, 163, 184, 0.2));
  background: var(--color-surface-soft, rgba(15, 23, 42, 0.45));
}

.field {
  display: grid;
  gap: 0.45rem;
}

.field-span-full {
  grid-column: span 1;
}

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

.btn {
  border: 1px solid transparent;
  border-radius: 0.85rem;
  padding: 0.75rem 1rem;
  font: inherit;
  cursor: pointer;
}

.btn-primary {
  background: linear-gradient(135deg, #8b5cf6, #6ea8fe);
  color: white;
}

.btn-secondary {
  background: transparent;
  border-color: var(--color-border, rgba(148, 163, 184, 0.25));
  color: inherit;
}

.btn:disabled {
  opacity: 0.65;
  cursor: not-allowed;
}

.feedback,
.empty-panel {
  padding: 1rem 1.1rem;
  border-radius: 1rem;
  background: var(--color-surface-soft, rgba(15, 23, 42, 0.45));
}

.feedback-error,
.form-error {
  color: #fda4af;
}

.feedback-success {
  color: #86efac;
}

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
  color: var(--color-text-muted, #94a3b8);
  font-size: 0.85rem;
  font-weight: 600;
  white-space: nowrap;
}

.badge {
  display: inline-flex;
  align-items: center;
  border-radius: 999px;
  padding: 0.35rem 0.65rem;
  font-size: 0.75rem;
  font-weight: 600;
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

.muted {
  color: var(--color-text-muted, #94a3b8);
}

.release-link {
  color: inherit;
  text-decoration: none;
  border-bottom: 1px solid rgba(148, 163, 184, 0.28);
}

.release-link:hover {
  color: #fde68a;
}

.release-workspace-link {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 0.4rem 0.75rem;
  border-radius: 999px;
  text-decoration: none;
  background: rgba(59, 130, 246, 0.14);
  color: #bfdbfe;
  font-weight: 600;
  white-space: nowrap;
}

.release-workspace-link:hover {
  background: rgba(59, 130, 246, 0.24);
  color: #eff6ff;
}

.release-workflow-grid {
  display: grid;
  gap: 0.9rem;
}

.release-form {
  margin-bottom: 1rem;
}

.release-workflow-card {
  display: grid;
  gap: 0.85rem;
  padding: 1rem;
  border-radius: 1rem;
  border: 1px solid rgba(148, 163, 184, 0.18);
  background: rgba(15, 23, 42, 0.28);
}

.release-workflow-head {
  display: flex;
  justify-content: space-between;
  gap: 1rem;
  align-items: flex-start;
}

.release-workflow-version {
  margin: 0;
  font-size: 1rem;
  font-weight: 700;
}

.release-workflow-meta {
  display: flex;
  gap: 1rem;
  flex-wrap: wrap;
  color: var(--color-text-muted, #94a3b8);
  font-size: 0.92rem;
}

.release-workspace-link-prominent {
  justify-self: flex-start;
}

@media (max-width: 1100px) {
  .workspace {
    grid-template-columns: 1fr;
  }

  .side-column {
    position: static;
  }
}

@media (max-width: 800px) {
  .stats-grid,
  .info-grid,
  .edit-grid {
    grid-template-columns: 1fr;
  }

  .info-item-span-2,
  .field-span-2 {
    grid-column: span 1;
  }
}
</style>
