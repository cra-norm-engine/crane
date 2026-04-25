<template>
  <section class="card timeline-card" :class="{ 'timeline-card-compact': compact }">
    <div class="timeline-header">
      <div>
        <p class="timeline-eyebrow">{{ eyebrow }}</p>
        <h2 class="timeline-title">{{ title }}</h2>
        <p v-if="description && !compact" class="muted timeline-copy">{{ description }}</p>
      </div>

      <div class="timeline-actions">
        <button
          v-if="showRefresh && !compact"
          class="button secondary timeline-refresh"
          type="button"
          :disabled="loading"
          @click="$emit('refresh')"
        >
          {{ loading ? "Refreshing..." : "Refresh" }}
        </button>

        <button
          v-if="compact"
          class="timeline-icon-btn"
          type="button"
          title="Expand timeline"
          @click="isExpanded = true"
        >
          <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <polyline points="15 3 21 3 21 9"/>
            <polyline points="9 21 3 21 3 15"/>
            <line x1="21" y1="3" x2="14" y2="10"/>
            <line x1="3" y1="21" x2="10" y2="14"/>
          </svg>
        </button>
      </div>
    </div>

    <div v-if="errorMessage" class="feedback feedback-error">
      {{ errorMessage }}
    </div>

    <div v-else-if="loading && events.length === 0" class="timeline-empty">
      Loading audit history…
    </div>

    <div v-else-if="events.length === 0" class="timeline-empty">
      No audit events found for this view yet.
    </div>

    <div v-else class="timeline-stream">
      <article
        v-for="(event, index) in visibleEvents"
        :key="event.id"
        class="timeline-entry"
        :class="{ 'timeline-entry-compact': compact }"
        :style="{ '--entry-delay': `${index * 55}ms` }"
      >
        <div class="timeline-rail" aria-hidden="true">
          <span class="timeline-dot" :class="statusClass(event.status)" />
          <span v-if="index !== visibleEvents.length - 1" class="timeline-line" />
        </div>

        <div class="timeline-event">
          <div class="timeline-meta">
            <span class="timeline-actor">
              {{ actorLabel(event) }}
            </span>
            <span class="timeline-separator">•</span>
            <time :datetime="event.occurred_at">{{ formatDateTime(event.occurred_at) }}</time>
          </div>

          <p class="timeline-summary">{{ event.summary }}</p>

          <div v-if="!compact" class="timeline-tags">
            <span class="timeline-tag">{{ formatAction(event.action_type) }}</span>
            <span v-if="event.entity_label" class="timeline-tag timeline-tag-soft">
              {{ event.entity_label }}
            </span>
            <span class="timeline-tag timeline-tag-soft">
              {{ formatEntity(event.entity_type) }}
            </span>
          </div>
        </div>
      </article>
    </div>

    <button
      v-if="compact && events.length > COMPACT_LIMIT"
      class="timeline-view-all"
      type="button"
      @click="isExpanded = true"
    >
      View all {{ events.length }} events
      <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
        <polyline points="15 3 21 3 21 9"/>
        <polyline points="9 21 3 21 3 15"/>
        <line x1="21" y1="3" x2="14" y2="10"/>
        <line x1="3" y1="21" x2="10" y2="14"/>
      </svg>
    </button>
  </section>

  <!-- Maximized modal -->
  <Teleport to="body">
    <Transition name="modal">
      <div v-if="isExpanded" class="timeline-modal-backdrop" @click.self="isExpanded = false">
        <div class="timeline-modal">
          <div class="timeline-modal-header">
            <div>
              <p class="timeline-eyebrow">{{ eyebrow }}</p>
              <h2 class="timeline-title">{{ title }}</h2>
              <p v-if="description" class="muted timeline-copy">{{ description }}</p>
            </div>
            <div class="timeline-actions">
              <button
                v-if="showRefresh"
                class="button secondary timeline-refresh"
                type="button"
                :disabled="loading"
                @click="$emit('refresh')"
              >
                {{ loading ? "Refreshing..." : "Refresh" }}
              </button>
              <button
                class="timeline-icon-btn"
                type="button"
                title="Close"
                @click="isExpanded = false"
              >
                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                  <line x1="18" y1="6" x2="6" y2="18"/>
                  <line x1="6" y1="6" x2="18" y2="18"/>
                </svg>
              </button>
            </div>
          </div>

          <div class="timeline-modal-body">
            <div v-if="errorMessage" class="feedback feedback-error">
              {{ errorMessage }}
            </div>
            <div v-else-if="loading && events.length === 0" class="timeline-empty">
              Loading audit history…
            </div>
            <div v-else-if="events.length === 0" class="timeline-empty">
              No audit events found for this view yet.
            </div>
            <div v-else class="timeline-stream">
              <article
                v-for="(event, index) in events"
                :key="event.id"
                class="timeline-entry"
                :style="{ '--entry-delay': `${index * 30}ms` }"
              >
                <div class="timeline-rail" aria-hidden="true">
                  <span class="timeline-dot" :class="statusClass(event.status)" />
                  <span v-if="index !== events.length - 1" class="timeline-line" />
                </div>

                <div class="timeline-event">
                  <div class="timeline-meta">
                    <span class="timeline-actor">{{ actorLabel(event) }}</span>
                    <span class="timeline-separator">•</span>
                    <time :datetime="event.occurred_at">{{ formatDateTime(event.occurred_at) }}</time>
                  </div>
                  <p class="timeline-summary">{{ event.summary }}</p>
                  <div class="timeline-tags">
                    <span class="timeline-tag">{{ formatAction(event.action_type) }}</span>
                    <span v-if="event.entity_label" class="timeline-tag timeline-tag-soft">
                      {{ event.entity_label }}
                    </span>
                    <span class="timeline-tag timeline-tag-soft">
                      {{ formatEntity(event.entity_type) }}
                    </span>
                  </div>
                </div>
              </article>
            </div>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup lang="ts">
