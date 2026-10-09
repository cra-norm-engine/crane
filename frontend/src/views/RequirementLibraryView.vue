<template>
  <section class="page library-page">
    <header class="page-header" data-guide="library-header">
      <div>
        <h1 class="page-title">Requirement library</h1>
        <p class="muted page-subtitle">Define technical requirements, trace them to CRA essentials, then select and verify them for each product release.</p>
      </div>
      <div class="header-actions">
        <AppButton class="embedded-guide-trigger" variant="secondary" type="button" @click="startGuide"><span aria-hidden="true">?</span> Guide</AppButton>
        <AppButton v-if="canManageLibrary" data-guide="library-create" variant="primary" @click="openSourceForm">Create requirement source</AppButton>
      </div>
    </header>

    <div v-if="errorMessage" class="alert error" role="alert">{{ errorMessage }}</div>
    <div v-if="successMessage" class="alert success" role="status">{{ successMessage }}</div>

    <section data-guide="library-summary" class="library-summary" aria-label="Library summary">
      <article><strong>{{ sources.length }}</strong><span>Sources</span></article>
      <article><strong>{{ publishedCount }}</strong><span>Published</span></article>
      <article><strong>{{ requirementCount }}</strong><span>Requirements</span></article>
      <article><strong>{{ draftCount }}</strong><span>Awaiting publication</span></article>
    </section>

    <div class="library-toolbar card" data-guide="library-filters">
      <label class="search-field">
        <span class="sr-only">Search requirement sources</span>
        <input v-model.trim="search" class="input" type="search" placeholder="Search standards, policies or editions…" />
      </label>
      <div class="filter-pills" aria-label="Source status">
        <button v-for="option in statusOptions" :key="option.value" :class="{ active: statusFilter === option.value }" @click="statusFilter = option.value">
          {{ option.label }}
        </button>
      </div>
    </div>

    <div v-if="loading" class="empty-state">Loading requirement library…</div>
    <div v-else-if="filteredSources.length === 0" class="empty-state">
      <strong>No requirement sources found</strong>
      <span>Create a source for a standard, internal policy or contractual obligation.</span>
    </div>
    <div v-else class="source-grid" data-guide="library-sources">
      <article v-for="source in filteredSources" :key="source.id" class="source-card" :class="`status-${source.status}`">
        <div class="source-card-top">
          <span class="source-icon" aria-hidden="true">{{ sourceIcon(source.source_type) }}</span>
          <span class="status-badge" :class="`badge-${source.status}`">{{ source.status }}</span>
        </div>
        <div>
          <span class="source-code">{{ source.identifier }}<template v-if="source.edition"> · {{ source.edition }}</template></span>
          <h2>{{ source.title }}</h2>
          <p>{{ source.publisher || sourceTypeLabel(source.source_type) }}</p>
        </div>
        <dl class="source-meta">
          <div><dt>Requirements</dt><dd>{{ source.requirement_count }}</dd></div>
          <div><dt>Coverage</dt><dd>{{ scopeLabel(source) }}</dd></div>
        </dl>
        <div class="source-actions">
          <button class="text-action" @click="openSource(source)">Open source <span aria-hidden="true">→</span></button>
          <span v-if="source.is_system_managed" class="managed-label">System managed</span>
        </div>
      </article>
    </div>

    <div v-if="showSourceForm" class="modal-backdrop" @click.self="showSourceForm = false">
      <section class="modal-card" role="dialog" aria-modal="true" aria-labelledby="source-form-title">
        <header><div><span class="eyebrow">New governed source</span><h2 id="source-form-title">Create requirement source</h2></div><button class="close" aria-label="Close" @click="showSourceForm = false">×</button></header>
        <form @submit.prevent="createSource">
          <div class="form-grid">
            <label><span>Source type</span><select v-model="sourceForm.source_type" class="select" required><option value="harmonized_standard">Harmonized standard</option><option value="standard">Other standard</option><option value="internal_policy">Internal policy</option><option value="contract">Contractual requirement</option><option value="product_specific">Product-specific source</option></select></label>
            <label><span>Identifier</span><input v-model.trim="sourceForm.identifier" class="input" placeholder="e.g. EN 18031-1" required /></label>
            <label class="full"><span>Title</span><input v-model.trim="sourceForm.title" class="input" placeholder="A clear name for product teams" required /></label>
            <label><span>Edition or version</span><input v-model.trim="sourceForm.edition" class="input" placeholder="2024 or v2.1" /></label>
            <label><span>Publisher or owner</span><input v-model.trim="sourceForm.publisher" class="input" placeholder="Standards body or internal owner" /></label>
            <label class="full"><span>External reference</span><input v-model.trim="sourceForm.reference_url" class="input" type="url" placeholder="Link to the authorized source" /></label>
          </div>
          <fieldset class="scope-box"><legend>Product coverage</legend><label class="scope-choice"><input v-model="sourceForm.organization_wide" type="checkbox" /><span><strong>Organization-wide</strong><small>Make this source available to teams for every product.</small></span></label><div v-if="!sourceForm.organization_wide" class="product-picker"><span>Select products</span><label v-for="product in products" :key="product.id"><input v-model="sourceForm.product_ids" type="checkbox" :value="product.id" />{{ product.name }} <small>{{ product.product_code }}</small></label></div></fieldset>
          <p class="license-note">CRANE stores only content your organization is authorized to use. Prefer clause references and organization-authored implementation objectives when licensed wording cannot be reproduced.</p>
          <footer><AppButton type="button" variant="secondary" @click="showSourceForm = false">Cancel</AppButton><AppButton type="submit" variant="primary" :disabled="busy">{{ busy ? "Creating…" : "Create draft source" }}</AppButton></footer>
        </form>
      </section>
    </div>

    <aside v-if="selectedSource" class="source-drawer" aria-label="Requirement source details">
      <header class="drawer-header"><div><span class="source-code">{{ selectedSource.identifier }}<template v-if="selectedSource.edition"> · {{ selectedSource.edition }}</template></span><h2>{{ selectedSource.title }}</h2><p>{{ scopeLabel(selectedSource) }} · {{ selectedSource.requirement_count }} requirements</p></div><button class="close" aria-label="Close" @click="selectedSource = null">×</button></header>
      <div class="drawer-body">
        <div v-if="errorMessage" class="alert error" role="alert">{{ errorMessage }}</div>
        <div v-if="successMessage" class="alert success" role="status">{{ successMessage }}</div>
        <div class="governance-strip"><span class="status-badge" :class="`badge-${selectedSource.status}`">{{ selectedSource.status }}</span><p v-if="selectedSource.status === 'draft'">Build and review this source before publication. Draft content never enters product assessments.</p><p v-else-if="selectedSource.status === 'published'">Published requirements can be selected for eligible product releases. Existing baselines stay unchanged.</p><p v-else>This edition is retained for historical assessments and no longer assigned to new releases.</p></div>
        <div class="drawer-toolbar"><div><h3>{{ selectedSource.is_system_managed ? "CRA essential requirements" : "Technical requirements" }}</h3><p>{{ selectedSource.is_system_managed ? "The compliance objectives every release must assess." : "Define testable objectives and show which CRA essentials they support." }}</p></div><AppButton v-if="canEditSelected" variant="secondary" size="sm" @click="toggleRequirementForm">{{ showRequirementForm ? "Cancel" : "Add requirement" }}</AppButton></div>
        <form v-if="showRequirementForm" class="requirement-form" @submit.prevent="createRequirement">
          <h3 class="full">{{ editingRequirementId ? "Edit technical requirement" : "New technical requirement" }}</h3>
          <label><span>Internal code</span><input v-model.trim="requirementForm.code" class="input" placeholder="SEC-001" required /></label>
          <label><span>Clause reference</span><input v-model.trim="requirementForm.clause_reference" class="input" placeholder="Clause 5.2.1" /></label>
          <label class="full"><span>Short title</span><input v-model.trim="requirementForm.title" class="input" required /></label>
          <label class="full"><span>Requirement objective</span><textarea v-model.trim="requirementForm.description" class="textarea" rows="3" required /></label>
          <label class="full"><span>Applicability guidance</span><textarea v-model.trim="requirementForm.applicability_guidance" class="textarea" rows="2" placeholder="When does this apply to a product or release?" /></label>
          <label class="full"><span>Acceptance criteria</span><textarea v-model.trim="requirementForm.acceptance_criteria" class="textarea" rows="3" required placeholder="Describe the observable outcome needed to pass, including relevant limits and conditions." /></label>
          <label class="full"><span>Verification method</span><textarea v-model.trim="requirementForm.verification_guidance" class="textarea" rows="2" placeholder="How should the team demonstrate that it is met?" /></label>
          <label class="full"><span>Expected evidence</span><textarea v-model.trim="requirementForm.expected_evidence" class="textarea" rows="2" placeholder="Design review, test report, configuration record…" /></label>
          <fieldset class="full contribution-picker">
            <legend>Supports CRA essential requirements</legend>
            <p class="muted">Select the essentials this requirement helps fulfill. Explain its contribution; one technical requirement may cover only part of an essential.</p>
            <div class="essential-options">
              <label v-for="essential in essentials" :key="essential.id" class="essential-option">
                <input type="checkbox" :checked="hasContribution(essential.id)" @change="toggleContribution(essential.id)" />
                <span><strong>{{ essential.title }}</strong><small>{{ essential.code }}</small></span>
              </label>
            </div>
            <label v-for="link in requirementForm.contributions" :key="link.essential_requirement_id" class="contribution-rationale">
              <span>{{ essentialTitle(link.essential_requirement_id) }}</span>
              <textarea v-model.trim="link.contribution" class="textarea" rows="2" required placeholder="Which aspect does this address? What remains outside its scope?" />
            </label>
            <small v-if="!requirementForm.contributions.length" class="muted">Without a CRA mapping, this remains an additional product obligation.</small>
          </fieldset>
          <label class="mandatory"><input v-model="requirementForm.is_mandatory" type="checkbox" /><span><strong>Always applicable when selected</strong><small>Otherwise, teams can record a justified non-applicability decision.</small></span></label>
          <div class="full form-actions"><AppButton type="submit" variant="primary" size="sm" :disabled="busy">Save requirement</AppButton></div>
        </form>
        <div v-if="requirements.length === 0" class="empty-state compact"><strong>No requirements yet</strong><span>Add concise, testable requirements before publishing this source.</span></div>
        <div v-else class="requirement-list">
          <article v-for="requirement in requirements" :key="requirement.id" class="requirement-card"><div><span class="requirement-code">{{ requirement.code }}<template v-if="requirement.clause_reference"> · {{ requirement.clause_reference }}</template></span><h4>{{ requirement.title }}</h4><p>{{ requirement.description }}</p></div><div class="requirement-tags"><span>{{ requirement.kind === "essential" ? "CRA essential" : "Technical requirement" }}</span><span>Revision {{ requirement.revision }}</span><span v-if="requirement.is_mandatory">Mandatory</span><span>{{ requirement.status }}</span></div><div v-if="requirement.contributions?.length" class="requirement-contributions"><strong>Supports {{ requirement.contributions.length }} CRA essential{{ requirement.contributions.length === 1 ? "" : "s" }}</strong><div v-for="link in requirement.contributions" :key="link.essential_requirement_id"><span>{{ essentialTitle(link.essential_requirement_id) }}</span><p>{{ link.contribution }}</p></div></div>
          <AppButton v-if="canEditSelected" variant="secondary" size="sm" @click="editRequirement(requirement)">Edit requirement</AppButton>
          <details v-if="requirement.acceptance_criteria || requirement.verification_guidance || requirement.expected_evidence"><summary>Acceptance criteria and guidance</summary><p v-if="requirement.acceptance_criteria"><strong>Acceptance:</strong> {{ requirement.acceptance_criteria }}</p><p v-if="requirement.applicability_guidance"><strong>Applicability:</strong> {{ requirement.applicability_guidance }}</p><p v-if="requirement.verification_guidance"><strong>Verification:</strong> {{ requirement.verification_guidance }}</p><p v-if="requirement.expected_evidence"><strong>Expected evidence:</strong> {{ requirement.expected_evidence }}</p></details></article>
        </div>
      </div>
      <footer v-if="canManageLibrary && !selectedSource.is_system_managed" class="drawer-footer"><span v-if="selectedSource.status === 'draft'">Publication freezes this edition. Product teams choose which requirements to adopt into a release.</span><AppButton v-if="selectedSource.status === 'draft'" variant="primary" :disabled="busy || requirements.length === 0" @click="setStatus('published')">Publish source</AppButton><AppButton v-else-if="selectedSource.status === 'published'" variant="secondary" :disabled="busy" @click="setStatus('retired')">Retire edition</AppButton></footer>
    </aside>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from "vue";
