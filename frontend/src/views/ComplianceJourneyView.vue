<!--
  CRANE — CRA Norm Engine
  Copyright (C) 2026 Ali Mohammad Hosseini
  SPDX-License-Identifier: AGPL-3.0-or-later
  This file is part of CRANE, free software under the GNU AGPL v3.0 or later.
  See <https://www.gnu.org/licenses/>.
-->
<template>
  <!--
    ComplianceJourneyView — "Guided focus", single product + release at a time.

    A product and release must be selected (there is no all-products overview).
    Left: a phase rail with every step visible and clickable; clicking a step
    previews it in the focus card on the right. The focus card's button is what
    navigates to the exact target screen. Soft guidance — nothing blocks.
  -->
  <section class="page cj-page">
    <header class="cj-top">
      <div>
        <h1 class="cj-h1">Compliance journey</h1>
        <p class="cj-sub">
          One step at a time. Pick a step on the left to see what it involves,
          then use its button to jump to where the work is done.
        </p>
      </div>

      <!-- Product + release selectors (both required) -->
      <div class="cj-filters">
        <div class="field">
          <label class="field-label" for="cj-product">Product</label>
          <select id="cj-product" class="select" v-model="selectedProductId">
            <option v-for="p in products" :key="p.id" :value="p.id">{{ p.name }}</option>
          </select>
        </div>
        <div class="field">
          <label class="field-label" for="cj-release">Release</label>
          <select
            id="cj-release"
            class="select"
            v-model="selectedReleaseId"
            :disabled="releaseOptions.length === 0"
          >
            <option v-if="releaseOptions.length === 0" value="">No releases yet</option>
            <option v-for="r in releaseOptions" :key="r.id" :value="r.id">{{ r.label }}</option>
          </select>
        </div>
      </div>
    </header>

    <!-- ── Loading ─────────────────────────────────────────────────────────── -->
    <div v-if="isLoading && !journey" class="cj-skeleton">
      <div class="cj-skeleton-row"></div>
    </div>

    <!-- ── Empty state ─────────────────────────────────────────────────────── -->
    <div v-else-if="!journey" class="card">
      <EmptyState :title="emptyTitle" :description="emptyDescription">
        <template v-if="products.length === 0" #action>
          <RouterLink class="cj-btn primary" :to="{ name: 'products' }">Create a product</RouterLink>
        </template>
      </EmptyState>
    </div>

    <!-- ── Journey ─────────────────────────────────────────────────────────── -->
    <template v-else>
      <!-- Status infographic: identity + compliance donut + legend breakdown -->
      <div class="card cj-status">
        <div class="cj-status-head">
          <div class="cj-ov-id">
            <span class="cj-ov-name">{{ journey.product_name }}</span>
            <span class="cj-ov-version">{{ journey.version }}</span>
            <StatusBadge
              v-if="journey.release_status"
              :label="prettyStatus(journey.release_status)"
              variant="info"
            />
          </div>
          <span class="cj-ov-count">{{ journey.completed_steps }} / {{ journey.total_steps }} steps complete</span>
        </div>

        <div class="cj-status-body">
          <!-- Donut: each segment is a share of the applicable steps -->
          <div class="cj-donut-wrap">
            <svg class="cj-donut" viewBox="0 0 100 100" aria-hidden="true">
              <circle cx="50" cy="50" :r="donut.r" fill="none" stroke="var(--c-surface-3)" stroke-width="13" />
              <circle
                v-for="(seg, i) in donut.segments"
                :key="i"
                cx="50" cy="50" :r="donut.r" fill="none"
                :stroke="seg.color" stroke-width="13"
                :stroke-dasharray="seg.dash"
                :stroke-dashoffset="seg.offset"
                transform="rotate(-90 50 50)"
              />
            </svg>
            <div class="cj-donut-center">
              <span class="cj-donut-pct">{{ progressPct }}%</span>
              <span class="cj-donut-lab">ready</span>
            </div>
          </div>

          <!-- Legend — only statuses that actually apply (count > 0) -->
          <ul class="cj-legend">
            <li v-for="m in legendRows" :key="m.key" class="cj-legend-row">
              <span class="cj-legend-dot" :style="{ background: m.color }"></span>
              <span class="cj-legend-label">{{ m.label }}</span>
              <span class="cj-legend-count">{{ statusCounts[m.key] }}</span>
            </li>
          </ul>
        </div>
      </div>

      <div class="c-grid">
        <!-- LEFT — phase spine, all steps visible & clickable -->
        <div class="c-rail">
          <div
            v-for="phase in phases"
            :key="phase.id"
            class="c-phase"
            :class="{ complete: phase.complete, current: phaseHasSelected(phase) }"
          >
            <div class="c-prow">
              <span class="c-pnum">
                <svg
                  v-if="phase.complete"
                  viewBox="0 0 16 16" width="13" height="13" fill="none"
                  stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"
                ><path d="M3 8.5 6.5 12 13 4.5" /></svg>
                <template v-else>{{ phase.id }}</template>
              </span>
              <span class="c-pname">{{ phase.name }}</span>
              <span class="c-pcount">{{ phase.done }}/{{ phase.total }}</span>
            </div>

            <div class="c-substeps">
              <button
                v-for="step in phase.steps"
                :key="step.id"
                type="button"
                class="c-sub"
                :class="subClass(step)"
                :disabled="step.status === 'not_applicable'"
                @click="selectStep(step)"
              >
                <span class="c-tick">
                  <svg
                    v-if="step.status === 'complete'"
                    viewBox="0 0 16 16" width="10" height="10" fill="none"
                    stroke="currentColor" stroke-width="3.4" stroke-linecap="round" stroke-linejoin="round"
                  ><path d="M3 8.5 6.5 12 13 4.5" /></svg>
                </span>
                {{ step.title }}
              </button>
            </div>
          </div>
        </div>

        <!-- RIGHT — focus on the selected step (fills the column height) -->
        <div class="c-focus" v-if="focusStep">
          <div class="c-ftop">
            <div class="c-kick">
              Step {{ focusNumber }} of {{ journey.total_steps }}
              <template v-if="focusStep.id === journey.next_step_id"> · Your next action</template>
            </div>
            <h2 class="c-ftitle">{{ focusStep.title }}</h2>
            <p class="c-fdesc">{{ focusStep.description }}</p>
            <div class="c-meta">
              <span v-if="craRef(focusStep.id)" class="cj-refchip">CRA {{ craRef(focusStep.id) }}</span>
              <StatusBadge :label="statusLabel(focusStep.status)" :variant="badgeVariant(focusStep.status)" />
              <span class="cj-phasechip">{{ phaseNameOf(focusStep.id) }}</span>
            </div>
          </div>

          <div v-if="whyText(focusStep.id)" class="c-why">
            <div class="lab">Why this matters</div>
            <p>{{ whyText(focusStep.id) }}</p>
          </div>

          <!-- CRA-grounded guidance: what the step requires + FAQs -->
          <div class="c-guide">
            <div v-if="guideFor(focusStep.id).requirements.length" class="c-guide-block">
              <div class="lab">What this step requires</div>
              <ul class="c-reqs">
                <li v-for="(req, i) in guideFor(focusStep.id).requirements" :key="i">
                  <svg class="c-req-ico" viewBox="0 0 16 16" width="13" height="13" fill="none"
                    stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"
                  ><path d="M3 8.5 6.5 12 13 4.5" /></svg>
                  <span>{{ req }}</span>
                </li>
              </ul>
            </div>

            <div v-if="guideFor(focusStep.id).faqs.length" class="c-guide-block">
              <div class="lab">FAQ</div>
              <div v-for="(f, i) in guideFor(focusStep.id).faqs" :key="i" class="c-faq">
                <div class="c-faq-q">{{ f.q }}</div>
                <div class="c-faq-a">{{ f.a }}</div>
              </div>
            </div>

            <p class="c-guide-note">
              Guidance based on Regulation (EU) 2024/2847 (CRA) and its annexes —
              informational, not legal advice.
            </p>
          </div>

          <div class="c-foot">
            <RouterLink class="cj-btn primary" :to="stepTo(focusStep)">
              {{ focusStep.next_action }}
              <svg viewBox="0 0 16 16" width="16" height="16" fill="none"
                stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"
              ><path d="M6 3.5 10.5 8 6 12.5" /></svg>
            </RouterLink>
            <span class="c-foot-hint">Opens {{ destinationLabel(focusStep) }}</span>
          </div>
        </div>

        <!-- Fully complete and nothing selected -->
        <div class="c-focus c-focus--done" v-else>
          <div class="c-ftop">
            <div class="c-kick">Journey complete</div>
            <h2 class="c-ftitle">This release is CRA-ready</h2>
            <p class="c-fdesc">
              Every applicable step is done. Select any step on the left to review or revisit it.
            </p>
          </div>
        </div>
      </div>
    </template>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref, watch } from "vue";
