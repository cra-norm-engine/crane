<!--
  CRANE — CRA Norm Engine
  Copyright (C) 2026 Ali Mohammad Hosseini
  SPDX-License-Identifier: AGPL-3.0-or-later
  This file is part of CRANE, free software under the GNU AGPL v3.0 or later.
  See <https://www.gnu.org/licenses/>.
-->
<template>
  <!--
    ReleaseReportView — interactive in-app CRA compliance dossier for one release.

    Renders the same data that backs the PDF export (GET …/report/data) as a
    17-section document with a sticky sidebar table of contents + scrollspy.
    Fields CRANE does not model yet show a "Not recorded in CRANE" placeholder.
  -->
  <section class="rpt-page">
    <div v-if="isLoading && !report" class="rpt-loading">Loading compliance report…</div>

    <template v-else-if="report">
      <div class="rpt-shell">
        <!-- Sidebar TOC -->
        <nav class="rpt-nav">
          <div class="rpt-nav-brand">
            <div class="rpt-nav-mark">CRANE · CRA Norm Engine</div>
            <div class="rpt-nav-name">Compliance Report</div>
            <div class="rpt-nav-tag">{{ report.product.name }} · {{ report.product.firmware_version }}</div>
          </div>
          <ul class="rpt-toc">
            <template v-for="item in SECTIONS" :key="item.id">
              <li v-if="item.group" class="rpt-toc-group">{{ item.label }}</li>
              <li v-else>
                <a :href="`#${item.id}`" :class="{ active: activeId === item.id }">
                  <span class="rpt-toc-num">{{ item.num }}</span>{{ item.label }}
                </a>
              </li>
            </template>
          </ul>
        </nav>

        <!-- Document -->
        <div class="rpt-doc">
          <!-- Header / actions -->
          <header class="rpt-head">
            <div>
              <div class="rpt-eyebrow">Cyber Resilience Act · Single-Product Compliance Report</div>
              <h1 class="rpt-title">{{ report.product.name }} <span class="muted">{{ disp(report.product.model) }}</span></h1>
              <div class="rpt-meta">
                Manufacturer <b>{{ disp(report.operators.manufacturer.name) }}</b> ·
                {{ report.meta.generated_at }} · {{ disp(report.meta.generated_by) }}
              </div>
            </div>
            <div class="rpt-actions">
              <span class="rpt-stamp">{{ report.meta.status }}</span>
              <AppButton variant="secondary" size="sm" :disabled="busy" @click="exportPdf">
                {{ busy ? "Generating…" : "Export PDF" }}
              </AppButton>
            </div>
          </header>

          <!-- Coverage meter -->
          <div class="rpt-meter-block">
            <div class="rpt-meter-label">
              <span>Annex I requirement coverage — {{ report.coverage.total }} requirements assessed</span>
            </div>
            <div v-if="report.coverage.available" class="rpt-meter">
              <span v-if="report.coverage.pct.compliant" class="seg seg-ok" :style="segW('compliant')"></span>
              <span v-if="report.coverage.pct.partial" class="seg seg-warn" :style="segW('partial')"></span>
              <span v-if="report.coverage.pct.gap" class="seg seg-bad" :style="segW('gap')"></span>
              <span v-if="report.coverage.pct.na" class="seg seg-na" :style="segW('na')"></span>
            </div>
            <div v-else class="muted sm">No Annex I requirement mappings recorded yet.</div>
            <div class="rpt-legend">
              <span><i class="dot dot-ok"></i>Compliant ({{ report.coverage.counts.compliant || 0 }})</span>
              <span><i class="dot dot-warn"></i>Partial ({{ report.coverage.counts.partial || 0 }})</span>
              <span><i class="dot dot-bad"></i>Gap ({{ report.coverage.counts.gap || 0 }})</span>
              <span><i class="dot dot-na"></i>N/A ({{ report.coverage.counts.na || 0 }})</span>
            </div>
          </div>

          <!-- 00 Document control -->
          <section id="doc-control" class="rpt-sec">
            <div class="rpt-sec-eyebrow">00 · Front matter</div>
            <h2>Document control</h2>
            <p class="rpt-intro">Identifies this specific report export — its id, version, and the moment
            its data was snapshotted — so reviewers can tell which export they are looking at and whether
            it is current.</p>
            <KvTable :rows="docControlRows" />
          </section>

          <!-- 01 Product identification -->
          <section id="product-id" class="rpt-sec">
            <div class="rpt-sec-eyebrow">01 · Scope &amp; identity — Art. 2–3</div>
            <h2>Product identification</h2>
            <p class="rpt-intro">Identifies the product and release covered by this report, including the
            versions in scope and whether it qualifies as a CRA "product with digital elements" under
            Art. 2–3.</p>
            <KvTable :rows="productRows" />

            <template v-if="report.remote_processing.available">
              <h3 class="rpt-subhead">Remote processing solutions</h3>
              <p class="rpt-intro">Each remote data-processing solution the product relies on, with the
              classification decision under Art. 3(2) and the rationale recorded for that decision.</p>
              <table class="rpt-table">
                <thead><tr><th>Solution</th><th>Provider</th><th>Data processed</th><th>Classification</th></tr></thead>
                <tbody>
                  <tr v-for="(r, i) in report.remote_processing.items" :key="i">
                    <td>
                      <strong>{{ r.name }}</strong>
                      <div class="muted sm">Location: {{ r.location }} · Criticality: {{ r.criticality }} · Necessary: {{ r.necessary }} · Bidirectional: {{ r.bidirectional }}</div>
                    </td>
                    <td>{{ r.provider }}</td>
                    <td class="muted sm">{{ r.data_processed }}</td>
                    <td>
                      <StatusBadge :label="r.classification" :variant="riskVariant(r.classification_bucket)" />
                      <div class="muted sm">{{ r.rationale }}</div>
                    </td>
                  </tr>
                </tbody>
              </table>
            </template>
          </section>

          <!-- 02 Economic operators -->
          <section id="operators" class="rpt-sec">
            <div class="rpt-sec-eyebrow">02 · Scope &amp; identity — Art. 13, 18–23</div>
            <h2>Economic operators</h2>
            <p class="rpt-intro">Lists the economic operators with CRA obligations for this product — the
            manufacturer and, where applicable, an authorised representative, importers, and
            distributors (Art. 13, 18–23) — plus the single point of contact for authorities and users.</p>
            <table class="rpt-table">
              <thead><tr><th>Role</th><th>Entity</th><th>Contact</th></tr></thead>
              <tbody>
                <tr><td><StatusBadge label="Manufacturer" variant="success" /></td>
                  <td><Val :v="report.operators.manufacturer.name" /></td>
                  <td><Val :v="report.operators.manufacturer.contact_email" /></td></tr>
                <tr><td><StatusBadge label="Authorised rep." variant="neutral" /></td><td colspan="2"><Val :v="report.operators.authorised_rep" /></td></tr>
                <tr><td><StatusBadge label="Importer(s)" variant="neutral" /></td><td colspan="2"><Val :v="report.operators.importers" /></td></tr>
                <tr><td><StatusBadge label="Distributor(s)" variant="neutral" /></td><td colspan="2"><Val :v="report.operators.distributors" /></td></tr>
                <tr><td><StatusBadge label="Single point of contact" variant="neutral" /></td><td colspan="2"><Val :v="report.operators.spoc" /></td></tr>
              </tbody>
            </table>
          </section>

          <!-- 03 Classification -->
          <section id="classification" class="rpt-sec">
            <div class="rpt-sec-eyebrow">03 · Scope &amp; identity — Art. 7–8, Annex III/IV</div>
            <h2>Classification</h2>
            <p class="rpt-intro">Records how the product is classified under the CRA's risk tiers and the
            conformity-assessment route that classification drives, with the reasoning behind the
            decision.</p>
            <KvTable :rows="classificationRows" />
          </section>

          <!-- 04 Risk assessment -->
          <section id="risk" class="rpt-sec">
            <div class="rpt-sec-eyebrow">04 · Essential requirements — Art. 13(2)–(4)</div>
            <h2>Cybersecurity risk assessment</h2>
            <p class="rpt-intro">Summarises the cybersecurity risk assessment performed for this release
            under Art. 13(2), the methodology used, and the individual risks identified together with
            their mitigations and residual risk.</p>
            <template v-if="report.risk.available">
              <KvTable :rows="riskRows" />
              <p v-if="report.risk.summary" class="muted">{{ report.risk.summary }}</p>
              <template v-if="report.risk.items && report.risk.items.length">
                <h3 class="rpt-subhead">Risk register</h3>
                <table class="rpt-table">
                  <thead><tr><th>Risk &amp; mitigation</th><th>Likelihood</th><th>Impact</th><th>Inherent</th><th>Residual</th><th>Status</th></tr></thead>
                  <tbody>
                    <tr v-for="(it, i) in report.risk.items" :key="i">
                      <td>
                        <strong>{{ it.title }}</strong>
                        <div class="muted sm">Threat: {{ it.threat }} · Asset: {{ it.asset }}</div>
                        <div class="muted sm">Mitigation: {{ it.mitigation }}</div>
                      </td>
                      <td>{{ it.likelihood }}</td>
                      <td>{{ it.impact }}</td>
                      <td><StatusBadge :label="it.risk_level" :variant="riskVariant(it.risk_bucket)" /></td>
                      <td><StatusBadge v-if="it.residual !== '—'" :label="it.residual" :variant="riskVariant(it.residual_bucket)" /><span v-else>—</span></td>
                      <td>{{ it.status }}</td>
                    </tr>
                  </tbody>
                </table>
              </template>
            </template>
            <p v-else class="muted sm">No risk assessment recorded for this release.</p>
          </section>

          <!-- 05 / 06 Annex I -->
          <section id="annex1-p1" class="rpt-sec">
            <div class="rpt-sec-eyebrow">05 · Essential requirements — Annex I, Part I</div>
            <h2>Product security properties</h2>
            <p class="rpt-intro">The Annex I, Part I essential requirements the product must meet by
            design and default. Each row shows the applicability decision and rationale, the
            implementation status, and any artifacts evidencing fulfilment.</p>
            <AnnexTable :rows="report.annex_part1" />
          </section>
          <section id="annex1-p2" class="rpt-sec">
            <div class="rpt-sec-eyebrow">06 · Essential requirements — Annex I, Part II</div>
            <h2>Vulnerability handling processes</h2>
            <p class="rpt-intro">The Annex I, Part II requirements covering the manufacturer's
            vulnerability-handling processes across the product's lifecycle. As above, each row records
            applicability, rationale, and supporting evidence.</p>
            <AnnexTable :rows="report.annex_part2" />
          </section>

          <!-- 07 SBOM -->
          <section id="sbom" class="rpt-sec">
            <div class="rpt-sec-eyebrow">07 · Annex I, Part II(1)</div>
            <h2>Software bill of materials</h2>
            <p class="rpt-intro">The machine-readable inventory of software components in this release,
            plus any known vulnerabilities matched against those components and their current fix
            status.</p>
            <template v-if="report.sbom.available">
              <KvTable :rows="sbomRows" />
              <template v-if="report.sbom.findings?.length">
                <h3 class="rpt-subhead">Top components &amp; known issues</h3>
                <table class="rpt-table">
                  <thead><tr><th>Component</th><th>Vuln ID</th><th>Severity</th><th>CVSS</th><th>Fix status</th></tr></thead>
                  <tbody>
                    <tr v-for="(f, i) in report.sbom.findings" :key="i">
                      <td>
                        <strong>{{ f.component }}</strong> <span class="muted sm">{{ f.version }}</span>
                        <div class="muted sm">{{ f.summary }}</div>
                      </td>
                      <td><code class="cite">{{ f.vuln_id }}</code></td>
                      <td><StatusBadge :label="f.severity" :variant="riskVariant(f.severity_bucket)" /></td>
                      <td>{{ f.cvss_score ?? "—" }}</td>
                      <td>{{ f.fix_status }}</td>
                    </tr>
                  </tbody>
                </table>
              </template>
            </template>
            <p v-else class="muted sm">No SBOM recorded for this release.</p>
          </section>

          <!-- 08 Vulnerability -->
          <section id="vuln" class="rpt-sec">
            <div class="rpt-sec-eyebrow">08 · PSIRT</div>
            <h2>Vulnerability &amp; incident management <span class="muted sm">— summary</span></h2>
            <p class="rpt-intro">Summary only — the full vulnerability register is maintained in-platform.
            Tracks open and resolved vulnerabilities, mean time to remediate, and the known-exploitable
            vulnerability (KEV) flag that blocks placing on market.</p>
            <div class="rpt-cards">
              <div class="card-n"><div class="n bad">{{ report.vuln.open_critical }}</div><div class="l">Open critical</div></div>
              <div class="card-n"><div class="n warn">{{ report.vuln.open_high }}</div><div class="l">Open high</div></div>
              <div class="card-n"><div class="n ok">{{ report.vuln.resolved_count }}</div><div class="l">Resolved</div></div>
              <div class="card-n"><div class="n">{{ report.vuln.mttr }}</div><div class="l">MTTR</div></div>
            </div>
            <table v-if="report.vuln.top.length" class="rpt-table">
              <thead><tr><th>ID</th><th>Title</th><th>Severity</th><th>VEX</th></tr></thead>
              <tbody>
                <tr v-for="(t, i) in report.vuln.top" :key="i">
                  <td><code class="cite">{{ t.cve }}</code></td><td>{{ t.title }}</td><td>{{ t.severity }}</td><td>{{ t.vex }}</td>
                </tr>
              </tbody>
            </table>
            <div class="rpt-note" :class="{ gap: report.vuln.kev_flag }">
              Known exploitable vulnerability flag:
              <b>{{ report.vuln.kev_flag ? "SET — blocks placing on market" : "not set" }}</b>.
            </div>
          </section>

          <!-- 09 Conformity -->
          <section id="conformity" class="rpt-sec">
            <div class="rpt-sec-eyebrow">09 · Conformity — Art. 32</div>
            <h2>Conformity assessment route</h2>
            <p class="rpt-intro">The conformity-assessment module chosen for this product under Art. 32,
            the harmonised standards relied on, and any certifications already on record.</p>
            <KvTable :rows="conformityRows" />
            <table v-if="report.conformity.certifications.length" class="rpt-table">
              <thead><tr><th>Scheme</th><th>Body</th><th>Certificate</th><th>Status</th><th>Valid until</th></tr></thead>
              <tbody>
                <tr v-for="(c, i) in report.conformity.certifications" :key="i">
                  <td><Val :v="c.scheme" /></td><td><Val :v="c.body" /></td><td><Val :v="c.number" /></td>
                  <td><Val :v="c.status" /></td><td>{{ c.valid_until }}</td>
                </tr>
              </tbody>
            </table>
          </section>

          <!-- 10 DoC & CE -->
          <section id="doc-ce" class="rpt-sec">
            <div class="rpt-sec-eyebrow">10 · Conformity — Art. 28–30, Annex V</div>
            <h2>EU declaration of conformity &amp; CE marking</h2>
            <p class="rpt-intro">The EU Declaration of Conformity drawn up for this release — its
            reference, signatory, and publication status — and the CE-marking information affixed to the
            product or its packaging.</p>
            <KvTable :rows="docRows" />
          </section>

          <!-- 11 Tech doc index -->
          <section id="tech-doc" class="rpt-sec">
            <div class="rpt-sec-eyebrow">11 · Conformity — Art. 31, Annex VII</div>
            <h2>Technical documentation index</h2>
            <p class="rpt-intro">Checks the technical documentation file against its required elements —
            product description, design/development records, risk assessment, support-period rationale,
            standards applied, test reports, the DoC, and the SBOM — and whether each is present in
            CRANE.</p>
            <ul class="rpt-checklist">
              <li v-for="t in report.techdoc" :key="t.n">
                <Ph v-if="isPh(t.status)" />
                <StatusBadge v-else :label="t.status" :variant="techVariant(t.status)" />
                ({{ t.n }}) {{ t.name }}
              </li>
            </ul>
            <template v-if="report.evidence.available">
              <h3 class="rpt-subhead">Evidence integrity &amp; retention</h3>
              <KvTable :rows="evidenceRows" />
              <div class="rpt-note">Each retained file is stored with a SHA-256 checksum and re-verified on download; external links are not retained by CRANE.</div>
            </template>
          </section>

          <!-- 12 User info -->
          <section id="user-info" class="rpt-sec">
            <div class="rpt-sec-eyebrow">12 · Conformity — Annex II</div>
            <h2>Information &amp; instructions to the user</h2>
            <p class="rpt-intro">The Annex II checklist of information that must be supplied to the user
            alongside the product — manufacturer identity, intended use, known risks, security-update
            mechanism, and how to report vulnerabilities — together with where each item is published or
            delivered.</p>
            <table v-if="report.user_info.available" class="rpt-table">
              <thead><tr><th>Ref</th><th>Required content</th><th>Status</th><th>Location</th></tr></thead>
              <tbody>
                <tr v-for="(it, i) in report.user_info.items" :key="i">
                  <td><code class="cite">{{ it.ref }}</code></td>
                  <td>{{ it.content }}</td>
                  <td><StatusBadge :label="it.status" :variant="it.status === 'Present' ? 'success' : 'warning'" /></td>
                  <td class="muted">{{ it.location }}</td>
                </tr>
              </tbody>
            </table>
            <div v-else class="rpt-note todo"><Ph /> — no Annex II content checklist recorded for this product yet.</div>
          </section>

          <!-- 13 Support -->
          <section id="support" class="rpt-sec">
            <div class="rpt-sec-eyebrow">13 · Lifecycle — Art. 13(8)</div>
            <h2>Support period &amp; lifecycle</h2>
            <p class="rpt-intro">The support period committed to under Art. 13(8) — how long security
            updates will be provided and the justification for that duration — plus how users are
            notified before support ends.</p>
            <KvTable v-if="report.support.available" :rows="supportRows" />
            <p v-else class="muted sm">No support period recorded.</p>
          </section>

          <!-- 14 Substantial modifications -->
          <section id="mods" class="rpt-sec">
            <div class="rpt-sec-eyebrow">14 · Lifecycle — Art. 3(30)</div>
            <h2>Substantial modifications log</h2>
            <p class="rpt-intro">Tracks every change assessed against the CRA's "substantial
            modification" test — a change is substantial when it affects compliance with the essential
            requirements or changes the product's intended purpose, which can trigger re-assessment of
            conformity.</p>
            <table v-if="report.mods.length" class="rpt-table">
              <thead><tr><th>Date</th><th>Change</th><th>Type</th><th>Outcome</th></tr></thead>
              <tbody>
                <tr v-for="(m, i) in report.mods" :key="i">
                  <td>{{ m.date }}</td><td>{{ m.description }}</td><td>{{ m.type }}</td>
                  <td><StatusBadge :label="m.outcome" :variant="m.substantial ? 'danger' : 'neutral'" /></td>
                </tr>
              </tbody>
            </table>
            <p v-else class="muted sm">No changes recorded against this release.</p>
          </section>

          <!-- 15 CVD -->
          <section id="cvd" class="rpt-sec">
            <div class="rpt-sec-eyebrow">15 · Lifecycle — Art. 14–15</div>
            <h2>CVD &amp; reporting readiness</h2>
            <p class="rpt-intro">The manufacturer's coordinated vulnerability disclosure (CVD) policy
            under Art. 14 — scope, safe-harbor commitment, response SLAs, and reporting channels — and
            the product's readiness to meet the mandatory 24-hour/72-hour/14-day exploitation and
            incident reporting timers.</p>
            <KvTable :rows="cvdRows" />
          </section>

          <!-- 16 Audit -->
          <section id="audit" class="rpt-sec">
            <div class="rpt-sec-eyebrow">16 · Assurance</div>
            <h2>Audit trail (recent activity)</h2>
            <p class="rpt-intro">CRANE's audit log is append-only and hash-chained; this is a recent
            excerpt of activity for this product/release.</p>
            <table v-if="report.audit.length" class="rpt-table">
              <thead><tr><th>Timestamp</th><th>Actor</th><th>Action</th></tr></thead>
              <tbody>
                <tr v-for="(a, i) in report.audit" :key="i"><td class="mono">{{ a.at }}</td><td>{{ a.actor }}</td><td>{{ a.action }}</td></tr>
              </tbody>
            </table>
            <p v-else class="muted sm">No audit events recorded for this product/release.</p>
          </section>

          <!-- 17 Sign-off -->
          <section id="signoff" class="rpt-sec">
            <div class="rpt-sec-eyebrow">17 · Assurance</div>
            <h2>Sign-off &amp; approval</h2>
            <p class="rpt-intro">Who approved this release for the market and when, as the final
            checkpoint before placing the product on the market under this conformity record.</p>
            <KvTable :rows="signoffRows" />
            <div class="rpt-note">Multi-role formal sign-off needs a data model CRANE does not have yet; the release-gate approver above is what is recorded today.</div>
          </section>

          <div class="rpt-foot">{{ report.meta.report_id }} · {{ report.meta.confidentiality }} · not legal advice</div>
        </div>
      </div>
    </template>
  </section>