import { useAuthStore } from "@/stores/auth";
import AppButton from "@/components/AppButton.vue";
import { productService } from "@/services/product-service";
import { requirementSourceService } from "@/services/requirement-source-service";
import type { RequirementContribution } from "@/types/annex-requirement";
import type { LibraryRequirement, RequirementSourceCreate, RequirementSourceRead } from "@/types/requirement-source";

const authStore = useAuthStore();
const canManageLibrary = computed(() => authStore.hasPermission("annex_requirement_write"));
const sources = ref<RequirementSourceRead[]>([]), requirements = ref<LibraryRequirement[]>([]), products = ref<any[]>([]);
const selectedSource = ref<RequirementSourceRead | null>(null), loading = ref(true), busy = ref(false), showSourceForm = ref(false), showRequirementForm = ref(false);
const errorMessage = ref(""), successMessage = ref(""), search = ref(""), statusFilter = ref("all");
const statusOptions = [{ value: "all", label: "All" }, { value: "published", label: "Published" }, { value: "draft", label: "Drafts" }, { value: "retired", label: "Retired" }];
const emptySource = (): RequirementSourceCreate => ({ identifier: "", title: "", source_type: "harmonized_standard", edition: "", publisher: "", reference_url: "", license_note: "", organization_wide: true, product_ids: [] });
const sourceForm = reactive(emptySource());
const emptyRequirement = () => ({ code: "", title: "", description: "", clause_reference: "", applicability_guidance: "", verification_guidance: "", expected_evidence: "", acceptance_criteria: "", contributions: [] as RequirementContribution[], is_mandatory: false });
const requirementForm = reactive(emptyRequirement());
const essentials = ref<LibraryRequirement[]>([]);
const editingRequirementId = ref("");
function hasContribution(id: string) { return requirementForm.contributions.some((link) => link.essential_requirement_id === id); }
function essentialTitle(id: string) { return essentials.value.find((r) => r.id === id)?.title || "CRA essential requirement"; }
function toggleContribution(id: string) {
  const index = requirementForm.contributions.findIndex((link) => link.essential_requirement_id === id);
  if (index >= 0) requirementForm.contributions.splice(index, 1);
  else requirementForm.contributions.push({ essential_requirement_id: id, contribution: "" });
}
function toggleRequirementForm() {
  showRequirementForm.value = !showRequirementForm.value;
  editingRequirementId.value = "";
  Object.assign(requirementForm, emptyRequirement());
}
function editRequirement(requirement: LibraryRequirement) {
  Object.assign(requirementForm, emptyRequirement(), requirement, { contributions: requirement.contributions.map((link) => ({ ...link })) });
  editingRequirementId.value = requirement.id;
  showRequirementForm.value = true;
}
const publishedCount = computed(() => sources.value.filter((s) => s.status === "published").length);
const draftCount = computed(() => sources.value.filter((s) => s.status === "draft").length);
const requirementCount = computed(() => sources.value.reduce((sum, source) => sum + source.requirement_count, 0));
const canEditSelected = computed(() => canManageLibrary.value && selectedSource.value?.status === "draft" && !selectedSource.value.is_system_managed);
const filteredSources = computed(() => sources.value.filter((source) => (statusFilter.value === "all" || source.status === statusFilter.value) && [source.identifier, source.title, source.edition, source.publisher].some((value) => value?.toLowerCase().includes(search.value.toLowerCase()))));