import { RouterLink } from "vue-router";

import EmptyState from "@/components/EmptyState.vue";
import StatusBadge from "@/components/StatusBadge.vue";
import type { BadgeVariant } from "@/components/StatusBadge.vue";
import { useAsyncState } from "@/composables/useAsyncState";
import { dashboardService } from "@/services/dashboard-service";
import { productService } from "@/services/product-service";
import type { JourneyStep, JourneyStepStatus, ReleaseJourney } from "@/types/dashboard";
import type { ProductSummaryRead } from "@/types/product";

// ── Static journey metadata ───────────────────────────────────────────────────
const PHASE_DEFS: { id: number; name: string; stepIds: string[] }[] = [
  { id: 1, name: "Product setup", stepIds: ["remote_processing", "cra_scope", "support_period"] },
  { id: 2, name: "Release preparation", stepIds: ["create_release", "risk_assessment", "annex_mapping"] },
  { id: 3, name: "Evidence & documentation", stepIds: ["artifact_submission", "technical_documentation", "declaration_of_conformity"] },
  { id: 4, name: "Conformity & placement", stepIds: ["approve_release", "placement_date"] },
];

const CRA_REFS: Record<string, string> = {
  remote_processing: "Art. 3(2)",
  cra_scope: "Art. 3",
  support_period: "Art. 13(8)",
  risk_assessment: "Annex I",
  annex_mapping: "Annex I",
  artifact_submission: "Annex VII",
  technical_documentation: "Annex VII",
  declaration_of_conformity: "Art. 28",
  approve_release: "Annex I Pt I §2(a)",
  placement_date: "Art. 3(20)",
};