</template>

<script setup lang="ts">
import { computed, h, onMounted, onUnmounted, ref } from "vue";
import type { FunctionalComponent } from "vue";

import AppButton from "@/components/AppButton.vue";
import StatusBadge from "@/components/StatusBadge.vue";
import type { BadgeVariant } from "@/components/StatusBadge.vue";
import { useAsyncState } from "@/composables/useAsyncState";
import { useToast } from "@/composables/useToast";
import { releaseGateService } from "@/services/release-gate-service";
import { REPORT_PLACEHOLDER, type AnnexRow, type Maybe, type ReleaseReport } from "@/types/report";

const props = defineProps<{ releaseId: string }>();

// ── State ─────────────────────────────────────────────────────────────────────
const { isLoading, execute } = useAsyncState();
const { showToast } = useToast();
const report = ref<ReleaseReport | null>(null);
const busy = ref(false);
const activeId = ref("doc-control");

onMounted(async () => {
  report.value = await execute(() => releaseGateService.getReportData(props.releaseId));
  window.addEventListener("scroll", onScroll, { passive: true });
});
onUnmounted(() => window.removeEventListener("scroll", onScroll));

// ── Sidebar table of contents (section order matches the PDF) ──────────────────
interface TocItem { id?: string; num?: string; label: string; group?: boolean }
const SECTIONS: TocItem[] = [
  { group: true, label: "Scope & identity" },
  { id: "doc-control", num: "00", label: "Document control" },
  { id: "product-id", num: "01", label: "Product identification" },
  { id: "operators", num: "02", label: "Economic operators" },
  { id: "classification", num: "03", label: "Classification" },
  { group: true, label: "Essential requirements" },
  { id: "risk", num: "04", label: "Risk assessment" },
  { id: "annex1-p1", num: "05", label: "Annex I · Part I" },
  { id: "annex1-p2", num: "06", label: "Annex I · Part II" },
  { id: "sbom", num: "07", label: "Software bill of materials" },
  { id: "vuln", num: "08", label: "Vulnerability & incident mgmt" },
  { group: true, label: "Conformity" },
  { id: "conformity", num: "09", label: "Conformity assessment route" },
  { id: "doc-ce", num: "10", label: "EU DoC & CE marking" },
  { id: "tech-doc", num: "11", label: "Technical documentation index" },
  { id: "user-info", num: "12", label: "Info & instructions to user" },
  { group: true, label: "Lifecycle" },
  { id: "support", num: "13", label: "Support period & lifecycle" },
  { id: "mods", num: "14", label: "Substantial modifications" },
  { id: "cvd", num: "15", label: "CVD & reporting readiness" },
  { group: true, label: "Assurance" },
  { id: "audit", num: "16", label: "Audit trail" },
  { id: "signoff", num: "17", label: "Sign-off" },
];

