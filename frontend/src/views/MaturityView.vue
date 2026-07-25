<template>
  <section class="page maturity-page">
    <header class="page-header">
      <div>
        <h1 class="page-title">SME maturity</h1>
        <p class="muted page-subtitle">
          Assess organisational cyber-resilience practices using the ENISA SME model.
        </p>
      </div>
      <AppButton v-if="!current" variant="primary" @click="showCreate = true">
        New assessment
      </AppButton>
    </header>

    <template v-if="!current">
      <section class="panel">
        <div class="panel-header">
          <div>
            <h2 class="section-title">Assessments</h2>
            <p class="muted section-subtitle">Track organisational maturity independently from product readiness.</p>
          </div>
          <span class="count-badge">{{ assessments.length }}</span>
        </div>

        <div v-if="isLoading" class="empty-state">Loading assessments…</div>
        <div v-else-if="!assessments.length" class="empty-state">
          <strong>No assessments yet</strong>
          <span>Create an assessment to establish your organisation's maturity baseline.</span>
        </div>
        <div v-else class="table-wrapper">
          <table class="data-table">
            <thead><tr><th>Assessment</th><th>Scope</th><th>Status</th><th>Created</th><th></th></tr></thead>
            <tbody>
              <tr v-for="item in assessments" :key="item.id" class="table-row-link" tabindex="0" @click="open(item.id)" @keydown.enter="open(item.id)">
                <td><strong>{{ item.title }}</strong></td>
                <td class="muted">{{ item.scope }}</td>
                <td><StatusBadge :label="formatLabel(item.status)" :variant="statusVariant(item.status)" /></td>
                <td class="muted nowrap">{{ formatDate(item.created_at) }}</td>
                <td class="row-arrow">›</td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>
    </template>

    <template v-else>
      <div class="detail-toolbar">
        <AppButton variant="ghost" @click="closeAssessment">← All assessments</AppButton>
      </div>

      <section class="panel assessment-header">
        <div class="assessment-heading">
          <div class="heading-badges">
            <StatusBadge :label="formatLabel(current.status)" :variant="statusVariant(current.status)" />
            <span class="model-label">ENISA SME · 2026</span>
          </div>
          <h2>{{ current.title }}</h2>
          <p class="muted">{{ current.scope }}</p>
        </div>
        <div class="header-actions">
          <AppButton v-if="current.status === 'draft'" variant="primary" :disabled="!current.results.complete || isLoading" @click="transition('submit')">
            Submit for review
          </AppButton>
          <AppButton v-if="current.status === 'submitted'" variant="primary" :disabled="isLoading" @click="showApproval = true">
            Review and approve
          </AppButton>
        </div>
      </section>

      <section class="metric-grid" aria-label="Assessment summary">
        <article class="metric-card">
          <span class="metric-label">Completion</span>
          <strong>{{ answeredCount }} / {{ current.catalog.length }}</strong>
          <div class="progress-track"><span :style="{ width: `${completionPercent}%` }" /></div>
        </article>
        <article class="metric-card">
          <span class="metric-label">Overall score</span>
          <strong>{{ current.results.overall_score?.toFixed(2) ?? "—" }}</strong>
          <span class="metric-detail">out of 5.00</span>
        </article>
        <article class="metric-card">
          <span class="metric-label">Profile</span>
          <strong class="capitalize">{{ current.results.profile ?? "Incomplete" }}</strong>
          <span class="metric-detail">Organisational maturity</span>
        </article>
        <article class="metric-card">
          <span class="metric-label">Evidence coverage</span>
          <strong>{{ current.results.evidence_coverage }}%</strong>
          <span class="metric-detail">Answers with linked records</span>
        </article>
      </section>

      <div class="notice" role="note">
        <svg viewBox="0 0 20 20" aria-hidden="true"><path d="M10 2a8 8 0 1 0 0 16 8 8 0 0 0 0-16zm-1 4h2v5H9zm0 6h2v2H9z" fill="currentColor"/></svg>
        <span>{{ current.results.disclaimer }}</span>
      </div>

      <nav class="tab-bar" aria-label="Maturity assessment sections">
        <button v-for="name in tabs" :key="name" :class="{ active: tab === name }" @click="tab = name">
          {{ name }}
          <span v-if="name === 'Improvement plan' && current.actions.length" class="tab-count">{{ current.actions.length }}</span>
        </button>
      </nav>

      <section v-if="tab === 'Assessment'" class="assessment-workspace">
        <aside class="domain-nav panel" aria-label="Assessment domains">
          <div class="domain-nav-header">
            <span class="field-label">Domains</span>
            <span class="muted">{{ completionPercent }}%</span>
          </div>
          <button v-for="domain in domains" :key="domain.code" :class="{ active: selectedDomain === domain.code }" @click="selectedDomain = domain.code">
            <span class="domain-number">{{ domain.code }}</span>
            <span class="domain-name">{{ domain.name }}</span>
            <span class="domain-progress" :class="{ complete: domain.answered === 5 }">{{ domain.answered }}/5</span>
          </button>
        </aside>

        <div class="domain-content">
          <section class="panel domain-intro">
            <div>
              <span class="eyebrow">Domain {{ selectedDomain }} of 5</span>
              <h2 class="section-title">{{ activeDomain?.name }}</h2>
              <p class="muted">Choose the lowest maturity level consistently achieved across the organisation.</p>
            </div>
            <StatusBadge :label="`${activeDomain?.answered ?? 0} of 5 answered`" :variant="activeDomain?.answered === 5 ? 'success' : 'neutral'" />
          </section>

          <article v-for="question in activeQuestions" :key="question.code" class="panel question-card">
            <header class="question-header">
              <span class="question-code">{{ question.code }}</span>
              <div><h3>{{ question.question }}</h3><p class="muted">Select one maturity level</p></div>
              <StatusBadge v-if="response(question.code)?.evidence.length" :label="`${response(question.code)?.evidence.length} evidence`" variant="info" />
            </header>

            <section v-if="question.crane_support" class="crane-support" :class="`support-${question.crane_support.level}`">
              <div class="support-icon" aria-hidden="true"><svg viewBox="0 0 20 20"><path d="M10 2 3 5v4.5c0 4 2.5 7.2 7 8.5 4.5-1.3 7-4.5 7-8.5V5zm3.7 5.8-4.4 4.4-2.4-2.4 1.2-1.2 1.2 1.2 3.2-3.2z" fill="currentColor"/></svg></div>
              <div class="support-body">
                <div class="support-heading"><strong>How CRANE helps</strong><StatusBadge :label="supportLabel(question.crane_support.level)" :variant="supportVariant(question.crane_support.level)" /></div>
                <p>{{ question.crane_support.summary }}</p>
                <p v-if="question.crane_support.gap" class="support-gap"><strong>Remaining gap:</strong> {{ question.crane_support.gap }}</p>
                <div class="support-links">
                  <RouterLink v-for="link in question.crane_support.links" :key="link.route" :to="{ name: link.route }">{{ link.label }} ↗</RouterLink>
                  <span v-if="current.evidence_suggestions[question.code]?.length" class="record-count">{{ current.evidence_suggestions[question.code].length }} live record{{ current.evidence_suggestions[question.code].length === 1 ? '' : 's' }} found</span>
                  <span v-else-if="question.crane_support.level !== 'gap'" class="record-count">No matching live records found</span>
                </div>
              </div>
            </section>

            <fieldset class="score-options" :disabled="current.status !== 'draft' || isLoading">
              <legend class="sr-only">Maturity level for question {{ question.code }}</legend>
              <label v-for="score in 5" :key="score" :class="{ selected: response(question.code)?.score === score }">
                <input type="radio" :name="question.code" :value="score" :checked="response(question.code)?.score === score" @change="saveAnswer(question.code, score)">
                <span class="score-number">{{ score }}</span>
                <span><strong>{{ levelLabel(score) }}</strong><small>{{ question.levels[String(score)] }}</small></span>
              </label>
            </fieldset>

            <div class="question-notes">
              <label class="field">
                <span class="field-label">Assessment rationale</span>
                <textarea class="textarea" rows="2" :value="response(question.code)?.rationale || ''" :disabled="current.status !== 'draft' || isLoading" placeholder="Explain why this level applies…" @change="saveRationale(question.code, ($event.target as HTMLTextAreaElement).value)" />
              </label>
              <div class="evidence-area">
                <span class="field-label">Supporting evidence</span>
                <div v-if="response(question.code)?.evidence.length" class="evidence-list">
                  <span v-for="link in response(question.code)?.evidence" :key="link.id" class="evidence-chip">✓ {{ link.label }}</span>
                </div>
                <div v-if="current.status === 'draft' && current.evidence_suggestions[question.code]?.length" class="suggestions">
                  <span class="muted">Suggested CRANE records:</span>
                  <AppButton v-for="suggestion in current.evidence_suggestions[question.code].slice(0, 3)" :key="suggestion.entity_id" size="sm" variant="secondary" :disabled="isLoading" @click="linkEvidence(question.code, suggestion)">
                    + {{ suggestion.label }}
                  </AppButton>
                </div>
                <span v-else-if="!response(question.code)?.evidence.length" class="muted evidence-empty">No evidence linked.</span>
              </div>
            </div>
          </article>

          <div class="domain-footer">
            <AppButton variant="secondary" :disabled="selectedDomain === '1'" @click="moveDomain(-1)">← Previous domain</AppButton>
            <AppButton v-if="selectedDomain !== '5'" variant="primary" @click="moveDomain(1)">Next domain →</AppButton>
            <AppButton v-else-if="current.status === 'draft'" variant="primary" :disabled="!current.results.complete" @click="transition('submit')">Submit for review</AppButton>
          </div>
        </div>
      </section>

      <section v-else-if="tab === 'Improvement plan'" class="panel">
        <div class="panel-header">
          <div><h2 class="section-title">Improvement roadmap</h2><p class="muted section-subtitle">Prioritised actions generated from weaker assessment responses.</p></div>
          <span class="count-badge">{{ current.actions.length }}</span>
        </div>
        <div v-if="!current.actions.length" class="empty-state"><strong>No actions yet</strong><span>Actions are generated when a completed assessment is submitted.</span></div>
        <div v-else class="table-wrapper">
          <table class="data-table actions-table"><thead><tr><th>Action</th><th>Priority</th><th>Status</th><th>Due date</th></tr></thead><tbody>
            <tr v-for="action in current.actions" :key="action.id">
              <td><strong>{{ action.title }}</strong><small class="muted">Domain {{ action.domain_code }} · Question {{ action.question_code }}</small></td>
              <td><StatusBadge :label="formatLabel(action.priority)" :variant="action.priority === 'high' ? 'warning' : 'neutral'" /></td>
              <td><select class="select compact-control" :value="action.status" @change="updateAction(action.id, 'status', ($event.target as HTMLSelectElement).value)"><option value="open">Open</option><option value="in_progress">In progress</option><option value="done">Done</option><option value="cancelled">Cancelled</option></select></td>
              <td><input class="input compact-control" type="date" :value="action.due_date || ''" @change="updateAction(action.id, 'due_date', ($event.target as HTMLInputElement).value || null)"></td>
            </tr>
          </tbody></table>
        </div>
      </section>

      <section v-else class="results-layout">
        <div class="support-summary-grid">
          <article><span>Strong CRANE support</span><strong>{{ supportCounts.strong }}</strong><small>questions with first-class workflows</small></article>
          <article><span>Partial CRANE support</span><strong>{{ supportCounts.partial }}</strong><small>questions with supporting records</small></article>
          <article><span>Capability gaps</span><strong>{{ supportCounts.gap }}</strong><small>questions needing capability outside CRANE</small></article>
        </div>
        <div class="panel">
          <div class="panel-header"><div><h2 class="section-title">Domain results</h2><p class="muted section-subtitle">Low-scoring domains remain visible even when the overall score is higher.</p></div></div>
          <div class="domain-results">
            <div v-for="domain in domains" :key="domain.code" class="domain-result">
              <div><strong>{{ domain.name }}</strong><span class="muted">Domain {{ domain.code }}</span></div>
              <div class="score-bar"><span :style="{ width: `${((current.results.domain_scores[domain.code] || 0) / 5) * 100}%` }" /></div>
              <strong>{{ current.results.domain_scores[domain.code]?.toFixed(2) ?? "—" }}</strong>
            </div>
          </div>
        </div>
        <div v-if="current.results.contradictions.length" class="panel warning-panel">
          <h2 class="section-title">Evidence review required</h2>
          <p class="muted">Level 4 and 5 claims should be supported before approval.</p>
          <ul><li v-for="warning in current.results.contradictions" :key="warning">{{ warning }}</li></ul>
        </div>
        <div class="panel">
          <div class="panel-header"><div><h2 class="section-title">Score history</h2><p class="muted section-subtitle">Approved assessments and the current completed assessment.</p></div></div>
          <div v-if="!current.history.length" class="empty-state">No completed score history yet.</div>
          <div v-else class="history-list"><div v-for="point in current.history" :key="point.id"><span>{{ point.title }}</span><div class="score-bar"><span :style="{ width: `${((point.overall_score || 0) / 5) * 100}%` }" /></div><strong>{{ point.overall_score?.toFixed(2) }}</strong></div></div>
        </div>
        <div class="panel export-panel"><div><h2 class="section-title">Export assessment</h2><p class="muted section-subtitle">Download a portable evidence record or management-ready report.</p></div><div><AppButton variant="secondary" @click="download('json')">Export JSON</AppButton><AppButton variant="primary" @click="download('pdf')">Export PDF</AppButton></div></div>
      </section>
    </template>

    <footer class="attribution-notice">
      <strong>ENISA model attribution</strong>
      <span>
        Based on the
        <a href="https://www.enisa.europa.eu/publications/sme-cyber-resilience-maturity-assessment-model" target="_blank" rel="noopener noreferrer">SME Cyber Resilience Maturity Assessment Model</a>,
        © European Union Agency for Cybersecurity (ENISA), 2026, licensed under
        <a href="https://creativecommons.org/licenses/by/4.0/" target="_blank" rel="noopener noreferrer">CC BY 4.0</a>.
        Adapted and supplemented by CRANE for interactive assessment, evidence linking, improvement planning, and CRA workflow guidance.
        ENISA has not endorsed, certified, or granted official status to CRANE.
      </span>
    </footer>

    <AppModal v-model="showCreate" title="New maturity assessment" size="md">
      <form id="maturity-create-form" class="modal-form" @submit.prevent="create">
        <label class="field"><span class="field-label">Assessment title</span><input v-model="draft.title" class="input" required maxlength="255"></label>
        <label class="field"><span class="field-label">Assessment scope</span><textarea v-model="draft.scope" class="textarea" rows="3" required placeholder="Organisation, business unit, or product portfolio" /></label>
        <p class="muted form-help">The assessment uses the ENISA SME Cyber Resilience Maturity Assessment Model (2026).</p>
      </form>
      <template #footer><AppButton variant="ghost" @click="showCreate = false">Cancel</AppButton><AppButton variant="primary" type="submit" form="maturity-create-form" :disabled="isLoading">{{ isLoading ? "Creating…" : "Create assessment" }}</AppButton></template>
    </AppModal>

    <AppModal v-model="showApproval" title="Approve maturity assessment" size="md">
      <div class="approval-summary"><StatusBadge label="Reviewer sign-off" variant="warning" /><p>Approval locks the assessment. Explain acceptance of any Level 4 or 5 answers that do not yet have linked evidence.</p><label class="field"><span class="field-label">Reviewer justification</span><textarea v-model="approvalJustification" class="textarea" rows="4" placeholder="Required when high maturity claims are unsupported…" /></label></div>
      <template #footer><AppButton variant="ghost" @click="showApproval = false">Cancel</AppButton><AppButton variant="primary" :disabled="isLoading" @click="approve">Approve assessment</AppButton></template>
    </AppModal>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from "vue"