const WHY_TEXT: Record<string, string> = {
  remote_processing: "Remote data processing can pull an otherwise-exempt product into CRA scope, so it must be identified and classified first.",
  cra_scope: "If the product falls outside CRA scope the journey ends here. If it's in scope, this decision sets every obligation that follows.",
  support_period: "The security support period defines how long you must provide updates — a core CRA obligation customers rely on.",
  create_release: "Conformity is assessed per version placed on the market, so each release carries its own journey.",
  risk_assessment: "The risk assessment drives which Annex I requirements apply and what evidence the release gate will need.",
  annex_mapping: "Mapping each Annex I requirement to a decision and evidence is what demonstrates conformity.",
  artifact_submission: "The release gate only approves once the required evidence is attached and reviewed.",
  technical_documentation: "Technical documentation (Annex VII) must exist and be accepted before the product can be placed on the market.",
  declaration_of_conformity: "The EU Declaration of Conformity is the manufacturer's formal statement that the product meets the CRA.",
  approve_release: "Approval confirms the gate is satisfied and there are no known exploitable vulnerabilities — a hard CRA requirement.",
  placement_date: "Recording the market-placement date anchors the support period and substantial-change obligations.",
};

// Per-step, CRA-grounded guidance shown in the focus card so users can actually
// act on the step. Based on Regulation (EU) 2024/2847 (Cyber Resilience Act),
// its annexes and published guidance/FAQs. Informational — not legal advice.
interface StepGuide {
  requirements: string[];
  faqs: { q: string; a: string }[];
}
const STEP_GUIDE: Record<string, StepGuide> = {
  remote_processing: {
    requirements: [
      "Identify every remote data processing solution the product needs to function — cloud backends, update servers, companion services.",
      "Classify each one: integral remote data processing (in CRA scope) versus an independent third-party service (out of scope).",
      "Record the rationale — remote processing whose absence would stop a product function, and that is under your responsibility, is in scope (Art. 3(2)).",
    ],
    faqs: [
      { q: "Is my cloud backend covered by the CRA?", a: "If the remote data processing is necessary for the product to perform its functions and is provided or under the manufacturer's responsibility, it is treated as part of the product and is in scope." },
      { q: "What about a third-party SaaS we only integrate with?", a: "Independent services not under your responsibility are generally out of scope — but document where the boundary lies." },
    ],
  },
  cra_scope: {
    requirements: [
      "Confirm the product is a 'product with digital elements' made available on the EU market (Art. 2).",
      "Check the exclusions — e.g. medical devices, motor vehicles, aviation and products covered by sector-specific law are carved out.",
      "Determine the class: default, important (Annex III, Class I/II) or critical (Annex IV) — this sets the conformity-assessment route.",
    ],
    faqs: [
      { q: "What if the product is out of scope?", a: "No CRA obligations apply, but keep a documented justification in case authorities ask." },
      { q: "Does open-source software fall under the CRA?", a: "Non-commercial open-source software is generally excluded; obligations target products made available in the course of a commercial activity." },
    ],
  },
  support_period: {
    requirements: [
      "Set a support period during which you provide free security updates (Art. 13(8)).",
      "It must be at least 5 years, unless the product is expected to be in use for a shorter period.",
      "Communicate the end-of-support date clearly to users (Annex II).",
    ],
    faqs: [
      { q: "Can the support period be under 5 years?", a: "Only if the product's expected in-use time is shorter; otherwise five years is the baseline." },
      { q: "What must happen during the support period?", a: "Handle vulnerabilities and distribute security updates free of charge and without undue delay." },
    ],
  },
  create_release: {
    requirements: [
      "Treat each version placed on the market as its own conformity scope.",
      "Record the hardware and/or software versions that make up this release.",
      "Remember a substantial modification creates a 'new' product that needs a fresh conformity assessment.",
    ],
    faqs: [
      { q: "When does a change count as a new product?", a: "When a modification changes the product's original intended function or affects its compliance/risk — i.e. a substantial modification." },
    ],
  },
  risk_assessment: {
    requirements: [
      "Perform a cybersecurity risk assessment and apply it across design, development, production and maintenance (Art. 13(2)).",
      "Use it to decide which Annex I Part I essential requirements apply to this product.",
      "Include the assessment in the technical documentation (Annex VII).",
    ],
    faqs: [
      { q: "Which methodology must I use?", a: "The CRA does not mandate one — recognised methods such as STRIDE or TARA are acceptable, as long as risks are identified and addressed." },
    ],
  },
  annex_mapping: {
    requirements: [
      "Work through the Annex I Part I essential requirements (secure by design and by default, no known exploitable vulnerabilities, secure configuration, data protection, minimal attack surface, etc.).",
      "For each, record applicable / not applicable with a justification and link the supporting evidence.",
      "Base any 'not applicable' decision on the documented risk assessment.",
    ],
    faqs: [
      { q: "Can a requirement be marked not applicable?", a: "Yes, where justified by the risk assessment — but the justification must be documented." },
    ],
  },
  artifact_submission: {
    requirements: [
      "Collect the evidence the release gate needs: risk assessment, test reports, SBOM and secure-development records.",
      "Attach each artifact to its checklist item for review.",
      "This evidence feeds both the technical documentation and the conformity decision.",
    ],
    faqs: [
      { q: "What is an SBOM, and is it required?", a: "A Software Bill of Materials listing the product's components. Annex I Part II requires drawing one up — at least for top-level dependencies — in a commonly used, machine-readable format." },
    ],
  },
  technical_documentation: {
    requirements: [
      "Draw up the technical documentation before placing the product on the market (Annex VII).",
      "Include the product description, design/development information, risk assessment, standards applied, the SBOM, vulnerability-handling processes and the EU DoC.",
      "Keep it for at least 10 years after placing on the market (or the support period, if longer).",
    ],
    faqs: [
      { q: "How long must I keep the documentation?", a: "At least 10 years from placing the product on the market, or the length of the support period if that is longer." },
    ],
  },
  declaration_of_conformity: {
    requirements: [
      "Draw up the EU Declaration of Conformity stating the product meets the essential requirements (Art. 28).",
      "Include the Annex V content: product and manufacturer identity, the conformity statement, standards used and any notified body.",
      "The DoC date must be on or before the placing-on-market date; provide the DoC with the product or as a link.",
    ],
    faqs: [
      { q: "What does drawing up the DoC mean?", a: "By drawing up the EU DoC and affixing CE marking, you take sole responsibility that the product conforms to the CRA." },
    ],
  },
  approve_release: {
    requirements: [
      "Ensure the product has no known exploitable vulnerabilities before it ships (Annex I Part I).",
      "Complete the conformity assessment appropriate to the product class — self-assessment for default products; third-party for important Class II and critical products.",
      "Affix the CE marking before placing the product on the market (Art. 30).",
    ],
    faqs: [
      { q: "A known exploitable vulnerability is still open — can we release?", a: "No. The CRA prohibits making a product available with a known exploitable vulnerability; resolve it first." },
      { q: "Do we always need a notified body?", a: "Not for default products, which use self-assessment. Third-party assessment is required for important Class II and critical products." },
    ],
  },
  placement_date: {
    requirements: [
      "Record the date the product is first made available on the EU market ('placing on the market').",
      "This date starts the support-period and documentation-retention clocks.",
      "Note the CRA deadlines: vulnerability/incident reporting applies from 11 Sep 2026; the full requirements from 11 Dec 2027.",
    ],
    faqs: [
      { q: "What's the difference between 'release' and 'placing on the market'?", a: "Placing on the market is the first making available in the EU; a product may be released internally before its formal EU placement." },
    ],
  },
};

