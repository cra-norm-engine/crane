<template>
  <main class="learn-page">
    <header class="topbar">
      <RouterLink class="brand-link" to="/login" aria-label="CRANE sign in"><AppLogo on-dark :scale="0.92" /></RouterLink>
      <div class="title-lockup"><span>Public learning space</span><strong>CRA Knowledge Graph</strong></div>
      <div class="top-actions">
        <span class="verified"><i aria-hidden="true">✓</i> {{ craQuestions.length }} verified questions</span>
        <RouterLink class="login-link" to="/login">Sign in to CRANE <span aria-hidden="true">→</span></RouterLink>
      </div>
    </header>

    <section class="intro">
      <div><p>Explore the Cyber Resilience Act</p><h1>Complex CRA questions, explained step by step.</h1><span>Choose a real compliance question and follow its evidence path through the relevant actors, duties, deadlines, and official sources.</span></div>
      <div class="source-legend" aria-label="Source authority legend">
        <span><i class="law"></i><b>Law</b> binding</span><span><i class="guidance"></i><b>Guidance</b> non-binding</span><span><i class="faq"></i><b>FAQ</b> non-authoritative</span>
      </div>
    </section>

    <section class="workspace" :class="{ learning: viewMode === 'learn' }">
      <aside class="navigator" aria-label="CRA learning navigation">
        <label class="search-box">
          <svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="11" cy="11" r="7"/><path d="m20 20-4-4"/></svg>
          <span class="sr-only">Search concepts</span><input v-model.trim="query" type="search" :placeholder="'Search ' + craLearningNodes.length + ' concepts…'" /><kbd v-if="!query">/</kbd>
        </label>

        <div class="nav-section">
          <div class="section-title"><span>Choose your situation</span><small>{{ craLearningPaths.length }}</small></div>
          <button v-for="path in craLearningPaths" :key="path.id" class="path-card" :class="{ active: activePathId === path.id && activeTopic === 'all' && !query }" type="button" @click="choosePath(path.id)">
            <span class="path-icon" aria-hidden="true">{{ pathIcon(path.id) }}</span>
            <span><strong>{{ path.title }}</strong><small>{{ path.description }}</small></span><span aria-hidden="true">→</span>
          </button>
        </div>

        <div class="nav-section topics">
          <div class="section-title"><span>Complete topic index</span></div>
          <div class="topic-grid">
            <button v-for="topic in craTopics" :key="topic.id" type="button" :class="{ active: activeTopic === topic.id && !query }" @click="chooseTopic(topic.id)">
              <span>{{ topic.label }}</span><small>{{ topicCount(topic.id) }}</small>
            </button>
          </div>
        </div>

        <div class="disclaimer"><span aria-hidden="true">i</span><p><strong>Learning aid, not legal advice.</strong> Guidance and FAQs do not create legal requirements. Use the linked official text for decisions.</p></div>
      </aside>

      <section class="canvas-panel" aria-label="Interactive CRA knowledge graph">
        <div class="canvas-toolbar">
          <div><span>{{ viewLabel }}</span><small v-if="viewMode === 'learn'">Guided lesson · every statement links to its source</small><small v-else-if="viewMode === 'graph'">Focused view · {{ graphNodes.length }} concepts · {{ visibleEdges.length }} explicit relations</small><small v-else>{{ candidateNodes.length }} concepts in this collection</small></div>
          <div class="tool-group"><button :class="{ active: viewMode === 'learn' }" type="button" @click="viewMode = 'learn'">Learn</button><button :class="{ active: viewMode === 'graph' }" type="button" @click="viewMode = 'graph'">Graph</button><button :class="{ active: viewMode === 'list' }" type="button" @click="viewMode = 'list'">Index</button></div>
        </div>

        <div v-if="viewMode === 'learn'" class="learn-panel">
          <form class="ask-box" @submit.prevent="submitQuestion">
            <div class="ask-heading"><span aria-hidden="true">?</span><div><strong>Ask the CRA</strong><small>Find the most relevant facts from the Act, Commission guidance, and FAQ.</small></div></div>
            <div class="ask-input"><input v-model.trim="question" type="search" placeholder="For example: Who must report a vulnerability?" aria-label="Ask a question about the CRA" /><button type="submit" :disabled="!question">Find facts</button></div>
            <div class="ask-examples"><span>Try:</span><button v-for="example in questionExamples" :key="example" type="button" @click="askExample(example)">{{ example }}</button></div>
            <div v-if="question && !asked && questionMatches.length" class="question-suggestions"><button v-for="item in questionMatches" :key="item.id" type="button" @click="askChallenge(item.id)"><span>{{ item.id }}</span>{{ item.question }}</button></div>
          </form>

          <section v-if="asked" class="answer-view" aria-live="polite">
            <div class="answer-title"><div><span>{{ activeQuestion?.question === question ? "Verified answer map" : "Closest verified question" }} · {{ activeQuestion?.id }}</span><h2>{{ activeQuestion?.question ?? question }}</h2><p>Follow the concepts in order. Every step is an explicit CRA fact; every connector is an explicit graph relation.</p></div><button type="button" @click="clearQuestion">Browse questions</button></div>
            <div v-if="answerSteps.length" class="answer-map">
              <template v-for="(step, index) in answerSteps" :key="`${step.node.id}-${index}`">
                <div v-if="step.relation" class="answer-relation"><span>{{ step.relation }}</span></div>
                <article class="answer-step">
                  <div class="answer-step-number">{{ index + 1 }}</div>
                  <div class="answer-step-copy"><span class="kind-pill" :class="`kind-${step.node.kind}`">{{ step.node.kind }}</span><h3>{{ step.node.title }}</h3><p>{{ step.node.summary }}</p><details><summary>Understand this concept</summary><p>{{ step.node.detail }}</p></details>
                    <div class="answer-sources"><a v-for="source in step.node.references" :key="`${source.sourceId}-${source.locator}`" :href="craSources[source.sourceId].url" target="_blank" rel="noopener"><span class="source-badge" :class="source.sourceId">{{ source.sourceId }}</span>{{ source.locator }} <small>{{ craSources[source.sourceId].authority }}</small> ↗</a></div>
                  </div>
                </article>
              </template>
            </div>
            <div v-else class="no-answer"><strong>No verified question matched</strong><p>Choose one of the 100 reviewed questions so the answer remains source-backed.</p><button type="button" @click="clearQuestion">Open question library</button></div>
          </section>

          <section v-else-if="browseQuestions" class="question-library">
            <div class="library-heading"><div><span>CRA question atlas</span><h2>100 difficult questions, explained as evidence paths</h2><p>Choose what you need to understand. CRANE connects the relevant actors, duties, processes, deadlines, and official sources.</p></div><strong>{{ questionCoverage }}/100 answerable</strong></div>
            <div class="category-tabs" role="tablist" aria-label="Question categories"><button type="button" :class="{ active: questionCategory === 'all' }" @click="questionCategory = 'all'">All</button><button v-for="category in craQuestionCategories" :key="category.id" type="button" :class="{ active: questionCategory === category.id }" @click="questionCategory = category.id">{{ category.label }}</button></div>
            <div class="question-grid"><button v-for="item in visibleQuestions" :key="item.id" type="button" @click="askChallenge(item.id)"><span>{{ item.id }}</span><strong>{{ item.question }}</strong><small>{{ item.concepts.length }} key concepts <b>View answer map →</b></small></button></div>
            <div class="library-footer"><span>Showing {{ visibleQuestions.length }} questions in this view</span><button type="button" @click="browseQuestions = false">Use guided lessons instead →</button></div>
          </section>

          <section v-else-if="activePath && lessonNode" class="lesson-view">

            <div class="lesson-intro"><span>Guided lesson · {{ activePath.title }}</span><h2>{{ activePath.description }}</h2><p>{{ journeyQuestion }}</p></div>
            <div class="lesson-progress"><span>Concept {{ pathStep + 1 }} of {{ activePath.nodes.length }}</span><div><i :style="{ width: `${((pathStep + 1) / activePath.nodes.length) * 100}%` }"></i></div></div>
            <article class="lesson-card">
              <div class="lesson-meta"><span class="kind-pill" :class="`kind-${lessonNode.kind}`">{{ lessonNode.kind }}</span><span>{{ topicLabel(lessonNode.topic) }}</span></div>
              <h2>{{ lessonNode.title }}</h2>
              <section class="key-fact"><span>Key fact</span><p>{{ lessonNode.summary }}</p></section>
              <section class="source-explanation"><h3>What the source says</h3><p>{{ lessonNode.detail }}</p></section>
              <div class="lesson-sources"><a v-for="source in lessonNode.references" :key="`${source.sourceId}-${source.locator}`" :href="craSources[source.sourceId].url" target="_blank" rel="noopener"><span class="source-badge" :class="source.sourceId">{{ source.sourceId }}</span><span>{{ source.locator }}</span><small>{{ craSources[source.sourceId].authority }}</small><b aria-hidden="true">↗</b></a></div>
            </article>
            <section class="recall-card"><div><span>Check your understanding</span><strong>Can you recall the central rule for “{{ lessonNode.shortLabel }}”?</strong></div><button v-if="!recallRevealed" type="button" @click="recallRevealed = true">Reveal answer</button><p v-else>{{ lessonNode.summary }}</p></section>
            <div class="lesson-nav"><button type="button" :disabled="pathStep === 0" @click="moveStep(-1)">← Previous</button><span v-if="lessonNext">Next: {{ lessonNext.shortLabel }}</span><span v-else>Journey complete</span><button v-if="lessonNext" type="button" @click="moveStep(1)">Continue →</button><button v-else type="button" @click="viewMode = 'graph'">Explore connections →</button></div>
          </section>
        </div>

        <div v-else-if="viewMode === 'graph' && graphNodes.length" class="graph-wrap">

          <svg class="graph" viewBox="0 0 1000 620" role="img" :aria-label="`${viewLabel}: focused knowledge graph with ${graphNodes.length} concepts`">
            <defs><filter id="node-glow" x="-40%" y="-40%" width="180%" height="180%"><feGaussianBlur stdDeviation="7" result="blur"/><feMerge><feMergeNode in="blur"/><feMergeNode in="SourceGraphic"/></feMerge></filter><linearGradient id="selected-fill" x1="0" y1="0" x2="1" y2="1"><stop stop-color="#2e8a63"/><stop offset="1" stop-color="#175942"/></linearGradient><marker id="edge-arrow" viewBox="0 0 8 8" refX="7" refY="4" markerWidth="7" markerHeight="7" orient="auto" markerUnits="strokeWidth"><path d="M0 0 L8 4 L0 8 Z" fill="rgba(134,183,156,.55)"/></marker><marker id="edge-arrow-active" viewBox="0 0 8 8" refX="7" refY="4" markerWidth="7" markerHeight="7" orient="auto" markerUnits="strokeWidth"><path d="M0 0 L8 4 L0 8 Z" fill="#72dca5"/></marker></defs>
            <g :transform="graphTransform">
              <g class="edges">
                <g v-for="edge in positionedEdges" :key="`${edge.from}-${edge.to}`">
                  <line :x1="edge.x1" :y1="edge.y1" :x2="edge.x2" :y2="edge.y2" :class="{ highlighted: edge.connected }" :marker-end="edge.connected ? 'url(#edge-arrow-active)' : 'url(#edge-arrow)'" />
                  <g v-if="edge.connected" class="edge-label" :transform="`translate(${edge.labelX} ${edge.labelY})`"><rect :x="-edge.labelWidth / 2" y="-9" :width="edge.labelWidth" height="18" rx="9"/><text text-anchor="middle" dy="3.5">{{ edge.displayLabel }}</text></g>
                </g>
              </g>
              <g v-for="item in positionedNodes" :key="item.node.id" class="graph-node" :class="[`kind-${item.node.kind}`, { selected: item.node.id === selectedId, connected: connectedIds.has(item.node.id) }]" :transform="`translate(${item.x} ${item.y})`" role="button" tabindex="0" :aria-label="`${item.node.title}. ${item.node.summary}`" @click="selectNode(item.node.id)" @keydown.enter.prevent="selectNode(item.node.id)" @keydown.space.prevent="selectNode(item.node.id)">
                <rect x="-88" y="-32" width="176" height="64" rx="16"/><circle cx="-68" cy="-12" r="5"/><text class="node-kind" x="-57" y="-8">{{ item.node.kind }}</text>
                <text class="node-label" text-anchor="middle"><tspan v-for="(line, index) in nodeLines(item.node.shortLabel)" :key="line" x="0" :y="index ? 17 : 14">{{ line }}</tspan></text>
              </g>
            </g>
          </svg>
          <div class="zoom-controls" aria-label="Graph zoom controls"><button type="button" aria-label="Zoom in" @click="setZoom(zoom + .1)">+</button><button type="button" aria-label="Reset zoom" @click="zoom = 1">{{ Math.round(zoom * 100) }}%</button><button type="button" aria-label="Zoom out" @click="setZoom(zoom - .1)">−</button></div>
          <p class="graph-hint"><span aria-hidden="true">✦</span> Only the relevant neighbourhood is shown, so labels remain readable</p>
        </div>

        <div v-else-if="candidateNodes.length" class="node-list">
          <button v-for="node in candidateNodes" :key="node.id" type="button" :class="{ active: node.id === selectedId }" @click="selectNode(node.id)">
            <span class="list-kind" :class="`kind-${node.kind}`">{{ node.kind }}</span><span><strong>{{ node.title }}</strong><small>{{ node.summary }}</small></span><span aria-hidden="true">→</span>
          </button>
        </div>

        <div v-else class="empty-state"><span aria-hidden="true">⌁</span><h2>No matching concepts</h2><p>Try a broader search term.</p><button type="button" @click="query = ''">Clear search</button></div>

        <footer v-if="activePath && !query && activeTopic === 'all' && viewMode !== 'learn'" class="path-progress">
          <button type="button" :disabled="pathStep === 0" aria-label="Previous step" @click="moveStep(-1)">←</button>
          <div><span>Step {{ pathStep + 1 }} of {{ activePath.nodes.length }}</span><div><i :style="{ width: `${((pathStep + 1) / activePath.nodes.length) * 100}%` }"></i></div><strong>{{ activePath.title }}</strong></div>
          <button type="button" :disabled="pathStep === activePath.nodes.length - 1" aria-label="Next step" @click="moveStep(1)">→</button>
        </footer>
      </section>

      <aside v-if="selectedNode && viewMode !== 'learn'" class="detail-panel" aria-live="polite">
        <div class="detail-top"><span class="kind-pill" :class="`kind-${selectedNode.kind}`">{{ selectedNode.kind }}</span><span>{{ topicLabel(selectedNode.topic) }}</span></div>
        <h2>{{ selectedNode.title }}</h2><p class="summary">{{ selectedNode.summary }}</p><p class="detail-copy">{{ selectedNode.detail }}</p>
        <section v-if="connections.length" class="detail-section"><h3>Explicit triples</h3>
          <button v-for="connection in connections" :key="`${connection.subject}-${connection.node.id}-${connection.label}`" type="button" class="connection" @click="revealConnection(connection.node.id)">
            <span><small>{{ connection.subject }} — {{ connection.label }} →</small><strong>{{ connection.object }}</strong></span><span aria-hidden="true">→</span>
          </button>
        </section>
        <section class="detail-section sources"><h3>Evidence</h3>
          <a v-for="source in selectedNode.references" :key="`${source.sourceId}-${source.locator}`" :href="craSources[source.sourceId].url" target="_blank" rel="noopener"><span class="source-badge" :class="source.sourceId">{{ source.sourceId }}</span><span><strong>{{ craSources[source.sourceId].label }}</strong><small>{{ source.locator }} · {{ craSources[source.sourceId].authority }}</small></span><span aria-hidden="true">↗</span></a>
        </section>
      </aside>
    </section>
  </main>
