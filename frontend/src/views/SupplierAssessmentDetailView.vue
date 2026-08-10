<template><section v-if="item" class="page"><RouterLink :to="{name:'supplier-assurance'}">← Supplier assurance</RouterLink><header><div><h1>{{item.title}}</h1><p>Version {{item.system_version}} · {{item.assessment_tier}} · {{item.status}}</p></div><button v-if="canWrite&&item.status==='draft'" @click="submit">Submit for review</button></header>
<div class="grid"><article class="card"><h2>Assessment responses</h2><form v-if="canWrite&&item.status==='draft'" @submit.prevent="saveResponse"><input v-model="response.criterion_key" required placeholder="Criterion key"><input v-model="response.criterion_title" required placeholder="Criterion title"><select v-model="response.decision"><option v-for="d in decisions" :key="d">{{d}}</option></select><textarea v-model="response.rationale" required placeholder="Rationale"></textarea><button>Save response</button></form><div v-for="r in item.responses" :key="r.id" class="entry"><strong>{{r.criterion_title}}</strong><span>{{r.decision}}</span><p>{{r.rationale}}</p></div></article>
<article class="card"><h2>Findings</h2><form v-if="canWrite&&item.status==='draft'" @submit.prevent="addFinding"><input v-model="finding.title" required placeholder="Finding title"><select v-model="finding.severity"><option value="low">Low</option><option value="medium">Medium</option><option value="high">High</option><option value="critical">Critical</option></select><textarea v-model="finding.description" required placeholder="Description"></textarea><textarea v-model="finding.mitigation_plan" required placeholder="Mitigation plan"></textarea><button>Add finding</button></form><div v-for="f in item.findings" :key="f.id" class="entry"><strong>{{f.title}}</strong><span>{{f.severity}} · {{f.status}}</span><p>{{f.mitigation_plan}}</p></div></article></div>
<article class="card"><h2>Evidence</h2><form v-if="canWrite&&item.status==='draft'" @submit.prevent="createAndLinkEvidence"><input v-model="evidence.title" required placeholder="Evidence title"><input v-model="evidence.external_url" required type="url" placeholder="Evidence URL"><input v-model="evidence.valid_until" type="date"><button>Create and link evidence</button></form><div v-for="e in item.evidence_links" :key="e.id" class="entry"><strong>{{e.evidence_item_id}}</strong><span>{{e.review_status}} · valid until {{e.valid_until||'not set'}}</span><div v-if="canApprove&&item.status==='in_review'&&e.review_status==='pending'" class="actions"><button @click="reviewEvidence(e.id,'accepted')">Accept</button><button @click="reviewEvidence(e.id,'needs_update')">Needs update</button></div></div></article>
<article v-if="canApprove&&item.status==='in_review'" class="card"><h2>Review decision</h2><form @submit.prevent="decide"><select v-model="review.decision"><option value="approved">Approve</option><option value="approved_with_conditions">Approve with conditions</option><option value="rejected">Reject</option></select><textarea v-model="review.conclusion" required placeholder="Reasoned conclusion"></textarea><textarea v-if="review.decision==='rejected'" v-model="review.rejection_reason" required placeholder="Rejection reason"></textarea><input v-model="review.valid_until" type="date"><button>Record decision</button></form></article></section>
</template>
<script setup lang="ts">
import { computed, onMounted, reactive, ref } from "vue";
import { RouterLink, useRoute } from "vue-router";
import { useAuthStore } from "@/stores/auth";
import { supplierAssessmentService as api } from "@/services/supplier-assessment-service";
import type { SupplierAssessment } from "@/types/supplier-assessment";

const id = useRoute().params.assessmentId as string;
const auth = useAuthStore();
const item = ref<SupplierAssessment | null>(null);
const canWrite = computed(() => auth.hasPermission("supplier_assessment_write"));
const canApprove = computed(() => auth.hasPermission("supplier_assessment_approve"));
const decisions = ["satisfied", "partially_satisfied", "not_satisfied", "not_applicable", "unknown"];
const response = reactive({ criterion_key: "", criterion_title: "", decision: "unknown", rationale: "" });
const finding = reactive({ title: "", severity: "medium", description: "", mitigation_plan: "" });
const evidence = reactive({ title: "", external_url: "", valid_until: "" });
const review = reactive({ decision: "approved", conclusion: "", rejection_reason: "", valid_until: "" });

async function load() { item.value = await api.assessment(id); }
async function saveResponse() { await api.upsertResponse(id, response); response.criterion_key = ""; response.criterion_title = ""; response.rationale = ""; await load(); }
async function addFinding() { await api.addFinding(id, finding); finding.title = ""; finding.description = ""; finding.mitigation_plan = ""; await load(); }
async function createAndLinkEvidence() { const created = await api.createEvidence({ supplier_assessment_id: id, title: evidence.title, evidence_type: "link", external_url: evidence.external_url, uploaded_by_user_id: auth.user?.id }); await api.linkEvidence(id, { evidence_item_id: created.id, valid_until: evidence.valid_until || null }); evidence.title = ""; evidence.external_url = ""; await load(); }
async function reviewEvidence(linkId: string, review_status: string) { await api.reviewEvidence(id, linkId, { review_status }); await load(); }
async function submit() { item.value = await api.submit(id); }
async function decide() { item.value = await api.decide(id, { ...review, valid_until: review.valid_until || null, rejection_reason: review.rejection_reason || null }); }
onMounted(load);
</script>
<style scoped>.page{display:grid;gap:1rem}.page header{display:flex;justify-content:space-between}.grid{display:grid;grid-template-columns:1fr 1fr;gap:1rem}.card{background:var(--color-surface);border:1px solid var(--color-border);border-radius:12px;padding:1rem}.card form{display:grid;gap:.6rem}.inline{grid-template-columns:2fr 1fr auto!important}.entry{padding:.7rem 0;border-bottom:1px solid var(--color-border)}.entry span{float:right;color:var(--color-text-muted)}input,select,textarea,button{font:inherit;padding:.6rem;border:1px solid var(--color-border);border-radius:7px;background:var(--color-surface);color:inherit}@media(max-width:800px){.grid{grid-template-columns:1fr}.inline{grid-template-columns:1fr!important}}</style>