// Friendly destination labels for the focus button hint.
const DEST_LABELS: Record<string, string> = {
  "product-detail": "the product page",
  "release-gate": "the release gate",
  "risk-assessments": "the risk assessments list",
  "risk-assessment-detail": "the risk assessment",
  "annex-matrix": "the Annex I matrix",
  "vulnerability-handling": "PSIRT vulnerability handling",
};

// ── State ─────────────────────────────────────────────────────────────────────
const { isLoading, execute } = useAsyncState();
const products = ref<ProductSummaryRead[]>([]);
const allJourneys = ref<ReleaseJourney[]>([]);
const selectedProductId = ref<string>("");
const selectedReleaseId = ref<string>("");
// Explicit step preview selection (stepId). Defaults to the journey's next step.
const selectedStepId = ref<string>("");

onMounted(async () => {
  products.value = await execute(() => productService.list());
  // No all-products view: auto-select the first product (its watcher loads the rest).
  if (products.value.length > 0) {
    selectedProductId.value = products.value[0].id;
  }
});

// Product change → reload its releases, then auto-select the first release.
watch(selectedProductId, async () => {
  selectedReleaseId.value = "";
  selectedStepId.value = "";
  await loadJourneys();
  const firstRelease = allJourneys.value.find((j) => j.release_id)?.release_id;
  if (firstRelease) selectedReleaseId.value = firstRelease;
});