function onScroll(): void {
  const ids = SECTIONS.filter((s) => s.id).map((s) => s.id as string);
  const pos = window.scrollY + 140;
  let active = ids[0];
  for (const id of ids) {
    const el = document.getElementById(id);
    if (el && el.offsetTop <= pos) active = id;
  }
  activeId.value = active;
}

// ── Helpers ───────────────────────────────────────────────────────────────────
function isPh(x: unknown): boolean {
  return x === REPORT_PLACEHOLDER || x === null || x === undefined || x === "";
}
function disp(x: Maybe): string {
  return isPh(x) ? "Not recorded in CRANE" : (x as string);
}
function segW(bucket: string) {
  return { width: `${report.value?.coverage.pct[bucket] ?? 0}%` };
}
function techVariant(status: string): BadgeVariant {
  if (status === "Present") return "success";
  if (status === "Missing") return "danger";
  return "warning";
}

// Small presentational helpers rendered as inline functional components.
const Ph: FunctionalComponent = () => h("span", { class: "rpt-ph" }, "Not recorded in CRANE");
const Val: FunctionalComponent<{ v: Maybe }> = (p) =>
  isPh(p.v) ? h(Ph) : h("span", p.v as string);
const KvTable: FunctionalComponent<{ rows: { k: string; v: Maybe }[] }> = (p) =>
  h("table", { class: "rpt-kv" }, [
    h("tbody", p.rows.map((row) =>
      h("tr", [
        h("td", { class: "k" }, row.k),
        h("td", [isPh(row.v) ? h(Ph) : h("span", row.v as string)]),
      ]),
    )),
  ]);