function sourceIcon(type: string) { return type === "harmonized_standard" ? "EN" : type === "internal_policy" ? "IP" : type === "contract" ? "CT" : type === "regulation" ? "EU" : "ST"; }
function sourceTypeLabel(type: string) { return type.split("_").map((p) => p[0].toUpperCase() + p.slice(1)).join(" "); }
function scopeLabel(source: RequirementSourceRead) { return source.organization_wide ? "All products" : `${source.product_ids.length} selected product${source.product_ids.length === 1 ? "" : "s"}`; }
function resetMessages() { errorMessage.value = ""; successMessage.value = ""; }
function startGuide() { window.dispatchEvent(new Event("crane-guide-start")); }
function openSourceForm() { Object.assign(sourceForm, emptySource()); showSourceForm.value = true; resetMessages(); }
async function loadSources() {
  sources.value = await requirementSourceService.list();
  const cra = sources.value.find((source) => source.is_system_managed);
  essentials.value = cra ? await requirementSourceService.requirements(cra.id) : [];
}
async function openSource(source: RequirementSourceRead) {
  resetMessages();
  try {
    const items = await requirementSourceService.requirements(source.id);
    selectedSource.value = source;
    requirements.value = items;
    showRequirementForm.value = false;
    editingRequirementId.value = "";
  } catch (error: any) { errorMessage.value = error?.message || "Could not open requirement source."; }
}
async function createSource() { busy.value = true; resetMessages(); try { const created = await requirementSourceService.create(sourceForm); await loadSources(); showSourceForm.value = false; await openSource(created); successMessage.value = "Draft requirement source created."; } catch (error: any) { errorMessage.value = error?.message ?? "Failed to create source."; } finally { busy.value = false; } }
async function createRequirement() { if (!selectedSource.value) return; busy.value = true; resetMessages(); try { const payload = { ...requirementForm, source_id: selectedSource.value.id };
  if (editingRequirementId.value) await requirementSourceService.updateRequirement(editingRequirementId.value, payload);
  else await requirementSourceService.createRequirement(selectedSource.value.id, payload);
  editingRequirementId.value = ""; Object.assign(requirementForm, emptyRequirement()); showRequirementForm.value = false; requirements.value = await requirementSourceService.requirements(selectedSource.value.id); await loadSources(); selectedSource.value = sources.value.find((s) => s.id === selectedSource.value?.id) ?? null; successMessage.value = "Technical requirement saved with its CRA mappings."; } catch (error: any) { errorMessage.value = error?.message ?? "Failed to create requirement."; } finally { busy.value = false; } }