// Release change → reset the previewed step so the focus shows that release's next step.
watch(selectedReleaseId, () => {
  selectedStepId.value = "";
});

async function loadJourneys(): Promise<void> {
  allJourneys.value = selectedProductId.value
    ? await execute(() => dashboardService.getReleaseJourneys({ productId: selectedProductId.value }))
    : [];
}

// ── Derived ───────────────────────────────────────────────────────────────────
const releaseOptions = computed(() =>
  allJourneys.value
    .filter((j) => j.release_id)
    .map((j) => ({ id: j.release_id as string, label: j.version })),
);

// The single journey shown: the selected release, else the product's only entry.
const journey = computed<ReleaseJourney | undefined>(() => {
  if (selectedReleaseId.value) {
    return allJourneys.value.find((j) => j.release_id === selectedReleaseId.value);
  }
  return allJourneys.value[0];
});

const progressPct = computed(() => {
  const j = journey.value;
  if (!j || j.total_steps === 0) return 0;
  return Math.round((j.completed_steps / j.total_steps) * 100);
});

// ── Compliance status infographic (donut) ─────────────────────────────────────
// Legend rows / segment order and colours (CSS theme colours).
const statusMeta: { key: JourneyStepStatus; label: string; color: string }[] = [
  { key: "complete", label: "Done", color: "var(--color-success)" },
  { key: "in_progress", label: "In progress", color: "var(--color-info)" },
  { key: "blocked", label: "Blocked", color: "var(--color-danger)" },
  { key: "todo", label: "To do", color: "var(--color-warning)" },
  { key: "not_applicable", label: "Not applicable", color: "var(--color-border-strong)" },
];

// Count steps by status for the current journey.
const statusCounts = computed<Record<JourneyStepStatus, number>>(() => {
  const counts = { complete: 0, in_progress: 0, blocked: 0, todo: 0, not_applicable: 0 };
  for (const s of journey.value?.steps ?? []) counts[s.status] += 1;
  return counts;
});

// Only show legend rows for statuses that are actually present.
const legendRows = computed(() => statusMeta.filter((m) => statusCounts.value[m.key] > 0));

// Build donut segments (one arc per status) over the applicable steps.
const donut = computed(() => {
  const r = 42;
  const circumference = 2 * Math.PI * r;
  const total = journey.value?.total_steps ?? 0; // applicable steps (excludes N/A)
  const segments: { color: string; dash: string; offset: number }[] = [];
  let used = 0;
  for (const m of statusMeta) {
    if (m.key === "not_applicable") continue; // N/A is not part of the ring
    const n = statusCounts.value[m.key];
    if (!n || total === 0) continue;
    const len = (n / total) * circumference;
    segments.push({
      color: m.color,
      dash: `${len} ${circumference - len}`,
      offset: -used,
    });
    used += len;
  }
  return { r, segments };
});

const emptyTitle = computed(() => (products.value.length === 0 ? "No products yet" : "No release yet"));
const emptyDescription = computed(() =>
  products.value.length === 0
    ? "Create your first product to start a compliance journey."
    : "This product has no release. Create a release candidate to start its journey.",
);

