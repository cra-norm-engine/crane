<template>
  <div class="assessment-wizard">
    <!-- Error message -->
    <div v-if="errorMessage" class="error-banner">
      <p>{{ errorMessage }}</p>
    </div>

    <!-- Step 1: Select methodology -->
    <div v-if="currentStep === 1" class="wizard-step">
      <h2 class="step-title">Select Assessment Methodology</h2>
      <p class="step-description">
        Choose a threat assessment framework to guide your evaluation of this change.
      </p>

      <div class="methodology-cards">
        <button
          class="methodology-card"
          :class="{ 'methodology-card--selected': selectedMethodology === 'stride' }"
          type="button"
          @click="selectMethodology('stride')"
        >
          <div class="card-header">
            <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 2v20M2 12h20"/></svg>
            <h3>STRIDE</h3>
          </div>
          <p class="card-description">6 threat categories covering Spoofing, Tampering, Repudiation, Information Disclosure, Denial of Service, and Elevation of Privilege.</p>
          <span class="card-meta">6 questions · ~3 min</span>
        </button>

        <button
          class="methodology-card"
          :class="{ 'methodology-card--selected': selectedMethodology === 'tara' }"
          type="button"
          @click="selectMethodology('tara')"
        >
          <div class="card-header">
            <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="1"/><path d="M12 8v-1"/><path d="M12 17v1"/><path d="M8.22 4.22L7.05 3.05"/><path d="M16.95 20.95l-1.17-1.17"/><path d="M4.22 8.22L3.05 7.05"/><path d="M20.95 16.95l-1.17-1.17"/><path d="M3 12h1"/><path d="M20 12h1"/><path d="M4.22 15.78l-1.17 1.17"/><path d="M20.95 7.05l-1.17 1.17"/><path d="M8.22 19.78l-1.17 1.17"/><path d="M16.95 3.05l-1.17 1.17"/></svg>
            <h3>TARA</h3>
          </div>
          <p class="card-description">4 risk assessment phases covering Asset Identification, Threat Analysis, Risk Assessment, and Control Selection.</p>
          <span class="card-meta">4 questions · ~2 min</span>
        </button>

        <button
          class="methodology-card"
          :class="{ 'methodology-card--selected': selectedMethodology === 'custom' }"
          type="button"
          @click="selectMethodology('custom')"
        >
          <div class="card-header">
            <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 5v14M5 12h14"/></svg>
            <h3>Manual Assessment</h3>
          </div>
          <p class="card-description">Manually evaluate the four CRA Article 3(3)(c) substantiality criteria without guided questions.</p>
          <span class="card-meta">Direct input · ~1 min</span>
        </button>
      </div>

      <div class="wizard-actions">
        <button class="btn-primary" type="button" :disabled="!selectedMethodology" @click="nextStep">
          Continue
        </button>
        <button class="btn-ghost btn-sm" type="button" @click="$emit('cancel')">Cancel</button>
      </div>
    </div>

    <!-- Step 2: Answer questions (only for STRIDE/TARA) -->
    <div v-if="currentStep === 2 && selectedMethodology !== 'custom'" class="wizard-step">
      <div class="progress-bar">
        <span class="progress-label">Question {{ currentQuestionIndex + 1 }} of {{ currentQuestions.length }}</span>
        <div class="progress-track">
          <div class="progress-fill" :style="{ width: `${progressPercent}%` }" />
        </div>
      </div>

      <div v-if="currentQuestion" class="question-panel">
        <h2 class="question-title">{{ currentQuestion.text }}</h2>
        <p v-if="currentQuestion.hint" class="question-hint">{{ currentQuestion.hint }}</p>

        <div class="question-meta">
          <span class="meta-category">{{ currentQuestion.threat_category }}</span>
          <span class="meta-criteria">{{ formatLabel(currentQuestion.cra_criteria_key) }}</span>
        </div>

        <div class="answer-options">
          <label class="radio-option">
            <input
              type="radio"
              :value="true"
              :checked="answers[currentQuestion.id] === true"
              @change="answers[currentQuestion.id] = true"
            />
            <span class="radio-label">Yes, this applies</span>
            <span class="radio-hint">This change introduces this threat or meets this criterion</span>
          </label>

          <label class="radio-option">
            <input
              type="radio"
              :value="false"
              :checked="answers[currentQuestion.id] === false"
              @change="answers[currentQuestion.id] = false"
            />
            <span class="radio-label">No, this does not apply</span>
            <span class="radio-hint">This change does not relate to this threat or criterion</span>
          </label>

          <label class="radio-option">
            <input
              type="radio"
              :value="null"
              :checked="answers[currentQuestion.id] === null || answers[currentQuestion.id] === undefined"
              @change="answers[currentQuestion.id] = null"
            />
            <span class="radio-label">Unsure</span>
            <span class="radio-hint">Treat as "No" for conservative assessment</span>
          </label>
        </div>
      </div>

      <div class="wizard-actions">
        <button
          class="btn-secondary"
          type="button"
          :disabled="currentQuestionIndex === 0"
          @click="previousQuestion"
        >
          ← Previous
        </button>
        <button
          class="btn-primary"
          type="button"
          @click="currentQuestionIndex < currentQuestions.length - 1 ? nextQuestion() : nextStep()"
        >
          {{ currentQuestionIndex < currentQuestions.length - 1 ? 'Next' : 'Review' }}
        </button>
        <button class="btn-ghost btn-sm" type="button" @click="$emit('cancel')">Cancel</button>
      </div>
    </div>

    <!-- Step 3: Review & confirm -->
    <div v-if="currentStep === 3" class="wizard-step">
      <h2 class="step-title">Review Assessment</h2>

      <div v-if="selectedMethodology !== 'custom'" class="answers-summary">
        <p class="summary-label">Your answers:</p>
        <div class="answers-grid">
          <div v-for="q in currentQuestions" :key="q.id" class="answer-item">
            <span class="answer-question">{{ q.id }}: {{ q.threat_category }}</span>
            <span
              class="answer-value"
              :class="{
                'answer-yes': answers[q.id] === true,
                'answer-no': answers[q.id] === false,
                'answer-unsure': answers[q.id] === null || answers[q.id] === undefined,
              }"
            >
              {{ answers[q.id] === true ? 'Yes' : answers[q.id] === false ? 'No' : 'Unsure' }}
            </span>
          </div>
        </div>
      </div>

      <div class="criteria-panel">
        <p class="panel-label">CRA Substantiality Criteria</p>
        <div class="criteria-grid">
          <div class="criterion" :class="{ 'criterion--met': derivedCriteria.alters_intended_use }">
            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg>
            <span>Alters intended use</span>
          </div>
          <div class="criterion" :class="{ 'criterion--met': derivedCriteria.introduces_new_threat_vectors }">
            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg>
            <span>New threat vectors</span>
          </div>
          <div class="criterion" :class="{ 'criterion--met': derivedCriteria.enables_new_attack_scenarios }">
            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg>
            <span>New attack scenarios</span>
          </div>
          <div class="criterion" :class="{ 'criterion--met': derivedCriteria.changes_attack_likelihood }">
            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg>
            <span>Changed attack likelihood</span>
          </div>
          <div class="criterion" :class="{ 'criterion--met': derivedCriteria.changes_attack_impact }">
            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg>
            <span>Changed attack impact</span>
          </div>
        </div>
      </div>

      <div class="substantiality-result" :class="{ 'substantiality--true': isSubstantial }">
        <div class="result-icon">
          <svg v-if="isSubstantial" xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><polyline points="12 8 12 12 16 14"/></svg>
          <svg v-else xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><line x1="8" y1="12" x2="16" y2="12"/></svg>
        </div>
        <div class="result-text">
          <p class="result-title">{{ isSubstantial ? 'Substantial Modification' : 'Non-Substantial Change' }}</p>
          <p class="result-description">
            {{ isSubstantial
              ? 'This change meets one or more substantiality criteria and requires compliance actions.'
              : 'This change does not meet substantiality criteria and follows simplified procedures.'
            }}
          </p>
        </div>
      </div>

      <label v-if="selectedMethodology !== 'custom'" class="field">
        <span class="field-label">Assessment reasoning (optional)</span>
        <textarea
          v-model.trim="reasoning"
          rows="3"
          placeholder="Summarize your assessment and any caveats or considerations…"
        />
      </label>

      <div class="wizard-actions">
        <button class="btn-secondary" type="button" @click="previousStep">
          ← Back
        </button>
        <button class="btn-primary" type="button" :disabled="submitting" @click="submitAssessment">
          {{ submitting ? 'Submitting…' : 'Submit Assessment' }}
        </button>
        <button class="btn-ghost btn-sm" type="button" :disabled="submitting" @click="$emit('cancel')">Cancel</button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue';