const AnnexTable: FunctionalComponent<{ rows: AnnexRow[] }> = (p) =>
  p.rows.length === 0
    ? h("p", { class: "muted sm" }, "No requirement mappings recorded.")
    : h("table", { class: "rpt-table" }, [
        h("thead", h("tr", [h("th", "Ref"), h("th", "Requirement"), h("th", "Status"), h("th", "Evidence")])),
        h("tbody", p.rows.map((r) =>
          h("tr", [
            h("td", h("code", { class: "cite" }, r.code)),
            h("td", [
              r.title,
              !isPh(r.rationale)
                ? h("div", { class: "muted sm" }, `Applicability: ${r.applicability} — ${r.rationale}`)
                : null,
              r.linked_artifacts.length
                ? h("div", { class: "muted sm" }, `Evidence files: ${r.linked_artifacts.join(", ")}`)
                : null,
            ]),
            h("td", h(StatusBadge, { label: r.status, variant: annexVariant(r.bucket) })),
            h("td", { class: "muted" }, r.evidence),
          ]),
        )),
      ]);

function annexVariant(bucket: string): BadgeVariant {
  if (bucket === "compliant") return "success";
  if (bucket === "partial") return "warning";
  if (bucket === "gap") return "danger";
  return "neutral";
}

function riskVariant(bucket: string): BadgeVariant {
  if (bucket === "bad") return "danger";
  if (bucket === "warn") return "warning";
  if (bucket === "ok") return "success";
  return "neutral";
}