</template>

<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref, watch } from "vue";
import AppLogo from "@/components/AppLogo.vue";
import { craLearningEdges, craLearningNodes, craLearningPaths, craSources, craTopics, type CraTopicId } from "@/content/cra-learning";
import { craQuestionCategories, craQuestions, type CraQuestionCategory } from "@/content/cra-questions";
import { findCraAnswerPath, layoutCraEdge, layoutCraGraph, rankCraQuestions } from "@/utils/cra-graph-layout";

const query = ref("");
const activeTopic = ref<CraTopicId | "all">("all");
const activePathId = ref<(typeof craLearningPaths)[number]["id"]>("start");
const pathStep = ref(0);
const selectedId = ref("cra");
const viewMode = ref<"learn" | "graph" | "list">("learn");
const zoom = ref(1);
const question = ref("");
const asked = ref(false);
const recallRevealed = ref(false);
const browseQuestions = ref(true);
const selectedQuestionId = ref<string>();
const questionCategory = ref<CraQuestionCategory | "all">("all");
const questionExamples = [craQuestions[0].question, craQuestions[44].question, craQuestions[69].question];

const topicRoots: Record<CraTopicId, string> = { scope: "pde", roles: "economic_operator", classification: "classification", security: "product_security", vulnerability: "vulnerability_handling", reporting: "reporting", conformity: "conformity", market: "market_surveillance", timeline: "entry_force" };
const activePath = computed(() => craLearningPaths.find(path => path.id === activePathId.value));
const selectedNode = computed(() => craLearningNodes.find(node => node.id === selectedId.value));
const lessonNode = computed(() => activePath.value ? craLearningNodes.find(node => node.id === activePath.value!.nodes[pathStep.value]) : undefined);
const lessonNext = computed(() => activePath.value ? craLearningNodes.find(node => node.id === activePath.value!.nodes[pathStep.value + 1]) : undefined);
const activeQuestion = computed(() => craQuestions.find(item => item.id === selectedQuestionId.value));
const questionMatches = computed(() => rankCraQuestions(craQuestions, question.value).slice(0, 5));
const visibleQuestions = computed(() => questionCategory.value === "all" ? craQuestions : craQuestions.filter(item => item.category === questionCategory.value));
const answerPathIds = computed(() => activeQuestion.value ? findCraAnswerPath(activeQuestion.value.concepts, craLearningEdges) : []);
const answerSteps = computed(() => answerPathIds.value.flatMap((id, index) => {
  const node = craLearningNodes.find(item => item.id === id);
  if (!node) return [];
  const previous = answerPathIds.value[index - 1];
  const edge = previous ? craLearningEdges.find(item => (item.from === previous && item.to === id) || (item.to === previous && item.from === id)) : undefined;
  const relation = !edge ? "" : edge.from === previous ? `— ${edge.label} →` : `← ${edge.label} —`;
  return [{ node, relation }];
}));
const questionCoverage = craQuestions.filter(item => item.concepts.every(id => findCraAnswerPath(item.concepts, craLearningEdges).includes(id))).length;