import { apiClient } from '@/services/api';

interface AssessmentQuestion {
  id: string;
  text: string;
  threat_category: string;
  cra_criteria_key: string;
  hint?: string;
}

interface TemplateResponse {
  methodology: string;
  questions: AssessmentQuestion[];
}

interface CriteriaMapping {
  alters_intended_use: boolean;
  introduces_new_threat_vectors: boolean;
  enables_new_attack_scenarios: boolean;
  changes_attack_likelihood: boolean;
  changes_attack_impact: boolean;
}

const props = defineProps<{
  changeId: string;
  changeType?: string;
}>();

const emit = defineEmits<{
  cancel: [];
  submitted: [];
}>();

const currentStep = ref(1);
const selectedMethodology = ref<'stride' | 'tara' | 'custom' | null>(null);
const currentQuestionIndex = ref(0);
const answers = ref<Record<string, boolean | null>>({});
const reasoning = ref('');
const submitting = ref(false);
const currentQuestions = ref<AssessmentQuestion[]>([]);
const errorMessage = ref('');

const progressPercent = computed(() => {
  if (currentQuestions.value.length === 0) return 0;
  return Math.round(((currentQuestionIndex.value + 1) / currentQuestions.value.length) * 100);
});

const currentQuestion = computed(() => currentQuestions.value[currentQuestionIndex.value]);