async function setStatus(status: "published" | "retired") { if (!selectedSource.value) return; busy.value = true; resetMessages(); try { const updated = await requirementSourceService.setStatus(selectedSource.value.id, status); await loadSources(); selectedSource.value = updated; requirements.value = await requirementSourceService.requirements(updated.id); successMessage.value = status === "published" ? "Source published. Its requirements are now available for product teams to select." : "Source retired. Historical assessments remain unchanged."; } catch (error: any) { errorMessage.value = error?.message ?? `Failed to ${status} source.`; } finally { busy.value = false; } }
onMounted(async () => { try { await Promise.all([loadSources(), productService.list().then((data) => { products.value = data; })]); } catch (error: any) { errorMessage.value = error?.message ?? "Failed to load requirement library."; } finally { loading.value = false; } });
</script>

<style scoped>
.library-page{max-width:1440px;margin:0 auto;padding:28px}.eyebrow,.source-code,.requirement-code{font-size:.75rem;font-weight:800;letter-spacing:.08em;text-transform:uppercase;color:var(--color-primary)}.library-summary{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin:20px 0}.library-summary article{background:var(--color-surface);border:1px solid var(--color-border);border-radius:14px;padding:17px 20px;display:flex;flex-direction:column}.library-summary strong{font-size:1.65rem}.library-summary span{color:var(--color-text-muted);font-size:.82rem}.library-toolbar{display:flex;justify-content:space-between;gap:16px;align-items:center;margin:24px 0}.search-field{width:min(480px,100%)}.filter-pills{display:flex;gap:6px;background:var(--color-surface);border:1px solid var(--color-border);padding:4px;border-radius:12px}.filter-pills button{border:0;background:transparent;color:var(--color-text-muted);padding:8px 12px;border-radius:8px;cursor:pointer}.filter-pills button.active{background:var(--color-primary);color:white}.source-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));gap:16px}.source-card{background:var(--color-surface);border:1px solid var(--color-border);border-radius:18px;padding:20px;display:flex;flex-direction:column;gap:18px;box-shadow:0 8px 26px rgba(15,23,42,.05)}.source-card:hover{border-color:color-mix(in srgb,var(--color-primary) 50%,var(--color-border));transform:translateY(-1px)}.source-card-top,.source-actions,.drawer-toolbar,.drawer-footer{display:flex;align-items:center;justify-content:space-between;gap:12px}.source-icon{width:42px;height:42px;display:grid;place-items:center;border-radius:12px;background:color-mix(in srgb,var(--color-primary) 12%,transparent);color:var(--color-primary);font-weight:900}.status-badge{font-size:.7rem;text-transform:uppercase;font-weight:800;letter-spacing:.06em;padding:5px 9px;border-radius:99px}.badge-published{background:#dcfce7;color:#166534}.badge-draft{background:#fef3c7;color:#92400e}.badge-retired{background:#e2e8f0;color:#475569}.source-card h2{font-size:1.08rem;margin:7px 0}.source-card p{color:var(--color-text-muted);margin:0}.source-meta{display:grid;grid-template-columns:1fr 1fr;margin:0;border-top:1px solid var(--color-border);border-bottom:1px solid var(--color-border);padding:14px 0}.source-meta div{display:flex;flex-direction:column}.source-meta dt{font-size:.72rem;color:var(--color-text-muted)}.source-meta dd{margin:3px 0 0;font-weight:700}.text-action{border:0;background:transparent;padding:0;color:var(--color-primary);font-weight:800;cursor:pointer}.managed-label{font-size:.72rem;color:var(--color-text-muted)}.empty-state{border:1px dashed var(--color-border);border-radius:16px;min-height:180px;display:grid;place-content:center;text-align:center;gap:6px;color:var(--color-text-muted)}.empty-state.compact{min-height:120px}.modal-backdrop{position:fixed;inset:0;background:rgba(15,23,42,.58);display:grid;place-items:center;padding:20px;z-index:1000}.modal-card{width:min(760px,100%);max-height:90vh;overflow:auto;background:var(--color-surface);border-radius:20px;box-shadow:0 24px 80px rgba(0,0,0,.3)}.modal-card>header,.drawer-header{display:flex;justify-content:space-between;gap:20px;padding:22px 26px;border-bottom:1px solid var(--color-border)}.modal-card h2,.drawer-header h2{margin:4px 0}.close{border:0;background:transparent;font-size:1.8rem;color:var(--color-text-muted);cursor:pointer}.modal-card form{padding:24px}.form-grid,.requirement-form{display:grid;grid-template-columns:1fr 1fr;gap:16px}.form-grid label,.requirement-form label{display:flex;flex-direction:column;gap:7px;font-size:.82rem;font-weight:700}.full{grid-column:1/-1}.scope-box{border:1px solid var(--color-border);border-radius:14px;padding:16px;margin:20px 0}.scope-choice,.mandatory{display:flex!important;flex-direction:row!important;align-items:flex-start;gap:10px}.scope-choice span,.mandatory span{display:flex;flex-direction:column}.scope-choice small,.mandatory small{font-weight:400;color:var(--color-text-muted)}.product-picker{display:grid;grid-template-columns:1fr 1fr;gap:8px;margin:14px 0 0 24px}.product-picker>span{grid-column:1/-1;font-weight:700}.product-picker label{display:flex;gap:7px;font-size:.84rem}.license-note{background:color-mix(in srgb,#f59e0b 10%,transparent);border-left:3px solid #f59e0b;padding:12px;font-size:.8rem;color:var(--color-text-muted)}.modal-card footer{display:flex;justify-content:flex-end;gap:10px;margin-top:20px}.source-drawer{position:fixed;z-index:900;top:0;right:0;height:100vh;width:min(720px,100%);background:var(--color-surface);box-shadow:-20px 0 60px rgba(15,23,42,.22);display:flex;flex-direction:column}.drawer-header p{margin:5px 0 0;color:var(--color-text-muted)}.drawer-body{padding:22px 26px;overflow:auto;flex:1}.governance-strip{display:flex;gap:12px;align-items:flex-start;background:var(--color-inset-surface);padding:14px;border-radius:12px}.governance-strip p{margin:0;color:var(--color-text-muted);font-size:.85rem}.drawer-toolbar{margin:24px 0 14px}.drawer-toolbar h3{margin:0}.drawer-toolbar p{margin:4px 0;color:var(--color-text-muted);font-size:.82rem}.requirement-form{border:1px solid var(--color-border);border-radius:14px;padding:18px;margin-bottom:18px;background:var(--color-inset-surface)}.mandatory{grid-column:1/-1}.form-actions{text-align:right}.requirement-list{display:grid;gap:12px}.requirement-card{border:1px solid var(--color-border);border-radius:14px;padding:17px}.requirement-card h4{margin:5px 0;font-size:1rem}.requirement-card p{color:var(--color-text-muted);font-size:.86rem;line-height:1.55}.requirement-tags{display:flex;gap:7px;margin-top:12px}.requirement-tags span{background:var(--color-inset-surface);border-radius:99px;padding:4px 8px;font-size:.7rem}.requirement-card details{border-top:1px solid var(--color-border);margin-top:14px;padding-top:10px}.requirement-card summary{cursor:pointer;font-weight:700;font-size:.82rem}.drawer-footer{border-top:1px solid var(--color-border);padding:16px 24px}.drawer-footer span{font-size:.78rem;color:var(--color-text-muted)}.textarea{width:100%;resize:vertical}.sr-only{position:absolute;width:1px;height:1px;overflow:hidden;clip:rect(0,0,0,0)}
/* CRANE design-system alignment */
.library-page {
  max-width: none;
  margin: 0;
  padding: 0;
  gap: var(--space-4);
}

.header-actions { display: flex; align-items: center; gap: var(--space-2); flex-wrap: wrap; }

.page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-4);
}