const journeyQuestion = computed(() => ({ start: "What does the CRA change across a product lifecycle?", scope: "Does the CRA apply to this product?", security: "What must be built and documented before release?", vulnerability: "How must vulnerabilities be handled during support?", incident: "What must be reported, by whom, and when?", market: "How can the product reach the EU market?", oversight: "What happens after the product is on the market?", dates: "Which CRA dates control the transition?" } as Record<string, string>)[activePathId.value]);
const candidateNodes = computed(() => {
  const needle = query.value.toLocaleLowerCase();
  if (needle) return craLearningNodes.filter(node => `${node.title} ${node.shortLabel} ${node.summary} ${node.detail}`.toLocaleLowerCase().includes(needle));
  if (activeTopic.value !== "all") return craLearningNodes.filter(node => node.topic === activeTopic.value);
  const ids = new Set<string>(activePath.value?.nodes ?? []);
  return craLearningNodes.filter(node => ids.has(node.id));
});
const connections = computed(() => craLearningEdges.flatMap(edge => {
  if (edge.from !== selectedId.value && edge.to !== selectedId.value) return [];
  const otherId = edge.from === selectedId.value ? edge.to : edge.from;
  const node = craLearningNodes.find(item => item.id === otherId);
  const subject = craLearningNodes.find(item => item.id === edge.from)?.shortLabel ?? edge.from;
  const object = craLearningNodes.find(item => item.id === edge.to)?.title ?? edge.to;
  return node ? [{ node, label: edge.label, subject, object }] : [];
}));
const connectedIds = computed(() => new Set(connections.value.map(connection => connection.node.id)));
const graphNodes = computed(() => {
  if (!candidateNodes.value.length) return [];
  if (!query.value && activeTopic.value === "all") return candidateNodes.value.slice(0, 11);
  const selected = candidateNodes.value.find(node => node.id === selectedId.value) ?? candidateNodes.value[0];
  const result = [selected];
  const seen = new Set([selected.id]);
  for (const node of [...connections.value.map(connection => connection.node), ...candidateNodes.value]) {
    if (!seen.has(node.id)) { seen.add(node.id); result.push(node); }
    if (result.length === 11) break;
  }
  return result;
});
const graphIds = computed(() => new Set(graphNodes.value.map(node => node.id)));
const visibleEdges = computed(() => craLearningEdges.filter(edge => graphIds.value.has(edge.from) && graphIds.value.has(edge.to)));
const viewLabel = computed(() => query.value ? `Search results for “${query.value}”` : activeTopic.value !== "all" ? topicLabel(activeTopic.value) : activePath.value?.title ?? "CRA concepts");
const graphTransform = computed(() => `translate(500 310) scale(${zoom.value}) translate(-500 -310)`);
const positionedNodes = computed(() => layoutCraGraph(graphNodes.value.map(node => node.id), selectedId.value).map(position => ({ ...position, node: craLearningNodes.find(node => node.id === position.id)! })));
const positions = computed(() => new Map(positionedNodes.value.map(item => [item.node.id, item])));
const positionedEdges = computed(() => visibleEdges.value.flatMap(edge => {
  const a = positions.value.get(edge.from); const b = positions.value.get(edge.to);
  if (!a || !b) return [];
  const connected = edge.from === selectedId.value || edge.to === selectedId.value;
  const displayLabel = edge.label.length > 24 ? `${edge.label.slice(0, 23)}…` : edge.label;
  return [{ ...edge, a, b, connected, displayLabel, labelWidth: Math.min(158, Math.max(62, displayLabel.length * 5.7 + 18)), ...layoutCraEdge(a, b) }];
}));