const derivedCriteria = computed<CriteriaMapping>(() => {
  const trueKeys = new Set(
    currentQuestions.value
      .filter(q => answers.value[q.id] === true)
      .map(q => q.cra_criteria_key),
  );
  return {
    alters_intended_use: trueKeys.has('alters_intended_use'),
    introduces_new_threat_vectors: trueKeys.has('introduces_new_threat_vectors'),
    enables_new_attack_scenarios: trueKeys.has('enables_new_attack_scenarios'),
    changes_attack_likelihood: trueKeys.has('changes_attack_likelihood'),
    changes_attack_impact: trueKeys.has('changes_attack_impact'),
  };
});

const isSubstantial = computed(() => {
  return Object.values(derivedCriteria.value).some(v => v);
});

function selectMethodology(methodology: 'stride' | 'tara' | 'custom') {
  selectedMethodology.value = methodology;
  errorMessage.value = '';
}

async function nextStep() {
  if (selectedMethodology.value === 'custom') {
    currentStep.value = 3;
  } else if (currentStep.value === 1) {
    // Load questions for selected methodology
    try {
      const { data } = await apiClient.get<TemplateResponse>(
        `/changes/assessment-templates/${selectedMethodology.value}`,
        { params: { t: Date.now() } }
      );
      currentQuestions.value = data.questions;
      // Initialize all answers to null
      currentQuestions.value.forEach(q => {
        if (!(q.id in answers.value)) {
          answers.value[q.id] = null;
        }
      });
      currentStep.value = 2;
    } catch (error) {
      const errorMsg = error instanceof Error ? error.message : String(error);
      console.error('❌ Failed to load assessment template:', error);
      errorMessage.value = `Error: ${errorMsg}`;
    }
  } else if (currentStep.value === 2) {
    currentStep.value = 3;
  }
}

function previousStep() {
  if (currentStep.value > 1) {
    currentStep.value -= 1;
  }
}

function nextQuestion() {
  if (currentQuestionIndex.value < currentQuestions.value.length - 1) {
    currentQuestionIndex.value += 1;
  }
}

function previousQuestion() {
  if (currentQuestionIndex.value > 0) {
    currentQuestionIndex.value -= 1;
  }
}

async function submitAssessment() {
  submitting.value = true;
  try {
    const payload = {
      methodology: selectedMethodology.value,
      template_answers: answers.value,
      alters_intended_use: derivedCriteria.value.alters_intended_use,
      introduces_new_threat_vectors: derivedCriteria.value.introduces_new_threat_vectors,
      enables_new_attack_scenarios: derivedCriteria.value.enables_new_attack_scenarios,
      changes_attack_likelihood: derivedCriteria.value.changes_attack_likelihood,
      changes_attack_impact: derivedCriteria.value.changes_attack_impact,
      reasoning: reasoning.value || null,
      decision_date: new Date().toISOString().split('T')[0],
    };

    await apiClient.post(`/changes/${props.changeId}/assess`, payload);
    emit('submitted');
  } catch (error) {
    console.error('Error submitting assessment:', error);
  } finally {
    submitting.value = false;
  }
}

function formatLabel(value: string): string {
  return value
    .replaceAll('_', ' ')
    .replace(/\b\w/g, (character) => character.toUpperCase());
}
</script>