// ── Key/value row sets ─────────────────────────────────────────────────────────
const docControlRows = computed(() => {
  const m = report.value!.meta;
  return [
    { k: "Report ID", v: m.report_id },
    { k: "Report version", v: m.version },
    { k: "Generated at", v: m.generated_at },
    { k: "Generated by", v: m.generated_by },
    { k: "Data snapshot", v: m.data_snapshot_at },
    { k: "Overall status", v: m.status },
  ];
});
const productRows = computed(() => {
  const p = report.value!.product;
  return [
    { k: "Product name", v: p.name },
    { k: "Model / code", v: p.model },
    { k: "Hardware version", v: p.hardware_version },
    { k: "Firmware / version", v: p.firmware_version },
    { k: "Product type", v: p.product_type },
    { k: "Intended use", v: p.intended_use },
    { k: "Embedded (HW+SW)", v: p.is_embedded },
    { k: "Remote data processing in scope?", v: p.remote_processing_in_scope },
  ];
});
const classificationRows = computed(() => {
  const c = report.value!.classification;
  return [
    { k: "Classification", v: c.classification },
    { k: "Critical (Annex IV)?", v: c.is_critical },
    { k: "Scope status", v: c.scope_status },
    { k: "Annex III/IV item", v: c.annex_item },
    { k: "Conformity route", v: c.conformity_route },
    { k: "Rationale", v: c.rationale },
  ];
});
const riskRows = computed(() => {
  const r = report.value!.risk;
  return [
    { k: "Methodology", v: r.methodology ?? null },
    { k: "Status", v: r.status ?? null },
    { k: "Approved by / date", v: `${disp(r.approved_by ?? null)} · ${r.approved_at ?? "—"}` },
    { k: "Risk items modelled", v: String(r.item_count ?? 0) },
  ];
});
const sbomRows = computed(() => {
  const s = report.value!.sbom;
  return [
    { k: "SBOM", v: s.id ?? null },
    { k: "Format", v: s.format ?? null },
    { k: "Component count", v: s.component_count != null ? String(s.component_count) : null },
    { k: "Quality score", v: s.quality_score != null ? `${s.quality_score} / 100` : null },
    { k: "NTIA minimum elements", v: s.ntia_compliant ?? null },
  ];
});
const conformityRows = computed(() => {
  const c = report.value!.conformity;
  return [
    { k: "Route (recorded)", v: c.route },
    { k: "CRA module (A / B+C / H)", v: c.module },
    { k: "Notified body", v: c.notified_body },
    { k: "NB number / type-exam cert", v: c.nb_number },
    { k: "Standards applied", v: c.standards },
  ];
});
const docRows = computed(() => {
  const d = report.value!.doc;
  return [
    { k: "DoC reference no.", v: d.reference_no },
    { k: "DoC date drawn up", v: d.date },
    { k: "Notified body", v: d.notified_body },
    { k: "Signatory", v: d.signatory },
    { k: "Simplified DoC URL", v: d.simplified_url },
    { k: "DoC status", v: d.status },
    { k: "CE marking", v: d.ce_marking },
  ];
});
const supportRows = computed(() => {
  const s = report.value!.support;
  return [
    { k: "Support start", v: s.start ?? null },
    { k: "End of support", v: s.end ?? null },
    { k: "Support type", v: s.type ?? null },
    { k: "Notify before (days)", v: s.notify_before_days != null ? String(s.notify_before_days) : null },
    { k: "Justification", v: s.justification ?? null },
  ];
});
const cvdRows = computed(() => {
  const c = report.value!.cvd;
  return [
    { k: "CVD policy", v: c.policy_status },
    { k: "Reporting contact", v: c.contact },
    { k: "Routing CSIRT (coordinator)", v: c.csirt_coordinator },
    { k: "24h / 72h / 14-day playbook", v: c.playbook_ready ? "Ready" : "Not exercised yet" },
    { k: "Last mandatory notification", v: c.last_notification },
    { k: "Safe harbor for good-faith research", v: c.safe_harbor },
    { k: "Reporter acknowledgement offered", v: c.acknowledgement_offered },
    { k: "Disclosure window", v: c.disclosure_window_days != null ? `${c.disclosure_window_days} days` : null },
    { k: "Response SLA", v: c.response_sla_hours != null ? `${c.response_sla_hours} hours` : null },
    { k: "security.txt", v: c.security_txt_url },
    { k: "PGP key", v: c.pgp_key_url },
    { k: "Bug bounty", v: c.bug_bounty_url },
    { k: "Scope", v: c.scope_description },
    { k: "Out of scope", v: c.out_of_scope_description },
    { k: "Supported versions", v: c.supported_versions },
  ];
});
const evidenceRows = computed(() => {
  const e = report.value!.evidence;
  return [
    { k: "Evidence items", v: `${e.total ?? 0} (${e.retained ?? 0} retained, ${e.external ?? 0} external)` },
    { k: "Integrity verified", v: `${e.verified ?? 0} verified${e.failed ? `, ${e.failed} failed/missing` : ""}` },
    { k: "Earliest retention until", v: e.earliest_retention ?? "—" },
    { k: "Under legal hold", v: String(e.legal_holds ?? 0) },
  ];
});
const signoffRows = computed(() => {
  const s = report.value!.signoff;
  const approver = s.gate_approver
    ? `${disp(s.gate_approver.email)} · ${s.gate_approver.at}`
    : null;
  return [
    { k: "Release-gate approver", v: approver },
    { k: "Compliance lead", v: s.compliance_lead },
    { k: "Notified body reviewer", v: s.notified_body_reviewer },
    { k: "Executive (DoC signatory)", v: s.executive },
  ];
});