import { ref, computed } from "vue";
import type { AuditEventRead } from "@/types/audit";

const COMPACT_LIMIT = 4;

const props = withDefaults(
  defineProps<{
    title: string;
    eyebrow?: string;
    description?: string;
    events: AuditEventRead[];
    loading?: boolean;
    errorMessage?: string;
    showRefresh?: boolean;
    compact?: boolean;
  }>(),
  {
    eyebrow: "Audit Trail",
    description: "",
    loading: false,
    errorMessage: "",
    showRefresh: false,
    compact: false,
  },
);

defineEmits<{
  refresh: [];
}>();

const isExpanded = ref(false);

const visibleEvents = computed(() =>
  props.compact ? props.events.slice(0, COMPACT_LIMIT) : props.events,
);

function actorLabel(event: AuditEventRead): string {
  return event.actor.full_name || event.actor.email || "System";
}

function formatDateTime(value: string): string {
  return new Intl.DateTimeFormat(undefined, {
    month: "short",
    day: "2-digit",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  }).format(new Date(value));
}

function formatAction(value: string): string {
  return value.replaceAll(".", " / ").replaceAll("_", " ");
}

function formatEntity(value: string): string {
  return value.replaceAll("_", " ");
}

function statusClass(status: string): string {
  return status === "failure" ? "timeline-dot-danger" : "timeline-dot-success";
}
</script>

<style scoped>
.timeline-card {
  display: grid;
  gap: 1rem;
  position: relative;
  overflow: hidden;
}

.timeline-card::before {
  content: "";
  position: absolute;
  inset: 0;
  background:
    radial-gradient(circle at top right, rgba(110, 168, 254, 0.14), transparent 38%),
    linear-gradient(180deg, rgba(255, 255, 255, 0.03), transparent 58%);
  pointer-events: none;
}

.timeline-header,
.timeline-meta,
.timeline-tags {
  display: flex;
  gap: 0.65rem;
  flex-wrap: wrap;
  align-items: center;
}

.timeline-header {
  justify-content: space-between;
  position: relative;
  z-index: 1;
}

.timeline-actions {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  flex-shrink: 0;
}

.timeline-eyebrow {
  margin: 0 0 0.35rem;
  text-transform: uppercase;
  letter-spacing: 0.14em;
  font-size: 0.72rem;
  color: rgba(233, 238, 252, 0.62);
}

