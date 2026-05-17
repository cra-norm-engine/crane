<template>
  <div
    class="drop-zone"
    :class="{ 'drop-zone-active': isDragging }"
    @dragover.prevent="isDragging = true"
    @dragleave.prevent="isDragging = false"
    @drop.prevent="onDrop"
  >
    <div class="drop-zone-content">
      <div class="drop-zone-icon">📁</div>
      <p class="drop-zone-text">
        Drop files here or <label class="drop-zone-link">browse
          <input
            ref="fileInput"
            type="file"
            :accept="accept"
            :multiple="multiple"
            class="drop-zone-input"
            @change="onFileInputChange"
          />
        </label>
      </p>
      <p v-if="hint" class="drop-zone-hint">{{ hint }}</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from "vue";

const props = withDefaults(
  defineProps<{
    accept?: string;
    multiple?: boolean;
    hint?: string;
  }>(),
  {
    accept: "*",
    multiple: false,
    hint: undefined,
  },
);

const emit = defineEmits<{
  "files-selected": [files: File[]];
}>();

const isDragging = ref(false);
const fileInput = ref<HTMLInputElement>();

function onDrop(event: DragEvent) {
  isDragging.value = false;
  const files = event.dataTransfer?.files;
  if (files && files.length > 0) {
    const fileArray = Array.from(files);
    emit("files-selected", fileArray);
  }
}

function onFileInputChange(event: Event) {
  const target = event.target as HTMLInputElement;
  const files = target.files;
  if (files && files.length > 0) {
    const fileArray = Array.from(files);
    emit("files-selected", fileArray);
  }
  if (fileInput.value) {
    fileInput.value.value = "";
  }
}
</script>

<style scoped>
.drop-zone {
  border: 2px dashed var(--color-border);
  border-radius: 0.85rem;
  padding: 2rem;
  text-align: center;
  cursor: pointer;
  transition: all 0.2s ease;
  background: var(--color-surface-soft);
}

.drop-zone:hover {
  border-color: var(--color-primary);
  background: var(--color-surface-elevated);
}

.drop-zone-active {
  border-color: rgba(175, 214, 46, 0.7);
  background: rgba(175, 214, 46, 0.08);
  box-shadow: 0 0 0 4px rgba(112, 185, 23, 0.12);
}

.drop-zone-content {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  align-items: center;
}

.drop-zone-icon {
  font-size: 2rem;
  opacity: 0.7;
}

.drop-zone-text {
  margin: 0;
  font-size: 0.95rem;
  color: var(--color-text);
}

.drop-zone-link {
  color: var(--color-primary);
  font-weight: 500;
  cursor: pointer;
  text-decoration: underline;
}

.drop-zone-link:hover {
  text-decoration-color: transparent;
}

.drop-zone-input {
  display: none;
}

.drop-zone-hint {
  margin: 0;
  font-size: 0.8rem;
  color: var(--color-text-muted);
}
</style>
