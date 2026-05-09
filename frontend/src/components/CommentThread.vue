<template>
  <section class="comment-thread">
    <h3 class="comment-thread-title">
      Comments
      <span v-if="comments.length" class="comment-count">{{ comments.length }}</span>
    </h3>

    <!-- Error banner -->
    <div v-if="loadError" class="feedback feedback-error">{{ loadError }}</div>

    <!-- Comment list -->
    <div v-if="isLoading" class="comment-empty">Loading comments…</div>

    <div v-else-if="comments.length === 0 && !isLoading" class="comment-empty">
      No comments yet. Be the first to add one.
    </div>

    <ul v-else class="comment-list">
      <li v-for="c in comments" :key="c.id" class="comment-item">
        <div class="comment-meta">
          <!-- Author avatar initials -->
          <span class="comment-avatar">{{ initials(c.author) }}</span>
          <span class="comment-author">{{ displayName(c.author) }}</span>
          <span class="comment-date muted">{{ formatDate(c.created_at) }}</span>
          <span v-if="c.updated_at !== c.created_at" class="comment-edited muted">(edited)</span>
        </div>

        <!-- View mode -->
        <div v-if="editingId !== c.id" class="comment-body">{{ c.body }}</div>

        <!-- Edit mode — only the author can edit -->
        <div v-else class="comment-edit-form">
          <textarea
            v-model.trim="editBody"
            class="comment-textarea"
            rows="3"
            :disabled="isSaving"
          />
          <div class="comment-edit-actions">
            <button class="btn btn-primary btn-sm" :disabled="!editBody || isSaving" @click="saveEdit(c.id)">
              Save
            </button>
            <button class="btn btn-ghost btn-sm" @click="cancelEdit">Cancel</button>
          </div>
        </div>

        <!-- Per-comment actions (author or admin only) -->
        <div v-if="editingId !== c.id" class="comment-actions">
          <button
            v-if="canEdit(c)"
            class="btn-link"
            @click="startEdit(c)"
          >
            Edit
          </button>
          <button
            v-if="canDelete(c)"
            class="btn-link btn-link-danger"
            @click="confirmDelete(c.id)"
          >
            Delete
          </button>
        </div>
      </li>
    </ul>

    <!-- New comment form -->
    <form class="comment-compose" @submit.prevent="postComment">
      <textarea
        v-model.trim="newBody"
        class="comment-textarea"
        rows="3"
        placeholder="Write a comment…"
        :disabled="isPosting"
      />
      <div class="comment-compose-actions">
        <button
          class="btn btn-primary btn-sm"
          type="submit"
          :disabled="!newBody || isPosting"
        >
          {{ isPosting ? "Posting…" : "Post comment" }}
        </button>
      </div>
      <div v-if="postError" class="feedback feedback-error">{{ postError }}</div>
    </form>
  </section>
</template>

<script setup lang="ts">
import { onMounted, ref } from "vue";

import { commentService } from "@/services/comment-service";
import { useAuthStore } from "@/stores/auth";
import type { CommentRead } from "@/types/comment";

// ── Props ─────────────────────────────────────────────────────────────────────
const props = defineProps<{
  entityType: string;
  entityId: string;
}>();

// ── State ─────────────────────────────────────────────────────────────────────
const auth = useAuthStore();

const comments = ref<CommentRead[]>([]);
const isLoading = ref(false);
const loadError = ref<string | null>(null);

const newBody = ref("");
const isPosting = ref(false);
const postError = ref<string | null>(null);

const editingId = ref<string | null>(null);
const editBody = ref("");
const isSaving = ref(false);

// ── Data loading ──────────────────────────────────────────────────────────────
async function loadComments(): Promise<void> {
  isLoading.value = true;
  loadError.value = null;
  try {
    comments.value = await commentService.list(props.entityType, props.entityId);
  } catch {
    loadError.value = "Failed to load comments.";
  } finally {
    isLoading.value = false;
  }
}

onMounted(loadComments);

// ── Post a new comment ────────────────────────────────────────────────────────
async function postComment(): Promise<void> {
  if (!newBody.value) return;
  isPosting.value = true;
  postError.value = null;
  try {
    const created = await commentService.create({
      entity_type: props.entityType,
      entity_id: props.entityId,
      body: newBody.value,
    });
    comments.value.push(created);
    newBody.value = "";
  } catch {
    postError.value = "Failed to post comment. Please try again.";
  } finally {
    isPosting.value = false;
  }
}

// ── Edit an existing comment ──────────────────────────────────────────────────
function startEdit(c: CommentRead): void {
  editingId.value = c.id;
  editBody.value = c.body;
}

function cancelEdit(): void {
  editingId.value = null;
  editBody.value = "";
}

async function saveEdit(commentId: string): Promise<void> {
  if (!editBody.value) return;
  isSaving.value = true;
  try {
    const updated = await commentService.update(commentId, { body: editBody.value });
    const idx = comments.value.findIndex((c) => c.id === commentId);
    if (idx !== -1) comments.value[idx] = updated;
    cancelEdit();
  } catch {
    // Keep edit form open so the user can retry.
  } finally {
    isSaving.value = false;
  }
}