function topicLabel(id: CraTopicId): string { return craTopics.find(topic => topic.id === id)?.label ?? id; }
function topicCount(id: CraTopicId | "all"): number { return id === "all" ? craLearningNodes.length : craLearningNodes.filter(node => node.topic === id).length; }
function pathIcon(id: string): string { return ({ start: "◇", scope: "⌁", security: "⌾", vulnerability: "✦", incident: "↗", market: "◎", oversight: "◉", dates: "◷" } as Record<string, string>)[id] ?? "◇"; }
function nodeLines(label: string): string[] {
  if (label.length <= 21) return [label];
  const words = label.split(" "); const midpoint = Math.ceil(words.length / 2);
  return [words.slice(0, midpoint).join(" ").slice(0, 22), words.slice(midpoint).join(" ").slice(0, 22)];
}
function selectNode(id: string): void {
  const node = craLearningNodes.find(item => item.id === id); if (!node) return;
  const fromSearch = Boolean(query.value);
  selectedId.value = id; query.value = ""; viewMode.value = "graph"; zoom.value = 1;
  if (fromSearch || activeTopic.value !== "all") activeTopic.value = node.topic;
}
function choosePath(id: (typeof craLearningPaths)[number]["id"]): void { activePathId.value = id; activeTopic.value = "all"; query.value = ""; viewMode.value = "learn"; pathStep.value = 0; recallRevealed.value = false; asked.value = false; browseQuestions.value = false; selectedId.value = craLearningPaths.find(path => path.id === id)?.nodes[0] ?? "cra"; }
function chooseTopic(id: CraTopicId | "all"): void { activeTopic.value = id; query.value = ""; viewMode.value = "graph"; const first = id === "all" ? activePath.value?.nodes[0] : topicRoots[id]; if (first) selectedId.value = first; }
function revealConnection(id: string): void {
  const node = craLearningNodes.find(item => item.id === id); if (!node) return;
  activeTopic.value = node.topic; selectedId.value = id; query.value = ""; viewMode.value = "graph"; zoom.value = 1;
}
function moveStep(delta: number): void { if (!activePath.value) return; pathStep.value = Math.min(activePath.value.nodes.length - 1, Math.max(0, pathStep.value + delta)); selectedId.value = activePath.value.nodes[pathStep.value]; recallRevealed.value = false; }
function submitQuestion(): void { const match = rankCraQuestions(craQuestions, question.value)[0]; selectedQuestionId.value = match?.id; asked.value = Boolean(question.value.trim()); browseQuestions.value = false; }
function askExample(example: string): void { question.value = example; submitQuestion(); }
function askChallenge(id: string): void { const item = craQuestions.find(candidate => candidate.id === id); if (!item) return; question.value = item.question; selectedQuestionId.value = id; asked.value = true; browseQuestions.value = false; }
function clearQuestion(): void { question.value = ""; selectedQuestionId.value = undefined; asked.value = false; browseQuestions.value = true; }
function setZoom(value: number): void { zoom.value = Math.min(1.25, Math.max(.75, Number(value.toFixed(2)))); }
function focusSearch(event: KeyboardEvent): void { if (event.key === "/" && !(event.target instanceof HTMLInputElement)) { event.preventDefault(); document.querySelector<HTMLInputElement>(".search-box input")?.focus(); } }
watch(query, value => { if (value) viewMode.value = "list"; });
onMounted(() => window.addEventListener("keydown", focusSearch));
onUnmounted(() => window.removeEventListener("keydown", focusSearch));
</script>