.timeline-title,
.timeline-summary {
  margin: 0;
}

.timeline-copy {
  margin: 0.35rem 0 0;
}

.timeline-empty {
  position: relative;
  z-index: 1;
  padding: 1rem;
  border-radius: 14px;
  border: 1px dashed rgba(233, 238, 252, 0.14);
  background: rgba(255, 255, 255, 0.03);
  color: var(--color-text-muted);
}

.feedback {
  position: relative;
  z-index: 1;
  padding: 0.85rem 1rem;
  border-radius: 14px;
}

.feedback-error {
  border: 1px solid rgba(251, 113, 133, 0.28);
  background: rgba(251, 113, 133, 0.12);
  color: #fecdd3;
}

.timeline-stream {
  display: grid;
  gap: 0.85rem;
  position: relative;
  z-index: 1;
}

.timeline-entry {
  display: grid;
  grid-template-columns: 28px minmax(0, 1fr);
  gap: 0.9rem;
  opacity: 0;
  transform: translateY(8px);
  animation: timeline-enter 300ms ease forwards;
  animation-delay: var(--entry-delay);
}

.timeline-rail {
  display: grid;
  justify-items: center;
  grid-template-rows: 18px 1fr;
}

.timeline-dot {
  width: 12px;
  height: 12px;
  border-radius: 999px;
  margin-top: 2px;
  box-shadow: 0 0 0 6px rgba(255, 255, 255, 0.03);
}