// ── Selection ─────────────────────────────────────────────────────────────────
function focusId(): string | null {
  return selectedStepId.value || journey.value?.next_step_id || null;
}
const focusStep = computed<JourneyStep | undefined>(() => {
  const id = focusId();
  if (!id || !journey.value) return undefined;
  return journey.value.steps.find((s) => s.id === id);
});
function selectStep(step: JourneyStep): void {
  if (step.status === "not_applicable") return;
  selectedStepId.value = step.id;
}

// ── Phase rail ────────────────────────────────────────────────────────────────
const phases = computed(() => {
  const j = journey.value;
  if (!j) return [];
  const byId = new Map(j.steps.map((s) => [s.id, s]));
  return PHASE_DEFS.map((def) => {
    const steps = def.stepIds.map((id) => byId.get(id)).filter((s): s is JourneyStep => !!s);
    const applicable = steps.filter((s) => s.status !== "not_applicable");
    const done = applicable.filter((s) => s.status === "complete").length;
    const total = applicable.length;
    return { id: def.id, name: def.name, steps, done, total, complete: total > 0 && done === total };
  });
});

function phaseHasSelected(phase: { steps: JourneyStep[] }): boolean {
  const id = focusId();
  return !!id && phase.steps.some((s) => s.id === id);
}
function phaseNameOf(stepId: string): string {
  return PHASE_DEFS.find((p) => p.stepIds.includes(stepId))?.name ?? "";
}
function subClass(step: JourneyStep): string {
  const cls: string[] = [];
  if (step.id === focusId()) cls.push("is-selected");
  if (journey.value && step.id === journey.value.next_step_id) cls.push("is-next");
  if (step.status === "complete") cls.push("is-done");
  if (step.status === "not_applicable") cls.push("is-na");
  return cls.join(" ");
}
const focusNumber = computed(() => {
  const j = journey.value;
  if (!j) return 0;
  const applicable = j.steps.filter((s) => s.status !== "not_applicable");
  return applicable.findIndex((s) => s.id === focusId()) + 1;
});

function craRef(stepId: string): string {
  return CRA_REFS[stepId] ?? "";
}
function whyText(stepId: string): string {
  return WHY_TEXT[stepId] ?? "";
}
function guideFor(stepId: string): StepGuide {
  return STEP_GUIDE[stepId] ?? { requirements: [], faqs: [] };
}
function destinationLabel(step: JourneyStep): string {
  return DEST_LABELS[step.route_name] ?? "the relevant page";
}

// ── Navigation ────────────────────────────────────────────────────────────────
function stepTo(step: JourneyStep) {
  return {
    name: step.route_name,
    params: step.route_params,
    query: step.route_query,
    hash: step.route_hash ?? undefined,
  };
}

// ── Labels ────────────────────────────────────────────────────────────────────
function statusLabel(status: JourneyStepStatus): string {
  switch (status) {
    case "complete": return "Done";
    case "in_progress": return "In progress";
    case "blocked": return "Blocked";
    case "not_applicable": return "N/A";
    default: return "To do";
  }
}
function badgeVariant(status: JourneyStepStatus): BadgeVariant {
  switch (status) {
    case "complete": return "success";
    case "in_progress": return "info";
    case "blocked": return "danger";
    case "not_applicable": return "neutral";
    default: return "warning";
  }
}
function prettyStatus(raw: string): string {
  return raw.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
}
</script>

<style scoped>
.cj-page {
  --c-border: var(--color-border);
  --c-border-2: var(--color-border-strong);
  --c-surface: var(--color-surface);
  --c-surface-2: var(--color-inset-surface);
  --c-surface-3: var(--color-surface-elevated);
  --c-brand: var(--color-primary);
  --c-brand-bg: var(--color-success-bg);
  --c-text: var(--color-text);
  --c-text-2: var(--color-text-muted);
  --c-text-3: var(--color-text-muted);
  --c-amber: var(--color-warning);

  display: flex;
  flex-direction: column;
  gap: 14px;
}

/* ── Top: title + selectors on one row ────────────────── */
.cj-top {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 1rem 2rem;
}
.cj-h1 { margin: 0; font-size: 1.5rem; font-weight: 800; letter-spacing: -0.02em; color: var(--c-text); }
.cj-sub { margin: 0.3rem 0 0; max-width: 60ch; font-size: 0.9rem; color: var(--c-text-2); line-height: 1.5; }

.cj-filters { display: flex; gap: 1rem; flex-wrap: wrap; }
.cj-filters .field { display: flex; flex-direction: column; gap: 0.3rem; min-width: 13rem; }
.field-label { font-size: 0.68rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.03em; color: var(--c-text-3); }