.page-title { margin: 0; }
.page-subtitle {
  max-width: 760px;
  margin: var(--space-1) 0 0;
  color: var(--color-text-muted);
  font-size: var(--text-sm);
}

.eyebrow {
  color: var(--color-eyebrow-text);
}

.library-summary {
  gap: var(--space-3);
  margin: 0;
}

.library-summary article {
  position: relative;
  overflow: hidden;
  min-height: 92px;
  justify-content: center;
  padding: var(--space-4) var(--space-5);
  background: linear-gradient(180deg, var(--color-card-start), var(--color-card-end));
  border-color: var(--color-border);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-lg);
}

.library-summary article::before {
  content: "";
  position: absolute;
  inset: 0 auto 0 0;
  width: 3px;
  background: linear-gradient(180deg, var(--color-primary-2), var(--color-primary-3));
}

.library-summary strong { color: var(--color-text); font-size: var(--text-2xl); }
.library-summary span { color: var(--color-text-muted); font-size: var(--text-xs); }

.library-toolbar {
  margin: 0;
  padding: var(--space-4);
  box-shadow: none;
}

.filter-pills {
  background: var(--color-inset-surface);
  border-color: var(--color-inset-border);
}

.filter-pills button {
  color: var(--color-text-muted);
  font: inherit;
  font-size: var(--text-sm);
  font-weight: 600;
}