import { useRoute } from "vue-router"
import AppButton from "@/components/AppButton.vue"
import AppModal from "@/components/AppModal.vue"
import StatusBadge from "@/components/StatusBadge.vue"
import { useAsyncState } from "@/composables/useAsyncState"
import { useToast } from "@/composables/useToast"
import { maturityService } from "@/services/maturity-service"
import type { MaturityDetail, MaturitySummary } from "@/types/maturity"

const assessments = ref<MaturitySummary[]>([])
const route = useRoute()
const current = ref<MaturityDetail | null>(null)
const showCreate = ref(false)
const showApproval = ref(false)
const approvalJustification = ref("")
const selectedDomain = ref("1")
const draft = reactive({ title: "Annual SME maturity assessment", scope: "Organisation-wide" })
const tabs = ["Assessment", "Improvement plan", "Results"] as const
const tab = ref<(typeof tabs)[number]>("Assessment")
const { isLoading, execute } = useAsyncState()
const { showToast } = useToast()

const answeredCount = computed(() => current.value?.responses.filter((item) => item.score !== null).length ?? 0)
const completionPercent = computed(() => current.value ? Math.round(answeredCount.value / current.value.catalog.length * 100) : 0)
const domains = computed(() => Array.from({ length: 5 }, (_, index) => {
  const code = String(index + 1)
  const questions = current.value?.catalog.filter((item) => item.domain_code === code) ?? []
  return { code, name: questions[0]?.domain ?? `Domain ${code}`, answered: questions.filter((item) => response(item.code)?.score !== null).length }
}))
const activeDomain = computed(() => domains.value.find((item) => item.code === selectedDomain.value))
const activeQuestions = computed(() => current.value?.catalog.filter((item) => item.domain_code === selectedDomain.value) ?? [])
const supportCounts = computed(() => current.value?.catalog.reduce((counts, question) => { const level = question.crane_support?.level; if (level) counts[level] += 1; return counts }, { strong: 0, partial: 0, gap: 0 }) ?? { strong: 0, partial: 0, gap: 0 })