// ── Delete a comment ──────────────────────────────────────────────────────────
async function confirmDelete(commentId: string): Promise<void> {
  if (!confirm("Delete this comment? This cannot be undone.")) return;
  try {
    await commentService.remove(commentId);
    comments.value = comments.value.filter((c) => c.id !== commentId);
  } catch {
    // Silent — the comment stays visible if deletion failed.
  }
}

// ── Permission helpers ────────────────────────────────────────────────────────
function canEdit(c: CommentRead): boolean {
  return c.author_user_id === auth.user?.id;
}

function canDelete(c: CommentRead): boolean {
  return c.author_user_id === auth.user?.id || auth.hasRole("admin");
}

// ── Display helpers ───────────────────────────────────────────────────────────
function displayName(author: CommentRead["author"]): string {
  return author?.full_name ?? author?.email ?? "Unknown";
}

function initials(author: CommentRead["author"]): string {
  const name = author?.full_name ?? author?.email ?? "?";
  return name
    .split(" ")
    .map((w) => w[0])
    .slice(0, 2)
    .join("")
    .toUpperCase();
}

function formatDate(iso: string): string {
  return new Date(iso).toLocaleString(undefined, {
    dateStyle: "medium",
    timeStyle: "short",
  });
}
</script>

<style scoped>
/* ── Thread container ──────────────────────────────────────────────────────── */
.comment-thread {
  margin-top: 1.5rem;
  border-top: 1px solid var(--color-border, #e2e8f0);
  padding-top: 1.25rem;
}

.comment-thread-title {
  font-size: 0.9rem;
  font-weight: 600;
  letter-spacing: 0.04em;
  text-transform: uppercase;
  color: var(--color-text-muted, #64748b);
  margin: 0 0 1rem;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.comment-count {
  background: var(--color-surface-alt, #f1f5f9);
  border-radius: 999px;
  padding: 0 0.45rem;
  font-size: 0.78rem;
  font-weight: 700;
  color: var(--color-text, #1e293b);
}

/* ── Comment list ─────────────────────────────────────────────────────────── */
.comment-list {
  list-style: none;
  padding: 0;
  margin: 0 0 1.25rem;
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.comment-item {
  display: flex;
  flex-direction: column;
  gap: 0.3rem;
}

.comment-meta {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.82rem;
}

.comment-avatar {
  width: 1.6rem;
  height: 1.6rem;
  border-radius: 50%;
  background: var(--color-primary, #2563eb);
  color: #fff;
  font-size: 0.65rem;
  font-weight: 700;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.comment-author {
  font-weight: 600;
  color: var(--color-text, #1e293b);
}

.comment-date,
.comment-edited {
  font-size: 0.78rem;
}

.comment-body {
  font-size: 0.88rem;
  color: var(--color-text, #1e293b);
  white-space: pre-wrap;
  padding-left: 2.1rem;
  line-height: 1.55;
}

.comment-actions {
  display: flex;
  gap: 0.75rem;
  padding-left: 2.1rem;
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

.btn-link-danger {
  color: var(--color-danger, #dc2626);
}

/* ── Edit form ────────────────────────────────────────────────────────────── */
.comment-edit-form {
  padding-left: 2.1rem;
  display: flex;
  flex-direction: column;
  gap: 0.4rem;
}

.comment-edit-actions {
  display: flex;
  gap: 0.5rem;
}

/* ── Compose area ─────────────────────────────────────────────────────────── */
.comment-compose {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.comment-textarea {
  width: 100%;
  border: 1px solid var(--color-border, #e2e8f0);
  border-radius: 6px;
  padding: 0.5rem 0.75rem;
  font-size: 0.88rem;
  font-family: inherit;
  resize: vertical;
  background: var(--color-surface, #fff);
  color: var(--color-text, #1e293b);
  box-sizing: border-box;
}

.comment-textarea:focus {
  outline: 2px solid var(--color-primary, #2563eb);
  outline-offset: 1px;
}

.comment-compose-actions {
  display: flex;
  justify-content: flex-end;
}

/* ── Empty / loading states ───────────────────────────────────────────────── */
.comment-empty {
  font-size: 0.88rem;
  color: var(--color-text-muted, #64748b);
  padding: 0.5rem 0 1rem;
}

/* ── Small button variant ─────────────────────────────────────────────────── */
.btn-sm {
  padding: 0.3rem 0.85rem;
  font-size: 0.82rem;
}

.btn-ghost {
  background: transparent;
  border: 1px solid var(--color-border, #e2e8f0);
  color: var(--color-text, #1e293b);
}

.btn-ghost:hover {
  background: var(--color-surface-alt, #f1f5f9);
}

/* ── Light-mode explicit overrides ───────────────────────────────────────── */
:root:not(.dark) .comment-textarea {
  background: #fff;
  color: #1e293b;
  border-color: #cbd5e1;
}

:root:not(.dark) .comment-avatar {
  background: #2563eb;
}
</style>
