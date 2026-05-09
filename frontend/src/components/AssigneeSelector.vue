<template>
  <!-- Inline assignment row — no card wrapper so it fits inside any detail section -->
  <div class="assignee-selector">
    <div class="assignee-row">
      <span class="assignee-label">Assigned to</span>

      <!-- View mode -->
      <template v-if="!editing">
        <span v-if="assignedUser" class="assignee-value">
          <span class="assignee-avatar">{{ initials(assignedUser) }}</span>
          {{ assignedUser.full_name || assignedUser.email }}
        </span>
        <span v-else class="muted assignee-value">Unassigned</span>
        <button class="btn-link" @click="startEdit">{{ assignedUser ? "Change" : "Assign" }}</button>
      </template>

      <!-- Edit mode -->
      <template v-else>
        <select v-model="selectedId" class="assignee-select" :disabled="isSaving">
          <option value="">— Unassign —</option>
          <option v-for="u in users" :key="u.id" :value="u.id">
            {{ u.full_name || u.email }}
          </option>
        </select>
        <button class="btn btn-primary btn-xs" :disabled="isSaving" @click="save">
          {{ isSaving ? "…" : "Save" }}
        </button>
        <button class="btn btn-ghost btn-xs" :disabled="isSaving" @click="cancel">Cancel</button>
      </template>
    </div>

    <!-- Due date row -->
    <div class="assignee-row">
      <span class="assignee-label">Due date</span>

      <template v-if="!editingDue">
        <span v-if="modelDueDate" :class="['assignee-value', isPast(modelDueDate) ? 'text-danger' : '']">
          {{ formatDate(modelDueDate) }}
        </span>
        <span v-else class="muted assignee-value">No due date</span>
        <button class="btn-link" @click="startEditDue">Set</button>
      </template>

      <template v-else>
        <input v-model="dueInput" type="date" class="assignee-date-input" :disabled="isSavingDue" />
        <button class="btn btn-primary btn-xs" :disabled="isSavingDue" @click="saveDue">
          {{ isSavingDue ? "…" : "Save" }}
        </button>
        <button class="btn btn-ghost btn-xs" :disabled="isSavingDue" @click="cancelDue">Cancel</button>
      </template>
    </div>

    <div v-if="saveError" class="feedback-inline feedback-error">{{ saveError }}</div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from "vue";

import { userService, type UserSummary } from "@/services/user-service";

// ── Props & emits ─────────────────────────────────────────────────────────────
const props = defineProps<{
  /** Current assigned user ID (null = unassigned). */
  assignedToUserId: string | null;
  /** Current due date as ISO date string YYYY-MM-DD (null = none). */
  modelDueDate: string | null;
}>();

const emit = defineEmits<{
  /** Emitted when the assignee changes. Payload is the new user ID or null. */
  (e: "update:assignedToUserId", value: string | null): void;
  /** Emitted when the due date changes. Payload is YYYY-MM-DD or null. */
  (e: "update:modelDueDate", value: string | null): void;
}>();

// ── State ─────────────────────────────────────────────────────────────────────
const users = ref<UserSummary[]>([]);
const editing = ref(false);
const selectedId = ref<string>("");
const isSaving = ref(false);
const saveError = ref<string | null>(null);

const editingDue = ref(false);
const dueInput = ref("");
const isSavingDue = ref(false);

// ── Derived ───────────────────────────────────────────────────────────────────
const assignedUser = computed(() =>
  props.assignedToUserId ? users.value.find((u) => u.id === props.assignedToUserId) ?? null : null
);

// ── Lifecycle ─────────────────────────────────────────────────────────────────
onMounted(async () => {
  try {
    users.value = await userService.listSummary();
  } catch {
    // Non-fatal — selector stays empty; user can still see current assignee.
  }
});

// ── Assignee editing ──────────────────────────────────────────────────────────
function startEdit(): void {
  selectedId.value = props.assignedToUserId ?? "";
  editing.value = true;
  saveError.value = null;
}

function cancel(): void {
  editing.value = false;
}

async function save(): Promise<void> {
  isSaving.value = true;
  saveError.value = null;
  try {
    emit("update:assignedToUserId", selectedId.value || null);
    editing.value = false;
  } catch {
    saveError.value = "Failed to save assignee.";
  } finally {
    isSaving.value = false;
  }
}

// ── Due date editing ──────────────────────────────────────────────────────────
function startEditDue(): void {
  dueInput.value = props.modelDueDate ?? "";
  editingDue.value = true;
}

function cancelDue(): void {
  editingDue.value = false;
}

async function saveDue(): Promise<void> {
  isSavingDue.value = true;
  try {
    emit("update:modelDueDate", dueInput.value || null);
    editingDue.value = false;
  } finally {
    isSavingDue.value = false;
  }
}

// ── Helpers ───────────────────────────────────────────────────────────────────
function initials(u: UserSummary): string {
  const name = u.full_name || u.email;
  return name.split(" ").map((w) => w[0]).slice(0, 2).join("").toUpperCase();
}

function formatDate(iso: string): string {
  return new Date(iso).toLocaleDateString(undefined, { dateStyle: "medium" });
}

function isPast(iso: string): boolean {
  return new Date(iso) < new Date(new Date().toDateString());
}
</script>

<style scoped>
.assignee-selector {
  display: flex;
  flex-direction: column;
  gap: 0.4rem;
}

.assignee-row {
  display: flex;
  align-items: center;
  gap: 0.6rem;
  font-size: 0.85rem;
  flex-wrap: wrap;
}

.assignee-label {
  font-weight: 600;
  color: var(--color-text-muted, #64748b);
  min-width: 5.5rem;
}

.assignee-value {
  display: flex;
  align-items: center;
  gap: 0.4rem;
}

.assignee-avatar {
  width: 1.4rem;
  height: 1.4rem;
  border-radius: 50%;
  background: var(--color-primary, #2563eb);
  color: #fff;
  font-size: 0.6rem;
  font-weight: 700;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.assignee-select {
  border: 1px solid var(--color-border, #e2e8f0);
  border-radius: 5px;
  padding: 0.2rem 0.5rem;
  font-size: 0.82rem;
  background: var(--color-surface, #fff);
  color: var(--color-text, #1e293b);
  max-width: 14rem;
}

.assignee-date-input {
  border: 1px solid var(--color-border, #e2e8f0);
  border-radius: 5px;
  padding: 0.2rem 0.5rem;
  font-size: 0.82rem;
  background: var(--color-surface, #fff);
  color: var(--color-text, #1e293b);
}

.btn-link {
  background: none;
  border: none;
  padding: 0;
  font-size: 0.78rem;
  cursor: pointer;
  color: var(--color-primary, #2563eb);
  text-decoration: underline;
}

.btn-xs {
  padding: 0.2rem 0.6rem;
  font-size: 0.78rem;
}

.btn-ghost {
  background: transparent;
  border: 1px solid var(--color-border, #e2e8f0);
  color: var(--color-text, #1e293b);
  border-radius: 5px;
  cursor: pointer;
}

.feedback-inline {
  font-size: 0.78rem;
  padding: 0.2rem 0.5rem;
  border-radius: 4px;
}

.feedback-error {
  background: #fef2f2;
  color: #dc2626;
}

.text-danger {
  color: var(--color-danger, #dc2626);
  font-weight: 600;
}
</style>