<style scoped>
.learn-page { --ink:#eef8f2;--muted:#96ad9f;--line:rgba(164,216,187,.14);--green:#68d79f;min-height:100vh;color:var(--ink);background:radial-gradient(circle at 48% 0%,rgba(67,167,116,.2),transparent 34rem),radial-gradient(circle at 100% 70%,rgba(26,116,91,.14),transparent 31rem),#07150f;font-family:inherit }
.learn-page::before { content:"";position:fixed;inset:0;pointer-events:none;opacity:.22;background-image:radial-gradient(rgba(168,229,194,.24) .7px,transparent .7px);background-size:23px 23px;mask-image:linear-gradient(#000,transparent 72%) }
.topbar { height:74px;display:flex;align-items:center;gap:18px;padding:0 clamp(18px,4vw,62px);border-bottom:1px solid var(--line);background:rgba(5,18,13,.82);backdrop-filter:blur(18px);position:sticky;top:0;z-index:20 }
.brand-link { display:flex;padding-right:18px;border-right:1px solid var(--line);text-decoration:none }.title-lockup { display:grid;gap:1px }.title-lockup span { color:var(--green);text-transform:uppercase;font-size:9px;font-weight:800;letter-spacing:.12em }.title-lockup strong { font-size:14px }.top-actions { margin-left:auto;display:flex;align-items:center;gap:14px }.verified { color:#a9c1b4;font-size:11px }.verified i { color:var(--green);font-style:normal;margin-right:5px }.login-link { padding:9px 13px;border:1px solid rgba(119,218,165,.27);border-radius:10px;color:#fff;background:rgba(49,133,91,.16);text-decoration:none;font-size:11px;font-weight:750 }.login-link:hover { border-color:var(--green);background:rgba(62,157,108,.25) }
.intro { position:relative;display:flex;align-items:end;justify-content:space-between;gap:28px;padding:30px clamp(20px,4vw,62px) 23px }.intro p { margin:0 0 7px;color:var(--green);font-size:9px;font-weight:800;letter-spacing:.14em;text-transform:uppercase }.intro h1 { margin:0;font-size:clamp(29px,3.7vw,47px);line-height:1.04;letter-spacing:-.043em }.intro > div > span { display:block;max-width:650px;margin-top:10px;color:var(--muted);font-size:13px;line-height:1.55 }.source-legend { display:flex;flex-wrap:wrap;justify-content:flex-end;gap:6px }.source-legend span { display:flex;align-items:center;gap:5px;padding:6px 8px;border:1px solid var(--line);border-radius:99px;background:rgba(15,40,30,.65);color:var(--muted);font-size:9px }.source-legend b { color:var(--ink) }.source-legend i { width:6px;height:6px;border-radius:50% }.source-legend i.law { background:#7ce1aa }.source-legend i.guidance { background:#71b8ff }.source-legend i.faq { background:#d7a8ff }
.workspace { position:relative;display:grid;grid-template-columns:250px minmax(520px,1fr) 310px;height:calc(100vh - 204px);min-height:650px;margin:0 clamp(12px,2.6vw,42px) 28px;border:1px solid var(--line);border-radius:22px;overflow:hidden;background:rgba(7,24,17,.72);box-shadow:0 35px 90px rgba(0,0,0,.34);backdrop-filter:blur(16px) }.workspace.learning { grid-template-columns:250px minmax(520px,1fr) }
.navigator,.detail-panel { overflow:auto;padding:19px;background:rgba(10,30,22,.84) }.navigator { border-right:1px solid var(--line) }.detail-panel { border-left:1px solid var(--line) }
.search-box { height:40px;display:flex;align-items:center;gap:8px;padding:0 10px;border:1px solid var(--line);border-radius:11px;background:rgba(255,255,255,.035) }.search-box:focus-within { border-color:rgba(102,212,156,.7);box-shadow:0 0 0 3px rgba(102,212,156,.08) }.search-box svg { width:15px;stroke:var(--muted);fill:none;stroke-width:1.8 }.search-box input { width:100%;min-width:0;border:0;outline:0;color:#fff;background:transparent;font:inherit;font-size:11px }.search-box input::placeholder { color:#718b7d }.search-box kbd { padding:1px 5px;border:1px solid var(--line);border-radius:4px;color:#718b7d;font:9px inherit }
.nav-section { margin-top:21px }.section-title { display:flex;justify-content:space-between;margin-bottom:8px;color:#a9c2b4;text-transform:uppercase;letter-spacing:.1em;font-size:8px;font-weight:850 }.section-title small { color:#5f7d6e }.path-card { width:100%;display:grid;grid-template-columns:27px 1fr 11px;align-items:center;gap:8px;padding:8px 7px;margin:2px 0;text-align:left;border:1px solid transparent;border-radius:10px;color:#abc1b5;background:transparent;cursor:pointer }.path-card:hover { background:rgba(255,255,255,.035) }.path-card.active { color:#fff;border-color:rgba(104,220,158,.2);background:linear-gradient(90deg,rgba(56,150,101,.2),rgba(37,105,79,.05)) }.path-card strong,.path-card small { display:block }.path-card strong { font-size:10px }.path-card small { margin-top:2px;color:#6e897b;font-size:8px;line-height:1.3 }.path-icon { width:26px;height:26px;display:grid;place-items:center;border:1px solid rgba(112,210,158,.2);border-radius:8px;color:var(--green);background:rgba(70,166,117,.1) }
.topic-grid { display:grid;gap:4px }.topic-grid button { display:flex;justify-content:space-between;padding:7px 8px;border:1px solid var(--line);border-radius:8px;color:#91aa9d;background:rgba(255,255,255,.025);font:650 9px inherit;cursor:pointer }.topic-grid button:hover,.topic-grid button.active { color:#fff;border-color:rgba(102,212,156,.4);background:rgba(56,147,100,.13) }.topic-grid small { color:#608071 }.disclaimer { display:flex;gap:8px;margin-top:20px;padding:10px;border:1px solid rgba(240,191,97,.15);border-radius:10px;background:rgba(133,93,25,.08);color:#999d88 }.disclaimer > span { width:14px;height:14px;display:grid;place-items:center;flex:none;border:1px solid #cfae63;border-radius:50%;color:#e1bc69;font-size:9px }.disclaimer p { margin:0;font-size:8px;line-height:1.45 }.disclaimer strong { display:block;color:#d7c99d }
.canvas-panel { min-width:0;position:relative;display:grid;grid-template-rows:auto 1fr auto;overflow:hidden;background:radial-gradient(circle at 50% 48%,rgba(43,130,88,.1),transparent 44%) }.canvas-panel::before { content:"";position:absolute;inset:54px 0 0;pointer-events:none;opacity:.14;background-image:linear-gradient(rgba(148,205,173,.1) 1px,transparent 1px),linear-gradient(90deg,rgba(148,205,173,.1) 1px,transparent 1px);background-size:35px 35px }.canvas-toolbar { z-index:2;display:flex;justify-content:space-between;align-items:center;padding:12px 15px;border-bottom:1px solid var(--line);background:rgba(8,26,19,.66) }.canvas-toolbar > div:first-child { display:grid }.canvas-toolbar span { font-size:11px;font-weight:780 }.canvas-toolbar small { margin-top:2px;color:#698578;font-size:8px }.tool-group { display:flex;padding:3px;border:1px solid var(--line);border-radius:8px;background:rgba(0,0,0,.15) }.tool-group button { border:0;padding:5px 9px;border-radius:5px;color:#758f82;background:transparent;font:750 9px inherit;cursor:pointer }.tool-group button.active { color:#d9f6e5;background:rgba(93,191,139,.17) }
.graph-wrap { min-height:0;position:relative }.graph { display:block;width:100%;height:100%;min-height:450px }.edges line { stroke:rgba(134,183,156,.3);stroke-width:1.3 }.edges line.highlighted { stroke:rgba(102,212,156,.52);stroke-width:1.8 }.edge-label rect { fill:#0c271c;stroke:rgba(102,212,156,.28) }.edge-label text { fill:#a9d4bb;font-size:8px;font-weight:700 }.graph-node { cursor:pointer;outline:none }.graph-node rect { fill:rgba(14,42,30,.97);stroke:rgba(135,190,159,.24);stroke-width:1;transition:fill .2s,stroke .2s,filter .2s }.graph-node:hover rect,.graph-node:focus-visible rect,.graph-node.connected rect { fill:rgba(20,58,42,.99);stroke:rgba(112,217,162,.57) }.graph-node.selected rect { fill:url(#selected-fill);stroke:#80ebb2;stroke-width:1.8;filter:url(#node-glow) }.graph-node circle { fill:#63d397 }.graph-node.kind-actor circle { fill:#70b9ff }.graph-node.kind-deadline circle { fill:#f4bd67 }.graph-node.kind-obligation circle { fill:#c18bf3 }.graph-node.kind-process circle { fill:#66d6d0 }.node-kind { fill:#7eaa93;font-size:7px;text-transform:uppercase;letter-spacing:1.05px }.graph-node.selected .node-kind { fill:#c0ead2 }.node-label { fill:#edf7f0;font-size:11px;font-weight:720;pointer-events:none }
.zoom-controls { position:absolute;right:13px;top:13px;display:flex;flex-direction:column;overflow:hidden;border:1px solid var(--line);border-radius:9px;background:rgba(8,27,19,.92) }.zoom-controls button { width:36px;min-height:30px;border:0;border-bottom:1px solid var(--line);color:#a7c4b4;background:transparent;font:700 10px inherit;cursor:pointer }.zoom-controls button:last-child { border:0 }.zoom-controls button:hover { color:#fff;background:rgba(79,177,125,.12) }.graph-hint { position:absolute;bottom:10px;left:50%;transform:translateX(-50%);margin:0;padding:6px 10px;border-radius:99px;color:#718e7f;background:rgba(5,20,14,.78);white-space:nowrap;font-size:8px }.graph-hint span { color:var(--green) }
.learn-panel { position:relative;min-height:0;overflow:auto;padding:clamp(18px,3vw,34px) }
.ask-box { max-width:880px;margin:0 auto 26px;padding:18px;border:1px solid rgba(104,215,159,.2);border-radius:16px;background:linear-gradient(135deg,rgba(45,130,87,.16),rgba(255,255,255,.025));box-shadow:0 18px 45px rgba(0,0,0,.16) }.ask-heading { display:flex;align-items:center;gap:11px;margin-bottom:13px }.ask-heading > span { width:31px;height:31px;display:grid;place-items:center;border:1px solid rgba(104,215,159,.35);border-radius:10px;color:var(--green);background:rgba(104,215,159,.1);font-weight:850 }.ask-heading strong,.ask-heading small { display:block }.ask-heading strong { font-size:13px }.ask-heading small { margin-top:2px;color:var(--muted);font-size:9px }.ask-input { display:flex;gap:8px }.ask-input input { min-width:0;flex:1;padding:11px 13px;border:1px solid var(--line);border-radius:10px;outline:0;color:#fff;background:rgba(2,13,8,.5);font:inherit;font-size:11px }.ask-input input:focus { border-color:rgba(104,215,159,.65);box-shadow:0 0 0 3px rgba(104,215,159,.08) }.ask-input button,.answer-title > button { padding:0 14px;border:1px solid rgba(104,215,159,.3);border-radius:10px;color:#e8fff1;background:rgba(51,145,96,.25);font:750 10px inherit;cursor:pointer }.ask-input button:disabled { opacity:.4;cursor:default }.ask-examples { display:flex;flex-wrap:wrap;align-items:center;gap:6px;margin-top:10px;color:#6f8c7e;font-size:8px }.ask-examples button { padding:5px 8px;border:1px solid var(--line);border-radius:99px;color:#8eaa9b;background:rgba(255,255,255,.025);font:inherit;cursor:pointer }.ask-examples button:hover { color:#fff;border-color:rgba(104,215,159,.32) }
.lesson-view,.answer-view { max-width:880px;margin:0 auto }.lesson-intro { margin-bottom:15px }.lesson-intro > span,.answer-title span { color:var(--green);text-transform:uppercase;letter-spacing:.11em;font-size:8px;font-weight:850 }.lesson-intro h2 { margin:6px 0 4px;font-size:20px;letter-spacing:-.02em }.lesson-intro p { margin:0;color:#87a092;font-size:10px }.lesson-progress { display:flex;align-items:center;gap:10px;margin-bottom:10px;color:#759183;font-size:8px;text-transform:uppercase;letter-spacing:.08em }.lesson-progress div { height:4px;flex:1;overflow:hidden;border-radius:4px;background:rgba(255,255,255,.07) }.lesson-progress i { display:block;height:100%;border-radius:inherit;background:linear-gradient(90deg,#45b77b,#82e8af);transition:width .25s }
.lesson-card { padding:clamp(20px,3vw,31px);border:1px solid rgba(136,203,165,.18);border-radius:18px;background:linear-gradient(145deg,rgba(16,47,34,.94),rgba(9,28,20,.94));box-shadow:0 20px 50px rgba(0,0,0,.2) }.lesson-meta { display:flex;align-items:center;justify-content:space-between;color:#708b7d;text-transform:uppercase;letter-spacing:.08em;font-size:8px }.lesson-card > h2 { margin:15px 0 18px;font-size:clamp(24px,3vw,35px);line-height:1.06;letter-spacing:-.035em }.key-fact { padding:15px 17px;border-left:3px solid var(--green);border-radius:0 11px 11px 0;background:rgba(79,177,124,.1) }.key-fact span,.source-explanation h3 { color:var(--green);text-transform:uppercase;letter-spacing:.1em;font-size:8px;font-weight:850 }.key-fact p { margin:6px 0 0;color:#e1f0e7;font-size:13px;line-height:1.55 }.source-explanation { margin-top:20px }.source-explanation h3 { margin:0 0 7px;color:#809e8e }.source-explanation p { margin:0;color:#98b0a3;font-size:10px;line-height:1.7 }.lesson-sources { display:flex;flex-wrap:wrap;gap:7px;margin-top:19px }.lesson-sources a { display:grid;grid-template-columns:auto auto auto auto;align-items:center;gap:7px;padding:7px 9px;border:1px solid var(--line);border-radius:8px;color:#abc2b5;text-decoration:none;font-size:8px }.lesson-sources a:hover { border-color:rgba(104,215,159,.4) }.lesson-sources small { color:#617d6e }.lesson-sources b { color:var(--green) }
.recall-card { display:grid;grid-template-columns:1fr auto;align-items:center;gap:15px;margin-top:10px;padding:14px 16px;border:1px solid rgba(112,185,255,.16);border-radius:13px;background:rgba(56,112,154,.08) }.recall-card span,.recall-card strong { display:block }.recall-card span { margin-bottom:3px;color:#82bff6;text-transform:uppercase;letter-spacing:.09em;font-size:7px;font-weight:850 }.recall-card strong { font-size:10px }.recall-card button { padding:7px 10px;border:1px solid rgba(112,185,255,.28);border-radius:8px;color:#cbe8ff;background:rgba(75,144,199,.12);font:750 9px inherit;cursor:pointer }.recall-card p { margin:0;color:#b8d4c6;font-size:9px;line-height:1.5 }.lesson-nav { display:grid;grid-template-columns:auto 1fr auto;align-items:center;gap:12px;margin-top:15px }.lesson-nav span { color:#6d897a;text-align:center;font-size:8px }.lesson-nav button { padding:8px 11px;border:1px solid var(--line);border-radius:9px;color:#c8ded2;background:rgba(255,255,255,.03);font:750 9px inherit;cursor:pointer }.lesson-nav button:last-child { border-color:rgba(104,215,159,.28);color:#e7fff0;background:rgba(56,151,101,.16) }.lesson-nav button:disabled { opacity:.3;cursor:default }
.question-suggestions { display:grid;gap:4px;margin-top:9px;padding:7px;border:1px solid var(--line);border-radius:10px;background:rgba(3,15,10,.72) }.question-suggestions button { display:flex;gap:9px;padding:7px;text-align:left;border:0;border-radius:7px;color:#a9c2b5;background:transparent;font:9px/1.35 inherit;cursor:pointer }.question-suggestions button:hover { color:#fff;background:rgba(86,181,132,.11) }.question-suggestions span { color:var(--green);font-weight:850 }
.question-library { max-width:960px;margin:0 auto }.library-heading { display:flex;align-items:start;justify-content:space-between;gap:25px;margin-bottom:17px }.library-heading span { color:var(--green);text-transform:uppercase;letter-spacing:.12em;font-size:8px;font-weight:850 }.library-heading h2 { margin:6px 0;font-size:clamp(21px,3vw,31px);letter-spacing:-.035em }.library-heading p { max-width:650px;margin:0;color:#88a194;font-size:10px;line-height:1.55 }.library-heading > strong { flex:none;padding:9px 11px;border:1px solid rgba(104,215,159,.24);border-radius:10px;color:#93e7b9;background:rgba(53,145,98,.12);font-size:9px }.category-tabs { display:flex;gap:5px;overflow:auto;padding-bottom:9px }.category-tabs button { flex:none;padding:6px 9px;border:1px solid var(--line);border-radius:99px;color:#7f9a8b;background:rgba(255,255,255,.02);font:750 8px inherit;cursor:pointer }.category-tabs button.active,.category-tabs button:hover { color:#eafff2;border-color:rgba(104,215,159,.34);background:rgba(62,157,107,.16) }.question-grid { display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:7px }.question-grid > button { min-height:92px;display:grid;grid-template-columns:34px 1fr;gap:4px 9px;padding:13px;text-align:left;border:1px solid var(--line);border-radius:12px;color:#dbeae1;background:rgba(255,255,255,.025);cursor:pointer }.question-grid > button:hover { transform:translateY(-1px);border-color:rgba(104,215,159,.4);background:rgba(55,145,98,.1) }.question-grid > button > span { grid-row:1/3;width:30px;height:30px;display:grid;place-items:center;border-radius:8px;color:var(--green);background:rgba(104,215,159,.09);font-size:8px;font-weight:850 }.question-grid strong { font-size:10px;line-height:1.45 }.question-grid small { color:#698577;font-size:7.5px }.question-grid small b { float:right;color:#7eddaa }.library-footer { display:flex;justify-content:space-between;align-items:center;margin-top:12px;color:#688476;font-size:8px }.library-footer button { border:0;color:#83dba9;background:transparent;font:750 8px inherit;cursor:pointer }
.answer-map { position:relative;max-width:790px;margin:0 auto;padding-left:18px }.answer-map::before { content:"";position:absolute;left:32px;top:25px;bottom:25px;width:1px;background:linear-gradient(var(--green),rgba(104,215,159,.08)) }.answer-step { position:relative;display:grid;grid-template-columns:32px 1fr;gap:13px;padding:15px;border:1px solid rgba(134,198,163,.17);border-radius:14px;background:linear-gradient(135deg,rgba(15,46,33,.96),rgba(8,27,19,.96));box-shadow:0 14px 35px rgba(0,0,0,.14) }.answer-step-number { z-index:1;width:32px;height:32px;display:grid;place-items:center;border:1px solid rgba(104,215,159,.38);border-radius:50%;color:#dff8e9;background:#103d2b;font-size:9px;font-weight:850 }.answer-step-copy h3 { margin:8px 0 5px;font-size:16px }.answer-step-copy > p { margin:0;color:#b2c9bd;font-size:10px;line-height:1.55 }.answer-step details { margin-top:10px;padding-top:9px;border-top:1px solid var(--line) }.answer-step summary { color:#7eddaa;font-size:8px;font-weight:750;cursor:pointer }.answer-step details p { margin:7px 0 0;color:#809b8c;font-size:9px;line-height:1.6 }.answer-relation { position:relative;z-index:1;display:flex;justify-content:center;height:32px;color:#74b991;font-size:8px;font-weight:750 }.answer-relation span { align-self:center;padding:4px 9px;border:1px solid rgba(104,215,159,.16);border-radius:99px;background:#0a2118 }.answer-sources { display:flex;flex-wrap:wrap;gap:5px;margin-top:11px }.answer-sources a { display:flex;align-items:center;gap:5px;padding:5px 7px;border:1px solid var(--line);border-radius:7px;color:#a5bdb0;text-decoration:none;font-size:7.5px }.answer-sources a:hover { border-color:rgba(104,215,159,.38) }.answer-sources small { color:#5f7e6e }.no-answer button { margin-top:10px;padding:7px 10px;border:1px solid var(--line);border-radius:8px;color:#dff5e8;background:rgba(60,153,104,.14);font:750 8px inherit;cursor:pointer }

.answer-title { display:flex;align-items:start;justify-content:space-between;gap:20px;margin-bottom:14px }.answer-title h2 { margin:5px 0 4px;font-size:20px }.answer-title p { max-width:630px;margin:0;color:#829d8f;font-size:9px;line-height:1.5 }.answer-title > button { min-height:32px;white-space:nowrap }.answer-grid { display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:10px }.answer-card { padding:16px;border:1px solid var(--line);border-radius:14px;background:rgba(12,38,27,.82) }.answer-card h3 { margin:10px 0 6px;font-size:14px }.answer-card p { min-height:44px;margin:0;color:#91aa9c;font-size:9px;line-height:1.55 }.answer-card > div { display:flex;align-items:end;justify-content:space-between;gap:10px;margin-top:13px }.answer-card a { color:#71b8ff;text-decoration:none;font-size:7.5px;line-height:1.4 }.answer-card button { flex:none;border:0;color:var(--green);background:transparent;font:750 8px inherit;cursor:pointer }.no-answer { padding:35px;text-align:center;border:1px dashed var(--line);border-radius:14px;color:#9bb2a5 }.no-answer strong { color:#fff }.no-answer p { margin:5px 0 0;font-size:9px }

.node-list { position:relative;overflow:auto;padding:13px }.node-list button { width:100%;display:grid;grid-template-columns:82px 1fr 15px;align-items:center;gap:10px;padding:10px;margin-bottom:6px;text-align:left;border:1px solid var(--line);border-radius:10px;color:#a9c1b4;background:rgba(255,255,255,.025);cursor:pointer }.node-list button:hover,.node-list button.active { border-color:rgba(102,212,156,.42);background:rgba(55,145,98,.12) }.node-list strong,.node-list small { display:block }.node-list strong { color:#e7f4ec;font-size:11px }.node-list small { margin-top:3px;color:#769385;font-size:8px;line-height:1.4 }.list-kind,.kind-pill { width:max-content;padding:4px 7px;border-radius:99px;color:#77dba7;background:rgba(95,203,146,.12);text-transform:uppercase;letter-spacing:.06em;font-size:7px;font-weight:850 }.kind-actor { color:#84c5ff }.kind-deadline { color:#eec074 }.kind-obligation { color:#cba1f1 }.kind-process { color:#75d8d3 }
.path-progress { z-index:2;display:grid;grid-template-columns:33px 1fr 33px;align-items:center;gap:10px;padding:10px 15px;border-top:1px solid var(--line);background:rgba(8,27,19,.87) }.path-progress button { width:31px;height:31px;border:1px solid var(--line);border-radius:8px;color:#b5d1c2;background:rgba(255,255,255,.03);cursor:pointer }.path-progress button:disabled { opacity:.28;cursor:default }.path-progress > div { display:grid;grid-template-columns:auto 1fr;gap:3px 9px;align-items:center }.path-progress span { color:#6f8c7e;font-size:8px;text-transform:uppercase;letter-spacing:.08em }.path-progress strong { font-size:9px }.path-progress > div > div { height:3px;border-radius:3px;background:rgba(255,255,255,.08) }.path-progress i { display:block;height:100%;border-radius:inherit;background:var(--green);transition:width .25s }
.empty-state { position:relative;display:grid;place-items:center;align-content:center;text-align:center;color:#799487 }.empty-state > span { color:var(--green);font-size:35px }.empty-state h2 { margin:7px 0 0;color:#fff;font-size:16px }.empty-state p { margin:5px 0 13px;font-size:10px }.empty-state button { padding:7px 10px;border:1px solid rgba(102,212,156,.3);border-radius:8px;color:#d9f2e5;background:rgba(54,148,99,.13);cursor:pointer }
.detail-top { display:flex;align-items:center;justify-content:space-between;color:#6f8c7d;font-size:8px;text-transform:uppercase;letter-spacing:.08em }.detail-panel h2 { margin:14px 0 9px;font-size:21px;line-height:1.16;letter-spacing:-.025em }.summary { margin:0;color:#c6dbcf;font-size:11px;line-height:1.56 }.detail-copy { margin:11px 0 0;color:#829d8f;font-size:9px;line-height:1.58 }.detail-section { margin-top:22px }.detail-section h3 { margin:0 0 8px;color:#759183;text-transform:uppercase;letter-spacing:.1em;font-size:8px }.connection { width:100%;display:flex;justify-content:space-between;align-items:center;padding:8px 2px;text-align:left;border:0;border-bottom:1px solid rgba(150,198,171,.09);color:#96b1a2;background:transparent;cursor:pointer }.connection:hover strong { color:var(--green) }.connection small,.connection strong { display:block }.connection small { color:#638173;font-size:7.5px;line-height:1.35 }.connection strong { margin-top:2px;color:#c7dacf;font-size:9.5px }.sources a { display:grid;grid-template-columns:auto 1fr auto;align-items:center;gap:8px;padding:9px;margin-top:6px;border:1px solid var(--line);border-radius:9px;color:#789486;background:rgba(255,255,255,.025);text-decoration:none }.sources a:hover { border-color:rgba(108,214,160,.35);background:rgba(55,145,98,.08) }.sources strong,.sources small { display:block }.sources strong { color:#c9ded2;font-size:9px }.sources small { margin-top:2px;color:#698578;font-size:7.5px;line-height:1.35 }.source-badge { padding:4px 6px;border-radius:5px;color:#8ee5b7;background:rgba(70,172,118,.12);font-size:7px;font-weight:850;text-transform:uppercase }.source-badge.guidance { color:#8bc6ff;background:rgba(80,151,220,.12) }.source-badge.faq { color:#d6b1f4;background:rgba(165,100,211,.12) }
.sr-only { position:absolute;width:1px;height:1px;overflow:hidden;clip:rect(0,0,0,0);white-space:nowrap }button:focus-visible,a:focus-visible { outline:2px solid var(--green);outline-offset:2px }
@media(max-width:1220px){.workspace{grid-template-columns:225px minmax(470px,1fr) 280px;margin-inline:12px}.intro{padding-inline:22px}}
@media(max-width:980px){.workspace{height:auto;min-height:0;grid-template-columns:220px 1fr;overflow:visible}.canvas-panel{min-height:650px}.detail-panel{grid-column:1/-1;border-left:0;border-top:1px solid var(--line)}.verified{display:none}}
@media(max-width:680px){.question-grid{grid-template-columns:1fr}.library-heading{display:block}.library-heading>strong{display:inline-block;margin-top:10px}.answer-map{padding-left:0}.answer-map::before{display:none}.answer-step{grid-template-columns:27px 1fr}.answer-step-number{width:27px;height:27px}.answer-grid{grid-template-columns:1fr}.ask-input{display:grid}.ask-input button{min-height:38px}.ask-examples{display:none}.recall-card{grid-template-columns:1fr}.lesson-nav{grid-template-columns:1fr 1fr}.lesson-nav span{display:none}.topbar{height:64px;padding-inline:14px}.title-lockup{display:none}.login-link{margin-left:auto}.intro{display:block;padding:23px 16px 19px}.source-legend{justify-content:flex-start;margin-top:14px}.workspace{display:block;margin:0 8px 18px;border-radius:15px}.navigator{border-right:0;border-bottom:1px solid var(--line)}.path-card small,.disclaimer{display:none}.canvas-panel{min-height:540px}.graph{min-height:440px}.detail-panel{padding:21px}.graph-hint{display:none}}
@media(prefers-reduced-motion:reduce){*,*::before,*::after{scroll-behavior:auto!important;transition:none!important;animation:none!important}}
</style>