/* ── Status infographic ───────────────────────────────── */
.cj-status { padding: 16px 20px; }
.cj-status-head {
  display: flex; align-items: center; justify-content: space-between;
  flex-wrap: wrap; gap: 0.5rem 1.5rem; padding-bottom: 14px;
  border-bottom: 1px solid var(--c-border); margin-bottom: 16px;
}
.cj-ov-id { display: flex; align-items: center; gap: 0.6rem; min-width: 0; }
.cj-ov-name { font-size: 1.05rem; font-weight: 800; color: var(--c-text); }
.cj-ov-version { font-size: 0.85rem; font-weight: 600; color: var(--c-text-3); }
.cj-ov-count { font-size: 0.75rem; color: var(--c-text-3); white-space: nowrap; }

.cj-status-body { display: flex; align-items: center; gap: 28px; flex-wrap: wrap; }

/* Donut */
.cj-donut-wrap { position: relative; width: 132px; height: 132px; flex: none; }
.cj-donut { width: 132px; height: 132px; transform: rotate(0deg); }
.cj-donut circle { transition: stroke-dasharray 0.4s ease; }
.cj-donut-center {
  position: absolute; inset: 0; display: flex; flex-direction: column;
  align-items: center; justify-content: center; pointer-events: none;
}
.cj-donut-pct { font-size: 1.7rem; font-weight: 800; color: var(--c-text); line-height: 1; }
.cj-donut-lab { font-size: 0.7rem; text-transform: uppercase; letter-spacing: 0.06em; color: var(--c-text-3); margin-top: 3px; }

/* Legend — compact, fixed width so the count stays beside its label */
.cj-legend { list-style: none; margin: 0; padding: 0; display: flex; flex-direction: column; gap: 8px; flex: 0 1 auto; min-width: 13rem; max-width: 16rem; }
.cj-legend-row { display: flex; align-items: center; gap: 10px; font-size: 13px; }
.cj-legend-dot { width: 11px; height: 11px; border-radius: 3px; flex: none; }
.cj-legend-label { color: var(--c-text-2); flex: 1; }
.cj-legend-count { font-weight: 800; color: var(--c-text); font-variant-numeric: tabular-nums; min-width: 1.5rem; text-align: right; }

/* ── Grid (rail + focus, sized to their content) ──────── */
.c-grid { display: grid; grid-template-columns: 340px 1fr; gap: 20px; align-items: start; }