.filter-pills button:hover { background: var(--color-nav-hover-bg); color: var(--color-text); }
.filter-pills button.active { background: var(--color-primary-3); color: var(--color-button-text); }

.source-grid { gap: var(--space-4); }
.source-card {
  min-height: 280px;
  padding: var(--space-5);
  background: linear-gradient(180deg, var(--color-card-start), var(--color-card-end));
  border-color: var(--color-border);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-lg);
  transition: transform var(--t-fast), border-color var(--t-fast), box-shadow var(--t-fast);
}

.source-card:hover {
  border-color: var(--color-border-strong);
  box-shadow: 0 22px 58px rgba(0, 0, 0, 0.3);
}

.source-icon {
  width: 44px;
  height: 44px;
  background: var(--color-status-bg);
  color: var(--color-status-text);
  border: 1px solid var(--color-status-border);
}

.badge-published { background: var(--color-success-bg); color: var(--color-success-text); border: 1px solid var(--color-success-border); }
.badge-draft { background: var(--color-warning-bg); color: var(--color-warning-text); border: 1px solid var(--color-warning-border); }
.badge-retired { background: var(--color-slate-bg); color: var(--color-slate-text); border: 1px solid var(--color-slate-border); }
.source-code,.requirement-code { color: var(--color-status-text); }
.source-card h2 { color: var(--color-text); font-size: var(--text-lg); line-height: 1.35; }
.source-meta { margin-top: auto; border-color: var(--color-divider); }
.text-action { color: var(--color-status-text); font-size: var(--text-sm); }
.text-action:hover { color: var(--color-primary-2); }