.timeline-dot-success {
  background: linear-gradient(180deg, #6ea8fe, #8b5cf6);
}

.timeline-dot-danger {
  background: linear-gradient(180deg, #fb7185, #f97316);
}

.timeline-line {
  width: 2px;
  height: 100%;
  margin-top: 0.4rem;
  background: linear-gradient(180deg, rgba(110, 168, 254, 0.55), rgba(255, 255, 255, 0.05));
}

.timeline-event {
  padding: 0.85rem 0.95rem;
  border-radius: 16px;
  background: rgba(9, 17, 31, 0.48);
  border: 1px solid rgba(233, 238, 252, 0.08);
}

/* Compact entry — tighter padding, no bottom gap for tags */
.timeline-entry-compact .timeline-event {
  padding: 0.55rem 0.75rem;
}

.timeline-meta {
  color: rgba(233, 238, 252, 0.7);
  font-size: 0.84rem;
}

.timeline-actor {
  font-weight: 600;
  color: var(--color-text);
}

.timeline-separator {
  opacity: 0.55;
}

.timeline-summary {
  margin-top: 0.35rem;
  font-weight: 600;
  line-height: 1.4;
  font-size: 0.88rem;
}

.timeline-tags {
  margin-top: 0.7rem;
}

.timeline-tag {
  display: inline-flex;
  align-items: center;
  padding: 0.28rem 0.62rem;
  border-radius: 999px;
  font-size: 0.72rem;
  border: 1px solid rgba(110, 168, 254, 0.18);
  background: rgba(110, 168, 254, 0.1);
}

.timeline-tag-soft {
  border-color: rgba(233, 238, 252, 0.12);
  background: rgba(255, 255, 255, 0.04);
}

.timeline-refresh {
  align-self: start;
}

/* Icon button (expand / close) */
.timeline-icon-btn {
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
  transition: background 150ms, color 150ms, border-color 150ms;
}

.timeline-icon-btn:hover {
  background: rgba(110, 168, 254, 0.14);
  border-color: rgba(110, 168, 254, 0.3);
  color: #e9eefc;
}

/* "View all" footer link */
.timeline-view-all {
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
  position: relative;
  z-index: 1;
  font-size: 0.8rem;
  font-weight: 600;
  color: rgba(110, 168, 254, 0.9);
  background: none;
  border: none;
  padding: 0;
  cursor: pointer;
  transition: color 150ms;
}

.timeline-view-all:hover {
  color: #6ea8fe;
}

/* ── Modal ── */
.timeline-modal-backdrop {
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

.timeline-modal {
  width: 100%;
  max-width: 680px;
  max-height: 88vh;
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

.timeline-modal-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 1rem;
  padding: 1.5rem 1.5rem 1rem;
  border-bottom: 1px solid rgba(233, 238, 252, 0.07);
  flex-shrink: 0;
  background:
    radial-gradient(circle at top right, rgba(110, 168, 254, 0.1), transparent 40%);
}

.timeline-modal-body {
  overflow-y: auto;
  padding: 1.25rem 1.5rem 1.5rem;
  flex: 1;
  scrollbar-width: thin;
  scrollbar-color: rgba(110, 168, 254, 0.3) transparent;
}

/* Vue transition */
.modal-enter-active,
.modal-leave-active {
  transition: opacity 200ms ease, transform 200ms ease;
}

.modal-enter-from,
.modal-leave-to {
  opacity: 0;
}

.modal-enter-from .timeline-modal,
.modal-leave-to .timeline-modal {
  transform: scale(0.96) translateY(8px);
}

@keyframes timeline-enter {
  to {
    opacity: 1;
    transform: translateY(0);
  }
}
</style>

<style>
:root[data-theme="light"] .timeline-card::before {
  background:
    radial-gradient(circle at top right, rgba(79, 156, 19, 0.07), transparent 38%),
    linear-gradient(180deg, rgba(0, 0, 0, 0.01), transparent 58%);
}
:root[data-theme="light"] .timeline-eyebrow {
  color: rgba(20, 33, 15, 0.55);
}
:root[data-theme="light"] .timeline-empty {
  border-color: rgba(28, 107, 39, 0.16);
  background: rgba(28, 107, 39, 0.03);
}
:root[data-theme="light"] .feedback-error {
  border-color: rgba(239, 68, 68, 0.28);
  background: rgba(239, 68, 68, 0.08);
  color: #be123c;
}
:root[data-theme="light"] .timeline-dot {
  box-shadow: 0 0 0 6px rgba(28, 107, 39, 0.08);
}
:root[data-theme="light"] .timeline-line {
  background: linear-gradient(180deg, rgba(79, 156, 19, 0.5), rgba(28, 107, 39, 0.06));
}
:root[data-theme="light"] .timeline-event {
  background: rgba(255, 255, 255, 0.88);
  border-color: rgba(28, 107, 39, 0.12);
}
:root[data-theme="light"] .timeline-meta {
  color: rgba(20, 33, 15, 0.65);
}
:root[data-theme="light"] .timeline-tag {
  border-color: rgba(37, 99, 235, 0.22);
  background: rgba(37, 99, 235, 0.08);
}
:root[data-theme="light"] .timeline-tag-soft {
  border-color: rgba(28, 107, 39, 0.14);
  background: rgba(28, 107, 39, 0.05);
}
:root[data-theme="light"] .timeline-icon-btn {
  border-color: rgba(28, 107, 39, 0.16);
  background: rgba(28, 107, 39, 0.06);
  color: rgba(20, 33, 15, 0.65);
}
:root[data-theme="light"] .timeline-icon-btn:hover {
  background: rgba(37, 99, 235, 0.1);
  border-color: rgba(37, 99, 235, 0.28);
  color: #1d4ed8;
}
:root[data-theme="light"] .timeline-view-all {
  color: #2563eb;
}
:root[data-theme="light"] .timeline-view-all:hover {
  color: #1d4ed8;
}
:root[data-theme="light"] .timeline-modal-backdrop {
  background: rgba(20, 33, 15, 0.5);
}
:root[data-theme="light"] .timeline-modal {
  background: #ffffff;
  border-color: rgba(28, 107, 39, 0.15);
  box-shadow: 0 32px 80px rgba(20, 33, 15, 0.12), 0 0 0 1px rgba(28, 107, 39, 0.08);
}
:root[data-theme="light"] .timeline-modal-header {
  border-bottom-color: rgba(28, 107, 39, 0.1);
  background: radial-gradient(circle at top right, rgba(79, 156, 19, 0.07), transparent 40%);
}
:root[data-theme="light"] .timeline-modal-body {
  scrollbar-color: rgba(79, 156, 19, 0.3) transparent;
}
</style>