/* ── Left spine ───────────────────────────────────────── */
.c-rail { border: 1px solid var(--c-border); border-radius: 18px; background: var(--c-surface-2); padding: 8px; }
.c-phase { padding: 4px; }
.c-phase + .c-phase { border-top: 1px solid var(--c-border); margin-top: 4px; padding-top: 8px; }
.c-prow { display: flex; align-items: center; gap: 11px; padding: 8px 12px; border-radius: 12px; }
.c-phase.current > .c-prow { background: var(--c-brand-bg); }
.c-pnum {
  width: 24px; height: 24px; border-radius: 8px; flex: none; display: grid; place-items: center;
  font-size: 12px; font-weight: 800; background: var(--c-surface-3); color: var(--c-text-2); border: 1px solid var(--c-border-2);
}
.c-phase.complete .c-pnum { background: var(--c-brand); color: #10250a; border-color: transparent; }
.c-phase.current .c-pnum { background: var(--c-brand-bg); color: var(--c-brand); border-color: var(--c-brand); }
.c-pname { font-size: 13.5px; font-weight: 700; flex: 1; color: var(--c-text); }
.c-phase.current .c-pname { color: var(--c-brand); }
.c-pcount { font-size: 11px; font-weight: 700; color: var(--c-text-3); }

.c-substeps { margin: 2px 0 6px 30px; padding-left: 14px; border-left: 2px solid var(--c-border); display: flex; flex-direction: column; gap: 2px; }
.c-sub {
  display: flex; align-items: center; gap: 9px; padding: 7px 9px; border-radius: 8px;
  font-size: 12.5px; color: var(--c-text-3); text-align: left; width: 100%;
  background: transparent; border: none; font-family: inherit; cursor: pointer;
  transition: background 0.15s ease, color 0.15s ease;
}
.c-sub:not(.is-na):hover { background: var(--c-surface-3); color: var(--c-text); }
.c-sub.is-done { color: var(--c-text-2); }
.c-sub.is-na { opacity: 0.45; cursor: default; }
.c-sub.is-selected { background: var(--c-brand-bg); color: var(--c-text); font-weight: 700; box-shadow: inset 0 0 0 1px var(--c-brand); }
.c-tick { width: 15px; height: 15px; border-radius: 999px; flex: none; display: grid; place-items: center; border: 1.5px solid var(--c-border-2); color: transparent; }
.c-sub.is-done .c-tick { background: var(--c-brand); border-color: var(--c-brand); color: #10250a; }
.c-sub.is-next:not(.is-done) .c-tick { border-color: var(--c-amber); background: var(--c-amber); }

/* ── Right focus card (flex column fills height) ──────── */
.c-focus {
  display: flex; flex-direction: column;
  border: 1px solid var(--c-brand); border-radius: 18px; overflow: hidden;
  background: linear-gradient(160deg, var(--c-surface-3), var(--c-surface));
}
.c-focus--done { border-color: var(--c-border); }
.c-ftop { padding: 26px 28px 22px; }
.c-kick { font-size: 11.5px; font-weight: 800; letter-spacing: 0.1em; text-transform: uppercase; color: var(--c-brand); }
.c-ftitle { margin: 8px 0 0; font-size: 28px; font-weight: 800; letter-spacing: -0.02em; color: var(--c-text); }
.c-fdesc { margin: 14px 0 0; font-size: 15px; color: var(--c-text-2); line-height: 1.65; }
.c-meta { display: flex; gap: 9px; margin-top: 20px; flex-wrap: wrap; align-items: center; }

.c-why { padding: 16px 28px; border-top: 1px solid var(--c-border); background: var(--c-surface-2); }
.c-why .lab { font-size: 11px; font-weight: 800; letter-spacing: 0.08em; text-transform: uppercase; color: var(--c-text-3); margin-bottom: 6px; }
.c-why p { margin: 0; font-size: 13.5px; color: var(--c-text-2); line-height: 1.55; }

/* ── Guidance (CRA requirements + FAQ) ────────────────── */
.c-guide { padding: 18px 28px; border-top: 1px solid var(--c-border); display: flex; flex-direction: column; gap: 18px; }
.c-guide .lab { font-size: 11px; font-weight: 800; letter-spacing: 0.08em; text-transform: uppercase; color: var(--c-text-3); margin-bottom: 10px; }

.c-reqs { list-style: none; margin: 0; padding: 0; display: flex; flex-direction: column; gap: 9px; }
.c-reqs li { display: flex; gap: 9px; font-size: 13.5px; color: var(--c-text-2); line-height: 1.5; }
.c-req-ico { flex: none; margin-top: 3px; color: var(--c-brand); }

.c-faq { padding: 11px 13px; border: 1px solid var(--c-border); border-radius: 10px; background: var(--c-surface-2); }
.c-faq + .c-faq { margin-top: 8px; }
.c-faq-q { font-size: 13px; font-weight: 700; color: var(--c-text); }
.c-faq-a { font-size: 13px; color: var(--c-text-2); line-height: 1.55; margin-top: 4px; }

.c-guide-note { margin: 0; font-size: 11.5px; font-style: italic; color: var(--c-text-3); line-height: 1.5; }

.c-foot { display: flex; align-items: center; gap: 14px; padding: 18px 28px; border-top: 1px solid var(--c-border); }
.c-foot-hint { font-size: 12.5px; color: var(--c-text-3); }

/* ── Chips & buttons ──────────────────────────────────── */
.cj-refchip, .cj-phasechip {
  display: inline-flex; align-items: center; padding: 3px 9px; border-radius: 999px;
  font-size: 11.5px; font-weight: 700; color: var(--c-text-2);
  background: var(--c-surface-3); border: 1px solid var(--c-border);
}
.cj-btn {
  display: inline-flex; align-items: center; gap: 6px; padding: 11px 18px; border-radius: 11px;
  font-size: 14px; font-weight: 700; cursor: pointer; text-decoration: none;
  border: 1px solid var(--c-border); background: var(--c-surface-3); color: var(--c-text); transition: filter 0.15s ease;
}
.cj-btn.primary { background: var(--c-brand); border-color: transparent; color: #10250a; }
.cj-btn:hover { filter: brightness(1.06); }

/* ── Skeleton ─────────────────────────────────────────── */
.cj-skeleton { display: flex; flex-direction: column; gap: 1rem; }
.cj-skeleton-row {
  height: 320px; border-radius: 18px;
  background: linear-gradient(90deg, var(--c-surface-3) 25%, var(--c-surface-2) 50%, var(--c-surface-3) 75%);
  background-size: 200% 100%; animation: cj-shimmer 1.3s ease-in-out infinite;
}
@keyframes cj-shimmer { from { background-position: 200% 0; } to { background-position: -200% 0; } }

/* ── Responsive ───────────────────────────────────────── */
@media (max-width: 860px) {
  .c-grid { grid-template-columns: 1fr; }
}
</style>