// ── Export ──────────────────────────────────────────────────────────────────
async function exportPdf(): Promise<void> {
  busy.value = true;
  try {
    await releaseGateService.downloadReport(props.releaseId);
  } catch {
    showToast({ type: "error", message: "Could not generate the PDF report." });
  } finally {
    busy.value = false;
  }
}
</script>

<style scoped>
.rpt-page { --rpt-accent: var(--color-primary); }
.rpt-loading { padding: 3rem; color: var(--color-text-muted); }
.muted { color: var(--color-text-muted); }
.rpt-intro { color: var(--color-text-muted); font-size: var(--text-sm); margin: 4px 0 14px; }
.sm { font-size: var(--text-sm); }
.mono { font-family: var(--font-mono, monospace); }

.rpt-shell { display: grid; grid-template-columns: 260px 1fr; gap: 28px; align-items: start; }

/* Sidebar */
.rpt-nav { position: sticky; top: 1rem; align-self: start; border: 1px solid var(--color-border); border-radius: var(--radius-lg); background: var(--color-inset-surface); padding: 14px; max-height: calc(100vh - 2rem); overflow-y: auto; }
.rpt-nav-brand { padding-bottom: 12px; border-bottom: 1px solid var(--color-border); margin-bottom: 8px; }
.rpt-nav-mark { font-family: var(--font-mono, monospace); font-size: 10px; letter-spacing: 0.12em; text-transform: uppercase; color: var(--color-primary); }
.rpt-nav-name { font-weight: 800; font-size: 1.05rem; color: var(--color-text); margin-top: 2px; }
.rpt-nav-tag { font-size: 0.78rem; color: var(--color-text-muted); }
.rpt-toc { list-style: none; margin: 0; padding: 0; }
.rpt-toc-group { font-family: var(--font-mono, monospace); font-size: 9.5px; letter-spacing: 0.1em; text-transform: uppercase; color: var(--color-text-muted); padding: 12px 6px 4px; }
.rpt-toc a { display: flex; gap: 8px; padding: 5px 8px; border-radius: var(--radius-md, 7px); text-decoration: none; color: var(--color-text); font-size: 12.5px; }
.rpt-toc a:hover { background: var(--color-surface-elevated); }
.rpt-toc a.active { background: var(--color-success-bg); color: var(--color-text); font-weight: 700; }
.rpt-toc-num { font-family: var(--font-mono, monospace); font-size: 11px; color: var(--color-text-muted); min-width: 18px; }