const response = (code: string) => current.value?.responses.find((item) => item.question_code === code)
const levelLabel = (score: number) => ["", "Not implemented", "Informal", "Documented", "Consistent", "Measured"][score]
const formatLabel = (value: string) => value.replaceAll("_", " ").replace(/\b\w/g, (letter) => letter.toUpperCase())
const formatDate = (value: string) => new Intl.DateTimeFormat(undefined, { dateStyle: "medium" }).format(new Date(value))
const statusVariant = (status: string): "success" | "warning" | "info" => status === "approved" ? "success" : status === "submitted" ? "warning" : "info"
const supportLabel = (level: "strong" | "partial" | "gap") => level === "strong" ? "Strong support" : level === "partial" ? "Partial support" : "Capability gap"
const supportVariant = (level: "strong" | "partial" | "gap"): "success" | "warning" | "neutral" => level === "strong" ? "success" : level === "partial" ? "warning" : "neutral"

async function load() { assessments.value = await execute(() => maturityService.list()) }
async function open(id: string) { current.value = await execute(() => maturityService.get(id)); selectedDomain.value = "1"; tab.value = "Assessment" }
function closeAssessment() { current.value = null; void load() }
async function create() { const item = await execute(() => maturityService.create(draft)); showCreate.value = false; await open(item.id) }
async function saveAnswer(code: string, score: number) { if (current.value) current.value = await execute(() => maturityService.answer(current.value!.id, code, { score, rationale: response(code)?.rationale || undefined })) }
async function saveRationale(code: string, rationale: string) { if (current.value) current.value = await execute(() => maturityService.answer(current.value!.id, code, { score: response(code)?.score ?? null, rationale })) }
async function linkEvidence(code: string, evidence: { entity_type: string; entity_id: string; label: string }) { if (current.value) current.value = await execute(() => maturityService.linkEvidence(current.value!.id, code, evidence)) }
async function transition(action: "submit" | "approve", justification?: string) { if (!current.value) return; current.value = await execute(() => maturityService.transition(current.value!.id, action, justification)); showToast({ type: "success", message: action === "submit" ? "Assessment submitted for review." : "Assessment approved." }) }
async function approve() { await transition("approve", approvalJustification.value.trim() || undefined); showApproval.value = false; approvalJustification.value = "" }
async function updateAction(id: string, field: string, value: string | null) { if (current.value) current.value = await execute(() => maturityService.updateAction(current.value!.id, id, { [field]: value })) }
async function download(format: "json" | "pdf") { if (!current.value) return; const blob = await execute(() => maturityService.export(current.value!.id, format)); const url = URL.createObjectURL(blob); const link = document.createElement("a"); link.href = url; link.download = `maturity-${current.value.id}.${format}`; link.click(); URL.revokeObjectURL(url) }
function moveDomain(offset: number) { selectedDomain.value = String(Math.min(5, Math.max(1, Number(selectedDomain.value) + offset))); window.scrollTo({ top: 0, behavior: "smooth" }) }