.empty-state {
  background: var(--color-inset-surface);
  border-color: var(--color-inset-border-dashed);
}

.modal-backdrop {
  z-index: 1200;
  background: var(--color-modal-backdrop);
  backdrop-filter: blur(6px);
}

.modal-card {
  color: var(--color-text);
  background: var(--color-modal-bg);
  border: 1px solid var(--color-modal-border);
  border-radius: var(--radius-lg);
  box-shadow: 0 32px 80px rgba(0, 0, 0, 0.48);
}

.modal-card > header,.drawer-header { border-color: var(--color-modal-header-border); }
.close { color: var(--color-icon-btn-text); }
.close:hover { color: var(--color-text); }
.scope-box { background: var(--color-inset-surface); border-color: var(--color-inset-border); }
.scope-box legend { padding: 0 var(--space-2); color: var(--color-text-muted); font-size: var(--text-sm); font-weight: 700; }
.license-note { background: var(--color-warning-bg); border-color: var(--color-warning-border); color: var(--color-warning-text); border-radius: var(--radius-md); }

.source-drawer {
  z-index: 1100;
  color: var(--color-text);
  background: var(--color-modal-bg);
  border-left: 1px solid var(--color-modal-border);
  box-shadow: -28px 0 80px rgba(0, 0, 0, 0.42);
}