/* Document */
.rpt-doc { min-width: 0; }
.rpt-head { display: flex; justify-content: space-between; gap: 1.5rem; flex-wrap: wrap; padding-bottom: 18px; border-bottom: 1px solid var(--color-border); margin-bottom: 22px; }
.rpt-eyebrow { font-family: var(--font-mono, monospace); font-size: 10.5px; letter-spacing: 0.12em; text-transform: uppercase; color: var(--color-primary); }
.rpt-title { margin: 6px 0 6px; font-size: 1.8rem; font-weight: 800; color: var(--color-text); }
.rpt-meta { font-size: 0.85rem; color: var(--color-text-muted); }
.rpt-actions { display: flex; align-items: center; gap: 12px; }
.rpt-stamp { font-family: var(--font-mono, monospace); font-size: 11px; text-transform: uppercase; letter-spacing: 0.05em; color: var(--color-warning); border: 1px solid var(--color-warning); border-radius: 6px; padding: 5px 10px; }

/* Coverage meter */
.rpt-meter-block { margin-bottom: 30px; }
.rpt-meter-label { font-family: var(--font-mono, monospace); font-size: 11px; color: var(--color-text-muted); margin-bottom: 6px; }
.rpt-meter { display: flex; height: 13px; border-radius: 7px; overflow: hidden; border: 1px solid var(--color-border); }
.rpt-meter .seg { height: 100%; }
.seg-ok { background: var(--color-success); } .seg-warn { background: var(--color-warning); } .seg-bad { background: var(--color-danger); } .seg-na { background: var(--color-border-strong); }
.rpt-legend { display: flex; gap: 16px; margin-top: 8px; font-size: 12px; color: var(--color-text-muted); flex-wrap: wrap; }
.rpt-legend .dot { display: inline-block; width: 8px; height: 8px; border-radius: 50%; margin-right: 5px; }
.dot-ok { background: var(--color-success); } .dot-warn { background: var(--color-warning); } .dot-bad { background: var(--color-danger); } .dot-na { background: var(--color-border-strong); }