<style scoped>
.assessment-wizard {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.error-banner {
  padding: 1rem;
  background-color: rgba(239, 68, 68, 0.1);
  border: 1px solid rgba(239, 68, 68, 0.3);
  border-radius: 0.5rem;
  color: #ef4444;
}

.error-banner p {
  margin: 0;
  font-size: 0.9rem;
}

/* Step container */
.wizard-step {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

/* Typography */
.step-title {
  margin: 0;
  font-size: 1.25rem;
  font-weight: 700;
  color: var(--color-text, #e9eefc);
}

.step-description {
  margin: 0;
  font-size: 0.95rem;
  color: rgba(233, 238, 252, 0.7);
  line-height: 1.5;
}

/* Methodology selection */
.methodology-cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 1rem;
}

.methodology-card {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  padding: 1.25rem;
  border: 2px solid rgba(233, 238, 252, 0.1);
  border-radius: 0.75rem;
  background: rgba(255, 255, 255, 0.02);
  cursor: pointer;
  transition: all 0.2s ease;
  text-align: left;
  font: inherit;
  color: inherit;
}

.methodology-card:hover {
  border-color: rgba(233, 238, 252, 0.2);
  background: rgba(255, 255, 255, 0.04);
}

.methodology-card--selected {
  border-color: #6ea8fe;
  background: rgba(110, 168, 254, 0.15);
}

.card-header {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.card-header h3 {
  margin: 0;
  font-size: 1.1rem;
  font-weight: 600;
}

.card-description {
  margin: 0;
  font-size: 0.9rem;
  color: rgba(233, 238, 252, 0.6);
  line-height: 1.4;
  flex: 1;
}

.card-meta {
  font-size: 0.8rem;
  color: rgba(233, 238, 252, 0.4);
}

/* Progress bar */
.progress-bar {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.progress-label {
  font-size: 0.85rem;
  font-weight: 600;
  color: rgba(233, 238, 252, 0.6);
}

.progress-track {
  height: 0.4rem;
  background: rgba(233, 238, 252, 0.1);
  border-radius: 999px;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, rgba(175, 214, 46, 0.95), rgba(28, 107, 39, 0.95));
  transition: width 0.3s ease;
}

/* Question panel */
.question-panel {
  display: flex;
  flex-direction: column;
  gap: 1rem;
  padding: 1.5rem;
  border-radius: 0.75rem;
  background: rgba(255, 255, 255, 0.02);
  border: 1px solid rgba(233, 238, 252, 0.08);
}

.question-title {
  margin: 0;
  font-size: 1.15rem;
  font-weight: 600;
  color: var(--color-text, #e9eefc);
  line-height: 1.4;
}

.question-hint {
  margin: 0;
  font-size: 0.9rem;
  color: rgba(233, 238, 252, 0.5);
  font-style: italic;
}

.question-meta {
  display: flex;
  gap: 0.75rem;
  flex-wrap: wrap;
}

.meta-category,
.meta-criteria {
  display: inline-block;
  padding: 0.3rem 0.65rem;
  border-radius: 0.4rem;
  font-size: 0.8rem;
  font-weight: 600;
  background: rgba(110, 168, 254, 0.15);
  color: #93c5fd;
}

.meta-criteria {
  background: rgba(139, 92, 246, 0.15);
  color: #d8b4fe;
}

/* Answer options */
.answer-options {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.radio-option {
  display: flex;
  align-items: flex-start;
  gap: 0.75rem;
  padding: 1rem;
  border-radius: 0.65rem;
  background: rgba(255, 255, 255, 0.02);
  border: 1px solid rgba(233, 238, 252, 0.08);
  cursor: pointer;
  transition: background 0.2s ease;
}

.radio-option:hover {
  background: rgba(255, 255, 255, 0.04);
}

.radio-option input[type="radio"] {
  margin-top: 0.2rem;
  flex-shrink: 0;
  cursor: pointer;
}

.radio-label {
  display: block;
  font-weight: 600;
  color: var(--color-text, #e9eefc);
  margin-bottom: 0.2rem;
}

.radio-hint {
  display: block;
  font-size: 0.85rem;
  color: rgba(233, 238, 252, 0.5);
}

/* Answers summary */
.answers-summary {
  padding: 1rem;
  border-radius: 0.65rem;
  background: rgba(255, 255, 255, 0.02);
  border: 1px solid rgba(233, 238, 252, 0.08);
}

.summary-label {
  margin: 0 0 0.75rem;
  font-size: 0.9rem;
  font-weight: 600;
  color: rgba(233, 238, 252, 0.7);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.answers-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 0.75rem;
}

.answer-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 0.5rem;
  padding: 0.6rem 0.8rem;
  border-radius: 0.4rem;
  background: rgba(0, 0, 0, 0.15);
  font-size: 0.85rem;
}

.answer-question {
  font-weight: 500;
  color: rgba(233, 238, 252, 0.7);
}

.answer-value {
  padding: 0.2rem 0.5rem;
  border-radius: 0.3rem;
  font-weight: 600;
  font-size: 0.8rem;
  background: rgba(110, 168, 254, 0.2);
  color: #93c5fd;
}

.answer-yes {
  background: rgba(52, 211, 153, 0.2);
  color: #86efac;
}

.answer-no {
  background: rgba(239, 68, 68, 0.2);
  color: #fca5a5;
}

.answer-unsure {
  background: rgba(245, 158, 11, 0.2);
  color: #fcd34d;
}

/* Criteria panel */
.criteria-panel {
  padding: 1.5rem;
  border-radius: 0.75rem;
  background: rgba(110, 168, 254, 0.08);
  border: 1px solid rgba(110, 168, 254, 0.2);
}

.panel-label {
  margin: 0 0 1rem;
  font-size: 0.9rem;
  font-weight: 600;
  color: #93c5fd;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.criteria-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 0.75rem;
}

.criterion {
  display: flex;
  align-items: center;
  gap: 0.6rem;
  padding: 0.75rem 1rem;
  border-radius: 0.65rem;
  background: rgba(255, 255, 255, 0.02);
  border: 1px solid rgba(110, 168, 254, 0.2);
  color: rgba(233, 238, 252, 0.5);
  font-size: 0.9rem;
  font-weight: 500;
}

.criterion--met {
  background: rgba(52, 211, 153, 0.12);
  border-color: rgba(52, 211, 153, 0.3);
  color: #86efac;
}

.criterion svg {
  flex-shrink: 0;
  opacity: 0.3;
}

.criterion--met svg {
  opacity: 1;
}

.criterion-ref {
  font-size: 0.72rem;
  font-weight: 500;
  opacity: 0.6;
  margin-left: 0.3rem;
}

/* Substantiality result */
.substantiality-result {
  display: flex;
  gap: 1rem;
  padding: 1.5rem;
  border-radius: 0.75rem;
  background: rgba(245, 158, 11, 0.08);
  border: 1px solid rgba(245, 158, 11, 0.2);
}

.substantiality--true {
  background: rgba(239, 68, 68, 0.08);
  border-color: rgba(239, 68, 68, 0.2);
}

.result-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 3rem;
  height: 3rem;
  flex-shrink: 0;
  border-radius: 50%;
  background: rgba(245, 158, 11, 0.15);
  color: #fcd34d;
}

.substantiality--true .result-icon {
  background: rgba(239, 68, 68, 0.15);
  color: #fca5a5;
}

.result-text {
  display: flex;
  flex-direction: column;
  justify-content: center;
}

.result-title {
  margin: 0 0 0.25rem;
  font-size: 1rem;
  font-weight: 700;
  color: var(--color-text, #e9eefc);
}

.result-description {
  margin: 0;
  font-size: 0.9rem;
  color: rgba(233, 238, 252, 0.6);
}

/* Form field */
.field {
  display: flex;
  flex-direction: column;
  gap: 0.4rem;
}

.field-label {
  font-size: 0.9rem;
  font-weight: 600;
  color: rgba(233, 238, 252, 0.8);
}

textarea {
  padding: 0.75rem;
  border: 1px solid rgba(233, 238, 252, 0.1);
  border-radius: 0.5rem;
  background: rgba(0, 0, 0, 0.2);
  color: var(--color-text, #e9eefc);
  font: inherit;
  font-size: 0.9rem;
  line-height: 1.5;
}

textarea:focus {
  outline: none;
  border-color: rgba(110, 168, 254, 0.4);
  background: rgba(0, 0, 0, 0.3);
}

/* Actions */
.wizard-actions {
  display: flex;
  gap: 0.6rem;
  flex-wrap: wrap;
  align-items: center;
  justify-content: center;
}

.btn-primary,
.btn-secondary,
.btn-ghost {
  padding: 0.6rem 1rem;
  border: none;
  border-radius: 0.65rem;
  font-weight: 600;
  font-size: 0.9rem;
  cursor: pointer;
  transition: all 0.2s ease;
}

.btn-primary {
  background: linear-gradient(135deg, rgba(175, 214, 46, 0.95), rgba(28, 107, 39, 0.95));
  color: #fff;
}

.btn-primary:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-secondary {
  background: rgba(110, 168, 254, 0.15);
  color: #93c5fd;
  border: 1px solid rgba(110, 168, 254, 0.3);
}

.btn-ghost {
  background: transparent;
  color: rgba(233, 238, 252, 0.6);
  border: 1px solid transparent;
  font-size: 0.85rem;
  font-weight: 500;
}

.btn-ghost:hover {
  color: rgba(233, 238, 252, 0.8);
}
</style>