.governance-strip { background: var(--color-inset-surface); border: 1px solid var(--color-inset-border); }
.requirement-form {
  background: var(--color-modal-bg);
  border: 1px solid var(--color-modal-border);
  box-shadow: 0 16px 44px rgba(0, 0, 0, 0.28);
}

.requirement-form input,.requirement-form textarea {
  background: var(--color-bg-secondary);
  border-color: var(--color-border-strong);
}

.requirement-card {
  background: var(--color-inset-surface);
  border-color: var(--color-inset-border);
}

.requirement-card:hover { background: var(--color-inset-surface-hover); }
.requirement-card h4 { color: var(--color-text); }
.requirement-tags span { background: var(--color-slate-bg); color: var(--color-slate-text); border: 1px solid var(--color-slate-border); }
.drawer-footer { background: var(--color-modal-bg); border-color: var(--color-modal-header-border); }

.contribution-picker { border: 1px solid var(--color-border); border-radius: var(--radius-md); padding: 16px; min-width: 0; }
.contribution-picker legend { font-weight: 700; padding: 0 6px; }
.contribution-picker > p { font-size: var(--text-sm); margin-top: 0; }
.essential-options { display: grid; gap: 8px; max-height: 240px; overflow: auto; padding: 4px; }
.essential-option { flex-direction: row !important; align-items: flex-start; font-weight: 400 !important; padding: 8px; background: var(--color-inset-surface); border-radius: 8px; }
.essential-option input { margin-top: 3px; }
.essential-option span { display: grid; gap: 3px; }
.essential-option small { color: var(--color-text-muted); }
.contribution-rationale { margin-top: 16px; }
.requirement-contributions { margin: 14px 0; font-size: var(--text-sm); }
.requirement-contributions > div { border-left: 2px solid var(--color-primary); padding-left: 12px; margin-top: 12px; }
.requirement-contributions p { margin: 5px 0; white-space: pre-wrap; }
.requirement-form h3 { margin: 0; }
@media(max-width:760px){.library-page{padding:18px}.page-header,.library-toolbar{align-items:stretch;flex-direction:column}.library-summary{grid-template-columns:1fr 1fr}.filter-pills{width:100%;overflow:auto}.form-grid,.requirement-form,.product-picker{grid-template-columns:1fr}.full{grid-column:auto}}
</style>