/* Sections */
.rpt-sec { padding-top: 26px; margin-top: 12px; border-top: 1px solid var(--color-border); scroll-margin-top: 90px; }
.rpt-sec-eyebrow { font-family: var(--font-mono, monospace); font-size: 10.5px; letter-spacing: 0.12em; text-transform: uppercase; color: var(--color-text-muted); margin-bottom: 4px; }
.rpt-sec h2 { margin: 0 0 12px; font-size: 1.25rem; font-weight: 800; color: var(--color-text); }
.rpt-subhead { margin: 18px 0 6px; font-size: 1rem; font-weight: 700; color: var(--color-text); }

/* Tables (rendered by KvTable / AnnexTable too) */
:deep(.rpt-kv) { width: 100%; border-collapse: collapse; margin: 6px 0 8px; }
:deep(.rpt-kv td) { padding: 8px 12px; border: 1px solid var(--color-border); vertical-align: top; font-size: 0.9rem; }
:deep(.rpt-kv td.k) { width: 32%; background: var(--color-inset-surface); color: var(--color-text-muted); font-family: var(--font-mono, monospace); font-size: 0.72rem; text-transform: uppercase; letter-spacing: 0.04em; }
.rpt-table, :deep(.rpt-table) { width: 100%; border-collapse: collapse; font-size: 0.85rem; margin: 6px 0 10px; }
.rpt-table th, :deep(.rpt-table th) { text-align: left; font-family: var(--font-mono, monospace); font-size: 0.68rem; letter-spacing: 0.05em; text-transform: uppercase; color: var(--color-text-muted); border-bottom: 1px solid var(--color-border); padding: 7px 9px; font-weight: 500; }
.rpt-table td, :deep(.rpt-table td) { padding: 8px 9px; border-bottom: 1px solid var(--color-border); vertical-align: top; }
.cite, :deep(.cite) { font-family: var(--font-mono, monospace); font-size: 0.78rem; color: var(--color-text); background: var(--color-surface-elevated); padding: 1px 6px; border-radius: 4px; }

.rpt-ph, :deep(.rpt-ph) { font-family: var(--font-mono, monospace); font-size: 0.74rem; color: var(--color-warning); background: var(--color-warning-bg); border: 1px dashed var(--color-warning-border); border-radius: 4px; padding: 1px 7px; }

.rpt-cards { display: grid; grid-template-columns: repeat(4, 1fr); gap: 10px; margin: 8px 0 12px; }
.card-n { border: 1px solid var(--color-border); border-radius: var(--radius-md, 8px); text-align: center; padding: 14px 8px; }
.card-n .n { font-size: 1.5rem; font-weight: 800; color: var(--color-text); }
.card-n .n.bad { color: var(--color-danger); } .card-n .n.warn { color: var(--color-warning); } .card-n .n.ok { color: var(--color-success); }
.card-n .l { font-family: var(--font-mono, monospace); font-size: 0.62rem; text-transform: uppercase; letter-spacing: 0.05em; color: var(--color-text-muted); margin-top: 5px; }

.rpt-checklist { list-style: none; padding: 0; margin: 0; }
.rpt-checklist li { display: flex; align-items: center; gap: 10px; padding: 8px 0; border-bottom: 1px solid var(--color-border); font-size: 0.9rem; }

.rpt-note { background: var(--color-inset-surface); border-left: 3px solid var(--color-primary); padding: 10px 14px; font-size: 0.85rem; color: var(--color-text-muted); border-radius: 0 var(--radius-md) var(--radius-md) 0; margin: 12px 0; }
.rpt-note.gap { border-left-color: var(--color-danger); }
.rpt-note.todo { border-left-color: var(--color-warning); background: var(--color-warning-bg); }

.rpt-foot { margin-top: 40px; padding-top: 16px; border-top: 1px solid var(--color-border); font-family: var(--font-mono, monospace); font-size: 0.7rem; color: var(--color-text-muted); }

@media (max-width: 900px) {
  .rpt-shell { grid-template-columns: 1fr; }
  .rpt-nav { position: static; max-height: none; }
  .rpt-cards { grid-template-columns: repeat(2, 1fr); }
}
</style>
