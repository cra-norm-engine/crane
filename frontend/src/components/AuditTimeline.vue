<template>
  <section class="card timeline-card">
    <div class="timeline-header">
      <div>
        <p class="timeline-eyebrow">{{ eyebrow }}</p>
        <h2 class="timeline-title">{{ title }}</h2>
        <p v-if="description" class="muted timeline-copy">{{ description }}</p>
      </div>

      <button
        v-if="showRefresh"
        class="button secondary timeline-refresh"
        type="button"
        :disabled="loading"
        @click="$emit('refresh')"
      >
        {{ loading ? "Refreshing..." : "Refresh" }}
      </button>
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
        v-for="(event, index) in events"
        :key="event.id"
        class="timeline-entry"
        :style="{ '--entry-delay': `${index * 55}ms` }"
      >
        <div class="timeline-rail" aria-hidden="true">
          <span class="timeline-dot" :class="statusClass(event.status)" />
          <span v-if="index !== events.length - 1" class="timeline-line" />
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
  </section>
</template>

<script setup lang="ts">
import type { AuditEventRead } from "@/types/audit";

withDefaults(
  defineProps<{
    title: string;
    eyebrow?: string;
    description?: string;
    events: AuditEventRead[];
    loading?: boolean;
    errorMessage?: string;
    showRefresh?: boolean;
  }>(),
  {
    eyebrow: "Audit Trail",
    description: "",
    loading: false,
    errorMessage: "",
    showRefresh: false,
  },
);

defineEmits<{
  refresh: [];
}>();

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
  margin-top: 0.45rem;
  font-weight: 600;
  line-height: 1.4;
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

@keyframes timeline-enter {
  to {
    opacity: 1;
    transform: translateY(0);
  }
}
</style>