onMounted(async () => {
  await load()
  const assessmentId = typeof route.query.assessment === "string" ? route.query.assessment : null
  if (assessmentId) await open(assessmentId)
})
</script>

<style scoped>
.maturity-page{gap:var(--space-5)}.page-header,.panel-header,.assessment-header,.detail-toolbar,.header-actions,.heading-badges,.domain-nav-header,.domain-footer,.export-panel,.export-panel>div{display:flex;align-items:center}.page-header,.panel-header,.assessment-header,.export-panel{justify-content:space-between;gap:var(--space-4)}.page-title,.section-title,.assessment-heading h2,.question-header h3{margin:0}.page-subtitle,.section-subtitle,.assessment-heading p,.question-header p{margin:var(--space-1) 0 0}.panel{background:linear-gradient(180deg,var(--color-card-start),var(--color-card-end));border:1px solid var(--color-border);border-radius:var(--radius-lg);padding:var(--space-5);box-shadow:var(--shadow-lg);color:var(--color-text)}.table-wrapper{overflow-x:auto}.data-table{width:100%;border-collapse:collapse}.data-table th,.data-table td{padding:.8rem .75rem;border-top:1px solid var(--color-divider);text-align:left}.data-table th{font-size:var(--text-xs);color:var(--color-text-muted);text-transform:uppercase;letter-spacing:.06em}.table-row-link{cursor:pointer}.table-row-link:hover{background:var(--color-surface-soft)}.nowrap{white-space:nowrap}.row-arrow{text-align:right!important;font-size:var(--text-xl)}.count-badge,.model-label,.tab-count{border-radius:999px;background:var(--color-surface-elevated);border:1px solid var(--color-border);padding:.2rem .6rem;font-size:var(--text-xs);color:var(--color-text-muted)}.empty-state{display:flex;flex-direction:column;gap:var(--space-1);margin-top:var(--space-4);padding:var(--space-8);text-align:center;border:1px dashed var(--color-border);border-radius:var(--radius-md);color:var(--color-text-muted)}.detail-toolbar{justify-content:flex-start;margin-bottom:-.5rem}.assessment-heading{min-width:0}.assessment-heading h2{font-size:var(--text-2xl);margin-top:var(--space-2)}.heading-badges,.header-actions{gap:var(--space-2)}.metric-grid{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:var(--space-3)}.metric-card{padding:var(--space-4);border:1px solid var(--color-border);border-radius:var(--radius-md);background:var(--color-surface)}.metric-label,.metric-detail{display:block;color:var(--color-text-muted);font-size:var(--text-xs)}.metric-card>strong{display:block;margin:.2rem 0;font-size:var(--text-2xl)}.capitalize{text-transform:capitalize}.progress-track,.score-bar{height:6px;background:var(--color-surface-elevated-strong);border-radius:999px;overflow:hidden}.progress-track{margin-top:var(--space-2)}.progress-track span,.score-bar span{display:block;height:100%;background:var(--color-primary);border-radius:inherit}.notice{display:flex;align-items:center;gap:var(--space-3);padding:var(--space-3) var(--space-4);border:1px solid var(--color-info-border);border-radius:var(--radius-md);background:var(--color-info-bg);color:var(--color-info-text);font-size:var(--text-sm)}.notice svg{width:18px;flex:none}.tab-bar{display:flex;gap:var(--space-1);border-bottom:1px solid var(--color-border)}.tab-bar button{display:flex;gap:var(--space-2);align-items:center;padding:.75rem 1rem;border:0;border-bottom:2px solid transparent;background:transparent;color:var(--color-text-muted);font:600 var(--text-sm)/1 inherit;cursor:pointer}.tab-bar button:hover{color:var(--color-text)}.tab-bar button.active{color:var(--color-primary);border-bottom-color:var(--color-primary)}.assessment-workspace{display:grid;grid-template-columns:260px minmax(0,1fr);gap:var(--space-4);align-items:start}.domain-nav{position:sticky;top:var(--space-4);padding:var(--space-3)}.domain-nav-header{justify-content:space-between;padding:var(--space-2)}.domain-nav>button{width:100%;display:grid;grid-template-columns:28px 1fr auto;gap:var(--space-2);align-items:center;padding:.7rem;border:1px solid transparent;border-radius:8px;background:transparent;color:var(--color-text-muted);text-align:left;cursor:pointer}.domain-nav>button:hover{background:var(--color-surface-elevated)}.domain-nav>button.active{background:var(--color-success-bg);border-color:var(--color-success-border);color:var(--color-text)}.domain-number{display:grid;place-items:center;width:26px;height:26px;border-radius:7px;background:var(--color-surface-elevated);font-weight:700}.domain-name{font-size:var(--text-sm);line-height:1.25}.domain-progress{font-size:var(--text-xs)}.domain-progress.complete{color:var(--color-success)}.domain-content{display:flex;flex-direction:column;gap:var(--space-3)}.domain-intro{display:flex;justify-content:space-between;align-items:flex-start;gap:var(--space-3)}.eyebrow,.field-label{display:block;font-size:var(--text-xs);font-weight:600;text-transform:uppercase;letter-spacing:.07em;color:var(--color-text-muted)}.domain-intro .section-title{margin-top:var(--space-1)}.question-card{padding:0;overflow:hidden}.question-header{display:grid;grid-template-columns:40px 1fr auto;gap:var(--space-3);align-items:start;padding:var(--space-4) var(--space-5);border-bottom:1px solid var(--color-divider)}.question-code{display:grid;place-items:center;width:38px;height:38px;border-radius:9px;background:var(--color-success-bg);color:var(--color-success-text);font-weight:700;font-size:var(--text-sm)}.question-header h3{font-size:var(--text-base);line-height:1.4}.question-header p{font-size:var(--text-xs)}.score-options{display:grid;grid-template-columns:repeat(5,1fr);gap:var(--space-2);margin:0;padding:var(--space-4) var(--space-5);border:0}.score-options label{display:flex;flex-direction:column;gap:var(--space-2);min-height:126px;padding:var(--space-3);border:1px solid var(--color-border);border-radius:9px;background:var(--color-surface-soft);cursor:pointer;transition:border-color var(--t-fast),background var(--t-fast)}.score-options label:hover{border-color:var(--color-border-strong)}.score-options label.selected{border-color:var(--color-primary);background:var(--color-success-bg);box-shadow:inset 0 0 0 1px var(--color-primary)}.score-options input{position:absolute;opacity:0;pointer-events:none}.score-number{display:grid;place-items:center;width:25px;height:25px;border-radius:50%;background:var(--color-surface-elevated-strong);font-size:var(--text-xs);font-weight:700}.score-options strong,.score-options small{display:block}.score-options strong{font-size:var(--text-xs)}.score-options small{margin-top:var(--space-1);font-size:11px;line-height:1.35;color:var(--color-text-muted)}.question-notes{display:grid;grid-template-columns:1fr 1fr;gap:var(--space-4);padding:var(--space-4) var(--space-5);border-top:1px solid var(--color-divider);background:var(--color-surface-soft)}.field{display:flex;flex-direction:column;gap:var(--space-2)}.input,.select,.textarea{width:100%;border:1px solid var(--color-border);border-radius:8px;background:var(--color-surface);color:var(--color-text);padding:.65rem .75rem;font:inherit}.textarea{resize:vertical}.evidence-area{display:flex;flex-direction:column;gap:var(--space-2)}.evidence-list,.suggestions{display:flex;flex-wrap:wrap;align-items:center;gap:var(--space-2)}.evidence-chip{padding:.25rem .55rem;border-radius:999px;background:var(--color-info-bg);color:var(--color-info-text);font-size:var(--text-xs)}.suggestions>.muted,.evidence-empty{font-size:var(--text-xs)}.domain-footer{justify-content:space-between;padding:var(--space-2) 0}.actions-table small{display:block;margin-top:var(--space-1)}.compact-control{min-width:140px;padding:.45rem .55rem}.results-layout{display:flex;flex-direction:column;gap:var(--space-4)}.domain-results,.history-list{display:flex;flex-direction:column;margin-top:var(--space-4)}.domain-result,.history-list>div{display:grid;grid-template-columns:minmax(180px,1fr) minmax(180px,2fr) 48px;gap:var(--space-4);align-items:center;padding:.75rem 0;border-top:1px solid var(--color-divider)}.domain-result>div:first-child span{display:block;font-size:var(--text-xs)}.warning-panel{border-color:var(--color-warning-border);background:var(--color-warning-bg)}.warning-panel ul{margin-bottom:0}.export-panel>div{gap:var(--space-2)}.modal-form,.approval-summary{display:flex;flex-direction:column;gap:var(--space-4)}.form-help{font-size:var(--text-sm);margin:0}.sr-only{position:absolute;width:1px;height:1px;padding:0;margin:-1px;overflow:hidden;clip:rect(0,0,0,0);white-space:nowrap;border:0}
.crane-support{display:grid;grid-template-columns:32px 1fr;gap:var(--space-3);margin:var(--space-4) var(--space-5) 0;padding:var(--space-3);border:1px solid var(--color-info-border);border-radius:10px;background:var(--color-info-bg)}.crane-support.support-strong{border-color:var(--color-success-border);background:var(--color-success-bg)}.crane-support.support-partial{border-color:var(--color-warning-border);background:var(--color-warning-bg)}.crane-support.support-gap{border-color:var(--color-border);background:var(--color-surface-elevated)}.support-icon{display:grid;place-items:center;width:30px;height:30px;color:var(--color-primary)}.support-icon svg{width:20px}.support-heading{display:flex;justify-content:space-between;align-items:center;gap:var(--space-2)}.support-body p{margin:var(--space-1) 0;font-size:var(--text-sm)}.support-gap{color:var(--color-text-muted)}.support-links{display:flex;flex-wrap:wrap;gap:var(--space-3);align-items:center;margin-top:var(--space-2);font-size:var(--text-xs)}.support-links a{color:var(--color-primary);font-weight:600;text-decoration:none}.support-links a:hover{text-decoration:underline}.record-count{color:var(--color-text-muted);margin-left:auto}.support-summary-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:var(--space-3)}.support-summary-grid article{padding:var(--space-4);border:1px solid var(--color-border);border-radius:var(--radius-md);background:var(--color-surface)}.support-summary-grid span,.support-summary-grid small{display:block;color:var(--color-text-muted);font-size:var(--text-xs)}.support-summary-grid strong{display:block;font-size:var(--text-3xl);margin:.15rem 0}
.attribution-notice{display:flex;flex-direction:column;gap:var(--space-1);padding:var(--space-4);border-top:1px solid var(--color-border);color:var(--color-text-muted);font-size:var(--text-xs);line-height:1.55}.attribution-notice strong{color:var(--color-text)}.attribution-notice a{color:var(--color-primary)}
@media(max-width:1050px){.metric-grid{grid-template-columns:repeat(2,1fr)}.assessment-workspace{grid-template-columns:1fr}.domain-nav{position:static;display:grid;grid-template-columns:repeat(5,1fr)}.domain-nav-header{grid-column:1/-1}.domain-nav>button{grid-template-columns:28px 1fr}.domain-progress{display:none}.score-options{grid-template-columns:1fr}.score-options label{min-height:0;display:grid;grid-template-columns:28px 1fr}.question-notes{grid-template-columns:1fr}}
@media(max-width:700px){.page-header,.assessment-header,.export-panel{align-items:stretch;flex-direction:column}.metric-grid{grid-template-columns:1fr 1fr}.domain-nav{grid-template-columns:1fr}.domain-name{display:block}.question-header{grid-template-columns:40px 1fr}.question-header>.badge{grid-column:2}.tab-bar{overflow-x:auto}.tab-bar button{white-space:nowrap}.domain-result,.history-list>div{grid-template-columns:1fr 48px}.domain-result .score-bar,.history-list .score-bar{grid-row:2;grid-column:1/-1}.question-notes,.score-options,.question-header{padding-left:var(--space-4);padding-right:var(--space-4)}.crane-support{margin-left:var(--space-4);margin-right:var(--space-4)}.support-heading{align-items:flex-start;flex-direction:column}.record-count{width:100%;margin-left:0}.support-summary-grid{grid-template-columns:1fr}}
</style>
